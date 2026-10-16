"""Video sintético VERTICAL a partir de una captura de un video de Andrés.
El gel se desplaza de costado (x) con pulsos de forma conocida cada 10 s
(desde 14 s), amplitud AMP px, más ruido y algunos fotogramas desenfocados.
Sirve para comprobar que main.py gira solo, encuentra los bordes y mide bien.

    python sintetico_vertical.py captura.png salida.mp4 [AMP]
"""
import sys
import cv2
import numpy as np

src, out = sys.argv[1], sys.argv[2]
AMP = float(sys.argv[3]) if len(sys.argv) > 3 else 4.0
img = cv2.imread(src, cv2.IMREAD_COLOR).astype(np.float32)
h, w = img.shape[:2]
h -= h % 2; w -= w % 2
img = img[:h, :w]
fps, dur = 30.0, 60.0
rng = np.random.default_rng(1)
vw = cv2.VideoWriter(out, cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))
pulsos = np.arange(14.0, dur - 2, 10.0)
borrosos = set(rng.choice(int(fps * dur), 12, replace=False).tolist())
for k in range(int(fps * dur)):
    t = k / fps
    d = 0.0
    for tp in pulsos:          # subida 0.1 s, bajada exponencial 0.15 s
        if tp <= t < tp + 0.1:
            d += AMP * (t - tp) / 0.1
        elif t >= tp + 0.1:
            d += AMP * np.exp(-(t - tp - 0.1) / 0.15)
    M = np.float32([[1, 0, d], [0, 1, 0]])
    f = cv2.warpAffine(img, M, (w, h), borderMode=cv2.BORDER_REFLECT)
    if k in borrosos:
        f = cv2.GaussianBlur(f, (0, 0), 2.0)
    f = f + rng.normal(0, 3.0, f.shape)
    vw.write(np.clip(f, 0, 255).astype(np.uint8))
vw.release()
print("pulsos (s):", pulsos.tolist(), " amplitud", AMP, "px  desenfocados:", len(borrosos))
