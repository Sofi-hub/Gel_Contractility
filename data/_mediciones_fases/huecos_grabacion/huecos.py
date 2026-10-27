"""Huecos de la grabacion y eventos cercanos (2026-10-27). Solo medicion: no toca
el analisis ni escribe en processed_data.

De donde sale: en D (`../h13_ruido_asimetrico/LEEME.md`) el unico evento de 1
fotograma de Video_prueba (7.28 s) cae tres fotogramas despues de un hueco de
0.398 s en la grabacion. Franco decidio NO implementar el piso de 2 fotogramas;
antes de volver sobre eso queremos saber si los huecos explican eventos raros.

Que se mide, en los 11 de referencia (serie por bordes) y los 9 de Andres
(serie por textura):

  1. Huecos: el eje temporal de cada serie es el de los timestamps del
     contenedor (`time_s`, la columna que escribe el pipeline con
     --base-tiempo pts). Hueco = intervalo entre fotogramas > 1.5 x la mediana
     de los intervalos de ese video. De cada uno: instante, duracion y
     fotogramas faltantes (duracion / mediana - 1).
  2. Para cada evento detectado: distancia al hueco mas cercano (en segundos,
     con signo: positivo = el evento va DESPUES del hueco) y su ancho en
     fotogramas, con la misma regla que `h13.py` y `filtro_ancho.py`.
  3. Tabla de los eventos a menos de 0.5 s de un hueco.

    python data/_mediciones_fases/huecos_grabacion/huecos.py
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
import contraction_report as cr                    # noqa: E402
from referencia import VIDEOS, PROCESADOS          # noqa: E402

AQUI = Path(__file__).resolve().parent
FACTOR = 1.5      # hueco = intervalo > FACTOR x la mediana
CERCA_S = 0.5     # "cerca de un hueco"
ANDRES = ["10V_1", "10V_2", "10V_3", "20V_1", "20V_2", "20V_3", "40V_1", "40V_2", "40V_3"]


def ancho_frames(r, p):
    """Fotogramas seguidos por encima de la mitad de la altura del pico (la misma
    definicion de h13.py). Un fotograma sin medida (NaN) corta el tramo."""
    A = r[p]
    if not np.isfinite(A) or A <= 0:
        return np.nan
    i = p
    while i - 1 >= 0 and np.isfinite(r[i - 1]) and r[i - 1] >= A / 2:
        i -= 1
    j = p
    while j + 1 < len(r) and np.isfinite(r[j + 1]) and r[j + 1] >= A / 2:
        j += 1
    return j - i + 1


def huecos_de(t):
    """Lista de huecos del eje temporal. `fin_s` es el instante del primer
    fotograma despues del corte."""
    dt = np.diff(np.asarray(t, float))
    med = float(np.median(dt))
    out = []
    for i, d in enumerate(dt):
        if d > FACTOR * med:
            out.append({"inicio_s": round(float(t[i]), 3),
                        "fin_s": round(float(t[i + 1]), 3),
                        "duracion_s": round(float(d), 4),
                        "frames_faltantes": int(round(d / med)) - 1,
                        "frame_antes": i})
    return out, med


def main():
    casos = ([(c, "referencia", v[2]) for c, v in VIDEOS.items()]
             + [(c, "Andres", [0.1]) for c in ANDRES])
    f_huecos, f_eventos, f_resumen = [], [], []

    print("=== 1. Huecos en el eje temporal (hueco = dt > 1.5 x mediana) ===")
    for carpeta, grupo, frec in casos:
        if not (PROCESADOS / carpeta).is_dir():
            print(f"  {carpeta}: no esta")
            continue
        serie = next((PROCESADOS / carpeta).glob("serie_temporal_*.xlsx"))
        df = pd.read_excel(serie, sheet_name="diagnostics")
        t = df["time_s"].to_numpy(float)
        hu, med = huecos_de(t)
        for h in hu:
            f_huecos.append({"video": carpeta, "grupo": grupo, **h})

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            a = cr.analizar(df, "center_px", None, None, None, 1.5,
                            frecuencia_estimulo=frec)
        ta, r, pk = a["_t"], a["_r"], a["_picos"]
        ruido = float(a["ruido_canal_px"])
        fin = np.array([h["fin_s"] for h in hu], float)
        dur = np.array([h["duracion_s"] for h in hu], float)

        cerca = 0
        for i, p in enumerate(pk, 1):
            te = float(ta[p])
            an = ancho_frames(r, p)
            fila = {"video": carpeta, "grupo": grupo, "evento": i,
                    "instante_s": round(te, 3),
                    "ancho_frames": None if not np.isfinite(an) else int(an),
                    "amplitud_px": round(float(r[p]), 4),
                    "amplitud_sobre_ruido": round(float(r[p]) / ruido, 1) if ruido else None,
                    "dist_hueco_s": None, "hueco_duracion_s": None,
                    "hueco_fin_s": None, "cerca_de_hueco": False}
            if len(fin):
                j = int(np.argmin(np.abs(te - fin)))
                d = te - fin[j]
                fila.update({"dist_hueco_s": round(float(d), 3),
                             "hueco_duracion_s": float(dur[j]),
                             "hueco_fin_s": float(fin[j]),
                             "cerca_de_hueco": bool(abs(d) <= CERCA_S)})
                cerca += int(abs(d) <= CERCA_S)
            f_eventos.append(fila)

        n_frames = len(t)
        falt = sum(h["frames_faltantes"] for h in hu)
        # Cuanto daria "estar cerca de un hueco" por puro azar: la fraccion de
        # fotogramas del video que esta a menos de CERCA_S de algun hueco. Sin
        # esto, el 58 % de los eventos de 1 fotograma no dice nada: 613 y 341
        # tienen muchos huecos Y casi todos los eventos de 1 fotograma.
        azar = (float(np.mean(np.min(np.abs(t[:, None] - fin[None, :]), axis=1) <= CERCA_S))
                if len(fin) else 0.0)
        f_resumen.append({"video": carpeta, "grupo": grupo, "frames": n_frames,
                          "dt_mediano_ms": round(med * 1000, 3),
                          "huecos": len(hu),
                          "frames_faltantes": falt,
                          "pct_faltantes": round(100 * falt / (n_frames + falt), 2),
                          "hueco_mayor_s": round(max([h["duracion_s"] for h in hu], default=0.0), 4),
                          "eventos": len(pk),
                          "eventos_cerca": cerca,
                          "esperado_por_azar_pct": round(100 * azar, 1),
                          "observado_pct": round(100 * cerca / len(pk), 1) if len(pk) else None,
                          "reportable": bool(a["conteo_reportable"])})
        print(f"  {carpeta[:28]:30s} {n_frames:5d} fot., dt {med*1000:6.2f} ms | "
              f"{len(hu):3d} huecos ({falt:3d} fot. faltantes, {100*falt/(n_frames+falt):4.1f} %), "
              f"mayor {max([h['duracion_s'] for h in hu], default=0.0):6.3f} s | "
              f"{len(pk):3d} ev, {cerca:2d} a < {CERCA_S} s")

    dh = pd.DataFrame(f_huecos)
    de = pd.DataFrame(f_eventos)
    dr = pd.DataFrame(f_resumen)
    dh.to_csv(AQUI / "huecos.csv", index=False)
    de.to_csv(AQUI / "eventos.csv", index=False)
    dr.to_csv(AQUI / "resumen.csv", index=False)

    print("\n=== 2. Resumen por video ===")
    print(dr.to_string(index=False))

    print(f"\n=== 3. Eventos a menos de {CERCA_S} s de un hueco ===")
    c = de[de["cerca_de_hueco"]]
    if len(c):
        print(c[["video", "evento", "instante_s", "dist_hueco_s", "hueco_duracion_s",
                 "ancho_frames", "amplitud_px", "amplitud_sobre_ruido"]].to_string(index=False))
    else:
        print("  (ninguno)")

    print("\n=== 4. Eventos de 1 fotograma: estan cerca de un hueco? ===")
    de["de_1_frame"] = de["ancho_frames"] == 1
    con = de[de["dist_hueco_s"].notna()]
    print("  Todos juntos (los 11 con huecos; los 9 de Andres no tienen ninguno):")
    for etiq, sub in (("de 1 fotograma  ", con[con["de_1_frame"]]),
                      ("de 2+ fotogramas", con[~con["de_1_frame"]])):
        n_cerca = int(sub["cerca_de_hueco"].sum())
        print(f"    {etiq}: {len(sub):3d} eventos, {n_cerca:3d} a < {CERCA_S} s "
              f"({100*n_cerca/max(len(sub),1):4.1f} %), distancia mediana "
              f"{sub['dist_hueco_s'].abs().median():.2f} s")
    print("\n  Dentro de cada video (lo anterior esta dominado por 613 y 341):")
    azar = dict(zip(dr["video"], dr["esperado_por_azar_pct"]))
    print(f"    {'video':26s} {'1 fot.':>14s} {'2+ fot.':>14s} {'azar':>7s}")
    for v, sub in con.groupby("video", sort=False):
        u, m = sub[sub["de_1_frame"]], sub[~sub["de_1_frame"]]
        f = lambda s: (f"{int(s['cerca_de_hueco'].sum())}/{len(s)}"  # noqa: E731
                       f" ({100*s['cerca_de_hueco'].mean():.0f}%)") if len(s) else "-"
        print(f"    {v[:26]:26s} {f(u):>14s} {f(m):>14s} {azar[v]:6.1f}%")
    print("\n=== 5. Solo los huecos GRANDES (>= 0.3 s, como el de 7.28 s) ===")
    grandes = dh[dh["duracion_s"] >= 0.3]
    print(f"  {len(grandes)} huecos de >= 0.3 s en {grandes['video'].nunique()} videos")
    cg = de[(de["hueco_duracion_s"] >= 0.3) & de["cerca_de_hueco"]]
    print(f"  eventos a < {CERCA_S} s de uno de ellos: {len(cg)}")
    if len(cg):
        print(cg[["video", "instante_s", "dist_hueco_s", "hueco_duracion_s",
                  "ancho_frames", "amplitud_sobre_ruido"]].to_string(index=False))

    print(f"\ntablas: huecos.csv ({len(dh)}), eventos.csv ({len(de)}), resumen.csv ({len(dr)})")


if __name__ == "__main__":
    main()
