# H16: deriva con ventana en segundos en vez de en fotogramas (2026-10-10)

**Pregunta:** con fotogramas perdidos, la mediana de la deriva (que cuenta fotogramas) cubre más tiempo que el
nominal en el 4–24 % de las ventanas (466: hasta +0.6 s). ¿Cambia algo medirla en segundos?

**Cómo:** `medir_h16.py` rehace el reporte de los 11 videos de las dos formas, sobre las series guardadas. No toca
el código. Salida: `salida.txt`.

**Resultado:** mismos eventos, instantes, k, meseta y TTP/RT50 en todos los reportables; el ruido cambia ≤ 2.3 %
y el período en la 5.ª decimal. Solo 341 (NO REPORTABLE) pasa de 22 a 23 candidatos. **Cerrado, sin cambios.**
