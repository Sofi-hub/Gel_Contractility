"""Fotogramas de Video_prueba entre 6.8 y 7.5 s, para mirar a ojo el evento de
7.28 s (fotograma 209, 1 fotograma, 24.9 x el ruido) y el hueco de 0.398 s
(entre los fotogramas 206 y 207). Solo LEE: no toca el analisis.

Salida en fotogramas_7_28/:
  fot_<n>.png        fotograma entero, con tiempo (pts) y numero arriba y los
                     bordes de la serie (y_top_px, y_bottom_px) dibujados sobre
                     la ROI. La serie guarda un valor por borde y fotograma (la
                     parabola por columna no se guarda), asi que la linea es
                     horizontal a esa altura.
  tira.png           todos en fila, recortados a la zona de los bordes
  tira_diferencia.png  |fotograma - anterior|, mismo recorte (ganancia x8)

    python data/_mediciones_fases/huecos_grabacion/fotogramas_7_28.py
"""
import sys
from pathlib import Path

import cv2
import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(RAIZ / "tests"))
from referencia import CRUDOS, PROCESADOS          # noqa: E402

AQUI = Path(__file__).resolve().parent
SALIDA = AQUI / "fotogramas_7_28"
T0, T1 = 6.8, 7.52
EVENTO = 209
HUECO = (206, 207)     # el hueco de 0.398 s va entre estos dos
MARGEN = 25            # px por encima y por debajo de cada borde en la tira
GANANCIA = 8


def guardar(ruta, img):
    """cv2.imwrite no escribe en rutas con acento: se codifica y se escribe con
    Python (la misma solucion que filtro_ancho.py, en D)."""
    bien, buf = cv2.imencode(".png", img)
    assert bien
    Path(ruta).write_bytes(buf.tobytes())


def video_de():
    p = CRUDOS / "Video_prueba.mp4"
    if not p.exists():   # en un worktree los videos crudos no estan
        p = RAIZ.parents[2] / "data" / "raw_videos" / "Video_prueba.mp4"
    return p


def rotulo(img, texto, color=(255, 255, 255)):
    cv2.rectangle(img, (0, 0), (img.shape[1], 22), (0, 0, 0), -1)
    cv2.putText(img, texto, (4, 16), cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 1, cv2.LINE_AA)


def main():
    xl = PROCESADOS / "Video_prueba" / "serie_temporal_Video_prueba.xlsx"
    s = pd.read_excel(xl, sheet_name="diagnostics")
    roi = pd.read_excel(xl, sheet_name="roi_alternativas")
    roi = roi[roi["elegida"].astype(bool)].iloc[0]
    x0, x1 = int(roi["x_start"]), int(roi["x_end"])
    sel = s[(s["time_s"] >= T0) & (s["time_s"] <= T1)]
    nums = sel["frame"].astype(int).tolist()

    # Leer en orden, como el pipeline (indice de fotograma = orden de lectura).
    cap = cv2.VideoCapture(str(video_de()))
    crudos = {}
    i = 0
    while i <= nums[-1]:
        ok, f = cap.read()
        if not ok:
            break
        if i >= nums[0] - 1:
            crudos[i] = f
        i += 1
    cap.release()

    SALIDA.mkdir(exist_ok=True)
    ytop = int(np.floor(sel["y_top_px"].min())) - MARGEN
    ybot = int(np.ceil(sel["y_bottom_px"].max())) + MARGEN
    tiras, difs = [], []
    for _, r in sel.iterrows():
        n = int(r["frame"])
        f = crudos[n].copy()
        for y, c in ((r["y_top_px"], (0, 255, 255)), (r["y_bottom_px"], (255, 0, 255))):
            cv2.line(f, (x0, int(round(y))), (x1, int(round(y))), c, 1)
        cv2.rectangle(f, (x0, 0), (x1, f.shape[0] - 1), (0, 255, 0), 1)
        txt = f"fot {n}  t={r['time_s']:.3f} s (pts)  centro={r['center_px']:.2f} px"
        if n == EVENTO:
            txt += "  EVENTO"
        if n == HUECO[1]:
            txt += "  <- HUECO 0.398 s antes"
        rotulo(f, txt, (0, 0, 255) if n in (EVENTO, HUECO[1]) else (255, 255, 255))
        guardar(SALIDA / f"fot_{n}.png", f)

        rec = f[max(ytop, 0):ybot, x0:x1].copy()
        rotulo(rec, f"{n} {r['time_s']:.3f}s", (0, 0, 255) if n == EVENTO else (255, 255, 255))
        tiras.append(rec)
        g = cv2.cvtColor(crudos[n], cv2.COLOR_BGR2GRAY).astype(np.int16)
        g0 = cv2.cvtColor(crudos[n - 1], cv2.COLOR_BGR2GRAY).astype(np.int16)
        d = np.clip(np.abs(g - g0) * GANANCIA, 0, 255).astype(np.uint8)[max(ytop, 0):ybot, x0:x1]
        d = cv2.cvtColor(d, cv2.COLOR_GRAY2BGR)
        rotulo(d, f"{n}-{n - 1}", (0, 0, 255) if n == EVENTO else (255, 255, 255))
        difs.append(d)
        if n == HUECO[0]:      # separador rojo donde esta el hueco
            for lst in (tiras, difs):
                lst.append(np.full((rec.shape[0], 12, 3), (0, 0, 255), np.uint8))
        else:
            for lst in (tiras, difs):
                lst.append(np.full((rec.shape[0], 3, 3), 128, np.uint8))

    guardar(SALIDA / "tira.png", np.hstack(tiras[:-1]))
    guardar(SALIDA / "tira_diferencia.png", np.hstack(difs[:-1]))
    print(f"{len(nums)} fotogramas ({nums[0]}-{nums[-1]}), ROI x={x0}-{x1}, recorte y={ytop}-{ybot}")


if __name__ == "__main__":
    main()
