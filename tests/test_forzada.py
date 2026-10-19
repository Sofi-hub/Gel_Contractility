"""Respuesta forzada (src/forzada.py, 2026-10-19).

Sintéticos (ruido blanco de 0.3 px por fotograma): (a) pulsos de 5 x ruido cada
10.1 s -> hay respuesta y la amplitud sale a +-20 %; (a') pulsos de 3 x ruido -> hay
respuesta (la amplitud sale ~10-30 % alta: el pico de la ventana agarra ruido); (b) solo ruido ->
no hay respuesta; (c) ruido con sacudidas al azar hacia los dos lados -> no hay.

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
    if fallos:
        print("FALLA: " + "; ".join(fallos)); sys.exit(1)
    print("TODO OK")


if __name__ == "__main__":
    main()
