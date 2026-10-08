# Notebook de flujo paso a paso (pedido de Tecnun)

**Fecha:** 2026-09-05

> **Documento histórico (archivado 2026-10-08).** Describe la primera versión del cuaderno, anterior a la v4: detectaba
> sobre el grosor y daba 26 eventos en Video_prueba (hoy son 29, sobre `center_px`). El cuaderno vigente es
> `Analisis_Contractilidad_v4.ipynb`, en la raíz del repo.

**Entregable:** `gel_contractility/Analisis_Contractilidad.ipynb` (en
`Facultad/Espana/Análisis_de_Datos/gel_contractility_pipeline/gel_contractility/`)

## Contexto
Tecnun envió `Contraction_Analysis.mlx` (live script de MATLAB, autor Andrés Felipe
Zemanate-Largo) y pidió el equivalente para nuestro pipeline de Python: un documento que muestre
qué entra y qué sale en cada paso.

## Qué se hizo
Notebook de 11 secciones que llama a los módulos reales de `src/` (no reimplementa nada) y se
detiene en cada etapa para mostrar la figura o tabla intermedia:

0. Entorno · 1. Parámetros (todo lo ajustable en una sola celda) · 2. Lectura del vídeo y mapa de
máxima intensidad · 3. Gauge region · 4. CLAHE + perfil de intensidad/gradiente de una columna ·
5. Overlay RANSAC inlier/outlier · 6. Serie temporal completa · 7. Línea base, ruido y umbral ·
8. Detección de contracciones · 9. Meseta del umbral + control de falsos positivos · 10. Ritmo y
segmentación · 11. Exportación. Cierra con una tabla de correspondencia sección-por-sección
contra el `.mlx`.

## Verificación
Ejecutado de punta a punta sobre `Video_prueba.mp4` (2007 fotogramas, 29.73 fps, 1920×1080).
Salida idéntica a la que ya estaba en `data/processed_data/Video_prueba/`:

- grosor por fotograma: diferencia máxima 2.3e-13 px
- 26 eventos, tiempos y amplitudes con diferencia 0.0
- 3 segmentos: 1.749 Hz (17 ev., CV 4.0 %), 3.303 Hz (4 ev., CV 5.4 %), 0.099 Hz (5 ev., CV 0 %)
- control de falsos positivos: 26 abajo / 1 arriba → señal por encima del ruido

## Diferencias de fondo respecto del flujo de MATLAB (para explicarlas si preguntan)
1. El `.mlx` arranca de un `.txt` de tiempo/amplitud ya existente; el notebook cubre además cómo
   se construye esa señal desde el vídeo.
2. En el `.mlx` hay escalas temporales fijas (`MinPeakDistance`, `Window_size`); acá todas las
   ventanas se derivan del ancho de evento medido en los propios datos.
3. El notebook agrega verificación estadística del umbral (meseta) y control de calidad visual
   del borde, que el `.mlx` no tiene.

## Pendiente / opcional
- Export a HTML ejecutado (`jupyter nbconvert --to html`) si en Tecnun lo quieren ver sin Jupyter.
- El notebook corre con `PX_TO_MM = 1.0`: los resultados quedan en píxeles hasta que se calibre.
