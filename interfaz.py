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
    cfg = {"frecuencia": "", "pasos": {1, 2, 4}, "detalle": False,
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
        if s.get("carpeta_resultados", "").strip():
            c = Path(s.get("carpeta_resultados").strip())
            cfg["carpeta_resultados"] = c if c.is_absolute() else RAIZ / c
    except Exception as e:   # un ini roto no impide abrir la ventana
        print(f"AVISO: no pude leer {ruta} ({e}); uso los valores de siempre.")
    return cfg


CONFIG = leer_configuracion()


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
def main():
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

    root.title("Contractilidad de geles - analisis")
    root.geometry("980x720")

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
    frm = ttk.Frame(root)
    frm.pack(fill="x", **pad)
    frm.columnconfigure(1, weight=1)

    ttk.Label(frm, text="Video:").grid(row=0, column=0, sticky="w")
    e_video = ttk.Entry(frm, textvariable=v_video)
    e_video.grid(row=0, column=1, sticky="ew", **pad)
    ttk.Button(frm, text="Elegir...", command=elegir_video).grid(row=0, column=2, **pad)
    ttk.Label(frm, foreground="gray",
              text=("(o arrastra el video a esta ventana)" if hay_dnd else
                    "(para arrastrar el archivo: pip install tkinterdnd2)")
              ).grid(row=1, column=1, sticky="w")

    ttk.Label(frm, text="o una carpeta entera:").grid(row=3, column=0, sticky="w")
    e_lote = ttk.Entry(frm, textvariable=v_lote)
    e_lote.grid(row=3, column=1, sticky="ew", **pad)
    ttk.Button(frm, text="Elegir...", command=elegir_lote).grid(row=3, column=2, **pad)
    ttk.Label(frm, foreground="gray",
              text=("(si hay una carpeta, se procesan TODOS sus videos y se arma una tabla "
                    "resumen; los resultados van a una subcarpeta por video)")
              ).grid(row=4, column=1, sticky="w")

    ttk.Label(frm, text="Guardar resultados en:").grid(row=2, column=0, sticky="w")
    e_carp = ttk.Entry(frm, textvariable=v_carpeta)
    e_carp.grid(row=2, column=1, sticky="ew", **pad)
    e_carp.bind("<Key>", lambda _e: carpeta_tocada.update(si=True))
    ttk.Button(frm, text="Elegir...", command=elegir_carpeta).grid(row=2, column=2, **pad)

    pasos = ttk.LabelFrame(root, text="Que correr (por separado o todo junto)")
    pasos.pack(fill="x", **pad)
    ttk.Checkbutton(pasos, variable=v_p1,
                    text="1. Medir el gel en cada fotograma (serie temporal; tarda unos minutos)"
                    ).pack(anchor="w")
    ttk.Checkbutton(pasos, variable=v_p2,
                    text="2. Buscar contracciones (segundos; usa la serie de la carpeta de resultados)"
                    ).pack(anchor="w")
    ttk.Checkbutton(pasos, variable=v_p3,
                    text="3. Confirmar con el segundo metodo (opcional; tarda unos minutos)"
                    ).pack(anchor="w")
    ttk.Checkbutton(pasos, variable=v_p4,
                    text="4. Armar el informe (una pagina HTML para mandar; segundos)"
                    ).pack(anchor="w")

    opc = ttk.LabelFrame(root, text="Opciones")
    opc.pack(fill="x", **pad)
    fila = ttk.Frame(opc)
    fila.pack(anchor="w")
    ttk.Label(fila, text="Frecuencia del estimulador (Hz, vacio = no se):").pack(side="left")
    ttk.Entry(fila, textvariable=v_freq, width=12).pack(side="left", padx=6)
    ttk.Label(fila, foreground="gray", text="ej: 0.1   o   0.1 0.2").pack(side="left")
    ttk.Checkbutton(opc, variable=v_verbose,
                    text="Mostrar detalle tecnico (--verbose)").pack(anchor="w")

    botones = ttk.Frame(root)
    botones.pack(fill="x", **pad)
    b_correr = ttk.Button(botones, text="Analizar")
    b_correr.pack(side="left")
    b_parar = ttk.Button(botones, text="Detener", state="disabled")
    b_parar.pack(side="left", padx=6)
    b_abrir = ttk.Button(botones, text="Abrir carpeta de resultados")
    b_abrir.pack(side="left", padx=6)
    estado = ttk.Label(botones, text="")
    estado.pack(side="left", padx=12)

    salida = ScrolledText(root, font=("Consolas", 9), wrap="word")
    salida.pack(fill="both", expand=True, **pad)
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
    b_parar.config(command=lambda: parar.update(si=True))
    b_abrir.config(command=abrir)
    root.after(100, vaciar_cola)
    root.mainloop()


if __name__ == "__main__":
    main()
