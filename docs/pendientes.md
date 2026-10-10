# Lista única de pendientes

Armada el 2026-10-07 y actualizada el 2026-10-08, juntando `raritos.md`, `propuesta-fase-4.md`, `ESTADO-arranque-chat-nuevo.md`, `preguntas-reunion-equipo.md` y `CLAUDE.md`. **Esta es la lista vigente**; las de esos documentos quedan como historia.

## Ya resuelto hoy (commit 4e4d37e)
Del "Pendiente de código" de `raritos.md`:
- 1: aviso de grosor alineado al 6 % y redactado como posibilidad
- 2: aviso del ancho de la zona, sacado
- 3: `motion_check` guarda en la carpeta del video
- 4: figuras NO REPORTABLE en gris, con los falsos de control
- 6: aviso de fotogramas sin borde y avisos de sklearn silenciados
- 7: sentido de los eventos corregido (estaba invertido en todos los videos)

Además: `--verbose` en los tres scripts, guía `docs/guia-salida-consola.md`.

## A. Depende del equipo (reunión 2026-10-08)
Las preguntas están en `docs/preguntas-reunion-equipo.md`. Lo central:
1. Frecuencia y estado del estimulador en cada RARITO (613, 068, 304, 341) y en 491 (36 Hz, ¿tétanos?).
2. ¿La actividad espontánea es resultado o estorbo? Esto define la **medida de actividad** (C1).
3. Adquisición:
   - ¿pueden grabar un subconjunto a 200–300 fps? (es lo único que permitiría medir TTP/RT50 en las muestras rápidas)
   - ¿pueden grabar un video de control de iluminación? (para probar con un número que el método no se engaña con la luz)
   - ¿pueden no tocar el montaje durante la grabación?
   - ¿se anota el aumento?
   - ¿cómo exportan los videos? (compresión)
4. **La reunión del 2026-10-08 se suspendió.** Se armó un mail para Cami (borrador en Gmail) con el PDF `docs/RARITOS_resultados_y_preguntas.pdf` (resultados de los RARITOS + 10 preguntas). Anotar acá las respuestas.

## B. Cambios de código que cambian números (medir antes + regresión sobre Video_prueba y 063)
1. **Posición inicial de búsqueda del borde** (068; hoy 068, 304 y 341 necesitan `--half-window 30` a mano). **Medido el 2026-10-08/10, sin implementar nada:**
   - Hoy la ventana (±15 px) se centra en una posición fija salida del **mapa de máximos**; si el gel se mueve mucho ese mapa "estira" la franja. En 068 la guía del borde superior queda en 303 px y el borde real anda en 317 [303–329]: el 67 % de los fotogramas queda fuera. Con la **mediana** del video (1 de cada 20 fotogramas, en la misma lectura) la guía queda en 316 y solo el 0.1 % queda fuera.
   - **Mediana siempre, con ±15, en los 11 videos:** Video_prueba idéntico; mismos conteos en todos los reportables; 068 pasa a 1 fotograma sin borde (antes 60 %); 304 igual (0); 341 21 candidatos en vez de 22 (NO REPORTABLE igual). Pero cambian décimas en el resto y más en 466 (TTP 255 → 288 ms, RT50 pasa a no medible) y 491 (2.º evento 33.96 → 34.36 s, TTP 570 → 770 ms).
   - **¿Mejor o peor? Criterio objetivo sin verdad conocida:** columnas descartadas por RANSAC (outliers) en los fotogramas que cambian; menos = la ventana agarra mejor el borde. Con mediana: **mejor** en 583 (5.2 → 4.2), 304 (3.4 → 2.4), 341, 613, 476; neutro/un poco peor en 268, 491, 063; **peor en 466** (10.6 → 12.3; peor en 1443 fotogramas, mejor en 385). Conclusión: "mediana siempre" NO es mejor en todos; descartada como está.
   - **Opciones que faltan medir con el mismo criterio** (outliers por fotograma, ruido en tramos quietos y, si hace falta, `motion_check` como referencia independiente por intensidad):
     - (a) guía actual y pasar a la mediana **solo si falla** (fotogramas sin borde > 1 %, el umbral del aviso actual). Duda: ¿en 304/341 la guía actual con ±15 falla visible o "en silencio"? (341 con ±15 daba 16 eventos en vez de 22 sin aviso aparente).
     - (b) **`--half-window 30` para todos** (pregunta de Franco: si con 30 se arreglaba, ¿por qué no dejarlo?). Riesgo: una ventana más ancha puede agarrar otro gradiente (halo, burbuja, anclaje) y cambia los validados. Hay que medirlo, no suponerlo.
     - (c) mediana siempre (ya medida, arriba).
   - Hallazgo aparte: correr la ventana 1–7 px cambia `center_px` en muchos fotogramas de algunos videos (466, 063, 491): en esos hay otro gradiente cerca del borde de la ventana. Vale entender por qué.
   - Código de la prueba (variable `B1=1`, no está en el repo) y resultados: solo en la sesión del 2026-10-08; se rehace fácil.
