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
   (`cumple_criterio_aceptacion`). **Fase 3:** ancho mínimo 40 columnas × 3 px =
   120 px; se usan `min(60, ancho // 3)` columnas; el rescate exige contener la
   cintura. Ningún video necesita ROI manual.
2. **Detección subpíxel.** Gradiente de intensidad por columna y ajuste
   parabólico al máximo. Si el gradiente no supera `min_gradient`, la columna se
   descarta en vez de forzar una medición dudosa.
3. **Ajuste robusto.** RANSAC sobre 40–60 columnas con **polinomio de grado 2** y
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

> **Fase 4 (2026-10-07): verificado por un método independiente.** La traslación
> medida por correlación de intensidad (sin bordes, `motion_check` arreglado)
> coincide con `center_px` en magnitud: 0.96 en Video_prueba, 0.99 en 063, 0.88 en
> 466 y 0.82 en 476 (las dos últimas, de la tanda EXP5, sin explicar).
> **2026-10-10 (D1):** medido evento por evento (la pendiente de `motion_check` se
> achica con el ruido), 476 da 0.99; 268, 466 y 491 dan 0.86–0.88 y el resto
> 0.96–0.99. No es cosa de EXP5. Desde entonces `motion_check` juzga el tamaño
> contracción por contracción. Detalle en `docs/pendientes.md` D1.

> **Fase 3 (2026-10-08): una sola métrica de contractilidad, la traslación.** Se
> reporta la amplitud de `center_px` como **% del grosor en reposo** (cifra
> principal, comparable entre videos) y en **px** al lado (solo a igual aumento).
> Su amplitud cambia ≤ 4 % con o sin CLAHE y con o sin RANSAC, y una prueba con
> desplazamiento conocido confirma que mide bien la magnitud. El
> **adelgazamiento es solo diagnóstico, no se reporta**: con y sin CLAHE
> Video_prueba da 18 % contra 9 %, y 268 y 466 hasta cambian de signo. Si un borde
> solo tiene más SNR que el centro es porque el **otro** borde es más ruidoso
> (H54), no porque mida otra cosa: no se pondera el centro.

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

> **Fase 3 (2026-10-07).** El instante de cada latido es su **inicio** (cruce del
> 10 %), no el pico. Con `--frecuencia-estimulo` el tren se busca **solo cerca de
> esa frecuencia** (±10 %): la pregunta es "¿el estimulador capturó?", y así el
> p-valor tiene más poder. La amplitud entra **solo junto con un desvío de
> tiempo** (sacar un latido que falla en las dos cosas; rescatar un dudoso), nunca
> sola. Si hay tren, la cinética principal es la de los estimulados. Detalle en
> `docs/separacion-estimuladas-espontaneas.md`.

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
`docs/base-de-tiempo-y-frames-perdidos.md`.

