"""B7, parte 2: promedio de la senal PLEGADA al periodo del estimulador (10 s).
No usa eventos detectados: si cada pulso deja una respuesta, aunque sea chica,
al promediar los ~5 tramos de 10 s alineados aparece un pico; con periodos de
control (que no son el del estimulador) no deberia aparecer.

SNR = (maximo del perfil plegado - su mediana) / ruido del perfil, con
ruido = 1.4826*MAD del perfil. Se miran los dos sentidos (|.|). Solo desde 8 s
(la basal 0-10 s no tiene estimulo; 8 s por margen).

    python data/_mediciones_fases/b7_dirigida_613_068/plegado.py
"""
from __future__ import annotations
import sys, warnings
from pathlib import Path
import numpy as np
import pandas as pd
RAIZ = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(RAIZ)); sys.path.insert(0, str(RAIZ / "scripts")); sys.path.insert(0, str(RAIZ / "tests"))
import contraction_report as cr  # noqa: E402
from referencia import PROCESADOS, leer_serie  # noqa: E402
from src.output_paths import buscar_serie  # noqa: E402
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

VIDEOS = ["Video_063_CTRL1_5V", "Video_268_EXP3_FAPS2_40V", "Video_466_EXP5_FAPS4_40V",
          "Video_583_EXP6_CTRL4_40V", "Video_476", "Video_613", "Video_068_hw30"]
CONTROLES = [7.3, 8.1, 8.9, 11.3, 12.1, 13.7]
DT = 1 / 30


def plegar(t, r, T):
    m = np.isfinite(r) & (t >= 8.0)
    fase = np.mod(t[m], T)
    nb = int(round(T / DT))
    idx = np.minimum((fase / DT).astype(int), nb - 1)
    s = np.bincount(idx, weights=r[m], minlength=nb)
    c = np.bincount(idx, minlength=nb)
    return np.where(c > 0, s / np.maximum(c, 1), np.nan), int(np.median(c))


def snr(p):
    p = p[np.isfinite(p)]
    med = np.median(p)
    ruido = 1.4826 * np.median(np.abs(p - med))
    return float(np.max(np.abs(p - med)) / ruido) if ruido > 0 else np.nan


filas = []
fig, axes = plt.subplots(len(VIDEOS), 1, figsize=(9, 2.0 * len(VIDEOS)))
for ax, carpeta in zip(axes, VIDEOS):
    df, _ = leer_serie(buscar_serie(PROCESADOS / carpeta))
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        a = cr.analizar(df, "center_px", None, None, None, 1.5, frecuencia_estimulo=[0.1])
    t, r = np.asarray(a["_t"], float), np.asarray(a["_r"], float)
    p10, n = plegar(t, r, 10.0)
    s10 = snr(p10)
    sc = [snr(plegar(t, r, T)[0]) for T in CONTROLES]
    # el periodo real puede no ser exactamente 10.000 s: barrido fino 9.98-10.02
    fino = max(snr(plegar(t, r, T)[0]) for T in np.arange(9.98, 10.0201, 0.002))
    grosor = float(np.nanmedian(df["thickness_px"]))
    amp = float(np.nanmax(np.abs(p10 - np.nanmedian(p10))))
    filas.append({"video": carpeta, "tramos_promediados": n, "SNR a 10 s": round(s10, 1),
                  "SNR max 9.98-10.02 s": round(fino, 1),
                  "SNR controles (min-max)": f"{min(sc):.1f}-{max(sc):.1f}",
                  "pico del plegado (px)": round(amp, 3), "pico (% grosor)": round(100 * amp / grosor, 3)})
    print(filas[-1], flush=True)
    ax.plot(np.arange(len(p10)) * DT, p10, lw=0.8)
    ax.set_title(f"{carpeta}: plegado a 10 s (SNR {s10:.1f}; controles {min(sc):.1f}-{max(sc):.1f})", fontsize=8)
    ax.tick_params(labelsize=7)
axes[-1].set_xlabel("fase dentro del periodo de 10 s (s)")
fig.tight_layout()
fig.savefig(Path(__file__).with_name("plegado_10s.png"), dpi=110)
pd.DataFrame(filas).to_csv(Path(__file__).with_name("tabla_plegado.csv"), index=False)
