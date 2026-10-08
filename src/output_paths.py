"""
output_paths.py
----------------
Estructura de salida del proyecto. Todo lo generado va a
    data/processed_data/<nombre_del_video>/
de modo que cada video tenga su propia carpeta con su Excel y sus
gráficos, en vez de archivos sueltos mezclados.
"""

from __future__ import annotations
from pathlib import Path


def project_root(start: Path | None = None) -> Path:
    """
    Busca la raíz del proyecto subiendo hasta encontrar la carpeta
    `data`. Así los scripts funcionan igual si se ejecutan desde la
    raíz o desde `scripts/`.
    """
    here = (start or Path(__file__).resolve()).parent
    for p in [here, *here.parents]:
        if (p / "data").is_dir():
            return p
    return Path.cwd()


def video_output_dir(source: str | Path, root: Path | None = None,
                     create: bool = True) -> Path:
    """
    Carpeta de salida para un video: data/processed_data/<stem>/

    `source` puede ser la ruta del video o de un archivo derivado de
    él; se usa el nombre sin extensión.
    """
    root = root or project_root()
    out = root / "data" / "processed_data" / Path(source).stem
    if create:
        out.mkdir(parents=True, exist_ok=True)
    return out


def buscar_serie(carpeta: str | Path) -> Path:
    """
    El Excel de la serie temporal dentro de una carpeta de resultados.

    Desde 2026-10-08 se llama `serie_temporal_<video>.xlsx`; antes,
    `serie_temporal.xlsx`. Se aceptan los dos para no romper resultados
    viejos: primero el nombre nuevo, y si no hay, el viejo. Si no existe
    ninguno devuelve la ruta vieja (el que llama decide qué avisar).
    """
    carpeta = Path(carpeta)
    nuevos = sorted(carpeta.glob("serie_temporal_*.xlsx"))
    if nuevos:
        return nuevos[0]
    return carpeta / "serie_temporal.xlsx"
