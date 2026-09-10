"""
robust_fitting.py
------------------
Ajuste robusto del borde, resistente a burbujas.

Por cada frame tenemos ~N puntos (x, y_borde), uno por columna
muestreada. Si una burbuja tapa el borde en 3-4 columnas, esos puntos
van a tener un y_borde muy distinto al resto (o directamente NaN si
edge_detection.py ya los descartó por bajo gradiente). En vez de
promediar todo, ajustamos un modelo robusto que IGNORA outliers.

POR QUÉ CAMBIÓ EL UMBRAL (lección del Video_063)
-------------------------------------------------
RANSAC separa inliers de outliers comparando el residuo de cada punto
contra `residual_threshold`. Ese umbral tiene que quedar ENTRE dos
escalas:

    ruido de medición  <  residual_threshold  <  desplazamiento por burbuja

Con un valor FIJO (1.5 px) eso no se cumple solo. En el Video_063 el
borde superior tiene una curvatura residual de 1.18 px de desviación
estándar (máx 3.15 px) porque la ROI caía sobre el hombro del anclaje:
el umbral quedó POR DEBAJO del error de modelo. Consecuencia: RANSAC
descartaba geometría buena (9 columnas contiguas marcadas "burbuja"),
y — peor — el conjunto de inliers cambiaba de un frame al siguiente.
Ese cambio de conjunto mueve la recta ajustada y mete saltos discretos
en la serie de grosor.

Medido sobre las 60 columnas reales de ese video, con el gel INMÓVIL y
solo ruido de medición por columna:

    grado 1, umbral 1.5 fijo  ->  std artefacto 0.249 px  (p2p 1.15 px)
    grado 1, umbral 2.5       ->  std artefacto 0.088 px
    grado 2, umbral 1.5       ->  std artefacto 0.093 px
    grado 2, umbral adaptativo->  del mismo orden que los anteriores

La serie real de ese video tiene std 0.361 px: es decir, ~70% de la
"señal" era artefacto de ajuste.

Solución adoptada: `residual_threshold=None` (default) mide el MAD de
los residuos DE ESE FRAME contra un ajuste polinómico recortado, y usa
`k * MAD` como umbral. Así el umbral se adapta solo a cada video y a
cada frame, en vez de estar calibrado a un único video de ejemplo.
"""

from __future__ import annotations
from dataclasses import dataclass
import numpy as np
from sklearn.linear_model import RANSACRegressor
from sklearn.preprocessing import PolynomialFeatures
from sklearn.pipeline import make_pipeline


@dataclass
class RobustEdgeFit:
    x: np.ndarray
    y_fitted: np.ndarray      # valor del modelo evaluado en x (todas las columnas)
    inlier_mask: np.ndarray   # True = columna confiable, False = outlier/burbuja
    n_inliers: int
    n_outliers: int
    residual_px: float = float("nan")   # MAD de los residuos de los inliers
    threshold_px: float = float("nan")  # umbral efectivamente usado


def _robust_mad(v: np.ndarray) -> float:
    v = np.asarray(v, dtype=float)
    if v.size == 0:
        return float("nan")
    return float(np.median(np.abs(v - np.median(v))) * 1.4826)


def _trimmed_polyfit(x: np.ndarray, y: np.ndarray, degree: int,
                     n_iter: int = 2, k: float = 3.0) -> tuple[np.ndarray, float]:
    """
    Ajuste polinómico con recorte iterativo de outliers.

    Sirve SOLO para estimar la ESCALA del residuo (no es el ajuste
    final: ese lo hace RANSAC). Dos iteraciones alcanzan para que unos
    pocos puntos de burbuja no inflen el MAD.
    """
    keep = np.ones(len(x), dtype=bool)
    coef = np.polyfit(x, y, degree)
    for _ in range(n_iter):
        r = y - np.polyval(coef, x)
        med = np.median(r)
        mad = _robust_mad(r)
        if not np.isfinite(mad) or mad <= 0:
            break
        keep = np.abs(r - med) <= k * mad
        if keep.sum() <= degree + 2:
            break
        coef = np.polyfit(x[keep], y[keep], degree)
    r = y - np.polyval(coef, x)
    return coef, _robust_mad(r)


