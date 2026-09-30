# Documentación del Pipeline de Contractilidad de Geles 3D

Actualizada 2026-09-30 (pipeline v4 + cinética). Reemplaza a la versión de
2026-09-05, que describía la detección sobre el grosor, la calibración a mm y
`analyze_contractions.py` como flujo principal: las tres cosas cambiaron.

Esta guía está escrita para quien diseña el experimento y necesita entender
**qué hace el software y por qué**, sin leer código Python. Para el detalle de
cada columna y cada eje de las salidas, ver `referencia-archivos-y-graficos.md`;
para los comandos y los chequeos de aceptación, `protocolo-analisis-videos.md`.

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
7. Mide la amplitud, el adelgazamiento y la cinética (TTP, RT50) de las
   contracciones, diciendo cuándo una métrica **no** se puede medir.
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
con `--x-start/--x-end` mirando `00_roi_profile.png`.

El ancho mínimo de la zona sale de cuántas columnas se muestrean (60 columnas ×
3 px), no del largo del gel: una regla anterior que dependía del largo se había
fijado mirando un solo video y fallaba en los demás.

### 2.3 El borde, con precisión subpíxel

En ~60 columnas de la zona útil, y en cada fotograma, se calcula el gradiente
de intensidad (dónde la imagen pasa de oscuro a claro) y se ajusta una
parábola alrededor de su máximo: el vértice da la posición del borde con
resolución de fracciones de píxel. Antes se normaliza el contraste con
**CLAHE**, que mejora la relación señal/ruido 1.5× sin deformar la señal
(probado con y sin CLAHE sobre Video_063). Si el gradiente es demasiado débil
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

**Criterio de aceptación:** en promedio se descarta **< 10 %** de las columnas.
Si los descartes son **dispersos**, son burbujas y se toleran; si son
**contiguos**, el modelo no sigue la forma del borde y hay que achicar o mover
la zona.

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

La deriva lenta (foco, temperatura) se quita restando una **mediana móvil** de
2 s. No se usa un filtro pasabanda: convertiría cada contracción en un valle
flanqueado por dos picos falsos. El sentido de los eventos (hacia arriba o
hacia abajo en la imagen) no se supone: se deduce de qué lado de la
distribución tiene la cola larga. Luego se buscan los picos que superan
`k × ruido`.

### 3.3 Cómo se elige el umbral `k`, y por qué el conteo es confiable

Se barre `k` de 3 a 20 y se cuenta cuántos eventos se detectan con cada uno.
Como control, se corre **el mismo detector sobre la señal invertida**: una
contracción solo va en un sentido, así que todo lo que aparezca del otro lado
es ruido.

- Si el conteo forma una **meseta** (no cambia al subir `k`) con **0 falsos**
  del lado invertido, los eventos son reales y el número no depende del umbral.
- El `k` se elige **automáticamente** dentro de esa meseta. Si hay varias,
  gana la de `k` más bajo (al subir el umbral se pierden eventos reales).
- **Si no hay meseta, el conteo no se reporta**: la salida lo marca
  `[NO REPORTABLE]`. No se baja `k` para "encontrar" eventos.

### 3.4 Estimuladas y espontáneas

El estimulador dispara en instantes `t = fase + n·T`; las contracciones
espontáneas no saben nada de ese reloj. El programa busca la grilla `(T,
fase)` que mejor explica un subconjunto de los eventos, con un p-valor por
simulación, y todo lo que queda fuera es espontáneo. **La amplitud no se usa
para clasificar**, así que si los dos grupos resultan de distinta amplitud,
eso es evidencia independiente. Se reporta la frecuencia del tren con su
error y se la compara con la configurada. Las espontáneas no tienen
frecuencia constante: se reportan mediana, rango intercuartil y frecuencia
instantánea. Detalle en `separacion-estimuladas-espontaneas.md`.

### 3.5 Adelgazamiento

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
| `main.py` | video → `serie_temporal.xlsx` (las cuatro series + hoja `resumen` con todos los parámetros), `00_roi_profile_<video>.png`, y con `--plot` `01_serie_temporal.png`. El mapa de máxima intensidad lo calcula internamente; `00_max_projection.png` como archivo lo guarda el cuaderno |
| `scripts/contraction_report.py` | **el análisis principal**: serie temporal → `contracciones.xlsx` y las figuras `09_contracciones`, `10_ritmo` y `11_cinetica` |
| `scripts/inspect_frame.py` | revisa un solo fotograma: overlay de inliers/outliers y perfil de una columna. Para calibrar parámetros o entender por qué se descartó una columna |
| `scripts/motion_check.py` | diagnóstico independiente de los bordes: **qué** se mueve (bordes, textura interior o nada) |
| `scripts/signal_check.py` | diagnóstico: ¿hay una población de eventos por encima del ruido en una serie? |
| `scripts/analyze_contractions.py` | **obsoleto**: detecta sobre el grosor con `k` fijo. Solo se conserva porque genera las figuras 02–06 y el cuaderno usa una función suya |
| `Analisis_Contractilidad_v4.ipynb` | recorre el flujo entero paso a paso, mostrando la salida de cada etapa |

---

## 5. Carpetas

```
Gel_Contractility/
├── main.py
├── src/                    módulos (ver CLAUDE.md para la lista)
├── scripts/                los scripts de la tabla de arriba
├── tests/                  pruebas: python tests/test_seleccion_k.py, python tests/test_cinetica.py
├── docs/                   esta documentación
└── data/
    ├── raw_videos/
    └── processed_data/
        ├── <video>/        RESULTADOS VIGENTES, uno por video
        └── _superadas/     corridas anteriores, archivadas (no usar)
```

---

## 6. Procesar un video nuevo

```bash
# 1. serie temporal
python main.py --video "data/raw_videos/mi_video.mp4" \
               --output-dir data/processed_data/mi_video --base-tiempo pts

# 2. contracciones, ritmo y cinética
python scripts/contraction_report.py \
       --input data/processed_data/mi_video/serie_temporal.xlsx \
       --frecuencia-estimulo 0.1
```

Antes de reportar un número, los tres chequeos de aceptación
(`protocolo-analisis-videos.md`):

1. `ROI cumple criterio` = 1 (variación de grosor < 6 %).
2. `outlier_frac` medio < 10 %.
3. `conteo_reportable` = True (meseta con 0 falsos).

Y además: `frames faltantes (%)` en la hoja `resumen`, y para la cinética,
`ttp_reportable` / `rt50_reportable`.

Si algo huele raro:

```bash
python scripts/inspect_frame.py --video "data/raw_videos/mi_video.mp4" --frame-index 0 \
       --output-dir data/processed_data/mi_video/qc
python scripts/motion_check.py --video "data/raw_videos/mi_video.mp4" \
       --output-dir data/processed_data/mi_video
```
