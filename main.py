"""
main.py
-------
Punto de entrada del pipeline: video -> serie temporal de grosor.

    python main.py --video data/raw_videos/mi_video.mp4 \
                   --output-dir data/processed_data/mi_video --base-tiempo pts

No se calibra px -> mm por decision del proyecto (los videos no se graban
todos al mismo aumento): --px-to-mm queda en 1.0 y todo sale en pixeles.

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
    p.add_argument("--base-tiempo", choices=["frames", "pts"], default="pts",
                   help="Como se construye el eje temporal. 'frames' = frame/fps "
                        "(supone que no falta ningun frame). 'pts' = timestamps del "
                        "contenedor, que es lo correcto si la grabacion perdio "
                        "frames. Default 'pts' (hallazgo 3 de CLAUDE.md); si el "
                        "archivo no trae timestamps, cae solo a 'frames' y avisa.")
    p.add_argument("--fps", type=float, default=None,
                   help="Solo con --base-tiempo frames: fuerza el fps en vez de "
                        "leerlo del archivo (el declarado es un promedio y baja si "
                        "faltan fotogramas; el real de captura es 30.000). Con 'pts' "
                        "no hace falta.")
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
    g.add_argument("--roi-min-spacing", type=float, default=3.0,
                   help="Separacion minima entre columnas muestreadas (px). Medido: el "
                        "error de borde deja de ser compartido a los 2-3 px.")
    g.add_argument("--roi-min-columnas", type=int, default=40,
                   help="Piso de columnas. El ancho minimo de la ROI es este valor x "
                        "--roi-min-spacing; en una ROI angosta se usan ancho/espaciado "
                        "columnas (hasta --n-columns).")
    g.add_argument("--roi-max-variacion", type=float, default=6.0,
                   help="Variacion de grosor maxima admitida dentro de la ROI "
                        "(%%). Criterio de aceptacion del protocolo.")
    g.add_argument("--exigir-roi", action="store_true",
                   help="Aborta si la ROI no cumple el criterio de aceptacion, "
                        "en vez de avisar y seguir emitiendo numeros.")
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
        roi_min_column_spacing_px=args.roi_min_spacing,
        roi_min_columns=args.roi_min_columnas,
        roi_max_variacion_pct=args.roi_max_variacion,
        fps_override=args.fps,
        base_tiempo=args.base_tiempo,
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
        "fps usado": round(float(df.attrs.get("fps", 0.0)), 5),
        "fps declarado por el archivo": round(float(df.attrs.get("fps_declarado", 0.0)), 5),
        "base de tiempo": df.attrs.get("base_tiempo"),
        "fps segun PTS": round(float(df.attrs.get("fps_segun_pts", float("nan"))), 4),
        "huecos en PTS": df.attrs.get("n_huecos_pts"),
        "duracion segun PTS (s)": round(float(df.attrs.get("duracion_pts_s", float("nan"))), 4),
        "frames faltantes estimados": round(float(df.attrs.get("frames_faltantes", float("nan"))), 1),
        "frames faltantes (%)": round(100 * float(df.attrs.get("frac_frames_faltantes", float("nan"))), 2),
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
        "ROI cumple criterio": q.get("cumple_criterio_aceptacion"),
        "ROI ancho minimo exigido (px)": q.get("ancho_minimo_exigido_px"),
        "ROI contiene cintura": q.get("roi_contiene_cintura"),
        "n_columns (maximo)": args.n_columns,
        "n_columnas usadas": q.get("n_columnas_usadas"),
        "roi_min_columnas": args.roi_min_columnas,
        "outlier_frac medio": round(float(df["outlier_frac"].mean()), 4),
        "half_window": args.half_window,
        "min_gradient": args.min_gradient,
        "edge_method": args.edge_method,
        "fit_method": args.fit_method,
        "ransac_degree": args.ransac_degree,
        "ransac_residual_threshold": args.ransac_residual_threshold or "adaptativo",
        "use_clahe": not args.no_clahe,
        "residuo medio borde sup (px)": round(float(df["residual_top_px"].mean()), 4),
        "residuo medio borde inf (px)": round(float(df["residual_bottom_px"].mean()), 4),
        # --- Fase 4 (H24): diagnosticos del ajuste, SIN umbral ---
        "error de modelo borde sup (px)": round(float(df.attrs.get("error_modelo_sup_px", float("nan"))), 4),
        "error de modelo borde inf (px)": round(float(df.attrs.get("error_modelo_inf_px", float("nan"))), 4),
        "error de modelo peor / grosor (%)": round(100 * max(
            float(df.attrs.get("error_modelo_sup_px", float("nan"))),
            float(df.attrs.get("error_modelo_inf_px", float("nan")))) / float(df["thickness_px"].median()), 3),
    }

    frac = float(df.attrs.get("frac_frames_faltantes", float("nan")))
    if frac == frac and frac > 0.01:
        print(f"  AVISO: la grabacion perdio ~{df.attrs.get('frames_faltantes'):.0f} frames "
              f"({100*frac:.1f}%), repartidos en {df.attrs.get('n_huecos_pts')} huecos de los "
              f"timestamps. El fps real de captura segun los timestamps es "
              f"{df.attrs.get('fps_segun_pts'):.4f}.")
        if df.attrs.get("base_tiempo") != "pts":
            print("         Con el eje frame/fps los huecos se comen y los eventos parecen")
            print("         MAS JUNTOS de lo que fueron. Volve a correr con --base-tiempo pts.")

    if args.exigir_roi and q.get("cumple_criterio_aceptacion") is False:
        raise SystemExit(
            f"ABORTADO: la ROI varia {q.get('variacion_en_roi_pct')}% de grosor, "
            f"por encima del {args.roi_max_variacion}% admitido. Eso no es una "
            f"gauge region. Mira 00_roi_profile.png y forza la ROI con "
            f"--x-start/--x-end, o corre sin --exigir-roi si sabes lo que haces.")

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

    # --- Diagnostico del ajuste (Fase 4, H24) ---
    # El viejo chequeo "outlier_frac < 10 %" ya NO es criterio de aceptacion:
    # el umbral de descarte se adapta a cada fotograma, asi que una ROI con
    # bordes limpios descarta MAS. Medido en 063 y 466: outlier_frac ordena las
    # ROIs al reves del ruido del canal. La ROI se acepta por su FORMA
    # (variacion <= 6 %, contiene la cintura). outlier_frac y el error de modelo
    # quedan en `resumen` como diagnostico, sin umbral (revisar con RARITOS).
    # Ver claude/propuesta-fase-4.md.
    frac = float(df["outlier_frac"].mean())
    resid = float(df[["residual_top_px", "residual_bottom_px"]].mean().mean())
    print(f"Ajuste (diagnostico, sin umbral): outliers {100*frac:.1f}% | residuo tipico "
          f"{resid:.3f} px | error de modelo sup/inf "
          f"{summary['error de modelo borde sup (px)']}/{summary['error de modelo borde inf (px)']} px "
          f"({summary['error de modelo peor / grosor (%)']}% del grosor)")

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
