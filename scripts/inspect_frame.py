"""
scripts/inspect_frame.py
-------------------------
Control de calidad visual sobre UN frame, para calibrar los parámetros
antes de procesar el video entero.

Salidas en --output-dir:
    maxproj_computed.png -> cache del maxProjection calculado
    roi_profile.png       -> NUEVO: perfil de grosor y nitidez de TODA la
                              imagen con la ROI elegida sombreada. Mirá
                              ESTE gráfico primero: dice si la ROI cayó
                              sobre la zona de grosor uniforme o sobre el
                              hombro de un anclaje, y por qué se cortó
                              donde se cortó.
    overlay.png           -> frame con bordes/inliers/outliers dibujados
    diagnostics.xlsx      -> tabla columna por columna, ahora con el
                              RESIDUO de cada punto contra el modelo
    column_<x>_top.png    -> (con --inspect-column) perfil detallado

CÓMO LEER LOS RESULTADOS
-------------------------
- Puntos rojos AISLADOS y dispersos  -> burbujas. RANSAC está haciendo
  su trabajo.
- Puntos rojos CONTIGUOS, en bloque  -> NO son burbujas: es el modelo que
  no representa la geometría del borde. Subí --ransac-degree, o achicá
  la ROI a la zona realmente plana con --x-start/--x-end.
- Residuo (MAD) del mismo orden que el umbral -> RANSAC está separando
  ruido de ruido; el conjunto de inliers va a cambiar de frame a frame y
  eso mete saltos falsos en la serie temporal.
"""

from __future__ import annotations
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import cv2
import numpy as np

from src import io_utils, preprocessing, qc_visualization
from src.pipeline import PipelineConfig, describe_roi


def load_single_frame(args) -> np.ndarray:
    if args.image:
        frame = cv2.imread(args.image, cv2.IMREAD_GRAYSCALE)
        if frame is None:
            raise IOError(f"No se pudo leer la imagen: {args.image}")
        return frame

    if args.video is not None:
        for idx, frame in io_utils.frame_generator(args.video, start_frame=args.frame_index,
                                                   end_frame=args.frame_index + 1):
            return frame
        raise IOError(f"No se pudo leer el frame {args.frame_index} de {args.video}")

    raise ValueError("Debés indicar --image o --video")


def load_or_compute_max_projection(args) -> np.ndarray:
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    cache_path = out_dir / "maxproj_computed.png"

    if args.maxproj:
        return io_utils.load_max_projection(args.maxproj)

    if args.video is not None:
        if cache_path.exists() and not args.recompute_maxproj:
            print(f"Usando maxProjection cacheado: {cache_path} "
                  f"(borralo o pasá --recompute-maxproj para recalcular)")
            return io_utils.load_max_projection(cache_path)

        print(f"Calculando maxProjection desde {args.video} (stride={args.maxproj_stride})...")
        max_proj = io_utils.compute_max_projection(
            args.video, stride=args.maxproj_stride, max_frames=args.maxproj_max_frames,
        )
        cv2.imwrite(str(cache_path), max_proj)
        print(f"maxProjection calculado y cacheado en: {cache_path}")
        return max_proj

    print("AVISO: sin --maxproj ni --video no hay serie temporal para calcular el "
          "maxProjection real. Usando el propio --image como aproximación.")
    return load_single_frame(args)


