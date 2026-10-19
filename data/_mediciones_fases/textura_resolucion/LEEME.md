# Textura: ¿cuál amplitud es la correcta, achicado x0.5 o 4K completo? (2026-10-19)

Pregunta: en 10V_1 la amplitud por textura da 1.16 px achicada y 0.98 px a resolución completa (−16 %, en los 6 pulsos). ¿Cuál es la verdadera? (El control de una noche está en `../textura/LEEME.md` §6.)

## Sintético (`sintetico_resolucion.py`, salida en `sintetico_resolucion_salida.txt`)
- Un gel grande (1600×800, franja de ~1000 px) con textura de grano 1.5, 3 y 6 px y ruido 2 o 6, corrido una cantidad **conocida** (0.5, 1 y 2 px del original). Se mide a resolución completa y achicado x0.5 (escala forzada). Cifra: medido/real.

| grano | ruido | real | completo | x0.5 |
|---|---|---|---|---|
| 1.5 | 2 | 0.5 / 1 / 2 px | 0.97 / 1.09 / 1.03 | 0.86 / 1.00 / 1.04 |
| 1.5 | 6 | 0.5 / 1 / 2 px | 0.93 / 1.04 / 1.01 | 0.82 / 0.95 / 1.01 |
| 3 | 2 | 0.5 / 1 / 2 px | 0.99 / 1.10 / 1.03 | 0.86 / 0.99 / 1.03 |
| 3 | 6 | 0.5 / 1 / 2 px | 0.91 / 1.01 / 0.99 | 0.80 / 0.91 / 1.00 |
| 6 | 2 | 0.5 / 1 / 2 px | 0.87 / 1.06 / 0.98 | 0.84 / 0.97 / 1.03 |
| 6 | 6 | — | la serie se va (pierde el entero) | 0.78 / 0.90 / 1.00 |

- **Desde 2 px los dos aciertan (±5 %).** Con 0.5–1 px los dos se equivocan hasta 10–20 %, y no siempre para el mismo lado.
- **En el sintético el achicado mide MENOS que el completo**; en 10V_1 real mide MÁS. El sintético no reproduce lo de 10V_1: la diferencia de 10V_1 no se explica solo por achicar (puede ser la textura real, la compresión o el ruido del video).
- Caso raro: grano grueso + ruido alto a resolución completa, la correlación de fase pierde el entero y la serie se va (no visto en videos reales; anotado).

## Conclusión
- **No se puede saber cuál de las dos es la correcta en 10V_1.** Para respuestas de ~1 px, la amplitud por textura tiene una incertidumbre de método de ~15–20 %, mayor que su IC 95 %.
- **Hecho (no cambia números):** `contraction_report.py` imprime `AVISO: respuesta chica para el metodo de textura ...` cuando la serie es de textura, el conteo es reportable y la amplitud es < 1.5 px o < 10 × ruido (columna `aviso_textura_chica` en `resumen_*`). Lo dan 10V_1 (achicado y 4K) y 40V_3; no 20V_3 ni 40V_1. Test en `tests/test_textura.py` (sección 4); regresión de los 11 idéntica.
- Lo único que daría la respuesta real: un video con un movimiento conocido del mismo montaje (p. ej. mover la platina una cantidad conocida) o un segundo método independiente sobre 10V_1.
