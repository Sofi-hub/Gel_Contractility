# Métricas de cinética de contracción (TTP, RT50): viabilidad

Fecha 2026-09-30. Evaluación del pedido del equipo de portar las métricas del
script `Contraction_Analysis.mlx` (Andrés Felipe Zemanate-Largo) al pipeline.

## Qué pide el script

Lee un `contraction.txt`, detecta picos, estima una línea de base con mediana
móvil, busca el inicio (onset) y el fin (offset) de cada evento cruzando esa
base, y calcula seis métricas por contracción:

| métrica | qué es |
|---|---|
| `Peak_Time` | instante del pico |
| `Peak_Amplitude` | pico menos base en el onset |
| `Relative_Amplitude_Change` | lo anterior en % |
| `Time_to_Peak` (TTP) | del onset al pico |
| `Half_Relax_Time` (RT50) | decaimiento al 50 % del pico |
| `Peak_to_Peak_Time` (P2P) | entre picos consecutivos |

Los dos papers respaldan TTP y RT50 como los descriptores estándar de
cinética de contracción (eLife, pág. 5: "Time to peak (TTP) and half-
relaxation time (RT50) can also be calculated from contraction profiles").

## Veredicto

**Factible, y tres de las seis ya las tenemos.** `Peak_Time`,
`Peak_Amplitude` y `P2P` salen hoy de `contracciones_<video>.xlsx`. Faltan onset,
offset, TTP y RT50, que son ~40 líneas sobre la detección de eventos que ya
está validada.

Pero hay tres cosas que hay que resolver antes, y la primera puede invalidar
el pedido para la mitad de los videos.

---

## Duda 1 (la seria): a 30 fps, TTP y RT50 no son medibles en todos los videos

Medido sobre el promedio de eventos alineados de cada video, que es el mejor
SNR posible (ruido del promedio 0.03 px):

| video | amplitud | TTP | RT50 | subida 10–90 % |
|---|---|---|---|---|
| Video_prueba | 6.14 px | 67 ms (**2 fotogramas**) | 67 ms (2 fr) | 33 ms (**1 fr**) |
| Video_063 | 1.49 px | 67 ms (**2 fotogramas**) | 67 ms (2 fr) | 33 ms (**1 fr**) |
| Video_268 | 1.55 px | 67 ms (**2 fotogramas**) | 67 ms (2 fr) | 33 ms (**1 fr**) |
| Video_466 | 4.33 px | 300 ms (9 fr) | 167 ms (5 fr) | 100 ms (3 fr) |
| Video_583 | 3.07 px | 300 ms (9 fr) | 200 ms (6 fr) | 133 ms (4 fr) |

La forma cruda del evento promedio lo muestra sin ambigüedad. Video_prueba,
en múltiplos del ruido del promedio:

    fotograma:  -3   -2   -1    0   +1   +2   +3   +4
    señal:      -0    1  147  190  146   77   31   10

Pasa de ruido a 147 sigma **en un fotograma**. La contracción entera dura
cuatro. Ahí no hay TTP que medir: lo que se reportaría es el intervalo de
muestreo, no la biología.

Video_583, en cambio:

    fotograma:  -8   -7   -6   -5   -4   -3   -2   -1    0   +1   +2   +3
    señal:      12   44   69   82   91   99  100  102  104  100   91   83

Sube en ocho fotogramas, hace meseta y baja. Acá TTP y RT50 sí significan
algo.

**Interpretación.** No es un defecto del pipeline: es que el twitch de
músculo esquelético tiene un TTP típico de 30–80 ms y la cámara muestrea cada
33 ms. En Video_466 y Video_583 la respuesta es mucho más lenta (300 ms, con
meseta), compatible con una respuesta fusionada o con la mecánica del gel más
que con el twitch.

Eso no es un problema a esconder, es un **resultado**: la cinética difiere
entre muestras, y en las rápidas sólo se puede afirmar "TTP < 100 ms" (ver
la corrección en "Implementación"). Lo que
no se puede hacer es tabular 67 ms como si fuera una medición y comparar
muestras con ese número.

**Para medir TTP de un twitch hacen falta ~10 muestras en la subida, o sea
200–300 fps.** Es una decisión de adquisición, no de código.

---

## Duda 2: el script tiene cuatro errores que no conviene heredar

Portarlo literal arrastraría estos:

**a) `Half_Relax_Time` no calcula RT50.** El código hace

    Half_Relax_Time(i) = (Time(Off) - Time(P)) * 0.5;

