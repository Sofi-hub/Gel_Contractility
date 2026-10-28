# Huecos de la grabación y eventos cercanos (2026-10-27)

**De dónde sale.** En la medición D (`../h13_ruido_asimetrico/LEEME.md`) apareció algo que no se
buscaba: el único evento de 1 fotograma de Video_prueba (7.28 s, 2.12 px, 24.9 × el ruido) cae **tres
fotogramas después de un hueco de 0.398 s en la grabación**. Franco decidió **no** implementar el piso
de 2 fotogramas; antes de volver sobre eso, la pregunta es si los huecos explican los eventos raros.

**Respuesta corta: no.** Los huecos son frecuentes y casi nunca hay un evento al lado. De los **32
huecos grandes** (≥ 0.3 s) que hay en los 11 videos de Tecnun, **solo uno tiene eventos a menos de
0.5 s: el de Video_prueba**, el mismo que disparó la pregunta. Y dentro de cada video, los eventos de
1 fotograma **no** están más cerca de los huecos que los de 2 o más, salvo en dos casos de un solo
evento cada uno. Los 9 videos de Andrés **no tienen ningún hueco**.

## Cómo se midió (`huecos.py`)

Solo medición: no toca `src/`, el detector ni las referencias, y no escribe en `processed_data`.

- **El eje temporal** es el que ya tienen las series (`time_s` en la hoja `diagnostics`), que el
  pipeline escribe desde los timestamps del contenedor (`--base-tiempo pts`, hallazgo 3 de
  `CLAUDE.md`). No hace falta volver a leer los videos.
- **Hueco** = intervalo entre fotogramas consecutivos **> 1.5 × la mediana** de los intervalos de ese
  video. De cada uno: instante, duración y fotogramas faltantes (`duración / mediana − 1`).
- **Eventos:** los que da `contraction_report.analizar` sobre `center_px`, con los mismos argumentos
  de `tests/referencia.py`. De cada evento: su **ancho en fotogramas** (los seguidos por encima de la
  mitad de la altura del pico, la misma regla de `h13.py` y `filtro_ancho.py`) y la **distancia al
  hueco más cercano**, con signo (positivo = el evento va **después** del hueco).
- **Control por azar:** qué fracción de los fotogramas del video está a menos de 0.5 s de algún hueco.
  Sin eso, "el 59 % de los eventos de 1 fotograma está cerca de un hueco" no dice nada, porque 613 y
  341 tienen a la vez muchos huecos y casi todos los eventos de 1 fotograma.

Tablas: `huecos.csv` (159 huecos), `eventos.csv` (138 eventos), `resumen.csv` (20 videos). Consola en
`salida.txt`.

    python data/_mediciones_fases/huecos_grabacion/huecos.py

## 1. Cuántos huecos hay

El `dt` mediano es **33.333 ms en los 20 videos** (los 30 fps reales del hallazgo 3).

| video | fotogramas | huecos | fot. faltantes | % perdido | hueco mayor | eventos | a < 0.5 s | azar | conteo |
|---|---|---|---|---|---|---|---|---|---|
| Video_prueba | 2007 | 7 | 29 | 1.4 % | 0.458 s | 29 | 4 | 9.5 % | reportable |
| 063 | 1848 | 24 | 35 | 1.9 % | 0.433 s | 6 | 2 | 33.9 % | reportable |
| 268 | 2283 | 21 | 53 | 2.3 % | 0.432 s | 6 | 1 | 24.1 % | reportable |
| 466 | 2076 | 23 | 106 | **4.9 %** | 0.380 s | 5 | 0 | 26.2 % | reportable |
| 583 | 2236 | 4 | 34 | 1.5 % | 0.437 s | 6 | 0 | 3.2 % | reportable |
| 491 | 1846 | 6 | 30 | 1.6 % | 0.418 s | 2 | 0 | 8.0 % | reportable |
| 476 | 2165 | 14 | 47 | 2.1 % | 0.430 s | 6 | 1 | 18.0 % | reportable |
| 613 | 2179 | 19 | 57 | 2.5 % | 0.478 s | 24 | 11 | 20.5 % | NO reportable |
| 068 | 1843 | 8 | 44 | 2.3 % | 0.342 s | 0 | — | 11.1 % | NO reportable |
| 304 | 2233 | 16 | 52 | 2.3 % | 0.345 s | 0 | — | 20.0 % | NO reportable |
| 341 | 1833 | 17 | 37 | 2.0 % | 0.297 s | 22 | 12 | 26.4 % | NO reportable |
| los 9 de Andrés | 1957–2076 | **0** | **0** | **0 %** | — | 0–8 | 0 | 0 % | 4 reportables de 9 |

Dos cosas:

- **Los 11 videos de Tecnun pierden fotogramas; los 9 de Andrés, ninguno.** Pérdida del 1.4 al 4.9 %
  (466 es el peor, el que ya se conocía). Los huecos son de dos tamaños: **0.050–0.052 s** (falta
  1 fotograma; el 60 % de los casos) o **0.26–0.48 s** (faltan 7 a 13 fotogramas; 32 casos).
