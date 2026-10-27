"""Respuesta forzada (src/forzada.py, 2026-10-19).

Sintéticos (ruido blanco de 0.3 px por fotograma): (a) pulsos de 5 x ruido cada
10.1 s -> hay respuesta y la amplitud sale a +-20 %; (a') pulsos de 3 x ruido -> hay
respuesta (la amplitud sale ~10-30 % alta: el pico de la ventana agarra ruido); (b) solo ruido ->
no hay respuesta; (c) ruido con sacudidas al azar hacia los dos lados -> no hay.

CINETICA DE LA RESPUESTA AL ESTIMULO (2026-10-27), pulso a pulso: (d) pulsos
sintéticos de cinética CONOCIDA (subida de 0.2 s, caída con tau 0.25 s: TTP 180 ms,
RT50 173 ms) -> la mediana los recupera a +-20 %; (e) pulsos rápidos (subida de
1 fotograma) -> no se informa valor, solo la cota; (f) en los videos REPORTABLES
466 y 583, la mediana pulso a pulso coincide con el TTP/RT50 del reporte dentro
del 5 % (es la comprobación que justifica usarla en los NO REPORTABLES).

    python tests/test_forzada.py
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.forzada import respuesta_forzada  # noqa: E402

FPS, DUR, T = 30.0, 68.0, 10.1


def serie(seed, amp=0.0, sacudidas=0):
    rng = np.random.default_rng(seed)
    t = np.arange(int(FPS * DUR)) / FPS
    x = rng.normal(0, 0.3, len(t)) + 0.02 * t
    forma = lambda s: np.where(s < 0, 0, np.where(s < 0.1, s / 0.1, np.exp(-(s - 0.1) / 0.3)))
    for n in range(1, 7):
        x = x + amp * forma(t - (0.7 + n * T))
    for _ in range(sacudidas):
        t0 = rng.uniform(5, DUR - 2)
        x = x + rng.choice([-1, 1]) * 2.0 * forma(t - t0)
    return t, x


# ---- cinetica de la respuesta al estimulo (2026-10-27), pulso a pulso ----
# De la forma de `serie_lenta`: onset = 10 % de A sobre la rampa, TTP = 0.9 * subida,
# RT50 = tau * ln 2. Lo medido queda unos puntos por debajo porque el pico es el
# PRIMER fotograma que llega al 95 % (B6) y la mediana movil de 2 s recorta algo de
# la cola: por eso la tolerancia es del 20 %, no del 5 %. Una forma mas lenta (tau
# 0.4 s) se sale de la regla del detrend (ventana >= 3 x el evento) y da -20 %.
TTP_REAL_MS, RT50_REAL_MS = 180.0, 173.0


def serie_lenta(seed, subida_s=0.2, tau_s=0.25, amp=3.0):
    """Pulsos de cinetica CONOCIDA: rampa lineal de `subida_s` y caida exponencial.
    onset = 10 % de A -> TTP = 0.9 * subida_s; RT50 = tau_s * ln 2."""
    rng = np.random.default_rng(seed)
    t = np.arange(int(FPS * DUR)) / FPS
    x = rng.normal(0, 0.05, len(t)) + 0.02 * t
    forma = lambda s: np.where(s < 0, 0.0,
                               np.where(s < subida_s, s / subida_s,
                                        np.exp(-np.clip(s - subida_s, 0, None) / tau_s)))
    for n in range(1, 7):
        x = x + amp * forma(t - (0.7 + n * T))
    return t, x


def probar_cinetica():
    fallos = []
    for seed in range(5):
        t, x = serie_lenta(seed)
        m = respuesta_forzada(t, x, 1000.0, 10.0)
        ok = (m.get("forzada_ttp_reportable") and m.get("forzada_rt50_reportable")
              and abs(m["forzada_ttp_ms"] / TTP_REAL_MS - 1) <= 0.20
              and abs(m["forzada_rt50_ms"] / RT50_REAL_MS - 1) <= 0.20)
        print(f"  cinetica conocida (seed {seed}): TTP {m.get('forzada_ttp_ms', float('nan')):.0f} ms "
              f"(real {TTP_REAL_MS:.0f}), RT50 {m.get('forzada_rt50_ms', float('nan')):.0f} ms "
              f"(real {RT50_REAL_MS:.0f})  {'OK' if ok else 'FALLA'}")
        if not ok:
            fallos.append(f"cinetica conocida seed {seed}")

    # pulsos rapidos: a 30 fps no se mide, solo la cota (hallazgo 5 de CLAUDE.md)
    t, x = serie_lenta(0, subida_s=1 / FPS, tau_s=0.05)
    m = respuesta_forzada(t, x, 1000.0, 10.0)
    ok = not m.get("forzada_ttp_reportable") and np.isfinite(m.get("forzada_ttp_cota_ms", np.nan))
    print(f"  pulsos rapidos: TTP no reportable, cota {m.get('forzada_ttp_cota_ms'):.0f} ms"
          f"  {'OK' if ok else 'FALLA'}")
    if not ok:
        fallos.append("pulsos rapidos: deberia dar solo la cota")
    return fallos


def probar_contra_reporte():
    """En los videos REPORTABLES la mediana pulso a pulso tiene que dar lo mismo
    que el TTP/RT50 que ya informa el reporte (dentro del 5 %)."""
    import pandas as pd
    P = Path(__file__).resolve().parents[1] / "data" / "processed_data"
    fallos = []
    for carpeta in ("Video_466_EXP5_FAPS4_40V", "Video_583_EXP6_CTRL4_40V"):
        d = P / carpeta
        series = sorted(d.glob("serie_temporal_*.xlsx"))
        contr = sorted(d.glob("contracciones_*.xlsx"))
        if not series or not contr:
            print(f"  {carpeta[:12]}: no estan los resultados, se saltea")
            continue
        h = pd.read_excel(series[0], sheet_name=None)
        dia = h["diagnostics"]
        meta = dict(zip(h["resumen"].iloc[:, 0].astype(str), h["resumen"].iloc[:, 1]))
        g = float(meta.get("grosor medio (px)", np.nan))
        if not np.isfinite(g):
            g = float(np.nanmedian(dia["thickness_px"]))
        m = respuesta_forzada(dia["time_s"].to_numpy(float),
                              dia["center_px"].to_numpy(float), g, 10.0)
        hr = pd.read_excel(contr[0], sheet_name=None)
        rep = hr[[k for k in hr if k.startswith("resumen")][0]].iloc[0].to_dict()
        for q in (("ttp"), ("rt50")):
            base = rep.get(f"{q}_s")
            if not rep.get(f"{q}_reportable") or not pd.notna(base):
                continue
            base_ms = 1000 * float(base)
            v = m.get(f"forzada_{q}_ms")
            dif = abs(v / base_ms - 1) if v and np.isfinite(v) else np.inf
            ok = m.get(f"forzada_{q}_reportable") and dif <= 0.05
            print(f"  {carpeta[6:9]} {q.upper()}: forzada {v:.0f} ms contra el reporte "
                  f"{base_ms:.0f} ms ({100 * (v - base_ms) / base_ms:+.0f} %)  "
                  f"{'OK' if ok else 'FALLA'}")
            if not ok:
                fallos.append(f"{carpeta[6:9]} {q}: {dif:.1%} de diferencia")
    return fallos


def main():
    fallos = []
    for seed in range(5):
        t, x = serie(seed, amp=1.5)
        m = respuesta_forzada(t, x, 1000.0, 10.0)
        ok = m["forzada_hay_respuesta"] and abs(m["forzada_amplitud_px"] / 1.5 - 1) <= 0.20
        print(f"  pulsos 1.5 px (5 x ruido) (seed {seed}): p {m['forzada_p']:.3f}, "
              f"{m['forzada_n_responden']}/{m['forzada_n_pulsos']}, ampl {m['forzada_amplitud_px']:.2f} px, "
              f"T {m['forzada_periodo_s']:.2f}  {'OK' if ok else 'FALLA'}")
        if not ok:
            fallos.append(f"pulsos seed {seed}")
        t, x = serie(seed, amp=0.9)
        if not respuesta_forzada(t, x, 1000.0, 10.0)["forzada_hay_respuesta"]:
            fallos.append(f"pulsos de 3 x ruido no detectados (seed {seed})")
    falsos = 0
    for seed in range(10):
        for sac in (0, 6):
            t, x = serie(100 + seed, amp=0.0, sacudidas=sac)
            falsos += respuesta_forzada(t, x, 1000.0, 10.0)["forzada_hay_respuesta"]
    print(f"  sin respuesta (20 series, la mitad con sacudidas): {falsos} falsas respuestas")
    if falsos > 2:   # p <= 0.05 -> se esperan ~1 de 20
        fallos.append(f"{falsos} falsas respuestas de 20")
    fallos += probar_cinetica()
    fallos += probar_contra_reporte()
    if fallos:
        print("FALLA: " + "; ".join(fallos)); sys.exit(1)
    print("TODO OK")


if __name__ == "__main__":
    main()
