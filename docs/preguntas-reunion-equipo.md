# Preguntas para la reunión con el equipo de Tecnun

Preparado 2026-10-07, al cerrar la Fase 4; actualizado con los `RARITOS` ya procesados (ver `raritos.md`). Anotar las respuestas acá.

## Sobre los videos de `RARITOS`
1. ¿Qué fallaba con MuscleMotion en cada uno? (¿demasiada actividad espontánea, mala imagen, movimiento, frecuencia alta?)
2. ¿A qué frecuencia se estimuló cada uno, o si estaba apagado? (los nombres sugieren 1–2 Hz y 5–10 Hz en algunos)
3. ¿Hubo cambios de frecuencia o de voltaje durante la grabación?
   - 3b. **Video_613 (CTRL7):** no vemos ninguna contracción en 5–63 s (solo vibración al inicio y al final). ¿El estimulador estaba encendido? ¿Es esperable que ese control no responda?
   - 3c. **Video_068 (FAPS2, 5 V):** el gel se mueve todo el tiempo (oscilación irregular de ~3 por segundo, más ~21 excursiones grandes), sin ningún ritmo de estimulador visible. ¿Se estimuló? ¿A qué frecuencia?
   - 3d. **Video_304 (1–2 Hz):** oscilación continua a ~3.5–4.3 Hz, que no coincide con 1 ni 2 Hz. ¿Cómo se estimuló?
   - 3e. **Video_341 (5–10 Hz):** ráfagas al inicio, 15 s quieto y un tren ordenado de ~3.2 Hz entre 33 y 54 s. ¿Cuándo y a qué frecuencia se estimuló?

## Qué quieren medir cuando hay mucha actividad espontánea (surgió con Video_068)

No es "actividad total **o** respuesta al estímulo": las dos se pueden medir por separado. La pregunta es qué número quieren para cada video y para qué lo usan. Preguntar en este orden:

A. **¿Qué pregunta biológica responde el experimento?** Por ejemplo:
   - "¿los FAPS cambian cuánto contrae el tejido?"
   - "¿cambian su excitabilidad o su actividad espontánea?"
   - "¿cambian cómo responde al estímulo?"

   De eso sale qué medir.
B. **¿La actividad espontánea es un resultado o un estorbo?**
   - Si es un **resultado**: medirla como actividad (cuánto se mueve, qué fracción del tiempo está activo, a qué frecuencias, cuán regular), no como un número de contracciones.
   - Si es un **estorbo**: interesa solo la respuesta al estímulo, y los videos con espontánea continua quizás no sirvan, o hay que estimular más fuerte o a una frecuencia que domine.
C. **Si interesa la respuesta al estímulo:** ¿qué número usan? Amplitud por pulso, % de pulsos que responden (captura), latencia, cinética.
D. **¿Cómo comparan entre videos?** ¿Promedio por condición (CTRL vs FAPS)? ¿Al mismo voltaje y frecuencia? Eso define si hace falta una métrica común a todos los videos.
E. ¿Qué entregaba MuscleMotion que usaban (número de picos, amplitud, tiempos), y qué les faltaba?

## Sobre los videos ya analizados
4. **Video_491 (36 Hz):** ¿cómo se estimuló? Da 2 contracciones de ~1 s, en sentido contrario a las demás. ¿Es esperable un tétanos?
5. **Video_583, final (72–74 s):** tiembla toda la imagen. ¿Alguien tocó el microscopio o se cambió algo al terminar? (También pasa en Video_613, al inicio y al final.)
6. **Video_063, inicio (0.3 s):** hay una contracción espontánea. ¿Es habitual que haya actividad espontánea antes de que arranque el estimulador?

## Sobre la adquisición
7. ¿Se puede grabar un subconjunto a 200–300 fps? (a 30 fps la cinética de las muestras rápidas no se puede medir)
8. ¿Se puede grabar un **video de control**: el mismo gel quieto, con un cambio de luz o parpadeo? (para mostrar con un número que el método no se engaña con la iluminación, y MuscleMotion sí)
9. ¿Se puede evitar tocar el montaje durante la grabación, o anotar cuándo pasa?
10. ¿Todos los videos se graban al mismo aumento? ¿Se anota?
   - 10b. ¿Cómo se comprimen o exportan los videos? (En 476 hay un salto de intensidad cada 5 fotogramas exactos, también en el fondo: probable compresión. Engaña a MuscleMotion; a nosotros no.)

