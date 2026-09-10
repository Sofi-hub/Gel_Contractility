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
    }


def process_video(
    video_path: str,
    max_projection_path: str | None = None,
    config: PipelineConfig | None = None,
    verbose: bool = True,
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
    fps = meta["fps"] if meta["fps"] > 0 else 30.0

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
    )

    if verbose:
        describe_roi(roi, max_proj.shape[1])

    x_positions = np.linspace(roi["x_start"], roi["x_end"] - 1, config.n_columns).astype(int)

    rows = []
    for idx, frame in io_utils.frame_generator(video_path):
        result = process_frame(frame, x_positions, roi["top_guess"], roi["bottom_guess"], config)
        result["frame"] = idx
        result["time_s"] = idx / fps
        rows.append(result)

    df = pd.DataFrame(rows)

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


def describe_roi(roi: dict, image_width: int) -> None:
    """Imprime el reporte del auto-ROI, con avisos cuando algo huele mal."""
    q = roi.get("roi_quality", {})
    xs, xe = roi["x_start"], roi["x_end"]
    print(f"ROI (gauge region): x = {xs} a {xe}  "
          f"({100 * (xe - xs) / image_width:.0f}% del ancho de la imagen)")
    print(f"  metodo: {q.get('method')}  -> {q.get('criterio', '')}")
    if q.get("cintura_px") is not None:
        print(f"  cintura del gel: {q['cintura_px']} px | "
              f"grosor en la ROI: {q.get('grosor_min_en_roi_px')} - "
              f"{q.get('grosor_max_en_roi_px')} px "
              f"({q.get('variacion_en_roi_pct')}% de variacion)")
    if q.get("n_franja_seguida") is not None:
        print(f"  columnas con franja seguida: {q['n_franja_seguida']}/{q['n_columnas_imagen']} | "
              f"descartadas por nitidez: {q.get('n_desc_por_nitidez')}, "
              f"por grosor: {q.get('n_desc_por_grosor')}, "
              f"por pendiente: {q.get('n_desc_por_pendiente')}")

    alts = q.get("alternativas")
    if alts:
        print("  alternativas de ROI (elegir a mano con --x-start/--x-end si conviene otra):")
        print("      %-16s %14s %9s %11s" % ("nivel", "rango x", "ancho", "variacion"))
        for a in alts:
            print("      %-16s %6d-%-7d %9d %10s%% %s" % (
                a["metodo"], a["x_start"], a["x_end"], a["ancho_px"],
                a["variacion_pct"], "<-- usada" if a["elegida"] else ""))

    var = q.get("variacion_en_roi_pct")
    if var is not None and var > 3:
        print(f"  AVISO: el grosor varia {var}% dentro de la ROI. Eso ya no es una "
              f"gauge region: probablemente incluye el hombro de un anclaje, donde la "
              f"deformacion esta condicionada por el anclaje y no por la contractilidad. "
              f"Mira roi_profile.png y, si hace falta, forza la ROI con --x-start/--x-end.")
    if q.get("method") in ("solo_nitidez", "franja_completa", "fallback_margin"):
        print("  AVISO: hubo que relajar el criterio de gauge region. Revisa roi_profile.png.")
    if (xe - xs) < 0.25 * image_width:
        print(f"  AVISO: la ROI cubre solo el {100 * (xe - xs) / image_width:.0f}% del ancho. "
              f"Verifica en roi_profile.png si se corto por halo/desenfoque o si el gel "
              f"realmente es corto.")
