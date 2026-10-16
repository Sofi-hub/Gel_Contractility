"""Gel VERTICAL (videos de Andrés, 2026-10-15): main.py gira solo los fotogramas.

    python tests/test_orientacion.py

1. La regla: un gel horizontal da cociente > 1 y girado < 1.
2. Con rotación 0 la lectura no cambia nada (mismo objeto).
3. El MISMO gel sintético grabado horizontal y vertical da la misma serie
   center_px (la detección de bordes es la de siempre, sobre la imagen girada).
"""
from __future__ import annotations
import sys
import tempfile
from pathlib import Path

import cv2
import numpy as np

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
from src import io_utils  # noqa: E402
from src.pipeline import PipelineConfig, process_video  # noqa: E402

ok = True


def check(nombre, cond):
    global ok
    print(f"  {'OK   ' if cond else 'FALLA'} {nombre}")
    ok &= bool(cond)


def gel(desp, h=240, w=360):
    """Franja horizontal clara con bordes suaves, desplazada `desp` px hacia abajo."""
    y = np.arange(h)[:, None] - desp
    franja = 1 / (1 + np.exp(-(y - 80) / 1.5)) - 1 / (1 + np.exp(-(y - 160) / 1.5))
    rng = np.random.default_rng(int(1000 * desp) % 2**31)
    img = 40 + 150 * franja + rng.normal(0, 2, (h, 1)) * 0 + np.zeros((h, w))
    return np.clip(img + rng.normal(0, 1.5, img.shape), 0, 255).astype(np.uint8)


img = gel(0)
check("horizontal: cociente > 1", io_utils.cociente_orientacion(img) > 1)
check("girado: cociente < 1 y se elige girar 90",
      io_utils.elegir_rotacion(cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE))[0] == 90)
check("rotación 0 no toca la imagen", io_utils.rotar(img, 0) is img)
check("girar 90 y volver con 270 da la misma imagen",
      np.array_equal(io_utils.rotar(io_utils.rotar(img, 90), 270), img))

with tempfile.TemporaryDirectory() as tmp:
    fps, n = 30, 240
    desp = [3.0 * np.exp(-((k / fps - 4.0) / 0.15) ** 2) for k in range(n)]   # un pulso de 3 px a los 4 s
    rutas = {}
    for nombre, giro in (("h", None), ("v", cv2.ROTATE_90_COUNTERCLOCKWISE)):
        p = Path(tmp) / f"{nombre}.avi"
        f0 = gel(0) if giro is None else cv2.rotate(gel(0), giro)
        vw = cv2.VideoWriter(str(p), cv2.VideoWriter_fourcc(*"FFV1"), fps, (f0.shape[1], f0.shape[0]), False)
        for d in desp:
            f = gel(d)
            vw.write(f if giro is None else cv2.rotate(f, giro))
        vw.release()
        rutas[nombre] = p
    dh = process_video(str(rutas["h"]), PipelineConfig(), verbose=False)
    dv = process_video(str(rutas["v"]), PipelineConfig(), verbose=False)
    check("horizontal: no se gira", dh.attrs["rotacion"] == 0)
    check("vertical: se gira 90 solo", dv.attrs["rotacion"] == 90 and dv.attrs["rotacion_modo"] == "automatica")
    ch = dh["center_px"].to_numpy(float) - np.nanmedian(dh["center_px"])
    cv = dv["center_px"].to_numpy(float) - np.nanmedian(dv["center_px"])
    # girado 90 en sentido horario, "abajo" en el horizontal es "arriba" o "abajo"
    # según el giro: se compara la magnitud del pulso y la forma
    amp_h = np.nanmax(np.abs(ch)); amp_v = np.nanmax(np.abs(cv))
    check(f"mismo pulso: {amp_h:.2f} px horizontal, {amp_v:.2f} px vertical (puesto: 3)",
          abs(amp_h - 3) < 0.3 and abs(amp_v - 3) < 0.3)
    check("misma forma (correlación > 0.98)", abs(np.corrcoef(ch, cv)[0, 1]) > 0.98)

print("\nTODO OK" if ok else "\nHAY FALLAS")
sys.exit(0 if ok else 1)
