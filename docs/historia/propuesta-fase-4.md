# Fase 4

Orden acordado con Franco (2026-10-07): (1) H24, chequeo 2; (2) `motion_check.py` (H50, H51);
(3) `signal_check.py` (H49); (4) sexto evento de Video_063 (H11); (5) ráfaga final de Video_583
(72–73.7 s). Mismas reglas que en la Fase 3: medir y proponer primero; regenerar y documentar una
sola vez al cerrar.

---

## Punto 1. H24: un criterio de ajuste comparable entre ROIs

**Problema.** El chequeo 2 (`outlier_frac` < 10 %) usa un umbral de descarte que se adapta a
cada fotograma (3×MAD). Una ROI con bordes limpios tiene un umbral estricto y descarta más.

**Candidatos:** (a) residuo del ajuste en px; (b) residuo / grosor; (c) columnas descartadas
de forma sistemática (> 50 % de los fotogramas); (d) `outlier_frac` (referencia). **Referencia de
calidad:** ruido del canal (MAD de `center_px` sin deriva, mediana móvil de 61 muestras) dentro del
mismo video.

### Medición 1 (2026-10-07): series ya guardadas, sin reprocesar

Fuentes: los seis vigentes + `_superadas/Video_063_v6` (ROI ancha) + `_superadas/Video_466_v6`
(ROI manual) + `_v4/_v5` de 466 (rescate viejo 944–1169; los dos son iguales). Residuo = mediana
por fotograma de `residual_*_px`; se usa el peor borde.

| video / ROI | outlier_frac | residuo sup / inf (px) | residuo / grosor | ruido canal (px) |
|---|---|---|---|---|
| 063 chica 875–1039 (vigente) | 6.8 % | 0.45 / 0.43 | 0.16 % | **0.024** |
| 063 ancha 390–1423 | 7.7 % | 0.88 / 0.78 | 0.31 % | 0.034 |
| 466 cintura 696–846 (vigente) | 10.5 % | 1.32 / 0.59 | 0.66 % | **0.182** |
| 466 rescate 944–1169 | 16.2 % | 0.82 / 0.72 | 0.40 % | 0.192 |
| 466 manual 700–900 | 7.9 % | 1.75 / 0.68 | 0.87 % | 0.212 |
| Video_prueba | 3.6 % | 0.77 / 0.80 | 0.27 % | 0.085 |
| 268 | 2.0 % | 0.88 / 0.73 | 0.33 % | 0.049 |
| 583 | 4.0 % | 0.86 / 1.43 | 0.61 % | 0.072 |
| 491 | 4.2 % | 0.97 / 0.94 | 0.38 % | 0.063 |

**Lectura.** En 063 los tres criterios ordenan igual que el ruido. En 466 ninguno: `outlier_frac`
elige la manual (la peor) y el residuo el rescate. Entre videos el ruido no sirve de vara.

### Medición 2 (2026-10-07): por columna, `scripts/medir_chequeo2.py`

Corrida por Franco sobre 063 y 466 (salida en `data/fase4_chequeo2/`). Nuevas medidas:
**error de modelo** = RMS sobre columnas del residuo mediano en el tiempo de cada columna (cuánto
se aparta la parábola del borde de forma estable); columnas sistemáticas (> 50 % de fotogramas
descartadas); fotogramas con ≥ 3 descartes seguidos. Se agregaron dos ROIs de 466 de la Etapa 2
(877–1177, 1500–1700).

| ROI | outlier_frac | error modelo peor / grosor | residuo peor / grosor | racha ≥3 (sup/inf) | ruido canal |
|---|---|---|---|---|---|
| 063 chica (vigente) | 6.8 % | 0.54 % | 0.16 % | 21 / 0 % | **0.024** |
| 063 ancha | 7.7 % | 0.83 % | 0.31 % | 0 / 55 % | 0.034 |
| 466 1500–1700 | 5.5 % | 0.30 % | 0.28 % | 39 / 27 % | **0.131** |
| 466 cintura (vigente) | 10.5 % | 1.01 % | 0.66 % | 39 / 38 % | 0.182 |
| 466 rescate | 16.2 % | 1.32 % | 0.40 % | 71 / 100 % | 0.192 |
| 466 877–1177 | 12.1 % | 1.40 % | 0.52 % | 57 / 100 % | 0.205 |
| 466 manual | 8.0 % | 1.13 % | 0.87 % | 23 / 32 % | 0.212 |

