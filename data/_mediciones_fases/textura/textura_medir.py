"""Medición por desplazamiento de TEXTURA (sin bordes), versión de medición.

Para cada fotograma (gel ya horizontal): correlación de fase subpíxel contra
una imagen de referencia (promedio de los 30 primeros fotogramas), sobre la
franja del gel. Se usa solo el corrimiento vertical (perpendicular al gel),
que es lo mismo que mide `center_px`.

Franja, sin bordes: perfil de brillo por filas de la imagen de referencia
(promedio sobre las columnas elegidas); la franja es el tramo seguido más
largo por encima de la mitad entre el percentil 5 y el 95. Margen afuera:
15 % del grosor (incluye los dos bordes y la rampa). Grosor en reposo =
ancho de la franja a media altura (aproximado).

Columnas: 'centro' = la mitad central de la imagen (autónomo), o un rango dado.
"""
from __future__ import annotations
import sys
from pathlib import Path
import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from src import io_utils  # noqa: E402

N_REF = 30
MARGEN = 0.15


def franja(ref: np.ndarray, x0: int, x1: int):
    p = ref[:, x0:x1].mean(axis=1)
    p = cv2.GaussianBlur(p.reshape(-1, 1), (1, 0), sigmaX=0, sigmaY=max(2, len(p) / 200)).ravel()
    lo, hi = np.percentile(p, 5), np.percentile(p, 95)
    on = p > lo + 0.5 * (hi - lo)
    # tramo seguido más largo
    best, cur, s = (0, 0), None, 0
    for i, v in enumerate(np.r_[on, False]):
        if v and cur is None:
            cur = i
        elif not v and cur is not None:
            if i - cur > best[1] - best[0]:
                best = (cur, i)
            cur = None
    a, b = best
    g = b - a
    m = int(round(MARGEN * g))
    return max(0, a - m), min(len(p), b + m), float(g)


def medir(video, rotacion=None, cols="centro", n_max=None):
    """Devuelve dict con dy (px, por fotograma), dx, respuesta, franja y grosor."""
    gen = io_utils.frame_generator(video, end_frame=N_REF)
    acc = None
    for _, f in gen:
        acc = f.astype(np.float64) if acc is None else acc + f
    ref0 = acc / N_REF
    if rotacion is None:   # misma regla que main.py (sobre el promedio en vez del máximo)
        rotacion, _, _ = io_utils.elegir_rotacion(ref0)
    ref = io_utils.rotar(ref0, rotacion).astype(np.float32)
    h, w = ref.shape
    if cols == "centro":
        x0, x1 = w // 4, w - w // 4
    else:
        x0, x1 = cols
    y0, y1, grosor = franja(ref, x0, x1)
    R = ref[y0:y1, x0:x1]
    win = cv2.createHanningWindow((x1 - x0, y1 - y0), cv2.CV_32F)
    dx, dy, rs = [], [], []
    for i, f in io_utils.frame_generator(video, end_frame=n_max, rotacion=rotacion):
        (sx, sy), r = cv2.phaseCorrelate(R, f[y0:y1, x0:x1].astype(np.float32), win)
        dx.append(sx); dy.append(sy); rs.append(r)
    return dict(dy=np.array(dy), dx=np.array(dx), resp=np.array(rs), y0=y0, y1=y1,
                x0=x0, x1=x1, grosor=grosor, rot=rotacion, centro_ref=(y0 + y1) / 2)


def _lk(R, G, Gy2, F):
    """Corrimiento vertical residual (px) por mínimos cuadrados de gradiente (Lucas-Kanade 1-D)."""
    return float(np.sum(G * (R - F)) / Gy2)


def medir_lk(video, rotacion=None, cols="centro", n_max=None, sigma=1.5):
    """Igual que medir(), pero: corrimiento entero por correlación de fase y la
    fracción por gradiente (sin sesgo hacia el entero). Imágenes suavizadas (sigma)."""
    acc = None
    for _, f in io_utils.frame_generator(video, end_frame=N_REF):
        acc = f.astype(np.float64) if acc is None else acc + f
    ref0 = acc / N_REF
    if rotacion is None:
        rotacion, _, _ = io_utils.elegir_rotacion(ref0)
    ref = cv2.GaussianBlur(io_utils.rotar(ref0, rotacion).astype(np.float32), (0, 0), sigma)
    h, w = ref.shape
    x0, x1 = (w // 4, w - w // 4) if cols == "centro" else cols
    y0, y1, grosor = franja(ref, x0, x1)
    M = 40                               # filas extra para poder correr la ventana
    a, b = y0 + M, y1 - M                 # zona comparada (dentro de lo que se lee)
    if b - a < 20:
        a, b = y0, y1
    R = ref[a:b, x0:x1]
    win = cv2.createHanningWindow((x1 - x0, y1 - y0), cv2.CV_32F)
    Rpc = ref[y0:y1, x0:x1]
    Gyfull = np.gradient(ref, axis=0)
    dy, rs = [], []
    for i, f in io_utils.frame_generator(video, end_frame=n_max, rotacion=rotacion):
        f = cv2.GaussianBlur(f.astype(np.float32), (0, 0), sigma)
        (_, sy), r = cv2.phaseCorrelate(Rpc, f[y0:y1, x0:x1], win)
        k = int(round(sy))
        k = max(-(a), min(h - b, k))
        F = f[a + k:b + k, x0:x1]
        G = Gyfull[a:b, x0:x1]
        # F(y) ~ R(y - d) ~ R - d*G  ->  d = sum(G*(R-F))/sum(G^2)
        d = k + _lk(R, G, float(np.sum(G * G)), F)
        # una iteración más: correr la referencia en d-k con Fourier no hace falta si |d-k|<0.6
        dy.append(d); rs.append(r)
    return dict(dy=np.array(dy), resp=np.array(rs), y0=y0, y1=y1, x0=x0, x1=x1,
                grosor=grosor, rot=rotacion, centro_ref=(y0 + y1) / 2)


def medir_final(video, rotacion=None, cols="centro", n_max=None):
    """El método implementado (src/textura.py: LK iterado). Solo columnas 'centro'."""
    from src import textura
    if rotacion is None:
        _, mp = io_utils.read_pts_and_max_projection(video, stride=5)
        rotacion, _, _ = io_utils.elegir_rotacion(mp)
    m = textura.medir(video, rotacion, n_max=n_max)
    return dict(dy=m["dy"], resp=m["respuesta"], y0=m["y0"], y1=m["y1"], x0=m["x0"], x1=m["x1"],
                grosor=m["grosor_px"], rot=rotacion, centro_ref=m["centro_ref"])
