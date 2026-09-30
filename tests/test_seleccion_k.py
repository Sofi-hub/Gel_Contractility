"""Regresion de la eleccion automatica de k (meseta del escaneo de estabilidad).

Cada caso es un escaneo REAL ya corrido, con la respuesta que quedo validada.
Si un cambio en `elegir_k_meseta` rompe alguno de estos, el cambio esta mal.

Correr con:  python tests/test_seleccion_k.py
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from contraction_report import elegir_k_meseta          # noqa: E402

K = [3, 4, 6, 8, 10, 12, 15, 20]

# nombre: (eventos por k, falsos_control por k, n_eventos esperado o None)
CASOS = {
    # --- los dos videos validados: la respuesta NO puede cambiar ---
    # Estos dos son las corridas v5, con el eje fotograma/fps. Con --base-tiempo
    # pts Video_prueba pasa a 28 eventos: ver el bloque "vigentes" al final.
    "Video_prueba":      ([84, 36, 29, 29, 29, 29, 29, 26], [0]*8,                    29),
    "Video_063":         ([10, 8, 6, 6, 5, 5, 5, 5],        [3, 1, 0, 0, 0, 0, 0, 0],  6),
    # Video_063 tiene DOS mesetas (6 ev en k=6..8 y 5 ev en k=10..20). Gana la
    # de k mas bajo: al subir el umbral se pierden eventos reales. Elegir "la
    # mas larga" daria 5, que es la respuesta equivocada.

    # --- bateria, corridas viejas (ROI rota) ---
    "V268 vieja":        ([8, 7, 6, 6, 6, 6, 1, 0],         [5, 1, 0, 0, 0, 0, 0, 0],  6),
    "V466 vieja":        ([10, 8, 6, 5, 5, 5, 5, 0],        [39, 29, 2, 0, 0, 0, 0, 0], 5),
    "V583 vieja":        ([17, 14, 10, 7, 7, 7, 6, 6],      [20, 10, 4, 1, 0, 0, 0, 0], 7),
    "V491 vieja":        ([15, 8, 5, 3, 1, 0, 0, 0],        [12, 5, 2, 2, 0, 0, 0, 0], None),

    # --- bateria, ROI corregida ---
    "V268 v4":           ([14, 9, 7, 6, 6, 6, 6, 6],        [4, 0, 0, 0, 0, 0, 0, 0],  6),
    "V466 v4":           ([12, 6, 5, 5, 5, 5, 5, 4],        [11, 8, 1, 0, 0, 0, 0, 0], 5),
    # V466 v4: el tramo de 5 eventos empieza en k=6, pero ahi todavia hay 1
    # falso. Hay que filtrar los falsos ANTES de buscar el tramo constante,
    # no despues; si no, la meseta real (k=8..15) se descarta entera.
    "V583 v4":           ([21, 14, 10, 9, 8, 6, 6, 6],      [15, 10, 5, 1, 0, 0, 0, 0], 6),
    # V583 v4: con el k=8 que era el default salian 9 eventos con 1 falso, y
    # los espurios hacian que rhythm_split NO encontrara el tren. La meseta
    # esta en k=12..20.
    "V491 v4":           ([12, 7, 5, 4, 2, 0, 0, 0],        [16, 7, 2, 2, 1, 0, 0, 0], None),
    # V491: sin meseta. Los 0 eventos de k=12..20 no cuentan como meseta.

    # --- vigentes (v6: --base-tiempo pts), los de data/processed_data/<video>/ ---
    "prueba v6":         ([83, 35, 28, 28, 28, 28, 28, 26], [0]*8,                    28),
    "063 v6":            ([10, 8, 6, 6, 5, 5, 5, 5],        [3, 1, 0, 0, 0, 0, 0, 0],  6),
    "V268 v6":           ([14, 9, 6, 6, 6, 6, 6, 6],        [6, 2, 0, 0, 0, 0, 0, 0],  6),
    "V466 v6":           ([9, 5, 5, 5, 5, 5, 5, 3],         [1, 0, 0, 0, 0, 0, 0, 0],  5),
    "V583 v6":           ([21, 14, 10, 9, 8, 6, 6, 6],      [15, 10, 5, 1, 0, 0, 0, 0], 6),
    "V491 v6":           ([13, 8, 6, 4, 2, 0, 0, 0],        [12, 5, 2, 2, 0, 0, 0, 0], None),
}


def main() -> int:
    fallas = 0
    for nombre, (eventos, falsos, esperado) in CASOS.items():
        df = pd.DataFrame({"k": K, "umbral_px": [0.0] * len(K),
                           "eventos": eventos, "falsos_control": falsos})
        r = elegir_k_meseta(df)
        obtenido = r["n_eventos"] if r["hay_meseta"] else None
        bien = obtenido == esperado
        fallas += not bien
        donde = f"k={r['k']:g}" if r["hay_meseta"] else "sin meseta"
        print(f"  {'OK ' if bien else 'MAL'} {nombre:16s} -> {donde:12s} "
              f"{obtenido!s:5s} (esperado {esperado})")
    print(f"\n{len(CASOS) - fallas}/{len(CASOS)} casos OK")
    return 1 if fallas else 0


if __name__ == "__main__":
    raise SystemExit(main())
