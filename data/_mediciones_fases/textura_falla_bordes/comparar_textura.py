"""Textura contra bordes en 583, 466, 063 y 268 (2026-10-26). Solo medición:
no toca el análisis ni escribe en data/processed_data.

Pregunta: con `--metodo textura` estos cuatro videos empeoran (583 pasa a 39
eventos, 466 parte uno, 063 y 268 pierden la meseta con la ventana de 1.5 s),
mientras que con bordes los cuatro están bien. ¿Es una falla de la textura o la
textura está viendo algo que los bordes tapan?

Qué hace:
  1. Mide la serie por textura con el método implementado (src/textura.py), la
     misma que usaría `main.py --metodo textura`, y la guarda en series/ para no
     tener que volver a medir.
  2. Corre la MISMA detección (contraction_report.analizar) sobre la serie de
     bordes y sobre la de textura, con la ventana automática y fijada en 1.5, 2
     y 3 s, y anota conteo, meseta y motivo.
  3. Compara las dos series: ruido en los tramos quietos, dónde difieren (en qué
     segundos) y amplitud evento a evento.
  4. Figuras: la serie entera de las dos y un zoom en el tramo que decide.

    python data/_mediciones_fases/textura_falla_bordes/comparar_textura.py
    python ... comparar_textura.py --remedir     (ignora la caché de series/)
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "scripts"))
sys.path.insert(0, str(RAIZ / "tests"))
import contraction_report as cr                      # noqa: E402
from src import textura as tx                        # noqa: E402
from src.estadistica import mad, detrend_median      # noqa: E402
from referencia import VIDEOS, CRUDOS, PROCESADOS    # noqa: E402

AQUI = Path(__file__).resolve().parent
SERIES = AQUI / "series"
VENTANAS = (1.5, 2.0, 3.0)
LEJOS_S = 1.0          # cuánto hay que alejarse de un evento para considerar "quieto"
EMPAREJA_S = 0.3       # dos eventos son el mismo si caen a menos de esto

# (carpeta de resultados, nombre corto, tramo de interés para el zoom, por qué)
CASOS = [
    ("Video_583_EXP6_CTRL4_40V", "583", (70.0, 76.0), "ráfaga/vibración del final"),
    ("Video_466_EXP5_FAPS4_40V", "466", (33.5, 35.5), "el evento que se parte"),
    ("Video_063_CTRL1_5V", "063", (0.0, 3.0), "primer evento, junto al borde"),
    ("Video_268_EXP3_FAPS2_40V", "268", (0.0, 3.0), "arranque de la serie"),
]


# ------------------------------------------------------------------ series
def serie_bordes(carpeta):
    s = next((PROCESADOS / carpeta).glob("serie_temporal_*.xlsx"))
    h = pd.read_excel(s, sheet_name=None)
    return h["diagnostics"], h["resumen"]


def serie_textura(carpeta, nombre, remedir=False):
    """center_px por textura. Se cachea: medir el video entero tarda minutos."""
    SERIES.mkdir(exist_ok=True)
    cache = SERIES / f"{nombre}_textura.csv"
    if cache.is_file() and not remedir:
        return pd.read_csv(cache)
    crudo = VIDEOS[carpeta][0]
    m = tx.medir(str(CRUDOS / crudo), rotacion=0)
    d = pd.DataFrame({"dy_px": m["dy"], "respuesta": m["respuesta"]})
    d.attrs = {}
    d["center_px"] = m["centro_ref"] + m["dy"]
    d["grosor_px"] = m["grosor_px"]
    d.to_csv(cache, index=False)
    print(f"  {nombre}: textura medida ({len(d)} fotogramas, franja "
          f"{m['y0']}-{m['y1']}, grosor {m['grosor_px']:.0f} px) -> {cache.name}")
    return d


def df_textura(df_bor, tex):
    """Una serie con la pinta de la de main.py pero con center_px de textura."""
    n = min(len(df_bor), len(tex))
    d = df_bor.iloc[:n].copy()
    d["center_px"] = tex["center_px"].to_numpy()[:n]
    d["thickness_px"] = float(tex["grosor_px"].iloc[0])
    d["y_top_px"] = d["center_px"] - d["thickness_px"] / 2
    d["y_bottom_px"] = d["center_px"] + d["thickness_px"] / 2
    return d


# ----------------------------------------------------------------- medidas
def correr(df, win_s):
    return cr.analizar(df, "center_px", None, win_s, None, 1.5, separar=False)


def resumen_corrida(a):
    return {
        "n_eventos": a["n_eventos"], "reportable": bool(a["conteo_reportable"]),
        "hay_meseta": bool(a["hay_meseta"]), "k_usado": round(float(a["k_usado"]), 3),
        "ruido_px": round(float(a["ruido_canal_px"]), 4),
        "win_s": round(float(a["win_s_usado"]), 2),
        "mesetas": a.get("mesetas"),
        "conteo_por_ventana": a.get("conteo_por_ventana"),
        "estable_ventana": bool(a.get("conteo_estable_ventana")),
        "motivo": a.get("motivo_no_reportable") or a.get("meseta_motivo"),
        "junto_al_borde": int(a.get("eventos_junto_al_borde", 0)),
    }


def quietos(t, picos_t, lejos=LEJOS_S):
    """Máscara de fotogramas lejos de cualquier evento (de los dos métodos)."""
    m = np.ones(len(t), bool)
    for x in picos_t:
        m &= np.abs(t - x) > lejos
    return m


def emparejar(ta, tb):
    """(i, j) de los eventos que coinciden en el tiempo, y los que sobran."""
    pares, usados = [], set()
    for i, x in enumerate(ta):
        if not len(tb):
            break
        j = int(np.argmin(np.abs(tb - x)))
        if abs(tb[j] - x) <= EMPAREJA_S and j not in usados:
            pares.append((i, j)); usados.add(j)
    solo_a = [i for i in range(len(ta)) if i not in {p[0] for p in pares}]
    solo_b = [j for j in range(len(tb)) if j not in usados]
    return pares, solo_a, solo_b


# ------------------------------------------------------------------ figura
def figura(nombre, t, rb, rt, ab, at, zoom, motivo, destino):
    import matplotlib
    matplotlib.use("Agg")
    from matplotlib.figure import Figure
    fig = Figure(figsize=(13, 5.6), dpi=130)
    for fila, (x0, x1, tit) in enumerate([(t[0], t[-1], "serie entera"),
                                          (zoom[0], zoom[1], f"zoom: {motivo}")]):
        ax = fig.add_subplot(2, 1, fila + 1)
        m = (t >= x0) & (t <= x1)
        ax.plot(t[m], rb[m], color="#1f77b4", lw=0.8, label="bordes (center_px)")
        ax.plot(t[m], rt[m], color="#d62728", lw=0.8, label="textura")
        for a, col, mk in ((ab, "#1f77b4", "v"), (at, "#d62728", "^")):
            p = a["_picos"]
            pm = (a["_t"][p] >= x0) & (a["_t"][p] <= x1)
            ax.plot(a["_t"][p][pm], a["_r"][p][pm], mk, color=col, ms=7, mfc="none")
        ax.axhline(0, color="#999", lw=0.5)
        ax.set_title(f"{nombre} · {tit}  (triángulos: eventos detectados por cada uno)",
                     fontsize=9)
        ax.set_ylabel("px sin deriva")
        ax.grid(alpha=0.25)
        if fila == 0:
            ax.legend(fontsize=8, loc="upper right")
        else:
            ax.set_xlabel("tiempo (s)")
    fig.tight_layout()
    fig.savefig(destino)
    return destino


# -------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--remedir", action="store_true")
    args = ap.parse_args()

    comp, vent, evs = [], [], []
    for carpeta, nombre, zoom, motivo in CASOS:
        print(f"\n=== {nombre} ===")
        df_bor, _ = serie_bordes(carpeta)
        tex = serie_textura(carpeta, nombre, args.remedir)
        df_tex = df_textura(df_bor, tex)

        ab, at = correr(df_bor, None), correr(df_tex, None)
        t = ab["_t"]
        rb, rt = ab["_r"], at["_r"][:len(t)]
        tb, tt = ab["_t"][ab["_picos"]], at["_t"][at["_picos"]]
        pares, solo_b, solo_t = emparejar(tb, tt)

        # ruido en los tramos quietos (lejos de TODOS los eventos de los dos)
        q = quietos(t, np.r_[tb, tt])
        ruido_b, ruido_t = float(mad(rb[q])), float(mad(rt[:len(t)][q]))
        # dónde difieren: la resta de las dos señales, en tramos de 1 s
        d = rt - rb
        umbral = 5 * float(mad(d[q]))
        seg = np.floor(t).astype(int)
        por_seg = pd.Series(np.abs(d)).groupby(seg).max()
        diferentes = [int(s) for s, v in por_seg.items() if v > umbral]

        fila = {
            "video": nombre, "motivo_mirado": motivo,
            "eventos_bordes": len(tb), "eventos_textura": len(tt),
            "emparejados": len(pares), "solo_bordes": len(solo_b), "solo_textura": len(solo_t),
            "reportable_bordes": bool(ab["conteo_reportable"]),
            "reportable_textura": bool(at["conteo_reportable"]),
            "ruido_quieto_bordes_px": round(ruido_b, 4),
            "ruido_quieto_textura_px": round(ruido_t, 4),
            "cociente_ruido": round(ruido_b / ruido_t, 2) if ruido_t else None,
            "umbral_diferencia_px": round(umbral, 4),
            "segundos_distintos": len(diferentes),
            "tramos_distintos_s": ", ".join(str(x) for x in diferentes[:25]) or "ninguno",
            "motivo_textura": at.get("motivo_no_reportable") or "reportable",
        }
        if pares:
            coc = np.array([at["_r"][at["_picos"]][j] / ab["_r"][ab["_picos"]][i] for i, j in pares])
            fila["ampl_textura_sobre_bordes"] = round(float(np.median(coc)), 3)
            fila["ampl_coc_min_max"] = f"{coc.min():.2f}-{coc.max():.2f}"
        comp.append(fila)
        print("  " + " | ".join(f"{k}={v}" for k, v in fila.items() if k != "tramos_distintos_s"))

        # eventos de cada método, emparejados
        for i, x in enumerate(tb):
            j = next((j for a, j in pares if a == i), None)
            evs.append({"video": nombre, "metodo": "bordes", "n": i + 1, "t_s": round(float(x), 3),
                        "amplitud_px": round(float(ab["_r"][ab["_picos"]][i]), 3),
                        "pareja_textura_s": round(float(tt[j]), 3) if j is not None else None})
        for j, x in enumerate(tt):
            i = next((i for i, b in pares if b == j), None)
            evs.append({"video": nombre, "metodo": "textura", "n": j + 1, "t_s": round(float(x), 3),
                        "amplitud_px": round(float(at["_r"][at["_picos"]][j]), 3),
                        "pareja_bordes_s": round(float(tb[i]), 3) if i is not None else None})

        # barrido de ventanas del detrend
        for win in (None,) + VENTANAS:
            for met, dfx in (("bordes", df_bor), ("textura", df_tex)):
                a = ab if (win is None and met == "bordes") else \
                    at if (win is None and met == "textura") else correr(dfx, win)
                r = resumen_corrida(a)
                r.update(video=nombre, metodo=met,
                         ventana="auto" if win is None else f"{win:g} s",
                         instantes_s=" ".join(f"{x:.2f}" for x in a["_t"][a["_picos"]][:40]))
                vent.append(r)
                print(f"   {met:8s} ventana {r['ventana']:>5s} -> {r['n_eventos']:3d} eventos, "
                      f"reportable {str(r['reportable']):5s}, meseta {str(r['hay_meseta']):5s}"
                      f"  k={r['k_usado']:.2f} ruido={r['ruido_px']:.4f}"
                      + (f"  [{r['motivo']}]" if not r["reportable"] else ""))

        figura(nombre, t, rb, rt, ab, at, zoom, motivo, AQUI / f"serie_{nombre}.png")

    pd.DataFrame(comp).to_csv(AQUI / "comparacion.csv", index=False)
    pd.DataFrame(vent).to_csv(AQUI / "ventanas.csv", index=False)
    pd.DataFrame(evs).to_csv(AQUI / "eventos.csv", index=False)
    print("\ntablas: comparacion.csv, ventanas.csv, eventos.csv; figuras: serie_<video>.png")


if __name__ == "__main__":
    main()
