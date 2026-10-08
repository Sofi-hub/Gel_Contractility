"""Regresión contra los resultados congelados (tests/referencia_regresion.json).

    python tests/test_regresion.py             rápido (segundos): rehace el reporte
                                               sobre cada serie_temporal guardada
    python tests/test_regresion.py --completo  además vuelve a procesar Video_prueba
                                               y Video_063 desde el video (~2-3 min)
                                               y exige center_px idéntico

El rápido detecta cambios en la detección, la meseta, el ritmo y la cinética.
El completo detecta además cambios en ROI, bordes y RANSAC. Necesita los videos
en data/raw_videos/ (si no están, avisa y no falla).

Si un cambio es intencional, medido y aprobado:
    python tests/generar_referencia.py --aprobar "motivo"
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import referencia as ref                       # noqa: E402
from src.output_paths import buscar_serie      # noqa: E402


def comparar(nombre: str, actual: dict, congelada: dict) -> bool:
    dif = ref.diferencias(congelada, actual)
    print(f"  {nombre:36s} {'OK' if not dif else 'DISTINTO'}"
          f"   ({actual['n_eventos']} eventos)")
    for d in dif:
        print(f"      {d}")
    return not dif


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--completo", action="store_true")
    a = ap.parse_args()
    congelada = ref.cargar_referencia()["videos"]
    ok = True

    print("Reporte sobre las series guardadas:")
    for carpeta, h in congelada.items():
        frec = ref.VIDEOS[carpeta][2]
        serie = buscar_serie(ref.PROCESADOS / carpeta)
        if not serie.exists():
            print(f"  {carpeta:36s} FALTA la serie"); ok = False; continue
        ok &= comparar(carpeta, ref.huella(serie, frec), h)

    if a.completo:
        print("\nDesde el video (main.py en una carpeta temporal):")
        for carpeta in ref.REGRESION_COMPLETA:
            video, extra, frec = ref.VIDEOS[carpeta]
            ruta = ref.CRUDOS / video
            if not ruta.exists():
                print(f"  {carpeta:36s} sin video, se omite"); continue
            with tempfile.TemporaryDirectory() as tmp:
                p = subprocess.run([sys.executable, "main.py", "--video", str(ruta),
                                    "--output-dir", tmp, "--base-tiempo", "pts", *extra],
                                   cwd=ref.RAIZ, capture_output=True, text=True)
                if p.returncode:
                    print(p.stderr[-2000:]); ok = False; continue
                ok &= comparar(carpeta + " (video)",
                               ref.huella(buscar_serie(tmp), frec), congelada[carpeta])

    print("\nTODO IGUAL" if ok else "\nHAY DIFERENCIAS")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
