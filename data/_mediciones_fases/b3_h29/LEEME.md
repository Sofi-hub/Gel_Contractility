# B3 / H29: ¿un ajuste sin RANSAC es menos ruidoso? (2026-10-10)

Compara RANSAC (lo actual) contra mínimos cuadrados con todas las columnas válidas
(mismo polinomio de grado 2), en los 8 videos que corren con ±15. Misma ROI, mismos bordes.

- `medir_lsq.py <carpeta> <ransac|lsq> <salida>`: corre el pipeline con el ajuste
  elegido (~1 min por video) y guarda la serie en `res/` (no va a git).
- `analizar.py`: compara contra la corrida con RANSAC (`res/<video>__max15.pkl`, que sale
  de `../b1_ventana/medir.py`). Salida: `salida.txt`.

Ruido rápido = MAD de center_px menos su mediana de 9 fotogramas, fuera de ±1.5 s de los
eventos. Ruido del reporte = el que fija el umbral (MAD de la señal sin deriva).

Resultado: sin RANSAC el ruido rápido baja en todos, pero el ruido del reporte sube en
063 (0.024 → 0.121 px, ×5; pierde el evento espontáneo de 0.31 s: 6 → 5), 476, 268 y 583.
Mejora algo en 466 (0.182 → 0.164; mismos 5 eventos, TTP 255 → 224 ms) y en Video_prueba.
Conclusión: ningún ajuste gana en todos; RANSAC se queda (igual que el cierre del
2026-10-08 en el índice de hallazgos). Idea no medida: que `y_*_px` sea la mediana de la
curva solo sobre las columnas inlier (H29 nota que hoy incluye las descartadas).
