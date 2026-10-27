# Textura contra bordes en 583, 466, 063 y 268 (2026-10-26)

**Pregunta.** Con `--metodo textura` estos cuatro videos empeoran: 583 pasa de 6 a 39 eventos, 466
parte uno (5 → 6) y 063 y 268 pierden la meseta con la ventana de 1.5 s. Con bordes los cuatro están
bien. ¿Es una falla de la textura, o la textura está viendo algo que los bordes tapan?

**Respuesta corta.** **Son dos cosas distintas y conviene no mezclarlas.**

- En **583, 063 y 268** la textura **no se inventa nada**: los movimientos que detecta de más están
  también en la señal de bordes, en el mismo instante, pero por debajo del umbral que bordes usa. La
  textura tiene 3.7 a 5.1 veces menos ruido y por eso los resuelve. Lo que falla no es la medición
  sino el **conteo**, que supone que entre contracción y contracción el gel está quieto.
- En **466 sí hay una falla de la textura**, y tiene nombre y arreglo: en el fotograma más rápido de
  la contracción la correlación de fase pierde el enganche y la serie da un bajón falso que parte el
  evento en dos. Se ve en un dato que la serie **ya guarda**: `respuesta_correlacion`.

## Cómo se midió

Dos scripts, que solo leen; no tocan el análisis ni `data/processed_data`.

- `comparar_textura.py`: mide la serie por textura con el método implementado (`src/textura.py`), la
  guarda en `series/` para no volver a medir, y corre la **misma** detección
  (`contraction_report.analizar`) sobre bordes y sobre textura, con la ventana automática y fijada en
  1.5, 2 y 3 s. Tablas: `comparacion.csv`, `ventanas.csv`, `eventos.csv`. Figuras: `serie_<video>.png`
  (serie entera y zoom, con los eventos de cada método marcados). Consola: `salida.txt`.
- `detalle_textura.py`: para cada evento que ve la textura y no los bordes, cuánto hay **en la señal
  de bordes en ese mismo instante**, en veces su ruido y como fracción de su umbral, más la
  correlación local de las dos señales. Tabla: `solo_textura.csv`. Consola: `salida_detalle.txt`.
  `correlacion_en_extras.csv` agrega la calidad de la correlación de fase en esos instantes.

## Resultado

### 1. Las dos señales miden lo mismo

| video | eventos bordes | eventos textura | emparejados (±0.3 s) | amplitud textura / bordes | ruido en tramos quietos (bordes / textura) |
|---|---|---|---|---|---|
| 583 | 6 | 39 | **6 de 6** | 0.97 (0.94–1.01) | 0.062 / 0.008 px → **7.4×** |
| 466 | 5 | 6 | **5 de 5** | 0.87 (0.79–0.92) | 0.177 / 0.095 px → 1.9× |
| 063 | 6 | 6 | **6 de 6** | 0.88 (0.59–0.92) | 0.023 / 0.006 px → 3.7× |
| 268 | 6 | 6 | **6 de 6** | 0.89 (0.85–0.92) | 0.045 / 0.010 px → 4.4× |

Todas las contracciones de bordes aparecen por textura, en el mismo instante. Lo que cambia es el
piso de ruido.

### 2. Los eventos "de más" están también en bordes, debajo del umbral

Para cada evento que solo ve la textura, cuánto vale la señal de **bordes** en ese mismo instante:

| video | eventos solo en textura | en textura | en bordes, mismo instante | % del umbral de bordes | correlación local |
|---|---|---|---|---|---|
| 583 | 33 | 0.12–0.76 px (9–53 × su ruido) | 0.09–0.83 px (**1.3–11.4 × su ruido**) | 21 % (mediana) | 0.91 (33 de 33 con r > 0.5) |
| 063 (ventana 1.5 s) | 2 | 0.07–0.10 px (11–16 ×) | 0.09–0.11 px (**3.8–4.6 ×**) | 34 % | 0.84 |
| 268 (ventana 1.5 s) | 3 | 0.10–0.19 px (10–19 ×) | 0.12–0.22 px (**2.6–4.8 ×**) | 35 % | 0.72 |

