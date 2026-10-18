"""40V/1 (copia x0.5) por textura + el mismo contraction_report, a 0.1 Hz."""
import sys, subprocess
from pathlib import Path
import numpy as np, pandas as pd
AQUI = Path(__file__).resolve().parent; RAIZ = AQUI.parents[2]
sys.path.insert(0, str(AQUI)); sys.path.insert(0, str(RAIZ))
import textura_medir as tm
from src import io_utils
v = RAIZ / "data/raw_videos/_copias_chicas/40V_1_x0.5.mp4"
out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
m = tm.medir_lk(str(v))
n = len(m["dy"]); fps = 30.0
pts = io_utils.read_pts_seconds(v)
t = pts - pts[0] if len(pts) == n else np.arange(n) / fps
df = pd.DataFrame(dict(frame=np.arange(n), time_s=t, center_px=m["centro_ref"] + m["dy"],
                       thickness_px=m["grosor"], frame_quality="OK"))
df["y_top_px"] = df.center_px - m["grosor"] / 2; df["y_bottom_px"] = df.center_px + m["grosor"] / 2
df["thickness_mm"] = df.thickness_px; df["thickness_mm_smooth"] = df.thickness_px
p = out / "serie_temporal_40V_1_x50.xlsx"
with pd.ExcelWriter(p) as w:
    df.to_excel(w, sheet_name="diagnostics", index=False)
    pd.DataFrame({"Métrica": ["video", "metodo"], "Valor": [str(v), "textura"]}).to_excel(w, sheet_name="resumen", index=False)
print(f"rot {m['rot']}, franja y {m['y0']}-{m['y1']}, x {m['x0']}-{m['x1']}, grosor {m['grosor']:.0f} px, respuesta mediana {np.median(m['resp']):.2f}")
r = subprocess.run([sys.executable, str(RAIZ / "scripts/contraction_report.py"), "--input", str(p), "--frecuencia-estimulo", "0.1"], capture_output=True, text=True)
print(r.stdout[-3500:], r.stderr[-1500:])
