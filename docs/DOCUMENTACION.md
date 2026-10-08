# Documentación del Pipeline de Contractilidad de Geles 3D

Actualizada 2026-10-08 (pipeline v4 hasta la Fase 4, consola nueva y ventana).

Esta guía está escrita para quien diseña el experimento y necesita entender
**qué hace el software y por qué**, sin leer código Python. Para el detalle de
cada columna y cada eje de las salidas, ver `referencia-archivos-y-graficos.md`;
para los chequeos de aceptación, `protocolo-analisis-videos.md`; para correrlo y
entender lo que imprime, `guia-salida-consola.md`.

---

## 1. ¿Para qué sirve?

Mide, de forma automática, reproducible y **verificable**, la contractilidad
mecánica de un cultivo celular 3D embebido en un gel, a partir del video de
microscopía.

El gel forma un puente entre dos anclajes. Cuando las células se contraen, el
gel se deforma. El pipeline:

1. Lee el video crudo (`.mp4`/`.avi`) fotograma a fotograma.
2. Encuentra solo la zona útil del gel (*gauge region*).
3. Localiza en cada fotograma los dos bordes del gel con precisión subpíxel.
4. Construye cuatro series temporales: posición de cada borde, grosor y
   posición del centro.
5. Detecta las contracciones, con una verificación estadística de que no son
   ruido.
6. Separa las contracciones estimuladas de las espontáneas.
7. Mide la amplitud (traslación de la franja, la **única** métrica de contractilidad
   que se reporta) y la cinética (TTP, RT50) de las contracciones, diciendo cuándo una métrica **no** se puede medir.
8. Deja figuras de control para auditar cada paso.

**Sin software externo.** No usa ImageJ ni MuscleMotion: todo ocurre dentro
del código y cada paso tiene una figura de diagnóstico. Además mide
**geometría de borde**, no intensidad, que es lo que lo distingue de
MuscleMotion (ver `comparacion-musclemotion.md`).

**Sin calibración a milímetros, por decisión del proyecto.** Los videos no se
graban todos al mismo aumento, así que un único factor px → mm no tendría
sentido. Todo se reporta en **píxeles**, y las comparaciones entre videos se
hacen con magnitudes relativas (porcentaje del grosor, cocientes) o entre
videos del mismo aumento.

---

## 2. De la imagen a la serie temporal

### 2.1 El mapa de máxima intensidad

Una imagen donde cada píxel guarda la intensidad **máxima** que alcanzó
durante el video (como *Z-Project > Max Intensity* de ImageJ, pero calculado
internamente). Todo lo que se movió en algún momento queda iluminado, así que
marca dónde puede estar el borde del gel en cualquier instante.

### 2.2 La zona útil (*gauge region*)

El gel tiene forma de reloj de arena: angosto y de grosor uniforme en el
centro, ancho cerca de los anclajes. Cerca de un anclaje la deformación la
manda la concentración de tensiones del anclaje y no la contractilidad, así
que ahí no se mide.

El programa sigue la franja del gel columna a columna, estima la **cintura**
(el grosor típico del tramo central) y busca el tramo más largo que cumple,
de más a menos exigente:

| nivel | criterio |
|---|---|
| `gauge_plana` | bordes nítidos + grosor cerca de la cintura + perfil plano |
| `gauge_cintura` | bordes nítidos + grosor cerca de la cintura |
| `gauge_relajada` | bordes nítidos + tolerancia de grosor al doble |
| `solo_nitidez` | solo bordes nítidos |
| `franja_completa` | todo lo que se pudo seguir |
| `gauge_rescate_plana` | si nada de lo anterior es plano: la ventana más ancha con variación de grosor ≤ 6 % |

**Criterio de aceptación:** la variación de grosor dentro de la zona elegida
tiene que ser **< 6 %**. La salida lo deja escrito (`ROI cumple criterio`), y
con `--exigir-roi` el programa se detiene en vez de seguir con una zona mala.
Si sale `solo_nitidez`, `franja_completa` o no cumple, se fuerza la zona a mano
con `--x-start/--x-end` mirando `00_roi_profile_<video>.png`.