2. **Ruido estimado solo en los tramos quietos.** En 341 el tren de 22 s infla el ruido (0.10 contra 0.034 px) y sube el umbral.
3. **Análisis de optimización del código** (pedido por Franco):
   - (a) **Tiempo.** Medido el 2026-10-08 (Video_prueba, 99 s en la máquina de prueba): ~40 % era leer el video 3 veces, ~60 % procesar los fotogramas (sobre todo RANSAC de sklearn, después bordes y CLAHE). **Hecho, sin cambiar ningún número (bit a bit):** marcas de tiempo y mapa de máximos en una sola lectura; fotogramas en paralelo (`--procesos`); sin los chequeos internos de sklearn. **RANSAC propio, hecho:** mismo algoritmo y mismo sorteo que sklearn, 5–6 veces más rápido por ajuste (Video_prueba en un núcleo: 81 → 60 s); en los seis videos, mismas columnas inlier, `center_px` idéntico y mismos conteos (test: `tests/test_ransac.py`). **CLAHE solo sobre la franja: medido y descartado (2026-10-08).** No da idéntico (el CLAHE de OpenCV no es independiente por baldosa: recortar cambia el resultado aunque se corte en los bordes de las baldosas). En los seis videos cambia `center_px` en 3–4 % de los fotogramas (hasta 0.047 px en 466, 0.029 px en 063), sin cambiar eventos, instantes ni amplitudes; gana solo ~10 % en un núcleo y nada en paralelo. No vale romper la regresión exacta por eso. Lo que más pesa ahora es leer el video (dos pasadas, en serie). H29 (¿un ajuste sin RANSAC sería menos ruidoso en 466?) sigue abierto. Varios videos a la vez: junto con C3 (procesar una carpeta). **En la notebook de Franco (4 núcleos, 2026-10-08) el paralelo casi no gana:** Video_prueba, solo `main.py`: 1 proceso 108 s, 2 → 102 s, 4 → 102 s, 7 (el default de entonces) → 127 s. Se pasó el default a 2. Falta medir cuánto tarda cada parte (lectura del video, mapa de máximos, fotogramas) en esa máquina para ver si conviene atacar la lectura.
   - (b) **Recortar código. Hecho (2026-10-08):** se borraron `--sep-s`, `--canal`, `--fit-method median`, `--maxproj`, `--table-format` y los scripts `medir_*.py`, `regenerar_fase4.py` e `inspect_frame.py` (siguen en el historial de git; sus mediciones, en `data/_mediciones_fases/`). También la separación vieja en dos poblaciones por amplitud (hoja `poblac_*`): no se usaba para clasificar.

4. **Comparar `--edge-method sigmoid` y `--denoise` contra lo actual** (quedan en el código porque nunca se midieron; H28: sigmoid difiere del parabólico +0.24 px en media, 0.57 px de desvío). Si alguno no es mejor, borrarlo.

## B2. Próximo paso de código (antes de lo demás)
1. **Hecho (2026-10-08).** **Nombres de los Excel con el nombre del video**, como las figuras: `serie_temporal_<video>.xlsx`, `contracciones_<video>.xlsx` y `movimiento_<video>.xlsx`. Los scripts y la ventana tienen que aceptar también el nombre viejo, y hay que actualizar la documentación. No cambia números.

## C. Herramientas nuevas (no cambian los números existentes)
1. **Medida de actividad** para los videos con actividad continua (068, 304, 341), que corre después del reporte y no lo reemplaza. Mediría amplitud, fracción de tiempo activo, frecuencia y regularidad. Requisito: confirmar con un anclaje que lo que se mueve es el tejido y no toda la imagen. Casi seguro les interesa cuantificarla (Franco, 2026-10-08; se les preguntó en la pregunta 4 del PDF, con esta propuesta): se puede ir diseñando, pero no es lo primero.
2. **Detector de vibración** usando una referencia fija con textura (el anclaje). En 068, 304 y 341 los anillos del anclaje sirvieron; en 583 no había ninguna referencia usable.
3. **Interfaz más amigable**. La ventana ya está hecha (`interfaz.py`, `Analizar.bat`). Quedan, de la sección 6 de la guía:
   - un solo comando que corra todo
   - procesar una carpeta entera con tabla resumen
   - un informe por video
   - un archivo de doble clic o una ventanita
   - un archivo de configuración
   - **Ventana más linda y con visor de resultados** (pedido por Franco, 2026-10-08):
     - pestañas (correr / resultados / opciones), con mejor aspecto;
     - abrir los gráficos del video que se acaba de correr, o de cualquier carpeta de
       `processed_data`, dentro de la ventana;
     - gráficos interactivos: zoom, desplazarse y leer valores con el mouse (por
       ejemplo, rehacer el de contracciones con la barra de herramientas de
       matplotlib o con plotly, leyendo los Excel; no regenerar nada);
     - ver al lado los números principales del `resumen` (eventos, k, período,
       amplitud, avisos y NO REPORTABLE).
     - Regla: la ventana solo lanza los scripts y muestra resultados; nunca calcula
       (así no se vuelve más lenta ni puede dar números distintos de la consola).
       Un gráfico en vivo, si se agrega, se redibuja cada 1–2 s como mucho.
