# Documentación del Pipeline de Contractilidad de Geles 3D

Esta guía está escrita para quien diseña el experimento y necesita entender
**qué hace el software y por qué**, sin necesidad de leer código Python.
Donde haga falta, se explica también la lógica interna para que puedas
justificar el método en un paper o defenderlo ante un revisor.

---

## 1. ¿Para qué sirve este pipeline?

El objetivo es medir, de forma automática y reproducible, la
**contractilidad mecánica** de un cultivo celular 3D embebido en un gel.

En estos ensayos, el gel forma un "puente" delgado entre dos anclajes
(pinzas o postes). Cuando las células se contraen, el gel se deforma y
**su grosor (eje Y) disminuye**. El pipeline:

1. Lee el video crudo (`.avi`/`.mp4`) fotograma a fotograma.
2. Mide el grosor del gel, en píxeles (y opcionalmente en milímetros, si
   calibraste tu óptica), en cada fotograma.
3. Convierte esa serie de grosores en una **curva de grosor vs. tiempo**.
4. Detecta automáticamente los eventos de contracción (micro-contracciones
   basales y macro-contracciones) sobre esa curva, con criterios
   estadísticos objetivos — no "a ojo".
5. Genera gráficos y tablas de control de calidad (QC) para que puedas
   auditar visualmente cada paso, en vez de confiar ciegamente en un número.

**Por diseño, no depende de ningún software externo** (no usa ImageJ ni
MUSCLEMOTION): todo el análisis, desde el video crudo hasta los eventos
detectados, ocurre dentro de este código, y cada paso puede visualizarse.
Esto es intencional: permite auditar exactamente qué píxel se consideró
"borde del gel" en cada fotograma, algo que un pipeline de caja negra no
te deja hacer.

---

## 2. ¿Cómo se detectan los bordes del gel? (StdProj y "gauge region")

Esta es la parte más importante para confiar en los resultados: cómo el
software decide, en cada fotograma, "acá empieza el gel" y "acá termina".

### 2.1 Paso previo: el mapa de proyección (`maxProjectStack`)

Antes de mirar fotograma por fotograma, el pipeline necesita saber **en
qué zona de la imagen buscar** el borde superior e inferior del gel (para
no perder tiempo — ni cometer errores — buscando en toda la imagen).

Para esto genera un **`maxProjectStack`**: una única imagen donde, para
cada píxel, se guarda el valor de intensidad **máximo** que ese píxel
alcanzó a lo largo de todo el video. Es el mismo concepto que "Z-Project >
Max Intensity" en ImageJ, pero calculado internamente ([io_utils.py](src/io_utils.py:74),
función `compute_max_projection`), sin exportar nada a otro programa.

La lógica: si el gel se mueve/deforma en algún momento del video, esa zona
de movimiento va a aparecer "iluminada" en el mapa de máxima intensidad,
incluso si en un fotograma puntual el gel está en otra posición. Esto le
da al pipeline un mapa de **dónde puede estar el borde en cualquier
instante**, sin tener que indicártelo manualmente vídeo por vídeo.

### 2.2 Aislar la "gauge region" (la zona útil de medición)

El gel real no es un rectángulo perfecto: tiene forma de **reloj de
arena** — delgado y de grosor uniforme en el centro, y más ancho cerca de
los anclajes (por la geometría de las pinzas).

Medir la deformación cerca de los anclajes sería **experimentalmente
incorrecto**: ahí la deformación está condicionada por la concentración
de tensiones del anclaje, no refleja la contractilidad del material en sí.
La convención estándar en ensayos mecánicos es medir solo en la sección de
grosor uniforme, llamada **"gauge region"** (o "gauge length").

`preprocessing.auto_detect_roi()` ([preprocessing.py](src/preprocessing.py:54)) aísla
automáticamente esta región a partir del `maxProjectStack`:

1. Aplica un umbral automático (método de Otsu) para separar "zona donde
   hubo movimiento del gel" del fondo.
2. Para cada columna vertical de la imagen, mide el grosor de esa franja
   y calcula el gradiente vertical máximo (qué tan nítido es el borde ahí).
