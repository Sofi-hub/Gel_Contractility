# Respuesta forzada a una frecuencia conocida (2026-10-19)

**Pregunta:** en 4 videos de Andrés (10V_2, 10V_3, 20V_1, 40V_2) y en 20V_2 se ve respuesta cada 10 s, pero el reporte normal los deja NO REPORTABLES (ruido o sacudidas). Si se sabe cuándo dispara el estimulador, ¿se puede medir la respuesta sin tener que detectar cada contracción?

**Método** (`forzada.py`; reglas fijadas antes de mirar los no reportables; solo lee las series, no toca el análisis):
1. `center_px` sin deriva (mediana móvil de 2 s).
2. Período fijo: 10.10 s en los de Andrés (lo que miden sus 4 reportables) y 10.00 s en los videos con timestamps reales.
3. **¿Hay respuesta?** Se pliega la señal al período (promedio de todos los ciclos desde 8 s) y se mide cuánto sobresale el pico (SNR). Lo mismo con 40 períodos de control que no son el del estimulador (0.55–0.9 y 1.15–1.75 T). p = (1 + controles con SNR ≥ la del período real) / 41; **el mínimo posible es 0.024** (ninguno de los 40 controles lo iguala).
4. **¿Cuánto?** En cada pulso esperado: pico en ±0.2 s menos la mediana de 1.2–0.4 s antes. Lo mismo en instantes sin pulso (2–8 s después de cada pulso, cada 0.5 s); un pulso "responde" si supera el percentil 95 de esos controles. Se informa la mediana de los pulsos (px y % del grosor).

## Resultado (`forzada.csv`)

| video | reporte normal | p | pulsos que responden | amplitud forzada | control p95 |
|---|---|---|---|---|---|
| 10V_1 | 6, reportable, 1.16 px | 0.024 | 6/6 | 1.17 px (0.059 %) | 0.20 px |
| 20V_3 | 6, reportable, 1.64 px | 0.024 | 6/6 | 1.66 px (0.085 %) | 0.23 px |
| 40V_1 | 5, reportable, 1.67 px | 0.024 | 5/5 | 1.69 px (0.086 %) | 0.17 px |
| 40V_3 | 6, reportable, 0.76 px | 0.024 | 6/6 | 0.77 px (0.034 %) | 0.28 px |
| Video_063 (bordes) | 6, reportable, 1.59 px | 0.024 | 5/5 | 1.59 px (0.56 %) | 0.08 px |
| **10V_2** | NO REPORTABLE | 0.024 | 6/6 | **0.44 px (0.022 %)** | 0.25 px |
| **10V_3** | NO REPORTABLE (sacudida) | 0.024 | 6/6 | **6.02 px (0.26 %)** | 1.18 px |
| **20V_1** | NO REPORTABLE | 0.024 | 6/6 | **1.93 px (0.084 %)** | 1.06 px |
| **20V_2** | NO REPORTABLE | 0.024 | 6/6 | **2.94 px (0.125 %)** | 1.76 px |
| **40V_2** | NO REPORTABLE | 0.024 | 6/6 | **0.59 px (0.029 %)** | 0.30 px |
| Video_613 (control) | sin respuesta (B7) | 0.63 | 1/7 | — | 0.32 px |
| Video_068 (control) | sin respuesta (B7) | 0.22 | 3/6 | — | 12.2 px |

- **Validación:** en los 5 reportables la amplitud forzada coincide con la del reporte normal (diferencia ≤ 1.5 %). Los dos controles negativos (613, 068) **no** pasan (p = 0.63 y 0.22).
- **Los 5 NO REPORTABLES de Andrés tienen respuesta al estímulo clara:** p mínimo y 6 de 6 pulsos por encima de los controles, todos. Con esto los 9 videos de Andrés responden a 0.1 Hz.
- **Límites:**
  - Supone el período (10.10 s, de los propios videos) y que el estimulador estaba encendido; mide la respuesta **a ese reloj**, no cuenta contracciones ni ve espontáneas.
  - En 068 (actividad continua) la prueba por pulso sola daría 3/6: **la que decide es la del plegado (p)**; la amplitud por pulso solo se informa si p es significativo.
  - 10V_2, 40V_2 (y 40V_3) son respuestas de < 1 px: valen las salvedades del aviso de textura (amplitud ±15–20 %). 20V_1 y 20V_2 tienen ruido alto (control p95 1–1.8 px) y respuestas bifásicas.
  - TTP/RT50 no se miden así.

## Propuesta (sin implementar: cambia números informados)
Agregar al reporte una sección **RESPUESTA FORZADA** que corra solo cuando se pasa `--frecuencia-estimulo` y el conteo sale NO REPORTABLE, con p, pulsos que responden y amplitud (px y %), marcada como "respuesta al estímulo, no conteo". El veredicto del conteo no cambia.

## Implementado (2026-10-19, aprobado por Franco)
- `src/forzada.py`, llamado desde `scripts/contraction_report.py` solo con `--frecuencia-estimulo` y conteo NO REPORTABLE: sección `RESPUESTA FORZADA` en la consola, columnas `forzada_*` en `resumen_*` y hoja `forzada_*` (un renglón por pulso). El veredicto del conteo y todos los demás números no cambian (regresión de los 11 igual).
- Diferencia con la medición de arriba: si el reporte no encontró tren, el período se busca a ±2 % de 1/f (los controles con la misma búsqueda). Da 10.09–10.12 s en los de Andrés y los mismos resultados (10V_2 0.44 px, 10V_3 6.02, 20V_1 1.93, 20V_2 2.94, 40V_2 0.58); 613 p = 0.78 y 068 p = 0.68.
- **Sensibilidad** (`tests/test_forzada.py`, ruido blanco): pulsos de 5 × el ruido por fotograma se ven siempre con la amplitud a ±20 %; de 3 ×, se ven siempre pero la amplitud sale ~10–30 % alta; de 2 ×, 2 de 5. Ruido solo o con sacudidas: 0 falsas respuestas en 20.
- **Falta:** mostrarla en el informe HTML, la ventana y la tabla de `procesar_carpeta`.
