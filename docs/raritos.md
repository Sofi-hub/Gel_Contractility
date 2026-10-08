# Procesamiento de RARITOS (2026-10-07)

Orden: 476 → 613 → 068 → 304 → 341. Flujo: `main.py --base-tiempo pts`, `contraction_report.py` (sin frecuencia primero), `motion_check --serie`. Las salidas de `motion_check` van a la carpeta del video desde el 2026-10-07.

**Estado (2026-10-07): los cinco procesados.** Guion para la reunión con el equipo (2026-10-08) en un doc de Claude Docs ("Guion reunión Tecnun — videos RARITOS"); preguntas en `preguntas-reunion-equipo.md`. El mail con gráficos se arma **después** de la reunión, con las respuestas.

## Lectura previa de MuscleMotion (Log/Overview/Contraction.jpg)
- MM elige un fotograma de referencia automático y su curva vale 0 ahí: 476 → frame 212 (7.07 s), 613 → 191 (6.4 s). La "caída a 0" de sus gráficos es eso, no luz.
- 068: 105 picos, actividad de fondo continua (~0.4–0.5 s) + picos grandes irregulares. 304: MM analizó solo ~19 s (hasta frame 560) de un video de 75.5 s; oscilación densa.
- 341: no tiene carpeta de resultados, pero el `Contraction.jpg` suelto en `RARITOS/` es de 341 (misma estructura de tramos, ~60 s).

## Video_476 (EXP5_FAPS5_40V) — cerrado
- ROI 981–1249 (`gauge_cintura`, 60 col, var 2.64 %). Angosta porque un bulto (x≈920–960, sin nitidez) corta la cintura; correcto. 42 frames perdidos (1.9 %, 14 huecos), PTS lo maneja. Error de modelo 0.58 %, outliers 5.2 %.
- **6 eventos, todos estimulados, 0.1 Hz** (T = 10.00051 ± 0.0026 s, 6/6, p = 0.001). Meseta k = 7.1–12.5 (×1.77), 0 falsos; estable con ventana 1.5/2/3 s. Amplitud 1.69 px = 0.64 % del grosor. TTP < 155 ms, RT50 < 167 ms (no medibles).
- `motion_check`: pendiente 0.82, correlación 0.91 → CONFIRMA. (466, mismo EXP5, daba 0.88: ¿algo de la tanda EXP5, p. ej. el aumento?)
- **Por qué falla MM (hipótesis):** |ΔI| tiene un pico cada 5 fotogramas exactos (6 Hz) en todo el video, **también en el fondo**. Probable artefacto de compresión (fotograma clave cada 5). MM mide intensidad → ~90 picos falsos. La traslación por bordes no lo ve. Confirmar: ¿aparece en otros RARITOS y no en los OK?
- Tras cada contracción, oscilación chica (~0.3–0.5 px) bajo el umbral. Mirar si se repite.

## Video_613 (EXP6_CTRL7_40V) — cerrado
- ROI 896–1200 (`gauge_cintura`, var 5.05 %): gel en U suave, ROI centrada en la cintura (199 px); anclajes lejos (x<260, >1700). Error de modelo 0.28 % (el mejor), ruido canal 0.029 px. 52 frames perdidos (2.3 %, 20 huecos).
- **NO REPORTABLE: sin meseta; falsos ≈ eventos en todo k.** Los 24 "eventos" están en 0–5 s y 64–72 s, en zigzag simétrico (para arriba y abajo) = **vibración**, como la ráfaga de 583. **Franco miró el video: al inicio tiembla toda la imagen** (confirmado a ojo). Entre 5 y 63 s la señal es plana. (No se midió con los anclajes.)
- Coincide con MM tramo a tramo (ráfagas 0–5 s, ~11 s, 62–72 s); MM además sube de 45 a 70 s (deriva de intensidad). MM las cuenta como contracciones; el control simétrico dice que no.
- Conclusión: **sin contracciones detectables** (sensibilidad ~0.2 px ≈ 0.1 % del grosor). Franco: el estimulador está casi seguro siempre encendido → el tejido no responde.

