"""B7 (2026-10-15): busqueda dirigida a 0.1 Hz en 613 y 068 (el equipo confirmo
que todos los videos con voltaje en el nombre son a 0.1 Hz). Corre el reporte
en memoria con y sin --frecuencia-estimulo 0.1, sin escribir nada.

    python data/_mediciones_fases/b7_dirigida_613_068/medir.py
"""
from __future__ import annotations
import sys, warnings
from pathlib import Path
import numpy as np
import pandas as pd
RAIZ = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(RAIZ)); sys.path.insert(0, str(RAIZ / "scripts")); sys.path.insert(0, str(RAIZ / "tests"))
import contraction_report as cr  # noqa: E402
from referencia import PROCESADOS, leer_serie  # noqa: E402
from src.output_paths import buscar_serie  # noqa: E402

filas = []
for carpeta in ("Video_613", "Video_068_hw30"):
    df, _ = leer_serie(buscar_serie(PROCESADOS / carpeta))
    for frec in (None, [0.1]):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            a = cr.analizar(df, "center_px", None, None, None, 1.5, frecuencia_estimulo=frec)
        rit = a.get("ritmo") or {}
        f = {"video": carpeta, "frecuencia": "libre" if frec is None else "0.1 Hz dirigida",
             "candidatos": a.get("n_eventos"), "conteo_reportable": a.get("conteo_reportable"),
             "k": a.get("k_usado"), "falsos_control": a.get("n_falsos", a.get("falsos_control")),
             "tren": rit.get("hay_estimulacion"), "n_estimulados": rit.get("n_estimulados"),
             "periodo_s": rit.get("periodo_s"), "captura": rit.get("captura"),
             "p_valor": rit.get("p_valor"), "veredicto_ritmo": rit.get("veredicto"),
             "amplitud_%": a.get("amplitud_relativa_pct"), "grupo": a.get("cinetica_grupo_principal")}
        if rit:
            f["claves_ritmo"] = ",".join(k for k in rit if not k.startswith("_"))[:400]
        filas.append(f)
        print(f, flush=True)
pd.DataFrame(filas).to_csv(Path(__file__).with_name("tabla.csv"), index=False)
