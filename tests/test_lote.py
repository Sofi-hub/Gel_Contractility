"""procesar_carpeta / armar_comando_carpeta: la tabla resumen solo LEE los Excel.

    python tests/test_lote.py

Lee las carpetas vigentes de data/processed_data (sin correr nada) y comprueba
que la fila de la tabla coincide con la referencia congelada.
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "scripts"))
import interfaz                       # noqa: E402
import procesar_carpeta as pc         # noqa: E402

ok = True


def check(nombre, cond):
    global ok
    print(f"  {nombre}: {'OK' if cond else 'FALLA'}")
    ok &= bool(cond)


P = RAIZ / "data" / "processed_data"
if (P / "Video_prueba").is_dir():
    f = pc.leer_fila(P / "Video_prueba")
    check("Video_prueba: 29 eventos, reportable", f.get("eventos") == 29 and f.get("reportable"))
    check("Video_prueba: tren 10.00043 s, 6 estimulados",
          f.get("tren") == "si" and abs(f["periodo_s"] - 10.00043) < 1e-9
          and f.get("n_estimulados") == 6)
    check("Video_prueba: amplitud 2.31 % / 6.81 px (estimulados)",
          abs(f["amplitud_pct"] - 2.314267) < 1e-5 and abs(f["amplitud_px"] - 6.80745) < 1e-5
          and f["amplitud_grupo"] == "estimulados")
if (P / "Video_341").is_dir():
    f = pc.leer_fila(P / "Video_341")
    check("Video_341: NO reportable, sin tren", f.get("reportable") is False and f.get("tren") == "no")

check("avisos_de", pc.avisos_de("x\n  AVISO: algo\nRESULTADO: NO REPORTABLE -> y\n  AVISO: algo\n")
      == ["AVISO: algo", "RESULTADO: NO REPORTABLE -> y"])

with tempfile.TemporaryDirectory() as tmp:
    c = interfaz.armar_comando_carpeta(tmp, "", True, True, False, "0.1")
    check("comando carpeta", c[0][1][-4:] == ["--pasos", "1 2", "--frecuencia-estimulo", "0.1"])
    try:
        interfaz.armar_comando_carpeta(tmp + "_no_existe", "", True, False, False)
        check("carpeta inexistente da error", False)
    except ValueError:
        check("carpeta inexistente da error", True)
    (Path(tmp) / "a.mp4").touch(); (Path(tmp) / "b.txt").touch()
    check("listar_videos", [p.name for p in pc.listar_videos(Path(tmp))] == ["a.mp4"])

print("\nTODO OK" if ok else "\nHAY FALLAS")
sys.exit(0 if ok else 1)