4. **Hecho (2026-10-08). Sacar el grosor (línea roja) del gráfico de contracciones** (`09_contracciones_*`) y dejarlo solo con `--verbose`: el adelgazamiento es diagnóstico y no se informa (CLAUDE.md, hallazgo 1), y en el gráfico invita a interpretarlo. No cambia ningún número. (Pedido por Franco, 2026-10-08.)
5. **Hecho (2026-10-08):** test de regresión automático (`tests/test_regresion.py`, referencia congelada en `tests/referencia_regresion.json`; `scripts/regenerar_todo.py` para regenerar).
8. **A futuro: visualizador en vivo** (pedido por Franco, 2026-10-10): que mientras se graba el video se vaya analizando y mostrando algo (por ejemplo, la posición de la franja y los eventos a medida que aparecen). Requiere leer de la cámara o de un archivo que crece, una versión del análisis que funcione por tramos (hoy la ROI y el umbral k se eligen mirando el video entero) y decidir qué se puede mostrar "en vivo" sin que sea un número final. No cambia los números del análisis completo, que se sigue haciendo al terminar.
6. Intervalos de confianza por bootstrap para las medianas por video.
7. Versiones fijas en `requirements.txt`.

## D. Dudas abiertas para revisar con más videos
1. 466: la medida por intensidad da 0.88 de la de bordes; no se sabe cuál está más cerca de la verdad. Puede que su % esté subestimado en un 10–20 %. ¿Pasa con toda la tanda EXP5? (476 da 0.82)
2. 476: ¿el salto de brillo cada 5 fotos (compresión) aparece en otros RARITOS y no en los OK?
3. 063: ¿la contracción espontánea de 0.31 s es local? A ojo no parece tan chica como mide la zona angosta. Medir la amplitud por tramos a lo largo del gel.
4. Reglas que salieron de pocos videos:
   - "meseta de k más bajo" (un solo caso real con dos mesetas)
   - piso de 40 columnas
   - "zona plana mejor que ancha"
   - error de modelo y `outlier_frac` sin umbral (medidos en 2 videos)
5. `signal_check` nunca se probó con un video real sin contracciones (lo resolvería el video de control de iluminación).
6. Riesgos que todavía no avisan:
   - timestamps inventados por el contenedor (H15)
   - poco contraste (H22)
   - cintura corta (H21)
7. 476: oscilación chica (~0.3–0.5 px) después de cada contracción, debajo del umbral. ¿Se repite en otros videos?

## E. Mantenimiento
1. **Hecho (2026-10-08):** los 11 resultados vigentes regenerados con el código nuevo (nombres nuevos, figuras NO REPORTABLE, resumen con las filas nuevas), sin cambiar ningún número. Se borró `Video_068` (sin hw30). Ojo: 304 y 341 se habían corrido con `--half-window 30` sin sufijo en la carpeta (anotado en `tests/referencia.py`). Queda sin regenerar el paso 3 de 476 (`movimiento.xlsx`, nombre viejo).
2. **Hecho (2026-10-08):** documentación ordenada:
   - una sola fuente en `docs/` (con copia de los vigentes en el proyecto);
   - fases cerradas en `docs/historia/`;
   - `CLAUDE.md`, `README.md`, `ESTADO`, protocolo, referencia y `DOCUMENTACION` al día;
   - borrados los duplicados (`gel_fix`, `LEEME`, `LEEME_v3`, `order.txt`, `qc_output/`);
   - borradas las copias viejas de código del proyecto.
   - carpeta ordenada: borrados `_superadas/` (sigue en el historial de git), `ordenar_carpeta.py` y la copia vieja en `.claude/worktrees/`; mediciones de fases en `data/_mediciones_fases/`; los videos crudos dejaron de guardarse en git (`.gitignore`). El historial viejo de git todavía los contiene: achicar el repo exigiría reescribirlo (no recomendado).
3. **Hecho:** queda un solo cuaderno, `Analisis_Contractilidad_v4.ipynb`. `v4-1` era una versión anterior: todavía tenía `SEP_S` y 28 eventos.
