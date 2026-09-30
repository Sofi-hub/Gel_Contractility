# Reproceso de la batería con ROI forzada y fps = 30

Fecha 2026-09-29. Resultados en `data/processed_data/<video>_v4/`. Las
carpetas originales quedaron intactas.

## Comandos exactos

    python main.py --video "<video>.mp4" --output-dir data/processed_data/<n>_v4 \
           --fps 30 --x-start <A> --x-end <B>
    python scripts/contraction_report.py --input .../serie_temporal.xlsx \
           --frecuencia-estimulo 0.1 [--k <k>]

| video | `--x-start` | `--x-end` | `--k` |
|---|---|---|---|
| Video_268_EXP3_FAPS2_40V | 918 | 1336 | 8 (default) |
| Video_466_EXP5_FAPS4_40V | 944 | 1169 | 8 (default) |
| Video_491_EXP5_CTRL1_36HZ | 420 | 1206 | — |
| Video_583_EXP6_CTRL4_40V | 718 | 1187 | **12** |

Las ventanas no las elegí a ojo: calculé el perfil de grosor con
`auto_detect_roi` y barrí exhaustivamente la **ventana contigua más ancha con
variación < 6 % y ambos bordes nítidos**, que es el criterio de aceptación
del propio protocolo. Las cuatro quedaron en 5.62–5.86 %.

## El resultado principal: fps = 30 queda confirmado fuera de muestra

El hallazgo #3 se había derivado de Video_prueba y Video_063. Estos dos
videos **no se usaron para derivarlo**, así que son una verificación
independiente:

| | frecuencia medida | veredicto contra 0.1 Hz configurado |
|---|---|---|
| **antes** (fps declarado) | | |
| Video_268 | 0.0987 Hz | −1.3 %, sesgado |
| Video_583 | 0.0989 Hz | −1.1 %, sesgado |
| **ahora** (`--fps 30`) | | |
| Video_268 | **0.09993 ± 0.000038 Hz** | t = −1.84, **indistinguible** |
| Video_583 | **0.09997 ± 0.000100 Hz** | t = −0.30, **indistinguible** |

Jitter 9.9 ms y 34.6 ms, captura 100 % en los dos. El fps declarado producía
un sesgo sistemático de ~1 % que desaparece al forzar 30.000. **El pendiente
#3 queda cerrado: hay que reprocesar todo con `--fps 30`.**

## Calidad del ajuste: antes vs ahora

| | V268 antes | V268 ahora | V466 antes | V466 ahora | V491 antes | V491 ahora | V583 antes | V583 ahora |
|---|---|---|---|---|---|---|---|---|
| método ROI | solo_nitidez | manual | franja_completa | manual | gauge_cintura | manual | gauge_relajada | manual |
| variación ROI | 13.11 % | **5.62 %** | 164.63 % | **5.77 %** | 5.08 % | 5.86 % | 10.83 % | **5.83 %** |
| residuo borde sup | 1.427 px | **0.870 px** | 6.996 px | **0.867 px** | 0.962 px | 0.941 px | 0.956 px | **0.861 px** |
| outlier_frac | 5.72 % | **2.37 %** | 11.10 % | **16.17 %** ✗ | 4.20 % | 3.00 % | 4.37 % | 4.00 % |
| ruido del canal | 0.098 px | **0.053 px** | 0.211 px | 0.192 px | 0.063 px | 0.057 px | 0.076 px | 0.073 px |

Los residuos de los cuatro cayeron al rango de los videos validados
(0.77–0.87 px). El de Video_466 bajó un factor 8.

## Veredicto por video

**Video_268 — aceptado.** 6 eventos, meseta ancha de 6 en k = 8…20 con 0
falsos. Tren 5/5 ranuras, CV 0.1 %, jitter 9.9 ms, frecuencia indistinguible
de 0.1 Hz. Un dudoso en t = 61.7 s con amplitud 1.396 px contra 1.517 px de
los estimulados: es un latido del tren corrido, no una espontánea.

**Video_583 — aceptado, pero hubo que mover `k`.** Con el `k = 8` por defecto
salían 9 eventos (1 falso) y **`rhythm_split` no encontraba el tren**
(p = 0.025, no superaba el azar): los eventos espurios ensuciaban el ajuste.
Con `k = 12`, que es donde está la meseta (6 eventos en k = 12, 15, 20 con 0
falsos), el tren aparece limpio: 5/5, CV 0.4 %, jitter 34.6 ms. **Lección: el
`k` por defecto no siempre cae dentro de la meseta, y cuando cae afuera no
falla de forma visible — falla haciendo desaparecer el tren.**

**Video_491 — rechazado, sin eventos detectables.** Con la ROI buena y fps 30
el escaneo sigue sin meseta: 12 → 7 → 5 → 4 → 2 → 0, con falsos 16, 7, 2, 2,
1, 0. Los 4 "eventos" de k = 8 son dos pares (12.70/13.17 y 33.60/33.97), o
sea las dos excursiones bifásicas ya identificadas, contadas dos veces cada
una. No se reporta conteo.

