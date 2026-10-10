"""
informe.py
----------
Un informe de UNA página por video, para mandar al equipo sin abrir los Excel.

    python scripts/informe.py --carpeta data/processed_data/<video>

No calcula nada: lee lo que ya guardaron los pasos 1-3 en la carpeta
(serie_temporal_*.xlsx, contracciones_*.xlsx, movimiento_*.xlsx si está, las
figuras y consola_<video>.txt si está) y arma informe_<carpeta>.html.
Es un solo archivo, con las figuras adentro: se puede mandar por mail tal cual
y se abre con doble clic en cualquier navegador (también se imprime a PDF
desde el navegador).

Sirve también para resultados viejos: no hace falta volver a correr nada.
"""
from __future__ import annotations

import argparse
import base64
import datetime as _dt
import html
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "scripts"))
import procesar_carpeta as pc                  # noqa: E402
from src.output_paths import buscar_serie      # noqa: E402

FIGURAS = [  # (prefijo, título, explicación)
    ("09_contracciones", "Contracciones detectadas",
     "Posición de la franja del gel en el tiempo (sin deriva). Cada marca es una contracción."),
    ("10_ritmo", "Ritmo: estimuladas y espontáneas",
     "Qué contracciones siguen al estimulador (enganche de fase) y cuáles no."),
    ("11_cinetica", "Forma de la contracción",
     "Contracciones alineadas y promediadas: subida (TTP) y relajación (RT50)."),
    ("00_roi_profile", "Zona del gel analizada",
     "La zona elegida automáticamente: la parte más plana y angosta del gel, lejos de los anclajes."),
    ("05_estabilidad_umbral", "Control del umbral",
     "El conteo tiene que mantenerse igual en un rango amplio de umbrales, sin falsos de control."),
    ("07_movimiento", "Confirmación por un segundo método",
     "Movimiento medido por intensidad, sin usar los bordes."),
]


def _num(x):
    try:
        v = float(x)
        return None if v != v else v
    except (TypeError, ValueError):
        return None


def _f(x, fmt=".2f", vacio="—"):
    v = _num(x)
    return vacio if v is None else format(v, fmt)


def _rango(txt: str, fmt: str = ".2f") -> str:
    try:
        a, b = (float(v) for v in str(txt).split("-"))
        return f"{a:{fmt}}–{b:{fmt}}"
    except ValueError:
        return html.escape(str(txt))


def _img(p: Path) -> str:
    return "data:image/png;base64," + base64.b64encode(p.read_bytes()).decode()


def leer(carpeta: Path) -> dict:
    """Todo lo que el informe necesita, leído de la carpeta. No recalcula nada."""
    d: dict = {"carpeta": carpeta, "fila": pc.leer_fila(carpeta), "serie": {}, "res": {}}
    serie = buscar_serie(carpeta)
    if serie.is_file():
        r = pd.read_excel(serie, sheet_name="resumen")
        d["serie"] = dict(zip(r["Métrica"].astype(str), r["Valor"]))
    contr = sorted(carpeta.glob("contracciones_*.xlsx"))
    if contr:
        h = pd.read_excel(contr[0], sheet_name=None)
        res = pc._hoja(h, "resumen")
        if res is not None and len(res):
            d["res"] = res.iloc[0].to_dict()
        d["eventos"] = pc._hoja(h, "eventos")
    mov = sorted(carpeta.glob("movimiento_*.xlsx"))
    if mov:
        try:
            d["veredicto"] = pd.read_excel(mov[0], sheet_name="veredicto").iloc[0].to_dict()
        except Exception:
            pass
    # la consola guardada (procesar_carpeta) solo si es de esta corrida: no mas vieja
    # que el reporte; si no, los avisos se arman con los Excel
    cons = sorted(carpeta.glob("consola_*.txt"))
    ref_t = max((p.stat().st_mtime for p in contr), default=0) if contr else 0
    d["avisos_consola"] = (pc.avisos_de(cons[0].read_text(encoding="utf-8"))
                           if cons and cons[0].stat().st_mtime >= ref_t - 1 else None)
    return d


