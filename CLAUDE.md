# Proyecto: Análisis de Contractilidad de Geles 3D

## Objetivo Principal
Automatizar el análisis de la contractilidad mecánica de cultivos celulares 3D
embebidos en geles: medir la deformación del gel a lo largo del tiempo de forma
automatizada, reproducible y **verificable**, a partir de video de microscopía.

## Arquitectura del Pipeline (v4)

1. **Mapeo espacial (auto-ROI).** Se genera un `maxProjectStack` internamente,
   sin software externo. Sobre él, `preprocessing.auto_detect_roi` sigue la
   franja del gel columna a columna desde el centro hacia afuera, estima la
   *cintura* usando sólo columnas cuyo grosor es compatible con el gel, y elige
   por planitud la *gauge region*. Reporta los niveles que descartó y un
   veredicto explícito contra el criterio de aceptación
   (`cumple_criterio_aceptacion`).
2. **Detección subpíxel.** Gradiente de intensidad por columna y ajuste
   parabólico al máximo. Si el gradiente no supera `min_gradient`, la columna se
   descarta en vez de forzar una medición dudosa.
3. **Ajuste robusto.** RANSAC sobre ~60 columnas con **polinomio de grado 2** y
   **umbral de residuo adaptativo** (3×MAD del propio fotograma).
4. **Cuatro series temporales, no una.** `y_top_px`, `y_bottom_px`,
   `thickness_px` (la resta) y `center_px` (el promedio).
5. **Eje temporal desde los timestamps del contenedor**, no `fotograma / fps`.
6. **Detección de eventos** sobre `center_px`, con elección automática del
   umbral dentro de la meseta y control de falsos positivos.
7. **Separación de estimuladas y espontáneas** por enganche de fase
   (`src/rhythm_split.py`).

## Los cinco hallazgos que definen el método — NO revertirlos

**1. Detectar sobre `center_px`, no sobre `thickness_px`.**
La contracción en este montaje es mayormente un **desplazamiento vertical de
toda la franja**, y `thickness_px`, al ser la resta de los dos bordes, es
**ciego a la traslación** por construcción. Medido: SNR por fotograma de 44 en
`center_px` contra 3 en `thickness_px` para el video débil. Con `thickness_px`
el escaneo daba 7 eventos con 11 falsos a k=3 y 0 eventos a k≥6.

El grosor **sigue midiéndose**, porque es la variable biomecánicamente
interesante, pero promediando eventos alineados en el tiempo, no evento a
evento.

> **CORRECCIÓN (2026-09-30).** La versión anterior de este documento decía que
> "sólo el 13–19 % de ese movimiento es cambio de grosor" y que el cociente era
> el mismo en todos los videos. Medido sobre seis: **depende del video**. 18 %
> en Video_prueba y 13 % en Video_063, pero 1–2 % y **no significativo**
> (1.0–1.1 σ) en Video_268 y Video_583. El argumento se sostiene —de hecho se
> refuerza—, pero el número no es una constante del montaje.

**2. Estimuladas vs espontáneas: por enganche de fase, no por amplitud ni por
ventana temporal.** El estimulador dispara en `t = fase + n·T`; las espontáneas
no saben nada de ese reloj. La amplitud **no** se usa para clasificar, y por eso
sirve como verificación independiente. Las espontáneas no mantienen frecuencia
constante (CV medido del 91 %): se reporta mediana, rango intercuartil y
frecuencia instantánea, nunca un solo número.

**3. El eje temporal sale de los timestamps del contenedor, no de
`fotograma / fps`.** *(Reemplaza al viejo hallazgo "el fps declarado está mal",
que era correcto pero incompleto.)*

El `fps` que declara un `.mp4` es el **promedio** `(n−1)/duración`, y baja
cuando la grabación pierde fotogramas: entonces el eje se come los huecos y los
eventos aparecen más juntos de lo que fueron. Video_466 perdió el 4.73 % de sus
fotogramas y su período medía 9.508 s (+5.15 % de error contra los 0.1 Hz
configurados); con los timestamps mide 10.006 s.

El fps real de captura es **30.000**: el `dt` mediano de los timestamps da
33.333 ms en los cinco videos medidos, con fps declarados que van de 28.97 a
29.87. Con la base de tiempo por PTS, los cinco videos estimulados dan una
frecuencia **indistinguible de los 0.1 Hz configurados**.

