# Ronda 2 — bug de la cintura, y el diagnóstico que faltaba

## Archivos a reemplazar (8)

```
src/preprocessing.py        <- corregido de nuevo (bug de la cintura + pendiente)
src/pipeline.py             <- corregido de nuevo (guarda y_top/y_bottom/center)
src/robust_fitting.py       <- igual que la ronda 1
src/qc_visualization.py     <- igual que la ronda 1
main.py                     <- igual que la ronda 1
scripts/inspect_frame.py    <- igual que la ronda 1
scripts/motion_check.py     <- NUEVO
scripts/signal_check.py     <- NUEVO
```

---

## 1. El hallazgo principal: la señal de grosor del Video_063 no tiene contracciones

No es una cuestión de umbral. Es una propiedad de la distribución, y no
depende de elegir ningún parámetro:

**Una contracción es una excursión hacia ABAJO, y el gel pasa más tiempo
relajado que contraído. Eso deja una cola larga hacia abajo: asimetría
(skew) negativa. El ruido es simétrico: skew ≈ 0.**

Quitando la deriva con una mediana móvil de 2 s (una mediana, no un
pasabanda: un pasabanda convierte cada evento real en un dip flanqueado
por dos picos falsos hacia arriba y destruye justamente la asimetría que
se quiere medir):

| serie | recorrido | ruido | **skew** | % bajo −4σ | % sobre +4σ |
|---|---|---|---|---|---|
| **Video_prueba** (el que funciona) | 1.79 px | 0.114 px | **−2.21** | **3.39%** | 0.10% |
| **Video_063** (ROI 800–1400, deg 2) | 1.20 px | 0.090 px | **+0.28** | 0.22% | 0.33% |

Video_prueba tiene una población clarísima de eventos hacia abajo.
Video_063 sube exactamente tanto como baja: eso es ruido, no contracción.

Para que los números tengan escala, corrí el detector sobre Video_prueba:
**26 eventos, amplitud mediana 1.04 px (0.36% del grosor), intervalo
0.57 s.** En el Video_063 el recorrido TOTAL de la serie es 1.20 px y no
hay ninguna excursión de ese tamaño.

Verificado con videos sintéticos de verdad conocida (renderizado
antialiased, para que el grosor pueda cambiar de a fracciones de píxel):

| video sintético | corr. con el pulso inyectado | skew | veredicto |
|---|---|---|---|
| contracción de grosor de 1.5 px | **−0.976** | **−1.97** | HAY población |
| traslación vertical de 1.5 px | +0.15 | −0.12 | NO hay |
| gel inmóvil | +0.18 | +0.02 | NO hay |

O sea: **−1.97 con contracción real, ≈0 sin ella**. El −2.21 de
Video_prueba y el +0.28 del Video_063 caen justo a cada lado.

### Descartes que hice por el camino

- **No es un ritmo enterrado.** Un primer análisis parecía mostrar un
  pico de 1.00 Hz a 28× el fondo, pero era un artefacto de usar un
  periodograma de una sola realización contra la mediana global del
  espectro. Con Welch promediado (16 g.l.) y fondo LOCAL, ese pico queda
  en **2.4×** — no significativo. No hay ritmo estadísticamente
  detectable, ni en el Video_063 ni en Video_prueba.
- **No es la compresión del mp4.** Comparé el mismo video sintético
  escrito sin pérdidas (FFV1) y comprimido (mp4v): skew −1.97 vs −1.54,
  p2p 1.78 vs 1.66 px. La compresión no borra la señal.
- **No es el ajuste.** En el Video_063 el skew de `residual_top_px`,
  `residual_bottom_px` y `n_outlier_columns` es +0.17, +0.23 y +0.02. Si
  la asimetría fuera un artefacto del ajuste, aparecería ahí.

---

## 2. Bug corregido: la cintura del gel se medía mal

Tu corrida dio `cintura del gel: 111.0 px` cuando el gel mide ~285 px, y
por eso `descartadas por grosor: 1588` y la selección cayó a
`solo_nitidez` (12.63% de variación).

Causa: la cintura era el percentil 5 del perfil de grosor sobre **todas**
las columnas seguidas. El seguimiento llega hasta el borde de la imagen y,
más allá del poste, sigue una hebra fina y desenfocada de 60–110 px. Esa
cola arrastraba el percentil.

Ahora se mide en tres pasos, solo sobre columnas con **ambos bordes
nítidos**: escala = mediana de ahí; se descarta lo que no esté en
[0.6, 1.6]× esa escala; cintura = percentil 5 de lo que queda.

Corrido sobre tu maxProjection real: **cintura = 285.0 px** (correcta), y
la ROI automática pasa a ser **x = 390–1423 (1033 px, 4.91% de
variación)** — la misma calidad que tu 800–1400 manual, pero 1.7× más
ancha y sin tener que elegirla a mano.

**Segundo bug relacionado**: `pendiente_max_en_roi` te daba 1.5 px/px, un
disparate. El grosor de la máscara es entero, así que el perfil avanza a
saltos de 1 px y derivarlo directo da picos espurios en cada escalón. Con
eso el criterio de planitud no se cumplía nunca. Ahora se promedia sobre
una ventana ancha antes de derivar.

### Ahora te muestra las alternativas

En tu video, la cascada da:

