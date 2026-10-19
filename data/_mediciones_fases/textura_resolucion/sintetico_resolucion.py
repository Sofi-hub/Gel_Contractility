"""¿Achicar x0.5 cambia la amplitud medida por textura? (2026-10-19)

Sintético de corrimiento CONOCIDO, con el gel grande (como los 4K de Andrés), medido
a resolución completa y achicado x0.5 (escala forzada). Se prueban tres tamaños de
grano de la textura (el real no se conoce) y corrimientos de 0.5 a 2 px (en px del
original). Resultado: medido/real en cada caso. Solo medición; no toca el análisis.

    python data/_mediciones_fases/textura_resolucion/sintetico_resolucion.py
"""
import sys, tempfile
from pathlib import Path
import cv2
import numpy as np

RAIZ = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(RAIZ))
from src import textura  # noqa: E402

FPS, PER = 30.0, 3.0
AMPS = [0.5, 1.0, 2.0]          # px del original
H, W = 1600, 800                # gel horizontal; franja de ~1000 px


def imagen(grano, seed=1):
    rng = np.random.default_rng(seed)
    tex = cv2.GaussianBlur(rng.normal(0, 1, (H, W)).astype(np.float32), (0, 0), grano)
    tex /= tex.std()
    y = np.arange(H)[:, None]
    banda = 1 / (1 + np.exp(-(y - 300) / 40.0)) - 1 / (1 + np.exp(-(y - 1300) / 40.0))
    return 40 + 110 * banda + 25 * tex * (0.4 + banda)


def video(ruta, grano, ruido):
    img = imagen(grano)
    n = int(FPS * PER * (len(AMPS) + 1))
    t = np.arange(n) / FPS
    forma = lambda s: np.where(s < 0, 0, np.where(s < 0.1, s / 0.1, np.exp(-(s - 0.1) / 0.3)))
    d = sum(A * forma(t - PER * (j + 1)) for j, A in enumerate(AMPS))
    F = np.fft.fft(img, axis=0)
    ky = np.fft.fftfreq(H)[:, None]
    rng = np.random.default_rng(0)
    vw = cv2.VideoWriter(str(ruta), cv2.VideoWriter_fourcc(*"mp4v"), FPS, (W, H), False)
    for i in range(n):
        g = np.real(np.fft.ifft(F * np.exp(-2j * np.pi * ky * d[i]), axis=0)) + rng.normal(0, ruido, (H, W))
        vw.write(np.clip(g, 0, 255).astype(np.uint8))
    vw.release()
    return d


def cocientes(dy, d):
    dy = dy - np.median(dy[: int(FPS * 2)])
    t = np.arange(len(d)) / FPS
    out = []
    for j, A in enumerate(AMPS):
        t0 = PER * (j + 1)
        sel = (t >= t0) & (t < t0 + 1.5) & (np.abs(d) > 0.2 * A)
        out.append(float(np.sum(dy[sel] * d[sel]) / np.sum(d[sel] ** 2)))
    return out


def main():
    orig = textura.escala_de
    print(f"{'grano px':>8} {'ruido':>5} {'amp px':>6} {'completo':>9} {'x0.5':>7} {'x0.5/completo':>14}")
    with tempfile.TemporaryDirectory() as tmp:
        for grano in (1.5, 3.0, 6.0):
            for ruido in (2.0, 6.0):
                v = Path(tmp) / f"s_{grano}_{ruido}.mp4"
                d = video(v, grano, ruido)
                textura.escala_de = lambda p: 0.5
                ca = cocientes(textura.medir(v, rotacion=0)["dy"], d)
                textura.escala_de = orig
                cb = cocientes(textura.medir(v, rotacion=0, resolucion_completa=True)["dy"], d)
                for A, a, b in zip(AMPS, ca, cb):
                    print(f"{grano:8.1f} {ruido:5.1f} {A:6.1f} {b:9.3f} {a:7.3f} {a / b:14.3f}", flush=True)


if __name__ == "__main__":
    main()
