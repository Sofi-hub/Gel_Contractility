"""H13: ¿aguanta el control de falsos con ruido desparejo? (2026-10-26). Solo medición.

Para decidir si un conteo es reportable, el programa busca picos también en la
señal DADA VUELTA ("falsos de control") y exige 0 en toda la meseta del umbral.
Eso supone que el ruido es igual de grande hacia los dos lados. Nunca se probó
con ruido desparejo. Lo que importa saber es hacia qué lado se equivoca:

  - si de más (dice "no se puede informar" cuando sí se podía) es SEGURO;
  - si de menos (da por bueno un conteo con contracciones inventadas) es GRAVE.

Series sintéticas con 6 contracciones conocidas (las mismas de
tests/test_deteccion.py) más:
  (a) ruido asimétrico: cola exponencial hacia UN lado, a favor de las
      contracciones (hacia arriba) o en contra, con tres severidades;
  (b) un rebote después de cada contracción, del 10, 30 y 50 % de la amplitud;
  (c) ruido simétrico, de control.

De cada corrida se anota conteo, reportable y falsos de control, y se compara
con la verdad (6). Al final, cuánto de asimetría y de rebote tienen los videos
REALES, medido igual, para saber si alguno se acerca a los casos que fallan.

    python data/_mediciones_fases/h13_ruido_asimetrico/h13.py
"""
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "scripts"))
sys.path.insert(0, str(RAIZ / "tests"))
from contraction_report import analizar          # noqa: E402
from referencia import VIDEOS, PROCESADOS        # noqa: E402

warnings.filterwarnings("ignore", category=RuntimeWarning)
AQUI = Path(__file__).resolve().parent
FPS = 30.0
SIGMA = 0.04
AMPL = 1.5
SEMILLAS = range(6)
RHOS = (0.0, 0.6)
N_VERDAD = 6
LEJOS_S = 1.0        # para medir el ruido "quieto", lejos de cualquier evento


# ------------------------------------------------------------- sintéticos
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


def ruido_asimetrico(n, sigma, rng, rho, lado, tasa, altura):
    """Ruido simétrico + una cola exponencial hacia `lado` (+1 arriba, -1 abajo):
    en una fracción `tasa` de los fotogramas se suma un golpe de media
    `altura` x sigma. Así el ruido es más largo de un lado que del otro."""
    x = ruido(n, sigma, rng, rho)
    golpe = (rng.random(n) < tasa) * rng.exponential(altura * sigma, n)
    return x + lado * golpe


ESCENARIOS = [
    ("simetrico (control)", dict(tipo="sim")),
    ("asim. A FAVOR 1 % x3s", dict(tipo="asim", lado=+1, tasa=0.01, altura=3)),
    ("asim. A FAVOR 2 % x5s", dict(tipo="asim", lado=+1, tasa=0.02, altura=5)),
    ("asim. A FAVOR 5 % x3s", dict(tipo="asim", lado=+1, tasa=0.05, altura=3)),
    ("asim. EN CONTRA 1 % x3s", dict(tipo="asim", lado=-1, tasa=0.01, altura=3)),
    ("asim. EN CONTRA 2 % x5s", dict(tipo="asim", lado=-1, tasa=0.02, altura=5)),
    ("asim. EN CONTRA 5 % x3s", dict(tipo="asim", lado=-1, tasa=0.05, altura=3)),
    ("rebote 10 %", dict(tipo="rebote", frac=0.10)),
    ("rebote 30 %", dict(tipo="rebote", frac=0.30)),
    ("rebote 50 %", dict(tipo="rebote", frac=0.50)),
]


def serie(cfg, rng, rho):
    t = np.arange(0, 70, 1 / FPS)
    y = np.zeros_like(t)
    for t0 in 5.0 + 10.0 * np.arange(N_VERDAD):
        y += pulso(t, t0, 0.04, 0.05, AMPL)
        if cfg["tipo"] == "rebote":
            # el gel se pasa de largo al volver: un valle después de la contracción
            y -= cfg["frac"] * pulso(t, t0 + 0.25, 0.12, 0.25, AMPL)
    n = len(t)
    if cfg["tipo"] == "asim":
        e = ruido_asimetrico(n, SIGMA, rng, rho, cfg["lado"], cfg["tasa"], cfg["altura"])
    else:
        e = ruido(n, SIGMA, rng, rho)
    v = 400.0 + y + e
    return pd.DataFrame({"time_s": t, "center_px": v,
                         "thickness_px": 250 + rng.normal(0, 0.05, n)})


