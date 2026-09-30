# Guía de revisión del código

Creada 2026-09-30. Para revisar `gel_contractility` de punta a punta en un
**chat aparte** del proyecto, mientras en otro chat se sigue implementando.

---

## Cómo arrancar el chat de revisión

Pegá esto como primer mensaje:

> Voy a revisar todo el código de `gel_contractility` siguiendo
> `claude/guia-revision-codigo.md`. Leela entera, y también `CLAUDE.md`,
> `claude/protocolo-analisis-videos.md` y
> `claude/referencia-archivos-y-graficos.md`. En este chat **no se modifica
> código**: el objetivo es entenderlo y encontrar problemas. Los hallazgos van
> a `claude/hallazgos-revision-codigo.md` con el formato que indica la guía.
> Empezamos por la preparación (sección 1) y seguimos etapa por etapa (sección
> 2), a mi ritmo: al terminar cada etapa, esperá mi confirmación antes de pasar
> a la siguiente.

## Reglas para no pisarse con el chat de implementación

- **El chat de revisión no edita código ni resultados.** Lee, corre cosas en
  una copia y escribe hallazgos. Si algo hay que arreglar, se anota; lo arregla
  el chat de implementación.
- **Los hallazgos van a un solo archivo**, `claude/hallazgos-revision-codigo.md`
  (y su copia en `docs/`). El chat de implementación lo lee antes de tocar un
  módulo.
- **Todo hallazgo lleva evidencia**: la línea de código, y si es un
  comportamiento, el comando o el fragmento que lo reproduce. "Me parece raro"
  va como pregunta, no como hallazgo.
- **No se tunea nada.** Si un parámetro parece mal elegido, se anota con el
  argumento; no se prueban valores hasta que el número dé lindo.

### Formato de cada hallazgo

    ### H<n>. <título corto>
    - Archivo / función / líneas:
    - Severidad: BUG (da un número equivocado) | RIESGO (puede darlo en un
      video nuevo) | DEUDA (duplicación, nombres, docs) | PREGUNTA
    - Qué pasa:
    - Evidencia (cómo reproducirlo):
    - Qué afecta hoy: ¿cambia algún resultado vigente?
    - Propuesta:
    - Estado: abierto | arreglado en <fecha> | descartado (motivo)

---

## 1. Preparación (30 min)

1. **Congelar el punto de partida.** En la carpeta del repo:
   `git status`, y si hay cambios sin commitear, commitearlos. Anotar el hash
   (`git log -1`): la revisión es sobre ese commit. Los cambios del 29/30 de
   septiembre (cinética y correcciones de documentación) se ven con
   `git diff <commit anterior>`.
2. **Correr las pruebas**, desde la raíz del repo:

       python tests/test_seleccion_k.py     # 16/16
       python tests/test_cinetica.py        # TODO OK

3. **Reproducir los resultados vigentes** (la regresión que exige CLAUDE.md).
   Copiar `data/processed_data/` a una carpeta temporal, correr
   `contraction_report.py` sobre cada `serie_temporal.xlsx` de la copia y
   comparar el `contracciones.xlsx` nuevo contra el vigente, hoja por hoja y
   columna por columna:

   ```python
   import sys, numpy as np, pandas as pd
   A = pd.read_excel(sys.argv[1], sheet_name=None)   # vigente
   B = pd.read_excel(sys.argv[2], sheet_name=None)   # recién corrido
   for s in A:
       for c in A[s].columns:
           x, y = A[s][c], B[s][c]
           try:
               ok = np.allclose(x.astype(float), y.astype(float), equal_nan=True, rtol=0, atol=1e-12)
           except (ValueError, TypeError):
               ok = (x.astype(str).values == y.astype(str).values).all()
           if not ok:
               print("DIFIERE", s, c)
   ```

   Tiene que dar idéntico en los seis. `main.py` (video → serie) no hace falta
   re-correrlo para la revisión: tarda y los `serie_temporal.xlsx` vigentes ya
   registran sus parámetros en la hoja `resumen`.