que es *la mitad de la duración total de la relajación*, no el tiempo hasta
caer al 50 % de la amplitud. La descripción del propio script dice lo
segundo. Son cantidades distintas y sólo coinciden si la relajación es
perfectamente lineal.

**b) `Relative_Amplitude_Change` divide por un número que oscila alrededor de
cero.**

    Peak_Change(i) = (Amplitude_Detrend(P) - Amplitude_Detrend(On)) / Amplitude_Detrend(On)

`Amplitude_Detrend` es la señal ya centrada en cero, así que el denominador
en el onset es ruido. El porcentaje sale inestable y a veces enorme. Debería
dividir por la línea de base **cruda**, `Amplitude(On)`.

**c) `Idx_Before = Idx_Before - 5`.** Corre todos los onsets 5 muestras hacia
atrás, sin justificación en el código ni en la descripción. A 30 fps son
167 ms sumados a todos los TTP. En Video_583, cuyo TTP real es 300 ms, eso
es un sesgo del 55 %.

**d) `Min_Peak_Distance = 520` hardcodeado**, con la versión paramétrica
comentada justo arriba. A 30 fps son 17.3 s de separación mínima: con
estimulación a 0.1 Hz fusionaría latidos. Es exactamente el modo de falla que
este proyecto viene corrigiendo.

---

## Duda 3: corre sobre la salida de MuscleMotion

El script lee `contraction.txt`, que es la señal de MuscleMotion. Ya medimos
(`docs/base-de-tiempo-y-frames-perdidos.md`) que su eje temporal está
comprimido entre 0.65 % y 4.05 % según el archivo, porque ImageJ importa
menos fotogramas que OpenCV. Cualquier TTP o RT50 calculado sobre esa señal
hereda ese error, y el error **cambia de video a video**, así que no se
cancela al comparar muestras.

Calculando sobre `center_px` el problema desaparece.

---

## Propuesta

1. **Implementar onset/offset, TTP, RT50 y amplitud relativa** sobre nuestra
   detección de eventos ya validada. Sale en `contracciones_<video>.xlsx` junto al
   resto.
2. **Definir RT50 como manda el paper** (caída al 50 % de la amplitud), no
   como la mitad de la duración. Si el equipo quiere la métrica del script
   para comparar con resultados viejos, se puede emitir también, con otro
   nombre y aclarando qué es cada una.
3. **Marcar cada métrica como no reportable cuando el evento dura menos de N
   fotogramas** (sugiero N = 5 para TTP, que da 20 % de error de
   cuantización). Mismo criterio que usamos con la meseta del umbral: mejor
   decir "no medible" que publicar el intervalo de muestreo.
4. **Emitir un intervalo, no un punto**, cuando el evento está poco
   muestreado: "TTP < 100 ms" en vez de "TTP = 67 ms".
5. **Plantearle al equipo la adquisición a alta velocidad.** Con 200–300 fps
   en un subconjunto de muestras, TTP y RT50 pasan a ser medibles de verdad,
   y de paso se podría calibrar cuánto sesga el submuestreo a 30 fps.

## Lo que NO cambia

Estas métricas son temporales o relativas, así que **no necesitan calibración
de píxeles a milímetros**. TTP, RT50 y P2P están en segundos; la amplitud
relativa está en porcentaje. La única que queda en píxeles es la amplitud
absoluta, que ya reportamos así. La decisión de no calibrar sigue en pie.

Ojo con una cosa distinta: los papers (sobre todo el de eLife) discuten
**fuerza contráctil normalizada por área de sección**, que sí requiere
calibración y un modelo mecánico del gel. Eso es otro pedido, mucho más
grande, y conviene no confundirlo con este.

---

## Implementación (2026-09-29)

Hecha en `src/cinetica.py`, llamada desde `scripts/contraction_report.py`.
Puntos 1 a 4 de la propuesta; el 5 (adquisición rápida) sigue pendiente y es
del equipo.

