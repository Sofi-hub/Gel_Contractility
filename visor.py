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


def leer_resultado(carpeta: Path) -> Resultado:
    """Lee todo lo de una carpeta. Con cache por fecha de los Excel."""
    import informe
    import procesar_carpeta as pc
    carpeta = Path(carpeta)
    archivos = sorted(carpeta.glob("*.xlsx"))
    clave = (str(carpeta), tuple((a.name, a.stat().st_mtime) for a in archivos))
    if clave in _CACHE:
        return _CACHE[clave]
    d = informe.leer(carpeta)                       # lo mismo que usa el informe
    r = Resultado(carpeta=carpeta, fila=d["fila"], serie_meta=d["serie"], res=d["res"],
                  veredicto=d.get("veredicto"))
    r.frase = informe.frase_resultado(d)
    r.avisos = informe.avisos(d)
    serie = buscar_serie(carpeta)
    df = pd.read_excel(serie, sheet_name="diagnostics")
    r.t = df["time_s"].to_numpy(float)
    c = df["center_px"].to_numpy(float)
    r.grosor = df["thickness_px"].to_numpy(float)
    if r.res:
        fps = float(r.res.get("fps_medido") or r.res.get("fps") or 30.0)
        win = float(r.res.get("win_s_usado") or 2.0)
        signo = float(r.res.get("signo") or 1.0)
        r.senal = signo * detrend_median(c, fps, win)
        contr = sorted(carpeta.glob("contracciones_*.xlsx"))
        h = pd.read_excel(contr[0], sheet_name=None)
        r.cin = _hoja(h, "cinetica")
        r.grilla = _hoja(h, "grilla")
        ev = _hoja(h, "eventos")
        if r.cin is not None and ev is not None and len(ev) == len(r.cin):
            for col in ("junto_al_borde", "junto_a_hueco", "en_promedio"):
                if col in ev:
                    r.cin[col] = ev[col].to_numpy()
    else:
        r.senal = c - np.nanmedian(c)
    _CACHE.clear()          # una sola entrada por carpeta alcanza; no crece sin limite
    _CACHE[clave] = r
    return r


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
        self.lista.column("#0", width=270, stretch=True)
        self.lista.column("ev", width=55, anchor="center", stretch=False)
        self.lista.pack(fill="both", expand=True)
        self.lista.tag_configure("si", foreground="#2e7d4f")
        self.lista.tag_configure("no", foreground="#b03a2e")
        self.lista.bind("<<TreeviewSelect>>", lambda _e: self._al_elegir())
        bot = ttk.Frame(izq)
        bot.pack(fill="x", pady=(6, 0))
        ttk.Button(bot, text="Actualizar", command=self.refrescar).pack(side="left")
        ttk.Button(bot, text="Otra carpeta...", command=self._elegir_base).pack(side="left", padx=4)

        # ---- derecha ----
        der = ttk.Frame(pan, padding=(8, 6))
        pan.add(der, weight=4)
        self.titulo = ttk.Label(der, text="Elegí un resultado de la lista", font=("Segoe UI", 13, "bold"))
        self.titulo.pack(anchor="w")
        self.frase = tk.Text(der, height=3, wrap="word", relief="flat", borderwidth=0,
                             font=("Segoe UI", 10))
        self.frase.pack(fill="x", pady=(4, 4))
        self.frase.configure(state="disabled")

        fila = ttk.Frame(der)
        fila.pack(fill="x")
        self.numeros = ttk.Treeview(fila, columns=("v",), show="tree", height=7)
        self.numeros.column("#0", width=190, stretch=False)
        self.numeros.column("v", width=360)
        self.numeros.pack(side="left", fill="x", expand=True)
        self.ficha = ttk.LabelFrame(fila, text="Contracción elegida (clic en el gráfico)", padding=6)
        self.ficha.pack(side="left", fill="both", padx=(8, 0))
        self.ficha_txt = ttk.Label(self.ficha, text="—", justify="left", width=52, wraplength=440)
        self.ficha_txt.pack(anchor="nw")

        barra = ttk.Frame(der)
        barra.pack(fill="x", pady=(6, 2))
        ttk.Label(barra, text="Vista:").pack(side="left")
        self.v_vista = tk.StringVar(value=VISTAS[0][0])
        cb = ttk.Combobox(barra, textvariable=self.v_vista, values=[v[0] for v in VISTAS],
                          state="readonly", width=38)
        cb.pack(side="left", padx=4)
        cb.bind("<<ComboboxSelected>>", lambda _e: self._dibujar())
        ttk.Button(barra, text="Abrir informe", command=self._abrir_informe).pack(side="right")
        ttk.Button(barra, text="Abrir carpeta",
                   command=lambda: self.r and abrir_en_sistema(self.r.carpeta)).pack(side="right", padx=4)
        ttk.Button(barra, text="Guardar gráfico...", command=self._guardar_png).pack(side="right")

        self.fig = Figure(figsize=(9, 4.2), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.fig, master=der)
        tb = NavigationToolbar2Tk(self.canvas, der, pack_toolbar=False)
        tb.update()
        tb.pack(fill="x")
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
        self.canvas.mpl_connect("pick_event", self._al_clic)
        self.estado = ttk.Label(der, text="", foreground="gray")
        self.estado.pack(anchor="w")

        # ancho inicial de la lista (si no, el panel puede arrancar cerrado)
        self.raiz.after(100, lambda: pan.sashpos(0, 330))
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
                self.raiz.after(0, lambda: self.estado.config(text=f"No pude leer {carpeta.name}: {e}"))
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
        self.numeros.delete(*self.numeros.get_children())
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
        for a, b in filas:
            self.numeros.insert("", "end", text=a, values=(b,))
        self.ficha_txt.config(text="—")
        self.estado.config(text=str(r.carpeta))
        self._dibujar()

    def _dibujar(self):
        r = self.r
        self.fig.clear()
        if r is None:
            self.canvas.draw_idle()
            return
        clave = dict(VISTAS)[self.v_vista.get()]
        if clave is None:
            self._dibujar_contracciones()
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
        self._sel_art.set_offsets([[r.t[p], r.senal[p]]])
        self.ficha_txt.config(text="\n".join(f"{a}:  {b}" for a, b in ficha_evento(r, i)))
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
