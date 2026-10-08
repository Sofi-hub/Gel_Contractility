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
