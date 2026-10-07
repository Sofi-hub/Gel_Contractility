# Hallazgos de la revisión de código

Lo escribe el chat de **revisión** (ver `claude/guia-revision-codigo.md`); lo
lee el chat de **implementación** antes de tocar un módulo. Formato de cada
entrada: el de la guía, sección "Formato de cada hallazgo".

Revisión sobre el commit: `2be99ca392bdb33eb9facb318d196076513ae6b5`
(rama `main`, 2026-09-30 03:21 UTC, mensaje "."). Anteriores: `1131be2` (02:57 UTC),
`1c1aaaa` (02:10 UTC), `96df20d` (merge del 2026-09-11, último previo a los cambios
del 29/30 de septiembre: `git diff 96df20d` los muestra).

Avance: **Preparación y Etapas 0 a 10 hechas: revisión completa**. 2026-09-30: el cuaderno `Analisis_Contractilidad_v4.ipynb` se actualizó (H44, H45, H46 resueltos *en el cuaderno*; H54 nuevo). `src/` y `scripts/` **no se tocaron** · falta sincronizar esta copia con `docs/` y cerrar el checklist de la guía.

---

## Índice de hallazgos (H1–H54)

Cada hallazgo tiene un número `H` para poder citarlo. H1–H7 venían de la guía; H8 en adelante son de esta revisión. Las líneas "Actualización" dentro de un hallazgo son evidencia nueva sobre uno ya anotado.

| H | severidad | en una línea |
|---|---|---|
| H1 | BUG | un solo fotograma `REJECTED` (NaN) anula el reporte en silencio — **resuelto 2026-10-01** |
| H2 | RIESGO | dos detectores de eventos (reporte vs `event_detection`/cuaderno): 28 vs 29 en Video_prueba |
| H3 | DEUDA | el cuaderno arma ventanas con el fps declarado, el reporte con el de los PTS |
| H4 | DEUDA | MAD y mediana móvil repetidos en varios módulos |
| H5 | DEUDA | `escaneo_estabilidad` tiene `sep_s=2.0` por defecto; el script usa 0.3 — **resuelto 2026-10-01** (Fase 2.2: sin separación mínima) |
| H6 | DEUDA | `detect_contractions` tiene `raw_col="thickness_px"` por defecto |
| H7 | — | default `pts`, `ordenar_carpeta.py`, escaneos vigentes en el test, `_v6` en docs |
| H8 | — | El 28 vs 29 de Video_prueba depende de la separación mínima entre picos (`sep_s`): hay una ráfaga real con espaciado ≈ 0.3 s — **resuelto 2026-10-01** (Fase 2.2: prominencia; Video_prueba = 29) |
| H9 | PREGUNTA | La regresión de CLAUDE.md no tiene una línea base clara, y el test no puede detectar H8 — **resuelto 2026-10-01** (`tests/test_deteccion.py` corre la detección) |
| H10 | DEUDA | El cuaderno se contradice sobre qué funciones usa |
| H11 | PREGUNTA | El "6" validado de Video_063 no es evidencia independiente de la regla "gana la meseta de k más bajo" — **a la vista, no resuelto**: el reporte lista las dos mesetas de Video_063 |
| H12 | DEUDA | La documentación no clasifica todos los métodos de ROI |
| H13 | PREGUNTA | El control por señal invertida supone ruido simétrico |
| H14 | DEUDA | `frames faltantes (%)` está inflado por el jitter de los timestamps |
| H15 | RIESGO | Un archivo sin timestamps reales pasa por PTS sin aviso |
| H16 | PREGUNTA | La serie es irregular en el tiempo, pero el análisis posterior cuenta por índice (a verificar) |
| H17 | DEUDA | Detalles menores de `io_utils` y `process_video` |
| H18 | RIESGO | Una ROI manual no recibe veredicto de aceptación, y `--exigir-roi` no puede frenarla |
| H19 | RIESGO | El ancho mínimo de 180 px rechazó la cintura real de Video_466, y su justificación no se sostiene — **resuelto 2026-10-08** (Fase 3: separación 3 px medida, piso 40 columnas, ancho mínimo 120 px; 466 sin ROI manual) |
| H20 | RIESGO | El rescate no exige que la ventana contenga la cintura: el veredicto "cumple" no distingue cintura de meseta — **resuelto 2026-10-08** (Fase 3: el rescate exige contener la cintura) |
| H21 | PREGUNTA | La cintura se estima con la mediana del grosor: depende de cuánto del cuadro ocupa la cintura |
| H22 | RIESGO | `roi_min_gradient = 10` es un umbral de contraste absoluto sin origen documentado |
| H23 | PREGUNTA | Ventanas de suavizado proporcionales al ancho del cuadro, no al gel |
| H24 | PREGUNTA | `outlier_frac` no es comparable entre ROIs: el criterio favorece la ventana de peor ajuste absoluto — **a la vista** (466 queda en 10.5 % con ROI automática; aviso "en el límite"; Fase 4) |
| H25 | DEUDA | `preprocessing.py`: parámetro muerto que reintroduce la trampa, y documentación vieja |
| H26 | RIESGO | CLAHE desplaza el borde por una cantidad que cambia de fotograma a fotograma, del orden de la señal de grosor — **medido 2026-10-08** (Fase 3: conteo y traslación no dependen de CLAHE; el adelgazamiento sí → no se reporta; CLAHE se queda) |
| H27 | RIESGO | La ventana de ±15 px deja poco margen real y descarta columnas en Video_466 — **cerrado 2026-10-08** (±25 px rompe 466: ±15 se queda) |
| H28 | DEUDA | `min_gradient` nunca actúa en estos videos; código muerto en `edge_detection.py` |
| H29 | RIESGO | En Video_466 el RANSAC agrega ruido y un corrimiento variable: los "outliers" son sistemáticos, no burbujas — **cerrado 2026-10-08** (ningún ajuste gana en todos: RANSAC se queda) |
| H30 | DEUDA | El umbral adaptativo casi nunca toca el piso y es muy grande; el MAD de residuos por columna es alto |
| H31 | RIESGO | Un solo fotograma rechazado (NaN) deja sin resultado a todo el video, y `frame_quality` no se consulta nunca — **NaN resuelto 2026-10-01**; `frame_quality` solo se cuenta |
| H32 | DEUDA | La hoja `resumen` no alcanza para reproducir una corrida, y algunas cifras se leen mal |
| H33 | RIESGO | El veredicto "reportable" cambia con `win_s`, y el control de falsos se contamina con el propio evento — **resuelto 2026-10-01** (ventana automática + control de estabilidad; Video_491 = 2 reportables) |
| H34 | RIESGO | La grilla de k es gruesa y despareja, y se elige el borde inferior de la meseta — **resuelto 2026-10-01** (grilla ×1.1, ancho ≥ ×1.25, k en el centro) |
| H35 | DEUDA | Detalles menores de `contraction_report.py` |
| H36 | RIESGO | En Video_prueba el primer "estimulado" (t = 4.87 s) tiene la amplitud de una espontánea y sesga el período |
| H37 | RIESGO | El rescate de "dudosos" usa ±1 s y extrapola la grilla fuera del tren |
| H38 | RIESGO | La significancia no está calibrada para actividad espontánea agrupada o regular; el p no resuelve más que 0.005 |
| H39 | DEUDA | Código muerto y documentación vieja en `rhythm_split.py` |
| H40 | RIESGO | El resumen por video mezcla estimuladas y espontáneas: la amplitud relativa describe a las espontáneas |
| H41 | RIESGO | "Reportable" (≥ 5 fotogramas) ignora el ancho del intervalo y la meseta del pico; RT50 de 466 está en el umbral |
| H42 | PREGUNTA | `win_s` = 1 s sesga eventos lentos (−22 % TTP); la amplitud relativa no es una deformación — **en parte** (la ventana ya no puede quedar corta sin aviso; lo de amplitud relativa sigue) |
| H43 | DEUDA | Las pruebas de `cinetica` solo cubren eventos triangulares ideales |
| H44 | RIESGO | Los dos detectores difieren en el tiempo del evento y en el ruido que fija el umbral (confirma H2) |
| H45 | RIESGO | El cuaderno usa el fps declarado en secciones 7, 8, 10, 11: 466 da 6 en vez de 5 eventos (confirma H3) |
| H46 | RIESGO | La sección 12 del cuaderno no ejecuta el enganche de fase que describe; la 13 no genera `contracciones.xlsx` |
| H47 | RIESGO | El control de falsos de `ed` se contradice con el del reporte; un NaN anula el motor — **sigue abierto en `ed`** (depende de la Fase 2.3) |
| H48 | DEUDA | Promesas del docstring sin respaldo de pruebas y escalas absolutas ocultas |
| H49 | RIESGO | `signal_check.py` sólo mira la cola negativa: sobre `center_px` no reconoce ninguna contracción real |
| H50 | RIESGO | El veredicto de `motion_check.py` contradice el hallazgo 1 de CLAUDE.md |
| H51 | PREGUNTA | La magnitud de `center_px` no coincide con la traslación medida por intensidad (0.18× en los eventos) — **resuelto 2026-10-08** (`center_px` mide bien la magnitud; el 0.18 es un defecto de `motion_check._subpixel_shift`: Fase 4) |
| H52 | — | Las diferencias entre fotogramas llevan un peine de 10 fotogramas que no está en las series de bordes |
| H53 | DEUDA | La MAD y la mediana móvil están copiadas 9 y 3 veces, y ninguna tolera NaN (cierra H4) — **resuelto 2026-10-01** (`src/estadistica.py`) |
| H54 | RIESGO | `CANAL="auto"` del cuaderno elegía `y_top_px`/`y_bottom_px` y cambiaba el conteo (Video_063: 8 en vez de 6); ya fijado a `center_px` — **resuelto 2026-10-08** (ruido desigual entre bordes, no otro observable; se registra el ruido por borde) |
| H55 | RIESGO | Con eventos lentos y `sep_s` = 0.3 s, la cola de bajada cuenta como un segundo evento, y la regla "meseta de k más bajo" lo convalida (sintético: 9 en vez de 6) — **resuelto 2026-10-01** (Fase 2.2: prominencia) |

---

## Preparación (sección 1 de la guía) — hecha 2026-09-30

| paso | resultado |
|---|---|
| Punto de partida | HEAD = `2be99ca`. `git status` **no se pudo correr** (el chat no tiene shell en la PC): se infirió árbol limpio porque ningún archivo tiene fecha posterior al commit. El usuario confirmó después que hizo commit **y push**: `origin/main` al día. |
| `tests/test_seleccion_k.py` | 16/16 OK. Usa escaneos **hardcodeados**: solo cubre `elegir_k_meseta`, no el escaneo ni la detección (ver H9). |
| `tests/test_cinetica.py` | TODO OK (lento: TTP err 0.05 fr, RT50 err 0.18 fr; rápido: no medible; sin conteo reportable: no reportable). |
| Regresión (`contraction_report.py --frecuencia-estimulo 0.1` sobre los seis `serie_temporal.xlsx`, en copia; comparación hoja por hoja y columna por columna, tolerancia 1e-12) | **Idéntico en los seis** (0 diferencias; 6, 6, 6, 4, 6 y 8 hojas). El comparador se verificó: detecta una perturbación de 1e-9. Python 3.11 / Linux; los vigentes se generaron en Windows. |
| Cuaderno v4 | Guardado **sin salidas** (0 de 15 celdas de código ejecutadas). Falta correrlo sobre Video_063. |
| Figuras de Video_063 | Disponibles: `00_roi_profile`, `09_contracciones`, `10_ritmo`, `11_cinetica`. No hay `01`, `07`, `08`. |

Supuesto de la regresión: no hay registro de los flags exactos de cada vigente; se usó
`--frecuencia-estimulo 0.1` y `--k auto`. Que dé idéntico indica que coinciden.

---

## Etapa 0 — el método, sin código (2026-09-30)

Leídos: `CLAUDE.md`, `DOCUMENTACION.md`, protocolo, referencia y el texto completo del
cuaderno v4 (celdas de texto y la celda de parámetros).

**Qué entra.** Un video crudo `.mp4`/`.avi` de un puente de gel entre dos anclajes; opcionalmente
la frecuencia configurada en el estimulador (Hz).

**Qué sale.** `serie_temporal.xlsx` (cuatro series por fotograma —`y_top_px`, `y_bottom_px`,
`thickness_px`, `center_px`— más la hoja `resumen` con los parámetros) y `contracciones.xlsx`
(escaneo de `k`, eventos, ritmo, adelgazamiento, cinética), con figuras `00`–`11`.

**Qué supone** (lo que, si falla, invalida el número):
1. El gel es una franja aproximadamente horizontal; cada borde es una curva `y(x)` de grado 2
   dentro de la zona útil.
2. La contracción es sobre todo una **traslación vertical** de la franja (por eso se detecta en
   `center_px`); el signo del evento es el mismo en todo el video.
3. La deriva es lenta frente a 2 s (mediana móvil) y las contracciones son minoritarias en el tiempo.
4. El ruido es simétrico: lo que aparece en la señal invertida es ruido y no contracción (el control
   de falsos positivos se apoya en esto).
5. El estimulador es un reloj periódico exacto (`t = fase + n·T`); hay como máximo un tren por video.
6. El fps real es 30.000 y los timestamps del contenedor son confiables.
7. Un conteo solo es reportable si hay meseta con 0 falsos.

**Contradicciones con los cinco hallazgos de `CLAUDE.md`:** ninguna en los documentos. Sí hay
tensiones entre documentos y código/datos: H8–H13 abajo.

**Verificación de H7** (lo que se pudo leer): `main.py:37` y `pipeline.py:82` tienen `pts` por
defecto ✔; `ordenar_carpeta.py` tiene la guarda "si no hay carpetas `_v6`, no mueve nada" ✔ (leído,
no ejecutado); `test_seleccion_k.py` incluye los seis vigentes (16 casos) ✔; CLAUDE.md, README,
referencia y DOCUMENTACION dicen "sin sufijo" ✔. Pendiente: el aviso al caer a `frames` si no hay
timestamps (`pipeline.py:252`, Etapa 5).

---

## Etapa 1 — lectura del video y eje temporal (2026-09-30)

Leídos: `src/io_utils.py` (completo) y `src/pipeline.py` líneas 60–334 (`PipelineConfig`,
`process_frame`, `process_video`, `describe_roi`).

**Qué entra.** La ruta de un video `.mp4`/`.avi`.
**Qué sale.** (a) `frame_generator`: cada fotograma en gris, de a uno; (b) `read_pts_seconds`: un
vector con la hora de cada fotograma según el contenedor; (c) `get_video_metadata`: fps declarado,
nº de fotogramas y tamaño; (d) `compute_max_projection`: una imagen con el máximo de cada píxel;
(e) en `process_video`: la columna `time_s` y los diagnósticos `fps segun PTS`, `huecos en PTS`,
`frames faltantes`.
**Qué supone.** (1) `CAP_PROP_POS_MSEC` leído *después* de `read()` da la hora de ese fotograma;
(2) esa hora es real y no fabricada por el lector (ver H15); (3) la mediana de los `dt` es el período
de captura; (4) el índice de `frame_generator` y el de `read_pts_seconds` coinciden (ambos cuentan
`read()` exitosos); (5) 1 de cada 5 fotogramas alcanza para la proyección de máximos.

**Respuestas a las preguntas de la guía**
- *¿Lee el timestamp después de `read()`?* Sí: `io_utils.py` l. 81 (`cap.read()`) y l. 84
  (`cap.get(POS_MSEC)`). Verificado contra `ffprobe -show_entries packet=pts_time` sobre
  `Video_prueba.mp4` (h264, `time_base` 1/600): 2007 contra 2007 fotogramas, diferencia máxima
  0.0003 ms. La afirmación del docstring es cierta.
- *¿Cómo se cuentan huecos y faltantes?* `pipeline.py` l. 219–226: `dt_med = mediana(diff(pts))`;
  hueco = todo `dt > 1.5 × dt_med`; `faltantes = round(Σ (dt/dt_med − 1))` sobre los huecos (se
  redondea la **suma**, no cada hueco). Un `dt` que no es múltiplo entero cuenta como fracción de
  fotograma perdido: ver H14.
- *¿Cae a `frames` y avisa si no hay timestamps?* Solo si no se puede leer ninguno (≤ 1 fotograma o
  excepción). Un archivo sin timestamps reales **no** cae: OpenCV inventa `idx/fps` y el programa lo
  toma por PTS: ver H15.
- *¿1 de cada 5 fotogramas puede achicar la zona de búsqueda?* Medido sobre Video_prueba: la
  proyección difiere en 9.5 % de los píxeles (hasta 58 niveles de gris), pero la ROI sale idéntica
  (x = 454–1516, `gauge_cintura`) y `top_guess`/`bottom_guess` difieren ≤ 1 px dentro de las 60
  columnas de la ROI (la ventana de búsqueda es ±15 px). Fuera de la ROI difieren hasta 65 px, sin
  consecuencia. **Descartado como riesgo, solo verificado en un video.**

**Dato nuevo sobre los timestamps reales.** Los seis videos vigentes tienen `dt` mediano exacto
(33.3333 ms) pero **con jitter**: entre 0.15 y 1.75 veces la mediana en centenares de fotogramas por
video (desvío de fase ~5 ms, hasta ~60–75 ms de máximo contra una recta) y **saltos reales de 8 a
13 fotogramas (~0.3–0.45 s)**: 2 en Video_prueba, 1 en Video_063, 3 en 268, 10 en Video_466, 3 en
491 y 3 en 583. Ninguna ranura del estimulador cae dentro de un salto (todas las ranuras capturadas
en los cinco videos con tren).

## Etapa 2 ★ — la zona útil (ROI) (2026-09-30)

Leído: `src/preprocessing.py` completo (623 líneas) y `main.py` l. 140–200. Pruebas: (a) imágenes
sintéticas de un gel en reloj de arena (inclinado, con un anclaje cortado, fino, poco contraste,
otra ampliación, zona plana corta), en `auto_detect_roi` sin modificarla; (b) `Video_466` real:
proyección de máximos, cascada completa y muestreo de 80 fotogramas por ventana candidata;
(c) las figuras `00_roi_profile.png` de Video_063 y Video_466.

