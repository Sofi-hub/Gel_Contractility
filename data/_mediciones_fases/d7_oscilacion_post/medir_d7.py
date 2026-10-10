"""D7: ¿la oscilación chica después de cada contracción (vista en 476) se repite
en otros videos?

Solo lee resultados vigentes (serie_temporal y contracciones); no cambia nada.

Para cada video reportable:
  1. center_px sin deriva (la misma mediana móvil y ventana que usó el reporte,
     `win_s_usado`), con el signo del video (contracción hacia +).
  2. Eventos AISLADOS: sin otro evento 1.5 s antes del inicio ni 3 s después del
     final (`offset_s` de la hoja cinetica).
  3. Promedio alineado al FINAL de cada evento, en una grilla de 1/30 s. Una
     oscilación que se repite en cada contracción con la misma forma sobrevive al
     promedio; el ruido baja como 1/sqrt(N).
  4. Se compara el tramo [final, final + 2.5 s] con un tramo quieto
     [inicio - 1.5 s, inicio - 0.2 s]:
       rms_post / rms_pre  (en el promedio y evento a evento)
       pico a pico del promedio después del final, en px y en "sigmas del
       promedio" (ruido del video / sqrt(N))
       frecuencia dominante del tramo post (FFT del promedio, sin la media)

    python data/_mediciones_fases/d7_oscilacion_post/medir_d7.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

RAIZ = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(RAIZ))
from src.estadistica import detrend_median, mad   # noqa: E402
from src.output_paths import buscar_serie         # noqa: E402

AQUI = Path(__file__).resolve().parent
P = RAIZ / "data" / "processed_data"
VIDEOS = ["Video_prueba", "Video_063_CTRL1_5V", "Video_268_EXP3_FAPS2_40V",
          "Video_466_EXP5_FAPS4_40V", "Video_476", "Video_583_EXP6_CTRL4_40V",
          "Video_491_EXP5_CTRL1_36HZ"]
DT = 1 / 30
POST = 2.5
PRE = (-1.5, -0.2)


def hoja(h, pref):
    return next(v for k, v in h.items() if k.startswith(pref + "_"))


def main():
    filas = []
    fig, axs = plt.subplots(len(VIDEOS), 1, figsize=(9, 2.1 * len(VIDEOS)), sharex=True)
    for ax, v in zip(axs, VIDEOS):
        h = pd.read_excel(next((P / v).glob("contracciones_*.xlsx")), sheet_name=None)
        res = hoja(h, "resumen").iloc[0]
        cin = hoja(h, "cinetica")
        d = pd.read_excel(buscar_serie(P / v), sheet_name="diagnostics")
        t = d["time_s"].to_numpy(float)
        fps = 1 / np.median(np.diff(t))
        s = res["signo"] * detrend_median(d["center_px"].to_numpy(float), fps,
                                          float(res["win_s_usado"]))
        ruido = mad(s)
        on, off = cin["onset_s"].to_numpy(float), cin["offset_s"].to_numpy(float)
        iso = []
        for i in range(len(cin)):
            if not (np.isfinite(on[i]) and np.isfinite(off[i])):
                continue
            prev_ok = i == 0 or off[i - 1] < on[i] + PRE[0]
            next_ok = i == len(cin) - 1 or on[i + 1] > off[i] + POST + 0.5
            if prev_ok and next_ok and off[i] + POST < t[-1] and on[i] + PRE[0] > t[0]:
                iso.append(i)
        g_post = np.arange(-0.5, POST + 1e-9, DT)
        g_pre = np.arange(PRE[0], PRE[1] + 1e-9, DT)
        ok = np.isfinite(s)
        P_post = np.array([np.interp(off[i] + g_post, t[ok], s[ok]) for i in iso])
        P_pre = np.array([np.interp(on[i] + g_pre, t[ok], s[ok]) for i in iso])
        n = len(iso)
        fila = {"video": v, "n_eventos": len(cin), "n_aislados": n, "ruido_px": ruido,
                "amplitud_mediana_px": float(np.median(cin["amplitud_px"]))}
        if n >= 3:
            m_post = P_post.mean(0)[g_post >= 0]
            m_pre = P_pre.mean(0)
            rms = lambda x: float(np.sqrt(np.mean((x - x.mean()) ** 2)))
            sig_prom = ruido / np.sqrt(n)
            spec = np.abs(np.fft.rfft(m_post - m_post.mean()))
            fr = np.fft.rfftfreq(len(m_post), DT)
            fila.update(
                rms_post_prom_px=rms(m_post), rms_pre_prom_px=rms(m_pre),
                cociente_prom=rms(m_post) / max(rms(m_pre), 1e-12),
                pp_post_prom_px=float(np.ptp(m_post)),
                pp_post_prom_sigmas=float(np.ptp(m_post) / sig_prom),
                pp_post_sobre_amplitud_pct=100 * float(np.ptp(m_post)) / fila["amplitud_mediana_px"],
                cociente_por_evento_mediana=float(np.median(
                    [rms(a[g_post >= 0]) / max(rms(b), 1e-12) for a, b in zip(P_post, P_pre)])),
                frecuencia_dominante_post_Hz=float(fr[1:][np.argmax(spec[1:])]),
            )
            ax.plot(g_post, P_post.T, color="0.8", lw=0.5)
            ax.plot(g_post, P_post.mean(0), color="crimson", lw=1.3, label=f"promedio de {n}")
            ax.plot(g_pre - 0.0, np.full_like(g_pre, np.nan))
            ax.axhspan(-2 * sig_prom, 2 * sig_prom, color="steelblue", alpha=0.15,
                       label="±2σ del promedio")
            ax.set_ylim(-max(0.6, 4 * ruido), max(0.6, 4 * ruido))
        ax.axvline(0, color="k", lw=0.6)
        ax.set_title(f"{v}: center_px sin deriva, alineado al FINAL de cada evento aislado",
                     fontsize=8)
        ax.set_ylabel("px"); ax.legend(fontsize=6, loc="upper right")
        filas.append(fila)
        print({k: (round(x, 4) if isinstance(x, float) else x) for k, x in fila.items()}, flush=True)
    axs[-1].set_xlabel("tiempo desde el final del evento (s)")
    fig.tight_layout(); fig.savefig(AQUI / "d7_post_evento.png", dpi=120)
    df = pd.DataFrame(filas)
    df.to_csv(AQUI / "tabla_d7.csv", index=False)
    print(df.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