Concordancia de orden con el ruido en las 5 ROIs de 466 (Spearman): error de modelo 0.7,
residuo 0.7, `outlier_frac` 0.3. Las rachas y las columnas sistemáticas no ordenan.

**Lectura.**
- `outlier_frac` es el peor de los candidatos; el error de modelo y el residuo, mejores pero no
  perfectos. Ninguno ordena las cinco bien. Las diferencias de ruido entre 0.18 y 0.21 son chicas.
- **La ROI 1500–1700 tiene el menor ruido de 466 pero NO es la gauge region** (grosor 284 px contra
  201 de la cintura, variación 13.9 %: hombro del anclaje). El ruido del canal tampoco es una vara
  completa: una zona con menos ruido puede medir la mecánica equivocada. La forma del gel (cintura,
  planitud) tiene que seguir mandando sobre la ROI; el ajuste solo puede avisar.
- Ningún número de esta tabla sirve para fijar un umbral (dos videos).

**Propuesta:** el chequeo 2 deja de ser criterio de aceptación. La aceptación de la ROI queda en la
forma (variación ≤ 6 %, contiene la cintura). En `resumen` se registran como diagnóstico
`outlier_frac` y el error de modelo relativo, sin umbral, y se revisan con `RARITOS`. La calidad de
la medida ya la juzga el reporte (meseta, señal/ruido).

**Decisión (Franco, 2026-10-07): aprobada.** Se implementa al cerrar la Fase 4 (`main.py`: el
chequeo 2 pasa a diagnóstico; hoja `resumen` con `outlier_frac medio` y `error de modelo relativo`;
sin aviso "en el límite"). El cálculo del error de modelo por columna sale de
`scripts/medir_chequeo2.py`.

Estado: **cerrado, pendiente de implementar.**

---

## Punto 2. `motion_check.py` (H50, H51)

**Qué hace.** Mide, sin usar los bordes, qué se mueve: |ΔI| entre fotogramas (gel, interior,
fondo) y dos desplazamientos por correlación de perfiles (`desp_vert_px`, `desp_axial_px`). Es la
única verificación independiente de `center_px` y de lo que mide MuscleMotion.

**Defectos (leído el código vigente, 2026-10-07):**
1. `_subpixel_shift` (H51): normaliza los perfiles enteros y después suma productos sólo sobre la
   parte superpuesta, sin renormalizar por lag. Penaliza los lags ≠ 0 y achica el corrimiento
   (0.18–0.43 × aun con verdad perfecta; Fase 3, tema 7). Arreglo: Pearson sobre la superposición
   (sintético: 0.248 / 0.499 / 0.997 / 1.997 / 2.998 para 0.25 / 0.5 / 1 / 2 / 3 px).
2. Veredicto (H50): deduce "cambio de grosor" de que el interior se mueva < 2× el fondo. Un gel sin
   textura que se traslada también mueve solo los bordes. El corte de 2× es arbitrario.
3. Eje de tiempo `idx / fps declarado` (hasta 0.33 s de error a mitad del video); debe ser PTS.
4. Interpreta el skew suponiendo contracciones hacia abajo (mismo error que H49).
5. Menores: descarta el primer fotograma; la referencia de la correlación es el primer fotograma.

**Propuesta de medición:** arreglar 1, 3 y 4 en una copia y correrla sobre Video_prueba, 063 y 466.
Comparar, evento por evento, la amplitud de `desp_vert_px` contra la de `center_px` (de
`serie_temporal.xlsx`). Si el arreglo es correcto, el cociente tiene que dar ~1 (antes 0.18).
Recién con eso se reescribe el veredicto (2), basado en `desp_vert` (traslación) contra el cambio de
grosor, no en |ΔI|.

### Medición (2026-10-07): `scripts/medir_motion_check.py`, corrido por Franco

