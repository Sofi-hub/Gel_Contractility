"""
achicar_video.py
----------------
Copia de un video a menor resolución, con TODOS sus fotogramas, para poder
pasarla a Claude (límite de 400 MB por archivo) o probar rápido. No se usa en
el análisis: el original queda igual.

    python scripts/achicar_video.py --video "data/raw_videos/Videos_Andres/40V/1.mp4"

Escribe data/raw_videos/_copias_chicas/<carpeta>_<video>_x<porcentaje>.mp4 (x50 = mitad) (gris,
mismo fps). Por defecto factor 0.5 (4K -> 1920x1080) y los primeros 70 s.
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import cv2

RAIZ = Path(__file__).resolve().parents[1]


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--video", required=True)
    p.add_argument("--factor", type=float, default=0.5, help="escala (0.5 = mitad de ancho y alto)")
    p.add_argument("--segundos", type=float, default=70.0, help="cuánto copiar desde el inicio")
    p.add_argument("--salida", default=None)
    a = p.parse_args()
    v = Path(a.video)
    cap = cv2.VideoCapture(str(v))
    if not cap.isOpened():
        sys.exit(f"No pude abrir {v}")
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) * a.factor) // 2 * 2
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) * a.factor) // 2 * 2
    nombre = f"{v.parent.name}_{v.stem}" if v.stem.isdigit() else v.stem
    out = Path(a.salida) if a.salida else RAIZ / "data" / "raw_videos" / "_copias_chicas" / f"{nombre}_x{round(100 * a.factor)}.mp4"
    out.parent.mkdir(parents=True, exist_ok=True)
    vw = cv2.VideoWriter(str(out), cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h), False)
    n, t0, maxn = 0, time.time(), int(a.segundos * fps)
    print(f"{v.name}: {int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))}x{int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))} "
          f"a {fps:.2f} fps -> {w}x{h}, {a.segundos:g} s")
    while n < maxn:
        ok, f = cap.read()
        if not ok:
            break
        g = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY) if f.ndim == 3 else f
        vw.write(cv2.resize(g, (w, h), interpolation=cv2.INTER_AREA))
        n += 1
        if n % 300 == 0:
            print(f"  {n} fotogramas ({time.time() - t0:.0f} s)", flush=True)
    cap.release()
    vw.release()
    print(f"Listo: {n} fotogramas en {out} ({out.stat().st_size / 1e6:.0f} MB)")


if __name__ == "__main__":
    main()
