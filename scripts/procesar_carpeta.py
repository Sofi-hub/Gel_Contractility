"""
procesar_carpeta.py
-------------------
Procesa TODOS los videos de una carpeta, uno detras del otro, y arma una tabla
resumen (una fila por video).

    python scripts/procesar_carpeta.py --carpeta "<carpeta con videos>"
    python scripts/procesar_carpeta.py --carpeta "<...>" --frecuencia-estimulo 0.1
    python scripts/procesar_carpeta.py --carpeta "<...>" --pasos 2      (solo el reporte,
                                                                         sobre series ya hechas)

No calcula nada propio: para cada video corre los MISMOS comandos que la ventana
(interfaz.armar_comandos / interfaz.correr: main.py, contraction_report.py y, si
se pide, motion_check.py) y despues LEE los Excel que esos comandos guardaron.
Los numeros son identicos a correr cada video a mano.

Salida:
  <salida>/<video>/...                    lo de siempre, una carpeta por video
  <salida>/<video>/consola_<video>.txt    lo que imprimio cada paso (para revisar)
  <salida>/resumen_carpeta_<fecha>.xlsx   la tabla (y .csv al lado)

Si un video falla, se anota en la tabla y se sigue con el siguiente.
"""
from __future__ import annotations

import argparse
import ast
import datetime as _dt
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
import interfaz                                # noqa: E402  (no abre ventana)
from src.output_paths import buscar_serie      # noqa: E402

EXTENSIONES = {".mp4", ".avi", ".mov"}

# columnas de la tabla, en orden (las explica docs/guia-salida-consola.md)
COLUMNAS = ["video", "estado", "eventos", "reportable", "motivo_no_reportable",
            "tren", "periodo_s", "periodo_err_s", "frecuencia_Hz", "n_estimulados",
            "captura_pct", "amplitud_pct", "amplitud_px", "amplitud_grupo",
            "roi_cumple", "half_window", "n_avisos", "avisos", "carpeta"]


def listar_videos(carpeta: Path, recursivo: bool = False) -> list[Path]:
    it = carpeta.rglob("*") if recursivo else carpeta.iterdir()
    return sorted(p for p in it if p.is_file() and p.suffix.lower() in EXTENSIONES)


def _hoja(hojas: dict, prefijo: str):
    """Las hojas se llaman <prefijo>_<video> (cortado a 31 letras)."""
    for k, v in hojas.items():
        if k.startswith(prefijo + "_") or k == prefijo:
            return v
    return None


def _num(x):
    try:
        return None if x is None or x != x else float(x)
    except (TypeError, ValueError):
        return None


def leer_fila(carpeta: Path) -> dict:
    """Saca los numeros de los Excel ya guardados en la carpeta de un video.
    No recalcula nada: si algo no esta, queda vacio."""
    import pandas as pd
    fila: dict = {}

    serie = buscar_serie(carpeta)
    if serie.is_file():
        try:
            r = pd.read_excel(serie, sheet_name="resumen")
            m = dict(zip(r["Métrica"].astype(str), r["Valor"]))
            if "ROI cumple criterio" in m:
                fila["roi_cumple"] = bool(_num(m["ROI cumple criterio"]))
            if "half_window" in m:
                fila["half_window"] = m["half_window"]
        except Exception:
            pass

    contr = sorted(carpeta.glob("contracciones_*.xlsx"))
    if not contr:
        return fila
    hojas = pd.read_excel(contr[0], sheet_name=None)
    res = _hoja(hojas, "resumen")
    if res is None or res.empty:
        return fila
    r = res.iloc[0].to_dict()
    fila["eventos"] = int(r["n_eventos"]) if _num(r.get("n_eventos")) is not None else None
    fila["reportable"] = bool(r.get("conteo_reportable"))
    mot = r.get("motivo_no_reportable")
    fila["motivo_no_reportable"] = "" if mot is None or mot != mot else str(mot)
    fila["amplitud_pct"] = _num(r.get("amplitud_relativa_pct"))
    fila["amplitud_px"] = _num(r.get("amplitud_px"))
    if fila["amplitud_px"] is None:   # resultados anteriores a H40
        fila["amplitud_px"] = _num(r.get("amplitud_traslacion_px"))
    g = r.get("cinetica_grupo_principal")
    fila["amplitud_grupo"] = "" if g is None or g != g else str(g)

    # tren: la hoja `trenes` (fila del tren clasificado como estimulado)
    tr = _hoja(hojas, "trenes")
    fila["tren"] = "no"
    if tr is not None and not tr.empty and "clasificacion" in tr:
        est = tr[tr["clasificacion"].astype(str) == "estimulados"]
        if not est.empty:
            t = est.iloc[0]
            fila.update(tren="si", periodo_s=_num(t.get("periodo_s")),
                        periodo_err_s=_num(t.get("periodo_err_s")),
                        frecuencia_Hz=_num(t.get("frecuencia_Hz")),
                        n_estimulados=int(t["n_eventos_tren"]),
                        captura_pct=_num(t.get("captura_pct")))
    return fila


