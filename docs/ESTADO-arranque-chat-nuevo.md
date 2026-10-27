# Estado y arranque de un chat nuevo

Actualizado 2026-10-26. Corto a propósito: lo que falta está en `docs/pendientes.md`; la versión larga
anterior, en `docs/historia/estado-hasta-2026-10-26.md`.

## Prompt para pegar en el chat nuevo

```
Continuamos gel_contractility (Tecnun). Leé CLAUDE.md, docs/ESTADO-arranque-chat-nuevo.md y
docs/pendientes.md (son cortos; lo demás, solo si la tarea lo pide). Repo:
C:\Users\Franco Rita\Facultad\Espana\Análisis_de_Datos\gel_contractility_git\Gel_Contractility
Videos: solo si la tarea los pide, nunca los originales de Andrés (520 MB, 4K): copias de
scripts/achicar_video.py.

Reglas: medir y proponer primero, explicarme en simple, respuestas cortas, comandos de git juntos al final.
- No cambia ningún número: hacelo, corré verificar.bat, commit sin push y contame al final.
- Cambia un número informado: medilo, dejame la tabla y esperá mi visto bueno.
- Decime siempre si la tarea conviene hacerla en Claude Code o en el chat; si va a Claude Code,
  dame el prompt listo para pegar (formato en CLAUDE.md, "Modo de trabajo").
- Mediciones: data/_mediciones_fases/<tema>/ con LEEME.md y una línea en data/_mediciones_fases/LEEME.md.
- Al terminar algo: sacarlo de pendientes.md y anotar una línea en la historia de este archivo.
Objetivo de este chat: <completar>
```

## Cómo trabajamos

- **Regla y dónde va cada tarea (Claude Code o chat):** `CLAUDE.md`, sección "Modo de trabajo".

- **Los documentos viven solo en `docs/`** (git). El proyecto de Claude tiene un solo archivo con este
  prompt; no hay copias que sincronizar.
- **Verificar un cambio:** doble clic en `verificar.bat` (todos los tests y la regresión rápida, con los
  tiempos y OK/FALLA al final). `verificar.bat completo` agrega `--completo` (si se tocó ROI, bordes,
  RANSAC o la lectura del video). Cambio intencional y aprobado:
  `python tests/generar_referencia.py --aprobar "motivo"`.
- **Recomendado:** Claude Code abierto en la carpeta del repo (lee, corre tests y commitea en la notebook,
  sin copiar archivos a la nube).

## Cómo se usa el programa

Doble clic en `Analizar.bat` (pestañas Analizar, Resultados y Comparar). Por consola: `main.py` y
`scripts/contraction_report.py`; una carpeta: `scripts/procesar_carpeta.py`. Todo lo que se imprime:
`docs/guia-salida-consola.md`.

## Resultados de referencia (vigentes; TTP/RT50 con el pico de B6, 2026-10-15)

| video | eventos | amplitud (estimulados) | TTP | RT50 |
|---|---|---|---|---|
| Video_prueba | 29 (6 estimulados) | 2.31 % = 6.81 px | < ~100 ms | < ~100 ms |
| Video_063 | 6 (5 estimulados) | 0.56 % = 1.59 px | < ~100 ms | < ~100 ms |
| Video_268 | 6 | 0.57 % = 1.55 px | < ~100 ms | < ~100 ms |
| Video_466 | 5 | 2.16 % = 4.36 px | 183 ms | 226 ms |
| Video_583 | 6 | 1.31 % = 3.10 px | 189 ms | 252 ms |
| Video_491 | 2 (sin tren) | 0.40 % = 1.02 px (todos) | 557 ms | 480 ms |

Regresión: los 11 videos de `tests/referencia.py` contra `tests/referencia_regresion.json` (Video_prueba 29 y
063 con 6 son los de siempre). Los cinco con tren dan 0.1 Hz (confirmado por el equipo), captura 100 %, p = 0.001.
491 (36 Hz): dos contracciones de ~1 s en sentido contrario, compatible con un tétanos fusionado; no citar
sin el equipo.

RARITOS (`docs/raritos.md`): 476 normal (6 estimuladas, 0.64 %); 613 NO REPORTABLE (vibración);
068 y 304 actividad continua (el conteo no aplica); 341 NO REPORTABLE (mezcla).

Videos de Andrés (textura, `data/_mediciones_fases/textura/LEEME.md`): 4 de 9 reportables (10V_1, 20V_3,
40V_1, 40V_3); los otros 5 responden por respuesta forzada (`respuesta_forzada/LEEME.md`).

## Historia (una línea por paso; detalle en `docs/historia/` y en los LEEME de mediciones)

- **2026-10-26:** tres mediciones: cinética desde la respuesta forzada (sirve pulso a pulso), textura en
  583/466/063/268 (solo 466 falla, por la correlación) y H13 (el control solo se equivoca grave con ruido
  asimétrico a favor).
- **2026-10-26:** marcas dudosas y selección de pulsos guardadas por instante.
- **2026-10-26:** tabla de carpeta sin amplitud en conteos NO REPORTABLES; RARITOS docx/pdf a `docs/historia`.
- **2026-10-26:** revisión de la forma de trabajar: documentos solo en `docs/`, pendientes y ESTADO cortos,
  `verificar.bat`, índice de mediciones.
- **2026-10-19:** control 4K completo contra achicado; aviso de respuesta chica con textura; respuesta forzada
  (consola, Excel, informe, ventana, tabla de carpeta).
- **2026-10-16/17:** medición por textura como opción (`--metodo textura`); carpeta de Andrés.
- **2026-10-15:** B6 (pico = primer fotograma ≥ 95 % del máximo); basal (C8); rotación para gel vertical;
  ventana: pulsos, selección y Comparar; textos "mediana"/"media".
- **2026-10-11:** pestaña Comparar, detalles de la ventana; tiempos de `main.py` en la notebook (~50 s).
- **2026-10-10:** ventana de búsqueda automática (±15/±30); carpeta entera; informe HTML; IC 95 %; avisos;
  versiones fijas; mediciones D1–D7, H16, H23, H28–H30.
- **2026-10-08:** nombres de Excel con el video; código más rápido (RANSAC propio, paralelo); regresión automática.
- **2026-10-07:** RARITOS procesados; consola clara; ventana (`interfaz.py`).
- **Fases 2.2–4 y v4 (septiembre–octubre):** ver `docs/historia/`.
