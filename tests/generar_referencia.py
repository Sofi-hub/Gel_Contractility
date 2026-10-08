"""Congela las huellas de los resultados vigentes en referencia_regresion.json.

Correr SOLO después de un cambio medido y aprobado (o la primera vez):

    python tests/generar_referencia.py --aprobar "motivo del cambio"

Sin --aprobar, muestra qué cambiaría respecto de la referencia actual y no
escribe nada.
"""
from __future__ import annotations

import argparse
import datetime as dt
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import referencia as ref                                       # noqa: E402
from src.output_paths import buscar_serie                      # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--aprobar", metavar="MOTIVO", default=None)
    a = ap.parse_args()

    try:
        vieja = ref.cargar_referencia()
    except FileNotFoundError:
        vieja = {"videos": {}}

    nuevas = {}
    for carpeta, (_, _, frec) in ref.VIDEOS.items():
        serie = buscar_serie(ref.PROCESADOS / carpeta)
        if not serie.exists():
            print(f"  {carpeta}: sin serie, se omite")
            continue
        nuevas[carpeta] = ref.huella(serie, frec)
        dif = ref.diferencias(vieja["videos"].get(carpeta, {}), nuevas[carpeta])
        print(f"  {carpeta:28s} {'igual' if not dif else 'CAMBIA'}")
        for d in dif:
            print(f"      {d}")

    if not a.aprobar:
        print("\nNo se escribió nada (falta --aprobar \"motivo\").")
        return
    historial = vieja.get("historial", []) + [
        {"fecha": dt.date.today().isoformat(), "motivo": a.aprobar}]
    ref.guardar_referencia({"historial": historial, "videos": nuevas})
    print(f"\nEscrito {ref.ARCHIVO_REFERENCIA.name}.")


if __name__ == "__main__":
    main()