Perfil vertical de la franja (ROI vigente) contra el primer fotograma; eje PTS; comparado con
`center_px` sin deriva. Salida en `data/fase4_motion/`.

Autoprueba (perfil sintético corrido una cantidad conocida): viejo 0.025 / 0.10 / 0.30 px para
0.25 / 1 / 3 px; nuevo 0.250 / 0.997 / 2.997.

| video | eventos | cociente mediano en eventos (viejo → nuevo) | pendiente todo el video (viejo → nuevo) | correlación nuevo | ruido center / intensidad (px) |
|---|---|---|---|---|---|
| Video_prueba | 29 | 0.18 → **0.96** | 0.41 → 0.96 | 0.996 | 0.085 / 0.065 |
| Video_063 | 6 | 0.52 → **0.99** | 0.46 → 0.94 | 0.974 | 0.024 / 0.011 |
| Video_466 | 5 | 0.29 → **0.88** | 0.23 → 0.85 | 0.959 | 0.182 / 0.097 |

**Lectura.**
- **H51 cerrado:** con la correlación arreglada, dos métodos que no comparten nada (bordes e
  intensidad) dan la misma amplitud en Video_prueba y 063 (96–99 %). El 0.18 era el defecto.
- **466 queda 12 % abajo.** En la Fase 3, con desplazamiento conocido, los bordes con CLAHE de 466
  medían 0.92× de la verdad; acá la intensidad mide 0.88× de los bordes. No está resuelto cuál está
  más cerca: queda anotado (el % del grosor de 466 puede estar subestimado hasta ~10–20 %).
- **Evidencia para H11:** el sexto evento de Video_063 (t = 0.308 s) aparece también por intensidad
  (0.28 px contra 0.36 px por bordes). Es movimiento real de la franja, no un artefacto del borde.
- El canal por intensidad tiene menos ruido que `center_px` en los tres (promedia todo el perfil).
  Solo se registra; no se propone cambiar el observable.

**Propuesta para `motion_check.py`:**
1. `_subpixel_shift` → Pearson sobre la superposición (la versión de `medir_motion_check.py`).
2. Eje de tiempo por PTS; no descartar el primer fotograma.
3. Skew: reportar el sentido de la cola pesada (como `_signo_evento`), no exigir negativo.
4. Veredicto nuevo: si existe `serie_temporal.xlsx` del video, comparar `desp_vert_px` con
   `center_px` (cociente y correlación) y decir "la traslación por intensidad confirma / no confirma
   a `center_px`". Se borra el razonamiento "solo bordes ⇒ grosor" y el corte de 2× el fondo; los
   canales |ΔI| quedan como información (sirven para comparar con MuscleMotion, H52).

**Decisión (Franco, 2026-10-07): aprobada.** Se implementa al cerrar la Fase 4.

**Abierto / probado en pocos videos:** (a) 466: intensidad 0.88× bordes, sin saber cuál está más
cerca de la verdad; (b) el cociente ~1 se midió en 3 videos (prueba, 063, 466): repetir en 268,
583, 491 y `RARITOS`; (c) el canal por intensidad tiene menos ruido que `center_px` en los tres:
no se usa, pero mirar si se sostiene.

---

## Punto 3. `signal_check.py` (H49)

**Qué hace.** Sin umbrales: mira si la señal sin deriva tiene una cola larga hacia un lado (skew y %
de muestras más allá de ±4σ). El ruido es simétrico; una población de contracciones no.

**Defectos:** exige la cola hacia ABAJO (skew ≤ −1) y usa `thickness_px` por defecto. Sobre
`center_px` las contracciones salen hacia arriba en cinco de los seis videos. Docstring con números
viejos ("Video_063 no contrae").

### Medición (2026-10-07), sobre los seis `serie_temporal.xlsx` vigentes

Mismo veredicto; "con signo" = la señal se da vuelta si la cola pesada está arriba (criterio de
`_signo_evento`).

