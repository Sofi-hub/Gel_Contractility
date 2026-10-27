# H13: ¿aguanta el control de falsos con ruido desparejo? (2026-10-26)

**Qué es el control.** Para decidir si un conteo se puede informar, el programa busca contracciones
también en la señal **dada vuelta**. Como una contracción solo puede ir para un lado, todo lo que
aparece del lado invertido es ruido; si hay aunque sea uno, el umbral no sirve. Ese razonamiento
**supone que el ruido es igual de grande hacia arriba que hacia abajo**. Nunca se había probado con
ruido desparejo (H13 en `docs/pendientes.md`).

**Lo que importa saber** no es solo "¿se equivoca?", sino **hacia qué lado**:

- equivocarse **de más** (decir "no se puede informar" cuando sí se podía) es **seguro**: se pierde
  un dato, no se publica uno falso;
- equivocarse **de menos** (dar por bueno un conteo que tiene contracciones inventadas) es **grave**.

**Respuesta corta.** El control **sí se puede equivocar de la manera grave**, pero solo en un caso
muy concreto: cuando el ruido tiene una cola larga **hacia el mismo lado al que van las
contracciones**. Ahí llegó a informar hasta **18 contracciones donde había 6**, marcadas como
reportables. En todos los demás casos probados (ruido desparejo hacia el otro lado, rebote después de
cada contracción) se equivoca **siempre hacia el lado seguro**. Y las contracciones inventadas tienen
una marca clara: **duran 1 fotograma, contra 2.5–3 de las reales**.

## Cómo se midió (`h13.py`)

Series sintéticas de 70 s a 30 fps con **6 contracciones conocidas** de 1.5 px (las mismas de
`tests/test_deteccion.py`), ruido base de 0.04 px, 6 semillas × 2 correlaciones (ρ = 0 y 0.6) = 12
corridas por escenario. Sobre cada una se corre la detección entera (`contraction_report.analizar`),
y el resultado se clasifica:

- **correcto**: 6 eventos y reportable;
- **conservador**: no reportable (sea cual sea el conteo) → seguro;
- **INVENTA**: reportable con más de 6 → grave;
- **PIERDE**: reportable con menos de 6.

Escenarios: ruido simétrico (control); cola exponencial hacia un lado, **a favor** (hacia donde van
las contracciones) y **en contra**, con tres severidades; y un **rebote** después de cada contracción
(el gel se pasa de largo al volver) del 10, 30 y 50 % de la amplitud.

Tablas: `sinteticos.csv` (una fila por corrida), `resumen_escenarios.csv`, `videos_reales.csv`.
Consola: `salida.txt`.

## Resultado

| escenario | correcto | conservador (seguro) | **INVENTA** | eventos (mín–máx) | ancho de los inventados |
|---|---|---|---|---|---|
| simétrico (control) | **12/12** | 0 | 0 | 6–6 | — |
| asim. **a favor** 1 % × 3σ | 3/12 | 2/12 | **7/12** | 6–**13** | 1 fotograma |
| asim. **a favor** 2 % × 5σ | 2/12 | 4/12 | **6/12** | 6–**18** | 1 fotograma |
| asim. **a favor** 5 % × 3σ | 5/12 | 4/12 | **3/12** | 6–**16** | 1 fotograma |
| asim. **en contra** 1 % × 3σ | 11/12 | 1/12 | 0 | 6–6 | — |
| asim. **en contra** 2 % × 5σ | 4/12 | 8/12 | 0 | 6–6 | — |
| asim. **en contra** 5 % × 3σ | 6/12 | 6/12 | 0 | 5–11 | 1 fotograma |
| rebote 10 % | **12/12** | 0 | 0 | 6–6 | — |
| rebote 30 % | 0 | **12/12** | 0 | 4–6 | 7 fotogramas |
| rebote 50 % | 0 | **12/12** | 0 | 6–6 | 8.5 fotogramas |

(Los eventos verdaderos miden 2.5–3 fotogramas por encima de la mitad de su altura.)

### Cuándo se equivoca, y por qué