def frase_resultado(d: dict) -> tuple[str, str]:
    """(clase, frase) en palabras simples."""
    f, res = d["fila"], d["res"]
    if not res:
        return "gris", "Todavía no se buscaron contracciones (falta el paso 2)."
    n = f.get("eventos") or 0
    if not f.get("reportable"):
        mot = f.get("motivo_no_reportable") or "no hay meseta en el escaneo del umbral"
        return "mal", (f"<b>El conteo NO es reportable</b> ({html.escape(mot)}). Hay {n} "
                       f"candidatos, pero no se distinguen del ruido con seguridad: no informar "
                       f"números de este video. Las figuras quedan para revisar qué pasó.")
    if n == 0:
        return "gris", "No se detectaron contracciones."
    amp = (f"{_f(f.get('amplitud_pct'))} % del grosor en reposo "
           f"({_f(f.get('amplitud_px'))} px)")
    if f.get("tren") == "si":
        fr = _num(f.get("frecuencia_Hz"))
        return "bien", (f"<b>{n} contracciones</b>; <b>{f.get('n_estimulados')}</b> siguen al "
                        f"estimulador a {_f(fr, '.3g')} Hz (período {_f(f.get('periodo_s'), '.4f')} ± "
                        f"{_f(f.get('periodo_err_s'), '.4f')} s, captura {_f(f.get('captura_pct'), '.0f')} %). "
                        f"Amplitud de las estimuladas: <b>{amp}</b>.")
    return "bien", (f"<b>{n} contracciones</b>, sin un tren de estímulo detectable "
                    f"(se tratan como espontáneas). Amplitud mediana: <b>{amp}</b>.")


def cinetica_txt(res: dict, m: str) -> str:
    if not res or not _num(res.get(f"{m}_n_eventos")):
        return "—"
    if not res.get("conteo_reportable"):
        return "no se informa (conteo no reportable)"
    if bool(res.get(f"{m}_reportable")):
        ic = res.get(f"{m}_ic95_s")
        ic_t = ""
        if isinstance(ic, str) and "-" in ic:
            a, b = (float(v) for v in ic.split("-"))
            ic_t = f" (IC 95 %: {1000 * a:.0f}–{1000 * b:.0f} ms)"
        return f"{1000 * float(res[f'{m}_s']):.0f} ms{ic_t}"
    return (f"menos de {1000 * float(res[f'{m}_cota_sup_s']):.0f} ms "
            f"(más rápida que la cámara: a 30 fps no se puede dar un valor)")


def avisos(d: dict) -> list[str]:
    if d.get("avisos_consola") is not None:
        out = [a for a in d["avisos_consola"] if "NO REPORTABLE" not in a.upper()]
        if out:
            return out
    s, res, out = d["serie"], d["res"], []
    if _num(s.get("ROI cumple criterio")) == 0:
        out.append("La zona analizada no cumple el criterio de planitud (el grosor varía más del 6 %).")
    if (_num(s.get("frames faltantes (%)")) or 0) >= 1:
        out.append(f"La cámara perdió ~{_f(s.get('frames faltantes (%)'), '.1f')} % de los "
                   f"fotogramas (el eje de tiempo lo tiene en cuenta).")
    if "fallo" in str(s.get("half_window eleccion", "")):
        out.append(f"El gel se movía mucho: la búsqueda del borde se agrandó sola a "
                   f"±{_f(s.get('half_window'), '.0f')} px.")
    if (_num(s.get("timestamps identicos (%)")) or 0) >= 99:
        out.append("Los intervalos entre fotogramas son todos iguales: el archivo probablemente "
                   "no trae los tiempos reales de la cámara (no se pueden detectar fotogramas perdidos).")
    cr = _num(s.get("cintura: columnas seguidas (px)"))
    if cr is not None and cr < (_num(s.get("ROI ancho minimo exigido (px)")) or 120):
        out.append(f"La parte más angosta del gel abarca solo {cr:.0f} px: la zona analizada no "
                   f"puede ser plana y ancha a la vez.")
    ni = _num(s.get("nitidez del borde en la zona (mediana)"))
    if ni is not None and ni < 12:
        out.append("Los bordes del gel tienen poco contraste: la medida es más ruidosa "
                   "(revisar enfoque e iluminación).")
    if res and res.get("conteo_estable_ventana") is False:
        out.append("El conteo cambia según la ventana usada para quitar la deriva.")
    if res and (_num(res.get("eventos_junto_al_borde")) or 0) > 0:
        out.append(f"{int(res['eventos_junto_al_borde'])} contracción(es) muy cerca del inicio o "
                   f"del final del video: su amplitud es menos segura.")
    if res and (_num(res.get("eventos_junto_a_hueco")) or 0) > 0:
        out.append(f"{int(res['eventos_junto_a_hueco'])} contracción(es) junto a un fotograma sin medida.")
    return out


