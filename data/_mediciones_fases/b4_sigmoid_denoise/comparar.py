import sys, glob, subprocess
import numpy as np, pandas as pd
for v in ["Video_prueba", "Video_063"]:
    base = None
    for m in ["base", "sigmoid", "denoise"]:
        f = glob.glob(f"/home/claude/w/b4/{v}/{m}/serie_temporal_*.xlsx")
        if not f: print(v, m, "falta"); continue
        d = f"/home/claude/w/b4/{v}/{m}"
        if not glob.glob(d+"/contracciones_*.xlsx"):
            subprocess.run([sys.executable, "scripts/contraction_report.py", "--input", f[0], "--frecuencia-estimulo", "0.1"],
                           cwd="/home/claude/w/orig", capture_output=True)
        df = pd.read_excel(f[0], sheet_name=0)
        c = df["center_px"].to_numpy(float)
        if base is None: base = c
        dc = np.diff(c); ruido = 1.4826*np.nanmedian(np.abs(dc-np.nanmedian(dc)))/np.sqrt(2)
        hs = pd.read_excel(glob.glob(d+"/contracciones_*.xlsx")[0], sheet_name=None)
        R = next(x for k,x in hs.items() if k.startswith("resumen_")).iloc[0]; Rt=next(x for k,x in hs.items() if k.startswith("ritmo_"))
        g = lambda *ks: next((R[k] for k in ks if k in R.index), None)
        print(f"{v:12s} {m:8s} ev={g('n_eventos')} k={g('k_usado','k')} ruido={g('ruido_canal_px'):.4f} meseta={g('meseta_k_rango')} amp_px={g('amplitud_px')} ruido_fot={ruido:.4f}px "
              f"outl={df['outlier_frac'].median():.4f} |dif|med={np.nanmedian(np.abs(c-base)):.3f}px "
              f"amp%={g('amplitud_rel_pct','amplitud_relativa_pct')}")
    print()
