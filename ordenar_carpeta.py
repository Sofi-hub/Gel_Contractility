"""Ordena la carpeta del proyecto. Correr desde la raiz del repo:

    python ordenar_carpeta.py           # muestra que haria, sin tocar nada
    python ordenar_carpeta.py --aplicar # lo hace

No borra nada: todo se mueve. Si algo no gusta, se deshace moviendo de vuelta.
"""
import shutil
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
APLICAR = "--aplicar" in sys.argv

# --- 1. corridas superadas -> data/processed_data/_superadas/ ---------------
PROC = RAIZ / "data" / "processed_data"
SUPERADAS = PROC / "_superadas"

# --- 2. documentos de analisis -> docs/ -------------------------------------
DOCS = RAIZ / "docs"
A_DOCS = [
    "cambios-roi-y-k.md",
    "diagnostico-bateria-4videos.md",
    "reproceso-bateria-v4.md",
    "base-de-tiempo-y-frames-perdidos.md",
    "comparacion-musclemotion.md",
    "DOCUMENTACION.md",
    "LEEME.md",
    "LEEME_v3.md",
    "gel_fix.md",
    "order.txt",
]
# Estos se quedan en la raiz: README.md (portada del repo) y CLAUDE.md
# (instrucciones del proyecto, que las herramientas buscan ahi).

# --- 3. resultados/ viejo -> data/processed_data/_superadas/ ----------------
RESULTADOS = RAIZ / "resultados"

acciones = []


def mover(origen: Path, destino: Path):
    if not origen.exists():
        return
    acciones.append((origen, destino))


def main():
    if not PROC.exists():
        sys.exit(f"No encuentro {PROC}. Corre esto desde la raiz del repo.")

    # YA SE APLICO (2026-09-30). Despues de aplicarlo, los vigentes quedan SIN
    # sufijo, y la regla de abajo ("todo lo que no termina en _v6 esta
    # superado") los tomaria a ELLOS como superados. Si no hay ningun _v6, no
    # hay nada que ordenar: se sale sin tocar nada.
    if not any(d.is_dir() and d.name.endswith("_v6") for d in PROC.iterdir()):
        print("No hay carpetas _v6: el ordenamiento ya se aplico. Los vigentes son las\n"
              "carpetas sin sufijo de data/processed_data/; no se mueve nada.")
        return

    # corridas superadas: todo lo que NO termina en _v6
    for d in sorted(PROC.iterdir()):
        if not d.is_dir() or d.name == "_superadas":
            continue
        if not d.name.endswith("_v6"):
            mover(d, SUPERADAS / d.name)

    # resultados/ viejo
    if RESULTADOS.exists():
        mover(RESULTADOS, SUPERADAS / "resultados_abril")

    # documentos
    for nombre in A_DOCS:
        mover(RAIZ / nombre, DOCS / nombre)

    if not acciones:
        print("No hay nada que mover: la carpeta ya esta ordenada.")
        return

    print(f"{'APLICANDO' if APLICAR else 'SIMULACION (nada se toca)'}\n")
    for origen, destino in acciones:
        print(f"  {origen.relative_to(RAIZ)}")
        print(f"    -> {destino.relative_to(RAIZ)}")
        if APLICAR:
            destino.parent.mkdir(parents=True, exist_ok=True)
            if destino.exists():
                print("       (ya existe en el destino, se saltea)")
                continue
            shutil.move(str(origen), str(destino))

    # renombrar los _v6 sin sufijo, ya que son los unicos que quedan
    print()
    for d in sorted(PROC.iterdir()) if PROC.exists() else []:
        if d.is_dir() and d.name.endswith("_v6"):
            nuevo = d.with_name(d.name[:-3])
            print(f"  {d.name}  ->  {nuevo.name}")
            if APLICAR and not nuevo.exists():
                d.rename(nuevo)

    if not APLICAR:
        print("\nNada de esto se ejecuto. Volve a correr con --aplicar.")
    else:
        print("\nListo.")


if __name__ == "__main__":
    main()
