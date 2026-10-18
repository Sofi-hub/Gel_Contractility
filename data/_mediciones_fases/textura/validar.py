"""Textura contra bordes en los videos de referencia reportables.
Para cada video: serie por textura (medir_lk), con columnas 'centro' (autónomo)
y con la ROI de bordes; arma una serie_temporal igual a la de main.py con
center_px = centro de la franja + corrimiento, y corre el MISMO
contraction_report. Compara eventos, instantes, k y amplitud.
    python validar.py <tmp>          medir_lk (primera versión): validacion.csv
    python validar.py <tmp> final    el método implementado (src/textura.py): validacion_final.csv
"""
import subprocess, sys, json
from pathlib import Path
import numpy as np
import pandas as pd

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[2]
sys.path.insert(0, str(AQUI)); sys.path.insert(0, str(RAIZ)); sys.path.insert(0, str(RAIZ / "tests"))
import textura_medir as tm  # noqa
from referencia import VIDEOS, CRUDOS, PROCESADOS  # noqa

TMP = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/tmp/textura_val")
REPORTABLES = ["Video_prueba", "Video_063_CTRL1_5V", "Video_268_EXP3_FAPS2_40V",
               "Video_466_EXP5_FAPS4_40V", "Video_583_EXP6_CTRL4_40V",
               "Video_491_EXP5_CTRL1_36HZ", "Video_476"]


def hojas(p):
    return pd.read_excel(p, sheet_name=None)


def resumen_reporte(xlsx):
    h = hojas(xlsx)
    res = next(v for k, v in h.items() if k.startswith("resumen"))
    ev = next((v for k, v in h.items() if k.startswith("eventos")), pd.DataFrame(columns=["tiempo_s", "amplitud_px"]))
    tr = next((v for k, v in h.items() if k.startswith("trenes")), None)
    r = res.iloc[0].to_dict()
    r["periodo_s"] = float(tr["periodo_s"].iloc[0]) if tr is not None and len(tr) else None
    return r, ev


filas = []
for nom in REPORTABLES:
    crudo, _, frec = VIDEOS[nom]
    video = CRUDOS / crudo
    serie = next((PROCESADOS / nom).glob("serie_temporal_*.xlsx"))
    hs = hojas(serie)
    df = hs["diagnostics"]
    meta = dict(zip(hs["resumen"]["Métrica"], hs["resumen"]["Valor"]))
    roi = (int(meta["ROI x_start"]), int(meta["ROI x_end"]))
    r_bor, cin_bor = resumen_reporte(next((PROCESADOS / nom).glob("contracciones_*.xlsx")))
    FINAL = len(sys.argv) > 2 and sys.argv[2] == "final"
    modos = (("centro", "centro"),) if FINAL else (("centro", "centro"), ("roi_bordes", roi))
    for modo, cols in modos:
        m = (tm.medir_final if FINAL else tm.medir_lk)(str(video), rotacion=0, cols=cols)
        n = min(len(m["dy"]), len(df))
        d2 = df.iloc[:n].copy()
        d2["center_px"] = m["centro_ref"] + m["dy"][:n]
        d2["thickness_px"] = m["grosor"]
        d2["y_top_px"] = d2["center_px"] - m["grosor"] / 2
        d2["y_bottom_px"] = d2["center_px"] + m["grosor"] / 2
        d2["frame_quality"] = "OK"
        out = TMP / nom / modo
        out.mkdir(parents=True, exist_ok=True)
        p = out / f"serie_temporal_{nom}.xlsx"
        with pd.ExcelWriter(p) as w:
            d2.to_excel(w, sheet_name="diagnostics", index=False)
            hs["resumen"].to_excel(w, sheet_name="resumen", index=False)
        cmd = [sys.executable, str(RAIZ / "scripts" / "contraction_report.py"), "--input", str(p),
               "--output-dir", str(out)]
        if frec:
            cmd += ["--frecuencia-estimulo", ",".join(str(x) for x in frec)]
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        r_tex, cin_tex = resumen_reporte(next(out.glob("contracciones_*.xlsx")))
        # instantes (inicio) y cociente de amplitud evento a evento (mismos eventos emparejados a +-0.3 s)
        tb = cin_bor["tiempo_s"].to_numpy(float)
        tt = cin_tex["tiempo_s"].to_numpy(float)
        pares = [(i, int(np.argmin(np.abs(tt - x)))) for i, x in enumerate(tb) if len(tt) and np.min(np.abs(tt - x)) < 0.3]
        coc = [cin_tex["amplitud_px"].iloc[j] / cin_bor["amplitud_px"].iloc[i] for i, j in pares] \
            if len(pares) else []
        filas.append(dict(
            video=nom, columnas=modo, x=f"{m['x0']}-{m['x1']}", franja_y=f"{m['y0']}-{m['y1']}",
            grosor_textura=round(m["grosor"], 1), grosor_bordes=round(float(np.nanmedian(df.thickness_px)), 1),
            eventos_bordes=r_bor.get("n_eventos"), eventos_textura=r_tex.get("n_eventos"),
            emparejados=len(pares), reportable_textura=r_tex.get("conteo_reportable"),
            k_bordes=r_bor.get("k_usado"), k_textura=r_tex.get("k_usado"),
            ruido_bordes=r_bor.get("ruido_canal_px"), ruido_textura=r_tex.get("ruido_canal_px"),
            ampl_px_bordes=r_bor.get("amplitud_px"), ampl_px_textura=r_tex.get("amplitud_px"),
            ampl_pct_bordes=r_bor.get("amplitud_relativa_pct"), ampl_pct_textura=r_tex.get("amplitud_relativa_pct"),
            ttp_bordes=r_bor.get("ttp_s"), ttp_textura=r_tex.get("ttp_s"), rt50_bordes=r_bor.get("rt50_s"), rt50_textura=r_tex.get("rt50_s"),
            cociente_eventos_mediana=round(float(np.median(coc)), 3) if coc else None,
            cociente_eventos_min=round(float(np.min(coc)), 3) if coc else None,
            cociente_eventos_max=round(float(np.max(coc)), 3) if coc else None,
            periodo_bordes=r_bor.get("periodo_s"), periodo_textura=r_tex.get("periodo_s"),
        ))
        print(json.dumps(filas[-1], default=str), flush=True)
pd.DataFrame(filas).to_csv(AQUI / ("validacion_final.csv" if len(sys.argv) > 2 and sys.argv[2] == "final" else "validacion.csv"), index=False)