**Qué entra.** La imagen de máximos (uint8, alto × ancho) y los parámetros de ROI.
**Qué sale.** `x_start`/`x_end`; `top_guess`/`bottom_guess` (centro de la ventana de búsqueda de cada
borde, por columna); `roi_quality` (método, cintura, variación, conteos de descartes, alternativas,
veredicto `cumple_criterio_aceptacion`); perfiles de grosor y de nitidez.
**Qué supone.** (1) El gel es **más claro** que el fondo (la máscara es `Otsu > 0`) y cruza el centro
del cuadro (la semilla son las columnas del 35 % al 65 % del ancho). (2) El grosor de la máscara de la
proyección de máximos representa el grosor real. (3) Existe una cintura: percentil 5 del grosor entre
las columnas nítidas cuyo grosor está entre 0.6 y 1.6 × la **mediana** (ver H21). (4) La zona útil es la
plana y cercana a la cintura. (5) Ancho mínimo = 60 columnas × 3 px = 180 px (ver H19). (6) La
variación se mide en % sobre un grosor **entero en píxeles**. (7) El gel es aproximadamente horizontal
(el seguimiento tolera saltos de hasta 0.75 × el grosor entre columnas vecinas).

**Cómo funciona, en orden.** Suaviza y binariza la proyección (Otsu) → sigue la franja del gel columna
a columna desde el centro hacia los lados (`_track_gel_band`) → mide nitidez de cada borde
(`_edge_sharpness`, el **mínimo** de los dos) → suaviza el grosor y calcula su pendiente → estima la cintura →
recorre la cascada `gauge_plana` → `gauge_cintura` → `gauge_relajada` → `solo_nitidez` → `franja_completa`;
el primero cuyo bloque contiguo más largo mide ≥ 180 px gana → si el elegido no cumple ≤ 6 % (o no hay
ninguno), corre el **rescate** (`_widest_flat_window`: la ventana más ancha con variación ≤ 6 % entre columnas
nítidas) → si nada sirve, `fallback_margin` (5 % de margen a cada lado).

**Cascada vs. tabla de DOCUMENTACION §2.2:** coincide (cinco niveles + rescate). Faltan en la tabla:
`fallback_margin`, y la condición exacta del rescate (se activa si el nivel elegido tiene variación > 6 %,
no solo "si nada es plano").

**Parámetros y su relación con el tamaño del sujeto** (la regla de CLAUDE.md):
- Relativos al gel, sin problema: `roi_thickness_tolerance` (5 % sobre la cintura), `max_center_jump_frac`,
  `max_thickness_ratio`; `roi_max_slope` es adimensional (px de grosor por px de x).
- **En píxeles absolutos:** ancho mínimo 180 px (H19), `min_run` = 5 px, blur de 5 px, margen de 4 px
  en `_edge_sharpness`.
- **Proporcionales al ancho del cuadro, no del gel:** mediana de suavizado `w // 60` = 32 px y promedio de
  la pendiente `w // 50` = 38 px de semiancho (H23).
- **Dependiente del contraste de imagen:** `roi_min_gradient` = 10 (H22).
- **Dependiente de qué parte del cuadro ocupa la cintura:** la escala de referencia es la mediana (H21).

**Perfiles reales (figuras).** Video_063: cintura de 285 px y un tramo casi horizontal larguísimo
(x ≈ 350–1450); la ROI 390–1423 es la zona plana. Video_466: **no hay un tramo plano largo**: el grosor
baja de ~315 a ~206 px hacia x = 700, queda en 201–220 px entre x ≈ 700 y 1100 y vuelve a subir despacio
hasta ~350 px; la nitidez baja hasta ~3.5 en x ≈ 850, dentro de la ROI manual.

**Video_466 en detalle (medido).** Cintura estimada 206 px (correcta). Cascada: `gauge_plana` 796–816
(20 px), `gauge_cintura` **696–846, 150 px, variación 4.85 %**, `gauge_relajada` 877–1177 (300 px,
12.44 %), `solo_nitidez` 1302–1817 (40.6 %), `franja_completa` (164.6 %). El bloque de la cintura mide
150 px < 180 px de mínimo, se rechaza; gana `gauge_relajada` con 12.44 % → el rescate → 944–1169
(5.77 %). Muestreo de 80 fotogramas por ventana (mismo código de `process_frame`; reproduce los valores
documentados: 16.2 % y 8.4 %):

| ventana | ancho | variación grosor | outliers | residuo sup. | residuo inf. |
|---|---|---|---|---|---|
| 696–846 (bloque de la cintura) | 150 | 4.85 % | 9.3 % | 1.40 | 0.61 |
| 700–900 (manual, vigente) | 200 | 5.47 % | 8.4 % | 1.78 | 0.67 |
| 796–996 | 200 | 9.45 % | 5.2 % | 1.89 | 1.88 |
| 877–1177 | 300 | 12.44 % | 12.2 % | 1.07 | 1.08 |
| 944–1169 (automática, rescate) | 225 | 5.77 % | **16.2 %** | 0.85 | 0.72 |
| 1000–1200 | 200 | 14.76 % | 7.0 % | 2.37 | 0.66 |
| 1100–1300 | 200 | 17.76 % | 9.4 % | 5.96 | 1.29 |
| 1500–1700 | 200 | 13.92 % | 5.4 % | 0.72 | 0.79 |

**¿Dónde habría que meter `outlier_frac` en la decisión de la ROI?** La ROI se decide sobre la
proyección de máximos, **antes** de ajustar ningún fotograma, así que `outlier_frac` no existe en ese
momento. Hace falta una pasada piloto: ajustar unos pocos fotogramas (80 fotogramas leídos y ajustados
llevaron ~12 s para 10 ventanas en la nube) en cada ventana candidata de `alternativas` y comparar. Pero
antes hay que resolver H24: `outlier_frac` no es comparable entre ventanas.

**Prueba con imágenes sintéticas** (gel 285 px de grosor, imagen 1920 × 1080, zona verdaderamente plana
conocida):

| caso | resultado |
|---|---|
| base (plana 1000 px) | `gauge_plana` 479–1435, dentro de la zona plana verdadera (405–1514) |
| inclinado 5° y 10° | correcto (ROI dentro de la zona verdadera, variación ≤ 0.35 %) |
| cuadro corta un anclaje | correcto (0–734 dentro de 0–814) |
| gel fino (70 px y 30 px) | correcto pero estrecho (~230 px de una zona de ~1100 px) |
| poco contraste (gel 90 / fondo 60) | **falla, con aviso**: `franja_completa` 0–1920, variación 131 %, `cumple = False` (H22) |
| ampliación × 0.5, plana 500 px | correcto |
| plana corta (300, 150 px) | cintura mal estimada (444 y 450 contra 285); con 150 px el **rescate elige la meseta del anclaje** (H20, H21) |

## Etapa 3 — el borde con precisión de subpíxel (2026-09-30)

**Archivos:** `src/edge_detection.py` (completo) y `preprocessing.apply_clahe`. **Se ejecutó** sobre Video_prueba
y Video_466 (150 fotogramas muestreados cada 10 × 60 columnas × 2 bordes = 18 120 medidas por video) y
sobre los primeros 900 fotogramas para la comparación con/sin CLAHE.

**Entra:** un fotograma en grises, las 60 columnas `x_positions` y, por columna, la posición aproximada de los
bordes (`top_guess`, `bottom_guess`, que salen de la imagen de máximos de la Etapa 2).
**Sale:** por fotograma, `y_top[60]` y `y_bottom[60]` (NaN donde no hubo borde confiable) y un `quality` que
nadie usa después.
**Supone:** (1) gel CLARO sobre fondo OSCURO (polaridad +1 arriba, −1 abajo, fija en el código); (2) el borde
real está a menos de 15 px de la posición de la imagen de máximos; (3) el pico del gradiente de la imagen
procesada con CLAHE coincide con el borde físico; (4) la parábola de 3 puntos da la posición subpíxel.

**Cómo funciona.** Por columna: se recorta una ventana de 30 px (`half_window` = 15 a cada lado de la
posición aproximada), se calcula el gradiente (`np.gradient`: diferencia entre vecinos), se toma el píxel de
mayor gradiente y se ajusta una parábola a ese píxel y sus dos vecinos; el vértice da la fracción de píxel
(`delta`). Si el pico cae en el extremo de la ventana, o es menor que `min_gradient` (5), la columna queda NaN.

**Resultados medidos**

| chequeo | Video_prueba | Video_466 |
|---|---|---|
| \|delta\| máximo (200 000 perfiles aleatorios) | 0.49998 | (ídem, propiedad matemática) |
| pico de gradiente con CLAHE, percentil 1 (arriba / abajo) | 31 / 35.5 | **9.5** / 18.5 |
| medidas con pico < `min_gradient` = 5 | 0 de 18 120 | 0 de 18 120 |
| medidas inválidas por pico pegado a la ventana | 0 | **47** (0.26 %) |
| corrimiento del borde real respecto de la posición aproximada, abajo (mediana / mín) | −9.2 / −12.0 px | −5.4 / **−13.1** px |
| corrimiento arriba (máx) | +12.9 px | **+13.5** px |
| histograma de la parte fraccionaria (10 cajas, ideal 0.10) | 0.087–0.119 (parejo) | 0.036–0.164 (irregular) |
| sigmoide − parabólico (mediana de 1 020 pares) | media +0.24 px, desvío 0.57 px | — |

**Con CLAHE vs sin CLAHE (misma ROI, mismos fotogramas)**

| | Video_prueba | Video_466 |
|---|---|---|
| desplazamiento medio del borde superior / inferior | +0.48 / −0.42 px | +0.76 / −1.21 px |
| desvío de (CLAHE − crudo) en `center_px` | 0.12 px (señal cruda: 0.69) | 0.24 px (señal cruda: 0.74) |
| desvío de (CLAHE − crudo) en grosor | 0.27 px (señal cruda: 0.27) | **0.44 px (señal cruda: 0.31)** |
| correlación crudo–CLAHE, borde superior / inferior | 0.97 / 0.99 | 0.95 / 0.86 |

**La parábola, en un ejemplo.** Si el pico entero (píxel 412) vale 60 y sus vecinos 40 (411) y 50 (413), el
pico verdadero está algo hacia el 413; la parábola por esos tres puntos tiene su cima en
`delta = 0.5·(40−50)/(40−120+50) = +0.17` → borde en 412.17. Supone que el pico del gradiente es parabólico
cerca de la cima; el ajuste por sigmoide (no usado) da otras posiciones (desvío 0.57 px), o sea que el
resultado subpíxel depende del método elegido.

**Gráfico de la etapa.** En el cuaderno, sección 4: fotograma crudo vs CLAHE y `qc.plot_column_profile`
(perfil de intensidad de una columna con el gradiente y el borde marcado). Se lee así: la curva de
intensidad sube/baja en el borde; el gradiente tiene un pico justo ahí; la marca debe caer en el pico. Sirve
para ver a ojo si el borde está nítido, pero es UNA columna de UN fotograma.

---

## Etapa 4 — el ajuste robusto (RANSAC) y la serie por fotograma (2026-09-30)

**Archivos:** `src/robust_fitting.py` (completo) y `pipeline.process_frame` (l. 99–176). **Se ejecutó** sobre los
primeros 1 200 fotogramas de Video_prueba y Video_466 (sus 60 bordes por fotograma, guardados en
`/tmp/claude-0/rev/edges_*.npz`) y una simulación con burbujas conocidas (`e4c.py`).

**Entra:** por fotograma, 60 valores `y_top` y 60 `y_bottom` (algunos NaN).
**Sale:** `y_top_px`, `y_bottom_px`, `thickness_px`, `center_px`, `residual_*_px`, `outlier_frac`, `frame_quality`.
**Supone:** (1) el borde, en las 60 columnas de la ROI, es una parábola (grado 2); (2) lo que se aparta de esa
parábola más de 3×MAD son burbujas ocasionales y dispersas; (3) la posición del borde es la MEDIANA de la
parábola evaluada en las 60 columnas (también en las descartadas).

**Cómo funciona.** Para cada borde por separado: (a) se estima la escala del ruido con un ajuste recortado y el
MAD de sus residuos; (b) umbral = `max(3×MAD, 0.4 px)`; (c) RANSAC prueba 200 veces con 3 puntos al azar, arma la
parábola, cuenta cuántos puntos caen a menos del umbral y se queda con la que reúne más; (d) `y_top_px` =
mediana de esa parábola sobre las 60 columnas; grosor = mediana de (inferior − superior); centro = promedio
de las dos posiciones. Un fotograma sin borde ajustable queda `REJECTED` (NaN); con ≥ 30 % de columnas
descartadas, `LOW_QUALITY`. `random_state=0` fijo: el resultado es determinista.

**Resultados medidos (datos reales, 1 200 fotogramas por video)**

| | Video_prueba | Video_466 |
|---|---|---|
| ruido fotograma a fotograma del centro: RANSAC / mínimos cuadrados (sin descartar nada) | 0.313 / 0.314 px | **0.132 / 0.104** px |
| ídem del grosor | 0.128 / 0.112 px | **0.212 / 0.144** px |
| diferencia RANSAC − mínimos cuadrados (sup.): media / desvío | −0.01 / 0.06 px | **−0.46 / 0.26 px** (máx 1.3) |
| diferencia RANSAC − mínimos cuadrados (inf.): media / desvío | −0.01 / 0.05 px | **−0.94 / 0.24 px** (máx 1.4) |
| umbral RANSAC: percentil 5 / 50 / 95 | 2.0 / 2.4 / 2.9 px | 2.0 / 2.9 / **5.2** px |
| frames con el umbral en el piso de 0.4 px | 0 % | 0 % |
| columnas inliers (de 60): mediana | 57 (sup.) / 59 (inf.) | 51 (sup.) / 49 (inf.) |
| columnas que cambian de inlier a outlier entre fotogramas seguidos | 1.0 / 0.8 | 2.9 / 2.0 |
| columnas descartadas casi siempre | col. 37 sup.: **100 %** (otras 3 > 25 %) | inf., primeras 10 cols: **47 %**; sup., últimas 10: 20 % |

(El "ruido" es desvío de la diferencia entre fotogramas consecutivos dividido por √2; incluye movimiento real
del gel, que es igual para todos los métodos, así que la comparación entre métodos es válida pero el valor
absoluto es una cota superior.)

**Simulación (borde parabólico conocido + ruido + burbujas de +6 px, 600 repeticiones):** con 4 burbujas, la
posición por mínimos cuadrados sale sesgada +0.39 px y RANSAC +0.00 px; con 8 burbujas, +0.77 px contra 0.00.
Sin burbujas RANSAC cuesta ~8 % más de ruido (0.117 vs 0.109 px). Burbujas pequeñas (+2 px) quedan bajo el
umbral y no se detectan (sesgo RANSAC +0.08 px). Es decir: **el método hace lo que dice cuando el modelo es
correcto y las burbujas son escasas.**

**Gráfico de la etapa.** Cuaderno, sección 5: la imagen del fotograma con el ajuste superpuesto. Verde = borde
aceptado (inlier), rojo = detectado pero descartado (outlier), amarillo = columna sin borde confiable, cian = el
modelo final. La regla del propio cuaderno: outliers DISPERSOS = burbujas; CONTIGUOS (≥ 3 seguidos) = el modelo
no representa el borde. Además, la sección 6 grafica las cuatro series (`y_top_px`, `y_bottom_px`,
`thickness_px`, `center_px`) y `residual_*_px`; si el residuo se mueve junto con el grosor, se está midiendo el
ajuste y no el gel.

---

## Etapa 5 — el orquestador: `process_video`, `main.py` y la tabla de salida (2026-09-30)

**Archivos:** `src/pipeline.py` (completo), `main.py`, `src/output_paths.py`, `src/qc_visualization.save_diagnostics`
y `src/plotting.plot_timeseries`. **Se ejecutó:** lectura de las seis `serie_temporal.xlsx` vigentes, comparación de
los valores por defecto entre `PipelineConfig`, `argparse` y el cuaderno, y una prueba de robustez del análisis
posterior con fotogramas rechazados (NaN).

**Entra:** el video (y opcionalmente una imagen de máximos y los flags). **Sale:** `data/processed_data/<video>/serie_temporal.xlsx`
con la hoja `diagnostics` (una fila por fotograma, 13 columnas: `thickness_px`, `thickness_mm`, `n_outlier_columns`,
`outlier_frac`, `y_top_px`, `y_bottom_px`, `center_px`, `residual_top_px`, `residual_bottom_px`, `frame_quality`,
`frame`, `time_s`, `thickness_mm_smooth`) y la hoja `resumen` (≈ 35 pares métrica–valor), más `00_roi_profile_<video>.png`
y, con `--plot`, `01_serie_temporal_<video>.png`.
**Supone:** (1) el eje de tiempo son los timestamps del contenedor; (2) un fotograma rechazado queda NaN y "no se
inventa" (`frame_quality`); (3) los defaults de `PipelineConfig`, de `main.py` y del cuaderno coinciden.

**Orden de `process_video`:** lee metadatos → lee TODOS los timestamps (primera pasada por el video) → estima huecos →
imagen de máximos (segunda pasada, 1 de cada 5) → ROI → por cada fotograma: CLAHE, bordes, ajuste, fila (tercera
pasada) → suavizado Savitzky–Golay del grosor (11 fotogramas, sólo para el gráfico) → guarda ROI y metadatos en
`df.attrs`. `main.py` arma la hoja `resumen`, avisa (frames perdidos > 1 %, outliers > 10 %, px sin calibrar), aborta
si se pidió `--exigir-roi` y la ROI no cumple, y guarda. Los avisos salen sólo por pantalla: no quedan en el xlsx.

**Medido en las seis series vigentes**

| video | fotogramas | `frame_quality` | NaN en `center_px` | `outlier_frac` medio / máx |
|---|---|---|---|---|
| Video_063 | 1 848 | 100 % OK | 0 | 0.077 / 0.12 |
| Video_268 | 2 283 | 100 % OK | 0 | 0.020 / 0.05 |
| Video_466 | 2 076 | 100 % OK | 0 | 0.079 / 0.17 |
| Video_491 | 1 846 | 100 % OK | 0 | 0.042 / 0.11 |
| Video_583 | 2 236 | 100 % OK | 0 | 0.040 / 0.11 |
| Video_prueba | 2 007 | 100 % OK | 0 | 0.036 / 0.08 |

