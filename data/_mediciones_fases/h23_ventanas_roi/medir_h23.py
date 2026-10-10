"""H23: ¿cambia la ROI si las ventanas de suavizado escalan con el GEL y no con la imagen?

Hoy, en auto_detect_roi:
    k = max(5, w // 60)    mediana del perfil de grosor y de los bordes guía (32 px a 1920)
    d = max(10, w // 50)   promedio antes de derivar la pendiente (38 px a 1920)
Las dos dependen solo del ANCHO DE LA IMAGEN (igual en los 11 videos).

Variantes medidas (sin tocar el código del repo: se ejecuta una copia de la
función con las dos ventanas reemplazadas):
    actual     k, d como hoy
    gel        k = 32 * G/294, d = 38 * G/294   (G = grosor mediano del gel en ese
               video; 294 px = Video_prueba, así ahí da lo mismo que hoy)
    x0.5, x2   k y d a la mitad y al doble (sensibilidad: ¿importa la ventana?)

Para cada video y variante: ROI (x_start, x_end, método, variación, columnas).
Si la ROI es la misma, center_px no puede cambiar.

    python data/_mediciones_fases/h23_ventanas_roi/medir_h23.py
"""
from __future__ import annotations

import inspect
import sys
import textwrap
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "tests"))
import referencia as ref                          # noqa: E402
from src import preprocessing as pp              # noqa: E402
from src import io_utils                          # noqa: E402

AQUI = Path(__file__).resolve().parent
SRC = textwrap.dedent(inspect.getsource(pp.auto_detect_roi))
assert "max(5, w // 60)" in SRC and "max(10, w // 50)" in SRC
SRC = (SRC.replace("def auto_detect_roi(", "def roi_variante(")
          .replace("max(5, w // 60)", "_K(w, thickness, valid)")
          .replace("max(10, w // 50)", "_D(w, thickness, valid)"))


def hacer(fk, fd):
    ns = dict(vars(pp))
    ns["_K"], ns["_D"] = fk, fd
    exec(SRC, ns)
    return ns["roi_variante"]


def G(th, valid):
    v = th[valid & np.isfinite(th)]
    return float(np.median(v)) if v.size else 294.0


VARIANTES = {
    "actual": (lambda w, t, v: max(5, w // 60), lambda w, t, v: max(10, w // 50)),
    "gel":    (lambda w, t, v: max(5, int(round((w // 60) * G(t, v) / 294))),
               lambda w, t, v: max(10, int(round((w // 50) * G(t, v) / 294)))),
    "x0.5":   (lambda w, t, v: max(5, (w // 60) // 2), lambda w, t, v: max(10, (w // 50) // 2)),
    "x2":     (lambda w, t, v: max(5, 2 * (w // 60)), lambda w, t, v: max(10, 2 * (w // 50))),
}


def main():
    filas = []
    cache = AQUI / "_maxproj"
    cache.mkdir(exist_ok=True)
    for carpeta, (video, _, _) in ref.VIDEOS.items():
        f = cache / f"{carpeta}.npy"
        if f.exists():
            mp = np.load(f)
        else:
            _, mp = io_utils.read_pts_and_max_projection(str(ref.CRUDOS / video), stride=5)
            np.save(f, mp)
        base = None
        for nom, (fk, fd) in VARIANTES.items():
            r = hacer(fk, fd)(mp)
            q = r["roi_quality"]
            fila = {"video": carpeta, "variante": nom, "x_start": r["x_start"],
                    "x_end": r["x_end"], "metodo": q.get("method"),
                    "variacion_pct": q.get("variacion_en_roi_pct"),
                    "cumple": q.get("cumple_criterio_aceptacion"),
                    "n_columnas": q.get("n_columnas_usadas")}
            if nom == "actual":
                base = r
            else:
                fila["misma_roi"] = (r["x_start"], r["x_end"]) == (base["x_start"], base["x_end"])
                xs, xe = base["x_start"], base["x_end"]
                # la guia entra a process_frame como entero: contar columnas donde cambia
                dt = r["top_guess"][xs:xe].astype(int) != base["top_guess"][xs:xe].astype(int)
                db = r["bottom_guess"][xs:xe].astype(int) != base["bottom_guess"][xs:xe].astype(int)
                fila["guia_cols_distintas_pct"] = round(100 * float(np.mean(dt | db)), 1)
                fila["guia_dif_max_px"] = float(np.nanmax(np.abs(np.r_[
                    r["top_guess"][xs:xe] - base["top_guess"][xs:xe],
                    r["bottom_guess"][xs:xe] - base["bottom_guess"][xs:xe]])))
            filas.append(fila)
            print(fila, flush=True)
    df = pd.DataFrame(filas)
    df.to_csv(AQUI / "tabla_h23.csv", index=False)
    print(df.to_string(index=False))


if __name__ == "__main__":
    main()
