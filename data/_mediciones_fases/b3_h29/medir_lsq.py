"""H29: ajuste sin RANSAC (minimos cuadrados con todas las columnas validas) vs RANSAC.
uso: python b3.py <carpeta> <ransac|lsq> <salida>"""
import sys, pickle
from pathlib import Path
import numpy as np
REPO = Path(__file__).resolve().parents[3]; sys.path[:0] = [str(REPO), str(REPO/"tests")]
import referencia as ref
from src import pipeline, robust_fitting
carpeta, modo, out = sys.argv[1], sys.argv[2], Path(sys.argv[3])
if modo == "lsq":
    orig = robust_fitting.fit_edge_ransac
    def lsq(x, y, degree=2, **kw):
        r = orig(x, y, degree=degree, **kw)
        if r is None: return None
        ok = np.isfinite(y); xn = (x - x.mean()) / max(x.std(), 1e-9)
        c = np.polyfit(xn[ok], y[ok], degree)
        r.y_fitted = np.polyval(c, xn); r.inlier_mask = ok.copy()
        r.residual_px = float(np.median(np.abs(y[ok] - r.y_fitted[ok])))
        return r
    pipeline.robust_fitting.fit_edge_ransac = lsq
video = str(ref.CRUDOS / ref.VIDEOS[carpeta][0])
df = pipeline.process_video(video, pipeline.PipelineConfig(), verbose=False, n_procesos=1)
out.mkdir(parents=True, exist_ok=True)
pickle.dump(df.drop(columns=[c for c in df.columns if c.startswith("_")]), open(out/f"{carpeta}__{modo}.pkl", "wb"))
print("listo", carpeta, modo)
