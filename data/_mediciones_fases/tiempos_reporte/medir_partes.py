"""Cuanto tarda cada parte de contraction_report.py (2026-10-10).

    python data/_mediciones_fases/tiempos_reporte/medir_partes.py [carpeta] [procesos...]

Por defecto: Video_613 con 1, 2 y 4 procesos. Corre el reporte completo (escribe en una
carpeta temporal, no toca processed_data) y separa: cargar librerias, leer el Excel,
el analisis (y dentro, el Monte Carlo del tren y el arranque de los procesos), los
graficos y escribir el Excel. El resultado del analisis no cambia con los procesos.
"""
import sys, time, tempfile
T0 = time.perf_counter()
from pathlib import Path
RAIZ = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(RAIZ), str(RAIZ / "scripts"), str(RAIZ / "tests")]
import contraction_report as cr
import pandas as pd
from src import rhythm_split as rs
import referencia as ref
from src.output_paths import buscar_serie
T_IMPORT = time.perf_counter() - T0

tiempos = {}

def medir(nombre, f):
    def g(*a, **k):
        t = time.perf_counter()
        try:
            return f(*a, **k)
        finally:
            tiempos[nombre] = tiempos.get(nombre, 0.0) + time.perf_counter() - t
    return g

cr._leer = medir("leer el Excel", cr._leer)
cr.analizar = medir("analisis (total)", cr.analizar)
rs._z_nulo = medir("  dentro: Monte Carlo del tren", rs._z_nulo)
for n in ("graficar", "graficar_ritmo", "graficar_cinetica", "graficar_estabilidad"):
    setattr(cr, n, medir("graficos", getattr(cr, n)))
_EW = pd.ExcelWriter
import contextlib
@contextlib.contextmanager
def EW(*a, **k):
    t = time.perf_counter()
    with _EW(*a, **k) as w:
        yield w
    tiempos["escribir el Excel"] = tiempos.get("escribir el Excel", 0.0) + time.perf_counter() - t
class _PD:                                   # pandas igual, salvo ExcelWriter
    def __getattr__(s, n):
        return EW if n == "ExcelWriter" else getattr(pd, n)
cr.pd = _PD()
cr.imprimir = lambda *a, **k: None          # sin consola: solo tiempos

if __name__ == "__main__":
    # OJO: los argumentos se leen aca adentro. Los procesos del Monte Carlo
    # vuelven a ejecutar la parte de arriba de este archivo (Windows y "spawn").
    carpeta = sys.argv[1] if len(sys.argv) > 1 else "Video_613"
    procesos = [int(x) for x in sys.argv[2:]] or [1, 2, 4]
    serie = buscar_serie(ref.PROCESADOS / carpeta)
    print(f"cargar librerias: {T_IMPORT:.1f} s   ({carpeta})")
    for p in procesos:
        tiempos.clear()
        with tempfile.TemporaryDirectory() as tmp:
            sys.argv = ["x", "--input", str(serie), "--output-dir", tmp, "--procesos", str(p)]
            frec = ref.VIDEOS.get(carpeta, (None, None, None))[2]
            if frec:
                sys.argv += ["--frecuencia-estimulo", *map(str, frec)]
            t = time.perf_counter()
            import contextlib, io
            with contextlib.redirect_stdout(io.StringIO()):
                cr.main()
            total = time.perf_counter() - t
        print(f"\n--procesos {p}: total {total:.1f} s")
        for k, v in tiempos.items():
            print(f"   {k:32s} {v:6.1f} s")
