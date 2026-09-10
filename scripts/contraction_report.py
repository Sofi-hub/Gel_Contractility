"""
scripts/contraction_report.py
------------------------------
Detecta las contracciones usando el observable CORRECTO y mide el
adelgazamiento aunque este por debajo del ruido frame a frame.

POR QUE ESTE SCRIPT EXISTE
---------------------------
Medido sobre dos videos reales del proyecto (Video_prueba, que "funciona",
y Video_063, que "no funcionaba"), la contraccion NO se manifiesta
principalmente como adelgazamiento: se manifiesta como un DESPLAZAMIENTO
VERTICAL de toda la franja. Los dos bordes se mueven juntos, en el mismo
sentido, y solo una parte chica de ese movimiento es un cambio de grosor.

    canal                     Video_prueba     Video_063
    traslacion (center_px)       6.82 px        1.49 px
    adelgazamiento (grosor)      1.26 px        0.28 px
    cociente adelg./trasl.       18.5 %         19.0 %

El cociente es practicamente el MISMO en los dos videos: la mecanica de la
contraccion es igual, lo que cambia es la amplitud (Video_063 contrae ~4.6
veces mas debil). Como el grosor es un observable atenuado ~5x respecto de
la traslacion, en el video debil el adelgazamiento cae por debajo del ruido
por frame y el detector no lo ve. La traslacion, en cambio, sigue estando
44 sigma por encima del ruido.

Consecuencia practica:

  * DETECTAR sobre `center_px` (la posicion media de la franja), no sobre
    `thickness_px`. Prueba de estabilidad del umbral sobre Video_063:

        center_px      k=10..20 -> 5 eventos, 0 falsos    (meseta limpia)
        thickness_px   k=3..4   -> 7 eventos, 5-11 falsos (=ruido)
                       k>=6     -> 0 eventos

  * MEDIR el adelgazamiento promediando los eventos alineados en el tiempo
    (event-locked average). Con 5 eventos el ruido del promedio baja
    sqrt(5) veces y el adelgazamiento de Video_063 pasa de invisible
    (~1 sigma por frame) a 9.7 sigma. El grosor sigue siendo la variable
    biomecanicamente interesante; lo que no sirve es usarlo para DETECTAR.

Uso:
    python scripts/contraction_report.py --input data/processed_data/mi_video/serie_temporal.xlsx
    python scripts/contraction_report.py --input A.xlsx --compare B.xlsx
"""

from __future__ import annotations
import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.signal import find_peaks


# --------------------------------------------------------------------------
def detrend_median(v: np.ndarray, fps: float, win_s: float = 2.0) -> np.ndarray:
    """Quita la deriva lenta con una MEDIANA movil.

    No usar pasabanda: convierte cada evento en un dip flanqueado por dos
    picos falsos, y eso arruina tanto la asimetria como el conteo.
    """
    s = pd.Series(v)
    w = int(win_s * fps) | 1
    return (s - s.rolling(w, center=True, min_periods=1).median()).to_numpy()


def mad(v: np.ndarray) -> float:
    return float(np.median(np.abs(v - np.median(v))) * 1.4826)


def _signo_evento(r: np.ndarray) -> int:
    """+1 si los eventos son excursiones hacia arriba, -1 si hacia abajo.

    Se decide por la cola de la distribucion, no por un supuesto: el signo
    de `center_px` depende de la convencion de la imagen y de si el gel
    sube o baja al contraerse, y eso cambia entre montajes.
    """
    m = mad(r)
    if m <= 0:
        return 1
    arriba = float(np.mean(r > 4 * m))
    abajo = float(np.mean(r < -4 * m))
    return 1 if arriba >= abajo else -1


def escaneo_estabilidad(r: np.ndarray, fps: float, ks=(3, 4, 6, 8, 10, 12, 15, 20),
                        sep_s: float = 2.0) -> pd.DataFrame:
    """Conteo de eventos vs umbral, con control simetrico de falsos positivos.

    El control: correr el mismo detector sobre la senal INVERTIDA. Una
    contraccion solo puede ir en un sentido, asi que todo lo que aparece
    del lado invertido es ruido. Si el conteo real no despega del conteo
    invertido, no hay eventos.
    """
    m = mad(r)
    d = max(1, int(sep_s * fps))
    filas = []
    for k in ks:
        pk, _ = find_peaks(r, height=k * m, distance=d)
        pn, _ = find_peaks(-r, height=k * m, distance=d)
        filas.append({"k": k, "umbral_px": round(k * m, 4),
                      "eventos": len(pk), "falsos_control": len(pn)})
    return pd.DataFrame(filas)


