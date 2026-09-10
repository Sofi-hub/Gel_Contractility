"""
scripts/signal_check.py
------------------------
¿Hay una población de contracciones en esta serie, sí o no?

Se corre sobre el `serie_temporal.xlsx` que produce main.py y responde
esa pregunta ANTES de discutir umbrales, k, agudeza o conteos.

POR QUÉ HACE FALTA, además de la curva de estabilidad del umbral
------------------------------------------------------------------
La curva de estabilidad (`05_estabilidad_umbral.png`) responde "¿el
conteo depende del umbral?". Es útil, pero es indirecta: una serie sin
señal y una serie con señal mal medida dan curvas parecidas (decaimiento
monótono, sin meseta), y no distingue una de la otra.

La ASIMETRÍA sí las distingue, y no depende de ningún umbral:

  Una contracción es una excursión hacia ABAJO desde una línea base, y
  el gel pasa más tiempo relajado que contraído. Entonces la
  distribución de la señal sin deriva queda con una cola larga hacia
  abajo: asimetría (skew) claramente NEGATIVA.

  El ruido de medición — venga del sensor, del ajuste, o de la
  compresión — es simétrico: sube tanto como baja. Skew ~ 0.

Medido sobre dos videos reales del proyecto:

    Video_prueba (contrae, validado)   skew = -2.21   3.4% del tiempo bajo -4 sigma
    Video_063                          skew = +0.28   0.2% del tiempo bajo -4 sigma

Ese contraste es inequívoco y no depende de elegir ningún parámetro.

IMPORTANTE — no usar un filtro pasabanda para quitar la deriva. Un
pasabanda convierte cada evento real en un dip flanqueado por dos picos
falsos hacia arriba, y eso destruye justamente la asimetría que se
quiere medir. Acá la deriva se quita con una MEDIANA móvil.

Uso:
    python scripts/signal_check.py --input data/processed_data/mi_video/serie_temporal.xlsx
    python scripts/signal_check.py --input A.xlsx --compare B.xlsx   (control positivo)
"""

from __future__ import annotations
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.stats import skew


def _detrend_median(v: np.ndarray, fps: float, win_s: float) -> np.ndarray:
    s = pd.Series(v)
    w = int(win_s * fps) | 1
    return (s - s.rolling(w, center=True, min_periods=1).median()).to_numpy()


def analizar(df: pd.DataFrame, col: str = "thickness_px", win_s: float = 2.0) -> dict:
    t = df["time_s"].to_numpy(float)
    v = df[col].to_numpy(float)
    ok = np.isfinite(v)
    t, v = t[ok], v[ok]
    fps = 1.0 / np.median(np.diff(t))
    r = _detrend_median(v, fps, win_s)
    ru = float(np.median(np.abs(r - np.median(r))) * 1.4826)
    return {
        "columna": col,
        "n": len(v),
        "fps": round(fps, 2),
        "media_px": round(float(v.mean()), 3),
        "recorrido_px": round(float(v.max() - v.min()), 4),
        "ruido_sin_deriva_px": round(ru, 4),
        "skew": round(float(skew(r)), 3),
        "pct_bajo_-4sigma": round(100 * float(np.mean(r < -4 * ru)), 3),
        "pct_sobre_+4sigma": round(100 * float(np.mean(r > 4 * ru)), 3),
        "_t": t, "_v": v, "_r": r, "_ru": ru,
    }


def veredicto(a: dict) -> str:
    sk, lo, hi = a["skew"], a["pct_bajo_-4sigma"], a["pct_sobre_+4sigma"]
    asim = lo / hi if hi > 0 else (np.inf if lo > 0 else 1.0)
    if sk <= -1.0 and lo >= 0.5 and asim >= 2:
        return "HAY una poblacion de contracciones (asimetria clara hacia abajo)"
    if sk <= -0.5 and lo >= 0.2 and asim >= 1.5:
        return "posible senal debil: asimetria hacia abajo, pero poco marcada"
    if abs(sk) < 0.5 and asim < 1.5:
        return ("NO hay poblacion de contracciones en esta senal: es simetrica, "
                "sube tanto como baja (=ruido)")
    return "ambiguo: revisar a mano"


