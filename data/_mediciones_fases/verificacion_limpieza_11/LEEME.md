# Mediciones de la tarde (2026-10-10), sin tocar el código

Las tres se corrieron en la máquina de prueba con el código vigente (después de H14). No se
implementó nada: son mediciones para decidir. Destino sugerido en el repo:
`data/_mediciones_fases/` (una subcarpeta por medición).

## 1. Verificación de la limpieza en los 11 videos (`verificacion_11_videos/`)
Los 11 reprocesados desde el video con el código de hoy.
- `center_px`, `y_top_px` y `y_bottom_px` **idénticos bit a bit** a los resultados vigentes en los 11.
  `thickness_px` difiere en ~1e-12 px (redondeo de punto flotante al guardar).
- Reporte: los 11 **IGUAL** a la referencia congelada.
- **`min_gradient` (H28):** no actúa nunca en 10 de los 11. Solo actúa en **068**: 9134 de 368600
  bordes (2.5 %), en el video con actividad continua y borde que se sale de ±15. El gradiente más
  bajo en los otros 10 es 9 (476); el umbral es 5. **Confirmado: se queda** como protección.

## 2. H30: umbral y cantidad de intentos de RANSAC (`h30_ransac/`)
11 videos, tres variantes contra lo actual (3 × MAD, 200 intentos).
- **1000 intentos en vez de 200:** idéntico bit a bit en los 11. El corte dinámico (99 %) termina
  antes de llegar a 200: `max_trials` nunca limita. No hay nada que cambiar.
- **Umbral 2 × MAD (más estricto):** peor. Descarta el doble de columnas, el ruido sube en 10 de 11
  y **063 pierde un evento (6 → 5)**; 268 pasa de 6 a 5 estimulados.
- **Umbral 4 × MAD (más permisivo):** mixto. Mismos conteos en los 7 reportables y ruido 9–14 % menor
  en Video_prueba, 063 y 583, pero **sube** en 466 (+6 %) y cambian instantes en 466 y 476
  (`center_px` hasta 0.8 px distinto en 466). En 341 (NO REPORTABLE) cambia de 22 a 0 candidatos.
- Conclusión: **3 × MAD se queda.** Ningún umbral gana en todos; el del 2 rompe 063.
  La duda de H30 ("una burbuja que corre 2 px no se descarta") no tiene caso real medido.

## 3. B2: sensibilidad del ruido "solo en tramos quietos" (`b2_sensibilidad/`)
Corte 4, 5 y 6 MAD × margen 0.3, 0.5 y 1 s, en los 7 reportables (63 combinaciones).
- **En las 63: mismos eventos y mismos instantes** que hoy. El ruido baja entre 0 y 27 %
  (Video_prueba siempre lo que más, 063 casi nada).
- Confirma lo medido antes: es estable frente a los parámetros, pero hoy no cambia ningún resultado.
  Sigue en espera hasta que aparezca un video reportable con mucha actividad.
- No se corrieron 613, 068, 304 y 341: con ruido bajo tienen cientos de candidatos y el reporte
  tarda minutos cada uno; ya se sabe que siguen NO REPORTABLE.
