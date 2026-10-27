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
from src.excel import read_excel as leer_excel  # noqa: E402
from src.output_paths import buscar_serie      # noqa: E402

EXTENSIONES = {".mp4", ".avi", ".mov"}

# columnas de la tabla, en orden (las explica docs/guia-salida-consola.md)
COLUMNAS = ["video", "estado", "eventos", "reportable", "motivo_no_reportable",
            "tren", "periodo_s", "periodo_err_s", "frecuencia_Hz", "n_estimulados",
            "captura_pct", "amplitud_pct", "amplitud_px", "amplitud_grupo",
            "forzada_p", "forzada_pulsos", "forzada_amplitud_pct", "forzada_amplitud_px",
            "forzada_ttp_ms", "forzada_rt50_ms",
            "roi_cumple", "half_window", "n_avisos", "avisos", "informe", "carpeta"]


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
            r = leer_excel(serie, sheet_name="resumen")
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
    hojas = leer_excel(contr[0], sheet_name=None)
    res = _hoja(hojas, "resumen")
    if res is None or res.empty:
        return fila
    r = res.iloc[0].to_dict()
    fila["eventos"] = int(r["n_eventos"]) if _num(r.get("n_eventos")) is not None else None
    fila["reportable"] = bool(r.get("conteo_reportable"))
    mot = r.get("motivo_no_reportable")
    fila["motivo_no_reportable"] = "" if mot is None or mot != mot else str(mot)
    # amplitud: SOLO si el conteo es reportable. Con el conteo NO reportable sale de
    # candidatos que no se distinguen del ruido, asi que no se informa; ahi el numero a
    # mirar es la respuesta forzada (columnas forzada_*, que siguen igual).
    if fila["reportable"]:
        fila["amplitud_pct"] = _num(r.get("amplitud_relativa_pct"))
        fila["amplitud_px"] = _num(r.get("amplitud_px"))
        if fila["amplitud_px"] is None:   # resultados anteriores a H40
            fila["amplitud_px"] = _num(r.get("amplitud_traslacion_px"))
        g = r.get("cinetica_grupo_principal")
        fila["amplitud_grupo"] = "" if g is None or g != g else str(g)
    else:
        fila["amplitud_pct"] = fila["amplitud_px"] = fila["amplitud_grupo"] = None
    # respuesta forzada (2026-10-19): solo si el reporte la calculo (conteo NO reportable)
    if _num(r.get("forzada_p")) is not None:
        fila["forzada_p"] = _num(r.get("forzada_p"))
        n, tot = _num(r.get("forzada_n_responden")), _num(r.get("forzada_n_pulsos"))
        fila["forzada_pulsos"] = f"{n:.0f}/{tot:.0f}" if n is not None and tot is not None else ""
        hay = str(r.get("forzada_hay_respuesta")).strip().lower() in ("true", "1", "1.0")
        fila["forzada_amplitud_pct"] = _num(r.get("forzada_amplitud_pct")) if hay else None
        fila["forzada_amplitud_px"] = _num(r.get("forzada_amplitud_px")) if hay else None
        # cinetica de la respuesta al estimulo (2026-10-27): solo el valor
        # medible; si es una cota queda vacio (la cota esta en el informe)
        for _m in ("ttp", "rt50"):
            _ok = str(r.get(f"forzada_{_m}_reportable")).strip().lower() in ("true", "1", "1.0")
            fila[f"forzada_{_m}_ms"] = _num(r.get(f"forzada_{_m}_ms")) if hay and _ok else None

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
             verbose: bool = False, escribir=print, detener=lambda: False,
             metodo: str = "bordes") -> list[dict]:
    filas = []
    for i, video in enumerate(videos, 1):
        if detener():
            break
        carpeta = salida / interfaz.nombre_resultado(video)
        escribir(f"\n=================== [{i}/{len(videos)}] {video.name} ===================\n")
        fila = {"video": interfaz.nombre_resultado(video) + video.suffix, "carpeta": str(carpeta)}
        log: list[str] = []

        def esc(linea, _log=log):
            _log.append(linea)
            escribir(linea)
        try:
            # el informe (paso 4) se arma DESPUES de guardar la consola: asi incluye los avisos
            cmds = (interfaz.armar_comandos(str(video), str(carpeta), 1 in pasos, 2 in pasos,
                                            3 in pasos, frecuencias, verbose, metodo=metodo)
                    if pasos & {1, 2, 3} else [])
            ok = interfaz.correr(cmds, esc, detener) if cmds else True
            fila["estado"] = "OK" if ok else "ERROR"
        except ValueError as e:
            esc(f"\n*** {e} ***\n")
            fila["estado"] = "ERROR: " + str(e).splitlines()[0]
        texto = "".join(log)
        if carpeta.is_dir():
            cons = carpeta / f"consola_{interfaz.nombre_resultado(video)}.txt"
            if pasos & {1, 2, 3}:          # solo el informe: no pisar la consola guardada
                cons.write_text(texto, encoding="utf-8")
            elif cons.is_file():
                texto = cons.read_text(encoding="utf-8")
            fila.update(leer_fila(carpeta))
            if 4 in pasos and fila["estado"] == "OK" and buscar_serie(carpeta).is_file():
                import informe
                fila["informe"] = str(informe.generar(carpeta))
                escribir(f"Informe: {fila['informe']}\n")
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


