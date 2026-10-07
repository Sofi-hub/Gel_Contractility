"""
scripts/motion_check.py
------------------------
¿QUÉ se mueve en el video?

El pipeline principal detecta sobre `center_px` (posición media de los dos
bordes): mide la TRASLACIÓN vertical de la franja por geometría de borde.
Este script la verifica con un método que no usa los bordes (correlación
de intensidad) y mira además el movimiento axial, al que el pipeline es
ciego. Mide,
cuadro a cuadro y dentro de la misma ROI que usa el pipeline:

  mov_gel_*      : movimiento promedio |I(t) - I(t-1)| dentro del gel,
                   en tres tercios axiales. Es el proxy tipo MUSCLEMOTION:
                   detecta CUALQUIER movimiento, venga de donde venga.
  mov_fondo      : lo mismo en una franja de fondo del mismo tamaño.
                   CONTROL: si mov_gel ~ mov_fondo, lo que se ve es ruido
                   de sensor / parpadeo de iluminación / compresión, no
                   movimiento del tejido.
  desp_axial_px  : desplazamiento horizontal subpíxel del patrón de
                   textura del gel, por correlación cruzada contra un
                   cuadro de referencia.
  desp_vert_px   : desplazamiento vertical subpíxel de la franja entera
                   (traslación, no cambio de grosor).

Para cada canal se reporta la asimetría (skew) de la señal sin deriva y
hacia qué lado está la cola pesada. Una población de contracciones da una
cola larga hacia UN lado (cuál, depende del eje); el ruido es simétrico.

VEREDICTO (Fase 4): compara desp_vert_px (intensidad, sin bordes) con
center_px de serie_temporal.xlsx (bordes). Si coinciden en forma y magnitud,
la medida principal queda confirmada por un método independiente. Las
diferencias |I(t)-I(t-1)| son informativas: no deciden nada.

Uso:
    python scripts/motion_check.py --video data/raw_videos/mi_video.mp4 \
        --serie data/processed_data/mi_video/serie_temporal.xlsx

Las salidas van a la carpeta de --serie (la del video). Sin --serie ni
--output-dir, van a qc_output/<nombre del video>/ (antes iban todas a
qc_output/ y se pisaban entre videos).

Salidas:
    07_movimiento.png      grafico multipanel de todos los canales
    movimiento.xlsx        la tabla, para analizar aparte
"""

from __future__ import annotations
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.stats import skew
from scipy.signal import welch

from src import io_utils, preprocessing
from src.pipeline import describe_roi


# ------------------------------------------------------------------
# correlación cruzada subpíxel de perfiles 1-D
# ------------------------------------------------------------------

def _subpixel_shift(ref: np.ndarray, cur: np.ndarray, max_lag: int = 20,
                    min_corr: float = 0.5) -> tuple[float, float]:
    """
    Desplazamiento subpíxel de `cur` respecto de `ref`: correlación de
    Pearson calculada SOLO sobre la parte superpuesta, en cada lag, más
    interpolación parabólica del pico.

    Devuelve (corrimiento_px, correlacion_del_pico). NaN si el pico no llega
    a `min_corr` (el perfil no tiene estructura para engancharse).

    FASE 4 (H51): la versión anterior normalizaba los perfiles ENTEROS y
    después sumaba productos solo sobre la superposición. Eso castiga a los
    lags distintos de cero y achica el corrimiento: con verdad conocida daba
    0.10 px para 1 px (0.18x en los eventos de Video_prueba). Con Pearson por
    lag da 0.997 px para 1 px, y en los eventos reales coincide con
    center_px (cociente 0.96 en Video_prueba, 0.99 en 063, 0.88 en 466).
    Ver claude/propuesta-fase-4.md.
    """
    ref = np.asarray(ref, float)
    cur = np.asarray(cur, float)
    n = len(ref)
    lags = np.arange(-max_lag, max_lag + 1)
    corr = np.full(len(lags), -1.0)
    for i, L in enumerate(lags):
        a = ref[max(0, -L): n - max(0, L)]
        b = cur[max(0, L): n - max(0, -L)]
        a = a - a.mean()
        b = b - b.mean()
        d = np.linalg.norm(a) * np.linalg.norm(b)
        if d > 1e-9:
            corr[i] = float(np.dot(a, b) / d)

    j = int(np.argmax(corr))
    peak = float(corr[j])
    if peak < min_corr:
        return np.nan, peak
    if j == 0 or j == len(corr) - 1:
        return float(lags[j]), peak
    cm, c0, cp = corr[j - 1], corr[j], corr[j + 1]
    denom = cm - 2 * c0 + cp
    delta = 0.0 if abs(denom) < 1e-12 else float(0.5 * (cm - cp) / denom)
    return float(lags[j] + delta), peak