El ancho mínimo de la zona sale de cuántas columnas se muestrean y de cuán
juntas pueden estar, no del largo del gel (una regla anterior que dependía del
largo se había fijado mirando un solo video y fallaba en los demás). Desde la
Fase 3, con mediciones: las columnas van separadas al menos **3 px** (más cerca
comparten ruido) y son como mínimo **40** (con menos, un video ya daba eventos
falsos). La zona tiene que medir al menos 120 px; se usan hasta 60 columnas, menos
si la zona es angosta. Así ningún video validado necesita zona forzada a mano.
Si la cascada no encuentra nada plano, el **rescate** busca la ventana plana más
ancha **que contenga la cintura** (si no, podía elegir un anclaje ancho y plano).

### 2.3 El borde, con precisión subpíxel

En ~60 columnas de la zona útil, y en cada fotograma, se calcula el gradiente
de intensidad (dónde la imagen pasa de oscuro a claro) y se ajusta una
parábola alrededor de su máximo: el vértice da la posición del borde con
resolución de fracciones de píxel. Antes se normaliza el contraste con
**CLAHE**, que mejora la relación señal/ruido en la mayoría de los videos. La
amplitud de la traslación cambia ≤ 4 % con o sin CLAHE (probado en los seis), pero
el grosor sí depende de él: por eso el adelgazamiento no se reporta (3.5). Si el gradiente es demasiado débil
(`min_gradient`), la columna se descarta en vez de forzar una medición dudosa.

### 2.4 Robustez frente a burbujas

Con 60 columnas es esperable que alguna esté tapada por una burbuja.
**RANSAC** ajusta un polinomio de **grado 2** a subconjuntos al azar de las
columnas, se queda con el que reúne más columnas coherentes (*inliers*) y
**excluye** del todo a las demás. Dos detalles importan:

- **Grado 2, no una recta**: el borde real tiene curvatura, y con una recta esa
  curvatura se clasificaba como error.
- **Umbral adaptativo**: una columna es *outlier* si se aparta más de 3 veces
  la dispersión típica **de ese fotograma**, no un número fijo de píxeles.

**El porcentaje de columnas descartadas es un diagnóstico, no un criterio.**
Como el umbral se adapta a cada fotograma, una zona con bordes muy limpios
descarta *más*, y el porcentaje no sirve para comparar zonas (Fase 4). Se guarda
en la hoja `resumen` junto con el **error de modelo** (cuánto se aparta la parábola
del borde real de forma estable; 0.3–1 % del grosor en los videos validados). La
zona se acepta por su forma (2.2). Si los descartes son **dispersos**, son
burbujas y se toleran; si son **contiguos**, el modelo no sigue la forma del borde.

Cada fotograma queda como `OK`, `LOW_QUALITY` (muchas columnas descartadas) o
`REJECTED` (no se pudo medir: queda vacío, no se inventa).

### 2.5 Cuatro series temporales

| serie | qué es | ciega a |
|---|---|---|
| `y_top_px` | posición del borde superior | — |
| `y_bottom_px` | posición del borde inferior | — |
| `thickness_px` | inferior − superior: el **grosor** | la traslación (si los dos bordes bajan 1 px, no cambia) |
| `center_px` | promedio de los dos: la **posición** de la franja | el cambio de grosor |

`y` crece **hacia abajo** (convención de imagen).

### 2.6 El eje de tiempo

Sale de los **timestamps que trae el archivo de video** (`--base-tiempo pts`,
el default), no de `fotograma / fps`. El fps que declara un `.mp4` es un
promedio y baja cuando la grabación pierde fotogramas; con ese eje los eventos
parecen más juntos de lo que fueron. Un video del proyecto perdió el 4.7 % de
sus fotogramas y su período de estimulación medía 9.51 s en vez de 10.01 s.
El fps real de captura es 30.000. Detalle en `base-de-tiempo-y-frames-perdidos.md`.

---

## 3. De la serie temporal a las contracciones

### 3.1 Qué señal se usa para detectar: `center_px`

La intuición dice que una contracción es un **adelgazamiento**. En este montaje,
en cambio, la contracción es mayormente un **desplazamiento vertical de toda
la franja**. El grosor, al ser la resta de los dos bordes, no ve ese
desplazamiento. Medido en el video más débil: relación señal/ruido por
fotograma de 44 en `center_px` contra 3 en el grosor. Por eso se detecta sobre
`center_px`, y el grosor se mide aparte (3.5).

