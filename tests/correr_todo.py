"""Corre TODOS los tests y la regresión, uno detrás del otro, y dice OK o FALLA al final.

    python tests/correr_todo.py              todos los tests + regresión rápida
    python tests/correr_todo.py --completo   además la regresión desde el video (~2-3 min más)
    python tests/correr_todo.py --rapido     sin test_textura (el más lento: corre main.py)

No cambia nada: solo ejecuta cada tests/test_*.py como siempre (python tests/test_x.py) y mira si
terminó bien. Guarda la salida completa en tests/ultimo_resultado.txt (no va a git).
Es lo mismo que verificar.bat (doble clic).
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
TESTS = Path(__file__).resolve().parent
LENTOS = {"test_textura.py"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--completo", action="store_true", help="regresión también desde el video")
    ap.add_argument("--rapido", action="store_true", help="saltear los tests lentos")
    a = ap.parse_args()

    tests = sorted(p for p in TESTS.glob("test_*.py") if p.name != "test_regresion.py")
    if a.rapido:
        tests = [p for p in tests if p.name not in LENTOS]
    pasos = [(p.name, [sys.executable, str(p)]) for p in tests]
    reg = [sys.executable, str(TESTS / "test_regresion.py")] + (["--completo"] if a.completo else [])
    pasos.append(("test_regresion.py" + (" --completo" if a.completo else ""), reg))

    log = [f"python {sys.version.split()[0]} | {time.strftime('%Y-%m-%d %H:%M')}\n"]
    resultados = []
    t_total = time.time()
    for nombre, cmd in pasos:
        print(f"  {nombre:34s} ...", end="", flush=True)
        t0 = time.time()
        p = subprocess.run(cmd, cwd=RAIZ, capture_output=True, text=True,
                           encoding="utf-8", errors="replace")
        dt = time.time() - t0
        ok = p.returncode == 0
        resultados.append((nombre, ok, dt))
        print(f"\r  {nombre:34s} {'OK   ' if ok else 'FALLA'} {dt:6.1f} s")
        log.append(f"\n===== {nombre}: {'OK' if ok else 'FALLA'} ({dt:.1f} s)\n{p.stdout}{p.stderr}")
        if not ok:
            ult = (p.stdout + p.stderr).strip().splitlines()[-8:]
            for linea in ult:
                print("      " + linea)

    fallas = [n for n, ok, _ in resultados if not ok]
    total = time.time() - t_total
    print("\n" + ("TODO OK" if not fallas else f"FALLA: {', '.join(fallas)}")
          + f"   ({len(resultados)} pasos, {total:.0f} s; salida completa en tests/ultimo_resultado.txt)")
    (TESTS / "ultimo_resultado.txt").write_text("".join(log), encoding="utf-8")
    return 1 if fallas else 0


if __name__ == "__main__":
    raise SystemExit(main())
