# Protocolo de análisis por video

Actualizado 2026-09-29. Validado sobre seis videos: Video_prueba, Video_063 y
los cuatro de la batería (268, 466, 491, 583).

## Reglas centrales

**1. Detectar sobre `center_px`, no sobre `thickness_px`.** La contracción en
este montaje es mayormente un desplazamiento vertical de toda la franja; el
grosor es la resta de los dos bordes y por lo tanto es ciego a esa
componente. El grosor sigue sirviendo como medida biomecánica (vía promedio
de eventos alineados), no como canal de detección.

**2. El eje temporal sale de los timestamps del contenedor, no de
`fotograma / fps`.** Correr siempre con `--base-tiempo pts`. Ver
`claude/base-de-tiempo-y-frames-perdidos.md`.

**3. El `k` se elige dentro de la meseta, y eso ya es automático.** No pasar
`--k` a mano salvo que quieras contradecir al escaneo, y en ese caso
justificarlo.

## Comandos por video

    python main.py --video "<video>" --output-dir data/processed_data/<nombre> \
           --base-tiempo pts
    python scripts/contraction_report.py \
           --input data/processed_data/<nombre>/serie_temporal.xlsx \
           --frecuencia-estimulo 0.1

Opcional, cuando algo huele raro:

    python scripts/motion_check.py --video "<video>" --output-dir <carpeta>
    python scripts/signal_check.py --input .../serie_temporal.xlsx --column center_px

Para que el pipeline **aborte** en vez de emitir números con una ROI mala:

    python main.py ... --exigir-roi

## Chequeos de aceptación por video

1. **ROI**: `00_roi_profile.png` y la hoja `resumen`. Variación de grosor
   dentro de la ROI **< 6 %**. La hoja registra `ROI cumple criterio`
   directamente. Métodos aceptables: `gauge_plana`, `gauge_cintura`,
   `gauge_rescate_plana` o `manual`. Si sale `solo_nitidez`,
   `franja_completa` o `fallback_margin`, mirar el perfil y forzar con
   `--x-start/--x-end`.
2. **`outlier_frac` medio < 10 %.** Si sube, correr el diagnóstico de
   outliers: si salen **contiguos** es el modelo que no sigue la geometría
   del borde (achicar o mover la ROI, o subir `--ransac-degree`); si salen
   **dispersos** son burbujas y se toleran.
   > Cuidado: los dos primeros chequeos pueden tirar para lados distintos.
   > En Video_466 la ventana más ancha y plana (944–1169, 5.77 %) deja 16 %
   > de outliers, y una ventana más angosta (700–900, 5.47 %) deja 7.9 %.
   > Gana la que cumple los dos.
3. **Meseta del escaneo de estabilidad.** Ya es automático: el reporte
   imprime el `k` elegido y el rango de la meseta, y la hoja `resumen` graba
   `hay_meseta` y `conteo_reportable`.
4. **Si no hay meseta, el conteo no se reporta.** El reporte lo marca
   `[NO REPORTABLE]`. No bajar `k` para "encontrar" eventos.
5. **Fotogramas perdidos.** La hoja `resumen` trae `frames faltantes (%)`. Por
   encima del 1 % el pipeline avisa. Con `--base-tiempo pts` ya está
   corregido; con `frames` no.

## Métricas a tabular por video

`n_eventos`, `intervalo_mediano_s`, `amplitud_traslacion_px`,
`adelgazamiento_robusto_px`, `cociente_robusto_pct`, `ruido_canal_px`,
`ruido_grosor_px`, más `k_usado`, `meseta_k_rango` y `conteo_reportable`.
Todas salen en `contracciones.xlsx`.

**Cinética (desde 2026-09-29):** `ttp_s`, `rt50_s`, `amplitud_relativa_pct`,
con `ttp_reportable` y `rt50_reportable`. Si `*_reportable` es `False`, el
valor es NaN a propósito: se tabula la cota `ttp_cota_sup_s` como
"TTP < X ms", **nunca** como un valor. Es reportable sólo si el conteo es
reportable y la mediana de fotogramas de la subida (o de la bajada al 50 %) es
≥ 5. La amplitud relativa es respecto del **grosor en reposo**, no se calibra
y sí se puede comparar entre videos grabados a distinto aumento. Detalle por
evento en la hoja `cinetica_<serie>`; figura `11_cinetica_*.png`.

**`cociente_robusto_pct` va con signo.** Positivo = el gel adelgaza;
negativo = engruesa. Hasta el 2026-09-29 el código tomaba la magnitud y un
engrosamiento se leía como adelgazamiento.

## Prueba de CLAHE: resuelta, CLAHE se queda encendido

Video_063 procesado con y sin CLAHE:

| | CLAHE ON | CLAHE OFF |
|---|---|---|
| eventos detectados | 5 | 5 |
| tiempos | idénticos | idénticos |
| amplitud traslación | 1.514 px | 1.481 px |
| **ruido de `center_px`** | **0.0338 px** | 0.0495 px |
| **ruido del grosor** | **0.0652 px** | 0.0970 px |

CLAHE mejora el SNR ~1.5× y no fabrica ni deforma la señal: la amplitud
medida cambia 2 %. Dejarlo encendido por defecto.

Nota aparte: la correlación punto a punto entre las dos versiones da r = 0.90
para `center_px` pero sólo **r = 0.52 para el grosor**. Buena parte de la
fluctuación del grosor depende del preproceso, no del gel. Otro argumento
para no detectar sobre grosor.

## Lo único que falta para el argumento contra MuscleMotion

Un **video de control donde SOLO cambie la luz y el gel no se mueva**: mismo
campo, mismo gel, quieto, con un cambio de iluminación gradual o un
parpadeo. La afirmación "nuestro método es inmune a cambios sutiles de
iluminación" hoy es teórica (medimos geometría de borde, no intensidad); ese
video la vuelve un número.

Lo que **sí** está medido contra MuscleMotion está en
`claude/comparacion-musclemotion.md`: sobre-detección (35 y 47 picos donde
hay 6 y ninguno certificable), ausencia de control de falsos positivos, y una
escala temporal comprimida entre 0.65 % y 4.05 % según el archivo.

## Pendiente administrativo

`--px-to-mm` sigue en 1.0: todos los "mm" de las salidas son píxeles. Por
decisión del proyecto no se calibra; las comparaciones entre videos se hacen
en términos relativos o dentro de un mismo aumento.
