"""C8 (2026-10-15): resumen de la BASAL, de 0 s hasta el inicio de la primera
estimulada (o 0-10 s si no hay tren). Solo mide; no cambia nada del reporte.

Para cada video: contracciones detectadas (las del reporte) dentro de la basal,
su frecuencia y amplitud; y, sin depender de la deteccion, cuanta actividad hay:
fraccion del tiempo con |senal| > 3 ruido (los dos sentidos) y amplitud tipica
(percentil 95 de |senal|, en % del grosor).

    python data/_mediciones_fases/c8_basal/medir.py
"""
from __future__ import annotations
import sys, warnings
from pathlib import Path
import numpy as np
import pandas as pd
RAIZ = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(RAIZ)); sys.path.insert(0, str(RAIZ / "scripts")); sys.path.insert(0, str(RAIZ / "tests"))
import contraction_report as cr  # noqa: E402
from referencia import VIDEOS, PROCESADOS, leer_serie  # noqa: E402
from src.output_paths import buscar_serie  # noqa: E402

filas = []
for carpeta, (_, _, frec) in VIDEOS.items():
    df, _ = leer_serie(buscar_serie(PROCESADOS / carpeta))
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        a = cr.analizar(df, "center_px", None, None, None, 1.5, frecuencia_estimulo=frec)
    t, r = np.asarray(a["_t"], float), np.asarray(a["_r"], float)
    ruido = float(a["ruido_canal_px"])
    grosor = float(np.nanmedian(df["thickness_px"]))
    ev = a["_cinetica"]
    rit = a.get("ritmo") or {}
    hay_tren = bool(rit.get("hay_estimulacion"))
    if hay_tren and len(ev) and "grupo" in ev:
        est = ev[ev["grupo"] == "estimulados"]
        on = est["onset_s"].to_numpy(float)
        fin = float(np.nanmin(on)) if np.isfinite(on).any() else float(est["tiempo_s"].min())
        origen = "hasta la 1.a estimulada"
    else:
        fin, origen = 10.0, "0-10 s (sin tren)"
    mb = (t >= t[0]) & (t < fin) & np.isfinite(r)
    dur = float(t[mb][-1] - t[mb][0]) if mb.any() else 0.0
    activo = float(np.mean(np.abs(r[mb]) > 3 * ruido)) if mb.any() else np.nan
    p95 = float(np.percentile(np.abs(r[mb]), 95)) if mb.any() else np.nan
    eb = ev[ev["tiempo_s"] < fin] if len(ev) else ev
    # ruido rapido: de fotograma a fotograma (no lo infla la actividad lenta)
    d = np.diff(r[mb]); d = d[np.isfinite(d)]
    rr = float(1.4826 * np.median(np.abs(d - np.median(d))) / np.sqrt(2))
    act_r = float(np.mean(np.abs(r[mb]) > 3 * rr))
    n = len(eb)
    tiempos = eb["tiempo_s"].to_numpy(float) if n else np.array([])
    iv = np.diff(tiempos)
    fila = {"video": carpeta, "reportable": bool(a.get("conteo_reportable")),
            "basal": origen, "basal_fin_s": round(fin, 2), "basal_dur_s": round(dur, 2),
            "contracciones_en_basal": n,
            "instantes_s": ", ".join(f"{x:.2f}" for x in tiempos),
            "junto_al_borde": int(np.asarray(a.get("_junto_al_borde", np.zeros(len(ev), bool)))[:n].sum()) if n else 0,
            "contracciones 0-10 s": int((ev["tiempo_s"] < 10.0).sum()) if len(ev) else 0,
            "frecuencia_Hz (mediana; IQR)": ("—" if len(iv) < 1 else
                                            f"{1 / np.median(iv):.2f}" + (f"; {1/np.percentile(iv,75):.2f}-{1/np.percentile(iv,25):.2f}" if len(iv) >= 3 else "")),
            "tasa (contr./s)": round(n / dur, 2) if dur > 0 else np.nan,
            "amplitud mediana (%)": round(float(np.median(eb["amplitud_relativa_pct"])), 3) if n else np.nan,
            "ruido (px)": round(ruido, 4),
            "fraccion |r|>3 ruido (%)": round(100 * activo, 1),
            "p95 |r| (% grosor)": round(100 * p95 / grosor, 3),
            "p95 |r| / ruido": round(p95 / ruido, 1),
            "ruido rapido (px)": round(rr, 4),
            "fraccion |r|>3 ruido rapido (%)": round(100 * act_r, 1),
            "p95 |r| / ruido rapido": round(p95 / rr, 1)}
    filas.append(fila)
    print(fila, flush=True)
T = pd.DataFrame(filas)
T.to_csv(Path(__file__).with_name("tabla_basal.csv"), index=False)