Ningún fotograma de ningún video fue `REJECTED` ni `LOW_QUALITY` (el máximo de `outlier_frac` es 0.17 < 0.30): el
camino de los NaN **nunca se ejercitó con datos reales**. Los valores por defecto coinciden hoy entre `PipelineConfig`
y `argparse` (comparados por programa, 0 diferencias) y con la celda de parámetros del cuaderno (revisada a ojo), pero
viven en tres lugares.

**Gráfico de la etapa.** `01_serie_temporal_*.png` (flag `--plot`): el grosor crudo (gris) y su suavizado Savitzky–Golay
(rojo) contra el tiempo. **Muestra el grosor, que no es el canal de detección** (es `center_px`); en Video_268 y
Video_583 el grosor casi no se mueve. Figura de esta revisión (`cuatro_series_video_prueba.png`, 20 s de Video_prueba):
los dos bordes suben y bajan juntos (recorrido ≈ 7.3–7.6 px) y el grosor sólo 1.7 px, o sea que casi todo el
movimiento es traslación y `center_px` es el que lo muestra. Cómo leerla: picos hacia arriba en los bordes = el gel
baja en la imagen (y crece hacia abajo); el grosor debería quedar plano; saltos en escalera en el grosor indican
cambios del conjunto de inliers (Etapa 4).

---

## Etapa 6 ★ — detección de contracciones y elección del umbral k (2026-09-30)

**Archivos:** `scripts/contraction_report.py` (funciones `detrend_median`, `mad`, `_signo_evento`, `escaneo_estabilidad`,
`elegir_k_meseta`, `analizar`, `graficar`, `main`) y el test `tests/test_seleccion_k.py`. **Se ejecutó** sobre las seis
`serie_temporal.xlsx` vigentes: escaneo con grilla fina, sensibilidad a `win_s` y `sep_s`, calibración contra ruido
(bootstrap de bloques del ruido real) y curva de detección con eventos inyectados.

**Entra:** `center_px` por fotograma (hoja `diagnostics`). **Sale:** lista de eventos (tiempo y amplitud en px), `k` elegido,
veredicto `conteo_reportable`, y todo lo de las Etapas 7–8 (ritmo, cinética); archivos `contracciones.xlsx`,
`09_contracciones_<video>.png`, `10_ritmo_*.png`, `11_cinetica_*.png`.
**Supone:** (1) la deriva lenta se quita bien con una mediana móvil de 2 s; (2) el ruido es el MAD de esa señal; (3) un
evento es un pico por encima de `k × MAD` separado ≥ `sep_s` del siguiente; (4) la señal invertida sirve de control de
ruido (H13); (5) un `k` dentro de una meseta de conteo constante con 0 falsos da el conteo verdadero.

**Cómo funciona, paso a paso**
1. `fps = 1 / mediana(diff(time_s))` (30.00 en los seis videos).
2. **Quitar deriva:** `señal − mediana móvil centrada` de `int(2 s × fps) | 1` = 61 muestras.
3. **Signo:** se mira qué cola (> 4 MAD hacia arriba o hacia abajo) es más pesada y se da vuelta la señal para que los
   eventos queden hacia arriba (empate → +1).
4. **Ruido `m`** = 1.4826 × mediana de |señal − mediana|.
5. **Escaneo:** para k en (3, 4, 6, 8, 10, 12, 15, 20) cuenta picos de la señal con `find_peaks(altura = k·m, distance = int(0.3·fps))`
   y picos de la señal invertida (falsos de control).
6. **Elegir k:** descarta los k con falsos ≠ 0, busca tramos de k consecutivos con el mismo conteo (> 0) y ≥ 2 puntos;
   gana la meseta de k más bajo y se usa su k más bajo. Sin meseta: `conteo_reportable = False`, se usa k = 10 sólo para auditar.
7. Con ese `k` se detectan los eventos finales; después `rhythm_split` (Etapa 7) y `cinetica` (Etapa 8).

**Escaneo con grilla fina (0.25) frente a la grilla del código**

| video | lo que elige el código | meseta con grilla fina | comentario |
|---|---|---|---|
| Video_prueba | k=6 → 28 | 28 eventos en k=5.25–15 (×2.9) | estable; ver H8 por `sep_s` |
| Video_063 | k=6 → 6 | 6 en 5.25–8.5 (×1.6); 5 en 8.75–25 (×2.9) | la elegida es la más angosta (H11) |
| Video_268 | k=6 → 6 | 6 en 5.5–25 (×4.6) | muy estable |
| Video_466 | k=4 → 5 | 5 en 4.0–18.25 (×4.6) | el k elegido es el borde de la meseta |
| Video_491 | sin meseta | sólo tramos de 1–3 eventos (k 9–12) | "no reportable" |
| Video_583 | k=12 → 6 | 6 en 11.75–25 (×2.1) | estable |

**Sensibilidad (resultado = eventos, k elegido; "NR" = no reportable)**

| `win_s` (s) | 1.0 | 1.5 | 2.0 (defecto) | 3.0 | 5.0 |
|---|---|---|---|---|---|
| Video_prueba | 28 (k 8) | 28 | 28 | 28 | 28 |
| Video_063 | **5 (k 15)** | 6 | 6 | 6 | 6 |
| Video_268 | 6 (k 10) | 6 | 6 | 6 | 6 |
| Video_466 | 5 (k 6) | 5 | 5 | 5 | 5 (k 6) |
| Video_491 | NR | NR | NR | **6 (k 8)** | **6 (k 8)** |
| Video_583 | 7 (k 12) | 6 | 6 | 6 | 6 |

**Calibración (bootstrap de bloques de 60 muestras del ruido real, con eventos enmascarados ±2 s; 1 800 muestras)**
- **Sólo ruido:** 0 de 600 series (200 × 3 videos) salen con "hay meseta": el criterio es conservador.
  Precaución: al enmascarar eventos el ruido remanente puede ser más limpio que el real.
- **5 eventos inyectados** (forma tomada del promedio alineado de Video_268), fracción de series declaradas reportables:

| amplitud del pico | 4 MAD | 6 MAD | 8 MAD | 10 MAD | 15 MAD |
|---|---|---|---|---|---|
| ruido de Video_268 | 0 % | 12 % | 56 % | 96 % | 100 % |
| ruido de Video_466 | 0 % | 3 % | 57 % | 90 % | 100 % |
| ruido de Video_063 | 3 % | 25 % | 72 % | 95 % | 100 % |

  Cuando se declara reportable, el conteo es exactamente 5 en el 91–100 % de los casos a partir de 8 MAD. Es decir: el
  método casi no da falsos positivos, pero necesita eventos de ≥ 8–10 MAD para verlos de forma confiable.

**Gráficos de la etapa.** (a) `09_contracciones_<video>.png` (un renglón por video): a la izquierda, `center_px` sin deriva
contra el tiempo con un triángulo rojo por evento; a la derecha, el promedio de los eventos alineados en su pico
(azul = traslación, rojo = grosor, cada uno en su eje). Se lee: los triángulos tienen que caer sobre picos claros; el
promedio debe ser un pico limpio y angosto. (b) El escaneo de umbral (conteo de eventos y de falsos contra k; en el
proyecto sale en la sección 10 del cuaderno / `05_estabilidad_umbral`): una meseta ancha con falsos = 0 es buena señal;
una escalera que baja sin tramos planos o con falsos parecidos a los eventos, es ruido. Figura de esta revisión:
`escaneo_umbral_fino.png`.

---

## Etapa 7 — separar estimuladas de espontáneas: enganche de fase (2026-09-30)

**Archivo:** `src/rhythm_split.py` (completo, 621 líneas), llamado desde `contraction_report.analizar`. **Se ejecutó** sobre
los eventos de los seis videos vigentes: comparación contra 0.1 Hz, prueba con eventos al azar, series espontáneas
barajadas, pérdida progresiva de latidos estimulados y 1 000 simulaciones del nulo.

**Entra:** tiempos (y amplitudes) de los eventos de la Etapa 6, la duración del video y la resolución (1 / fps).
**Sale:** `hay_estimulacion`, período `T ± error`, frecuencia, jitter, tasa de captura, y tres grupos de eventos:
`estimulados`, `estimulados_dudosos` y `espontaneos`; tablas `grilla_*`, `ritmo_*`, `espont_*` y `10_ritmo_*.png`.
**Supone:** (1) un estimulador de cuarzo dispara en instantes `fase + n·T`; (2) las espontáneas no saben del reloj; (3) un
tren real ocupa ≥ 75 % de sus ranuras; (4) bajo "sin reloj" los instantes de los eventos son uniformes en la ventana.

**Cómo funciona.**
1. **Barrido:** 600 períodos candidatos (0.3 s hasta span/3); para cada uno se ancla la grilla en cada evento y se cuentan
   las ranuras ocupadas dentro de ±3 fotogramas (0.1 s).
2. **Puntaje z** contra lo esperado por azar según la densidad de eventos. Anti-armónicos: exige captura ≥ 75 % y, entre los
   candidatos con z ≥ 90 % del máximo, elige el período MÁS LARGO.
3. **Refinado:** Theil–Sen (robusto) y dos o tres pasadas que reasignan con tolerancia = 4 × jitter (mín. 2 fotogramas) y
   sueltan espontáneas que coincidían por azar; ajuste final por mínimos cuadrados, con piso de error = resolución/√12.
4. **Prueba de significancia:** Monte Carlo (200 simulaciones, semilla 0) con tiempos uniformes en la misma ventana y el
   mismo número de eventos; p = (casos con z ≥ observado + 1)/(201); alfa 0.01. Con menos de 6 eventos no se hace.
5. **Rescate:** por cada ranura libre, el evento libre más cercano dentro de ±10 % de T (±1 s si T = 10 s) se marca
   "estimulado dudoso".
6. `comparar_con_equipo` contrasta la frecuencia medida con la configurada.

**Resultados en los cinco videos con tren (suponiendo 0.1 Hz configurados)**

| video | eventos | período (s) | f (Hz) | t vs 0.1 Hz | captura | p |
|---|---|---|---|---|---|---|
| Video_prueba | 28 | 10.00744 ± 0.00408 | 0.09993 | −1.7 | 7/7 | 0.00498 (piso) |
| Video_063 | 6 | 9.99917 ± 0.00304 | 0.10001 | 0.3 | 5/5 | 0.00498 (piso) |
| Video_268 | 6 | 9.99990 ± 0.00230 | 0.10000 | 0.0 | 6/6 | 0.00498 (piso) |
| Video_466 | 5 | 9.99433 ± 0.01197 | 0.10006 | 0.5 | 5/5 | **NaN (no se corrió la prueba)** |
| Video_583 | 6 | 10.00119 ± 0.00675 | 0.09999 | −0.15 | 6/6 | 0.00498 (piso) |
| Video_491 | 2 | sin tren (menos de 4 eventos) | — | — | — | — |

Cuatro estimulados alcanzan para encontrar el tren aun con 21 espontáneas alrededor; con tres, el buscador se engancha
a la actividad espontánea (T = 0.566 s, 15–17 "estimulados") o no declara tren. Sobre los cinco videos, el período medido
coincide con el configurado dentro de 1.8 errores estándar: es una validación independiente de la base de tiempo PTS.

**Gráfico de la etapa.** `10_ritmo_<video>.png`: izquierda, la señal sin deriva con triángulos rojos (estimulados),
naranjas (dudosos) y azules (espontáneos) y líneas rojas punteadas en las ranuras esperadas del tren; derecha, el
error en ms de cada latido estimulado respecto de su ranura, con la banda de tolerancia. Se lee: los rojos deben caer
sobre las punteadas; los puntos de la derecha, cerca de 0 y dentro de la banda. Figura de esta revisión: `10_ritmo_ejemplos.png`.

---

## Etapa 8 — cinética: TTP, RT50 y amplitud relativa (2026-09-30)

**Archivo:** `src/cinetica.py` (254 líneas, completo) y `tests/test_cinetica.py` (90 líneas). Se llama desde
`contraction_report.analizar`. **Se ejecutó** sobre los seis videos vigentes, por grupo (estimuladas/espontáneas), variando
los niveles de umbral y `win_s`, y con eventos sintéticos con meseta en el pico.

**Entra:** tiempos `t`, señal `r` (centro sin deriva), posiciones de los picos, el ruido (MAD) y el grosor en reposo.
**Sale:** por evento: amplitud A, TTP, RT50, duración (onset→offset), cada uno con intervalo [mín, máx], y la marca
"medible" (≥ 5 fotogramas); por video: mediana, cota superior si no es reportable, y amplitud relativa (%).
**Supone:** (1) el evento sube y baja sin otro evento adentro (la ventana se corta en el pico vecino); (2) cruces de 10 % y
50 % de A bien definidos por encima del ruido; (3) el pico es un punto, no una meseta; (4) el grosor en reposo es una
mediana móvil del grosor crudo.

**Cómo funciona.**
1. **A** = valor de la señal en el pico. **Onset** = último instante antes del pico con señal < 10 % de A (buscando hacia atrás).
2. **TTP** (time to peak, tiempo de subida) = t(pico) − t(onset). **RT50** = tiempo desde el pico hasta caer al 50 % de A.
3. Como el muestreo es discreto (33 ms), cada tiempo tiene un intervalo [mín, máx] según en qué fotograma cae el cruce, y
   el "pico" se toma como la meseta de fotogramas a menos de 2 × ruido del máximo (Z_PICO).
4. **Medible:** el evento necesita ≥ 5 fotogramas entre onset y pico (TTP) o entre pico y 50 % (RT50).
5. **Resumen:** el video es "reportable" solo si el conteo de eventos lo es Y la mediana de fotogramas ≥ 5; si no, el valor
   es NaN y se informa la cota superior. **Amplitud relativa** = 100 · A / grosor en reposo (traslación del centro sobre grosor).

**Resultados (reproducen la tabla de `metricas-cinetica-TTP-RT50.md`)**

| video | fotogramas TTP / RT50 | TTP | RT50 | amp. relativa | veredicto |
|---|---|---|---|---|---|
| Video_prueba | 2 / 2 | < 102 ms | < 103 ms | 0.71 % | no medible (cota) |
| Video_063 | 2 / 2 | cota | cota | 0.53 % | no medible |
| Video_268 | 2 / 2 | cota | cota | 0.57 % | no medible |
| Video_466 | 9 / 5 | 284 [137, 365] ms | 160 [70, 260] ms | 2.13 % | reportable |
| Video_583 | 8 / 6 | 258 [129, 335] ms | 181 [99, 301] ms | 1.31 % | reportable |
| Video_491 | — | conteo no reportable (2 eventos, uno sin TTP/RT50) | | | no reportable |

**Gráfico de la etapa.** `11_cinetica_<video>.png`. Izquierda: cada evento (gris) normalizado por su amplitud y alineado en
el pico (fotograma 0), con la mediana en azul y líneas punteadas al 10 % (verde) y 50 % (rojo); se lee el TTP como lo que hay
entre el cruce verde de subida y el 0, y el RT50 como lo que hay entre 0 y el cruce rojo de bajada. Derecha: TTP y RT50 de cada
evento con su barra [mín, máx] y la zona gris "< 5 fotogramas": si el punto y su barra caen en la zona gris, no es medible.
Video_prueba (arriba): el pulso dura ~3 fotogramas, todo en gris. Video_583 (abajo): pulso lento de ~15 fotogramas, medible.
Figura de esta revisión: `11_cinetica_ejemplos.png`.

---

## Etapa 9 — el segundo motor (`event_detection.py`) y el cuaderno (2026-09-30)

**Archivos:** `src/event_detection.py` (431 líneas, completo) y `Analisis_Contractilidad_v4.ipynb` (todas las celdas). **Se ejecutó**
el motor sobre los seis videos con la configuración del cuaderno (canal `center_px` con signo, k automático, agudeza 1.30) y se
comparó evento por evento con el reporte; se repitió el escaneo de k con el fps declarado en vez del de los PTS; se probó un NaN
y se corrieron los segmentos de ritmo del cuaderno. No se re-ejecutó el cuaderno entero (no hay los videos crudos en esta sesión);
se lo revisó celda por celda contra las salidas ya guardadas.

**Qué es.** `event_detection.py` es el detector **original** (anterior a `contraction_report.py`). El reporte (Etapa 6) es el que
produce `contracciones.xlsx`; este motor sigue vivo porque el cuaderno lo usa en las secciones 8, 9, 10 (segunda opinión) y 12, y porque
`scripts/analyze_contractions.py` (obsoleto) lo importa.

**Entra:** un `DataFrame` con `time_s` y una columna de señal (en el cuaderno, `senal_contraccion = −signo·center_px`, **sin quitar la deriva**).
**Sale:** `ContractionResult` (tabla de eventos, línea base, profundidad, señal suavizada, ancho de evento medido, ruido, umbral) y,
aparte, segmentos de ritmo y perfil de frecuencia.
**Supone:** (1) la contracción es una excursión hacia abajo; (2) los eventos ocupan una minoría del tiempo, así que un percentil alto móvil
da el estado relajado; (3) el ancho de evento medido en los propios datos alcanza para fijar todas las ventanas; (4) el ruido simétrico.

**Cómo funciona.**
1. **Suavizado ligero:** Savitzky–Golay de ventana 0.1 s (5 fotogramas), grado 3.
2. **Pasada 1, medir la escala:** línea base = percentil 90 móvil con ventana `clip(0.15·duración, 3, 30)` s (unos 10 s acá); profundidad = base − señal;
   ruido = MAD; picos con prominencia ≥ 5 × ruido; **ancho de evento** = mediana del ancho a media altura (mínimo 2 fotogramas; 0.2 s si no hubo picos).
3. **Pasada 2:** ventana de línea base = `max(8·ancho, 1.5 s)`; nuevo ruido (MAD de la profundidad); umbral = k × ruido; candidatos = picos de profundidad con
   prominencia ≥ umbral y separación 0.8·ancho.
4. **Agudeza:** amplitud cruda dividida por la amplitud tras suavizar con una ventana de 3× el ancho; se descarta si < 1.30.
   El tiempo del evento es el mínimo de la señal **cruda** (sin suavizar) en ±1 ancho alrededor del candidato.
5. **Herramientas:** `threshold_stability_scan` (conteo vs k), `symmetric_false_positive_check` (mismo detector sobre la señal invertida; "dudoso" si
   `n_arriba ≥ 0.5·n_abajo`), `segment_by_rhythm` (tramos de frecuencia por razones entre intervalos), `analyze_segments`, `frequency_profile` (autocorrelación móvil).

