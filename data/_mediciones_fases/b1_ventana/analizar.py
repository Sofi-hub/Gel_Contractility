import sys, pickle, warnings, math
from pathlib import Path
import numpy as np, pandas as pd
REPO = Path(__file__).resolve().parents[3]; sys.path.insert(0, str(REPO)); sys.path.insert(0, str(REPO/"tests")); sys.path.insert(0, str(REPO/"scripts"))
import referencia as ref
from contraction_report import analizar
R = Path(__file__).resolve().parent / "res"; CONG = ref.cargar_referencia()["videos"]
def huella(df, frec):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        r = analizar(df, "center_px", None, None, None, 1.5, frecuencia_estimulo=frec)
    rit = r.get("ritmo") or {}
    return dict(n=r.get("n_eventos"), rep=bool(r.get("conteo_reportable")), k=r.get("k_usado"),
        meseta=r.get("meseta_k_rango"), ruido=r.get("ruido_canal_px"), t=list(r.get("tiempos_s", [])),
        amp=r.get("amplitud_traslacion_px"), pct=r.get("amplitud_relativa_pct"), nest=rit.get("n_estimulados"),
        T=rit.get("periodo_s"), ttp=r.get("ttp_s"), rt50=r.get("rt50_s"), hash=ref.hash_serie(df["center_px"]))
def malos(df): return ((df.frame_quality != "OK").sum()) / len(df)
def ruido_hf(df, tev):
    c = df.center_px.to_numpy(float); t = df.time_s.to_numpy(float)
    m = pd.Series(c).rolling(9, center=True, min_periods=5).median().to_numpy()
    quieto = np.ones(len(c), bool)
    for te in tev: quieto &= np.abs(t - te) > 1.5
    d = (c - m)[quieto & np.isfinite(c)]
    return 1.4826 * np.median(np.abs(d - np.median(d))) if len(d) else np.nan
filas = []
for v, (vid, extra, frec) in ref.VIDEOS.items():
    p = {m: R / f"{v}__{m}.pkl" for m in ("max15", "max30", "med15")}
    if not all(x.exists() for x in p.values()): continue
    D = {m: pickle.load(open(x, "rb")) for m, x in p.items()}
    refm = "max30" if extra else "max15"
    opc = {"ref": refm, "a": "max15" if malos(D["max15"]["df"]) <= 0.01 else "med15", "b": "max30", "c": "med15"}
    H = {m: huella(D[m]["df"], frec) for m in D}
    hr = H[refm]; assert hr["hash"] == CONG[v]["hash_center_px"], (v, "no reproduce")
    tev = hr["t"]
    dr = D[refm]["df"]
    for o in ("a", "b", "c"):
        m = opc[o]; d = D[m]["df"]; h = H[m]
        dif = np.abs(d.center_px - dr.center_px).to_numpy()
        cambia = ~(dif < 0.01)  # incluye NaN de un lado
        f = dict(video=v[:9], op=o, guia=m, igual=(m == refm),
                 eventos=f"{hr['n']}{'' if hr['rep'] else 'NR'}->{h['n']}{'' if h['rep'] else 'NR'}",
                 k=f"{hr['k']}->{h['k']}", amp_pct=f"{hr['pct'] and round(hr['pct'],3)}->{h['pct'] and round(h['pct'],3)}",
                 T=f"{hr['T']}->{h['T']}", ttp=f"{hr['ttp']}->{h['ttp']}", rt50=f"{hr['rt50']}->{h['rt50']}",
                 dt_max=max([min(abs(a-b) for b in h['t']) for a in hr['t']] or [0]) if h['t'] else None,
                 malos=f"{100*malos(dr):.1f}->{100*malos(d):.1f}%", n_camb=int(cambia.sum()),
                 dif_med=float(np.nanmedian(dif[cambia])) if cambia.any() else 0,
                 outl=f"{dr.n_outlier_columns[cambia].mean():.2f}->{d.n_outlier_columns[cambia].mean():.2f}" if cambia.any() else "-",
                 mejor_peor=f"{int((d.n_outlier_columns<dr.n_outlier_columns)[cambia].sum())}/{int((d.n_outlier_columns>dr.n_outlier_columns)[cambia].sum())}" if cambia.any() else "-",
                 nan_col=f"{(dr.nan_top+dr.nan_bot).mean():.2f}->{(d.nan_top+d.nan_bot).mean():.2f}",
                 cerca=f"{dr.cerca.mean():.2f}->{d.cerca.mean():.2f}",
                 ruido=f"{ruido_hf(dr,tev):.4f}->{ruido_hf(d,tev):.4f}", ruido_rep=f"{hr['ruido']:.4f}->{h['ruido']:.4f}")
        filas.append(f)
pd.set_option("display.width", 400); pd.set_option("display.max_columns", 30); pd.set_option("display.max_colwidth", 30)
T = pd.DataFrame(filas); print(T.to_string(index=False)); T.to_csv(Path(__file__).resolve().parent / "tabla.csv", index=False)
