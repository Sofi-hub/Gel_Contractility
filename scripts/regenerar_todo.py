"""Regenera los resultados vigentes de todos los videos de referencia.

Para cada carpeta de `tests/referencia.py` (VIDEOS):
  1. guarda la huella de los resultados viejos (antes de pisarlos);
  2. corre main.py y contraction_report.py con los argumentos de ese video;
  3. compara la huella vieja con la nueva;
  4. si son idénticas, borra los Excel con nombre viejo (serie_temporal.xlsx,
     contracciones.xlsx). Si algo cambió, NO borra nada y lo muestra.

No cambia ningún número: si la tabla final dice "CAMBIÓ", hay que mirarlo antes
de seguir. Los resultados viejos siguen en el historial de git.

    python scripts/regenerar_todo.py                    # los 11 (~15 min)
    python scripts/regenerar_todo.py --solo Video_prueba Video_063_CTRL1_5V
    python scripts/regenerar_todo.py --sin-video        # solo el reporte (segundos)
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "tests"))
sys.path.insert(0, str(RAIZ))
import referencia as ref                      # noqa: E402
from src.output_paths import buscar_serie     # noqa: E402

NOMBRES_VIEJOS = ("serie_temporal.xlsx", "contracciones.xlsx")


def correr(cmd: list[str]) -> None:
    print("   $", " ".join(str(c) for c in cmd[1:]))
    p = subprocess.run(cmd, cwd=RAIZ, capture_output=True, text=True)
    if p.returncode != 0:
        print(p.stdout[-2000:], p.stderr[-3000:])
        raise SystemExit(f"Falló: {' '.join(map(str, cmd[1:3]))}")


def regenerar(carpeta: str, sin_video: bool, tmp: Path) -> tuple[str, list[str]]:
    video, extra, frec = ref.VIDEOS[carpeta]
    out = ref.PROCESADOS / carpeta
    serie_vieja = buscar_serie(out)
    if not serie_vieja.exists():
        return "SIN DATOS VIEJOS", [f"no hay serie en {out}"]
    copia = tmp / f"{carpeta}.xlsx"
    shutil.copy2(serie_vieja, copia)
    h_vieja = ref.huella(copia, frec)

    if sin_video:
        serie_nueva = serie_vieja
    else:
        ruta_video = ref.CRUDOS / video
        if not ruta_video.exists():
            return "SIN VIDEO", [str(ruta_video)]
        correr([sys.executable, "main.py", "--video", str(ruta_video),
                "--output-dir", str(out), "--base-tiempo", "pts", *extra])
        serie_nueva = out / f"serie_temporal_{Path(video).stem}.xlsx"

    cmd = [sys.executable, "scripts/contraction_report.py", "--input", str(serie_nueva)]
    if frec:
        cmd += ["--frecuencia-estimulo", *map(str, frec)]
    correr(cmd)

    h_nueva = ref.huella(serie_nueva, frec)
    dif = ref.diferencias(h_vieja, h_nueva)
    if dif:
        return "CAMBIÓ (no se borró nada)", dif
    borrados = []
    for n in NOMBRES_VIEJOS:
        p = out / n
        if p.exists() and p != serie_nueva:
            p.unlink()
            borrados.append(n)
    return "idéntico", ([f"borrados: {', '.join(borrados)}"] if borrados else [])


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--solo", nargs="+", choices=list(ref.VIDEOS), default=None)
    ap.add_argument("--sin-video", action="store_true",
                    help="no correr main.py: solo rehacer el reporte sobre la serie existente")
    a = ap.parse_args()

    filas = []
    with tempfile.TemporaryDirectory() as tmp:
        for carpeta in a.solo or ref.VIDEOS:
            print(f"\n== {carpeta}")
            t0 = time.time()
            estado, det = regenerar(carpeta, a.sin_video, Path(tmp))
            filas.append((carpeta, estado, det))
            print(f"   {estado} ({time.time() - t0:.0f} s)")

    print("\nRESUMEN")
    for carpeta, estado, det in filas:
        print(f"  {carpeta:28s} {estado}")
        for d in det:
            print(f"      {d}")
    if any(e != "idéntico" for _, e, _ in filas):
        sys.exit(1)


if __name__ == "__main__":
    main()
