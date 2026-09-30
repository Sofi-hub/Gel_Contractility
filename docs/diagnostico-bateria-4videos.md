# Diagnóstico conjunto de la batería de 4 videos

Fecha 2026-09-29. Fuente: los `serie_temporal.xlsx` y `contracciones.xlsx` que
ya estaban en `data/processed_data/`, leídos directamente del disco. Se
comparan contra los dos videos validados (Video_prueba y Video_063) como
referencia.

## Veredicto en una línea

**Los tiempos de evento de Video_268 y Video_583 son confiables. Ninguna
métrica de amplitud ni de grosor de los cuatro lo es**, porque la ROI
automática falló en tres de los cuatro. Video_491 no tiene eventos
detectables y no debe reportarse.

## Tabla de aceptación

| chequeo | V268 | V466 | V491 | V583 | (V063 ref) |
|---|---|---|---|---|---|
| **1. ROI: método** | `solo_nitidez` | `franja_completa` | `gauge_cintura` | `gauge_relajada` | `gauge_cintura` |
| **1. ROI: variación** | **13.11 %** ✗ | **164.63 %** ✗✗ | 5.08 % ✓ | **10.83 %** ✗ | ✓ |
| **2. outlier_frac medio** | 5.72 % ✓ | **11.10 %** ✗ | 4.20 % ✓ | 4.37 % ✓ | 7.73 % ✓ |
| **3. meseta con 0 falsos** | 6 en k=6–12 ✓ | 5 en k=8–15 ✓ | **sin meseta** ✗ | 7 en k=10–12 (angosta) | 6 en k=6–8 ✓ |
| **4. enganche de fase** | 5/5, CV 0.0 % ✓ | 4/5, CV 35.8 % ✗ | **sin tren** ✗ | 5/5, CV 0.2 % ✓ | 4/5 ✓ |
| residuo medio borde sup | 1.43 px | **7.00 px** | 0.96 px | 0.96 px | 0.77–0.87 px |

## 1. El problema dominante: la ROI automática no generaliza

De cuatro videos, el detector eligió **cuatro métodos distintos**, y sólo uno
de ellos (`gauge_cintura`, en Video_491) es de los que el protocolo acepta.
`gauge_relajada` ni siquiera figura en el protocolo.

**Video_466 es el caso grave.** El método cayó a `franja_completa`: tomó
x = 71–1920, o sea el ancho entero del cuadro, con 164.63 % de variación de
grosor dentro de la ROI. El residuo del borde superior es 7.00 px contra
0.77–0.87 px de los videos validados: un factor 8. Todo lo que salió de ese
video — amplitud 3.76 px, ruido 0.211 px, adelgazamiento −0.41 px — es el
promedio de un polinomio de grado 2 ajustado sobre un perfil que no es
plano ni de lejos. **No es una medida de contractilidad.**

Video_268 y Video_583 son menos graves: la ROI agarró el hombro de un
anclaje además de la zona plana. Es exactamente lo que el protocolo dice que
significa una variación > 6 %.

Leyendo los perfiles de `00_roi_profile`, las ventanas planas reales están
aproximadamente en:

| video | ROI usada | ROI plana leída del perfil | grosor en la cintura |
|---|---|---|---|
| V268 | 396–917 | **~650–1000** | ~268 px |
| V466 | 71–1920 | **~690–960** | ~205 px |
| V583 | 634–1296 | **~750–1150** | ~245 px |
| V491 | 459–1206 | dejar la automática | ~255 px |

Son valores leídos del gráfico, para confirmar en la corrida.

## 2. Video_491 (36 Hz): no hay eventos detectables

El escaneo de umbral **no tiene meseta**: 15 → 8 → 5 → 3 → 1 → 0, decaimiento
monótono, y los falsos acompañan (12, 5, 2, 2, 0). Los 3 eventos reportados
salieron de k=8, donde `falsos_control` vale **2**. Dos de cada tres son
ruido. Por la regla del propio protocolo, este video no reporta conteo.

Lo que se ve en `09_contracciones`: la señal es ruido de ±0.2 px con dos
excursiones grandes en t ≈ 13 s y t ≈ 34 s, ambas **bifásicas** (sube 0.6 px y
baja a −0.55 px de inmediato). Una contracción no hace eso; un salto de campo
o un glitch de cuadro sí. Coherente con que sea el único video con
`signo = −1` y con un `cociente_adelg_trasl_pct` de 73 % contra 7–19 % de
todos los demás.

**Sobre la hipótesis de tétanos:** la descarté con el espectro. Si hubiera
respuesta a 36 Hz muestreada a ~29.7 fps, aliasaría a ~6 Hz. No hay pico ahí:
la potencia de `center_px` se concentra en 0.35–0.50 Hz y el espectro no tiene
nada en 6 Hz. Tampoco hay meseta sostenida de desplazamiento. Las dos
lecturas posibles son que el gel no respondió, o que respondió con una
contracción sostenida tan suave que queda por debajo de 0.06 px de ruido.