def parse_args():
    p = argparse.ArgumentParser(
        description="Test de asimetria: hay o no una poblacion de contracciones",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    p.add_argument("--input", required=True, help="serie_temporal.xlsx (salida de main.py)")
    p.add_argument("--compare", default=None,
                   help="Segunda serie para comparar (ideal: un video que SI contrae, "
                        "como control positivo).")
    p.add_argument("--column", default="thickness_px",
                   help="Columna a analizar. Probar tambien 'center_px': el grosor es "
                        "ciego a una traslacion vertical del gel, center_px no.")
    p.add_argument("--win-s", type=float, default=2.0,
                   help="Ventana (s) de la mediana movil que quita la deriva. Debe ser "
                        "bastante mayor que la duracion de un evento.")
    p.add_argument("--output-dir", default=None)
    return p.parse_args()


def _leer(path):
    p = Path(path)
    return pd.read_csv(p) if p.suffix == ".csv" else pd.read_excel(p, sheet_name="diagnostics")


def main():
    a = parse_args()
    series = [(Path(a.input).parent.name or Path(a.input).stem, _leer(a.input))]
    if a.compare:
        series.append((Path(a.compare).parent.name or Path(a.compare).stem, _leer(a.compare)))

    resultados = []
    for nombre, df in series:
        cols = [a.column] + (["center_px"] if ("center_px" in df.columns and a.column != "center_px") else [])
        for c in cols:
            if c not in df.columns:
                print(f"(la serie '{nombre}' no tiene la columna '{c}'; se omite)")
                continue
            r = analizar(df, c, a.win_s)
            r["serie"] = nombre
            resultados.append(r)

    print()
    print("%-26s %-13s %9s %10s %8s %9s %9s" % (
        "serie", "columna", "recorrido", "ruido", "skew", "<-4sig%", ">+4sig%"))
    print("-" * 92)
    for r in resultados:
        print("%-26s %-13s %9.4f %10.4f %+8.2f %9.3f %9.3f" % (
            r["serie"][:26], r["columna"], r["recorrido_px"], r["ruido_sin_deriva_px"],
            r["skew"], r["pct_bajo_-4sigma"], r["pct_sobre_+4sigma"]))
    print()
    for r in resultados:
        print(f"  {r['serie'][:26]:26s} {r['columna']:13s} -> {veredicto(r)}")
    print()
    print("  Referencia: una contraccion real es una excursion hacia ABAJO y el gel pasa")
    print("  mas tiempo relajado que contraido, asi que la distribucion queda con cola")
    print("  hacia abajo (skew negativo). El ruido es simetrico (skew ~ 0).")

    # --- gráfico: serie sin deriva + histograma ---
    n = len(resultados)
    fig, axes = plt.subplots(n, 2, figsize=(13, 2.8 * n), squeeze=False,
                             gridspec_kw={"width_ratios": [3, 1]})
    for i, r in enumerate(resultados):
        ax1, ax2 = axes[i, 0], axes[i, 1]
        ax1.plot(r["_t"], r["_r"], color="crimson", lw=0.6)
        for k, ls in ((-4, "--"), (4, "--")):
            ax1.axhline(k * r["_ru"], color="gray", ls=ls, lw=0.8)
        ax1.set_ylabel(f"{r['columna']}\n(sin deriva, px)")
        ax1.set_title(f"{r['serie']}  —  skew {r['skew']:+.2f}  |  "
                      f"{r['pct_bajo_-4sigma']:.2f}% abajo vs {r['pct_sobre_+4sigma']:.2f}% arriba",
                      fontsize=10)
        ax1.grid(alpha=0.3)
        ax2.hist(r["_r"], bins=80, color="steelblue", edgecolor="none")
        ax2.axvline(0, color="black", lw=0.8)
        ax2.set_yscale("log"); ax2.set_title("distribucion (log)", fontsize=9)
    axes[-1, 0].set_xlabel("Tiempo (s)")
    fig.tight_layout()
    out = Path(a.output_dir) if a.output_dir else Path(a.input).parent
    out.mkdir(parents=True, exist_ok=True)
    png = out / "08_asimetria.png"
    fig.savefig(png, dpi=140); plt.close(fig)
    print(f"\nGrafico: {png}")


if __name__ == "__main__":
    main()
