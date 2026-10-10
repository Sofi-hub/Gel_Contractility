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

print("\nTODO OK" if ok else "\nHAY FALLAS")
sys.exit(0 if ok else 1)
