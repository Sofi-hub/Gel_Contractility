import sys, glob, json, warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, '/home/claude/w/repo'); sys.path.insert(0, '/home/claude/w/repo/tests')
import numpy as np, pandas as pd
import referencia as ref
from src.output_paths import buscar_serie
filas = []
for c in ref.VIDEOS:
    fr = ref.VIDEOS[c][2]
    bse = f"/home/claude/w/v11/{c}"
    hb = ref.huella(glob.glob(bse + "/serie_temporal_*.xlsx")[0], fr)
    db = pd.read_excel(glob.glob(bse + "/serie_temporal_*.xlsx")[0], sheet_name=0)
    for var in ["actual", "k2", "k4", "trials1000"]:
        d = bse if var == "actual" else f"/home/claude/w/h30/{var}/{c}"
        f = glob.glob(d + "/serie_temporal_*.xlsx")
        if not f: continue
        h = hb if var == "actual" else ref.huella(f[0], fr)
        df = db if var == "actual" else pd.read_excel(f[0], sheet_name=0)
        dc = np.nanmax(np.abs(df.center_px.to_numpy(float) - db.center_px.to_numpy(float)))
        filas.append({"video": c[:12], "var": var, "eventos": h["n_eventos"], "reportable": h["conteo_reportable"],
                      "mismos_instantes": h["tiempos_s"] == hb["tiempos_s"], "k": h["k_usado"],
                      "ruido": round(h["ruido_canal_px"], 4), "amp_%": h["amplitud_relativa_pct"],
                      "estim": h["n_estimulados"], "outlier_med": round(float(df.outlier_frac.median()), 4),
                      "center_dif_max": round(float(dc), 4)})
t = pd.DataFrame(filas); print(t.to_string()); t.to_csv("/home/claude/w/h30/tabla.csv", index=False)
