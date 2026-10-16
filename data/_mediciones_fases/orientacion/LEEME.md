# Orientación del gel y videos de Andrés (2026-10-15)

Los videos nuevos (carpeta "Videos Andrés") tienen el gel **vertical**, más zoom, sin anclajes a la vista y una banda de transición entre el fondo y el gel.

## 1. Rotación automática (implementada; no cambia ningún número de los 11)
- `medir.py`: cociente = variación del perfil promedio en y / en x, sobre el mapa de máximos. Los 11 videos dan **3.0–13.8**; los mismos girados 90°, **0.07–0.33**; la captura de un video de Andrés, **0.05**. Regla: se gira 90° si el cociente es < 1, con aviso si está entre 0.5 y 2.
- `main.py --rotar auto|0|90|270` (default auto), igual en `motion_check.py`; el `resumen` guarda `rotacion (grados)`, `rotacion eleccion` y `cociente de orientacion`; el fotograma de la ventana se gira igual.
- Verificado: los 11 eligen 0 (regresión y `--completo` idénticos); `tests/test_orientacion.py`: el mismo gel sintético horizontal y vertical da el mismo pulso (3.03 px) y la misma forma.

## 2. Borde de estos videos: problema abierto (falta un video real)
`sintetico_vertical.py` arma un video con la captura (vertical, 5 pulsos de 4 px cada 10 s, ruido y 12 fotogramas desenfocados). Se gira bien, pero:
- en gris, la banda azulada es casi tan clara como el gel: el borde es una **rampa de ~100–150 px con textura granulada**, no un escalón;
- la detección toma el borde exterior (grosor ~900 px), con poca nitidez (5; validados 18–51) y el borde pegado al límite de la ventana en el 98 % de los fotogramas;
- ruido de la señal 0.72 px (validados 0.03–0.18): los pulsos de 4 px **no se detectan** (NO REPORTABLE).
- `probar_suavizado.py`: suavizar a lo largo del borde (sigma 8 y 20 px) no lo arregla.

La captura está comprimida y achicada: no alcanza para decidir. Con un video real: (a) ver qué borde es el físico; (b) probar ventana de búsqueda adaptada al ancho de la rampa; (c) medir la traslación por correlación de la textura (como `motion_check`, que ya existe), que con esta textura podría ser lo más robusto.
