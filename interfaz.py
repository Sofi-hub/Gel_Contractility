"""
interfaz.py
-----------
Ventana simple para correr el analisis sin escribir comandos.

    python interfaz.py        (o doble clic en Analizar.bat)

No hace ningun calculo propio: arma y corre los MISMOS comandos de siempre
(main.py, scripts/contraction_report.py, scripts/motion_check.py), uno detras
del otro, y muestra en vivo lo que imprimen. Los numeros son identicos a
correrlos desde la consola.

Pasos (se pueden elegir por separado o todos juntos):
  1. Medir el gel        -> main.py           -> <carpeta>/serie_temporal_<video>.xlsx
  2. Buscar contracciones-> contraction_report-> <carpeta>/contracciones_<carpeta>.xlsx
  3. Confirmar (2.o metodo) -> motion_check   -> <carpeta>/movimiento_<video>.xlsx
  4. Informe               -> informe.py      -> <carpeta>/informe_<carpeta>.html
Los pasos 2 y 3 usan el serie_temporal de la carpeta de resultados, asi
que se pueden correr despues sin repetir el paso 1. Tambien aceptan el
nombre viejo (serie_temporal.xlsx, resultados anteriores al 2026-10-08).

Carpeta entera: si se elige "o una carpeta entera", se corren los pasos marcados
sobre TODOS sus videos (scripts/procesar_carpeta.py, que usa estas mismas
funciones) y se arma una tabla resumen, una fila por video. "Guardar resultados
en" es entonces la carpeta madre (una subcarpeta por video).

Arrastrar el video a la ventana necesita `pip install tkinterdnd2`. Sin eso,
todo funciona igual con el boton "Elegir...".
"""

from __future__ import annotations

import os
import queue
import subprocess
import sys
import threading
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
sys.path.insert(0, str(RAIZ))
from src.output_paths import buscar_serie  # noqa: E402  (solo pathlib)


# --------------------------------------------------------------------------
# Logica (sin ventana): se puede probar sola.
# --------------------------------------------------------------------------
def leer_configuracion(ruta: Path | None = None) -> dict:
    """configuracion.ini (C3): con que arranca la ventana. Si no esta o tiene un
    error, los valores de siempre. No hay parametros del analisis a proposito."""
    import configparser
    cfg = {"frecuencia": "", "pasos": {1, 2, 4}, "detalle": False, "tema": "claro", "zoom": 1.0,
           "carpeta_resultados": RAIZ / "data" / "processed_data"}
    ruta = ruta or RAIZ / "configuracion.ini"
    try:
        cp = configparser.ConfigParser(inline_comment_prefixes=(";", "#"))
        cp.read(ruta, encoding="utf-8")
        s = cp["ventana"] if cp.has_section("ventana") else {}
        if s.get("frecuencia", "").strip():
            cfg["frecuencia"] = s.get("frecuencia").strip()
        if s.get("pasos", "").strip():
            cfg["pasos"] = {int(x) for x in s.get("pasos").replace(",", " ").split()
                            if x in {"1", "2", "3", "4"}}
        cfg["detalle"] = s.get("detalle", "no").strip().lower() in ("si", "sí", "yes", "1", "true")
        try:
            z = float(s.get("tamano_letra", "1").replace(",", ".") or 1)
            cfg["zoom"] = min(2.5, max(0.6, z))
        except ValueError:
            pass
        if s.get("tema", "").strip().lower() in ("claro", "oscuro"):
            cfg["tema"] = s.get("tema").strip().lower()
        if s.get("carpeta_resultados", "").strip():
            c = Path(s.get("carpeta_resultados").strip())
            cfg["carpeta_resultados"] = c if c.is_absolute() else RAIZ / c
    except Exception as e:   # un ini roto no impide abrir la ventana
        print(f"AVISO: no pude leer {ruta} ({e}); uso los valores de siempre.")
    return cfg


CONFIG = leer_configuracion()


TEMA_ERROR = {"txt": ""}


