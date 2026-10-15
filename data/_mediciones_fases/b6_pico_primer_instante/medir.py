"""B6 (2026-10-15): pico = PRIMER instante en que se llega al maximo.

Mide variantes de "llegar al maximo" con ruido, en los 11 videos de referencia,
SIN tocar el codigo: envuelve cin.cinetica_eventos y corre el reporte en memoria.
Solo cambian TTP y RT50 (el instante del pico). Amplitud, onset, eventos, ritmo
y periodo no cambian (el onset se busca hacia atras y entre el primer instante
y el maximo todo esta por encima del 10 %).

    python data/_mediciones_fases/b6_pico_primer_instante/medir.py
"""
from __future__ import annotations
import sys, warnings
from pathlib import Path
import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(RAIZ)); sys.path.insert(0, str(RAIZ / "scripts")); sys.path.insert(0, str(RAIZ / "tests"))
import src.cinetica as cin  # noqa: E402
import contraction_report as cr  # noqa: E402
from referencia import VIDEOS, PROCESADOS, leer_serie  # noqa: E402
from src.output_paths import buscar_serie  # noqa: E402

ORIG = cin.cinetica_eventos

# variante -> (tipo, parametro). "z": A - z*ruido ; "f": fraccion de A
VARIANTES = {
    "actual (fotograma mas alto)": None,
    "1er fotograma >= max - 1 ruido": ("z", 1.0),
    "1er fotograma >= max - 2 ruido": ("z", 2.0),
    "1er fotograma >= 95 % del max": ("f", 0.95),
    "1er fotograma >= 90 % del max": ("f", 0.90),
    "instante interpolado al 95 %": ("fi", 0.95),
    "instante interpolado a max - 1 ruido": ("zi", 1.0),
}
VAR = {"v": None}


def envoltura(t, r, picos, ruido, grosor_reposo=None, ventana_s=1.5, min_frames=cin.MIN_FRAMES):
    ev = ORIG(t, r, picos, ruido, grosor_reposo=grosor_reposo, ventana_s=ventana_s, min_frames=min_frames)
    v = VAR["v"]
    if v is None or not len(ev):
        return ev
    tipo, par = v
    t = np.asarray(t, float); r = np.asarray(r, float)
    ev = ev.copy()
    ev["pico_nuevo_s"] = np.nan
    for k, p in enumerate(np.asarray(picos, int)):
        A = float(r[p])
        nivel = A - par * ruido if tipo in ("z", "zi") else par * A
        lim = max(0, int(picos[k - 1]) if k > 0 else 0)
        q = p
        while q - 1 > lim and np.isfinite(r[q - 1]) and r[q - 1] >= nivel:
            q -= 1
        # q = primer fotograma del tramo contiguo >= nivel que termina en el maximo
        if tipo in ("fi", "zi") and q - 1 >= 0 and np.isfinite(r[q - 1]) and r[q] != r[q - 1]:
            tq = t[q - 1] + (nivel - r[q - 1]) / (r[q] - r[q - 1]) * (t[q] - t[q - 1])
        else:
            tq = t[q]
        ev.loc[k, "pico_nuevo_s"] = tq
        if np.isfinite(ev.loc[k, "ttp_s"]):
            on_s = ev.loc[k, "onset_s"]
            ev.loc[k, "ttp_s"] = float(tq - on_s)
            fr_on = p - int(ev.loc[k, "ttp_frames"])
            ev.loc[k, "ttp_frames"] = int(q - fr_on)
            ev.loc[k, "ttp_medible"] = bool(q - fr_on >= min_frames)
        if np.isfinite(ev.loc[k, "rt50_s"]):
            t50 = float(t[p]) + float(ev.loc[k, "rt50_s"])
            j50 = p + int(ev.loc[k, "rt50_frames"])
            ev.loc[k, "rt50_s"] = float(t50 - tq)
            ev.loc[k, "rt50_frames"] = int(j50 - q)
            ev.loc[k, "rt50_medible"] = bool(j50 - q >= min_frames)
    return ev


cin.cinetica_eventos = envoltura


def ms(x):
    return "—" if x is None or x != x else f"{1000 * x:.0f}"


def resumen_txt(res, m):
    if not res.get(f"{m}_n_eventos"):
        return "—"
    if res.get(f"{m}_reportable"):
        return f"{ms(res[f'{m}_s'])} ({res[f'{m}_n_medibles']}/{res[f'{m}_n_eventos']})"
    if not res.get("conteo_reportable"):
        return "no rep."
    return f"< {ms(res[f'{m}_cota_sup_s'])} ({res[f'{m}_n_medibles']}/{res[f'{m}_n_eventos']})"


filas, detalle = [], []
for carpeta, (_, _, frec) in VIDEOS.items():
    serie = buscar_serie(PROCESADOS / carpeta)
    df, _ = leer_serie(serie)
    for nom, v in VARIANTES.items():
        VAR["v"] = v
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            res = cr.analizar(df, "center_px", None, None, None, 1.5, frecuencia_estimulo=frec)
        filas.append({"video": carpeta, "variante": nom, "grupo": res.get("cinetica_grupo_principal"),
                      "TTP ms (medibles/n)": resumen_txt(res, "ttp"),
                      "RT50 ms (medibles/n)": resumen_txt(res, "rt50"),
                      "n_eventos": res.get("n_eventos"), "amplitud_%": res.get("amplitud_relativa_pct")})
        ev = res["_cinetica"]
        if len(ev) and carpeta in ("Video_466_EXP5_FAPS4_40V", "Video_583_EXP6_CTRL4_40V",
                                   "Video_491_EXP5_CTRL1_36HZ", "Video_476"):
            for _, e in ev.iterrows():
                detalle.append({"video": carpeta, "variante": nom, "evento": int(e["evento"]),
                                "grupo": e.get("grupo"), "meseta_Z2_fr": int(e["meseta_pico_frames"]),
                                "ttp_ms": ms(e["ttp_s"]), "ttp_fr": e["ttp_frames"],
                                "rt50_ms": ms(e["rt50_s"]), "rt50_fr": e["rt50_frames"]})
    print(carpeta, "listo", flush=True)

out = Path(__file__).parent
T = pd.DataFrame(filas)
T.to_csv(out / "tabla_videos.csv", index=False)
pd.DataFrame(detalle).to_csv(out / "detalle_eventos.csv", index=False)
# controles: lo que NO debe cambiar
chk = T.groupby("video")[["n_eventos", "amplitud_%"]].nunique()
print("\ncontrol (1 = igual en todas las variantes):\n", chk.to_string())
for m in ("TTP ms (medibles/n)", "RT50 ms (medibles/n)"):
    print("\n", m)
    print(T.pivot(index="video", columns="variante", values=m)[list(VARIANTES)].to_string())
