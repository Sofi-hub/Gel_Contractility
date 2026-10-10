"""D3: en Video_063, ¿la contracción espontánea de 0.31 s es local?

La ROI vigente de 063 es angosta (875-1039, la zona plana). A ojo el evento de
0.31 s no parece tan chico como lo mide esa zona. Acá se mide la amplitud de cada
evento en TRAMOS a lo largo de todo el gel, con el mismo método del pipeline
(process_frame: CLAHE, borde subpíxel, RANSAC grado 2 con umbral adaptativo),
pero cada tramo con sus propias 40 columnas. No cambia nada del análisis.

  - Tramos de 120 px (el ancho mínimo de una ROI) en las columnas donde la
    franja del gel se pudo seguir y los dos bordes son nítidos (>= 10), sin
    pisarse, de punta a punta del gel.
  - Para cada tramo: center_px por fotograma, sin deriva (mediana móvil con la
    ventana del reporte), y la amplitud de cada uno de los 6 eventos del reporte
    = máximo en ±3 fotogramas del pico menos la mediana de [-1.0, -0.3] s antes
    (para el de 0.31 s, de [0, 0.15] s: no hay 1 s antes).
  - Cociente evento 0.31 s / mediana de los otros 5, por tramo. Si el evento es
    del gel entero, el cociente es parecido en todos los tramos.

    python data/_mediciones_fases/d3_amplitud_tramos/medir_d3.py [carpeta]
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[2]
sys.path.insert(0, str(RAIZ)); sys.path.insert(0, str(RAIZ / "tests"))
import referencia as ref                                     # noqa: E402
from src import io_utils, preprocessing as pp                # noqa: E402
from src.pipeline import PipelineConfig, process_frame       # noqa: E402
from src.estadistica import detrend_median, mad              # noqa: E402
from src.output_paths import buscar_serie                    # noqa: E402

CARPETA = sys.argv[1] if len(sys.argv) > 1 else "Video_063_CTRL1_5V"
ANCHO, NCOL = 120, 40


def main():
    video = ref.CRUDOS / ref.VIDEOS[CARPETA][0]
    pts, mp = io_utils.read_pts_and_max_projection(str(video), stride=5)
    roi = pp.auto_detect_roi(mp)
    ok = roi["valid_columns"] & np.isfinite(roi["sharpness_profile"]) & (roi["sharpness_profile"] >= 10)
    T = roi["thickness_profile"]
    med = np.nanmedian(T[ok])
    ok &= (T > 0.6 * med) & (T < 1.6 * med)
    tramos, x = [], 0
    while x + ANCHO <= len(ok):
        if ok[x:x + ANCHO].all():
            tramos.append((x, x + ANCHO)); x += ANCHO
        else:
            x += 4
    # el tramo de la ROI vigente, para calibrar contra el reporte
    tramos.append((roi["x_start"], roi["x_end"]))
    print(f"{CARPETA}: ROI {roi['x_start']}-{roi['x_end']}, {len(tramos) - 1} tramos de {ANCHO} px:",
          tramos[:-1], flush=True)
    cfg = PipelineConfig()
    xs = [np.linspace(a, b - 1, NCOL if (a, b) != tramos[-1] else
                      int(roi["roi_quality"]["n_columnas_usadas"])).astype(int) for a, b in tramos]
    C = np.full((len(pts), len(tramos)), np.nan)
    G = np.full((len(pts), len(tramos)), np.nan)
    for idx, frame in io_utils.frame_generator(str(video)):
        for j, x_ in enumerate(xs):
            r = process_frame(frame, x_, roi["top_guess"], roi["bottom_guess"], cfg)
            C[idx, j] = r["center_px"]; G[idx, j] = r["thickness_px"]
        if idx % 300 == 0:
            print(f"  {idx} fotogramas", flush=True)
    t = pts - pts[0]
    np.savez_compressed(AQUI / f"centros_{CARPETA}.npz", C=C, G=G, t=t, tramos=np.array(tramos))

    h = pd.read_excel(next((RAIZ / "data/processed_data" / CARPETA).glob("contracciones_*.xlsx")),
                      sheet_name=None)
    res = next(v for k, v in h.items() if k.startswith("resumen_")).iloc[0]
    cin = next(v for k, v in h.items() if k.startswith("cinetica_"))
    ref_serie = pd.read_excel(buscar_serie(RAIZ / "data/processed_data" / CARPETA), sheet_name="diagnostics")
    print("calibracion: tramo ROI == center_px vigente:",
          np.allclose(C[:, -1], ref_serie.center_px.to_numpy(), atol=1e-3, equal_nan=True))
    fps = 1 / np.median(np.diff(t))
    filas = []
    for j, (a, b) in enumerate(tramos):
        s = res["signo"] * detrend_median(C[:, j], fps, float(res["win_s_usado"]))
        fila = {"tramo": f"{a}-{b}" + (" (ROI)" if j == len(tramos) - 1 else ""),
                "x_centro": (a + b) / 2, "grosor_px": float(np.nanmedian(G[:, j])),
                "ruido_px": mad(s)}
        amps = []
        for _, e in cin.iterrows():
            i = int(e["frame_pico"])
            pre = (t >= t[i] - 1.0) & (t <= t[i] - 0.3)
            if pre.sum() < 5:
                pre = t <= 0.15
            w = slice(max(0, i - 3), i + 4)
            amps.append(float(np.nanmax(s[w]) - np.nanmedian(s[pre])))
        for k, (a_, e) in enumerate(zip(amps, cin.itertuples())):
            fila[f"ev{k + 1}_{e.tiempo_s:.2f}s"] = a_
        otros = np.median(amps[1:])
        fila["ev1_sobre_otros"] = amps[0] / otros
        fila["otros_pct_grosor"] = 100 * otros / fila["grosor_px"]
        fila["ev1_pct_grosor"] = 100 * amps[0] / fila["grosor_px"]
        filas.append(fila)
    df = pd.DataFrame(filas)
    df.to_csv(AQUI / f"tabla_d3_{CARPETA}.csv", index=False)
    print(df.round(3).to_string(index=False))

    fig, ax = plt.subplots(2, 1, figsize=(10, 7))
    d = df.iloc[:-1]
    ax[0].plot(d.x_centro, d.ev1_pct_grosor, "o-", label="evento de 0.31 s")
    ax[0].plot(d.x_centro, d.otros_pct_grosor, "s-", label="mediana de los otros 5")
    ax[0].axvspan(roi["x_start"], roi["x_end"], color="0.85", label="ROI vigente")
    ax[0].set_ylabel("amplitud (% del grosor)"); ax[0].legend(fontsize=8)
    ax[0].set_title(f"{CARPETA}: amplitud de cada evento a lo largo del gel")
    ax[1].plot(d.x_centro, d.ev1_sobre_otros, "o-k")
    ax[1].axvspan(roi["x_start"], roi["x_end"], color="0.85")
    ax[1].set_ylabel("evento 0.31 s / otros"); ax[1].set_xlabel("columna (px)")
    fig.tight_layout(); fig.savefig(AQUI / f"d3_{CARPETA}.png", dpi=120)


if __name__ == "__main__":
    main()
