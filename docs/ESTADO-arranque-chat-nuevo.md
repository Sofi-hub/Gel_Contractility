# Estado del proyecto y arranque de un chat nuevo

Actualizado 2026-10-08 (tarde). Sirve para dos cosas: es el resumen del estado actual, y su primera sección se puede pegar tal cual al abrir un chat nuevo. **Lo que falta hacer está en `docs/pendientes.md`**, no acá.

---

## Prompt para pegar en el chat nuevo

> Trabajo en `gel_contractility`, un pipeline en Python que mide la contractilidad de geles 3D a partir de video de microscopía, para el equipo de Tecnun. Funciona: está validado sobre seis videos y se aplicó a cinco videos "raros" (`RARITOS`). El código está en mi carpeta (repo git) y los documentos en `docs/`, con copia en este proyecto.
>
> **Cómo funciona, una línea por etapa:**
> 1. El video se convierte en un mapa de máxima intensidad.
> 2. Se detecta automáticamente la zona plana del gel, lejos de los anclajes.
> 3. En cada fotograma se localizan los dos bordes con precisión subpíxel en 40–60 columnas.
> 4. Un polinomio de grado 2 ajustado con RANSAC descarta las columnas arruinadas por burbujas.
> 5. Salen cuatro series: `y_top_px`, `y_bottom_px`, `thickness_px` y `center_px`.
> 6. Se detectan las contracciones sobre `center_px`, con un control de falsos positivos sobre la señal invertida.
> 7. Se separan estimuladas y espontáneas por enganche de fase con el estimulador.
>
> **Los cinco hallazgos que definen el método, y que no hay que perder:**
> 1. **La contracción se detecta sobre `center_px`, no sobre el grosor.** En este montaje es sobre todo un desplazamiento de toda la franja, y el grosor es ciego a eso. La métrica que se informa es la amplitud de ese desplazamiento en % del grosor en reposo.
> 2. **Estimuladas y espontáneas se separan por enganche de fase**, no por amplitud.
> 3. **El eje temporal sale de los timestamps del video** (`--base-tiempo pts`), no de `fotograma / fps`.
> 4. **El umbral `k` se elige solo, dentro de la meseta del escaneo** con 0 falsos de control. Sin meseta, el conteo no se informa (NO REPORTABLE).
> 5. **A 30 fps, TTP y RT50 no son medibles en las muestras rápidas:** se da una cota ("menos de X ms"), no un valor.
>
> **Fuera de alcance:** no se calibra a milímetros; todo en píxeles y comparaciones relativas.
>
> **Principio de trabajo:** medir y proponer antes de cambiar. Ningún cambio de algoritmo sin regresión sobre Video_prueba y Video_063. Nunca ajustar un parámetro hasta que el número dé lindo.
>
> Antes de empezar leé `CLAUDE.md`, este documento y `docs/pendientes.md`.

---

## Cómo se usa hoy

- **La forma fácil:** doble clic en `Analizar.bat`, que abre la ventana de `interfaz.py`. Ahí se elige el video y la carpeta, se marcan los pasos que se quieren correr y se ve la salida en vivo.
- **Por consola:**
  - `main.py` → `scripts/contraction_report.py`, con `scripts/motion_check.py` como paso opcional.
  - Comandos y explicación de todo lo que se imprime en `docs/guia-salida-consola.md`.
  - `--verbose` muestra el detalle técnico. Todo queda igual guardado en los Excel.

## Dónde está todo

**Resultados vigentes:** `data/processed_data/<video>/`, sin sufijo. Las corridas anteriores están solo en el historial de git. Mediciones de las fases: `data/_mediciones_fases/`. Los videos crudos (`data/raw_videos/`) no están en git. `Video_068_hw30` es 068 corrido con `--half-window 30`; esa es la medición buena.

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
| `historia/` | cómo se llegó a cada decisión: propuestas de cada fase, diagnósticos viejos y la revisión de código (hallazgos H1–H55) |

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
| Video_prueba | < ~100 ms (no medible) | < ~100 ms | 2.31 % | 2.09 |
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
| 068 | NO REPORTABLE (con `--half-window 30`) | actividad continua del tejido, sin pausas: el método de eventos no aplica |
| 304 | 0 eventos | oscilación continua a ~3.5–4.3 Hz: mismo caso que 068 |
| 341 | NO REPORTABLE | mezcla: ráfagas del tejido hacia los dos lados y un tren limpio a ~3.2 Hz |

## Historia en una línea por fase

- **v4 (septiembre):** detección sobre `center_px`, ROI automática, eje por timestamps.
- **Revisión de código** (H1–H55, `historia/hallazgos-revision-codigo.md`).
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
- **2026-10-07:** se procesaron los RARITOS. Después: consola clara, `--verbose`, sentido de los eventos corregido, figuras NO REPORTABLE, la ventana (`interfaz.py`) y la documentación ordenada.

## Límites conocidos del método

- Una serie espontánea **muy** regular es indistinguible de una estimulada por los tiempos solos.
- `rhythm_split` necesita al menos 4 latidos estimulados y el 75 % de los pulsos ocupados.
- **Una vibración del montaje entra en `center_px` igual que una contracción.** El control con la señal invertida la delata cuando va hacia los dos lados (613), pero no siempre: la ráfaga final de 583 casi cuenta como evento.
- **El método cuenta contracciones separadas por reposo.** Si el tejido no se queda quieto nunca (068, 304), el conteo no aplica; falta una medida de actividad (`pendientes.md`).
- **Si el gel se mueve más de ±15 px**, el borde se sale de la ventana de búsqueda: usar `--half-window 30` (068).
- A 30 fps, TTP y RT50 no son medibles cuando la subida dura menos de 5 fotogramas.
- En las muestras lentas (466, 583) el pico es una meseta de 4–5 fotogramas: el instante del pico es ambiguo, el del inicio no.
- El grosor da un salto positivo en el fotograma de máxima velocidad: es motion blur, no engrosamiento.