| video | `center_px`: veredicto actual | con signo | `thickness_px` (actual) |
|---|---|---|---|
| Video_prueba | ambiguo | **HAY** | HAY |
| Video_063 | ambiguo | **HAY** | débil |
| Video_268 | ambiguo | **HAY** | ambiguo |
| Video_466 | ambiguo | **HAY** | ambiguo |
| Video_583 | ambiguo | **HAY** | débil |
| Video_491 | HAY (sentido contrario) | **HAY** | débil |

Control negativo sintético (ruido t de Student, colas pesadas, 3 semillas): skew −0.08 a +0.39,
no da "HAY". Con signo, `center_px` coincide con el reporte en los seis (todos reportables).

**Propuesta:** arreglarlo, no borrarlo: `center_px` por defecto, signo por la cola más pesada (lo
informa), docstring con la tabla nueva. Sirve como chequeo rápido sin `k` antes del reporte, útil
para `RARITOS`.

**Abierto:** nunca se probó con un video real **sin** contracciones (control negativo real). El
video de control de iluminación del protocolo serviría.

---

## Para revisar con el resto de los videos y con `RARITOS`

Lista acumulada de la Fase 4 (lo que salió de pocos videos o no cerró):
1. Chequeo 2: error de modelo y `outlier_frac` medidos en 2 videos (063, 466); sin umbral.
2. ROI 466 1500–1700: menos ruido que la cintura, pero es el hombro del anclaje. Si en otro video
   pasa lo mismo, pensar si la "vara" del ruido sirve.
3. `motion_check`: cociente intensidad/bordes ~1 en 3 videos; 466 a 0.88 sin explicar.
4. `signal_check`: sin control negativo real.

**Decisión punto 3 (Franco, 2026-10-07): aprobada.** Se implementa al cerrar.

---

## Punto 4. Sexto evento de Video_063 (H11)

**La pregunta.** El evento de t = 0.308 s (9 fotogramas desde el inicio) aparece o desaparece según
el procesamiento. Es el que separa las dos mesetas del escaneo de 063: 6 eventos en k = 9.4–13.8 y
5 en k = 15.2–24.4. La regla "gana la meseta de k más bajo" elige 6, y esa regla se había
justificado justamente con 063 (H11: argumento circular).

### Medición (2026-10-07), sin reprocesar

Sobre `serie_temporal.xlsx` vigente de 063, `contracciones.xlsx` y la serie por intensidad del punto 2.

- **Está en la señal cruda, antes de quitar la deriva.** `center_px` pasa de 464.52 a 464.94 px en
  2 fotogramas (0.24 → 0.31 s) y vuelve en 3: +0.42 px. Ruido fotograma a fotograma de ese tramo:
  ~0.002 px. No es un efecto de la mediana móvil incompleta del inicio.
- **Tiene la forma de las estimuladas:** subida en 1–2 fotogramas y bajada en ~3, como los cinco
  estimulados (+1.65 px en 1 fotograma, vuelta en ~4). Mide ~25 % de su amplitud.
- **Lo confirma el método por intensidad** (punto 2), que no usa bordes: +0.28 px en el mismo fotograma.
- **El grosor baja 0.46 px en ese fotograma** (282.38 → 281.93), como en una contracción.
- **No cae en el tren:** la ranura anterior a 11.88 s sería 1.88 s; está 1.6 s antes. El reporte ya
  lo clasifica como **espontáneo** (5 estimulados + 1 espontáneo).
- Altura 0.362 px / ruido 0.024 = 15 σ: por eso desaparece en k > 15 y aparece la meseta de 5.

**Lectura.** Es una contracción real (espontánea), no un artefacto. El "6" de 063 queda respaldado por
evidencia independiente del umbral (señal cruda + intensidad). Esto le da un apoyo propio a la regla
"meseta de k más bajo" en 063; H11 cerrado para este video.

**Propuesta.**
1. Se sigue reportando 6 (5 estimulados + 1 espontáneo). Sin cambio de código ni de números.
2. Marca nueva `junto_al_borde` en `eventos_*` (como `junto_a_hueco`): evento a menos de media
   ventana de detrend del inicio o del fin del video. No lo saca; avisa que la línea base ahí se estima
   con media ventana. Hoy afecta solo a este evento.

