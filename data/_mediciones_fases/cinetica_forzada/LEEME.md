# Cinética (TTP y RT50) desde la respuesta forzada (2026-10-26)

**Pregunta.** En los videos NO REPORTABLES la respuesta forzada ya dice *si* el gel responde al
estimulador y *cuánto* se mueve, pero no dice *cuán rápido*: no hay contracciones detectadas, así que
no hay TTP ni RT50. ¿Se pueden sacar igual, usando los instantes en que sabemos que disparó el
estimulador?

**Respuesta corta.** Sí, pero **midiendo pulso por pulso y quedándose con la mediana**, no promediando
la forma de todos los pulsos. Hecho así, en los videos reportables da lo mismo que el reporte normal
(diferencias de 1 a 4 %), y agrega TTP y RT50 a **3 de los 5 videos NO REPORTABLES** de Andrés. La
forma promedio, en cambio, **no sirve**: en Video_466 da un TTP 42 % más alto que el real.

## Cómo se midió (`cinetica_forzada.py`)

Nada de esto toca el análisis: solo lee las series ya guardadas en `data/processed_data`.

1. Señal: `center_px` sin deriva (mediana móvil de 2 s), lo mismo que usa `src/forzada.py`.
2. Período, fase y sentido del pulso: los que calcula `src.forzada.respuesta_forzada` con 0.1 Hz y
   búsqueda a ±2 %, igual que el reporte.
3. Cada pulso se recorta de −1.5 a +2.5 s alrededor de su instante y se le resta su propia línea de
   base (mediana de −1.2 a −0.4 s, la misma ventana con que forzada mide la amplitud).
4. TTP y RT50 **con las reglas de `src/cinetica.py`, sin inventar ninguna**: el pico es el primer
   fotograma que llega al 95 % del máximo; el valor se da solo si la subida (o la bajada al 50 %)
   abarca ≥ 5 fotogramas, y si no, solo la cota.
5. Dos maneras de combinar los pulsos:
   - **por pulso** (la que sirve): se mide cada pulso por separado y se toma la mediana de los
     medibles, con la regla del reporte de "al menos la mitad". IC 95 % con `ic95_mediana`, la misma
     función del reporte.
   - **forma promedio** (la que no sirve): se promedian los pulsos y se mide esa única curva. IC 95 %
     re-sorteando los pulsos (bootstrap).
6. Sensibilidades: usar todos los pulsos esperados o solo los que responden, y quitar la deriva con
   2 s o con 4 s.

## Resultado

Tablas: `cinetica_forzada.csv` (una fila por video y combinación) y `pulsos.csv` (una fila por pulso).
Figura: `formas.png`. Salida de consola: `salida.txt`.

### Control: ¿da lo mismo que el reporte en los videos donde el reporte sí mide?

| video | TTP reporte | TTP por pulso | TTP forma promedio | RT50 reporte | RT50 por pulso | RT50 forma promedio |
|---|---|---|---|---|---|---|
| **466** | 183 ms | **185 ms (+1 %)** | 260 ms (**+42 %**) | 226 ms | **219 ms (−3 %)** | 176 ms (**−22 %**) |
| **583** | 189 ms | **193 ms (+2 %)** | 190 ms (+0 %) | 252 ms | **251 ms (−1 %)** | 275 ms (+9 %) |
| **20V_3** | no medible | no medible ✔ | no medible ✔ | 153 ms | **147 ms (−4 %)** | 140 ms (−8 %) |
| 10V_1, 40V_1, 40V_3 | no medible | no medible ✔ | no medible ✔ | no medible | no medible ✔ | no medible ✔ |

En los seis controles **la medición por pulso nunca se contradice con el reporte**: donde el reporte da
un número, lo reproduce dentro del 4 %; donde el reporte dice "no medible a 30 fps", también dice que
no es medible.

### Lo nuevo: los NO REPORTABLES