### 3.2 Quitar la deriva y encontrar los picos

La deriva lenta (foco, temperatura) se quita restando una **mediana móvil**.
La ventana no es fija: mide al menos **3 veces la contracción más larga** del
video, y nunca menos de 2 s. Si fuera más corta, la mediana "bajaría con la
contracción" y al restarla se la comería (pasaba en Video_491, cuyas
contracciones duran ~1 s). No se usa un filtro pasabanda: convertiría cada
contracción en un valle flanqueado por dos picos falsos. El sentido de los
eventos no se supone: se deduce de qué lado de la distribución tiene la cola
larga.

Un **evento** es un pico que cumple dos condiciones: sube al menos `k × ruido`
sobre el reposo (**altura**) y sobresale al menos `k × ruido` sobre el valle que
lo separa de su vecino más alto (**prominencia**). La segunda condición es la
que decide si dos picos cercanos son dos contracciones (la señal baja entre
ellos) o una sola con ruido encima. No se usa una separación mínima en tiempo:
fundía contracciones reales de una ráfaga y contaba la cola de una contracción
lenta como otra.

### 3.3 Cómo se elige el umbral `k`, y por qué el conteo es confiable

Se barre `k` de 3 a ~24 (23 valores, pasos de ×1.1) y se cuenta cuántos
eventos se detectan con cada uno.
Como control, se corre **el mismo detector sobre la señal invertida**: una
contracción solo va en un sentido, así que todo lo que aparezca del otro lado
es ruido.

- Si el conteo forma una **meseta** (no cambia al subir `k`) con **0 falsos**
  del lado invertido, los eventos son reales y el número no depende del umbral.
- El `k` se elige **automáticamente**, en el centro de esa meseta. Si hay
  varias, gana la de `k` más bajo (al subir el umbral se pierden eventos
  reales), y el reporte las lista todas.
- **El conteo tiene que ser el mismo con tres ventanas de deriva distintas**
  (0.75×, 1× y 1.5× la elegida). Si cambia, no se reporta: un número que
  depende de una elección arbitraria no es un resultado.
- **Si no hay meseta, el conteo no se reporta**: la salida lo marca
  `[NO REPORTABLE]`. No se baja `k` para "encontrar" eventos.

### 3.4 Estimuladas y espontáneas

El estimulador dispara en instantes `t = fase + n·T`; las contracciones
espontáneas no saben nada de ese reloj. El programa busca la grilla `(T,
fase)` que mejor explica un subconjunto de los eventos, y todo lo que queda
fuera es espontáneo. El instante de cada contracción es su **inicio**, no su
pico (el pico de un evento lento lo decide el ruido).

**Dónde se busca.** Si se le dice a qué frecuencia estaba el estimulador, busca
solo cerca de ella (±10 %) y responde "enganchado a 0.1 Hz" o "no hay
enganche": el estimulador no capturó. Si no se le dice, busca en todos los
ritmos y lo aclara en el veredicto.

**El p-valor.** El buscador siempre encuentra algún tren, así que en cada
corrida se sortean 1000 listas de instantes al azar (tantos como eventos), se
les corre la misma búsqueda y se mira qué fracción arma un tren tan bueno como
el del video. Se exige menos de 1 en 100. Buscar solo cerca de la frecuencia
configurada le da al azar menos intentos, y por eso detecta mejor.

**La amplitud no se usa para clasificar**, así que si los dos grupos resultan
de distinta amplitud, eso es evidencia independiente. Solo interviene junto
con un desvío de tiempo: un latido que se corre más de un fotograma **y** tiene
la amplitud de una espontánea sale del tren. Se reporta la frecuencia del tren
con su error y se la compara con la configurada. Las espontáneas no tienen
frecuencia constante: se reportan mediana, rango intercuartil y frecuencia
instantánea. Detalle en `separacion-estimuladas-espontaneas.md`.

### 3.5 Adelgazamiento (diagnóstico, no se reporta)

**Desde la Fase 3 el adelgazamiento no se reporta.** La métrica de contractilidad
es una sola: la **traslación** de la franja, en % del grosor en reposo (y en px al
lado). El adelgazamiento depende de cómo se procesa la imagen: con y sin CLAHE,
Video_prueba da 18 % contra 9 %, y en dos videos cambia de signo. Se sigue
calculando para entender el movimiento.

