# Estado del proyecto y arranque de un chat nuevo

Actualizado 2026-10-11. Sirve para dos cosas: es el resumen del estado actual, y su primera sección se puede pegar tal cual al abrir un chat nuevo. **Lo que falta hacer está en `docs/pendientes.md`**, no acá.

---

## Prompt para pegar en el chat nuevo

```
Continuamos gel_contractility (Tecnun), con el código.
ANTES DE EMPEZAR leé del proyecto CLAUDE.md, claude/ESTADO-arranque-chat-nuevo.md y claude/pendientes.md. Leé el código desde mi carpeta (repo git): C:\Users\Franco Rita\Facultad\Espana\Análisis_de_Datos\gel_contractility_git\Gel_Contractility. Traé los videos solo si una tarea lo pide.

Reglas de siempre: medir y proponer primero, explicarme en simple, respuestas cortas, comandos de git juntos al final. Los documentos viven en docs/ del repo, con copia de los vigentes en el proyecto: si cambiás uno, actualizá los dos y verificá que lo que copiás a mi carpeta llegó bien (re-traerlo y comparar; una vez la copia quedó vieja aunque la herramienta dijo que había escrito). Verificación de cada cambio: tests (incluidos test_lote y test_visor), `python tests/test_regresion.py` y, si se toca ROI, bordes o RANSAC, `--completo`. Las versiones fijas están en requirements.txt.

Modo de trabajo: resolver lo que MENOS atención mía requiera.
* Si un cambio NO cambia ningún número (o solo agrega diagnósticos o mejora la ventana), hacelo directo, verificalo y copialo; contame al final.
* Si cambia un número informado, medilo y dejame la propuesta con la tabla; no lo implementes sin mi visto bueno.
* Mediciones largas: de fondo, revisarlas cada ~10 min; scripts y tablas en data/_mediciones_fases/<tema>/ con un LEEME.md.
* Al final, un resumen corto: qué se hizo, qué quedó esperando mi decisión, y los comandos de git.

Dónde quedamos (2026-10-15): la ventana (Analizar / Resultados / Comparar) está probada en Windows y al equipo le gustó. main.py bajó de ~90 a ~50 s sin cambiar números. Hubo reunión con el equipo de Tecnun: respuestas en docs/preguntas-reunion-equipo.md (todos los videos con voltaje en el nombre son a 0.1 Hz; permiso para pasar la frecuencia conocida; el pico es el PRIMER instante en que se llega al máximo; la basal 0–10 s sirve para caracterizar espontáneas; quieren ver cada pulso y elegir cuáles promediar). Regla de nombres: "promedio" = media; donde es mediana, decir "mediana".

Objetivo de este chat: la sección 0 de docs/pendientes.md, en este orden:
A. Ventana (sin cambiar números, hacer directo): 1) textos promedio/mediana; 2) tabla de pulsos individuales visible; 3) elegir pulsos (p. ej. los 3 primeros estimulados) y ver su media; 4) comparar selecciones entre videos; 5) tests.
B. Cambian números (medir y traerme la tabla, no implementar sin mi visto bueno): 6) pico = primer instante en que se llega al máximo (proponer cómo definirlo con ruido); 7) búsqueda dirigida a 0.1 Hz en 613 y 068.
C. Nuevo: 8) resumen de la basal (medir en los 11 y mostrar la tabla primero). Después: videos de frecuencia y los videos nuevos de otra estudiante.
```

---

## Cómo se usa hoy

- **La forma fácil:** doble clic en `Analizar.bat`, que abre la ventana de `interfaz.py`. Pestaña Analizar: video o carpeta entera, pasos (1 medir, 2 contracciones, 3 confirmar, 4 informe HTML) y salida en vivo. Pestaña Resultados (`visor.py`): todo `processed_data`, números, avisos y gráfico interactivo (clic en una contracción = su ficha; marcar dudosa, fotograma, exportar). Pestaña Comparar (`comparar.py`): 2 o más resultados lado a lado.
- **Por consola:**
  - `main.py` → `scripts/contraction_report.py`, con `scripts/motion_check.py` como paso opcional.
  - Comandos y explicación de todo lo que se imprime en `docs/guia-salida-consola.md`.
  - `--verbose` muestra el detalle técnico. Todo queda igual guardado en los Excel.

## Dónde está todo