**Resultados: motor `ed` contra el reporte, mismos datos (k del reporte)**

| video | k | reporte | `ed` | diferencia |
|---|---|---|---|---|
| Video_prueba | 6 | 28 | 29 | `ed` agrega t = 15.28 s (1.92 px), dentro de la ráfaga |
| Video_063 | 6 | 6 | 6 | — |
| Video_268 | 6 | 6 | 6 | — |
| Video_466 | 4 | 5 | 6 | `ed` agrega t = 59.01 s (1.08 px, 2 % sobre su umbral de 1.058 px); además su 1.er evento cae en 14.243 s contra 14.312 s del reporte |
| Video_491 | 10 | 2 (no reportable) | 0 | `ed` no detecta nada |
| Video_583 | 12 | 6 | 6 | — |

Control de falsos de `ed` (arriba / abajo) con el k del reporte: Video_prueba 12 de 29 (razón 0.41, pasa como "señal por encima del ruido"); Video_466 4 de 6 ("dudoso: subir amp_k"),
aunque el escaneo del reporte da 0 falsos en su meseta; los otros cuatro, 0 a 1.

**Gráfico de la etapa.** `12_motor_ed_comparacion.png`: fila de arriba, la señal (gris), la versión suavizada (rojo) y la línea base de percentil 90 (azul punteada); fila de abajo,
la profundidad = base − señal, el umbral (rojo punteado), los eventos de `ed` (▼, a la altura de su amplitud) y los del reporte (▲, abajo). Se lee: un evento es un pico de profundidad que
supera el umbral. **Izquierda (Video_prueba, 10–22 s):** ráfaga de tres o cuatro eventos; `ed` ve uno más (15.28 s) que el reporte. **Derecha (Video_466, 8–64 s):** la línea base no es plana (escalones de hasta ~1 px
cuando hay eventos o deriva), el ruido de profundidad es alto (0.26 px) y el evento de 59 s apenas roza el umbral.

La **sección 12 del cuaderno** es el otro gráfico: muestra tramos de ritmo de `ed`, no el enganche de fase de la Etapa 7 (ver H46).

---

## Etapa 10 — scripts de diagnóstico, figuras 07 y 08, y utilidades (2026-09-30)

**Archivos:** `scripts/motion_check.py` (351 líneas, completo), `scripts/signal_check.py` (182, completo), `scripts/analyze_contractions.py` (obsoleto; cabecera y
funciones), `scripts/inspect_frame.py` (290; cabecera y argumentos, **no se ejecutó**), `ordenar_carpeta.py` (cabecera y guardas). **Se ejecutó** `motion_check.py` sobre
Video_prueba completo (2 006 fotogramas, con la misma ROI 454–1516 del reporte; el video se trajo de la computadora de Franco) y `signal_check.py` sobre los seis videos con las dos columnas,
más las pruebas (`test_seleccion_k.py`: 16/16; `test_cinetica.py`: todo OK).

**Para qué sirven.** Son herramientas para responder dos preguntas antes de discutir conteos: ¿qué se mueve en el video? (`motion_check`) y ¿hay una población de contracciones o es ruido? (`signal_check`).
No forman parte del flujo que produce `contracciones.xlsx`.

**`motion_check.py`.** *Entra:* el video crudo (y opcionalmente la ROI). *Sale:* `07_movimiento.png`, `movimiento.xlsx` y un veredicto impreso. *Supone:* que comparar cuánto se modulan las diferencias entre fotogramas consecutivos
|I(t) − I(t−1)| dentro del gel, dentro del interior del gel y en una franja de fondo de control, distingue "se mueven sólo los bordes" (= cambio de grosor) de "se mueve la textura" (= traslación/axial). Además mide dos desplazamientos por
correlación cruzada con subpíxel: `desp_vert_px` (traslación vertical de la franja) y `desp_axial_px` (a lo largo del gel).

**Resultado sobre Video_prueba.** Modulación del gel con bordes 2.8 × el fondo; interior 1.9 × el fondo; veredicto impreso: "se mueven sólo los bordes, compatible con cambio de grosor: el observable del pipeline principal es el correcto" (ver H50).
`desp_vert_px`: RMS 0.30 px, skew +11.3, correlación del pico > 0.5 en el 100 % de los cuadros. `desp_axial_px`: RMS 0.24 px, skew −9.6, eventos de hasta −3.3 px.
Correlación entre `center_px` (bordes) y `desp_vert_px` (intensidad), ambos sin deriva: **0.915**; con `thickness_px`: −0.43. Pendiente `desp_vert ≈ 0.42 · center` en todo el video y **0.18 × en los eventos** (ver H51).

**Gráficos de la etapa.**
- `07_movimiento.png` (cuatro paneles, eje x = tiempo en s): (1) movimiento total |I(t)−I(t−1)| del gel (rojo) contra el fondo (gris); (2) el mismo movimiento por tercio axial del gel; (3) traslación vertical de la franja (`desp_vert_px`, px);
  (4) desplazamiento axial de la textura (`desp_axial_px`, px). Se lee: los seis picos grandes (cada 10 s) son el tren estimulado; en los paneles 1 y 2 se ve además un "peine" regular de picos chicos
  en todo el video, también en el fondo (ver H52); en los paneles 3 y 4 los eventos son limpios (el axial va hacia abajo, el vertical hacia arriba: el signo depende del eje).
- `08_asimetria.png` (por serie: izquierda, la señal sin deriva con líneas a ±4 × ruido; derecha, histograma con eje y logarítmico). Se lee: una cola larga hacia un solo lado indica eventos; el script sólo sabe mirar la cola **negativa** (ver H49).
  Figura de esta revisión: `08_asimetria_ejemplo.png` (Video_063 y Video_prueba sobre `center_px`: ambos con cola larga hacia **arriba** y el veredicto dice "ambiguo").
- `13_traslacion_dos_metodos.png` (de esta revisión): `center_px` (rojo, por bordes) y `desp_vert_px` (azul, por correlación de intensidad), ambos sin deriva y con el signo de evento, sobre Video_prueba; abajo, zoom de 10 a 22 s. Se lee: coinciden en **cuándo** ocurre cada evento y en su forma; difieren en cuánto valen (la azul es más chica).

**Utilidades.** `ordenar_carpeta.py` tiene una guarda explícita (se niega a correr si no hay carpetas `_v6`), y mueve en vez de borrar: está bien. `analyze_contractions.py` está rotulado obsoleto; el cuaderno sigue importándolo (H46).
`inspect_frame.py`: sólo leí la cabecera y los argumentos; no la ejecuté.

---

## Conocidos antes de empezar (a confirmar)

Detalle y evidencia en la sección 3 de la guía.

| id | severidad | resumen | estado |
|---|---|---|---|
| H1 | BUG | un solo fotograma `REJECTED` (NaN) anula el reporte en silencio | **confirmado** en Etapa 5 (ver H31: 28 → 0 eventos con un solo NaN) |
| H2 | RIESGO | dos detectores de eventos (reporte vs `event_detection`/cuaderno): 28 vs 29 en Video_prueba. **Hipótesis nueva:** esa diferencia puede ser el efecto de H8 y no de que los algoritmos difieran | abierto |
| H3 | DEUDA | el cuaderno arma ventanas con el fps declarado, el reporte con el de los PTS | abierto |
| H4 | DEUDA | MAD y mediana móvil repetidos en varios módulos | abierto |
| H5 | DEUDA | `escaneo_estabilidad` tiene `sep_s=2.0` por defecto; el script usa 0.3 | **resuelto 2026-10-01** (Fase 2.2: sin separación mínima) |
| H6 | DEUDA | `detect_contractions` tiene `raw_col="thickness_px"` por defecto | abierto |
| H7 | — | default `pts`, `ordenar_carpeta.py`, escaneos vigentes en el test, `_v6` en docs | verificado 2026-09-30. El aviso de caída a `frames` existe (`pipeline.py` l. 252) pero solo salta si no hay timestamps legibles: ver H15 |

---

## Nuevos

### H8. El 28 vs 29 de Video_prueba depende de la separación mínima entre picos (`sep_s`): hay una ráfaga real con espaciado ≈ 0.3 s
- Archivo / función / líneas: `scripts/contraction_report.py`: `escaneo_estabilidad` (l. 105,
  `d = max(1, int(sep_s * fps))`), `analizar` (l. 257 y 272) y el aviso de fusión (l. 297).
- Severidad: **RIESGO** (afecta hoy a un número vigente).
- Qué pasa: `distance` de `find_peaks` se calcula con `int(sep_s · fps)`, que **trunca**. Con el fps de
  los PTS (`30.000000000001705`) da `int(9.0000000000005) = 9`; con el fps declarado (29.73) daba
  `int(8.92) = 8`. Dos picos de Video_prueba están separados exactamente 8 fotogramas: t = 15.278 s
  (1.663 px) y t = 15.550 s (1.886 px), ambos ~19–22 × MAD (MAD = 0.0854 px). Con `distance = 9` el
  algoritmo se queda con el más alto y borra el otro. Con `distance = 8` quedan los dos.
- Evidencia: sobre `data/processed_data/Video_prueba/serie_temporal.xlsx`, `center_px`,
  `r = signo · detrend_median(x, fps, 2.0)`, `find_peaks(r, height=6*mad(r), distance=8)` → 29 picos;
  `distance=9` → 28. `escaneo_estabilidad(r, 29.73, sep_s=0.3)` da `[84,36,29,29,29,29,29,26]`
  (meseta de 29); con el fps de los PTS da `[83,35,28,28,28,28,28,26]` (meseta de 28). En Video_063 no
  cambia nada. El aviso `picos_con_sep_menor` **no aparece** en el `resumen` de Video_prueba.
- Qué afecta hoy: sí. `n_eventos` = 28 de Video_prueba (y, arrastrados, intervalos, amplitud
  mediana, cinética) depende de esto. El cambio 29 → 28 que se atribuyó a "pasar a PTS" llega por un
  camino indirecto: el fps pasó de 29.73 a 30.000 y eso movió `distance` de 8 a 9 fotogramas. No es que
  los tiempos de los eventos estén mejor corregidos; es un efecto de redondeo. Comprobado que la
  ventana de la mediana móvil no influye: con la ventana de 30.000 fps y `distance=8` también da 29.
- Propuesta: (1) mirar la señal entre 15.28 y 15.55 s para decidir si son dos eventos; (2) tratar la
  separación mínima como un número entero de fotogramas explícito (o al menos `round`, no `int`), de modo
  que no dependa de la parte decimal de un fps; (3) revisar por qué no saltó el aviso de fusión.
- Estado: abierto.
- **Actualización Etapa 6.** No es un solo fotograma: el conteo baja de a uno al subir `sep_s`. Video_prueba:
  29 (≤ 0.25 s) → **28 (0.30)** → 27 (0.35) → 26 (0.40–0.50) → 16 (1.0). Video_466: 7 (0.1) → 6 (0.2) → 5 (≥ 0.25).
  Video_583: 8 (0.1) → 6 (≥ 0.2). Causa en Video_prueba: una ráfaga a 14.94–15.84 s con picos de 19–22 MAD separados
  por 0.340, **0.272** y **0.288** s, y un par a 0.392 s (7.28–7.67 s); `sep_s = 0.3` cae justo en medio. El 28 o el 29 no
  es un error de tiempo: es una ráfaga real cuyo espaciado es del orden del parámetro. Video_063 y Video_268 no cambian.

### H9. La regresión de CLAUDE.md no tiene una línea base clara, y el test no puede detectar H8
- Archivo: `CLAUDE.md` (regla "Regresión sobre Video_prueba y Video_063 … exactamente los mismos
  números que antes"), `tests/test_seleccion_k.py`.
- Severidad: PREGUNTA / DEUDA.
- Qué pasa: Video_prueba pasó de 29 a 28 eventos (H8), así que la regla no se cumplió literalmente; el
  test conserva el caso `"Video_prueba": … 29` bajo el comentario "los dos videos validados: la respuesta
  NO puede cambiar" junto al caso vigente `"prueba v6": … 28`. Además el test alimenta a
  `elegir_k_meseta` con conteos escritos a mano: no corre el escaneo, así que un cambio en
  `find_peaks`/`distance` no lo rompe.
- Evidencia: `tests/test_seleccion_k.py`, diccionario `CASOS`; H8.
- Qué afecta hoy: no cambia resultados; sí hace que "16/16 OK" tranquilice más de lo que debería.
- Propuesta: decidir cuál es la línea base vigente; agregar una regresión sobre las series guardadas que
  corra el escaneo real (la comparación de la sección 1 de la guía ya hace eso a mano).
- Estado: abierto.

### H10. El cuaderno se contradice sobre qué funciones usa
- Archivo: `Analisis_Contractilidad_v4.ipynb`, celda de la sección 0 vs. secciones 8, 9 y 11c.
- Severidad: DEUDA (relacionado con H2 y H3).
- Qué pasa: la sección 0 dice "No se reimplementa nada: este cuaderno llama exactamente a las mismas
  funciones que `main.py` y `scripts/contraction_report.py`". Pero la sección 8 dice "Todo el motor de
  detección (`src/event_detection.py`) sigue siendo el mismo" (percentil 90 móvil + agudeza) y la 11c
  admite que sus eventos "pueden diferir en uno o dos de los de la sección 9 (en Video_prueba: 28 contra
  29)". La sección 10 dice tener "diez escaneos reales" en el test; hoy son 16.
- Evidencia: texto de las celdas 2, 18, 22 y 26 del cuaderno.
- Qué afecta hoy: no cambia resultados del reporte; sí puede llevar a reportar del cuaderno un conteo
  distinto al de `contracciones.xlsx`.
- Propuesta: corregir el texto de la sección 0; decidir el detector canónico (Etapa 9).
- Estado: abierto.

### H11. El "6" validado de Video_063 no es evidencia independiente de la regla "gana la meseta de k más bajo"
- Archivo: `CLAUDE.md` hallazgo 4; `contraction_report.py::elegir_k_meseta`; `contracciones.xlsx` de Video_063.
- Severidad: PREGUNTA (posible RIESGO).
- Qué pasa: los 6 eventos de Video_063 son 5 estimulados (t = 11.91, 21.91, 31.91, 41.91, 51.91 s: grilla
  de 10 s, capturada 5/5, error ≤ 0.5 ms) **más uno en t = 0.308 s**, con amplitud 0.295 px contra
  ~1.5 px de los estimulados, a 9 fotogramas del inicio del video (zona donde la mediana móvil de 2 s
  no tiene ventana completa). El reloj del estimulador respalda 5, no 6. La regla "meseta de k más bajo"
  se justificó con este caso (la meseta de 6 tiene solo 2 puntos, k = 6 y 8; la de 5 tiene 4).
- Evidencia: hoja `eventos_Video_063_CTRL1_5V` y `grilla_Video_063_CTRL1_5V`; resumen: `meseta_k_rango`
  = `6-8`.
- Qué afecta hoy: el `n_eventos` = 6 y la amplitud/intervalo mediano de Video_063.
- Propuesta: en la Etapa 6 ver cómo `detrend_median` trata los bordes y si el evento de 0.31 s es real;
  argumentar la regla del k más bajo con algo distinto de "da 6 en Video_063".
- Estado: abierto.
- **Actualización Etapa 6.** (1) Con grilla fina (0.25) la meseta de 6 eventos de Video_063 abarca k = 5.25–8.5 (factor
  ×1.6) y la de 5 eventos k = 8.75–25 (×2.9): la regla elige la más angosta en k. (2) El sexto evento (t = 0.308 s) tiene
  0.295 px = 8.6 MAD; en la simulación de la Etapa 6 un evento de ~8 MAD se declara "reportable" sólo el 56–72 % de las
  veces: está en el límite de la resolución del método. Ver H33 y H34.

### H12. La documentación no clasifica todos los métodos de ROI
- Archivo: `DOCUMENTACION.md` §2.2, `protocolo-analisis-videos.md`, `referencia-archivos-y-graficos.md`.
- Severidad: DEUDA / PREGUNTA.
- Qué pasa: `gauge_relajada` está en la cascada de DOCUMENTACION pero no figura entre los métodos
  aceptables ni entre los que obligan a mirar el perfil; `fallback_margin` figura en el protocolo pero no
  en la cascada. El criterio real de aceptación es la variación < 6 %, así que el nombre del método es
  secundario, pero los documentos no lo dicen.
- Evidencia: comparar las tres tablas. **Confirmado en la Etapa 2**: el código tiene 5 niveles + rescate + `fallback_margin`; `describe_roi` avisa solo para `solo_nitidez`, `franja_completa` y `fallback_margin`. El criterio efectivo es la variación ≤ 6 %, así que las listas de métodos son redundantes (ver H25).
- Estado: confirmado; se cierra con H25.

### H13. El control por señal invertida supone ruido simétrico
- Archivo: `contraction_report.py::escaneo_estabilidad` (conceptual).
- Severidad: PREGUNTA.
- Qué pasa: se llama "falso" a todo lo que el mismo detector encuentra en la señal invertida. Eso vale si
  el ruido es simétrico. Pero el propio método documenta asimetrías (motion blur positivo; excursiones
  bifásicas en Video_491). Un evento real con rebote se contaría como falso y podría impedir una meseta
  (o, al revés, un ruido asimétrico podría no aparecer del lado invertido).
- Evidencia: a mirar en Etapa 6 con `08_asimetria` / `skew` y con los falsos de Video_491.
- Estado: abierto.

---
- **Actualización Etapa 6.** Evidencia directa en datos reales: en Video_491 los "falsos" a k = 8 (2 en total) caen en
  t = 13.65 s y 34.6 s, **0.27 y 0.20 s después del último evento de cada ráfaga** (13.38 y 34.40 s): son el rebote
  posterior al evento, no ruido simétrico. Con `win_s = 3` desaparecen. Además, la cola > 4 MAD hacia arriba vs hacia
  abajo de la señal sin deriva es muy asimétrica en los seis videos (por ejemplo Video_prueba 6.6 % vs 0 %, Video_583
  5.2 % vs 0.8 %, Video_491 3.1 % vs 1.3 %).

