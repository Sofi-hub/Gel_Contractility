"""Prueba de src/cinetica.py con senales SINTETICAS de cinetica conocida.

No se ajusta nada contra los videos: se fabrica un evento con TTP y RT50
verdaderos, se lo muestrea a 30 fps con ruido y fase aleatoria, y se exige:

  1. evento lento (TTP 300 ms): la mediana de TTP y RT50 cae a menos de un
     fotograma del valor verdadero y se declara medible;
  2. evento rapido (TTP 40 ms, como un twitch): se declara NO medible, y el
     valor verdadero cae dentro del intervalo [min, max] de cada evento;
  3. el intervalo [min, max] contiene al valor verdadero en ambos casos;
  4. la amplitud relativa es A / grosor.

Correr con:  python tests/test_cinetica.py
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src import cinetica as cin          # noqa: E402

FPS = 30.0


def evento(tt, t0, ttp, rt50, A=1.0):
    """Subida lineal desde el 0 en t0 hasta A en t0+ttp; bajada exponencial
    que cae al 50 % en rt50. TTP verdadero (desde el 10 %) = 0.9 * ttp."""
    y = np.zeros_like(tt)
    sube = (tt >= t0) & (tt < t0 + ttp)
    y[sube] = A * (tt[sube] - t0) / ttp
    baja = tt >= t0 + ttp
    y[baja] = A * 0.5 ** ((tt[baja] - t0 - ttp) / rt50)
    return y


def serie(ttp, rt50, ruido=0.02, n_ev=8, periodo=3.0, semilla=0):
    rng = np.random.default_rng(semilla)
    t = np.arange(0, n_ev * periodo + 2, 1 / FPS)
    r = np.zeros_like(t)
    t0s = 1.0 + periodo * np.arange(n_ev) + rng.uniform(0, 1 / FPS, n_ev)  # fase al azar
    for t0 in t0s:
        r += evento(t, t0, ttp, rt50)
    r += rng.normal(0, ruido, len(t))
    picos = np.array([np.argmax(np.where((t > a) & (t < a + 1.5), r, -np.inf)) for a in t0s])
    return t, r, picos


def caso(ttp, rt50, esperar_medible, semillas=range(20)):
    ttp_real = 0.9 * ttp
    dentro_ttp = dentro_rt = 0
    total = 0
    meds_ttp, meds_rt = [], []
    for s in semillas:
        t, r, pk = serie(ttp, rt50, semilla=s)
        ev = cin.cinetica_eventos(t, r, pk, ruido=0.02, grosor_reposo=np.full(len(t), 50.0))
        res = cin.resumir(ev, conteo_reportable=True)
        assert res["ttp_reportable"] == esperar_medible, (ttp, s, res["cinetica_motivo"])
        assert np.allclose(ev["amplitud_relativa_pct"], 100 * ev["amplitud_px"] / 50.0)
        dentro_ttp += int(((ev.ttp_min_s <= ttp_real) & (ttp_real <= ev.ttp_max_s)).sum())
        dentro_rt += int(((ev.rt50_min_s <= rt50) & (rt50 <= ev.rt50_max_s)).sum())
        total += len(ev)
        if esperar_medible:
            meds_ttp.append(res["ttp_s"]); meds_rt.append(res["rt50_s"])
        else:
            assert np.isnan(res["ttp_s"]), "no medible tiene que dar NaN, no un numero"
    assert dentro_ttp / total >= 0.95, f"TTP fuera del intervalo en {total - dentro_ttp}/{total}"
    assert dentro_rt / total >= 0.95, f"RT50 fuera del intervalo en {total - dentro_rt}/{total}"
    if esperar_medible:
        e1 = abs(np.median(meds_ttp) - ttp_real) * FPS
        e2 = abs(np.median(meds_rt) - rt50) * FPS
        assert e1 < 1 and e2 < 1, (e1, e2)
        return f"TTP err {e1:.2f} fr, RT50 err {e2:.2f} fr, cobertura {dentro_ttp}/{total}, {dentro_rt}/{total}"
    return f"no medible OK, cobertura {dentro_ttp}/{total}, {dentro_rt}/{total}"


def test_no_medible_si_conteo_no_reportable():
    t, r, pk = serie(0.3, 0.2)
    ev = cin.cinetica_eventos(t, r, pk, ruido=0.02)
    res = cin.resumir(ev, conteo_reportable=False)
    assert not res["ttp_reportable"] and not res["rt50_reportable"]
    assert np.isnan(res["ttp_s"])


if __name__ == "__main__":
    print("lento  (TTP 270 ms, RT50 200 ms):", caso(0.30, 0.20, True))
    print("rapido (TTP  36 ms, RT50  40 ms):", caso(0.04, 0.04, False))
    test_no_medible_si_conteo_no_reportable()
    print("conteo no reportable -> cinetica no reportable: OK")
    print("TODO OK")
