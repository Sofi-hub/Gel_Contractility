"""
visor.py
--------
La pestaña "Resultados" de la ventana (interfaz.py): ver lo que ya está
guardado en data/processed_data/<carpeta>/, con un gráfico interactivo.

Regla de siempre: la ventana NO calcula números. Todo lo que se muestra como
cifra sale de los Excel (serie_temporal, contracciones, movimiento). Lo único
que se hace acá es DIBUJAR: para la curva se quita la deriva de center_px con la
misma función y la misma ventana que usó el reporte (`win_s_usado`), igual que
la figura 09; los valores de la ficha de cada contracción salen de la hoja
`cinetica` del reporte.

La parte de datos (leer_resultado, ficha_evento, listar_carpetas) no usa tkinter
y se prueba sola (tests/test_visor.py).
"""
from __future__ import annotations

import os
import subprocess
import sys
import threading
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parent
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "scripts"))
from src.excel import read_excel as leer_excel  # noqa: E402
from src.output_paths import buscar_serie          # noqa: E402
from src.estadistica import detrend_median         # noqa: E402

COLOR = {"estimulados": "#d62728", "espontaneos": "#1f77b4", "candidatos": "#7f7f7f"}


# --------------------------------------------------------------------------
# Datos (sin ventana)
# --------------------------------------------------------------------------
@dataclass
class Resultado:
    carpeta: Path
    fila: dict = field(default_factory=dict)        # la de procesar_carpeta.leer_fila
    serie_meta: dict = field(default_factory=dict)  # hoja resumen de serie_temporal
    res: dict = field(default_factory=dict)         # hoja resumen del reporte
    t: np.ndarray | None = None
    senal: np.ndarray | None = None                 # center_px sin deriva, con signo (solo para dibujar)
    grosor: np.ndarray | None = None
    cin: pd.DataFrame | None = None                 # una fila por contraccion (hoja cinetica)
    grilla: pd.DataFrame | None = None
    frase: tuple[str, str] = ("gris", "")
    avisos: list[str] = field(default_factory=list)
    veredicto: dict | None = None


def listar_carpetas(base: Path) -> list[Path]:
    """Carpetas de resultados: las que tienen una serie_temporal."""
    base = Path(base)
    if not base.is_dir():
        return []
    out = [p for p in base.iterdir()
           if p.is_dir() and not p.name.startswith("_") and buscar_serie(p).is_file()]
    return sorted(out, key=lambda p: p.name.lower())


def _hoja(h: dict, pref: str):
    return next((v for k, v in h.items() if k == pref or k.startswith(pref + "_")), None)


_CACHE: dict = {}


def leer_resultado(carpeta: Path, cache: bool = True) -> Resultado:
    """Lee todo lo de una carpeta. Con cache por fecha de los Excel (una sola
    entradas por carpeta; Comparar también la usa)."""
    import informe
    import procesar_carpeta as pc
    carpeta = Path(carpeta)
    archivos = sorted(carpeta.glob("*.xlsx"))
    clave = (str(carpeta), tuple((a.name, a.stat().st_mtime) for a in archivos))
    if cache and clave in _CACHE:
        return _CACHE[clave]
    d = informe.leer(carpeta)                       # lo mismo que usa el informe
    r = Resultado(carpeta=carpeta, fila=d["fila"], serie_meta=d["serie"], res=d["res"],
                  veredicto=d.get("veredicto"))
    r.frase = informe.frase_resultado(d)
    r.avisos = informe.avisos(d)
    serie = buscar_serie(carpeta)
    df = leer_excel(serie, sheet_name="diagnostics")
    r.t = df["time_s"].to_numpy(float)
    c = df["center_px"].to_numpy(float)
    r.grosor = df["thickness_px"].to_numpy(float)
    if r.res:
        fps = float(r.res.get("fps_medido") or r.res.get("fps") or 30.0)
        win = float(r.res.get("win_s_usado") or 2.0)
        signo = float(r.res.get("signo") or 1.0)
        r.senal = signo * detrend_median(c, fps, win)
        contr = sorted(carpeta.glob("contracciones_*.xlsx"))
        h = leer_excel(contr[0], sheet_name=None)
        r.cin = _hoja(h, "cinetica")
        r.grilla = _hoja(h, "grilla")
        ev = _hoja(h, "eventos")
        if r.cin is not None and ev is not None and len(ev) == len(r.cin):
            for col in ("junto_al_borde", "junto_a_hueco", "en_promedio"):
                if col in ev:
                    r.cin[col] = ev[col].to_numpy()
    else:
        r.senal = c - np.nanmedian(c)
    if cache:
        # las ultimas 30 carpetas: volver a una ya vista es instantaneo
        for k in [k for k in _CACHE if k[0] == clave[0]]:
            del _CACHE[k]          # version vieja de la misma carpeta
        while len(_CACHE) >= 30:
            del _CACHE[next(iter(_CACHE))]
        _CACHE[clave] = r
    return r


def leer_resultado_sin_cache(carpeta: Path) -> Resultado:
    return leer_resultado(carpeta, cache=False)


def _ms(x) -> str:
    try:
        v = float(x)
    except (TypeError, ValueError):
        return "—"
    return "—" if v != v else f"{1000 * v:.0f} ms"


