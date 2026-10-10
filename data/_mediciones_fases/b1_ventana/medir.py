"""B1: corre un video con una configuracion de guia y guarda serie + diagnosticos por fotograma.
uso: python medir.py <carpeta_ref> <modo: max15|max30|med15> <salida_dir>"""
import sys, json, pickle
from pathlib import Path
import numpy as np, cv2
REPO = Path(__file__).resolve().parents[3]; sys.path.insert(0, str(REPO)); sys.path.insert(0, str(REPO/"tests"))
import referencia as ref
from src import pipeline, preprocessing, edge_detection, io_utils

carpeta, modo, out = sys.argv[1], sys.argv[2], Path(sys.argv[3])
video = str(ref.CRUDOS / ref.VIDEOS[carpeta][0])
hw = 30 if modo.endswith("30") else 15

def mediana_video(path, paso=20):
    cap = cv2.VideoCapture(path); fr = []; i = 0
    while True:
        ok, f = cap.read()
        if not ok: break
        if i % paso == 0: fr.append(cv2.cvtColor(f, cv2.COLOR_BGR2GRAY))
        i += 1
    cap.release()
    return np.median(np.stack(fr), axis=0).astype(np.uint8)

orig_roi = preprocessing.auto_detect_roi
GUIAS = {}
def roi_parcheada(maxp, **kw):
    r = orig_roi(maxp, **kw)
    GUIAS["max"] = (r["top_guess"].copy(), r["bottom_guess"].copy())
    if modo.startswith("med"):
        med = mediana_video(video)
        kw2 = dict(kw); kw2["x_start"], kw2["x_end"] = r["x_start"], r["x_end"]
        r2 = orig_roi(med, **kw2)
        r["top_guess"], r["bottom_guess"] = r2["top_guess"], r2["bottom_guess"]
    GUIAS["usada"] = (r["top_guess"].copy(), r["bottom_guess"].copy())
    return r
pipeline.preprocessing.auto_detect_roi = roi_parcheada

orig_ext = edge_detection.extract_edges_for_frame
EXTRA = {}
def ext(frame, xp, tg, bg, half_window=15, **kw):
    x, yt, yb, q = orig_ext(frame, xp, tg, bg, half_window=half_window, **kw)
    t0 = np.array([tg[i] for i in xp]); b0 = np.array([bg[i] for i in xp])
    # borde pegado (<=2 px) al limite de la ventana: posible borde fuera de ella
    cerca = lambda y, g: np.isfinite(y) & ((y - (g.astype(int) - half_window) <= 2) | ((g.astype(int) + half_window) - y <= 2))
    EXTRA.update(nan_top=int(np.isnan(yt).sum()), nan_bot=int(np.isnan(yb).sum()),
                 cerca=int(cerca(yt, t0).sum() + cerca(yb, b0).sum()),
                 dist_top=float(np.nanmedian(yt - t0)) if np.isfinite(yt).any() else np.nan,
                 dist_bot=float(np.nanmedian(yb - b0)) if np.isfinite(yb).any() else np.nan)
    return x, yt, yb, q
pipeline.edge_detection.extract_edges_for_frame = ext
orig_pf = pipeline.process_frame
def pf(*a, **k):
    r = orig_pf(*a, **k); r.update(EXTRA); return r
pipeline.process_frame = pf

cfg = pipeline.PipelineConfig(half_window=hw, base_tiempo="pts")
df = pipeline.process_video(video, cfg, verbose=False, n_procesos=1)
out.mkdir(parents=True, exist_ok=True)
roi = df.attrs["roi"]; xs, xe = roi["x_start"], roi["x_end"]
g = {k: (np.asarray(v[0])[xs:xe], np.asarray(v[1])[xs:xe]) for k, v in GUIAS.items()}
pickle.dump({"df": df.drop(columns=[c for c in df.columns if c.startswith("_")]), "attrs": {k: v for k, v in df.attrs.items() if k != "roi"},
             "roi": (xs, xe, roi["roi_quality"].get("method"), roi["roi_quality"].get("n_columnas_usadas")),
             "guias": g}, open(out / f"{carpeta}__{modo}.pkl", "wb"))
print("listo", carpeta, modo, len(df))
