# D3: ¿el evento de 0.31 s de 063 es local? (2026-10-10)

**Cómo:** `medir_d3.py`. Mismo método del pipeline (`process_frame`: CLAHE, borde subpíxel, RANSAC grado 2), pero en tramos de 120 px con 40 columnas cada uno, a lo largo de todo el gel (donde los dos bordes son nítidos). Amplitud de cada uno de los 6 eventos del reporte por tramo. Calibración: el tramo de la ROI vigente reproduce `center_px` vigente (idéntico).

| tramo (columnas) | grosor (px) | evento 0.31 s (px) | otros 5, mediana (px) | 0.31 s / otros |
|---|---|---|---|---|
| 136–256 | 308 | −0.08 | 0.95 | −0.08 |
| 256–376 | 297 | 0.05 | 1.17 | 0.04 |
| 376–496 | 293 | 0.04 | 1.28 | 0.03 |
| 496–616 | 290 | 0.16 | 1.46 | 0.11 |
| 616–736 | 286 | 0.19 | 1.46 | 0.13 |
| 736–856 | 285 | 0.25 | 1.61 | 0.15 |
| 856–976 | 282 | 0.34 | 1.52 | 0.22 |
| 976–1096 | 283 | 0.38 | 1.69 | 0.22 |
| 1096–1216 | 285 | 0.41 | 1.55 | 0.26 |
| 1216–1336 | 291 | 0.39 | 1.36 | 0.28 |
| 1336–1456 | 295 | **0.52** | 1.32 | **0.39** |
| 1592–1712 | 331 | 0.12 | 0.51 | 0.20 |
| **ROI vigente 875–1039** | 282 | 0.37 | 1.58 | 0.23 |

**Resultado: sí, el evento de 0.31 s es local.** Las 5 contracciones estimuladas mueven todo el gel parecido (más en el centro, menos cerca de los anclajes). La de 0.31 s, en cambio, **no existe en el tercio izquierdo** (0.0 px) y crece hacia la derecha hasta 0.52 px en 1336–1456, **1.4 veces lo que mide la ROI**. Coincide con la impresión a ojo: mirada en la mitad derecha parece más grande que lo que da la zona angosta.

No cambia ningún número: el reporte mide en la ROI (como debe, por el criterio de zona plana) y la amplitud informada es la de los estimulados. Lo que agrega: **una contracción espontánea puede ser local**, y su amplitud depende de dónde está la ROI. Para las estimuladas, la ROI central da el máximo (en % del grosor: 0.56 % en la ROI, entre 0.18 y 0.60 % en los tramos).

Cuidado: el evento está a 0.31 s del inicio, su línea base sale de los primeros 0.15 s.

Figura: `d3_Video_063_CTRL1_5V.png`. Tabla: `tabla_d3_Video_063_CTRL1_5V.csv`. Series por tramo: `centros_*.npz`.
