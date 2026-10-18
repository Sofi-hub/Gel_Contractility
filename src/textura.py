"""
src/textura.py
--------------
Medición por DESPLAZAMIENTO DE TEXTURA, sin bordes (`main.py --metodo textura`).

Para videos donde el borde del gel no es un escalón nítido (videos de Andrés,
2026-10-16: 4K, borde = rampa granulada; por bordes dan 0 eventos). Mide lo
mismo que `center_px`: el corrimiento vertical de la franja del gel (con el gel
ya horizontal), pero siguiendo la textura de toda la franja en vez de los dos
bordes. Es geometría (cuánto se corre la imagen), no intensidad.

Cómo:
  1. Referencia = promedio de los N_REF primeros fotogramas, suavizado (SIGMA).
  2. Franja, sin bordes: perfil de brillo por filas en la mitad central de las
     columnas; tramo seguido más largo por encima de la mitad entre los
     percentiles 5 y 95. Margen hacia afuera: MARGEN x grosor (incluye la rampa).
     Grosor en reposo (aproximado) = ancho de ese tramo, a media altura.
  3. Cada fotograma: corrimiento entero por correlación de fase y la fracción
     por mínimos cuadrados del gradiente (Lucas-Kanade en una dimensión,
     iterado: se corre el fotograma lo ya medido y se vuelve a medir). La
     correlación de fase sola tira los corrimientos chicos hacia el entero
     (sintético: 0.25 px -> 0.04 px); así, 0.5-4 px se miden a +-5 %.

Validación (data/_mediciones_fases/textura/LEEME.md): sintético de corrimiento
conocido; contra center_px en los 7 reportables, todos los eventos de bordes
aparecen en el mismo instante y la amplitud da 0.87-0.98 de la de bordes. Con
menos ruido que los bordes ve más: 583 queda NO REPORTABLE (vibración) y en 466
un evento se parte en dos. Por eso es una OPCIÓN, no el método por defecto.
"""
from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

from src import io_utils

N_REF = 30        # fotogramas promediados para la referencia
SIGMA = 1.5       # suavizado (px) de referencia y fotogramas
MARGEN = 0.15     # margen de la franja, en fracción del grosor
MARGEN_CORRIMIENTO = 40   # filas que puede correrse la franja dentro de lo leído (px)
LADO_MAX = 1920   # 2026-10-17: fotogramas más grandes (4K) se achican a este lado mayor
PAD = 12          # filas extra al suavizar solo la franja (> 3 sigma: mismo resultado)


def escala_de(video_path) -> float:
    """Factor para achicar (1 = sin cambio). 4K en una notebook: ~1 h por video sin
    achicar (2026-10-17); a la mitad, 4 veces menos píxeles. Validado con la copia x0.5
    de 40V/1 (ruido 0.018 px de la copia, 5 contracciones)."""
    m = io_utils.get_video_metadata(video_path)
    lado = max(m["width"], m["height"])
    return 1.0 if lado <= LADO_MAX else LADO_MAX / lado


def _achicar(f, escala):
    if escala == 1.0:
        return f
    return cv2.resize(f, (round(f.shape[1] * escala), round(f.shape[0] * escala)),
                      interpolation=cv2.INTER_AREA)


def referencia(video_path, rotacion: int, n: int = N_REF, escala: float = 1.0) -> np.ndarray:
    """Promedio de los n primeros fotogramas (ya girados y achicados), float32, sin suavizar."""
    acc, k = None, 0
    for _, f in io_utils.frame_generator(video_path, end_frame=n, rotacion=rotacion):
        f = _achicar(f, escala)
        acc = f.astype(np.float64) if acc is None else acc + f
        k += 1
    if acc is None:
        raise IOError(f"No se pudo leer ningún fotograma de: {video_path}")
    return (acc / k).astype(np.float32)


def franja(ref: np.ndarray, x0: int, x1: int) -> tuple[int, int, float, np.ndarray]:
    """(y0, y1, grosor_px, perfil). y0:y1 = franja con margen; grosor = sin margen."""
    p = ref[:, x0:x1].mean(axis=1).astype(np.float64)
    s = max(2.0, len(p) / 200)
    p = cv2.GaussianBlur(p.reshape(-1, 1), (1, 0), sigmaX=0, sigmaY=s).ravel()
    lo, hi = np.percentile(p, 5), np.percentile(p, 95)
    on = np.r_[False, p > lo + 0.5 * (hi - lo), False]
    d = np.diff(on.astype(int))
    ini, fin = np.where(d == 1)[0], np.where(d == -1)[0]
    if len(ini) == 0:
        raise ValueError("No se encontró la franja del gel en la imagen de referencia.")
    j = int(np.argmax(fin - ini))
    a, b = int(ini[j]), int(fin[j])
    m = int(round(MARGEN * (b - a)))
    return max(0, a - m), min(len(p), b + m), float(b - a), p


