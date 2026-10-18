"""Textura: ¿achicar los 4K a la mitad cambia el resultado? (2026-10-17)

Compara dos carpetas de resultados del MISMO video: una medida achicada (lo
normal) y otra con --resolucion-completa. Solo lee los Excel.

Cómo correrlo (una noche, 1 o 2 videos):
    python main.py --video "data/raw_videos/Videos_Andres/40V/1.mp4" --metodo textura ^
        --resolucion-completa --output-dir data/processed_data/_4k_completo/40V_1
    python scripts/contraction_report.py ^
        --input data/processed_data/_4k_completo/40V_1/serie_temporal_1.xlsx --frecuencia-estimulo 0.1
    python data/_mediciones_fases/textura/comparar_resolucion.py ^
        data/processed_data/40V_1  data/processed_data/_4k_completo/40V_1

Escribe comparacion_<nombre>.txt al lado de este script.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from src.estadistica import detrend_median  # noqa: E402


def leer(carpeta: Path):
    serie = next(carpeta.glob("serie_temporal_*.xlsx"))
    h = pd.read_excel(serie, sheet_name=None)
    df = h["diagnostics"]
    meta = dict(zip(h["resumen"]["Métrica"], h["resumen"]["Valor"]))
    c = next(carpeta.glob("contracciones_*.xlsx"), None)
    res = ev = None
    if c is not None:
        hc = pd.read_excel(c, sheet_name=None)
        res = next(v for k, v in hc.items() if k.startswith("resumen")).iloc[0]
        ev = next(v for k, v in hc.items() if k.startswith("eventos"))
    return df, meta, res, ev


def main():
    a, b = Path(sys.argv[1]), Path(sys.argv[2])
    (da, ma, ra, ea), (db, mb, rb, eb) = leer(a), leer(b)
    out = []
    p = out.append
    p(f"A = {a}  (escala {ma.get('textura escala (1 = tamano original)')})")
    p(f"B = {b}  (escala {mb.get('textura escala (1 = tamano original)')})")
    n = min(len(da), len(db))
    t = da["time_s"].to_numpy(float)[:n]
    fps = 1.0 / np.median(np.diff(t))
    sa = detrend_median(da["center_px"].to_numpy(float)[:n], fps, 2.0)
    sb = detrend_median(db["center_px"].to_numpy(float)[:n], fps, 2.0)
    dif = sa - sb
    p(f"serie (sin deriva): correlación {np.corrcoef(sa, sb)[0, 1]:.4f}; "
      f"diferencia RMS {np.sqrt(np.mean(dif ** 2)):.4f} px, máx {np.max(np.abs(dif)):.4f} px")
    p(f"grosor aproximado: A {float(ma.get('grosor medio (px)')):.1f} px, B {float(mb.get('grosor medio (px)')):.1f} px")
    if ra is not None and rb is not None:
        for nom, col in (("eventos", "n_eventos"), ("reportable", "conteo_reportable"),
                         ("ruido (px)", "ruido_canal_px"), ("amplitud (px)", "amplitud_px"),
                         ("amplitud (% grosor)", "amplitud_relativa_pct"), ("k", "k_usado")):
            p(f"{nom:22s} A {ra.get(col)}   B {rb.get(col)}")
        ta, tb = ea["tiempo_s"].to_numpy(float), eb["tiempo_s"].to_numpy(float)
        pares = [(i, int(np.argmin(np.abs(tb - x)))) for i, x in enumerate(ta)
                 if len(tb) and np.min(np.abs(tb - x)) < 0.3]
        p(f"eventos emparejados (±0.3 s): {len(pares)} de A {len(ta)} / B {len(tb)}")
        for i, j in pares:
            aa, ab = ea["amplitud_px"].iloc[i], eb["amplitud_px"].iloc[j]
            p(f"  {ta[i]:7.2f} s   A {aa:.3f} px   B {ab:.3f} px   A/B {aa / ab:.3f}")
    else:
        p("(falta contracciones_*.xlsx en alguna carpeta: correr el paso 2)")
    texto = "\n".join(out)
    print(texto)
    (Path(__file__).parent / f"comparacion_{b.name}.txt").write_text(texto, encoding="utf-8")


if __name__ == "__main__":
    main()
