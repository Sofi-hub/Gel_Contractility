#!/usr/bin/env python
"""
medir_motion_check.py  -  Fase 4, punto 2 (H50, H51). SOLO MIDE.

Pregunta: con la correlacion arreglada, ¿la traslacion vertical medida por
INTENSIDAD (perfil vertical de la franja, sin usar bordes) coincide en
magnitud con center_px (medida por BORDES)?

Por fotograma, dentro de la ROI vigente:
  desp_vert_viejo  = motion_check._subpixel_shift actual (normaliza todo el
                     perfil y suma solo la superposicion: achica)
  desp_vert_nuevo  = Pearson sobre la parte superpuesta, en cada lag
Eje de tiempo: PTS. Se compara contra center_px de serie_temporal.xlsx
(mismo indice de fotograma), los dos sin deriva (mediana movil 2 s).

Salida por video: pendiente (desp / center) en todo el video y en los
eventos, correlacion, y cociente de amplitudes evento por evento.

USO (desde la raiz del repo):
    python scripts/medir_motion_check.py                  # prueba, 063, 466
    python scripts/medir_motion_check.py 063
Salida: data/fase4_motion/motion_<video>.xlsx  y  resumen_motion.md
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.signal import find_peaks

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "scripts"))

from src import io_utils, preprocessing  # noqa: E402
from src.estadistica import mad, detrend_median  # noqa: E402
from motion_check import _subpixel_shift as shift_viejo  # noqa: E402

OK = "data/raw_videos/OK-20260904T142817Z-1-001/OK/"
VIDEOS = {  # nombre: (video, x_start, x_end)  -- ROI vigente (Fase 3)
    "Video_prueba": ("data/raw_videos/Video_prueba.mp4", 454, 1516),
    "Video_063_CTRL1_5V": (OK + "Video_063_CTRL1_5V.mp4", 875, 1039),
    "Video_466_EXP5_FAPS4_40V": (OK + "Video_466_EXP5_FAPS4_40V.mp4", 696, 846),
}
MAX_LAG = 25


def shift_nuevo(ref, cur, max_lag=MAX_LAG, min_corr=0.5):
    """Correlacion de Pearson sobre la parte superpuesta, para cada lag."""
    ref = np.asarray(ref, float)
    cur = np.asarray(cur, float)
    n = len(ref)
    lags = np.arange(-max_lag, max_lag + 1)
    corr = np.full(len(lags), -1.0)
    for i, L in enumerate(lags):
        a = ref[max(0, -L): n - max(0, L)]
        b = cur[max(0, L): n - max(0, -L)]
        a = a - a.mean()
        b = b - b.mean()
        d = np.linalg.norm(a) * np.linalg.norm(b)
        if d > 1e-9:
            corr[i] = float(np.dot(a, b) / d)
    j = int(np.argmax(corr))
    pico = float(corr[j])
    if pico < min_corr:
        return np.nan, pico
    if j == 0 or j == len(corr) - 1:
        return float(lags[j]), pico
    cm, c0, cp = corr[j - 1], corr[j], corr[j + 1]
    den = cm - 2 * c0 + cp
    delta = 0.0 if abs(den) < 1e-12 else 0.5 * (cm - cp) / den
    return float(lags[j] + delta), pico


def autoprueba():
    """Perfil sintetico corrido una cantidad conocida (interpolacion lineal)."""
    y = np.arange(400, dtype=float)
    perfil = lambda c: 50 + 100 / (1 + np.exp(-(y - c + 140) / 3)) - 100 / (1 + np.exp(-(y - c - 140) / 3))
    ref = perfil(200.0)
    filas = []
    for s in (0.25, 0.5, 1.0, 2.0, 3.0):
        cur = perfil(200.0 + s)
        filas.append({"verdad_px": s, "viejo_px": shift_viejo(ref, cur, max_lag=MAX_LAG)[0],
                      "nuevo_px": shift_nuevo(ref, cur)[0]})
    return pd.DataFrame(filas)


def pendiente(x, y):
    ok = np.isfinite(x) & np.isfinite(y)
    if ok.sum() < 10:
        return np.nan, np.nan
    x, y = x[ok], y[ok]
    return float(np.dot(x, y) / np.dot(x, x)), float(np.corrcoef(x, y)[0, 1])


def medir(nombre):
    t0 = time.time()
    ruta, xs, xe = VIDEOS[nombre]
    video = str(RAIZ / ruta)
    serie = pd.read_excel(RAIZ / f"data/processed_data/{nombre}/serie_temporal.xlsx",
                          sheet_name="diagnostics")
    pts = io_utils.read_pts_seconds(video)
    max_proj = io_utils.compute_max_projection(video, stride=5)
    roi = preprocessing.auto_detect_roi(max_proj, x_start=xs, x_end=xe)
    top = roi["top_guess"][xs:xe]
    bot = roi["bottom_guess"][xs:xe]
    H = max_proj.shape[0]
    y0, y1 = int(max(0, np.median(top) - 40)), int(min(H, np.median(bot) + 40))

    filas, ref = [], None
    for idx, frame in io_utils.frame_generator(video):
        p = frame[y0:y1, xs:xe].astype(np.float32).mean(axis=1)
        if ref is None:
            ref = p.copy()
        sv, cv = shift_viejo(ref, p, max_lag=MAX_LAG)
        sn, cn = shift_nuevo(ref, p)
        filas.append({"frame": idx, "time_s": float(pts[idx] - pts[0]) if idx < len(pts) else np.nan,
                      "desp_viejo_px": sv, "corr_viejo": cv, "desp_nuevo_px": sn, "corr_nuevo": cn})
        if idx % 500 == 0:
            print(f"  {nombre} fotograma {idx}: {time.time() - t0:.0f} s", flush=True)

    d = pd.DataFrame(filas).merge(serie[["frame", "center_px"]], on="frame", how="left")
    fps = 1.0 / np.nanmedian(np.diff(d["time_s"].to_numpy()))
    c = detrend_median(d["center_px"].to_numpy(float), fps, 2.0)
    vv = detrend_median(d["desp_viejo_px"].to_numpy(float), fps, 2.0)
    vn = detrend_median(d["desp_nuevo_px"].to_numpy(float), fps, 2.0)
    d["center_sd"], d["viejo_sd"], d["nuevo_sd"] = c, vv, vn

    # eventos: picos de center_px sin deriva, en el sentido de la cola mas pesada
    ruido = mad(c)
    signo = 1.0 if np.nanmean(c > 4 * ruido) >= np.nanmean(c < -4 * ruido) else -1.0
    picos, _ = find_peaks(np.nan_to_num(signo * c, nan=-np.inf), height=8 * ruido,
                          prominence=8 * ruido)
    ev = d.iloc[picos][["time_s", "center_sd", "viejo_sd", "nuevo_sd"]].copy()
    ev["cociente_viejo"] = ev["viejo_sd"] / ev["center_sd"]
    ev["cociente_nuevo"] = ev["nuevo_sd"] / ev["center_sd"]
    en_ev = np.zeros(len(d), bool)
    for p in picos:
        en_ev[max(0, p - 3): p + 4] = True

    res = {"video": nombre, "fotogramas": len(d), "n_eventos": len(picos)}
    for nom, v in (("viejo", vv), ("nuevo", vn)):
        k_all, r_all = pendiente(c, v)
        k_ev, _ = pendiente(c[en_ev], v[en_ev])
        res[f"pendiente_todo_{nom}"] = k_all
        res[f"correlacion_{nom}"] = r_all
        res[f"pendiente_eventos_{nom}"] = k_ev
        res[f"cociente_mediano_eventos_{nom}"] = float(np.nanmedian(ev[f"cociente_{nom}"]))
        res[f"frac_sin_enganche_{nom}_pct"] = 100 * float(np.isnan(d[f"desp_{nom}_px"]).mean())
    res["ruido_center_px"] = ruido
    res["ruido_desp_nuevo_px"] = mad(vn)
    print(f"{nombre}: {time.time() - t0:.0f} s", flush=True)
    return pd.DataFrame([res]), ev, d


def main():
    pedidos = sys.argv[1:]
    nombres = [v for v in VIDEOS if not pedidos or any(p in v for p in pedidos)]
    salida = RAIZ / "data/fase4_motion"
    salida.mkdir(parents=True, exist_ok=True)
    prueba = autoprueba()
    print("Autoprueba (perfil sintetico corrido una cantidad conocida):")
    print(prueba.round(3).to_string(index=False), flush=True)
    todos = []
    for nom in nombres:
        res, ev, d = medir(nom)
        with pd.ExcelWriter(salida / f"motion_{nom}.xlsx") as w:
            res.to_excel(w, sheet_name="resumen", index=False)
            ev.to_excel(w, sheet_name="eventos", index=False)
            d.to_excel(w, sheet_name="serie", index=False)
        todos.append(res)
        tabla = pd.concat(todos, ignore_index=True)
        md = ["# Fase 4, punto 2: motion_check viejo vs arreglado\n",
              "Autoprueba:\n```\n" + prueba.round(3).to_string(index=False) + "\n```\n",
              "```\n" + tabla.round(3).T.to_string() + "\n```\n"]
        (salida / "resumen_motion.md").write_text("\n".join(md), encoding="utf-8")
    print(tabla.round(3).T.to_string())
    print(f"\nlisto -> {salida}")


if __name__ == "__main__":
    main()