### H14. `frames faltantes (%)` está inflado por el jitter de los timestamps
- Archivo / función / líneas: `src/pipeline.py`, `process_video`, l. 219–226.
- Severidad: DEUDA (afecta un número de diagnóstico y el aviso del 1 %; no toca el eje de tiempo).
- Qué pasa: hueco = `dt > 1.5 × mediana`, y se suman las partes fraccionarias (`dt/med − 1`) antes de
  redondear. Los timestamps tienen jitter: muchos `dt` caen entre 1.5 y 1.9 medianas sin que falte
  ningún fotograma, y cada uno suma 0.5–0.9 "fotogramas perdidos". El comentario del propio código
  dice "los huecos son los `dt` que valen un múltiplo entero", pero el código no lo exige.
- Evidencia (sobre la columna `time_s` de los seis `serie_temporal.xlsx`; pequeñas diferencias con la
  hoja `resumen` porque el xlsx guarda `time_s` redondeado): faltantes según el código actual vs. solo
  saltos ≥ 1.9 intervalos con `round(dt/med) − 1` por salto:
  Video_prueba 27 vs 24; Video_063 **24 vs 12** (23 "huecos" de jitter contaron 11.9 fotogramas);
  268 43 vs 35; 466 102 vs 93; 491 28 vs 27; 583 33 vs 33.
- Qué afecta hoy: el campo `frames faltantes (%)` de los seis (p. ej. Video_063: 1.28 % → ~0.65 %) y,
  con él, qué videos superan el aviso del 1 %.
- Propuesta: contar por salto (`round(dt/med) − 1`) y solo para saltos claros (≥ ~1.9); guardar aparte
  la medida del jitter (desvío de `dt/med`).
- Estado: abierto.

### H15. Un archivo sin timestamps reales pasa por PTS sin aviso
- Archivo / función / líneas: `src/io_utils.py::read_pts_seconds` (l. 58–87); `src/pipeline.py`
  l. 251–254.
- Severidad: RIESGO (no cambia ningún resultado vigente).
- Qué pasa: `read_pts_seconds` devuelve lo que OpenCV llame `POS_MSEC`. En contenedores sin hora por
  fotograma OpenCV la fabrica como `idx/fps`; el código no distingue eso de un PTS real. `usar_pts` es
  verdadero mientras haya más de 1 valor, así que el eje sería `idx/fps_declarado` (justo lo que el
  hallazgo 3 de CLAUDE.md dice que no hay que usar), la hoja `resumen` diría `base de tiempo: pts`, `0`
  huecos y `0 %` faltantes, y no habría aviso.
- Evidencia: video de 60 fotogramas escrito con `cv2.VideoWriter` en `.avi` (MJPG) y en `.mp4` (mp4v):
  `read_pts_seconds` devuelve `dt` únicos = 0.03333 s (perfectamente regular). Los seis videos reales,
  en cambio, tienen jitter (ver arriba), así que `dt` sin variación es una firma de tiempo fabricado.
  Límite de esta prueba: solo se probaron archivos escritos por OpenCV, no un `.avi` real del
  microscopio.
- Propuesta: comparar la variación de los `dt` (o su igualdad exacta con `1/fps_declarado`); si es
  nula, avisar "timestamps no confiables, el eje es frame/fps" y grabarlo en `resumen`.
- Estado: abierto.

### H16. La serie es irregular en el tiempo, pero el análisis posterior cuenta por índice (a verificar)
- Archivo: `contraction_report.py` (`analizar`: `fps = 1/mediana(diff(t))`, `detrend_median`,
  `find_peaks(distance=…)`), `cinetica.py` (fotogramas); ver Etapas 6 y 8.
- Severidad: PREGUNTA.
- Qué pasa: `time_s` conserva los saltos y el jitter, pero la ventana de 2 s, la separación mínima y los
  "5 fotogramas" de la cinética se cuentan en muestras. Con un salto de 13 fotogramas dentro de la
  ventana, esa ventana cubre más de 2 s reales; Video_466 tiene 10 saltos.
- Evidencia (parcial): una ventana de 61 muestras cubre 2.000 s en la mediana, pero hasta 2.400 s en
  Video_063 (3.4 % de las ventanas > 2.1 s) y hasta 2.602 s en Video_466 (**23.4 %** de las ventanas > 2.1 s).
  Falta ver cuánto cambia el resultado: se resuelve leyendo esas funciones y con un experimento.
- Estado: abierto.

### H17. Detalles menores de `io_utils` y `process_video`
- Severidad: DEUDA.
- (a) El período de Video_466 con PTS figura como 10.008 s en el docstring de `read_pts_seconds`, 10.006 s
  en el cuaderno y 10.00667 s en `cambios-roi-y-k.md`: son mediciones de corridas distintas (ROI distinta,
  `cambios-roi-y-k.md` lo explica: "mi ventana era un poco más ancha"), no un cálculo repetido. El valor
  vigente (`contracciones.xlsx`) es 9.9875 s de intervalo mediano (0.1001 Hz) y 9.9943 s entre ranuras de
  la grilla. Ningún documento dice cuál manda. (b) `process_video` decodifica el video tres
  veces (timestamps, proyección de máximos —que decodifica todos los fotogramas aunque use 1 de cada
  5— y el ciclo principal); medido en la nube: ~11 s para los timestamps y ~26 s para dos proyecciones de
  Video_prueba. (c) Si `idx >= n_pts` la rama de respaldo usa `idx/fps` con otro origen que
  `pts − pts[0]`; hoy es inalcanzable porque ambos lectores cuentan los mismos `read()`.
- Estado: abierto.

---

### H18. Una ROI manual no recibe veredicto de aceptación, y `--exigir-roi` no puede frenarla
- Archivo / función / líneas: `src/preprocessing.py`, rama manual de `auto_detect_roi` (l. 449–470);
  `main.py` l. 172 y 196.
- Severidad: RIESGO.
- Qué pasa: el diccionario `roi_quality` de la ROI manual no trae `cumple_criterio_aceptacion` ni
  `ancho_minimo_exigido_px`. `main.py` lo lee con `q.get(...)`, obtiene `None`, y el chequeo de
  `--exigir-roi` es `is False`, así que `None` pasa.
- Evidencia: hoja `resumen` de Video_466 (vigente, ROI manual 700–900): `ROI cumple criterio` = NaN y
  `ROI ancho minimo exigido (px)` = NaN, mientras los otros cinco tienen `1` y `180`. La variación (5.47 %) sí
  se calcula, pero no se convierte en veredicto.
- Qué afecta hoy: solo el registro de Video_466: su ROI cumple (5.47 %, ancho 200 ≥ 180) pero el resumen no
  lo dice. Un `--x-start/--x-end` con 30 % de variación tampoco abortaría con `--exigir-roi`.
- Propuesta: calcular el veredicto también para la ROI manual.
- Estado: abierto.

### H19. El ancho mínimo de 180 px rechazó la cintura real de Video_466, y su justificación no se sostiene
- Archivo / función / líneas: `src/preprocessing.py` l. 502 (`min_width`), 536; `main.py --roi-min-spacing`.
- Severidad: RIESGO (violación de la regla "ningún parámetro atado al tamaño del sujeto": esta vez en píxeles).
- Qué pasa: `min_width = 60 × 3.0 = 180 px`. En Video_466 el bloque `gauge_cintura` (696–846, 4.85 %, es
  decir, la cintura) mide 150 px y se descarta por 30 px; después gana `gauge_relajada` (12.44 %) y el rescate
  elige 944–1169. El comentario justifica los 3 px de separación con "no compartir el mismo ruido de imagen y el
  mismo tile de CLAHE". Pero con la grilla 8 × 8 de CLAHE, en 1920 × 1080 cada tile mide **240 × 135 px**: una
  ROI de 180–240 px cae en 1 o 2 tiles sea cual sea la separación de las columnas. La correlación del ruido
  entre columnas vecinas no se midió en ninguna parte.
- Evidencia: `roi_quality["alternativas"]` de Video_466 (ver Etapa 2); cálculo del tile arriba. Reproducir:
  `auto_detect_roi` sobre la proyección de máximos de `Video_466_EXP5_FAPS4_40V.mp4` con los defaults.
- Qué afecta hoy: la ROI automática de Video_466 (944–1169) y, por eso, que el vigente sea manual.
  Nada cambia en los otros cinco.
- Propuesta: medir cómo decae la correlación del error de borde entre columnas con la distancia; si no hay
  evidencia, definir el mínimo por un criterio distinto de "3 px" (no se probó cambiarlo).
- Estado: abierto.

### H20. El rescate no exige que la ventana contenga la cintura: el veredicto "cumple" no distingue cintura de meseta
- Archivo / función / líneas: `src/preprocessing.py`, `_widest_flat_window` (l. 261–296) y su uso (l. 562–575).
- Severidad: RIESGO (verificado con imágenes sintéticas; no observado todavía en un video real).
- Qué pasa: la ventana se elige solo por "la más ancha con variación ≤ 6 % entre columnas nítidas". No
  hay ninguna condición sobre la cintura. Si en el borde del cuadro hay una meseta de grosor constante (un
  anclaje ancho), es "plana" y puede ganar; `cumple_criterio_aceptacion` sale `True` porque solo mira
  la variación.
- Evidencia: gel sintético con zona plana de 150 px y meseta de anclaje al 230 % del grosor: método
  `gauge_rescate_plana`, ROI 0–615, variación 5.65 %, `cumple = True`; la zona plana verdadera (y la cintura)
  está en 831–1090. Igual con ampliación × 0.5 (zona plana de 150 px): ROI 480–750 contra 859–1062. En el
  Video_466 real el rescate eligió 944–1169, con grosor 208–220 px contra la cintura de 206 px (hasta +6.8 %,
  fuera del "+5 %" que define `near_waist`), es decir, junto a la cintura pero no en ella.
- Qué afecta hoy: ninguna ROI vigente comprobada; la de Video_466 es manual. Riesgo en videos nuevos con
  zona plana corta.
- Propuesta: exigir que la ventana rescatada contenga columnas con grosor ≤ cintura × (1 + tolerancia) y
  registrar la distancia a la cintura en `roi_quality`.
- Estado: abierto.

### H21. La cintura se estima con la mediana del grosor: depende de cuánto del cuadro ocupa la cintura
- Archivo / función / líneas: `src/preprocessing.py` l. 422–434.
- Severidad: PREGUNTA (posible RIESGO).
- Qué pasa: `escala = mediana(T)` sobre las columnas nítidas, y solo se usan las de grosor entre 0.6 y 1.6 ×
  esa escala. Si la cintura ocupa menos de la mitad de las columnas, la mediana cae en el anclaje y la
  cintura verdadera queda fuera de la banda.
- Evidencia (sintética, cintura verdadera 285 px): zona plana 450 px → cintura estimada 387; 300 px → 444;
  150 px → 450; con ampliación × 0.5 (verdadera 142) → 222. En los videos reales comprobados salió bien:
  Video_466 estima 206 (el mínimo real es ~201–206) porque su mediana (274) deja a 206 dentro de la banda.
- Qué afecta hoy: nada comprobado. Es la clase de dependencia que la regla de CLAUDE.md pide evitar.
- Propuesta: verificar `cintura_px` contra el mínimo del perfil en los seis vigentes; considerar un criterio
  que no dependa de la mediana.
- Estado: abierto.

### H22. `roi_min_gradient = 10` es un umbral de contraste absoluto sin origen documentado
- Archivo / línea: `src/preprocessing.py` (`min_gradient_for_roi`), `main.py --roi-min-gradient`.
- Severidad: RIESGO.
- Qué pasa: se compara la nitidez del borde, en niveles de gris por píxel, sobre la proyección de máximos
  **sin normalizar**. Un video más oscuro o con menos contraste no llega a 10.
- Evidencia: gel sintético gel 90 / fondo 60 (gradiente ≈ 4): ninguna columna pasa,
  método `franja_completa`, ROI 0–1920, variación 131 %, `cumple = False`; el fallo es ruidoso (aviso e
  incumplimiento), pero `--exigir-roi` está apagado por defecto. En Video_466 real la nitidez llega a 3.5
  dentro de la ROI manual y a ~10 en el borde de la ventana automática; en Video_063, 30–70.
- Qué afecta hoy: nada comprobado en los seis.
- Propuesta: documentar de dónde salió el 10 y evaluar expresar el umbral en relación con el contraste
  gel/fondo de la propia imagen.
- Estado: abierto.

### H23. Ventanas de suavizado proporcionales al ancho del cuadro, no al gel
- Archivo / líneas: `src/preprocessing.py` l. 393 (`k = max(5, w // 60)` = 32 px) y l. 403
  (`d = max(10, w // 50)` = 38 px).
- Severidad: PREGUNTA.
- Qué pasa: escalan con la resolución de la cámara, no con el tamaño de la cintura o del gel. Con una zona
  plana corta, una mediana de 32 px y un promedio de pendiente de ±38 px son grandes frente al detalle que
  el criterio de planitud quiere ver.
- Evidencia: solo lectura de código; no se cuantificó el efecto.
- Estado: abierto.

### H24. `outlier_frac` no es comparable entre ROIs: el criterio favorece la ventana de peor ajuste absoluto
- Archivo: `src/robust_fitting.py` l. 149–153 (umbral `max(3 × MAD, 0.4)`), criterio "outlier_frac < 10 %" del
  protocolo. A cerrar en la Etapa 4.
- Severidad: PREGUNTA.
- Qué pasa: el umbral de descarte se adapta a la dispersión del propio fotograma. Una ventana con núcleo
  muy estrecho y colas pesadas descarta una fracción mayor con errores absolutos menores.
- Evidencia: tabla de Video_466 arriba. La ventana automática 944–1169 tiene residuos 0.85/0.72 px y 16.2 % de
  outliers ("mala" según el criterio); la manual 700–900 tiene 1.78/0.67 px y 8.4 % ("buena"). El residuo del
  borde superior de la vigente (1.77 px) duplica el de la automática. Además, dos vigentes están por encima del
  0.77–0.87 px que `referencia-archivos-y-graficos.md` describe como sano: Video_466 (superior 1.77 px) y Video_583
  (inferior 1.43 px). Ni el residuo ni su asimetría forman parte de los tres chequeos de aceptación.
- Estado: abierto.

### H25. `preprocessing.py`: parámetro muerto que reintroduce la trampa, y documentación vieja
- Severidad: DEUDA.
- `auto_detect_roi(min_roi_width_frac=0.35)` sigue en la firma (l. 307) y en el docstring (l. 331), descrito
  como el ancho mínimo, pero ya no se usa: la variable `n_gel` (l. 488) se calcula y nadie la lee. Es
  exactamente el parámetro que CLAUDE.md cita como ejemplo de qué no hacer, y el docstring lo presenta como
  vigente. Además `_widest_flat_window` anuncia costo O(n) pero recalcula mínimo y máximo de la ventana en
  cada paso (no cambia resultados). Y `describe_roi` (pipeline.py l. 328) avisa solo para `solo_nitidez`,
  `franja_completa` y `fallback_margin`: `gauge_relajada` (variación 12.44 % en Video_466) no dispara aviso
  propio; el veredicto real es el 6 %, así que las listas de "métodos aceptables" son redundantes (cierra H12).
- Estado: abierto.

### H26. CLAHE desplaza el borde por una cantidad que cambia de fotograma a fotograma, del orden de la señal de grosor
- Severidad: RIESGO. Estado: abierto (a verificar con el control de sólo-luz).
- Qué pasa: `apply_clahe` remapea el contraste por tile (240×135 px) con un mapeo que depende del histograma
  del tile. Comparando crudo vs CLAHE con la misma ROI en 900 fotogramas: el borde superior se corre
  +0.48/+0.76 px y el inferior −0.42/−1.21 px (Video_prueba / Video_466) y la diferencia CLAHE−crudo **varía con
  el tiempo**: desvío 0.12/0.24 px en `center_px` y 0.27/0.44 px en el grosor. En Video_466 esa variación
  (0.44 px) supera el desvío del propio grosor crudo (0.31 px).
- Por qué importa: `protocolo-analisis-videos.md` concluye "CLAHE no fabrica ni deforma la señal" con UN video
  (Video_063: 5 eventos iguales, amplitud ±2 %, correlación 0.90 en `center_px` y 0.52 en grosor). Que el ruido
  baje con CLAHE (0.034 vs 0.050 px) no prueba que la posición sea más correcta; el mismo documento reconoce
  que la correlación de grosor es 0.52. El docstring de `apply_clahe` advierte justo de este riesgo (burbujas).
- Efecto práctico: detectar sobre `center_px` lo atenúa (los dos bordes se corren en sentido opuesto y casi se
  cancelan), pero cualquier número en px absolutos del grosor depende del preproceso.
- Matiz (aclarado con Nacho): un corrimiento CONSTANTE no molesta, porque se resta. Lo que preocupa es que
  cambia con el tiempo: CLAHE recalcula el mapeo de brillo por bloque según el contenido de ese fotograma, y
  el contenido cambia cuando el gel se contrae. No se sabe cuál versión (crudo o CLAHE) está más cerca de la
  verdad; sólo se sabe que difieren de forma variable. En `center_px` los dos bordes se corren en sentidos
  opuestos y casi se cancelan (por eso detectar sobre el centro es más robusto); el grosor queda expuesto.
- Pruebas propuestas, en orden de costo: (1) correr los seis videos con `--no-clahe` y comparar conteo y
  amplitudes; (2) el video de control de sólo-luz que ya pide el protocolo; (3) comprobar si la diferencia
  CLAHE−crudo se correlaciona con la señal (si lo hace, CLAHE estaría fabricando movimiento).
- Evidencia: `/tmp/claude-0/rev/e3d.py` (comparación por fotograma). Sugerencia de prueba: repetir el
  conteo con `--no-clahe` en los seis videos, y el control de sólo-luz que el protocolo ya pide.

### H27. La ventana de ±15 px deja poco margen real y descarta columnas en Video_466
- Severidad: RIESGO (bajo hoy, crece con el movimiento).
- Qué pasa: la ventana se centra en el borde de la imagen de MÁXIMOS, que es el borde más externo alcanzado.
  El borde real está casi siempre hacia adentro: abajo a −9.2 px de mediana (Video_prueba) y hasta −13.1 px
  (Video_466); arriba hasta +13.5 px. Del "±15" sólo sobran ~2 px de margen. En Video_466 el 0.26 % de las
  medidas (47 de 18 120) cae pegada al extremo de la ventana y queda NaN.
- Además: `half_window = 15` es un valor absoluto en píxeles, no relativo al movimiento del gel ni a la
  ampliación (regla del proyecto: ningún parámetro atado al tamaño del sujeto). La ventana no se re-centra con
  el fotograma anterior.
