"""Separacion de estimuladas y espontaneas (src/rhythm_split.py), Fase 3.

Series SINTETICAS chicas, de resultado conocido, que fijan cada regla:

  1. Un pulso del medio que falla (fatiga): el tren se detecta igual y la
     grilla muestra esa ranura como no capturada.
  2. Dos pulsos de 6 que fallan: con captura 4/6 = 67 % (< 75 %) no hay tren.
     Bajando --min-captura aparece el intento, pero 4 latidos entre
     espontaneas no pasan la prueba (p ~ 0.02): el limite es de evidencia.
  3. Los ultimos pulsos fallan: el tren termina antes, sin penalidad.
  4. R5: un evento que se desvia > 1 fotograma Y tiene la amplitud de una
     espontanea sale del tren (como el de 4.82 s de Video_prueba); con la
     amplitud de los estimulados se queda (el tiempo solo no alcanza).
  5. R6: un latido corrido dentro del tren y con amplitud compatible queda
     "dudoso"; con amplitud de espontanea, o fuera del tren, no se rescata.
  6. Veredictos: sin frecuencia, "no se configuro ninguna frecuencia"; con
     frecuencia y solo espontaneas, no hay estimulados.
  7. Dos frecuencias configuradas (cambio a mitad del registro): dos trenes.
  8. El p-valor llega a 1/1001 con 1000 simulaciones, desde 4-5 eventos.
  9. El puntaje vectorizado de `buscar_grilla` es identico al calculo uno por
     uno con `_asignar` (la version anterior, lenta).
 10. Cinetica por grupo: con tren, la cifra principal es la de los estimulados.

Correr con:  python tests/test_ritmo.py
"""
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "scripts"))
from src import rhythm_split as rs            # noqa: E402
from contraction_report import analizar       # noqa: E402

warnings.filterwarnings("ignore", category=RuntimeWarning)
RES = 1 / 30.0


def q(x):
    """Instantes en la grilla de fotogramas, como los que mide la camara."""
    return np.round(np.asarray(x, float) / RES) * RES


def espontaneas(rng, n, lejos_de, t_max=68.0):
    """`n` instantes al azar a mas de 0.4 s de los de `lejos_de`."""
    out = []
    while len(out) < n:
        x = rng.uniform(0.5, t_max)
        if np.min(np.abs(np.r_[lejos_de, out] - x)) > 0.4:
            out.append(x)
    return np.array(out)


def juntar(est, a_est, esp, a_esp):
    t = np.r_[est, esp]
    a = np.r_[a_est, a_esp]
    o = np.argsort(t)
    return q(t[o]), a[o]


def separar(t, a, f=0.1, **kw):
    return rs.separar(t, a, duracion_s=70.0, resolucion_s=RES, frecuencia_configurada_Hz=f, **kw)


