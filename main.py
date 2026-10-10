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
import os
from pathlib import Path

import pandas as pd

from src.pipeline import PipelineConfig, process_video
from src.qc_visualization import save_diagnostics, plot_roi_profile
from src.output_paths import video_output_dir
from src import plotting


def _trazabilidad() -> dict:
    """Commit de git y versiones de las librerias (H32): con esto una corrida
    se puede reproducir. Nunca falla: si no hay git, dice "desconocido"."""
    import platform, subprocess
    raiz = Path(__file__).resolve().parent
    try:
        c = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=raiz,
                           capture_output=True, text=True, timeout=10)
        commit = c.stdout.strip() or "desconocido"
        if commit != "desconocido":
            d = subprocess.run(["git", "status", "--porcelain", "--", "src", "scripts", "main.py"],
                               cwd=raiz, capture_output=True, text=True, timeout=10)
            if d.stdout.strip():
                commit += " +cambios sin commitear"
    except Exception:
        commit = "desconocido"
    out = {"commit": commit, "python": platform.python_version()}
    for nombre, modulo in [("numpy", "numpy"), ("scipy", "scipy"), ("opencv", "cv2"),
                           ("pandas", "pandas"), ("scikit-learn", "sklearn")]:
        try:
            out[f"version {nombre}"] = __import__(modulo).__version__
        except Exception:
            out[f"version {nombre}"] = "no instalado"
    return out


# B1 (2026-10-10). Ventana de busqueda automatica. Medido en los 11 videos de
# referencia (fotogramas con algun borde pegado al limite de la ventana, +-15):
# 068 68 %, 341 34 % (falla en silencio: 0 % sin borde), 466 12 %, 063 3 %,
# el resto < 1 %. Con +-30 para todos, 466 engancha otro gradiente (5 -> 2
# eventos): por eso 30 es solo el plan B. El 20 % sale de pocos casos
# (pendientes.md, D4).
HW_NORMAL, HW_AMPLIA, UMBRAL_LIMITE, UMBRAL_SIN_BORDE = 15, 30, 0.20, 0.01


def _falla_ventana(df):
    """(fraccion de fotogramas con bordes en el limite, fraccion sin borde o dudosos)."""
    lim = float((df["n_bordes_en_limite"] > 0).mean())
    mal = float((df["frame_quality"] != "OK").mean())
    return lim, mal