def ficha_evento(r: Resultado, i: int) -> list[tuple[str, str]]:
    """Los datos de UNA contraccion, leidos de la hoja cinetica (no se recalcula)."""
    e = r.cin.iloc[i]
    reportable = bool(r.fila.get("reportable"))
    grupo = str(e.get("grupo", ""))
    nombre_grupo = {"estimulados": "estimulada", "espontaneos": "espontánea"}.get(grupo, grupo)
    filas = [("Contracción", f"{int(e['evento'])} de {len(r.cin)}"
              + ("" if reportable else "  (candidata: conteo NO reportable)")),
             ("Instante del pico", f"{float(e['tiempo_s']):.3f} s"),
             ("Tipo", nombre_grupo or "—")]
    if r.grilla is not None and grupo == "estimulados" and "t_medido_s" in r.grilla:
        g = r.grilla.dropna(subset=["t_medido_s"])
        if len(g):
            k = int(np.argmin(np.abs(g["t_medido_s"].to_numpy(float) - float(e["onset_s"]))))
            if abs(float(g["t_medido_s"].iloc[k]) - float(e["onset_s"])) < 0.5:
                filas.append(("Desvío del estimulador", f"{1000 * float(g['error_s'].iloc[k]):+.0f} ms"))
    filas += [("Amplitud", f"{float(e['amplitud_px']):.2f} px = "
                           f"{float(e['amplitud_relativa_pct']):.2f} % del grosor"),
              ("Grosor en reposo", f"{float(e['grosor_reposo_px']):.0f} px")]
    for m, nom in (("ttp", "Tiempo al pico (TTP)"), ("rt50", "Relajación 50 % (RT50)")):
        if m + "_s" not in e or e[m + "_s"] != e[m + "_s"]:
            filas.append((nom, "—"))
        elif bool(e.get(m + "_medible")):
            filas.append((nom, f"{_ms(e[m + '_s'])}  ({int(e[m + '_frames'])} fotogramas)"))
        else:
            filas.append((nom, f"menos de {_ms(e[m + '_max_s'])}  "
                               f"({int(e[m + '_frames'])} fot.; no medible a 30 fps)"))
    filas.append(("Duración (10 % a 10 %)", _ms(e.get("duracion_s"))))
    notas = []
    if bool(e.get("junto_al_borde", False)):
        notas.append("cerca del inicio o del final del video")
    if bool(e.get("junto_a_hueco", False)):
        notas.append("junto a un fotograma sin medida")
    if "en_promedio" in e and e["en_promedio"] is False:
        notas.append("no entra en el promedio")
    if notas:
        filas.append(("Ojo", "; ".join(notas)))
    return filas


def ficha_texto(r: Resultado, i: int) -> str:
    """La ficha como texto (para copiar o guardar): de qué resultado es y sus filas."""
    filas = [("Resultado", r.carpeta.name)] + ficha_evento(r, i)
    m = leer_marcas(r.carpeta).get(str(int(r.cin.iloc[i]["evento"])))
    if m:
        filas.append(("Marca manual", m))
    return "\n".join(f"{a}:\t{b}" for a, b in filas)


# ---- marcas manuales ("dudosa"): archivo aparte, nunca tocan los Excel ----
def archivo_marcas(carpeta: Path) -> Path:
    return Path(carpeta) / f"marcas_{Path(carpeta).name}.json"


def leer_marcas(carpeta: Path) -> dict[str, str]:
    """{numero de evento (texto): nota}. Archivo aparte: los Excel no se tocan
    y ningún número cambia. Si no existe o está roto, vacío."""
    import json
    try:
        d = json.loads(archivo_marcas(carpeta).read_text(encoding="utf-8"))
        return {str(k): str(v) for k, v in d.get("dudosas", {}).items()}
    except Exception:
        return {}


def marcar_dudosa(carpeta: Path, evento: int, dudosa: bool = True, nota: str = "dudosa") -> dict:
    import json
    from datetime import datetime
    m = leer_marcas(carpeta)
    if dudosa:
        m[str(int(evento))] = nota or "dudosa"
    else:
        m.pop(str(int(evento)), None)
    p = archivo_marcas(carpeta)
    if m:
        p.write_text(json.dumps({"que_es": "contracciones marcadas a mano como dudosas desde la "
                                           "ventana. Solo una nota: no cambia ningún número.",
                                 "actualizado": datetime.now().isoformat(timespec="seconds"),
                                 "dudosas": dict(sorted(m.items(), key=lambda kv: int(kv[0])))},
                                ensure_ascii=False, indent=1), encoding="utf-8")
    elif p.is_file():
        p.unlink()
    return m


# ---- para comparar y para las vistas nuevas (solo dibujo y lectura) ----
def eventos_principales(r: Resultado) -> np.ndarray:
    """Qué contracciones entran en el promedio que se compara: las del grupo de
    la amplitud informada (`cinetica_grupo_principal`), y de esas las que tienen
    la ventana entera (`en_promedio`). Si no es reportable, todas las candidatas."""
    if r.cin is None or not len(r.cin):
        return np.zeros(0, bool)
    m = np.ones(len(r.cin), bool)
    g = r.res.get("cinetica_grupo_principal") if r.res else None
    if bool(r.fila.get("reportable")) and isinstance(g, str) and g and g != "todos":
        sel = r.cin["grupo"].astype(str).to_numpy() == g
        if sel.any():
            m &= sel
    if "en_promedio" in r.cin:
        m &= np.array([bool(x) if x == x else True for x in r.cin["en_promedio"].to_numpy()])
    return m


def promedio_para_dibujar(r: Resultado, half_s: float = 1.5):
    """Contracción promedio en % del grosor en reposo, alineada en el pico.
    Es un DIBUJO (la misma idea que promedio_alineado del reporte, cada evento
    dividido por su grosor en reposo); los números que se comparan salen del
    resumen. Devuelve (lag_s, y_pct, n) o (None, None, 0)."""
    m = eventos_principales(r)
    if not m.any() or r.senal is None:
        return None, None, 0
    fps = float(r.res.get("fps_medido") or r.res.get("fps") or 30.0) if r.res else 30.0
    h = int(half_s * fps)
    segs = []
    for _, e in r.cin[m].iterrows():
        p = int(e["frame_pico"])
        g = float(e["grosor_reposo_px"])
        if p - h >= 0 and p + h + 1 <= len(r.senal) and g > 0:
            segs.append(100.0 * r.senal[p - h:p + h + 1] / g)
    if not segs:
        return None, None, 0
    return np.arange(-h, h + 1) / fps, np.nanmean(np.asarray(segs), axis=0), len(segs)


def ic_amplitud(r: Resultado) -> tuple[float, float] | None:
    """El IC 95 % de la amplitud tal como está en el resumen ('a-b'); None si
    el resultado es anterior al IC (2026-10-10) o no hay."""
    ic = r.res.get("amplitud_relativa_ic95_pct") if r.res else None
    try:
        a, b = (float(v) for v in str(ic).split("-"))
        return a, b
    except (TypeError, ValueError):
        return None


def _txt_num(x, fmt=".2f", vacio="—"):
    try:
        v = float(x)
    except (TypeError, ValueError):
        return vacio
    return vacio if v != v else format(v, fmt)