4. **Tener a mano** el cuaderno `Analisis_Contractilidad_v4.ipynb` corrido sobre
   Video_063 (pocos eventos y débiles: se ve todo) y las figuras de
   `data/processed_data/Video_063_CTRL1_5V/`.

**Ojo:** en `.claude/worktrees/video-processing-pipeline-10178f/` hay una copia
vieja del código, anterior a la v4. No revisar esa.

---

## 2. Orden de lectura

En el orden en que viajan los datos. Para cada módulo, responder por escrito
**tres preguntas: qué entra, qué sale, qué supone**. Después chequear que no
contradiga los cinco hallazgos de `CLAUDE.md`. No todo merece el mismo tiempo:
las etapas marcadas ★ son las delicadas.

Tamaños (líneas): `preprocessing` 622, `rhythm_split` 621, `contraction_report`
751, `event_detection` 431, `pipeline` 333, `cinetica` 254, el resto < 350.
Unas 5 600 en total.

### Etapa 0 — el método, sin código (30 min)
`CLAUDE.md` y `docs/DOCUMENTACION.md` (reescrita el 2026-09-30). Objetivo:
poder explicar en voz alta cada paso antes de leer cómo está programado.

### Etapa 1 — lectura del video y eje temporal
`src/io_utils.py` (`frame_generator`, `read_pts_seconds`,
`compute_max_projection`), la parte de PTS de `src/pipeline.py`
(`process_video`, ~líneas 200–280).
- ¿`read_pts_seconds` lee el timestamp **después** de `read()`? (el docstring
  explica por qué importa).
- ¿Cómo se cuentan los huecos y los fotogramas faltantes? ¿Qué pasa con un
  `dt` que no es múltiplo entero de la mediana?
- Si el archivo no trae timestamps, ¿cae a `frames` y **avisa**? Desde el
  2026-09-30 el default de `main.py` y de `PipelineConfig` es `pts`.
- `compute_max_projection` usa 1 de cada 5 fotogramas: ¿puede perderse un
  movimiento breve del borde y achicar la zona de búsqueda?

### Etapa 2 ★ — la zona útil (ROI)
`src/preprocessing.py`: `_track_gel_band`, `_edge_sharpness`,
`_widest_flat_window`, `auto_detect_roi`. Figura `00_roi_profile_*.png`.
- Seguir la cascada de niveles (`gauge_plana` → … → `gauge_rescate_plana`) y
  confirmar que coincide con la tabla de `DOCUMENTACION.md` §2.2.
- **Buscar parámetros atados al tamaño del sujeto** (la regla de CLAUDE.md):
  `roi_thickness_tolerance` 0.05, `roi_max_slope` 0.02, `roi_min_gradient` 10,
  el tamaño de las ventanas de mediana. ¿Alguno depende de cuán ancho es el
  gel o de cuántos píxeles mide?
- Video_466 es el único que necesita ROI forzada (700–900): el automático
  elige 944–1169, plana pero con 16 % de outliers. ¿Dónde habría que meter
  `outlier_frac` en la decisión?
- ¿Qué pasa si el gel no está horizontal, o si el cuadro corta un anclaje?

### Etapa 3 — el borde subpíxel
`src/edge_detection.py` (`subpixel_edge_parabolic`, `extract_edges_for_frame`)
y `preprocessing.apply_clahe`.
- La parábola sobre 3 puntos: ¿el vértice se acota a ±0.5 px? ¿Qué pasa si el
  máximo del gradiente está en el borde de la ventana?
- `min_gradient` = 5 se compara contra la imagen **ya pasada por CLAHE**: ¿es
  un número que dependa del video?
- `polarity`: ¿cómo sabe cuál borde es oscuro→claro y cuál claro→oscuro?

