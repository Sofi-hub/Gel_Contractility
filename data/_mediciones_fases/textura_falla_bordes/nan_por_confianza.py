"""B (2026-10-27). Textura con los fotogramas de confianza baja marcados como
"sin medida". Solo medición: no toca el análisis ni escribe en processed_data.

De la medición del 2026-10-26 (`LEEME.md`): en 466 la textura parte un evento en
dos porque en el fotograma más rápido la correlación de fase se desploma (0.285
contra 0.984 de mediana del video) — motion blur. La propuesta era marcar esos
fotogramas como **sin medida** (NaN), que el pipeline ya sabe manejar
(`tests/test_nan.py`), en vez de creerles una posición inventada.

Regla que se prueba: `respuesta_correlacion < u * mediana del video` -> NaN,
con u = 0.3, 0.5 (la propuesta) y 0.7. Se compara contra no marcar nada.

Qué se corre:
  - los 11 videos de referencia, medidos por TEXTURA (la serie se cachea en
    `series/`, igual que en `comparar_textura.py`: medir el video entero tarda
    minutos). No se tocan sus resultados por bordes, que son los vigentes.
  - los 9 videos de Andrés, que YA están medidos por textura en
    `data/processed_data`: su `serie_temporal_*.xlsx` trae la columna
    `respuesta_correlacion` por fotograma, así que no hace falta volver a leer
    los 4K (son las series guardadas, no los videos).

Para cada uno: fotogramas marcados, eventos, si el conteo es reportable y la
amplitud, antes y después.

    python data/_mediciones_fases/textura_falla_bordes/nan_por_confianza.py
"""
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "scripts"))
sys.path.insert(0, str(RAIZ / "tests"))
import contraction_report as cr                    # noqa: E402
from src import textura as tx                      # noqa: E402
from referencia import VIDEOS, CRUDOS, PROCESADOS  # noqa: E402

AQUI = Path(__file__).resolve().parent
SERIES = AQUI / "series"
UMBRALES = [None, 0.3, 0.5, 0.7]
ANDRES = ["10V_1", "10V_2", "10V_3", "20V_1", "20V_2", "20V_3", "40V_1", "40V_2", "40V_3"]
CORTO = {"Video_prueba": "prueba", "Video_063_CTRL1_5V": "063",
         "Video_268_EXP3_FAPS2_40V": "268", "Video_466_EXP5_FAPS4_40V": "466",
         "Video_583_EXP6_CTRL4_40V": "583", "Video_491_EXP5_CTRL1_36HZ": "491",
         "Video_476": "476", "Video_613": "613", "Video_068_hw30": "068",
         "Video_304": "304", "Video_341": "341"}


# --------------------------------------------------------------- las series
def serie_bordes(carpeta):
    s = next((PROCESADOS / carpeta).glob("serie_temporal_*.xlsx"))
    return pd.read_excel(s, sheet_name="diagnostics")


def serie_textura(carpeta, nombre):
    """center_px y respuesta por fotograma, medidos por textura. Se cachea."""
    SERIES.mkdir(exist_ok=True)
    cache = SERIES / f"{nombre}_textura.csv"
    if cache.is_file():
        return pd.read_csv(cache)
    m = tx.medir(str(CRUDOS / VIDEOS[carpeta][0]), rotacion=0)
    d = pd.DataFrame({"dy_px": m["dy"], "respuesta": m["respuesta"]})
    d["center_px"] = m["centro_ref"] + m["dy"]
    d["grosor_px"] = m["grosor_px"]
    d.to_csv(cache, index=False)
    print(f"  {nombre}: textura medida ({len(d)} fotogramas) -> {cache.name}", flush=True)
    return d


def df_referencia(carpeta, nombre):
    """Serie con pinta de main.py pero con center_px de textura, y la respuesta."""
    bor = serie_bordes(carpeta)
    tex = serie_textura(carpeta, nombre)
    n = min(len(bor), len(tex))
    d = bor.iloc[:n].copy()
    d["center_px"] = tex["center_px"].to_numpy()[:n]
    d["thickness_px"] = float(tex["grosor_px"].iloc[0])
    d["y_top_px"] = d["center_px"] - d["thickness_px"] / 2
    d["y_bottom_px"] = d["center_px"] + d["thickness_px"] / 2
    return d, tex["respuesta"].to_numpy(float)[:n]


