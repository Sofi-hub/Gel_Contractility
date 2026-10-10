"""B1 (resto): ¿qué es el "otro gradiente" a ~15 px del borde en 466?

Con ±15 px, en el 12 % de los fotogramas de 466 algún borde queda pegado al
límite de la ventana; con ±30 el borde salta a otra estructura (el grosor pasa de
201 a 191 px y los eventos de 5 a 2). Este script solo mira, no cambia nada:

  - Usa la misma ROI, las mismas columnas y el mismo CLAHE que main.py.
  - En 1 de cada 5 fotogramas, para cada columna y cada borde, toma el gradiente
    (con la polaridad del borde) en guía ± 40 px y busca TODOS los máximos locales
    por encima de min_gradient (5).
  - Para cada borde: dónde caen los máximos respecto de la guía (histograma),
    cuál es el principal, a qué distancia está el segundo y de qué lado (hacia
    adentro del gel o hacia afuera), cuán fuerte es comparado con el principal,
    y si se mueve junto con el borde (correlación de su posición con center_px).
  - Figura: gradiente promedio alrededor de cada borde, y la imagen con las
    ventanas ±15 y ±30 dibujadas.

    python data/_mediciones_fases/b1_gradiente_466/medir_b1_466.py [carpeta_de_referencia]
"""
from __future__ import annotations

import sys
from pathlib import Path

import cv2
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.signal import find_peaks

RAIZ = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "tests"))
import referencia as ref                                     # noqa: E402
from src import io_utils, preprocessing as pp                # noqa: E402
from src.output_paths import buscar_serie                    # noqa: E402

AQUI = Path(__file__).resolve().parent
CARPETA = sys.argv[1] if len(sys.argv) > 1 else "Video_466_EXP5_FAPS4_40V"
VIDEO = ref.CRUDOS / ref.VIDEOS[CARPETA][0]
HW = 40
STRIDE = 5


