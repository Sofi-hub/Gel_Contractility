#!/usr/bin/env python
"""
medir_roi_ancho.py  -  Fase 3, H19. SOLO MIDE.

Pregunta: ¿es mejor medir en una zona ANCHA (mas gel, pero el grosor varia
hasta ~5 %) o en una zona CHICA y muy plana (la parabola ajusta mejor, pero
menos gel)?

Caso: Video_063.
    ancha_vigente  390-1423 (1033 px, var 4.91 %), 60 columnas  -> control
    chica_plana    875-1039 ( 164 px, var 0.35 %), 164 // 3 = 54 columnas
                   (el bloque gauge_plana que hoy se rechaza por < 180 px)

Se lee el video una vez y se calculan las dos series con el mismo codigo que
main.py (CLAHE, +-15 px, RANSAC), y cada una pasa por contraction_report.

USO (desde la raiz del repo):
    python scripts/medir_roi_ancho.py
Salida: data/fase3_columnas/resumen_ancho_063.md   (~6 min)
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "scripts"))

from src import io_utils, preprocessing, edge_detection  # noqa: E402
import medir_borde_ajuste as mb  # noqa: E402

CFG = mb.CFG
NOMBRE = "Video_063_CTRL1_5V"


def main():
    t0 = time.time()
    video = str(RAIZ / mb.VIDEOS[NOMBRE])
    diag_vig, xs, xe, _ = mb.leer_vigente(NOMBRE)
    pts = io_utils.read_pts_seconds(video)
    max_proj = io_utils.compute_max_projection(video, stride=5)

    roi_auto = preprocessing.auto_detect_roi(max_proj)
    alt = {a["metodo"]: a for a in roi_auto["roi_quality"]["alternativas"]}
    p = alt["gauge_plana"]
    a, b = p["x_start"], p["x_end"]
    confs = [("ancha_vigente", xs, xe, 60),
             ("chica_plana", a, b, min(60, (b - a) // 3))]
    print(f"zonas: {confs}  ({time.time() - t0:.0f} s)", flush=True)

    roi = preprocessing.auto_detect_roi(max_proj, x_start=xs, x_end=xe)
    tg, bg = roi["top_guess"], roi["bottom_guess"]
    xpos = {c[0]: np.linspace(c[1], c[2] - 1, c[3]).astype(int) for c in confs}
    filas = {c[0]: [] for c in confs}
    for idx, frame in io_utils.frame_generator(video):
        img = preprocessing.preprocess_frame(frame, use_clahe=True)
        t = float(pts[idx] - pts[0]) if idx < len(pts) else np.nan
        for et, *_ in confs:
            x, yt, yb, _ = edge_detection.extract_edges_for_frame(
                img, xpos[et], tg, bg, half_window=CFG.half_window,
                method=CFG.edge_method, min_gradient=CFG.min_gradient)
            fila, _, _ = mb._fila(x, yt, yb, "ransac")
            fila["frame"], fila["time_s"] = idx, t
            filas[et].append(fila)
        if idx % 250 == 0:
            print(f"  fotograma {idx}: {time.time() - t0:.0f} s", flush=True)

    tabla, ev = [], {}
    for et, a, b, n in confs:
        d = pd.DataFrame(filas[et])
        r = mb.cr.analizar(d, "center_px", None, None, None, 1.5, frecuencia_estimulo=[0.1])
        c = d["center_px"].to_numpy(float)
        g = d["thickness_px"].to_numpy(float)
        rit = r.get("ritmo") or {}
        tabla.append({
            "zona": et, "roi": f"{a}-{b}", "ancho_px": b - a, "n_col": n,
            "variacion_grosor_pct": (alt["gauge_plana"]["variacion_pct"] if et == "chica_plana" else 4.91),
            "n_eventos": r.get("n_eventos"), "reportable": r.get("conteo_reportable"),
            "mesetas": r.get("mesetas"),
            "amplitud_px": r.get("amplitud_traslacion_px"), "amplitud_rel_pct": r.get("amplitud_relativa_pct"),
            "ruido_canal_px": r.get("ruido_canal_px"), "ruido_grosor_px": r.get("ruido_grosor_px"),
            "ruido_fotog_centro_px": float(np.nanstd(np.diff(c)) / np.sqrt(2)),
            "ruido_fotog_grosor_px": float(np.nanstd(np.diff(g)) / np.sqrt(2)),
            "snr_amplitud/ruido": (r.get("amplitud_traslacion_px") or np.nan) / r.get("ruido_canal_px"),
            "outlier_frac_medio": float(d["outlier_frac"].mean()),
            "residuo_sup_px": float(d["residual_top_px"].median()),
            "residuo_inf_px": float(d["residual_bottom_px"].median()),
            "periodo_s": rit.get("periodo_s"), "periodo_err_s": rit.get("periodo_err_s"),
            "control_max_dif_center_vs_vigente": (float(np.nanmax(np.abs(c - diag_vig["center_px"].to_numpy(float))))
                                                  if et == "ancha_vigente" else None),
        })
        ev[et] = [round(float(x), 2) for x in np.asarray(r.get("tiempos_s", []), float)]
    tabla = pd.DataFrame(tabla)
    print(tabla.T.to_string())
    salida = RAIZ / "data/fase3_columnas"
    salida.mkdir(parents=True, exist_ok=True)
    md = ["# H19: zona ancha vs zona chica y plana (Video_063)\n",
          "```\n" + tabla.T.to_string() + "\n```\n", "Eventos (s):\n```",
          *[f"{k}: {v}" for k, v in ev.items()], "```\n"]
    (salida / "resumen_ancho_063.md").write_text("\n".join(md), encoding="utf-8")
    print(f"\nlisto en {time.time() - t0:.0f} s -> {salida / 'resumen_ancho_063.md'}")


if __name__ == "__main__":
    main()
