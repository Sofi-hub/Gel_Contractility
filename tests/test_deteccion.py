"""Deteccion de eventos sobre series SINTETICAS de conteo conocido (Fase 2.2).

A diferencia de `test_seleccion_k.py`, que le da a `elegir_k_meseta` conteos
escritos a mano, esta prueba corre la deteccion ENTERA de
`contraction_report.analizar` (detrend con ventana automatica, escaneo de k,
meseta, control de estabilidad). Asi, un cambio en como se define un evento
rompe la prueba (H9 de la revision de codigo).

Cada escenario reproduce un modo de falla medido en los videos reales:

  rapidos              como Video_063/268: 1-2 fotogramas de subida
  lentos               como Video_583: subida 0.3 s, RT50 0.2 s. Con la regla
                       vieja (sep_s = 0.3 s) la cola contaba como otro evento (H55)
  lentos con meseta    como Video_466
  rafaga a 0.28 s      como Video_prueba a los 15 s. La regla vieja fundia los
                       eventos (H8)
  largos (1 s)         como Video_491. Con la ventana fija de 2 s la mediana se
                       comia la contraccion (H33)
  chicos + grandes     espontaneas de 0.6 px entre estimuladas de 3 px: la
                       meseta de k mas bajo tiene que contar las dos poblaciones

Se exige el conteo EXACTO y reportable en todas las series (ruido blanco y
correlacionado, varias semillas).

Correr con:  python tests/test_deteccion.py
"""
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "scripts"))
from contraction_report import analizar          # noqa: E402

warnings.filterwarnings("ignore", category=RuntimeWarning)
FPS = 30.0
SEMILLAS = range(6)


def pulso(t, t0, subida, rt50, A, meseta=0.0):
    y = np.zeros_like(t)
    sube = (t >= t0) & (t < t0 + subida)
    y[sube] = A * (t[sube] - t0) / subida
    mes = (t >= t0 + subida) & (t < t0 + subida + meseta)
    y[mes] = A
    baja = t >= t0 + subida + meseta
    y[baja] = A * 0.5 ** ((t[baja] - t0 - subida - meseta) / rt50)
    return y


def ruido(n, sigma, rng, rho):
    e = rng.normal(0, sigma * np.sqrt(1 - rho ** 2), n)
    x = np.empty(n)
    x[0] = rng.normal(0, sigma)
    for i in range(1, n):
        x[i] = rho * x[i - 1] + e[i]
    return x


def escenario(nombre, rng):
    t = np.arange(0, 70, 1 / FPS)
    est = 5.0 + 10.0 * np.arange(6)
    y = np.zeros_like(t)
    if nombre == "rapidos":
        for t0 in est:
            y += pulso(t, t0, 0.04, 0.05, 1.5)
        n = 6
    elif nombre == "lentos (como 583)":
        for t0 in est:
            y += pulso(t, t0, 0.3, 0.2, 1.5)
        n = 6
    elif nombre == "lentos con meseta (como 466)":
        for t0 in est:
            y += pulso(t, t0, 0.3, 0.2, 1.5, meseta=0.13)
        n = 6
    elif nombre == "rafaga a 0.28 s (como prueba)":
        for t0 in est:
            y += pulso(t, t0, 0.04, 0.05, 1.5)
        for t0 in (32.0, 32.28, 32.56, 32.90):
            y += pulso(t, t0, 0.04, 0.05, 1.0)
        n = 10
    elif nombre == "largos de 1 s (como 491)":
        for t0 in (13.0, 34.0, 55.0):
            y += pulso(t, t0, 0.3, 0.1, 1.0, meseta=0.7)
        n = 3
    elif nombre == "chicos + grandes":
        for t0 in est:
            y += pulso(t, t0, 0.04, 0.05, 3.0)
        esp = np.sort(rng.uniform(1, 68, 15))
        esp = esp[np.r_[True, np.diff(esp) > 0.6]]
        esp = esp[np.min(np.abs(esp[:, None] - est[None, :]), axis=1) > 0.6]
        for t0 in esp:
            y += pulso(t, t0, 0.04, 0.05, 0.6)
        n = 6 + len(esp)
    return t, y, n


ESCENARIOS = ["rapidos", "lentos (como 583)", "lentos con meseta (como 466)",
              "rafaga a 0.28 s (como prueba)", "largos de 1 s (como 491)", "chicos + grandes"]


def main() -> int:
    fallas = 0
    for nombre in ESCENARIOS:
        malos = []
        total = 0
        for rho in (0.0, 0.6):
            for sem in SEMILLAS:
                rng = np.random.default_rng(sem)
                t, y, n = escenario(nombre, rng)
                v = 400.0 + y + ruido(len(t), 0.04, rng, rho)
                df = pd.DataFrame({"time_s": t, "center_px": v,
                                   "thickness_px": 250 + rng.normal(0, 0.05, len(t))})
                a = analizar(df, "center_px", None, None, None, 1.5, separar=False)
                total += 1
                if not (a["n_eventos"] == n and a["conteo_reportable"]):
                    malos.append(f"rho={rho} sem={sem}: {a['n_eventos']} "
                                 f"({'reportable' if a['conteo_reportable'] else 'NO reportable'}, "
                                 f"esperado {n})")
        bien = total - len(malos)
        print(f"  {'OK ' if not malos else 'MAL'} {nombre:32s} {bien}/{total} exactos")
        for m in malos[:3]:
            print(f"        {m}")
        fallas += bool(malos)
    print(f"\n{'TODO OK' if not fallas else f'{fallas} escenario(s) con fallas'}")
    return 1 if fallas else 0


if __name__ == "__main__":
    raise SystemExit(main())
