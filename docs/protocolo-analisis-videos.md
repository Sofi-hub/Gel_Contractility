# Protocolo de análisis por video

Actualizado 2026-10-08. Validado sobre seis videos (Video_prueba, Video_063, 268, 466, 491 y 583)
y aplicado a los cinco `RARITOS` (476, 613, 068, 304 y 341; ver `raritos.md`). Para correrlo y
entender la consola: `guia-salida-consola.md`. Este documento dice qué mirar **antes de informar
un número**.

## Reglas centrales

**1. Detectar sobre `center_px`, no sobre `thickness_px`.** La contracción en
este montaje es mayormente un desplazamiento vertical de toda la franja; el
grosor es la resta de los dos bordes y por lo tanto es ciego a esa
componente. El grosor sigue sirviendo como medida biomecánica (vía promedio
de eventos alineados), no como canal de detección.

**2. El eje temporal sale de los timestamps del contenedor, no de
`fotograma / fps`.** Correr siempre con `--base-tiempo pts`. Ver
`docs/base-de-tiempo-y-frames-perdidos.md`.

**3. El `k` se elige dentro de la meseta, y eso ya es automático.** No pasar
`--k` a mano salvo que quieras contradecir al escaneo, y en ese caso
justificarlo.

## Comandos por video

Los comandos (y la ventana `Analizar.bat`, que corre los mismos) están en
`guia-salida-consola.md`, sección 1. Lo que importa para el protocolo:

- `--frecuencia-estimulo` decide dónde se busca el tren (solo a ±10 % de esa
  frecuencia). Si el protocolo cambió de frecuencia, pasar todas
  (`--frecuencia-estimulo 0.1 0.2`); si no se sabe, omitirlo (búsqueda libre). Si
  hay tren, la cinética principal es la de los estimulados; la hoja `cin_grupos_*`
  tiene todos, estimulados y espontáneos.
- Si `main.py` avisa que muchos fotogramas quedaron sin borde (el gel se mueve más
  de ±15 px), repetirlo con `--half-window 30` en otra carpeta (`<video>_hw30`).
- `--exigir-roi` hace que `main.py` **aborte** en vez de emitir números con una
  zona mala.
- Opcionales cuando algo huele raro: `motion_check.py --video ... --serie
  .../serie_temporal_<video>.xlsx` (confirma el movimiento por intensidad) y
  `signal_check.py --input .../serie_temporal_<video>.xlsx` (¿hay población de eventos?).

## Chequeos de aceptación por video

1. **ROI**: `00_roi_profile_<video>.png` y la hoja `resumen`. Variación de grosor
   dentro de la ROI **≤ 6 %**. La hoja registra
   `ROI cumple criterio` directamente: **ése es el criterio**, sea cual sea el
   método que eligió la zona (el método solo dice por qué se eligió; una zona
   `manual` también tiene que cumplirlo, H18). Si no cumple, mirar el perfil y,
   si hace falta, forzar con `--x-start/--x-end`. La hoja trae también `n_columnas usadas`
   (60, o menos en una ROI angosta, nunca menos de 40) y `ROI contiene cintura`
   (tiene que ser 1). Ningún video (validados ni RARITOS) necesitó ROI manual.
   `main.py` avisa en pantalla solo si la variación supera el 6 % o la zona no
   contiene la cintura; el detalle de la zona está en `resumen` y en la hoja
   `roi_alternativas`.
2. **Ajuste del borde: diagnóstico, no criterio (Fase 4, H24).** La hoja
   `resumen` trae `outlier_frac medio` y `error de modelo borde sup/inf (px)` (y
   `peor / grosor (%)`). **No tienen umbral**: el viejo "outlier_frac < 10 %"
   ordenaba las ROIs al revés del ruido del canal (063 y 466). Sirven para
   comparar y para mirar videos raros: si el error de modelo es alto, correr el
   diagnóstico de outliers; outliers **contiguos** = el modelo no sigue el borde,
   **dispersos** = burbujas. Valores de los seis validados: error de modelo
   0.33–1.01 % del grosor, `outlier_frac` 2.0–10.5 % (RARITOS: 0.06–1.04 % y 2.5–5.2 %).
   **Ojo con vibraciones:** si a ojo tiembla toda la imagen (Video_583, 72–74 s;
   Video_613), eso entra en `center_px` como si fuera contracción. Si va hacia los
   dos lados el control lo delata (NO REPORTABLE); si no, el reporte no lo distingue.
