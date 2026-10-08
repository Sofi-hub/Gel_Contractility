# Referencia: qué contiene cada archivo y qué significa cada eje

Actualizado 2026-10-08 (incluye la Fase 4 y la consola nueva). Cubre la salida del pipeline (`main.py`,
`scripts/contraction_report.py`, `scripts/motion_check.py`,
`scripts/signal_check.py`) y el cuaderno `Analisis_Contractilidad_v4.ipynb`.

Convención de coordenadas que aplica a todo el documento: **`x` es la columna
de la imagen** (0 a la izquierda, creciente hacia la derecha) y **`y` es la
fila** (0 arriba, creciente **hacia abajo**). Es la convención de imagen, no la
de un gráfico matemático. Por eso "y aumenta" significa "se movió hacia abajo
en la pantalla".

`px_to_mm` vale 1.0 por decisión del proyecto, así que **todo lo que dice "mm"
son píxeles**. Las figuras lo indican con "SIN CALIBRAR" en el título.

Los resultados vigentes están en `data/processed_data/<video>/`, **sin sufijo**;
las corridas anteriores (`_v4` a `_v7`) se borraron de la carpeta el 2026-10-08 y siguen en el historial de git (cualquier commit anterior a esa fecha).

---

## 1. `serie_temporal.xlsx` — la salida principal de `main.py`

### Hoja `diagnostics` — una fila por fotograma

| columna | unidad | qué es |
|---|---|---|
| `frame` | — | índice del fotograma, desde 0 |
| `time_s` | s | instante del fotograma. **Con `--base-tiempo pts` sale del timestamp del contenedor; con `frames` es `frame / fps`** |
| `y_top_px` | px | posición del **borde superior**, mediana del modelo RANSAC evaluado en las 40–60 columnas muestreadas (`n_columnas usadas`). Sube de valor cuando el borde baja en pantalla |
| `y_bottom_px` | px | ídem para el **borde inferior** |
| `thickness_px` | px | `y_bottom_px − y_top_px`. El **grosor** |
| `center_px` | px | `(y_bottom_px + y_top_px) / 2`. La **posición** de la franja. **Es el canal de detección** |
| `thickness_mm` | mm | `thickness_px × px_to_mm` |
| `thickness_mm_smooth` | mm | lo anterior, suavizado con Savitzky-Golay |
| `n_outlier_columns` | — | cuántas de las 2N mediciones (N columnas × 2 bordes) descartó RANSAC |
| `outlier_frac` | 0–1 | `n_outlier_columns / (2N)`. Diagnóstico, sin umbral desde la Fase 4 (H24): no es criterio de aceptación |
| `residual_top_px` | px | MAD de los residuos del ajuste del borde superior en ese fotograma |
| `residual_bottom_px` | px | ídem, borde inferior |
| `frame_quality` | texto | `OK`, `LOW_QUALITY` (outlier_frac ≥ `low_quality_frac`) o `REJECTED` (ningún ajuste posible; las medidas quedan `NaN`) |

**`thickness_px` y `center_px` son complementarios.** El grosor es la resta de
los dos bordes: si ambos se mueven juntos 1 px, no cambia — es **ciego a la
traslación**. El centro es el promedio: si el borde de arriba baja 1 px y el de
abajo sube 1 px, no cambia — es **ciego al cambio de grosor**. Entre los dos
describen todo el movimiento vertical.

**`residual_*` es el control interno del método.** Si esas columnas se mueven
al mismo tiempo que el grosor, lo que se está midiendo es el ajuste, no el gel.
En los vídeos validados el residuo se queda en 0.77–0.87 px y plano. Un residuo
de varios px indica que la ROI está mal (Video_466 llegó a 7.0 px con la ROI
automática rota).

### Hoja `resumen` — dos columnas, `Métrica` y `Valor`

Registra el vídeo de origen, el conteo de fotogramas por categoría de calidad,
los estadísticos globales del grosor, la ROI elegida con su método y su
porcentaje de variación, y **todos los parámetros usados** (`n_columns`,
`half_window`, `min_gradient`, `edge_method`, `fit_method`, `ransac_degree`,
`ransac_residual_threshold`, `use_clahe`, `px_to_mm`) más los residuos medios.
Existe para que cualquier número sea reproducible sin adivinar la configuración.

**Campos agregados en la v4:**