def tabla_comparar(rs: list[Resultado]) -> list[tuple[str, list[str]]]:
    """Filas de la tabla lado a lado: (métrica, [valor de cada resultado]).
    Todo sale de los Excel; lo que no está (resultados viejos) queda '—'."""
    import informe

    def fila(nombre, f):
        out = []
        for r in rs:
            try:
                out.append(f(r))
            except Exception:
                out.append("—")
        return (nombre, out)

    def rep(r):
        v = r.fila.get("reportable")
        return "—" if v is None else ("sí" if v else "NO")

    def tren(r):
        f = r.fila
        if f.get("tren") != "si":
            return "no" if r.res else "—"
        return (f"{f['n_estimulados']} estim., {f['periodo_s']:.4f} ± {f['periodo_err_s']:.4f} s, "
                f"captura {f['captura_pct']:.0f} %")

    def amp_pct(r):
        if not r.fila.get("reportable") or r.fila.get("amplitud_pct") is None:
            return "—"
        ic = ic_amplitud(r)
        return f"{r.fila['amplitud_pct']:.2f} %" + (f"  (IC {ic[0]:.2f}–{ic[1]:.2f})" if ic else "  (sin IC)")

    def cin(m):
        def f(r):
            if not r.fila.get("reportable") or not r.res:
                return "—"
            return informe.cinetica_txt(r.res, m).replace(
                " (más rápida que la cámara: a 30 fps no se puede dar un valor)", " (no medible)")
        return f

    def roi(r):
        s = r.serie_meta
        return f"{int(float(s['ROI x_start']))}–{int(float(s['ROI x_end']))} px"

    return [
        fila("Contracciones", lambda r: _txt_num(r.fila.get("eventos"), ".0f")),
        fila("Reportable", rep),
        fila("Tren de estímulo", tren),
        fila("Amplitud (% del grosor)", amp_pct),
        fila("Amplitud (px)", lambda r: _txt_num(r.fila.get("amplitud_px"))
             if r.fila.get("reportable") else "—"),
        fila("Grupo de la amplitud", lambda r: (r.fila.get("amplitud_grupo") or "—")
             if r.fila.get("reportable") else "—"),
        fila("TTP", cin("ttp")),
        fila("RT50", cin("rt50")),
        fila("Grosor medio (px)", lambda r: _txt_num(r.serie_meta.get("grosor medio (px)"), ".0f")),
        fila("Zona (ROI)", roi),
        fila("Duración (s)", lambda r: _txt_num(r.serie_meta.get("duracion segun PTS (s)"), ".1f")),
        fila("Fotogramas perdidos (%)", lambda r: _txt_num(r.serie_meta.get("frames faltantes (%)"))),
        fila("2.º método", lambda r: str(r.veredicto.get("veredicto", "—")) if r.veredicto else "—"),
        fila("Avisos", lambda r: str(len(r.avisos)) if r.avisos else "ninguno"),
        fila("Marcadas dudosas (a mano)", lambda r: str(len(leer_marcas(r.carpeta)))),
    ]


def guardar_tabla_comparar(rs: list[Resultado], destino: Path) -> Path:
    """La tabla lado a lado a un Excel (o .csv), tal como se ve."""
    filas = tabla_comparar(rs)
    df = pd.DataFrame({"métrica": [a for a, _ in filas]}
                      | {r.carpeta.name: [v[i] for _, v in filas] for i, r in enumerate(rs)})
    destino = Path(destino)
    if destino.suffix.lower() == ".csv":
        df.to_csv(destino, index=False, encoding="utf-8-sig")
    else:
        df.to_excel(destino, index=False)
    return destino


def fotograma(r: Resultado, i: int):
    """El fotograma del pico de la contracción i, leído del video original, con
    los bordes medidos (y_top_px / y_bottom_px de la serie) y la zona (ROI).
    Devuelve (imagen gris, x0, x1, y_top, y_bottom, nro) o levanta
    FileNotFoundError si el video ya no está donde se analizó."""
    import cv2
    video = Path(str(r.serie_meta.get("video", "")))
    if not video.is_file():   # se movio la carpeta: buscarlo por nombre en data/raw_videos
        nombre = str(r.serie_meta.get("video", "")).replace("\\", "/").split("/")[-1]
        cand = sorted((RAIZ / "data" / "raw_videos").rglob(nombre)) if nombre else []
        if not cand:
            raise FileNotFoundError(f"No encuentro el video {nombre or '?'} (ni donde se analizó "
                                    f"ni en data/raw_videos)")
        video = cand[0]
    p = int(r.cin.iloc[i]["frame_pico"])
    df = leer_excel(buscar_serie(r.carpeta), sheet_name="diagnostics",
                       usecols=["frame", "y_top_px", "y_bottom_px"])
    fila = df.iloc[min(p, len(df) - 1)]
    nro = int(fila["frame"])
    cap = cv2.VideoCapture(str(video))
    try:
        cap.set(cv2.CAP_PROP_POS_FRAMES, nro)
        ok, img = cap.read()
    finally:
        cap.release()
    if not ok:
        raise RuntimeError(f"No pude leer el fotograma {nro} de {video.name}")
    if img.ndim == 3:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    x0 = float(r.serie_meta.get("ROI x_start", 0))
    x1 = float(r.serie_meta.get("ROI x_end", img.shape[1]))
    return img, x0, x1, float(fila["y_top_px"]), float(fila["y_bottom_px"]), nro


def guardar_ficha_png(r: Resultado, i: int, destino: Path) -> Path:
    """Imagen de una contracción: su forma y la ficha al lado (para mandar)."""
    from matplotlib.figure import Figure
    e = r.cin.iloc[i]
    p = int(min(e["frame_pico"], len(r.t) - 1))
    fig = Figure(figsize=(10, 4.2), dpi=150)
    ax = fig.add_axes([0.07, 0.14, 0.42, 0.74])
    m = (r.t >= r.t[p] - 1.0) & (r.t <= r.t[p] + 1.5)
    ax.plot(r.t[m] - r.t[p], r.senal[m], color="#4a6fa5", lw=1.3, marker=".", ms=4)
    for col, ls, lab in (("onset_s", ":", "inicio"), ("offset_s", "--", "fin")):
        v = e.get(col)
        if v is not None and v == v:
            ax.axvline(float(v) - r.t[p], color="gray", ls=ls, lw=0.8, label=lab)
    ax.axvline(0, color="#d62728", lw=0.8, label="pico")
    ax.axhline(0, color="#999", lw=0.5)
    ax.set_xlabel("s desde el pico")
    ax.set_ylabel("posición de la franja sin deriva (px)")
    ax.legend(fontsize=7)
    ax.grid(alpha=0.25)
    fig.suptitle(f"{r.carpeta.name} · contracción {int(e['evento'])}", fontsize=11)
    filas = ficha_evento(r, i)
    nota = leer_marcas(r.carpeta).get(str(int(e["evento"])))
    if nota:
        filas.append(("Marca manual", nota))
    fig.text(0.54, 0.86, "\n".join(f"{a}:  {b}" for a, b in filas), va="top", fontsize=8.5,
             family="DejaVu Sans", wrap=True)
    fig.savefig(destino)
    return Path(destino)