## Video_068 (FAPS2_5V) — medición resuelta, interpretación abierta
- **Corrida por defecto (`Video_068/`): mala.** 346 rechazados (19 %), 769 baja calidad, outliers 40.9 %. Causa medida: la franja se mueve ±10 px y la posición inicial de búsqueda sale de la proyección de máximos (= la envolvente): borde sup 301 en la proyección contra 316 de mediana por fotograma (rango 305–325); inf 660 contra 651 (639–658). Con ventana ±15 px los fotogramas extremos quedan afuera. Desde el 2026-10-07 `main.py` lo avisa ("60 % de los fotogramas sin borde o dudosos… probá --half-window 30").
- **Con `--half-window 30` (`Video_068_hw30/`): 0 rechazados, 0 baja calidad, outliers 4.6 %**, error de modelo 0.064 %. Fondo negro arriba y abajo: no hay otro borde para engancharse.
- **No es vibración:** el anclaje superior (x 1650–1920, filas 0–280) tiene textura, correlación de fase 0.82, y se queda quieto (±0.5 px; 0.01 px entre fotogramas). Primer video con **referencia fija** utilizable. La textura del gel y el anclaje inferior no sirven (correlación ~0).
- **Señal:** traslación (grosor casi constante, 335 ± 3 px; bordes correlacionados 0.75) con oscilación continua de ~5–8 px cada ~0.33 s (CV 42 %, espectro ancho 1.2–2.7 Hz) + ~21 excursiones grandes (hasta ~15 px) irregulares, cada 0.5–6.7 s (t ≈ 13.4, 17.3, 20.0, 22.8, …). Coinciden con los picos grandes de MM (~0.5 s después por los fotogramas perdidos). **Sin ritmo de estimulador visible.** Las contracciones llevan la franja hacia ARRIBA en la imagen.
- **Reporte (`Video_068_hw30`): NO REPORTABLE, 0 eventos.** Ruido del canal 3.67 px (la oscilación continua cuenta como ruido); a k = 3: 16 eventos y **0 falsos en todo el escaneo** (las excursiones grandes son de un solo lado: reales), pero no hay meseta. El método supone gel quieto entre contracciones; acá no lo hay.

## Video_304 (EXP3_FAPS1_1_2HZ) — medición bien, interpretación abierta (mismo caso que 068)
- Corrido directo con `--half-window 30`. Duración real **75.5 s** (MM analizó ~19 s). ROI 407–1199 (`gauge_cintura`, 60 col, var 5.79 %: curva suave de la cintura, anclaje izquierdo en x<250). 0 rechazados, outliers 2.5 %, error de modelo 1.04 % (el más alto; borde sup 2.69 px). 48 frames perdidos (2.1 %, 17 huecos).
- **Señal:** oscilación continua de traslación a **~3.5–4.3 Hz** (7–8 fotogramas por ciclo), ~1 px de amplitud (~0.4 % del grosor), todo el video; grosor constante (258 ± 0.4 px). Frecuencia por tramos de 10 s: 3.75 / 3.75 / 3.75 / 4.29 / 4.29 / 4.29 / 3.53 / 3.75 Hz (cuantizado a 7 u 8 fotogramas); CV del intervalo 20–40 %.
- **No es vibración:** los anillos de los anclajes (derecha, arriba y abajo; correlación 0.69 y 0.59) quietos: 0.01 px entre fotogramas, sin potencia a 3–5 Hz.
- **No coincide con 1 ni 2 Hz.** A 30 fps (7–8 fotogramas por ciclo) la regularidad no se puede medir con precisión.
- **Reporte: 0 eventos.** Ruido del canal 0.41 px (= la oscilación); a k = 3: 10 eventos y 2 falsos; nada desde k = 4. `--frecuencia-estimulo 1 2` no se corrió: sin eventos detectados, `rhythm_split` no tiene con qué trabajar.

