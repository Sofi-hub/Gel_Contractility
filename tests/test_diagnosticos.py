"""
tests/test_diagnosticos.py  -  Fase 4.

1. motion_check._subpixel_shift mide bien un corrimiento conocido (H51: la
   version vieja daba 0.10 px para 1 px).
2. signal_check reconoce una poblacion de eventos hacia CUALQUIER lado (H49)
   y no la inventa en ruido simetrico de colas pesadas.
3. contraction_report marca `junto_al_borde` un evento pegado al inicio (H11).

Uso:  python tests/test_diagnosticos.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "scripts"))

from motion_check import _subpixel_shift  # noqa: E402
import signal_check as sc  # noqa: E402
import contraction_report as cr  # noqa: E402

fallas = []


def chequear(cond, texto):
    print(("  OK  " if cond else "  FALLA ") + texto)
    if not cond:
        fallas.append(texto)


# --- 1. corrimiento conocido ------------------------------------------------
y = np.arange(400, dtype=float)
perfil = lambda c: 50 + 100 / (1 + np.exp(-(y - c + 140) / 3)) - 100 / (1 + np.exp(-(y - c - 140) / 3))
ref = perfil(200.0)
for s in (0.25, 0.5, 1.0, 2.0, -1.5, 3.0):
    m, _ = _subpixel_shift(ref, perfil(200.0 + s), max_lag=25)
    chequear(abs(m - s) < 0.02, f"corrimiento {s:+.2f} px -> medido {m:+.3f} px")

# --- 2. signal_check en los dos sentidos ------------------------------------
fps, n = 30.0, 2000
t = np.arange(n) / fps
rng = np.random.default_rng(1)
base = rng.normal(0, 0.05, n)
ev = np.zeros(n)
for t0 in range(60, n - 10, 200):
    ev[t0:t0 + 4] = [0.6, 1.5, 0.8, 0.3]
for signo, nombre in ((+1, "eventos hacia valores mayores"), (-1, "eventos hacia valores menores")):
    df = pd.DataFrame({"time_s": t, "center_px": 400 + base + signo * ev})
    v = sc.veredicto(sc.analizar(df, "center_px"))
    chequear(v.startswith("HAY"), f"{nombre}: {v}")
for semilla in range(3):
    ruido = np.random.default_rng(10 + semilla).standard_t(5, n) * 0.05
    df = pd.DataFrame({"time_s": t, "center_px": 400 + ruido})
    v = sc.veredicto(sc.analizar(df, "center_px"))
    chequear(not v.startswith("HAY"), f"ruido t de Student (semilla {semilla}): {v}")

# --- 3. junto_al_borde -------------------------------------------------------
x = 400 + rng.normal(0, 0.02, n)
for t0 in (9, 400, 800, 1200, 1600):          # el primero, a 9 fotogramas del inicio
    x[t0:t0 + 4] += [0.6, 1.5, 0.8, 0.3]
df = pd.DataFrame({"time_s": t, "center_px": x, "thickness_px": 280 + rng.normal(0, 0.02, n)})
r = cr.analizar(df, "center_px", None, None, None, 1.5)
borde = np.asarray(r.get("_junto_al_borde", []), bool)
chequear(r["n_eventos"] == 5, f"5 eventos detectados (dio {r['n_eventos']})")
chequear(borde.sum() == 1 and bool(borde[0]), f"solo el primero marcado junto_al_borde ({borde.tolist()})")

print()
print("TODO OK" if not fallas else f"{len(fallas)} FALLA(S)")
sys.exit(1 if fallas else 0)