## 3. Hallazgo confirmado: fps real = 30.000

La batería confirma el hallazgo #3 en dos videos más. Fotogramas por período
del estimulador, calculados de la grilla ajustada:

| video | T ajustado | fps declarado | **fotogramas/T** |
|---|---|---|---|
| Video_prueba | 10.09118 s | 29.72893 | **300.000** |
| Video_063 | 10.04357 s | 29.86988 | **300.000** |
| Video_268 | 10.13095 s | 29.61218 | **299.999** |
| Video_583 | 10.10665 s | 29.67354 | **299.900** |
| Video_466 | 9.85635 s | 28.96609 | 285.500 |

**Cuatro videos independientes, con cuatro fps declarados distintos, dan
300.0 fotogramas por período.** Con el estimulador a 0.1 Hz eso fija
fps real = 30.000 y deja el fps declarado como un error del archivo, no del
equipo. El pendiente #3 queda cerrado: hay que reprocesar con `fps = 30`.

Video_466 da 285.5 y no encaja. Pero es el mismo video cuya ROI abarca el
cuadro entero, al que le falta la ranura 3 de la grilla y cuyo CV de
intervalo es 35.8 %. No lo tomaría como contraejemplo hasta reprocesarlo con
la ROI corregida.

## 4. Un bug: el cociente de adelgazamiento pierde el signo

En Video_268 y Video_466 el `adelgazamiento_robusto_px` sale **negativo**
(−0.0815 y −0.4063 px), o sea el gel se **engrosa** después del pico de
traslación, no se adelgaza. Pero `cociente_robusto_pct` los reporta como
**+6.11 %** y **+11.08 %**:

    V268: -0.0815 / 1.3281 = -6.14 %   ->   reportado +6.11 %
    V466: -0.4063 / 3.7639 = -10.79 %  ->   reportado +11.08 %

El cociente está tomando la magnitud y descartando el signo. Un engrosamiento
aparece en la tabla como si fuera un adelgazamiento del mismo tamaño. Hay que
arreglarlo en `contraction_report.py` antes de tabular nada.

El `retardo_adelgazamiento_s` apunta al mismo lado: −0.844 s en V268 y
−0.587 s en V466, contra +0.034 s (un fotograma) en los dos videos validados.
Un retardo negativo de 25 fotogramas significa que el mínimo de grosor cae
**antes** del pico de traslación. Con la ROI rota de esos dos videos no vale
la pena interpretarlo: lo más probable es que se arregle solo al corregir la
ROI. Si sobrevive al reproceso, ahí sí es un problema de alineación de
eventos.

## 5. Menor: `--sep-s` está fusionando picos

`picos_con_sep_menor` aparece en tres de los cuatro: V466 (12), V491 (5),
V583 (12). Según la referencia, ese campo sólo se emite cuando la separación
mínima está fusionando eventos. En V583 se reportan 7 eventos habiendo 12
picos por debajo del límite de separación. Con estimulación a 0.1 Hz sobra
margen, así que conviene mirar si `--sep-s` está calibrado para el régimen
espontáneo de Video_prueba (0.57 s) y no para éste.

## Qué hacer, en orden

1. **Reprocesar los cuatro con `--fps 30`** (o el flag que corresponda) y con
   `--x-start/--x-end` forzados según la tabla de la sección 1. Sin eso no
   hay número de amplitud ni de grosor que se pueda tabular.
2. **Arreglar el signo del cociente** en `contraction_report.py` y volver a
   emitir.
3. **Revisar el detector de ROI.** Que haya elegido cuatro métodos distintos
   en cuatro videos, y que haya caído a `franja_completa` en uno, es el
   síntoma clásico de sobreajuste al video de ejemplo — justo el modo de falla
   que el principio de trabajo del proyecto marca. Como mínimo, el pipeline
   debería **abortar** cuando la variación dentro de la ROI supera el 6 % en
   vez de seguir y emitir números.
4. **Video_491 sale del conteo.** Se reporta como "sin eventos detectables",
   con el escaneo de umbral como evidencia.
5. Recién después, la tabla comparativa de métricas entre videos.

## Lo que sí quedó en pie

- El canal de detección: `center_px` sigue siendo el bueno. En los cuatro
  videos el ruido del grosor es ~1.6–2× el del centro
  (V268 0.188/0.098, V466 0.333/0.211, V491 0.102/0.063, V583 0.151/0.076).
- El enganche de fase funciona sin retoques en los videos con ROI decente:
  V268 5/5 ranuras con error 0.0000 s, V583 5/5 con |error| < 24 ms.
- El control de falsos sobre señal invertida hizo exactamente su trabajo: es
  lo que detectó que Video_491 no tiene señal. Sin ese control, se habrían
  reportado 3 contracciones.
