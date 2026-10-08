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
4. Mail con gráficos de los RARITOS: **después** de la reunión, con sus respuestas.

## B. Cambios de código que cambian números (medir antes + regresión sobre Video_prueba y 063)
1. **Posición inicial de búsqueda del borde por mediana**, no por la proyección de máximos (068). Arreglaría el caso "gel que se mueve mucho" sin tener que usar `--half-window 30` a mano.
2. **Ruido estimado solo en los tramos quietos.** En 341 el tren de 22 s infla el ruido (0.10 contra 0.034 px) y sube el umbral.
3. **Análisis de optimización del código** (pedido por Franco):
   - (a) **Tiempo.** Medido el 2026-10-08 (Video_prueba, 99 s en la máquina de prueba): ~40 % era leer el video 3 veces, ~60 % procesar los fotogramas (sobre todo RANSAC de sklearn, después bordes y CLAHE). **Hecho, sin cambiar ningún número (bit a bit):** marcas de tiempo y mapa de máximos en una sola lectura; fotogramas en paralelo (`--procesos`); sin los chequeos internos de sklearn. **RANSAC propio, hecho:** mismo algoritmo y mismo sorteo que sklearn, 5–6 veces más rápido por ajuste (Video_prueba en un núcleo: 81 → 60 s); en los seis videos, mismas columnas inlier, `center_px` idéntico y mismos conteos (test: `tests/test_ransac.py`). **CLAHE solo sobre la franja: medido y descartado (2026-10-08).** No da idéntico (el CLAHE de OpenCV no es independiente por baldosa: recortar cambia el resultado aunque se corte en los bordes de las baldosas). En los seis videos cambia `center_px` en 3–4 % de los fotogramas (hasta 0.047 px en 466, 0.029 px en 063), sin cambiar eventos, instantes ni amplitudes; gana solo ~10 % en un núcleo y nada en paralelo. No vale romper la regresión exacta por eso. Lo que más pesa ahora es leer el video (dos pasadas, en serie). H29 (¿un ajuste sin RANSAC sería menos ruidoso en 466?) sigue abierto. Varios videos a la vez: junto con C3 (procesar una carpeta).
   - (b) **Recortar código. Hecho (2026-10-08):** se borraron `--sep-s`, `--canal`, `--fit-method median`, `--maxproj`, `--table-format` y los scripts `medir_*.py`, `regenerar_fase4.py` e `inspect_frame.py` (siguen en el historial de git; sus mediciones, en `data/_mediciones_fases/`). También la separación vieja en dos poblaciones por amplitud (hoja `poblac_*`): no se usaba para clasificar.

4. **Comparar `--edge-method sigmoid` y `--denoise` contra lo actual** (quedan en el código porque nunca se midieron; H28: sigmoid difiere del parabólico +0.24 px en media, 0.57 px de desvío). Si alguno no es mejor, borrarlo.

## B2. Próximo paso de código (antes de lo demás)
1. **Hecho (2026-10-08).** **Nombres de los Excel con el nombre del video**, como las figuras: `serie_temporal_<video>.xlsx`, `contracciones_<video>.xlsx` y `movimiento_<video>.xlsx`. Los scripts y la ventana tienen que aceptar también el nombre viejo, y hay que actualizar la documentación. No cambia números.

## C. Herramientas nuevas (no cambian los números existentes)
1. **Medida de actividad** para los videos con actividad continua (068, 304, 341), que corre después del reporte y no lo reemplaza. Mediría amplitud, fracción de tiempo activo, frecuencia y regularidad. Requisito: confirmar con un anclaje que lo que se mueve es el tejido y no toda la imagen. Esperar la respuesta de A2.
2. **Detector de vibración** usando una referencia fija con textura (el anclaje). En 068, 304 y 341 los anillos del anclaje sirvieron; en 583 no había ninguna referencia usable.
3. **Interfaz más amigable**. La ventana ya está hecha (`interfaz.py`, `Analizar.bat`). Quedan, de la sección 6 de la guía:
   - un solo comando que corra todo
   - procesar una carpeta entera con tabla resumen
   - un informe por video
   - un archivo de doble clic o una ventanita
   - un archivo de configuración
4. Test de regresión automático contra los `contracciones_<video>.xlsx` vigentes (hoy se compara a mano).
5. Intervalos de confianza por bootstrap para las medianas por video.
6. Versiones fijas en `requirements.txt`.

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
1. Regenerar las figuras de 341, 304 y `068_hw30` con el código nuevo, para que digan NO REPORTABLE en el título (613 ya está). Con la ventana: solo el paso 2, sobre la carpeta existente y con la frecuencia vacía. No cambia ningún número.
2. **Hecho (2026-10-08):** documentación ordenada:
   - una sola fuente en `docs/` (con copia de los vigentes en el proyecto);
   - fases cerradas en `docs/historia/`;
   - `CLAUDE.md`, `README.md`, `ESTADO`, protocolo, referencia y `DOCUMENTACION` al día;
   - borrados los duplicados (`gel_fix`, `LEEME`, `LEEME_v3`, `order.txt`, `qc_output/`);
   - borradas las copias viejas de código del proyecto.
   - carpeta ordenada: borrados `_superadas/` (sigue en el historial de git), `ordenar_carpeta.py` y la copia vieja en `.claude/worktrees/`; mediciones de fases en `data/_mediciones_fases/`; los videos crudos dejaron de guardarse en git (`.gitignore`). El historial viejo de git todavía los contiene: achicar el repo exigiría reescribirlo (no recomendado).
3. **Hecho:** queda un solo cuaderno, `Analisis_Contractilidad_v4.ipynb`. `v4-1` era una versión anterior: todavía tenía `SEP_S` y 28 eventos.