def _txt_forzada(r: dict) -> str:
    if r.get("forzada_p") is None:
        return ""
    if r.get("forzada_amplitud_px") is None:
        return "no"
    return f"{r['forzada_amplitud_px']:.2f} px {r.get('forzada_pulsos', '')}"


def _vacio() -> str:
    """Celda sin numero. Guion largo, o guion normal si la consola no lo puede imprimir
    (una consola vieja de Windows no tiene el guion largo y el print falla)."""
    try:
        "—".encode(sys.stdout.encoding or "ascii")
    except (UnicodeEncodeError, LookupError, AttributeError):
        return "-"
    return "—"


def tabla_texto(filas: list[dict]) -> str:
    def f(x, fmt):
        return "" if x is None or x != x else format(x, fmt)
    vacio = _vacio()
    lin = [f"{'video':34s} {'estado':6s} {'ev':>3s} {'report.':7s} {'periodo (s)':>12s} "
           f"{'ampl %':>6s} {'ampl px':>7s} {'forzada':>16s} avisos"]
    for r in filas:
        rep = "" if r.get("reportable") is None else ("si" if r["reportable"] else "NO")
        per = (f(r.get("periodo_s"), ".4f") if r.get("tren") == "si"
               else "sin tren" if r.get("tren") == "no" else "")
        # conteo NO reportable: la amplitud no se informa (leer_fila la deja vacia)
        no_rep = r.get("reportable") is False
        a_pct = vacio if no_rep else f(r.get("amplitud_pct"), ".2f")
        a_px = vacio if no_rep else f(r.get("amplitud_px"), ".2f")
        lin.append(f"{r['video'][:34]:34s} {str(r.get('estado',''))[:6]:6s} "
                   f"{f(r.get('eventos'), 'd'):>3s} {rep:7s} {per:>12s} "
                   f"{a_pct:>6s} {a_px:>7s} "
                   f"{_txt_forzada(r):>16s} {r.get('n_avisos', 0)}")
    lin.append("(ampl % y px: MEDIANA de las contracciones del grupo informado)")
    if any(r.get("reportable") is False for r in filas):
        lin.append("(ampl vacia = conteo NO reportable: esos numeros saldrian de candidatos que "
                   "no se distinguen del ruido, asi que no se informan; mirar la columna forzada)")
    if any(r.get("forzada_p") is not None for r in filas):
        lin.append("(forzada: respuesta al reloj del estimulador cuando el conteo es NO reportable; "
                   "px de la mediana de los pulsos y pulsos que responden. 'no' = sin respuesta. No es un conteo)")
    return "\n".join(lin)


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--carpeta", required=True, help="Carpeta con los videos (.mp4/.avi/.mov)")
    cfg = interfaz.CONFIG   # configuracion.ini: los mismos valores con que arranca la ventana
    p.add_argument("--salida", default=str(cfg["carpeta_resultados"]),
                   help="Donde crear una carpeta por video y la tabla (default: data/processed_data)")
    p.add_argument("--pasos", default=" ".join(str(n) for n in sorted(cfg["pasos"])),
                   help="Que pasos correr: '1 2 4' (default: medir, contracciones e informe), "
                        "'1 2 3 4', o '2 4' sobre series ya hechas")
    p.add_argument("--frecuencia-estimulo", default=cfg["frecuencia"],
                   help="Igual que en contraction_report (vacio = no se sabe)")
    p.add_argument("--metodo", default="bordes", choices=["bordes", "textura"],
                   help="Como se mide el paso 1 (main.py --metodo). 'textura' = sin bordes, "
                        "para bordes poco nitidos (videos de Andres)")
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
                     escribir=lambda s: print(s, end="" if s.endswith("\n") else "\n", flush=True),
                     metodo=a.metodo)
    xlsx = guardar_tabla(filas, Path(a.salida))
    print("\n=================== RESUMEN DE LA CARPETA ===================")
    print(tabla_texto(filas))
    print(f"\nTabla: {xlsx}")
    print("Avisos completos y salida de cada paso: consola_<video>.txt en cada carpeta.")
    sys.exit(0 if all(r.get("estado") == "OK" for r in filas) else 1)


if __name__ == "__main__":
    main()
