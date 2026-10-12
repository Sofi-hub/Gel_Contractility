"""visor.py (pestaña Resultados): la parte de datos, sin ventana.

    python tests/test_visor.py

Comprueba que lo que muestra sale de los Excel vigentes (no recalcula):
mismos conteos, ficha de una contraccion con los valores de la hoja cinetica.
"""
from __future__ import annotations

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
import visor  # noqa: E402
import numpy as np  # noqa: E402

ok = True


def check(nombre, cond):
    global ok
    print(f"  {nombre}: {'OK' if cond else 'FALLA'}")
    ok &= bool(cond)


P = RAIZ / "data" / "processed_data"
cs = visor.listar_carpetas(P)
check("lista de resultados (sin carpetas que empiezan con _)",
      len(cs) >= 1 and all(not c.name.startswith("_") for c in cs))
if (P / "Video_prueba").is_dir():
    r = visor.leer_resultado(P / "Video_prueba")
    check("Video_prueba: 29 contracciones en la hoja cinetica", len(r.cin) == 29)
    check("serie para dibujar del largo del video", len(r.senal) == len(r.t) > 1000)
    i = int((r.cin["grupo"] == "estimulados").to_numpy().nonzero()[0][0])
    f = dict(visor.ficha_evento(r, i))
    check("ficha de una estimulada: tipo, desvio y amplitud de la hoja",
          f["Tipo"] == "estimulada" and "Desvío del estimulador" in f
          and f"{r.cin['amplitud_px'].iloc[i]:.2f} px" in f["Amplitud"])
    check("cache: la segunda lectura devuelve el mismo objeto",
          visor.leer_resultado(P / "Video_prueba") is r)
if (P / "Video_613").is_dir():
    r = visor.leer_resultado(P / "Video_613")
    f = dict(visor.ficha_evento(r, 0))
    check("613: las fichas dicen que es candidata (NO reportable)", "candidata" in f["Contracción"])

# ---- Comparar, marcas y ficha (2026-10-11): solo leen y dibujan ----
import shutil, tempfile  # noqa: E402
nombres = [n for n in ("Video_prueba", "Video_063_CTRL1_5V", "Video_613") if (P / n).is_dir()]
if len(nombres) >= 2:
    rs = [visor.leer_resultado_sin_cache(P / n) for n in nombres]
    filas = dict(visor.tabla_comparar(rs))
    check("tabla comparar: una columna por resultado",
          all(len(v) == len(rs) for v in filas.values()))
    if "Video_prueba" in nombres:
        rp = rs[nombres.index("Video_prueba")]
        check("tabla comparar: Video_prueba 29 contracciones, amplitud del resumen",
              filas["Contracciones"][0] == "29"
              and filas["Amplitud (% del grosor)"][0].startswith(f"{rp.fila['amplitud_pct']:.2f} %"))
        lag, y, n = visor.promedio_para_dibujar(rp)
        check("promedio para dibujar: los 6 estimulados, pico cerca de la amplitud informada",
              n == 6 and abs(float(np.nanmax(y)) - rp.fila["amplitud_pct"]) < 0.1 * rp.fila["amplitud_pct"])
    if "Video_613" in nombres:
        check("613 en la tabla: NO reportable y sin amplitud",
              filas["Reportable"][nombres.index("Video_613")] == "NO"
              and filas["Amplitud (% del grosor)"][nombres.index("Video_613")] == "—")
    with tempfile.TemporaryDirectory() as tmp:
        x = visor.guardar_tabla_comparar(rs, Path(tmp) / "c.xlsx")
        import pandas as pd
        check("guardar tabla comparar (Excel)", pd.read_excel(x).shape == (len(filas), len(rs) + 1))

if (P / "Video_prueba").is_dir():
    with tempfile.TemporaryDirectory() as tmp:
        c = Path(tmp) / "Video_prueba"
        shutil.copytree(P / "Video_prueba", c)
        antes = {p.name: p.read_bytes() for p in c.glob("*.xlsx")}
        visor.marcar_dudosa(c, 3)
        r = visor.leer_resultado_sin_cache(c)
        check("marca dudosa: se guarda aparte", visor.leer_marcas(c) == {"3": "dudosa"})
        check("marca dudosa: los Excel no se tocan",
              {p.name: p.read_bytes() for p in c.glob("*.xlsx")} == antes)
        check("marca dudosa: la ficha la menciona", "Marca manual" in visor.ficha_texto(r, 2))
        visor.marcar_dudosa(c, 3, dudosa=False)
        check("quitar la última marca borra el archivo", not visor.archivo_marcas(c).exists())
        png = visor.guardar_ficha_png(r, 0, c / "f.png")
        check("exportar ficha como imagen", png.stat().st_size > 10000)

print("\nTODO OK" if ok else "\nHAY FALLAS")
sys.exit(0 if ok else 1)
