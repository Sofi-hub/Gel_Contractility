# Fase 3 (grupo 1): ritmo y cinética — propuesta medida

2026-10-01, chat de implementación. **APLICADA el 2026-10-07, con un cambio en la búsqueda del
tren** (ver "Cómo quedó" al final). Cubre H36, H37, H38 (ritmo) y H40,
H41, H43 (cinética) de `hallazgos-revision-codigo.md`. Todo medido con el código de la Fase 2.2
sobre los seis videos vigentes y sobre series sintéticas; experimentos en copias, sin tocar el
código del proyecto.

---

## Ritmo: la separación de estimuladas y espontáneas

### Lo que se encontró al medir

**1. El instante de un evento lento está mal definido por su pico.** En Video_466 y 583 los
latidos estimulados se desvían ±40 ms de su ranura; en los videos de eventos rápidos, < 1 ms.
La causa es la meseta del pico (3–6 fotogramas casi iguales): cuál queda como máximo lo decide el
ruido. El **inicio** de la contracción (cruce del 10 %, interpolado) está bien definido:

| video | jitter con el pico | jitter con el inicio | período con el pico | período con el inicio |
|---|---|---|---|---|
| Video_prueba | 20.9 ms | 19.7 ms | 10.00744 ± 0.00408 | 10.00661 ± 0.00358 |
| Video_063 | 9.6 ms | 9.6 ms | 9.99917 ± 0.00304 | 10.00190 ± 0.00304 |
| Video_268 | 9.6 ms | 9.6 ms | 9.99990 ± 0.00230 | 10.00132 ± 0.00230 |
| Video_466 | 35.1 ms | **17.0 ms** | 9.99433 ± 0.01197 | 10.00224 ± **0.00693** |
| Video_583 | 25.4 ms | **9.6 ms** | 10.00119 ± 0.00675 | 10.00024 ± **0.00230** |

(9.6 ms es el piso de la resolución: 1 fotograma / √12.)

**2. H36: el primer "estimulado" de Video_prueba es una espontánea.** Medidos por su inicio, los
otros seis caen a 14.875, 24.876, 34.876, 44.876, 54.880 y 64.875 s (cada 10.000 s). El de 4.82 s
cae 58 ms antes de su ranura y mide 2.10 px, como las espontáneas (1.30–2.52 px), no como los
estimulados (6.6–7.0 px). Con la actividad espontánea de ese tramo, una espontánea cae dentro de la
tolerancia de una ranura el 17 % de las veces. Entra porque la tolerancia tiene un piso de 2
fotogramas (67 ms). Bajar el piso a 1 fotograma lo saca, pero en Video_466 expulsa además a un
estimulado real (su jitter genuino es de 17 ms). **El tiempo solo no alcanza para decidirlo.**

**3. H37: el rescate de "dudosos" busca fuera del tren.** Con el de 4.82 s fuera de los
estimulados, el rescate (±1 s de cualquier ranura entre el primer y el último evento del video) lo
vuelve a traer como "dudoso", aunque su ranura queda 10 s antes del primer latido del tren.

**4. H38: sin la frecuencia del estimulador, el ritmo espontáneo se confunde con un tren.** Con
las 22 espontáneas reales de Video_prueba (intervalos barajados, sin estimulador), la búsqueda libre
declara "tren" en **3 de 25** series, con T = 0.54–1.13 s. Buscando solo cerca de la frecuencia
configurada (9–11 s para 0.1 Hz): **0 de 25**. Hoy `--frecuencia-estimulo` solo se usa para comparar
al final, no para buscar.

**5. H38: con actividad espontánea densa el buscador arma trenes falsos.** Seis estimulados más
espontáneas a ~1 por segundo (sintético, 60 series, 360 latidos estimulados):

| variante | jitter 5 ms | 15 ms | 30 ms |
|---|---|---|---|
| actual (búsqueda 9–11 s, "el período más largo", tolerancia 3 fotogramas) | 165 perdidos | 171 | 190 |
| + elegir el mejor puntaje, no el más largo | 75 | 76 | 86 |
| + tolerancia de búsqueda de 2 fotogramas | **33** | **41** | **51** |
| + tolerancia de 1 fotograma | 5 | 6 | 102 |

La regla "el período más largo" existe para no confundir T con T/2 en la búsqueda libre; con la
búsqueda restringida a ±10 % de T no hay armónicos posibles y empuja hacia el borde (T = 10.96 s).
**En los cinco videos reales ninguna variante cambia el resultado.**

**6. H38: con 4–5 eventos no hay prueba de significancia.** Hoy el Monte Carlo exige 6 eventos; con
menos, `p = NaN` y el tren se acepta sin prueba (Video_466). Corrido con 5 eventos: p = 0.001 con
1000 simulaciones (3 s). Con 200 simulaciones el p mínimo es 0.005, que es lo que dan cuatro de los
cinco videos: no dice cuán fuerte es la evidencia.

