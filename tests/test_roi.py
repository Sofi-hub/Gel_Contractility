"""
tests/test_roi.py  -  eleccion de la ROI (H19 y H20, Fase 3).

Geles sinteticos en forma de reloj de arena con la zona plana (cintura) de
ancho conocido. Se verifica:
  1. Zona plana ancha (1000 px): la ROI cae dentro y usa 60 columnas.
  2. Zona plana angosta (150 px): la ROI cubre la zona plana y no un anclaje,
     con min(60, ancho // 3) columnas. (En este sintetico la cintura se
     estima mal -H21- y gana el rescate; antes de H20 elegia el anclaje 0-553.)
  3. Rescate con cintura (H20): con una zona plana de 100 px (debajo del
     minimo de 120) y anclajes planos, el rescate NO puede elegir el anclaje:
     la ventana tiene que contener la cintura.
  4. El piso de columnas: ninguna ROI usa menos de 40 ni mas de 60.

Correr:  python tests/test_roi.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import cv2  # noqa: E402
from src import preprocessing  # noqa: E402


def gel(plana, w=1920, h=1080, cintura=285, anclaje=2.3, xc=960):
    x = np.arange(w, dtype=float)
    d = np.clip(np.abs(x - xc) - plana / 2, 0, None)
    T = cintura + (anclaje - 1) * cintura * np.clip(d / 350.0, 0, 1) ** 2
    img = np.full((h, w), 40, np.uint8)
    for i in range(w):
        a, b = int(round(h / 2 - T[i] / 2)), int(round(h / 2 + T[i] / 2))
        img[max(a, 0):min(b, h), i] = 200
    img = cv2.GaussianBlur(img, (0, 0), 2.0)
    rng = np.random.default_rng(0)
    return np.clip(img + rng.normal(0, 3, img.shape), 0, 255).astype(np.uint8)


fallos = []


def chequear(cond, msg):
    print(("  OK   " if cond else "  FALLA ") + msg)
    if not cond:
        fallos.append(msg)


def dentro(roi, a, b, tol=40):
    return roi["x_start"] >= a - tol and roi["x_end"] <= b + tol


print("1. zona plana ancha (1000 px)")
r = preprocessing.auto_detect_roi(gel(1000))
q = r["roi_quality"]
chequear(dentro(r, 460, 1460), f"ROI {r['x_start']}-{r['x_end']} dentro de 460-1460")
chequear(q["n_columnas_usadas"] == 60, f"60 columnas (dio {q['n_columnas_usadas']})")
chequear(q["roi_contiene_cintura"], "contiene la cintura")

print("2. zona plana angosta (150 px)")
r = preprocessing.auto_detect_roi(gel(150))
q = r["roi_quality"]
ancho = r["x_end"] - r["x_start"]
solapa = min(r["x_end"], 1035) - max(r["x_start"], 885)
chequear(solapa >= 0.8 * 150 and not (r["x_end"] < 700 or r["x_start"] > 1220),
         f"metodo {q['method']}, ROI {r['x_start']}-{r['x_end']} cubre la zona plana 885-1035")
chequear(q["roi_contiene_cintura"], "contiene la cintura")
chequear(q["n_columnas_usadas"] == min(60, ancho // 3),
         f"{q['n_columnas_usadas']} columnas = min(60, {ancho} // 3)")
chequear(q["cumple_criterio_aceptacion"], f"cumple el 6 % (var {q['variacion_en_roi_pct']} %)")

print("3. rescate con cintura (zona plana de 100 px)")
r = preprocessing.auto_detect_roi(gel(100))
q = r["roi_quality"]
chequear(q["roi_contiene_cintura"],
         f"metodo {q['method']}, ROI {r['x_start']}-{r['x_end']} contiene la cintura (910-1010)")
chequear(not (r["x_end"] < 700 or r["x_start"] > 1220), "no eligio un anclaje")

print("4. piso y techo de columnas")
for plana in (100, 150, 300, 1000):
    n = preprocessing.auto_detect_roi(gel(plana))["roi_quality"]["n_columnas_usadas"]
    chequear(40 <= n <= 60, f"plana {plana} px -> {n} columnas")
n = preprocessing.auto_detect_roi(gel(1000), x_start=700, x_end=760)["roi_quality"]["n_columnas_usadas"]
chequear(n == 40, f"ROI manual de 60 px -> piso de 40 columnas (dio {n})")

print()
print("TODO OK" if not fallos else f"FALLAN {len(fallos)}: {fallos}")
sys.exit(1 if fallos else 0)