**Resultados vigentes:** `data/processed_data/<video>/`, sin sufijo. Las corridas anteriores están solo en el historial de git. Mediciones de las fases: `data/_mediciones_fases/`. Los videos crudos (`data/raw_videos/`) no están en git. `Video_068_hw30` es 068 (corre con ±30, ahora automático; la carpeta conserva el sufijo).py`. **Regresión con un comando:** `python tests/test_regresion.py` (agregar `--completo` si se tocó ROI, bordes o RANSAC).

| documento (`docs/`) | para qué |
|---|---|
| `guia-salida-consola.md` | comandos, la ventana y qué significa cada línea que se imprime. Para usar el programa y explicarlo |
| `pendientes.md` | **la lista única de lo que falta** |
| `protocolo-analisis-videos.md` | reglas del método y chequeos de aceptación antes de informar un número |
| `referencia-archivos-y-graficos.md` | qué contiene cada archivo, cada columna y cada eje |
| `DOCUMENTACION.md` | el método explicado sin código, para quien diseña el experimento |
| `raritos.md` | resultados y diagnóstico de los cinco videos `RARITOS` |
| `preguntas-reunion-equipo.md` | preguntas para el equipo de Tecnun (anotar ahí las respuestas) |
| `base-de-tiempo-y-frames-perdidos.md` | el eje temporal, en detalle |
| `separacion-estimuladas-espontaneas.md` | enganche de fase y sus límites |
| `metricas-cinetica-TTP-RT50.md` | cinética: viabilidad, implementación y resultados |
| `comparacion-musclemotion.md` | nuestros números contra MuscleMotion |
| `contexto-tecnun-y-musclemotion.md` | para quién es el trabajo y qué es la carpeta `OK` |
| `revision-script-matlab.md` | los errores del script del equipo, para conversarlo con ellos |
| `historia/` | cómo se llegó a cada decisión: propuestas de cada fase, diagnósticos viejos (la revisión de código H1–H55 se borró el 2026-10-10: lo abierto está en `pendientes.md`, sección F; el detalle, en el historial de git) |

## Resultados de referencia (los seis validados)

| video | ROI (método, columnas) | var | k (meseta) | eventos | período del tren |
|---|---|---|---|---|---|
| Video_prueba | 454–1516 (`gauge_cintura`, 60) | 5.32 % | 9.4 (5.3–15.2) | 29 (6 estimulados) | 10.00043 ± 0.00230 s |
| Video_063 | 875–1039 (`gauge_plana`, 54) | 0.35 % | 11.4 (9.4–13.8) | 6 (5 estimulados) | 9.99812 ± 0.00304 s |
| Video_268 | 918–1328 (`gauge_cintura`, 60) | 5.24 % | 12.5 (5.8–24.4) | 6 | 10.00132 ± 0.00230 s |
| Video_466 | 696–846 (`gauge_cintura`, 50) | 4.85 % | 11.4 (6.4–20.2) | 5 | 10.00184 ± 0.00542 s |
| Video_583 | 718–1187 (`gauge_cintura`, 60) | 5.83 % | 16.7 (12.5–24.4) | 6 | 10.00024 ± 0.00230 s |
| Video_491 | 459–1206 (`gauge_cintura`, 60) | 5.08 % | 10.4 (7.8–13.8) | 2 | sin tren |

**Video_prueba (29) y Video_063 (6) son la regresión:** cualquier cambio de algoritmo tiene que darlos iguales. Los cinco videos con tren dan 0.1 Hz dentro del error, con captura del 100 % y p = 0.001. Ninguno usa zona (ROI) manual.

| video | TTP | RT50 | amplitud relativa (estimulados) | amplitud (px) |
|---|---|---|---|---|
| Video_prueba | < ~100 ms (no medible) | < ~100 ms | 2.31 % | 6.81 |
| Video_063 | < ~100 ms | < ~100 ms | 0.56 % | 1.59 |
| Video_268 | < ~100 ms | < ~100 ms | 0.57 % | 1.55 |
| Video_466 | 255 ms [137, 365] | 192 ms [33, 260] | 2.16 % | 4.36 |
| Video_583 | 258 ms [129, 335] | 181 ms [99, 301] | 1.31 % | 3.10 |
| Video_491 | 570 ms | 467 ms | 0.40 % (todos; sin tren) | 1.02 |

**Video_491 (36 Hz)** es distinto: dos contracciones de ~1 s, en sentido contrario (la franja sube). Es compatible con un tétanos fusionado, pero no está confirmado. Consultar con el equipo antes de citarlo.

## RARITOS (procesados 2026-10-07; detalle en `docs/raritos.md`)

| video | resultado | lectura |
|---|---|---|
| 476 | 6 estimuladas a 0.1 Hz, 0.64 % | normal; MuscleMotion falla por la compresión del video |
| 613 | NO REPORTABLE | vibración al inicio y al final; sin contracciones detectables |
| 068 | NO REPORTABLE (con ventana ±30, automática) | actividad continua del tejido, sin pausas: el método de eventos no aplica |
| 304 | 0 eventos | oscilación continua a ~3.5–4.3 Hz: mismo caso que 068 |
| 341 | NO REPORTABLE | mezcla: ráfagas del tejido hacia los dos lados y un tren limpio a ~3.2 Hz |

## Historia en una línea por fase

- **v4 (septiembre):** detección sobre `center_px`, ROI automática, eje por timestamps.
- **Revisión de código** (H1–H55; lo que sigue abierto, en `pendientes.md` F).
- **Fase 2.2:** qué es un evento (altura y prominencia, ventana automática).
- **Fase 3:**
  - ritmo y cinética: tren dirigido e instante = inicio;
  - borde y ajuste: columnas adaptables, rescate con cintura;
  - una sola métrica: la traslación.
- **Fase 4:**
  - el chequeo de outliers pasa a ser solo diagnóstico;
  - `motion_check` arreglado;
  - el sexto evento de 063 es real;
  - la ráfaga final de 583 es vibración.
- **2026-10-08 (código, sin cambiar números):** Excel con el nombre del video (se aceptan los nombres viejos); video leído una vez menos, fotogramas en paralelo (`--procesos`) y RANSAC propio (igual al de sklearn): de 5–6 min a ~70 s por video; borradas opciones y scripts sin uso. CLAHE sobre la franja: medido y descartado. Mail a Cami con los RARITOS y preguntas (`docs/RARITOS_resultados_y_preguntas.pdf`).
- **2026-10-10:** ventana de búsqueda automática (B1, opción a'): ±15 y, si el borde se sale, ±30. Solo cambia 304 (sin cambiar números informados).
- **2026-10-10 (tarde, sin cambiar números):** versiones fijas en `requirements.txt`; procesar una **carpeta entera** con tabla resumen (ventana y `scripts/procesar_carpeta.py`). Medidas y cerradas: D2/H52 (el peine de compresión está en los 11 videos, no pasa a los bordes), D3 (la espontánea de 0.31 s de 063 es local), D7 (la oscilación post-evento es solo de 476), B1 (en 466 el borde superior tiene un segundo escalón a ~15 px). D1: por contracción 476 da 0.99 y 268, 466 y 491 dan 0.86–0.88; `motion_check` ahora juzga el tamaño contracción por contracción. H23: escalar la ventana de la ROI con el gel no cambia ningún número informado; se deja como está.
- **2026-10-10 (noche, sin cambiar números):** informe HTML de una página por video (paso 4, `scripts/informe.py`); `configuracion.ini`; IC 95 % por bootstrap de la amplitud (y TTP/RT50); avisos de timestamps inventados, cintura corta y poco contraste (D6).
- **2026-10-15 (noche):** B6 aprobado e implementado (pico = primer fotograma ≥ 95 % del máximo; cambian TTP/RT50 de 466, 583 y 491; referencia regenerada y `processed_data` rehecho). Rotación automática para gel vertical (videos de Andrés); el borde de esos videos es una rampa granulada y queda por probar con un video real.
- **2026-10-15 (tarde, sin cambiar números):** resumen de la **basal** (C8: consola, hoja `basal_*`, informe, ventana); Comparar con selector de pulsos arriba, tabla de pulsos elegidos y vistas de forma normalizada, TTP/RT50 por pulso y amplitud pulso a pulso.
- **2026-10-15 (sin cambiar números):** textos "mediana"/"promedio (media)" en consola, informe, ventana y figuras; sub-pestaña Pulsos (tabla por pulso, elegir pulsos y su media) y Comparar con los N primeros estimulados o la selección guardada. Medidos y esperando decisión: B6 (pico = primer fotograma ≥ 95 % del máximo), B7 (613 y 068 sin respuesta a 0.1 Hz, ni plegando la señal) y C8 (resumen de la basal). Ver `pendientes.md` sección 0.
- **2026-10-11 (sin cambiar números):** pestaña Comparar; en Resultados, números en varias líneas, atajos, exportar la ficha, marcar dudosa (aparte), fotograma del pico y amplitud contra el tiempo. Script para medir los tiempos de `main.py` en la notebook (`data/_mediciones_fases/tiempos_main/`).
- **2026-10-08 (tarde):** resultados regenerados con nombres nuevos (sin cambiar números); test de regresión automático de los 11 videos; `--procesos` por defecto 2 (medido en la notebook).
- **2026-10-07:** se procesaron los RARITOS. Después: consola clara, `--verbose`, sentido de los eventos corregido, figuras NO REPORTABLE, la ventana (`interfaz.py`) y la documentación ordenada.

## Límites conocidos del método

- Una serie espontánea **muy** regular es indistinguible de una estimulada por los tiempos solos.
- `rhythm_split` necesita al menos 4 latidos estimulados y el 75 % de los pulsos ocupados.
- **Una vibración del montaje entra en `center_px` igual que una contracción.** El control con la señal invertida la delata cuando va hacia los dos lados (613), pero no siempre: la ráfaga final de 583 casi cuenta como evento.
- **El método cuenta contracciones separadas por reposo.** Si el tejido no se queda quieto nunca (068, 304), el conteo no aplica; falta una medida de actividad (`pendientes.md`).
- **Si el gel se mueve más de ±15 px**, el borde se sale de la ventana de búsqueda: desde 2026-10-10 `main.py` lo detecta (bordes pegados al límite) y reprocesa solo con ±30 (068, 341).
- A 30 fps, TTP y RT50 no son medibles cuando la subida dura menos de 5 fotogramas.
- En las muestras lentas (466, 583) el pico es una meseta de 4–5 fotogramas: el instante del pico es ambiguo, el del inicio no.
- El grosor da un salto positivo en el fotograma de máxima velocidad: es motion blur, no engrosamiento.