- **En los videos con muchos huecos, el "azar" ya es alto**: en 063, el 34 % de los fotogramas está a
  menos de 0.5 s de algún hueco. Cualquier evento tiene una chance de uno en tres de caer ahí sin que
  signifique nada.

## 2. Los eventos a menos de 0.5 s de un hueco (31 de 138)

Tabla completa en `eventos.csv` (columnas `dist_hueco_s`, `hueco_duracion_s`, `cerca_de_hueco`);
la lista impresa está en `salida.txt`, sección 3. Resumen de los **videos reportables**:

| video | evento | instante | distancia al hueco | hueco | ancho | amplitud / ruido |
|---|---|---|---|---|---|---|
| Video_prueba | 10 | 5.447 s | −0.083 s | 0.057 s | 3 fot. | 24.5 |
| Video_prueba | 11 | 5.972 s | +0.442 s | 0.057 s | 3 fot. | 24.4 |
| **Video_prueba** | **13** | **7.280 s** | **+0.032 s** | **0.398 s** | **1 fot.** | **24.9** |
| Video_prueba | 14 | 7.672 s | +0.424 s | 0.398 s | 2 fot. | 23.9 |
| 063 | 3 | 21.910 s | +0.417 s | 0.050 s | 2 fot. | 65.9 |
| 063 | 6 | 51.908 s | −0.117 s | 0.050 s | 2 fot. | 65.7 |
| 268 | 3 | 32.665 s | +0.117 s | 0.050 s | 2 fot. | 31.7 |
| 476 | 1 | 11.323 s | −0.217 s | 0.050 s | 4 fot. | 14.9 |

Los otros 23 son de 613 (11) y 341 (12), los dos NO REPORTABLES, y están en `salida.txt`.

## 3. ¿Los eventos de 1 fotograma se concentran junto a los huecos?

Juntando todo parece que sí, pero es un artefacto de mezclar videos:

| | eventos | a < 0.5 s de un hueco | distancia mediana |
|---|---|---|---|
| de 1 fotograma | 17 | 10 (**59 %**) | 0.38 s |
| de 2+ fotogramas | 89 | 21 (24 %) | 1.57 s |

Dentro de cada video, la diferencia se cae:

| video | de 1 fot. | de 2+ fot. | azar |
|---|---|---|---|
| Video_prueba | 1/1 (100 %) | 3/28 (11 %) | 9.5 % |
| 613 | 7/14 (50 %) | 4/10 (40 %) | 20.5 % |
| 341 | 2/2 (100 %) | 10/20 (50 %) | 26.4 % |
| 063 / 268 / 466 / 583 / 491 / 476 | — (ninguno de 1 fot.) | 0–33 % | 3–34 % |

- **El 59 % es de 613 y 341**, que aportan 16 de los 17 eventos de 1 fotograma. En **613 los de 1
  fotograma y los de 2+ están igual de cerca de los huecos** (50 % contra 40 %): no hay diferencia por
  ancho. En **341** los de 1 fotograma son **dos**, y los de 2+ también están al 50 %.
- En los dos, **tanto los de 1 fotograma como los de 2+ superan el azar** (613: 50 % y 40 % contra
  20.5 %). Eso no es un efecto de los huecos: en esos dos videos los eventos vienen **en ráfagas**
  concentradas en el tiempo, y los huecos también, así que todo cae junto. El propio `CLAUDE.md`
  describe esos dos como los casos de vibración y de actividad continua.
- Los **2 casos de 100 %** (Video_prueba y 341) son de **un y dos eventos**: anécdotas, no una
  tendencia.

### La prueba que más dice: los huecos grandes

Si un corte de 0.3–0.5 s en la grabación generara picos falsos, se vería en los **32 huecos grandes**
(≥ 0.3 s) repartidos en 10 videos. No se ve:

> **De los 32 huecos de ≥ 0.3 s, solo uno tiene algún evento a menos de 0.5 s: el de Video_prueba a
> los 7.28 s.** Los otros 31 — incluidos los 8 de 466, los 4 de 613 y los 3 de 068, 304, 268, 476 y
> 583 — no tienen ningún evento al lado.

O sea: perder 8–13 fotogramas de golpe **no produce** una contracción detectada. Lo que pasa en
Video_prueba a los 7.28 s es, por lo que se puede medir, **una coincidencia**.

## Conclusión (3 líneas)

1. **No, los eventos de 1 fotograma no se concentran junto a los huecos.** El 59 % aparente es de 613
   y 341, donde los eventos de 2+ fotogramas están igual de cerca (40–50 %) y por encima del azar
   porque vienen en ráfagas; dentro de ningún video el ancho predice la cercanía a un hueco.
2. **Los huecos grandes no generan eventos:** 32 huecos de ≥ 0.3 s en 10 videos y **un solo** evento
   cercano, el de Video_prueba. Los huecos de 1 fotograma (0.05 s), que son el 60 %, tampoco.