3. Se queda **solo** con las columnas donde:
   - el grosor no se aparta más de un 10% (configurable) del grosor
     mediano de la zona central de la imagen, **y**
   - hay un borde realmente nítido (gradiente por encima de un umbral) —
     no es solo halo o desenfoque óptico.
4. De todas las columnas que cumplen ambos criterios, toma el **bloque
   contiguo más largo** (para no quedarse con parches sueltos aislados).

Ese bloque contiguo es la gauge region: el rango de columnas (`x_start` a
`x_end`) donde el pipeline va a medir el grosor en cada fotograma. Todo lo
que quede fuera (los ensanchamientos cerca de los anclajes) queda
excluido del análisis.

> **Por qué importa:** si la ROI incluyera los ensanchamientos, el ajuste
> de la línea de grosor (ver sección 2.3) no podría seguir esa curvatura y
> marcaría como "outlier" un montón de columnas perfectamente medidas — el
> problema no serían burbujas, sino que se estaría midiendo donde no
> corresponde.

### 2.3 Localización del borde con precisión subpíxel

Una vez que sabemos DÓNDE buscar (gracias a la gauge region), en cada
fotograma y en cada columna muestreada (`n_columns`, típicamente 60) el
pipeline localiza el borde superior y el inferior con precisión
**subpíxel** (es decir, con más resolución que un píxel entero), usando
`edge_detection.py`.

Hay dos métodos disponibles:

- **Parabólico** (por defecto, rápido): se calcula el gradiente de
  intensidad a lo largo de la columna (dónde la imagen pasa de oscuro a
  claro, o viceversa) y se ajusta una parábola a los 3 puntos alrededor
  del pico de ese gradiente. El vértice de esa parábola da la posición
  del borde con precisión de fracciones de píxel — mucho más preciso que
  quedarse con el píxel entero del pico.
- **Sigmoide** (más lento, más robusto a ruido): ajusta una curva en
  forma de "S" a todo el perfil de intensidad de la ventana, y el punto
  de inflexión de esa curva es la posición del borde. Útil para validar
  el método parabólico o para videos con transiciones muy ruidosas.

Un parámetro clave es `min_gradient`: si el gradiente máximo detectado en
la ventana de búsqueda es menor a este umbral, el punto se descarta como
"no confiable" (probablemente tapado por una burbuja, desenfoque, o
iluminación pobre) en vez de forzar una medición dudosa.

### 2.4 Robustez frente a burbujas y ruido local

Con ~60 columnas medidas por fotograma, es esperable que algunas pocas
estén afectadas por una burbuja, una mota de suciedad, o un reflejo. En
vez de promediar todas las columnas (lo que "diluiría" el error de esas
pocas columnas malas en el resultado final), `robust_fitting.py` ajusta
un modelo robusto:

- **RANSAC** (por defecto): prueba muchos subconjuntos aleatorios de
  columnas, ajusta una recta (o polinomio de bajo grado) a cada
  subconjunto, y se queda con el modelo que logra que más columnas caigan
  "cerca" de él (los *inliers*). Las columnas que no encajan (los
  *outliers* — probablemente burbujas) quedan completamente excluidas del
  cálculo final de grosor, no promediadas.
- **Mediana + MAD** (alternativa más liviana): descarta columnas cuya
  posición se aparta demasiado de la mediana, usando la desviación
  absoluta mediana (una medida de dispersión que, a diferencia del
  desvío estándar, no se distorsiona por los propios outliers).

El grosor final de ese fotograma es la mediana de las diferencias
(borde inferior − borde superior) evaluadas sobre el modelo ajustado, y
cada fotograma queda etiquetado como `OK`, `LOW_QUALITY` (muchas columnas
descartadas) o `REJECTED` (no se pudo ajustar ningún modelo confiable —
por ejemplo, burbuja gigante tapando todo el gel).

### 2.5 Verificación visual (nunca es una caja negra)

Para cualquier fotograma se puede generar un **overlay visual**
(`scripts/inspect_frame.py`) que dibuja sobre la imagen:

- puntos **verdes**: borde detectado y aceptado (inlier).
- puntos **rojos**: borde detectado pero descartado como outlier (posible
  burbuja).
- cruces **amarillas**: columnas donde no se detectó ningún borde
  confiable.
- línea **cian**: el modelo final ajustado, que es lo que realmente
  determina el grosor reportado.

Esto permite calibrar los parámetros (`min_gradient`, `half_window`,
umbral de RANSAC) mirando literalmente lo que el algoritmo "ve", en vez de
confiar ciegamente en el número final.

---

## 3. ¿Cómo se detectan los eventos de contracción?

Una vez que tenemos la curva de grosor vs. tiempo (una fila por
fotograma), `event_detection.py` decide **cuáles de esas variaciones son
contracciones reales** y cuáles son simplemente ruido de la medición.

Principio de diseño central: **ningún parámetro fija una escala temporal
absoluta**. Todas las ventanas de análisis se calculan a partir del ancho
de evento medido en los propios datos, así que el mismo código funciona
igual de bien con contracciones que duran 0.1 s o 3 s, sin tener que
retocar nada según el experimento.

### 3.1 Filtrado temporal (Savitzky-Golay)

La curva cruda de grosor tiene "jitter" (ruido) fotograma a fotograma,
proveniente de la propia precisión de la medición subpíxel. Para
suavizarla se usa el filtro **Savitzky-Golay** (`scipy.signal.savgol_filter`)
en vez de un promedio móvil simple.

La diferencia importa: un promedio móvil "aplanaría" los picos de
contracción reales (los recortaría), mientras que Savitzky-Golay ajusta un
polinomio local a cada ventana de puntos, lo que reduce el ruido de alta
frecuencia **preservando la forma** de los eventos rápidos. Esto se usa en
dos lugares distintos con distinto propósito:

- un suavizado **liviano** (ventana ~0.1 s), solo para quitar el ruido
  fotograma-a-fotograma sin tocar la forma del evento;
- un suavizado **de comparación**, con una ventana atada a 3× el ancho de
  evento medido, que se usa exclusivamente para el cálculo de "agudeza"
  (ver 3.3).

### 3.2 Línea base ("estado relajado") y umbral de detección

Para saber si el gel se contrajo, primero hay que saber cuál era su
grosor "en reposo" en cada momento (la línea base puede derivar
lentamente por foco, iluminación, etc.). Esto se estima con un
**percentil móvil alto (90%)** de la señal suavizada: en una ventana
centrada en cada punto, se asume que el grosor "relajado" es
aproximadamente el percentil 90 de esa ventana (porque las contracciones
son deflexiones hacia abajo, minoritarias en el tiempo).

El "hundimiento" respecto de esa línea base (`profundidad = base − señal`)
es la señal sobre la que se buscan picos con `scipy.signal.find_peaks`.
Un pico se acepta como candidato solo si su prominencia supera:

```
umbral = amp_k × ruido
```

donde `ruido` se mide con MAD (igual que en la sección 2.4: robusto a que
los propios eventos grandes contaminen la estimación de ruido) y `amp_k`
es un factor de seguridad (por defecto 6). Cuanto más alto `amp_k`, más
exigente es el criterio.

### 3.3 "Agudeza": el criterio para descartar ruido y deriva lenta

Detectar un pico por sobre un umbral de amplitud no alcanza: una deriva
lenta de foco o temperatura también puede superar ese umbral sin ser una
contracción real. Para distinguir un evento **real y transitorio** de una
deriva lenta, se calcula la **agudeza** (`agudeza` en la tabla de
eventos):

```
agudeza = amplitud_cruda / amplitud_tras_suavizado_ancho
```

La idea: si se suaviza la señal con una ventana ancha (3× el ancho de
evento medido), un evento transitorio real pierde casi toda su amplitud
(porque dura poco comparado con la ventana), mientras que una deriva
lenta prácticamente no cambia (porque ya es "ancha" por naturaleza). Por
eso:

