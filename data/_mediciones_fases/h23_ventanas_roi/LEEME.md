# H23: ventanas de suavizado de la ROI, ¿con la imagen o con el gel? (2026-10-10)

**Hoy:** en `auto_detect_roi`, la mediana del perfil de grosor y de los bordes guía usa `k = w // 60` (32 px) y el promedio antes de la pendiente `d = w // 50` (38 px), con `w` = ancho de la IMAGEN. Los 11 videos miden 1920 px, así que hoy son constantes.

**Cómo:**
- `medir_h23.py`: ROI de los 11 videos con una copia de la función con las ventanas cambiadas (el código del repo no se toca). Variantes: `gel` (k y d proporcionales al grosor del gel, iguales a hoy en Video_prueba, 294 px), y ×0.5 y ×2 (para ver si la ventana importa). Tabla: `tabla_h23.csv`.
- `reprocesar_h23.py`: los 11 reprocesados desde el video con la variante `gel`, huella contra la referencia congelada (`reproceso_gel.jsonl`).

**¿Importa la ventana?** Sí: con ×0.5 o ×2 la ROI cambia en 9 de 11 videos (solo 583 y 613 quedan igual con las dos) (por ejemplo 063 con ×0.5 pasa de la zona plana 875–1039 a 390–1423). O sea: el tamaño de la ventana no es inocuo, y hoy está fijo a ojo (H23 tenía razón en que es un parámetro atado a otra cosa que el gel).

**Variante `gel` (la que pedía H23), reprocesada desde el video:**

| video | ROI | resultado |
|---|---|---|
| Video_prueba, 063, 268, 583, 491, 613, 304 | igual | **idéntico bit a bit** |
| 466 | igual (guía 1 px distinta en 4 % de columnas) | mismos eventos, k, período, amplitud y TTP; `center_px` distinto; ruido 0.1824 → 0.1808 px |
| 476 | igual (guía distinta en 7.5 %) | ídem; ruido 0.1149 → 0.1134 px |
| 068 | 391–542 → 381–532 | sigue NO REPORTABLE (0 eventos) |
| **341** | **427–946 → 428–785** | sigue NO REPORTABLE, pero candidatos 22 → 38 y el "mejor tren" 0.81 → 1.61 s |

**Conclusión:** escalar con el gel **no cambia ningún número informado** en los 7 reportables (mismos eventos, instantes, k, período, amplitud, TTP/RT50; solo el ruido de 466 y 476 en la tercera cifra). Cambia la zona de dos NO REPORTABLES (068, 341). Como hoy todos los videos tienen el mismo ancho de imagen y grosores parecidos, la diferencia práctica es casi nula; importaría con un video de otra resolución o con otro aumento (gel mucho más finito o más grueso en píxeles). **Propuesta: no cambiarlo ahora** (rompe la regresión exacta de 466, 476, 068 y 341 sin mejorar nada medible) y anotar que la ventana se escale con el gel el día que llegue un video de otra resolución o aumento. Decide Franco.