def medir(video_path, rotacion: int, n_max: int | None = None,
          resolucion_completa: bool = False) -> dict:
    """Corrimiento vertical de la franja (px) en cada fotograma, contra la referencia.

    Devuelve dict: dy (array), respuesta (pico de la correlación de fase, 0-1),
    y0, y1, x0, x1 (zona usada), grosor_px, centro_ref (centro de la franja en
    la referencia), ref (imagen de referencia) y perfil.
    Todo en píxeles del video ORIGINAL (si se achicó, se multiplica por 1/escala);
    y0..x1 y la figura quedan en píxeles de la imagen achicada (escala)."""
    escala = 1.0 if resolucion_completa else escala_de(video_path)
    ref_crudo = referencia(video_path, rotacion, escala=escala)
    ref = cv2.GaussianBlur(ref_crudo, (0, 0), SIGMA)
    h, w = ref.shape
    x0, x1 = w // 4, w - w // 4
    y0, y1, grosor, perfil = franja(ref, x0, x1)
    a, b = y0 + MARGEN_CORRIMIENTO, y1 - MARGEN_CORRIMIENTO
    if b - a < 20:
        a, b = y0, y1
    R = ref[a:b, x0:x1]
    G = np.gradient(ref, axis=0)[a:b, x0:x1]
    G2 = float(np.sum(G * G))
    Rpc = ref[y0:y1, x0:x1]
    win = cv2.createHanningWindow((x1 - x0, y1 - y0), cv2.CV_32F)
    # solo se suaviza la franja (+PAD filas): fuera de PAD el suavizado no llega
    B0, B1 = max(0, y0 - PAD), min(h, y1 + PAD)
    kmin, kmax = (B0 - a) + 2, (B1 - b) - 2
    mx = np.arange(x1 - x0, dtype=np.float32)[None, :].repeat(b - a, 0)
    filas = np.arange(b - a, dtype=np.float32)[:, None].repeat(x1 - x0, 1)
    dy, resp = [], []
    for _, f in io_utils.frame_generator(video_path, end_frame=n_max, rotacion=rotacion):
        f = _achicar(f, escala)
        fb = cv2.GaussianBlur(f[B0:B1].astype(np.float32), (0, 0), SIGMA)[:, x0:x1]
        (_, sy), r = cv2.phaseCorrelate(Rpc, fb[y0 - B0:y1 - B0], win)
        k = int(np.clip(round(sy), kmin, kmax))
        F0 = fb[a + k - 2 - B0:b + k + 2 - B0]          # 2 filas extra para interpolar
        d_fr = 0.0
        for _ in range(5):
            # F0 muestreado en y + d_fr (corrido de vuelta la parte ya medida)
            F = cv2.remap(F0, mx, filas + (2 + d_fr), cv2.INTER_CUBIC,
                          borderMode=cv2.BORDER_REPLICATE)
            # F(y) ~ R(y - r) ~ R - r*G   ->   r = sum(G (R - F)) / sum(G^2)
            r_ = float(np.sum(G * (R - F)) / G2)
            d_fr += r_
            if abs(r_) < 1e-4 or abs(d_fr) > 1.5:
                break
        dy.append((k + d_fr) / escala)
        resp.append(float(r))
    return dict(dy=np.asarray(dy), respuesta=np.asarray(resp), y0=y0, y1=y1, x0=x0, x1=x1,
                zona_y=(a, b), grosor_px=grosor / escala, centro_ref=(y0 + y1) / 2.0 / escala,
                escala=escala,
                ref=ref_crudo, perfil=perfil)


def graficar_franja(m: dict, salida: Path, titulo: str = "") -> Path:
    """Figura de control (cero cajas negras): la referencia con la zona usada
    y el perfil de brillo con la franja elegida."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(1, 2, figsize=(11, 4.5), gridspec_kw={"width_ratios": [3, 1]})
    ax[0].imshow(m["ref"], cmap="gray")
    ax[0].add_patch(plt.Rectangle((m["x0"], m["y0"]), m["x1"] - m["x0"], m["y1"] - m["y0"],
                                  fill=False, ec="tab:orange", lw=1.5, label="franja (con margen)"))
    a, b = m["zona_y"]
    ax[0].add_patch(plt.Rectangle((m["x0"], a), m["x1"] - m["x0"], b - a, fill=False,
                                  ec="tab:cyan", lw=1, ls="--", label="zona comparada"))
    ax[0].legend(loc="lower right", fontsize=8)
    ax[0].set_title(f"{titulo}  referencia (promedio de {N_REF} fotogramas, gel horizontal)", fontsize=9)
    ax[1].plot(m["perfil"], np.arange(len(m["perfil"])), color="k", lw=1)
    ax[1].axhspan(m["y0"], m["y1"], color="tab:orange", alpha=0.2)
    ax[1].invert_yaxis()
    ax[1].set_xlabel("brillo medio por fila")
    ax[1].set_title(f"grosor aprox. {m['grosor_px']:.0f} px", fontsize=9)
    fig.tight_layout()
    fig.savefig(salida, dpi=90)
    plt.close(fig)
    return Path(salida)
