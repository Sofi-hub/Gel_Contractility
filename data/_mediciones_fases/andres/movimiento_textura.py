"""¿Se mueve el gel en los videos de Andrés? Sin bordes: desplazamiento de cada
fotograma contra uno de referencia por correlación de fase (subpíxel), sobre la
franja del gel (textura). Después: señal plegada a 10 s contra 6 períodos de
control (como en b7). Solo mide.
    python movimiento_textura.py video.mp4 salida_prefijo
"""
import sys
from pathlib import Path
import cv2
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from src.forzado_util import plegar_snr  # noqa: E402

v, pref = sys.argv[1], sys.argv[2]
def leer(v):
    cap = cv2.VideoCapture(v)
    while True:
        ok, f = cap.read()
        if not ok:
            break
        yield (cv2.cvtColor(f, cv2.COLOR_BGR2GRAY) if f.ndim == 3 else f).astype(np.float32)
    cap.release()


fps = cv2.VideoCapture(v).get(cv2.CAP_PROP_FPS) or 30
# referencia y franja con los primeros 30 fotogramas (de a uno: no carga el video entero)
acc, n = None, 0
for g in leer(v):
    acc = g if acc is None else acc + g
    n += 1
    if n == 30:
        break
ref_full = acc / n
h, w = ref_full.shape
perfil = ref_full.mean(axis=0)
cols = np.where(perfil > perfil.min() + 0.5 * (perfil.max() - perfil.min()))[0]
x0, x1 = cols.min(), cols.max()
pad = 60
x0, x1 = max(0, x0 - pad), min(w, x1 + pad)       # incluye los dos bordes y la banda
ref = ref_full[:, x0:x1]
win = cv2.createHanningWindow((x1 - x0, h), cv2.CV_32F)
dx, dy, resp = [], [], []
for g in leer(v):
    (sx, sy), r = cv2.phaseCorrelate(ref, g[:, x0:x1], win)
    dx.append(sx); dy.append(sy); resp.append(r)
F = dx
dx, dy = np.array(dx), np.array(dy)
t = np.arange(len(dx)) / fps
# sin deriva: mediana movil de 2 s
from scipy.ndimage import median_filter
def sd(s): return s - median_filter(s, size=int(2 * fps) | 1, mode="nearest")
rx, ry = sd(dx), sd(dy)
ruido = lambda s: 1.4826 * np.median(np.abs(s - np.median(s)))
print(f"{Path(v).name}: {len(dx)} fotogramas {w}x{h}, franja x {x0}-{x1}")
for nom, s in (("x (perpendicular al gel)", rx), ("y (a lo largo)", ry)):
    snr, ctrl = plegar_snr(t, s, 10.0)
    print(f"  {nom}: ruido {ruido(s):.4f} px, max |s| {np.max(np.abs(s)):.3f} px, "
          f"plegado a 10 s SNR {snr:.1f} (controles {min(ctrl):.1f}-{max(ctrl):.1f})")
fig, ax = plt.subplots(2, 1, figsize=(11, 5))
ax[0].plot(t, rx, lw=0.6); ax[0].set_ylabel("dx sin deriva (px)"); ax[0].set_title(Path(v).name + " — movimiento por textura (sin bordes)")
ax[1].plot(t, ry, lw=0.6, color="gray"); ax[1].set_ylabel("dy (px)"); ax[1].set_xlabel("tiempo (s)")
for a in ax: a.grid(alpha=.3)
fig.tight_layout(); fig.savefig(pref + "_movimiento.png", dpi=90)
np.savetxt(pref + "_movimiento.csv", np.c_[t, dx, dy], delimiter=",", header="t_s,dx_px,dy_px", comments="")
