# B6 — pico = primer instante en que se llega al máximo (2026-10-15)

Pedido del equipo (reunión 2026-10-15, pregunta 13 / H41). **Solo medido; no implementado** (cambia TTP y RT50 informados).

`medir.py` envuelve `cin.cinetica_eventos` y corre el reporte en memoria sobre los 11 videos de referencia (mismas frecuencias que `tests/referencia.py`). Solo cambia el instante del pico; la amplitud (sigue siendo el máximo), el inicio, los eventos, el ritmo y el período son idénticos en todas las variantes (control en la salida). Salidas: `tabla_videos.csv`, `detalle_eventos.csv` (evento por evento en 466, 583, 491 y 476).

## Resultado (mediana de los estimulados; entre paréntesis, medibles / eventos)

| video | actual (fotograma más alto) | ≥ máx − 1 ruido | ≥ máx − 2 ruido | **≥ 95 % del máx** | ≥ 90 % del máx | interpolado al 95 % |
|---|---|---|---|---|---|---|
| 466 TTP | 255 (5/5) | 183 | 183 | **183 (5/5)** | 183 | 174 |
| 466 RT50 | 192 (3/5) | 226 (4/5) | 223 (5/5) | **226 (4/5)** | 223 (5/5) | 232 (4/5) |
| 583 TTP | 258 (6/6) | 223 | 189 | **189 (6/6)** | 190 (4/6) | 176 |
| 583 RT50 | 181 (6/6) | 221 | 252 | **252 (6/6)** | 270 | 264 |
| 491 TTP | 570 (2/2) | 523 | 437 | **557** | 453 | 537 |
| 491 RT50 | 467 (2/2) | 513 | 599 | **480** | 583 | 499 |

Las rápidas (Video_prueba, 063, 268, 476) siguen siendo cotas iguales (< 100–155 ms) en todas las variantes; 613, 068, 304 y 341 siguen NO reportables o sin eventos.

## Lectura
- En 466 y 583 casi todas las variantes coinciden en el comienzo de la meseta (TTP ~183–189 ms, RT50 ~223–252 ms), como lo medido el 2026-10-10.
- Las variantes por ruido (máx − z·ruido) dependen de la relación señal/ruido: en 491 (amplitud ~1 px, ruido 0.07 px) 2 ruidos son el 13 % de la amplitud y el "pico" se adelanta mucho (TTP 570 → 437 ms). Una fracción de la amplitud no depende de eso.
- **Propuesta:** pico = **primer fotograma ≥ 95 % del máximo**, en el tramo continuo que termina en el máximo. Fácil de explicar, no depende del ruido, y en 466/583 da lo mismo que "comienzo de la meseta". Aviso si el 5 % de la amplitud es menor que 2 ruidos (ahí el ruido decide el fotograma): hoy solo pasaría en 491.
- Implementarlo cambia TTP/RT50 de 466, 583 y 491 y obliga a regenerar la referencia (`--aprobar`). La cota de RT50 (`rt50_max_s`) se seguiría calculando con la meseta de 2 ruidos.