### Etapa 4 — ajuste robusto
`src/robust_fitting.py` (`fit_edge_ransac`, `_trimmed_polyfit`).
- Umbral = max(3 × MAD de los residuos, 0.4 px). ¿De dónde sale el piso 0.4?
- `random_state=0`: el resultado es reproducible. Confirmarlo.
- ¿Qué se reporta por fotograma: la mediana del modelo evaluado en las
  columnas, o el modelo en el centro? (afecta a `thickness_px`).

### Etapa 5 — el orquestador
`src/pipeline.py` (`PipelineConfig`, `process_frame`, `process_video`) y
`main.py`.
- Etiquetas `OK` / `LOW_QUALITY` / `REJECTED`: ¿un `REJECTED` queda en `NaN`?
  (sí; ver el hallazgo conocido H1 abajo, sobre qué hace después el reporte).
- ¿La hoja `resumen` registra **todos** los parámetros que influyen en el
  resultado? Contrastar con los flags de `main.py`.

### Etapa 6 ★ — detección, umbral y adelgazamiento
`scripts/contraction_report.py`: `detrend_median`, `_signo_evento`,
`escaneo_estabilidad`, `elegir_k_meseta`, `promedio_alineado`, `analizar`.
Pruebas: `tests/test_seleccion_k.py`.
- La mediana móvil de 2 s (`--win-s`): si una contracción durara más de ~1 s,
  la mediana se la "comería". ¿Es un parámetro atado a la duración del evento?
  Hoy el evento más largo (583) dura ~0.6 s.
- La grilla de `k` es fija (3…20) y la meseta exige 2 puntos seguidos: ¿el
  resultado depende de esa grilla?
- `_signo_evento` decide por la cola más pesada: ¿qué pasa en un video sin
  eventos o con eventos en los dos sentidos?
- El adelgazamiento robusto usa los 3 fotogramas posteriores al pico: ¿en las
  muestras lentas (pico con meseta) eso cae todavía en la meseta?

### Etapa 7 ★ — estimuladas y espontáneas
`src/rhythm_split.py` (`buscar_grilla`, `_z_periodicidad`, `_z_nulo`,
`_theil_sen`, `separar`, `comparar_con_equipo`) y
`docs/separacion-estimuladas-espontaneas.md`.
- El p-valor por Monte Carlo usa una semilla fija: ¿cuántas simulaciones, y
  cambia la decisión con otra semilla?
- Tolerancia de asignación a una ranura: ¿de dónde sale?
- Límites ya conocidos: un solo tren por video, mínimo 4 estimulados.

### Etapa 8 — cinética (nuevo, 2026-09-29)
`src/cinetica.py`, el bloque final de `analizar()`, `imprimir_cinetica`,
`graficar_cinetica` y `tests/test_cinetica.py`. Documento:
`claude/metricas-cinetica-TTP-RT50.md` (sección "Implementación").
- Decisiones a validar o discutir: nivel del 10 % para el inicio; el 2×ruido
  que define la meseta del pico (`Z_PICO`); el mínimo de 5 fotogramas; que la
  amplitud relativa divida por el grosor en reposo.
- **Intentar romperlo** en vez de solo leerlo: correr con
  `--min-frames-cinetica 3` y ver qué cambia; en el test, subir el ruido o
  acortar el evento lento; mirar las seis `11_cinetica_*.png`.
- ¿El intervalo [min, max] contiene siempre el valor puntual?

### Etapa 9 — el segundo detector y el cuaderno
`src/event_detection.py`, `scripts/analyze_contractions.py` (marcado obsoleto
el 2026-09-30) y las secciones 7–12 del cuaderno.
- El cuaderno detecta en la sección 9 con `event_detection` (percentil 90
  móvil + agudeza), **no** con el detector de `contraction_report`. Ver H2.
- Decidir cuál es el detector canónico y si el otro se elimina.