def main() -> int:
    fallas = []

    def chequear(cond, msg):
        print(f"  {'OK ' if cond else 'MAL'} {msg}")
        if not cond:
            fallas.append(msg)

    rng = np.random.default_rng(7)
    ranuras = 5.0 + 10.0 * np.arange(6)
    esp = espontaneas(rng, 10, ranuras)
    a_esp = rng.uniform(1.3, 2.5, len(esp))

    # 1. falla un pulso del medio -------------------------------------------
    est = np.delete(ranuras, 2)
    t, a = juntar(est, np.full(5, 6.8), esp, a_esp)
    r = separar(t, a)
    g = r["grilla"]
    chequear(r["hay_estimulacion"] and r["n_estimulados"] == 5 and r["n_ranuras"] == 6
             and (~g["capturada"]).sum() == 1 and not g["capturada"].iloc[2],
             f"falla el 3er pulso de 6: tren detectado, {r.get('n_estimulados')}/{r.get('n_ranuras')} "
             f"ranuras, la 3a figura como no capturada")

    # 2. fallan dos de seis ---------------------------------------------------
    est = np.delete(ranuras, [2, 3])
    t, a = juntar(est, np.full(4, 6.8), esp, a_esp)
    r = separar(t, a)
    chequear(not r["hay_estimulacion"],
             f"fallan el 3o y el 4o: captura 4/6 < 75 %, sin tren ({r.get('veredicto')})")
    r = separar(t, a, min_captura=0.6)
    chequear(not r["hay_estimulacion"] and r["trenes"]["n_eventos_tren"].iloc[0] == 4
             and r["trenes"]["p_valor"].iloc[0] > 0.01,
             f"... con --min-captura 0.6 aparece el intento (4/6) pero 4 latidos entre "
             f"espontaneas no alcanzan: p = {r['trenes']['p_valor'].iloc[0]:.3f} > 0.01")

    # 3. fallan los ultimos ---------------------------------------------------
    est = ranuras[:4]
    t, a = juntar(est, np.full(4, 6.8), esp, a_esp)
    r = separar(t, a)
    chequear(r["hay_estimulacion"] and r["n_estimulados"] == 4 and r["n_ranuras"] == 4,
             f"fallan los 2 ultimos: tren de 4/4 que termina en {r.get('tren_fin_s')} s")

    # 4. R5: tiempo Y amplitud ------------------------------------------------
    est = 14.875 + 10.0 * np.arange(6)
    intruso = 4.817                                   # -58 ms de su ranura
    # Espontaneas lejos del comienzo: si hay varias cerca del intruso, sumarlo
    # baja el puntaje del tren y la busqueda misma lo deja afuera (tambien
    # correcto, pero entonces R5 no llega a actuar y no se la prueba).
    esp2 = espontaneas(np.random.default_rng(3), 10, np.r_[est, intruso, np.arange(0, 17, 0.4)])
    for amp, debe_salir in ((2.1, True), (6.8, False)):
        # El inicio de una contraccion se INTERPOLA entre fotogramas, asi que el
        # intruso no se redondea (redondeado quedaria a -33 ms = 1 fotograma justo).
        t, a = juntar(est, np.full(6, 6.8), esp2,
                      np.random.default_rng(4).uniform(1.3, 2.5, len(esp2)))
        o = np.argsort(np.r_[t, intruso])
        t, a = np.r_[t, intruso][o], np.r_[a, amp][o]
        r = separar(t, a)
        sac = r["sacados_tiempo_amplitud"]
        salio = len(sac) == 1 and np.isclose(sac["tiempo_s"].iloc[0], intruso, atol=1e-3)
        chequear(r["hay_estimulacion"] and r["n_estimulados"] == (6 if debe_salir else 7)
                 and salio == debe_salir,
                 f"evento a -58 ms con {amp} px (tren 6.8 px): la regla tiempo+amplitud "
                 f"{'lo saca' if salio else 'no lo saca'} (esperado: {'saca' if debe_salir else 'no saca'})")

    # 5. R6: rescate de dudosos -----------------------------------------------
    for desc, t_corr, amp, debe in (("en el medio, amplitud del tren", 25.0 + 0.20, 6.8, True),
                                    ("en el medio, amplitud de espontanea", 25.0 + 0.20, 2.0, False),
                                    ("antes del primer latido", 5.0 - 0.20, 6.8, False)):
        base = np.array([5.0, 15.0, 35.0, 45.0, 55.0, 65.0]) if t_corr > 10 else ranuras[1:]
        t, a = juntar(np.r_[base, t_corr], np.r_[np.full(len(base), 6.8), amp], esp, a_esp)
        r = separar(t, a)
        i = int(np.argmin(np.abs(t - q(t_corr))))
        es_dudoso = i in set(r.get("estimulados_dudosos", []))
        chequear(r["hay_estimulacion"] and es_dudoso == debe,
                 f"latido corrido 200 ms {desc}: {'dudoso' if es_dudoso else 'no rescatado'}")

    # 6. veredictos -------------------------------------------------------------
    t, a = juntar(ranuras, np.full(6, 6.8), esp, a_esp)
    r = separar(t, a, f=None)
    chequear(r["hay_estimulacion"] and "no se configuro ninguna frecuencia" in r["veredicto"],
             f"sin frecuencia: '{r.get('veredicto')}'")
    r = separar(t, a, f=0.1)
    chequear("enganchado a la frecuencia configurada (0.1 Hz)" in r["veredicto"],
             f"con 0.1 Hz: '{r.get('veredicto')}'")
    solo = q(np.sort(espontaneas(np.random.default_rng(11), 25, np.array([-10.0]))))
    r = separar(solo, np.random.default_rng(12).uniform(1.3, 2.5, len(solo)))
    chequear(not r["hay_estimulacion"], f"solo espontaneas, 0.1 Hz: '{r.get('veredicto')}'")

    # 7. dos frecuencias --------------------------------------------------------
    e1, e2 = 5.0 + 10.0 * np.arange(4), 41.5 + 5.0 * np.arange(6)
    esp3 = espontaneas(np.random.default_rng(5), 8, np.r_[e1, e2])
    t, a = juntar(np.r_[e1, e2], np.full(10, 6.8), esp3, np.full(len(esp3), 2.0))
    r = separar(t, a, f=[0.1, 0.2])
    chequear(r["n_trenes_estimulados"] == 2 and len(r["estimulados"]) == 10,
             f"0.1 Hz y despues 0.2 Hz: {r['n_trenes_estimulados']} trenes, "
             f"{len(r['estimulados'])} estimulados")
    r = separar(t, a, f=0.1)
    chequear(r["n_trenes_estimulados"] == 1 and len(r["estimulados"]) == 4,
             "configurando solo 0.1 Hz: el tramo de 0.2 Hz queda espontaneo")

    # 8. resolucion del p -------------------------------------------------------
    r = separar(q(ranuras[:5]), np.full(5, 6.8))
    chequear(np.isclose(r["p_valor"], 1 / 1001), f"5 eventos limpios: p = {r['p_valor']:.4f} (1/1001)")

    # 9. puntaje vectorizado == calculo uno por uno ------------------------------
    def lento(t, per, tol):
        c, an = rs._contar_vectorizado(t, per, tol)
        out = {}
        for k in np.flatnonzero(c >= 4):
            idx, ran = rs._asignar(t, per[k], t[an[k]], tol[k])
            if len(idx) < 4:
                continue
            nr = int(ran[-1] - ran[0]) + 1
            if len(idx) < 0.75 * nr:
                continue
            dur = max(t[idx[-1]] - t[idx[0]], 1e-9)
            env = int(np.sum((t >= t[idx[0]]) & (t <= t[idx[-1]])))
            out[round(float(per[k]), 9)] = rs._z_periodicidad(len(idx), nr, env / dur, tol[k])
        return out
    iguales = 0
    rr = np.random.default_rng(1)
    for s in range(30):
        tt = np.sort(rr.uniform(0, 70, rr.integers(6, 35)))
        if s % 2:
            tt = np.sort(np.r_[tt, ranuras + rr.normal(0, 0.01, 6)])
        g = rs.buscar_grilla(tt, 70, periodo_min=0.3, tol_s=2 * RES)
        # el ganador vectorizado tiene que tener el z de algun candidato calculado
        # uno por uno sobre la misma grilla de periodos, y ninguno puede superarlo
        span = tt[-1] - tt[0]
        pmax = span / 3
        n_fino = int(np.ceil(np.log(pmax / 0.3) * span / (2 * RES)))
        per = np.geomspace(0.3, pmax, max(600, n_fino))
        ref = lento(tt, per, np.full_like(per, 2 * RES))
        if g is None:
            iguales += int(len(ref) == 0)
        else:
            iguales += int(any(abs(g["z"] - z) < 1e-9 for z in ref.values())
                           and g["z"] <= max(ref.values()) + 1e-9)
    chequear(iguales == 30, f"puntaje vectorizado == uno por uno en {iguales}/30 series al azar")

    # 10. cinetica por grupo (corre analizar entero) ------------------------------
    fps = 30.0
    tt = np.arange(0, 70, 1 / fps)
    y = np.zeros_like(tt)

    def pulso(t0, A):
        s = (tt >= t0) & (tt < t0 + 0.04)
        y[s] += A * (tt[s] - t0) / 0.04
        b = tt >= t0 + 0.04
        y[b] += A * 0.5 ** ((tt[b] - t0 - 0.04) / 0.05)
    for t0 in ranuras:
        pulso(t0, 3.0)
    for t0 in (2.3, 9.1, 21.7, 33.2, 48.6, 61.4):
        pulso(t0, 0.6)
    rg = np.random.default_rng(0)
    df = pd.DataFrame({"time_s": tt, "center_px": 400 + y + rg.normal(0, 0.04, len(tt)),
                       "thickness_px": 250 + rg.normal(0, 0.05, len(tt))})
    a_ = analizar(df, "center_px", None, None, None, 1.5, frecuencia_estimulo=0.1)
    cg = a_["_cinetica_grupos"].set_index("grupo")
    chequear(a_["n_eventos"] == 12 and a_["cinetica_grupo_principal"] == "estimulados"
             and np.isclose(a_["amplitud_relativa_pct"], cg.loc["estimulados", "amplitud_relativa_pct"])
             and cg.loc["estimulados", "amplitud_relativa_pct"] > 3 * cg.loc["espontaneos", "amplitud_relativa_pct"],
             f"dos grupos: cifra principal = estimulados "
             f"({cg.loc['estimulados', 'amplitud_relativa_pct']:.2f} % contra "
             f"{cg.loc['todos', 'amplitud_relativa_pct']:.2f} % mezclando)")

    print(f"\n{'TODO OK' if not fallas else f'{len(fallas)} FALLA(S)'}")
    return 1 if fallas else 0


if __name__ == "__main__":
    raise SystemExit(main())