CSS = """
:root{--fg:#1b1f24;--bg:#fff;--mut:#5b6470;--lin:#d8dde3;--bien:#e8f5ec;--bienb:#2e7d4f;
--mal:#fdecea;--malb:#b03a2e;--gris:#f1f3f5;--grisb:#6c757d}
@media (prefers-color-scheme:dark){:root{--fg:#e6e9ee;--bg:#15181c;--mut:#9aa4b0;--lin:#2c3238;
--bien:#173324;--bienb:#5cc48a;--mal:#3a1d1a;--malb:#ef8a7f;--gris:#22272c;--grisb:#a0a8b0}}
body{font-family:system-ui,Segoe UI,Arial,sans-serif;color:var(--fg);background:var(--bg);
max-width:980px;margin:0 auto;padding:24px 16px;line-height:1.45}
h1{font-size:1.5rem;margin:0 0 4px}h2{font-size:1.1rem;margin:28px 0 8px}
.mut{color:var(--mut);font-size:.9rem}
.res{border-left:5px solid;padding:12px 16px;border-radius:6px;margin:16px 0}
.bien{background:var(--bien);border-color:var(--bienb)}.mal{background:var(--mal);border-color:var(--malb)}
.gris{background:var(--gris);border-color:var(--grisb)}
table{border-collapse:collapse;width:100%}td{padding:6px 8px;border-bottom:1px solid var(--lin);vertical-align:top}
td:first-child{color:var(--mut);width:38%}
figure{margin:18px 0}figure img{max-width:100%;border:1px solid var(--lin);border-radius:4px;background:#fff}
figcaption{font-size:.9rem;color:var(--mut)}ul{padding-left:20px}
@media print{body{max-width:none}figure{break-inside:avoid}}
"""