- Pérdida hoy: pequeña y el RANSAC la tolera, pero `outlier_frac` mezcla estas pérdidas con ruido real (H24).
- Estado: abierto. Prueba sugerida: repetir con `half_window` 20 y 25 y ver que las series no cambian.

### H28. `min_gradient` nunca actúa en estos videos; código muerto en `edge_detection.py`
- Severidad: DEUDA.
- `min_gradient = 5` se compara contra el gradiente tras CLAHE. El percentil 1 del pico es 9.5 (Video_466,
  borde superior) y 31 (Video_prueba): 0 medidas de 36 240 quedan por debajo. El filtro de "borde oculto" está
  de hecho apagado; las únicas columnas inválidas vienen del pico pegado a la ventana (H27). Un borde tapado de
  verdad sólo se detectaría si el pico cayera bajo 5, y nadie verificó que eso ocurra con una burbuja.
- `np.clip(delta, -1, 1)` es código muerto: con el máximo en el centro, \|delta\| ≤ 0.5 (máximo observado
  0.49998 en 200 000 perfiles). Su comentario ("delta puede explotar") es engañoso.
- `quality` se calcula (`pipeline.py` l. 123) pero no se usa después; el docstring de `EdgePoint` dice que sirve
  para descartar columnas y no es así.
- Polaridad fija (+1 arriba, −1 abajo): un gel oscuro sobre fondo claro fallaría sin aviso (a verificar).
- `subpixel_edge_sigmoid` (no se usa por defecto) difiere del parabólico en media +0.24 px y desvío 0.57 px
  (1 020 pares), comparable con las amplitudes de 0.3–1.9 px; no hay validación cruzada documentada y
  emite `RuntimeWarning: overflow` y `OptimizeWarning`.
- Estado: abierto.

### H29. En Video_466 el RANSAC agrega ruido y un corrimiento variable: los "outliers" son sistemáticos, no burbujas
- Severidad: RIESGO. Estado: abierto.
- En Video_466 el RANSAC es MÁS ruidoso que un ajuste por mínimos cuadrados que no descarta nada: +27 % en
  `center_px` (0.132 vs 0.104 px) y +48 % en el grosor (0.212 vs 0.144 px). Además desplaza la posición
  −0.46 px (superior) y −0.94 px (inferior) respecto de mínimos cuadrados, con un desvío temporal de 0.25 px
  (máx 1.4): la parte que varía con el tiempo es del tamaño del ruido del centro.
- Causa probable: el 47 % de las primeras 10 columnas del borde inferior y el 20 % de las últimas 10 del superior
  se descartan en casi todos los fotogramas. No son burbujas (cambiarían de columna): son los extremos de la ROI,
  donde el borde se aparta de una parábola. El conjunto de inliers cambia 2–3 columnas por fotograma y eso
  mueve la curva; y como `y_*_px` es la mediana de la curva sobre las 60 columnas, **incluidas las descartadas**,
  el valor depende de cómo se extrapola el modelo hacia ese extremo.
- El cuaderno ya da la regla ("outliers contiguos = el modelo está mal"); en Video_466 se cumple y nada
  lo frena: ni el veredicto de la ROI (H18/H24) ni `frame_quality` (todo `OK` mientras < 30 %).
- En Video_prueba RANSAC y mínimos cuadrados coinciden (diferencia 0.06 px): ahí el RANSAC no aporta ni
  perjudica. No hay evidencia, en estos dos videos, de burbujas que justifiquen el RANSAC; la simulación sí
  muestra que funciona cuando las hay.
- Relación con H19/H24: una ROI que incluye los extremos donde el borde se curva genera este efecto.
- Pruebas sugeridas: (1) repetir el conteo de eventos con `--fit-method` alternativo o mínimos cuadrados en los
  seis videos; (2) ver si la diferencia RANSAC−MCO se correlaciona con la señal de contracción; (3) medir el
  residuo del borde inferior en las primeras 10 columnas de Video_466 contra el resto.

### H30. El umbral adaptativo casi nunca toca el piso y es muy grande; el MAD de residuos por columna es alto
- Severidad: DEUDA.
- `3×MAD` da 2.0–2.9 px (mediana 2.4–2.9), con percentil 95 de 5.2 px en Video_466; el piso `residual_floor = 0.4`
  no se activó en ninguno de los 2 400 fotogramas. Con un umbral de ~2.5 px una burbuja que desplaza el borde
  2 px no se descarta (sesgo +0.08 px en simulación), y en los fotogramas con mal ajuste el umbral sube a 5 px
  y deja pasar aún más. El residuo típico por columna (MAD ≈ 0.78 px) es 2–6 veces mayor que el ruido entre
  fotogramas de la serie (0.1–0.3 px): el borde por columna es ruidoso y el promedio de 60 columnas lo
  compensa.
- `fit_edge_median` (opción `--fit-method median`) ajusta una constante: en simulación es la peor opción
  (sesgo +0.15 a +0.43 px, ruido ~1.3× el de RANSAC) y no hay aviso en la ayuda del flag salvo el docstring.
- `max_trials = 200` y `min_samples = grado + 1` (3 puntos) son los valores por defecto de sklearn, sin
  justificación documentada.
- Estado: abierto.

### H31. Un solo fotograma rechazado (NaN) deja sin resultado a todo el video, y `frame_quality` no se consulta nunca
- Severidad: RIESGO (robustez; hoy no ocurre en los seis videos). Estado: abierto. **Es la confirmación de H1** (ya figuraba como pendiente en `ESTADO-arranque-chat-nuevo.md`).
- El pipeline deja NaN en los fotogramas `REJECTED` ("no se inventan") y el análisis posterior no los maneja.
  Prueba: a `serie_temporal.xlsx` de Video_prueba le puse NaN en UN fotograma (fila 100) y corrí
  `contraction_report.analizar`: pasó de **28 eventos** (k=6, meseta) a **0 eventos** (k=10, sin meseta, `conteo_reportable = False`,
  ruido = NaN). Con el mismo fotograma interpolado vuelve a 28. Causa: `mad()` usa `np.median` y propaga el NaN.
- El resultado no es silencioso del todo (queda marcado "no reportable"), pero el motivo aparece como "no hay
  meseta" y no como "falta un fotograma": engaña al diagnosticar.
- `frame_quality` y `outlier_frac` no se usan en ningún script posterior (búsqueda en `scripts/`, `src/cinetica.py`,
  `event_detection.py`, `rhythm_split.py`): un fotograma `LOW_QUALITY` entra igual que uno `OK`. `thickness_mm_smooth` sólo
  se grafica.
- Sugerencia de prueba: test automático con 1, 3 y 30 NaN dispersos y 1 tramo contiguo de NaN.

### H32. La hoja `resumen` no alcanza para reproducir una corrida, y algunas cifras se leen mal
- Severidad: DEUDA (trazabilidad).
- Parámetros que cambian el resultado y NO se guardan: `ransac_residual_k`, `ransac_residual_floor`,
  `roi_tolerance`, `roi_min_gradient`, `roi_max_slope`, `roi_max_variacion`, `denoise`, `savgol_window`, `low_quality_frac`,
  `fps` forzado y si la ROI fue manual. Tampoco se guarda el commit del código, la fecha ni las versiones de
  OpenCV/scikit-learn. Los avisos de pantalla no quedan escritos.
- `fps usado` (en la hoja `resumen`) vale el fps DECLARADO por el archivo (29.72893 en Video_prueba) aun cuando el tiempo
  salga de los PTS (fps real 30.000): la cifra no es la que se usó.
- `contraccion max (px)` = máximo − mínimo del GROSOR. Con un solo fotograma anómalo cambia, y contradice el
  hallazgo del proyecto (la contracción es sobre todo traslación: ver la figura de la etapa).
- La columna `thickness_mm` es igual a `thickness_px` (`px_to_mm = 1`): el nombre sugiere una calibración que el
  proyecto decidió no hacer. `--plot` grafica sólo el grosor.
- `serie_temporal.xlsx` tiene nombre fijo: volver a correr pisa la salida anterior sin versión (las carpetas
  `_v5`/`_superadas` se arman a mano).
- Los valores por defecto están repetidos en `PipelineConfig`, `argparse` y el cuaderno; hoy coinciden, pero nada lo verifica.
- Estado: abierto.

### H33. El veredicto "reportable" cambia con `win_s`, y el control de falsos se contamina con el propio evento
- Severidad: RIESGO. Estado: abierto.
- El protocolo trata `win_s = 2 s` como un parámetro sin importancia, pero Video_491 pasa de "sin meseta" (2 s) a
  "6 eventos, meseta k = 8–12" (3 s y 5 s); Video_063 pasa de 6 a 5 (1 s), Video_583 de 6 a 7 (1 s). En 1.5–3 s, 5 de los 6
  videos no cambian. No hay una prueba de sensibilidad documentada ni una razón para 2 s.
- Mecanismo (Video_491): con `win_s = 2` hay 2 "falsos" a k = 8 justo después de cada ráfaga (13.65 s y 34.6 s, ver H13);
  con 3 s desaparecen, la meseta aparece y salen 6 eventos de 11–16 MAD en dos ráfagas (≈ 12.6–13.4 s y 33.7–34.4 s).
  O sea que el veredicto del control (falsos = 0) depende de la ventana del quita-deriva y no sólo del ruido.
- Lo que NO se puede decir: cuál de los dos resultados es el verdadero para Video_491.
- Prueba sugerida: escaneo de `win_s` en 1–5 s en los seis videos y reportar el veredicto sólo si es estable en 1.5–3 s.

### H34. La grilla de k es gruesa y despareja, y se elige el borde inferior de la meseta
- Severidad: RIESGO (bajo hoy). Estado: abierto.
- Grilla (3, 4, 6, 8, 10, 12, 15, 20): pasos de ×1.33 a ×1.25; "≥ 2 puntos" significa rangos muy distintos: la meseta
  de 6 eventos de Video_063 son 2 puntos (k = 6–8, ×1.33, con grilla fina ×1.6) y la de 5 eventos son 4 puntos (×2.9).
- El código usa el k MÁS BAJO de la meseta: queda pegado al precipicio donde empiezan los falsos (Video_466: k = 4 y
  hay 1 falso en k = 3.75; Video_063: k = 6 y hay falsos hasta k = 4.75). Pequeños cambios (`win_s`, `sep_s`, un
  fotograma) mueven ese borde. Elegir el centro (en escala log) de la meseta sería más estable (no cambia el conteo
  en los seis videos: 28, 6, 6, 5, –, 6).
- `escaneo_estabilidad` tiene `sep_s = 2.0` por defecto (H5) mientras el script usa 0.3. Medido: con `sep_s = 1.0` el conteo de
  Video_prueba ya cae de 28 a 16 (con 2.0 no se midió; la ayuda del propio script cita 23 → 5 en un tren de 1.75 Hz).
- Estado: abierto.

### H35. Detalles menores de `contraction_report.py`
- Severidad: DEUDA.
- El promedio alineado excluye los eventos a menos de 1.5 s de los extremos: en Video_063 el título del gráfico dice
  "promedio de 5 eventos" y la leyenda "6 eventos"; el adelgazamiento se mide sobre 5 de los 6.
- `detrend_median` usa una ventana en MUESTRAS (61) sobre una serie irregular en el tiempo (ver H16).
- Sin meseta, el script usa k = 10 (el punto medio de la grilla) y aun así lista los eventos; la hoja `eventos_<video>` no
  marca que no son reportables (el aviso está sólo en `resumen_*`).
- `contracciones.xlsx` tiene nombre fijo (se pisa) y los nombres de hoja se truncan a 18–20 caracteres: con `--compare`
  dos videos con el mismo prefijo chocarían.
- Estado: abierto.

### H36. En Video_prueba el primer "estimulado" (t = 4.87 s) tiene la amplitud de una espontánea y sesga el período
- Severidad: RIESGO (afecta el número que se reporta como validación). Estado: abierto.
- Amplitud de los 7 estimulados: **2.10 px** (4.87 s) y 6.6–7.0 px (los otros seis). Las 21 espontáneas miden 2.07 px de
  mediana (1.30–2.52). Además es el latido con mayor error respecto de su ranura (−35 ms).
- Con los 7: período 10.00744 ± 0.00408 s (−1.8 σ de 10 s). **Sin el primero: 10.00043 ± 0.00068 s** (error 6 veces
  menor; −0.6 σ). Un evento que cae en un extremo del tren tiene el mayor brazo de palanca.
- Probabilidad de coincidencia casual: con 1.75 Hz de espontáneas y tolerancia ±0.067 s, cada ranura tiene ~23 % de tener
  una espontánea encima. Con 7 ranuras es esperable que alguna caiga así.
- Lo que NO se puede afirmar: que sea espontáneo (el estimulador podría haber arrancado con un latido débil). Pero el
  diseño dice que la amplitud "no se usa para clasificar y sirve de verificación independiente": aquí esa verificación
  da una señal y no hay ningún aviso. Un chequeo automático ("amplitud de un estimulado fuera del rango de los demás") lo
  detectaría.

### H37. El rescate de "dudosos" usa ±1 s y extrapola la grilla fuera del tren
- Severidad: RIESGO (clasificación engañosa). Estado: abierto.
- `rescate_frac = 0.10` → ventana de ±0.10·T = ±1 s para T = 10 s, y se aplica a TODAS las ranuras entre el primer y el
  último evento del registro, también antes del inicio o después del fin del tren detectado.
- Demostración: a los eventos de Video_prueba se les quitó el de 4.87 s; el rescate marca como "estimulado dudoso" un evento
  de 2.09 px a 5.447 s, **0.51 s fuera de su ranura 0** (antes del primer latido real del tren); es una espontánea. Con 1.75 Hz
  de espontáneas siempre habrá una a menos de 1 s de cualquier ranura.
- Se informa aparte como "dudoso", no entra en el período, pero sale de las espontáneas (cambia la frecuencia y la
  cinética de esos grupos) y el texto sugiere "si coincide la amplitud, es un latido del tren", sin aplicarlo.
- Sugerencia: limitar el rescate a ranuras dentro de [inicio, fin] del tren y exigir amplitud compatible con los estimulados.

### H38. La significancia no está calibrada para actividad espontánea agrupada o regular; el p no resuelve más que 0.005
- Severidad: RIESGO (bajo hoy). Estado: abierto.
- El nulo son tiempos uniformes al azar. Con las 21 espontáneas reales de Video_prueba (sin ningún estimulador), `separar`
  declara "hay estimulación" (T = 0.566 s, z = 6.7, p = 0.005). Con series de intervalos barajados de esas mismas
  espontáneas (misma distribución, sin reloj), el **28 %** (11 de 40) sale "estimulado" a alfa = 0.01. El docstring lo
  admite ("una espontánea muy regular da significativa"); la magnitud no estaba medida. En los videos reales gana bien el
  tren de 10 s por la regla "el T más largo con z ≥ 90 % del máximo" (z 12.4 contra 6.7), pero depende de que haya ≥ 4 latidos.
- Con 200 simulaciones el p mínimo es 1/201 = 0.004975 y es exactamente el que se reporta en cuatro de cinco videos: no
  informa cuán fuerte es la evidencia. Con 1 000 simulaciones: 0/1 000 simulaciones superan el z observado en los cinco;
  márgenes chicos en los de 5–6 eventos (z del barrido 14.1–15.7 contra máximo nulo 11.8–12.6).
- Con 4 o 5 eventos no hay Monte Carlo (mínimo 6): `p = NaN` y `hay_estimulacion` queda verdadero automáticamente
  (`significativo = not isfinite(p) or p <= alfa`). Es el caso de Video_466 (5 eventos). Con eventos uniformes al azar, la
  tasa de falsos es baja (0/1 895 con N = 4; 8/1 803 = 0.4 % con N = 5), protegida por la exigencia de captura ≥ 75 %.
- El z observado se recalcula tras el refinado con tolerancia más estrecha, mientras el nulo usa el z del barrido: dos
  estadísticos distintos. No cambia el veredicto hoy (el z del barrido también supera todas las simulaciones).
- Estado: abierto.

### H39. Código muerto y documentación vieja en `rhythm_split.py`
- Severidad: DEUDA.
- `buscar_grilla` tiene un `return mejor` inalcanzable después del `return` real (`mejor` no existe). Los parámetros
  `tol_frac` y `tol_min_s` de `separar` se documentan y no se usan (la tolerancia sale de `tol_s`, o 3 fotogramas);
  `_reasignar` sólo envuelve a `_asignar`; `err_T = nan` se sobreescribe.
- `comparar_con_equipo` está escrita para la base `frames` ("todos los tiempos salen de dividir por el fps declarado") y
  calcula un `fps_corregido`; con la base PTS, `fps_nominal` ya es el fps de los timestamps (30.0) y esa corrección no
  tiene sentido. Hoy no dispara (todas las diferencias < 1.8 σ).
- Estado: abierto.

