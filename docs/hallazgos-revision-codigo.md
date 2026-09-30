# Hallazgos de la revisión de código

Lo escribe el chat de **revisión** (ver `claude/guia-revision-codigo.md`); lo
lee el chat de **implementación** antes de tocar un módulo. Formato de cada
entrada: el de la guía, sección "Formato de cada hallazgo".

Revisión sobre el commit: `<completar con git log -1>`

---

## Conocidos antes de empezar (a confirmar)

Detalle y evidencia en la sección 3 de la guía.

| id | severidad | resumen | estado |
|---|---|---|---|
| H1 | BUG | un solo fotograma `REJECTED` (NaN) anula el reporte en silencio | abierto |
| H2 | RIESGO | dos detectores de eventos (reporte vs `event_detection`/cuaderno): 28 vs 29 en Video_prueba | abierto |
| H3 | DEUDA | el cuaderno arma ventanas con el fps declarado, el reporte con el de los PTS | abierto |
| H4 | DEUDA | MAD y mediana móvil repetidos en varios módulos | abierto |
| H5 | DEUDA | `escaneo_estabilidad` tiene `sep_s=2.0` por defecto; el script usa 0.3 | abierto |
| H6 | DEUDA | `detect_contractions` tiene `raw_col="thickness_px"` por defecto | abierto |
| H7 | — | default `pts`, `ordenar_carpeta.py`, escaneos vigentes en el test, `_v6` en docs | arreglado 2026-09-30, verificar |

---

## Nuevos

(el chat de revisión agrega acá H8, H9, …)

---

## Qué arreglar primero

(al terminar la revisión)
