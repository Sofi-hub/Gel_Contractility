# Separación de contracciones estimuladas vs espontáneas

`src/rhythm_split.py`, llamado desde `contraction_report.py`. Validado sobre seis videos.

> **Actualizado 2026-10-07 (Fase 3, grupo 1).** Cambió dónde se busca el tren (dirigido por la
> frecuencia configurada), qué instante representa a cada latido (el inicio, no el pico), cómo se
> calcula el p-valor y cuándo la amplitud puede intervenir. Los números de abajo son los nuevos.
> Propuesta y mediciones: `docs/historia/propuesta-fase-3-ritmo-cinetica.md`.

## El criterio: enganche de fase

No se usa la amplitud para clasificar (con estimulación débil los grupos se solapan) ni la ventana
temporal (las espontáneas siguen apareciendo durante el tren). Se usa la única propiedad que define
a una contracción estimulada y no depende del montaje: **está enganchada en fase a un reloj
periódico**. El estimulador dispara en `t = fase + n·T`; las espontáneas no saben nada de ese reloj.

El algoritmo busca la grilla `(T, fase)` que mejor explica un subconjunto de los eventos, y llama
espontáneo a lo que quede afuera.

## Dónde se busca el tren

| | con `--frecuencia-estimulo` | sin ella |
|---|---|---|
| búsqueda | **dirigida**: solo entre 0.9 y 1.1 veces el período configurado | **libre**: de 0.3 s a ~1/3 del registro |
| cuántos trenes | uno por frecuencia configurada | uno |
| veredicto | "enganchado a la frecuencia configurada (0.1 Hz)" o "se buscó a 0.1 Hz: no hay enganche" | "tren periódico a X Hz, no se configuró ninguna frecuencia" |

La pregunta del experimento es **"¿el estimulador capturó a las células?"**: es una pregunta sobre
una frecuencia conocida, y la búsqueda dirigida la responde con más poder (ver abajo por qué). Si el
protocolo cambia de frecuencia a mitad del video, se pasan todas: `--frecuencia-estimulo 0.1 0.2`.
Si se busca a una frecuencia y aparece un tren a otra muy distinta (> 5 % y fuera del error), sus
eventos quedan como espontáneos.

**Las espontáneas no se buscan como tren.** No siguen un reloj (en Video_prueba los intervalos
varían un 91 %), así que se describen por la mediana, el rango intercuartil y la frecuencia
**evento a evento** de sus intervalos (hoja `espont_*`). Nunca como un solo número.

## El instante de cada latido: su inicio

Se usa el **inicio** de la contracción (cruce del 10 % de la amplitud, interpolado entre fotogramas;
el mismo `onset_s` de la cinética), no el pico. En los eventos lentos el pico es una meseta de 3–6
fotogramas casi iguales y cuál queda como máximo lo decide el ruido: el desvío de los latidos
respecto del tren era de ±40 ms en Video_466 y 583 con el pico, y es de 17 y 10 ms con el inicio. Si
un evento no tiene inicio medible (hueco, o no cruza el 10 % antes del pico vecino), se usa su pico.

## El p-valor: listas de instantes al azar

El buscador **siempre** encuentra algún tren: entre 29 instantes cualesquiera hay algún ritmo en el
que 5 o 6 caen alineados. La pregunta es si el tren del video es mejor que lo que arma el azar. Se
responde en cada corrida, en memoria (no se guarda nada):

1. Se cuenta cuántos eventos tiene el video y en qué tramo están (por ejemplo, 29 entre 0 y 70 s).
2. Se sortean esos 29 instantes al azar en el mismo tramo, sin ningún reloj detrás (respetando el
   intervalo mínimo observado entre eventos, para no generar ráfagas imposibles), y se les corre
   **la misma búsqueda**. Sale el puntaje `z` del mejor tren que se pudo armar.
3. Se repite **1000 veces**. Así se ve qué puntajes produce el azar solo.
4. p = fracción de listas al azar con `z` mayor o igual que el del video (estimador (k+1)/(n+1):
   el mínimo es 1/1001 ≈ 0.001). Se exige **p ≤ 0.01**.

La semilla del sorteo es fija: dos corridas sobre el mismo video dan exactamente lo mismo.

**Por qué la búsqueda dirigida tiene más poder.** A las listas al azar se les aplica la misma
búsqueda que al video. Si se prueban todos los períodos posibles, el azar tiene miles de intentos y
arma trenes que puntúan casi como uno real; si se prueba solo cerca de 10 s, tiene pocos. Las dos
comparaciones son justas, pero la dirigida le hace al azar una pregunta más difícil. Medido sobre
series sintéticas con espontáneas a ~0.3 por segundo y 6 latidos estimulados: la búsqueda libre no
confirmaba el tren en 6 de 20 series, la dirigida en 0 de 20; y en 25 series de solo espontáneas
(los intervalos reales de Video_prueba, barajados) la dirigida no inventó ningún tren.

Antes (hasta la Fase 2) se comparaba el `z` final del video, medido con una tolerancia más estrecha,
contra el `z` de búsqueda de las listas al azar: no eran comparables y el p salía optimista. Además
se exigían 6 eventos (con 4–5 el tren se aceptaba sin prueba: Video_466) y 200 simulaciones (p mínimo
0.005: cuatro de los cinco videos daban exactamente eso).

## Cuándo interviene la amplitud

**Nunca sola.** Entra solo junto con un desvío de tiempo, en dos reglas:

