# Pipeline de contractilidad de geles 3D

Mide la contractilidad de geles 3D a partir de video de microscopía, sin
depender de ImageJ ni de MuscleMotion. Lee un `.mp4`/`.avi` crudo y hace todo
internamente: detecta la zona útil del gel, localiza los dos bordes con
precisión subpíxel en ~60 columnas por fotograma, ajusta un polinomio robusto
que descarta columnas arruinadas por burbujas, y de ahí saca las series
temporales, los eventos de contracción y la separación entre contracciones
estimuladas y espontáneas.

## Instalación

```bash
pip install -r requirements.txt
```

## Uso

```bash
python main.py --video "data/raw_videos/mi_video.mp4" \
               --output-dir data/processed_data/mi_video \
               --base-tiempo pts

python scripts/contraction_report.py \
       --input data/processed_data/mi_video/serie_temporal.xlsx \
       --frecuencia-estimulo 0.1
```

Eso es todo: los dos comandos generan los `.xlsx` y los PNG numerados en la
carpeta de salida. `--frecuencia-estimulo` decide **dónde se busca el tren**:
con ella, solo cerca de esa frecuencia (±10 %), y el reporte dice "enganchado" o
"no hay enganche"; si el protocolo cambia de frecuencia, se pasan todas
(`--frecuencia-estimulo 0.1 0.2`). Sin ella, se busca un tren en todos los
períodos y el veredicto aclara que no se configuró ninguna frecuencia.

Flags que conviene conocer:

| flag | para qué |
|---|---|
| `--base-tiempo pts` | eje temporal desde los timestamps del contenedor. **Usarlo siempre** (ver abajo) |
| `--exigir-roi` | aborta si la ROI no cumple el criterio de aceptación, en vez de avisar y seguir |
| `--x-start` / `--x-end` | fuerza la zona de medición a mano cuando la automática no sirve |
| `--k` | fuerza el umbral de detección. Por defecto es `auto` y lo elige la meseta del escaneo |

## Tres cosas que hay que saber antes de usarlo

**1. La detección se hace sobre `center_px`, no sobre el grosor.** En este
montaje la contracción es mayormente un desplazamiento vertical de toda la
franja. Como el grosor es la resta de los dos bordes, es **ciego a la
traslación** por construcción: si los dos bordes bajan 1 px, no cambia. Medido,
el SNR por fotograma es 44 en `center_px` contra 3 en `thickness_px`. El grosor
se sigue midiendo, pero promediando eventos alineados en el tiempo.

**2. El eje temporal sale de los timestamps del contenedor.** El `fps` que
declara un `.mp4` es el **promedio** `(n−1)/duración`, y baja cuando la
grabación pierde fotogramas: entonces `fotograma / fps` se come los huecos y los
eventos aparecen más juntos de lo que fueron. Uno de nuestros videos perdió el
4.7 % de sus fotogramas y su período de estimulación medía 9.51 s en vez de
10.01 s, un error del +5 %. Con `--base-tiempo pts` el problema desaparece.

**3. Ningún número se reporta sin verificarlo.** El pipeline aplica tres
chequeos de aceptación y los deja por escrito en las salidas: variación de
grosor dentro de la ROI < 6 %, `outlier_frac` medio < 10 %, y una meseta en el
escaneo de umbral con cero falsos de control. **Si no hay meseta, el conteo de
eventos se marca como no reportable** en vez de publicarse igual.

## Calibración: fuera de alcance por decisión del proyecto

**No se calibra píxeles a milímetros.** Los videos no se graban todos al mismo
aumento, así que un factor único no tendría sentido. `--px-to-mm` queda en 1.0
y **todos los resultados se reportan en píxeles**; las figuras lo indican con
"SIN CALIBRAR" en el título. Las comparaciones entre videos se hacen en términos
relativos (porcentaje del grosor, cocientes) o dentro de un mismo aumento.

## Estructura

    src/io_utils.py          lectura del video y de sus timestamps
    src/preprocessing.py     CLAHE + detección automática de la zona útil
    src/edge_detection.py    borde subpíxel por columna
    src/robust_fitting.py    RANSAC grado 2 con umbral adaptativo
    src/pipeline.py          orquestador -> 4 series por fotograma
    src/estadistica.py       MAD, mediana móvil y búsqueda de picos (una sola copia, tolera NaN)
    src/rhythm_split.py      estimuladas vs espontáneas por enganche de fase
    src/qc_visualization.py  overlays de diagnóstico
    src/plotting.py          figuras numeradas
    scripts/contraction_report.py   el script principal de análisis
    scripts/motion_check.py         diagnóstico: qué se mueve
    scripts/signal_check.py         diagnóstico: ¿hay población de eventos?
    src/cinetica.py          TTP, RT50 y amplitud relativa, con cotas cuando no son medibles
    tests/test_seleccion_k.py       regresión de la elección automática del umbral
    tests/test_cinetica.py          TTP/RT50 sobre eventos sintéticos de cinética conocida
    tests/test_ritmo.py             estimuladas/espontáneas: pulsos que fallan, R5, R6, veredictos

Resultados vigentes: `data/processed_data/<video>/` (sin sufijo). Las corridas
anteriores están archivadas en `data/processed_data/_superadas/`.

## Documentación

`Analisis_Contractilidad_v4.ipynb` recorre el flujo entero paso a paso,
mostrando la salida de cada etapa. Es el mejor punto de entrada.

En `docs/`:

| documento | para qué |
|---|---|
| `ESTADO-arranque-chat-nuevo.md` | el estado actual y qué está pendiente |
| `protocolo-analisis-videos.md` | los comandos por video y los chequeos de aceptación |
| `referencia-archivos-y-graficos.md` | qué contiene cada archivo y qué significa cada eje |
| `base-de-tiempo-y-frames-perdidos.md` | el eje temporal, en detalle |
| `separacion-estimuladas-espontaneas.md` | el método de enganche de fase y sus límites |
| `comparacion-musclemotion.md` | los números medidos contra MuscleMotion |
| `metricas-cinetica-TTP-RT50.md` | métricas de cinética: viabilidad, implementación y resultados |
| `revision-script-matlab.md` | revisión del script del equipo |
| `guia-revision-codigo.md` | guía para revisar el código de punta a punta |
| `DOCUMENTACION.md` | el método explicado sin código, para quien diseña el experimento |

## Pendiente

- Procesar los videos de la carpeta `RARITOS`.
- Grabar un video de control de iluminación: mismo gel, quieto, con un cambio
  de luz. Es lo único que falta para demostrar con un número que medir
  geometría de borde es inmune a la iluminación.
- Adquisición a 200–300 fps si se quieren medir TTP y RT50 de verdad: a 30 fps
  la subida de las muestras rápidas dura 1–2 fotogramas y solo se puede dar
  una cota (TTP < 100 ms). TTP, RT50 y amplitud relativa ya están
  implementados y salen en `contracciones.xlsx`.

El detalle de lo pendiente está en `docs/ESTADO-arranque-chat-nuevo.md`.
