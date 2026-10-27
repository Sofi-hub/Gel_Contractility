"""Detalle de la comparación textura / bordes (2026-10-26). Solo medición.

La pregunta que decide todo: cuando la textura detecta algo que los bordes no,
¿se está inventando movimiento o los bordes lo tienen tapado por su propio ruido?

Para cada evento que ve la textura y no los bordes, se mide:
  - cuánto sobresale en la señal de TEXTURA (px y en veces su ruido),
  - cuánto hay en la señal de BORDES en ESE MISMO instante (px y en veces el ruido
    de bordes) y a cuántas veces del umbral que bordes estaba usando,
  - la correlación de las dos señales en +-1 s alrededor del instante.
Si en bordes hay una subida en el mismo instante pero por debajo de su umbral,
la textura no inventa nada: ve algo que bordes no puede resolver.

Además, para 466: el valle entre los dos picos del evento de 34.2 s, medido en
las dos señales y en veces el ruido de cada una.

    python data/_mediciones_fases/textura_falla_bordes/detalle_textura.py
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "scripts"))
sys.path.insert(0, str(RAIZ / "tests"))
import contraction_report as cr                      # noqa: E402
from src.estadistica import mad                      # noqa: E402
from referencia import PROCESADOS                    # noqa: E402

AQUI = Path(__file__).resolve().parent
SERIES = AQUI / "series"
# (carpeta, nombre, ventana donde aparecen los eventos de mas)
CASOS = [("Video_583_EXP6_CTRL4_40V", "583", None),
         ("Video_466_EXP5_FAPS4_40V", "466", None),
         ("Video_063_CTRL1_5V", "063", 1.5),
         ("Video_268_EXP3_FAPS2_40V", "268", 1.5)]


def series(carpeta, nombre):
    df = pd.read_excel(next((PROCESADOS / carpeta).glob("serie_temporal_*.xlsx")),
                       sheet_name="diagnostics")
    tex = pd.read_csv(SERIES / f"{nombre}_textura.csv")
    n = min(len(df), len(tex))
    d = df.iloc[:n].copy()
    d2 = d.copy()
    d2["center_px"] = tex["center_px"].to_numpy()[:n]
    d2["thickness_px"] = float(tex["grosor_px"].iloc[0])
    d2["y_top_px"] = d2["center_px"] - d2["thickness_px"] / 2
    d2["y_bottom_px"] = d2["center_px"] + d2["thickness_px"] / 2
    return d, d2


def main():
    filas, notas = [], []
    for carpeta, nombre, win in CASOS:
        df_bor, df_tex = series(carpeta, nombre)
        ab = cr.analizar(df_bor, "center_px", None, win, None, 1.5, separar=False)
        at = cr.analizar(df_tex, "center_px", None, win, None, 1.5, separar=False)
        t, rb, rt = ab["_t"], ab["_r"], at["_r"]
        n = min(len(rb), len(rt))
        t, rb, rt = t[:n], rb[:n], rt[:n]
        tb = ab["_t"][ab["_picos"]]
        ruido_b, ruido_t = float(ab["ruido_canal_px"]), float(at["ruido_canal_px"])
        umbral_b = float(ab["k_usado"]) * ruido_b
        print(f"\n=== {nombre} (ventana {'auto' if win is None else win}) ===")
        print(f"  ruido bordes {ruido_b:.4f} px (umbral {umbral_b:.3f} px, k={ab['k_usado']:.2f}) | "
              f"ruido textura {ruido_t:.4f} px (umbral {float(at['k_usado']) * ruido_t:.3f} px, "
              f"k={at['k_usado']:.2f}) | textura {ruido_b / ruido_t:.1f}x menos ruido")
        for p in at["_picos"]:
            x = at["_t"][p]
            if len(tb) and np.min(np.abs(tb - x)) <= 0.3:
                continue                       # ese evento también lo ve bordes
            i = int(np.argmin(np.abs(t - x)))
            w = (t >= x - 1.0) & (t <= x + 1.0)
            # en bordes: el máximo local en +-2 fotogramas del instante
            lo, hi = max(0, i - 2), min(n, i + 3)
            vb = float(np.nanmax(rb[lo:hi]))
            vt = float(rt[i])
            cc = (float(np.corrcoef(rb[w], rt[w])[0, 1])
                  if np.isfinite(rb[w]).all() and np.isfinite(rt[w]).all() else np.nan)
            filas.append({
                "video": nombre, "t_s": round(float(x), 2),
                "textura_px": round(vt, 3), "textura_x_ruido": round(vt / ruido_t, 1),
                "bordes_mismo_instante_px": round(vb, 3),
                "bordes_x_ruido": round(vb / ruido_b, 1),
                "bordes_x_umbral": round(vb / umbral_b, 2),
                "lo_ve_bordes": bool(vb >= umbral_b),
                "correlacion_local": round(cc, 3) if np.isfinite(cc) else None,
            })
        d = pd.DataFrame([f for f in filas if f["video"] == nombre])
        if len(d):
            print(f"  {len(d)} eventos que solo ve la textura:")
            print(f"    en textura: {d.textura_px.min():.2f}-{d.textura_px.max():.2f} px "
                  f"({d.textura_x_ruido.min():.0f}-{d.textura_x_ruido.max():.0f} x su ruido)")
            print(f"    en bordes, mismo instante: {d.bordes_mismo_instante_px.min():.2f}-"
                  f"{d.bordes_mismo_instante_px.max():.2f} px "
                  f"({d.bordes_x_ruido.min():.1f}-{d.bordes_x_ruido.max():.1f} x su ruido; "
                  f"{100 * d.bordes_x_umbral.median():.0f} % del umbral de bordes, mediana)")
            print(f"    correlación local de las dos señales: mediana "
                  f"{d.correlacion_local.median():.2f} "
                  f"({(d.correlacion_local > 0.5).sum()} de {len(d)} con r > 0.5)")
            notas.append(f"{nombre}: {len(d)} eventos solo en textura; en bordes valen "
                         f"{100 * d.bordes_x_umbral.median():.0f} % del umbral (mediana)")
        else:
            print("  no hay eventos que solo vea la textura con esta ventana")

        if nombre == "466":
            # el valle entre los dos picos del evento partido
            pk = [float(at["_t"][p]) for p in at["_picos"] if 33.8 <= at["_t"][p] <= 34.8]
            if len(pk) >= 2:
                a, b = min(pk), max(pk)
                m = (t >= a) & (t <= b)
                for met, r, ru in (("textura", rt, ruido_t), ("bordes", rb, ruido_b)):
                    alto = min(float(np.interp(a, t, r)), float(np.interp(b, t, r)))
                    valle = float(np.nanmin(r[m]))
                    print(f"  466, valle entre los picos de {a:.2f} y {b:.2f} s en {met}: "
                          f"{alto - valle:.3f} px = {(alto - valle) / ru:.1f} x su ruido "
                          f"({100 * (alto - valle) / alto:.0f} % de la altura del evento)")
                    notas.append(f"466 valle {met}: {alto - valle:.3f} px = "
                                 f"{(alto - valle) / ru:.1f} x ruido")
    pd.DataFrame(filas).to_csv(AQUI / "solo_textura.csv", index=False)
    print("\ntabla: solo_textura.csv")
    for x in notas:
        print("  ·", x)


if __name__ == "__main__":
    main()