| video | amplitud | TTP | pulsos medibles | IC 95 % | RT50 | pulsos medibles | IC 95 % |
|---|---|---|---|---|---|---|---|
| **10V_3** | 5.78 px | **214 ms** | 6 de 6 | 160–263 ms | **234 ms** | 6 de 6 | 201–286 ms |
| **20V_1** | 1.54 px | **174 ms** | 5 de 6 | 157–184 ms | **167 ms** | 3 de 6 | 167–179 ms |
| **20V_2** | 2.62 px | **157 ms** | 6 de 6 | 139–175 ms | **144 ms** | 3 de 6 | 141–205 ms |
| 10V_2 | 0.39 px | solo cota: < 133 ms | 0 de 6 | — | solo cota: < 100 ms | 0 de 6 | — |
| 40V_2 | 0.56 px | solo cota: < 133 ms | 0 de 6 | — | solo cota: < 133 ms | 2 de 6 | — |

10V_2 y 40V_2 son las dos respuestas más chicas (< 0.6 px): duran 1 o 2 fotogramas y a 30 fps no se
pueden medir, igual que pasa con los videos rápidos de siempre. **No es una falla del método: es la
cámara.**

### Por qué la forma promedio falla y la mediana por pulso no

Promediar supone que todos los pulsos están alineados. No lo están, por dos motivos que se ven en
`formas.png`:

- **Pulsos sin respuesta.** Video_466 tiene 6 instantes esperados pero solo 5 contracciones (el tren va
  de 14 a 54 s); el 6.º pulso mide 0.17 px, o sea nada. Promediarlo achata la curva. Sacando los pulsos
  que no responden la amplitud promedio pasa de 3.60 a 4.34 px, que ya es la del reporte (4.36 px).
- **El reloj supuesto no es exactamente el real.** Aun sacando ese pulso, el TTP promedio de 466 queda
  en 260 ms contra 183 reales: el período buscado (9.98 s) y el del tren medido (10.0018 s) difieren lo
  justo para que los pulsos se corran unos fotogramas entre sí a lo largo del minuto, y la subida del
  promedio sale más ancha de lo que es.

La mediana por pulso no tiene ese problema porque cada pulso se mide en su propio instante, y además
**los pulsos sin respuesta se caen solos**: no llegan a ser medibles, así que no entran en la mediana.
Por eso la columna "todos los pulsos" y la columna "solo los que responden" dan exactamente lo mismo.

### Estabilidad

La mediana por pulso casi no cambia si se quita la deriva con 4 s en vez de 2 s: TTP se mueve ≤ 6 %
(10V_3: 214 → 201 ms, el que más) y RT50 ≤ 8 % (10V_3: 234 → 253 ms). Los demás, ≤ 4 %. La ventana de
2 s no se está comiendo la relajación.

### Un detalle clínico que apareció solo

**20V_1 es bifásico:** antes del pico la franja se va para el otro lado (se ve claro en `formas.png`).
Eso no rompe la medida —el onset se toma igual, al 10 % de la amplitud—, pero conviene mirarlo con el
equipo: en los otros videos no pasa.

## Conclusión

1. **TTP y RT50 se pueden medir en los NO REPORTABLES**, con el método por pulso, y quedan validados
   contra el reporte en 3 videos donde hay con qué comparar.
2. **No usar la forma promedio.** Es la idea que parecía natural y es la que falla.
3. Lo que se ganaría si se implementara: TTP y RT50 en 10V_3, 20V_1 y 20V_2 (hoy no tienen ninguno).
   Los otros dos quedarían con la cota, igual que hoy.
4. **Hay que decidirlo con el equipo antes de implementarlo**, porque sería un número nuevo que hoy la
   regla del proyecto prohíbe: `src/cinetica.py` solo emite TTP/RT50 si el **conteo** es reportable, y
   acá el conteo no lo es. La propuesta sería tratarlo como la amplitud forzada: un número aparte,
   rotulado "cinética de la respuesta al estímulo, no de contracciones contadas", que no cambia el
   veredicto del conteo.

## Límites

- Supone que el estimulador estaba encendido y a 0.1 Hz, igual que toda la respuesta forzada.
- Con respuestas de menos de ~1 px (10V_2, 40V_2) no alcanza: hacen falta más fotogramas por segundo.
- Los IC con 5 o 6 pulsos son gruesos (466: 155–259 ms) y saltan entre los valores de los propios
  pulsos. Es honesto, no un error.
- Las series de Andrés están medidas por textura y achicadas a la mitad; valen las salvedades de
  `data/_mediciones_fases/textura/LEEME.md`.
- No se implementó nada. Ningún número informado cambia.
