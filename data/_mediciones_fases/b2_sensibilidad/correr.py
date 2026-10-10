"""B2, sensibilidad: ruido = MAD de los fotogramas quietos, con corte C (MAD) y margen M (s)."""
import sys, json
sys.path.insert(0, '/home/claude/w/repo'); sys.path.insert(0, '/home/claude/w/repo/tests'); sys.path.insert(0, '/home/claude/w/repo/scripts')
import numpy as np, pandas as pd
import referencia as ref
import contraction_report as cr
from src.output_paths import buscar_serie
mad_orig = cr.mad
def hacer_mad(C, M, fps=30.0):
    def mad_quieto(r):
        r = np.asarray(r, float); ok = np.isfinite(r)
        if ok.sum() < 10: return mad_orig(r)
        quieto = ok.copy(); m = mad_orig(r); w = int(round(M * fps))
        for _ in range(20):
            med = np.nanmedian(r[quieto]); fuera = ok & (np.abs(r - med) > C * m)
            idx = np.flatnonzero(fuera); q = ok.copy()
            for i in idx: q[max(0, i - w): i + w + 1] = False
            if q.sum() < 0.2 * ok.sum(): break
            m2 = mad_orig(np.where(q, r, np.nan))
            quieto = q
            if abs(m2 - m) < 1e-6 * max(m, 1e-12): m = m2; break
            m = m2
        return m
    return mad_quieto
VID = ["Video_prueba","Video_063_CTRL1_5V","Video_268_EXP3_FAPS2_40V","Video_466_EXP5_FAPS4_40V","Video_583_EXP6_CTRL4_40V","Video_491_EXP5_CTRL1_36HZ","Video_476"]
filas = []
for C, M in [(None, None), (4,0.3),(4,0.5),(4,1.0),(5,0.3),(5,0.5),(5,1.0),(6,0.3),(6,0.5),(6,1.0)]:
    cr.mad = mad_orig if C is None else hacer_mad(C, M)
    for c in VID:
        df = pd.read_excel(buscar_serie(ref.PROCESADOS / c), sheet_name=0)
        r = cr.analizar(df, "center_px", None, "auto", None, 1.5, frecuencia_estimulo=ref.VIDEOS[c][2]) if False else None
        h = ref.huella(buscar_serie(ref.PROCESADOS / c), ref.VIDEOS[c][2])
        filas.append({"corte": C, "margen_s": M, "video": c, **{k: (v if not isinstance(v, (list, dict)) else json.dumps(v)) for k, v in h.items()}})
        print(C, M, c, flush=True)
pd.DataFrame(filas).to_csv("/home/claude/w/b2s/tabla.csv", index=False)
print("FIN")
