import sys, json, glob
sys.path.insert(0, '/home/claude/w/repo'); sys.path.insert(0, '/home/claude/w/repo/tests')
import numpy as np, pandas as pd
import referencia as ref
from src.output_paths import buscar_serie
cong = ref.cargar_referencia()["videos"]
filas = []
for c in ref.VIDEOS:
    o = f"/home/claude/w/v11/{c}"
    nueva = glob.glob(o + "/serie_temporal_*.xlsx")
    if not nueva: filas.append({"video": c, "estado": "sin correr"}); continue
    a = pd.read_excel(buscar_serie(ref.PROCESADOS / c), sheet_name=0)
    b = pd.read_excel(nueva[0], sheet_name=0)
    fila = {"video": c, "fotogramas": len(b)}
    for col in ["center_px", "y_top_px", "y_bottom_px", "thickness_px"]:
        x, y = a[col].to_numpy(float), b[col].to_numpy(float)
        fila[col] = "identico" if (len(x) == len(y) and np.array_equal(np.isnan(x), np.isnan(y)) and np.nanmax(np.abs(x - y)) == 0) else f"dif max {np.nanmax(np.abs(x-y)):.2e}"
    dif = ref.diferencias(cong[c], ref.huella(nueva[0], ref.VIDEOS[c][2]))
    fila["reporte"] = "IGUAL" if not dif else "; ".join(dif)[:200]
    info = json.load(open(o + "/info.json"))
    fila.update(info)
    r = pd.read_excel(nueva[0], sheet_name=None)
    res = next(v for k, v in r.items() if "resumen" in k)
    d = dict(zip(res.iloc[:, 0].astype(str), res.iloc[:, 1]))
    fila["half_window"] = d.get("half_window"); fila["faltantes"] = d.get("frames faltantes estimados"); fila["faltantes_%"] = d.get("frames faltantes (%)")
    filas.append(fila)
t = pd.DataFrame(filas); print(t.to_string()); t.to_csv("/home/claude/w/v11/tabla.csv", index=False)
