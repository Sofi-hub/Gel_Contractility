# Separación de contracciones estimuladas vs espontáneas

`src/rhythm_split.py`, disponible desde `contraction_report.py` con
`--frecuencia-estimulo`. Validado sobre seis videos.

> **Actualizado 2026-09-30.** Los números de este documento se recalcularon con
> la base de tiempo por PTS (`--base-tiempo pts`). Las versiones anteriores
> usaban `fotograma / fps` y tenían un sesgo de entre −0.4 % y −0.9 %. La
> sección "hallazgo colateral sobre el fps" se reemplazó por
> `claude/base-de-tiempo-y-frames-perdidos.md`, que la explica completa.

## El criterio: enganche de fase

No se usa la amplitud (con estimulación débil los grupos se solapan) ni la
ventana temporal (las espontáneas siguen apareciendo durante el tren). Se usa la
única propiedad que define a una contracción estimulada y no depende del
montaje: **está enganchada en fase a un reloj periódico**. El estimulador
dispara en `t = fase + n·T`; las espontáneas no saben nada de ese reloj.

El algoritmo busca la grilla `(T, fase)` que mejor explica un subconjunto de los
eventos, y llama espontáneo a lo que quede afuera. Como la amplitud no
interviene en la clasificación, que los grupos resulten tener amplitudes
distintas es **evidencia independiente** de que la separación es real.

Validación estadística: el p-valor sale de un Monte Carlo que corre el
procedimiento completo sobre datos con los intervalos permutados (conserva la
distribución de intervalos, destruye el enganche de fase), así que ya incluye el
haber probado muchos períodos y el haber elegido la ventana post-hoc.

## Resultados (base de tiempo PTS)

| video | frecuencia medida | vs 0.1 Hz | jitter | captura | veredicto |
|---|---|---|---|---|---|
| Video_prueba | 0.09993 ± 0.000041 Hz | −0.07 % | 20.9 ms | 7/7 | indistinguible |
| Video_063 | 0.10001 ± 0.000030 Hz | +0.01 % | 9.6 ms | 5/5 | indistinguible |
| Video_268 | 0.10000 ± 0.000023 Hz | 0.00 % | 9.6 ms | 6/6 | indistinguible |
| Video_466 | 0.10006 ± 0.000120 Hz | +0.06 % | 35.1 ms | 5/5 | indistinguible |
| Video_583 | 0.09999 ± 0.000067 Hz | −0.01 % | 25.4 ms | 6/6 | indistinguible |

**Los cinco dan una frecuencia indistinguible de lo configurado.** Con el eje
`fotograma / fps` daban −0.9 %, −0.43 % y, en el caso de Video_466, +5.15 %.

Video_prueba tiene además 22 contracciones espontáneas con intervalo mediano
0.572 s (1.75 Hz) y **CV del 91 %**. Deliberadamente **no se reporta como "una
frecuencia"**: estas células no la mantienen constante. Salen la mediana, el
rango intercuartil y la frecuencia **instantánea** evento a evento (hoja
`espont_*`), que es lo que hay que graficar para ver cómo deriva.

Video_491 (36 Hz) no tiene tren: su escaneo de umbral no tiene meseta, así que
no se reporta conteo.

## Latidos dudosos

Un latido del tren cuyo instante detectado se corrió más que la tolerancia no se
descarta ni se mezcla con las espontáneas: se reporta aparte como
`estimulados_dudosos`, y no entra en el ajuste del período. Para decidir qué es,
se compara su amplitud con la de los estimulados — y como la amplitud no se usó
para clasificar, esa comparación es independiente.

Con el eje temporal corregido, **varios de los que antes salían dudosos pasaron
a ser latidos capturados**: Video_063 fue de 4/4 ranuras a 5/5, Video_268 de 5/5
a 6/6, Video_prueba de 6/6 a 7/7. El tiempo mal escalado los corría fuera de
tolerancia.

## Tres problemas que hubo que resolver

**Armónicos.** El z-score solo hacía que ganara `T/3 = 3.362 s` con 44 % de
captura. Si el período real es T, la grilla de T/2 también contiene todos los
eventos verdaderos pero con la mitad de las ranuras vacías, y como tiene más
ranuras puede acumular un z mayor. Se exige `min_captura` (75 % por defecto) y,
entre los candidatos que puntúan casi igual, se elige el período **más largo**:
un armónico siempre está en T/2, T/3, … o sea siempre es menor. Bajar
`min_captura` sólo si se sospecha bloqueo 2:1 real.

**Intrusos con brazo de palanca.** Un espontáneo tomado como primera ranura
movía el período y repartía su error entre todos los residuos, quedando
indetectable. Se ajusta primero con **Theil-Sen** (mediana de las pendientes de
a pares), que una minoría de puntos malos no mueve, y recién al final por
mínimos cuadrados sobre el conjunto ya limpio.

**Error estándar cero.** El tren cae siempre en el mismo número de fotogramas,
así que los residuos daban exactamente 0 y el ajuste reportaba error 0, que es
falso: el jitter real está por debajo de un fotograma. Se pone como piso el
error de cuantización, `resolución/√12`.

## Interacción con la elección de k

`rhythm_split` es sensible a eventos espurios: un par de detecciones de ruido
ensucian el ajuste de la grilla lo suficiente como para que **no encuentre el
tren**. En Video_583, con el `k=8` que era el default, salían 9 eventos (1 falso
de control) y el p-valor no superaba el azar. Con `k=12`, que es donde está la
meseta, el tren aparece limpio: 5/5 ranuras, CV 0.4 %.

El fallo no era ruidoso: no avisaba nada, simplemente no había tren. Por eso la
elección de `k` ahora es automática y sale de la meseta.

## Salidas

`10_ritmo.png` (eventos coloreados por grupo, grilla del estimulador marcada, y
el error de cada latido en ms) y las hojas `ritmo_*`, `grilla_*` y `espont_*` de
`contracciones.xlsx`.

## Limitaciones conocidas

- Necesita al menos 4 latidos estimulados para encontrar el tren.
- Un evento espontáneo puede coincidir con una ranura por azar. Su amplitud, que
  no se usó para clasificar, es lo que lo delata.
- Si la estimulación cambia de frecuencia a mitad del video, esta versión
  encuentra un solo tren. Habría que correrla por tramos.