**Correr siempre con `--base-tiempo pts`.** Detalle en
`claude/base-de-tiempo-y-frames-perdidos.md`.

**4. El umbral `k` se elige dentro de la meseta, y ya es automático.**
`--k auto` es el default. Dos reglas que no son obvias:
- Cuando hay varias mesetas, gana la de **`k` más bajo**: al subir el umbral se
  pierden eventos reales. "La meseta más larga" da la respuesta equivocada (en
  Video_063 daría 5 eventos donde la validada es 6).
- Los falsos se filtran **antes** de buscar el tramo de conteo constante, no
  después (en Video_466 la meseta real es k=8..15 pero el tramo de 5 eventos
  empieza en k=6, donde todavía hay 1 falso).

Si no hay meseta, el conteo **no se reporta**: se marca `[NO REPORTABLE]` y
`conteo_reportable = False`. Hay regresión: `python tests/test_seleccion_k.py`.

**5. A 30 fps la cinética de contracción (TTP, RT50) no es medible en las
muestras rápidas.** En tres de los cinco videos la contracción entera dura 2
fotogramas y la subida 1. Ahí sólo se puede afirmar una cota (`TTP < 100 ms`:
tres intervalos de muestreo, porque el pico verdadero puede estar un fotograma
después del muestreado; la versión anterior decía 67 ms y era demasiado
optimista), no un valor. Implementado en `src/cinetica.py`: el reporte da el
valor sólo si la subida (o la bajada al 50 %) abarca ≥ 5 fotogramas, y si no,
sólo la cota. Para medirlo hacen falta 200–300 fps. Ver
`claude/metricas-cinetica-TTP-RT50.md`.

## Fuera de alcance por decisión del proyecto

**No se calibra píxeles a milímetros.** Los videos no se graban todos al mismo
aumento, así que un factor único no tendría sentido. `px_to_mm` queda en 1.0 y
**todo se reporta en píxeles**. Las comparaciones entre videos se hacen en
términos relativos (porcentaje del grosor, cocientes) o dentro de un mismo
aumento. No proponer calibrarlo salvo que el usuario lo pida.

## Contexto: para quién es y qué es la carpeta `OK`

El trabajo es para que **la Universidad de Tecnun** mida contracciones en sus células. El equipo usa MuscleMotion y a veces
tiene errores; este proyecto busca un método propio, más robusto y verificable. La carpeta
`data/raw_videos/OK-20260904T142817Z-1-001/OK/` (la misma donde están los videos crudos) tiene **los videos que cumplen los
requerimientos de Tecnun** (no hay un criterio técnico escrito), cada uno con una subcarpeta `<video>_-Contr-Results` con la salida
de MuscleMotion: `contraction.txt` (contracción), `speed-of-contraction.txt` (velocidad de contracción), `Overview-results.txt`,
`Log_file.txt` y tres `.jpg`. **"OK" no significa que MuscleMotion haya medido bien** (ver `docs/comparacion-musclemotion.md`).
Hay otra carpeta hermana, `RARITOS-…/RARITOS/`, con los videos que MuscleMotion maneja mal y todavía no se procesaron.
Detalle en `docs/contexto-tecnun-y-musclemotion.md`.

## Stack Tecnológico

`opencv-python` (video e imagen), `numpy`, `scipy` (señal y picos),
`scikit-learn` (RANSAC), `matplotlib` (QC), `pandas` y `openpyxl` (salidas).

## Reglas Estrictas para el Código

* **Cero dependencia externa.** El pipeline lee un `.avi` o `.mp4` crudo y hace
  todo internamente. **Bajo ninguna circunstancia sugerir MUSCLEMOTION o
  ImageJ** como parte del flujo. Superar a MuscleMotion en robustez es un
  objetivo explícito: por eso se mide **geometría de borde**, no intensidad.
  (Sí se leen sus salidas cuando existen, para comparar: ver
  `claude/comparacion-musclemotion.md`.)
* **Cero cajas negras.** Todo análisis debe poder generar un output visual de
  diagnóstico para validar los parámetros.
* **Manejo de outliers.** Los problemas de iluminación o burbujas se resuelven
  estadísticamente por columnas, no "adivinando" datos faltantes.