def fit_edge_ransac(
    x: np.ndarray,
    y: np.ndarray,
    degree: int = 2,
    residual_threshold: float | None = None,
    min_valid_points: int = 10,
    residual_k: float = 3.0,
    residual_floor: float = 0.4,
    max_trials: int = 200,
) -> RobustEdgeFit | None:
    """
    Ajusta el borde (top o bottom) con RANSAC, tolerante a outliers.

    Parameters
    ----------
    x, y : puntos (x, y_borde). `y` puede tener NaN (columnas donde no se
        detectó borde); se filtran acá.
    degree : grado del polinomio. 1 = recta. 2 (default) permite seguir
        la leve curvatura que tiene el gel incluso dentro de la gauge
        region — con grado 1 esa curvatura se confunde con burbujas.
        Subir a 3 solo si ves sesgo sistemático en los residuos.
    residual_threshold : distancia máxima (px) para considerar un punto
        inlier. **None (default) = adaptativo**: se mide el MAD de los
        residuos de este frame y se usa `residual_k * MAD`, con piso
        `residual_floor`. Pasá un número solo si querés fijarlo a mano.
    residual_k : multiplicador del MAD cuando el umbral es adaptativo.
        3.0 deja fuera aprox. lo que se aparta más de 3 sigma robustos.
    residual_floor : piso absoluto del umbral (px). Evita que en un frame
        excepcionalmente limpio el umbral se vuelva tan chico que empiece
        a descartar ruido normal.
    min_valid_points : mínimo de puntos no-NaN para confiar en el ajuste.

    Returns
    -------
    RobustEdgeFit, o None si no hay suficientes puntos válidos.
    """
    valid = ~np.isnan(y)
    x_valid = x[valid].astype(np.float64)
    y_valid = y[valid].astype(np.float64)

    if x_valid.shape[0] < min_valid_points:
        return None

    # --- Normalización numérica de x ---
    # Con x en píxeles (~1000) y degree=2, la matriz de diseño tiene
    # columnas de orden 1, 1e3 y 1e6: mal condicionada. Mapeamos x a
    # [-1, 1] antes de ajustar y deshacemos el mapeo al predecir.
    x0 = float(x_valid.mean())
    span = float(x_valid.max() - x_valid.min())
    scale = max(span / 2.0, 1.0)
    xn = (x_valid - x0) / scale

    if residual_threshold is None:
        _, mad = _trimmed_polyfit(xn, y_valid, degree)
        if not np.isfinite(mad) or mad <= 0:
            mad = 0.0
        thr = max(residual_k * mad, residual_floor)
    else:
        thr = float(residual_threshold)

    model = make_pipeline(
        PolynomialFeatures(degree=degree),
        RANSACRegressor(residual_threshold=thr, random_state=0, max_trials=max_trials),
    )
    model.fit(xn.reshape(-1, 1), y_valid)

    ransac: RANSACRegressor = model.named_steps["ransacregressor"]
    inlier_mask_valid = ransac.inlier_mask_

    # Máscara de inliers en el espacio ORIGINAL de x (las columnas que ya
    # eran NaN quedan marcadas como outlier)
    full_inlier_mask = np.zeros_like(x, dtype=bool)
    full_inlier_mask[valid] = inlier_mask_valid

    xn_all = (x.astype(np.float64) - x0) / scale
    y_fitted_all = model.predict(xn_all.reshape(-1, 1))

    resid_in = y_valid[inlier_mask_valid] - model.predict(xn[inlier_mask_valid].reshape(-1, 1))

    return RobustEdgeFit(
        x=x,
        y_fitted=y_fitted_all,
        inlier_mask=full_inlier_mask,
        n_inliers=int(full_inlier_mask.sum()),
        n_outliers=int((~full_inlier_mask).sum()),
        residual_px=_robust_mad(resid_in),
        threshold_px=float(thr),
    )


def fit_edge_median(x: np.ndarray, y: np.ndarray, mad_k: float = 3.5) -> RobustEdgeFit | None:
    """
    Alternativa liviana a RANSAC: mediana + MAD, sin scikit-learn.

    ATENCIÓN: este método ajusta una CONSTANTE, o sea que asume que el
    borde es horizontal. Si el borde tiene pendiente (en el Video_063 el
    borde superior baja 9 px a lo largo de la ROI), la mediana no
    representa la geometría y este método va a marcar como outlier a los
    extremos de la ROI. Usalo solo para un preview rápido o cuando ya
    verificaste que el borde es realmente plano; para medir, usá RANSAC.

    Un punto se descarta si |y_i - mediana(y)| > mad_k * MAD, con
    MAD = mediana(|y_i - mediana(y)|) * 1.4826.
    """
    valid = ~np.isnan(y)
    if valid.sum() < 5:
        return None

    y_valid = y[valid]
    median_y = np.median(y_valid)
    mad = _robust_mad(y_valid)

    if not np.isfinite(mad) or mad < 1e-6:
        inlier_valid = np.ones_like(y_valid, dtype=bool)
        thr = float("nan")
    else:
        thr = mad_k * mad
        inlier_valid = np.abs(y_valid - median_y) <= thr

    full_inlier_mask = np.zeros_like(x, dtype=bool)
    full_inlier_mask[valid] = inlier_valid

    robust_value = np.median(y_valid[inlier_valid])
    y_fitted_all = np.full_like(x, robust_value, dtype=float)

    return RobustEdgeFit(
        x=x,
        y_fitted=y_fitted_all,
        inlier_mask=full_inlier_mask,
        n_inliers=int(full_inlier_mask.sum()),
        n_outliers=int((~full_inlier_mask).sum()),
        residual_px=_robust_mad(y_valid[inlier_valid] - robust_value),
        threshold_px=float(thr),
    )
