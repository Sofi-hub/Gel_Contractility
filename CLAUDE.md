# Proyecto: Análisis de Contractilidad de Geles 3D

## Objetivo Principal
Automatizar el análisis de la contractilidad mecánica de cultivos celulares 3D
embebidos en geles: medir la deformación del gel a lo largo del tiempo de forma
automatizada, reproducible y **verificable**, a partir de video de microscopía.

## Arquitectura del Pipeline (v3)

1. **Mapeo espacial (auto-ROI).** Se genera un `maxProjectStack` internamente,
   sin software externo. Sobre él, `preprocessing.auto_detect_roi` **sigue la
   franja del gel columna a columna desde el centro hacia afuera** (así un halo
   o un reflejo no la estiran), estima la *cintura* usando sólo columnas cuyo
   grosor es compatible con el gel, y elige por planitud la *gauge region*: la
   zona uniforme lejos de los anclajes, donde la deformación la manda la
   contractilidad del material y no la concentración de tensiones del anclaje.
   Reporta también los niveles de criterio que descartó, para poder forzar otro
   a mano con `--x-start`/`--x-end`.
2. **Detección subpíxel.** Gradiente de intensidad por columna y ajuste
   parabólico al máximo (el default es `parabolic`; `sigmoid` está disponible).
   Si el gradiente no supera `min_gradient`, la columna se descarta en vez de
   forzar una medición dudosa.
3. **Ajuste robusto.** RANSAC sobre ~60 columnas con **polinomio de grado 2**
   (no recta: el borde real tiene curvatura, y con grado 1 esa curvatura se
   clasifica como outlier) y **umbral de residuo adaptativo** (3×MAD del propio
   fotograma, no un valor fijo).
4. **Cuatro series temporales, no una.** Se guardan `y_top_px`, `y_bottom_px`,
   `thickness_px` (la resta) y `center_px` (el promedio).
5. **Detección de eventos** sobre el observable elegido, con verificación
   estadística del umbral.
6. **Separación de contracciones estimuladas y espontáneas** por enganche de
   fase (`src/rhythm_split.py`).

## Los tres hallazgos que definen el método — NO revertirlos

**1. Detectar sobre `center_px`, no sobre `thickness_px`.**
La intuición de que una contracción se ve como adelgazamiento supone que los
dos extremos están perfectamente fijos y que la contracción es simétrica. En
este montaje no es así: la contracción es mayormente un **desplazamiento
vertical de toda la franja**, y sólo el 13–19 % de ese movimiento es cambio de
grosor. Ese cociente resultó ser el mismo en el video que "funcionaba" y en el
que "no funcionaba": la mecánica es la misma, cambia la amplitud.

Como `thickness_px` es la resta de los dos bordes, es **ciego a la traslación**
por construcción. Medido: SNR por fotograma de 44 en `center_px` contra 3 en
`thickness_px` para el video débil. Con `thickness_px`, el escaneo de umbral
daba 7 eventos con 11 falsos a k=3 y 0 eventos a k≥6 — que era exactamente el
síntoma que reportaba el usuario. Con `center_px`, meseta limpia de k=10 a 20
con 0 falsos.

El grosor **sigue midiéndose**, porque es la variable biomecánicamente
interesante, pero promediando eventos alineados en el tiempo (event-locked
average), no evento a evento.

**2. Estimuladas vs espontáneas: por enganche de fase, no por amplitud ni por
ventana temporal.** El estimulador dispara en `t = fase + n·T`; las espontáneas
no saben nada de ese reloj. Se busca esa grilla y lo que queda afuera es
espontáneo. La amplitud **no** se usa para clasificar, y por eso sirve como
verificación independiente. Las espontáneas no mantienen frecuencia constante
(CV medido del 91 %): se reporta mediana, rango intercuartil y frecuencia
instantánea, nunca un solo número.

**3. El `fps` que declaran los archivos de video está mal.** Contrastado contra
el estimulador: 300.0 fotogramas por período exactos en dos videos distintos,
o sea fps real = 30.000 contra 29.7289 y 29.8699 declarados. Todos los tiempos
están escalados entre 0.4 % y 0.9 %. El estimulador es un reloj de cuarzo; el
metadato del archivo no.

## Fuera de alcance por decisión del proyecto

**No se calibra píxeles a milímetros.** Los videos no se graban todos al mismo
aumento, así que un factor único no tendría sentido. `px_to_mm` queda en 1.0 y
**todo se reporta en píxeles**. Las comparaciones entre videos se hacen en
términos relativos (porcentaje del grosor, cocientes) o dentro de un mismo
aumento. No proponer calibrarlo salvo que el usuario lo pida.

