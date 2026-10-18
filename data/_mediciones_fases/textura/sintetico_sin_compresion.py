"""(Igual que sintetico.py pero SIN compresión: FFV1 sin pérdida.)
Sintético de desplazamiento CONOCIDO: una imagen real (promedio de los 30
primeros fotogramas) corrida en vertical por desplazamiento subpíxel exacto
(en Fourier), con ruido y compresión mp4. Pulsos de amplitud conocida.
    python sintetico.py <video> <salida_prefijo>
"""
import sys
from pathlib import Path
import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from src import io_utils  # noqa
import textura_medir as tm  # noqa

video, pref = sys.argv[1], sys.argv[2]
FPS, AMPS, PER = 30.0, [0.25, 0.5, 1.0, 2.0, 4.0, -1.0], 5.0
acc = None
for _, f in io_utils.frame_generator(video, end_frame=30):
    acc = f.astype(np.float64) if acc is None else acc + f
img = acc / 30
rot, _, _ = io_utils.elegir_rotacion(img)
img = io_utils.rotar(img, rot)
h, w = img.shape
n = int(FPS * PER * (len(AMPS) + 1))
t = np.arange(n) / FPS
d = np.zeros(n)
forma = lambda s: np.where(s < 0, 0, np.where(s < 0.1, s / 0.1, np.exp(-(s - 0.1) / 0.3)))
for j, A in enumerate(AMPS):
    d += A * forma(t - PER * (j + 1))
F = np.fft.fft(img, axis=0)
ky = np.fft.fftfreq(h)[:, None]
rng = np.random.default_rng(0)
out = f"{pref}_sint.avi"
vw = cv2.VideoWriter(out, cv2.VideoWriter_fourcc(*"FFV1"), FPS, (w, h), False)
for i in range(n):
    g = np.real(np.fft.ifft(F * np.exp(-2j * np.pi * ky * d[i]), axis=0))
    g = g + rng.normal(0, 2.0, g.shape)
    vw.write(np.clip(g, 0, 255).astype(np.uint8))
vw.release()
r = getattr(tm, sys.argv[3] if len(sys.argv) > 3 else "medir")(out, rotacion=0)
dy = r["dy"] - np.median(r["dy"][: int(FPS * 4)])
print(f"{Path(video).name}: franja y {r['y0']}-{r['y1']}, grosor {r['grosor']:.0f} px")
print("  amplitud real -> medida (pico)   cociente")
for j, A in enumerate(AMPS):
    i = int(round(FPS * (PER * (j + 1) + 0.1)))
    m = dy[i - 2:i + 3][np.argmax(np.abs(dy[i - 2:i + 3]))]
    print(f"  {A:+5.2f} -> {m:+7.3f}   {m / A:5.3f}")
quieto = np.abs(d) < 1e-3
print(f"  ruido (MAD fuera de pulsos): {1.4826*np.median(np.abs(dy[quieto]-np.median(dy[quieto]))):.4f} px")
print(f"  error RMS en toda la serie: {np.sqrt(np.mean((dy - d) ** 2)):.4f} px")
np.savetxt(f"{pref}_sint.csv", np.c_[t, d, dy], delimiter=",", header="t,real,medido", comments="")
Path(out).unlink()
