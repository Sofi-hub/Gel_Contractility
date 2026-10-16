"""Orientación del gel (2026-10-15, videos de Andrés: gel vertical).
Mide, sobre el mapa de máximos, si los bordes del gel son horizontales o
verticales. Medida: perfil promedio a lo largo de cada eje; un gel horizontal da
un perfil con escalones fuertes en y (promediando en x) y casi plano en x.
  cociente = variación del perfil en y / variación del perfil en x
  > 1: gel horizontal (como siempre); < 1: vertical.
Se prueba en los 11 videos (deben dar > 1), en los mismos girados 90° (< 1) y
en la captura de un video de Andrés (vertical).

    python data/_mediciones_fases/orientacion/medir.py [captura.png]
"""
from __future__ import annotations
import sys
from pathlib import Path
import cv2
import numpy as np
RAIZ = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(RAIZ)); sys.path.insert(0, str(RAIZ / "tests"))
from src import io_utils  # noqa: E402
from referencia import VIDEOS, CRUDOS  # noqa: E402


def cociente(img):
    g = img.astype(float)
    py = g.mean(axis=1)            # perfil a lo largo de y (promedio de cada fila)
    px = g.mean(axis=0)            # perfil a lo largo de x
    vy = np.percentile(py, 95) - np.percentile(py, 5)
    vx = np.percentile(px, 95) - np.percentile(px, 5)
    return vy / max(vx, 1e-9)


filas = []
for carpeta, (video, _, _) in VIDEOS.items():
    p = CRUDOS / video
    if not p.is_file():
        continue
    _, mp = io_utils.read_pts_and_max_projection(p, stride=5)
    c = cociente(mp); cr = cociente(cv2.rotate(mp, cv2.ROTATE_90_CLOCKWISE))
    filas.append((carpeta, c, cr)); print(f"{carpeta:28s} normal {c:7.2f}   girado {cr:6.3f}", flush=True)
for a in sys.argv[1:]:
    img = cv2.imread(a, cv2.IMREAD_GRAYSCALE)
    print(f"{Path(a).name:28s} tal cual {cociente(img):7.3f}   girado {cociente(cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)):6.2f}")