def main():
    _, mp = io_utils.read_pts_and_max_projection(str(VIDEO), stride=5)
    roi = pp.auto_detect_roi(mp)
    n = pp._n_columnas(roi["x_start"], roi["x_end"], 60, 40, 3.0) if hasattr(pp, "_n_columnas") else 60
    n = n if isinstance(n, int) else 60
    xs = np.linspace(roi["x_start"], roi["x_end"] - 1, n).astype(int)
    tg = roi["top_guess"][xs].astype(int)
    bg = roi["bottom_guess"][xs].astype(int)
    serie = pd.read_excel(buscar_serie(RAIZ / "data" / "processed_data" / CARPETA),
                          sheet_name="diagnostics").set_index("frame")
    print(f"{CARPETA}: ROI {roi['x_start']}-{roi['x_end']}, {n} columnas")

    picos = []                       # (frame, borde, col, offset, valor, es_principal15)
    gsum = {"sup": np.zeros(2 * HW), "inf": np.zeros(2 * HW)}
    ng = 0
    for idx, frame in io_utils.frame_generator(str(VIDEO)):
        if idx % STRIDE:
            continue
        f = pp.preprocess_frame(frame, use_clahe=True).astype(np.float64)
        for nom, guia, pol in (("sup", tg, 1), ("inf", bg, -1)):
            for j, (x, g) in enumerate(zip(xs, guia)):
                a, b = g - HW, g + HW
                if a < 1 or b > f.shape[0] - 1:
                    continue
                gr = np.gradient(f[a:b, x]) * pol
                gsum[nom] += gr
                pk, pr = find_peaks(gr, height=5.0)
                # el que elige el pipeline con +-15: maximo en [g-15, g+15)
                w15 = gr[HW - 15:HW + 15]
                elegido = HW - 15 + int(np.argmax(w15))
                for p in pk:
                    picos.append((idx, nom, j, p - HW, gr[p], p == elegido))
        ng += 1
    gsum = {k: v / (ng * len(xs)) for k, v in gsum.items()}
    df = pd.DataFrame(picos, columns=["frame", "borde", "col", "offset_px", "grad", "elegido15"])
    df.to_csv(AQUI / f"picos_{CARPETA}.csv.gz", index=False)

    filas = []
    for nom in ("sup", "inf"):
        d = df[df.borde == nom]
        # hacia adentro del gel = +offset en el sup, -offset en el inf
        dentro = d.offset_px * (1 if nom == "sup" else -1)
        hist = dentro.round().value_counts().sort_index()
        modos = hist[hist > 0.05 * hist.max()]
        # segundo maximo de cada (frame, col): el mas fuerte que NO es el elegido
        sec = (d[~d.elegido15].sort_values("grad", ascending=False)
               .groupby(["frame", "col"]).head(1))
        pri = d[d.elegido15].set_index(["frame", "col"])
        sec = sec.set_index(["frame", "col"])
        com = sec.join(pri, lsuffix="_2", rsuffix="_1", how="inner")
        com["dentro_2"] = com.offset_px_2 * (1 if nom == "sup" else -1)
        com["dentro_1"] = com.offset_px_1 * (1 if nom == "sup" else -1)
        com["sep"] = com.dentro_2 - com.dentro_1
        com["cociente"] = com.grad_2 / com.grad_1
        fuertes = com[com.cociente > 0.5]
        # se mueve con el borde? posicion media del 2.o por fotograma vs center_px
        pf = fuertes.groupby(level=0).offset_px_2.median()
        cc = serie["center_px"].reindex(pf.index)
        rho = float(np.corrcoef(pf, cc)[0, 1]) if len(pf) > 30 else np.nan
        pf1 = com.groupby(level=0).offset_px_1.median()
        rho1 = float(np.corrcoef(pf1, serie["center_px"].reindex(pf1.index))[0, 1])
        lim = d[d.elegido15 & (d.offset_px.abs() >= 13)]
        filas.append({
            "borde": nom,
            "pico_principal_hacia_adentro_px_mediana": float(com.dentro_1.median()),
            "segundo_hacia_adentro_px_mediana": float(com.dentro_2.median()),
            "separacion_px_mediana": float(com.sep.median()),
            "separacion_px_IQR": f"{com.sep.quantile(.25):.0f}..{com.sep.quantile(.75):.0f}",
            "cociente_2o_1o_mediana": float(com.cociente.median()),
            "pct_col_fotog_con_2o_mayor_mitad": 100 * len(fuertes) / max(len(pri), 1),
            "sep_px_mediana_cuando_fuerte": float(fuertes.sep.median()) if len(fuertes) else np.nan,
            "corr_pos_2o_con_center_px": rho,
            "corr_pos_1o_con_center_px": rho1,
            "pct_elegidos15_a_13px_o_mas": 100 * len(lim) / max(len(pri), 1),
            "modos_hacia_adentro_px": ", ".join(f"{int(k)}" for k in modos.index[:40]),
        })
    tab = pd.DataFrame(filas)
    tab.to_csv(AQUI / f"tabla_b1_{CARPETA}.csv", index=False)
    print(tab.T.to_string())

    # figura
    fig, ax = plt.subplots(1, 3, figsize=(15, 4.5))
    off = np.arange(-HW, HW)
    for k, nom in enumerate(("sup", "inf")):
        dentro = off * (1 if nom == "sup" else -1)
        o = np.argsort(dentro)
        ax[k].plot(dentro[o], gsum[nom][o], color="k")
        ax[k].axvspan(-15, 15, color="tab:green", alpha=0.12, label="ventana ±15")
        ax[k].axvspan(-30, 30, color="tab:orange", alpha=0.08, label="±30")
        ax[k].set_xlabel("px desde la guía (+ = hacia adentro del gel)")
        ax[k].set_ylabel("gradiente medio (con polaridad)")
        ax[k].set_title(f"{CARPETA}: borde {nom}"); ax[k].legend(fontsize=7)
    xm = int(np.median(xs))
    y0 = max(0, int(tg.min()) - 80); y1 = min(mp.shape[0], int(bg.max()) + 80)
    crop = mp[y0:y1, max(0, xm - 250):xm + 250]
    ax[2].imshow(crop, cmap="gray", aspect="auto")
    xx = np.arange(crop.shape[1]) + max(0, xm - 250)
    for gg, c in ((roi["top_guess"], "c"), (roi["bottom_guess"], "m")):
        for w, ls in ((15, "-"), (30, ":")):
            ax[2].plot(xx - xx[0], gg[xx] - y0 - w, c, ls=ls, lw=0.7)
            ax[2].plot(xx - xx[0], gg[xx] - y0 + w, c, ls=ls, lw=0.7)
    ax[2].set_title("mapa de máximos: ventanas ±15 (—) y ±30 (···)")
    fig.tight_layout(); fig.savefig(AQUI / f"b1_{CARPETA}.png", dpi=120)


if __name__ == "__main__":
    main()
