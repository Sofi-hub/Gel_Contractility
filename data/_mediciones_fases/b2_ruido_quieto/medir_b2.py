"""B2: ruido estimado solo en tramos quietos. Compara contra el reporte actual en los 11 videos.
uso: python medir_b2.py [corte_en_mad] [margen_s]"""
import sys, time, types, warnings
from pathlib import Path
import numpy as np
REPO = Path(__file__).resolve().parents[3]; sys.path[:0] = [str(REPO), str(REPO/"scripts"), str(REPO/"tests")]
import referencia as ref
from src.output_paths import buscar_serie
from src.estadistica import mad
import contraction_report as cr
CORTE = float(sys.argv[1]) if len(sys.argv) > 1 else 5.0
MARGEN = float(sys.argv[2]) if len(sys.argv) > 2 else 0.5

def ruido_quieto(r, fps):
    """MAD solo de los fotogramas quietos: se saca todo lo que pasa de CORTE*ruido
    (hacia los DOS lados, para no favorecer al control invertido) y MARGEN s alrededor;
    se repite hasta que el ruido no cambia."""
    m = mad(r); n = max(1, int(round(MARGEN * fps)))
    for _ in range(10):
        act = np.abs(r) > CORTE * m
        act = np.convolve(act.astype(float), np.ones(2 * n + 1), "same") > 0
        q = ~act & np.isfinite(r)
        if q.sum() < 0.3 * np.isfinite(r).sum(): break       # casi todo activo: no achicar mas
        m2 = mad(r[q])
        if abs(m2 - m) < 1e-6 * m: m = m2; break
        m = m2
    return m

src = Path(cr.__file__).read_text(encoding="utf-8")
lineas = src.split("\n")
# solo el ruido que fija el umbral (escaneo de k y analizar); signo y duracion quedan igual
for i in (124, 325):
    assert lineas[i].strip() == "m = mad(r)", lineas[i]
    lineas[i] = lineas[i].replace("mad(r)", "ruido_quieto(r, fps)")
nuevo = types.ModuleType("cr_b2"); nuevo.__dict__["__file__"] = cr.__file__
exec(compile("\n".join(lineas), "cr_b2", "exec"), nuevo.__dict__)
nuevo.ruido_quieto = ruido_quieto

def res(mod, df, frec):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        t = time.time(); r = mod.analizar(df, "center_px", None, None, None, 1.5, frecuencia_estimulo=frec)
    e = r["estabilidad"]; kk = r["k_usado"]
    f = int(e.loc[(e.k - kk).abs().idxmin(), "falsos_control"])
    rit = r.get("ritmo") or {}
    return dict(n=r["n_eventos"], rep=r["conteo_reportable"], k=kk, mes=r.get("meseta_k_rango"),
                ruido=r["ruido_canal_px"], umbral=kk * r["ruido_canal_px"], falsos=f,
                t=list(r.get("tiempos_s", [])), est=rit.get("n_estimulados"), T=rit.get("periodo_s"),
                pct=r.get("amplitud_relativa_pct"), ttp=r.get("ttp_s"), seg=time.time() - t)
print(f"corte {CORTE} MAD, margen {MARGEN} s")
for v, (_, _, frec) in ref.VIDEOS.items():
    df, _ = ref.leer_serie(buscar_serie(REPO / "data/processed_data" / v))
    a, b = res(cr, df, frec), res(nuevo, df, frec)
    nuevos = [round(x, 2) for x in b["t"] if min([abs(x - y) for y in a["t"]] or [9]) > 0.1]
    perdidos = [round(x, 2) for x in a["t"] if min([abs(x - y) for y in b["t"]] or [9]) > 0.1]
    nr = lambda h: "" if h["rep"] else "NR"
    print(f"{v[:9]:10s} ruido {a['ruido']:.4f}->{b['ruido']:.4f} | eventos {a['n']}{nr(a)}->{b['n']}{nr(b)} "
          f"| k {a['k']}->{b['k']} meseta {a['mes']}->{b['mes']} | umbral {a['umbral']:.3f}->{b['umbral']:.3f} px "
          f"| falsos {a['falsos']}->{b['falsos']} | estim {a['est']}->{b['est']} T {a['T']}->{b['T']} "
          f"| amp% {a['pct'] and round(a['pct'],3)}->{b['pct'] and round(b['pct'],3)} "
          f"| +{nuevos} -{perdidos} | {a['seg']:.1f}s->{b['seg']:.1f}s")