def promedio_alineado(r: np.ndarray, picos: np.ndarray, fps: float,
                      half_s: float = 1.5):
    """Promedia la senal alineando todos los eventos en su pico."""
    h = int(half_s * fps)
    segs = [r[p - h:p + h + 1] for p in picos if p - h >= 0 and p + h + 1 <= len(r)]
    if not segs:
        return None, None, 0
    segs = np.asarray(segs)
    lag = np.arange(-h, h + 1) / fps
    return lag, segs.mean(axis=0), len(segs)


# --------------------------------------------------------------------------
def analizar(df: pd.DataFrame, canal: str, k: float, win_s: float,
             sep_s: float, half_s: float) -> dict:
    t = df["time_s"].to_numpy(float)
    fps = 1.0 / float(np.median(np.diff(t)))

    if canal not in df.columns:
        raise SystemExit(
            f"La serie no tiene la columna '{canal}'. Si el xlsx es de una version "
            f"vieja del pipeline, hay que reprocesar el video: 'center_px' se agrego "
            f"despues.")

    v = df[canal].to_numpy(float)
    r = detrend_median(v, fps, win_s)
    signo = _signo_evento(r)
    r = signo * r                       # ahora los eventos van hacia ARRIBA
    m = mad(r)

    estab = escaneo_estabilidad(r, fps, sep_s=sep_s)
    picos, _ = find_peaks(r, height=k * m, distance=max(1, int(sep_s * fps)))

    # --- grosor: se mide, no se usa para detectar -------------------------
    rg = detrend_median(df["thickness_px"].to_numpy(float), fps, win_s)
    mg = mad(rg)
    lag, prom_g, n_ev = promedio_alineado(rg, picos, fps, half_s)
    _, prom_c, _ = promedio_alineado(r, picos, fps, half_s)

    res = {
        "canal": canal, "fps": fps, "n_frames": len(t), "duracion_s": float(t[-1] - t[0]),
        "signo": signo, "ruido_canal_px": m, "ruido_grosor_px": mg,
        "n_eventos": len(picos), "estabilidad": estab,
        "_t": t, "_r": r, "_picos": picos, "_lag": lag,
        "_prom_g": prom_g, "_prom_c": prom_c, "_n_prom": n_ev,
    }

    if len(picos):
        res["tiempos_s"] = t[picos]
        res["intervalo_mediano_s"] = (float(np.median(np.diff(t[picos])))
                                      if len(picos) > 1 else float("nan"))
        res["amplitud_traslacion_px"] = float(np.median(r[picos]))
    if prom_g is not None and n_ev:
        ruido_prom = mg / np.sqrt(n_ev)
        i = int(np.argmin(prom_g))
        i0 = int(np.argmin(np.abs(lag)))          # frame del pico de traslacion
        pico_c = float(np.max(prom_c)) if prom_c is not None else float("nan")

        res["adelgazamiento_px"] = float(-prom_g[i])
        res["adelgazamiento_sigma"] = float(abs(prom_g[i]) / ruido_prom) if ruido_prom else float("nan")
        res["retardo_adelgazamiento_s"] = float(lag[i])
        res["cociente_adelg_trasl_pct"] = (100 * abs(prom_g[i]) / pico_c) if pico_c else float("nan")

        # Medida ROBUSTA: promedio de los 3 frames posteriores al pico.
        # POR QUE: justo en el frame de maxima velocidad el grosor medido da un
        # salto POSITIVO (el borde se emborrona por el movimiento y los dos
        # bordes se "abren"). Ese frame no es adelgazamiento, es un artefacto de
        # motion blur, y contamina el minimo si cae cerca. Promediar la cola
        # posterior lo evita.
        j0, j1 = i0 + 1, min(i0 + 4, len(prom_g))
        cola = prom_g[j0:j1]
        if len(cola):
            res["adelgazamiento_robusto_px"] = float(-cola.mean())
            res["adelgazamiento_robusto_sigma"] = (
                float(abs(cola.mean()) / (ruido_prom / np.sqrt(len(cola)))) if ruido_prom else float("nan"))
            res["cociente_robusto_pct"] = (100 * abs(cola.mean()) / pico_c) if pico_c else float("nan")

        # Aviso de motion blur: excursion POSITIVA del grosor cerca del pico.
        ven = prom_g[max(0, i0 - 2):min(len(prom_g), i0 + 2)]
        if len(ven) and ven.max() > 3 * ruido_prom:
            res["blur_px"] = float(ven.max())
            res["blur_sigma"] = float(ven.max() / ruido_prom)
    return res


