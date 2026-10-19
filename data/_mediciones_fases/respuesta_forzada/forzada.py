"""Respuesta FORZADA a una frecuencia conocida (2026-10-19). Solo medición: no toca el análisis.

Idea: si se sabe cada cuánto dispara el estimulador, no hace falta DETECTAR cada
contracción: se mide la señal en cada instante esperado de pulso y se compara con
la misma medida en instantes donde no hay pulso (controles). Reglas fijadas ANTES
de mirar los videos no reportables:

  1. Señal: center_px sin deriva (mediana móvil de 2 s, src/estadistica).
  2. Período T fijo (videos de Andrés: 10.10 s, el medido en los 4 reportables;
     videos con timestamps reales: 10.00 s).
  3. Fase y sentido: el pico de la señal plegada a T (desde 8 s). Prueba de que hay
     respuesta: el mismo plegado a 40 períodos de control (0.55-1.75 T, lejos de T,
     T/2 y 2T); p = (1 + controles con SNR >= la de T) / 41.
  4. Por pulso: amplitud = pico (en el sentido del paso 3) en t_n +-0.2 s menos la
     mediana de [t_n-1.2, t_n-0.4] s. Lo mismo en instantes de control (t_n + 2..8 s,
     cada 0.5 s). Un pulso "responde" si su amplitud supera el percentil 95 de los
     controles.

    python data/_mediciones_fases/respuesta_forzada/forzada.py
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(RAIZ))
from src.estadistica import detrend_median  # noqa: E402
from src.forzado_util import plegar, _snr  # noqa: E402

P = RAIZ / "data" / "processed_data"
VIDEOS = [  # carpeta, T (s), resultado del reporte normal (textura, achicado)
    ("10V_1", 10.10, "6, reportable, 1.16 px"), ("10V_2", 10.10, "NO REPORTABLE"),
    ("10V_3", 10.10, "NO REPORTABLE (sacudida)"), ("20V_1", 10.10, "NO REPORTABLE"),
    ("20V_2", 10.10, "NO REPORTABLE"), ("20V_3", 10.10, "6, reportable, 1.64 px"),
    ("40V_1", 10.10, "5, reportable, 1.67 px"), ("40V_2", 10.10, "NO REPORTABLE"),
    ("40V_3", 10.10, "6, reportable, 0.76 px"),
    # controles negativos ya medidos (B7: sin respuesta a 0.1 Hz) y uno positivo por bordes
    ("Video_613", 10.00, "control: sin respuesta (B7)"), ("Video_068_hw30", 10.00, "control: sin respuesta (B7)"),
    ("Video_063_CTRL1_5V", 10.00, "6, reportable (bordes)"),
]
CONTROLES = np.r_[np.linspace(0.55, 0.9, 20), np.linspace(1.15, 1.75, 20)]  # x T


def leer(c):
    s = next((P / c).glob("serie_temporal_*.xlsx"))
    h = pd.read_excel(s, sheet_name=None)
    d = h["diagnostics"]
    meta = dict(zip(h["resumen"].iloc[:, 0].astype(str), h["resumen"].iloc[:, 1]))
    g = float(meta.get("grosor medio (px)", np.nan))
    if not np.isfinite(g):
        g = float(np.nanmedian(d["thickness_px"]))
    return d["time_s"].to_numpy(float), d["center_px"].to_numpy(float), g


def amp_en(t, r, t0, sg):
    w = (t >= t0 - 0.2) & (t <= t0 + 0.2)
    b = (t >= t0 - 1.2) & (t <= t0 - 0.4)
    if w.sum() < 3 or b.sum() < 5:
        return np.nan
    return float(np.nanmax(sg * r[w]) - np.nanmedian(sg * r[b]))


def medir(c, T):
    t, x, grosor = leer(c)
    fps = 1 / np.median(np.diff(t))
    r = detrend_median(x, fps, 2.0)
    pl = plegar(t, r, T)
    snr = _snr(pl)
    ctrl = np.array([_snr(plegar(t, r, T * f)) for f in CONTROLES])
    p = (1 + np.sum(ctrl >= snr)) / (len(ctrl) + 1)
    med = np.nanmedian(pl)
    i = int(np.nanargmax(np.abs(pl - med)))
    sg = np.sign(pl[i] - med)
    dt = np.median(np.diff(t))
    fase = i * dt
    tn = np.arange(fase, t[-1], T)
    tn = tn[(tn >= 8.0) & (tn <= t[-1] - 0.5)]
    a = np.array([amp_en(t, r, x0, sg) for x0 in tn])
    tc = np.array([x0 + o for x0 in tn for o in np.arange(2.0, 8.01, 0.5) if x0 + o <= t[-1] - 0.5])
    ac = np.array([amp_en(t, r, x0, sg) for x0 in tc])
    ac = ac[np.isfinite(ac)]
    u95 = float(np.percentile(ac, 95))
    resp = int(np.sum(a > u95))
    return dict(video=c, T=T, snr=snr, snr_ctrl_max=float(np.max(ctrl)), p=p,
                sentido="abajo" if sg > 0 else "arriba", fase_s=round(fase, 2),
                pulsos=len(tn), responden=resp, ampl_px=float(np.nanmedian(a)),
                ampl_pct=100 * float(np.nanmedian(a)) / grosor,
                ctrl_p95_px=u95, ctrl_mediana_px=float(np.median(ac)),
                amps=" ".join(f"{v:.2f}" for v in a))


def main():
    filas = []
    for c, T, nota in VIDEOS:
        if not (P / c).is_dir():
            print(f"{c}: no está"); continue
        m = medir(c, T); m["reporte_normal"] = nota; filas.append(m)
        print(f"{c:20s} SNR {m['snr']:5.1f} (controles max {m['snr_ctrl_max']:5.1f}) p={m['p']:.3f} | "
              f"{m['responden']}/{m['pulsos']} pulsos > p95 ctrl ({m['ctrl_p95_px']:.2f} px) | "
              f"ampl {m['ampl_px']:.2f} px = {m['ampl_pct']:.3f} % | {m['sentido']} | {nota}")
        print(f"{'':20s} por pulso: {m['amps']}")
    pd.DataFrame(filas).to_csv(Path(__file__).with_name("forzada.csv"), index=False)


if __name__ == "__main__":
    main()
