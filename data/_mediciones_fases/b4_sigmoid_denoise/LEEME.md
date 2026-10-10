# B4 / H28: sigmoid y denoise contra lo actual (2026-10-10)

Video_prueba y Video_063, `main.py --base-tiempo pts --procesos 2` (máquina de prueba, 2 núcleos),
con lo actual, `--edge-method sigmoid` y `--denoise`; reporte con `--frecuencia-estimulo 0.1`.
Salida completa en `resultado.txt`, tiempos en `tiempos.txt`.

| video | método | eventos | ruido (px) | meseta k | amplitud | tiempo |
|---|---|---|---|---|---|---|
| prueba | actual | 29 | 0.085 | 5.3–15.2 | 2.31 % | 48 s |
| prueba | sigmoid | 29 | 0.075 | 6.4–16.7 | 2.31 % | 160 s |
| prueba | denoise | 29 | 0.084 | 5.8–13.8 | 2.28 % | 1693 s |
| 063 | actual | 6 | 0.024 | 9.4–13.8 | 0.56 % | 41 s |
| 063 | sigmoid | 6 | 0.022 | 9.4–15.2 | 0.59 % | 97 s |
| 063 | denoise | 6 | 0.023 | 11.4–15.2 | 0.57 % | 1420 s |

Ninguno es mejor en lo que se informa; los dos son mucho más lentos. Se borraron.
Los scripts corren contra el código ANTERIOR al borrado (commit previo).