* **Verificar antes de reportar.** El código original estaba sobreajustado a un
  único video y eso causó varios problemas serios. Ningún número se reporta sin:
  - **Meseta del escaneo de umbral** con 0 falsos de control.
  - **Control simétrico de falsos positivos** sobre la señal invertida.
  - **Regresión sobre Video_prueba y Video_063** cada vez que se toca un
    algoritmo. Los dos tienen que dar exactamente los mismos números que antes.
  - **Nunca** ajustar un parámetro hasta que el resultado dé lindo.
* **Ningún parámetro atado al tamaño del sujeto.** El `min_roi_width_frac = 0.35`
  (35 % de las columnas con gel) es el ejemplo de qué no hacer: se fijó mirando
  un video y rompía en todos los demás. El ancho mínimo ahora sale de cuántas
  columnas se muestrean.
* **No suavizar con pasabanda.** Para quitar la deriva se usa mediana móvil. Un
  pasabanda convierte cada evento real en un valle flanqueado por dos picos
  falsos y destruye la asimetría, que es justamente lo que se mide.
* **`--sep-s` y parámetros de proximidad.** `find_peaks(distance=...)` no filtra
  ruido: se queda con el pico **más alto** de cada ventana y borra el resto. Un
  valor grande borra eventos reales de un tren rápido.

## Estructura y comandos

    src/preprocessing.py     CLAHE + auto-ROI (gauge region) + rescate por barrido
    src/edge_detection.py    borde subpíxel por columna
    src/robust_fitting.py    RANSAC grado 2, umbral adaptativo
    src/io_utils.py          lectura de video + timestamps (read_pts_seconds)
    src/pipeline.py          orquestador -> 4 series por fotograma
    src/event_detection.py   detección escala-invariante + ritmo por segmentos
    src/rhythm_split.py      estimuladas vs espontáneas (enganche de fase)
    src/cinetica.py          TTP, RT50, onset/offset y amplitud relativa, con cotas
    src/qc_visualization.py  overlay de inliers/outliers, perfil de ROI
    src/plotting.py          figuras numeradas
    scripts/contraction_report.py   EL script principal de análisis
    scripts/motion_check.py         diagnóstico: QUÉ se mueve
    scripts/signal_check.py         diagnóstico: ¿hay población de eventos?
    tests/test_seleccion_k.py       regresión de la elección automática de k
    tests/test_cinetica.py          TTP/RT50 sobre eventos sintéticos de cinética conocida

Flujo normal:

    python main.py --video "<ruta>" --output-dir data/processed_data/<nombre> \
           --base-tiempo pts
    python scripts/contraction_report.py \
           --input data/processed_data/<nombre>/serie_temporal.xlsx \
           --frecuencia-estimulo 0.1

`--exigir-roi` hace que aborte si la ROI no cumple el criterio de aceptación,
en vez de avisar y seguir emitiendo números.

Los resultados vigentes están en `data/processed_data/<video>/`, **sin sufijo**.
Las corridas anteriores (las primeras, `_v4` y `_v5`) están archivadas en
`data/processed_data/_superadas/`. Los vigentes se generaron como `<video>_v6`
y `ordenar_carpeta.py` les quitó el sufijo al archivar el resto.

## Límites conocidos

- Una serie espontánea **muy** regular es indistinguible de una estimulada por
  los tiempos solos. Ahí hay que mirar la amplitud y saber si el estimulador
  estaba encendido.
- `rhythm_split` necesita al menos 4 latidos estimulados, y encuentra un solo
  tren por video.
- El grosor da un salto **positivo** en el fotograma de máxima velocidad: es
  motion blur, no engrosamiento. Usar siempre la medida robusta.
- `frequency_profile` no resuelve períodos mayores a `window_s / 2`. Con el
  default de 8 s no ve el ritmo de 10 s: subirlo a 20.
- El rescate de ROI por barrido maximiza ancho sujeto a planitud, y puede elegir
  una ventana plana pero con bordes difíciles de seguir (Video_466: 5.77 % de
  variación pero 16 % de outliers). Mirar siempre el `outlier_frac`.
- Video_491 (36 Hz) no tiene eventos certificables. **Descartada la hipótesis de
  tétanos:** el alias de 36 Hz a ~30 fps caería en ~6 Hz y el espectro no tiene
  nada ahí.
- A 30 fps, TTP y RT50 no son medibles cuando la contracción dura menos de ~5
  fotogramas.