def aplicar_tema(root, oscuro: bool = False) -> bool:
    """Tema moderno (sv-ttk, opcional: pip install sv-ttk). Sin el, el de siempre.
    Si falla, el motivo queda en TEMA_ERROR y la ventana lo muestra (antes se
    callaba y no se sabia por que se veia igual)."""
    try:
        import sv_ttk
        sv_ttk.set_theme("dark" if oscuro else "light", root)
        TEMA_ERROR["txt"] = ""
        return True
    except Exception as e:
        TEMA_ERROR["txt"] = f"{type(e).__name__}: {e} (python: {sys.executable})"
        return False


def carpeta_por_defecto(video: str) -> Path:
    return Path(CONFIG["carpeta_resultados"]) / Path(video).stem


def armar_comandos(video: str, carpeta: str, paso1: bool, paso2: bool, paso3: bool,
                   frecuencias: str = "",
                   verbose: bool = False, paso4: bool = False) -> list[tuple[str, list[str]]]:
    """Devuelve [(titulo, comando), ...] o levanta ValueError con un mensaje claro."""
    py = sys.executable
    carpeta = Path(carpeta) if carpeta else (carpeta_por_defecto(video) if video else None)
    if not (paso1 or paso2 or paso3 or paso4):
        raise ValueError("Marca al menos un paso.")
    if (paso1 or paso3) and not video:
        raise ValueError("Falta elegir el video.")
    if video and not Path(video).is_file():
        raise ValueError(f"No encuentro el video:\n{video}")
    if carpeta is None:
        raise ValueError("Falta elegir la carpeta de resultados.")
    if paso1:   # todavia no existe: se sabe como se va a llamar
        serie = carpeta / f"serie_temporal_{Path(video).stem}.xlsx"
    else:       # nombre nuevo o, en resultados viejos, serie_temporal.xlsx
        serie = buscar_serie(carpeta)
    if (paso2 or paso3 or paso4) and not paso1 and not serie.is_file():
        raise ValueError(f"Para los pasos 2, 3 y 4 sin el paso 1 tiene que existir:\n{serie}\n"
                         f"Corre primero el paso 1, o elegi la carpeta donde ya esta.")
    freqs = frecuencias.replace(",", " ").split()
    for f in freqs:
        try:
            float(f)
        except ValueError:
            raise ValueError(f"Frecuencia no valida: '{f}'. Ejemplo: 0.1  (o 0.1 0.2)")
    extra = ["--verbose"] if verbose else []

    cmds = []
    if paso1:
        c = [py, "-u", str(RAIZ / "main.py"), "--video", str(video),
             "--output-dir", str(carpeta), "--base-tiempo", "pts"]
        cmds.append(("Paso 1: medir el gel en cada fotograma", c + extra))
    if paso2:
        c = [py, "-u", str(RAIZ / "scripts" / "contraction_report.py"), "--input", str(serie)]
        if freqs:
            c += ["--frecuencia-estimulo"] + freqs
        cmds.append(("Paso 2: buscar contracciones", c + extra))
    if paso3:
        c = [py, "-u", str(RAIZ / "scripts" / "motion_check.py"), "--video", str(video),
             "--serie", str(serie)]
        cmds.append(("Paso 3: confirmar con el segundo metodo", c + extra))
    if paso4:
        c = [py, "-u", str(RAIZ / "scripts" / "informe.py"), "--carpeta", str(carpeta)]
        cmds.append(("Paso 4: armar el informe", c))
    return cmds


