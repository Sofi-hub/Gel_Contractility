#!/usr/bin/env python
"""
medir_borde_ajuste.py  -  Fase 3, tema 6 (H19, H20, H26, H27, H29). SOLO MIDE.

No cambia ningun modulo de src/ ni ningun resultado de data/processed_data/.
Escribe todo en  data/fase3_borde/<video>/  y un resumen en
data/fase3_borde/resumen_medicion.md.

QUE HACE, POR VIDEO
-------------------
Lee el video UNA vez. En cada fotograma calcula, en paralelo, cinco versiones
de las cuatro series (misma ROI y mismas posiciones aproximadas del borde que
el resultado vigente):

    vigente      CLAHE + ventana +-15 px + RANSAC   (= lo que hace main.py)
    clahe_mco    CLAHE + +-15 + minimos cuadrados (no descarta columnas)
    crudo        sin CLAHE + +-15 + RANSAC
    crudo_mco    sin CLAHE + +-15 + minimos cuadrados
    ventana25    CLAHE + ventana +-25 px + RANSAC

y despues pasa cada version por contraction_report.analizar (mismos
argumentos que el flujo normal: k auto, ventana auto, --frecuencia-estimulo
0.1).

Pruebas:
  A (H26)  conteo, k, amplitud, ruido, periodo: vigente vs crudo
  B (H26)  la diferencia CLAHE - crudo, ¿sube en las contracciones?
  C (H29)  vigente vs clahe_mco; en que columnas descarta RANSAC y cuanto se
           aparta el borde de la parabola en cada columna
  D (H27)  vigente vs ventana25; cuantos bordes quedan NaN por pico pegado
  E (H19)  cuanto ruido comparten dos columnas segun su distancia (columnas
           densas, 1 de cada --paso-denso fotogramas)
  F (H20)  rescate de la ROI con y sin "tiene que contener la cintura",
           sobre la imagen de maximos del video y sobre un gel sintetico

CONTROL DE QUE LA MEDICION ES VALIDA
------------------------------------
La version "vigente" tiene que reproducir el serie_temporal.xlsx vigente.
El resumen informa la diferencia maxima de center_px y thickness_px contra el
archivo. Si no da ~0, las demas comparaciones no valen.

USO (desde la raiz del repo)
----------------------------
Prueba rapida (unos 300 fotogramas de Video_prueba, para ver cuanto tarda):
    python scripts/medir_borde_ajuste.py --videos Video_prueba --max-frames 300
Todo:
    python scripts/medir_borde_ajuste.py
Solo algunos:
    python scripts/medir_borde_ajuste.py --videos Video_063_CTRL1_5V Video_466_EXP5_FAPS4_40V
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "scripts"))

from src import io_utils, preprocessing, edge_detection, robust_fitting  # noqa: E402
from src.pipeline import PipelineConfig  # noqa: E402
from src.estadistica import mad, detrend_median  # noqa: E402
import contraction_report as cr  # noqa: E402

OK = "data/raw_videos/OK-20260904T142817Z-1-001/OK"
VIDEOS = {
    "Video_prueba": "data/raw_videos/Video_prueba.mp4",
    "Video_063_CTRL1_5V": f"{OK}/Video_063_CTRL1_5V.mp4",
    "Video_268_EXP3_FAPS2_40V": f"{OK}/Video_268_EXP3_FAPS2_40V.mp4",
    "Video_466_EXP5_FAPS4_40V": f"{OK}/Video_466_EXP5_FAPS4_40V.mp4",
    "Video_583_EXP6_CTRL4_40V": f"{OK}/Video_583_EXP6_CTRL4_40V.mp4",
    "Video_491_EXP5_CTRL1_36HZ": f"{OK}/Video_491_EXP5_CTRL1_36HZ.mp4",
}

# (nombre, preproceso, half_window, ajuste)
VARIANTES = [
    ("vigente", "clahe", 15, "ransac"),
    ("clahe_mco", "clahe", 15, "mco"),
    ("crudo", "crudo", 15, "ransac"),
    ("crudo_mco", "crudo", 15, "mco"),
    ("ventana25", "clahe", 25, "ransac"),
]

CFG = PipelineConfig()


# ---------------------------------------------------------------------------
# Ajustes
# ---------------------------------------------------------------------------
def _mco(x, y, degree=2, min_valid=10):
    """Minimos cuadrados de grado 2 sobre TODAS las columnas validas (no
    descarta nada). Misma normalizacion de x que fit_edge_ransac."""
    valid = ~np.isnan(y)
    if valid.sum() < min_valid:
        return None
    xv, yv = x[valid].astype(float), y[valid].astype(float)
    x0 = xv.mean()
    scale = max((xv.max() - xv.min()) / 2.0, 1.0)
    coef = np.polyfit((xv - x0) / scale, yv, degree)
    y_all = np.polyval(coef, (x.astype(float) - x0) / scale)
    return y_all, valid.copy(), float(mad(yv - np.polyval(coef, (xv - x0) / scale)))


def _ransac(x, y):
    f = robust_fitting.fit_edge_ransac(
        x, y, degree=CFG.ransac_degree,
        residual_threshold=CFG.ransac_residual_threshold,
        residual_k=CFG.ransac_residual_k, residual_floor=CFG.ransac_residual_floor)
    if f is None:
        return None
    return f.y_fitted, f.inlier_mask, float(f.residual_px)


def _fila(x, yt, yb, metodo):
    """Replica pipeline.process_frame a partir de bordes ya extraidos."""
    fn = _ransac if metodo == "ransac" else _mco
    a, b = fn(x, yt), fn(x, yb)
    n_slots = 2 * len(x)
    if a is None or b is None:
        return dict(thickness_px=np.nan, y_top_px=np.nan, y_bottom_px=np.nan,
                    center_px=np.nan, outlier_frac=1.0, residual_top_px=np.nan,
                    residual_bottom_px=np.nan, frame_quality="REJECTED"), None, None
    th = float(np.median(b[0] - a[0]))
    yt_px, yb_px = float(np.median(a[0])), float(np.median(b[0]))
    n_out = int((~a[1]).sum() + (~b[1]).sum())
    frac = n_out / n_slots
    fila = dict(
        thickness_px=th, y_top_px=round(yt_px, 4), y_bottom_px=round(yb_px, 4),
        center_px=round(0.5 * (yt_px + yb_px), 4), outlier_frac=round(frac, 4),
        residual_top_px=round(a[2], 4), residual_bottom_px=round(b[2], 4),
        frame_quality="OK" if frac < CFG.low_quality_frac else "LOW_QUALITY")
    return fila, a[1], b[1]


# ---------------------------------------------------------------------------
# Lectura del vigente
# ---------------------------------------------------------------------------
def leer_vigente(nombre):
    p = RAIZ / "data/processed_data" / nombre / "serie_temporal.xlsx"
    diag = pd.read_excel(p, sheet_name="diagnostics")
    res = pd.read_excel(p, sheet_name="resumen")
    kv = dict(zip(res.iloc[:, 0].astype(str), res.iloc[:, 1]))
    return diag, int(kv["ROI x_start"]), int(kv["ROI x_end"]), kv


# ---------------------------------------------------------------------------
# Prueba F: rescate con condicion de cintura
# ---------------------------------------------------------------------------
def _ventana_plana(T, ok, max_var, min_w, cerca=None):
    """Copia de preprocessing._widest_flat_window. Si `cerca` se da, ademas
    exige que la ventana contenga al menos una columna cerca de la cintura.
    (Si la ventana mas ancha que termina en `hi` no la contiene, ninguna
    mas angosta que termine en `hi` la contiene: alcanza con chequear esa.)"""
    n, best, lo = len(T), None, 0
    for hi in range(n):
        if not ok[hi] or not np.isfinite(T[hi]):
            lo = hi + 1
            continue
        while lo <= hi:
            seg = T[lo:hi + 1]
            mn = float(np.nanmin(seg))
            if 100.0 * (float(np.nanmax(seg)) - mn) / max(mn, 1e-9) <= max_var:
                break
            lo += 1
        if cerca is not None and not cerca[lo:hi + 1].any():
            continue
        if hi - lo + 1 >= min_w and (best is None or hi + 1 - lo > best[1] - best[0]):
            best = (lo, hi + 1)
    return best


def prueba_F(img, etiqueta, anchos=(180,)):
    roi = preprocessing.auto_detect_roi(img)  # defaults = los de main.py
    q = roi["roi_quality"]
    T = np.asarray(roi["thickness_profile"], float)
    sh = np.asarray(roi["sharpness_profile"], float)
    valid = np.asarray(roi["valid_columns"], bool)
    waist = float(q["cintura_px"]) if q.get("cintura_px") is not None else np.nan
    ok = valid & np.isfinite(sh) & (sh >= CFG.roi_min_gradient)
    cerca = np.isfinite(T) & (T <= waist * (1 + CFG.roi_thickness_tolerance))
    out = {"caso": etiqueta, "metodo_auto": q["method"],
           "roi_auto": f"{roi['x_start']}-{roi['x_end']}",
           "var_auto_pct": q.get("variacion_en_roi_pct"), "cintura_px": waist,
           "minimo_perfil_en_ok_px": float(np.nanmin(np.where(ok, T, np.nan))) if ok.any() else np.nan,
           "alternativas": [(a["metodo"], a["x_start"], a["x_end"], a["variacion_pct"])
                            for a in q.get("alternativas", [])]}
    xs, xe = roi["x_start"], roi["x_end"]
    seg = T[xs:xe]
    out["roi_auto_contiene_cintura"] = bool(cerca[xs:xe].any())
    out["roi_auto_grosor_min_sobre_cintura_pct"] = (
        round(100 * (np.nanmin(seg) / waist - 1), 2) if seg.size and np.isfinite(waist) else None)
    for w in anchos:
        a = _ventana_plana(T, ok, CFG.roi_max_variacion_pct, w)
        b = _ventana_plana(T, ok, CFG.roi_max_variacion_pct, w, cerca)
        out[f"rescate_actual_min{w}"] = f"{a[0]}-{a[1]}" if a else None
        out[f"rescate_con_cintura_min{w}"] = f"{b[0]}-{b[1]}" if b else None
    return out


def gel_sintetico(plana=150, w=1920, h=1080, cintura=285, anclaje=2.3, xc=960):
    """Reloj de arena: zona plana de `plana` px en la cintura, rampas, y
    mesetas de anclaje a `anclaje` x cintura (el caso de H20)."""
    import cv2
    x = np.arange(w, dtype=float)
    d = np.clip(np.abs(x - xc) - plana / 2, 0, None)
    T = cintura + (anclaje - 1) * cintura * np.clip(d / 350.0, 0, 1) ** 2
    img = np.full((h, w), 40, np.uint8)
    yc = h / 2
    for i in range(w):
        a, b = int(round(yc - T[i] / 2)), int(round(yc + T[i] / 2))
        img[max(a, 0):min(b, h), i] = 200
    img = cv2.GaussianBlur(img, (0, 0), 2.0)
    rng = np.random.default_rng(0)
    return np.clip(img + rng.normal(0, 3, img.shape), 0, 255).astype(np.uint8), T


# ---------------------------------------------------------------------------
# Prueba E: ruido compartido entre columnas segun la distancia
# ---------------------------------------------------------------------------
def correlacion_por_distancia(R, dmax=200):
    """R: (fotogramas, columnas) de residuos del borde respecto de la parabola
    del fotograma, sin la parte fija de cada columna. Devuelve r(d)."""
    R = R - np.nanmedian(R, axis=0, keepdims=True)
    out = []
    for d in range(1, min(dmax, R.shape[1] - 1) + 1):
        a, b = R[:, :-d].ravel(), R[:, d:].ravel()
        m = np.isfinite(a) & np.isfinite(b)
        out.append(float(np.corrcoef(a[m], b[m])[0, 1]) if m.sum() > 50 else np.nan)
    return np.array(out)


def _cruce(r, nivel):
    i = np.where(r < nivel)[0]
    return int(i[0] + 1) if len(i) else None


# ---------------------------------------------------------------------------
# Un video
# ---------------------------------------------------------------------------
def procesar(nombre, max_frames, paso_denso, out_dir):
    t0 = time.time()
    video = str(RAIZ / VIDEOS[nombre])
    diag_vig, xs, xe, kv = leer_vigente(nombre)
    print(f"\n=== {nombre}  ROI vigente {xs}-{xe} ===", flush=True)

    pts = io_utils.read_pts_seconds(video)
    max_proj = io_utils.compute_max_projection(video, stride=5)
    roi = preprocessing.auto_detect_roi(max_proj, x_start=xs, x_end=xe,
                                        n_columns=CFG.n_columns)
    tg, bg = roi["top_guess"], roi["bottom_guess"]
    xpos = np.linspace(xs, xe - 1, CFG.n_columns).astype(int)
    xden = np.arange(xs, xe)
    print(f"  timestamps + proyeccion: {time.time() - t0:.0f} s", flush=True)

    filas = {v[0]: [] for v in VARIANTES}
    nan_bordes = {k: 0 for k in ("clahe15", "crudo15", "clahe25")}
    inl_top, inl_bot, res_top, res_bot = [], [], [], []
    den = {"clahe": ([], []), "crudo": ([], [])}

    for idx, frame in io_utils.frame_generator(video):
        if max_frames and idx >= max_frames:
            break
        imgs = {"clahe": preprocessing.preprocess_frame(frame, use_clahe=True),
                "crudo": preprocessing.preprocess_frame(frame, use_clahe=False)}
        bordes = {}
        for pre, hw in (("clahe", 15), ("crudo", 15), ("clahe", 25)):
            x, yt, yb, _ = edge_detection.extract_edges_for_frame(
                imgs[pre], xpos, tg, bg, half_window=hw,
                method=CFG.edge_method, min_gradient=CFG.min_gradient)
            bordes[(pre, hw)] = (x, yt, yb)
            nan_bordes[f"{pre}{hw}"] += int(np.isnan(yt).sum() + np.isnan(yb).sum())
        t = float(pts[idx] - pts[0]) if idx < len(pts) else np.nan
        for nom, pre, hw, met in VARIANTES:
            fila, mt, mb = _fila(*bordes[(pre, hw)], met)
            fila["frame"], fila["time_s"] = idx, t
            filas[nom].append(fila)
            if nom == "vigente":
                x, yt, yb = bordes[(pre, hw)]
                inl_top.append(mt if mt is not None else np.zeros(len(x), bool))
                inl_bot.append(mb if mb is not None else np.zeros(len(x), bool))
                for y, dest in ((yt, res_top), (yb, res_bot)):
                    f = _mco(x, y)
                    dest.append(y - f[0] if f else np.full(len(x), np.nan))
        if paso_denso and idx % paso_denso == 0:
            for pre in ("clahe", "crudo"):
                x, yt, yb, _ = edge_detection.extract_edges_for_frame(
                    imgs[pre], xden, tg, bg, half_window=15,
                    method=CFG.edge_method, min_gradient=CFG.min_gradient)
                for y, dest in ((yt, den[pre][0]), (yb, den[pre][1])):
                    f = _mco(x, y)
                    dest.append(y - f[0] if f else np.full(len(x), np.nan))
        if idx % 250 == 0:
            print(f"  fotograma {idx}: {time.time() - t0:.0f} s", flush=True)

    n = len(filas["vigente"])
    dfs = {k: pd.DataFrame(v) for k, v in filas.items()}
    out_dir.mkdir(parents=True, exist_ok=True)
    ancho = pd.concat({k: d.drop(columns=["frame_quality"]) for k, d in dfs.items()}, axis=1)
    ancho.columns = [f"{a}__{b}" for a, b in ancho.columns]
    ancho.to_csv(out_dir / "series_variantes.csv", index=False)

    R = {"video": nombre, "n_frames": n, "roi": f"{xs}-{xe}",
         "segundos_proceso": None}

    # ---- control: vigente reproduce el xlsx ----
    v0 = diag_vig.iloc[:n]
    R["control_max_dif_center_px"] = float(np.nanmax(np.abs(dfs["vigente"]["center_px"].values - v0["center_px"].values)))
    R["control_max_dif_thickness_px"] = float(np.nanmax(np.abs(dfs["vigente"]["thickness_px"].values - v0["thickness_px"].values)))

    # ---- analisis de cada variante ----
    t_all = dfs["vigente"]["time_s"].to_numpy(float)
    eventos = {}
    tabla = []
    for nom, *_ in VARIANTES:
        d = dfs[nom]
        try:
            a = cr.analizar(d, "center_px", None, None, None, 1.5, frecuencia_estimulo=[0.1])
        except Exception as e:  # que un fallo no tire el resto
            tabla.append({"variante": nom, "error": repr(e)})
            continue
        rit = a.get("ritmo") or {}
        ev = np.asarray(a.get("tiempos_s", []), float)
        eventos[nom] = ev
        c, g = d["center_px"].to_numpy(float), d["thickness_px"].to_numpy(float)
        tabla.append({
            "variante": nom,
            "n_eventos": a.get("n_eventos"), "k_usado": a.get("k_usado"),
            "meseta": a.get("meseta_k_rango"), "mesetas": a.get("mesetas"),
            "reportable": a.get("conteo_reportable"),
            "amplitud_px": a.get("amplitud_traslacion_px"),
            "ruido_canal_px": a.get("ruido_canal_px"), "ruido_grosor_px": a.get("ruido_grosor_px"),
            "ruido_fotograma_centro_px": float(np.nanstd(np.diff(c)) / np.sqrt(2)),
            "ruido_fotograma_grosor_px": float(np.nanstd(np.diff(g)) / np.sqrt(2)),
            "outlier_frac_medio": float(d["outlier_frac"].mean()),
            "periodo_s": rit.get("periodo_s"), "periodo_err_s": rit.get("periodo_err_s"),
            "cociente_robusto_pct": a.get("cociente_robusto_pct"),
            "amplitud_relativa_pct": a.get("amplitud_relativa_pct"),
            "ttp_s": a.get("ttp_s"), "rt50_s": a.get("rt50_s"),
        })
    tabla = pd.DataFrame(tabla)

    # eventos que aparecen / desaparecen respecto de vigente (+-2 fotogramas)
    base = eventos.get("vigente", np.array([]))
    tol = 2.5 / 30.0
    cambios = {}
    for nom, ev in eventos.items():
        if nom == "vigente":
            continue
        nuevos = [round(x, 3) for x in ev if not np.any(np.abs(base - x) <= tol)]
        perdidos = [round(x, 3) for x in base if not np.any(np.abs(ev - x) <= tol)]
        cambios[nom] = {"nuevos_s": nuevos, "perdidos_s": perdidos}
    R["eventos_vs_vigente"] = cambios
    tabla.to_csv(out_dir / "variantes.csv", index=False)

    # ---- B (y C2): ¿la diferencia entre metodos sube en los eventos? ----
    fps = 1.0 / float(np.median(np.diff(t_all)))
    ipk = np.searchsorted(t_all, base) if len(base) else np.array([], int)
    r_vig = detrend_median(dfs["vigente"]["center_px"].to_numpy(float), fps, 2.0)

    def en_eventos(dif):
        rd = detrend_median(dif, fps, 2.0)
        m = mad(rd)
        if not len(ipk) or not np.isfinite(m) or m == 0:
            return {"ruido_dif_px": m}
        cerca = np.zeros(len(rd), bool)
        for p in ipk:
            cerca[max(0, p - 2):p + 3] = True
        exc = [float(rd[max(0, p - 2):p + 3][np.nanargmax(np.abs(rd[max(0, p - 2):p + 3]))]) for p in ipk]
        ok = np.isfinite(rd) & np.isfinite(r_vig)
        return {"ruido_dif_px": float(m),
                "desvio_dif_total_px": float(np.nanstd(dif)),
                "excursion_en_eventos_px": [round(e, 3) for e in exc],
                "excursion_mediana_en_ruidos": float(np.median(np.abs(exc)) / m),
                "frac_fotogramas_fuera_de_eventos_sobre_4ruidos_pct":
                    float(100 * np.mean(np.abs(rd[~cerca & ok]) > 4 * m)),
                "corr_con_senal": float(np.corrcoef(rd[ok], r_vig[ok])[0, 1])}

    for etiqueta, a_, b_ in (("B_clahe_menos_crudo", "vigente", "crudo"),
                             ("C_ransac_menos_mco", "vigente", "clahe_mco")):
        R[etiqueta] = {col: en_eventos(dfs[a_][col].to_numpy(float) - dfs[b_][col].to_numpy(float))
                       for col in ("center_px", "thickness_px", "y_top_px", "y_bottom_px")}
        R[etiqueta]["media_dif_px"] = {col: float(np.nanmean(dfs[a_][col] - dfs[b_][col]))
                                       for col in ("y_top_px", "y_bottom_px")}

    # ---- C: columnas que RANSAC descarta y residuo por columna ----
    it, ib = np.array(inl_top), np.array(inl_bot)
    rt, rb = np.abs(np.array(res_top)), np.abs(np.array(res_bot))
    tercios = {"primeras10": slice(0, 10), "centro": slice(10, -10), "ultimas10": slice(-10, None)}
    R["C_columnas"] = {
        borde: {z: {"descartadas_pct": round(100 * float(1 - inl[:, s].mean()), 1),
                    "residuo_mediano_px": round(float(np.nanmedian(res[:, s])), 3)}
                for z, s in tercios.items()}
        for borde, inl, res in (("superior", it, rt), ("inferior", ib, rb))}
    R["C_columnas_descartadas_mas_50pct"] = {
        "superior": [int(i) for i in np.where(1 - it.mean(0) > 0.5)[0]],
        "inferior": [int(i) for i in np.where(1 - ib.mean(0) > 0.5)[0]]}
    np.savez_compressed(out_dir / "columnas.npz", inl_top=it, inl_bot=ib, res_top=rt, res_bot=rb)

    # ---- D: bordes perdidos por pico pegado a la ventana ----
    tot = 2 * CFG.n_columns * n
    R["D_bordes_nan_pct"] = {k: round(100 * v / tot, 3) for k, v in nan_bordes.items()}
    R["D_max_dif_ventana25_vs_15"] = {
        col: float(np.nanmax(np.abs(dfs["ventana25"][col] - dfs["vigente"][col])))
        for col in ("center_px", "thickness_px")}

    # ---- E: ruido compartido entre columnas ----
    paso60 = (xe - 1 - xs) / (CFG.n_columns - 1)
    R["E_separacion_columnas_px"] = round(paso60, 2)
    corr = {}
    for pre in ("clahe", "crudo"):
        for i, borde in enumerate(("superior", "inferior")):
            if not den[pre][i]:
                continue
            r = correlacion_por_distancia(np.array(den[pre][i]))
            corr[f"{pre}_{borde}"] = r
            j = int(round(paso60))
            R.setdefault("E_ruido_compartido", {})[f"{pre}_{borde}"] = {
                "r_a_1px": round(float(r[0]), 3), "r_a_3px": round(float(r[2]), 3),
                "r_a_la_separacion_actual": round(float(r[j - 1]), 3) if j - 1 < len(r) else None,
                "distancia_r_bajo_0.5_px": _cruce(r, 0.5),
                "distancia_r_bajo_0.2_px": _cruce(r, 0.2)}
    if corr:
        pd.DataFrame(corr, index=pd.Index(range(1, len(next(iter(corr.values()))) + 1),
                                          name="distancia_px")).to_csv(out_dir / "E_correlacion.csv")

    # ---- F: rescate sobre la imagen de maximos del propio video ----
    R["F_rescate"] = prueba_F(max_proj, nombre, anchos=(180, 150, 120))

    R["segundos_proceso"] = round(time.time() - t0, 1)
    with open(out_dir / "resultado.json", "w", encoding="utf-8") as fh:
        json.dump(R, fh, ensure_ascii=False, indent=1, default=str)
    print(tabla.to_string(index=False), flush=True)
    print(f"  listo en {R['segundos_proceso']} s", flush=True)
    return R, tabla


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--videos", nargs="+", default=list(VIDEOS))
    p.add_argument("--max-frames", type=int, default=0,
                   help="Solo los primeros N fotogramas (0 = todos). Para medir el tiempo.")
    p.add_argument("--paso-denso", type=int, default=10,
                   help="Prueba E: columnas densas en 1 de cada N fotogramas (0 = no).")
    p.add_argument("--salida", default="data/fase3_borde")
    a = p.parse_args()

    salida = RAIZ / a.salida
    salida.mkdir(parents=True, exist_ok=True)
    md = ["# Fase 3, tema 6: medicion de borde y ajuste\n",
          f"max_frames = {a.max_frames or 'todos'}, paso_denso = {a.paso_denso}\n"]

    # F sobre sinteticos (no necesitan video)
    sint = []
    for plana in (150, 300, 1000):
        img, _ = gel_sintetico(plana=plana)
        sint.append(prueba_F(img, f"sintetico plana {plana} px (verdadera {960 - plana // 2}-{960 + plana // 2})",
                             anchos=(180, 150, 120)))
    md.append("## F en sinteticos\n```\n" + json.dumps(sint, ensure_ascii=False, indent=1, default=str) + "\n```\n")
    print(json.dumps(sint, ensure_ascii=False, indent=1, default=str))

    for nombre in a.videos:
        if nombre not in VIDEOS:
            print(f"(no conozco el video {nombre}; opciones: {list(VIDEOS)})")
            continue
        try:
            R, tabla = procesar(nombre, a.max_frames, a.paso_denso, salida / nombre)
        except Exception as e:
            import traceback
            traceback.print_exc()
            md.append(f"## {nombre}\nERROR: {e!r}\n")
            continue
        md.append(f"## {nombre}\n\n```\n{tabla.to_string(index=False)}\n```\n\n```\n"
                  + json.dumps(R, ensure_ascii=False, indent=1, default=str) + "\n```\n")
        (salida / "resumen_medicion.md").write_text("\n".join(md), encoding="utf-8")

    (salida / "resumen_medicion.md").write_text("\n".join(md), encoding="utf-8")
    print(f"\nResumen: {salida / 'resumen_medicion.md'}")


if __name__ == "__main__":
    main()
