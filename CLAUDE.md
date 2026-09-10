# Proyecto: Análisis de Contractilidad de Geles 3D

## Objetivo Principal
Automatizar el análisis de la contractilidad mecánica de cultivos celulares 3D embebidos en geles. El sistema mide la deformación del material en el eje Y (reducción de grosor) a lo largo del tiempo de forma automatizada y reproducible.

## Arquitectura del Pipeline
1. **Mapeo Espacial (Auto-ROI):** Generación automática de un `maxProjectStack` a partir de los fotogramas del video crudo para guiar la ventana de búsqueda (sin depender de software externo).
2. **Detección Subpíxel:** Uso de gradientes y ajuste sigmoide para ubicar los bordes superior e inferior del gel con precisión de subpíxel.
3. **Robustez a Artefactos (Burbujas):** Cálculo del grosor en múltiples columnas usando RANSAC/mediana espacial para descartar columnas afectadas por burbujas o ruido local.
4. **Análisis de Señal:** Filtrado temporal de la curva con Savitzky-Golay y detección de picos (micro-contracciones basales y macro-contracciones) mediante `scipy.signal.find_peaks`.

## Stack Tecnológico y Librerías
* `opencv-python`: Procesamiento de imágenes (lectura de video, filtros, detección de bordes).
* `numpy`: Operaciones de matrices matriciales rápidas y matemática subpíxel.
* `scipy`: Filtrado de señales y detección dinámica de picos.
* `matplotlib`: Gráficos de series temporales y *overlays* de validación visual (QC).

## Reglas Estrictas para el Código
* **Cero dependencia externa:** El pipeline debe leer un `.avi` o `.mp4` crudo y hacer todo el proceso internamente. **Bajo ninguna circunstancia sugerir el uso de MUSCLEMOTION o ImageJ.**
* **Cero cajas negras:** Todo análisis debe permitir generar un output visual de diagnóstico (ej. dibujar los bordes detectados sobre un frame crudo) para validar los parámetros.
* **Manejo de Outliers:** Los problemas de iluminación o burbujas se resuelven estadísticamente por columnas, no "adivinando" datos faltantes.