"""
comparar.py
-----------
La pestaña "Comparar" de la ventana (interfaz.py): dos o más resultados de
data/processed_data (nuevos o viejos) lado a lado.

  * tabla con los números principales, una columna por resultado;
  * la contracción promedio de cada uno superpuesta, en % del grosor en reposo
    (dibujo: alineada en el pico, mismo grupo que la amplitud informada);
  * la amplitud de cada uno con su IC 95 % (si el resultado es anterior al IC,
    solo el punto).

Regla de siempre: NO calcula ningún número. La tabla y la amplitud salen de los
Excel (las mismas funciones del visor y del informe); la curva promedio es solo
un dibujo. La parte de datos está en visor.py y se prueba en tests/test_visor.py.
"""
from __future__ import annotations

import threading
from pathlib import Path

import visor

# colores distinguibles (mismo orden en la curva, la amplitud y el encabezado)
PALETA = ["#1f77b4", "#d62728", "#2ca02c", "#9467bd", "#ff7f0e",
          "#17becf", "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22"]


class PestanaComparar:
    def __init__(self, padre, base: Path):
        import tkinter as tk
        from tkinter import ttk
        import matplotlib
        matplotlib.use("TkAgg")
        from matplotlib.figure import Figure
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

        self.tk, self.ttk = tk, ttk
        self.base = Path(base)
        self.raiz = padre.winfo_toplevel()
        self.rs: list[visor.Resultado] = []
        k = float(getattr(self.raiz, "_factor_ui", 1.0))
        px = lambda n: int(round(n * k))

        frm = ttk.Frame(padre)
        frm.pack(fill="both", expand=True)
        pan = ttk.PanedWindow(frm, orient="horizontal")
        pan.pack(fill="both", expand=True)

        # ---- izquierda: elegir ----
        izq = ttk.Frame(pan, padding=(6, 6))
        pan.add(izq, weight=0)
        ttk.Label(izq, text="Elegí 2 o más (Ctrl o Shift + clic)").pack(anchor="w")
        self.v_buscar = tk.StringVar()
        self.v_buscar.trace_add("write", lambda *_: self._llenar())
        self.e_buscar = ttk.Entry(izq, textvariable=self.v_buscar)
        self.e_buscar.pack(fill="x", pady=(2, 6))
        self.lista = ttk.Treeview(izq, show="tree", selectmode="extended", height=20)
        self.lista.column("#0", width=px(300), stretch=True)
        self.lista.pack(fill="both", expand=True)
        self.lista.bind("<Double-1>", lambda _e: self.comparar())
        bot = ttk.Frame(izq)
        # abajo de todo y reservado antes que la lista (si no, la lista lo tapaba)
        bot.pack(side="bottom", fill="x", pady=(6, 6), before=self.lista)
        ttk.Button(bot, text="Comparar", style="Accent.TButton",
                   command=self.comparar).pack(side="left")
        ttk.Button(bot, text="Actualizar", command=self.refrescar).pack(side="left", padx=4)
        ttk.Button(bot, text="Otra carpeta...", command=self._elegir_base).pack(side="left")

        # ---- derecha: tabla + gráfico ----
        der = ttk.Frame(pan, padding=(8, 6))
        pan.add(der, weight=4)
        self.titulo = ttk.Label(der, text="Elegí resultados a la izquierda y apretá Comparar",
                                style="Seccion.TLabel")
        self.titulo.pack(anchor="w")
        self.estado = ttk.Label(der, text="", foreground="gray")
        self.estado.pack(side="bottom", anchor="w")
        # dos sub-pestañas: tabla o grafico (juntos, todo quedaba chico)
        self.sub = ttk.Notebook(der)
        self.sub.pack(fill="both", expand=True, pady=(4, 0))
        t_tab = ttk.Frame(self.sub, padding=(0, 6))
        t_graf = ttk.Frame(self.sub, padding=(0, 4))
        self.sub.add(t_tab, text="  Tabla  ")
        self.sub.add(t_graf, text="  Gráfico  ")
        bt = ttk.Frame(t_tab)
        bt.pack(side="bottom", fill="x", pady=(6, 0))
        ttk.Button(bt, text="Guardar tabla...", command=self._guardar_tabla).pack(side="left")
        ttk.Label(bt, text="todo sale de los Excel", foreground="gray").pack(side="left", padx=8)
        caja = ttk.Frame(t_tab)
        caja.pack(fill="both", expand=True)
        self.tabla = ttk.Treeview(caja, show="headings", height=8)
        sx = ttk.Scrollbar(caja, orient="horizontal", command=self.tabla.xview)
        sy = ttk.Scrollbar(caja, orient="vertical", command=self.tabla.yview)
        self.tabla.configure(xscrollcommand=sx.set, yscrollcommand=sy.set)
        self.tabla.grid(row=0, column=0, sticky="nsew")
        sy.grid(row=0, column=1, sticky="ns")
        sx.grid(row=1, column=0, sticky="ew")
        caja.columnconfigure(0, weight=1)
        caja.rowconfigure(0, weight=1)
        self._px = px

        barra = ttk.Frame(t_graf)
        barra.pack(fill="x", pady=(2, 2))
        ttk.Button(barra, text="Guardar gráfico...", command=self._guardar_png).pack(side="left")
        ttk.Label(barra, text="amplitud: de los Excel · curva promedio: solo dibujo",
                  foreground="gray").pack(side="left", padx=8)
        der = t_graf

        try:
            dpi = max(80.0, min(200.0, 0.85 * 96.0 * k))
        except Exception:
            dpi = 100.0
        self.fig = Figure(figsize=(9, 4), dpi=dpi)
        self.canvas = FigureCanvasTkAgg(self.fig, master=der)
        tb = NavigationToolbar2Tk(self.canvas, der, pack_toolbar=False)
        tb.update()
        tb.pack(fill="x")
        # ancho pedido chico: el grafico igual ocupa todo; si pide mucho, el panel
        # de la lista no se puede acomodar
        self.canvas.get_tk_widget().configure(width=300, height=200)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        # ancho inicial de la lista: se fija cuando el panel ya tiene su ancho real
        # (fijarlo antes, con la pestaña sin dibujar, lo dejaba en cualquier lado)
        self._sash_ok = False

        def _sash(e, pan=pan):
            if not self._sash_ok and e.width > 400:
                self._sash_ok = True
                self.raiz.after_idle(lambda w=e.width: pan.sashpos(0, min(px(330), int(0.4 * w))))
        pan.bind("<Configure>", _sash, add="+")
        self._carpetas: list[Path] = []
        self.refrescar()

    # ---------------- lista ----------------
    def refrescar(self):
        self._carpetas = visor.listar_carpetas(self.base)
        self._llenar()
        self.estado.config(text=f"{len(self._carpetas)} resultados en {self.base}")

    def _llenar(self):
        q = self.v_buscar.get().lower().strip()
        sel = set(self.lista.selection())
        self.lista.delete(*self.lista.get_children())
        for c in self._carpetas:
            if not q or q in c.name.lower() or c.name in sel:
                self.lista.insert("", "end", iid=c.name, text=c.name)
        for s in sel:
            if self.lista.exists(s):
                self.lista.selection_add(s)

    def _elegir_base(self):
        from tkinter import filedialog
        r = filedialog.askdirectory(title="Carpeta con resultados", initialdir=str(self.base))
        if r:
            self.base = Path(r)
            self.refrescar()

    # ---------------- comparar ----------------
    def comparar(self):
        from tkinter import messagebox
        nombres = list(self.lista.selection())
        if len(nombres) < 2:
            messagebox.showinfo("Comparar", "Elegí al menos 2 resultados (Ctrl + clic).")
            return
        self.estado.config(text=f"Leyendo {len(nombres)} resultados...")
        carpetas = [self.base / n for n in nombres]

        def trabajo():
            rs, errores = [], []
            for c in carpetas:
                try:
                    rs.append(visor.leer_resultado(c))
                except Exception as e:
                    errores.append(f"{c.name}: {e}")
            self.raiz.after(0, lambda: self._mostrar(rs, errores))
        threading.Thread(target=trabajo, daemon=True).start()

    def _mostrar(self, rs, errores):
        self.rs = rs
        self.titulo.config(text=f"Comparando {len(rs)} resultados")
        filas = visor.tabla_comparar(rs)
        cols = ["m"] + [f"r{i}" for i in range(len(rs))]
        self.tabla.configure(columns=cols, height=len(filas))
        self.tabla.heading("m", text="")
        self.tabla.column("m", width=self._px(190), stretch=False, anchor="w")
        for i, r in enumerate(rs):
            self.tabla.heading(f"r{i}", text=f"{i + 1} · {r.carpeta.name}")
            self.tabla.column(f"r{i}", width=self._px(230), stretch=True, anchor="w")
        self.tabla.delete(*self.tabla.get_children())
        for a, vals in filas:
            self.tabla.insert("", "end", values=[a] + vals)
        self._dibujar()
        txt = "Listo." if not errores else "No pude leer: " + "; ".join(errores)
        if any(visor.ic_amplitud(r) is None and r.fila.get("reportable") for r in rs):
            txt += "  Punto hueco = resultado anterior al IC 95 % (se agrega al rehacer el paso 2)."
        self.estado.config(text=txt)

    def _dibujar(self):
        self.fig.clear()
        rs = self.rs
        if not rs:
            self.canvas.draw_idle()
            return
        gs = self.fig.add_gridspec(1, 3)
        ax = self.fig.add_subplot(gs[0, :2])
        ax2 = self.fig.add_subplot(gs[0, 2])
        for i, r in enumerate(rs):
            col = PALETA[i % len(PALETA)]
            lag, y, n = visor.promedio_para_dibujar(r)
            rep = bool(r.fila.get("reportable"))
            if lag is not None:
                grupo = r.fila.get("amplitud_grupo") or "todas"
                lab = f"{i + 1} · {r.carpeta.name} (n={n}, {grupo if rep else 'NO reportable'})"
                ax.plot(lag, y, color=col, lw=1.5 if rep else 1.0, ls="-" if rep else "--", label=lab)
            amp = r.fila.get("amplitud_pct") if rep else None
            if amp is not None:
                ic = visor.ic_amplitud(r)
                if ic:
                    ax2.errorbar([i], [amp], yerr=[[amp - ic[0]], [ic[1] - amp]], fmt="o",
                                 color=col, capsize=4, ms=6)
                else:
                    ax2.plot([i], [amp], "o", mfc="white", color=col, ms=6)
            else:
                ax2.text(i, 0, "NO\nrep.", ha="center", va="bottom", fontsize=7, color="gray")
        ax.axhline(0, color="#999", lw=0.5)
        ax.axvline(0, color="#bbb", lw=0.5)
        ax.set_xlabel("s desde el pico")
        ax.set_ylabel("% del grosor en reposo")
        ax.set_title("Contracción promedio (dibujo, alineada en el pico)", fontsize=9)

        ax.legend(fontsize=7, loc="upper left")
        ax.grid(alpha=0.25)
        ax2.set_xticks(range(len(rs)))
        ax2.set_xticklabels([str(i + 1) for i in range(len(rs))])
        ax2.set_xlim(-0.6, len(rs) - 0.4)
        ax2.set_ylim(bottom=0)
        ax2.set_xlabel("resultado (orden de la tabla)")
        ax2.set_ylabel("amplitud (% del grosor)")
        ax2.set_title("Amplitud informada ± IC 95 %\n(punto hueco: resultado sin IC)", fontsize=9)
        ax2.grid(alpha=0.25, axis="y")
        self.fig.tight_layout()
        self.canvas.draw_idle()

    # ---------------- guardar ----------------
    def _guardar_tabla(self):
        if not self.rs:
            return
        from tkinter import filedialog
        f = filedialog.asksaveasfilename(defaultextension=".xlsx", initialdir=str(self.base),
                                         initialfile="comparacion.xlsx",
                                         filetypes=[("Excel", "*.xlsx"), ("CSV", "*.csv")])
        if f:
            visor.guardar_tabla_comparar(self.rs, Path(f))
            self.estado.config(text=f"Tabla guardada en {f}")

    def _guardar_png(self):
        if not self.rs:
            return
        from tkinter import filedialog
        f = filedialog.asksaveasfilename(defaultextension=".png", initialdir=str(self.base),
                                         initialfile="comparacion.png", filetypes=[("PNG", "*.png")])
        if f:
            self.fig.savefig(f, dpi=150)
            self.estado.config(text=f"Gráfico guardado en {f}")