El grosor es la variable biomecánicamente interesante, pero por fotograma
queda por debajo del ruido. Se mide **alineando todos los eventos en su pico
y promediándolos**: el ruido baja como √N. Se usa la medida **robusta**
(promedio de los 3 fotogramas posteriores al pico), porque en el fotograma de
máxima velocidad el borde se emborrona y el grosor da un salto positivo falso
(motion blur). El cociente adelgazamiento/traslación **va con signo** y
**depende del video**: 18 % y 13 % en los dos de referencia, 1–2 % y no
significativo en otros dos.

### 3.6 Cinética y amplitud relativa

Por cada contracción (`src/cinetica.py`):

- **TTP**: del inicio (cruce del 10 % de la amplitud) al pico.
- **RT50**: del pico hasta caer al 50 % de la amplitud.
- **Amplitud relativa**: amplitud / grosor en reposo, en %. No depende del
  aumento, así que sí se puede comparar entre videos.

**Límite de fondo:** la cámara toma una imagen cada 33 ms. En las muestras
rápidas la subida entera ocupa 1–2 fotogramas, y ahí no hay TTP que medir:
lo único que se puede afirmar es una **cota** (TTP < 100 ms). El programa da
el valor solo si la subida ocupa al menos 5 fotogramas, y siempre informa el
intervalo que contiene al valor verdadero. Para medir la cinética de verdad
hacen falta 200–300 fps. Detalle en `metricas-cinetica-TTP-RT50.md`.

---

## 4. Los scripts

| script | qué hace |
|---|---|
| `main.py` | video → `serie_temporal_<video>.xlsx` (las cuatro series + hoja `resumen` con todos los parámetros), `00_roi_profile_<video>.png`, y con `--plot` `01_serie_temporal_<video>.png`. El mapa de máxima intensidad lo calcula internamente; `00_max_projection.png` como archivo lo guarda el cuaderno |
| `scripts/contraction_report.py` | **el análisis principal**: serie temporal → `contracciones_<video>.xlsx` y las figuras `05_estabilidad_umbral`, `09_contracciones`, `10_ritmo` y `11_cinetica`. Es el **único** detector de eventos del proyecto: el viejo (`event_detection.py` y `analyze_contractions.py`) se borró el 2026-10-01 |
| `scripts/inspect_frame.py` | revisa un solo fotograma: overlay de inliers/outliers y perfil de una columna. Para calibrar parámetros o entender por qué se descartó una columna |
| `scripts/motion_check.py` | segunda opinión, sin usar los bordes: mide el desplazamiento de la franja por intensidad y lo compara con `center_px` (CONFIRMA / no confirma) |
| `scripts/signal_check.py` | diagnóstico: ¿hay una población de eventos por encima del ruido en una serie? |
| `interfaz.py` (`Analizar.bat`) | la ventana: elegir video y carpeta, marcar los pasos y ver la salida en vivo. Corre los mismos scripts, no calcula nada propio |
| `Analisis_Contractilidad_v4.ipynb` | recorre el flujo entero paso a paso, mostrando la salida de cada etapa |

---

## 5. Carpetas

```
Gel_Contractility/
├── main.py
├── src/                    módulos (ver CLAUDE.md para la lista)
├── scripts/                los scripts de la tabla de arriba
├── tests/                  pruebas: python tests/test_<nombre>.py (seis archivos)
├── docs/                   esta documentación
└── data/
    ├── raw_videos/
    └── processed_data/
        ├── <video>/        RESULTADOS VIGENTES, uno por video
        └── _superadas/     corridas anteriores, archivadas (no usar)
```

---

## 6. Procesar un video nuevo

Doble clic en `Analizar.bat`, o los comandos de `guia-salida-consola.md`
(sección 1). Antes de informar un número, los chequeos de
`protocolo-analisis-videos.md`:

1. `ROI cumple criterio` = 1 (variación de grosor ≤ 6 %) y `ROI contiene cintura` = 1.
2. `conteo_reportable` = True (meseta con 0 falsos de control).
3. Para la cinética, `ttp_reportable` / `rt50_reportable`; si son `False`, solo la cota.

Si el resultado es NO REPORTABLE, mirar el video: picos hacia los dos lados son
vibración; movimiento sin pausas es actividad continua del tejido, que este
método de conteo no mide.
