# D2 / H52: el "peine" de compresión en todos los videos (2026-10-10)

**Pregunta:** el salto de brillo cada pocos fotogramas (visto en 476 y en |dI| de 063), ¿aparece en los otros RARITOS y no en los OK? ¿Pasa a los bordes?

**Cómo:** `medir_d2.py`. Tipo de cada fotograma comprimido (I, P o B) con `ffprobe` (`tipos_<video>.csv`), y las series de `motion_check.py` sin cambios (`../d1_d2_intensidad/`). Se compara |dI| en los fotogramas P (o I) contra los B, en el fondo (sin gel) y en el gel; y lo mismo con |Δ center_px|. Además, cuánto se corre `center_px` en promedio según la fase del patrón (px).

**Los 11 videos son H.264 con el mismo patrón:** un fotograma P cada 4 (B B B P; en 466, 613 y 068 cada 2), un I cada ~29. Los P pesan 4–10 veces más que los B. El peine es eso.

| video | grupo | P cada | bytes P/B | \|dI\| P/B fondo | \|dI\| P/B gel | \|Δcenter\| P/B (mediana) | center: corrimiento por fase (px) | ídem / ruido rápido |
|---|---|---|---|---|---|---|---|---|
| Video_prueba | — | 4 | 6.7 | 1.17 | 1.26 | 1.03 | 0.004 | 0.02 |
| 063 | OK | 4 | 8.2 | 1.12 | 1.34 | **2.09** | 0.001 | 0.02 |
| 268 | OK | 4 | 9.7 | 1.13 | 1.37 | **1.84** | 0.003 | 0.03 |
| 466 | OK | 2 | 6.6 | 1.04 | 1.10 | 1.10 | 0.007 | 0.01 |
| 583 | OK | 4 | 6.9 | 1.10 | 1.22 | 1.16 | 0.016 | 0.04 |
| 491 | OK | 4 | 8.3 | 1.14 | 1.33 | 1.12 | 0.001 | 0.00 |
| 476 | RARITOS | 4 | 7.6 | 1.12 | 1.32 | 1.05 | 0.001 | 0.01 |
| 613 | RARITOS | 2 | 6.8 | 1.04 | 1.09 | 1.02 | 0.002 | 0.05 |
| 068 | RARITOS | 2 | 3.7 | 1.04 | 1.02 | 1.00 | 0.147 | 0.09 |
| 304 | RARITOS | 4 | 5.0 | 1.12 | 1.10 | 1.08 | 0.002 | 0.01 |
| 341 | RARITOS | 4 | 6.6 | 1.20 | 1.18 | 1.42 | 0.006 | 0.03 |

**Resultado:**
1. **El peine está en los 11 videos, OK y RARITOS por igual** (|dI| 4–20 % más alto en los P en el fondo, 10–37 % en el gel). No es lo que separa a los RARITOS. D2 se cierra con "no".
2. **A los bordes casi no pasa:** el corrimiento sistemático de `center_px` según la fase del patrón es ≤ 0.016 px (≤ 5 % del ruido rápido; 068 0.15 px con ruido de 1.7). En los dos videos más limpios (063 y 268, ruido 0.02–0.05 px) los saltos de `center_px` en los P son ~2 veces los de los B: la compresión agrega un poco de ruido ahí, pero sin sesgo. Nada que corregir.
3. Para la comparación con MuscleMotion (H52): un método por intensidad sí arrastra el peine (es justamente |dI|). Es un argumento más a favor de medir bordes.

No cambia ningún número.