def imprimir(nombre: str, a: dict) -> None:
    print("=" * 74)
    print(f"{nombre}   ({a['n_frames']} frames, {a['duracion_s']:.1f} s, {a['fps']:.2f} fps)")
    print(f"  canal de deteccion: {a['canal']}  "
          f"(eventos hacia {'arriba' if a['signo'] > 0 else 'abajo'} en la imagen)")
    print(f"  ruido del canal: {a['ruido_canal_px']:.4f} px | "
          f"ruido del grosor: {a['ruido_grosor_px']:.4f} px")
    print()
    print("  estabilidad del umbral (falsos = mismo detector sobre la senal invertida)")
    print("      %5s %12s %10s %16s" % ("k", "umbral_px", "eventos", "falsos_control"))
    for _, f in a["estabilidad"].iterrows():
        print("      %5g %12.4f %10d %16d" % (f.k, f.umbral_px, f.eventos, f.falsos_control))
    print()
    if not a["n_eventos"]:
        print("  NO se detectaron eventos con el umbral elegido.")
        return
    print(f"  EVENTOS: {a['n_eventos']}")
    print("    tiempos (s): " + ", ".join(f"{x:.2f}" for x in a["tiempos_s"]))
    if a["n_eventos"] > 1:
        iv = a["intervalo_mediano_s"]
        print(f"    intervalo mediano: {iv:.3f} s  ({1 / iv:.4f} Hz)")
    print(f"    traslacion (amplitud mediana): {a['amplitud_traslacion_px']:.3f} px")
    if "adelgazamiento_px" in a:
        print(f"    adelgazamiento (promedio de {a['_n_prom']} eventos alineados)")
        print(f"       minimo:  {a['adelgazamiento_px']:.4f} px  "
              f"({a['adelgazamiento_sigma']:.1f} sigma, a {a['retardo_adelgazamiento_s']:+.2f} s del pico)"
              f"   = {a['cociente_adelg_trasl_pct']:.1f}% de la traslacion")
        if "adelgazamiento_robusto_px" in a:
            print(f"       robusto: {a['adelgazamiento_robusto_px']:.4f} px  "
                  f"({a['adelgazamiento_robusto_sigma']:.1f} sigma, 3 frames post-pico)"
                  f"   = {a['cociente_robusto_pct']:.1f}% de la traslacion")
        if "blur_sigma" in a:
            print(f"    AVISO: el grosor da un salto POSITIVO de {a['blur_px']:.3f} px "
                  f"({a['blur_sigma']:.1f} sigma) en el frame mas rapido. Eso no es "
                  f"engrosamiento: es motion blur (el borde se emborrona y los dos bordes "
                  f"se abren). Usa la medida robusta, no el minimo.")


def graficar(resultados, out_png: Path) -> None:
    n = len(resultados)
    fig, axes = plt.subplots(n, 2, figsize=(13, 3.1 * n), squeeze=False,
                             gridspec_kw={"width_ratios": [2.4, 1]})
    for i, (nombre, a) in enumerate(resultados):
        ax, ax2 = axes[i, 0], axes[i, 1]
        ax.plot(a["_t"], a["_r"], color="#1f77b4", lw=0.7, label=a["canal"])
        if a["n_eventos"]:
            ax.plot(a["_t"][a["_picos"]], a["_r"][a["_picos"]], "v", color="crimson",
                    ms=7, label=f"{a['n_eventos']} eventos")
        ax.axhline(0, color="gray", lw=0.6)
        ax.set_ylabel(f"{a['canal']} (sin deriva, px)")
        ax.set_title(nombre, fontsize=10)
        ax.legend(fontsize=8, loc="upper right")
        ax.grid(alpha=0.3)

        if a["_lag"] is not None:
            ax2.plot(a["_lag"], a["_prom_c"], color="#1f77b4", lw=1.4, label="traslacion")
            ax2b = ax2.twinx()
            ax2b.plot(a["_lag"], a["_prom_g"], color="crimson", lw=1.4, label="grosor")
            ax2b.axhline(0, color="crimson", lw=0.5, ls=":")
            ax2.set_xlabel("t respecto del pico (s)")
            ax2.set_ylabel("traslacion (px)", color="#1f77b4")
            ax2b.set_ylabel("grosor (px)", color="crimson")
            ax2.set_title(f"promedio de {a['_n_prom']} eventos", fontsize=9)
            ax2.grid(alpha=0.3)
    axes[-1, 0].set_xlabel("Tiempo (s)")
    fig.tight_layout()
    fig.savefig(out_png, dpi=140)
    plt.close(fig)


