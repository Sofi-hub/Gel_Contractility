"""Videos de referencia y "huella" de sus resultados, para la regresión.

La huella son los números que importan de un video: la ROI, la serie
`center_px` (por su hash) y lo que sale del reporte (eventos, k, meseta,
instantes, amplitudes, tren y cinética). La usan:

  scripts/regenerar_todo.py      regenera todo y compara viejo contra nuevo
  tests/generar_referencia.py    congela las huellas en referencia_regresion.json
  tests/test_regresion.py        compara lo actual contra lo congelado

Sobre las frecuencias: en los seis videos de la carpeta OK, 0.1 Hz NO está
confirmado por el equipo (el nombre del archivo no lo dice; lo midió el propio
pipeline en búsqueda libre). Se mantiene para que la regresión siga siendo la
misma. En videos nuevos no se pasa frecuencia salvo que el equipo la confirme.
"""
from __future__ import annotations

import hashlib
import json
import math
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "scripts"))

PROCESADOS = RAIZ / "data" / "processed_data"
CRUDOS = RAIZ / "data" / "raw_videos"
OK = "OK-20260904T142817Z-1-001/OK"
RAR = "RARITOS-20260904T171415Z-1-001/RARITOS"
ARCHIVO_REFERENCIA = Path(__file__).with_name("referencia_regresion.json")

# carpeta de resultados -> (video crudo, argumentos extra de main.py, frecuencia)
VIDEOS = {
    "Video_prueba":               ("Video_prueba.mp4", [], [0.1]),
    "Video_063_CTRL1_5V":         (f"{OK}/Video_063_CTRL1_5V.mp4", [], [0.1]),
    "Video_268_EXP3_FAPS2_40V":   (f"{OK}/Video_268_EXP3_FAPS2_40V.mp4", [], [0.1]),
    "Video_466_EXP5_FAPS4_40V":   (f"{OK}/Video_466_EXP5_FAPS4_40V.mp4", [], [0.1]),
    "Video_583_EXP6_CTRL4_40V":   (f"{OK}/Video_583_EXP6_CTRL4_40V.mp4", [], [0.1]),
    "Video_491_EXP5_CTRL1_36HZ":  (f"{OK}/Video_491_EXP5_CTRL1_36HZ.mp4", [], None),
    "Video_476":                  (f"{RAR}/Video_476_EXP5_FAPS5_40V.mp4", [], [0.1]),
    "Video_613":                  (f"{RAR}/Video_613_EXP6_CTRL7_40V.mp4", [], None),
    # B1 (2026-10-10): la ventana de busqueda es automatica. 068 y 341 pasan solos
    # a +-30 (068 conserva el sufijo _hw30 en la carpeta por historia); 304 queda
    # en +-15 (antes iba con 30 a mano; con 15 RANSAC descarta menos columnas).
    "Video_068_hw30":             (f"{RAR}/Video_068_FAPS2_5V.mp4", [], None),
    "Video_304":                  (f"{RAR}/Video_304_EXP3_FAPS1_1_2HZ.mp4", [], None),
    "Video_341":                  (f"{RAR}/Video_341_EXP3_FAPS6_5_10HZ.mp4", [], None),
}
# los que el modo --completo vuelve a procesar desde el video
REGRESION_COMPLETA = ["Video_prueba", "Video_063_CTRL1_5V"]

TOL_REL = 1e-9   # "idéntico", salvo el redondeo de guardar en Excel


def leer_serie(path: Path) -> tuple[pd.DataFrame, dict]:
    hojas = pd.read_excel(path, sheet_name=None)
    df = hojas["diagnostics"]
    res = hojas.get("resumen")
    meta = dict(zip(res["Métrica"], res["Valor"])) if res is not None else {}
    return df, meta


def hash_serie(v: np.ndarray) -> str:
    v = np.round(np.asarray(v, float), 9)
    return hashlib.sha256(np.nan_to_num(v, nan=-1e12).tobytes()).hexdigest()[:16]


def _num(x):
    if x is None:
        return None
    if isinstance(x, (np.integer, int, bool, np.bool_)):
        return x.item() if hasattr(x, "item") else x
    try:
        f = float(x)
    except (TypeError, ValueError):
        return str(x)
    return None if math.isnan(f) else f


def huella(serie_path: Path, frecuencia=None) -> dict:
    """Corre el reporte (sin escribir nada) sobre una serie y resume el resultado."""
    from contraction_report import analizar
    df, meta = leer_serie(serie_path)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        r = analizar(df, "center_px", None, None, None, 1.5,
                     frecuencia_estimulo=frecuencia)
    rit = r.get("ritmo") or {}
    h = {
        "roi": [_num(meta.get("ROI x_start")), _num(meta.get("ROI x_end")),
                meta.get("ROI metodo"), _num(meta.get("n_columnas usadas"))],
        "n_frames": int(len(df)),
        "hash_center_px": hash_serie(df["center_px"]),
        "signo": _num(r.get("signo")),
        "n_eventos": _num(r.get("n_eventos")),
        "conteo_reportable": bool(r.get("conteo_reportable")),
        "k_usado": _num(r.get("k_usado")),
        "meseta_k_rango": _num(r.get("meseta_k_rango")),
        "ruido_canal_px": _num(r.get("ruido_canal_px")),
        "tiempos_s": [float(x) for x in r.get("tiempos_s", [])],
        "amplitudes_px": [float(x) for x in np.asarray(r["_r"])[r["_picos"]]]
                         if r.get("n_eventos") else [],
        "amplitud_traslacion_px": _num(r.get("amplitud_traslacion_px")),
        "amplitud_relativa_pct": _num(r.get("amplitud_relativa_pct")),
        "hay_estimulacion": bool(rit.get("hay_estimulacion", False)),
        "n_estimulados": _num(rit.get("n_estimulados")),
        "periodo_s": _num(rit.get("periodo_s")),
        "periodo_err_s": _num(rit.get("periodo_err_s")),
        "ttp_s": _num(r.get("ttp_s")),
        "rt50_s": _num(r.get("rt50_s")),
    }
    return h


def _igual(a, b) -> bool:
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(_igual(x, y) for x, y in zip(a, b))
    if isinstance(a, float) or isinstance(b, float):
        if a is None or b is None:
            return a is b
        return math.isclose(float(a), float(b), rel_tol=TOL_REL, abs_tol=1e-12)
    return a == b


def diferencias(vieja: dict, nueva: dict) -> list[str]:
    """Lista legible de lo que cambió entre dos huellas (vacía = idénticas)."""
    out = []
    for k in sorted(set(vieja) | set(nueva)):
        a, b = vieja.get(k), nueva.get(k)
        if not _igual(a, b):
            if any(isinstance(x, list) and len(x) > 4 for x in (a, b)):
                a, b = f"{len(a or [])} valores", f"{len(b or [])} valores (difieren)"
            out.append(f"{k}: {a} -> {b}")
    return out


def cargar_referencia() -> dict:
    return json.loads(ARCHIVO_REFERENCIA.read_text(encoding="utf-8"))


def guardar_referencia(d: dict) -> None:
    ARCHIVO_REFERENCIA.write_text(json.dumps(d, indent=1, ensure_ascii=False),
                                  encoding="utf-8")