- **R5, sacar un latido del tren:** si se desvía de su ranura **más de 1 fotograma** (medido contra
  el tren ajustado sin él) **y** su amplitud está fuera de 0.5–2× la mediana de los demás
  estimulados. Ninguna de las dos alcanza sola: el tiempo solo expulsaba latidos reales de
  Video_466 (su jitter genuino es de 17 ms); la amplitud sola sería clasificar por amplitud. En los
  seis videos solo lo cumple el evento de 4.82 s de Video_prueba (−58 ms; 2.10 px contra 6.8 px del
  tren). Se lista en la hoja `sacados_*`.
- **R6, rescatar un dudoso:** un latido cuyo instante se corrió más que la tolerancia (hasta ±10 % de
  T) se reporta aparte como `estimulados_dudosos`, sin entrar en el ajuste del período, **solo si**
  cae entre la primera y la última ranura del tren y su amplitud es compatible (0.5–2×). Antes se
  buscaba en cualquier ranura del video y volvía a traer como dudosa la espontánea de 4.82 s, 10 s
  antes del tren.

## Si falla un pulso

- **Uno del medio** (por ejemplo, por fatiga): con 5 de 6 ranuras el tren se detecta igual y la hoja
  `grilla_*` marca esa ranura como `capturada = False`.
- **Dos de seis:** la captura es 4/6 = 67 %, menos que el 75 % de `min_captura`, y no hay tren.
  Bajando `--min-captura` aparece el intento, pero 4 latidos entre espontáneas no siempre alcanzan
  para p ≤ 0.01: el límite es de evidencia, no solo de la regla.
- **Los últimos:** el tren termina antes, sin penalidad (la captura se cuenta entre el primer y el
  último latido capturado).

Los tres casos están fijados en `tests/test_ritmo.py`.

## Resultados (Fase 3)

| video | período | vs 0.1 Hz | jitter | captura | p |
|---|---|---|---|---|---|
| Video_prueba | 10.00043 ± 0.00230 s | indistinguible | 9.6 ms | 6/6 | 0.001 |
| Video_063 | 10.00190 ± 0.00304 s | indistinguible | 9.6 ms | 5/5 | 0.001 |
| Video_268 | 10.00132 ± 0.00230 s | indistinguible | 9.6 ms | 6/6 | 0.001 |
| Video_466 | 10.00224 ± 0.00693 s | indistinguible | 17.0 ms | 5/5 | 0.001 |
| Video_583 | 10.00024 ± 0.00230 s | indistinguible | 9.6 ms | 6/6 | 0.001 |

9.6 ms es el piso de la resolución (1 fotograma / √12). Antes de la Fase 3 Video_prueba tenía 7
estimulados (incluía el de 4.82 s) y período 10.00744 ± 0.00408 s; ahora 6 estimulados y 23
espontáneas (intervalo mediano 0.568 s, CV 91 %). Video_491 tiene 2 eventos: no alcanza para buscar
un tren.

## Cómo se elige el tren entre los candidatos

- **Puntaje:** `z = (ranuras ocupadas − esperado) / √varianza`, con el esperado calculado a partir de
  la densidad de eventos en el tramo del tren. Una ranura está ocupada si hay un evento a menos de 2
  fotogramas.
- **Armónicos.** Si el período real es T, la grilla de T/2 también contiene todos los latidos
  verdaderos pero con la mitad de las ranuras vacías. Se exige `min_captura` (75 %), y gana el mejor
  puntaje salvo que un candidato casi igual de bueno sea múltiplo ×2 o ×3 del ganador. (Antes ganaba
  "el período más largo" entre los casi mejores, y con espontáneas densas eso empujaba al borde del
  rango.) En la búsqueda dirigida no hay armónicos posibles.
- **Grilla fina.** El paso entre períodos candidatos se ajusta a la tolerancia, para que en el
  extremo del registro ninguna ranura se corra más de media tolerancia.
- **Intrusos con brazo de palanca.** Un espontáneo tomado como primera ranura movía el período y
  repartía su error entre todos los residuos. Se ajusta primero con **Theil-Sen** y recién al final
  por mínimos cuadrados sobre el conjunto limpio.
- **Error estándar cero.** El tren cae siempre en el mismo número de fotogramas y los residuos daban
  0. Se pone como piso el error de cuantización, `resolución/√12`.

## Interacción con la elección de k

`rhythm_split` es sensible a eventos espurios: un par de detecciones de ruido ensucian el ajuste lo
suficiente como para que no encuentre el tren (Video_583 con el viejo `k=8`). Por eso la elección de
`k` es automática y sale de la meseta.

## Salidas

`10_ritmo_*.png` (eventos coloreados por grupo, grilla marcada y el desvío de cada latido en ms) y,
en `contracciones.xlsx`: `trenes_*` (cada búsqueda con su veredicto, z, p, captura), `ritmo_*`
(resumen por grupo), `grilla_*`, `sacados_*` (R5), `dudosos_*` (R6) y `espont_*`.

## Limitaciones conocidas

- Necesita al menos 4 latidos estimulados y el 75 % de las ranuras ocupadas entre el primero y el
  último.
- Sin frecuencia configurada, una serie espontánea **muy** regular es indistinguible de una
  estimulada por los tiempos solos: por eso el veredicto aclara que no se configuró ninguna
  frecuencia. (En Video_prueba, la ráfaga espontánea late cada ~0.56 s con bastante regularidad.)
- Con actividad espontánea muy densa (~1 por segundo) y solo 6 latidos estimulados, ni la búsqueda
  dirigida alcanza a probar el tren: el azar arma trenes igual de buenos (medido: 17 de 20 series
  sin tren). Es un límite de evidencia.
- Un espontáneo puede caer dentro de una ranura por azar; si su amplitud es compatible con la del
  tren, nada lo distingue.