Es decir: **los bordes también se mueven en esos instantes** (hasta 11 veces su ruido en 583), solo
que el umbral del conteo, que está calibrado con el ruido alto de bordes, los deja afuera. Y la
calidad de la correlación de fase en esos instantes es **normal** (la mediana del video), así que no
son fallas de medición.

### 3. Dónde están esos movimientos

- **583: confirmado, es la vibración.** De los 33 eventos de más, **11 caen entre 71.90 y 73.82 s,
  separados ~0.10 s** (≈10 Hz): es exactamente la ráfaga conocida (`fase4_rafaga583/`, "~10 Hz,
  tiembla toda la imagen"). Otros 10 están entre 64 y 68.4 s, o sea los últimos 10 s del video están
  agitados, no solo los 2 s de la ráfaga. Los de más miden 0.12–0.76 px contra 2.94–3.01 px de las
  contracciones reales: 4 a 25 veces más chicos.
- **063 con ventana 1.5 s:** los 2 de más están a **0.37 s y 2.01 s después** de la contracción de
  41.91 s, o sea pegados a un evento real y a una distancia del orden de la ventana. Con 2 s y con
  3 s no aparecen. **Con la ventana de 3 s, 063 por textura es REPORTABLE con los mismos 6 eventos.**
- **268 con ventana 1.5 s:** 3 de más (18.37, 18.66 y 66.13 s). Con 2 s y 3 s, 6 eventos.
- O sea, 063 y 268 no "fallan": el conteo deja de ser estable solo porque la regla pide el mismo
  número con 0.75×, 1× y 1.5× la ventana, y a 1.5 s el piso de ruido bajo deja pasar el rebote que
  sigue a una contracción.

### 4. 466: esto sí es una falla de la textura

El evento de 34.28 s sale partido en dos picos, a 34.18 y 34.31 s. El valle entre ellos:

| | valle | en veces el ruido | % de la altura del evento |
|---|---|---|---|
| **textura** | 0.871 px | **8.9 ×** | 27 % |
| **bordes** | 0.069 px | **0.4 ×** | 2 % |

En bordes el valle **no existe** (0.4 veces el ruido es nada), y los dos bordes (`y_top_px`,
`y_bottom_px`) suben sin interrupción. O sea no es que bordes no lo resuelva: es que no está.

La causa se ve fotograma a fotograma (`salida_detalle.txt` y la tabla de abajo): en el fotograma de
34.210 s la textura baja de 3.285 a 2.414 px y **la respuesta de la correlación de fase cae a 0.285**,
que es el **mínimo de todo el video** (mediana 0.984, percentil 5 0.911). Los fotogramas de la subida
rápida tienen todos la respuesta baja (0.45, 0.35, 0.29, 0.58): es el **motion blur del momento de
máxima velocidad**, el mismo que ya se conoce por el salto positivo del grosor.

| t (s) | bordes | textura | respuesta corr. |
|---|---|---|---|
| 34.150 | 2.711 | 2.315 | 0.350 |
| 34.177 | 3.755 | 3.285 | 0.753 |
| **34.210** | **3.686** | **2.414** | **0.285** ← mínimo del video |
| 34.252 | 3.712 | 3.625 | 0.577 |
| 34.277 | 4.364 | 3.665 | 0.584 |

Y la separación es limpia: en 583, 063 y 268 los eventos de más tienen la respuesta **normal**
(0.81–0.90, con la mediana del video en 0.85–0.90) y **ninguno** por debajo de la mitad de la mediana.
Solo 466 tiene el bajón.

## Conclusión

1. **La textura mide bien.** En los cuatro videos encuentra las mismas contracciones, en el mismo
   instante, con amplitudes del 87 al 97 % de las de bordes (ya medido en `textura/`), y con 2 a 7
   veces menos ruido.
2. **583, 063 y 268 no son fallas de la textura:** la textura ve movimiento real que los bordes no
   pueden resolver. El problema es que **el conteo supone reposo entre contracciones**, y con un piso
   de ruido 4–7 veces más bajo deja de haberlo. Es el mismo límite ya anotado para 068 y 304
   (actividad continua), que acá aparece por tener mejor resolución, no peor medición.
3. **466 sí es una falla de la textura, y es arreglable sin tocar la medición:** la correlación de
   fase pierde el enganche en el fotograma más rápido. La serie **ya guarda** `respuesta_correlacion`,
   así que el arreglo natural sería marcar esos fotogramas como **sin medida** (NaN), que es algo que
   el pipeline ya sabe manejar: un fotograma sin medida no se interpola, no cuenta para el ruido y no
   puede ser un pico (`src/estadistica.py`). Con un umbral del tipo "la respuesta cae por debajo de la
   mitad de la mediana del video" se marcarían los 3 o 4 fotogramas del pico de 466 y **ninguno** de
   los instantes conflictivos de 583, 063 y 268.
4. **No se implementó nada:** esto cambiaría números informados (el conteo de 466 por textura), así
   que hay que medirlo y aprobarlo antes.

### Qué significa para usar textura en videos nuevos

- La textura **no es peor** que los bordes; es más sensible. Donde el gel está realmente quieto entre
  contracciones (Video_prueba, 491, 476) da el mismo conteo y es reportable.
- Donde el tejido tiene actividad de fondo, la textura la ve y **el conteo se vuelve no reportable**.
  Eso es honesto, no un error: la medida que falta ahí es la de actividad, que ya está anotada en
  `docs/pendientes.md`.
- **Conviene mirar siempre `respuesta_correlacion`**: si cae mucho en los picos, los eventos partidos
  son sospechosos. Hoy esa columna está en la serie pero nadie la mira.
- La ventana de 1.5 s del chequeo de estabilidad es la que más molesta con señales de poco ruido. No
  conviene tocarla sin medirlo en los 11 videos: la regla de las tres ventanas es la que protege de
  los eventos largos (Video_491).

## Límites

- Las series de textura de esta carpeta se midieron una sola vez y quedaron cacheadas en `series/`;
  con `--remedir` se vuelven a medir.
- El emparejamiento de eventos usa ±0.3 s, el mismo criterio de `textura/validar.py`.
- Los eventos "de más" se comparan contra la señal de bordes **sin volver a detectar**: se mira el
  valor en ese instante, no se afirma que bordes los detectaría con otro umbral.
- No se tocó ningún archivo del análisis. Ningún número informado cambia.

---

# B. Marcar como "sin medida" los fotogramas de confianza baja: **no sirve** (2026-10-27)

**Lo que se proponía arriba.** En 466, la textura parte en dos el evento de ~34 s, y justo en el
fotograma más rápido la correlación de fase se desploma (0.285 contra 0.984 de mediana). Parecía
motion blur, así que la idea era **no creerle** a esos fotogramas: marcarlos como sin medida (NaN),
que el pipeline ya sabe manejar, y esperar que 466 por textura pasara de 6 eventos a 5.

**Lo que se probó** (`nan_por_confianza.py`, solo medición): la regla
`respuesta_correlacion < u × la mediana del video` → NaN, con **u = 0.3, 0.5 y 0.7**, contra no
marcar nada. Corrida sobre los **11 de referencia medidos por textura** (las series se cachean en
`series/`) y sobre los **9 de Andrés**, que ya están medidos por textura y guardan la columna
`respuesta_correlacion` por fotograma (o sea: las series guardadas, sin volver a leer los 4K).
Tabla completa: `nan_por_confianza.csv` (80 filas), consola en `salida_nan_por_confianza.txt`.

## Resultado: en 17 de los 20 no marca nada, y donde marca, empeora

| video | marcados 0.3 / 0.5 / 0.7 | eventos sin marcar → 0.3 → 0.5 → 0.7 |
|---|---|---|
| **466** | 3 / 10 / 21 | 6 (NO rep) → **8 (rep)** → **12 (rep)** → **13 (NO rep)** |
| Video_prueba | 0 / 0 / 2 | 29 → 29 → 29 → **31** |
| 068 | 40 / 166 / 368 | 0 → 0 → 0 → 0 (no cambia: ya no cuenta) |
| 20V_2 | 0 / 31 / 409 | 0 → 0 → 0 → 0 (ídem) |
| 304 | 0 / 0 / 1 | 0 → 0 → 0 → 0 |
| los otros 15 | 0 / 0 / 0 | sin cambios |

**En ningún umbral 466 baja a 5.** Sube: 6 → 8 → 12 → 13.

## Por qué: la correlación baja no marca una medición mala, marca la contracción

Mirando dónde caen esos fotogramas en 466 (los 6 eventos por textura están en 14.31, 24.32, 34.18,
34.31, 44.29 y 54.32 s):

| fotograma marcado | respuesta | señal en ese instante | distancia al evento más cercano |
|---|---|---|---|
| 14.143 s | 0.365 | +2.12 px | 0.168 s |
| 24.117 / 24.143 / 24.177 s | 0.46 / 0.37 / 0.29 | +1.93 / +2.33 / +2.31 px | 0.20 / 0.18 / 0.14 s |
| 34.112 / 34.150 / 34.210 s | 0.45 / 0.35 / 0.29 | +2.01 / +2.32 / +2.41 px | 0.07 / 0.03 / 0.03 s |
| 44.112 / 44.185 s | 0.40 / 0.28 | +2.13 / +2.76 px | 0.18 / 0.10 s |
| 54.120 s | 0.36 | +2.52 px | 0.20 s |

**Los diez están adentro de una contracción real**, a 0.03–0.20 s de su pico y con la señal cerca del
máximo (+1.9 a +2.8 px). Uno por contracción, siempre en el tramo rápido. O sea: la correlación de
fase baja **porque el gel se está moviendo rápido**, que es exactamente cuando hay que medir. Marcar
esos fotogramas como sin medida le hace un agujero al medio a cada contracción, y el detector cuenta
los pedazos: por eso el conteo sube en vez de bajar.

Dicho de otro modo: la interpretación del 2026-10-26 era correcta en el **síntoma** (en 466 la
textura se equivoca en el fotograma más rápido) y equivocada en el **remedio**. Tirar el dato no
arregla nada, porque es el dato que importa.

## Dos cosas más que salieron

1. **La respuesta no es comparable entre videos.** La mediana va de 0.295 (068) a 1.18 (20V_1): en
   los de Andrés es mayor que 1 y en 068 es tres veces más baja que en el resto. Cualquier umbral
   tiene que ser relativo al propio video, y aun así 0.7 × mediana marca 409 fotogramas en 20V_2 y
   368 en 068, contra 2 en Video_prueba. **No hay un umbral que signifique lo mismo en todos.**
2. **Video_prueba con 0.7 pasa de 29 a 31 eventos**, por el mismo mecanismo que 466: se parten
   contracciones. Es otra señal de que el umbral alto rompe en vez de limpiar.

## Conclusión de B

1. **No implementar.** La regla no arregla 466 (6 → 8/12/13, nunca 5) y en el mejor de los casos no
   hace nada en los otros 19.
2. **466 por textura se queda como está**, con 6 eventos NO REPORTABLE. Hoy 466 se mide con
   **bordes**, donde da 5 reportables, que es el resultado vigente y no cambia.
3. Si alguna vez hace falta arreglar la textura en el tramo rápido, el camino no es borrar el
   fotograma sino **no dejar que el corrimiento se parta**: por ejemplo medir contra el fotograma de
   reposo en lugar de contra el anterior, o interpolar el corrimiento dentro del evento. Eso es un
   cambio del método, hay que medirlo aparte y hoy no hace falta para ningún resultado.
4. Lo de la medición anterior sigue en pie: en 583, 063 y 268 la textura **no** se equivoca, ve
   movimiento real que los bordes tapan bajo su propio ruido.