3. **Meseta del escaneo de estabilidad.** Ya es automático: el reporte
   imprime el `k` elegido y el rango de la meseta, y la hoja `resumen` graba
   `hay_meseta` y `conteo_reportable`.
4. **Si no hay meseta, el conteo no se reporta.** El reporte dice
   `RESULTADO: NO REPORTABLE` y las figuras lo llevan en el título, con los
   candidatos en gris y los falsos de control dibujados. No bajar `k` para
   "encontrar" eventos. Mirar el video para distinguir vibración (picos a los dos
   lados, 613) de actividad continua del tejido (sin pausas, 068 y 304).
5. **Fotogramas perdidos.** La hoja `resumen` trae `frames faltantes (%)`. Por
   encima del 1 % el pipeline avisa. Con `--base-tiempo pts` ya está
   corregido; con `frames` no.

## Métricas a tabular por video

**Métrica de contractilidad (Fase 3): una sola, la traslación de la franja.**
`amplitud_relativa_pct` (% del grosor en reposo: cifra principal, comparable
entre videos) y `amplitud_px` al lado (del mismo grupo que el %; comparable solo a igual
aumento). `amplitud_traslacion_px` es la mediana de TODOS los eventos: no ponerla al lado del % (H40). El **adelgazamiento** (`adelgazamiento_robusto_px`,
`cociente_robusto_pct`) **no se reporta**: es un diagnóstico, porque depende del
preproceso (con y sin CLAHE, Video_prueba 18 % contra 9 %; 268 y 466 cambian de
signo).

Además: `n_eventos`, `intervalo_mediano_s`, `ruido_canal_px`, `k_usado`,
`mesetas` y `conteo_reportable`. Desde la Fase 3, `ruido_borde_sup_px`,
`ruido_borde_inf_px` y `cociente_ruido_bordes`: si un borde es mucho más
ruidoso que el otro, revisar la ROI y ese borde (H54; todavía sin umbral).
Todas salen en `contracciones_<video>.xlsx`.

**Desde la Fase 2.2 (2026-10-01)** además: `win_s_usado` (ventana del detrend,
automática), `conteo_por_ventana` (el conteo con 0.75×, 1× y 1.5× esa ventana:
tiene que coincidir para que sea reportable), `mesetas` (todas las mesetas del
escaneo; si hay más de una, decirlo al reportar) y `motivo_no_reportable`.

**Cinética (desde 2026-09-29):** `ttp_s`, `rt50_s`, `amplitud_relativa_pct`,
con `ttp_reportable` y `rt50_reportable`. Si `*_reportable` es `False`, el
valor es NaN a propósito: se tabula la cota `ttp_cota_sup_s` como
"TTP < X ms", **nunca** como un valor. Es reportable sólo si el conteo es
reportable y la mediana de fotogramas de la subida (o de la bajada al 50 %) es
≥ 5. La amplitud relativa es respecto del **grosor en reposo**, no se calibra
y sí se puede comparar entre videos grabados a distinto aumento. Detalle por
evento en la hoja `cinetica_<serie>`; figura `11_cinetica_*.png`.

**`cociente_robusto_pct` (diagnóstico) va con signo.** Positivo = el gel adelgaza;
negativo = engruesa. Hasta el 2026-09-29 el código tomaba la magnitud y un
engrosamiento se leía como adelgazamiento.

## Prueba de CLAHE: resuelta, CLAHE se queda encendido

> **Fase 3 (2026-10-08), sobre los seis videos:** el conteo no depende de CLAHE
> (salvo efectos de umbral en 063 y 583) y la amplitud de la traslación cambia
> ≤ 4 %. Pero CLAHE desplaza los bordes de forma que varía con el tiempo: el
> **adelgazamiento** depende de él (por eso no se reporta), y con un
> desplazamiento conocido en Video_466 los bordes con CLAHE miden ~8 % de menos
> (sin CLAHE, exacto). Si en videos nuevos la amplitud con/sin CLAHE difiere más
> de ~5 %, reconsiderarlo. La tabla de abajo es la prueba original, sobre un solo
> video.

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
`docs/comparacion-musclemotion.md`: sobre-detección (35 y 47 picos donde
hay 6 y ninguno certificable), ausencia de control de falsos positivos, y una
escala temporal comprimida entre 0.65 % y 4.05 % según el archivo.

## Pendiente administrativo

`--px-to-mm` sigue en 1.0: todos los "mm" de las salidas son píxeles. Por
decisión del proyecto no se calibra; las comparaciones entre videos se hacen
en términos relativos o dentro de un mismo aumento.