**Video_466 — rechazado, por dos motivos nuevos.**
1. El `outlier_frac` **empeoró** con la ROI ajustada: 11.1 % → 16.2 %. El
   aviso del propio pipeline dice qué hacer: correr `inspect_frame.py` y ver
   si los outliers salen contiguos (modelo que no sigue la geometría) o
   dispersos (burbujas). Falta hacerlo.
2. Su frecuencia da **0.10515 ± 0.000414 Hz, un +5.15 % sobre lo
   configurado** (t = 12.4), con jitter de 133 ms contra 10–35 ms de los
   otros. El veredicto automático es "demasiado para ser la base de tiempo".
   Son 285.5 fotogramas por período contra 300.0 exactos de los otros cuatro
   videos. O ese video se grabó con otra configuración, o el estimulador no
   estaba en 0.1 Hz esa vez. **Hay que mirar el cuaderno de laboratorio.**

## El adelgazamiento se desploma al corregir la ROI

Éste es el resultado que cambia la historia, y no me parece un artefacto:

| | adelg. robusto | sigma | % de la traslación |
|---|---|---|---|
| Video_prueba (ref) | 0.565 px | 56.9 | 18.2 % |
| Video_063 (ref) | 0.191 px | 11.4 | 12.8 % |
| **Video_268 (v4)** | **0.022 px** | **1.0** | **1.5 %** |
| **Video_583 (v4)** | **0.030 px** | **1.1** | **1.0 %** |

En los dos videos aceptados el adelgazamiento **no es significativo**
(1.0 y 1.1 sigma). El 13–19 % de los videos validados **no se reproduce**: acá
la contracción es traslación casi pura. Eso refuerza el hallazgo #1 — detectar
sobre `center_px` no es una preferencia, es la única opción en estos videos —
pero obliga a revisar la afirmación "el 13–19 % del movimiento es
adelgazamiento", que por ahora vale sólo para Video_prueba y Video_063.

Los valores negativos que había visto antes (−0.08 y −0.41 px) eran, en
Video_268, un artefacto de la ROI rota: ahora da +0.022. En Video_466 sigue
negativo (−0.179 px, 3.0 sigma), pero ese video no pasa aceptación.

## Dos bugs confirmados en el código

**1. `contraction_report.py` crashea cuando no hay tren.** Video_491 abortó
con `KeyError: 'resumen_grupos'` en la línea 298, así que **no se generó su
`contracciones.xlsx`**. Pasa cuando `rhythm_split` no encuentra tren y además
no hay resumen de grupos. Es justo el caso de un video sin eventos, o sea el
caso en el que más importa que el reporte salga.

**2. `cociente_robusto_pct` pierde el signo.** Confirmado otra vez en el
reproceso: Video_466 tiene `adelgazamiento_robusto_px = −0.1787` y
`amplitud_traslacion_px = 4.0263`, o sea −4.44 %, y la tabla reporta
**+4.3704**. Un engrosamiento se lee como adelgazamiento.

## Causa raíz de la falla de ROI: `min_roi_width_frac = 0.35`

`auto_detect_roi` exige que la ROI cubra el **35 % de las columnas con gel**.
En estos videos el gel ocupa casi todo el cuadro (~1850 columnas), así que el
mínimo queda en ~647 px, mientras que las gauge regions reales miden 225–470
px. Ningún nivel estricto puede cumplirlo y la cascada cae hasta
`solo_nitidez` o `franja_completa`.

Ese 35 % está justificado en un comentario del propio código con el caso de
Video_063, donde el criterio estricto daba 164 px y eso era demasiado angosto.
Es decir: **el parámetro se fijó mirando un video y no generaliza** — el modo
de falla que el principio de trabajo del proyecto marca.

Sugerencia: que el mínimo sea absoluto (p. ej. 200 px, suficiente para que 60
columnas queden a más de 3 px) en vez de una fracción del gel, y que el
pipeline **aborte** si la variación dentro de la ROI supera el 6 %, en vez de
avisar y seguir emitiendo números.

## Cambios que hice en el código (en el contenedor, NO commiteados)

1. `main.py`: flag nuevo `--fps` (no existía; el fps salía sólo de la
   metadata del archivo).
2. `src/pipeline.py`: campo `fps_override` en `PipelineConfig` y su uso en
   `process_video`.
3. `main.py` + `src/pipeline.py`: la hoja `resumen` ahora registra
   `fps usado` y `fps declarado por el archivo`, para trazabilidad.

No toqué el bug del signo ni el crash: son decisiones tuyas.

## Qué sigue

1. Decidir si querés que commitee los tres cambios de código.
2. Arreglar los dos bugs.
3. `inspect_frame.py` sobre Video_466 para ver si los outliers son burbujas o
   modelo.
4. Buscar en el cuaderno a qué frecuencia se estimuló Video_466.
5. Reprocesar Video_prueba y Video_063 con `--fps 30` para que toda la serie
   quede en la misma base de tiempo.