- un evento real da una agudeza alta (≈1.5 o más en los casos validados);
- ruido o deriva lenta da una agudeza cercana a 1.0.

Como la ventana de suavizado de comparación se deriva del ancho de evento
medido en los propios datos (no de un valor fijo en segundos), este
criterio es **escala-invariante**: funciona igual para eventos rápidos o
lentos sin tener que ajustar nada a mano. Solo se conservan como eventos
reales los candidatos cuya agudeza supera `sharpness_threshold` (por
defecto 1.30) **y** cuya amplitud supera el umbral de la sección 3.2.

### 3.4 La "prueba de la meseta" (`threshold_stability_scan`)

Elegir `amp_k` (el multiplicador del umbral) "a dedo" sería arbitrario.
Para elegirlo de forma honesta, el pipeline barre varios valores de
`amp_k` (por ejemplo 3, 4, 5, 6, 7, 8, 10, 12) y cuenta cuántos eventos se
detectan en cada caso (`threshold_stability_scan`, graficado en
`05_estabilidad_umbral.png`).

**Cómo interpretar el gráfico:**

- Si el número de eventos detectados se mantiene **estable en una
  meseta** a lo largo de un rango de valores de `amp_k`, esos eventos son
  reales — el resultado no depende de la elección exacta del umbral.
- Si el conteo **decae monótonamente** sin ninguna meseta, lo que se está
  contando en gran parte es ruido, y hay que subir `amp_k` o revisar la
  calidad del video.

Esta verificación se recomienda hacer **siempre** al analizar un video
nuevo, antes de confiar en el número de eventos reportado.

Como control adicional, `symmetric_false_positive_check` corre el mismo
detector sobre la señal **invertida** (hacia arriba en vez de hacia
abajo): como las contracciones reales solo pueden ir hacia abajo,
cualquier detección "hacia arriba" solo puede ser ruido, y sirve como
alarma si su número se acerca al de detecciones reales.

---

## 4. ¿Qué hace cada script?

### `main.py` — Punto de entrada principal

Procesa un video completo y produce la serie temporal de grosor.

```bash
python main.py --video data/raw_videos/mi_video.mp4 --px-to-mm 0.0021 --plot
```

Internamente:
1. Calcula (o carga) el `maxProjectStack`.
2. Detecta la gauge region (sección 2.2).
3. Recorre el video fotograma a fotograma, midiendo el grosor con
   precisión subpíxel y ajuste robusto (secciones 2.3–2.4).
4. Aplica el suavizado Savitzky-Golay temporal final.
5. Guarda la tabla de resultados (`serie_temporal.xlsx`) y,
   opcionalmente, el gráfico `01_serie_temporal.png`.

La calibración **píxeles → milímetros** (`--px-to-mm`) se obtiene
fotografiando una regla o retícula con el mismo objetivo/zoom que usás
para grabar los geles, midiendo cuántos píxeles ocupan N milímetros
conocidos, y calculando `px_to_mm = mm_conocidos / píxeles_medidos`. Si no
se pasa este parámetro, los resultados quedan en píxeles (el pipeline lo
avisa explícitamente para que no se reporten "mm" sin calibrar).

### `scripts/inspect_frame.py` — Calibración y control de calidad

Corre el mismo análisis que `main.py`, pero sobre **un solo fotograma** (o
imagen suelta), y genera el overlay visual descrito en la sección 2.5.
Es la herramienta para ajustar `min_gradient`, `half_window` y el umbral
de RANSAC **antes** de procesar el video entero.

```bash
python scripts/inspect_frame.py --video data/raw_videos/mi_video.mp4 --frame-index 0 --output-dir qc_output
```

También permite inspeccionar en detalle una columna puntual
(`--inspect-column 340`), generando el perfil de intensidad y de
gradiente de esa columna — útil para responder "¿por qué esta columna se
descartó?".

### `scripts/analyze_contractions.py` — Detección de eventos

Toma la tabla de salida de `main.py` (`serie_temporal.xlsx`) y aplica la
lógica de la sección 3: detecta contracciones, las agrupa por ritmo
(`segment_by_rhythm`, útil si el video tiene tramos con distinta
frecuencia de estimulación), analiza frecuencia/regularidad por segmento,
y corre la prueba de la meseta.

