# La base de tiempo: fotogramas perdidos y timestamps del contenedor

Fecha 2026-09-29. **Este documento reemplaza al hallazgo #3** ("el fps
declarado está mal, el real es 30.000"). Ese hallazgo era correcto pero
incompleto, y la versión completa explica además el caso de Video_466, que
quedaba como anomalía.

## El resultado

Los cinco videos estimulados, medidos con la base de tiempo corregida:

| video | frecuencia medida | diferencia vs 0.1 Hz | jitter | captura |
|---|---|---|---|---|
| Video_prueba | 0.09993 ± 0.000041 Hz | −0.07 % | 20.9 ms | 7/7 |
| Video_063 | 0.10001 ± 0.000030 Hz | +0.01 % | 9.6 ms | 5/5 |
| Video_268 | 0.10000 ± 0.000023 Hz | 0.00 % | 9.6 ms | 6/6 |
| Video_466 | 0.10006 ± 0.000120 Hz | +0.06 % | 35.1 ms | 5/5 |
| Video_583 | 0.09999 ± 0.000067 Hz | −0.01 % | 25.4 ms | 6/6 |

**Cinco de cinco indistinguibles de lo configurado.** Antes, con el fps
declarado, Video_prueba daba −0.9 %, Video_063 −0.43 % y Video_466 +5.15 %.

## Por qué el fps declarado está mal

El `fps` que declara un mp4 es el **promedio**: `(n_frames − 1) / duración`.
Si la grabación perdió fotogramas, ese promedio baja, y el eje
`tiempo = fotograma / fps` se come los huecos: los eventos aparecen más
juntos de lo que ocurrieron.

Por eso el fps declarado varía de 28.97 a 29.87 entre videos que salieron de
la misma cámara.

## La medida correcta del fps: el espaciado de los timestamps

El contenedor trae un timestamp por fotograma. El espaciado **típico** entre
fotogramas consecutivos es el período real de captura — a diferencia del
promedio, no lo contamina un hueco. En los cinco videos:

    dt mediano = 33.333 ms   ->   fps = 30.0003

Idéntico en los cinco, con fps declarados que van de 28.97 a 29.87. **Es una
confirmación del fps = 30 completamente independiente del estimulador.**

Dos advertencias prácticas sobre los timestamps:

1. `ffprobe -show_entries packet=pts_time` los devuelve en **orden de
   decodificación**. Con B-frames no son monótonos: la mitad de los deltas
   salen negativos. Hay que ordenarlos.
2. `cv2.CAP_PROP_POS_MSEC` leído **antes** de `read()` devuelve el timestamp
   del fotograma *anterior*. Hay que leerlo después. Verificado contra
   ffprobe: con ese corrimiento coinciden exacto, 0.000 ms de diferencia.

## Fotogramas perdidos por video

> **Valores vigentes (2026-10-08, hoja `resumen` de cada `serie_temporal_<video>.xlsx`).** La tabla de abajo es
> de la primera medición; los conteos vigentes difieren levemente (no quedó anotado por qué). Hoy:
> Video_prueba 7 huecos / 27 fotogramas (1.33 %), 063 22 / 23 (1.23 %), 268 17 / 41 (1.76 %),
> **466 24 / 102 (4.68 %)**, 491 6 / 28 (1.49 %), 583 4 / 33 (1.45 %); RARITOS: 476 1.9 %, 613 2.3 %,
> 068 2.3 %, 304 2.1 %, 341 1.7 %. La conclusión no cambia: con `--base-tiempo pts` no afectan.
> El período de cada tren, vigente, está en `separacion-estimuladas-espontaneas.md`.

Un hueco es un `dt` que vale un múltiplo entero del `dt` mediano:

| video | huecos | fotogramas perdidos | % |
|---|---|---|---|
| Video_063 | 28 | 26 | 1.39 % |
| Video_268 | 21 | 43 | 1.85 % |
| **Video_466** | **25** | **103** | **4.73 %** |
| Video_491 | 6 | 28 | 1.49 % |
| Video_583 | 4 | 33 | 1.45 % |

## Video_466 no era una anomalía

Era el caso raro: 285.5 fotogramas por período contra 300.0 exactos de los
otros cuatro, y un +5.15 % de error contra los 0.1 Hz configurados, que el
reporte marcaba como "revisar el equipo o la detección de eventos".

Perdió el 4.73 % de sus fotogramas. El déficit predice el error casi exacto:
285.25 / 300 = 0.9508, o sea 4.92 % corto.

| Video_466 | período medido |
|---|---|
| eje `fotograma / fps` | 9.5083 s (**+5.15 % de error**) |
| eje con timestamps del contenedor | **10.0063 s (+0.06 %)** |

No hay nada que revisar en el equipo. Era el eje temporal.

## Qué cambió en el código

`src/io_utils.py`: función nueva `read_pts_seconds()`.

`src/pipeline.py`: campo `base_tiempo` en `PipelineConfig` (`"frames"` o
`"pts"`). Los timestamps se leen **siempre**, aunque la base sea `frames`,
porque es lo que detecta los fotogramas perdidos.

`main.py`: flag `--base-tiempo {frames,pts}`. La hoja `resumen` ahora
registra `base de tiempo`, `fps segun PTS`, `huecos en PTS`,
`frames faltantes estimados` y `frames faltantes (%)`. Si faltan más del 1 %,
el pipeline avisa y recomienda `--base-tiempo pts`.

**Recomendación: correr siempre con `--base-tiempo pts`.** Es correcto
tanto si faltan fotogramas como si no: en Video_268, que casi no perdió,
`--fps 30` y `--base-tiempo pts` dan el mismo período hasta la cuarta cifra.

## MuscleMotion tiene el mismo problema, peor

Los archivos de MuscleMotion de la carpeta `OK` corrieron con
`recordedFramerate: 30`, así que su base de tiempo nominal es la correcta.
Pero **ImageJ lee menos fotogramas que OpenCV** en los cinco videos:

| video | MuscleMotion | OpenCV / ffprobe | déficit |
|---|---|---|---|
| Video_063 | 1836 | 1848 | 12 (0.65 %) |
| Video_268 | 2250 | 2283 | 33 (1.45 %) |
| **Video_466** | **1992** | **2076** | **84 (4.05 %)** |
| Video_491 | 1822 | 1846 | 24 (1.30 %) |
| Video_583 | 2204 | 2236 | 32 (1.43 %) |

OpenCV coincide exactamente con el conteo de paquetes de ffprobe; ImageJ
descarta fotogramas al importar.

Eso se ve directamente al comparar los tiempos de evento: en Video_466 el
desfase entre nuestros picos y los de MuscleMotion **crece linealmente**
(0.57 s en el primero, 2.20 s en el quinto). El período de MuscleMotion sale
273.0 fotogramas; predicho a partir del nuestro escalado por el déficit,
285.25 × 1992/2076 = 273.7. Coincide.

**Conclusión: la escala temporal de MuscleMotion está comprimida entre 0.65 %
y 4.05 % según el video, y el error depende del archivo.** No es un
argumento retórico, es un número reproducible.
