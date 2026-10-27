"""Compara el movimiento de los bordes del evento de 7.28 s (fotograma 209) con
contracciones reales de Video_prueba. Solo LEE: no toca el analisis.

Para cada evento, de 3 fotogramas antes a 4 despues del pico: y_top_px,
y_bottom_px, largo (bottom - top) y centro (promedio), relativos al fotograma
-3; y el corrimiento vertical de una zona FIJA fuera del gel (franja por encima
del borde superior, con la misma ROI de columnas), medido por correlacion de
fase contra el fotograma -3.

Salida en comparacion_7_28/: tabla.csv y salida.txt.

    python data/_mediciones_fases/huecos_grabacion/comparacion_7_28.py
"""
import sys
from pathlib import Path

import cv2
import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(RAIZ / "tests"))
from referencia import PROCESADOS          # noqa: E402
from fotogramas_7_28 import video_de       # noqa: E402

AQUI = Path(__file__).resolve().parent
SALIDA = AQUI / "comparacion_7_28"
# pico -> rotulo. En Video_prueba ningun estimulado dura 2-3 fotogramas (todos
# 6): se usan los tres estimulados mas cercanos y las dos espontaneas vecinas.
EVENTOS = {209: "7.28 s (dudoso)", 198: "espont. 6.57 s", 222: "espont. 7.67 s",
           440: "estim. 14.94 s", 740: "estim. 24.94 s", 1040: "estim. 34.94 s"}
ANTES, DESPUES = 3, 4
MARGEN = 15     # px entre la zona fija y el borde superior mas alto
ALTO_FIJA = 60  # alto de la zona fija


def main():
    xl = PROCESADOS / "Video_prueba" / "serie_temporal_Video_prueba.xlsx"
    s = pd.read_excel(xl, sheet_name="diagnostics").set_index("frame")
    roi = pd.read_excel(xl, sheet_name="roi_alternativas")
    roi = roi[roi["elegida"].astype(bool)].iloc[0]
    x0, x1 = int(roi["x_start"]), int(roi["x_end"])
    y1 = int(np.floor(s["y_top_px"].min())) - MARGEN
    y0 = max(y1 - ALTO_FIJA, 0)

    quiero = {p + d for p in EVENTOS for d in range(-ANTES, DESPUES + 1)}
    cap = cv2.VideoCapture(str(video_de()))
    zonas, i = {}, 0
    while i <= max(quiero):
        ok, f = cap.read()
        if not ok:
            break
        if i in quiero:
            g = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY).astype(np.float64)
            zonas[i] = g[y0:y1, x0:x1]
        i += 1
    cap.release()
    ventana = cv2.createHanningWindow(zonas[min(zonas)].shape[::-1], cv2.CV_64F)

    filas = []
    for p, nombre in EVENTOS.items():
        ref = p - ANTES
        b = s.loc[ref]
        for d in range(-ANTES, DESPUES + 1):
            n = p + d
            r = s.loc[n]
            (_, dy), _ = cv2.phaseCorrelate(zonas[ref], zonas[n], ventana)
            filas.append(dict(
                evento=nombre, pico=p, rel=d, frame=n, time_s=round(r["time_s"], 3),
                d_top=r["y_top_px"] - b["y_top_px"], d_bottom=r["y_bottom_px"] - b["y_bottom_px"],
                d_largo=(r["y_bottom_px"] - r["y_top_px"]) - (b["y_bottom_px"] - b["y_top_px"]),
                d_centro=r["center_px"] - b["center_px"], d_fija=dy))
    t = pd.DataFrame(filas)
    SALIDA.mkdir(exist_ok=True)
    t.round(3).to_csv(SALIDA / "tabla.csv", index=False)

    lineas = [f"ROI x={x0}-{x1}; zona fija y={y0}-{y1} (por encima del gel)",
              "Valores relativos al fotograma -3 del pico, en px (+ = hacia abajo).", ""]
    for nombre, g in t.groupby("evento", sort=False):
        lineas.append(f"== {nombre} (pico fot. {g['pico'].iloc[0]})")
        lineas.append(g.drop(columns=["evento", "pico"]).round(2).to_string(index=False))
        pk = g[g["rel"] == 0].iloc[0]
        lineas.append(f"   en el pico: largo/centro = {pk['d_largo'] / pk['d_centro']:+.2f}, "
                      f"zona fija {pk['d_fija']:+.2f} px")
        lineas.append("")
    texto = "\n".join(lineas)
    (SALIDA / "salida.txt").write_text(texto, encoding="utf-8")
    print(texto)


if __name__ == "__main__":
    main()