# Mediana movil y MAD: una sola definicion (src/estadistica.py).
from src.estadistica import mad, detrend_median as _detrended


def _describe_channel(name, v, fps, unidad="px"):
    ok = np.isfinite(v)
    if ok.sum() < 30:
        return {"canal": name, "n": int(ok.sum())}
    r = _detrended(v[ok], fps)
    ru = mad(r)
    fr, P = welch(r, fs=fps, nperseg=min(512, len(r) // 4 * 2))
    band = (fr > 0.25) & (fr < 6)
    f0, ratio = np.nan, np.nan
    if band.sum() > 5:
        fb, Pb = fr[band], P[band]
        fondo = np.array([np.median(Pb[np.abs(fb - x) < 0.35]) for x in fb])
        i = int(np.argmax(Pb / fondo))
        f0, ratio = float(fb[i]), float((Pb / fondo)[i])
    return {
        "canal": name,
        "unidad": unidad,
        "rms_sin_deriva": round(float(np.std(r)), 5),
        "ruido_MAD": round(ru, 5),
        "skew": round(float(skew(r)), 3),
        "frac_bajo_-4sigma_pct": round(100 * float(np.mean(r < -4 * ru)), 3),
        "frac_sobre_+4sigma_pct": round(100 * float(np.mean(r > 4 * ru)), 3),
        "frec_dominante_Hz": round(f0, 3) if np.isfinite(f0) else None,
        "pico_sobre_fondo": round(ratio, 2) if np.isfinite(ratio) else None,
    }


def parse_args():
    p = argparse.ArgumentParser(
        description="Diagnostico: que se mueve en el video (grosor / traslacion / axial)",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    p.add_argument("--video", required=True)
    p.add_argument("--maxproj", default=None)
    p.add_argument("--output-dir", default=None,
                   help="Carpeta de salida. Por defecto, la de --serie; si no, "
                        "qc_output/<nombre del video>.")
    p.add_argument("--x-start", type=int, default=None)
    p.add_argument("--x-end", type=int, default=None)
    p.add_argument("--roi-tolerance", type=float, default=0.05)
    p.add_argument("--roi-min-gradient", type=float, default=10.0)
    p.add_argument("--roi-max-slope", type=float, default=0.02)
    p.add_argument("--margin", type=int, default=10,
                   help="Cuantos px hacia AFUERA de cada borde se incluyen en la zona de "
                        "movimiento. El borde es donde el desplazamiento produce mas senal.")
    p.add_argument("--inset", type=int, default=12,
                   help="Cuantos px meterse hacia adentro de cada borde para definir el "
                        "interior del gel (evita que el propio borde domine el movimiento).")
    p.add_argument("--gap", type=int, default=60,
                   help="Separacion (px) entre el gel y la franja de fondo de control.")
    p.add_argument("--serie", default=None,
                   help="serie_temporal.xlsx del mismo video (por defecto, la de --output-dir) "
                        "para comparar desp_vert_px con center_px.")
    p.add_argument("--stride", type=int, default=1, help="Procesar 1 de cada N cuadros.")
    p.add_argument("--max-frames", type=int, default=None)
    p.add_argument("--verbose", action="store_true",
                   help="Imprime tambien la tabla por canal, la zona y el detalle de |dI|. "
                        "Todo queda igual en movimiento.xlsx.")
    return p.parse_args()


def main():
    a = parse_args()
    if a.output_dir:
        out = Path(a.output_dir)
    elif a.serie:
        out = Path(a.serie).parent
    else:
        out = Path("qc_output") / Path(a.video).stem
    out.mkdir(parents=True, exist_ok=True)

    meta = io_utils.get_video_metadata(a.video)
    fps_video = meta["fps"] if meta["fps"] > 0 else 30.0
    # Eje de tiempo por PTS (hallazgo 3 de CLAUDE.md), como el pipeline. Con
    # fotograma / fps declarado el error llegaba a 0.33 s a mitad del video.
    try:
        pts = io_utils.read_pts_seconds(a.video)
    except Exception:
        pts = np.array([])

    max_proj = (io_utils.load_max_projection(a.maxproj) if a.maxproj
                else io_utils.compute_max_projection(a.video, stride=5))
    roi = preprocessing.auto_detect_roi(
        max_proj, thickness_tolerance=a.roi_tolerance,
        min_gradient_for_roi=a.roi_min_gradient, max_thickness_slope=a.roi_max_slope,
        x_start=a.x_start, x_end=a.x_end)
    if a.verbose:
        describe_roi(roi, max_proj.shape[1], detallado=True)

    xs, xe = roi["x_start"], roi["x_end"]
    H, W = max_proj.shape
    cols = np.arange(xs, xe)
    top = roi["top_guess"][xs:xe]
    bot = roi["bottom_guess"][xs:xe]

    # --- máscara del interior del gel y franja de fondo de control ---
    yy = np.arange(H)[:, None]
    # Zona "gel" para el movimiento: INCLUYE los bordes (top-margen ..
    # bot+margen). Ahi es donde un desplazamiento produce el mayor |dI|,
    # porque el gradiente espacial es maximo. Si se midiera solo el interior,
    # un gel de textura pobre daria movimiento cero aunque se estuviera
    # deformando.
    gel = (yy >= (top - a.margin)[None, :]) & (yy <= (bot + a.margin)[None, :])
    # Interior (sin bordes): mide movimiento de la TEXTURA del material.
    interior = (yy >= (top + a.inset)[None, :]) & (yy <= (bot - a.inset)[None, :])
    alto = int(np.median(bot - top)) + 2 * a.margin
    y_fondo0 = int(max(0, np.median(top) - a.gap - alto))
    fondo = np.zeros_like(gel)
    fondo[y_fondo0:y_fondo0 + alto, :] = True
    if fondo.sum() < 100:   # no entra arriba -> probar abajo
        y_fondo0 = int(min(H - alto - 1, np.median(bot) + a.gap))
        fondo[:] = False
        fondo[y_fondo0:y_fondo0 + alto, :] = True

    # bandas verticales para el perfil de traslación
    y0v = int(max(0, np.median(top) - 40))
    y1v = int(min(H, np.median(bot) + 40))

    tercios = np.array_split(np.arange(len(cols)), 3)

    print(f"Zona analizada: columnas {xs} a {xe}. Procesando fotogramas...")
    if a.verbose:
        print(f"  [detalle] interior del gel: {gel.sum()} px por cuadro | franja de fondo: "
              f"{fondo.sum()} px")

    prev = None
    ref_axial = None
    ref_vert = None
    rows = []
    for idx, frame in io_utils.frame_generator(a.video):
        if idx % a.stride != 0:
            continue
        if a.max_frames is not None and len(rows) >= a.max_frames:
            break
        f = frame[:, xs:xe].astype(np.float32)

        # perfiles para la correlación cruzada
        p_ax = np.where(interior[:, :], f, np.nan)
        p_ax = np.nanmean(p_ax, axis=0)                 # perfil a lo largo del eje
        p_ve = f[y0v:y1v, :].mean(axis=1)               # perfil vertical (los dos bordes)

        if ref_axial is None:
            ref_axial, ref_vert = p_ax.copy(), p_ve.copy()

        sa, ca = _subpixel_shift(ref_axial, p_ax, max_lag=25)
        sv, cv = _subpixel_shift(ref_vert, p_ve, max_lag=25)
        r = {
            "frame": idx,
            "time_s": float(pts[idx] - pts[0]) if idx < len(pts) else idx / fps_video,
            "desp_axial_px": sa, "corr_axial": round(ca, 4),
            "desp_vert_px": sv, "corr_vert": round(cv, 4),
        }

        if prev is not None:
            d = np.abs(f - prev)
            r["mov_fondo"] = float(d[fondo].mean())
            r["mov_gel"] = float(d[gel].mean())
            r["mov_interior"] = float(d[interior].mean())
            for k, t in enumerate(tercios, 1):
                sub = np.zeros_like(gel); sub[:, t] = gel[:, t]
                r[f"mov_gel_t{k}"] = float(d[sub].mean())
        prev = f
        rows.append(r)

        if len(rows) % 300 == 0:
            print(f"  {len(rows)} fotogramas...")

    # El primer fotograma no tiene |dI| (no hay anterior): queda NaN, no se borra.
    df = pd.DataFrame(rows)
    fps = 1.0 / np.median(np.diff(df.time_s.to_numpy()))
    print(f"Listo: {len(df)} fotogramas a {fps:.2f} fps")

    # --- resumen por canal ---
    canales = ["mov_gel", "mov_fondo", "mov_interior", "mov_gel_t1", "mov_gel_t2",
               "mov_gel_t3", "desp_axial_px", "desp_vert_px"]
    resumen = pd.DataFrame([_describe_channel(c, df[c].to_numpy(), fps) for c in canales])
    if a.verbose:
        print(resumen.to_string(index=False))

    # --- veredicto (Fase 4, H50) ---
    # El veredicto viejo deducia "cambio de grosor" de que el interior del gel
    # se moviera menos de 2x el fondo. No vale: un gel sin textura que se
    # TRASLADA tambien mueve solo sus bordes. Ahora se usa lo que si distingue:
    # la traslacion vertical medida por INTENSIDAD (desp_vert_px), que no usa
    # los bordes, contra center_px, que si. Si coinciden, la medida principal
    # queda confirmada por un metodo independiente.
    print()
    print("=" * 74)
    print("VEREDICTO: ¿el movimiento medido por bordes (center_px) se confirma midiendo")
    print("           la imagen entera por otro metodo (intensidad)?")
    serie = Path(a.serie) if a.serie else out / "serie_temporal.xlsx"
    veredicto = {"serie_comparada": str(serie)}
    if serie.exists():
        st = pd.read_excel(serie, sheet_name="diagnostics")
        d2 = df[["frame", "desp_vert_px"]].merge(st[["frame", "center_px"]], on="frame", how="inner")
        c = _detrended(d2["center_px"].to_numpy(float), fps)
        dv = _detrended(d2["desp_vert_px"].to_numpy(float), fps)
        ok = np.isfinite(c) & np.isfinite(dv)
        if ok.sum() > 30:
            pend = float(np.dot(c[ok], dv[ok]) / np.dot(c[ok], c[ok]))
            rho = float(np.corrcoef(c[ok], dv[ok])[0, 1])
            print(f"  tamano: {abs(pend):.2f} veces (1 = igual) | forma: correlacion "
                  f"{abs(rho):.2f} (1 = identica)")
            if abs(rho) >= 0.9 and 0.8 <= abs(pend) <= 1.2:
                txt = "CONFIRMA: los dos metodos ven el mismo movimiento (forma y tamano)."
                print(f"  -> {txt}")
            elif abs(rho) >= 0.9:
                txt = ("Coinciden en forma pero no en tamano: revisar (en 466 da 0.88; no se "
                       "sabe cual de los dos esta mas cerca de la verdad).")
                print(f"  -> {txt}")
            else:
                txt = ("NO confirma: el movimiento por intensidad no sigue a los bordes. Mirar "
                       "el video: puede haber vibracion, desenfoque o un borde mal medido.")
                print(f"  -> AVISO: {txt}")
            veredicto.update({"pendiente_desp_vert_sobre_center_px": pend,
                              "correlacion": rho, "veredicto": txt})
    else:
        print(f"  (no se encontro {serie}: correr main.py antes, o pasar --serie, para comparar)")
        veredicto["veredicto"] = "sin serie_temporal para comparar"
    R = resumen.set_index("canal")
    base = max(float(R["rms_sin_deriva"].get("mov_fondo", np.nan)), 1e-9)
    if a.verbose:
        print(f"  [detalle] |dI| (informativo, NO decide nada): gel con bordes "
              f"{float(R['rms_sin_deriva'].get('mov_gel', np.nan)) / base:.1f}x el fondo, "
              f"interior {float(R['rms_sin_deriva'].get('mov_interior', np.nan)) / base:.1f}x.")

    for nom, col in (("axial", "corr_axial"), ("vertical", "corr_vert")):
        if col in df.columns:
            buena = float(np.mean(df[col] > 0.5))
            if buena < 0.8:
                print(f"  AVISO: la medida {nom} por intensidad solo funciona en el {100*buena:.0f}% "
                      f"de los fotogramas (mediana {df[col].median():.2f}); ese canal no es "
                      f"fiable en este video.")

    for c_, etiqueta in [("desp_vert_px", "traslacion vertical de la franja"),
                         ("desp_axial_px", "movimiento axial (a lo largo del gel)")]:
        if c_ in R.index and "rms_sin_deriva" in R.columns:
            arriba, abajo = R.loc[c_, "frac_sobre_+4sigma_pct"], R.loc[c_, "frac_bajo_-4sigma_pct"]
            lado = "hacia +" if arriba > abajo else "hacia -" if abajo > arriba else "pareja"
            if not a.verbose:
                continue
            print(f"  [detalle] {etiqueta:38s} RMS = {R.loc[c_,'rms_sin_deriva']:.4f} px | "
                  f"skew = {R.loc[c_,'skew']:+.2f} | cola pesada {lado} "
                  f"({arriba:.2f}% / {abajo:.2f}% mas alla de +-4 sigma)")
    if a.verbose:
        print("  (una cola pesada hacia UN lado, cualquiera, = poblacion de excursiones =")
        print("   compatible con contracciones; el signo depende del eje. Simetrico = ruido.)")
    print("=" * 74)

    # --- gráfico ---
    t = df.time_s.to_numpy()
    fig, axes = plt.subplots(4, 1, figsize=(12, 10), sharex=True)
    axes[0].plot(t, df.mov_gel, color="crimson", lw=0.8, label="gel")
    axes[0].plot(t, df.mov_fondo, color="gray", lw=0.8, label="fondo (control)")
    axes[0].set_ylabel("|I(t)-I(t-1)|"); axes[0].legend(fontsize=8)
    axes[0].set_title("Movimiento total (detecta cualquier movimiento, en cualquier direccion)")
    for k, col in enumerate(["mov_gel_t1", "mov_gel_t2", "mov_gel_t3"], 1):
        axes[1].plot(t, df[col], lw=0.7, label=f"tercio {k}")
    axes[1].set_ylabel("|I(t)-I(t-1)|"); axes[1].legend(fontsize=8, ncol=3)
    axes[1].set_title("Movimiento por tercio axial (¿es local o es todo el gel?)")
    axes[2].plot(t, df.desp_vert_px, color="steelblue", lw=0.9)
    axes[2].set_ylabel("px"); axes[2].set_title("Traslacion VERTICAL de la franja (el grosor es ciego a esto)")
    axes[3].plot(t, df.desp_axial_px, color="darkgreen", lw=0.9)
    axes[3].set_ylabel("px"); axes[3].set_xlabel("Tiempo (s)")
    axes[3].set_title("Desplazamiento AXIAL de la textura del gel")
    for axx in axes:
        axx.grid(alpha=0.3)
    fig.tight_layout()
    png = out / "07_movimiento.png"
    fig.savefig(png, dpi=140); plt.close(fig)

    xlsx = out / "movimiento.xlsx"
    with pd.ExcelWriter(xlsx) as w:
        df.to_excel(w, sheet_name="movimiento", index=False)
        resumen.to_excel(w, sheet_name="resumen_canales", index=False)
        # El veredicto antes solo salia en pantalla.
        pd.DataFrame([veredicto]).to_excel(w, sheet_name="veredicto", index=False)
    print(f"Archivos en {out}:")
    print(f"  {xlsx.name}")
    print(f"  {png.name}")


if __name__ == "__main__":
    main()