**Abierto:** la regla "meseta de k más bajo" sigue apoyada en un solo caso real con dos mesetas.
Revisar cada video de `RARITOS` que tenga dos mesetas con el mismo método (señal cruda + intensidad).

**Decisión punto 4 (Franco, 2026-10-07): aprobada.** Franco miró el video: se ve una contracción
real y **a ojo no parece mucho más chica que las estimuladas** (no es una medida fiable, pero no
cierra con el 25 %). Hipótesis a revisar: la contracción espontánea es **local** (otra parte del gel)
y la ROI chica de 063 (875–1039) la ve atenuada. Se podría medir la amplitud por tramos de columnas a
lo largo del gel. Anotado para después de la Fase 4.

---

## Punto 5. Ráfaga final de Video_583 (72–73.7 s)

### Medición 1 (2026-10-07), sobre `serie_temporal.xlsx` vigente

| tramo | desvío `center_px` | desvío entre fotogramas | autocorrelación a 1 fotograma | frecuencia dominante | corr. bordes sup/inf (diferencias) |
|---|---|---|---|---|---|
| calma 60–70 s | 0.57 px | 0.17 px | +0.96 | 0.1 Hz (el tren) | 0.65 |
| ráfaga 71.85–73.9 s | 0.31 px | **0.50 px** | **−0.32** | **~10 Hz** | 0.75 |

Los dos bordes saltan juntos de un fotograma al siguiente (zigzag de ±0.5–1 px) a ~10 Hz, sin cambio
claro del residuo ni de `outlier_frac`. El video termina a 75.3 s.

**Dos hipótesis:** (a) vibración de toda la imagen (cámara, platina, alguien tocando el microscopio
al terminar); (b) el tejido respondiendo a una estimulación de ~10 Hz (en `RARITOS` hay protocolos
de 5–10 Hz). Se distinguen midiendo si se mueven también zonas sin gel.

**Medición 2 (propuesta, `scripts/medir_rafaga_583.py`):** correlación de fase (cv2) contra el
fotograma de 70 s, en el gel, los dos anclajes y una franja de fondo, de 66 a 75.5 s.

### Medición 2 (2026-10-07), corrida por Franco

- **Gel:** en la ráfaga salta tanto en vertical (0.40 px entre fotogramas, contra 0.05 en calma)
  como en **horizontal** (0.35 contra 0.03). Una contracción en este montaje es sobre todo vertical;
  un corrimiento igual en x y en y apunta a que se mueve todo el cuadro.
- **Anclajes y fondo: la medición falló** (desvíos de 15–300 px, sin sentido, también en calma). No
  tienen textura fija para enganchar la correlación. No se puede usar como referencia.
- **Franco miró el video: tiembla toda la imagen.** Conclusión: **vibración mecánica**, no tejido.

**¿El reporte lo detectaba?** Casi lo cuenta. Escaneo de 583: 7 eventos en k = 9.4–11.4 (no llega a
meseta: ×1.21 < ×1.25) y 6 desde k = 12.5. El séptimo es t = 72.29 s, en plena ráfaga, a 11.4 σ (los
reales están a 40–43 σ). La regla de la meseta lo dejó afuera por poco; sin CLAHE (Fase 3) contaban
9–12. No hay ningún aviso.

**Probé un detector simple** (ventanas de 1 s con zigzag: autocorrelación negativa y saltos > 3×
lo normal): da falsas alarmas en 063, 268 y 466. No sirve así.

**Propuesta.**
1. Sin cambio de código en la detección. 583 sigue en 6 eventos.
2. Anotar en `CLAUDE.md` (límites conocidos) que una vibración del montaje entra en `center_px` igual
   que una contracción, y que el reporte no la distingue; en 583 hay una en 71.9–73.9 s.
3. Para después: un detector de vibración necesita una referencia fija en la imagen (algo con textura
   que no sea el gel). Mirar si los videos de `RARITOS` la tienen. Si no, pedir al equipo que no
   toquen el microscopio durante la grabación (o que corten el video).

**Decisión punto 5 (Franco, 2026-10-07): aprobada.** Franco confirmó a ojo que tiembla toda la imagen.

