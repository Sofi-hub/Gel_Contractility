# B2: ruido estimado solo en los tramos quietos (2026-10-10). EN ESPERA

    python data/_mediciones_fases/b2_ruido_quieto/medir_b2.py [corte_MAD=5] [margen_s=0.5]

Rehace el reporte sobre las series guardadas de los 11 videos, una vez como hoy y
otra con el ruido calculado solo en los fotogramas quietos (se saca lo que pasa de
`corte`·ruido hacia los DOS lados, `margen` s alrededor, y se repite hasta que el
ruido no cambia). Solo reemplaza el ruido que fija el umbral (`escaneo_estabilidad`
y `analizar`); el signo y la duración de los eventos quedan como hoy. No toca el
código del repo: arma una copia en memoria de `contraction_report.py`. Si se cambian
esas líneas del reporte, el `assert` del script avisa.

Salida: `salida_corte5_margen0.5.txt`. Resumen:
- Seis validados y 476: mismos eventos, instantes, período y amplitud. El ruido baja
  2–27 % y k sube en la misma proporción: el umbral en px casi no cambia.
- 341: ruido 0.103 → 0.037 px, 22 → 98 candidatos, falsos de control 4 → 33: sigue
  NO REPORTABLE (actividad hacia los dos lados: caso C1).
- 613: 24 → 46 candidatos, 23 → 39 falsos: sigue NO REPORTABLE.
- 068, 304: sin cambios.

Pendiente para la próxima vez: probar la sensibilidad a `corte` (4, 5, 6) y `margen`
(0.3, 0.5, 1 s), y buscar un video reportable con mucha actividad donde el ruido
inflado haga perder eventos (es el único caso en que B2 serviría).

## Tiempo

Calcular el ruido así es instantáneo. Lo que se alarga es el reporte cuando hay
muchos candidatos: 341 pasa de 10 a ~300 s y 613 de 21 a 98 s. Perfilado en 341
(cProfile, 295 s en total): el 99.9 % está en `rhythm_split._z_nulo`, el test nulo
del ritmo, que repite `buscar_grilla` 1000 veces; adentro, `_contar_vectorizado`
(280 s), sobre todo `np.round` (53 s) y sumas (26 s). Crece con la cantidad de
candidatos. Afecta también al reporte actual (341 tarda 10 s, 613 21 s). Anotado en
pendientes, B3 (tiempo).