def armar_comando_carpeta(carpeta_videos: str, salida: str, paso1: bool, paso2: bool,
                          paso3: bool, frecuencias: str = "",
                          verbose: bool = False, paso4: bool = False) -> list[tuple[str, list[str]]]:
    """Una CARPETA entera: corre scripts/procesar_carpeta.py, que para cada video
    usa armar_comandos/correr (lo mismo de arriba) y arma la tabla resumen."""
    if not (paso1 or paso2 or paso3 or paso4):
        raise ValueError("Marca al menos un paso.")
    if not carpeta_videos or not Path(carpeta_videos).is_dir():
        raise ValueError(f"No encuentro la carpeta de videos:\n{carpeta_videos}")
    for f in frecuencias.replace(",", " ").split():
        try:
            float(f)
        except ValueError:
            raise ValueError(f"Frecuencia no valida: '{f}'. Ejemplo: 0.1  (o 0.1 0.2)")
    pasos = " ".join(str(n) for n, v in ((1, paso1), (2, paso2), (3, paso3), (4, paso4)) if v)
    c = [sys.executable, "-u", str(RAIZ / "scripts" / "procesar_carpeta.py"),
         "--carpeta", str(carpeta_videos), "--pasos", pasos]
    if salida:
        c += ["--salida", str(salida)]
    if frecuencias.strip():
        c += ["--frecuencia-estimulo", frecuencias.strip()]
    if verbose:
        c.append("--verbose")
    return [("Carpeta entera: todos los videos y una tabla resumen", c)]


def correr(cmds, escribir, detener=lambda: False) -> bool:
    """Corre los comandos en orden y pasa cada linea a `escribir`. Para si uno falla."""
    env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUNBUFFERED="1",
               MPLBACKEND="Agg")
    for titulo, c in cmds:
        escribir(f"\n##### {titulo} #####\n")
        p = subprocess.Popen(c, cwd=str(RAIZ), stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT, text=True, encoding="utf-8",
                             errors="replace", env=env,
                             creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        for linea in p.stdout:
            escribir(linea)
            if detener():
                p.terminate()
                escribir("\n*** Detenido por el usuario ***\n")
                return False
        if p.wait() != 0:
            escribir(f"\n*** ERROR en '{titulo}' (codigo {p.returncode}). "
                     f"Lo de arriba dice que paso. No se corren los pasos siguientes. ***\n")
            return False
    escribir("\n##### LISTO #####\n")
    return True


# --------------------------------------------------------------------------
# Ventana
# --------------------------------------------------------------------------
def activar_nitidez_windows():
    """Sin esto, Windows agranda la ventana como una imagen en pantallas con
    escala (125 %, 150 %...) y todo se ve borroso. Con esto Tk dibuja a la
    resolucion real. En otros sistemas no hace nada."""
    if not sys.platform.startswith("win"):
        return
    try:
        import ctypes
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)   # por monitor
        except Exception:
            ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass


_TAMANOS_ORIGINALES: dict = {}


def escalar_letras(root, zoom: float = 1.0) -> float:
    """Con la nitidez activada, las letras definidas en PIXELES (las del tema
    sv-ttk) quedan chicas en pantallas con escala 125-150 %. Se agrandan segun la
    densidad real de la pantalla (96 = 100 %) y el `zoom` de configuracion.ini.
    Las definidas en puntos ya escalan solas; a esas solo se les aplica el zoom.
    Se guarda el tamano original para no agrandar dos veces."""
    import tkinter.font as tkfont
    try:
        escala = float(root.winfo_fpixels("1i")) / 96.0
    except Exception:
        escala = 1.0
    for nombre in tkfont.names(root):
        try:
            f = tkfont.nametofont(nombre, root)
        except Exception:
            continue
        orig = _TAMANOS_ORIGINALES.setdefault(nombre, int(f.cget("size")))
        if orig < 0:      # pixeles
            f.configure(size=-max(1, round(-orig * escala * zoom)))
        elif orig > 0:    # puntos
            f.configure(size=max(1, round(orig * zoom)))
    return escala


