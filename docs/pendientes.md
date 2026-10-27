# Pendientes (solo lo abierto)

Actualizado 2026-10-26. **Lista única de lo que falta.** Lo hecho y cómo se decidió está en
`docs/historia/pendientes-hasta-2026-10-26.md` (copia completa de la lista anterior) y en los
LEEME de `data/_mediciones_fases/` (índice: `data/_mediciones_fases/LEEME.md`).
Regla: cuando algo se termina, se borra de acá y se anota en una línea en `ESTADO` (historia).

## 1. Próximo (no depende del equipo)
- **Videos de Andrés:** pasos 2 y 4 ya rehechos (commit "Resultados de Andres rehechos"). Falta solo mirar en
  Windows cómo se ve la respuesta forzada en la ventana (Números y Comparar).
- **Textura en 583/466/063/268:** por qué textura los deja NO REPORTABLES o cambia el conteo (583 ve
  la vibración; 466 parte un evento, 5 → 6; 063/268 pierden la meseta con la ventana de 1.5 s).
  Hoy se miden con bordes: no afecta resultados.

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
- **H13:** el control con la señal invertida supone ruido simétrico (sin caso real).
