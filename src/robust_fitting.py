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

from src.estadistica import mad as _mad


# --------------------------------------------------------------------------
# RANSAC PROPIO (2026-10-08). Mismo algoritmo que el RANSACRegressor de
# sklearn, paso por paso, sin su estructura de objetos (que era casi todo el
# costo: ~7 ms por ajuste contra ~1.3 ms, y ~4000 ajustes por video):
#   - 4 columnas al azar por intento (sklearn usa n_variables + 1 = 4 con la
#     parabola [1, x, x^2]), sorteadas con EL MISMO sorteador y la misma
#     semilla que sklearn (`sample_without_replacement`, RandomState(0));
#   - inlier = |residuo| <= umbral; gana el intento con mas inliers y, si
#     empatan, el de mejor R^2 sobre sus inliers (empate exacto: el ultimo);
#   - corte dinamico de intentos con probabilidad 0.99, maximo `max_trials`;
#   - ajuste final por minimos cuadrados con los inliers del mejor intento.
# Medido en los seis videos validados: las mismas columnas inlier en todos los
# fotogramas, center_px identico, mismos conteos; las cuentas difieren solo en
# la cifra 12. Test: tests/test_ransac.py.
# --------------------------------------------------------------------------


def _parabola(xn, y, degree=2):
    A = np.vander(xn, degree + 1)             # columnas x^d ... x, 1
    return np.linalg.lstsq(A, y, rcond=None)[0]


def _r2(y, yp):
    ss_tot = float(((y - y.mean()) ** 2).sum())
    ss_res = float(((y - yp) ** 2).sum())
    if ss_tot == 0.0:
        return 1.0 if ss_res == 0.0 else 0.0   # como sklearn.metrics.r2_score
    return 1.0 - ss_res / ss_tot


def _ransac_propio(xn, y, thr, max_trials, degree=2, stop_probability=0.99):
    from sklearn.utils.random import sample_without_replacement
    n, m = len(xn), degree + 2          # como sklearn: n_variables + 1
    rs = np.random.RandomState(0)
    best_n, best_score, best_mask = 1, -np.inf, None
    tope, t = max_trials, 0
    while t < tope:
        t += 1
        idx = sample_without_replacement(n, m, random_state=rs)
        coef = _parabola(xn[idx], y[idx], degree)
        mask = np.abs(y - np.polyval(coef, xn)) <= thr
        k = int(mask.sum())
        if k < best_n:
            continue
        score = _r2(y[mask], np.polyval(coef, xn[mask]))
        if k == best_n and score < best_score:
            continue
        best_n, best_score, best_mask = k, score, mask
        ratio = k / n
        nom = max(np.spacing(1), 1 - stop_probability)
        den = max(np.spacing(1), 1 - ratio ** m)
        dyn = 0 if nom == 1 else (float("inf") if den == 1 else abs(float(np.ceil(np.log(nom) / np.log(den)))))
        tope = min(tope, dyn)
    if best_mask is None:
        raise ValueError("RANSAC propio: ningun intento valido")
    return best_mask, _parabola(xn[best_mask], y[best_mask], degree)


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
    # Una sola definicion para todo el proyecto (src/estadistica.py). Aca las
    # entradas ya vienen sin NaN (se filtran con ~np.isnan antes).
    return _mad(v)


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

    inlier_mask_valid, coef = _ransac_propio(xn, y_valid, thr, max_trials, degree)

    # Máscara de inliers en el espacio ORIGINAL de x (las columnas que ya
    # eran NaN quedan marcadas como outlier)
    full_inlier_mask = np.zeros_like(x, dtype=bool)
    full_inlier_mask[valid] = inlier_mask_valid

    xn_all = (x.astype(np.float64) - x0) / scale
    y_fitted_all = np.polyval(coef, xn_all)
    resid_in = y_valid[inlier_mask_valid] - np.polyval(coef, xn[inlier_mask_valid])

    return RobustEdgeFit(
        x=x,
        y_fitted=y_fitted_all,
        inlier_mask=full_inlier_mask,
        n_inliers=int(full_inlier_mask.sum()),
        n_outliers=int((~full_inlier_mask).sum()),
        residual_px=_robust_mad(resid_in),
        threshold_px=float(thr),
    )
