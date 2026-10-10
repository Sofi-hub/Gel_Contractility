"""H23, segunda parte: reprocesa desde el video con las ventanas de la ROI
escaladas con el GEL (variante "gel" de medir_h23.py) y compara la huella contra
la referencia congelada. No toca el código del repo: reemplaza
preprocessing.auto_detect_roi solo dentro de este proceso.

    python data/_mediciones_fases/h23_ventanas_roi/reprocesar_h23.py [carpeta ...]
"""
from __future__ import annotations

import json
import sys
import tempfile
import time
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[2]
sys.path.insert(0, str(RAIZ)); sys.path.insert(0, str(AQUI)); sys.path.insert(0, str(RAIZ / "tests"))
import referencia as ref                       # noqa: E402
import medir_h23 as m                          # noqa: E402
from src import preprocessing                  # noqa: E402
from src.output_paths import buscar_serie      # noqa: E402
import main as main_mod                        # noqa: E402

def correr():
    preprocessing.auto_detect_roi = m.hacer(*m.VARIANTES["gel"])

    congelada = ref.cargar_referencia()["videos"]
    carpetas = sys.argv[1:] or list(ref.VIDEOS)
    salida = AQUI / "reproceso_gel.jsonl"
    for c in carpetas:
        video, extra, frec = ref.VIDEOS[c]
        t0 = time.time()
        with tempfile.TemporaryDirectory() as tmp:
            sys.argv = ["main.py", "--video", str(ref.CRUDOS / video), "--output-dir", tmp,
                        "--base-tiempo", "pts", "--procesos", "1", *extra]
            main_mod.main()
            h = ref.huella(buscar_serie(tmp), frec)
        dif = ref.diferencias(congelada[c], h)
        reg = {"video": c, "segundos": round(time.time() - t0), "identico": not dif,
               "diferencias": dif, "huella": h}
        with open(salida, "a", encoding="utf-8") as f:
            f.write(json.dumps(reg, ensure_ascii=False, default=str) + "\n")
        print(f"### {c}: {'IDENTICO' if not dif else 'DISTINTO'}", *dif, sep="\n    ", flush=True)


if __name__ == "__main__":
    correr()