def df_andres(carpeta):
    """Los de Andrés ya están medidos por textura: la serie guardada alcanza."""
    d = serie_bordes(carpeta)
    return d, d["respuesta_correlacion"].to_numpy(float)


# ------------------------------------------------------------------ medida
def _f(a, k):
    v = a.get(k)
    try:
        v = float(v)
    except (TypeError, ValueError):
        return None
    return None if not np.isfinite(v) else v


def correr(d, respuesta, umbral, frecuencia):
    """Marca como sin medida los fotogramas de confianza baja y corre el reporte."""
    d = d.copy()
    med = float(np.nanmedian(respuesta))
    if umbral is None:
        marcados = 0
    else:
        malos = respuesta < umbral * med
        marcados = int(np.sum(malos))
        d.loc[malos, ["center_px", "y_top_px", "y_bottom_px"]] = np.nan
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        a = cr.analizar(d, "center_px", None, None, None, 1.5,
                        frecuencia_estimulo=frecuencia)
    amp, pct = _f(a, "amplitud_traslacion_px"), _f(a, "amplitud_relativa_pct")
    return {"umbral": "sin marcar" if umbral is None else f"{umbral:g} x mediana",
            "respuesta_mediana": round(med, 3),
            "respuesta_minima": round(float(np.nanmin(respuesta)), 3),
            "fotogramas": len(d), "fotogramas_marcados": marcados,
            "marcados_pct": round(100 * marcados / len(d), 3),
            "n_eventos": int(a["n_eventos"]),
            "reportable": bool(a["conteo_reportable"]),
            "k_usado": float(a["k_usado"]),
            "amplitud_px": None if amp is None else round(amp, 3),
            "amplitud_pct": None if pct is None else round(pct, 4),
            "motivo": a.get("motivo_no_reportable")}


def linea(nombre, grupo):
    base = grupo[0]
    return (f"  {nombre:7s} respuesta mediana {base['respuesta_mediana']:.3f}, "
            f"minima {base['respuesta_minima']:.3f} | "
            + " | ".join(f"{x['umbral']}: {x['fotogramas_marcados']} marc, "
                         f"{x['n_eventos']} ev{'' if x['reportable'] else ' (NO rep)'}"
                         for x in grupo))


def main():
    filas = []
    print("=== 11 de referencia, medidos por TEXTURA ===", flush=True)
    for carpeta, (_, _, frec) in VIDEOS.items():
        nombre = CORTO[carpeta]
        try:
            d, resp = df_referencia(carpeta, nombre)
        except Exception as e:                       # noqa: BLE001
            print(f"  {nombre}: no se pudo ({type(e).__name__}: {e})", flush=True)
            continue
        g = []
        for u in UMBRALES:
            f = {"video": nombre, "grupo": "referencia (textura)"}
            f.update(correr(d, resp, u, frec))
            g.append(f)
        filas += g
        print(linea(nombre, g), flush=True)

    print("\n=== 9 de Andres, series de textura ya guardadas ===", flush=True)
    for carpeta in ANDRES:
        if not (PROCESADOS / carpeta).is_dir():
            print(f"  {carpeta}: no esta"); continue
        d, resp = df_andres(carpeta)
        g = []
        for u in UMBRALES:
            f = {"video": carpeta, "grupo": "Andres (textura)"}
            f.update(correr(d, resp, u, [0.1]))
            g.append(f)
        filas += g
        print(linea(carpeta, g), flush=True)

    d = pd.DataFrame(filas)
    d.to_csv(AQUI / "nan_por_confianza.csv", index=False)
    print(f"\ntabla: nan_por_confianza.csv ({len(d)} filas)")


if __name__ == "__main__":
    main()
