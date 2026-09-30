# Referencia: qué contiene cada archivo y qué significa cada eje

Actualizado 2026-09-30 (v4). Cubre la salida del pipeline (`main.py`,
`scripts/contraction_report.py`, `scripts/motion_check.py`,
`scripts/signal_check.py`) y el cuaderno `Analisis_Contractilidad_v4.ipynb`.

Convención de coordenadas que aplica a todo el documento: **`x` es la columna
de la imagen** (0 a la izquierda, creciente hacia la derecha) y **`y` es la
fila** (0 arriba, creciente **hacia abajo**). Es la convención de imagen, no la
de un gráfico matemático. Por eso "y aumenta" significa "se movió hacia abajo
en la pantalla".

`px_to_mm` vale 1.0 por decisión del proyecto, así que **todo lo que dice "mm"
son píxeles**. Las figuras lo indican con "SIN CALIBRAR" en el título.

Los resultados vigentes están en `data/processed_data/<video>_v6/`.

---

## 1. `serie_temporal.xlsx` — la salida principal de `main.py`

### Hoja `diagnostics` — una fila por fotograma

| columna | unidad | qué es |
|---|---|---|
| `frame` | — | índice del fotograma, desde 0 |
| `time_s` | s | instante del fotograma. **Con `--base-tiempo pts` sale del timestamp del contenedor; con `frames` es `frame / fps`** |
| `y_top_px` | px | posición del **borde superior**, mediana del modelo RANSAC evaluado en las ~60 columnas muestreadas. Sube de valor cuando el borde baja en pantalla |
| `y_bottom_px` | px | ídem para el **borde inferior** |
| `thickness_px` | px | `y_bottom_px − y_top_px`. El **grosor** |
| `center_px` | px | `(y_bottom_px + y_top_px) / 2`. La **posición** de la franja. **Es el canal de detección** |
| `thickness_mm` | mm | `thickness_px × px_to_mm` |
| `thickness_mm_smooth` | mm | lo anterior, suavizado con Savitzky-Golay |
| `n_outlier_columns` | — | cuántas de las 2N mediciones (N columnas × 2 bordes) descartó RANSAC |
| `outlier_frac` | 0–1 | `n_outlier_columns / (2N)`. **Chequeo de aceptación 2: sano < 0.10** |
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
| `ROI ancho minimo exigido (px)` | `n_columns × roi_min_column_spacing_px`. Ya **no** depende del largo del gel |

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
| `adelgazamiento_robusto_px` / `_sigma` | promedio de los 3 fotogramas **posteriores** al pico. **Ésta es la que hay que usar** |
| `cociente_adelg_trasl_pct`, `cociente_robusto_pct` | cuánto del movimiento es adelgazamiento, en %. **Van con signo: positivo adelgaza, negativo engruesa.** Hasta el 2026-09-29 el código tomaba la magnitud y un engrosamiento se leía como adelgazamiento |
| `retardo_adelgazamiento_s` | dónde cae el mínimo de grosor respecto del pico |
| `blur_px` / `blur_sigma` | tamaño del artefacto de motion blur, si lo hay |
| `picos_con_sep_menor` | aparece sólo si `--sep-s` está fusionando eventos |

**`eventos_<serie>`** — `evento`, `tiempo_s`, `amplitud_px` de cada uno.

**`ritmo_<serie>`** — una fila por grupo (`estimulados`, `estimulados_dudosos`,
`espontaneos`), con `n`, ventana temporal, intervalo mediano e IQR, frecuencia
mediana, `CV_intervalo_pct` y amplitud mediana e IQR.

**`grilla_<serie>`** — la grilla del estimulador ajustada: una fila por ranura,
con `t_esperado_s`, `t_medido_s`, `error_s` y `capturada`. Es donde se ve si
faltó algún latido del tren.

**`espont_<serie>`** — las espontáneas con su frecuencia instantánea evento a
evento. Aparece sólo si las hay.

**`cinetica_<serie>`** — una fila por evento (desde 2026-09-29, `src/cinetica.py`).
Todo sobre el canal de detección sin deriva, con el reposo en 0 y la amplitud
`A` = la misma `amplitud_px` de `eventos_*`.

| columna | qué es |
|---|---|
| `grupo` | `estimulados`, `estimulados_dudosos` o `espontaneos`, si se separó el ritmo |
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
`_frames_mediana`, **`_reportable`**, `_s` (mediana, **NaN si no es
reportable**), `_iqr_s`, `_cota_inf_s`, `_cota_sup_s`; más `cinetica_min_frames`
y `cinetica_motivo`. Si `ttp_reportable` es `False`, lo único que se reporta
es "TTP < `ttp_cota_sup_s`".

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

**Hoja `resumen_canales`** — por canal: `rms_sin_deriva`, `ruido_MAD`, `skew`,
`frac_bajo_-4sigma_pct`, `frec_dominante_Hz`, `pico_sobre_fondo`.

