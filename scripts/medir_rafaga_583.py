#!/usr/bin/env python
"""
medir_rafaga_583.py  -  Fase 4, punto 5. SOLO MIDE.

Pregunta: la oscilacion de ~10 Hz al final de Video_583 (71.9-73.9 s), ¿es
el gel que se contrae o es TODA la imagen que vibra (camara / platina)?

Se mide el desplazamiento (dx, dy) por correlacion de fase (cv2.phaseCorrelate,
subpixel) contra un fotograma de referencia (t = 70 s), en cuatro zonas:
  gel         la franja del gel dentro de la ROI vigente (718-1187)
  ancla_izq   las primeras 200 columnas a la altura del gel (anclaje izquierdo)
  ancla_der   las ultimas 200 columnas a la altura del gel (anclaje derecho)
  fondo       una franja sin gel arriba (o abajo) del gel, ancho completo
Si las cuatro se mueven igual -> vibracion de toda la imagen.
Si solo se mueve el gel -> el tejido.

USO (desde la raiz del repo):
    python scripts/medir_rafaga_583.py
Salida: data/fase4_rafaga583/rafaga_583.xlsx y resumen_rafaga_583.md  (~1-2 min)
"""
from __future__ import annotations

import sys
from pathlib import Path

import cv2
import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
from src import io_utils, preprocessing  # noqa: E402

VIDEO = RAIZ / "data/raw_videos/OK-20260904T142817Z-1-001/OK/Video_583_EXP6_CTRL4_40V.mp4"
XS, XE = 718, 1187
T_REF, T0, T1 = 70.0, 66.0, 75.5
RAFAGA = (71.85, 73.9)
CALMA = (66.0, 71.0)


def main():
    pts = io_utils.read_pts_seconds(str(VIDEO))
    t = np.asarray(pts) - pts[0]
    max_proj = io_utils.compute_max_projection(str(VIDEO), stride=5)
    roi = preprocessing.auto_detect_roi(max_proj, x_start=XS, x_end=XE)
    H, W = max_proj.shape
    top = int(np.median(roi["top_guess"][XS:XE]))
    bot = int(np.median(roi["bottom_guess"][XS:XE]))
    y0, y1 = max(0, top - 40), min(H, bot + 40)
    alto = y1 - y0
    if top - 60 - alto >= 0:
        f0 = top - 60 - alto
    else:
        f0 = min(H - alto, bot + 60)
    zonas = {
        "gel": (slice(y0, y1), slice(XS, XE)),
        "ancla_izq": (slice(y0, y1), slice(0, 200)),
        "ancla_der": (slice(y0, y1), slice(W - 200, W)),
        "fondo": (slice(f0, f0 + alto), slice(0, W)),
    }
    print({k: (v[0].start, v[0].stop, v[1].start, v[1].stop) for k, v in zonas.items()}, flush=True)

    i_ref = int(np.argmin(np.abs(t - T_REF)))
    refs, filas = None, []
    frames = {}
    for idx, frame in io_utils.frame_generator(str(VIDEO)):
        if idx >= len(t) or t[idx] < T0:
            continue
        if t[idx] > T1:
            break
        frames[idx] = frame.astype(np.float32)
    ref = frames[i_ref]
    win = {k: cv2.createHanningWindow((ref[s].shape[1], ref[s].shape[0]), cv2.CV_32F)
           for k, s in zonas.items()}
    for idx in sorted(frames):
        f = frames[idx]
        fila = {"frame": idx, "time_s": float(t[idx])}
        for k, s in zonas.items():
            (dx, dy), resp = cv2.phaseCorrelate(ref[s], f[s], win[k])
            fila[f"dx_{k}"], fila[f"dy_{k}"], fila[f"resp_{k}"] = dx, dy, resp
        filas.append(fila)
    d = pd.DataFrame(filas)

    res = []
    for nom, (a, b) in (("calma", CALMA), ("rafaga", RAFAGA)):
        s = (d.time_s > a) & (d.time_s < b)
        fila = {"tramo": nom, "t": f"{a}-{b}"}
        for k in zonas:
            for e in ("dx", "dy"):
                v = d.loc[s, f"{e}_{k}"].to_numpy()
                fila[f"{e}_{k}_std_px"] = float(np.std(v))
                fila[f"{e}_{k}_saltos_px"] = float(np.std(np.diff(v)))
            if k != "gel":
                fila[f"corr_dy_gel_{k}"] = float(np.corrcoef(np.diff(d.loc[s, "dy_gel"]),
                                                             np.diff(d.loc[s, f"dy_{k}"]))[0, 1])
        res.append(fila)
    res = pd.DataFrame(res)

    out = RAIZ / "data/fase4_rafaga583"
    out.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(out / "rafaga_583.xlsx") as w:
        res.to_excel(w, sheet_name="resumen", index=False)
        d.to_excel(w, sheet_name="serie", index=False)
    txt = res.round(3).T.to_string()
    (out / "resumen_rafaga_583.md").write_text("# Rafaga final de 583\n\n```\n" + txt + "\n```\n",
                                               encoding="utf-8")
    print(txt)
    print(f"\nlisto -> {out}")


if __name__ == "__main__":
    main()
