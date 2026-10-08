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

**La forma fácil:** doble clic en `Analizar.bat`. Se abre una ventana donde se
elige el video (o se lo arrastra; para eso, una vez, `pip install tkinterdnd2`)
y la carpeta de resultados, se marcan los pasos a correr y se ve la salida en
vivo. La ventana corre los mismos comandos de abajo: los números son idénticos.

**Por consola:**

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
| `--half-window 30` | cuando el gel se mueve mucho y `main.py` avisa que hay fotogramas sin borde |
| `--verbose` | (los tres scripts) imprime también el detalle técnico; sin él, solo resultados y avisos |

Opcional, para confirmar el movimiento por un segundo método (intensidad, sin bordes):

```bash
python scripts/motion_check.py --video "data/raw_videos/mi_video.mp4" \
       --serie data/processed_data/mi_video/serie_temporal.xlsx
```

Qué significa cada línea que se imprime, qué es normal y qué contestar si
alguien pregunta: `docs/guia-salida-consola.md`.

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

**3. Ningún número se reporta sin verificarlo.** El pipeline deja por escrito
en las salidas sus chequeos de aceptación: la variación de grosor dentro de la
zona medida es ≤ 6 % y la zona contiene la cintura del gel; y el escaneo del
umbral tiene una meseta con cero falsos de control (el mismo detector sobre la
señal invertida). **Si no hay meseta, el conteo se marca NO REPORTABLE** en vez
de publicarse igual, y las figuras lo dicen en el título.

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
    src/cinetica.py          TTP, RT50 y amplitud relativa, con cotas cuando no son medibles
    src/qc_visualization.py  overlays de diagnóstico y escritura de los Excel
    src/plotting.py          figuras numeradas
    main.py                         paso 1: video -> serie_temporal.xlsx
    scripts/contraction_report.py   paso 2: contracciones, ritmo y cinética
    scripts/motion_check.py         paso 3 (opcional): confirma el movimiento por intensidad
    scripts/signal_check.py         diagnóstico: ¿hay población de eventos?
    scripts/inspect_frame.py        diagnóstico de un solo fotograma
    scripts/medir_*.py              mediciones de las fases (no son parte del flujo)
    interfaz.py, Analizar.bat       la ventana
    tests/test_*.py                 siete pruebas: python tests/test_<nombre>.py

Resultados vigentes: `data/processed_data/<video>/` (sin sufijo). Las corridas
anteriores están archivadas en `data/processed_data/_superadas/`.

## Documentación

`Analisis_Contractilidad_v4.ipynb` recorre el flujo entero paso a paso,
mostrando la salida de cada etapa.

En `docs/`:

| documento | para qué |
|---|---|
| `guia-salida-consola.md` | **para usarlo:** la ventana, los comandos y qué significa cada línea que se imprime |
| `pendientes.md` | la lista única de lo que falta |
| `ESTADO-arranque-chat-nuevo.md` | el estado actual, los resultados de referencia y el texto para arrancar un chat nuevo |
| `protocolo-analisis-videos.md` | reglas del método y chequeos de aceptación antes de informar un número |
| `referencia-archivos-y-graficos.md` | qué contiene cada archivo, cada columna y cada eje |
| `DOCUMENTACION.md` | el método explicado sin código, para quien diseña el experimento |
| `raritos.md` | resultados de los videos `RARITOS` |
| `preguntas-reunion-equipo.md` | preguntas para el equipo de Tecnun |
| `base-de-tiempo-y-frames-perdidos.md` | el eje temporal, en detalle |
| `separacion-estimuladas-espontaneas.md` | el método de enganche de fase y sus límites |
| `metricas-cinetica-TTP-RT50.md` | métricas de cinética: viabilidad, implementación y resultados |
| `comparacion-musclemotion.md` | los números medidos contra MuscleMotion |
| `contexto-tecnun-y-musclemotion.md` | para quién es el trabajo y qué es la carpeta `OK` |
| `revision-script-matlab.md` | revisión del script del equipo |
| `historia/` | propuestas y diagnósticos de las fases ya cerradas, y la revisión de código: cómo se llegó a cada decisión |

## Pendiente

Todo en `docs/pendientes.md`. Lo principal: respuestas del equipo de Tecnun
(estimulación de los RARITOS, adquisición a 200–300 fps, video de control de
iluminación), una medida de actividad para los videos con actividad continua, y
optimizar el tiempo de procesamiento.
