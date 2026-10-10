# D6: umbrales de tres avisos nuevos (2026-10-10)

`medir_d6.py` mide en los 11 videos dónde caería cada umbral. Tabla: `tabla_d6.csv`.

| video | dt idénticos (%) | cintura: columnas seguidas (px) | nitidez del borde en la zona (mediana) |
|---|---|---|---|
| Video_prueba | 37 | 1062 | 37 |
| 063 | 42 | 1033 | 51.5 |
| 268 | 44 | 410 | 32.5 |
| 466 | 46 | **150** | 18.5 |
| 583 | 35 | 469 | 26.5 |
| 491 | 45 | 747 | 25.5 |
| 476 | 50 | 268 | **18** |
| 613 | 43 | 304 | 40 |
| 068 | 45 | 666 | 45.5 |
| 304 | 40 | 792 | 38.5 |
| 341 | 37 | 519 | 32 |

Umbrales elegidos (en `src/pipeline.py`, avisos en `main.py`), con margen para que ninguno de los 11 avise:
- **H15 timestamps inventados:** ≥ 99 % de intervalos idénticos. Un contenedor que inventa los tiempos da ~100 %; los reales, 35–50 %. Margen enorme.
- **H21 cintura corta:** menos columnas seguidas cerca de la cintura que el ancho mínimo de la zona (120 px). El más justo es 466 (150).
- **H22 poco contraste:** nitidez mediana < 12. La elección de zona ya exige ≥ 10; los más bajos que funcionan bien son 476 y 466 (18).

H21 y H22 salen de pocos casos (D4): si un video nuevo avisa, mirar la figura antes de descartarlo.
