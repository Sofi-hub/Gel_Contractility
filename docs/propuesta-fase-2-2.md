# Fase 2.2: qué es un evento — propuesta medida

2026-10-01, chat de implementación. **APLICADA el 2026-10-01** (ver "Cómo quedó" al final). Resuelve
H8, H33, H34 y H55 de `hallazgos-revision-codigo.md`. Laboratorio: se reimplementó solo
la detección, con el mismo detrend, la misma MAD y la misma elección de `k`, y se
comparó sobre (a) cinco escenarios sintéticos de conteo conocido, 30 series con
ruido blanco y 30 con ruido correlacionado cada uno, y (b) los seis videos vigentes.

## El problema

Hoy un evento es "un pico que supera `k`·ruido **sobre el reposo** y está a ≥ `sep_s`
= 0.3 s del siguiente" (si hay dos más cerca, gana el más alto). Eso tiene dos modos
de falla, los dos medidos:

- **Funde eventos reales cercanos** (H8). Video_prueba tiene una ráfaga con eventos a
  0.27–0.29 s: la señal vuelve al reposo entre ellos (−0.6 MAD) y cada uno sube a ~20 MAD,
  pero el de 15.278 s se borra por estar a 8 fotogramas de otro más alto.
- **Convierte la cola de un evento lento en otro evento** (H55). Con eventos como los de
  Video_583, un repunte de ruido en la bajada supera la altura y está a > 0.3 s del pico.

Los dos vienen de lo mismo: `sep_s` es un tiempo absoluto, y "separado" no es una
cuestión de tiempo sino de si la señal **baja entre los dos picos**.

## Reglas comparadas

| | definición de evento |
|---|---|
| **A** (actual) | altura ≥ k·ruido, separación ≥ 0.3 s |
| **B** (propuesta) | altura ≥ k·ruido **y prominencia ≥ k·ruido**, sin separación mínima |
| C | altura ≥ k·ruido, separación ≥ 0.5 × duración medida del evento |

**Prominencia**: cuánto sobresale el pico por encima del valle más alto que lo separa de
un pico más alto. Un repunte en la cola de otro evento tiene prominencia ≈ ruido; un
evento real dentro de una ráfaga, prominencia ≈ su altura. No depende de ninguna escala
de tiempo. El control de falsos usa la misma regla sobre la señal invertida.

## Resultados

**Sintéticos: series con el conteo exacto y reportable (de 30)**

| escenario | ruido | A | B | C |
|---|---|---|---|---|
| rápidos (como 063/268) | blanco / correl. | 30 / 30 | **30 / 30** | 29 / 30 |
| lentos (como 583) | blanco / correl. | 20 / 16 | **30 / 30** | 24 / 20 |
| lentos con meseta (como 466) | blanco / correl. | 9 / 14 | **30 / 30** | 24 / 26 |
| ráfaga a 0.28 s (como prueba) | blanco / correl. | 0 / 0 | **30 / 30** | 29 / 30 |
| espontáneos chicos + estimulados | blanco / correl. | 30 / 30 | **30 / 30** | 27 / 29 |

**Videos reales: A contra B**

| video | A | B | diferencia |
|---|---|---|---|
| Video_prueba | 28, k 6 (6–15) | **29**, k 6 (6–15) | B agrega 15.278 s (19.5 MAD, real: ver arriba). Estimulados 7, período 10.00744 s, iguales |
| Video_063 | 6, k 6 (6–8) | 6, k 6 (6–8) | ninguna |
| Video_268 | 6, k 6 (6–20) | 6, k 6 (6–20) | ninguna |
| Video_466 | 5, k 4 (4–15) | 5, k 4 (4–15) | ninguna |
| Video_583 | 6, k 12 (12–20) | 6, k 12 (12–20) | ninguna |
| Video_491 | no reportable | no reportable | ninguna en el veredicto |

**`win_s` (ventana del detrend) con la regla B:** entre 1.5 y 5 s, cinco videos no cambian
y los sintéticos dan 30/30 en todos los casos. Con 1 s cambian tres videos (063, 268, 583):
es demasiado corta para eventos de hasta 0.6 s (H42). Video_491 es el único sensible:
no reportable con 1.5–2 s, 2 eventos con 3–5 s. Medir la ventana en segundos reales en
lugar de muestras (H16) no cambia ningún conteo.

**Grilla de `k` y elección de meseta con la regla B** (grilla fina ×1.1 de 3 a 24, meseta
= tramo que abarca ≥ ×1.25 en `k`): mismos conteos en los seis. En 300 sintéticos, la regla
"meseta de `k` más bajo" nunca eligió mal; cuando hay dos mesetas (eventos chicos y
grandes), la de `k` más bajo es la que cuenta todos. El contraejemplo de H55 desaparece
porque existía solo por las colas contadas como eventos. Video_063 sigue con dos mesetas
(6 eventos en k 5.3–8.6; 5 en 9.4–24): eso es H11 y lo decide si el evento de 0.31 s es
real, no un parámetro.

