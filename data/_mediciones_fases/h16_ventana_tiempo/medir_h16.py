"""H16: ¿cambia algo si la mediana de la deriva usa una ventana en SEGUNDOS (con los
timestamps reales) en vez de en FOTOGRAMAS? Rehace el reporte de los 11 videos de las
dos formas, sobre las series guardadas. No toca el codigo del repo."""
import sys, warnings
from pathlib import Path
import numpy as np, pandas as pd
REPO = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(REPO), str(REPO / "scripts"), str(REPO / "tests")]
import referencia as ref
from src.output_paths import buscar_serie
import contraction_report as cr
from src import estadistica as est

ORIG = cr.detrend_median
T_ACTUAL = {}

def detrend_tiempo(v, fps, win_s=2.0):
    """Misma ventana nominal (int(win_s*fps)|1 muestras), pero medida en segundos con
    los timestamps: entran las muestras a |dt| <= (w//2)/fps + medio intervalo."""
    t = T_ACTUAL["t"]; v = np.asarray(v, float)
    if len(t) != len(v):
        return ORIG(v, fps, win_s)
    w = int(win_s * fps) | 1
    half = (w // 2) / fps + 0.5 / fps
    lo = np.searchsorted(t, t - half, "left"); hi = np.searchsorted(t, t + half, "right")
    med = np.array([np.nanmedian(v[a:b]) if np.isfinite(v[a:b]).any() else np.nan
                    for a, b in zip(lo, hi)])
    return v - med

def huella(df, f):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        r = cr.analizar(df, "center_px", None, None, None, 1.5, frecuencia_estimulo=f)
    rit = r.get("ritmo") or {}
    return dict(n=r["n_eventos"], rep=r["conteo_reportable"], k=r["k_usado"], mes=r.get("meseta_k_rango"),
                ruido=r["ruido_canal_px"], t=np.round(r.get("tiempos_s", []), 3).tolist(),
                pct=r.get("amplitud_relativa_pct"), px=r.get("amplitud_px"), T=rit.get("periodo_s"),
                est=rit.get("n_estimulados"), ttp=r.get("ttp_s"), rt50=r.get("rt50_s"), win=r.get("win_s"))

print("ventanas de 'win_s' con fotogramas perdidos adentro y cuanto se estiran:")
for v, (_, _, f) in ref.VIDEOS.items():
    df, _ = ref.leer_serie(buscar_serie(ref.PROCESADOS / v))
    t = df["time_s"].to_numpy(float); T_ACTUAL["t"] = t
    a = huella(df, f)
    cr.detrend_median = detrend_tiempo
    try:
        b = huella(df, f)
    finally:
        cr.detrend_median = ORIG
    fps = 1 / np.median(np.diff(t)); w = int((a["win"] or 2) * fps) | 1
    span = t[w - 1:] - t[:len(t) - w + 1]; nominal = (w - 1) / fps
    larga = 100 * np.mean(span > nominal + 0.5 / fps)
    camb = {k: (a[k], b[k]) for k in a if a[k] != b[k] and not (isinstance(a[k], float) and isinstance(b[k], float)
            and (np.isclose(a[k], b[k], rtol=1e-9) or (np.isnan(a[k]) and np.isnan(b[k]))))}
    print(f"\n{v}: {larga:.1f}% de las ventanas cubren mas tiempo que el nominal (max +{span.max() - nominal:.2f} s)")
    if not camb:
        print("   sin cambios")
    for k, (x, y) in camb.items():
        print(f"   {k}: {x} -> {y}")