3. **Para la decisión del piso de 2 fotogramas, esto no da un argumento nuevo**: el evento de 7.28 s
   sigue siendo raro por su **forma** (1 fotograma de 29), no por el hueco, que ahora se ve como
   coincidencia. La pregunta vuelve a ser la de D: ¿un pico de 1 fotograma con 24.9 × el ruido es una
   contracción o no? Eso lo tiene que decir el equipo.

## Anexo: los bordes del evento de 7.28 s contra contracciones reales (`comparacion_7_28.py`)

Pregunta: en `fotogramas_7_28/` los dos bordes bajan juntos en el fotograma 209 y vuelven en el 210;
¿es una sacudida (solo se corre el centro) o una contracción (cambia el largo de la franja)?

**Con qué se compara.** En Video_prueba **ningún estimulado dura 2–3 fotogramas**: los 6 duran 6. Se
usan los tres estimulados más cercanos (14.94, 24.94 y 34.94 s) y, como tienen el triple de amplitud,
también las dos espontáneas vecinas (6.57 y 7.67 s), de amplitud parecida. Todo en px, relativo al
fotograma −3 del pico (+ = hacia abajo); "largo" = `y_bottom − y_top`, "centro" = su promedio. La
**zona fija** es una franja de 60 px por encima del gel (mismas columnas de la ROI), y su corrimiento
vertical se mide por correlación de fase contra el fotograma −3. Detalle completo, fotograma a
fotograma de −3 a +4: `comparacion_7_28/tabla.csv` y `salida.txt`.

| evento | fot. en el pico | Δ top | Δ bottom | Δ largo | Δ centro | largo / centro | zona fija | fot. con Δcentro > 0.5 px |
|---|---|---|---|---|---|---|---|---|
| **7.28 s** | 209 | +2.78 | +1.65 | **−1.12** | +2.22 | **−0.51** | **+0.03** | **1** |
| espont. 6.57 s | 198 | +2.92 | +2.13 | −0.79 | +2.52 | −0.31 | −0.00 | 4 |
| espont. 7.67 s | 222 | +2.41 | +1.47 | −0.94 | +1.94 | −0.48 | +0.01 | 4 |
| estim. 14.94 s | 440 | +7.06 | +6.74 | −0.32 | +6.90 | −0.05 | −0.06 | 4 |
| estim. 24.94 s | 740 | +7.46 | +6.82 | −0.64 | +7.14 | −0.09 | +0.02 | 5 |
| estim. 34.94 s | 1040 | +6.92 | +6.54 | −0.38 | +6.73 | −0.06 | +0.03 | 4 |

En los estimulados el largo se acorta más **un fotograma después** del pico del centro (−1.0 a −1.4 px
en +1): la traslación y el acortamiento no van exactamente juntos.

**Conclusión (3 líneas)**

1. **El de 7.28 s cambia el largo, no solo el centro:** el borde de arriba baja 1.1 px más que el de
   abajo (largo −1.12 px), igual que en las espontáneas vecinas de amplitud parecida (−0.79 y −0.94 px;
   cociente largo/centro −0.51 contra −0.31 y −0.48). Una traslación pura daría Δ largo ≈ 0.
2. **La zona fija fuera del gel no se mueve** en el 209 (+0.03 px, contra los 2.22 px del centro): no
   tiembla la imagen entera. Por forma de bordes, no parece una sacudida del montaje.
3. **Lo único distinto es la duración:** 1 fotograma arriba de 0.5 px, contra 4–5 en todas las demás,
   y sin subida ni bajada. Eso no lo decide esta medición; sigue siendo la pregunta de D para el equipo.

> **Decidido (2026-10-27, Franco): sin piso de duración.** El evento de 7.28 s queda como
> contracción; Video_prueba sigue en 29. Pregunta 10 al equipo en `docs/preguntas-reunion-equipo.md`.

**Límites del anexo.** La zona fija se corre 0.4–0.96 px en algunos fotogramas **después** de las dos
espontáneas (199–202, 225–226) y no en el 209; no se investigó qué se mueve ahí (puede haber algo que
flota en la franja de 60 px). La serie guarda un valor por borde y fotograma, no la parábola por
columna, así que no se ve si el 209 se mueve igual en todo el ancho.

## Límites

- Lo que se mide es **cercanía en el tiempo**, no causa. Con 0.5 s de ventana y 14–34 % de los
  fotogramas "cerca" en los videos con muchos huecos, un evento suelto cerca de un hueco no prueba
  nada; es la ausencia (31 de 32 huecos grandes sin eventos) la que se puede afirmar.
- Los videos sin eventos detectados (068, 304 y cuatro de Andrés) no aportan a la comparación por
  ancho. Los 9 de Andrés no aportan nada: no tienen huecos.
- Los eventos de 1 fotograma son **17 en total** y 16 están en dos videos NO REPORTABLES. Con esa
  cantidad no se puede medir un efecto chico; sí se puede descartar uno grande.
- "Fotogramas faltantes" sale de `duración / mediana − 1`, que supone que la cámara captura a cadencia
  fija y el contenedor solo se saltea fotogramas. Es la misma hipótesis del hallazgo 3.
- No se tocó ningún archivo del análisis. Ningún número informado cambia.