| campo | qué es |
|---|---|
| `base de tiempo` | `pts` o `frames`. **Tiene que decir `pts`** |
| `fps usado` | el fps con el que se construyó el eje, si la base es `frames` |
| `fps declarado por el archivo` | lo que dice el metadato del `.mp4`. Es un **promedio** y baja cuando faltan fotogramas: no es confiable |
| `fps segun PTS` | 1 / mediana de los `dt` entre fotogramas. **Éste sí es el fps real de captura**: da 30.000 en los cinco vídeos, con declarados de 28.97 a 29.87 |
| `duracion segun PTS (s)` | último timestamp menos el primero |
| `huecos en PTS` | cuántos saltos hay en los timestamps |
| `frames faltantes estimados` | cuántos fotogramas se perdieron en esos huecos |
| `frames faltantes (%)` | lo anterior como fracción. **Por encima del 1 % el pipeline avisa** |
| `ROI cumple criterio` | `1` si la variación de grosor en la ROI está por debajo de `roi_max_variacion_pct`. **Chequeo de aceptación 1** |
| `ROI ancho minimo exigido (px)` | `roi_min_columnas × roi_min_column_spacing_px` = 40 × 3 = 120 px (Fase 3; antes 60 × 3). No depende del largo del gel |
| `n_columns (maximo)`, `n_columnas usadas`, `roi_min_columnas` | (Fase 3) se usan `min(60, ancho // 3)` columnas, nunca menos de 40 |
| `ROI contiene cintura` | (Fase 3) `1` si la ROI incluye alguna columna con grosor ≤ cintura × 1.05. Tiene que ser `1` |
| `outlier_frac medio` | promedio de `outlier_frac`. Solo diagnóstico: no es comparable entre ROIs (H24) |
| `error de modelo borde sup/inf (px)`, `error de modelo peor / grosor (%)` | (Fase 4) cuánto se aparta la parábola del borde de forma estable. Diagnóstico sin umbral; validados 0.33–1.01 % |
| `ROI criterio`, `ROI cintura del gel (px)`, `ROI grosor min/max en la zona (px)`, `ROI fraccion del ancho de la imagen`, `ROI columnas con franja seguida`, `ROI columnas de la imagen`, `ROI columnas descartadas por nitidez/grosor/pendiente` | (2026-10-07) el detalle de la zona elegida que antes solo salía en pantalla |

### Hoja `roi_alternativas` (2026-10-07)

Una fila por nivel de la cascada de la ROI (`gauge_plana`, `gauge_cintura`, …):
rango `x`, ancho, variación de grosor y si fue la elegida. Sirve para forzar otra
zona con `--x-start/--x-end` si hiciera falta.

---

## 2. `contracciones.xlsx` — salida de `contraction_report.py`

**`estab_<serie>`** — el escaneo de estabilidad del umbral:

| columna | qué es |
|---|---|
| `k` | umbral en múltiplos del ruido |
| `umbral_px` | `k × MAD` |
| `eventos` | eventos detectados con ese umbral |
| `falsos_control` | eventos que detecta el **mismo** algoritmo sobre la señal **invertida** |

Cómo leerla: una contracción sólo puede ir en un sentido, así que todo lo que
aparece del lado invertido es ruido. Si `eventos` tiene una **meseta** (no
cambia al subir `k`) y `falsos_control` es 0 en esa meseta, los eventos son
reales. Si el conteo cae monótonamente y los falsos acompañan al conteo real,
es ruido. **Desde la v4 el `k` se elige solo dentro de esa meseta.**

**`resumen_<serie>`** — una sola fila:

