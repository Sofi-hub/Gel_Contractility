"""
scripts/motion_check.py
------------------------
¿QUÉ se mueve en el video?

El pipeline principal mide UNA cosa: el grosor vertical del gel. Ese
observable es CIEGO a dos movimientos perfectamente visibles a ojo:

  * una TRASLACIÓN vertical del puente entero (si los dos bordes bajan
    1 px, el grosor no cambia ni un poco);
  * un movimiento AXIAL (a lo largo del eje del gel), que es lo que
    esperarías de una contracción que acorta el tejido entre anclajes.

Si a ojo se ven contracciones y la serie de grosor sale plana, hay que
saber si el problema es la MEDICIÓN o es que el grosor no es el
observable correcto para este video. Este script lo responde midiendo,
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

Para cada canal se reporta la asimetría (skew) de la señal sin deriva.
Una población de contracciones reales da asimetría claramente NEGATIVA
(muchas excursiones en un sentido, pocas en el otro); el ruido da ~0.

Uso:
    python scripts/motion_check.py --video data/raw_videos/mi_video.mp4 \
        --output-dir data/processed_data/mi_video

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
    Desplazamiento subpíxel de `cur` respecto de `ref`, por correlación
    cruzada normalizada + interpolación parabólica del pico.

    Devuelve (corrimiento_px, correlacion_del_pico). El corrimiento es NaN
    si la correlación del pico no llega a `min_corr`: eso significa que el
    perfil no tiene estructura suficiente para engancharse (por ejemplo, un
    gel sin textura visible a lo largo del eje), y en ese caso el
    "desplazamiento" que saldría sería puro ruido de correlación — un
    resultado sin sentido disfrazado de número.
    """
    a = np.asarray(ref, float) - np.mean(ref)
    b = np.asarray(cur, float) - np.mean(cur)
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    if na < 1e-9 or nb < 1e-9:
        return np.nan, 0.0
    a, b = a / na, b / nb

    lags = np.arange(-max_lag, max_lag + 1)
    n = len(a)
    corr = np.empty(len(lags))
    for i, L in enumerate(lags):
        if L < 0:
            corr[i] = np.dot(a[-L:], b[:n + L])
        elif L > 0:
            corr[i] = np.dot(a[:n - L], b[L:])
        else:
            corr[i] = np.dot(a, b)

    j = int(np.argmax(corr))
    peak = float(corr[j])
    if peak < min_corr:
        return np.nan, peak
    if j == 0 or j == len(corr) - 1:
        return float(lags[j]), peak
    c0, cm, cp = corr[j], corr[j - 1], corr[j + 1]
    denom = cm - 2 * c0 + cp
    delta = 0.0 if abs(denom) < 1e-12 else float(np.clip(0.5 * (cm - cp) / denom, -1, 1))
    return float(lags[j] + delta), peak


def _detrended(v: np.ndarray, fps: float, win_s: float = 2.0) -> np.ndarray:
    """Quita la deriva lenta con una mediana móvil (no produce ringing,
    a diferencia de un filtro pasabanda, que convierte cada evento real
    en un dip flanqueado por dos falsos picos hacia arriba)."""
    s = pd.Series(v)
    w = int(win_s * fps) | 1
    return (s - s.rolling(w, center=True, min_periods=1).median()).to_numpy()


def _describe_channel(name, v, fps, unidad="px"):
    ok = np.isfinite(v)
    if ok.sum() < 30:
        return {"canal": name, "n": int(ok.sum())}
    r = _detrended(v[ok], fps)
    ru = float(np.median(np.abs(r - np.median(r))) * 1.4826)
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
        "frec_dominante_Hz": round(f0, 3) if np.isfinite(f0) else None,
        "pico_sobre_fondo": round(ratio, 2) if np.isfinite(ratio) else None,
    }