def abrir_en_sistema(p: Path):
    p = str(p)
    if sys.platform.startswith("win"):
        os.startfile(p)
    elif sys.platform == "darwin":
        subprocess.Popen(["open", p])
    else:
        subprocess.Popen(["xdg-open", p])


# --------------------------------------------------------------------------
# Pestaña
# --------------------------------------------------------------------------
VISTAS = [("Contracciones (interactivo)", None),
          ("Amplitud de cada contracción vs tiempo", "amp_t"),
          ("Grosor (diagnóstico)", "grosor"),
          ("Ritmo (figura guardada)", "10_ritmo"),
          ("Forma promedio (figura guardada)", "11_cinetica"),
          ("Zona del gel (figura guardada)", "00_roi_profile"),
          ("Control del umbral (figura guardada)", "05_estabilidad_umbral"),
          ("Confirmación, 2.º método (figura guardada)", "07_movimiento")]


class PestanaResultados:
    def __init__(self, padre, base: Path, oscuro: bool = False):
        import tkinter as tk
        from tkinter import ttk
        import matplotlib
        matplotlib.use("TkAgg")
        from matplotlib.figure import Figure
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

        self.tk, self.ttk = tk, ttk
        self.base = Path(base)
        self.raiz = padre.winfo_toplevel()
        self.r: Resultado | None = None
        self.sel: int | None = None
        self.oscuro = oscuro

        k = float(getattr(self.raiz, "_factor_ui", 1.0))   # escala de pantalla x tamano_letra
        px = lambda n: int(round(n * k))
        # filas de las tablas a la altura de la letra (si no, con letra grande se cortan)
        import tkinter.font as tkfont
        lh = 0
        for nf in ("SunValleyBodyFont", "TkDefaultFont"):
            try:
                lh = max(lh, tkfont.nametofont(nf, self.raiz).metrics("linespace"))
            except Exception:
                pass
        if lh:
            ttk.Style(self.raiz).configure("Treeview", rowheight=lh + 8)
        frm = ttk.Frame(padre)
        frm.pack(fill="both", expand=True)
        pan = ttk.PanedWindow(frm, orient="horizontal")
        pan.pack(fill="both", expand=True)

        # ---- izquierda: lista de carpetas ----
        izq = ttk.Frame(pan, padding=(6, 6))
        pan.add(izq, weight=0)
        self.v_buscar = tk.StringVar()
        self.v_buscar.trace_add("write", lambda *_: self._llenar_lista())
        ttk.Label(izq, text="Buscar").pack(anchor="w")
        ttk.Entry(izq, textvariable=self.v_buscar).pack(fill="x", pady=(0, 6))
        self.lista = ttk.Treeview(izq, columns=("ev",), show="tree headings", height=20,
                                  selectmode="browse")
        self.lista.heading("#0", text="Resultado")
        self.lista.heading("ev", text="Contr.")
        self.lista.column("#0", width=px(270), stretch=True)
        self.lista.column("ev", width=px(55), anchor="center", stretch=False)
        self.lista.pack(fill="both", expand=True)
        self.lista.tag_configure("si", foreground="#2e7d4f")
        self.lista.tag_configure("no", foreground="#b03a2e")
        self.lista.bind("<<TreeviewSelect>>", lambda _e: self._al_elegir())
        bot = ttk.Frame(izq)
        # abajo de todo y reservado antes que la lista (si no, la lista lo tapaba)
        bot.pack(side="bottom", fill="x", pady=(6, 6), before=self.lista)
        ttk.Button(bot, text="Actualizar", command=self.refrescar).pack(side="left")
        ttk.Button(bot, text="Otra carpeta...", command=self._elegir_base).pack(side="left", padx=4)

        # ---- derecha ----
        der = ttk.Frame(pan, padding=(8, 6))
        pan.add(der, weight=4)
        self.titulo = ttk.Label(der, text="Elegí un resultado de la lista", style="Seccion.TLabel")
        self.titulo.pack(anchor="w")
        self.frase = tk.Text(der, height=3, width=30, wrap="word", relief="flat", borderwidth=0,
                             font=("Segoe UI", 10))
        self.frase.pack(fill="x", pady=(4, 4))
        self.frase.configure(state="disabled")
        self.estado = ttk.Label(der, text="", foreground="gray")
        self.estado.pack(side="bottom", anchor="w")

        # dos sub-pestañas: con todo junto el grafico quedaba muy chico
        self.sub = ttk.Notebook(der)
        self.sub.pack(fill="both", expand=True, pady=(2, 0))
        t_num = ttk.Frame(self.sub, padding=(4, 8))
        t_graf = ttk.Frame(self.sub, padding=(0, 4))
        self.sub.add(t_num, text="  Números y ficha  ")
        self.sub.add(t_graf, text="  Gráfico  ")
        self.sub.select(1)

        fila = ttk.Frame(t_num)
        fila.pack(fill="both", expand=True)
        # numeros: etiquetas que parten los textos largos en varias lineas
        # (una tabla Treeview no parte el texto y los avisos largos se cortaban)
        self.numeros = ttk.Frame(fila)
        self.numeros.pack(side="left", fill="y")
        self.numeros.columnconfigure(1, weight=1)
        self._ancho_num = px(330)
        self._px = px
        # los numeros usan como mucho la mitad del ancho; el resto, la ficha
        fila.bind("<Configure>", lambda e: self._ajustar_numeros(e.width), add="+")
        self.ficha = ttk.LabelFrame(fila, text="Contracción elegida (clic en el gráfico, ← →)", padding=6)
        self.ficha.pack(side="left", fill="both", expand=True, padx=(8, 0))
        self.ficha_txt = ttk.Label(self.ficha, text="—", justify="left", wraplength=px(520))
        self.ficha_txt.pack(anchor="nw")
        fb = ttk.Frame(self.ficha)
        fb.pack(anchor="sw", side="bottom", pady=(6, 0), fill="x")
        self.b_dudosa = ttk.Button(fb, text="Marcar dudosa (D)", command=self.alternar_dudosa,
                                   state="disabled")
        self.b_copiar = ttk.Button(fb, text="Copiar", command=self.copiar_ficha, state="disabled")
        self.b_gficha = ttk.Button(fb, text="Guardar...", command=self.guardar_ficha,
                                   state="disabled")
        self.b_foto = ttk.Button(fb, text="Fotograma (F)", command=self.ver_fotograma,
                                 state="disabled")
        # 2 x 2: entran aunque la ficha quede angosta
        for k, b in enumerate((self.b_dudosa, self.b_foto, self.b_copiar, self.b_gficha)):
            b.grid(row=k // 2, column=k % 2, sticky="ew", padx=2, pady=2)
        fb.columnconfigure((0, 1), weight=1)
        # el texto de la ficha se acomoda al ancho que quede libre
        self.ficha.bind("<Configure>",
                        lambda e: self.ficha_txt.config(wraplength=max(150, e.width - 24)))

        barra = ttk.Frame(t_graf)
        barra.pack(fill="x", pady=(2, 2))
        ttk.Label(barra, text="Vista:").pack(side="left")
        self.v_vista = tk.StringVar(value=VISTAS[0][0])
        cb = ttk.Combobox(barra, textvariable=self.v_vista, values=[v[0] for v in VISTAS],
                          state="readonly", width=22)
        cb.pack(side="left", padx=4)
        cb.bind("<<ComboboxSelected>>", lambda _e: self._dibujar())
        ttk.Button(barra, text="Abrir informe", command=self._abrir_informe).pack(side="right")
        ttk.Button(barra, text="Abrir carpeta",
                   command=lambda: self.r and abrir_en_sistema(self.r.carpeta)).pack(side="right", padx=4)
        ttk.Button(barra, text="Guardar gráfico...", command=self._guardar_png).pack(side="right")

        # con la nitidez de Windows activada, los px son reales: la figura usa la
        # densidad de la pantalla para que el texto no quede diminuto
        try:
            # 85 % de la densidad: con 100 % los textos del grafico quedan mas
            # grandes que los de la ventana
            dpi = max(80.0, min(200.0, 0.85 * float(self.raiz.winfo_fpixels("1i")) * float(
                getattr(self.raiz, "_factor_ui", 1.0)) / max(float(self.raiz.winfo_fpixels("1i")) / 96.0, 1e-6)))
        except Exception:
            dpi = 100.0
        self.fig = Figure(figsize=(9, 4.2), dpi=dpi)
        self.canvas = FigureCanvasTkAgg(self.fig, master=t_graf)
        tb = NavigationToolbar2Tk(self.canvas, t_graf, pack_toolbar=False)
        tb.update()
        tb.pack(fill="x")
        # ancho pedido chico: el grafico igual ocupa todo; si pide mucho, el panel
        # de la lista no se puede acomodar
        self.canvas.get_tk_widget().configure(width=300, height=200)
        # resumen de la contraccion elegida, para no tener que cambiar de sub-pestaña
        self.ficha_corta = ttk.Label(t_graf, text="", justify="left")
        self.ficha_corta.pack(side="bottom", anchor="w", fill="x", pady=(2, 0))
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
        self.canvas.mpl_connect("pick_event", self._al_clic)

        # ancho inicial de la lista (si no, el panel puede arrancar cerrado)
        # ancho inicial de la lista: se fija cuando el panel ya tiene su ancho real
        # (fijarlo antes, con la pestaña sin dibujar, lo dejaba en cualquier lado)
        self._sash_ok = False

        def _sash(e, pan=pan):
            if not self._sash_ok and e.width > 400:
                self._sash_ok = True
                self.raiz.after_idle(lambda w=e.width: pan.sashpos(0, min(px(340), int(0.4 * w))))
        pan.bind("<Configure>", _sash, add="+")
        self._carpetas: list[Path] = []
        self._info: dict[str, tuple] = {}
        self.refrescar()

    # ---------------- lista ----------------
    def refrescar(self, elegir: str | None = None):
        self._carpetas = listar_carpetas(self.base)
        self._llenar_lista()
        self.estado.config(text=f"{len(self._carpetas)} resultados en {self.base}")
        # conteo y color de cada carpeta en segundo plano (lee un Excel chico por carpeta)

        def trabajo(carpetas=list(self._carpetas)):
            import procesar_carpeta as pc
            for c in carpetas:
                try:
                    f = pc.leer_fila(c)
                    self._info[c.name] = (f.get("eventos"), f.get("reportable"))
                except Exception:
                    self._info[c.name] = (None, None)
            self.raiz.after(0, self._llenar_lista)
        threading.Thread(target=trabajo, daemon=True).start()
        if elegir:
            self.elegir(elegir)

    def _llenar_lista(self):
        q = self.v_buscar.get().lower().strip()
        actual = self.lista.selection()
        self.lista.delete(*self.lista.get_children())
        for c in self._carpetas:
            if q and q not in c.name.lower():
                continue
            ev, rep = self._info.get(c.name, (None, None))
            tag = "si" if rep else ("no" if rep is False else "")
            marca = "● " if rep is not None else "  "
            self.lista.insert("", "end", iid=c.name, text=marca + c.name,
                              values=("" if ev is None else ev,), tags=(tag,))
        for s in actual:
            if self.lista.exists(s):
                self.lista.selection_set(s)

    def elegir(self, nombre: str):
        if self.lista.exists(nombre):
            self.lista.selection_set(nombre)
            self.lista.see(nombre)

    def _elegir_base(self):
        from tkinter import filedialog
        r = filedialog.askdirectory(title="Carpeta con resultados", initialdir=str(self.base))
        if r:
            self.base = Path(r)
            self.refrescar()

    def _al_elegir(self):
        s = self.lista.selection()
        if not s:
            return
        carpeta = self.base / s[0]
        self.estado.config(text=f"Leyendo {carpeta.name}...")

        def trabajo():
            try:
                r = leer_resultado(carpeta)
                self.raiz.after(0, lambda: self._mostrar(r))
            except Exception as e:
                msg = str(e)   # `e` deja de existir al salir del except
                self.raiz.after(0, lambda: self.estado.config(text=f"No pude leer {carpeta.name}: {msg}"))
        threading.Thread(target=trabajo, daemon=True).start()

    # ---------------- mostrar ----------------
    def _mostrar(self, r: Resultado):
        self.r, self.sel = r, None
        self.titulo.config(text=r.carpeta.name)
        import re
        clase, frase = r.frase
        self.frase.configure(state="normal")
        self.frase.delete("1.0", "end")
        color = {"bien": "#2e7d4f", "mal": "#b03a2e"}.get(clase, "gray")
        self.frase.insert("end", re.sub(r"<[^>]+>", "", frase))
        self.frase.tag_add("c", "1.0", "end")
        self.frase.tag_config("c", foreground=color)
        self.frase.configure(state="disabled")

        import informe
        for w in self.numeros.winfo_children():
            w.destroy()
        f, res = r.fila, r.res
        filas = [("Contracciones", f"{f.get('eventos', '—')}"
                  + ("" if f.get("reportable") is None else
                     (" (reportable)" if f.get("reportable") else " (NO reportable)")))]
        if f.get("tren") == "si":
            filas.append(("Tren de estímulo", f"{f.get('n_estimulados')} estimuladas, período "
                          f"{f.get('periodo_s'):.4f} ± {f.get('periodo_err_s'):.4f} s, "
                          f"captura {f.get('captura_pct'):.0f} %"))
        elif res:
            filas.append(("Tren de estímulo", "no se encontró"))
        if f.get("reportable") and f.get("amplitud_pct") is not None:
            ic = res.get("amplitud_relativa_ic95_pct")
            filas.append((f"Amplitud ({f.get('amplitud_grupo') or 'todas'})",
                          f"{f['amplitud_pct']:.2f} % = {f.get('amplitud_px', float('nan')):.2f} px"
                          + (f"   (IC 95 %: {informe._rango(ic)} %)" if isinstance(ic, str) else "")))
            for m, nom in (("ttp", "TTP"), ("rt50", "RT50")):
                txt = informe.cinetica_txt(res, m)
                filas.append((nom, txt.replace(" (más rápida que la cámara: a 30 fps no se puede dar un valor)",
                                               "  (no medible a 30 fps)")))
        if r.veredicto:
            filas.append(("2.º método", str(r.veredicto.get("veredicto", ""))))
        for a in r.avisos:
            filas.append(("Aviso", a))
        dud = leer_marcas(r.carpeta)
        if dud:
            filas.append(("Marcadas dudosas", ", ".join(sorted(dud, key=int))
                          + "  (a mano; no cambia ningún número)"))
        ttk = self.ttk
        for k, (a, b) in enumerate(filas):
            col = "#b03a2e" if a == "Aviso" else None
            ttk.Label(self.numeros, text=a).grid(row=k, column=0, sticky="nw", padx=(0, 10), pady=1)
            lb = ttk.Label(self.numeros, text=b, wraplength=self._ancho_num, justify="left")
            if col:
                lb.configure(foreground=col)
            lb.grid(row=k, column=1, sticky="nw", pady=1)
        self.ficha_txt.config(text="—")
        self.ficha_corta.config(text="Clic en una contracción (o ← →) para ver su resumen acá.")
        for b in (self.b_dudosa, self.b_copiar, self.b_gficha, self.b_foto):
            b.config(state="disabled")
        self.estado.config(text=str(r.carpeta))
        self._dibujar()

    def _ajustar_numeros(self, ancho: int):
        w = max(160, int(0.5 * ancho) - self._px(170))
        if abs(w - self._ancho_num) < 8:
            return
        self._ancho_num = w
        for lb in self.numeros.grid_slaves(column=1):
            lb.configure(wraplength=w)

    def _dibujar(self):
        r = self.r
        self.fig.clear()
        if r is None:
            self.canvas.draw_idle()
            return
        clave = dict(VISTAS)[self.v_vista.get()]
        if clave is None:
            self._dibujar_contracciones()
        elif clave == "amp_t":
            self._dibujar_amplitud_tiempo()
        elif clave == "grosor":
            ax = self.fig.add_subplot(111)
            ax.plot(r.t, r.grosor, lw=0.7, color="#555")
            ax.set_xlabel("tiempo (s)"); ax.set_ylabel("grosor (px)")
            ax.set_title("Grosor de la franja: solo diagnóstico (no se informa)", fontsize=10)
            ax.grid(alpha=0.3)
        else:
            png = sorted(r.carpeta.glob(f"{clave}_*.png"))
            ax = self.fig.add_subplot(111)
            ax.axis("off")
            if png:
                import matplotlib.image as mpimg
                ax.imshow(mpimg.imread(png[0]))
                self.fig.subplots_adjust(0, 0, 1, 1)
            else:
                ax.text(0.5, 0.5, "Esta figura no está en la carpeta\n(se arma con el paso que la genera)",
                        ha="center", va="center", color="gray")
        self.canvas.draw_idle()

    def _dibujar_contracciones(self):
        r = self.r
        gs = self.fig.add_gridspec(1, 4)
        ax = self.fig.add_subplot(gs[0, :3])
        self.ax_zoom = self.fig.add_subplot(gs[0, 3])
        ax.plot(r.t, r.senal, lw=0.6, color="#4a6fa5", zorder=1)
        ax.axhline(0, color="#999", lw=0.5)
        self._puntos = None
        if r.cin is not None and len(r.cin):
            rep = bool(r.fila.get("reportable"))
            idx = np.clip(r.cin["frame_pico"].to_numpy(int), 0, len(r.t) - 1)
            grupos = r.cin["grupo"].astype(str).to_numpy() if rep else np.array(["candidatos"] * len(idx))
            cols = [COLOR.get(g, "#444") for g in grupos]
            self._puntos = ax.scatter(r.t[idx], r.senal[idx], s=38, c=cols, marker="v",
                                      zorder=3, picker=6, edgecolors="white", linewidths=0.5)
            for g in dict.fromkeys(grupos):
                n = int((grupos == g).sum())
                nom = {"estimulados": "estimuladas", "espontaneos": "espontáneas",
                       "candidatos": "candidatos (no reportable)"}.get(g, g)
                ax.scatter([], [], c=COLOR.get(g, "#444"), marker="v", label=f"{n} {nom}")
            ax.legend(fontsize=8, loc="upper right")
            dud = leer_marcas(r.carpeta)
            md = np.array([str(int(v)) in dud for v in r.cin["evento"].to_numpy()])
            if md.any():
                ax.scatter(r.t[idx[md]], r.senal[idx[md]], s=110, facecolors="none",
                           edgecolors="#e67e22", linewidths=1.4, zorder=4,
                           label=f"{int(md.sum())} marcadas dudosas (a mano)")
                ax.legend(fontsize=8, loc="upper right")
            self._sel_art = ax.scatter([], [], s=160, facecolors="none", edgecolors="k",
                                       linewidths=1.5, zorder=4)
        ax.set_xlabel("tiempo (s)")
        ax.set_ylabel("posición de la franja sin deriva (px)")
        ax.set_title("Clic en una contracción para ver su ficha · rueda/lupa: zoom", fontsize=9,
                     color="gray")
        ax.grid(alpha=0.25)
        self.ax = ax
        self.ax_zoom.set_title("forma de la elegida", fontsize=9, color="gray")
        self.ax_zoom.set_xticks([]); self.ax_zoom.set_yticks([])
        self.fig.tight_layout()
        if self.sel is not None:
            self._seleccionar(self.sel)

    def _dibujar_amplitud_tiempo(self):
        """Amplitud de cada contraccion (hoja cinetica) contra su instante: ¿se
        cansa el gel? Solo dibuja lo del Excel; no ajusta ninguna tendencia."""
        r = self.r
        ax = self.fig.add_subplot(111)
        self._puntos = None
        if r.cin is None or not len(r.cin):
            ax.axis("off")
            ax.text(0.5, 0.5, "No hay contracciones (falta el paso 2)", ha="center", color="gray")
            return
        rep = bool(r.fila.get("reportable"))
        grupos = r.cin["grupo"].astype(str).to_numpy() if rep else np.array(["candidatos"] * len(r.cin))
        t = r.cin["tiempo_s"].to_numpy(float)
        a = r.cin["amplitud_relativa_pct"].to_numpy(float)
        dud = leer_marcas(r.carpeta)
        md = np.array([str(int(v)) in dud for v in r.cin["evento"].to_numpy()])
        for g in dict.fromkeys(grupos):
            m = grupos == g
            nom = {"estimulados": "estimuladas", "espontaneos": "espontáneas",
                   "candidatos": "candidatos (no reportable)"}.get(g, g)
            ax.plot(t[m], a[m], "o-" if g == "estimulados" else "o", color=COLOR.get(g, "#444"),
                    ms=5, lw=0.8, label=f"{int(m.sum())} {nom}")
        if md.any():
            ax.scatter(t[md], a[md], s=110, facecolors="none", edgecolors="#e67e22",
                       linewidths=1.4, label="marcadas dudosas (a mano)", zorder=4)
        amp = r.fila.get("amplitud_pct") if rep else None
        if amp is not None:
            ax.axhline(amp, color="gray", ls="--", lw=0.8,
                       label=f"amplitud informada ({r.fila.get('amplitud_grupo') or 'todas'}): {amp:.2f} %")
        ax.set_xlabel("tiempo (s)")
        ax.set_ylabel("amplitud (% del grosor en reposo)")
        ax.set_title("Amplitud de cada contracción (hoja cinetica) · ¿se cansa el gel?",
                     fontsize=9, color="gray")
        ax.set_ylim(0, 1.2 * float(np.nanmax(a)) if np.isfinite(a).any() else 1)
        ax.grid(alpha=0.25)
        ax.legend(fontsize=8, loc="lower right")
        self.fig.tight_layout()

    def _al_clic(self, ev):
        if ev.artist is not self._puntos or not len(ev.ind):
            return
        # si hay varias bajo el mouse, la mas cercana en x
        x = ev.mouseevent.xdata
        idx = self.r.cin["frame_pico"].to_numpy(int)
        cand = list(ev.ind)
        i = min(cand, key=lambda k: abs(self.r.t[min(idx[k], len(self.r.t) - 1)] - (x or 0)))
        self._seleccionar(i)

    def _seleccionar(self, i: int):
        r = self.r
        self.sel = i
        e = r.cin.iloc[i]
        p = int(min(e["frame_pico"], len(r.t) - 1))
        filas = ficha_evento(r, i)
        nota = leer_marcas(r.carpeta).get(str(int(e["evento"])))
        if nota:
            filas.append(("Marca manual", f"{nota} (no cambia ningún número)"))
        self.ficha_txt.config(text="\n".join(f"{a}:  {b}" for a, b in filas))
        d = dict(filas)
        self.ficha_corta.config(text="  ·  ".join(x for x in (
            f"Contracción {d.get('Contracción', '')}", d.get("Instante del pico", ""),
            d.get("Tipo", ""), d.get("Amplitud", ""),
            f"TTP {d.get('Tiempo al pico (TTP)', '—')}", "dudosa" if nota else "")
            if x))
        self.b_dudosa.config(text="Quitar marca (D)" if nota else "Marcar dudosa (D)")
        for b in (self.b_dudosa, self.b_copiar, self.b_gficha, self.b_foto):
            b.config(state="normal")
        if dict(VISTAS)[self.v_vista.get()] is not None:   # otra vista: solo la ficha
            return
        self._sel_art.set_offsets([[r.t[p], r.senal[p]]])
        az = self.ax_zoom
        az.clear()
        m = (r.t >= r.t[p] - 1.0) & (r.t <= r.t[p] + 1.5)
        az.plot(r.t[m] - r.t[p], r.senal[m], color="#4a6fa5", lw=1.2, marker=".", ms=3)
        for col, ls, lab in (("onset_s", ":", "inicio"), ("offset_s", "--", "fin")):
            v = e.get(col)
            if v == v and v is not None:
                az.axvline(float(v) - r.t[p], color="gray", ls=ls, lw=0.8, label=lab)
        az.axvline(0, color="#d62728", lw=0.8, label="pico")
        az.axhline(0, color="#999", lw=0.5)
        az.set_title(f"contracción {int(e['evento'])}", fontsize=9)
        az.set_xlabel("s desde el pico", fontsize=8)
        az.tick_params(labelsize=7)
        az.legend(fontsize=7)
        self.canvas.draw_idle()

    # ---------------- ficha: mover, marcar, exportar, fotograma ----------------
    def mover(self, paso: int):
        """Contracción anterior / siguiente (flechas)."""
        if self.r is None or self.r.cin is None or not len(self.r.cin):
            return
        n = len(self.r.cin)
        i = 0 if self.sel is None else (self.sel + paso) % n
        self._seleccionar(i)

    def alternar_dudosa(self):
        if self.r is None or self.sel is None:
            return
        ev = int(self.r.cin.iloc[self.sel]["evento"])
        ya = str(ev) in leer_marcas(self.r.carpeta)
        try:
            marcar_dudosa(self.r.carpeta, ev, dudosa=not ya)
        except OSError as e:
            self.estado.config(text=f"No pude guardar la marca: {e}")
            return
        self.estado.config(text=(f"Contracción {ev}: marca quitada" if ya else
                                 f"Contracción {ev} marcada dudosa")
                           + f" (en {archivo_marcas(self.r.carpeta).name}; ningún número cambia)")
        sel = self.sel
        self._mostrar(self.r)
        self._seleccionar(sel)

    def copiar_ficha(self):
        if self.r is None or self.sel is None:
            return
        self.raiz.clipboard_clear()
        self.raiz.clipboard_append(ficha_texto(self.r, self.sel))
        self.estado.config(text="Ficha copiada: se puede pegar en Excel, Word o un mail.")

    def guardar_ficha(self):
        if self.r is None or self.sel is None:
            return
        from tkinter import filedialog
        ev = int(self.r.cin.iloc[self.sel]["evento"])
        f = filedialog.asksaveasfilename(
            defaultextension=".png", initialdir=str(self.r.carpeta),
            initialfile=f"ficha_{self.r.carpeta.name}_contraccion_{ev}.png",
            filetypes=[("Imagen con la ficha y la forma", "*.png"), ("Texto", "*.txt")])
        if not f:
            return
        if f.lower().endswith(".txt"):
            Path(f).write_text(ficha_texto(self.r, self.sel), encoding="utf-8")
        else:
            guardar_ficha_png(self.r, self.sel, Path(f))
        self.estado.config(text=f"Ficha guardada en {f}")

    def ver_fotograma(self):
        if self.r is None or self.sel is None:
            return
        r, i = self.r, self.sel
        self.estado.config(text="Leyendo el fotograma del video...")

        def trabajo():
            try:
                datos = fotograma(r, i)
                self.raiz.after(0, lambda: self._ventana_fotograma(r, i, datos))
            except Exception as e:
                msg = str(e)
                self.raiz.after(0, lambda: self.estado.config(text=f"Fotograma: {msg}"))
        threading.Thread(target=trabajo, daemon=True).start()

    def _ventana_fotograma(self, r, i, datos):
        from matplotlib.figure import Figure
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
        img, x0, x1, yt, yb, nro = datos
        ev = int(r.cin.iloc[i]["evento"])
        top = self.tk.Toplevel(self.raiz)
        top.title(f"{r.carpeta.name} · contracción {ev} · fotograma {nro}")
        fig = Figure(figsize=(9, 5), dpi=100)
        ax = fig.add_subplot(111)
        ax.imshow(img, cmap="gray")
        ax.hlines([yt, yb], x0, x1, colors=["#e74c3c", "#3498db"], lw=1.2)
        ax.axvline(x0, color="#f1c40f", lw=0.8, ls="--")
        ax.axvline(x1, color="#f1c40f", lw=0.8, ls="--", label="zona (ROI)")
        ax.plot([], [], color="#e74c3c", label=f"borde sup. medido ({yt:.1f} px)")
        ax.plot([], [], color="#3498db", label=f"borde inf. medido ({yb:.1f} px)")
        ax.legend(fontsize=8, loc="lower right")
        ax.set_title(f"Fotograma del pico (n.º {nro}); las líneas son los bordes de la serie, "
                     "en el centro de la zona", fontsize=9)
        fig.tight_layout()
        cv = FigureCanvasTkAgg(fig, master=top)
        tb = NavigationToolbar2Tk(cv, top, pack_toolbar=False)
        tb.update()
        tb.pack(fill="x")
        cv.get_tk_widget().pack(fill="both", expand=True)
        cv.draw_idle()
        self.estado.config(text=f"Fotograma {nro} (lupa de la barra para acercarse al borde)")

    # ---------------- atajos ----------------
    def atajos(self, activa=lambda: True):
        """Teclas de la pestaña. `activa()` dice si la pestaña está a la vista;
        en un campo de texto las letras y flechas no se roban."""
        def h(f, letra=False):
            def g(ev):
                if not activa():
                    return None
                if letra and ev.widget.winfo_class() in ("TEntry", "Entry", "Text", "TCombobox"):
                    return None
                f()
                return "break"
            return g
        r = self.raiz
        r.bind("<Control-f>", h(lambda: self._foco_buscar()), add="+")
        r.bind("<F5>", h(self.refrescar), add="+")
        r.bind("<Control-s>", h(self._guardar_png), add="+")
        r.bind("<Left>", h(lambda: self.mover(-1), True), add="+")
        r.bind("<Right>", h(lambda: self.mover(+1), True), add="+")
        r.bind("<KeyPress-d>", h(self.alternar_dudosa, True), add="+")
        r.bind("<KeyPress-f>", h(self.ver_fotograma, True), add="+")
        r.bind("<Control-c>", h(self.copiar_ficha, True), add="+")

    def _foco_buscar(self):
        for w in self.lista.master.winfo_children():
            if w.winfo_class() == "TEntry":
                w.focus_set()
                return

    # ---------------- botones ----------------
    def _abrir_informe(self):
        if not self.r:
            return
        import informe
        p = self.r.carpeta / f"informe_{self.r.carpeta.name}.html"
        if not p.is_file():
            p = informe.generar(self.r.carpeta)
        abrir_en_sistema(p)

    def _guardar_png(self):
        if not self.r:
            return
        from tkinter import filedialog
        f = filedialog.asksaveasfilename(defaultextension=".png", initialdir=str(self.r.carpeta),
                                         initialfile=f"vista_{self.r.carpeta.name}.png",
                                         filetypes=[("PNG", "*.png")])
        if f:
            self.fig.savefig(f, dpi=150)
