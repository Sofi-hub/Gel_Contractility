# Correcciones al pipeline — ROI, ajuste RANSAC y parámetros expuestos

## Qué archivos reemplazar

Copiá estos 6 archivos sobre los tuyos (**solo estos**; el resto del proyecto no cambia):

```
src/preprocessing.py
src/robust_fitting.py
src/pipeline.py
src/qc_visualization.py
main.py
scripts/inspect_frame.py
```

## El diagnóstico, en una línea

La ROI del Video_063 fue `x = 184..577` (20% de la imagen) y dentro de ese
rango el gel pasa de 308.9 px a 288.6 px de grosor: no era la gauge region,
era el hombro del anclaje izquierdo. Con el borde superior curvo y
`ransac_residual_threshold` fijo en 1.5 px, RANSAC descartaba geometría en
vez de burbujas, y el conjunto de inliers cambiaba de frame a frame. Eso
solo ya generaba **std 0.25 px y p2p 1.2 px** en la serie de grosor con el
gel inmóvil — contra los 0.36 px de std que efectivamente mediste.

## Qué cambió

### 1. `auto_detect_roi` (preprocessing.py)

- La franja del gel se **sigue** columna por columna desde el centro hacia
  afuera, eligiendo tramos contiguos de máscara compatibles en posición y
  grosor. Antes se tomaba `col.min()` / `col.max()`, con lo cual cualquier
  halo o reflejo en la columna estiraba la "franja" y rompía la ROI.
- La gauge region se define por **planitud** (`|d(grosor)/dx| <= 0.02 px/px`)
  y cercanía a la **cintura del propio gel**, no por parecido a la mediana
  del centro de la imagen.
- La nitidez se exige a **ambos** bordes (antes era el máximo de toda la
  columna, y un borde superior nítido tapaba un inferior desenfocado).
- Override manual: `--x-start` / `--x-end`.
- `roi_quality` ahora dice cuántas columnas cayó cada criterio.

### 2. Umbral RANSAC adaptativo (robust_fitting.py)

`residual_threshold=None` (default) mide el MAD de los residuos **de ese
frame** y usa `3 x MAD`. Además `ransac_degree` pasa a 2 y se normaliza x a
[-1,1] antes de ajustar (con x en píxeles y grado 2 la matriz de diseño
estaba mal condicionada).

Medido sobre tus 60 columnas reales, gel inmóvil, solo ruido de medición:

| configuración | std artefacto | burbujas detectadas (5 col, +4 px) | falsos positivos |
|---|---|---|---|
| deg=1, umbral fijo 1.5 (antes) | 0.248 px | 4.71 / 5 | 11.5 |
| deg=1, umbral adaptativo | 0.052 px | 1.39 / 5 | 0.1 |
| **deg=2, umbral adaptativo (ahora)** | **0.090 px** | **4.95 / 5** | **2.3** |

Grado 1 con umbral adaptativo baja más el artefacto, pero para lograrlo el
umbral se abre a 4.4 px y deja de ver las burbujas. Grado 2 es el que baja
el artefacto **manteniendo** el umbral apretado (~1.8 px).

### 3. `pipeline.py`

- Bug corregido: `n_outlier_columns` suma los dos bordes (máx 2N) pero se
  comparaba contra `0.3 * N`. El umbral efectivo de `LOW_QUALITY` era 15%,
  no 30%.
- Nuevas columnas por frame: `outlier_frac`, `residual_top_px`,
  `residual_bottom_px`.
- El resultado del auto-ROI queda en `df.attrs["roi"]`.

### 4. CLI

`main.py` e `inspect_frame.py` exponen ahora `--min-gradient`,
`--half-window`, `--ransac-degree`, `--ransac-residual-threshold`,
`--ransac-residual-k/-floor`, `--x-start`, `--x-end`, `--roi-tolerance`,
`--roi-min-gradient`, `--roi-max-slope`, `--no-clahe`, `--denoise`,
`--savgol-window`, `--low-quality-frac`. Todos quedan registrados en la hoja
`resumen` del xlsx, así que una corrida es reproducible.

### 5. Diagnósticos nuevos

- **`roi_profile.png`** (inspect_frame) / **`00_roi_profile.png`** (main):
  grosor y nitidez de toda la imagen con la ROI sombreada. Mirá este
  primero: dice si la ROI cayó sobre la zona plana y por qué se cortó donde
  se cortó.
- `inspect_frame` ahora clasifica los outliers automáticamente:
  **contiguos** = el modelo no sigue la geometría; **dispersos** = burbujas.
- La tabla `diagnostics.xlsx` trae el residuo de cada columna contra el
  modelo, y el overlay muestra el umbral y el residuo efectivos.

## Verificación (video sintético con verdad conocida)

Video con 7 contracciones de 1.5 px inyectadas, hombros de anclaje, halos,
un reflejo difuso bajo el gel y 5 burbujas sobre el borde inferior:

| | ROI elegida | variación de grosor en la ROI | outliers | SNR | eventos k=6 | barrido de estabilidad |
|---|---|---|---|---|---|---|
| config vieja | 556–1170 (48%) | 9.6% | 36% | 3.1 | **0 / 7** | 8, 3, 0, 0, 0, 0 (sin meseta) |
| config nueva | 214–1077 (67%) | 0.0% | 8% | 6.3 | 5 / 7 | 7, 7, 7, 5, 2, 0 (**meseta en k=3–5**) |

Con la config nueva y **k = 4 o 5** (dentro de la meseta): **7/7 eventos, 0
falsos positivos**.

Fijate que el barrido de la config vieja sobre un video que SÍ se contrae da
`8, 3, 0, 0, 0, 0, 0, 0` — prácticamente idéntico al que obtuviste vos con
el Video_063 (`9, 1, 0, 0, 0, 0, 0, 0`). Esa curva no era la firma de "no hay
señal": era la firma de "la medición está dominada por artefacto de ajuste".

## Cómo correrlo

```bash
# 1. Mirar la ROI ANTES de procesar
python scripts/inspect_frame.py --video data\raw_videos\Video_063_CTRL1_5V.mp4 ^
    --frame-index 100 --output-dir data\processed_data\Video_063_CTRL1_5V\qc
#    -> abrir roi_profile.png y overlay.png

# 2. Si la ROI sigue sin caer en la zona plana, forzala:
#    --x-start 700 --x-end 1500   (leyendo los valores de roi_profile.png)

# 3. Procesar
python main.py --video data\raw_videos\Video_063_CTRL1_5V.mp4 --plot

# 4. Detectar eventos, empezando por el barrido
python scripts\analyze_contractions.py ^
    --input data\processed_data\Video_063_CTRL1_5V\serie_temporal.xlsx --amp-k 6
#    -> mirar 05_estabilidad_umbral.png y elegir un k DENTRO de la meseta

# 5. Control con burbujas: comparar con CLAHE apagado
python main.py --video ... --no-clahe --output-dir ...\sin_clahe
```

## Lo que queda pendiente de verificar con tus datos

- Por qué exactamente la ROI vieja se cortó en x=577 en tu video. Con el
  `maxproj_computed.png` que genera `inspect_frame` se ve de una.
- `--px-to-mm` sigue en 1.0: los "mm" de los reportes son píxeles.
- Si `--no-clahe` cambia la serie de forma apreciable, CLAHE está
  interactuando con las burbujas y conviene apagarlo para este set.
