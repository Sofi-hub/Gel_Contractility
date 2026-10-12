"""Cuánto tarda cada parte de main.py en ESTA máquina (pendientes B3a).

    python data/_mediciones_fases/tiempos_main/medir_tiempos.py --video "<ruta al video>"

No cambia nada ni guarda resultados: repite, cronometrando, los mismos pasos
que hace process_video (mismas funciones) y al final imprime una tabla para
pegar en el chat. Tarda ~3-4 veces lo que tarda main.py (lee el video varias
veces a propósito, para separar las partes).
"""
from __future__ import annotations

import argparse
import os
import platform
import sys
import time
from pathlib import Path

T0 = time.perf_counter()
RAIZ = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(RAIZ))
import numpy as np                                    # noqa: E402
from src import io_utils, preprocessing, pipeline     # noqa: E402
from src.pipeline import PipelineConfig               # noqa: E402
T_IMPORT = time.perf_counter() - T0


def cron(nombre, f, filas):
    t = time.perf_counter()
    out = f()
    dt = time.perf_counter() - t
    filas.append((nombre, dt))
    print(f"  {nombre:<55s} {dt:7.1f} s", flush=True)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", required=True)
    ap.add_argument("--procesos", type=int, nargs="+", default=[1, 2],
                    help="con cuántos procesos medir los fotogramas (default: 1 y 2)")
    a = ap.parse_args()
    v = a.video
    filas = [("cargar librerías (numpy, opencv, sklearn...)", T_IMPORT)]
    print(f"Video: {v}\n  {'cargar librerías':<55s} {T_IMPORT:7.1f} s", flush=True)
    cfg = PipelineConfig()

    meta = cron("metadatos del video", lambda: io_utils.get_video_metadata(v), filas)
    pts, maxp = cron("1.ª lectura: timestamps + mapa de máximos",
                     lambda: io_utils.read_pts_and_max_projection(v, stride=5), filas)
    roi = cron("elegir la zona (auto-ROI)", lambda: preprocessing.auto_detect_roi(
        maxp, thickness_tolerance=cfg.roi_thickness_tolerance,
        min_gradient_for_roi=cfg.roi_min_gradient, max_thickness_slope=cfg.roi_max_slope,
        n_columns=cfg.n_columns, min_column_spacing_px=cfg.roi_min_column_spacing_px,
        min_columns=cfg.roi_min_columns, max_variacion_pct=cfg.roi_max_variacion_pct), filas)

    def solo_decodificar():
        n = 0
        for _ in io_utils.frame_generator(v):
            n += 1
        return n
    n = cron("2.ª lectura SOLA: decodificar todos los fotogramas", solo_decodificar, filas)

    n_cols = int(roi.get("roi_quality", {}).get("n_columnas_usadas") or cfg.n_columns)
    xs = np.linspace(roi["x_start"], roi["x_end"] - 1, n_cols).astype(int)
    for p in a.procesos:
        cron(f"2.ª lectura + bordes/RANSAC de cada fotograma ({p} proc.)",
             lambda p=p: sum(1 for _ in pipeline._procesar_fotogramas(
                 v, xs, roi["top_guess"], roi["bottom_guess"], cfg, p)), filas)

    # bordes/RANSAC solos, sin leer el video: sobre 200 fotogramas ya en memoria
    frames = [f for _, f in zip(range(200), (f for _, f in io_utils.frame_generator(v)))]
    t = time.perf_counter()
    for f in frames:
        pipeline.process_frame(f, xs, roi["top_guess"], roi["bottom_guess"], cfg)
    por_fot = (time.perf_counter() - t) / max(len(frames), 1)
    filas.append((f"bordes/RANSAC sin leer (1 proc., estimado {n} fot.)", por_fot * n))
    print(f"  {'bordes/RANSAC sin leer (1 proc.), estimado':<55s} {por_fot * n:7.1f} s", flush=True)

    print("\n=== PEGAR ESTO EN EL CHAT ===")
    print(f"maquina: {platform.platform()} | {os.cpu_count()} nucleos | python {platform.python_version()}")
    print(f"video: {Path(v).name} | {n} fotogramas | {meta.get('width')}x{meta.get('height')}")
    for nom, dt in filas:
        print(f"{nom:<60s} {dt:7.1f} s")
    print(f"{'total de esta medición':<60s} {time.perf_counter() - T0:7.1f} s")


if __name__ == "__main__":
    main()