| campo | qué es |
|---|---|
| `canal`, `fps`, `n_frames`, `duracion_s` | contexto |
| `signo` | `+1` si los eventos son excursiones hacia abajo en pantalla, `−1` si hacia arriba. Se decide mirando qué cola de la distribución es más pesada, no se supone |
| `ruido_canal_px` | MAD del canal de detección tras quitar la deriva |
| `ruido_grosor_px` | MAD del grosor tras quitar la deriva |
| `n_eventos` | conteo final |
| **`k_usado`** | el umbral efectivamente aplicado |
| **`k_automatico`** | `True` si lo eligió la meseta, `False` si se forzó con `--k` |
| **`hay_meseta`** | si el escaneo tiene un tramo de conteo constante con 0 falsos |
| **`meseta_k_rango`** | el rango de `k` de esa meseta, p. ej. `12-20` |
| **`conteo_reportable`** | **`False` = el número de eventos NO se reporta.** Chequeo de aceptación 3 |
| `intervalo_mediano_s` | mediana de los intervalos entre eventos |
| `amplitud_traslacion_px` | mediana de la amplitud de los picos |
| `adelgazamiento_px` / `_sigma` | mínimo del promedio de eventos alineados, y su significancia |
| `adelgazamiento_robusto_px` / `_sigma` | promedio de los 3 fotogramas **posteriores** al pico. Mejor que el mínimo, pero **desde la Fase 3 el adelgazamiento es solo diagnóstico: no se reporta** (depende del preproceso) |
| `cociente_adelg_trasl_pct`, `cociente_robusto_pct` | cuánto del movimiento es adelgazamiento, en %. **Van con signo: positivo adelgaza, negativo engruesa.** Hasta el 2026-09-29 el código tomaba la magnitud y un engrosamiento se leía como adelgazamiento |
| `retardo_adelgazamiento_s` | dónde cae el mínimo de grosor respecto del pico |
| `blur_px` / `blur_sigma` | tamaño del artefacto de motion blur, si lo hay |
| `win_s_usado`, `win_s_automatico` | ventana del detrend y si la eligió la regla (≥ 3 × el evento más largo, mínimo 2 s) |
| `duracion_evento_max_s` | duración del evento claro (≥ 10 MAD) más largo, medida con una ventana de 10 s |
| `ventana_corta` | `True` si se forzó una ventana menor que 3 × esa duración |
| `conteo_por_ventana` | conteo con 0.75×, 1× y 1.5× la ventana, p. ej. `1.5 s: 29 \| 2 s: 29 \| 3 s: 29` |
| `conteo_estable_ventana` | si los tres coinciden. **Si no, el conteo no es reportable** |
| `mesetas` | todas las mesetas del escaneo, p. ej. `6 ev en k=5.3-8.6; 5 ev en k=9.4-24.4` |
| `motivo_no_reportable` | por qué no se reporta: sin meseta, o depende de la ventana |
| `ruido_borde_sup_px`, `ruido_borde_inf_px` | (Fase 3, H54) MAD sin deriva de cada borde por separado |
| `cociente_ruido_bordes` | el mayor de los dos ruidos sobre el menor. Si es grande, un borde ensucia al centro: revisar la ROI y ese borde. Sin umbral todavía |

(`picos_con_sep_menor` ya no existe: con la detección por prominencia no hay separación mínima que funda eventos.)

**`eventos_<serie>`** — `evento`, `tiempo_s`, `amplitud_px`, `junto_a_hueco` (un fotograma sin medida en el pico o al lado) y `junto_al_borde` (a menos de media ventana del inicio o del fin del video: su línea de base es menos precisa) de cada uno.

**Qué es un evento (Fase 2.2):** un pico de la señal sin deriva con **altura** y
**prominencia** ≥ `k × ruido` (la prominencia es cuánto sobresale sobre el valle
que lo separa de un pico más alto). No hay separación mínima en tiempo. La hoja
`estab_*` tiene ahora 23 filas: `k` de 3 a ~24 en pasos de ×1.1.