- **Ruido desparejo hacia el mismo lado que las contracciones: ahí falla, y falla grave.** Los golpes
  de ruido van para arriba, así que se cuentan como contracciones; pero del lado invertido no hay
  nada, así que **el control no ve ningún falso** y la meseta parece limpia. El programa informa un
  conteo inflado con total confianza. Con la cola más suave (1 % de los fotogramas, golpes de 3σ) ya
  pasa en 7 de 12 corridas.
- **Ruido desparejo hacia el otro lado: seguro.** Los golpes van del lado invertido, el control los
  cuenta como falsos y el conteo se marca NO REPORTABLE. Nunca inventó nada.
- **Rebote después de cada contracción: seguro, y bastante sensible.** Con un rebote del 10 % no pasa
  nada (12/12 correcto). Con 30 % o más, el rebote mismo es un pico del lado invertido: el control lo
  cuenta como falso y el video queda NO REPORTABLE en las 12 corridas. O sea: **un gel que se pasa de
  largo al relajarse hace que el conteo no se informe**, aunque las contracciones estén bien.

### ¿Algún video real se acerca a estos casos?

Medido igual en los 11 videos de referencia (`videos_reales.csv`): sesgo del ruido en los tramos
quietos, cociente entre la cola de arriba y la de abajo, rebote después de cada contracción y ancho
de los eventos.

| video | sesgo | cola arriba/abajo | rebote | ancho de los eventos | conteo |
|---|---|---|---|---|---|
| Video_prueba | **+1.26** | **2.59** | 7 % | 3 fot. (1 evento de 1 fot. de 29) | 29, reportable |
| 063 | +0.17 | 1.47 | 3 % | 2 fot. | 6, reportable |
| 268 | −0.27 | 0.80 | 5 % | 2 fot. | 6, reportable |
| 466 | +0.13 | 1.08 | 12 % | 10 fot. | 5, reportable |
| 583 | +0.33 | 0.94 | 4 % | 12 fot. | 6, reportable |
| 491 | −0.10 | 0.90 | **50 %** | 30 fot. | 2, reportable |
| 476 | +0.35 | 1.22 | 27 % | 4 fot. | 6, reportable |
| **613** | −0.05 | 0.91 | **84 %** | 1 fot. (**14 de 24** de 1 fot.) | 24, **NO reportable** |
| 068 | +0.66 | 1.62 | — | — | 0, NO reportable |
| 304 | +0.35 | 1.30 | — | — | 0, NO reportable |
| **341** | +0.79 | 1.21 | **64 %** | 2 fot. (2 de 22 de 1 fot.) | 22, **NO reportable** |

Tres cosas de acá:

1. **Video_prueba está en la zona peligrosa por la asimetría** (sesgo +1.26, cola 2.59; el sintético
   que inventa tiene sesgo 2.4–2.6 y cola 1.1–2.3). Pero su conteo de 29 está validado por otras
   vías, y lo más probable es que esa asimetría **sea señal, no ruido**: las contracciones
   espontáneas chicas que no llegan al umbral empujan la "cola quieta" hacia arriba. O sea: en un
   video real, una cola asimétrica hacia arriba puede ser tanto el problema como la prueba de que hay
   actividad. **No se puede usar sola como alarma.**
2. **Los dos videos reales con más rebote (613 con 84 %, 341 con 64 %) son justamente los dos que el
   programa se niega a informar.** Eso confirma en datos reales el mecanismo que mostró el sintético,
   y es una buena noticia: el control está haciendo su trabajo.
3. **El ancho separa bien lo real de lo inventado**: en los videos reportables los eventos duran 2 a
   30 fotogramas, y el único de 1 fotograma es 1 de los 29 de Video_prueba. En 613 (no reportable),
   14 de 24 duran 1 fotograma.

## Conclusión

1. **El control con la señal invertida es seguro salvo en un caso:** ruido con cola larga **hacia el
   lado de las contracciones**. Ahí puede informar contracciones inventadas sin ningún aviso.
2. **En todos los demás casos se equivoca hacia "no informar"**, que es el lado correcto. El rebote
   del gel (≥ 30 %) es una causa frecuente de NO REPORTABLE, y eso explica 613 y 341.