**4. El umbral `k` se elige dentro de la meseta, y ya es automático.**
`--k auto` es el default. Dos reglas que no son obvias:
- Cuando hay varias mesetas, gana la de **`k` más bajo**: al subir el umbral se
  pierden eventos reales. El reporte lista **todas** las mesetas y usa el `k` del
  **centro** de la elegida (grilla fina ×1.1; una meseta tiene que abarcar ≥ ×1.25
  en `k`). "La meseta más larga" da la respuesta equivocada (en
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
`docs/metricas-cinetica-TTP-RT50.md`.

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
Hay otra carpeta hermana, `RARITOS-…/RARITOS/`, con los videos que MuscleMotion maneja mal: procesados el 2026-10-07
(resultados en `docs/raritos.md`).
Detalle en `docs/contexto-tecnun-y-musclemotion.md`.

## Stack Tecnológico

`opencv-python` (video e imagen), `numpy`, `scipy` (señal y picos),
`scikit-learn` (solo el sorteador de RANSAC; el ajuste es propio desde 2026-10-08), `matplotlib` (QC), `pandas` y `openpyxl` (salidas).

## Reglas Estrictas para el Código

* **Cero dependencia externa.** El pipeline lee un `.avi` o `.mp4` crudo y hace
  todo internamente. **Bajo ninguna circunstancia sugerir MUSCLEMOTION o
  ImageJ** como parte del flujo. Superar a MuscleMotion en robustez es un
  objetivo explícito: por eso se mide **geometría de borde**, no intensidad.
  (Sí se leen sus salidas cuando existen, para comparar: ver
  `docs/comparacion-musclemotion.md`.)
* **Cero cajas negras.** Todo análisis debe poder generar un output visual de
  diagnóstico para validar los parámetros.
* **Manejo de outliers.** Los problemas de iluminación o burbujas se resuelven
  estadísticamente por columnas, no "adivinando" datos faltantes.
* **Verificar antes de reportar.** El código original estaba sobreajustado a un
  único video y eso causó varios problemas serios. Ningún número se reporta sin:
  - **Meseta del escaneo de umbral** con 0 falsos de control.
  - **Control simétrico de falsos positivos** sobre la señal invertida.
  - **Regresión sobre Video_prueba y Video_063** cada vez que se toca un
    algoritmo. Los dos tienen que dar exactamente los mismos números que antes,
    salvo un cambio **intencional, medido y aprobado** (28 → 29 en Video_prueba
    en la Fase 2.2; nueva ROI de Video_063 en la Fase 3).
  - **Nunca** ajustar un parámetro hasta que el resultado dé lindo.
* **Ningún parámetro atado al tamaño del sujeto.** El `min_roi_width_frac = 0.35`
  (35 % de las columnas con gel) es el ejemplo de qué no hacer: se fijó mirando
  un video y rompía en todos los demás. El ancho mínimo ahora sale de cuántas
  columnas se muestrean y de cuán juntas pueden estar, **medido** (Fase 3): el
  error de borde deja de ser compartido a 2–3 px (separación 3 px) y con menos de
  40 columnas Video_063 da eventos falsos (piso 40). Detalle en
  `docs/historia/propuesta-fase-3-resto.md`.
* **No suavizar con pasabanda.** Para quitar la deriva se usa mediana móvil. Un
  pasabanda convierte cada evento real en un valle flanqueado por dos picos
  falsos y destruye la asimetría, que es justamente lo que se mide.
* **Una sola MAD, una sola mediana móvil** (`src/estadistica.py`). No
  volver a copiarlas: las nueve copias que había no toleraban NaN, y un solo
  fotograma rechazado dejaba el video en 0 eventos. Un fotograma sin medida
  **no se interpola**: no cuenta para el ruido ni puede ser un pico.
* **Qué es un evento (Fase 2.2): altura Y prominencia ≥ k·ruido, sin separación
  mínima en tiempo.** La vieja `--sep-s 0.3` fundía contracciones reales de una
  ráfaga (Video_prueba: 28 en vez de 29) y contaba la cola de un evento lento
  como otro evento. `find_peaks(distance=...)` no filtra ruido: se queda con el
  pico **más alto** de cada ventana y borra el resto. La opción `--sep-s` se
  borró el 2026-10-08.
* **La ventana del detrend no es fija (Fase 2.2):** al menos 3 veces el evento
  más largo, mínimo 2 s, y el conteo tiene que ser el mismo con 0.75×, 1× y
  1.5× esa ventana. Una mediana corta "baja con el evento" y se come la
  contracción (Video_491, eventos de ~1 s). Detalle en
  `docs/historia/propuesta-fase-2-2.md`.

## Estructura y comandos

    src/preprocessing.py     CLAHE + auto-ROI (gauge region) + rescate por barrido
    src/edge_detection.py    borde subpíxel por columna
    src/robust_fitting.py    RANSAC grado 2 (propio, igual al de sklearn), umbral adaptativo
    src/io_utils.py          lectura de video + timestamps (read_pts_seconds)
    src/pipeline.py          orquestador -> 4 series por fotograma
    src/rhythm_split.py      estimuladas vs espontáneas (enganche de fase)
    src/cinetica.py          TTP, RT50, onset/offset y amplitud relativa, con cotas
    src/estadistica.py       MAD, mediana móvil y búsqueda de picos: UNA sola copia, tolerante a NaN
    src/qc_visualization.py  overlay de inliers/outliers, perfil de ROI
    src/plotting.py          figuras numeradas
    scripts/contraction_report.py   EL script principal de análisis
    scripts/motion_check.py         diagnóstico: QUÉ se mueve; confirma center_px por intensidad
    scripts/signal_check.py         diagnóstico sin umbral: ¿hay población de eventos? (cualquier sentido)
    tests/test_seleccion_k.py       regresión de la elección automática de k
    tests/test_cinetica.py          TTP/RT50 sobre eventos sintéticos de cinética conocida
    tests/test_nan.py               fotogramas sin medida (NaN): el análisis no se anula
    tests/test_deteccion.py         la detección ENTERA sobre sintéticos de conteo conocido
    tests/test_ritmo.py             estimuladas/espontáneas: pulsos que fallan, R5, R6, veredictos
    tests/test_roi.py               elección de ROI: columnas adaptables, piso 40, rescate con cintura
    tests/test_diagnosticos.py      motion_check (corrimiento conocido), signal_check, junto_al_borde
    tests/test_ransac.py            el RANSAC propio da lo mismo que el de sklearn (grados 1-3)
    tests/test_regresion.py         REGRESIÓN de los 11 videos contra tests/referencia_regresion.json
                                    (--completo: además Video_prueba y 063 desde el video)
    tests/referencia.py             lista de videos de referencia, con sus argumentos, y la "huella"
    tests/generar_referencia.py     congela la referencia; solo con --aprobar "motivo"
    scripts/regenerar_todo.py       regenera los 11 y compara viejo contra nuevo antes de borrar
    interfaz.py + Analizar.bat      ventana para correr los pasos sin consola (no calcula nada propio)
    scripts/procesar_carpeta.py     una CARPETA entera (ventana o consola): mismos pasos por video + tabla resumen
    visor.py                        pestaña Resultados de la ventana: lista, numeros y grafico interactivo (solo LEE)
    tests/test_visor.py             la pestaña Resultados muestra lo de los Excel (ficha de cada contraccion)
    scripts/informe.py              paso 4: informe_<carpeta>.html de una pagina; solo LEE los Excel y figuras
    configuracion.ini               valores con que arranca la ventana (sin parametros del analisis, a proposito)
    tests/test_lote.py              la tabla de procesar_carpeta lee bien los Excel (no recalcula)
    docs/                           documentación vigente; docs/historia/ = propuestas y diagnósticos de fases cerradas
    docs/pendientes.md              la lista ÚNICA de lo que falta

Flujo normal: doble clic en `Analizar.bat` (la ventana corre estos mismos comandos; también una carpeta entera), o:

    python main.py --video "<ruta>" --output-dir data/processed_data/<nombre> \
           --base-tiempo pts
    python scripts/contraction_report.py \
           --input data/processed_data/<nombre>/serie_temporal_<nombre>.xlsx \
           --frecuencia-estimulo 0.1

Una carpeta entera: `python scripts/procesar_carpeta.py --carpeta "<videos>"` (tabla
`resumen_carpeta_<fecha>.xlsx` en `data/processed_data`). Versiones fijas en
`requirements.txt` (las del `.venv`; con ellas la regresión da idéntico).

`--procesos N` (en `main.py`) reparte los fotogramas entre N núcleos; por
defecto 2 (en la notebook de Franco, 4 núcleos, más procesos no ganan nada y 7
es más lento: lo que tarda es leer el video, en serie). El resultado es
idéntico con cualquier N. `contraction_report.py` también tiene `--procesos`
(default 2): reparte el Monte Carlo de la prueba del tren, que es lo que más
tarda con muchos eventos (613: 21 → 11 s; 2026-10-10). Resultado idéntico.
`--exigir-roi` hace que aborte si la ROI no cumple el criterio de aceptación,
en vez de avisar y seguir emitiendo números. `--verbose` (en los tres scripts)
imprime el detalle técnico; sin él la consola muestra solo resultados y AVISOS
cuando hay que actuar, y todo queda igual en los Excel. La ventana de búsqueda del
borde es automática (B1, 2026-10-10): ±15 px y, si el borde se sale (más del 20 %
de los fotogramas con bordes en el límite de la ventana, o más del 1 % sin borde),
`main.py` reprocesa solo con ±30 y lo dice. `--half-window N` la fija a mano. Qué significa cada línea de
la consola: `docs/guia-salida-consola.md`.

Los resultados vigentes están en `data/processed_data/<carpeta>/`,
regenerados el 2026-10-08 con `scripts/regenerar_todo.py` (nombres nuevos, sin
cambiar ningún número). Las corridas anteriores, solo en el historial de git.
Qué argumentos lleva cada carpeta está en `tests/referencia.py` (desde B1 ninguno
lleva `--half-window`: 068 y 341 pasan solos a ±30; 304 queda en ±15). La frecuencia 0.1 Hz de los seis videos de `OK` y de 476
**no está confirmada** por el equipo (la midió el propio pipeline); se mantiene
para la regresión, y en videos nuevos no se pasa salvo que el equipo la confirme.

**Verificar un cambio:** `python tests/test_regresion.py` (segundos) y, si se tocó
ROI, bordes o RANSAC, `--completo`. Si el cambio es intencional y aprobado:
`python tests/generar_referencia.py --aprobar "motivo"`. **No guardar en
`processed_data` salidas del cuaderno**: el `contracciones.xlsx` (nombre viejo) de Video_prueba
apareció reescrito con `win_s` fijo de 2 s (28 eventos; probablemente el
cuaderno) y la regeneración lo devolvió a 29. Línea base: Video_prueba 29 eventos (6 estimulados, T = 10.00043 ±
0.0023 s); 063: 6; 268: 6; 466: 5 (ROI automática); 583: 6; 491: 2.

## Límites conocidos

- Una serie espontánea **muy** regular es indistinguible de una estimulada por
  los tiempos solos. Ahí hay que mirar la amplitud y saber si el estimulador
  estaba encendido.
- `rhythm_split` necesita al menos 4 latidos estimulados y el 75 % de las
  ranuras ocupadas. Con `--frecuencia-estimulo` busca un tren por frecuencia
  configurada (solo a ±10 % de cada una: búsqueda dirigida); sin ella, un tren
  en todos los períodos. Ver `docs/separacion-estimuladas-espontaneas.md`.
- El grosor da un salto **positivo** en el fotograma de máxima velocidad: es
  motion blur, no engrosamiento. Usar siempre la medida robusta.
- **Fase 4: el chequeo `outlier_frac` < 10 % ya no es criterio de aceptación**
  (H24): el umbral de descarte se adapta al fotograma y, medido en 063 y 466,
  ordena las ROIs al revés del ruido del canal. La ROI se acepta por su forma
  (variación ≤ 6 %, contiene la cintura). `resumen` registra `outlier_frac` y el
  **error de modelo** (cuánto se aparta la parábola del borde de forma estable)
  como diagnóstico, sin umbral (en `RARITOS`: outliers 2.5–5.2 %, error de
  modelo 0.06–1.04 % del grosor; sin problemas).
- **Una vibración del montaje entra en `center_px` igual que una contracción** y
  el reporte no siempre la distingue. Video_583 tiene una en 71.9–73.9 s (~10 Hz,
  tiembla toda la imagen): da un 7.º candidato a 11 σ que la meseta deja afuera por
  poco. En Video_613 la vibración va hacia los dos lados y el control con la señal
  invertida la delata (NO REPORTABLE). Detectarla siempre necesita una referencia
  fija con textura: en 068, 304 y 341 los anillos del anclaje sirven.
- **El método cuenta contracciones separadas por reposo.** Con actividad continua
  del tejido (068, 304) la oscilación cuenta como ruido y el conteo no aplica; hace
  falta otra medida (actividad), anotada en `docs/pendientes.md`.
- **Ventana de búsqueda del borde: ±15 px, o ±30 automática** si el borde se sale
  (068, 341). No usar ±30 para todos: en 466 engancha otro gradiente (5 → 2
  eventos). Un borde fuera de la ventana puede fallar **en silencio** (341: 0 %
  sin borde y 22 → 16 eventos); por eso se cuentan los bordes pegados al límite.
- Un evento a menos de media ventana del detrend del inicio o del fin queda
  marcado `junto_al_borde` (su línea base se estima con media ventana). El de
  Video_063 en 0.31 s es real (se ve en la señal cruda y por intensidad).
- Varias reglas salieron de pocos videos (piso de 40 columnas, "zona plana mejor
  que ancha", "meseta de k más bajo"). Lista en `docs/pendientes.md`, sección D.
- **Video_491 (36 Hz) es distinto de los otros cinco** y hay que consultarlo con el
  equipo antes de citarlo. Desde la Fase 2.2 da **2 eventos reportables** (13.0 y
  34.0 s): excursiones de ~1 s con el fondo plano, el doble de largas que las de
  los demás, y **en sentido contrario** (`signo` −1: la franja sube en la pantalla;
  en los otros cinco baja). Con la ventana fija de 2 s la mediana se comía esos
  eventos y el video salía "sin meseta". Una contracción sostenida ~1 s con
  estimulación a 36 Hz es compatible con un **tétanos fusionado** (meseta lisa,
  sin ondulación a la frecuencia del estímulo); el descarte anterior buscaba una
  ondulación a ~6 Hz, que un tétanos fusionado no tiene. No está confirmado.
- A 30 fps, TTP y RT50 no son medibles cuando la contracción dura menos de ~5
  fotogramas.