## Stack Tecnológico

`opencv-python` (video e imagen), `numpy`, `scipy` (señal y picos),
`scikit-learn` (RANSAC), `matplotlib` (QC), `pandas` y `openpyxl` (salidas).

## Reglas Estrictas para el Código

* **Cero dependencia externa.** El pipeline lee un `.avi` o `.mp4` crudo y hace
  todo internamente. **Bajo ninguna circunstancia sugerir MUSCLEMOTION o
  ImageJ.** Superar a MuscleMotion en robustez a cambios sutiles de iluminación
  es un objetivo explícito del proyecto: por eso se mide **geometría de borde**,
  no intensidad.
* **Cero cajas negras.** Todo análisis debe poder generar un output visual de
  diagnóstico para validar los parámetros.
* **Manejo de outliers.** Los problemas de iluminación o burbujas se resuelven
  estadísticamente por columnas, no "adivinando" datos faltantes.

* **NUEVA — Verificar antes de reportar.** El código original estaba
  sobreajustado a un único video de ejemplo y eso causó varios problemas
  serios. Ningún número se reporta sin verificación:
  - **Meseta del escaneo de umbral.** Si el conteo de eventos no se estabiliza
    a lo largo de un rango de `k`, no hay eventos: hay ruido.
  - **Control simétrico de falsos positivos.** Correr el mismo detector sobre
    la señal invertida. Una contracción sólo puede ir en un sentido.
  - **Simulación con verdad conocida** cada vez que se toca un algoritmo.
  - **Nunca** ajustar un parámetro hasta que el resultado dé lindo. Si hay que
    moverlo, primero entender qué lo rompe.
* **NUEVA — No suavizar con pasabanda.** Para quitar la deriva se usa mediana
  móvil. Un pasabanda convierte cada evento real en un valle flanqueado por dos
  picos falsos y destruye la asimetría, que es justamente lo que se mide.
* **NUEVA — `--sep-s` y parámetros de proximidad.** `find_peaks(distance=...)`
  no filtra ruido: se queda con el pico **más alto** de cada ventana y borra el
  resto. Un valor grande borra eventos reales de un tren rápido.

## Estructura y comandos

    src/preprocessing.py     CLAHE + auto-ROI (gauge region)
    src/edge_detection.py    borde subpíxel por columna
    src/robust_fitting.py    RANSAC grado 2, umbral adaptativo
    src/pipeline.py          orquestador -> 4 series por fotograma
    src/event_detection.py   detección escala-invariante + ritmo por segmentos
    src/rhythm_split.py      estimuladas vs espontáneas (enganche de fase)
    src/qc_visualization.py  overlay de inliers/outliers, perfil de ROI
    src/plotting.py          figuras numeradas
    scripts/contraction_report.py   EL script principal de análisis
    scripts/motion_check.py         diagnóstico: QUÉ se mueve
    scripts/signal_check.py         diagnóstico: ¿hay población de eventos?
    scripts/inspect_frame.py        diagnóstico: un fotograma en detalle

Flujo normal:

    python main.py --video "<ruta>" --output-dir data/processed_data/<nombre>
    python scripts/contraction_report.py --input data/processed_data/<nombre>/serie_temporal.xlsx

`--frecuencia-estimulo 0.1` es opcional: sin ese flag igual mide la frecuencia
del tren, sólo que no la contrasta contra un valor configurado.

## Límites conocidos

- Una serie espontánea **muy** regular es indistinguible de una estimulada por
  los tiempos solos. Ahí hay que mirar la amplitud y saber si el estimulador
  estaba encendido.
- `rhythm_split` necesita al menos 4 latidos estimulados, y encuentra un solo
  tren por video (si la estimulación cambia de frecuencia a mitad, hay que
  extenderlo).
- El grosor medido da un salto **positivo** en el fotograma de máxima
  velocidad: es motion blur, no engrosamiento. Usar siempre la medida robusta
  (promedio de los 3 fotogramas posteriores al pico).
- `frequency_profile` no resuelve períodos mayores a `window_s / 2`. Con el
  default de 8 s no ve el ritmo de 10 s de los videos estimulados.
- Video a ~30 fps: una estimulación a 36 Hz no se resuelve (Nyquist). Lo más
  probable es que ahí la respuesta sea un tétanos sostenido, en cuyo caso
  contar picos no es la herramienta correcta.
