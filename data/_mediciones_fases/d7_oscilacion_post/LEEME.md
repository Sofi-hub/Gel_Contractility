# D7: oscilación chica después de cada contracción (2026-10-10)

**Pregunta:** en 476 se ve una oscilación de ~0.3–0.5 px después de cada contracción, debajo del umbral. ¿Se repite en otros videos?

**Cómo:** `medir_d7.py` (solo lee resultados vigentes). `center_px` sin deriva (misma ventana del reporte), eventos aislados, promedio alineado al FINAL de cada evento. Una oscilación que se repite con la misma forma sobrevive al promedio; el ruido baja como 1/√N. Se compara la variación en [final, final + 2.5 s] con un tramo quieto antes del evento.

| video | eventos aislados | ruido (px) | post/pre (promedio) | post/pre (por evento, mediana) | frecuencia dominante post |
|---|---|---|---|---|---|
| Video_prueba | 4 | 0.085 | 1.27 | 1.05 | 2.0 Hz (*) |
| 063 | 5 | 0.024 | 0.97 | 1.24 | — |
| 268 | 6 | 0.049 | 1.53 | 1.29 | 0.4 Hz (cola lenta) |
| 466 | 5 | 0.182 | 1.54 | 1.11 | 0.4 Hz (cola lenta) |
| **476** | 6 | 0.115 | **2.54** | **2.23** | **2.4 Hz** |
| 583 | 6 | 0.072 | 1.24 | 1.06 | 0.4 Hz (cola lenta) |
| 491 | 2 | 0.068 | (menos de 3 eventos) | | |

(*) En Video_prueba los "golpes" a 0.4 y 0.8 s después del final son espontáneas chicas (laten cada ~0.57 s), no una oscilación del gel.

**Resultado:** la oscilación es **propia de 476**: ~2.4 Hz (período ~0.4 s), ±0.2–0.3 px en el promedio, durante ~2.5 s después de cada contracción, y se repite en los 6 eventos (cociente 2.2 evento a evento). En los otros cinco no hay oscilación: lo que queda después del evento es una vuelta lenta a la línea base (0.4 Hz = el tramo entero), de 0.1–0.2 px en 268 y 466. No cambia ningún número (está debajo del umbral y no genera eventos).

Figura: `d7_post_evento.png`. Tabla: `tabla_d7.csv`.

**Para pensar (no es un pedido):** una oscilación a ~2.4 Hz que arranca con cada contracción puede ser mecánica (el gel/poste "rebota") o actividad del tejido. Es una pregunta para Cami si interesa.