### H40. El resumen por video mezcla estimuladas y espontáneas, y la cifra de amplitud relativa describe solo a las espontáneas
- Severidad: RIESGO. Estado: abierto.
- En Video_prueba (28 eventos) la amplitud relativa del resumen es 0.71 %. Por grupo: espontáneas (n = 21) A = 2.07 px, 0.70 %;
  estimuladas (n = 7) A = 6.74 px, 2.29 %. O sea, el número del video es el de la población más numerosa, no el de la estimulada,
  que es la de interés mecánico. `cinetica_eventos` ya guarda la columna `grupo` (la inserta `analizar`) pero `resumir` la ignora
  (mejora #9 de `metricas-cinetica-TTP-RT50.md`).
- Propuesta: resumir por grupo y reportar el de las estimuladas por separado; al menos rotular qué población describe la cifra.

### H41. El criterio "reportable" (mediana ≥ 5 fotogramas) ignora el ancho del intervalo y la meseta del pico
- Severidad: RIESGO. Estado: abierto.
- Los intervalos [mín, máx] son anchos respecto del valor: Video_466 TTP 192 ms = 67 % del valor, RT50 190 ms = 119 %;
  Video_583 TTP 91 %, RT50 129 %. Aun "reportable", el RT50 de 466 es 160 [70, 260] ms.
- El RT50 de 466 está justo en el umbral: fotogramas por evento 4, 5, 5, 6, 6, mediana 5. El evento de 4 fotogramas es "no medible"
  pero entra igual en la mediana (las marcas `*_medible` por evento no se usan en `resumir`). Un evento más lento o uno menos
  cambia el veredicto.
- Prueba sintética con meseta (subida 0.25 s, meseta 130 ms, RT50 real 150 ms desde el fin de la meseta; SNR 20 y 43; 480 eventos):
  TTP medido ≈ 289 ms = hasta el CENTRO de la meseta (al inicio 225, al fin 355); RT50 medido 206–211 ms = desde el centro (215),
  +38–41 % sobre el definido desde el fin de la meseta. La cobertura de [mín, máx] sobre el valor verdadero cae a 70–95 % según
  la definición. El ruido casi no importa; la meseta sí.
- Sensibilidad al nivel: TTP con onset de 5 a 30 %: 466 290→258 ms, 583 262→243 ms (baja, ≤ 11 %); RT con caída de 30 a 70 %:
  466 248→107 ms (depende de la definición; a 60 % quedan 5 fotogramas, a 70 % 4).
- Propuesta: decidir la definición (¿desde el inicio, el centro o el fin de la meseta?) y documentarla; considerar tiempo de
  subida 10–90 % o reportar el intervalo; exigir que los eventos medibles sean los que entren en la mediana.

### H42. `win_s` = 1 s sesga los eventos lentos; la "amplitud relativa" es una normalización, no una deformación
- Severidad: PREGUNTA. Estado: abierto.
- Con `win_s` = 1 s (ver H33) Video_466 da TTP 221 ms (−22 %) y amplitud relativa 1.58 % (−26 %); Video_583 pasa a 7 eventos y 1.01 %.
  Con 2–5 s todo es estable (466: TTP 284–294 ms, 2.13–2.18 %; 583: 1.31–1.32 %). Un detrend de mediana corta recorta el pulso lento.
- Amplitud relativa = traslación del centro / grosor en reposo: sirve para comparar videos entre sí, pero no es una
  deformación (strain) del gel; la documentación no lo dice explícitamente.
- El nivel de onset (10 % de A) equivale a 2–4 MAD (Video_466: 2.0, Video_prueba: 2.5), cerca del ruido: el cruce es frágil en
  eventos chicos, aunque el TTP cambia poco en los lentos.

### H43. Las pruebas de `cinetica` solo cubren eventos triangulares ideales
- Severidad: DEUDA. Estado: abierto.
- `test_cinetica.py` usa subida lineal + caída exponencial con A/σ = 50, 20 semillas. No hay meseta en el pico, ni jitter en los
  tiempos, ni grupos mezclados, ni interacción con el detrend; por eso no ven H41 ni H40.
- Un evento sin RT50 (Video_491: 1 de 2) queda fuera del resumen sin aviso.
- Estado: abierto.

### H44. Los dos detectores difieren en algo más que un evento: el tiempo del evento y el ruido que fija el umbral (confirma y amplía H2)
- Severidad: RIESGO. Estado: **resuelto en el cuaderno (2026-09-30)**; `event_detection.py` sigue en `src/` sin decidir.
- Motor `ed` contra reporte con el mismo k: Video_prueba 29 vs 28, Video_466 6 vs 5, Video_491 0 vs 2; los otros tres coinciden (tabla de la Etapa 9).
- **Dos definiciones de "tiempo del evento".** `ed` toma el mínimo de la señal **cruda** en ±1 ancho; el reporte, el pico de la señal sin deriva. En eventos lentos con cima plana
  (Video_466) el primero cae 69 ms (2 fotogramas) antes: 14.243 s contra 14.312 s. Como `ed` alimenta los segmentos del cuaderno, su período sale 9.967 s contra 9.994 s
  del reporte (los 5 latidos).
- **Dos definiciones de ruido.** `ed` mide el MAD de la **profundidad** (base − señal, sin quitar la deriva por mediana): 0.2646 px en Video_466; el reporte mide el MAD de la señal sin deriva: 0.212 px. Con k = 4 el
  umbral queda en 1.058 px contra 0.847 px. El evento de 59.01 s (1.0776 px) supera el umbral de `ed` por 2 %; en el reporte no pasa. Una diferencia de 2 % en un umbral decide si hay un sexto evento.
- El evento de `ed` en 15.28 s (Video_prueba) cae entre los de 14.94 y 15.55 s; el reporte lo pierde por la separación `sep_s` (ver H8).
- Propuesta: decidir cuál es el motor oficial, y hacer que el cuaderno use **sólo** ése; si `ed` se conserva, que use el mismo criterio de ruido y de tiempo.

### H45. El cuaderno usa el fps declarado en las secciones 7, 8, 10 y 11, y eso cambia conteos (confirma H3)
- Severidad: RIESGO. Estado: **resuelto en el cuaderno (2026-09-30)**; `event_detection.py` sigue en `src/` sin decidir.
- El cuaderno toma `fps = meta["fps"]` (el declarado por el archivo, 28.97–29.87) para `detrend_median` y `escaneo_estabilidad`; la sección 11c usa `cr.analizar`, que usa el fps de los PTS (30.000).
- Efecto medido: la separación `sep_s = 0.3 s` son `int(0.3 × fps)` muestras = 9 con 30 fps y 8 con 29.x; la ventana de deriva de 2 s son 61 muestras contra 57–59.
  Con el fps declarado: Video_466 da **6** eventos (en vez de 5) en la meseta del escaneo, y Video_prueba **29** (en vez de 28; el fps declarado de Video_prueba no consta en los documentos: probé 29.70 a modo de ejemplo). Video_063, 268, 583 y 491 no cambian.
- Consecuencia: las secciones 7–11 del cuaderno pueden contar distinto que `contracciones.xlsx`, y la sección 11c avisa: "pueden diferir en uno o dos".
- Propuesta: que el cuaderno calcule `fps` de los PTS (`fps_pts`, que ya calcula en la sección 2) y lo use en todas partes.

### H46. La sección 12 del cuaderno no ejecuta lo que su texto describe, y la 13 no genera `contracciones.xlsx` (amplía H10)
- Severidad: RIESGO. Estado: **resuelto en el cuaderno (2026-09-30)**; `event_detection.py` sigue en `src/` sin decidir.
- El texto de la sección 12 explica el enganche de fase, el Monte Carlo, los latidos dudosos y el contraste contra 0.1 Hz. La celda de código llama a `ed.segment_by_rhythm`, `ed.analyze_segments` y `ed.frequency_profile`. No imprime ni usa
  `a_rep["ritmo"]` (p, z, período de la grilla, estimulados, dudosos, jitter).
- Resultado de esos segmentos sobre Video_prueba: tres "tramos" (19 eventos a 0.57 s, 4 a 0.288 s y 6 a 10.0 s); los **6** de 10 s son 6 de los 7 estimulados del reporte. No es "estimuladas vs espontáneas": `segment_by_rhythm` agrupa por frecuencia local y se fragmenta con la ráfaga.
- La sección 13 dice que los archivos son "exactamente los que producen `main.py` y `contraction_report.py`" y lista `contracciones.xlsx`; en las celdas sólo se escriben `serie_temporal.xlsx` (con una hoja `resumen` más corta que la de `main.py`) y `eventos.xlsx` (eventos del motor `ed`).
  También importa `analyze_contractions` (marcado obsoleto) sólo por `_append_sheet`.
- Sección 10: la "segunda opinión" de `ed` dice "dudoso: subir amp_k" en Video_466, mientras el escaneo del reporte de la misma sección da meseta con 0 falsos; el cuaderno no dice a cuál creer.
- Propuesta: que la sección 12 muestre la salida de `cr.analizar` (ritmo) y los tres gráficos de `10_ritmo_*`; o reescribir el texto para decir qué hacen de verdad las celdas.

### H47. El control de falsos de `ed` se contradice con el del reporte, y un solo NaN anula el motor
- Severidad: RIESGO (el NaN) / PREGUNTA (el control). Estado: abierto.
- Un único NaN en la señal da 0 eventos y ruido NaN en `ed` (igual que H1/H31: `savgol_filter` propaga el NaN y `robust_mad` usa `np.median`).
- `symmetric_false_positive_check` declara "señal por encima del ruido" en Video_prueba con 12 detecciones invertidas sobre 29 (razón 0.41, por debajo del corte arbitrario 0.5), y "dudoso" en Video_466 con k = 4, donde el escaneo del reporte
  tiene 0 falsos. La regla `n_arriba ≥ 0.5·n_abajo` no tiene justificación escrita. La línea base por percentil 90 no es simétrica (ya lo advierte el docstring), así que la razón no es una tasa.

### H48. Promesas del docstring sin respaldo, y escalas absolutas ocultas
- Severidad: DEUDA. Estado: abierto.
- El docstring dice "validado con eventos sintéticos de 0.2, 0.5, 1.0 y 2.0 s: 15/15" y "ningún parámetro fija una escala temporal absoluta". En `tests/` no hay ninguna prueba de `event_detection` (sólo `test_seleccion_k.py` y `test_cinetica.py`): esa validación no se puede reproducir.
- Escalas absolutas que sí existen: suavizado ligero de 0.1 s, ventana de la pasada 1 acotada a 3–30 s, ancho mínimo de 2 fotogramas, ancho por defecto 0.2 s, ventana de base de al menos 1.5 s, separación mínima de picos 0.8·ancho.
  En Video_491 el ancho medido da 2.33 s (ruido, no eventos), y la ventana de la línea base pasa a ~19 s.
- `detect_contractions` conserva `raw_col="thickness_px"` por defecto (H6); `scripts/analyze_contractions.py` (obsoleto) lo usa así, con k = 6 fijo.
- Estado de la regresión: el motor `ed` no tiene línea base de resultados; los números "29", "6/6/6/6" del cuaderno no están fijados por ninguna prueba.

### H49. `signal_check.py` sólo mira la cola negativa: sobre `center_px` no reconoce ninguna contracción real
- Severidad: RIESGO (herramienta de diagnóstico que induce a error). Estado: abierto.
- El veredicto exige skew ≤ −1 y más puntos por debajo de −4 σ que por encima. En `center_px` las contracciones van hacia **arriba** en coordenadas de imagen (hay que dar vuelta el signo; el reporte lo decide con `_signo_evento`), así que el skew sale positivo:
  Video_prueba +6.88, Video_063 +10.12, Video_268 +8.10, Video_466 +4.62, Video_583 +4.87, y el veredicto es "ambiguo: revisar a mano" en los cinco. En cambio Video_491 (conteo no reportable) da skew −1.84 y **"HAY una población de contracciones"**.
- Con `thickness_px` (la columna por defecto): Video_063 da "NO hay población de contracciones" aunque tiene 6 eventos validados, y el docstring usa justo ese caso como contraste ("Video_prueba contrae, Video_063 no"). Ese contraste quedó desactualizado con el hallazgo 1 de `CLAUDE.md`.
- Propuesta: decidir el signo con el mismo criterio del reporte (cola más pesada) y usar `center_px` por defecto; o retirar el script y dejar sólo el escaneo de k con control de falsos.

### H50. El veredicto de `motion_check.py` contradice el hallazgo 1 de `CLAUDE.md`
- Severidad: RIESGO (herramienta de diagnóstico que induce a error). Estado: abierto.
- Con Video_prueba imprime "se mueven sólo los bordes: compatible con cambio de grosor, el observable del pipeline principal es el correcto". Pero el mismo script mide `desp_vert_px` = traslación, con RMS 0.30 px, skew +11 y correlación 0.915 con `center_px`; y `thickness_px` correlaciona −0.43 con esa traslación.
  El razonamiento "se mueven sólo los bordes ⇒ cambio de grosor" no vale: un gel sin textura interior que se traslada mueve sólo sus bordes en |ΔI| igual que uno que se adelgaza.
- El corte de 2 × el fondo es arbitrario y aquí está al borde (interior 1.9 ×, gel con bordes 2.8 ×).
- El eje de tiempo de `07_movimiento.png` es `fotograma / fps declarado` (no PTS): difiere de la base de tiempo del pipeline hasta **0.33 s** en medio del video (se iguala al final porque el fps declarado es el promedio). Además descarta el primer fotograma (2 006 filas de 2 007) y toma el primer fotograma como referencia fija de la correlación.
- Propuesta: que el veredicto use `desp_vert_px` y `desp_axial_px` (que sí distinguen traslación de adelgazamiento) y no el cociente de |ΔI|; y que use los PTS.

### H51. La magnitud de `center_px` no coincide con la de la traslación medida por intensidad (pregunta abierta)
- Severidad: PREGUNTA. Estado: abierto.
- **Lo que se sostiene:** la forma y el momento de los eventos coinciden entre dos métodos que no comparten nada (bordes contra correlación de intensidad de todo el perfil vertical): correlación 0.915 sin deriva en Video_prueba. Es una validación independiente de que `center_px` mide una traslación real.
- **Lo que no cierra:** en los eventos, `desp_vert_px` vale 0.18 × lo que `center_px` (mediana sobre los eventos del reporte; 0.36–0.44 px contra 1.9–2.5 px) y en todo el video la pendiente es 0.42. No sé cuál subestima o sobreestima. Hipótesis sin probar: (a) la correlación sobre el perfil promediado de una franja con bordes borrosos se atenúa cuando el movimiento es de un fotograma;
  (b) el desenfoque por movimiento en el fotograma del pico (ya conocido en el grosor) infla el borde. Todo lo que se reporta en píxeles (`amplitud_px`) depende de cuál de las dos sea la magnitud física.
- Propuesta: una prueba con verdad conocida (desplazar un fotograma real una cantidad subpíxel conocida y medir con los dos métodos) antes de citar amplitudes absolutas en píxeles. La amplitud **relativa** entre eventos del mismo video no se ve afectada por un factor constante.

### H52. Las diferencias entre fotogramas llevan un "peine" periódico de 10 fotogramas que no está en las series de bordes (observación)
- Severidad: — (información útil para la comparación con MuscleMotion). Estado: abierto.
- En `mov_fondo` (franja de fondo, sin gel) de Video_prueba, la distancia más frecuente entre picos de |ΔI| es de **10 fotogramas** (119 de 302 picos) y hay un pico espectral a 5.92 Hz, 27 veces sobre su vecindad, también en los canales del gel. Es compatible con el patrón de compresión del video (no lo verifiqué).
- Las series de bordes no lo tienen: potencia a 5.93 Hz / vecindad = 1.1 (`center_px`) y 0.7 (`thickness_px`) en Video_prueba; 0.9 y 1.0 en Video_583.
- Consecuencia posible: una medida basada en diferencias de intensidad (como las de MuscleMotion) arrastra ese patrón; la de bordes no. Falta comprobar si aparece en los videos de `OK` que analizó MuscleMotion.

### H53. La MAD y la mediana móvil están copiadas nueve y tres veces (cierra H4)
- Severidad: DEUDA. Estado: abierto.
- La expresión `median(|x − median(x)|) · 1.4826` aparece en 9 lugares de 6 archivos (`contraction_report.py`, `event_detection.py`, `robust_fitting.py`, `rhythm_split.py` ×3, `signal_check.py`, `motion_check.py`); la mediana móvil de deriva (`rolling(w, center=True).median()`) en 3 (`contraction_report.py`, `signal_check.py`, `motion_check.py`).
  Todas son iguales hoy y **ninguna ignora NaN**: por eso arreglar H1 exige tocar al menos las tres que consume el reporte, y cualquier copia que se olvide reintroduce el problema. Además `motion_check.py` arma su eje de tiempo con `fotograma / fps declarado` en vez de los PTS (H50).
- Propuesta: un único módulo `src/estadistica.py` con `mad()` y `detrend_median()` tolerantes a NaN, que lo importen todos; el reporte y el cuaderno incluidos.

### H54. `CANAL = "auto"` del cuaderno elegía un canal distinto de `center_px` y eso cambiaba el conteo
- Severidad: RIESGO. Estado: **resuelto en el cuaderno (2026-09-30)**.
- La sección 7 elegía el canal de mayor SNR. En Video_063 gana `y_top_px` (con ese canal, k=8 da **8** eventos; el reporte vigente, sobre `center_px`, da **6**) y en Video_268 gana `y_bottom_px`. Contradice el hallazgo 1 de `CLAUDE.md` y al reporte.
- Un texto del cuaderno decía "sobre Video_063, 44 contra 3"; lo medido es 45.6 contra 9.2 (`center_px` contra `thickness_px`). Se reemplazó por una tabla con los seis videos (SNR `center_px` / `thickness_px`: prueba 82/17, 063 46/9, 268 33/10, 466 21/5, 583 44/10, 491 12/6).
- Arreglo aplicado: `CANAL = "center_px"` por defecto; si el de mayor SNR es otro, la celda lo avisa. `"auto"` sigue disponible pero documentado como no apto para cifras a citar.
- Sigue abierto: el reporte (`contraction_report.py`) no compara canales; que `y_top`/`y_bottom` tengan algo más de SNR que `center_px` en algunos videos no se investigó (¿por qué? ¿menos ruido en un borde?). Ver item 8 de la lista.

---

### H55. Con eventos lentos y `sep_s` = 0.3 s, la cola de bajada cuenta como un segundo evento, y la regla del k más bajo lo convalida
- Archivo: `scripts/contraction_report.py` (`escaneo_estabilidad`, `analizar`: `distance = int(sep_s·fps)`; `elegir_k_meseta`).
- Severidad: RIESGO. Encontrado por el chat de implementación el 2026-10-01, al armar `tests/test_nan.py`.
- Qué pasa: serie sintética con 6 eventos lentos, como los de Video_583 (subida lineal de 0.3 s, bajada exponencial con
  RT50 = 0.2 s, amplitud 1.5 px, ruido blanco de 0.04 px: A/σ ≈ 37, parecido al de 583). Sin ningún NaN, el reporte da
  **9 eventos**: tres "eventos" extra de 0.36–0.48 px (~10 σ) a 0.30–0.37 s de su pico, en la cola de bajada. El escaneo
  da `[12, 11, 9, 9, 7, 6, 6, 6]` con 0 falsos desde k = 4: dos mesetas, 9 eventos en k = 6–8 (2 puntos) y 6 en k = 12–20
  (3 puntos). La regla "gana la de k más bajo" elige **9**. Con `sep_s` = 0.5 s o 0.8 s da 6.
- Por qué importa: es el mismo patrón de H8/H11/H33: `sep_s` es un tiempo absoluto que no se relaciona con la duración
  del evento, y la regla de la meseta de k más bajo, justificada con Video_063 (H11), acá elige la respuesta equivocada.
- Qué afecta hoy: nada comprobado. Video_583 y Video_466 reales dan 6 y 5 (el ruido real parece menos "blanco" en la
  cola; no se midió). Riesgo concreto en videos lentos nuevos (`RARITOS`).
- Evidencia: `serie()` de `tests/test_nan.py` con `pulso(t, t0, 0.3, 0.2)` en lugar de los pulsos rápidos, y
  `analizar(df, "center_px", None, 2.0, sep_s, 1.5)` con `sep_s` = 0.3 / 0.5 / 0.8 → 9 / 6 / 6.
- Propuesta: entra en la Fase 2.2 (regla escrita para `sep_s`, probablemente relativa a la duración medida del evento, y
  revisar la regla de la meseta con este caso como contraejemplo).
- Estado: abierto.

---

## Implementación

### Fase 2.1 — NaN (2026-10-01, chat de implementación)

**Qué se hizo**
- `src/estadistica.py` (nuevo): `mad()`, `detrend_median()` y `buscar_picos()`. La MAD ignora los NaN; la mediana
  móvil ya los ignoraba; `buscar_picos` trata los NaN como −inf (un fotograma sin medida nunca es pico y no le impide
  a su vecino serlo). No se interpola nada.
- Las 9 copias de la MAD y las 3 de la mediana móvil ahora llaman a ese módulo: `contraction_report.py` (re-exporta
  `mad` y `detrend_median`, que usa el cuaderno), `rhythm_split.py` (×3), `robust_fitting.py`, `event_detection.py`,
  `signal_check.py`, `motion_check.py`. Los parámetros no se tocaron (`int(win_s·fps) | 1`, etc.: eso es la Fase 2.2).
- `contraction_report.py`: los cuatro `find_peaks` pasan por `buscar_picos`; el promedio alineado usa `nanmean`.
- `cinetica.py`: si entre el pico y el cruce del 10 % (o del 50 %) hay un fotograma sin medida, la métrica de ese
  evento queda NaN. Antes la búsqueda saltaba el hueco y encontraba un cruce del otro lado.
- Salidas nuevas (al final, no reordenan nada): en `resumen_*`, `fotogramas_sin_medida`, `fotogramas_sin_medida_pct`,
  `fotogramas_low_quality` y `eventos_junto_a_hueco`; en `eventos_*`, la columna `junto_a_hueco` (evento con un NaN en
  el pico o al lado: instante y amplitud inciertos). Avisos impresos.
- `tests/test_nan.py` (nuevo).

**Verificación**
- Equivalencia: `np.nanmedian` = `np.median` bit a bit en 137 vectores sin NaN (incluidas las 24 series de los seis
  vigentes). Las copias de `robust_fitting` y `rhythm_split` reciben vectores ya filtrados, así que `main.py` no cambia.
- Regresión: los seis `contracciones.xlsx` vigentes, **idénticos** hoja por hoja y columna por columna; solo se agregan
  las columnas nuevas.
- NaN inyectados en los seis videos reales (1, 3 y 30 dispersos, 15 seguidos, en un pico, al lado de un pico): **ningún
  caso da 0 eventos**; conteo y k iguales en los 36 casos.
- `tests/test_nan.py`: TODO OK. Con el código viejo falla en 9 de 14 chequeos (reproduce 28 → 0 en Video_prueba).
  `test_seleccion_k.py` 16/16, `test_cinetica.py` OK.

**Lo que dejó a la vista (no se arregló)**
- **H38, evidencia nueva:** en Video_466, un solo NaN en el pico del 3.er evento (pico en meseta: 4.294 y 4.289 px en
  fotogramas vecinos) corre ese pico un fotograma; el jitter de la grilla baja de 35 a 10 ms, la tolerancia de 107 a
  67 ms, y el latido de 44.24 s pasa a "dudoso" (estimulados 5 → 4). La clasificación de estimulados en videos con
  pocos eventos depende de un fotograma.
- Un hueco encima de un evento corre su pico al borde del hueco (Video_466: 24.32 → 24.08 s con 15 NaN). Ahora queda
  marcado `junto_a_hueco`; no se corrige.
- **H47 sigue abierto en `event_detection.py`**: `savgol_filter` propaga el NaN. No se arregló porque su destino es la
  Fase 2.3; hoy nadie lo usa para reportar.
- `frame_quality` sigue sin usarse para excluir fotogramas `LOW_QUALITY`; solo se cuentan (decisión pendiente).
- H55 (arriba).

### Fase 2.3 — un solo detector (2026-10-01, chat de implementación)

**Decisión (de Franco):** borrar el detector viejo si no aporta nada que no esté en otro lado.

- Se evaluó qué se perdía: las figuras 02 (señal con eventos: ya está en `09_contracciones`), 03 (amplitudes: hoja
  `eventos_*` y `10_ritmo` por grupo), 04 (perfil de frecuencia: lo reemplaza el enganche de fase, y con su ventana
  por defecto no veía el ritmo de 10 s) y 06 (tramos: `10_ritmo`). La única útil era la **05 (escaneo de `k`)**, pero
  graficaba el escaneo del detector viejo y sin los falsos de control.
- **Borrados:** `src/event_detection.py`, `scripts/analyze_contractions.py`, y de `src/plotting.py` las seis funciones
  que solo ellos usaban (queda `plot_timeseries`). Nada más los importaba (el cuaderno ya no los usa desde la revisión).
- **Nuevo:** `contraction_report.py` genera `05_estabilidad_umbral_<video>.png` con **su propio** escaneo: eventos y
  falsos contra `k`, la meseta sombreada y el `k` usado (o "solo para auditar" si no hay meseta).
- Documentos actualizados: `CLAUDE.md`, `README.md`, `DOCUMENTACION.md`, `referencia-archivos-y-graficos.md`, glosario y
  dos textos del cuaderno.
- Verificación: los seis `contracciones.xlsx`, idénticos; las tres pruebas pasan.
- **Se cierran por la borrada:** H2, H6, H44 (la parte de `src/`), H47 (el NaN en `ed` y su control de falsos), H48.

---

### Fase 2.2 — qué es un evento (2026-10-01, chat de implementación)

Detalle completo, con la medición previa y los resultados, en `claude/propuesta-fase-2-2.md`.

- **Evento = altura y prominencia ≥ k·ruido, sin separación mínima** (resuelve H8, H55 y H5).
- **Ventana del detrend automática**: `max(2 s, 3 × el evento claro más largo)`, con el conteo repetido
  con 0.75×, 1× y 1.5× la ventana; si cambia, no es reportable (resuelve H33; en parte H42). La versión
  automática salió de una observación de Franco sobre Video_491: sus eventos duran ~1 s y la ventana
  fija de 2 s se los comía.
- **Grilla de k fina (×1.1), meseta de ancho ≥ ×1.25, k en el centro, todas las mesetas listadas**
  (resuelve H34; deja H11 a la vista).
- **Nueva línea base:** Video_prueba 29 (antes 28), Video_491 2 reportables (antes no reportable); los
  otros cuatro, mismos conteos.
- **Pruebas:** `tests/test_deteccion.py` (nuevo, resuelve H9).
- **Hallazgo nuevo, a consultar con el equipo:** Video_491 es distinto de los otros cinco: eventos de
  ~1 s y en sentido contrario (`signo` −1). Compatible con un tétanos fusionado (no confirmado).

---

### Fase 3, grupo 1 — ritmo y cinética (2026-10-07, chat de implementación)

Resuelve H36, H37, H38, H40, H41 y H43 (y H39: el código muerto y el docstring viejo de
`rhythm_split.py`). Propuesta, mediciones y resultados en `claude/propuesta-fase-3-ritmo-cinetica.md`.

- **`src/rhythm_split.py`**: el instante de cada latido es el inicio (lo pasa `contraction_report`);
  `separar(..., frecuencia_configurada_Hz=...)` busca un tren por frecuencia a ±10 % (búsqueda
  dirigida) o uno libre sin frecuencia; tabla `trenes` con veredicto; tolerancia de búsqueda 2
  fotogramas con grilla de períodos fina; puntaje vectorizado (idéntico al anterior); "mejor
  puntaje salvo múltiplo ×2/×3"; Monte Carlo desde 4 eventos, 1000 simulaciones, sobre el z de la
  búsqueda; R5 (tiempo y amplitud, desvío contra el tren sin ese evento) y R6 (dudosos solo dentro del
  tren, con amplitud compatible). Docstring del módulo reescrito (explica las listas al azar).
- **`src/cinetica.py`**: `resumir` usa solo los eventos medibles en la mediana; reportable si lo es al
  menos la mitad.
- **`scripts/contraction_report.py`**: la cinética se calcula antes del ritmo (para tener el inicio);
  resumen por grupo (`_cinetica_grupos`, hoja `cin_grupos_*`) con la cifra principal de los
  estimulados; `--frecuencia-estimulo` acepta varias; hojas `trenes_*`, `sacados_*`, `dudosos_*`;
  figura 10 con un tren por color.
- **`src/io_utils.load_max_projection`**: lee con `np.fromfile` + `cv2.imdecode`, porque `cv2.imread`
  no abre rutas con acentos en Windows ("Análisis"). Lo detectó Franco en el cuaderno.
- **Cuaderno**: se recuperaron los cambios de la Fase 2.2, que se habían perdido al guardar una copia
  vieja, y se agregaron los de la Fase 3 (celdas 4, 5, 21, 27, 28, 29, 31).

### Fase 3, resto — borde y ajuste, magnitud, canal (2026-10-08, chat de implementación)

Resuelve H19, H20, H51 y H54; cierra H27 y H29 sin cambio; mide H26. Mediciones,
decisiones y la lista de lo que puede cambiar con `RARITOS` en
`claude/propuesta-fase-3-resto.md`. Scripts de medición (no son del flujo):
`scripts/medir_borde_ajuste.py`, `medir_magnitud_px.py`, `medir_roi_columnas.py`,
`medir_roi_ancho.py`.

- **Medido (seis videos, cinco variantes por fotograma):** ±25 px rompe Video_466 (H27);
  RANSAC vs mínimos cuadrados: ninguno gana en todos (H29); CLAHE: conteo y amplitud de la
  traslación estables (≤ 4 %), adelgazamiento no (Video_prueba 18 → 9 %, 268 y 466 cambian
  de signo) (H26); el error de borde deja de ser compartido entre columnas a 2–3 px (H19).
- **Decisión:** una sola métrica de contractilidad, la **traslación** (% del grosor en
  reposo, y px al lado). El adelgazamiento queda como diagnóstico.
- **`src/preprocessing.py`:** ancho mínimo = 40 columnas × 3 px = 120 px; columnas usadas
  `min(60, ancho // 3)` (`roi_quality["n_columnas_usadas"]`); el rescate exige contener la
  cintura (`roi_contiene_cintura`). Piso de 40: con 30 columnas Video_063 da eventos falsos.
  Comentario del ancho mínimo reescrito con las mediciones (lo de "una zona corta mide más
  ruidoso" era falso: en 063 la zona plana de 164 px da 30 % menos ruido que la de 1033 px).
- **`src/pipeline.py`, `main.py`:** columnas según la ROI; `--roi-min-columnas`; hoja `resumen`
  con columnas usadas, `ROI contiene cintura`, `outlier_frac medio`; aviso "en el límite" del
  chequeo 2 (H24).
- **H51:** con desplazamiento conocido, los bordes miden bien (1.00 en Video_prueba y 063; 0.92
  con CLAHE en 466, 1.02 sin CLAHE). La correlación de `motion_check` da 0.18–0.43 aun con verdad
  perfecta: suma productos sin normalizar por la superposición. Arreglo en la Fase 4.
- **H54:** los dos bordes se mueven casi lo mismo; uno es mucho más ruidoso (063 inferior 3×,
  268 superior 2×). `contraction_report` registra `ruido_borde_sup_px`, `ruido_borde_inf_px`,
  `cociente_ruido_bordes`. Con la ROI nueva de 063 el cociente baja de 2.8 a 1.1.
- **Cuaderno:** columnas según la ROI (celda 9), parámetros y textos.
- **`tests/test_roi.py`** (nuevo). Las seis pruebas pasan.
- **Regenerado (2026-10-08):** Video_prueba, 268, 583 y 491 **idénticos** a la corrida anterior
  (archivada como `_superadas/<video>_v6`). Video_063: ROI 875–1039 (`gauge_plana`, 54 col.),
  6 eventos, ruido 0.034 → 0.024 px, amplitud 1.51 → 1.59 px, T = 9.99812 ± 0.00304 s.
  Video_466: **ROI automática** 696–846 (50 col.), 5 eventos, ruido 0.212 → 0.182 px,
  T = 10.00184 ± 0.00542 s, `outlier_frac` 10.5 %.

## Qué arreglar primero

Orden de prioridad, del que más puede torcer un número sin aviso al que sólo ordena. Cada ítem cita los hallazgos con la evidencia. **Nada de `src/` ni `scripts/` se cambió todavía**; el cuaderno sí (2026-09-30).

### Hecho (2026-09-30, sólo el cuaderno)
- H44, H45, H46, H54: el cuaderno usa `cr.analizar` (mismo detector que el reporte), el fps de los PTS, muestra el enganche de fase real, genera `contracciones.xlsx` llamando al script, y detecta sobre `center_px`. Verificado sobre Video_063: 6 eventos, k=6 (meseta 6–8, 0 falsos), período 9.99917 ± 0.00304 s, p = 0.005, captura 5/5, `contracciones.xlsx` coincide.
- Falta verificarlo en los otros cinco videos (sólo se corrió Video_063).

### Fase 2. Que un resultado no desaparezca ni cambie en silencio (antes de `RARITOS`)
1. **✅ HECHO 2026-10-01 (ver "Implementación").** **NaN anula todo** (H1, H31, H47, H53). Un fotograma rechazado da 0 eventos y "no hay meseta". Un módulo `src/estadistica.py` con `mad()` y `detrend_median()` tolerantes a NaN que usen las 9 + 3 copias. Ningún video vigente está afectado; los de `RARITOS` podrían. **Prueba de aceptación:** los seis videos vigentes dan exactamente los mismos números; un video con un NaN inyectado ya no da 0 eventos.
2. **✅ HECHO 2026-10-01 (Fase 2.2).** **Parámetros que deciden el conteo** (H8, H34, H33/H42). Conteo de Video_prueba según `sep_s`: 29, 28, 27, 26 con 0.25, 0.3, 0.35, 0.4–0.5 s (hay una ráfaga real con espaciado ≈ 0.3 s); Video_491 es "no reportable" a `win_s` = 2 s y da 6 eventos a 3 y 5 s; la grilla de k es gruesa y se elige el borde inferior de la meseta. Decidir cada valor por una regla escrita, no por el video que lo motivó, y dejar una prueba que fije el resultado.
3. **✅ HECHO 2026-10-01 (borrado; ver "Implementación").** **Destino de `event_detection.py`** (H2, H44, H47, H48). Ya no lo usa el cuaderno; sólo `analyze_contractions.py` (obsoleto). Borrar, o archivar con una nota, y quitar sus promesas de docstring.

### Fase 3. Decisiones metodológicas que hay que validar con datos o con el equipo
4. **✅ HECHO 2026-10-07 (Fase 3, grupo 1; H42 ya en la 2.2).** **Cinética** (H40, H41, H42). Resumir por grupo (la amplitud relativa de Video_prueba es la de las espontáneas: 0.71 % contra 2.29 % de las estimuladas); cambiar "reportable" (≥ 5 fotogramas de mediana) por algo que mire el ancho del intervalo y la meseta del pico; fijar `win_s` por encima de la duración del evento más lento.
5. **✅ HECHO 2026-10-07 (Fase 3, grupo 1).** **Ritmo** (H36, H37, H38). El primer "estimulado" de Video_prueba (t = 4.87 s) tiene la amplitud de una espontánea y mueve el período de 10.00043 a 10.00744 s; el rescate de dudosos usa ±1 s y extrapola la grilla; la significancia no está calibrada para espontáneas agrupadas (28 % de falsos con intervalos barajados).
6. **✅ HECHO 2026-10-08 (Fase 3; ver "Implementación").** **Borde y ajuste** (H26, H27, H29, H19, H20). CLAHE desplaza el borde por cantidades que cambian de fotograma a fotograma; RANSAC agrega ruido en Video_466 por rechazar columnas del extremo de la ROI; el ancho mínimo de 180 px rechazó la cintura real. Probar `--no-clahe` en los seis videos.
7. **✅ HECHO 2026-10-08 (Fase 3).** **Magnitud en píxeles** (H51). `center_px` y la traslación por correlación coinciden en forma (0.915) pero no en valor (0.18× en los eventos). Probar con un desplazamiento subpíxel conocido antes de citar amplitudes absolutas.
8. **✅ HECHO 2026-10-08 (Fase 3).** **Por qué `y_top`/`y_bottom` superan en SNR a `center_px` en 063 y 268** (H54). Decidir si eso cambia el observable o es ruido correlacionado entre bordes.

### Fase 4. Herramientas que inducen a error si se las lee al pie de la letra
9. `signal_check.py` (H49) y `motion_check.py` (H50): sus veredictos contradicen el hallazgo 1. Corregir el signo y el razonamiento, o retirarlos.
10. Documentos y pruebas que no respaldan lo que dicen (H9, H10, H48, H43): línea base de regresión, validación sintética, pruebas de cinética con eventos ideales.

### Deuda menor (sin apuro)
H12, H14, H15, H16, H17, H18, H21–H25, H28, H30, H32, H35, H39, H52 (observación).

### Lo que se sostuvo
- La base de tiempo por PTS: los cinco videos estimulados dan 0.1 Hz dentro de 1.8 errores estándar (Etapa 7).
- Detectar sobre `center_px`: lo respalda ahora una medición independiente por intensidad (correlación 0.915 en Video_prueba, H51) y el peine de |ΔI| no está en las series de bordes (H52).
- Las pruebas del repositorio pasan: `test_seleccion_k.py` 16/16 y `test_cinetica.py` todo OK. Las cifras de eventos, período y cinética de los seis videos se reprodujeron al correr el código (Etapas 6, 7 y 8).
- No se encontró ningún caso en que un hallazgo de `CLAUDE.md` esté revertido por el código.
