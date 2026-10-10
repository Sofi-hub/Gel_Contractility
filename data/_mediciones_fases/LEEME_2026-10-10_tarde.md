# Mediciones del 2026-10-10 (tarde)

Ninguna cambia el código del análisis. Cada carpeta tiene su LEEME.md con la tabla y la conclusión.

| carpeta | pregunta | resultado |
|---|---|---|
| `d1_d2_intensidad/` | D1: intensidad/bordes (0.82–0.88), ¿toda la tanda EXP5? | No es EXP5. Por eventos: 476 0.99; 268, 466, 491 0.86–0.88; resto 0.96–0.99. Propuesta chica pendiente |
| `d2_peine/` | D2/H52: ¿el peine de compresión está en los otros videos? | Sí, en los 11 (fotogramas P del H.264). No pasa a los bordes |
| `d3_amplitud_tramos/` | D3: ¿la espontánea de 0.31 s de 063 es local? | Sí: 0 en el tercio izquierdo, 1.4× la ROI a la derecha |
| `d7_oscilacion_post/` | D7: ¿la oscilación post-evento de 476 se repite? | No: solo 476 (~2.4 Hz, ±0.2–0.3 px) |
| `b1_gradiente_466/` | B1: ¿qué es el otro gradiente a ~15 px en 466? | Segundo escalón en el borde superior, casi tan fuerte como el borde |
| `h23_ventanas_roi/` | H23: ventanas de la ROI con el gel | Ningún número informado cambia; propuesta: no cambiar ahora |

Para correrlas hacen falta los videos en `data/raw_videos/` y los resultados vigentes en `data/processed_data/`.
