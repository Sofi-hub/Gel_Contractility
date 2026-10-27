# Pendientes (solo lo abierto)

Actualizado 2026-10-26. **Lista única de lo que falta.** Lo hecho y cómo se decidió está en
`docs/historia/pendientes-hasta-2026-10-26.md` (copia completa de la lista anterior) y en los
LEEME de `data/_mediciones_fases/` (índice: `data/_mediciones_fases/LEEME.md`).
Regla: cuando algo se termina, se borra de acá y se anota en una línea en `ESTADO` (historia).

## 1. Próximo (no depende del equipo)
- **Videos de Andrés:** pasos 2 y 4 rehechos el 2026-10-27, ya con la cinética de la respuesta forzada.
  Falta solo mirar en Windows cómo se ve en la ventana (Números y Comparar).
- **Textura en 583/466/063/268: medido, falta decidir** —
  `data/_mediciones_fases/textura_falla_bordes/`. En 583, 063 y 268 la textura no se equivoca (ve
  movimiento real que los bordes tapan bajo su propio ruido); en 466 sí falla en el fotograma más
  rápido. **Marcar esos fotogramas como sin medida NO sirve** (medido el 2026-10-27, sección B del
  LEEME): la correlación baja marca el tramo rápido de la contracción, no una medición mala, y el
  conteo de 466 sube de 6 a 8/12/13 en vez de bajar a 5. **Falta decidir** si se deja así (466 se
  mide con bordes y da 5, que es lo vigente) o si se cambia el método de textura para que el
  corrimiento no se parta (medir contra el fotograma de reposo). Hoy no afecta ningún resultado.

## 2. Esperando al equipo (preguntas en `preguntas-reunion-equipo.md`)
- **Videos de frecuencia (304, 341, 491):** qué frecuencias, en qué orden y cuándo empieza el primer
  tren. Después: respuesta a cada tren de 1 s y curva amplitud contra frecuencia.
- **Andrés:** fps real de la cámara (el período sale 10.10 s en vez de 10.00); si los próximos videos
  serán como los suyos; qué hacer con videos sacudidos.
- **2026-10-26 (6–8):** video con movimiento conocido (para saber qué medición es correcta con
  respuestas ≤ 1 px); si la respuesta forzada les sirve como resultado; bajar el ruido de la imagen.
- **Videos nuevos de otra estudiante:** correrlos como carpeta; ver si alguno sirve de control de luz.

## 3. En espera (medido, sin implementar hasta que aparezca un caso)
- **B2, ruido solo en tramos quietos:** no cambia ningún resultado hoy (`b2_ruido_quieto/`,
  `b2_sensibilidad/`). Retomar con un video reportable donde el ruido inflado haga perder eventos.
- **C1, medida de actividad** (068, 304, 341): baja prioridad (el equipo pidió solo la basal).
- **C2, detector de vibración** con una referencia fija (anclaje).
- **H23, ventana de la ROI escalada con el gel:** revisar si llega un video de otra resolución o aumento.
- **Visualizador en vivo** (mientras se graba): idea a futuro.

## 3b. Código repetido: arreglarlo la próxima vez que se toque la ventana (no antes)
Medido el 2026-10-26. No molesta hoy; unificarlo en `visor.py` y que `comparar.py` lo use.
- **Ancho inicial de la lista** (el bloque `_sash`): `visor.py` ~línea 856 y `comparar.py` ~línea 165. Ojo: no son
  idénticos, uno usa 340 px y el otro 330 px. Si se cambia uno, cambiar el otro (o pasar el ancho como argumento).
- **`_elegir_base`** (botón "Otra carpeta..."): idéntico en `visor.py` ~línea 910 y `comparar.py` ~línea 194.
- **Arranque de cada pestaña** (imports de tkinter/matplotlib y variables base): `visor.py` ~708 y `comparar.py` ~36.
- **`_num`** (pasar a número o None): tres versiones apenas distintas en `scripts/informe.py`,
  `scripts/procesar_carpeta.py` y `tests/referencia.py`. No unificar sin revisar las diferencias (la de
  `referencia.py` devuelve texto en vez de None).
- `visor.py` ~línea 855: un comentario repetido.

## 4. Dudas abiertas
- **D4, reglas que salieron de pocos videos:** meseta de k más bajo; piso de 40 columnas; zona plana
  mejor que ancha; ±30 si > 20 % de bordes en el límite; error de modelo y `outlier_frac` sin umbral.
- **D5:** `signal_check` nunca se probó con un video real sin contracciones.
- **H38:** sin `--frecuencia-estimulo`, espontáneas agrupadas pueden salir "estimuladas" (28 % en el
  barajado de Video_prueba). Hoy lo protege la búsqueda dirigida.
- **H13: medido, falta decidir** — `data/_mediciones_fases/h13_ruido_asimetrico/`. El control solo se
  equivoca de forma GRAVE (informar contracciones inventadas) con ruido asimétrico **a favor** de las
  contracciones: 18 eventos donde hay 6. Hacia el otro lado y con rebote ≥ 30 % se equivoca siempre
  hacia "no informar" (eso explica 613 y 341). La asimetría **ya se guarda como diagnóstico** (hecho el
  2026-10-27, sin umbral). **Falta decidir el piso de ancho** (sección D del LEEME): un piso de 2
  fotogramas no tocaría 16 de los 20 videos y limpiaría 14 de los 24 de 613, pero sacaría 1 de los 29
  de Video_prueba —el de 7.28 s, que tiene la altura de una contracción (24.9 × el ruido) y la forma de
  un artefacto (1 fotograma, justo después de un hueco de 0.4 s en la grabación).
