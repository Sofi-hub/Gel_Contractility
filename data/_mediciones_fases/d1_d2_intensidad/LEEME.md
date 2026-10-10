# D1: tamaño por intensidad / tamaño por bordes en los 11 videos (2026-10-10)

**Pregunta:** 466 da 0.88 y 476 0.82 (intensidad/bordes). ¿Pasa en toda la tanda EXP5?

**Cómo:**
- `correr_motion_check.sh`: `motion_check.py` **sin cambios** sobre los 11 videos (en una carpeta por video acá se guardó solo `movimiento_<video>.xlsx`; los gráficos se borraron, se rehacen corriendo el script; no toca `processed_data`).
- `medir_d1.py`: el mismo cociente calculado de cuatro maneras. El de `motion_check` es una pendiente de mínimos cuadrados (`ols`), que **sale más chica que la verdadera cuando `center_px` tiene ruido propio** (atenuación por regresión). Por eso se agrega `eventos`: la mediana, evento por evento, de (pico por intensidad)/(pico por bordes), que solo depende de las contracciones.

| video | tanda | ols (motion_check) | std/std | eventos (mediana, IQR) | n |
|---|---|---|---|---|---|
| Video_prueba | — | 0.96 | 0.96 | 0.96 (0.94–0.97) | 29 |
| 063 | CTRL1 | 0.94 | 0.96 | 0.99 (0.97–1.00) | 6 |
| 268 | EXP3 | 0.76 | 0.81 | **0.88** (0.88–0.90) | 6 |
| 466 | EXP5 | 0.85 | 0.88 | **0.86** (0.85–0.87) | 5 |
| 476 | EXP5 | 0.82 | 0.90 | **0.99** (0.93–1.01) | 6 |
| 491 | EXP5 | 0.75 | 0.80 | **0.86** (0.86–0.87) | 2 |
| 583 | EXP6 | 1.00 | 1.01 | 0.99 (0.97–1.02) | 6 |
| 613, 068, 304, 341 | — | 0.90, 0.97, 0.93, 0.92 | | (no reportables) | |

**Resultado:**
1. **El 0.82 de 476 era del estimador, no del gel:** evento por evento da 0.99. Su `center_px` es ruidoso (0.115 px) y eso achica la pendiente.
2. **No es cosa de la tanda EXP5:** de los tres EXP5, 466 y 491 dan 0.86 y 476 da 0.99; y 268 (EXP3) también da 0.88. Quedan **tres videos (268, 466, 491) donde la intensidad ve ~12–14 % menos** que los bordes, de forma pareja en todos sus eventos; los otros cuatro reportables dan 0.96–0.99.
3. Sigue sin saberse cuál de los dos está más cerca de la verdad en esos tres. Una explicación posible del lado de la intensidad: la correlación de perfiles mide el corrimiento de TODA la franja vertical (bordes + textura interior); si el interior se mueve menos que los bordes (deformación no rígida), la intensidad da menos. No hay medición que lo decida todavía.
4. Ojo con 063 y 466: con la ROI y el código de hoy, `ols` da 0.94 y 0.85 (CLAUDE.md dice 0.99 y 0.88, medidos en la Fase 4 con otra ROI de 063).

**Propuesta chica (no cambia ningún número informado):** que el veredicto de `motion_check` muestre también el cociente por eventos, que no se achica con el ruido. Cambia solo un texto de diagnóstico; queda para tu visto bueno porque cambia la cifra que imprime `motion_check` (476: 0.82 → 0.99).

Tabla: `tabla_d1.csv`.