def _leer(path: str) -> pd.DataFrame:
    p = Path(path)
    return pd.read_csv(p) if p.suffix == ".csv" else pd.read_excel(p, sheet_name="diagnostics")


def parse_args():
    p = argparse.ArgumentParser(
        description="Detecta contracciones sobre center_px y mide el adelgazamiento "
                    "por promedio de eventos alineados.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    p.add_argument("--input", required=True)
    p.add_argument("--compare", default=None,
                   help="Segunda serie, como control (ideal: un video que ya sabes que contrae).")
    p.add_argument("--canal", default="center_px",
                   help="Observable de DETECCION. 'center_px' = posicion media de la franja "
                        "(sensible a traslacion). 'thickness_px' solo si ya verificaste que "
                        "en tu montaje la contraccion es adelgazamiento puro.")
    p.add_argument("--k", type=float, default=8.0,
                   help="Umbral en unidades de MAD. Elegilo en la meseta del escaneo.")
    p.add_argument("--win-s", type=float, default=2.0,
                   help="Ventana (s) de la mediana movil que quita la deriva.")
    p.add_argument("--sep-s", type=float, default=2.0,
                   help="Separacion minima entre eventos (s).")
    p.add_argument("--half-s", type=float, default=1.5,
                   help="Semiventana (s) del promedio de eventos alineados.")
    p.add_argument("--output-dir", default=None)
    return p.parse_args()


def main():
    a = parse_args()
    entradas = [(Path(a.input).parent.name or Path(a.input).stem, _leer(a.input))]
    if a.compare:
        entradas.append((Path(a.compare).parent.name or Path(a.compare).stem, _leer(a.compare)))

    resultados = []
    for nombre, df in entradas:
        r = analizar(df, a.canal, a.k, a.win_s, a.sep_s, a.half_s)
        imprimir(nombre, r)
        resultados.append((nombre, r))

    print()
    print("  Como leer el escaneo: si 'eventos' tiene una MESETA (no cambia al subir k)")
    print("  y 'falsos_control' es 0 en esa meseta, los eventos son reales. Si el conteo")
    print("  cae monotonamente y hay falsos parecidos al conteo real, es ruido.")

    out = Path(a.output_dir) if a.output_dir else Path(a.input).parent
    out.mkdir(parents=True, exist_ok=True)
    graficar(resultados, out / "09_contracciones.png")

    with pd.ExcelWriter(out / "contracciones.xlsx", engine="openpyxl") as w:
        for nombre, r in resultados:
            r["estabilidad"].to_excel(w, sheet_name=f"estab_{nombre[:20]}", index=False)
            fila = {kk: vv for kk, vv in r.items()
                    if not kk.startswith("_") and kk not in ("estabilidad", "tiempos_s")}
            pd.DataFrame([fila]).to_excel(w, sheet_name=f"resumen_{nombre[:18]}", index=False)
            if r["n_eventos"]:
                pd.DataFrame({"evento": np.arange(1, r["n_eventos"] + 1),
                              "tiempo_s": r["tiempos_s"],
                              "amplitud_px": r["_r"][r["_picos"]]}
                             ).to_excel(w, sheet_name=f"eventos_{nombre[:18]}", index=False)

    print(f"\nGrafico: {out / '09_contracciones.png'}")
    print(f"Tabla:   {out / 'contracciones.xlsx'}")


if __name__ == "__main__":
    main()