### Etapa 10 — diagnósticos y figuras (por encima)
`scripts/motion_check.py`, `scripts/signal_check.py`,
`scripts/inspect_frame.py`, `src/qc_visualization.py`, `src/plotting.py`.
- Hay funciones repetidas entre scripts: ver H4.

---

## 3. Hallazgos ya conocidos (confirmar, no redescubrir)

Encontrados al preparar esta guía. Pasarlos a `hallazgos-revision-codigo.md`
con su estado.

**H1. BUG — un solo fotograma `REJECTED` anula el reporte en silencio.**
`contraction_report.mad()` usa `np.median`, que devuelve `NaN` si hay un solo
`NaN`. Reproducido sobre Video_063: con un `NaN` en el fotograma 500, el
ruido da `NaN`, 0 eventos y el motivo dice "no hay meseta", como si el video
no tuviera contracciones. **Hoy no afecta a ningún resultado** (ninguno de los
seis tiene fotogramas `REJECTED`), pero es probable en los videos de
`RARITOS`. Arreglarlo toca el algoritmo validado: hace falta la regresión
completa, y respetar la regla de no inventar datos faltantes.

**H2. RIESGO — dos detectores de eventos que no coinciden.**
`contraction_report` (mediana móvil + `find_peaks` + meseta) y
`event_detection.detect_contractions` (percentil 90 + agudeza), que usa el
cuaderno en las secciones 8–12. En Video_prueba dan 28 y 29 eventos. Los
números que valen son los del reporte (`contracciones.xlsx`); la sección 11c
del cuaderno ya usa ese detector.

**H3. DEUDA — el cuaderno arma las ventanas con el fps declarado.**
En las secciones 7, 10 y 11, `cr.detrend_median(..., fps, ...)` y
`cr.promedio_alineado` reciben el `fps` del metadato (p. ej. 29.73), mientras
que el reporte lo calcula de los timestamps (30.000). La ventana de la mediana
pasa de 61 a 59 fotogramas: los números del cuaderno pueden diferir un poco de
los del reporte.

**H4. DEUDA — funciones repetidas.** El MAD está en
`contraction_report.mad`, `event_detection.robust_mad` y
`robust_fitting._robust_mad`; la mediana móvil sin deriva en
`contraction_report.detrend_median`, `motion_check._detrended` y
`signal_check._detrend_median`. Si divergen, el mismo "ruido" significa cosas
distintas en cada script.

**H5. DEUDA — default de separación inconsistente.**
`escaneo_estabilidad(..., sep_s=2.0)` tiene default 2.0 s, pero el script
siempre lo llama con `--sep-s` (default 0.3 s). Quien la llame directamente
(desde un cuaderno) obtiene otro escaneo. CLAUDE.md advierte que una
separación grande borra eventos de un tren rápido.

**H6. DEUDA — `event_detection.detect_contractions` tiene
`raw_col="thickness_px"` por defecto**, lo contrario del hallazgo 1.

**H7. Resuelto el 2026-09-30 (verificar):**
- `main.py` tenía `--base-tiempo frames` como default. Ahora `pts`.
- `ordenar_carpeta.py`, corrido otra vez, habría archivado los resultados
  vigentes. Ahora se niega si no hay carpetas `_v6`.
- `test_seleccion_k.py` solo tenía los escaneos anteriores a PTS (Video_prueba
  con 29 eventos; el vigente da 28). Se agregaron los seis vigentes.
- La documentación decía que los vigentes estaban en `<video>_v6/`: están sin
  sufijo.

---

## 4. Al terminar

- [ ] Las diez etapas tienen sus tres respuestas escritas (qué entra, qué
      sale, qué supone).
- [ ] Cada hallazgo tiene evidencia y severidad.
- [ ] H1–H6 confirmados o descartados.
- [ ] Una lista corta, ordenada, de qué arreglar primero, al final de
      `hallazgos-revision-codigo.md`, para el chat de implementación.
