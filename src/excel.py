"""Leer los Excel de resultados más rápido (solo lectura; la ventana, el informe y la tabla).

Con `python-calamine` instalado, pandas lee ~8 veces más rápido y da exactamente las
mismas tablas (comprobado en los 23 Excel de processed_data, 2026-10-11). Sin él, se
usa el lector de siempre (openpyxl). Escribir los Excel no cambia.
"""
from __future__ import annotations

import pandas as pd

try:
    import python_calamine  # noqa: F401
    MOTOR = "calamine"
except Exception:   # opcional
    MOTOR = None


def read_excel(*args, **kwargs):
    if MOTOR and "engine" not in kwargs:
        try:
            return pd.read_excel(*args, engine=MOTOR, **kwargs)
        except Exception:
            pass   # cualquier problema: el lector de siempre
    return pd.read_excel(*args, **kwargs)
