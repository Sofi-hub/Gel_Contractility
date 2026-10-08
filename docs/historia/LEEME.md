# Historia del proyecto

Documentos de etapas **ya cerradas**. Explican cómo y por qué se tomó cada decisión, con las mediciones de ese momento. **No describen el estado actual**: para eso, `../ESTADO-arranque-chat-nuevo.md` y `../../CLAUDE.md`. Los números de acá pueden estar superados, y las rutas `claude/...` que aparecen adentro corresponden hoy a `docs/` o a `docs/historia/`.

En orden cronológico:

| documento | etapa | qué se decidió |
|---|---|---|
| `notebook-flujo-tecnun.md` | 2026-09-05 | primer cuaderno paso a paso, pedido por Tecnun (anterior a la v4) |
| `diagnostico-video063-roi-y-ransac.md` | 2026-09-09 | rondas 1–3: ROI y RANSAC sobreajustados; **la contracción es un desplazamiento y se detecta sobre `center_px`** |
| `diagnostico-bateria-4videos.md` | 2026-09-29 | la ROI automática no generalizaba a 268, 466, 491 y 583 |
| `reproceso-bateria-v4.md` | 2026-09-29 | reproceso con ROI forzada; se confirma el fps real de 30 |
| `cambios-roi-y-k.md` | 2026-09-29 | ancho mínimo de la ROI sin depender del largo del gel; `k` automático por meseta |
| `guia-revision-codigo.md` | 2026-09-30 | cómo se organizó la revisión de todo el código |
| `hallazgos-revision-codigo.md` | 2026-09-30 → 10-07 | los hallazgos H1–H55 de la revisión y su implementación (el detalle de cada H que se cita en otros documentos) |
| `glosario-revision-codigo.md` | 2026-09-30 | glosario para leer los hallazgos |
| `propuesta-fase-2-2.md` | 2026-10-01 | qué es un evento: altura y prominencia, ventana del detrend automática (Video_prueba 28 → 29) |
| `propuesta-fase-3-ritmo-cinetica.md` | 2026-10-07 | tren buscado por la frecuencia configurada, instante = inicio, cinética por grupo |
| `propuesta-fase-3-resto.md` | 2026-10-08 | columnas adaptables, rescate con cintura, una sola métrica (la traslación) |
| `propuesta-fase-4.md` | 2026-10-07 | outliers solo como diagnóstico, `motion_check` arreglado, sexto evento de 063 real, ráfaga de 583 = vibración |