3. **Ningún video de referencia está demostrado como afectado**, pero Video_prueba tiene la asimetría
   en el rango del escenario que falla, así que **el riesgo no es teórico**: hoy el programa no tiene
   forma de distinguir "cola asimétrica porque hay actividad chica real" de "cola asimétrica porque
   el ruido es desparejo".

### Qué se podría hacer (sin implementar: cambiaría números informados)

- ~~**Diagnóstico, sin umbral** (como `outlier_frac`)~~ → **HECHO el 2026-10-27** (aprobado por
  Franco): `contraction_report.asimetria_ruido` guarda en la hoja `resumen_*` las columnas
  `ruido_sesgo_quieto` y `ruido_cola_arriba_sobre_abajo`. Sin umbral y sin aviso; ningún número
  cambia y la regresión de los 11 es idéntica. Medidos en los 11 de referencia y los 9 de Andrés:
  sesgo de −0.30 (10V_3) a +1.26 (Video_prueba), cola de 0.80 (268) a 2.59 (Video_prueba); el
  segundo más alto es 068 (1.62). Los de Andrés quedan entre −0.30 y +0.63 de sesgo y 0.89–1.41 de
  cola: ninguno llega a donde está Video_prueba.
- **Filtro por ancho** (más fuerte, y hay que medirlo antes): pedir que un evento dure al menos 2
  fotogramas por encima de la mitad de su altura. En los sintéticos eso borraría **todos** los
  inventados (duran 1) y **ninguno** de los verdaderos. En los videos reales tocaría 1 de los 29
  eventos de Video_prueba, así que **cambia un número de la línea base** y hay que medirlo en los 11
  y aprobarlo. Ojo con el hallazgo 5 de `CLAUDE.md`: a 30 fps hay contracciones reales de 2
  fotogramas, así que un piso de 3 sería demasiado.
- **No** conviene poner una alarma automática por asimetría sola: Video_prueba la dispararía y su
  conteo es correcto.

## Límites

- Los sintéticos usan una sola forma de contracción (rápida, 1.5 px, 0.04 px de ruido) y una sola
  manera de hacer el ruido desparejo (cola exponencial de un lado). No cubre, por ejemplo, deriva
  asimétrica lenta ni artefactos de compresión.
- "Rebote" está medido como el mínimo entre 0.2 y 1.5 s después del pico, como % de la amplitud de
  ese pico. En los videos con muchos eventos seguidos (613, 341) esa ventana puede caer sobre el
  evento siguiente, así que el 84 % y el 64 % son cotas, no medidas finas.
- El sesgo y la cola de los videos reales se miden sobre los fotogramas a más de 1 s de cualquier
  evento **detectado**; las contracciones que no se detectan quedan adentro y suben el sesgo. Eso es
  justamente lo que hace ambigua la interpretación en Video_prueba.
- No se tocó ningún archivo del análisis. Ningún número informado cambia.

---

# D. El filtro por duración, medido en los videos reales (2026-10-27)

**Qué se probó** (`filtro_ancho.py`, solo medición): en los 11 de referencia (con su serie vigente,
por bordes) y en los 9 de Andrés (sus series, por textura), cuánto dura cada evento —los fotogramas
seguidos por encima de la mitad de la altura del pico, la misma regla del sintético— y cuáles se
caerían si se exigiera un piso de **2 fotogramas**. Tablas: `filtro_ancho_eventos.csv` (138 eventos,
uno por fila) y `filtro_ancho_resumen.csv`; consola en `salida_filtro_ancho.txt`.