## Sobre qué necesitan
11. ¿Qué números usan del análisis (amplitud, frecuencia, TTP/RT50, espontáneas)? ¿En qué formato?
12. ¿Qué significa "OK" para ellos? ¿Hay un criterio escrito?

## Sobre la cinética: qué es "el pico" (agregado 2026-10-10, H41)
13. **En las contracciones lentas (466, 583) el gel se queda arriba unos 5 fotogramas (~150 ms) antes de relajarse: el máximo es una meseta, no un punto.** TTP (inicio → pico) y RT50 (pico → 50 % de relajación) dependen de qué instante de esa meseta se toma como "pico". Mediana de los eventos estimulados:

    | se toma como pico | 466 TTP | 466 RT50 | 583 TTP | 583 RT50 |
    |---|---|---|---|---|
    | el fotograma más alto (lo que hace hoy el programa) | 255 ms | 158 ms | 258 ms | 181 ms |
    | el comienzo de la meseta | 183 ms | 223 ms | 189 ms | 252 ms |
    | el centro de la meseta | 249 ms | 156 ms | 239 ms | 198 ms |
    | el final de la meseta (comienzo de la relajación) | 315 ms | 96 ms | 292 ms | 146 ms |

    Según la definición, TTP cambia ~±25 % y RT50 hasta ×2. Hoy se usa "el fotograma más alto", que dentro de la meseta lo decide el ruido.
    - ¿Qué definición usan ustedes o la bibliografía que siguen (MuscleMotion, el paper de eLife)?
    - Alternativa que no depende de la meseta: **tiempo de subida 10–90 %** y **bajada 90–50 %**. Medido: 466 161 ms / 82 ms; 583 146 ms / 110 ms. Pero a 30 fps son 3–5 fotogramas: quedarían en el límite de lo medible (pregunta 7, grabar a 200–300 fps).

---

## Respuestas de Cami por mail (2026-10-14)

1. **Protocolo de grabación.** El estimulador (C-Pace) está siempre encendido, pero no siempre estimula. Cada video dura ~1 minuto: **los primeros 10 s son basales, sin estimulación**; después se activa el programa.
   - **Voltajes:** 5, 10, 20, 30 y 40 V; pulsos de 2 ms a **0.1 Hz** (twitch).
   - **Frecuencias:** 40 V; trenes de **1 s** a 1–5, 10, 20, 30 y 36 Hz (tetanus), con **10 s de descanso** entre frecuencias.
2. **Los programas son siempre los mismos en todas las muestras.** Si la frecuencia que medimos no coincide, puede ser actividad espontánea.
3. **La actividad espontánea no es muy importante.** Buscan sacar más información; propone cuantificarla **solo en los primeros 10 s** (la ventana basal).
4. **MuscleMotion:** su análisis se basa en la intensidad del píxel, y eso afectaba la magnitud de la contracción.
5. **fps:** cuanto más alto, mejor, pero están limitados por la cámara (sin compromiso de 200–300 fps).
6. **Videos nuevos:** otra estudiante grabó videos la semana pasada; los van a pasar (sirven para probar la luz, etc.).

### Qué significa para el análisis (lectura nuestra, 2026-10-15)
- **0.1 Hz confirmado** para los videos de voltaje (063 5 V, 268/466/583 40 V, 476): coincide con lo que mide el programa. Se puede pasar `--frecuencia-estimulo 0.1` en esos.
- **El estímulo arranca a los ~10 s.** Lo anterior es basal: la espontánea de 063 a 0.31 s cae en la basal (esperable).
- **Videos de frecuencia (304 "1_2HZ", 341 "5_10HZ", 491 "36HZ"):** cada estímulo es un **tren de 1 s**, no un pulso. A frecuencias altas el gel no se relaja entre pulsos (tétanos), así que la unidad a medir es **la respuesta a cada tren de 1 s**, no contracciones sueltas. Explica 491 (2 contracciones de ~1 s, compatibles con un tétanos fusionado) y por qué 304 y 341 salían NO REPORTABLE con el método de contracciones sueltas. Hace falta un análisis por bloques de estímulo (pendiente nuevo).
- **Espontánea:** basta un resumen de la ventana 0–10 s (cuántas, amplitud), no la medida de actividad completa (C1 baja de prioridad).
- **TTP/RT50 en muestras rápidas:** seguirán sin poder medirse a 30 fps.
- Sin respuesta todavía: pregunta 13 (qué es "el pico" en una meseta), 613 y 068.