def avisos_de(texto: str) -> list[str]:
    """Las lineas AVISO / NO REPORTABLE que imprimieron los pasos."""
    out = []
    for ln in texto.splitlines():
        s = ln.strip()
        if s.upper().startswith("AVISO") or "NO REPORTABLE" in s.upper():
            s = re.sub(r"\s+", " ", s)
            if s not in out:
                out.append(s)
    return out


def procesar(videos: list[Path], salida: Path, pasos: set[int], frecuencias: str = "",
             verbose: bool = False, escribir=print, detener=lambda: False) -> list[dict]:
    filas = []
    for i, video in enumerate(videos, 1):
        if detener():
            break
        carpeta = salida / video.stem
        escribir(f"\n=================== [{i}/{len(videos)}] {video.name} ===================\n")
        fila = {"video": video.name, "carpeta": str(carpeta)}
        log: list[str] = []

        def esc(linea, _log=log):
            _log.append(linea)
            escribir(linea)
        try:
            cmds = interfaz.armar_comandos(str(video), str(carpeta), 1 in pasos, 2 in pasos,
                                           3 in pasos, frecuencias, verbose)
            ok = interfaz.correr(cmds, esc, detener)
            fila["estado"] = "OK" if ok else "ERROR"
        except ValueError as e:
            esc(f"\n*** {e} ***\n")
            fila["estado"] = "ERROR: " + str(e).splitlines()[0]
        texto = "".join(log)
        if carpeta.is_dir():
            (carpeta / f"consola_{video.stem}.txt").write_text(texto, encoding="utf-8")
            fila.update(leer_fila(carpeta))
        av = avisos_de(texto)
        fila["n_avisos"] = len(av)
        fila["avisos"] = " | ".join(av)
        filas.append(fila)
    return filas


def guardar_tabla(filas: list[dict], salida: Path) -> Path:
    import pandas as pd
    df = pd.DataFrame(filas)
    df = df.reindex(columns=COLUMNAS + [c for c in df.columns if c not in COLUMNAS])
    sello = _dt.datetime.now().strftime("%Y%m%d_%H%M")
    salida.mkdir(parents=True, exist_ok=True)
    xlsx = salida / f"resumen_carpeta_{sello}.xlsx"
    df.to_excel(xlsx, index=False, sheet_name="resumen_carpeta")
    df.to_csv(xlsx.with_suffix(".csv"), index=False, encoding="utf-8-sig")
    return xlsx


def tabla_texto(filas: list[dict]) -> str:
    def f(x, fmt):
        return "" if x is None or x != x else format(x, fmt)
    lin = [f"{'video':34s} {'estado':6s} {'ev':>3s} {'report.':7s} {'periodo (s)':>12s} "
           f"{'ampl %':>6s} {'ampl px':>7s} avisos"]
    for r in filas:
        rep = "" if r.get("reportable") is None else ("si" if r["reportable"] else "NO")
        per = (f(r.get("periodo_s"), ".4f") if r.get("tren") == "si"
               else "sin tren" if r.get("tren") == "no" else "")
        lin.append(f"{r['video'][:34]:34s} {str(r.get('estado',''))[:6]:6s} "
                   f"{f(r.get('eventos'), 'd'):>3s} {rep:7s} {per:>12s} "
                   f"{f(r.get('amplitud_pct'), '.2f'):>6s} {f(r.get('amplitud_px'), '.2f'):>7s} "
                   f"{r.get('n_avisos', 0)}")
    return "\n".join(lin)


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--carpeta", required=True, help="Carpeta con los videos (.mp4/.avi/.mov)")
    p.add_argument("--salida", default=str(RAIZ / "data" / "processed_data"),
                   help="Donde crear una carpeta por video y la tabla (default: data/processed_data)")
    p.add_argument("--pasos", default="1 2",
                   help="Que pasos correr: '1 2' (default), '1 2 3', o '2' sobre series ya hechas")
    p.add_argument("--frecuencia-estimulo", default="",
                   help="Igual que en contraction_report (vacio = no se sabe)")
    p.add_argument("--recursivo", action="store_true", help="Buscar videos tambien en subcarpetas")
    p.add_argument("--verbose", action="store_true")
    a = p.parse_args()

    carpeta = Path(a.carpeta)
    if not carpeta.is_dir():
        sys.exit(f"No existe la carpeta: {carpeta}")
    pasos = {int(x) for x in a.pasos.replace(",", " ").split()}
    videos = listar_videos(carpeta, a.recursivo)
    if not videos:
        sys.exit(f"No hay videos (.mp4/.avi/.mov) en {carpeta}")
    print(f"{len(videos)} video(s) en {carpeta}")
    filas = procesar(videos, Path(a.salida), pasos, a.frecuencia_estimulo, a.verbose,
                     escribir=lambda s: print(s, end="" if s.endswith("\n") else "\n", flush=True))
    xlsx = guardar_tabla(filas, Path(a.salida))
    print("\n=================== RESUMEN DE LA CARPETA ===================")
    print(tabla_texto(filas))
    print(f"\nTabla: {xlsx}")
    print("Avisos completos y salida de cada paso: consola_<video>.txt en cada carpeta.")
    sys.exit(0 if all(r.get("estado") == "OK" for r in filas) else 1)


if __name__ == "__main__":
    main()
