"""D6: dónde caerían los umbrales de tres avisos nuevos (H15, H21, H22), medido en
los 11 videos. Solo mide; no cambia nada.

  H15 timestamps inventados: si el contenedor no trae tiempos reales, los arma
      todos iguales (1/fps) y entonces no se puede detectar ningún fotograma
      perdido. Medida: fracción de intervalos dt idénticos al mediano (±1 µs) y
      su dispersión.
  H21 cintura corta: cuántas columnas seguidas hay cerca de la cintura (grosor
      <= cintura + 5 %, bordes nítidos). Si es menor que el ancho mínimo de ROI
      (120 px), la ROI no puede ser plana y ancha a la vez.
  H22 poco contraste: nitidez del borde (gradiente, el menor de los dos bordes)
      en la ROI, sobre el mapa de máximos, comparada con el mínimo que exige la
      elección de ROI (10).

    python data/_mediciones_fases/d6_avisos/medir_d6.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[2]
sys.path.insert(0, str(RAIZ)); sys.path.insert(0, str(RAIZ / "tests"))
import referencia as ref                       # noqa: E402
from src import io_utils, preprocessing as pp  # noqa: E402


def racha_max(m):
    best = cur = 0
    for v in m:
        cur = cur + 1 if v else 0
        best = max(best, cur)
    return best


filas = []
for carpeta, (video, _, _) in ref.VIDEOS.items():
    pts, mp = io_utils.read_pts_and_max_projection(str(ref.CRUDOS / video), stride=5)
    dt = np.diff(pts)
    med = np.median(dt)
    roi = pp.auto_detect_roi(mp)
    q = roi["roi_quality"]
    T, S, V = roi["thickness_profile"], roi["sharpness_profile"], roi["valid_columns"]
    w = q.get("cintura_px")
    cerca = V & np.isfinite(S) & (S >= 10) & np.isfinite(T) & (T <= w * 1.05)
    xs, xe = roi["x_start"], roi["x_end"]
    s_roi = S[xs:xe]
    filas.append({
        "video": carpeta,
        "dt_identicos_pct": 100 * float(np.mean(np.abs(dt - med) < 1e-6)),
        "dt_cv_pct": 100 * float(np.std(dt) / med),
        "cintura_racha_px": racha_max(cerca),
        "cintura_cols_total": int(cerca.sum()),
        "roi_ancho_px": xe - xs,
        "nitidez_roi_mediana": float(np.nanmedian(s_roi)),
        "nitidez_roi_p10": float(np.nanpercentile(s_roi, 10)),
    })
    print(filas[-1], flush=True)
df = pd.DataFrame(filas)
df.to_csv(AQUI / "tabla_d6.csv", index=False)
print(df.round(2).to_string(index=False))