**Definiciones.** Sobre `center_px` sin deriva, con la amplitud `A` igual a
la `amplitud_px` que ya se reportaba. Onset y offset: cruces del 10 % de `A`.
TTP: onset → pico. RT50: pico → cruce del 50 % de `A` (la del paper, no la del
script). Amplitud relativa: `A` / **grosor en reposo**, no / valor crudo del
canal: el crudo de `center_px` es una fila de la imagen y no significa nada.
Sin el corrimiento de −5 muestras ni la distancia mínima fija del script.

**Corrección a lo escrito arriba: la cota es 100 ms, no 67 ms.** El pico
muestreado no es el pico verdadero: éste puede caer hasta un fotograma
después. Con el onset entre los fotogramas −2 y −1, el TTP verdadero está en
(0, 3 fotogramas) = (0, 100 ms). La tabla de arriba medía sobre la muestra y
subestimaba la incertidumbre.

**Hallazgo nuevo: el pico de las muestras lentas es una meseta.** En
Video_466 y Video_583 hay 4–5 fotogramas entre el 96 y el 100 % de `A`,
indistinguibles dentro del ruido. El instante del pico queda indeterminado
en ±2 fotogramas, y eso ensancha el intervalo de TTP y RT50 de cada evento
(p. ej. 583: TTP 258 ms con intervalo [129, 335] ms). No es un defecto del
método: "tiempo al pico" está mal definido cuando el pico es plano. El
**onset**, en cambio, está bien definido: en Video_583 cae a 10.995, 20.999,
30.997, 41.000, 50.996 y 60.998 s, enganchado al estimulador con ~2 ms de
dispersión, mientras que los picos se dispersan ±35 ms.

**Resultados sobre los seis videos:**

| video | TTP | RT50 | fotogramas (subida / bajada 50 %) | amplitud relativa |
|---|---|---|---|---|
| Video_prueba | **< 102 ms** (no medible) | **< 103 ms** | 2 / 2 | 0.71 % → **2.31 %** (Fase 3) |
| Video_063 | **< 100 ms** (no medible) | **< 99 ms** | 2 / 2 | 0.53 % → 0.54 % (Fase 3) |
| Video_268 | **< 101 ms** (no medible) | **< 100 ms** | 2 / 2 | 0.57 % |
| Video_466 | 284 ms [137, 365] | 160 ms [70, 260] | 9 / 5 | 2.13 % |
| Video_583 | 258 ms [129, 335] | 181 ms [99, 301] | 8 / 6 | 1.31 % |
| Video_491 | ~~no reportable~~ desde la Fase 2.2: **570 ms** | **467 ms** | 17.5 / 14.5 | 0.40 % |

**Fase 3 (2026-10-07): resumen por grupo y "reportable" por eventos medibles.**
Las cifras del resumen son ahora las de los **estimulados** si hay tren (antes,
todos los eventos mezclados: la amplitud relativa de Video_prueba, 0.71 %, era
la de sus 22 espontáneas; la de las estimuladas es 2.31 %). La hoja
`cin_grupos_*` tiene todos, estimulados y espontáneos. La mediana de TTP y RT50
usa **solo los eventos medibles** (≥ 5 fotogramas), y la métrica es reportable
si lo es al menos la mitad. En Video_466 el RT50 queda en 160 ms con 4 de 5
eventos medibles; en los demás no cambia ningún valor.

Video_491 se agregó el 2026-10-01: con la ventana automática del detrend (3.1 s) sus dos
eventos de ~1 s se detectan enteros. Son distintos de los demás (más largos y en sentido
contrario); ver `CLAUDE.md`, límites conocidos.

Los valores de 466 y 583 son medianas por evento; entre corchetes, la mediana
del intervalo [min, max]. Concuerdan con la medición sobre el promedio de
eventos de la tabla de arriba (300/167 y 300/200 ms).

**Verificación.**
- Regresión: en los seis videos, todas las hojas y columnas que ya existían en
  `contracciones_<video>.xlsx` dan exactamente lo mismo; la cinética sólo agrega.
- `tests/test_seleccion_k.py`: 10/10.
- `tests/test_cinetica.py` (nuevo), con eventos sintéticos de cinética
  conocida muestreados a 30 fps con fase aleatoria y ruido: evento lento (TTP
  270 ms), error de la mediana 0.05 fotogramas en TTP y 0.18 en RT50;
  twitch (TTP 36 ms), declarado no medible con valor NaN. En los dos casos el
  intervalo [min, max] contiene al valor verdadero en 319 de 320 eventos.
