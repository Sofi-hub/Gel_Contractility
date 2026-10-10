# B1 (resto): el "otro gradiente" a ~15 px del borde en 466 (2026-10-10)

**Cómo:** `medir_b1_466.py`. Misma ROI, columnas y CLAHE que `main.py`. En 1 de cada 5 fotogramas, para cada columna y borde, el gradiente (con la polaridad del borde) en guía ± 40 px y todos sus máximos locales > 5. No cambia nada.

| | borde superior | borde inferior |
|---|---|---|
| máximo principal (px hacia adentro de la guía, mediana) | +1 | +5 |
| segundo máximo, mediana | **+17 (hacia adentro del gel)** | +10 |
| separación 2.º − 1.º, mediana | **15 px** (IQR 4..21) | 5 px (hombro del mismo borde) |
| fuerza del 2.º / 1.º, mediana | **0.94** | 0.46 |
| columnas×fotogramas con 2.º > mitad del 1.º | **87 %** | 44 % |
| ¿se mueve con el gel? (correlación con `center_px`) | 0.74 (el 1.º: 0.88) | 0.37 |
| elegidos con ±15 a ≥ 13 px de la guía | 2.9 % | 0.1 % |

**Qué es:** en el **borde superior** de 466 hay un **segundo escalón oscuro→claro ~15–20 px hacia adentro del gel**, casi tan fuerte como el borde verdadero, que se mueve con el gel. En el mapa de máximos se ve como una franja brillante paralela al borde, justo debajo (`b1_Video_466_EXP5_FAPS4_40V.png`, panel derecho). Lo más probable: la cara superior del gel vista algo inclinada o fuera de foco (una "doble línea" del borde en un objeto 3D), o una capa más densa en la superficie. El inferior no tiene nada parecido (solo un hombro a 5 px del mismo borde).

**Por qué importa:** con ±15 el pico verdadero casi siempre gana (solo el 2.9 % de las elecciones queda cerca del límite), pero con ±30 el segundo escalón entra en la ventana y, como es casi igual de fuerte, a veces gana: de ahí el salto de grosor 201 → 191 px y 5 → 2 eventos que descartó B1. Confirma que **±30 para todos no sirve** y que la elección automática (±15, y ±30 solo si el borde se sale) es la correcta. No cambia ningún número.

Tabla: `tabla_b1_Video_466_EXP5_FAPS4_40V.csv`. Picos crudos: `picos_*.csv.gz`.