def parse_args():
    p = argparse.ArgumentParser(
        description="Diagnostico: que se mueve en el video (grosor / traslacion / axial)",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    p.add_argument("--video", required=True)
    p.add_argument("--maxproj", default=None)
    p.add_argument("--output-dir", default="qc_output")
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
    p.add_argument("--stride", type=int, default=1, help="Procesar 1 de cada N cuadros.")
    p.add_argument("--max-frames", type=int, default=None)
    return p.parse_args()


def main():
    a = parse_args()
    out = Path(a.output_dir); out.mkdir(parents=True, exist_ok=True)

    meta = io_utils.get_video_metadata(a.video)
    fps_video = meta["fps"] if meta["fps"] > 0 else 30.0

    max_proj = (io_utils.load_max_projection(a.maxproj) if a.maxproj
                else io_utils.compute_max_projection(a.video, stride=5))
    roi = preprocessing.auto_detect_roi(
        max_proj, thickness_tolerance=a.roi_tolerance,
        min_gradient_for_roi=a.roi_min_gradient, max_thickness_slope=a.roi_max_slope,
        x_start=a.x_start, x_end=a.x_end)
    describe_roi(roi, max_proj.shape[1])

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

    print(f"\nROI de analisis: x={xs}..{xe} ({len(cols)} columnas)")
    print(f"Interior del gel: {gel.sum()} px por cuadro | franja de fondo: {fondo.sum()} px")
    print("Procesando cuadros...")

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
            "time_s": idx / fps_video,
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
            print(f"  {len(rows)} cuadros...")

    df = pd.DataFrame(rows).dropna(subset=["mov_gel"]).reset_index(drop=True)
    fps = 1.0 / np.median(np.diff(df.time_s.to_numpy()))
    print(f"Listo: {len(df)} cuadros a {fps:.2f} fps\n")

    # --- resumen por canal ---
    canales = ["mov_gel", "mov_fondo", "mov_interior", "mov_gel_t1", "mov_gel_t2",
               "mov_gel_t3", "desp_axial_px", "desp_vert_px"]
    resumen = pd.DataFrame([_describe_channel(c, df[c].to_numpy(), fps) for c in canales])
    print(resumen.to_string(index=False))

    # --- veredicto ---
    # OJO: NO se comparan los niveles absolutos de |dI|. Ese nivel esta
    # dominado por el ruido de sensor (es casi el mismo dentro y fuera del
    # gel), asi que la razon de medianas da ~1.00x aunque el gel se este
    # moviendo muchisimo. Lo que delata movimiento es la MODULACION en el
    # tiempo: cuanto varia |dI| una vez quitada la deriva.
    R = resumen.set_index("canal")["rms_sin_deriva"]
    base = max(float(R.get("mov_fondo", np.nan)), 1e-9)
    r_gel = float(R.get("mov_gel", np.nan)) / base
    r_int = float(R.get("mov_interior", np.nan)) / base

    print()
    print("=" * 74)
    print("VEREDICTO  (modulacion de |I(t)-I(t-1)| respecto del fondo de control)")
    print(f"  zona del gel con bordes : {r_gel:6.1f}x el fondo")
    print(f"  solo el interior        : {r_int:6.1f}x el fondo")
    if r_gel < 2:
        print("  -> NO hay movimiento del gel por encima del fondo. Lo que se ve en la")
        print("     serie de grosor no puede ser deformacion del tejido: es ruido de")
        print("     sensor, parpadeo de iluminacion o compresion del video.")
    elif r_int < 2:
        print("  -> Se mueven SOLO LOS BORDES, no la textura del material. Eso es")
        print("     compatible con un cambio de GROSOR: el observable del pipeline")
        print("     principal es el correcto para este video.")
    else:
        print("  -> Se mueve la TEXTURA del gel, no solo sus bordes. Hay traslacion o")
        print("     movimiento axial. El grosor es CIEGO a eso: mira desp_vert_px y")
        print("     desp_axial_px, y considera usarlos como observable de contraccion.")

    for nom, col in (("axial", "corr_axial"), ("vertical", "corr_vert")):
        if col in df.columns:
            buena = float(np.mean(df[col] > 0.5))
            if buena < 0.8:
                print(f"  OJO: la correlacion {nom} engancha solo en el {100*buena:.0f}% de los "
                      f"cuadros (mediana {df[col].median():.2f}); ese canal no es fiable aca.")

    ax = resumen.set_index("canal")
    for c, etiqueta in [("desp_vert_px", "traslacion vertical de la franja"),
                        ("desp_axial_px", "movimiento axial (a lo largo del gel)")]:
        if c in ax.index and "rms_sin_deriva" in ax.columns:
            print(f"  {etiqueta:38s} RMS = {ax.loc[c,'rms_sin_deriva']:.4f} px | "
                  f"skew = {ax.loc[c,'skew']:+.2f} | "
                  f"pico {ax.loc[c,'frec_dominante_Hz']} Hz ({ax.loc[c,'pico_sobre_fondo']}x fondo)")
    print("  (skew claramente negativo = poblacion de excursiones en un solo sentido =")
    print("   compatible con contracciones. skew ~ 0 = simetrico = ruido.)")
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
    print(f"\nGrafico: {png}")

    xlsx = out / "movimiento.xlsx"
    with pd.ExcelWriter(xlsx) as w:
        df.to_excel(w, sheet_name="movimiento", index=False)
        resumen.to_excel(w, sheet_name="resumen_canales", index=False)
    print(f"Tabla:   {xlsx}")


if __name__ == "__main__":
    main()