```bash
python scripts/analyze_contractions.py --input data/processed_data/mi_video/serie_temporal.xlsx
```

Produce `eventos.xlsx` (con hojas `eventos`, `resumen`, `por_segmento`,
`perfil_frecuencia`, `estabilidad_umbral`) y los gráficos
`02_eventos_detectados.png` a `06_comparacion_tramos.png`.

**Siempre revisar `05_estabilidad_umbral.png`** (sección 3.4) antes de
reportar el número de eventos de un video nuevo.

### Módulos internos de soporte (`src/`)

Estos no se ejecutan directamente, pero son la base matemática de los
scripts de arriba:

| Módulo | Rol |
|---|---|
| [io_utils.py](src/io_utils.py) | Lectura de video frame a frame (sin cargar todo en memoria) y cálculo del `maxProjectStack`. |
| [preprocessing.py](src/preprocessing.py) | Normalización de contraste (CLAHE), reducción de ruido, y detección automática de la gauge region. |
| [edge_detection.py](src/edge_detection.py) | Localización subpíxel del borde (métodos parabólico y sigmoide). |
| [robust_fitting.py](src/robust_fitting.py) | Ajuste robusto (RANSAC / mediana-MAD) resistente a burbujas. |
| [pipeline.py](src/pipeline.py) | Orquestador: une todo lo anterior para convertir un video en la serie temporal de grosor. |
| [event_detection.py](src/event_detection.py) | Detección escala-invariante de contracciones (sección 3). |
| [qc_visualization.py](src/qc_visualization.py) | Generación de overlays y tablas de diagnóstico visual. |
| [plotting.py](src/plotting.py) | Generación de todos los gráficos PNG finales. |
| [output_paths.py](src/output_paths.py) | Define dónde se guarda cada resultado (sección 5). |

---

## 5. Estructura de carpetas

```
gel_contractility/
├── data/
│   ├── raw_videos/                     <- Videos crudos de entrada (.avi, .mp4)
│   │   └── Video_prueba.mp4
│   │
│   └── processed_data/                 <- Toda la salida generada por el pipeline
│       └── <nombre_del_video>/         <- Una carpeta por video analizado
│           ├── serie_temporal.xlsx     <- Grosor por fotograma (salida de main.py)
│           ├── 01_serie_temporal.png   <- Curva de grosor vs. tiempo
│           ├── eventos.xlsx            <- Contracciones detectadas (salida de analyze_contractions.py)
│           ├── 02_eventos_detectados.png
│           ├── 03_amplitudes.png
│           ├── 04_perfil_frecuencia.png
│           ├── 05_estabilidad_umbral.png
│           └── 06_comparacion_tramos.png
│
├── scripts/
│   ├── inspect_frame.py                <- Calibración / QC visual sobre un frame
│   └── analyze_contractions.py         <- Detección de eventos
│
├── src/                                 <- Módulos internos (ver tabla arriba)
│
└── main.py                              <- Punto de entrada: video -> serie temporal
```

**Regla de nombrado:** la carpeta de salida se deduce automáticamente del
nombre del archivo de video (sin extensión). Por ejemplo,
`data/raw_videos/Video_prueba.mp4` genera sus resultados en
`data/processed_data/Video_prueba/`. Esto permite tener muchos videos
analizados en paralelo sin que sus resultados se mezclen ni se
sobrescriban entre sí.

---

## Flujo de trabajo recomendado (resumen)

1. Colocar el video en `data/raw_videos/`.
2. Correr `scripts/inspect_frame.py` sobre uno o dos fotogramas
   representativos y revisar `overlay.png`: ¿la gauge region tiene
   sentido? ¿hay demasiados puntos rojos/amarillos? Ajustar
   `--min-gradient` / `--half-window` si hace falta.
3. Correr `main.py --video ... --px-to-mm ... --plot` para procesar el
   video completo.