def armar_html(d: dict) -> str:
    carpeta: Path = d["carpeta"]
    nombre = carpeta.name
    f, s, res = d["fila"], d["serie"], d["res"]
    clase, frase = frase_resultado(d)
    video = re.split(r"[\\/]", str(s.get("video", nombre)))[-1]
    filas = [
        ("Video", html.escape(video)),
        ("Duración", f"{_f(s.get('duracion segun PTS (s)') or res.get('duracion_s'), '.1f')} s, "
                     f"{_f(s.get('frames totales') or res.get('n_frames'), '.0f')} fotogramas a "
                     f"{_f(s.get('fps segun PTS') or res.get('fps'), '.0f')} fps"),
        ("Contracciones", f"{f.get('eventos', '—')}"
                          + ("" if f.get("reportable") is None else
                             (" (conteo reportable)" if f.get("reportable") else " (NO reportable)"))),
    ]
    if f.get("tren") == "si":
        filas.append(("Tren de estímulo", f"{f.get('n_estimulados')} estimuladas; período "
                      f"{_f(f.get('periodo_s'), '.4f')} ± {_f(f.get('periodo_err_s'), '.4f')} s "
                      f"({_f(f.get('frecuencia_Hz'), '.4g')} Hz); captura {_f(f.get('captura_pct'), '.0f')} %"))
    elif res:
        filas.append(("Tren de estímulo", "no se encontró"))
    if f.get("reportable") and _num(f.get("amplitud_pct")) is not None:
        ic = res.get("amplitud_relativa_ic95_pct")
        filas.append((f"Amplitud ({f.get('amplitud_grupo') or 'todas'})",
                      f"<b>{_f(f.get('amplitud_pct'))} %</b> del grosor en reposo = "
                      f"{_f(f.get('amplitud_px'))} px"
                      + (f"<br><span class='mut'>IC 95 % de la mediana: {_rango(ic)} %</span>"
                         if isinstance(ic, str) else "")))
        filas.append(("Tiempo al pico (TTP)", cinetica_txt(res, "ttp")))
        filas.append(("Relajación al 50 % (RT50)", cinetica_txt(res, "rt50")))
    v = d.get("veredicto")
    if v:
        tam = _num(v.get("tamano_por_contraccion_mediana")) or _num(v.get("pendiente_desp_vert_sobre_center_px"))
        filas.append(("Confirmación (2.º método)",
                      html.escape(str(v.get("veredicto", "")))
                      + (f"<br><span class='mut'>tamaño {abs(tam):.2f} veces; correlación "
                         f"{abs(_num(v.get('correlacion')) or 0):.2f}</span>" if tam else "")))
    filas.append(("Zona analizada", f"columnas {_f(s.get('ROI x_start'), '.0f')}–{_f(s.get('ROI x_end'), '.0f')}"
                  f"; grosor en reposo ~{_f(s.get('grosor medio (px)'), '.0f')} px"
                  + ("" if _num(s.get("ROI cumple criterio")) != 0 else " (<b>no cumple el criterio</b>)")))

    av = avisos(d)
    figs = []
    for pref, tit, exp in FIGURAS:
        p = sorted(carpeta.glob(f"{pref}_*.png"))
        if p:
            figs.append(f"<figure><h2>{tit}</h2><img src='{_img(p[0])}' alt='{tit}'>"
                        f"<figcaption>{exp}</figcaption></figure>")
    commit = s.get("commit")
    pie = (f"Generado el {_dt.datetime.now():%Y-%m-%d %H:%M} a partir de los archivos de "
           f"<code>{html.escape(str(carpeta))}</code>. Este informe no calcula nada: resume lo que "
           f"guardaron los pasos del análisis" + (f" (versión {html.escape(str(commit))})" if commit else "")
           + ". Todas las medidas en píxeles; la amplitud en % del grosor permite comparar videos.")
    return f"""<!doctype html><html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Informe {html.escape(nombre)}</title><style>{CSS}</style></head><body>
<h1>Informe: {html.escape(nombre)}</h1>
<div class="mut">Contractilidad del gel medida por la posición de sus bordes</div>
<div class="res {clase}">{frase}</div>
<h2>Números</h2><table>{''.join(f'<tr><td>{a}</td><td>{b}</td></tr>' for a, b in filas)}</table>
<h2>Avisos</h2>{'<ul>' + ''.join(f'<li>{html.escape(a)}</li>' for a in av) + '</ul>' if av else '<p class="mut">Ninguno.</p>'}
{''.join(figs)}
<p class="mut" style="margin-top:32px">{pie}</p>
</body></html>"""


def generar(carpeta: Path) -> Path:
    carpeta = Path(carpeta)
    out = carpeta / f"informe_{carpeta.name}.html"
    out.write_text(armar_html(leer(carpeta)), encoding="utf-8")
    return out


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--carpeta", required=True, help="Carpeta de resultados de un video")
    a = p.parse_args()
    c = Path(a.carpeta)
    if not c.is_dir():
        sys.exit(f"No existe la carpeta: {c}")
    if not buscar_serie(c).is_file():
        sys.exit(f"En {c} no hay serie_temporal: correr primero el paso 1.")
    print(f"Informe: {generar(c)}")


if __name__ == "__main__":
    main()