---

## Implementación (2026-10-07)

- `src/pipeline.py`: `process_video` calcula el **error de modelo** por borde (mediana en el tiempo
  del residuo de cada columna, RMS sobre columnas) → `df.attrs["error_modelo_sup_px"/"inf_px"]`.
  La hoja `diagnostics` no cambia.
- `main.py`: el chequeo 2 deja de ser criterio; se borran el aviso del 10 % y el "en el límite".
  `resumen` suma `error de modelo borde sup/inf (px)` y `error de modelo peor / grosor (%)`; se
  imprime una línea de diagnóstico sin umbral.
- `scripts/contraction_report.py`: columna `junto_al_borde` en `eventos_*`,
  `eventos_junto_al_borde` en `resumen_*` y nota impresa (evento a menos de media ventana del
  detrend del inicio o del fin).
- `scripts/motion_check.py`: correlación de Pearson por lag (H51), eje PTS, primer fotograma
  conservado, cola pesada hacia cualquier lado, veredicto nuevo contra `center_px` (`--serie`);
  |ΔI| solo informativo (H50).
- `scripts/signal_check.py`: `center_px` por defecto, sentido por la cola más pesada (H49),
  docstring nuevo.
- `tests/test_diagnosticos.py` (nuevo): corrimiento conocido, signal_check en los dos sentidos y
  con ruido de colas pesadas, `junto_al_borde`.
- `scripts/regenerar_fase4.py`: archiva en `_superadas/<video>_v7`, regenera y compara.

**Verificación en la nube:** las siete pruebas pasan. Reporte sobre las seis series vigentes:
mismos números en todas las hojas (solo cambia la representación en texto de `ritmo`), más las
columnas nuevas. `junto_al_borde`: 1 evento en 063 (0.31 s) y 2 en Video_prueba. Prueba de
punta a punta de `main.py` y `motion_check.py` sobre un video sintético con traslación conocida:
`motion_check` da pendiente 0.999 y "CONFIRMA".

**Ojo:** el `contracciones.xlsx` de Video_prueba que estaba en `processed_data` daba **28** eventos
(`win_s` fijo de 2 s: lo había reescrito el cuaderno). Con el código del repo da 29, la línea base.
La regeneración lo corrige.

## Regeneración (2026-10-07)

`scripts/regenerar_fase4.py` (corrido por Franco; anterior en `_superadas/<video>_v7`,
comparación en `data/fase4_regeneracion.md`):
- Las seis `serie_temporal.xlsx` (hoja `diagnostics`): **idénticas**.
- Conteo, k, meseta, ruido, amplitud y ventana: **iguales** en los seis. Video_prueba 28 → 29
  porque el archivo guardado estaba mal (ver arriba).
- Error de modelo peor / grosor: prueba 0.38 %, 063 0.54 %, 268 0.33 %, 466 1.01 %, 583 0.70 %,
  491 0.50 %. `junto_al_borde`: prueba 2, 063 1, resto 0.

Documentación actualizada: `CLAUDE.md`, `claude/ESTADO-arranque-chat-nuevo.md`,
`claude/hallazgos-revision-codigo.md`, `claude/protocolo-analisis-videos.md`.

**Fase 4 cerrada.** Siguiente: `RARITOS`.

---

## Pendiente para después: tiempo de procesamiento (anotado 2026-10-07)

Hoy ~5–6 min por video. Sin medir todavía; candidatos por lectura de código:
1. RANSAC (sklearn, 200 intentos × 2 bordes × fotograma; arma el pipeline en cada llamada):
   probable cuello de botella. Una versión vectorizada en numpy puede cambiar números → regresión.
2. El video se decodifica tres veces (PTS, proyección de máximos, medición; H17): juntar pasadas,
   sin cambio de resultados.
3. CLAHE sobre el cuadro entero: recortar a la franja cambia los tiles → medir antes.
4. Procesar varios videos en paralelo (un proceso por video): sin cambio de resultados.
Orden: perfilar un video (cProfile) → 2 y 4 → 1 y 3 con regresión sobre los seis.