### Propuesta (ritmo)

- **R1.** El enganche de fase se mide sobre el **inicio** de cada contracción (el mismo cruce del
  10 % de la cinética), no sobre el pico. Si un evento no tiene inicio medible, se usa su pico.
- **R2.** Con `--frecuencia-estimulo`, la búsqueda se restringe a ±10 % del período configurado y
  gana el **mejor puntaje**. Sin ella, la búsqueda sigue libre y el reporte aclara que un tren
  encontrado puede ser actividad espontánea regular.
- **R3.** Tolerancia de la búsqueda: **2 fotogramas** (antes 3).
- **R4.** Monte Carlo desde 4 eventos, con **1000** simulaciones, comparando el mismo estadístico
  que el nulo (el z de la búsqueda).
- **R5 (H36).** Un estimulado pasa a espontáneo solo si se cumplen **las dos** cosas: se desvía de
  su ranura más de 1 fotograma **y** su amplitud está fuera de 0.5–2× la mediana de los demás
  estimulados. Ni el tiempo solo ni la amplitud sola alcanzan: el tiempo solo expulsa latidos reales
  de Video_466, y la amplitud sola violaría el principio de no clasificar por amplitud. Solo lo cumple
  el de 4.82 s de Video_prueba; su período pasa de 10.00661 a **10.00043 ± 0.00230 s**.
- **R6 (H37).** El rescate de "dudosos" solo entre la primera y la última ranura capturada del tren,
  y con amplitud compatible (0.5–2× la mediana de los estimulados).

**Efecto esperado en los videos vigentes:** Video_prueba, 6 estimulados y 23 espontáneas (antes 7 y
22), período 10.00043 s. En los otros cuatro, los mismos estimulados; cambian los períodos en el
tercer o cuarto decimal (por el inicio en vez del pico), dentro de su error, y 466 pasa a tener p.

---

## Cinética

### Lo que se encontró al medir

**7. H40: el resumen mezcla los dos grupos.** Amplitud relativa de Video_prueba: 0.71 % en el
resumen = la de las 22 espontáneas (0.70 %); las 7 estimuladas dan **2.29 %**. En los otros videos
casi todo es estimulado y no cambia.

**8. H41: lo que ensancha los intervalos es la meseta del pico, no el muestreo.** Fotogramas del
pico indistinguibles del máximo: 3–6 en 466 y 583, **18–19** en 491. El TTP y el RT50 se miden contra
un máximo cuya posición la decide el ruido: en 491 el RT50 puede valer entre 0 y 667 ms. Además, en
466 el RT50 de un evento tiene 4 fotogramas ("no medible") y entra igual en la mediana.

**9. Métricas por cruces de nivel.** Se miden entre instantes en que la señal cruza un nivel, que se
interpolan y no dependen de dónde cayó el ruido en la cima:

| video | TTP / RT50 actuales (dispersión entre eventos) | subida 10–90 % | meseta > 90 % | RT50 desde el fin de la meseta |
|---|---|---|---|---|
| Video_466 | 284 (45) / 160 (22) ms | 183 (38) ms, 5 fr | 134 (45) ms | 108 (33) ms, 4 fr |
| Video_583 | 258 (22) / 181 (25) ms | 146 (19) ms, 4.5 fr | 182 (17) ms | **110 (4) ms**, 4 fr |
| Video_491 | 570 (13) / 467 (14) ms | 435 (35) ms, 13 fr | 586 (32) ms | **15 (2) ms, 1 fr** |
| Video_063 | 38 (6) / 50 (4) ms | 35 ms, 1 fr | 16 ms | 37 ms, 2 fr |

Para 583, el RT50 desde el fin de la meseta es mucho más consistente (4 ms de dispersión contra 25).
Pero estas métricas son más cortas, así que más eventos quedan por debajo de 5 fotogramas.
**Video_491:** sube en ~435 ms, se sostiene ~590 ms y **cae en menos de un fotograma**, con un rebote.
Una relajación tras un tétanos suele ser más lenta que la contracción; una caída instantánea es otro
rasgo raro de ese video, para consultar con el equipo.

### Propuesta (cinética)

- **C1 (H40).** Resumen **por grupo**: estimulados y espontáneos por separado, además de todos. Si
  hay tren, la cifra principal es la de los estimulados.
- **C2 (H41).** Solo los eventos **medibles** (≥ 5 fotogramas) entran en la mediana, y la métrica es
  reportable si lo es al menos la mitad de los eventos. En 466 el RT50 sigue siendo reportable (4 de
  5 medibles; mediana 160 ms).
- **C3 (H41), a decidir.** Agregar las métricas por cruces de nivel (subida 10–90 %, meseta > 90 %,
  RT50 desde el fin de la meseta), con la misma regla de ≥ 5 fotogramas, y marcar "pico en meseta"
  cuando el máximo se reparte en ≥ 3 fotogramas. El TTP y el RT50 actuales se mantienen porque son los
  que usa la literatura (eLife); las nuevas son el complemento que no depende del ruido en la cima.
