"""
main.py
-------
Punto de entrada del pipeline: video -> serie temporal de grosor.

    python main.py --video data/raw_videos/mi_video.mp4 --px-to-mm 0.0021 --plot

Calibración px->mm: fotografiá una regla/retícula en tu mismo setup
óptico, medí cuántos píxeles ocupan N milímetros conocidos, y calculá
px_to_mm = mm_conocidos / píxeles_medidos.

NUEVO EN ESTA VERSIÓN: todos los parámetros que antes estaban
hardcodeados en PipelineConfig ahora se pueden pasar por línea de
comandos, incluidos los de la ROI y el ajuste RANSAC. Eso es lo que
permite verificar que el pipeline no está sobreajustado a un video en
particular, en vez de tener que editar el código para probar.
"""

from __future__ import annotations
import argparse
from pathlib import Path

from src.pipeline import PipelineConfig, process_video
from src.qc_visualization import save_diagnostics, plot_roi_profile
from src.output_paths import video_output_dir
from src import plotting


def parse_args():
    p = argparse.ArgumentParser(
        description="Pipeline de contractilidad de geles 3D (bordes subpíxel + RANSAC)",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("--video", required=True, help="Ruta al video del gel")
    p.add_argument("--maxproj", default=None, help="Ruta al maxProjectStack (PNG/TIFF)")
    p.add_argument("--px-to-mm", type=float, default=1.0, help="Factor de calibración píxeles->mm")
    p.add_argument("--output-dir", default=None,
                   help="Carpeta de salida. Por defecto: data/processed_data/<nombre_video>/")
    p.add_argument("--table-format", choices=["xlsx", "csv", "both"], default="xlsx")
    p.add_argument("--plot", action="store_true", help="Genera la curva de grosor vs tiempo")

    g = p.add_argument_group("muestreo y deteccion de borde")
    g.add_argument("--n-columns", type=int, default=60,
                   help="Columnas muestreadas por frame. Subirlo NO compensa un modelo mal elegido.")
    g.add_argument("--half-window", type=int, default=15,
                   help="Semi-ancho (px) de la ventana de busqueda del borde alrededor del guess.")
    g.add_argument("--min-gradient", type=float, default=5.0,
                   help="Gradiente minimo para aceptar un borde. Se mide sobre la imagen ya "
                        "pasada por CLAHE, asi que su valor cambia si usas --no-clahe.")
    g.add_argument("--edge-method", choices=["parabolic", "sigmoid"], default="parabolic")

    g = p.add_argument_group("ajuste robusto (RANSAC)")
    g.add_argument("--fit-method", choices=["ransac", "median"], default="ransac",
                   help="'median' asume borde horizontal; si el borde tiene pendiente, usa ransac.")
    g.add_argument("--ransac-degree", type=int, default=2,
                   help="Grado del polinomio del borde. 1=recta, 2=permite la curvatura leve "
                        "que tiene el gel incluso dentro de la gauge region.")
    g.add_argument("--ransac-residual-threshold", type=float, default=None,
                   help="Umbral fijo de inlier (px). Por defecto es ADAPTATIVO (k*MAD del "
                        "propio frame). Pasa un numero solo para reproducir corridas viejas.")
    g.add_argument("--ransac-residual-k", type=float, default=3.0,
                   help="Multiplicador del MAD cuando el umbral es adaptativo.")
    g.add_argument("--ransac-residual-floor", type=float, default=0.4,
                   help="Piso absoluto (px) del umbral adaptativo.")

    g = p.add_argument_group("ROI / gauge region")
    g.add_argument("--x-start", type=int, default=None,
                   help="Forzar el inicio de la ROI (px). Desactiva la seleccion automatica.")
    g.add_argument("--x-end", type=int, default=None, help="Forzar el fin de la ROI (px).")
    g.add_argument("--roi-tolerance", type=float, default=0.05,
                   help="Cuanto puede exceder el grosor de una columna a la cintura del gel "
                        "para seguir siendo gauge region (0.05 = 5%%).")
    g.add_argument("--roi-min-gradient", type=float, default=10.0,
                   help="Nitidez minima exigida a AMBOS bordes para incluir una columna.")
    g.add_argument("--roi-max-slope", type=float, default=0.02,
                   help="|d(grosor)/dx| maximo, en px de grosor por px de x. Este es el "
                        "criterio que realmente define 'grosor uniforme'.")

    g = p.add_argument_group("preproceso y suavizado")
    g.add_argument("--no-clahe", action="store_true",
                   help="Desactiva CLAHE. RECOMENDADO PROBARLO en videos con burbujas moviles: "
                        "CLAHE remapea el contraste por tiles, y una burbuja entrando a un tile "
                        "corre la posicion subpixel de todo el borde de ese tile.")
    g.add_argument("--denoise", action="store_true", help="Activa non-local-means (lento).")
    g.add_argument("--savgol-window", type=int, default=11, help="Ventana del suavizado temporal (impar).")
    g.add_argument("--low-quality-frac", type=float, default=0.30,
                   help="Fraccion de columnas descartadas (sobre 2N) para marcar LOW_QUALITY.")

    return p.parse_args()


def main():
    args = parse_args()

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
        savgol_window=args.savgol_window,
        low_quality_frac=args.low_quality_frac,
    )

    print(f"Procesando {args.video} ...")
    df = process_video(args.video, args.maxproj, config)
    roi = df.attrs.get("roi", {})

    n_rejected = int((df["frame_quality"] == "REJECTED").sum())
    n_low_quality = int((df["frame_quality"] == "LOW_QUALITY").sum())
    q = roi.get("roi_quality", {})

    summary = {
        "video": args.video,
        "frames totales": len(df),
        "frames rechazados": n_rejected,
        "frames baja calidad": n_low_quality,
        "px_to_mm": args.px_to_mm,
        "grosor medio (px)": round(float(df["thickness_px"].mean()), 3),
        "grosor min (px)": round(float(df["thickness_px"].min()), 3),
        "grosor max (px)": round(float(df["thickness_px"].max()), 3),
        "contraccion max (px)": round(float(df["thickness_px"].max() - df["thickness_px"].min()), 3),
        # --- trazabilidad: sin esto no se puede reproducir una corrida ---
        "ROI x_start": roi.get("x_start"),
        "ROI x_end": roi.get("x_end"),
        "ROI metodo": q.get("method"),
        "ROI variacion grosor (%)": q.get("variacion_en_roi_pct"),
        "n_columns": args.n_columns,
        "half_window": args.half_window,
        "min_gradient": args.min_gradient,
        "edge_method": args.edge_method,
        "fit_method": args.fit_method,
        "ransac_degree": args.ransac_degree,
        "ransac_residual_threshold": args.ransac_residual_threshold or "adaptativo",
        "use_clahe": not args.no_clahe,
        "residuo medio borde sup (px)": round(float(df["residual_top_px"].mean()), 4),
        "residuo medio borde inf (px)": round(float(df["residual_bottom_px"].mean()), 4),
    }

    out_dir = Path(args.output_dir) if args.output_dir else video_output_dir(args.video)
    out_dir.mkdir(parents=True, exist_ok=True)
    video_name = Path(args.video).stem

    # Perfil de ROI: el gráfico que explica por dónde quedó la gauge region
    roi_profile_path = out_dir / f"00_roi_profile_{video_name}.png"
    try:
        plot_roi_profile(roi, roi_profile_path)
        print(f"Perfil de ROI guardado en {roi_profile_path}")
    except Exception as e:  # nunca dejar que un gráfico rompa el análisis
        print(f"(no se pudo graficar el perfil de ROI: {e})")

    saved = save_diagnostics(df, out_dir / "serie_temporal", fmt=args.table_format, summary=summary)
    print(f"Resultados guardados en {saved}")
    print(f"Frames totales: {len(df)} | Rechazados: {n_rejected} | Baja calidad: {n_low_quality}")

    # --- Aviso de sanidad sobre el ajuste ---
    # Una fraccion ALTA y SOSTENIDA de outliers casi nunca son burbujas
    # (las burbujas afectan unas pocas columnas): lo habitual es que el
    # polinomio no represente la geometria del borde. Cuando eso pasa, el
    # conjunto de inliers cambia de frame a frame y mete saltos falsos en
    # la serie de grosor.
    frac = float(df["outlier_frac"].mean())
    resid = float(df[["residual_top_px", "residual_bottom_px"]].mean().mean())
    span = float(df["thickness_px"].max() - df["thickness_px"].min())
    print(f"Outliers: {100*frac:.1f}% de las columnas en promedio | "
          f"residuo tipico del ajuste: {resid:.3f} px | recorrido del grosor: {span:.3f} px")
    if frac > 0.10:
        print()
        print(f"AVISO: se descarta el {100*frac:.0f}% de las columnas en promedio. Unos pocos por "
              f"ciento es normal con burbujas; 10% o mas sostenido, no. Corre scripts/inspect_frame.py sobre un frame: si los "
              f"outliers salen CONTIGUOS, no son burbujas sino el modelo que no sigue la geometria "
              f"del borde -> subi --ransac-degree o achica la ROI a la zona plana con "
              f"--x-start/--x-end. Mira tambien 00_roi_profile.png.")

    if args.px_to_mm == 1.0:
        print("AVISO: --px-to-mm sigue en 1.0, asi que los valores 'mm' son en realidad PIXELES.")

    if args.plot:
        calibrated = abs(args.px_to_mm - 1.0) > 1e-9
        p = plotting.plot_timeseries(
            df, out_dir,
            unit_label="mm" if calibrated else "px (SIN CALIBRAR)",
            calibrated=calibrated,
            name=f"01_serie_temporal_{video_name}",
        )
        print(f"Gráfico guardado en {p}")


if __name__ == "__main__":
    main()