## Respuestas de la reunión (2026-10-15, contadas por Franco)

- **Todos los videos con voltaje en el nombre se estimularon a 0.1 Hz** (incluidos 613 "40V" y 068 "5V"). Algunos videos (los de frecuencia) tienen cambios de frecuencia.
- **Videos difíciles:** "no te mates buscándolo". Hay permiso para **pasar la frecuencia conocida** y hacer la búsqueda dirigida, más sensible (068, 613, 341, 304).
- **Pregunta 13 (H41): el pico es el PRIMER instante en que se llega al máximo** (comienzo de la meseta), también en las contracciones sostenidas. Cambia TTP y RT50 en las muestras lentas: hay que medirlo y aprobarlo antes de implementarlo.
- **Basal (0–10 s):** casi seguro sin estimulados; sirve como período de espontáneas. Estaría bueno caracterizarla; no pidieron parámetros concretos.
- **Ventana:** les gustó (individuales y promedios). Pedidos:
  - que la información de **cada pulso** sea más visible (Franco);
  - **elegir qué pulsos entran** (por ejemplo, los 3 primeros estimulados) y ver su promedio y los pulsos individuales, porque no siempre pueden garantizar que se registraron los 6;
  - **comparar esa selección entre dos videos** (los 3 primeros de cada uno).

## Preguntas nuevas (2026-10-17, videos de Andrés)

Contexto: los 9 videos de Andrés (4K, mucho zoom, gel vertical) no se pueden medir por bordes; por textura sí (4 de 9 reportables y respuesta visible cada 10 s en casi todos). Detalle: `data/_mediciones_fases/textura/LEEME.md`.

1. **¿Los próximos videos van a ser como los de Andrés (4K, mucho zoom, gel vertical) o como los de antes?** Define cuánto conviene invertir en el método por textura.
2. **¿A cuántos fotogramas por segundo graba la cámara de Andrés?** En los 9 videos el período del estímulo sale 10.10 s en vez de 10.00 (−1 %). Lo más probable es la cámara (~29.7 fps reales aunque el archivo diga 30), no el estimulador. ¿Se puede conseguir el archivo original de la cámara, con los tiempos reales?
3. **Si durante una grabación alguien toca o sacude el equipo, ¿descartan ese video o lo usan igual?** (10V_3 tiene una sacudida a los ~15 s; 20V_1, temblores continuos).
   - Si lo usan igual: ¿se puede dejar algo fijo con textura dentro de la imagen, para distinguir una sacudida del microscopio de un movimiento del tejido?
4. **Videos de frecuencia (304 "1_2HZ", 341 "5_10HZ", 491 "36HZ"):** el protocolo general ya lo pasó Cami (40 V; trenes de 1 s a 1–5, 10, 20, 30 y 36 Hz con 10 s de descanso). ¿Qué frecuencias tiene cada uno de estos tres videos, en qué orden y cuándo empieza el primer tren?
5. **Para comparar voltajes, ¿les alcanza con 1 o 2 videos limpios por voltaje, o necesitan los 3?** Hoy por textura son reportables 10V_1, 20V_3, 40V_1 y 40V_3. Si necesitan los 3, conviene implementar la "respuesta forzada" (medir en cada instante esperado de estímulo, contra controles).

> **Actualización (2026-10-19) de la pregunta 5:** ya no hace falta elegir. La "respuesta forzada" está hecha y los 5 videos que no eran reportables (10V_2, 10V_3, 20V_1, 20V_2, 40V_2) **sí responden** al estímulo. Ver la explicación C de abajo.

## Explicaciones para la reunión (2026-10-26)

Para contarle al equipo, en palabras simples, tres cosas que salen de los videos de Andrés. Detalle técnico: `data/_mediciones_fases/textura/LEEME.md` §6, `data/_mediciones_fases/textura_resolucion/LEEME.md` y `data/_mediciones_fases/respuesta_forzada/LEEME.md`.

### A. ¿Por qué un video sale "NO REPORTABLE" si a ojo se ven las contracciones?

**"NO REPORTABLE" no quiere decir "no hay contracciones".** Quiere decir que el programa no puede **asegurar cuántas** hay sin que el número dependa de una elección arbitraria. Para contar, el programa busca picos que sobresalgan del temblor normal de la medición (el "ruido") y solo informa el número si pasa **tres pruebas**:

1. **El número no cambia al mover el umbral.** Se prueban umbrales de 3 a 24 veces el ruido. Si en un tramo amplio de umbrales sale siempre el mismo número (la "meseta"), el conteo es firme. Si con un umbral salen 6 y con uno apenas más alto salen 4, no hay un número verdadero para dar.
2. **Nada del lado contrario.** Una contracción mueve el gel hacia **un** lado; una sacudida o el ruido lo mueven hacia **los dos**. El programa busca picos también en la señal dada vuelta: si aparece alguno con ese umbral, lo que está contando puede ser ruido o vibración.
3. **El número no depende de cómo se quita la deriva.** Antes de contar se quita el corrimiento lento (foco, temperatura) con una ventana de unos segundos. Se cuenta con tres ventanas (1.5, 2 y 3 s) y las tres tienen que dar lo mismo.

**De qué depende, en la práctica:** del **tamaño de la respuesta comparado con el ruido**. Ejemplos reales:
- **20V_3:** la respuesta es ~25 veces el ruido → pasa las tres pruebas siempre.
- **40V_3:** ~9 veces el ruido → pasaba "raspando" (la meseta apenas tenía el ancho mínimo); medido en 4K, con un poco más de ruido, dejó de pasar.
- **40V_1:** respuesta clara, pero en el primer segundo del video hay un poco de ruido que, con la ventana de 1.5 s, aparece como un sexto "evento" → falla la prueba 3.
- **10V_3:** respuestas grandes (~6 px), pero una **sacudida** a los ~15 s mueve la imagen hacia los dos lados → falla la prueba 2.
- **10V_2, 40V_2:** respuestas de ~0.5 px, apenas por encima del ruido → no hay meseta (prueba 1).

**Por qué es así a propósito:** el programa prefiere **no informar** antes que informar un número que cambia según un ajuste. El error siempre va hacia "no informar", nunca hacia inventar contracciones.

### B. Videos 4K: ¿se miden achicados o en tamaño completo? ¿Cuál es el verdadero?

**Qué se hace hoy:** los videos 4K se miden **achicados a la mitad** (cada 2×2 píxeles se promedian en uno) y el resultado se pasa a píxeles del video original. Achicado tarda ~4 veces menos.

**Cómo lo comprobamos:** medimos 5 videos de las dos formas, 4K completo y achicado, y comparamos.
- **Respuesta grande (más de ~1.5 px; 20V_3, 40V_1, 10V_3):** las dos dan **lo mismo**: mismas contracciones, mismo instante y amplitud dentro del 0–2 %.
- **Respuesta chica (~1 px o menos):** **no dan lo mismo.** En 10V_1 la amplitud es 16 % menor en 4K (en los 6 pulsos); en 40V_3 cambia hasta el veredicto.

**Por qué no sabemos cuál es el verdadero:** en un video real **no conocemos el movimiento verdadero**, así que no hay contra qué comparar. Para averiguarlo hicimos un video **sintético**: una imagen con textura que movimos una cantidad **exacta y conocida** (0.5, 1 y 2 px), y la medimos de las dos formas.
- Con 2 px, las dos formas aciertan (error menor que 5 %).
- Con 0.5–1 px, **las dos se equivocan** hasta 10–20 %, y no siempre hacia el mismo lado.
- En el sintético, el achicado mide **menos** que el 4K; en 10V_1 real mide **más**. O sea, el sintético no reproduce lo que pasa en el video real: la diferencia de 10V_1 depende de algo propio de la imagen real (la textura del gel, la compresión del video o el ruido de la cámara), que un sintético no copia.

**Por qué pasa (la idea):** con movimientos de menos de un píxel, el programa tiene que "adivinar" fracciones de píxel a partir de cómo cambia el brillo entre píxeles vecinos. Eso funciona muy bien cuando el movimiento es de varios píxeles; con fracciones chicas, cualquier detalle de la imagen (cómo es el grano, la compresión) sesga un poco la estimación. Al achicar, un movimiento de 1 px pasa a ser de 0.5 px en la imagen medida, todavía más chico.

**Cuál usar:**
- **Respuestas de más de ~1.5 px:** el **achicado** (lo de siempre). Da lo mismo y es mucho más rápido.
- **Respuestas de ~1 px o menos:** cualquiera de las dos, pero **informar la amplitud con un margen de ~15–20 %** (más grande que el intervalo de confianza que da el programa). El programa ya avisa en estos casos: `AVISO: respuesta chica para el metodo de textura`.
- **Para saber el verdadero** haría falta un video del mismo montaje con un movimiento **conocido** (ver la pregunta 6).