Cómo se interpreta: se compara la **modulación** (RMS tras quitar la deriva) de
cada canal contra la del fondo, **no** su nivel absoluto. Tres desenlaces:

- gel ≈ fondo → no hay movimiento por encima del ruido
- gel ≫ fondo pero interior ≈ fondo → **se mueven sólo los bordes**, compatible
  con cambio de grosor
- gel ≫ fondo **e** interior ≫ fondo → **se mueve la textura entera**:
  traslación o movimiento axial, al que `thickness_px` es ciego

---

## 4. Las figuras, eje por eje

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

### `02_eventos_detectados.png`
`x` = tiempo (s). `y` = el canal de detección (px). Gris = señal cruda, rojo =
suavizado ligero, azul punteado = estado relajado (percentil 90 móvil). Los
triángulos marcan cada contracción, coloreados por segmento de ritmo.

### `03_amplitudes.png` — dos paneles lado a lado
- **Izquierda:** `x` = tiempo (s), `y` = amplitud del evento (px). Cada evento
  es una línea vertical desde 0. La punteada horizontal es el umbral.
- **Derecha:** histograma horizontal de las mismas amplitudes. Dos modas
  separadas significan dos tipos de evento.

### `04_perfil_frecuencia.png`
`x` = tiempo (s). `y` = **período dominante en segundos, en escala
logarítmica**. Log porque los períodos de interés abarcan dos órdenes de
magnitud. Se calcula por autocorrelación en ventana móvil, sin usar la lista de
eventos, así que es un control independiente. **Limitación:** no resuelve
períodos mayores a la mitad de la ventana. Con `window_s = 8` no ve el ritmo de
10 s; hay que subirlo a 20.

### `05_estabilidad_umbral.png`
`x` = `k`, `y` = número de eventos. Lo que se busca es una **zona horizontal**.
Un decaimiento monótono sin meseta significa que se está contando ruido. La
vertical roja marca el `k` que se usó.

### `06_comparacion_tramos.png`
Un panel por tramo de ritmo, con `x` = tiempo (s) acotado a su tramo e `y` = el
canal de detección (px).

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
  por evento.
- **Derecha:** el **promedio de eventos alineados**. `x` = tiempo respecto del
  pico (s). Eje `y` izquierdo (azul) = traslación promedio (px); eje `y` derecho
  (rojo) = cambio de grosor promedio (px). **Los dos ejes tienen escalas
  distintas a propósito**: el punto es comparar la forma y el retardo, no la
  magnitud. El pico positivo que a veces aparece justo antes es motion blur.

### `10_ritmo.png` — dos paneles por serie
- **Izquierda:** `x` = tiempo (s), `y` = el canal sin deriva (px). Los eventos
  van coloreados por grupo (rojo estimulados, naranja dudosos, azul
  espontáneos) y las verticales marcan la grilla del estimulador ajustada.
- **Derecha:** el error de cada latido respecto de su ranura, en ms. Si el tren
  está bien enganchado, todos caen por debajo de un fotograma (33 ms).

---

### `11_cinetica.png` — dos paneles por serie
- **Izquierda:** `x` = **fotogramas** respecto del pico (no segundos, para que
  se vea cuántas muestras tiene la subida). `y` = señal / amplitud del evento.
  Gris = cada evento, azul con un punto por fotograma = mediana. Punteadas en
  el 10 % (onset/offset) y el 50 % (RT50). El título da TTP y RT50, o la cota
  si no son medibles.
- **Derecha:** `x` = número de evento, `y` = ms. TTP (azul) y RT50 (rojo) de
  cada evento con su intervalo [min, max]. La franja gris es la zona de menos
  de 5 fotogramas: un evento cuyo intervalo cae ahí no tiene cinética medible.

## 5. Los tres chequeos de aceptación

Ninguno es opcional. Están en `claude/protocolo-analisis-videos.md`.

1. **Variación del grosor dentro de la ROI < 6 %.** Campo `ROI cumple criterio`
   de la hoja `resumen`. Más que eso significa que la ROI incluye el hombro de
   un anclaje, donde la deformación la manda el anclaje y no la contractilidad.
2. **`outlier_frac` medio < 10 %.** Unos pocos por ciento es normal con
   burbujas. Si sube, mirar si los outliers son **contiguos** (el modelo no
   sigue la geometría: achicar o mover la ROI) o **dispersos** (burbujas: se
   toleran).
3. **Meseta del escaneo de umbral con 0 falsos.** Campo `conteo_reportable`.
   Sin meseta, el conteo de eventos no se reporta.

Y uno más, que no es de aceptación pero hay que mirarlo: **`frames faltantes
(%)`**. Por encima del 1 %, el eje `fotograma/fps` está comprimido y hay que
usar `--base-tiempo pts`.
