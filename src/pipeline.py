"""
pipeline.py
-----------
Orquestador: une preprocessing + edge_detection + robust_fitting para
convertir un video crudo en una serie temporal de grosor, con control de
calidad por frame.

CAMBIOS RESPECTO DE LA VERSIÓN ANTERIOR
----------------------------------------
1. `ransac_degree` pasa de 1 a 2 y `ransac_residual_threshold` pasa de
   1.5 fijo a None (adaptativo). Ver el encabezado de robust_fitting.py:
   con los valores viejos, el ajuste solo generaba ~0.25 px de std en la
   serie de grosor con el gel inmóvil.
2. La ROI se puede forzar a mano (`roi_x_start` / `roi_x_end`) y los
   parámetros del auto-ROI son configurables.
3. BUG CORREGIDO en `frame_quality`: `n_outlier_columns` suma los dos
   bordes (máximo 2N), pero se comparaba contra `0.3 * N`. El umbral
   efectivo era 15%, no 30%. Ahora se calcula la fracción sobre 2N.
4. Se agregan al DataFrame `residual_top_px` y `residual_bottom_px` (MAD
   de los residuos del ajuste, por frame). Si esa columna se mueve junto
   con el grosor, lo que estás midiendo es el ajuste, no el gel.
5. `process_video` deja el resultado del auto-ROI en `df.attrs["roi"]`
   para poder reportarlo y graficarlo sin recalcularlo.
"""

from __future__ import annotations
from dataclasses import dataclass
import numpy as np
import pandas as pd
from scipy.signal import savgol_filter

from . import io_utils
from . import preprocessing
from . import edge_detection
from . import robust_fitting


@dataclass
class PipelineConfig:
    # --- muestreo y detección de borde ---
    n_columns: int = 60          # cuántas columnas muestrear por frame.
                                  # Subirlo NO arregla un problema de
                                  # modelo: si el polinomio no representa
                                  # la geometría, más columnas es más
                                  # ruido, no menos.
    half_window: int = 15        # ventana de búsqueda del borde (px)
    min_gradient: float = 5.0    # gradiente mínimo para aceptar un borde.
                                  # OJO: se compara contra el gradiente de
                                  # la imagen YA pasada por CLAHE, así que
                                  # su valor no es portable entre videos
                                  # si cambiás use_clahe.
    edge_method: str = "parabolic"   # "parabolic" o "sigmoid"

    # --- ajuste robusto ---
    fit_method: str = "ransac"       # "ransac" o "median"
    ransac_degree: int = 2
    ransac_residual_threshold: float | None = None   # None = adaptativo
    ransac_residual_k: float = 3.0
    ransac_residual_floor: float = 0.4

    # --- ROI / gauge region ---
    roi_x_start: int | None = None   # override manual
    roi_x_end: int | None = None
    roi_thickness_tolerance: float = 0.05
    roi_min_gradient: float = 10.0
    roi_max_slope: float = 0.02
    # Ancho minimo de la ROI = roi_min_columns * este espaciado (ver el
    # comentario ANCHO MINIMO en auto_detect_roi).
    roi_min_column_spacing_px: float = 3.0
    # Piso de columnas (H19, Fase 3). n_columns pasa a ser el MAXIMO: en una
    # ROI angosta se usan ancho // espaciado columnas, nunca menos que esto.
    roi_min_columns: int = 40
    # Criterio de aceptacion del protocolo: variacion de grosor dentro de
    # la ROI. Por encima de esto la ROI incluye el hombro de un anclaje.
    roi_max_variacion_pct: float = 6.0

    # --- base de tiempo ---
    # El fps que declara el archivo de video es poco confiable: medido
    # contra el estimulador da 300.0 fotogramas por periodo en 4 videos
    # independientes, o sea fps real = 30.000. Este override lo fuerza.
    fps_override: float | None = None
    # "frames": time = frame / fps (supone que no falta ningun frame).
    # "pts": usa el timestamp de cada frame que trae el contenedor. Es lo
    # correcto cuando la grabacion perdio frames (ver read_pts_seconds).
    base_tiempo: str = "pts"

    # --- calibración y preproceso ---
    px_to_mm: float = 1.0        # mm por píxel. Calibrar con retícula.
    use_clahe: bool = True
    use_denoise: bool = False

    # --- suavizado temporal final ---
    savgol_window: int = 11      # debe ser impar
    savgol_polyorder: int = 3

    # --- QC ---
    low_quality_frac: float = 0.30   # fracción de columnas descartadas
                                      # (sobre 2N) a partir de la cual el
                                      # frame se marca LOW_QUALITY