```
nivel                 rango x    ancho    variacion
gauge_plana        875-1039        164        0.35%
gauge_cintura      390-1423       1033        4.91%   <-- usada
gauge_relajada     184-1553       1369        9.82%
solo_nitidez       135-1568       1433       12.63%
```

El criterio más estricto (`gauge_plana`) da un tramo perfecto pero de solo
164 px: con 60 columnas ahí quedan a 2.7 px entre sí, comparten el mismo
ruido de imagen y el mismo tile de CLAHE, y el grosor sale **más** ruidoso.
Por eso el ancho mínimo ahora se mide como fracción de las columnas **con
gel** (35% por defecto), no del ancho de la imagen. La tabla se imprime
siempre, así que la decisión —dónde es legítimo medir— queda en tus manos.

---

## 3. `scripts/motion_check.py` — qué se mueve, si no es el grosor

Vos ves contracciones a ojo y la serie de grosor está plana. El grosor es
**ciego** a dos movimientos perfectamente visibles:

- una **traslación vertical** del puente entero (si los dos bordes bajan
  1 px, el grosor no cambia nada);
- un movimiento **axial**, que es lo que esperarías de un tejido que se
  acorta entre anclajes.

Este script mide, en la misma ROI, cuadro a cuadro:

- `mov_gel` / `mov_interior`: |I(t)−I(t−1)| en la zona del gel *con*
  bordes y en el interior *sin* bordes;
- `mov_fondo`: lo mismo en una franja de fondo — el control;
- `desp_vert_px`, `desp_axial_px`: desplazamiento subpíxel por
  correlación cruzada (con guardia: si la correlación no engancha, el
  canal devuelve NaN en vez de un número sin sentido).

La clave está en comparar la **modulación** de |ΔI| contra el fondo, no su
nivel absoluto (el nivel está dominado por el ruido de sensor y da 1.00×
siempre, aunque el gel se esté moviendo muchísimo).

Validado sobre los tres sintéticos:

| video | bordes | interior | veredicto automático |
|---|---|---|---|
| cambio de grosor | **8.3×** | 1.0× | se mueven solo los bordes → el grosor es el observable correcto |
| traslación vertical | 216× | **217×** | se mueve la textura → el grosor es ciego, mirá `desp_vert_px` |
| inmóvil | 0.9× | 1.0× | no hay movimiento sobre el fondo |

**Corré esto sobre el Video_063 antes que cualquier otra cosa.** Tiene
tres respuestas posibles y las tres son útiles:

1. *"no hay movimiento sobre el fondo"* → lo que ves a ojo no está en esa
   zona del gel; habría que mirar los postes o el borde del campo.
2. *"se mueven solo los bordes"* → el grosor es el observable correcto y
   el problema quedó en la medición.
3. *"se mueve la textura"* → hay traslación o movimiento axial, y el
   grosor nunca lo iba a ver. Ahí el observable pasa a ser `desp_vert_px`
   o `desp_axial_px`.

---

## 4. `y_top_px`, `y_bottom_px`, `center_px` en la serie temporal

Cuesta cero y distingue el caso 2 del 3. En los sintéticos:

| video | skew de `thickness_px` | skew de `center_px` |
|---|---|---|
| contracción de grosor | **−1.97** | +0.03 |
| traslación vertical | −0.12 | **−1.93** |

---

## 5. `scripts/signal_check.py` — el test de asimetría

```bash
python scripts/signal_check.py --input data\processed_data\Video_063_CTRL1_5V\serie_temporal.xlsx ^
    --compare data\processed_data\Video_prueba\serie_temporal.xlsx
```

Analiza `thickness_px` y `center_px`, imprime la tabla de arriba, da un
veredicto y guarda `08_asimetria.png` (serie sin deriva + histograma en
log). Es un complemento de la curva de estabilidad, no un reemplazo: la
curva responde "¿el conteo depende del umbral?"; la asimetría responde
"¿hay algo que contar?", que es la pregunta anterior.

---

## Orden sugerido

```bash
# 1. QUE se mueve  <-- primero esto
python scripts\motion_check.py --video data\raw_videos\...\Video_063_CTRL1_5V.mp4 ^
    --output-dir data\processed_data\Video_063_CTRL1_5V

# 2. Reprocesar con la ROI automatica ya corregida (deberia dar 390-1423 solo)
python main.py --video data\raw_videos\...\Video_063_CTRL1_5V.mp4 --plot

# 3. Hay poblacion de eventos, si o no
python scripts\signal_check.py --input data\processed_data\Video_063_CTRL1_5V\serie_temporal.xlsx

# 4. Reprocesar Video_prueba con el codigo nuevo (control positivo, y para
#    comparar el piso de ruido en igualdad de condiciones)
python main.py --video data\raw_videos\Video_prueba.mp4 --plot
python scripts\signal_check.py --input data\processed_data\Video_063_CTRL1_5V\serie_temporal.xlsx ^
    --compare data\processed_data\Video_prueba\serie_temporal.xlsx
```

El paso 4 importa: el `serie_temporal.xlsx` de Video_prueba que me pasaste
está hecho con el código viejo (su MAD cuadro a cuadro es 0.043 px contra
los 0.006 px del Video_063 nuevo), así que ese piso de ruido no es
comparable hasta reprocesarlo.
