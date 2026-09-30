"""Fotogramas sin medida (NaN): el analisis no puede anularse en silencio.

Hallazgos H1 / H31 / H47 / H53 de la revision de codigo: con UN fotograma NaN,
Video_prueba pasaba de 28 eventos a 0 y el reporte decia "no hay meseta". La
causa era que la MAD usaba `np.median`, que propaga el NaN. Ahora todo pasa
por `src/estadistica.py`, que ignora los NaN sin inventar valores.

Se exige, sobre una serie SINTETICA de conteo conocido (6 eventos rapidos,
como los de Video_prueba/063/268, uno cada 10 s):

  1. `estadistica`: la MAD ignora NaN; sin NaN da lo mismo que la formula
     vieja; `buscar_picos` sin NaN da lo mismo que `find_peaks`.
  2. 1, 3 y 30 NaN dispersos, o un tramo de 15 seguidos, lejos de los eventos:
     mismo conteo, mismo k, ruido finito, y la hoja lo registra.
  3. NaN justo en un pico: el evento se sigue detectando y queda marcado
     `junto_a_hueco`.
  4. NaN entre el inicio y el pico de un evento LENTO: su TTP queda sin medir
     (NaN), no se inventa saltando el hueco. Se prueba llamando directo a
     `cinetica_eventos`, porque la deteccion de eventos lentos tiene su propio
     problema (H55: con `sep_s` = 0.3 s la cola de bajada cuenta como un segundo
     evento) y esta prueba es sobre NaN, no sobre deteccion.
  5. Si esta el video real Video_prueba, un NaN no le cambia los 29 eventos
     (28 antes de la Fase 2.2, que recupero la contraccion de 15.278 s).

Correr con:  python tests/test_nan.py
"""
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.signal import find_peaks

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "scripts"))
from src import estadistica as est                 # noqa: E402
from src import cinetica as cin                    # noqa: E402
from contraction_report import analizar            # noqa: E402

warnings.filterwarnings("ignore", category=RuntimeWarning)
FPS = 30.0
T0S = 5.0 + 10.0 * np.arange(6)                    # 6 eventos, uno cada 10 s


def pulso(t, t0, subida, rt50, A=1.5):
    """Subida lineal de `subida` s y bajada exponencial con RT50 = `rt50` s."""
    y = np.zeros_like(t)
    sube = (t >= t0) & (t < t0 + subida)
    y[sube] = A * (t[sube] - t0) / subida
    baja = t >= t0 + subida
    y[baja] = A * 0.5 ** ((t[baja] - t0 - subida) / rt50)
    return y


def serie(semilla=0):
    rng = np.random.default_rng(semilla)
    t = np.arange(0, 66, 1 / FPS)
    c = sum(pulso(t, t0, 0.04, 0.05) for t0 in T0S)   # rapidos: 1-2 fotogramas
    c = c + rng.normal(0, 0.04, len(t)) + 400.0
    return pd.DataFrame({"time_s": t, "center_px": c,
                         "thickness_px": 250 + rng.normal(0, 0.05, len(t)),
                         "frame_quality": "OK"})


def correr(df):
    return analizar(df, "center_px", None, None, None, 1.5, separar=False)


def con_nan(df, idx):
    d = df.copy()
    d.loc[np.asarray(idx), ["center_px", "thickness_px"]] = np.nan
    d.loc[np.asarray(idx), "frame_quality"] = "REJECTED"
    return d


