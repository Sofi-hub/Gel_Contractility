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
              and filas["Amplitud, mediana (% del grosor)"][0].startswith(f"{rp.fila['amplitud_pct']:.2f} %"))
        lag, y, n = visor.promedio_para_dibujar(rp)
        check("promedio para dibujar: los 6 estimulados, pico cerca de la amplitud informada",
              n == 6 and abs(float(np.nanmax(y)) - rp.fila["amplitud_pct"]) < 0.1 * rp.fila["amplitud_pct"])
    if "Video_613" in nombres:
        check("613 en la tabla: NO reportable y sin amplitud",
              filas["Reportable"][nombres.index("Video_613")] == "NO"
              and filas["Amplitud, mediana (% del grosor)"][nombres.index("Video_613")] == "—")
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

# ---- pulsos individuales y selección (2026-10-15): media de valores del Excel ----
import openpyxl  # noqa: E402


def _cinetica_cruda(carpeta: Path):
    """La hoja cinetica leída directo con openpyxl (sin visor ni pandas)."""
    x = sorted(carpeta.glob("contracciones_*.xlsx"))[0]
    wb = openpyxl.load_workbook(x, read_only=True, data_only=True)
    hoja = next(wb[n] for n in wb.sheetnames if n == "cinetica" or n.startswith("cinetica_"))
    filas = list(hoja.iter_rows(values_only=True))
    cab = list(filas[0])
    return [dict(zip(cab, f)) for f in filas[1:]]


for nombre, primeros in (("Video_063_CTRL1_5V", [2, 3, 4]), ("Video_466_EXP5_FAPS4_40V", [1, 2, 3])):
    if not (P / nombre).is_dir():
        continue
    r = visor.leer_resultado(P / nombre)
    cruda = _cinetica_cruda(P / nombre)
    check(f"{nombre}: tabla de pulsos, una fila por contracción", len(visor.tabla_pulsos(r)) == len(cruda))
    sel = visor.seleccion_rapida(r, "primeros", 3)
    check(f"{nombre}: 3 primeros estimulados = {primeros}", sel == primeros)
    d = visor.media_seleccion(r, sel)
    amp = [f["amplitud_relativa_pct"] for f in cruda if int(f["evento"]) in sel]
    px_ = [f["amplitud_px"] for f in cruda if int(f["evento"]) in sel]
    check(f"{nombre}: media de la selección = media de la hoja cinetica (% y px)",
          d["n"] == 3 and abs(d["amplitud_pct"] - float(np.mean(amp))) < 1e-9
          and abs(d["amplitud_px"] - float(np.mean(px_))) < 1e-9)
    ttp = [f["ttp_s"] for f in cruda if int(f["evento"]) in sel and f["ttp_medible"]]
    check(f"{nombre}: TTP de la selección = media de los medibles (o cota si ninguno)",
          (len(ttp) == 0 and d["ttp_n_medibles"] == 0 and d["ttp_cota_s"] > 0)
          or abs(d["ttp_s"] - float(np.mean(ttp))) < 1e-9)
    todos_est = visor.seleccion_rapida(r, "estimulados")
    dm = [f["amplitud_relativa_pct"] for f in cruda if int(f["evento"]) in todos_est]
    check(f"{nombre}: la MEDIANA de todos los estimulados es la amplitud informada",
          abs(float(np.median(dm)) - r.fila["amplitud_pct"]) < 1e-9)
    check(f"{nombre}: rótulo 'media de la selección: 3 de N pulsos'",
          visor.texto_media(d)[0][1].startswith(f"3 de {len(cruda)} pulsos"))
    check(f"{nombre}: ninguno y todos", visor.seleccion_rapida(r, "ninguno") == []
          and len(visor.seleccion_rapida(r, "todos")) == len(cruda))

if (P / "Video_613").is_dir():
    r = visor.leer_resultado(P / "Video_613")
    check("613 (NO reportable): sin estimulados, 'primeros' toma los primeros candidatos",
          visor.seleccion_rapida(r, "estimulados") == [] and len(visor.seleccion_rapida(r, "primeros", 3)) == 3
          and all(f["tipo"] == "candidata" for f in visor.tabla_pulsos(r)))

if (P / "Video_063_CTRL1_5V").is_dir():
    with tempfile.TemporaryDirectory() as tmp:
        c = Path(tmp) / "Video_063_CTRL1_5V"
        shutil.copytree(P / "Video_063_CTRL1_5V", c)
        antes = {p.name: p.read_bytes() for p in c.glob("*.xlsx")}
        check("sin selección guardada: None", visor.leer_seleccion(c) is None)
        visor.guardar_seleccion(c, [4, 2], "a mano")
        check("selección guardada aparte y releída", visor.leer_seleccion(c) == [2, 4])
        r = visor.leer_resultado_sin_cache(c)
        ev, txt = visor.eventos_para_comparar(r, "guardada")
        check("Comparar usa la selección guardada", ev == [2, 4] and "guardada" in txt)
        x = visor.exportar_seleccion(r, [2, 3], c / "sel.xlsx")
        import pandas as pd
        check("exportar selección: 2 pulsos y la media",
              len(pd.read_excel(x, sheet_name="pulsos_elegidos")) == 2
              and "Media de la selección" in pd.read_excel(x, sheet_name="media")["qué"].tolist())
        x2 = visor.exportar_seleccion(r, [2, 3], c / "sel.csv")
        check("exportar selección como CSV", x2.stat().st_size > 50)
        check("selección: los Excel no se tocan",
              {p.name: p.read_bytes() for p in c.glob("*.xlsx") if p.name != "sel.xlsx"} == antes)

nombres = [n for n in ("Video_063_CTRL1_5V", "Video_466_EXP5_FAPS4_40V") if (P / n).is_dir()]
if len(nombres) == 2:
    rs = [visor.leer_resultado(P / n) for n in nombres]
    filas = dict(visor.tabla_seleccion(rs, "primeros", 3))
    check("Comparar: media de los 3 primeros de cada uno",
          filas["Media: amplitud (% del grosor)"] ==
          [f"{visor.media_seleccion(r, visor.seleccion_rapida(r, 'primeros', 3))['amplitud_pct']:.2f} %"
           for r in rs])
    lag, ys, ym = visor.pulsos_para_dibujar(rs[1], [1, 2, 3])
    check("dibujo de la selección: 3 pulsos y su media", len(ys) == 3 and ym.shape == lag.shape)

# ---- Comparar: pulsos elegidos y vistas (2026-10-15) ----
if len(nombres) == 2:
    df = visor.pulsos_comparar(rs, "primeros", 3)
    check("Comparar, pulsos elegidos: 3 por video, con su resultado",
          len(df) == 6 and df["resultado"].str.startswith("1 · ").sum() == 3)
    v = visor.valores_pulsos(rs[1], [3, 1, 2])
    check("valores de los pulsos en orden de tiempo", v["evento"].tolist() == [1, 2, 3])
check("compactar números de pulso", visor.compactar([1, 2, 3, 5, 7, 8]) == "1–3, 5, 7, 8")

# ---- basal (C8): el texto sale del resumen; resultados viejos lo avisan ----
import informe  # noqa: E402
check("basal: resultado viejo -> avisa que falta el paso 2",
      "rehacer el paso 2" in informe.texto_basal({"amplitud_relativa_pct": 1.0}))
check("basal: texto guardado", informe.texto_basal({"basal_resumen": "0 contraccion(es)", "basal_fin_s": 10.0})
      == "0–10.0 s: 0 contraccion(es)")

print("\nTODO OK" if ok else "\nHAY FALLAS")
sys.exit(0 if ok else 1)
