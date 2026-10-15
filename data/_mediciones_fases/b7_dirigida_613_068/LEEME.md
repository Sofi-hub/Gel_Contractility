# B7 — búsqueda dirigida a 0.1 Hz en 613 y 068 (2026-10-15)

El equipo confirmó 0.1 Hz para todo video con voltaje en el nombre. **Solo medido.**

## 1. Pasar `--frecuencia-estimulo 0.1` (`medir.py`, `tabla.csv`)
La detección no depende de la frecuencia: mismos candidatos y mismo k.

| video | frecuencia | candidatos | reportable | tren a 0.1 Hz |
|---|---|---|---|---|
| 613 | libre | 24 | NO | no (p = 0.90) |
| 613 | 0.1 dirigida | 24 | NO | "ningún tren de 4 o más eventos" |
| 068 | libre / 0.1 | 0 | NO | (sin eventos) |

## 2. Promedio plegado a 10 s (`plegado.py`, `tabla_plegado.csv`, `plegado_10s.png`)
Sin usar eventos: se promedian los tramos de 10 s (desde 8 s) y se mira si aparece un pico, contra 6 períodos de control (7.3–13.7 s).

| video | SNR a 10 s | SNR controles | pico (% grosor) |
|---|---|---|---|
| 063 | 132 | 18–27 | 0.56 |
| 268 | 56 | 10–25 | 0.52 |
| 466 | 33 | 4–11 | 1.78 |
| 583 | 78 | 4–18 | 1.11 |
| 476 | 19 | 6–10 | 0.51 |
| **613** | **6.5** | 4–11 | 0.07 |
| **068** | **3.9** | 2.5–5 | — (actividad) |

En los 5 con tren la respuesta salta a la vista; en **613 y 068 no hay respuesta al estímulo distinguible del azar**, ni siquiera promediando. En 613, si responde, es < ~0.07 % del grosor (las demás: 0.5–1.8 %).

## Propuesta
- Pasar 0.1 Hz en 613 y 068 en `tests/referencia.py` **no cambia ningún número informado** (siguen NO REPORTABLES); solo cambia el texto del ritmo de 613 y su huella (`n_estimulados`/`periodo_s` de la búsqueda libre). Requiere `--aprobar`.
- El plegado a 10 s podría ser un diagnóstico nuevo ("¿hay respuesta al estímulo?") para videos difíciles, sin cambiar números. No implementado.