# --------------------------------------------------- asimetría y rebote medidos
def asimetria(r, t, picos_t, lejos=LEJOS_S):
    """Cuán desparejo es el ruido fuera de las contracciones. Dos números:
    el sesgo (skew) y el cociente entre la cola de arriba y la de abajo
    (percentil 99 sobre |percentil 1|). 1.0 = parejo."""
    m = np.ones(len(t), bool)
    for x in picos_t:
        m &= np.abs(t - x) > lejos
    q = r[m]
    q = q[np.isfinite(q)]
    if len(q) < 50:
        return np.nan, np.nan
    s = float(((q - q.mean()) ** 3).mean() / max(q.std() ** 3, 1e-12))
    p99, p1 = np.percentile(q, 99), np.percentile(q, 1)
    return s, float(p99 / abs(p1)) if p1 != 0 else np.nan


def rebote(r, picos, fps):
    """Cuánto se pasa de largo el gel después de cada contracción: el mínimo
    entre 0.2 y 1.5 s después del pico, como % de la amplitud de ese pico."""
    out = []
    for p in picos:
        a, b = p + int(0.2 * fps), p + int(1.5 * fps)
        if b >= len(r) or r[p] <= 0:
            continue
        v = float(np.nanmin(r[a:b]))
        out.append(100.0 * max(0.0, -v) / float(r[p]))
    return float(np.median(out)) if out else np.nan


def ancho_frames(r, p):
    """Fotogramas seguidos por encima de la mitad de la altura del pico. Una
    contracción real dura varios; un golpe de ruido, uno o dos."""
    A = r[p]
    if not np.isfinite(A) or A <= 0:
        return np.nan
    i = p
    while i - 1 >= 0 and np.isfinite(r[i - 1]) and r[i - 1] >= 0.5 * A:
        i -= 1
    j = p
    while j + 1 < len(r) and np.isfinite(r[j + 1]) and r[j + 1] >= 0.5 * A:
        j += 1
    return j - i + 1


def anchos(t, r, picos, verdaderos, tol=0.3):
    """Ancho mediano de los eventos que caen sobre una contracción verdadera y
    de los que no (los inventados)."""
    buenos, malos = [], []
    for p in picos:
        a = ancho_frames(r, p)
        if not np.isfinite(a):
            continue
        (buenos if np.min(np.abs(verdaderos - t[p])) <= tol else malos).append(a)
    return (float(np.median(buenos)) if buenos else np.nan,
            float(np.median(malos)) if malos else np.nan, len(malos))


def veredicto(n, reportable):
    if reportable and n == N_VERDAD:
        return "correcto"
    if reportable and n > N_VERDAD:
        return "INVENTA"
    if reportable and n < N_VERDAD:
        return "PIERDE (reporta de menos)"
    return "conservador (no informa)"