def main() -> int:
    fallas = []

    def chequear(cond, msg):
        print(f"  {'OK ' if cond else 'MAL'} {msg}")
        if not cond:
            fallas.append(msg)

    # 1. estadistica ---------------------------------------------------------
    x = np.random.default_rng(3).normal(size=500)
    vieja = float(np.median(np.abs(x - np.median(x))) * 1.4826)
    chequear(est.mad(x) == vieja, "mad sin NaN == formula vieja (bit a bit)")
    xn = x.copy(); xn[[5, 50, 400]] = np.nan
    chequear(est.mad(xn) == est.mad(np.delete(x, [5, 50, 400])), "mad ignora los NaN")
    chequear(np.isnan(est.mad([np.nan, np.nan])), "mad de todo NaN es NaN")
    chequear(np.array_equal(est.buscar_picos(x, height=1)[0], find_peaks(x, height=1)[0]),
             "buscar_picos sin NaN == find_peaks")

    # 2. base y NaN lejos de los eventos -------------------------------------
    df = serie()
    a0 = correr(df)
    chequear(a0["n_eventos"] == 6 and a0["conteo_reportable"],
             f"serie sintetica sin NaN: 6 eventos reportables (dio {a0['n_eventos']})")
    picos = a0["_picos"]
    n = len(df)
    lejos = np.array([i for i in range(n) if np.min(np.abs(picos - i)) > 30])
    rng = np.random.default_rng(1)
    casos = {"1 NaN": rng.choice(lejos, 1, replace=False),
             "3 NaN": rng.choice(lejos, 3, replace=False),
             "30 NaN": rng.choice(lejos, 30, replace=False),
             "tramo de 15": np.arange(int(8.0 * FPS), int(8.0 * FPS) + 15)}
    for nombre, idx in casos.items():
        a = correr(con_nan(df, idx))
        chequear(a["n_eventos"] == 6 and a["k_usado"] == a0["k_usado"] and a["conteo_reportable"]
                 and np.isfinite(a["ruido_canal_px"]) and a["fotogramas_sin_medida"] == len(idx),
                 f"{nombre}: {a['n_eventos']} eventos, k={a['k_usado']:g}, "
                 f"ruido={a['ruido_canal_px']:.4f}, sin medida={a['fotogramas_sin_medida']}")

    # 3. NaN en un pico ------------------------------------------------------
    p = int(picos[2])
    a = correr(con_nan(df, [p]))
    chequear(a["n_eventos"] == 6 and a["eventos_junto_a_hueco"] == 1
             and bool(a["_junto_a_hueco"][2]),
             f"NaN en el pico del evento 3: {a['n_eventos']} eventos, "
             f"junto_a_hueco={a['eventos_junto_a_hueco']}")

    # 4. NaN en la subida de un evento lento: su TTP sin medir ---------------
    t = np.arange(0, 66, 1 / FPS)
    r = sum(pulso(t, t0, 0.3, 0.2) for t0 in T0S)
    r = r + np.random.default_rng(2).normal(0, 0.02, len(t))
    pk = np.array([int(np.argmax(np.where((t > t0) & (t < t0 + 1), r, -np.inf))) for t0 in T0S])
    ev0 = cin.cinetica_eventos(t, r, pk, ruido=0.02)
    chequear(ev0["ttp_s"].notna().all() and ev0["rt50_s"].notna().all(),
             "evento lento sin NaN: todos tienen TTP y RT50")
    r2 = r.copy(); r2[pk[2] - 3] = np.nan; r2[pk[4] + 2] = np.nan
    ev = cin.cinetica_eventos(t, r2, pk, ruido=0.02)
    chequear(np.isnan(ev.loc[2, "ttp_s"]) and ev.drop(index=2)["ttp_s"].notna().all(),
             "NaN en la subida del evento 3: su TTP queda NaN, los demas se miden")
    chequear(np.isnan(ev.loc[4, "rt50_s"]) and ev.drop(index=4)["rt50_s"].notna().all(),
             "NaN en la bajada del evento 5: su RT50 queda NaN, los demas se miden")

    # 5. video real, si esta -------------------------------------------------
    real = RAIZ / "data" / "processed_data" / "Video_prueba" / "serie_temporal.xlsx"
    if real.exists():
        dr = pd.read_excel(real, sheet_name="diagnostics")
        ar = analizar(con_nan(dr, [100]), "center_px", None, None, None, 1.5, separar=False)
        chequear(ar["n_eventos"] == 29 and ar["conteo_reportable"],
                 f"Video_prueba con un NaN en la fila 100: {ar['n_eventos']} eventos (29 desde la Fase 2.2; antes de la 2.1 daba 0)")
    else:
        print("  --  Video_prueba no esta en data/processed_data: se saltea el caso real")

    print(f"\n{'TODO OK' if not fallas else f'{len(fallas)} FALLA(S)'}")
    return 1 if fallas else 0


if __name__ == "__main__":
    raise SystemExit(main())
