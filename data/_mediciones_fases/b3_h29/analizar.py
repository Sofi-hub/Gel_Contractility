import sys, pickle, warnings
from pathlib import Path
import numpy as np, pandas as pd
REPO=Path(__file__).resolve().parents[3]; sys.path[:0]=[str(REPO),str(REPO/"scripts"),str(REPO/"tests")]
import referencia as ref
R = Path(__file__).resolve().parent / "res"
from contraction_report import analizar
def an(df,f):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore"); r=analizar(df,"center_px",None,None,None,1.5,frecuencia_estimulo=f)
    return r
def hf(df,tev):
    c=df.center_px.to_numpy(float); t=df.time_s.to_numpy(float)
    m=pd.Series(c).rolling(9,center=True,min_periods=5).median().to_numpy()
    q=np.ones(len(c),bool)
    for te in tev: q&=np.abs(t-te)>1.5
    d=(c-m)[q&np.isfinite(c)]; return 1.4826*np.median(np.abs(d-np.median(d)))
for v in ["Video_466_EXP5_FAPS4_40V","Video_476","Video_prueba","Video_063_CTRL1_5V","Video_268_EXP3_FAPS2_40V","Video_583_EXP6_CTRL4_40V","Video_491_EXP5_CTRL1_36HZ","Video_613"]:
    f=ref.VIDEOS[v][2]
    A=pickle.load(open(f"{R}/{v}__max15.pkl","rb"))["df"]; B=pickle.load(open(f"{R}/{v}__lsq.pkl","rb"))
    ra,rb=an(A,f),an(B,f); ta=ra.get("tiempos_s",[])
    d=(B.center_px-A.center_px).to_numpy()
    amp=lambda r:[round(float(x),2) for x in np.asarray(r["_r"])[r["_picos"]]] if r["n_eventos"] else []
    nr=lambda r:"" if r["conteo_reportable"] else "NR"
    print(f"{v[:9]:9s} ruido_hf {hf(A,ta):.4f}->{hf(B,ta):.4f} | ruido rep {ra['ruido_canal_px']:.4f}->{rb['ruido_canal_px']:.4f} | ev {ra['n_eventos']}{nr(ra)}->{rb['n_eventos']}{nr(rb)} k {ra['k_usado']}->{rb['k_usado']} mes {ra.get('meseta_k_rango')}->{rb.get('meseta_k_rango')} | amp% {ra.get('amplitud_relativa_pct') and round(ra['amplitud_relativa_pct'],3)}->{rb.get('amplitud_relativa_pct') and round(rb['amplitud_relativa_pct'],3)} | ttp {ra.get('ttp_s')}->{rb.get('ttp_s')} rt50 {ra.get('rt50_s')}->{rb.get('rt50_s')} | dif centro med {np.nanmedian(d):+.3f} sd {np.nanstd(d):.3f} | grosor sd {A.thickness_px.std():.3f}->{B.thickness_px.std():.3f}")
    print("    amp px", amp(ra), "->", amp(rb))