## Video_341 (EXP3_FAPS6_5_10HZ) — medición bien, interpretación abierta
- Corrido con `--half-window 30`. 61.6 s. ROI 427–946 (`gauge_cintura`, var 5.93 %; anclaje en x<280). 0 rechazados, outliers 4.0 %, error de modelo 0.51 %. 32 frames perdidos (1.7 %, 18 huecos).
- **Tramos:** 0–8 s ráfaga (~27 picos, ~3.5/s, irregular); 8–11 s actividad chica; 11.5–13.5 s ráfaga corta (~8, ~4/s); **15–32 s quieto** (ruido 0.034 px); **33–54 s tren ordenado**: ~66 contracciones de ~0.9 px, de un solo lado, cada 0.30–0.33 s (~3.1–3.3 Hz), fondo plano entre ellas, arranca y termina de golpe; 55–62 s quieto.
- **Reporte (video entero): NO REPORTABLE**, sin meseta. 22 eventos para auditar, amplitud 0.996 px = 0.39 % del grosor. Ruido estimado 0.10 px (el tren infla la estimación; el tramo quieto da 0.034). Las contracciones llevan la franja hacia ARRIBA en la imagen.
- **De dónde salen los falsos** (umbral fijo 0.55 px, detrend 61 muestras): lado de las contracciones 27 (0–14 s) / 0 / **64 (32–55 s)** / 0; lado contrario **17 (0–14 s)** / 1 / 1 / 0.
- **Las ráfagas de 0–14 s NO son vibración** (medido): los dos anillos del anclaje derecho (correlación 0.49 y 0.60) se mueven 0.011–0.016 px entre fotogramas en todos los tramos, mientras el gel se mueve 0.22 px en 0–8 s. Son tejido que se mueve hacia los dos lados. Franco lo confirma a ojo (contracciones muy rápidas).
- MM (`Contraction.jpg` suelto): ve las ráfagas del inicio como lo más grande (hasta 280 u.a.) y el tren de 33–53 s como una franja densa sin picos claros.
- **Decisión (2026-10-07):** no clasificar estimuladas/espontáneas desde el video (límite conocido: espontánea muy regular = estimulada por los tiempos, y a 30 fps hay 9–10 fotogramas por ciclo). Se pregunta al equipo frecuencia y momento del estímulo. **Descartado por ahora** recortar 14–62 s. Si el estimulador estuvo siempre encendido: los tramos quietos de 15 s con estímulo implican que el tren no es respuesta 1 a 1, o que la frecuencia cambió.

## Patrón de RARITOS
- **476:** normal (MM falla por la compresión, no el tejido). **613:** sin contracciones (solo vibración). **068 y 304:** actividad continua del tejido, sin pausas → el método de eventos no aplica. **341:** mezcla (ráfagas de tejido en ambos sentidos + tren limpio).
- Nombres (deducido, confirmar): EXP = experimento/tanda; CTRL = control; FAPS = gel con FAPs (progenitores fibro-adipogénicos); número = réplica; V = voltaje; HZ = frecuencia. 068 sin EXP; carpeta MM de 304 dice "1HZ".

## Propuesta: medida de actividad (después de la reunión, según lo que respondan)
- **No cambia el pipeline:** usa la serie `center_px` que ya produce `main.py`. Es un script nuevo que corre después, al lado de `contraction_report.py`, sin reemplazarlo.
- Medidas: amplitud del movimiento (variación típica, en % del grosor); fracción de tiempo activo (por encima del nivel de "quieto"); ritmo (frecuencia dominante); regularidad (variación del intervalo entre ciclos).
- Nivel de "quieto": medido, no fijado a mano. Referencias: el movimiento del anclaje (ruido de cámara) y los tramos quietos del mismo video cuando los hay.
- **Idea de Franco: usarla como respaldo cuando el reporte sale NO REPORTABLE.** Sí, con una condición: "no reportable" también sale con vibración (613) o sin nada. Antes de pasar a actividad hay que comprobar con el anclaje que lo que se mueve es el tejido; si se mueve todo el cuadro, se informa vibración, no actividad. Y la salida tiene que decir explícitamente "conteo no reportable; se informa actividad". Alternativa más simple: calcular la actividad **siempre** (es barato) y mostrarla al lado del conteo.
- Requisito para el anclaje como referencia: que tenga textura (en 068, 304 y 341 los anillos sirvieron; en 068 el anclaje inferior no). Sin referencia utilizable, avisarlo.

## Pendientes de código que salieron de los RARITOS
**Resueltos el 2026-10-07** (commit `4e4d37e`, sin cambiar ningún número):
- aviso de grosor alineado al 6 % y como posibilidad;
- aviso del ancho de la ROI, sacado;
- `motion_check` guarda en la carpeta del video;
- figuras NO REPORTABLE en gris, con los falsos de control;
- aviso claro cuando hay muchos fotogramas sin borde (y avisos de sklearn silenciados);
- sentido de los eventos corregido (el texto estaba invertido en **todos** los videos, no solo en 068 y 341; el cálculo estaba bien).

**Abiertos** (cambian números; en `pendientes.md`, sección B):
- posición inicial de búsqueda del borde por mediana, no por máximo (068);
- ruido estimado solo en los tramos quietos (341).