- **C4 (H43).** Pruebas de la cinética con eventos con meseta, ruido y dos grupos.

---

## Cómo quedó al aplicarla (2026-10-07)

**Un cambio respecto de la propuesta: la búsqueda del tren.** La propuesta R2 decía "con
frecuencia configurada, búsqueda a ±10 %". En la discusión se pasó a "la frecuencia no restringe la
búsqueda, solo el veredicto", con búsqueda libre de varios trenes. Al medirlo apareció el costo: el
p-valor compara contra listas de instantes al azar a las que se les corre la misma búsqueda, y si se
prueban todos los períodos el azar arma trenes casi tan buenos como el real. Series sintéticas con
espontáneas a ~0.3/s y 6 latidos estimulados (20 series, 120 latidos, jitter 15 ms, Monte Carlo
activo):

| variante | latidos perdidos | series sin tren |
|---|---|---|
| código anterior | 66 | 11 |
| nuevo, solo búsqueda libre | 36 | 6 |
| nuevo, búsqueda dirigida | **0** | **0** |

Con solo espontáneas (intervalos reales de Video_prueba barajados, 25 series), el código anterior
declaraba "tren estimulado" en 4; el nuevo, en 0 (libre o dirigido). Con espontáneas a ~1/s (límite
de evidencia) ninguna variante prueba el tren: el código anterior y la búsqueda libre, 0 de 20; la
dirigida, 3 de 20.

Franco definió el objetivo: encontrar el tren estimulado si el estimulador capturó, y dar una
frecuencia aproximada de las espontáneas. Quedó así:

- **Con `--frecuencia-estimulo`** (una o varias): un tren por frecuencia, buscado solo a ±10 %. Veredicto
  "enganchado a la frecuencia configurada" o "se buscó a X Hz: no hay enganche".
- **Sin frecuencia:** búsqueda libre de **un** tren; veredicto "tren periódico a X Hz, no se configuró
  ninguna frecuencia" (texto elegido por Franco).
- **Espontáneas:** no se buscan como tren; mediana, rango y frecuencia evento a evento (como antes).

Lo demás, como se propuso: R1 (inicio), R3 (2 fotogramas), R4 (Monte Carlo desde 4 eventos, 1000
simulaciones, mismo estadístico), R5 (tiempo **y** amplitud, con el desvío medido contra el tren
ajustado **sin** ese evento: con él adentro, el ajuste lo esconde), R6, C1 (resumen por grupo), C2
(mediana sobre medibles, reportable si lo es la mitad) y C4 (pruebas). **C3** (métricas por cruces de
nivel) **no se aplicó**: queda para consultar con el equipo.

**Dos arreglos que salieron al implementar:**

- **Grilla de períodos fina.** Con la tolerancia de 2 fotogramas, la grilla fija de 600 candidatos
  era demasiado gruesa (paso de 0.07 s cerca de 10 s: a 5 períodos del ancla las ranuras se corrían
  0.18 s) y el tren de Video_prueba no entraba entero en ningún candidato. Ahora el paso se ajusta a
  la tolerancia.
- **Puntaje vectorizado.** Con la grilla fina el Monte Carlo tardaba minutos (un bucle de Python por
  candidato). Se calcula el puntaje de todos los candidatos a la vez; es **idéntico** al cálculo uno
  por uno (verificado en 200 series al azar, y fijado en `tests/test_ritmo.py`). Video_prueba tarda
  1.6 s.

**Resultados** (los seis videos, `--frecuencia-estimulo 0.1`; conteos y `k` sin cambios):

| video | estimulados | período | p | cinética principal |
|---|---|---|---|---|
| Video_prueba | 7 → **6** | 10.00744 → **10.00043 ± 0.00230** | 0.005 → 0.001 | estimulados: amplitud relativa 0.71 → **2.31 %** |
| Video_063 | 5 | 9.99917 → 10.00190 ± 0.00304 | 0.005 → 0.001 | 0.53 → 0.54 % |
| Video_268 | 6 | 9.99990 → 10.00132 ± 0.00230 | 0.005 → 0.001 | igual |
| Video_466 | 5 | 9.99433 → 10.00224 ± 0.00693 | NaN → **0.001** | RT50 160 ms sobre 4 de 5 medibles |
| Video_583 | 6 | 10.00119 → 10.00024 ± 0.00230 | 0.005 → 0.001 | igual |
| Video_491 | — (2 eventos) | — | — | igual |

**Pruebas:** `tests/test_ritmo.py` (nueva, 17 chequeos: pulsos que fallan, R5, R6, veredictos, dos
frecuencias, resolución del p, puntaje vectorizado, cinética por grupo) y `tests/test_cinetica.py`
(+ evento con meseta, regla de la mitad). `test_deteccion`, `test_nan` y `test_seleccion_k` sin
cambios, OK.
