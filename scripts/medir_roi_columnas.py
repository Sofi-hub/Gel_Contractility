#!/usr/bin/env python
"""
medir_roi_columnas.py  -  Fase 3, tema 6 (H19). SOLO MIDE.

Objetivo: poder sacar la ROI manual de Video_466. Propuesta en estudio:
separacion minima entre columnas = 3 px (medida: el ruido de borde deja de
ser compartido a los 2-3 px), y la CANTIDAD de columnas se adapta al ancho
de la zona buena: n = min(60, ancho // 3), con un piso a determinar.

Dos mediciones, cada video leido una vez:
  1. PISO DE COLUMNAS (Video_prueba, Video_063): misma ROI vigente con
     60, 50, 40, 30 y 20 columnas. Si el ruido de las columnas es
     independiente, el ruido de la serie crece como sqrt(60/n); se reporta
     el ruido medido contra esa prediccion, y si el conteo cambia.
  2. VIDEO_466 CON ROI AUTOMATICA: la manual vigente (700-900, 60 col,
     control), el rescate actual (944-1169, 60 col) y la cintura
     (bloque gauge_cintura de auto_detect_roi, ~696-846) con 50, 40 y 30
     columnas.

USO (desde la raiz del repo):
    python scripts/medir_roi_columnas.py
Salida: data/fase3_columnas/resumen_columnas.md
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
import medir_borde_ajuste as mb  # noqa: E402  (mismas funciones de ajuste y lectura)

CFG = mb.CFG
SEP = 3


def configuraciones(nombre, max_proj, xs_vig, xe_vig):
    """Lista de (etiqueta, x_start, x_end, n_columnas)."""
    if nombre.startswith("Video_466"):
        roi = preprocessing.auto_detect_roi(max_proj)
        alt = {a["metodo"]: a for a in roi["roi_quality"]["alternativas"]}
        c = alt.get("gauge_cintura")
        if c is None:
            raise SystemExit("466: auto_detect_roi no devolvio bloque gauge_cintura")
        a, b = c["x_start"], c["x_end"]
        n_auto = min(60, (b - a) // SEP)
        out = [("manual_vigente", xs_vig, xe_vig, 60),
               ("rescate_actual", roi["x_start"], roi["x_end"], 60)]
        for n in sorted({n_auto, 40, 30}, reverse=True):
            out.append((f"cintura_n{n}", a, b, n))
        print(f"  cintura auto: {a}-{b} ({b - a} px, var {c['variacion_pct']} %) -> n = {n_auto}")
        return out
    return [(f"vigente_n{n}", xs_vig, xe_vig, n) for n in (60, 50, 40, 30, 20)]


def procesar(nombre):
    t0 = time.time()
    video = str(RAIZ / mb.VIDEOS[nombre])
    diag_vig, xs, xe, _ = mb.leer_vigente(nombre)
    print(f"\n=== {nombre} ===", flush=True)
    pts = io_utils.read_pts_seconds(video)
    max_proj = io_utils.compute_max_projection(video, stride=5)
    confs = configuraciones(nombre, max_proj, xs, xe)
    # posiciones aproximadas del borde: no dependen de la ROI elegida
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
    ref = None
    for et, a, b, n in confs:
        d = pd.DataFrame(filas[et])
        r = mb.cr.analizar(d, "center_px", None, None, None, 1.5, frecuencia_estimulo=[0.1])
        c, g = d["center_px"].to_numpy(float), d["thickness_px"].to_numpy(float)
        rit = r.get("ritmo") or {}
        fila = {"config": et, "roi": f"{a}-{b}", "ancho_px": b - a, "n_col": n,
                "separacion_px": round((b - 1 - a) / (n - 1), 2),
                "n_eventos": r.get("n_eventos"), "reportable": r.get("conteo_reportable"),
                "mesetas": r.get("mesetas"), "amplitud_px": r.get("amplitud_traslacion_px"),
                "amplitud_rel_pct": r.get("amplitud_relativa_pct"),
                "ruido_canal_px": r.get("ruido_canal_px"), "ruido_grosor_px": r.get("ruido_grosor_px"),
                "ruido_fotog_centro_px": float(np.nanstd(np.diff(c)) / np.sqrt(2)),
                "outlier_frac_medio": float(d["outlier_frac"].mean()),
                "residuo_sup_px": float(d["residual_top_px"].median()),
                "residuo_inf_px": float(d["residual_bottom_px"].median()),
                "fotogramas_rechazados": int((d["frame_quality"] == "REJECTED").sum()),
                "periodo_s": rit.get("periodo_s"), "ttp_s": r.get("ttp_s"), "rt50_s": r.get("rt50_s")}
        if ref is None:
            ref = fila
            fila["control_max_dif_center_vs_vigente"] = float(np.nanmax(np.abs(c - diag_vig["center_px"].to_numpy(float))))
        fila["ruido_canal / referencia"] = round(fila["ruido_canal_px"] / ref["ruido_canal_px"], 3)
        fila["prediccion_independiente"] = round(np.sqrt(ref["n_col"] / n), 3)
        ev[et] = [round(x, 2) for x in np.asarray(r.get("tiempos_s", []), float)]
        tabla.append(fila)
    tabla = pd.DataFrame(tabla)
    print(tabla.to_string(index=False), flush=True)
    print(f"  listo en {time.time() - t0:.0f} s", flush=True)
    return tabla, ev


def main():
    salida = RAIZ / "data/fase3_columnas"
    salida.mkdir(parents=True, exist_ok=True)
    md = ["# H19: cantidad de columnas y ROI automatica de 466\n",
          "La primera fila de cada video es la referencia (en Video_prueba y 063, la vigente; en 466, "
          "la manual vigente): `control_max_dif_center_vs_vigente` tiene que dar ~0.\n"]
    for nombre in ("Video_prueba", "Video_063_CTRL1_5V", "Video_466_EXP5_FAPS4_40V"):
        try:
            tabla, ev = procesar(nombre)
        except Exception as e:
            import traceback
            traceback.print_exc()
            md.append(f"## {nombre}\nERROR {e!r}\n")
            continue
        tabla.to_csv(salida / f"{nombre}.csv", index=False)
        md.append(f"## {nombre}\n\n```\n{tabla.T.to_string()}\n```\n\nEventos (s):\n```\n"
                  + "\n".join(f"{k}: {v}" for k, v in ev.items()) + "\n```\n")
        (salida / "resumen_columnas.md").write_text("\n".join(md), encoding="utf-8")
    print(f"\nResumen: {salida / 'resumen_columnas.md'}")


if __name__ == "__main__":
    main()
