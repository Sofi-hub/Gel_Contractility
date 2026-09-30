# Contexto: para quién es esto y qué es la carpeta `OK` de MuscleMotion

Escrito el 2026-09-30, a partir de lo que explicó Franco Rita en el chat de revisión de código.

## Para quién y por qué

El trabajo es para que **la Universidad de Tecnun** pueda medir contracciones en sus células. El equipo de Tecnun viene usando
**MuscleMotion** (un plugin de ImageJ) y a veces tiene errores. Este proyecto busca un método propio, sin software externo, que
sea más robusto y **verificable** (ver `CLAUDE.md`, "Cero dependencia externa").

MuscleMotion, en el uso de Tecnun, entrega: contracción (amplitud), velocidad de contracción y algún archivo más.
El script de MATLAB del equipo (`Contraction_Analysis.mlx`) parte de su salida `contraction.txt` (ver `claude/revision-script-matlab.md`).

## La carpeta `OK`

Ruta en la PC de Franco (Windows):

    C:\Users\Franco Rita\Facultad\Espana\Análisis_de_Datos\gel_contractility_git\Gel_Contractility\data\raw_videos\OK-20260904T142817Z-1-001

Es la **misma carpeta donde están guardados los videos crudos** (`data/raw_videos/`). Dentro de `OK` hay dos partes:

- por un lado, **los videos** (`Video_063_CTRL1_5V.mp4`, `Video_268_EXP3_FAPS2_40V.mp4`, `Video_466_EXP5_FAPS4_40V.mp4`, `Video_491_EXP5_CTRL1_36HZ.mp4`, `Video_583_EXP6_CTRL4_40V.mp4`);
- por otro, **una subcarpeta por video, `<video>_-Contr-Results`, con los resultados de MuscleMotion**. Cada una tiene siete archivos:
  `contraction.txt` (la contracción: tiempo y amplitud), `speed-of-contraction.txt` (velocidad de contracción),
  `Overview-results.txt` (resumen de MuscleMotion), `Log_file.txt` (su registro, con los avisos `lowUp/lowDown false at peak`),
  y tres imágenes: `Contraction.jpg`, `Speed of contraction.jpg` y `Comparison calculated (red) and measured (black) speed.jpg`.

La ruta completa `data/raw_videos/OK-20260904T142817Z-1-001/OK/` está dentro de la carpeta `raw_videos`, junto a `Video_prueba.mp4`
y a `RARITOS-20260904T171415Z-1-001/RARITOS/`, que tiene el mismo formato (videos + `_-Contr-Results`) para los videos que MuscleMotion maneja mal:
Video_068, Video_304, Video_341 (sin carpeta de resultados), Video_476 y Video_613. Todavía no se procesaron.

**Qué significa "OK".** No es un criterio estadístico ni técnico escrito en ningún lado. Son los videos que **cumplen los
requerimientos de Tecnun** (los que sean: Franco no los conoce en detalle) y en los que, según el equipo, MuscleMotion
funciona. Por eso sirven como banco de comparación, pero **"OK" no garantiza que MuscleMotion haya medido bien**: en
`claude/comparacion-musclemotion.md` se midió que en Video_063 y Video_491 más de la mitad de los picos de MuscleMotion
llevan avisos de sus propios chequeos, y Video_491 está en `OK` aunque ninguno de los dos métodos pudo certificar eventos ahí.

Los cinco videos de `OK` que se compararon: Video_063, Video_268, Video_466, Video_491, Video_583.

## Cómo usar esto

- Si hace falta una salida de MuscleMotion para comparar, buscarla en la subcarpeta de resultados de `OK`; nunca sugerir
  MuscleMotion como parte del flujo (regla de `CLAUDE.md`).
- No asumir que "OK" = "correcto". Es "cumple los requerimientos de Tecnun".
- La ruta es de la PC del usuario, no del entorno de sesión: hay que pedir la carpeta o leerla por el puente al equipo.
