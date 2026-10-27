# Índice de mediciones

Una línea por carpeta (2026-10-26). Cada carpeta tiene su LEEME o `resumen_*.md` con el script, la tabla y la
conclusión. **Al agregar una medición nueva, sumar una línea acá.** Ninguna de estas carpetas es parte del
análisis: son scripts y tablas para decidir.

| carpeta | fecha | pregunta → resultado |
|---|---|---|
| `fase3_borde/` | 2026-10-07 | Fase 3, borde y ajuste: medición en sintéticos y videos (`resumen_medicion.md`) |
| `fase3_columnas/` | 2026-10-08 | H19: cuántas columnas y ROI automática de 466 → columnas adaptables, piso 40 (`resumen_columnas.md`) |
| `fase3_magnitud/` | 2026-10-07 | H51: desplazamiento conocido → mide bien la magnitud (`resumen_magnitud.md`) |
| `fase4_chequeo2/` | 2026-10-07 | H24: calidad de ajuste por ROI → `outlier_frac` solo diagnóstico (`resumen_chequeo2.md`) |
| `fase4_motion/` | 2026-10-07 | `motion_check` viejo contra arreglado (`resumen_motion.md`) |
| `fase4_rafaga583/` | 2026-10-07 | ráfaga final de 583 → vibración (`resumen_rafaga_583.md`) |
| `fase4_regeneracion.md` | 2026-10-07 | regeneración de la Fase 4: series idénticas |
| `b1_ventana/` | 2026-10-10 | B1: ventana de búsqueda del borde → opción a' (±15, y ±30 si se sale) |
| `b1_gradiente_466/` | 2026-10-10 | el "otro gradiente" de 466 → segundo escalón en el borde superior |
| `b2_ruido_quieto/` | 2026-10-10 | B2: ruido solo en tramos quietos → no cambia resultados; EN ESPERA |
| `b2_sensibilidad/` | 2026-10-10 | sensibilidad de B2 (63 combinaciones) → estable, sin cambios |
| `b3_h29/` | 2026-10-10 | H29: ¿sin RANSAC es menos ruidoso? → no en todos; RANSAC se queda |
| `b4_sigmoid_denoise/` | 2026-10-10 | H28: sigmoid y denoise → no son mejores; borrados |
| `h16_ventana_tiempo/` | 2026-10-10 | H16: deriva con ventana en segundos → mismos resultados; sin cambios |
| `h23_ventanas_roi/` | 2026-10-10 | H23: ventanas de la ROI con el gel → ningún número cambia; se deja |
| `h30_ransac/` | 2026-10-10 | H30: intentos y umbral de RANSAC → 3 × MAD se queda |
| `d1_d2_intensidad/` | 2026-10-10 | D1: intensidad/bordes → 0.86–0.99 por contracción; no es EXP5 |
| `d2_peine/` | 2026-10-10 | D2/H52: peine de compresión → en los 11 videos; no pasa a los bordes |
| `d3_amplitud_tramos/` | 2026-10-10 | D3: espontánea de 0.31 s de 063 → es local |
| `d6_avisos/` | 2026-10-10 | D6: umbrales de los avisos nuevos (timestamps, cintura, contraste) |
| `d7_oscilacion_post/` | 2026-10-10 | D7: oscilación después de cada contracción → solo 476 |
| `verificacion_limpieza_11/` | 2026-10-10 | los 11 reprocesados con el código limpio → idénticos |
| `LEEME_2026-10-10_tarde.md` | 2026-10-10 | resumen de las mediciones de esa tarde |
| `tiempos_reporte/` | 2026-10-10 | cuánto tarda cada parte de `contraction_report.py` → el Monte Carlo del tren |
| `tiempos_main/` | 2026-10-11 | cuánto tarda cada parte de `main.py` en la notebook → ~90 → ~50 s |
| `b6_pico_primer_instante/` | 2026-10-15 | B6: pico = primer fotograma ≥ 95 % del máximo → aprobado e implementado |
| `b7_dirigida_613_068/` | 2026-10-15 | B7: 0.1 Hz dirigida en 613 y 068 → sin respuesta |
| `c8_basal/` | 2026-10-15 | C8: resumen de la basal → implementado |
| `orientacion/` | 2026-10-15 | gel vertical (Andrés) → rotación automática |
| `andres/` | 2026-10-16 | videos de Andrés: bordes no sirven; primera medición por textura |
| `textura/` | 2026-10-16/19 | medición por textura (opción `--metodo textura`), carpeta de Andrés, 4K contra achicado |
| `textura_resolucion/` | 2026-10-19 | ¿achicado o 4K? sintético → con ≤ 1 px las dos se equivocan 10–20 % |
| `respuesta_forzada/` | 2026-10-19 | respuesta forzada → implementada; los 5 NO REPORTABLES de Andrés responden |
| `cinetica_forzada/` | 2026-10-26 | TTP/RT50 desde la respuesta forzada → sirve pulso a pulso (±4 % contra el reporte), NO con la forma promedio |

Nota: `b2_sensibilidad/`, `h30_ransac/` y `verificacion_limpieza_11/` tienen el mismo LEEME (uno solo que
describe las tres mediciones de esa tarde).