4. Correr `scripts/analyze_contractions.py --input .../serie_temporal.xlsx`.
5. Revisar `05_estabilidad_umbral.png` **antes** de reportar el número de
   eventos: si hay meseta, la detección es confiable.

---

## 6. Comandos para procesar un video nuevo (paso a paso)

Todos los comandos se corren desde la raíz del proyecto
(`gel_contractility/`), donde está `main.py`. Reemplazá `mi_video.mp4` por
el nombre real de tu archivo (ya colocado en `data/raw_videos/`) y
`0.0021` por tu factor de calibración píxeles→mm (ver sección 4, o dejalo
en 1.0 si todavía no calibraste).

### Paso 0 — Colocar el video

Copiá el archivo crudo a `data/raw_videos/`:

```
data/raw_videos/mi_video.mp4
```

### Paso 1 — Calibrar parámetros sobre un fotograma (recomendado)

Antes de procesar el video entero, revisá cómo se detectan los bordes en
un fotograma de prueba (por ejemplo, el primero):

```bash
python scripts/inspect_frame.py --video data/raw_videos/mi_video.mp4 --frame-index 0 --output-dir data/processed_data/mi_video/qc
```

Abrí `data/processed_data/mi_video/qc/overlay.png` y revisá:
- ¿la zona verde (inliers) cubre bien el gel?
- ¿hay muchos puntos rojos o cruces amarillas donde no debería haberlos?

Si hace falta ajustar, repetí el comando agregando parámetros, por ejemplo:

```bash
python scripts/inspect_frame.py --video data/raw_videos/mi_video.mp4 --frame-index 0 --output-dir data/processed_data/mi_video/qc --min-gradient 3.0 --half-window 20
```

Para entender por qué una columna puntual se descarta (por ejemplo, la
columna x=340):

```bash
python scripts/inspect_frame.py --video data/raw_videos/mi_video.mp4 --frame-index 0 --output-dir data/processed_data/mi_video/qc --inspect-column 340
```

### Paso 2 — Procesar el video completo (grosor vs. tiempo)

```bash
python main.py --video data/raw_videos/mi_video.mp4 --px-to-mm 0.0021 --plot
```

Si todavía no calibraste la óptica, podés omitir `--px-to-mm` (queda en
píxeles) y agregarlo más adelante — no hace falta reprocesar el video para
recalibrar, alcanza con volver a correr este mismo comando con el valor
correcto.

Esto genera:
```
data/processed_data/mi_video/serie_temporal.xlsx
data/processed_data/mi_video/01_serie_temporal.png   (por --plot)
```

Si preferís usar un `min_gradient` distinto al default (ajustado en el
Paso 1), pasalo también acá con `--n-columns`, `--fit-method`,
`--edge-method`, etc. (ver `python main.py --help` para la lista completa).

### Paso 3 — Detectar contracciones

```bash
python scripts/analyze_contractions.py --input data/processed_data/mi_video/serie_temporal.xlsx
```

Esto genera, en la misma carpeta:
```
eventos.xlsx
02_eventos_detectados.png
03_amplitudes.png
04_perfil_frecuencia.png
05_estabilidad_umbral.png
06_comparacion_tramos.png
```

### Paso 4 — Verificar antes de reportar resultados

Abrí `data/processed_data/mi_video/05_estabilidad_umbral.png`: si el
número de eventos forma una **meseta** a lo largo de varios valores de
`k`, la detección es confiable (sección 3.4). Si no, subí el umbral con
`--amp-k` y volvé a correr el Paso 3, por ejemplo:

```bash
python scripts/analyze_contractions.py --input data/processed_data/mi_video/serie_temporal.xlsx --amp-k 8
```

### Resumen de los tres comandos (caso típico, sin ajustes finos)

```bash
python scripts/inspect_frame.py --video data/raw_videos/mi_video.mp4 --frame-index 0 --output-dir data/processed_data/mi_video/qc
python main.py --video data/raw_videos/mi_video.mp4 --px-to-mm 0.0021 --plot
python scripts/analyze_contractions.py --input data/processed_data/mi_video/serie_temporal.xlsx
```