### C. "Respuesta forzada": cómo se rescatan los videos que no se pueden contar

**Idea:** sabemos que el estimulador dispara cada 10 s. Entonces no hace falta encontrar cada contracción: alcanza con preguntar **"¿el gel se mueve en los instantes del estímulo más que en cualquier otro momento?"**. Es como escuchar golpes en una puerta en una habitación ruidosa: un golpe solo se pierde, pero si sabés cuándo va a golpear y escuchás justo ahí, lo notás.

**Cómo:**
1. Se corta la señal en tramos de 10 s y se superponen (como hojas transparentes). Las respuestas al estímulo caen siempre en el mismo lugar y se suman; el ruido cae en lugares distintos y se borra.
2. **Control:** lo mismo cortando en tramos de 40 duraciones que **no** son la del estimulador (5.5 s, 7 s, 12 s…). Ahí no hay nada que se sume. Si el período verdadero sobresale más que los 40 falsos, hay respuesta (p = 0.024 es el mejor valor posible: ninguno de los 40 le ganó).
3. En cada pulso se mide cuánto sube la franja y se compara con instantes **sin** estímulo. La amplitud es la mediana de los pulsos.

**Cómo sabemos que funciona:**
- En los 5 videos que ya se podían contar, da **la misma amplitud** que el método normal (diferencia ≤ 1.5 %).
- En 2 videos que sabemos que **no** responden al estímulo (613 y 068), dice "no hay respuesta".
- En videos sintéticos: encuentra pulsos desde 3 veces el ruido y no inventa respuestas en ruido puro ni con sacudidas al azar.

**Resultado:** los 5 videos de Andrés que no se podían contar **sí responden**: 10V_2 0.44 px (0.022 %), 10V_3 6.02 px (0.26 %), 20V_1 1.93 px (0.084 %), 20V_2 2.94 px (0.125 %), 40V_2 0.58 px (0.028 %). **Los 9 videos de Andrés responden a 0.1 Hz.**

**Lo que no hace:** no cuenta contracciones (el conteo sigue diciendo NO REPORTABLE), no ve contracciones espontáneas ni da TTP/RT50, y supone que el estimulador estaba encendido a esa frecuencia.

## Preguntas nuevas (2026-10-26)

6. **¿Se puede grabar un video con un movimiento conocido**, con el mismo microscopio y aumento que Andrés? Por ejemplo, mover la platina una cantidad medida (unos pocos µm) o filmar una muestra fija mientras se la corre. Es la única forma de saber cuál medición es la correcta cuando la respuesta es de ~1 px o menos (explicación B).
7. **¿Les sirve la respuesta forzada como resultado?** Es decir: "el tejido responde al estímulo, con una amplitud de X % del grosor", aunque no se pueda dar el número de contracciones ni la cinética. ¿O para esos videos necesitan sí o sí el conteo?
8. **Respuestas de menos de 1 px** (10V_2, 40V_2, 40V_3): ¿se puede bajar el ruido de la imagen en las próximas grabaciones? Por ejemplo, más luz o contraste, que el equipo no vibre, o exportar el video con menos compresión. Lo que decide si una respuesta chica se puede medir es cuánto sobresale del ruido.

## Preguntas nuevas (2026-10-27)

9. **20V_1 es bifásico: antes de contraerse, la franja se mueve un poco hacia el otro lado.**
   En los 6 pulsos de ese video, y siempre igual, la franja primero se desplaza ~0.9 px en el
   sentido contrario durante casi medio segundo y recién después hace la contracción (~1.7 px).
   **En ningún otro de los 20 videos medidos pasa esto** (en 20V_2 se insinúa, pero mucho más
   chico). Se ve en la figura `data/_mediciones_fases/cinetica_forzada/formas.png`, panel
   "20V_1": las 6 curvas grises tienen el mismo valle antes del pico, así que no es ruido.
   **¿Puede ser algo del montaje de ese gel** (cómo quedó anclado, una tensión previa, que el
   electrodo esté más cerca de un lado) **o es algo del tejido?** Saberlo cambia si ese video se
   puede comparar con los otros dos de 20 V o si conviene repetirlo.
