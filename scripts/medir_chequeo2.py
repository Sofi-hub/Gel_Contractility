#!/usr/bin/env python
"""
medir_chequeo2.py  -  Fase 4, H24. SOLO MIDE (no toca el flujo).

Pregunta: ¿que criterio de "calidad del ajuste" ordena las ROIs igual que el
ruido del canal (center_px), que es lo que de verdad importa?

Por cada video se lee el video UNA vez y en cada fotograma se ajustan los
bordes en todas las ROIs de la lista (mismo codigo que main.py: CLAHE, +-15 px,
RANSAC grado 2 con umbral adaptativo). Por ROI se guarda, columna por columna,
si se descarto y su residuo. Con eso se calcula:

  outlier_frac        el criterio actual (referencia)
  residuo_px          mediana del MAD de residuos de las columnas aceptadas
  error_modelo_px     cuanto se aparta, EN PROMEDIO EN EL TIEMPO, cada columna
                      de la parabola (RMS sobre columnas). Si la parabola no
                      representa el borde, este numero es grande y estable.
  frac_col_sistem     fraccion de columnas descartadas en > 50 % de los fotogramas
  frac_desc_sistem    de todos los descartes, cuantos caen en esas columnas
  frac_fot_racha3     fotogramas con >= 3 columnas descartadas seguidas
  ruido_canal_px      MAD de center_px sin deriva (mediana movil de 2 s) = la vara

USO (desde la raiz del repo):
    python scripts/medir_chequeo2.py                 # los seis (~6 min c/u)
    python scripts/medir_chequeo2.py 466 063         # solo algunos
Salida: data/fase4_chequeo2/chequeo2_<video>.xlsx  y  resumen_chequeo2.md
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from src import io_utils, preprocessing, edge_detection  # noqa: E402
from src.pipeline import PipelineConfig, _fit  # noqa: E402
from src.estadistica import mad, detrend_median  # noqa: E402

CFG = PipelineConfig()
OK = "data/raw_videos/OK-20260904T142817Z-1-001/OK/"

# video -> (ruta, [(nombre_roi, x_start, x_end, n_columnas), ...])
# La primera de cada lista es la vigente (resultados de la Fase 3).
VIDEOS = {
    "Video_prueba": ("data/raw_videos/Video_prueba.mp4",
                     [("vigente", 454, 1516, 60)]),
    "Video_063_CTRL1_5V": (OK + "Video_063_CTRL1_5V.mp4",
                           [("vigente_chica", 875, 1039, 54),
                            ("vieja_ancha", 390, 1423, 60)]),
    "Video_268_EXP3_FAPS2_40V": (OK + "Video_268_EXP3_FAPS2_40V.mp4",
                                 [("vigente", 918, 1328, 60)]),
    "Video_466_EXP5_FAPS4_40V": (OK + "Video_466_EXP5_FAPS4_40V.mp4",
                                 [("vigente_cintura", 696, 846, 50),
                                  ("vieja_manual", 700, 900, 60),
                                  ("vieja_rescate", 944, 1169, 60),
                                  ("alt_877_1177", 877, 1177, 60),
                                  ("alt_1500_1700", 1500, 1700, 60)]),
    "Video_583_EXP6_CTRL4_40V": (OK + "Video_583_EXP6_CTRL4_40V.mp4",
                                 [("vigente", 718, 1187, 60)]),
    "Video_491_EXP5_CTRL1_36HZ": (OK + "Video_491_EXP5_CTRL1_36HZ.mp4",
                                  [("vigente", 459, 1206, 60)]),
}


def _racha_max(mask: np.ndarray) -> int:
    best = cur = 0
    for v in mask:
        cur = cur + 1 if v else 0
        best = max(best, cur)
    return best


def medir_video(nombre: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    t0 = time.time()
    ruta, rois = VIDEOS[nombre]
    video = str(RAIZ / ruta)
    pts = io_utils.read_pts_seconds(video)
    max_proj = io_utils.compute_max_projection(video, stride=5)
    # top_guess / bottom_guess son por columna de la imagen: sirven para todas las ROIs
    roi0 = preprocessing.auto_detect_roi(max_proj, x_start=rois[0][1], x_end=rois[0][2])
    tg, bg = roi0["top_guess"], roi0["bottom_guess"]

    xpos = {r[0]: np.linspace(r[1], r[2] - 1, r[3]).astype(int) for r in rois}
    acc = {r[0]: {"out_t": [], "out_b": [], "res_t": [], "res_b": [],
                  "rcol_t": [], "rcol_b": [], "center": [], "grosor": [], "of": []}
           for r in rois}

    for idx, frame in io_utils.frame_generator(video):
        img = preprocessing.preprocess_frame(frame, use_clahe=CFG.use_clahe,
                                             use_denoise=CFG.use_denoise)
        for nom, *_ in rois:
            x, yt, yb, _ = edge_detection.extract_edges_for_frame(
                img, xpos[nom], tg, bg, half_window=CFG.half_window,
                method=CFG.edge_method, min_gradient=CFG.min_gradient)
            ft, fb = _fit(x, yt, CFG), _fit(x, yb, CFG)
            a = acc[nom]
            if ft is None or fb is None:
                n = len(x)
                for k in ("out_t", "out_b"):
                    a[k].append(np.ones(n, bool))
                for k in ("rcol_t", "rcol_b"):
                    a[k].append(np.full(n, np.nan))
                for k in ("res_t", "res_b", "center", "grosor"):
                    a[k].append(np.nan)
                a["of"].append(1.0)
                continue
            a["out_t"].append(~ft.inlier_mask)
            a["out_b"].append(~fb.inlier_mask)
            a["rcol_t"].append(yt - ft.y_fitted)
            a["rcol_b"].append(yb - fb.y_fitted)
            a["res_t"].append(ft.residual_px)
            a["res_b"].append(fb.residual_px)
            ytp, ybp = np.median(ft.y_fitted), np.median(fb.y_fitted)
            a["center"].append(0.5 * (ytp + ybp))
            a["grosor"].append(np.median(fb.y_fitted - ft.y_fitted))
            a["of"].append(((~ft.inlier_mask).sum() + (~fb.inlier_mask).sum()) / (2 * len(x)))
        if idx % 250 == 0:
            print(f"  {nombre} fotograma {idx}: {time.time() - t0:.0f} s", flush=True)

    t = np.asarray(pts) - pts[0]
    fps = 1.0 / np.median(np.diff(t))
    resumen, columnas = [], []
    for nom, xs, xe, n in rois:
        a = acc[nom]
        fila = {"video": nombre, "roi": nom, "x": f"{xs}-{xe}", "n_col": n,
                "outlier_frac_pct": 100 * np.nanmean(a["of"])}
        center = np.asarray(a["center"], float)
        fila["ruido_canal_px"] = mad(detrend_median(center, fps, 2.0))  # señal - mediana movil
        fila["grosor_px"] = float(np.nanmedian(a["grosor"]))
        for b in ("t", "b"):
            lado = "sup" if b == "t" else "inf"
            out = np.vstack(a[f"out_{b}"])              # fotogramas x columnas
            rcol = np.vstack(a[f"rcol_{b}"])
            frac_col = out.mean(axis=0)
            sistem = frac_col > 0.5
            perfil = np.nanmedian(rcol, axis=0)         # sesgo de cada columna en el tiempo
            fila[f"residuo_{lado}_px"] = float(np.nanmedian(a[f"res_{b}"]))
            fila[f"error_modelo_{lado}_px"] = float(np.sqrt(np.nanmean(perfil ** 2)))
            fila[f"frac_col_sistem_{lado}_pct"] = 100 * sistem.mean()
            fila[f"frac_desc_sistem_{lado}_pct"] = (100 * out[:, sistem].sum() / max(out.sum(), 1))
            fila[f"frac_fot_racha3_{lado}_pct"] = 100 * np.mean([_racha_max(f) >= 3 for f in out])
            for i in range(n):
                columnas.append({"video": nombre, "roi": nom, "borde": lado, "col": i,
                                 "x": int(np.linspace(xs, xe - 1, n).astype(int)[i]),
                                 "frac_descartada": frac_col[i], "sesgo_mediano_px": perfil[i],
                                 "nan_frac": float(np.isnan(rcol[:, i]).mean())})
        g = fila["grosor_px"]
        fila["error_modelo_peor_rel_pct"] = 100 * max(fila["error_modelo_sup_px"],
                                                      fila["error_modelo_inf_px"]) / g
        fila["residuo_peor_rel_pct"] = 100 * max(fila["residuo_sup_px"], fila["residuo_inf_px"]) / g
        resumen.append(fila)
        print(f"  {nombre} / {nom}: listo", flush=True)
    print(f"{nombre}: {time.time() - t0:.0f} s", flush=True)
    return pd.DataFrame(resumen), pd.DataFrame(columnas)


def main():
    pedidos = sys.argv[1:]
    nombres = [v for v in VIDEOS if not pedidos or any(p in v for p in pedidos)]
    salida = RAIZ / "data/fase4_chequeo2"
    salida.mkdir(parents=True, exist_ok=True)
    todos = []
    for nom in nombres:
        res, col = medir_video(nom)
        with pd.ExcelWriter(salida / f"chequeo2_{nom}.xlsx") as w:
            res.to_excel(w, sheet_name="resumen", index=False)
            col.to_excel(w, sheet_name="columnas", index=False)
        todos.append(res)
    tabla = pd.concat(todos, ignore_index=True)
    md = ["# H24: criterios de calidad de ajuste por ROI\n",
          "```\n" + tabla.round(3).T.to_string() + "\n```\n"]
    (salida / "resumen_chequeo2.md").write_text("\n".join(md), encoding="utf-8")
    print(tabla.round(3).T.to_string())
    print(f"\nlisto -> {salida}")


if __name__ == "__main__":
    main()