def main():
    activar_nitidez_windows()
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox
    from tkinter.scrolledtext import ScrolledText

    try:
        from tkinterdnd2 import TkinterDnD, DND_FILES
        root = TkinterDnD.Tk()
        hay_dnd = True
    except Exception:
        root = tk.Tk()
        hay_dnd = False

    root.title("Contractilidad de geles")
    # tamano segun la pantalla (con la nitidez activada, los px son reales)
    sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
    root.geometry(f"{int(sw * 0.72)}x{int(sh * 0.82)}+{int(sw * 0.14)}+{int(sh * 0.05)}")
    root.minsize(int(sw * 0.5), int(sh * 0.55))
    tema = {"oscuro": CONFIG.get("tema") == "oscuro"}
    hay_tema = aplicar_tema(root, tema["oscuro"])
    root._factor_ui = escalar_letras(root, CONFIG.get("zoom", 1.0)) * CONFIG.get("zoom", 1.0)

    fuente = "Segoe UI" if sys.platform.startswith("win") else "TkDefaultFont"

    def estilos():
        # se vuelven a aplicar al cambiar de tema (el tema nuevo los borra)
        st = ttk.Style(root)
        z = CONFIG.get("zoom", 1.0)
        st.configure("Titulo.TLabel", font=(fuente, round(17 * z), "bold"))
        st.configure("Sub.TLabel", font=(fuente, round(10 * z)), foreground="#7a8490")
        st.configure("Seccion.TLabel", font=(fuente, round(11 * z), "bold"))
        st.configure("Ayuda.TLabel", font=(fuente, round(9 * z)), foreground="#7a8490")
    estilos()

    cab = ttk.Frame(root, padding=(18, 12, 18, 6))
    cab.pack(fill="x")
    ttk.Label(cab, text="Contractilidad de geles", style="Titulo.TLabel").pack(side="left")
    sub = ttk.Label(cab, text="", style="Sub.TLabel")
    sub.pack(side="left", padx=(14, 0), pady=(6, 0))

    def actualizar_sub():
        try:
            import visor
            n = len(visor.listar_carpetas(CONFIG["carpeta_resultados"]))
            sub.config(text=f"{n} resultados guardados  ·  medición por bordes del gel")
        except Exception:
            sub.config(text="medición por bordes del gel")
    actualizar_sub()

    nb = ttk.Notebook(root)
    nb.pack(fill="both", expand=True, padx=12, pady=(0, 10))
    tab1 = ttk.Frame(nb, padding=14)
    tab2 = ttk.Frame(nb)
    tab3 = ttk.Frame(nb)
    nb.add(tab1, text="  Analizar  ")
    nb.add(tab2, text="  Resultados  ")
    nb.add(tab3, text="  Comparar  ")
    visor_ref: dict = {}

    def pestana_resultados():
        # se arma la primera vez que se abre: asi la ventana arranca rapido
        if "v" not in visor_ref:
            import visor
            visor_ref["v"] = visor.PestanaResultados(tab2, CONFIG["carpeta_resultados"],
                                                     oscuro=tema["oscuro"])
            visor_ref["v"].atajos(activa=lambda: nb.index("current") == 1)
        return visor_ref["v"]

    def pestana_comparar():
        if "c" not in visor_ref:
            import comparar
            visor_ref["c"] = comparar.PestanaComparar(tab3, CONFIG["carpeta_resultados"])
        return visor_ref["c"]

    def al_cambiar_pestana(_e=None):
        i = nb.index("current")
        if i == 1:
            pestana_resultados()
        elif i == 2:
            pestana_comparar()

    nb.bind("<<NotebookTabChanged>>", al_cambiar_pestana)
    # atajos generales: Ctrl+1/2/3 cambian de pestaña
    for n in (1, 2, 3):
        root.bind(f"<Control-Key-{n}>", lambda _e, n=n: nb.select(n - 1))

    v_video = tk.StringVar()
    v_carpeta = tk.StringVar()
    v_freq = tk.StringVar(value=CONFIG["frecuencia"])
    v_lote = tk.StringVar()
    v_p1, v_p2, v_p3, v_p4 = (tk.BooleanVar(value=n in CONFIG["pasos"]) for n in (1, 2, 3, 4))
    v_verbose = tk.BooleanVar(value=CONFIG["detalle"])
    carpeta_tocada = {"si": False}

    def poner_video(ruta: str):
        ruta = ruta.strip().strip("{}").strip('"')
        v_video.set(ruta)
        if ruta and not carpeta_tocada["si"]:
            v_carpeta.set(str(carpeta_por_defecto(ruta)))

    def elegir_video():
        r = filedialog.askopenfilename(
            title="Elegir video", initialdir=str(RAIZ / "data" / "raw_videos"),
            filetypes=[("Videos", "*.mp4 *.avi *.mov"), ("Todos", "*.*")])
        if r:
            poner_video(r)

    def elegir_lote():
        r = filedialog.askdirectory(title="Carpeta con videos",
                                    initialdir=str(RAIZ / "data" / "raw_videos"))
        if r:
            v_lote.set(r)
            if not carpeta_tocada["si"]:
                v_carpeta.set(str(CONFIG["carpeta_resultados"]))

    def elegir_carpeta():
        r = filedialog.askdirectory(title="Carpeta de resultados",
                                    initialdir=str(CONFIG["carpeta_resultados"]))
        if r:
            carpeta_tocada["si"] = True
            v_carpeta.set(r)

    pad = {"padx": 6, "pady": 4}

    def tarjeta(padre, titulo):
        f = ttk.Frame(padre)
        f.pack(fill="x", pady=(0, 12))
        ttk.Label(f, text=titulo, style="Seccion.TLabel").pack(anchor="w", pady=(0, 4))
        c = ttk.Frame(f, padding=12, relief="solid", borderwidth=1) if not hay_tema \
            else ttk.LabelFrame(f, padding=12, text="")
        c.pack(fill="x")
        return c

    # --- 1. que analizar ---
    frm = tarjeta(tab1, "Qué analizar")
    frm.columnconfigure(1, weight=1)
    ttk.Label(frm, text="Video").grid(row=0, column=0, sticky="w", padx=(0, 10))
    e_video = ttk.Entry(frm, textvariable=v_video)
    e_video.grid(row=0, column=1, sticky="ew", pady=3)
    ttk.Button(frm, text="Elegir…", command=elegir_video).grid(row=0, column=2, padx=(8, 0))
    ttk.Label(frm, style="Ayuda.TLabel",
              text=("o arrastrá el video a la ventana" if hay_dnd else
                    "para arrastrar el archivo: pip install tkinterdnd2")
              ).grid(row=1, column=1, sticky="w", pady=(0, 6))
    ttk.Label(frm, text="o una carpeta").grid(row=2, column=0, sticky="w", padx=(0, 10))
    e_lote = ttk.Entry(frm, textvariable=v_lote)
    e_lote.grid(row=2, column=1, sticky="ew", pady=3)
    ttk.Button(frm, text="Elegir…", command=elegir_lote).grid(row=2, column=2, padx=(8, 0))
    ttk.Label(frm, style="Ayuda.TLabel",
              text="se procesan todos sus videos, una subcarpeta por video, y una tabla resumen"
              ).grid(row=3, column=1, sticky="w", pady=(0, 6))
    ttk.Label(frm, text="Guardar en").grid(row=4, column=0, sticky="w", padx=(0, 10))
    e_carp = ttk.Entry(frm, textvariable=v_carpeta)
    e_carp.grid(row=4, column=1, sticky="ew", pady=3)
    e_carp.bind("<Key>", lambda _e: carpeta_tocada.update(si=True))
    ttk.Button(frm, text="Elegir…", command=elegir_carpeta).grid(row=4, column=2, padx=(8, 0))

    # --- 2. pasos y opciones, lado a lado ---
    medio = ttk.Frame(tab1)
    medio.pack(fill="x")
    col1 = ttk.Frame(medio)
    col1.pack(side="left", fill="both", expand=True, padx=(0, 6))
    col2 = ttk.Frame(medio)
    col2.pack(side="left", fill="both", expand=True, padx=(6, 0))
    pasos = tarjeta(col1, "Pasos")
    for var, txt, ayuda in (
            (v_p1, "1 · Medir el gel en cada fotograma", "unos minutos"),
            (v_p2, "2 · Buscar contracciones", "segundos"),
            (v_p3, "3 · Confirmar con un segundo método", "opcional, unos minutos"),
            (v_p4, "4 · Armar el informe", "una página HTML para mandar")):
        f = ttk.Frame(pasos)
        f.pack(fill="x", pady=2)
        ttk.Checkbutton(f, variable=var, text=txt).pack(side="left")
        ttk.Label(f, text=ayuda, style="Ayuda.TLabel").pack(side="left", padx=8)
    opc = tarjeta(col2, "Opciones")
    fila = ttk.Frame(opc)
    fila.pack(fill="x", pady=2)
    ttk.Label(fila, text="Frecuencia del estimulador (Hz)").pack(side="left")
    ttk.Entry(fila, textvariable=v_freq, width=10).pack(side="left", padx=8)
    ttk.Label(opc, text="vacío = no se sabe   ·   ej: 0.1   o   0.1 0.2",
              style="Ayuda.TLabel").pack(anchor="w", pady=(0, 6))
    ttk.Checkbutton(opc, variable=v_verbose,
                    text="Mostrar detalle técnico (--verbose)").pack(anchor="w", pady=2)

    botones = ttk.Frame(tab1)
    botones.pack(fill="x", pady=(2, 10))
    b_correr = ttk.Button(botones, text="  Analizar  ",
                          style="Accent.TButton" if hay_tema else "TButton")
    b_correr.pack(side="left")
    b_parar = ttk.Button(botones, text="Detener", state="disabled")
    b_parar.pack(side="left", padx=6)
    b_abrir = ttk.Button(botones, text="Abrir carpeta de resultados")
    b_abrir.pack(side="left", padx=6)
    b_ver = ttk.Button(botones, text="Ver resultados", state="disabled")
    b_ver.pack(side="left", padx=6)
    estado = ttk.Label(botones, text="")
    estado.pack(side="left", padx=12)
    if hay_tema:
        def cambiar_tema():
            tema["oscuro"] = not tema["oscuro"]
            aplicar_tema(root, tema["oscuro"])
            escalar_letras(root, CONFIG.get("zoom", 1.0))
            estilos()
            colores_salida()
        ttk.Button(botones, text="Claro / oscuro", command=cambiar_tema).pack(side="right")
    ultimo = {"carpeta": None}

    ttk.Label(tab1, text="Salida", style="Seccion.TLabel").pack(anchor="w", pady=(0, 4))
    salida = ScrolledText(tab1, font=("Consolas", round(10 * CONFIG.get("zoom", 1.0))), wrap="word", relief="flat",
                          borderwidth=0, padx=10, pady=8)
    salida.pack(fill="both", expand=True)

    def colores_salida():
        if tema["oscuro"] and hay_tema:
            salida.configure(background="#1c1c1c", foreground="#e6e6e6", insertbackground="#e6e6e6")
        else:
            salida.configure(background="#ffffff", foreground="#1b1f24", insertbackground="#1b1f24")
    colores_salida()
    if not hay_tema:
        salida.insert("end", "(Tema moderno no activo: " + (TEMA_ERROR["txt"] or "?")
                      + ". La ventana funciona igual.)\n")
    salida.tag_config("aviso", foreground="#b03a2e")
    salida.tag_config("titulo", foreground="#1f4e8c", font=("Consolas", 9, "bold"))

    if hay_dnd:
        root.drop_target_register(DND_FILES)
        root.dnd_bind("<<Drop>>", lambda ev: poner_video(root.tk.splitlist(ev.data)[0]))

    cola: queue.Queue = queue.Queue()
    parar = {"si": False}

    def escribir(linea: str):
        cola.put(linea)

    def vaciar_cola():
        try:
            while True:
                ln = cola.get_nowait()
                if ln is None:
                    terminar()
                    continue
                u = ln.upper()
                tag = ("titulo" if ln.startswith("\n#####") or ln.startswith("=====")
                       else "aviso" if ("AVISO" in u or "NO REPORTABLE" in u or "ERROR" in u)
                       else None)
                salida.insert("end", ln, tag)
                salida.see("end")
        except queue.Empty:
            pass
        root.after(100, vaciar_cola)

    def terminar():
        b_correr.config(state="normal")
        b_parar.config(state="disabled")
        estado.config(text="Terminado")
        actualizar_sub()
        if ultimo["carpeta"] is not None:
            b_ver.config(state="normal")
            if "v" in visor_ref:          # que la lista de Resultados incluya lo nuevo
                visor_ref["v"].refrescar()
            if "c" in visor_ref:
                visor_ref["c"].refrescar()

    def ver_resultados():
        nb.select(1)
        v = pestana_resultados()
        c = ultimo["carpeta"]
        if c is not None:
            if Path(c).parent.resolve() != v.base.resolve() and Path(c).is_dir():
                v.base = Path(c).parent
            v.refrescar(elegir=Path(c).name)
    b_ver.config(command=ver_resultados)

    def analizar():
        lote = v_lote.get().strip().strip('"')
        try:
            if lote:
                cmds = armar_comando_carpeta(lote, v_carpeta.get().strip(), v_p1.get(),
                                             v_p2.get(), v_p3.get(), v_freq.get(),
                                             v_verbose.get(), v_p4.get())
            else:
                cmds = armar_comandos(v_video.get().strip().strip('"'), v_carpeta.get().strip(),
                                      v_p1.get(), v_p2.get(), v_p3.get(), v_freq.get(),
                                      v_verbose.get(), v_p4.get())
        except ValueError as e:
            messagebox.showwarning("Falta algo", str(e))
            return
        if lote and not v_carpeta.get().strip():
            v_carpeta.set(str(CONFIG["carpeta_resultados"]))
        elif not v_carpeta.get().strip():
            v_carpeta.set(str(carpeta_por_defecto(v_video.get())))
        # que abrir "Ver resultados" al terminar: el video, o la primera carpeta del lote
        if lote:
            vids = sorted(q for q in Path(lote).iterdir()
                          if q.suffix.lower() in (".mp4", ".avi", ".mov"))
            base = Path(v_carpeta.get().strip())
            ultimo["carpeta"] = base / vids[0].stem if vids else None
        else:
            ultimo["carpeta"] = Path(v_carpeta.get().strip())
        b_ver.config(state="disabled")
        salida.delete("1.0", "end")
        b_correr.config(state="disabled")
        b_parar.config(state="normal")
        estado.config(text="Corriendo... (no cierres la ventana)")
        parar["si"] = False

        def trabajo():
            try:
                correr(cmds, escribir, lambda: parar["si"])
            finally:
                cola.put(None)
        threading.Thread(target=trabajo, daemon=True).start()

    def abrir():
        c = Path(v_carpeta.get().strip() or ".")
        if not c.is_dir():
            messagebox.showinfo("Carpeta", f"Todavia no existe:\n{c}")
            return
        if sys.platform.startswith("win"):
            os.startfile(str(c))
        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(c)])
        else:
            subprocess.Popen(["xdg-open", str(c)])

    b_correr.config(command=analizar)
    root.bind("<Control-Return>", lambda _e: (analizar() if nb.index("current") == 0
                                              and str(b_correr["state"]) != "disabled" else None))
    ttk.Label(tab1, style="Ayuda.TLabel",
              text="Atajos: Ctrl+Enter analizar · Ctrl+1/2/3 pestañas · en Resultados: ← → contracción, "
                   "D marcar dudosa, F fotograma, Ctrl+C copiar ficha, Ctrl+F buscar, F5 actualizar, "
                   "Ctrl+S guardar gráfico").pack(anchor="w", pady=(6, 0))
    b_parar.config(command=lambda: parar.update(si=True))
    b_abrir.config(command=abrir)
    root.after(100, vaciar_cola)
    root.mainloop()


if __name__ == "__main__":
    main()