| video | eventos | ancho mediano | el más corto | de 1 fotograma | quedarían | conteo |
|---|---|---|---|---|---|---|
| Video_prueba | 29 | 3 fot. | **1** | **1** (7.28 s) | 28 | reportable |
| 063 | 6 | 2 fot. | 2 | 0 | 6 | reportable |
| 268 | 6 | 2 fot. | 2 | 0 | 6 | reportable |
| 466 | 5 | 10 fot. | 9 | 0 | 5 | reportable |
| 583 | 6 | 12 fot. | 12 | 0 | 6 | reportable |
| 491 | 2 | 30 fot. | 29 | 0 | 2 | reportable |
| 476 | 6 | 4 fot. | 3 | 0 | 6 | reportable |
| **613** | 24 | **1 fot.** | 1 | **14** | 10 | NO reportable |
| 068 / 304 | 0 | — | — | — | — | NO reportable |
| **341** | 22 | 2 fot. | 1 | **2** | 20 | NO reportable |
| 10V_1 | 6 | 5 fot. | 4 | 0 | 6 | reportable |
| 10V_3 | 8 | 12.5 fot. | 1 | **1** (15.80 s) | 7 | NO reportable |
| 20V_3 | 6 | 5.5 fot. | 5 | 0 | 6 | reportable |
| 40V_1 | 5 | 5 fot. | 5 | 0 | 5 | reportable |
| 40V_2 | 1 | 4 fot. | 4 | 0 | 1 | NO reportable |
| 40V_3 | 6 | 3.5 fot. | 2 | 0 | 6 | reportable |
| 10V_2 / 20V_1 / 20V_2 | 0 | — | — | — | — | NO reportable |

**En 16 de los 20 videos el filtro no cambiaría nada.** Toca cuatro: 613 (−14 de 24), 341 (−2 de 22),
10V_3 (−1 de 8) y Video_prueba (−1 de 29). Los tres primeros ya son NO REPORTABLES, así que su
conteo no se informa igual: **el único número informado que cambiaría es el 29 de Video_prueba, la
línea base del proyecto**.

## El evento de Video_prueba que se caería (7.28 s)

Figura: `prueba_evento_1_frame.png` (la señal) y `prueba_evento_1_frame_fotograma.jpg` (el fotograma
del video en ese instante).

- **Por tamaño es indiscutible:** 2.124 px, **24.9 veces el ruido** del canal, casi igual de alto que
  sus vecinos reales (2.1, 2.4, 2.0, 2.2 px).
- **Por forma es el único raro de los 29:** sube y baja en **un solo fotograma**, sin subida ni cola.
  Sus cuatro vecinos de la misma ráfaga (5.97, 6.57, 7.67 y 8.28 s) duran 3, 3, 2 y 3 fotogramas y
  tienen la cola de relajación de siempre.
- **Y hay algo más, que no se buscaba:** justo antes hay un **hueco de 0.398 s en la grabación**
  (entre los fotogramas 206 y 207; el `dt` normal es 0.0333 s, o sea que faltan ~12 fotogramas). El
  evento es el tercer fotograma después del hueco. Los dos de antes y los siete de después están
  planos. **Medido después** (`../huecos_grabacion/`, 2026-10-27): es una **coincidencia**. En los 11
  videos hay 32 huecos de ≥ 0.3 s y este es el único con algún evento a menos de 0.5 s; y los eventos
  de 1 fotograma no están más cerca de los huecos que los de 2+ dentro de ningún video.
- A ojo, el fotograma del video no tiene nada llamativo (la franja se ve nítida, sin arrastre).

Dicho sin vueltas: ese evento **tiene la altura de una contracción y la forma de un artefacto**, y
aparece pegado al único corte grande de la grabación en esa zona. No alcanza para afirmar que sea
falso, pero tampoco para defenderlo.

## Conclusión de D

1. El filtro por duración (piso de 2 fotogramas) **hace lo que promete el sintético**: no toca ningún
   evento de los videos reportables salvo uno, y limpia 14 de los 24 de 613, que es justamente el
   video donde el control se equivoca.
2. **No se puede subir el piso a 3:** en 063 y 268 *todos* los eventos duran 2 fotogramas, y son
   conteos validados. El piso tiene que ser 2, no más.
3. **Falta decidir.** Cambia un número de la línea base (Video_prueba 29 → 28), así que no se
   implementa sin que Franco lo apruebe. Lo que habría que mirar primero es el evento de 7.28 s con
   el equipo: si aceptan que un pico de 1 fotograma pegado a un hueco de 0.4 s no es una contracción,
   el filtro entra; si no, no.
4. Alternativa más conservadora, por si el filtro parece demasiado: **no filtrar, pero avisar**, como
   `junto_al_borde`, marcando los eventos de 1 fotograma y los que caen a menos de medio segundo de
   un hueco de la grabación. Eso no cambia ningún número.

