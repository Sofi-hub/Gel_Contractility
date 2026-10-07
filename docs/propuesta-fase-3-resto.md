# Fase 3 (resto): borde y ajuste, magnitud en píxeles, canal

**Cerrada 2026-10-08.** Mediciones, decisiones, lo implementado y el resultado de la
regeneración de los seis videos. Lo que queda abierto está al final.

---

## Decisiones tomadas con Franco (2026-10-07/08)

- **Una sola métrica de contractilidad:** la traslación de la franja (`center_px`). Cifra
  principal: amplitud relativa (% del grosor en reposo), comparable entre videos. Al lado, la
  amplitud en px (solo comparable a igual aumento). El **adelgazamiento queda como diagnóstico
  interno, no se reporta** (depende del preproceso; en 268 y 583 no es significativo).
- **H27** (no cambiar ±15 px) y **H29** (no cambiar RANSAC): aprobados, sin cambio de código.
- **H20** (rescate con condición de cintura): aprobado e implementado.
- **H19:** eliminar la ROI manual de Video_466. Regla aprobada: separación mínima 3 px, piso
  de 40 columnas (ancho mínimo 120 px), columnas = min(60, ancho // 3). Implementada.
  Consecuencia aceptada: **Video_063 cambia de ROI**; cambio intencional y medido.
- **Chequeo de aceptación 2 (`outlier_frac` < 10 %)**: (a) por ahora solo avisa "en el límite"
  sin bloquear; (b) revisarlo en la Fase 4 (H24).
- **CLAHE se queda** (H26): lo que se reporta no depende de él más de un 4 %.
- **H54:** el canal sigue siendo `center_px` (sin ponderar); se registra el ruido de cada borde.
- **La regla de regresión** (Video_prueba y 063) detecta cambios **accidentales**; un cambio
  intencional y medido puede mover la línea base (como 28 → 29 en la Fase 2.2).

---

## Tema 6. Borde y ajuste (H19, H20, H26, H27, H29). Medido 2026-10-07

**Cómo se midió.** `scripts/medir_borde_ajuste.py` (solo mide), sobre los seis videos (~6 min
por video en la PC de Franco). Cada video se lee una vez y en cada fotograma se calculan cinco
versiones con la misma ROI y las mismas posiciones aproximadas del borde que el vigente:
`vigente` (CLAHE, ±15 px, RANSAC), `clahe_mco` (mínimos cuadrados, sin descartar columnas),
`crudo` (sin CLAHE), `crudo_mco` y `ventana25` (±25 px). Cada versión pasa por
`contraction_report.analizar` (k automático, ventana automática, 0.1 Hz). Salidas:
`data/fase3_borde/`.

**Control:** la versión `vigente` reproduce los seis `serie_temporal.xlsx` exactamente
(diferencia máxima de `center_px` = 0.0; de grosor, 2e-13 px).

### Conteo de eventos por versión

| video | vigente | clahe_mco | crudo | crudo_mco | ventana25 |
|---|---|---|---|---|---|
| Video_prueba | 29 | 29 | 29 | 29 | 29 |
| Video_063 | **6** | 5 | 5 (NR) | 5 | 5 |
| Video_268 | 6 | 6 | 6 | 6 | 6 |
| Video_466 | 5 | 5 | 5 | 5 | **0 (NR)** |
| Video_583 | 6 | 6 | **15 (NR)** | **18 (NR)** | 6 |
| Video_491 | 2 | 2 | 2 | 2 | 2 |

NR = no reportable. Los períodos coinciden en todas las versiones reportables (≤ 4 ms).

### Ruido del canal y del grosor (MAD sin deriva, px)

| video | vigente canal / grosor | crudo | clahe_mco | crudo_mco |
|---|---|---|---|---|
| Video_prueba | 0.085 / 0.090 | 0.091 / 0.086 | 0.074 / 0.068 | 0.076 / 0.061 |
| Video_063 | 0.034 / 0.065 | 0.051 / 0.101 | 0.059 / 0.112 | 0.066 / 0.104 |
| Video_268 | 0.049 / 0.070 | 0.077 / 0.133 | 0.058 / 0.103 | 0.054 / 0.098 |
| Video_466 | 0.212 / 0.365 | 0.202 / 0.236 | 0.167 / 0.280 | **0.106 / 0.106** |
| Video_583 | 0.072 / 0.117 | 0.040 / 0.055 | 0.085 / 0.158 | 0.036 / 0.053 |
| Video_491 | 0.068 / 0.103 | 0.059 / 0.079 | 0.068 / 0.128 | 0.047 / 0.043 |

No hay una versión que gane en todos.

### Lo que dice cada prueba

**A/B, CLAHE (H26).** El conteo no depende de CLAHE en 4 de 6 videos (en 063 y 583 cambia por
los dos motivos de abajo). La amplitud de la traslación cambia ≤ 4 % (Video_prueba 2.09 → 2.03
px; 466 4.29 → 4.34). El **adelgazamiento** sí depende: `cociente_robusto_pct` vigente → crudo:
Video_prueba 18.2 → 8.6 %; 268 −2.4 → +6.3 %; 466 6.3 → −0.4 %; 583 1.0 → −2.2 %. La diferencia
CLAHE − crudo se mueve con la señal en el grosor (Video_prueba: correlación −0.62); en
`center_px` mucho menos (0.01–0.36). Corrimiento medio CLAHE − crudo: borde superior +0.13 a
+0.91 px, inferior −0.22 a −0.65 px.

**C, RANSAC vs mínimos cuadrados (H29).** Conteo igual en 5 de 6. En 466 RANSAC suma ruido
(0.212 vs 0.167); en 063, 268 y 583 lo baja (063: 0.034 vs 0.059).

**D, ventana de búsqueda (H27).** ±25 px **rompe Video_466** (3.7 % de bordes perdidos, el
centro salta hasta 10 px, 0 eventos). En los otros cinco da lo mismo.

**E, ruido compartido entre columnas (H19).** La correlación del error de borde entre dos
columnas cae debajo de 0.2 a los **2–3 px** (peor caso 8 px).

**F, rescate con condición de cintura (H20).** En los seis reales no cambia nada. En el gel
sintético con zona plana de 150 px, el rescate viejo elige el anclaje (0–553) y con la
condición elige 813–1108 (zona verdadera 885–1035).

### Dos cosas que aparecieron y no eran de este tema

1. **El sexto evento de Video_063 (t = 0.308 s)** desaparece en las variantes de borde y con 50
   o 40 columnas; con la ROI nueva de 063 sí aparece (refuerza H11: depende del procesamiento).
2. **Video_583 tiene una ráfaga de oscilaciones al final (≈ 72.0–73.7 s, cada ~0.1 s,
   ~0.5–1 px en el borde superior)**, visible en la serie vigente. Sin CLAHE el umbral baja y
   cuentan como 9–12 eventos. Hay que mirar el video en ese tramo.

### H19: columnas adaptables y ROI automática de 466 (medido 2026-10-08)

`scripts/medir_roi_columnas.py` y `scripts/medir_roi_ancho.py` (solo miden).

**1. Piso de columnas** (ROI vigente con menos columnas):

| columnas | Video_prueba eventos / ruido* | Video_063 eventos / ruido* |
|---|---|---|
| 60 | 29 / 1.00 | 6 / 1.00 |
| 50 | 29 / 1.10 | 5 (NR) / 0.94 |
| 40 | 29 / 1.13 | 5 / 1.41 |
| 30 | 29 / 1.25 | **10** / 1.03 |
| 20 | 29 / 1.30 | **14** / 1.06 |

\*ruido del canal / el de 60 columnas (si fuera independiente: 1.10 / 1.22 / 1.41 / 1.73).

**Piso: 40 columnas**, el menor sin eventos espurios en ninguno de los dos. Lo fija un solo
video (063). Se descartó 50 porque deja a 466 justo en el límite (150 // 3 = 50) sin ventaja
medida.

**2. Video_466 con la ROI que encuentra el programa** (bloque `gauge_cintura`, 696–846):

| ROI | col. | eventos | ruido canal | outliers | residuo sup/inf | amplitud | período (s) |
|---|---|---|---|---|---|---|---|
| manual vieja 700–900 | 60 | 5 | 0.212 | 7.9 % | 1.75 / 0.68 | 4.29 px (2.13 %) | 10.0022 |
| rescate viejo 944–1169 | 60 | 5 | 0.192 | 16.2 % | 0.82 / 0.72 | 4.03 px (1.97 %) | 10.0024 |
| **cintura 696–846** | **50** | 5 | **0.182** | **10.5 %** | 1.32 / 0.59 | 4.36 px (2.16 %) | 10.0018 |

**3. ¿Zona ancha o zona chica y plana?** (Video_063):

| | ancha 390–1423 (vieja) | chica 875–1039 (nueva) |
|---|---|---|
| ancho / columnas / variación | 1033 px / 60 / 4.9 % | 164 px / 54 / 0.35 % |
| eventos | 6 | 6 (mismos tiempos) |
| ruido canal / grosor | 0.034 / 0.065 px | **0.024 / 0.049 px** |
| residuo de ajuste sup / inf | 0.88 / 0.78 px | **0.45 / 0.43 px** |
| outliers | 7.7 % | 6.8 % |
| amplitud / señal-ruido | 1.51 px (0.535 %) / 44 | 1.59 px (0.564 %) / 66 |

La zona chica y plana mide mejor; el comentario viejo del código ("la zona corta mide más
ruidoso") era falso.

---

## Tema 7. Magnitud en píxeles (H51)

`scripts/medir_magnitud_px.py` (solo mide): fotogramas quietos reales desplazados una cantidad
conocida (0.1 a 3 px; rígido, con desenfoque, solo la franja) y un gel sintético exacto.

Medido / verdadero, corrimiento rígido:

| video | bordes CLAHE | bordes crudo | correlación (`motion_check`) |
|---|---|---|---|
| Video_prueba | 1.007 | 0.994 | 0.226 |
| Video_063 | 1.001 | 1.001 | 0.430 |
| Video_466 (ROI vieja) | **0.916** | 1.019 | 0.228 |
| sintético exacto | 0.971 | 0.985 | 0.176 |

- **`center_px` mide bien la magnitud.** Con desenfoque da la posición media (~s/2).
- En 466 con CLAHE los bordes miden ~8 % de menos; en la serie real la diferencia con/sin CLAHE
  es 1 %. No se cambia CLAHE.
- **El 0.18 de H51 es un defecto de `motion_check._subpixel_shift`**: suma productos sin
  normalizar por la superposición. Con Pearson sobre la parte superpuesta el sintético da
  0.248 / 0.499 / 0.997 / 1.997 / 2.998 para 0.25 / 0.5 / 1 / 2 / 3 px. Arreglo: Fase 4.

---

## Tema 8. H54: por qué un borde solo supera en SNR a `center_px`

| video | amplitud sup / inf (px) | ruido sup / inf (px) | ρ | SNR sup / inf / centro |
|---|---|---|---|---|
| Video_prueba | 2.50 / 1.66 | 0.087 / 0.070 | 0.70 | 29 / 24 / 33 |
| **Video_063** | 1.53 / 1.43 | **0.022 / 0.062** | 0.00 | **71** / 23 / 44 |
| **Video_268** | 1.40 / 1.71 | **0.073 / 0.035** | 0.28 | 19 / **49** / 35 |
| Video_466 | 4.22 / 4.03 | 0.267 / 0.246 | 0.22 | 16 / 16 / 22 |
| Video_583 | 3.06 / 3.01 | 0.102 / 0.072 | 0.28 | 30 / 42 / 46 |
| Video_491 | 1.07 / 0.92 | 0.083 / 0.061 | 0.41 | 13 / 15 / 16 |

(Series de la ROI vieja.) **Causa: ruido desigual entre bordes**, no ruido correlacionado ni
otro observable. El conteo no cambia detectando sobre un borde. No se pondera el centro. Se
registra `ruido_borde_sup_px`, `ruido_borde_inf_px`, `cociente_ruido_bordes`. Con la ROI nueva
de 063 el cociente bajó de 2.77 a 1.09.

---

## Implementado

- **`src/preprocessing.py`:** `auto_detect_roi(..., min_columns=40)`; ancho mínimo 120 px;
  `roi_quality["n_columnas_usadas"]` = min(60, max(40, ancho // 3)); rescate con
  `cerca=near_waist`; `roi_quality["roi_contiene_cintura"]`; comentario del ancho mínimo
  reescrito; variable muerta `n_gel` borrada.
- **`src/pipeline.py`:** `roi_min_columns = 40`; muestrea `n_columnas_usadas` columnas.
- **`main.py`:** `--roi-min-columnas`; hoja `resumen` con `ROI contiene cintura`,
  `n_columns (maximo)`, `n_columnas usadas`, `roi_min_columnas`, `outlier_frac medio`; aviso
  "en el límite" del chequeo 2.
- **`scripts/contraction_report.py`:** ruido por borde.
- **`tests/test_roi.py`** (nuevo). **Cuaderno v4:** columnas según la ROI, parámetros y textos.

## Regeneración (2026-10-08)

Corrida anterior archivada en `data/processed_data/_superadas/<video>_v6`.

| video | ROI (método, col.) | eventos | k (meseta) | ruido canal | amplitud | período |
|---|---|---|---|---|---|---|
| Video_prueba | 454–1516 (cintura, 60) | 29 | 9.4 (5.3–15.2) | 0.085 | 2.09 px (2.31 %) | 10.00043 ± 0.0023 |
| Video_063 | **875–1039** (plana, 54) | 6 | 11.4 (9.4–13.8) | **0.024** | 1.59 px (0.56 %) | 9.99812 ± 0.00304 |
| Video_268 | 918–1328 (cintura, 60) | 6 | 12.5 (5.8–24.4) | 0.049 | 1.55 px (0.57 %) | 10.00132 ± 0.0023 |
| Video_466 | **696–846** (cintura, 50) | 5 | 11.4 (6.4–20.2) | **0.182** | 4.36 px (2.16 %) | 10.00184 ± 0.00542 |
| Video_583 | 718–1187 (cintura, 60) | 6 | 16.7 (12.5–24.4) | 0.072 | 3.10 px (1.31 %) | 10.00024 ± 0.0023 |
| Video_491 | 459–1206 (cintura, 60) | 2 | 10.4 (7.8–13.8) | 0.068 | 1.02 px (0.40 %) | sin tren |

Video_prueba, 268, 583 y 491: **idénticos** a la corrida anterior (mismos eventos, k, amplitud,
ruido, período, cinética). 063 y 466: cambio intencional, mismos eventos y menos ruido. 466:
TTP 255 ms [137, 365], RT50 192 ms [33, 260]; `outlier_frac` 10.5 % ("en el límite").

---

## Lo que queda abierto o puede cambiar con `RARITOS`

**Reglas que salieron de pocos videos:**
1. **Piso de 40 columnas**: lo fija un solo video (063). Si un gel angosto da eventos espurios
   a 40, subirlo; si uno con zona buena < 120 px cae al rescate, revisar.
2. **"Zona chica y plana mide mejor que ancha"**: medido solo en 063.
3. **Separación de 3 px**: medida en los seis (2–3 px; peor caso 8 px).
4. **CLAHE achica ~8 % el corrimiento en 466**: si la amplitud con/sin CLAHE difiere > 5 %,
   reconsiderar CLAHE (H26).
5. **La cintura se estima con la mediana del grosor (H21)**: falla con cintura corta (sintético:
   437 contra 285). El rescate con cintura lo mitiga, no lo arregla.
6. **Ruido desigual entre bordes (H54)**: con datos suficientes, fijar un umbral de aviso.

**Para la Fase 4 o después:**
- **H24 / chequeo 2**: reemplazar `outlier_frac` por un criterio comparable entre ROIs (p. ej.
  residuo de ajuste). Video_466 queda en 10.5 %.
- **`motion_check`**: `_subpixel_shift` (H51), veredicto (H50), eje de tiempo. `signal_check` (H49).
- **H11 / sexto evento de Video_063** (t = 0.31 s, a 9 fotogramas del inicio): aparece o
  desaparece según el procesamiento. Decidir si se reporta.
- **Ráfaga final de Video_583** (72–73.7 s): mirar el video.
- **Adelgazamiento**: sigue en `contracciones.xlsx` como diagnóstico; decidir si se saca.
- H25 (resto), H21, H22, H23, H28, H30.