**`trenes_<serie>`** (Fase 3) — una fila por búsqueda: `busqueda` ("dirigida a
0.1 Hz", o "libre" sin frecuencia configurada), `veredicto` ("enganchado a la
frecuencia configurada", "no hay enganche", "no se configuró ninguna frecuencia"),
`clasificacion`, período y frecuencia con error, `jitter_ms`, `z`, `p_valor`
(mínimo 1/1001), `n_eventos_tren`, `n_ranuras`, `captura_pct`, `n_dudosos`,
`n_sacados_tiempo_amplitud`, `inicio_s`, `fin_s`. Aparece aunque no haya tren: es
el "intento" que se buscó.

**`ritmo_<serie>`** — una fila por grupo (`estimulados`, `estimulados_dudosos`,
`espontaneos`), con `n`, ventana temporal, intervalo mediano e IQR, frecuencia
mediana, `CV_intervalo_pct` y amplitud mediana e IQR.

**`grilla_<serie>`** — la grilla del estimulador ajustada: una fila por ranura
(columna `tren` si hay más de una frecuencia), con `t_esperado_s`, `t_medido_s`
(el **inicio** de cada latido desde la Fase 3), `error_s` y `capturada`. Es donde
se ve si faltó algún latido del tren.

**`sacados_<serie>`** (Fase 3) — latidos que salieron del tren porque se desvían
más de 1 fotograma **y** su amplitud está fuera de 0.5–2× la del tren, con el
desvío y las dos amplitudes. Aparece solo si hay alguno (Video_prueba: 4.817 s).

**`dudosos_<serie>`** — latidos corridos más que la tolerancia, dentro del tren y
con amplitud compatible. Aparece solo si hay alguno.

**`espont_<serie>`** — las espontáneas con su frecuencia instantánea evento a
evento. Aparece sólo si las hay.

**`cinetica_<serie>`** — una fila por evento (desde 2026-09-29, `src/cinetica.py`).
Todo sobre el canal de detección sin deriva, con el reposo en 0 y la amplitud
`A` = la misma `amplitud_px` de `eventos_*`.

| columna | qué es |
|---|---|
| `grupo` | `estimulados`, `estimulados_dudosos` o `espontaneos`, si se separó el ritmo |
| `tren` | número de tren del evento (0 si no pertenece a ninguno) |
| `amplitud_relativa_pct` | `100 × A / grosor_reposo_px`. No depende del aumento |
| `grosor_reposo_px` | mediana móvil (la misma de la deriva) del grosor crudo, en el pico |
| `meseta_pico_frames` | fotogramas a menos de 2×ruido del máximo: si es > 1, el instante del pico es ambiguo |
| `onset_s` | cruce del 10 % de `A` antes del pico, interpolado |
| `ttp_frames`, `ttp_s` | del onset al pico, en fotogramas y en s |
| `ttp_min_s`, `ttp_max_s` | **intervalo** que contiene al TTP verdadero (muestreo + meseta del pico) |
| `ttp_medible` | `ttp_frames ≥ 5` |
| `rt50_*` | ídem para RT50: del pico al cruce del 50 % de `A` en la bajada. **No** es la mitad de la duración de la relajación |
| `offset_s`, `duracion_s` | cruce del 10 % después del pico; duración onset→offset |

Campos nuevos en **`resumen_<serie>`**: `amplitud_relativa_pct` (mediana) y
`amplitud_relativa_iqr_pct`; para `ttp` y `rt50`: `_n_eventos`,
`_frames_mediana`, `_n_medibles`, **`_reportable`**, `_s` (mediana de los eventos
**medibles**, **NaN si no es reportable**), `_iqr_s`, `_cota_inf_s`, `_cota_sup_s`;
más `cinetica_min_frames`, `cinetica_motivo`, `n_eventos_cinetica` y
**`cinetica_grupo_principal`**. Si `ttp_reportable` es `False`, lo único que se
reporta es "TTP < `ttp_cota_sup_s`".

Desde la Fase 3 estas cifras son las del grupo **principal**: los estimulados si
hay tren, todos los eventos si no lo hay. Una métrica es reportable si es medible
(≥ 5 fotogramas) en al menos la mitad de los eventos del grupo.

**`cin_grupos_<serie>`** (Fase 3) — las mismas columnas de cinética del resumen,
una fila por grupo: `todos`, `estimulados` y `espontaneos`. Ejemplo, Video_prueba:
amplitud relativa 0.71 % (todos), 2.31 % (estimulados), 0.70 % (espontáneos).

**`poblac_<serie>`** — aparece sólo si hay dos grupos de amplitud (razón de
medianas ≥ 2). Precede a `ritmo_*` históricamente; la separación buena es la de
enganche de fase, no ésta.

---

## 3. `movimiento.xlsx` — salida de `motion_check.py`

Esta herramienta responde una pregunta distinta: **qué se mueve**, sin usar la
detección de bordes.

**Hoja `movimiento`**, una fila por fotograma:

| columna | unidad | qué es |
|---|---|---|
| `mov_gel` | intensidad | mediana de \|I(t) − I(t−1)\| en la franja del gel **con** sus bordes |
| `mov_interior` | intensidad | ídem, sólo el **interior** del gel, sin bordes |
| `mov_fondo` | intensidad | ídem, en una franja de fondo del mismo tamaño. Es el control |
| `mov_gel_t1/t2/t3` | intensidad | lo mismo por tercios a lo largo del eje del gel |
| `desp_vert_px` | px | desplazamiento vertical de la franja por correlación cruzada subpíxel |
| `desp_axial_px` | px | desplazamiento a lo largo del eje |
| `corr_vert`, `corr_axial` | 0–1 | calidad del enganche de la correlación. Si es baja, el desplazamiento sale `NaN` |

**Dónde se guarda:** en la carpeta de `--serie` (la del video). Sin `--serie` ni
`--output-dir`, en `qc_output/<nombre del video>/`.

**Hoja `veredicto`** (2026-10-07) — la comparación que decide: `pendiente_desp_vert_sobre_center_px`
(tamaño del movimiento por intensidad respecto del de los bordes; 1 = igual),
`correlacion` (misma forma en el tiempo; 1 = idéntica) y el texto del veredicto:
CONFIRMA (correlación ≥ 0.9 y tamaño entre 0.8 y 1.2), coinciden solo en forma, o
NO confirma. Medido: 0.96 / 0.99 / 0.88 / 0.82 en prueba / 063 / 466 / 476.

**Hoja `resumen_canales`** — por canal: `rms_sin_deriva`, `ruido_MAD`, `skew`,
`frac_bajo_-4sigma_pct`, `frec_dominante_Hz`, `pico_sobre_fondo`.

Los canales `mov_*` (|ΔI|) son **informativos**: sirven para comparar con
MuscleMotion, que mide eso mismo, pero no deciden nada. Desde la Fase 4 (H50) el
veredicto sale de `desp_vert_px` contra `center_px` (hoja `veredicto`); la vieja
regla "interior ≈ fondo ⇒ cambio de grosor" era falsa (un gel sin textura que se
traslada también mueve solo sus bordes).

---

## 4. Las figuras, eje por eje

**De dónde sale cada una.** `00_*` y `01_*` salen de `main.py` (el
`00_max_projection.png` como archivo, del cuaderno). `05_*`, `09_*`, `10_*` y
`11_*` salen de `contraction_report.py`. `07_*` sale de `motion_check.py` y
`08_*` de `signal_check.py`. No hay `02`, `03`, `04` ni `06`: eran del detector
viejo, borrado el 2026-10-01.

### `00_max_projection.png`
Imagen. `x` = columna (px), `y` = fila (px). El gris es la intensidad **máxima
que alcanzó cada píxel a lo largo del vídeo**. Todo lo que se movió en algún
momento queda iluminado, y por eso sirve para acotar dónde puede estar el borde
en cualquier instante.

### `00_roi_profile.png` — dos paneles apilados
- **Arriba:** `x` = columna de la imagen (px). `y` = **grosor de la franja en
  esa columna** (px), suavizado. La línea punteada horizontal es la **cintura**
  estimada del gel; la banda verde es la ROI elegida; las marcas rojas al pie
  señalan columnas donde no se pudo seguir la franja. El perfil típico tiene
  forma de reloj de arena: alto en los anclajes, plano en el medio.
- **Abajo:** mismo `x`. `y` = **nitidez del borde**, definida como el
  **mínimo** entre el gradiente vertical máximo del borde superior y el del
  inferior. Mínimo, no máximo: los dos bordes tienen que ser nítidos para que
  la columna sirva.

El título dice qué método de ROI ganó. **Aceptables:** `gauge_plana`,
`gauge_cintura`, `gauge_rescate_plana` o `manual`. Si dice `solo_nitidez`,
`franja_completa` o `fallback_margin`, la ROI está mal.

### `01_serie_temporal.png`
`x` = tiempo (s). `y` = grosor (px). Gris = crudo, rojo = suavizado
Savitzky-Golay. Sin anotaciones: es la vista honesta de la señal antes de que
ningún detector la toque.

### `05_estabilidad_umbral_<video>.png` — una fila por serie
Sale de `contraction_report.py` (desde 2026-10-01) y grafica **el escaneo que
decide el conteo** (hoja `estab_*`). `x` = `k` en escala logarítmica; `y` =
número de picos. Azul = eventos de la señal; rojo = "falsos", el mismo detector
sobre la señal invertida. Franja verde = la meseta elegida (conteo constante
con 0 falsos); vertical punteada = el `k` usado ("solo para auditar" si no hay
meseta). Lo que se busca es una **zona horizontal del azul con el rojo en 0**.
Si el rojo acompaña al azul y no hay franja verde, el título dice NO REPORTABLE.

> Las figuras `02_eventos_detectados`, `03_amplitudes`, `04_perfil_frecuencia` y
> `06_comparacion_tramos` eran del detector viejo (`src/event_detection.py`) y
> se **borraron** con él el 2026-10-01: su contenido está en `09_contracciones`
> (señal y eventos), la hoja `eventos_*` y `10_ritmo` (amplitudes, por grupo) y
> el enganche de fase (período con su error, que reemplaza al perfil de
> frecuencia). La `05` vieja graficaba el escaneo de ese otro detector y no
> mostraba los falsos.

### `07_movimiento.png` — cuatro paneles apilados, `x` = tiempo (s)
1. **Movimiento total:** rojo = gel, gris = fondo de control.
2. **Movimiento por tercio axial:** dice si el movimiento es local o del puente.
3. **Traslación vertical:** `y` = px. Es lo que el grosor **no** ve.
4. **Desplazamiento axial:** `y` = px.

### `08_asimetria.png` — dos paneles por serie
- **Izquierda:** `x` = tiempo (s), `y` = el canal sin deriva (px), con punteadas
  a ±4×MAD.
- **Derecha:** histograma, `y` = número de fotogramas **en escala logarítmica**.
  Una cola larga hacia un solo lado es la firma de contracciones; una
  distribución simétrica es ruido.

### `09_contracciones.png` — dos paneles por serie
- **Izquierda:** `x` = tiempo (s), `y` = canal sin deriva (px), con un triángulo
  rojo por evento. **Si el conteo es NO REPORTABLE**, el título lo dice en rojo
  ("NO REPORTABLE — candidatos para auditar"), los candidatos van como triángulos
  grises huecos y se dibujan también los **falsos de control** (triángulos rojos
  huecos hacia abajo: los picos de la señal invertida). Si los rojos acompañan a
  los grises, es ruido o vibración.
- **Derecha:** el **promedio de eventos alineados**. `x` = tiempo respecto del
  pico (s). Eje `y` izquierdo (azul) = traslación promedio (px); eje `y` derecho
  (rojo) = cambio de grosor promedio (px). **Los dos ejes tienen escalas
  distintas a propósito**: el punto es comparar la forma y el retardo, no la
  magnitud. El pico positivo que a veces aparece justo antes es motion blur.

### `10_ritmo.png` — dos paneles por serie
- **Izquierda:** `x` = tiempo (s), `y` = el canal sin deriva (px). Los eventos
  van coloreados por grupo (rojo estimulados, naranja dudosos, azul
  espontáneos) y las verticales marcan la grilla del estimulador ajustada. Si el
  conteo es NO REPORTABLE: título en rojo, candidatos en gris y falsos de control,
  como en la `09`.
- **Derecha:** el error de cada latido respecto de su ranura, en ms. Si el tren
  está bien enganchado, todos caen por debajo de un fotograma (33 ms).

---

### `11_cinetica.png` — dos paneles por serie
- **Izquierda:** `x` = **fotogramas** respecto del pico (no segundos, para que
  se vea cuántas muestras tiene la subida). `y` = señal / amplitud del evento.
  Gris = cada evento, azul con un punto por fotograma = mediana. Punteadas en
  el 10 % (onset/offset) y el 50 % (RT50). El título da TTP y RT50, o la cota
  si no son medibles; si el conteo es NO REPORTABLE, lo dice en rojo en su lugar.
- **Derecha:** `x` = número de evento, `y` = ms. TTP (azul) y RT50 (rojo) de
  cada evento con su intervalo [min, max]. La franja gris es la zona de menos
  de 5 fotogramas: un evento cuyo intervalo cae ahí no tiene cinética medible.

## 5. Chequeos de aceptación

Están en un solo lugar: `protocolo-analisis-videos.md`, sección "Chequeos de
aceptación por video". En resumen: la zona medida varía ≤ 6 % y contiene la
cintura (`ROI cumple criterio`, `ROI contiene cintura`), y hay meseta con 0 falsos
(`conteo_reportable`). `outlier_frac` y el error de modelo son diagnóstico, sin
umbral. Mirar además `frames faltantes (%)`: con `--base-tiempo pts` no afecta.
