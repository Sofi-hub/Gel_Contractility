"""Resumen de la basal (C8, 2026-10-15) sobre los Excel vigentes, en memoria.

    python tests/test_basal.py

Comprueba los valores medidos en data/_mediciones_fases/c8_basal/ y que la
basal no cambia ningún número que ya se informaba (la regresión lo cubre).
"""
from __future__ import annotations
import sys
import warnings
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ)); sys.path.insert(0, str(RAIZ / "scripts")); sys.path.insert(0, str(RAIZ / "tests"))
from contraction_report import analizar  # noqa: E402
from referencia import VIDEOS, PROCESADOS, leer_serie  # noqa: E402
from src.output_paths import buscar_serie  # noqa: E402

ok = True


def check(nombre, cond):
    global ok
    print(f"  {'OK   ' if cond else 'FALLA'} {nombre}")
    ok &= bool(cond)


def correr(carpeta):
    df, _ = leer_serie(buscar_serie(PROCESADOS / carpeta))
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return analizar(df, "center_px", None, None, None, 1.5, frecuencia_estimulo=VIDEOS[carpeta][2])


casos = {  # carpeta -> (contable, n en la basal, actividad % aprox.)
    "Video_prueba": (True, 17, 0.67),
    "Video_063_CTRL1_5V": (True, 1, 0.02),
    "Video_466_EXP5_FAPS4_40V": (True, 0, 0.21),
    "Video_068_hw30": (False, None, 2.09),
    "Video_613": (False, None, 0.10),
}
for c, (contable, n, act) in casos.items():
    if not (PROCESADOS / c).is_dir():
        print(f"  --  {c} no está: se saltea")
        continue
    a = correr(c)
    check(f"{c}: basal hasta {a['basal_fin_s']:.1f} s (<= 10 s)", a["basal_fin_s"] <= 10.0)
    check(f"{c}: contable = {contable}", a.get("basal_contable") is contable)
    if n is not None:
        check(f"{c}: {n} contracciones en la basal", a.get("basal_n_contracciones") == n)
    check(f"{c}: actividad basal ~{act} % del grosor",
          abs(a["basal_actividad_p95_pct"] - act) < 0.01)
    if c == "Video_063_CTRL1_5V":
        check("063: la de 0.31 s queda marcada junto al borde", a.get("basal_junto_al_borde") == 1)
    if c == "Video_prueba":
        check("Video_prueba: frecuencia basal ~1.76 Hz con IQR",
              abs(a["basal_frecuencia_mediana_Hz"] - 1.76) < 0.02 and "basal_frecuencia_iqr_Hz" in a)

print("\nTODO OK" if ok else "\nHAY FALLAS")
sys.exit(0 if ok else 1)
