"""D (2026-10-27). ¿Qué sacaría un filtro por DURACIÓN del evento? Solo medición:
no toca el análisis ni escribe en processed_data.

De la medición del 2026-10-26 (`LEEME.md`): en los sintéticos, las contracciones
inventadas por el control duran **1 fotograma** por encima de la mitad de su
altura, y las verdaderas 2.5–3. Un piso de 2 fotogramas borraría todos los
inventados y ninguno de los verdaderos. Acá se mira qué pasaría en los videos
reales antes de proponer nada.

Qué se corre: los 11 de referencia (con su serie vigente, por bordes) y los 9 de
Andrés (sus series, por textura). De cada evento se anota el ancho en fotogramas
—los que están seguidos por encima de la mitad de la altura del pico, la misma
regla que `h13.py`— y se marca cuáles se caerían con un piso de 2.

Además: figura de la señal alrededor del evento de Video_prueba que se caería, y
el fotograma del video en ese instante, para mirarlo a ojo.

    python data/_mediciones_fases/h13_ruido_asimetrico/filtro_ancho.py
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
from referencia import VIDEOS, CRUDOS, PROCESADOS  # noqa: E402

AQUI = Path(__file__).resolve().parent
PISO = 2          # fotogramas minimos que se probarian
ANDRES = ["10V_1", "10V_2", "10V_3", "20V_1", "20V_2", "20V_3", "40V_1", "40V_2", "40V_3"]


def ancho_frames(r, p):
    """Fotogramas seguidos por encima de la mitad de la altura del pico (la
    misma definicion de h13.py). Un fotograma sin medida (NaN) corta el tramo."""
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


def analizar_carpeta(carpeta, frec):
    s = next((PROCESADOS / carpeta).glob("serie_temporal_*.xlsx"))
    df = pd.read_excel(s, sheet_name="diagnostics")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return cr.analizar(df, "center_px", None, None, None, 1.5,
                           frecuencia_estimulo=frec)


def eventos_de(nombre, grupo, a):
    t, r, pk = a["_t"], a["_r"], a["_picos"]
    ruido = float(a["ruido_canal_px"])
    out = []
    for i, p in enumerate(pk, 1):
        an = ancho_frames(r, p)
        out.append({"video": nombre, "grupo": grupo, "evento": i,
                    "instante_s": round(float(t[p]), 3),
                    "amplitud_px": round(float(r[p]), 4),
                    "amplitud_sobre_ruido": round(float(r[p]) / ruido, 1) if ruido else None,
                    "ancho_frames": None if not np.isfinite(an) else int(an),
                    "se_cae_con_piso_2": bool(np.isfinite(an) and an < PISO)})
    return out


def figura_prueba(a, instante, destino_png, destino_jpg):
    """La senal alrededor del evento que se caeria, y el fotograma del video."""
    import matplotlib
    matplotlib.use("Agg")
    from matplotlib.figure import Figure
    t, r, pk = a["_t"], a["_r"], a["_picos"]
    ruido = float(a["ruido_canal_px"])
    m = np.abs(t - instante) <= 1.5
    fig = Figure(figsize=(9, 3.4), dpi=140)
    ax = fig.add_subplot(111)
    ax.plot(t[m], r[m], color="#1f77b4", marker="o", ms=3, lw=1.0, label="senal sin deriva")
    ax.axhline(0, color="#999", lw=0.6)
    for y, c, lab in ((ruido, "#aaa", "1 x ruido"), (a["k_usado"] * ruido, "#d62728",
                                                     f"umbral k={a['k_usado']:g}")):
        ax.axhline(y, color=c, lw=0.8, ls="--", label=lab)
    for p in pk:
        if abs(t[p] - instante) <= 1.5:
            es = abs(t[p] - instante) < 1e-6
            ax.plot(t[p], r[p], "v", color="#d62728" if es else "#2ca02c", ms=9)
            ax.annotate(f"{t[p]:.2f} s\n{ancho_frames(r, p):.0f} fot.",
                        (t[p], r[p]), textcoords="offset points", xytext=(0, 10),
                        ha="center", fontsize=7)
    ax.set_xlabel("tiempo (s)")
    ax.set_ylabel("center_px sin deriva")
    ax.set_title(f"Video_prueba: el evento de {instante:.2f} s dura 1 fotograma "
                 f"(rojo); en verde, los vecinos")
    ax.legend(fontsize=7, loc="upper right")
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(destino_png)

    try:
        import cv2
        cap = cv2.VideoCapture(str(CRUDOS / VIDEOS["Video_prueba"][0]))
        p = int(np.argmin(np.abs(t - instante)))
        cap.set(cv2.CAP_PROP_POS_FRAMES, p)
        ok, img = cap.read()
        cap.release()
        if ok:
            # cv2.imwrite no escribe en rutas con acentos (Analisis_de_Datos)
            bien, buf = cv2.imencode(".jpg", img, [int(cv2.IMWRITE_JPEG_QUALITY), 92])
            if bien:
                Path(destino_jpg).write_bytes(buf.tobytes())
                return destino_png, destino_jpg
    except Exception as e:                            # noqa: BLE001
        print(f"  (no se pudo sacar el fotograma: {type(e).__name__}: {e})")
    return destino_png, None


def main():
    filas = []
    guardados = {}
    print("=== 11 de referencia (bordes) + 9 de Andres (textura) ===")
    casos = ([(c, c, "referencia", v[2]) for c, v in VIDEOS.items()]
             + [(c, c, "Andres", [0.1]) for c in ANDRES])
    for carpeta, nombre, grupo, frec in casos:
        if not (PROCESADOS / carpeta).is_dir():
            print(f"  {nombre}: no esta"); continue
        a = analizar_carpeta(carpeta, frec)
        guardados[carpeta] = a
        ev = eventos_de(nombre, grupo, a)
        filas += ev
        caen = [e for e in ev if e["se_cae_con_piso_2"]]
        anchos = [e["ancho_frames"] for e in ev if e["ancho_frames"] is not None]
        cuales = ", ".join("%.2f s" % e["instante_s"] for e in caen)
        print(f"  {nombre[:28]:30s} {len(ev):3d} ev, reportable "
              f"{str(bool(a['conteo_reportable'])):5s} | ancho mediano "
              f"{np.median(anchos) if anchos else float('nan'):5.1f} fot. | "
              f"se caerian {len(caen):2d} -> quedarian {len(ev) - len(caen):3d}"
              + (f"  ({cuales})" if caen else ""))

    d = pd.DataFrame(filas)
    d.to_csv(AQUI / "filtro_ancho_eventos.csv", index=False)

    res = (d.groupby(["grupo", "video"], sort=False)
           .agg(eventos=("evento", "count"),
                ancho_mediano=("ancho_frames", "median"),
                ancho_min=("ancho_frames", "min"),
                de_1_frame=("se_cae_con_piso_2", "sum"))
           .reset_index())
    res["quedarian"] = res["eventos"] - res["de_1_frame"]
    res.to_csv(AQUI / "filtro_ancho_resumen.csv", index=False)
    print("\n" + res.to_string(index=False))

    # --- el evento de Video_prueba que se caeria ---------------------------
    cae = d[(d["video"] == "Video_prueba") & d["se_cae_con_piso_2"]]
    if len(cae):
        inst = float(cae["instante_s"].iloc[0])
        png, jpg = figura_prueba(guardados["Video_prueba"], inst,
                                 AQUI / "prueba_evento_1_frame.png",
                                 AQUI / "prueba_evento_1_frame_fotograma.jpg")
        print(f"\nVideo_prueba: el evento de {inst:.2f} s dura 1 fotograma "
              f"(amplitud {float(cae['amplitud_px'].iloc[0]):.3f} px = "
              f"{float(cae['amplitud_sobre_ruido'].iloc[0]):.1f} x el ruido)")
        print(f"  figura: {Path(png).name}" + (f" y {Path(jpg).name}" if jpg else ""))
    else:
        print("\nVideo_prueba: ningun evento de 1 fotograma")
    print(f"\ntablas: filtro_ancho_eventos.csv ({len(d)}), filtro_ancho_resumen.csv")


if __name__ == "__main__":
    main()