def parse_args():
    p = argparse.ArgumentParser(
        description="QC visual: inspecciona la detección de bordes en un solo frame",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    src_group = p.add_mutually_exclusive_group(required=True)
    src_group.add_argument("--image", help="Imagen suelta a usar como frame de prueba")
    src_group.add_argument("--video", help="Video; se usará un frame puntual (--frame-index)")

    p.add_argument("--frame-index", type=int, default=0)
    p.add_argument("--maxproj", default=None)
    p.add_argument("--maxproj-stride", type=int, default=5)
    p.add_argument("--maxproj-max-frames", type=int, default=None)
    p.add_argument("--recompute-maxproj", action="store_true")
    p.add_argument("--output-dir", default="qc_output")
    p.add_argument("--table-format", choices=["xlsx", "csv", "both"], default="xlsx")
    p.add_argument("--px-to-mm", type=float, default=1.0)

    g = p.add_argument_group("muestreo y deteccion de borde")
    g.add_argument("--n-columns", type=int, default=60)
    g.add_argument("--half-window", type=int, default=15)
    g.add_argument("--min-gradient", type=float, default=5.0)
    g.add_argument("--edge-method", choices=["parabolic", "sigmoid"], default="parabolic")

    g = p.add_argument_group("ajuste robusto (RANSAC)")
    g.add_argument("--fit-method", choices=["ransac", "median"], default="ransac")
    g.add_argument("--ransac-degree", type=int, default=2)
    g.add_argument("--ransac-residual-threshold", type=float, default=None,
                   help="Umbral fijo (px). Por defecto ADAPTATIVO (k*MAD del propio frame).")
    g.add_argument("--ransac-residual-k", type=float, default=3.0)
    g.add_argument("--ransac-residual-floor", type=float, default=0.4)

    g = p.add_argument_group("ROI / gauge region")
    g.add_argument("--x-start", type=int, default=None)
    g.add_argument("--x-end", type=int, default=None)
    g.add_argument("--roi-tolerance", type=float, default=0.05)
    g.add_argument("--roi-min-gradient", type=float, default=10.0)
    g.add_argument("--roi-max-slope", type=float, default=0.02)

    g = p.add_argument_group("preproceso")
    g.add_argument("--no-clahe", action="store_true",
                   help="Desactiva CLAHE. Probalo si el video tiene burbujas moviles.")
    g.add_argument("--denoise", action="store_true")

    p.add_argument("--inspect-column", type=int, default=None,
                   help="Columna x a graficar en detalle (perfil de intensidad + gradiente)")

    return p.parse_args()


def main():
    args = parse_args()
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    frame = load_single_frame(args)
    max_proj = load_or_compute_max_projection(args)

    if frame.shape != max_proj.shape:
        print(f"AVISO: el frame ({frame.shape}) y el maxProjectStack ({max_proj.shape}) "
              f"tienen distinta resolución.")

    config = PipelineConfig(
        n_columns=args.n_columns,
        half_window=args.half_window,
        min_gradient=args.min_gradient,
        edge_method=args.edge_method,
        fit_method=args.fit_method,
        ransac_degree=args.ransac_degree,
        ransac_residual_threshold=args.ransac_residual_threshold,
        ransac_residual_k=args.ransac_residual_k,
        ransac_residual_floor=args.ransac_residual_floor,
        roi_x_start=args.x_start,
        roi_x_end=args.x_end,
        roi_thickness_tolerance=args.roi_tolerance,
        roi_min_gradient=args.roi_min_gradient,
        roi_max_slope=args.roi_max_slope,
        px_to_mm=args.px_to_mm,
        use_clahe=not args.no_clahe,
        use_denoise=args.denoise,
    )

    roi = preprocessing.auto_detect_roi(
        max_proj,
        thickness_tolerance=config.roi_thickness_tolerance,
        min_gradient_for_roi=config.roi_min_gradient,
        max_thickness_slope=config.roi_max_slope,
        x_start=config.roi_x_start,
        x_end=config.roi_x_end,
    )
    describe_roi(roi, max_proj.shape[1])

    roi_png = out_dir / "roi_profile.png"
    try:
        qc_visualization.plot_roi_profile(roi, roi_png)
        print(f"Perfil de ROI guardado en: {roi_png}   <-- MIRA ESTE PRIMERO")
    except Exception as e:
        print(f"(no se pudo graficar el perfil de ROI: {e})")

    if config.px_to_mm == 1.0:
        print("AVISO: --px-to-mm sigue en 1.0; los 'mm' de abajo son PIXELES.")

    x_positions = np.linspace(roi["x_start"], roi["x_end"] - 1, config.n_columns).astype(int)

    frame_p = preprocessing.preprocess_frame(frame, use_clahe=config.use_clahe,
                                             use_denoise=config.use_denoise)

    diag = qc_visualization.run_frame_diagnostics(
        frame_p, x_positions, roi["top_guess"], roi["bottom_guess"], config
    )

    overlay = qc_visualization.draw_diagnostics_overlay(frame_p, diag, px_to_mm=config.px_to_mm)
    overlay_path = out_dir / "overlay.png"
    cv2.imwrite(str(overlay_path), overlay)
    print(f"Overlay guardado en: {overlay_path}")

    df = qc_visualization.diagnostics_to_dataframe(diag)
    n_top_out = int(df["top_is_inlier"].eq(False).sum())
    n_bot_out = int(df["bottom_is_inlier"].eq(False).sum())
    q = roi.get("roi_quality", {})

    summary = {
        "archivo_fuente": args.video or args.image,
        "frame_index": args.frame_index if args.video else "(imagen suelta)",
        "ROI x_start": roi["x_start"],
        "ROI x_end": roi["x_end"],
        "ROI metodo": q.get("method", ""),
        "ROI variacion grosor (%)": q.get("variacion_en_roi_pct"),
        "ROI cintura (px)": q.get("cintura_px"),
        "columnas muestreadas": len(df),
        "grosor (px)": round(float(diag.thickness_px), 3),
        "px_to_mm": config.px_to_mm,
        "grosor (mm)": round(float(diag.thickness_px * config.px_to_mm), 5),
        "outliers borde superior": n_top_out,
        "outliers borde inferior": n_bot_out,
        "% outliers superior": round(100 * n_top_out / len(df), 1),
        "% outliers inferior": round(100 * n_bot_out / len(df), 1),
        "residuo MAD superior (px)": round(float(diag.top_fit.residual_px), 4) if diag.top_fit else None,
        "residuo MAD inferior (px)": round(float(diag.bottom_fit.residual_px), 4) if diag.bottom_fit else None,
        "umbral RANSAC superior (px)": round(float(diag.top_fit.threshold_px), 4) if diag.top_fit else None,
        "umbral RANSAC inferior (px)": round(float(diag.bottom_fit.threshold_px), 4) if diag.bottom_fit else None,
        "min_gradient": config.min_gradient,
        "half_window": config.half_window,
        "ransac_degree": config.ransac_degree,
        "ransac_residual_threshold": config.ransac_residual_threshold or "adaptativo",
        "use_clahe": config.use_clahe,
    }

    saved = qc_visualization.save_diagnostics(
        df, out_dir / "diagnostics", fmt=args.table_format, summary=summary
    )
    print(f"Diagnóstico columna-por-columna guardado en: {saved}")

    print()
    print(f"Grosor estimado: {diag.thickness_px:.3f} px")
    print(f"Outliers borde superior: {n_top_out}/{len(df)} | inferior: {n_bot_out}/{len(df)}")

    # --- Diagnóstico automático de outliers contiguos ---
    # Ésta es la distinción que más cuesta ver a ojo en el overlay y la
    # que decide qué parámetro tocar.
    for edge, col in (("superior", "top_is_inlier"), ("inferior", "bottom_is_inlier")):
        bad = ~df[col].to_numpy(dtype=bool)
        if bad.sum() == 0:
            continue
        idx = np.flatnonzero(bad)
        blocks = np.split(idx, np.flatnonzero(np.diff(idx) != 1) + 1)
        longest = max(len(b) for b in blocks)
        if longest >= 3:
            xs = df["x"].to_numpy()
            b = max(blocks, key=len)
            print(f"  -> borde {edge}: hay {longest} outliers CONTIGUOS "
                  f"(x={xs[b[0]]}..{xs[b[-1]]}). Eso NO parece una burbuja sino el modelo "
                  f"que no sigue la geometria del borde. Proba --ransac-degree "
                  f"{config.ransac_degree + 1}, o achica la ROI a la zona plana.")
        else:
            print(f"  -> borde {edge}: outliers dispersos (bloque mayor = {longest}). "
                  f"Compatible con burbujas/suciedad; RANSAC esta haciendo lo suyo.")

    if diag.top_fit is not None:
        print(f"\nResiduo MAD sup={diag.top_fit.residual_px:.3f} px "
              f"(umbral {diag.top_fit.threshold_px:.3f} px) | "
              f"inf={diag.bottom_fit.residual_px:.3f} px "
              f"(umbral {diag.bottom_fit.threshold_px:.3f} px)")

    if args.inspect_column is not None:
        x = args.inspect_column
        if x < 0 or x >= frame_p.shape[1]:
            print(f"--inspect-column {x} fuera de rango (0-{frame_p.shape[1]-1})")
        else:
            for name, polarity in (("top", 1), ("bottom", -1)):
                guess = roi["top_guess"][x] if polarity > 0 else roi["bottom_guess"][x]
                fig = qc_visualization.plot_column_profile(
                    frame_p, x, guess, config.half_window,
                    polarity=polarity, min_gradient=config.min_gradient,
                )
                path = out_dir / f"column_{x}_{name}.png"
                fig.savefig(path, dpi=150)
                print(f"Perfil detallado ({name}) guardado en: {path}")


if __name__ == "__main__":
    main()
