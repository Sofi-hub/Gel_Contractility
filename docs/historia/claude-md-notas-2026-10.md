# Notas sacadas de CLAUDE.md (2026-10-26)

Texto movido tal cual para achicar CLAUDE.md; en CLAUDE.md queda un resumen de una o dos líneas.

> **Fase 4 (2026-10-07): verificado por un método independiente.** La traslación
> medida por correlación de intensidad (sin bordes, `motion_check` arreglado)
> coincide con `center_px` en magnitud: 0.96 en Video_prueba, 0.99 en 063, 0.88 en
> 466 y 0.82 en 476 (las dos últimas, de la tanda EXP5, sin explicar).
> **2026-10-10 (D1):** medido evento por evento (la pendiente de `motion_check` se
> achica con el ruido), 476 da 0.99; 268, 466 y 491 dan 0.86–0.88 y el resto
> 0.96–0.99. No es cosa de EXP5. Desde entonces `motion_check` juzga el tamaño
> contracción por contracción. Detalle en `docs/pendientes.md` D1.


---

> **CORRECCIÓN (2026-09-30).** La versión anterior de este documento decía que
> "sólo el 13–19 % de ese movimiento es cambio de grosor" y que el cociente era
> el mismo en todos los videos. Medido sobre seis: **depende del video**. 18 %
> en Video_prueba y 13 % en Video_063, pero 1–2 % y **no significativo**
> (1.0–1.1 σ) en Video_268 y Video_583. El argumento se sostiene —de hecho se
> refuerza—, pero el número no es una constante del montaje.


---

El trabajo es para que **la Universidad de Tecnun** mida contracciones en sus células. El equipo usa MuscleMotion y a veces
tiene errores; este proyecto busca un método propio, más robusto y verificable. La carpeta
`data/raw_videos/OK-20260904T142817Z-1-001/OK/` (la misma donde están los videos crudos) tiene **los videos que cumplen los
requerimientos de Tecnun** (no hay un criterio técnico escrito), cada uno con una subcarpeta `<video>_-Contr-Results` con la salida
de MuscleMotion: `contraction.txt` (contracción), `speed-of-contraction.txt` (velocidad de contracción), `Overview-results.txt`,
`Log_file.txt` y tres `.jpg`. **"OK" no significa que MuscleMotion haya medido bien** (ver `docs/comparacion-musclemotion.md`).
Hay otra carpeta hermana, `RARITOS-…/RARITOS/`, con los videos que MuscleMotion maneja mal: procesados el 2026-10-07
(resultados en `docs/raritos.md`).
Detalle en `docs/contexto-tecnun-y-musclemotion.md`.