## Propuesta

1. **Evento = altura y prominencia ≥ k·ruido.** `--sep-s` deja de ser necesario; queda
   como opción manual, apagada por defecto. Se va el aviso de fusión (`picos_con_sep_menor`),
   que ya no aplica.
2. **`win_s` = 2 s, con regla escrita y control de estabilidad.** Regla: la ventana tiene que
   ser al menos 3 veces la duración del evento más largo (hoy 0.6 s). Control: el conteo es
   reportable solo si da lo mismo, con meseta, con 1.5, 2 y 3 s; si no, "no reportable:
   depende de la ventana". Aviso si la duración medida supera `win_s`/3. En los seis videos
   no cambia ningún veredicto (Video_491 sigue no reportable, ahora con el motivo correcto).
3. **Meseta de `k` más bajo (se mantiene), medida en una grilla fina y definida por su ancho
   en `k` (≥ ×1.25), no por "2 puntos de la grilla".** Se reporta el `k` en el centro
   geométrico de la meseta (lejos del borde donde empiezan los falsos, H34) y **todas** las
   mesetas encontradas, para que Video_063 diga "6 (hay otra meseta con 5)".
4. **Nueva línea base: Video_prueba = 29 eventos.** Lo demás, igual. `test_seleccion_k.py` se
   actualiza y se agrega `tests/test_deteccion.py` con los cinco escenarios sintéticos, que
   **corre el escaneo real** (lo que H9 pedía: hoy la prueba no corre la detección).

Opcional: mediana móvil en segundos reales (H16). No cambia conteos; es más correcta con
los saltos de Video_466, pero mueve algunos decimales de ruido y amplitud.

---

## Cómo quedó al aplicarla (2026-10-01)

**Un cambio respecto de la propuesta, por Video_491.** Franco observó que el evento de Video_491
parece más largo que los de los otros videos. Medido: dura ~1.03 s, y con la ventana fija de 2 s la
mediana móvil "bajaba con el evento" y se comía la mitad de la contracción. La regla del punto 2
("la ventana, al menos 3 veces el evento más largo") se implementó entonces **automática** en vez de
solo avisar: una primera pasada con ventana de 10 s mide la duración de los eventos claros (≥ 10 MAD,
tramo por encima del 10 % del pico y de 3 MAD), y la ventana es `max(2 s, 3 × la más larga)`. En los
otros cinco videos da 2 s (eventos de 0.2–0.6 s), así que no cambian; en Video_491 da 3.1 s.

**Implementación** (`scripts/contraction_report.py`): `detectar()` (altura + prominencia),
`K_GRILLA` (23 valores, ×1.1), `FACTOR_MESETA` = 1.25, `elegir_k_meseta()` con `k` en el centro
geométrico y la lista de mesetas, `duracion_eventos()` y `ventana_deriva()`, control de estabilidad con
0.75×, 1× y 1.5× la ventana. `--win-s` por defecto `auto`; `--sep-s` apagado. Figura 05 con la
grilla fina y las otras mesetas en naranja. Cuaderno actualizado (`WIN_DERIVA_S = None`, `SEP_S = None`).

**Resultados**

| video | antes | ahora | qué cambió en la hoja |
|---|---|---|---|
| Video_prueba | 28 | **29** | todo lo que depende de la lista de eventos (espontáneas 21 → 22; estimulados y período iguales) |
| Video_063 | 6 | 6 | `k_usado` 6 → 6.43, rango de meseta, hoja `estab`; ahora lista la otra meseta (5 ev) |
| Video_268 | 6 | 6 | `k_usado`, rango, `estab` |
| Video_466 | 5 | 5 | `k_usado`, rango, `estab`; desaparece `picos_con_sep_menor` |
| Video_583 | 6 | 6 | `k_usado`, rango, `estab`; desaparece `picos_con_sep_menor` |
| Video_491 | no reportable (2, auditoría) | **2, reportable** | eventos en 13.01 y 33.96 s; ventana 3.1 s; TTP 570 ms, RT50 467 ms |

**Pruebas:** `test_deteccion.py` (nuevo) corre la detección entera sobre seis escenarios sintéticos
(12 series cada uno): 72/72 exactos. Con la regla vieja falla en cuatro escenarios, y en el de eventos
de 1 s da 6–7 eventos **marcados como reportables** donde hay 3. `test_seleccion_k.py` 16/16 (los
escaneos históricos de la grilla gruesa se evalúan con la regla de 2 puntos), `test_nan.py` y
`test_cinetica.py` OK.