def parse_args():
    p = argparse.ArgumentParser(
        description="Pipeline de contractilidad de geles 3D (bordes subpíxel + RANSAC)",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("--video", required=True, help="Ruta al video del gel")
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
    p.add_argument("--procesos", type=int, default=min(2, os.cpu_count() or 1),
                   help="Cuantos fotogramas se procesan a la vez (nucleos del procesador). "
                        "Por defecto 2: medido en una notebook de 4 nucleos (Video_prueba), "
                        "1 -> 108 s, 2 -> 102 s, 4 -> 102 s, 7 -> 127 s; lo que tarda es "
                        "leer el video, que va en serie. 1 = en serie. El resultado es "
                        "identico con cualquier valor; solo cambia la velocidad.")
    p.add_argument("--plot", action="store_true", help="Genera la curva de grosor vs tiempo")

    g = p.add_argument_group("muestreo y deteccion de borde")
    g.add_argument("--n-columns", type=int, default=60,
                   help="Columnas muestreadas por frame. Subirlo NO compensa un modelo mal elegido.")
    g.add_argument("--half-window", type=int, default=None,
                   help="Semi-ancho (px) de la ventana de busqueda del borde. Por defecto es "
                        "AUTOMATICO: +-15 px y, si el borde se sale de la ventana (mas del "
                        f"{100*UMBRAL_LIMITE:.0f}%% de los fotogramas con bordes en el limite, o mas "
                        "del 1%% sin borde), se reprocesa solo con +-30. Pasar un numero lo fija.")
    g.add_argument("--min-gradient", type=float, default=5.0,
                   help="Gradiente minimo para aceptar un borde. Se mide sobre la imagen ya "
                        "pasada por CLAHE, asi que su valor cambia si usas --no-clahe.")

    g = p.add_argument_group("ajuste robusto (RANSAC)")
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
    g.add_argument("--savgol-window", type=int, default=11, help="Ventana del suavizado temporal (impar).")
    g.add_argument("--low-quality-frac", type=float, default=0.30,
                   help="Fraccion de columnas descartadas (sobre 2N) para marcar LOW_QUALITY.")

    p.add_argument("--verbose", action="store_true",
                   help="Imprime tambien el detalle tecnico (metodo de la zona, columnas "
                        "descartadas, zonas alternativas, diagnostico del ajuste). Todo eso "
                        "queda igual guardado en serie_temporal_<video>.xlsx.")

    return p.parse_args()


def main():
    args = parse_args()

    config = PipelineConfig(
        n_columns=args.n_columns,
        half_window=args.half_window or HW_NORMAL,
        min_gradient=args.min_gradient,
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
        savgol_window=args.savgol_window,
        low_quality_frac=args.low_quality_frac,
    )

    print(f"Procesando {args.video} ...")
    df = process_video(args.video, config, detallado=args.verbose,
                       n_procesos=args.procesos)
    lim, mal = _falla_ventana(df)
    hw_motivo = "fijada por el usuario" if args.half_window else "automatica: +-15 alcanzo"
    if args.half_window is None and (lim > UMBRAL_LIMITE or mal > UMBRAL_SIN_BORDE):
        print(f"  nota: el borde se sale de la ventana de +-{HW_NORMAL} px "
              f"({100*lim:.0f}% de los fotogramas con bordes en el limite, {100*mal:.0f}% sin "
              f"borde): el gel se mueve mucho. Se vuelve a procesar con +-{HW_AMPLIA} px.")
        lim15, mal15 = lim, mal
        config.half_window = HW_AMPLIA
        df = process_video(args.video, config, verbose=False, n_procesos=args.procesos)
        lim, mal = _falla_ventana(df)
        hw_motivo = (f"automatica: +-15 fallo ({100*lim15:.1f}% en el limite, "
                     f"{100*mal15:.1f}% sin borde)")
    roi = df.attrs.get("roi", {})

    n_rejected = int((df["frame_quality"] == "REJECTED").sum())
    n_low_quality = int((df["frame_quality"] == "LOW_QUALITY").sum())
    q = roi.get("roi_quality", {})

    summary = {
        "video": args.video,
        "frames totales": len(df),
        "frames rechazados": n_rejected,
        "frames baja calidad": n_low_quality,
        # H32: con base pts el eje sale de los timestamps, asi que el fps que
        # realmente se usa es el de los timestamps, no el declarado.
        "fps usado": round(float(df.attrs.get("fps_segun_pts", float("nan"))
                             if df.attrs.get("base_tiempo") == "pts"
                             else df.attrs.get("fps", 0.0)), 5),
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
        "half_window": config.half_window,
        "half_window eleccion": hw_motivo,
        "fotogramas con bordes en el limite (%)": round(100 * lim, 2),
        "min_gradient": args.min_gradient,
        "edge_method": "parabolic",   # unica opcion desde 2026-10-10 (se borro "sigmoid")
        "fit_method": "ransac",   # unica opcion desde 2026-10-08 (se borro "median")
        "ransac_degree": args.ransac_degree,
        "ransac_residual_threshold": args.ransac_residual_threshold or "adaptativo",
        "use_clahe": not args.no_clahe,
        # H32 (2026-10-10): el resto de los parametros, para poder reproducir la corrida
        "roi_tolerance": args.roi_tolerance,
        "roi_min_gradient": args.roi_min_gradient,
        "roi_max_slope": args.roi_max_slope,
        "ransac_residual_k": args.ransac_residual_k,
        "ransac_residual_floor": args.ransac_residual_floor,
        "savgol_window": args.savgol_window,
        "low_quality_frac": args.low_quality_frac,
        "procesos": args.procesos,
        **_trazabilidad(),
        "residuo medio borde sup (px)": round(float(df["residual_top_px"].mean()), 4),
        "residuo medio borde inf (px)": round(float(df["residual_bottom_px"].mean()), 4),
        # --- Fase 4 (H24): diagnosticos del ajuste, SIN umbral ---
        "error de modelo borde sup (px)": round(float(df.attrs.get("error_modelo_sup_px", float("nan"))), 4),
        "error de modelo borde inf (px)": round(float(df.attrs.get("error_modelo_inf_px", float("nan"))), 4),
        "error de modelo peor / grosor (%)": round(100 * max(
            float(df.attrs.get("error_modelo_sup_px", float("nan"))),
            float(df.attrs.get("error_modelo_inf_px", float("nan")))) / float(df["thickness_px"].median()), 3),
        # --- detalle de la zona (ROI) que antes solo salia en pantalla ---
        "ROI criterio": q.get("criterio"),
        "ROI cintura del gel (px)": q.get("cintura_px"),
        "ROI grosor min en la zona (px)": q.get("grosor_min_en_roi_px"),
        "ROI grosor max en la zona (px)": q.get("grosor_max_en_roi_px"),
        "ROI fraccion del ancho de la imagen": q.get("roi_width_frac"),
        "ROI columnas con franja seguida": q.get("n_franja_seguida"),
        "ROI columnas de la imagen": q.get("n_columnas_imagen"),
        "ROI columnas descartadas por nitidez": q.get("n_desc_por_nitidez"),
        "ROI columnas descartadas por grosor": q.get("n_desc_por_grosor"),
        "ROI columnas descartadas por pendiente": q.get("n_desc_por_pendiente"),
    }

    # D6 (2026-10-10): riesgos que antes no avisaban (solo diagnostico)
    from src.pipeline import diagnosticos_riesgo, UMBRAL_DT_IDENTICOS, UMBRAL_NITIDEZ_ROI
    riesgo = diagnosticos_riesgo(roi, args.roi_min_gradient, args.roi_tolerance)
    dt_ident = float(df.attrs.get("dt_identicos_frac", float("nan")))
    summary["timestamps identicos (%)"] = round(100 * dt_ident, 1) if dt_ident == dt_ident else None
    summary["cintura: columnas seguidas (px)"] = riesgo["cintura_racha_px"]
    summary["nitidez del borde en la zona (mediana)"] = (
        round(riesgo["nitidez_roi_mediana"], 1) if riesgo["nitidez_roi_mediana"] is not None else None)

    # ---------------- avisos (solo cuando hay que hacer algo) ----------------
    if dt_ident == dt_ident and dt_ident >= UMBRAL_DT_IDENTICOS:
        print(f"  AVISO: los intervalos entre fotogramas son todos iguales "
              f"({100*dt_ident:.0f}%): es probable que el archivo no traiga los tiempos reales "
              f"de la camara. Si se perdieron fotogramas, no se puede saber y el eje de "
              f"tiempo los ignora. Conviene pedir el video original.")
    min_ancho = q.get("ancho_minimo_exigido_px") or 120
    if riesgo["cintura_racha_px"] is not None and riesgo["cintura_racha_px"] < min_ancho \
            and q.get("method") != "manual":
        print(f"  AVISO: la parte mas angosta del gel abarca solo {riesgo['cintura_racha_px']} px "
              f"seguidos (menos que el ancho minimo de la zona, {min_ancho} px): la zona no "
              f"puede ser a la vez plana y ancha. Mira 00_roi_profile_<video>.png.")
    if riesgo["nitidez_roi_mediana"] is not None and riesgo["nitidez_roi_mediana"] < UMBRAL_NITIDEZ_ROI:
        print(f"  AVISO: los bordes del gel tienen poco contraste en la zona analizada "
              f"(nitidez {riesgo['nitidez_roi_mediana']:.0f}; en los videos validados 18-51). "
              f"La posicion del borde va a ser mas ruidosa: revisar enfoque e iluminacion.")

    frac_falt = float(df.attrs.get("frac_frames_faltantes", float("nan")))
    if frac_falt == frac_falt and frac_falt > 0.01:
        if df.attrs.get("base_tiempo") == "pts":
            print(f"  nota: la camara perdio ~{df.attrs.get('frames_faltantes'):.0f} fotogramas "
                  f"({100*frac_falt:.1f}%). El eje de tiempo usa las marcas de tiempo del "
                  f"video, asi que los tiempos siguen siendo correctos.")
        else:
            print(f"  AVISO: la camara perdio ~{df.attrs.get('frames_faltantes'):.0f} fotogramas "
                  f"({100*frac_falt:.1f}%) y el eje de tiempo se armo con fotograma / fps: "
                  f"los eventos van a parecer MAS JUNTOS de lo que fueron. Volve a correr "
                  f"con --base-tiempo pts.")

    if args.exigir_roi and q.get("cumple_criterio_aceptacion") is False:
        raise SystemExit(
            f"ABORTADO: la ROI varia {q.get('variacion_en_roi_pct')}% de grosor, "
            f"por encima del {args.roi_max_variacion}% admitido. Eso no es una "
            f"gauge region. Mira 00_roi_profile_<video>.png y "
            + ("elegi otra zona" if q.get("method") == "manual"
               else "forza la ROI con --x-start/--x-end")
            + ", o corre sin --exigir-roi si sabes lo que haces.")

    out_dir = Path(args.output_dir) if args.output_dir else video_output_dir(args.video)
    out_dir.mkdir(parents=True, exist_ok=True)
    video_name = Path(args.video).stem
    archivos = []

    # Perfil de ROI: el gráfico que explica por dónde quedó la gauge region
    roi_profile_path = out_dir / f"00_roi_profile_{video_name}.png"
    try:
        plot_roi_profile(roi, roi_profile_path)
        archivos.append(roi_profile_path.name)
    except Exception as e:  # nunca dejar que un gráfico rompa el análisis
        print(f"  (no se pudo graficar el perfil de la zona: {e})")

    alts = q.get("alternativas") or []
    extra = {"roi_alternativas": pd.DataFrame(alts)} if alts else None
    saved = save_diagnostics(df, out_dir / f"serie_temporal_{video_name}",
                             summary=summary, extra_sheets=extra)
    archivos.insert(0, Path(saved).name)

    # Fotogramas sin borde. Antes solo aparecian los avisos de sklearn ("R^2
    # score is not well-defined"), que no dicen nada. Causa medida en 068: el
    # gel se mueve mas que la ventana de busqueda (+-half_window px).
    n = len(df)
    print(f"Fotogramas: {n} | sin borde (descartados): {n_rejected} | "
          f"dudosos: {n_low_quality}")
    frac_mal = (n_rejected + n_low_quality) / max(n, 1)
    if frac_mal > 0.01:
        print(f"  AVISO: {100*frac_mal:.0f}% de los fotogramas sin borde o dudosos. "
              f"Lo mas comun: el gel se mueve mas que la ventana de busqueda "
              f"(+-{config.half_window} px). Mira la hoja diagnostics de la serie.")
    if lim > UMBRAL_LIMITE:
        print(f"  AVISO: en el {100*lim:.0f}% de los fotogramas hay bordes pegados al limite "
              f"de la ventana de busqueda (+-{config.half_window} px): el borde verdadero "
              f"puede estar afuera. Mira la columna n_bordes_en_limite de la hoja diagnostics.")

    # --- Diagnostico del ajuste (Fase 4, H24): sin umbral, solo en detalle ---
    # outlier_frac ya NO es criterio de aceptacion (el umbral de descarte se
    # adapta a cada fotograma). Queda en `resumen`. Ver claude/propuesta-fase-4.md.
    if args.verbose:
        frac = float(df["outlier_frac"].mean())
        resid = float(df[["residual_top_px", "residual_bottom_px"]].mean().mean())
        print(f"  [detalle] ajuste (sin umbral): outliers {100*frac:.1f}% | residuo tipico "
              f"{resid:.3f} px | error de modelo sup/inf "
              f"{summary['error de modelo borde sup (px)']}/{summary['error de modelo borde inf (px)']} px "
              f"({summary['error de modelo peor / grosor (%)']}% del grosor)")

    if args.plot:
        calibrated = abs(args.px_to_mm - 1.0) > 1e-9
        p = plotting.plot_timeseries(
            df, out_dir,
            unit_label="mm" if calibrated else "px (SIN CALIBRAR)",
            calibrated=calibrated,
            name=f"01_serie_temporal_{video_name}",
        )
        archivos.append(Path(p).name)

    if args.px_to_mm == 1.0:
        print("Medidas en pixeles (sin calibrar a mm, a proposito: los videos no tienen "
              "todos el mismo aumento).")
    print(f"Archivos en {out_dir}:")
    for a in archivos:
        print(f"  {a}")


if __name__ == "__main__":
    main()
