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
1. **Hecho (2026-10-10): ventana de búsqueda automática (opción a').** Antes 068, 304 y 341 necesitaban `--half-window 30` a mano.
   - **Cómo funciona:** se procesa con ±15 y la guía de siempre (mapa de máximos). Se cuenta en cuántos fotogramas hay algún borde pegado (≤ 2 px) al límite de la ventana (columna `n_bordes_en_limite` de `diagnostics`). Si pasa del 20 %, o si más del 1 % queda sin borde, se reprocesa solo con ±30 y la consola y el `resumen` lo dicen (`half_window eleccion`). `--half-window N` la fija a mano.
   - **Medición (11 videos, contra la referencia congelada; criterio: columnas descartadas por RANSAC en los fotogramas que cambian, ruido fuera de los eventos y bordes en el límite):**
     - (b) ±30 para todos: **descartada**. En 466 engancha otro gradiente (el grosor salta 201 → 191 px) y pasa de 5 a 2 eventos.
     - (c) mediana siempre: **descartada**. Peor en 466 (371 fotogramas mejoran, 1308 empeoran; TTP 255 → 288 ms). En 063 deja bordes en el límite en el 86 % de los fotogramas.
     - (a) mediana si hay > 1 % sin borde: **no sirve**. **341 con ±15 falla en silencio**: 0 % sin borde, pero 34 % de los fotogramas con bordes en el límite y 22 → 16 eventos (RANSAC peor en 875 fotogramas, mejor en 57).
     - (a') la elegida. Bordes en el límite con ±15: 068 68 %, 341 34 %, 466 12 %, 063 3 %, el resto < 1 %. Resultado: los 8 validados y 613 idénticos bit a bit; 068 y 341 pasan solos a ±30 (idénticos a la referencia); **304 queda en ±15** (cambia `center_px`, ningún número informado: 0 eventos, NO REPORTABLE; RANSAC mejor en 341 fotogramas, peor en 70). Referencia regenerada para 304.
   - El 20 % sale de pocos casos (D4).
   - Scripts y tabla de la medición: `data/_mediciones_fases/b1_ventana/`.
   - Queda abierto: en 466 hay otro gradiente a ~15 px del borde (12 % de los fotogramas con bordes en el límite). Vale entender qué es.
2. **Ruido estimado solo en los tramos quietos.** En 341 el tren de 22 s infla el ruido (0.10 contra 0.034 px) y sube el umbral.
   - **Medido el 2026-10-10, sin implementar (en espera):** ruido = MAD de los fotogramas quietos (se saca lo que pasa de 5 MAD hacia los dos lados, ±0.5 s alrededor, y se repite hasta que no cambia). Solo cambia el ruido que fija el umbral (escaneo de k y reporte).
     - Seis validados y 476: **mismos eventos, instantes, período y amplitud**. El ruido baja 2–27 % y k sube en la misma proporción: el umbral en px queda casi igual (Video_prueba 0.80 → 0.78 px). Ni mejora ni empeora.
     - 341: ruido 0.103 → 0.037 px, candidatos 22 → 98, pero falsos de control 4 → 33: sigue NO REPORTABLE. El umbral más bajo no rescata eventos: el tren de ~3 Hz es actividad hacia los dos lados (caso C1, no de conteo).
     - 613: 24 → 46 candidatos y 23 → 39 falsos: sigue NO REPORTABLE (vibración).
     - 068 y 304: sin cambios (casi todo es actividad; no queda tramo quieto suficiente).
     - Tiempo: el cálculo del ruido es instantáneo, pero con muchos candidatos el reporte se alarga mucho (341: 10 → 311 s; 613: 21 → 98 s).
     - Conclusión: hoy no aporta ningún número nuevo y cambia k en todos los videos. Queda en espera hasta que aparezca un video reportable donde el ruido inflado haga perder eventos. Script, salida y detalle (incluida la medición de tiempo): `data/_mediciones_fases/b2_ruido_quieto/`. La próxima vez: sensibilidad a corte (4–6 MAD) y margen (0.3–1 s), y buscar un video reportable con mucha actividad.
3. **Análisis de optimización del código** (pedido por Franco):
   - (a) **Tiempo.** Medido el 2026-10-08 (Video_prueba, 99 s en la máquina de prueba): ~40 % era leer el video 3 veces, ~60 % procesar los fotogramas (sobre todo RANSAC de sklearn, después bordes y CLAHE). **Hecho, sin cambiar ningún número (bit a bit):** marcas de tiempo y mapa de máximos en una sola lectura; fotogramas en paralelo (`--procesos`); sin los chequeos internos de sklearn. **RANSAC propio, hecho:** mismo algoritmo y mismo sorteo que sklearn, 5–6 veces más rápido por ajuste (Video_prueba en un núcleo: 81 → 60 s); en los seis videos, mismas columnas inlier, `center_px` idéntico y mismos conteos (test: `tests/test_ransac.py`). **CLAHE solo sobre la franja: medido y descartado (2026-10-08).** No da idéntico (el CLAHE de OpenCV no es independiente por baldosa: recortar cambia el resultado aunque se corte en los bordes de las baldosas). En los seis videos cambia `center_px` en 3–4 % de los fotogramas (hasta 0.047 px en 466, 0.029 px en 063), sin cambiar eventos, instantes ni amplitudes; gana solo ~10 % en un núcleo y nada en paralelo. No vale romper la regresión exacta por eso. Lo que más pesa ahora es leer el video (dos pasadas, en serie). **H29 cerrado (re-medido 2026-10-10 con la ROI actual, en 8 videos):** sin RANSAC baja el ruido rápido, pero el ruido que fija el umbral sube en 063 (×5, pierde el evento de 0.31 s), 476, 268 y 583; mejora algo en 466 (mismos 5 eventos, TTP 255 → 224 ms) y en Video_prueba. Ningún ajuste gana en todos: RANSAC se queda. Detalle: `data/_mediciones_fases/b3_h29/`. Varios videos a la vez: junto con C3 (procesar una carpeta). **En la notebook de Franco (4 núcleos, 2026-10-08) el paralelo casi no gana:** Video_prueba, solo `main.py`: 1 proceso 108 s, 2 → 102 s, 4 → 102 s, 7 (el default de entonces) → 127 s. Se pasó el default a 2. Falta medir cuánto tarda cada parte (lectura del video, mapa de máximos, fotogramas) en esa máquina para ver si conviene atacar la lectura.
   - **El reporte se vuelve lento con muchos candidatos (medido 2026-10-10).** En 341, con el ruido de B2 (98 candidatos), tarda ~300 s; hoy ya tarda 10 s en 341 y 21 s en 613, contra < 1 s en los demás. El 99.9 % está en el test nulo del ritmo (`rhythm_split._z_nulo`: 1000 repeticiones de `buscar_grilla`, sobre todo `_contar_vectorizado` con `np.round` y sumas). Se puede acelerar sin cambiar resultados (por ejemplo, redondear una vez fuera del bucle), verificando bit a bit con la regresión. Detalle en `data/_mediciones_fases/b2_ruido_quieto/LEEME.md`.
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
   - ventana de búsqueda automática: pasa a ±30 si > 20 % de los fotogramas tiene bordes en el límite (B1; 3 casos: 068, 341 y 466)
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

## F. Hallazgos de la revisión de código que siguen abiertos (revisados contra el código el 2026-10-10)

La revisión (H1–H55) estaba en `docs/historia/hallazgos-revision-codigo.md`, que se borró el 2026-10-10: el detalle de cada uno queda en el historial de git. Acá va solo lo que sigue sin resolver. Los demás se comprobaron resueltos o sin objeto: H1, H4, H5, H8, H9, H11, H19, H20, H24, H26, H27, H29, H31, H33, H34, H36 (Video_prueba ya da 6 estimulados y T = 10.00043 s), H37 (el rescate ya es solo dentro del tren y con amplitud compatible), H43 (los tests ya tienen eventos con meseta), H49–H51, H53–H55 (H55: prominencia en vez de `sep_s`; caso "lentos" en `test_deteccion.py`). H2, H6 y H44–H48 eran del motor `event_detection.py`, borrado. H17 (detalles de lectura) quedó resuelto o es inalcanzable.

**1. Pueden cambiar o confundir un número que se informa**
- **H40 (resto). La amplitud en px y en % describen grupos distintos.** El % sale de los estimulados si hay tren (Fase 3), pero "amplitud mediana: X px" (y `amplitud_traslacion_px`) es la mediana de TODOS los eventos. Video_prueba: 2.31 % (estimulados, ~6.8 px) al lado de 2.09 px (casi todas espontáneas). La tabla de ESTADO los pone juntos como si fueran lo mismo. Arreglo probable: dar los px del mismo grupo que el %. No cambia ningún conteo.
- **H41 (resto).** La mediana ya usa solo los eventos medibles (Fase 3). Falta decidir qué es "el pico" cuando el máximo es una meseta (466, 583): según inicio, centro o fin de la meseta, el TTP cambia ~±25 % y el RT50 hasta +40 %. Es una definición para acordar con el equipo y documentar.
- **H38 (resto).** El p-valor del tren supone espontáneas al azar: con espontáneas agrupadas o regulares (intervalos barajados de Video_prueba) el 28 % sale "estimulado". Hoy lo protege la búsqueda dirigida (`--frecuencia-estimulo`) y exigir ≥ 4 latidos con captura ≥ 75 %; sin frecuencia, el riesgo existe. (Ya resuelto: 1000 simulaciones y prueba desde 4 eventos.)
- **H16. Ventanas contadas en fotogramas, no en segundos.** La mediana de la deriva y el "≥ 5 fotogramas" de la cinética cuentan muestras; con fotogramas perdidos una ventana de "2 s" cubre hasta 2.6 s (466: 23 % de las ventanas > 2.1 s). Medir si cambia algún resultado.
- **H13. El control con la señal invertida supone ruido simétrico.** Un evento con rebote cuenta como falso; un ruido asimétrico puede no aparecer del lado invertido. Pregunta abierta, sin caso real comprobado.

**2. Riesgos que no avisan** (H15, H21 y H22 están en D6)
- **H18. Una ROI manual (`--x-start/--x-end`) no recibe veredicto de aceptación**, y `--exigir-roi` no la frena (el código lo confirma: la rama manual no calcula `cumple_criterio_aceptacion`). Hoy ningún video usa ROI manual.
- **H23.** Las ventanas de suavizado de la ROI escalan con el ancho de la imagen (`w // 60`, `w // 50`), no con el gel. Sin efecto medido.
- **H30.** El umbral de RANSAC (3 × MAD, ~2.5 px) es grande: una burbuja que corre el borde 2 px no se descarta. `max_trials = 200` y 3 puntos por intento sin justificación. Sin efecto medido.

**3. Trazabilidad y limpieza (no cambian números)**
- **H14.** `frames faltantes (%)` está inflado por el jitter de los timestamps (063: 24 contados contra 12 reales). No toca el eje de tiempo.
- **H32.** La hoja `resumen` no guarda varios parámetros (`roi_tolerance`, `roi_min_gradient`, `roi_max_slope`, `ransac_residual_k/floor`, `denoise`, `low_quality_frac`…), ni el commit ni las versiones; "fps usado" muestra el fps declarado aunque el eje salga de los timestamps; `thickness_mm` = `thickness_px`.
- **H35 (resto).** En el promedio alineado se excluyen eventos a < 1.5 s de los extremos (063: "promedio de 5" con 6 eventos); revisar que la hoja de eventos marque NO REPORTABLE.
- **H25 / H12.** `min_roi_width_frac` sigue en la firma de `auto_detect_roi` (documentado "sin uso"); borrarlo. Las listas de "métodos de ROI aceptables" de los documentos sobran: el criterio es la variación ≤ 6 %.
- **H28.** En B4 (sigmoid, denoise, `min_gradient` que nunca actúa, `clip` muerto, `quality` sin uso).
- **H39 (resto).** `tol_frac`/`tol_min_s` se aceptan "por compatibilidad" sin usarse; `comparar_con_equipo` calcula un `fps_corregido` que con eje por timestamps no tiene sentido.
- **H3 / H10 (resto). Cuaderno:** la celda que llama a `main.py` todavía pasa `--sep-s` si `SEP_S` tiene valor (la opción ya no existe: fallaría); dice "diez escaneos" del test; calcula la duración con el fps declarado.
- **H42 (resto).** Escribir en `DOCUMENTACION.md` que la amplitud relativa es una normalización para comparar videos, no una deformación del gel.

**4. Observación para la comparación con MuscleMotion**
- **H52.** Las diferencias de intensidad entre fotogramas tienen un "peine" cada 10 fotogramas (compresión del video, probablemente) que las series de bordes no tienen. Un método por intensidad, como MuscleMotion, lo arrastra. Falta verlo en los videos de `OK` (relacionado con D2).
