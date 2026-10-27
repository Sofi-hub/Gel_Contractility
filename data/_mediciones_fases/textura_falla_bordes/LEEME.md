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
