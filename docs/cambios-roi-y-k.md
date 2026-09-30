# Cambios de código: ROI automática y elección de k

Fecha 2026-09-29. Aplicados en `main.py`, `src/pipeline.py`,
`src/preprocessing.py`, `scripts/contraction_report.py`, más
`tests/test_seleccion_k.py` (nuevo). Resultados en
`data/processed_data/<video>_v5/`.

## 1. ROI: el ancho mínimo ya no depende del largo del gel

**Antes:** `min_width = 0.35 × (columnas con gel)`. Con un gel que ocupa
~1850 columnas, exigía una ROI de ~647 px. Las gauge regions reales de la
batería miden 225–470 px, así que ningún criterio estricto podía cumplirlo y
la cascada se relajaba sola hasta `solo_nitidez` o `franja_completa`.

**Ahora:** `min_width = n_columns × min_column_spacing_px` (60 × 3 = 180 px
por defecto). El ancho mínimo no tiene por qué depender de cuán largo es el
gel: depende de cuántas columnas se muestrean y de cuán juntas pueden estar
sin compartir el mismo ruido de imagen y el mismo tile de CLAHE.

Flags nuevos: `--roi-min-spacing` (default 3.0) y `--roi-max-variacion`
(default 6.0).

## 2. ROI: rescate por barrido cuando la cascada falla

La cascada evalúa el **bloque contiguo más largo** de cada criterio. Si el
gel tiene una cintura corta dentro de una franja larga, ese bloque incluye
los hombros y ningún nivel da una ROI plana.

Agregué `_widest_flat_window`: barrido de dos punteros que encuentra la
ventana contigua más ancha con variación de grosor ≤ 6 %.

**Va después de la cascada, no antes, y eso importa.** Lo probé primero como
nivel 0 prioritario y **empeoraba los dos videos validados**: maximizar el
ancho contra el límite del 6 % se pega al borde y agarra columnas del hombro.

| | cascada (`gauge_cintura`) | barrido |
|---|---|---|
| Video_prueba | 5.32 %, residuo 0.787 px | 5.98 %, residuo 0.817 px |
| Video_063 | 4.91 %, residuo 0.822 px | 5.96 %, residuo 1.052 px |

Es una red de seguridad, no una mejora. Sólo se activa si la cascada no
produjo una ROI que cumpla el criterio.

## 3. Veredicto explícito y `--exigir-roi`

`roi_quality` ahora trae `cumple_criterio_aceptacion`, y la hoja `resumen`
registra `ROI cumple criterio` y `ROI ancho minimo exigido (px)`. El flag
`--exigir-roi` aborta en vez de avisar y seguir emitiendo números.

## 4. `k` se elige solo, dentro de la meseta

`--k auto` es el default. `elegir_k_meseta()` aplica la regla del protocolo:
tramo de conteo constante con `falsos_control = 0` en todo el tramo.

Dos decisiones que salieron de encontrarme el error yo mismo:

**Cuál meseta, cuando hay varias: la de `k` más bajo.** Al subir el umbral se
pierden eventos reales, así que la primera meseta con 0 falsos es la que ya
eliminó el ruido y todavía no empezó a comerse señal. Mi primera versión
tomaba "la meseta más larga" y daba **5 eventos en Video_063**, donde la
respuesta validada es 6 (hay meseta de 6 en k=6..8, de 2 puntos, y otra de 5
en k=10..20, de 4 puntos).

**Filtrar los falsos ANTES de buscar el tramo constante, no después.** Mi
segunda versión agrupaba por conteo y después exigía 0 falsos en todo el
grupo. En Video_466 el tramo de 5 eventos empieza en k=6, donde todavía hay 1
falso, y eso invalidaba la meseta real (k=8..15) entera.

Si no hay meseta, el reporte lo dice, marca el conteo `[NO REPORTABLE]` y
graba `conteo_reportable = False`. No se niega a correr: hay que poder
auditar el gráfico.

## 5. Crash arreglado

`contraction_report.py` abortaba con `KeyError: 'resumen_grupos'` cuando
`rhythm_split` no encontraba tren — justo el caso de un video sin eventos,
donde más importa que el reporte salga. Video_491 ahora genera su
`contracciones.xlsx`.

## 6. Test de regresión

`tests/test_seleccion_k.py` guarda los diez escaneos reales con su respuesta
validada, incluidos los dos videos de referencia. Correr con
`python tests/test_seleccion_k.py`. Pasa 10/10.

---

# Verificación

## Los dos videos validados no cambian

Corridos de punta a punta con el código nuevo, sin forzar nada:

| | ROI | variación | residuo | eventos | período |
|---|---|---|---|---|---|
| Video_prueba | `gauge_cintura` 454–1516 | 5.32 % | 0.787 px | **29** | **10.09118 ± 0.00232 s** |
| Video_063 | `gauge_cintura` 390–1423 | 4.91 % | 0.822 px | **6** | **10.04356 ± 0.00432 s** |

Idénticos a los documentados. Video_prueba mantiene 6 estimulados + 1 dudoso
+ 22 espontáneos con CV 90.9 %; Video_063 mantiene 4 + 1 dudoso + 1
espontáneo. `k` se eligió solo y dio 6 en los dos.

## La batería, sin forzar ROI ni k

| | método ROI (auto) | ROI | var | k (auto) | eventos | frecuencia |
|---|---|---|---|---|---|---|
| Video_268 | `gauge_cintura` | 918–1328 | 5.24 % | 6 (meseta 6–20) | 6 | **0.10000 ± 0.000030 Hz** |
| Video_583 | `gauge_cintura` | 718–1187 | 5.83 % | 12 (meseta 12–20) | 6 | **0.09997 ± 0.000100 Hz** |
| Video_466 | `gauge_rescate_plana` | 944–1169 | 5.77 % | 8 (meseta 8–15) | 5 | 0.10515 ± 0.000414 Hz |
| Video_491 | `gauge_cintura` | 459–1206 | 5.08 % | 10, **sin meseta** | 2 | — |

El automático llega solo a las mismas ventanas que yo había puesto a mano, y
**Video_268 mejoró**: 0.10000 ± 0.000030 Hz, exacto, con jitter 9.6 ms (por
debajo de un fotograma). La corrida manual anterior daba 10.00667 s porque mi
ventana era un poco más ancha.

La cascada corregida resuelve sola tres de los cuatro. El rescate por barrido
se activa únicamente en Video_466.

## Lo que sigue sin cerrar

- **Video_466**: outliers 16.2 % y frecuencia +5.15 % sobre lo configurado
  (t = 12.4, jitter 133 ms). Son 285.5 fotogramas por período contra 300.0
  exactos de los otros cuatro. Falta `inspect_frame.py` y el cuaderno de
  laboratorio.
- **Video_491**: sin meseta, no reportable.
- **Bug del signo** en `cociente_robusto_pct`: sin tocar, por decisión tuya.