def _fit(x, y, config: PipelineConfig):
    if config.fit_method == "ransac":
        return robust_fitting.fit_edge_ransac(
            x, y,
            degree=config.ransac_degree,
            residual_threshold=config.ransac_residual_threshold,
            residual_k=config.ransac_residual_k,
            residual_floor=config.ransac_residual_floor,
        )
    return robust_fitting.fit_edge_median(x, y)


def process_frame(
    frame: np.ndarray,
    x_positions: np.ndarray,
    top_guess: np.ndarray,
    bottom_guess: np.ndarray,
    config: PipelineConfig,
) -> dict:
    """Procesa UN frame y devuelve grosor + métricas de calidad."""
    frame_p = preprocessing.preprocess_frame(
        frame, use_clahe=config.use_clahe, use_denoise=config.use_denoise
    )

    x, y_top, y_bot, quality = edge_detection.extract_edges_for_frame(
        frame_p, x_positions, top_guess, bottom_guess,
        half_window=config.half_window, method=config.edge_method,
        min_gradient=config.min_gradient,
    )

    top_fit = _fit(x, y_top, config)
    bot_fit = _fit(x, y_bot, config)

    n_slots = 2 * len(x_positions)   # dos bordes por columna

    if top_fit is None or bot_fit is None:
        # Frame demasiado degradado (ej. burbuja gigante tapando todo)
        return {
            "thickness_px": np.nan,
            "thickness_mm": np.nan,
            "n_outlier_columns": n_slots,
            "outlier_frac": 1.0,
            "y_top_px": np.nan,
            "y_bottom_px": np.nan,
            "center_px": np.nan,
            "residual_top_px": np.nan,
            "residual_bottom_px": np.nan,
            "frame_quality": "REJECTED",
        }

    thickness_per_column = bot_fit.y_fitted - top_fit.y_fitted
    thickness_px = float(np.median(thickness_per_column))

    # Posición de cada borde por separado, no solo su diferencia.
    # POR QUÉ: el grosor es ciego a una TRASLACIÓN vertical del gel entero
    # (si los dos bordes bajan 1 px, el grosor no cambia). Si a ojo se ven
    # contracciones pero la serie de grosor está plana, lo que hay que mirar
    # es `center_px`. Guardarlo cuesta cero y distingue los dos casos.
    y_top_px = float(np.median(top_fit.y_fitted))
    y_bottom_px = float(np.median(bot_fit.y_fitted))

    n_outliers = int((~top_fit.inlier_mask).sum() + (~bot_fit.inlier_mask).sum())
    frac = n_outliers / n_slots

    return {
        "thickness_px": thickness_px,
        "thickness_mm": thickness_px * config.px_to_mm,
        "n_outlier_columns": n_outliers,
        "outlier_frac": round(frac, 4),
        "y_top_px": round(y_top_px, 4),
        "y_bottom_px": round(y_bottom_px, 4),
        "center_px": round(0.5 * (y_top_px + y_bottom_px), 4),
        "residual_top_px": round(float(top_fit.residual_px), 4),
        "residual_bottom_px": round(float(bot_fit.residual_px), 4),
        "frame_quality": "OK" if frac < config.low_quality_frac else "LOW_QUALITY",
        # Residuo de cada columna (borde medido - parabola). No va a la tabla:
        # process_video lo acumula para el "error de modelo" (Fase 4, H24).
        "_rcol_top": y_top - top_fit.y_fitted,
        "_rcol_bot": y_bot - bot_fit.y_fitted,
    }