# -------------------------------------------------------------------- main
def main():
    filas = []
    print("=== sintéticos: 6 contracciones conocidas de 1.5 px, ruido 0.04 px ===")
    for nombre, cfg in ESCENARIOS:
        res = []
        for rho in RHOS:
            for sem in SEMILLAS:
                rng = np.random.default_rng(sem)
                df = serie(cfg, rng, rho)
                a = analizar(df, "center_px", None, None, None, 1.5, separar=False)
                t, r, pk = a["_t"], a["_r"], a["_picos"]
                sk, cola = asimetria(r, t, t[pk])
                est = a.get("estabilidad")
                falsos_k = None
                if est is not None and len(est):
                    cerca = est.iloc[(est["k"] - float(a["k_usado"])).abs().argsort()[:1]]
                    falsos_k = int(cerca["falsos_control"].iloc[0])
                v = veredicto(a["n_eventos"], bool(a["conteo_reportable"]))
                res.append(v)
                an_ok, an_mal, n_mal = anchos(t, r, pk, 5.0 + 10.0 * np.arange(N_VERDAD))
                filas.append({
                    "ancho_verdaderos_frames": an_ok, "ancho_inventados_frames": an_mal,
                    "n_inventados": n_mal,
                    "escenario": nombre, "rho": rho, "semilla": sem,
                    "n_eventos": a["n_eventos"], "verdad": N_VERDAD,
                    "reportable": bool(a["conteo_reportable"]),
                    "veredicto": v,
                    "k_usado": round(float(a["k_usado"]), 3),
                    "falsos_control_en_k": falsos_k,
                    "falsos_control_max": (int(est["falsos_control"].max())
                                           if est is not None and len(est) else None),
                    "hay_meseta": bool(a["hay_meseta"]),
                    "ruido_px": round(float(a["ruido_canal_px"]), 4),
                    "skew_quieto": round(sk, 3) if np.isfinite(sk) else None,
                    "cola_arriba_sobre_abajo": round(cola, 3) if np.isfinite(cola) else None,
                    "rebote_pct": round(rebote(r, pk, 30.0), 1),
                    "motivo": a.get("motivo_no_reportable"),
                })
        c = pd.Series(res).value_counts()
        print(f"  {nombre:26s} " + ", ".join(f"{k}: {v}/{len(res)}" for k, v in c.items()))
    d = pd.DataFrame(filas)
    d.to_csv(AQUI / "sinteticos.csv", index=False)

    print("\n=== resumen por escenario ===")
    g = d.groupby("escenario", sort=False).agg(
        corridas=("veredicto", "size"),
        correcto=("veredicto", lambda x: (x == "correcto").sum()),
        conservador=("veredicto", lambda x: x.str.startswith("conservador").sum()),
        inventa=("veredicto", lambda x: (x == "INVENTA").sum()),
        pierde=("veredicto", lambda x: x.str.startswith("PIERDE").sum()),
        eventos_min=("n_eventos", "min"), eventos_max=("n_eventos", "max"),
        skew=("skew_quieto", "median"), cola=("cola_arriba_sobre_abajo", "median"),
        rebote=("rebote_pct", "median"),
        ancho_ok=("ancho_verdaderos_frames", "median"),
        ancho_mal=("ancho_inventados_frames", "median"))
    print(g.to_string())
    g.to_csv(AQUI / "resumen_escenarios.csv")

    # -------------------------------------------------- los videos reales
    print("\n=== cuánto ruido desparejo y cuánto rebote tienen los videos REALES ===")
    reales = []
    for nombre in VIDEOS:
        carp = PROCESADOS / nombre
        if not carp.is_dir():
            continue
        try:
            df = pd.read_excel(next(carp.glob("serie_temporal_*.xlsx")), sheet_name="diagnostics")
            a = analizar(df, "center_px", None, None, None, 1.5, separar=False)
        except Exception as e:
            print(f"  {nombre}: no se pudo ({e})"); continue
        t, r, pk = a["_t"], a["_r"], a["_picos"]
        sk, cola = asimetria(r, t, t[pk])
        est = a.get("estabilidad")
        an = [ancho_frames(r, p) for p in pk]
        an = [x for x in an if np.isfinite(x)]
        reales.append({"video": nombre, "n_eventos": a["n_eventos"],
                       "ancho_eventos_frames_mediana": float(np.median(an)) if an else None,
                       "ancho_eventos_frames_min": float(np.min(an)) if an else None,
                       "eventos_de_1_frame": int(sum(1 for x in an if x <= 1)),
                       "reportable": bool(a["conteo_reportable"]),
                       "ruido_px": round(float(a["ruido_canal_px"]), 4),
                       "skew_quieto": round(sk, 3) if np.isfinite(sk) else None,
                       "cola_arriba_sobre_abajo": round(cola, 3) if np.isfinite(cola) else None,
                       "rebote_pct": round(rebote(r, pk, 30.0), 1),
                       "falsos_control_max": (int(est["falsos_control"].max())
                                              if est is not None and len(est) else None)})
        print(f"  {nombre:28s} skew {reales[-1]['skew_quieto']:+.2f}  "
              f"cola arriba/abajo {reales[-1]['cola_arriba_sobre_abajo']:.2f}  "
              f"rebote {reales[-1]['rebote_pct']:.0f} %  "
              f"ancho {reales[-1]['ancho_eventos_frames_mediana']} fot. "
              f"(mín {reales[-1]['ancho_eventos_frames_min']}, "
              f"{reales[-1]['eventos_de_1_frame']} de 1 fot.)  "
              f"({reales[-1]['n_eventos']} ev, reportable {reales[-1]['reportable']})")
    pd.DataFrame(reales).to_csv(AQUI / "videos_reales.csv", index=False)
    print("\ntablas: sinteticos.csv, resumen_escenarios.csv, videos_reales.csv")


if __name__ == "__main__":
    main()
