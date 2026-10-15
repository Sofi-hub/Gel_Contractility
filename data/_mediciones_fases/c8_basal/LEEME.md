# C8 — resumen de la basal (2026-10-15)

La basal es lo que pasa antes del estímulo (protocolo: primeros ~10 s). **Implementado el 2026-10-15 con la propuesta de abajo** (`resumen_basal` en `scripts/contraction_report.py`, test `tests/test_basal.py`). `medir.py` corre el reporte en memoria en los 11 videos; tabla completa en `tabla_basal.csv`.

| video | basal (s) | contr. en basal (0–10 s) | frecuencia Hz (mediana; IQR) | amplitud mediana (%) | p95 de \|señal\| (% grosor) |
|---|---|---|---|---|---|
| Video_prueba | 0–14.9 | 19 (17) | 1.75; 1.67–1.76 | 0.71 | 0.65 |
| 063 | 0–11.9 | 1 (1), junto al borde | — | 0.13 | 0.02 |
| 268 | 0–12.6 | 0 | — | — | 0.04 |
| 466 | 0–14.0 | 0 | — | — | 0.22 |
| 583 | 0–11.0 | 0 | — | — | 0.08 |
| 476 | 0–11.3 | 0 | — | — | 0.10 |
| 491 | 0–10 (sin tren) | 0 | — | — | 0.07 |
| 613 (NO rep.) | 0–10 | 7 candidatos (vibración) | — | — | 0.10 |
| 341 (NO rep.) | 0–10 | 14 candidatos | — | — | 0.39 |
| 304 (sin eventos) | 0–10 | 0 | — | — | 0.39 |
| 068 (NO rep.) | 0–10 | 0 | — | — | **2.09** |

## Lectura
- Con contracciones separadas, la basal se resume bien con cuántas, frecuencia y amplitud (Video_prueba: ~1.75 Hz espontánea, 0.71 %).
- "Fracción del tiempo activa" con un umbral de ruido **no sirve**: con el ruido del video, en 068 la actividad infla el ruido y da 0 %; con el ruido de fotograma a fotograma, en los videos quietos la deriva lenta da 30–70 % "activo". Se descarta.
- La **amplitud típica (percentil 95 de |señal|, % del grosor)** no depende de ningún umbral y ordena bien: quietos 0.02–0.22 %, actividad 0.39–2.1 %.
- En los NO reportables los candidatos no son contracciones confirmadas (613: vibración al inicio): no se cuentan.

## Propuesta (hoja nueva `basal` en el Excel del reporte, línea en consola, informe y ventana)
- Basal = de 0 s hasta **el menor entre 10 s y el inicio de la primera estimulada** (protocolo). Alternativa: hasta la primera estimulada (Video_prueba: 17 vs 19).
- Conteo reportable: n.º de contracciones, frecuencia (mediana e IQR si hay ≥ 4), amplitud mediana (%); marcar las `junto_al_borde`.
- Siempre: actividad basal = p95 de |señal| en % del grosor.
- NO reportable: "no contable", solo la actividad basal.