def process_video(
    video_path: str,
    max_projection_path: str | None = None,
    config: PipelineConfig | None = None,
    verbose: bool = True,
    detallado: bool = False,
) -> pd.DataFrame:
    """
    Procesa un video completo y devuelve un DataFrame con:
        frame, time_s, thickness_px, thickness_mm, n_outlier_columns,
        outlier_frac, residual_top_px, residual_bottom_px,
        frame_quality, thickness_mm_smooth

    El resultado del auto-ROI queda en `df.attrs["roi"]`.
    """
    if config is None:
        config = PipelineConfig()

    meta = io_utils.get_video_metadata(video_path)
    if config.fps_override is not None and config.fps_override > 0:
        fps = float(config.fps_override)
    else:
        fps = meta["fps"] if meta["fps"] > 0 else 30.0

    # Timestamps reales del contenedor. Se leen SIEMPRE, aunque la base de
    # tiempo sea "frames", porque comparar la duracion que declaran contra
    # n_frames/fps es lo que detecta que la grabacion perdio frames.
    try:
        pts = io_utils.read_pts_seconds(video_path)
    except Exception:
        pts = np.array([])
    n_pts = len(pts)
    dur_pts = float(pts[-1] - pts[0]) if n_pts > 1 else float("nan")

    # DETECCION DE FRAMES PERDIDOS, a partir del espaciado de los timestamps.
    #
    # No sirve comparar contra el fps que declara el archivo: ese fps es el
    # PROMEDIO (n-1)/duracion, asi que ya tiene los faltantes adentro y da
    # cero por construccion. El espaciado tipico entre frames consecutivos,
    # en cambio, es el periodo real de captura: su mediana da 33.333 ms
    # (= 30.0003 fps) en los cinco videos medidos, independientemente del
    # fps declarado, que va de 28.97 a 29.87. Los huecos son los dt que
    # valen un multiplo entero de esa mediana.
    if n_pts > 2:
        dts = np.diff(pts)
        dt_med = float(np.median(dts))
        fps_pts = 1.0 / dt_med if dt_med > 0 else float("nan")
        huecos = dts[dts > 1.5 * dt_med]
        faltantes = float(np.round((huecos / dt_med - 1).sum()))
        frac_faltantes = faltantes / max(n_pts + faltantes, 1.0)
        n_huecos = int(len(huecos))
    else:
        dt_med = fps_pts = faltantes = frac_faltantes = float("nan")
        n_huecos = 0

    if max_projection_path is not None:
        max_proj = io_utils.load_max_projection(max_projection_path)
    else:
        max_proj = io_utils.compute_max_projection(video_path, stride=5)

    roi = preprocessing.auto_detect_roi(
        max_proj,
        thickness_tolerance=config.roi_thickness_tolerance,
        min_gradient_for_roi=config.roi_min_gradient,
        max_thickness_slope=config.roi_max_slope,
        x_start=config.roi_x_start,
        x_end=config.roi_x_end,
        n_columns=config.n_columns,
        min_column_spacing_px=config.roi_min_column_spacing_px,
        min_columns=config.roi_min_columns,
        max_variacion_pct=config.roi_max_variacion_pct,
    )

    if verbose:
        describe_roi(roi, max_proj.shape[1], detallado=detallado)

    usar_pts = (config.base_tiempo == "pts") and n_pts > 1
    if config.base_tiempo == "pts" and not usar_pts:
        print("  AVISO: el video no trae marcas de tiempo usables; el eje de tiempo se "
              "arma con fotograma / fps.")

    n_cols = int(roi.get("roi_quality", {}).get("n_columnas_usadas") or config.n_columns)
    x_positions = np.linspace(roi["x_start"], roi["x_end"] - 1, n_cols).astype(int)

    rows = []
    rcol = {"top": [], "bot": []}
    for idx, frame in io_utils.frame_generator(video_path):
        result = process_frame(frame, x_positions, roi["top_guess"], roi["bottom_guess"], config)
        for b in ("top", "bot"):
            rcol[b].append(result.pop(f"_rcol_{b}", np.full(len(x_positions), np.nan)))
        result["frame"] = idx
        if usar_pts and idx < n_pts:
            result["time_s"] = float(pts[idx] - pts[0])
        else:
            result["time_s"] = idx / fps
        rows.append(result)

    df = pd.DataFrame(rows)
    df.attrs["fps"] = fps
    df.attrs["fps_declarado"] = meta["fps"]
    df.attrs["base_tiempo"] = "pts" if usar_pts else "frames"
    df.attrs["duracion_pts_s"] = dur_pts
    df.attrs["frames_faltantes"] = faltantes
    df.attrs["frac_frames_faltantes"] = frac_faltantes
    df.attrs["fps_segun_pts"] = fps_pts
    df.attrs["n_huecos_pts"] = n_huecos

    # ERROR DE MODELO (Fase 4, H24): cuanto se aparta la parabola del borde
    # de forma ESTABLE. Para cada columna, la mediana en el tiempo de su
    # residuo; despues, el RMS sobre columnas. Es comparable entre ROIs (no
    # depende del umbral adaptativo, a diferencia de outlier_frac). Se
    # registra como diagnostico, sin umbral. Ver claude/propuesta-fase-4.md.
    for b, nom in (("top", "sup"), ("bot", "inf")):
        m = np.vstack(rcol[b]) if rcol[b] else np.full((1, len(x_positions)), np.nan)
        with np.errstate(all="ignore"):
            perfil = np.nanmedian(m, axis=0)
            df.attrs[f"error_modelo_{nom}_px"] = float(np.sqrt(np.nanmean(perfil ** 2)))

    # Suavizado temporal robusto (Savitzky-Golay): preserva la forma de
    # los picos de contracción, a diferencia de un promedio móvil.
    valid_mask = df["frame_quality"] != "REJECTED"
    window = min(config.savgol_window, (valid_mask.sum() // 2) * 2 - 1)
    df["thickness_mm_smooth"] = np.nan
    if window >= 5:
        smoothed = savgol_filter(
            df.loc[valid_mask, "thickness_mm"].interpolate().values,
            window_length=window,
            polyorder=min(config.savgol_polyorder, window - 1),
        )
        df.loc[valid_mask, "thickness_mm_smooth"] = smoothed

    df.attrs["roi"] = roi
    return df


def describe_roi(roi: dict, image_width: int, detallado: bool = False) -> None:
    """Imprime la zona analizada (ROI). Corto por defecto; todo con `detallado`.

    Lo que aca no se imprime queda igual en la hoja `resumen` de
    serie_temporal.xlsx (y la tabla de alternativas en `roi_alternativas`).
    Los AVISOS salen solo cuando hay que hacer algo.
    """
    q = roi.get("roi_quality", {})
    xs, xe = roi["x_start"], roi["x_end"]
    var = q.get("variacion_en_roi_pct")
    lim = q.get("max_variacion_admitida_pct", 6.0)
    print(f"Zona analizada del gel: columnas {xs} a {xe} ({xe - xs} px de ancho)")
    if var is not None:
        ok = var <= lim
        print(f"  variacion del grosor dentro de la zona: {var}% "
              f"(aceptable hasta {lim:g}%) -> {'OK' if ok else 'NO CUMPLE'}")

    if detallado:
        print(f"  [detalle] metodo: {q.get('method')}  -> {q.get('criterio', '')}")
        print(f"  [detalle] la zona ocupa el {100 * (xe - xs) / image_width:.0f}% del ancho "
              f"de la imagen")
        if q.get("n_columnas_usadas") is not None:
            print(f"  [detalle] columnas muestreadas: {q['n_columnas_usadas']}"
                  f" (separacion {(xe - xs) / max(q['n_columnas_usadas'], 1):.1f} px)")
        if q.get("cintura_px") is not None:
            print(f"  [detalle] cintura del gel: {q['cintura_px']} px | grosor en la zona: "
                  f"{q.get('grosor_min_en_roi_px')} - {q.get('grosor_max_en_roi_px')} px")
        if q.get("n_franja_seguida") is not None:
            print(f"  [detalle] columnas con franja seguida: {q['n_franja_seguida']}/"
                  f"{q['n_columnas_imagen']} | descartadas por nitidez: "
                  f"{q.get('n_desc_por_nitidez')}, por grosor: {q.get('n_desc_por_grosor')}, "
                  f"por pendiente: {q.get('n_desc_por_pendiente')}")
        alts = q.get("alternativas")
        if alts:
            print("  [detalle] zonas evaluadas (forzar otra con --x-start/--x-end):")
            print("      %-16s %14s %9s %11s" % ("nivel", "rango x", "ancho", "variacion"))
            for a in alts:
                print("      %-16s %6d-%-7d %9d %10s%% %s" % (
                    a["metodo"], a["x_start"], a["x_end"], a["ancho_px"],
                    a["variacion_pct"], "<-- usada" if a["elegida"] else ""))

    # Avisos: solo cuando hay que actuar. El umbral es el MISMO del criterio de
    # aceptacion (antes saltaba a 3 % y afirmaba "anclaje" sin comprobarlo: fue
    # falso en 613, 304 y 341).
    if var is not None and var > lim:
        print(f"  AVISO: el grosor varia {var}% dentro de la zona (mas del {lim:g}% aceptable). "
              f"Puede que incluya el ensanchamiento cerca de un anclaje. Mira "
              f"00_roi_profile y, si hace falta, elegi la zona a mano con --x-start/--x-end.")
    if q.get("roi_contiene_cintura") is False:
        print("  AVISO: la zona no incluye la parte mas angosta del gel (la cintura). "
              "Mira 00_roi_profile.")
    if q.get("method") in ("solo_nitidez", "franja_completa", "fallback_margin"):
        print("  AVISO: no se encontro una zona plana del gel con el criterio normal; se uso "
              "uno mas flojo. Mira 00_roi_profile antes de confiar en los numeros.")
