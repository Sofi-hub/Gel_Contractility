# Video_063_CTRL1_5V — diagnóstico completo (3 rondas)

Última actualización: 2026-09-09. **Conclusión: resuelto.**

> **Documento histórico (archivado 2026-10-08).** Junta las tres rondas que antes estaban en `gel_fix.md` (ronda 1),
> `LEEME.md` (ronda 2) y `LEEME_v3.md` (ronda 3). Los números de esta página son de septiembre; los vigentes están en
> `../ESTADO-arranque-chat-nuevo.md`.

---

# RONDA 3 — resuelto: la contracción SÍ está, el observable estaba mal

**Esta ronda corrige la conclusión de la ronda 2.** El test de asimetría sobre
`thickness_px` decía "no hay población de contracciones en Video_063". Era
cierto *sobre esa columna*, y por eso llevaba a la conclusión equivocada: la
contracción existe, pero casi toda su amplitud está en un observable que
`thickness_px` no puede ver por construcción.

## Resultado

Video_063 tiene **5 contracciones limpias con marcapasos perfectamente regular
cada 10.044 s (0.0996 Hz)**. Video_prueba tiene el mismo marcapasos:
**10.091 s (0.0991 Hz)**. Los dos videos están estimulados igual (coherente con
el `5V` del nombre del archivo). Video_063 nunca estuvo roto: contrae ~4.4
veces más débil.

La contracción no se manifiesta principalmente como adelgazamiento sino como un
**desplazamiento vertical de toda la franja**: los dos bordes se mueven juntos,
y el grosor —que es la resta de los dos— es ciego a esa componente.

| | Video_prueba | Video_063 |
|---|---|---|
| traslación por evento (`center_px`) | 6.64 px | 1.51 px |
| adelgazamiento (medida robusta) | 0.77 px | 0.19 px |
| cociente adelgazamiento/traslación | 15.4 % | 12.8 % |
| ruido por frame de `center_px` | 0.086 px | 0.034 px |
| ruido por frame del grosor | 0.089 px | 0.065 px |
| SNR por frame en `center_px` | 77 | **44** |
| SNR por frame en `thickness_px` | 9 | **3** |

El cociente adelgazamiento/traslación es del mismo orden en los dos videos: **la
mecánica de la contracción es la misma**, cambia la amplitud. El grosor es un
observable atenuado ~6× respecto de la traslación, así que necesita ~6× más
señal para llegar al mismo SNR. En Video_prueba la traslación es lo bastante
grande como para que el resto igual asome sobre el ruido; en Video_063 no.

## Prueba de estabilidad del umbral

Falsos = el mismo detector corrido sobre la señal invertida (una contracción
solo puede ir en un sentido, así que lo que aparece invertido es ruido).

Video_063:

| canal | k | eventos | falsos |
|---|---|---|---|
| `center_px` | 6–8 | 6 | 0 |
| `center_px` | **10–20** | **5** | **0** |
| `thickness_px` | 3 | 7 | 11 |
| `thickness_px` | 4 | 7 | 5 |
| `thickness_px` | ≥6 | 0 | 0 |

La segunda mitad de esa tabla **es exactamente el síntoma original reportado**:
con `--amp-k 3.0` aparecían eventos mezclados con falsos positivos, y con
`--amp-k 6.0` no aparecía ninguno. No era un problema de umbral, ni de
sobreajuste del detector, ni de las burbujas: era que se estaba midiendo la
variable equivocada.

Video_prueba, para comparar: `center_px` da meseta de 10 eventos desde k=6
hasta k=20 con 0 falsos (6 del marcapasos + 4 espontáneos irregulares entre
2 y 10 s, antes de que arranque la estimulación).

## La hipótesis del anclaje flojo no hace falta

Video_prueba, que funciona, muestra el **mismo modo dominado por traslación** y
con un cociente adelgazamiento/traslación parecido. Si un extremo suelto
explicara el Video_063, el video de control debería mostrar adelgazamiento
puro, y no lo hace. Es la mecánica normal de este montaje, no un defecto de la
muestra 063.

## Artefacto de motion blur (nuevo)

En el frame de máxima velocidad el grosor medido da un salto **positivo**
(+0.39 px en 063, +0.17 px en prueba). No es engrosamiento: el borde se
emborrona por el movimiento y los dos bordes se "abren". Contamina el mínimo
del promedio alineado si cae cerca. Por eso ahora se reportan dos medidas:

- `mínimo`: mínimo del promedio alineado (puede estar contaminado)
- `robusto`: promedio de los 3 frames **posteriores** al pico (evita el blur)

Usar siempre la robusta para comparar entre videos.

## Herramienta nueva: `scripts/contraction_report.py`

    python scripts/contraction_report.py --input .../serie_temporal.xlsx
    python scripts/contraction_report.py --input A.xlsx --compare B.xlsx

1. **Detecta sobre `center_px`**, no sobre el grosor. Decide solo el signo de
   los eventos mirando qué cola de la distribución es más pesada, así que no
   depende de la convención de la imagen ni de si el gel sube o baja.
2. **Escaneo de estabilidad con control simétrico** (señal invertida).
3. **Mide el adelgazamiento promediando los eventos alineados**
   (event-locked average). Con 5 eventos el ruido del promedio baja √5 y el
   adelgazamiento del Video_063 pasa de ~1 σ por frame a **11 σ**. El grosor
   sigue siendo la variable biomecánicamente interesante; lo que no sirve es
   usarlo para *detectar*.

## ROI: el auto-ROI ya funciona sin forzarlo

Con los arreglos de la ronda 2 aplicados, en la máquina del usuario:

- Video_063: `gauge_cintura`, cintura 285 px, ROI **390–1423**, 4.91% de variación.
- Video_prueba: `gauge_cintura`, cintura 302 px, ROI **454–1516**, 5.32% de variación.

Ya no hace falta el `--x-start 800 --x-end 1400` manual.

## Pendiente

- Test de CLAHE on/off: es la prueba de si estamos reintroduciendo
  sensibilidad a la iluminación por la puerta de atrás.
- Video de control donde SOLO cambie la luz y el gel no se mueva — es el
  argumento cuantitativo contra MuscleMotion.
- `--px-to-mm` sigue en 1.0: los "mm" son píxeles.
- Batería de varios videos más, ya con `center_px` como canal de detección.

---

# RONDA 2 — asimetría, y los bugs de cintura/pendiente/ancho

> **Nota:** la conclusión principal de esta ronda ("no hay población de
> contracciones en Video_063") quedó **superada por la ronda 3**. El test de
> asimetría era correcto pero se aplicó solo a `thickness_px`, que es el
> observable equivocado para este montaje. Los bugs corregidos y las
> herramientas de esta ronda siguen siendo válidos.

## El test de asimetría

No depende de elegir ningún parámetro:

**Una contracción es una excursión hacia ABAJO y el gel pasa más tiempo
relajado que contraído → cola larga hacia abajo → asimetría (skew) negativa.
El ruido es simétrico → skew ≈ 0.**

Deriva quitada con mediana móvil de 2 s (mediana, NO pasabanda: un pasabanda
convierte cada evento real en un dip flanqueado por dos picos falsos hacia
arriba y destruye la asimetría que se quiere medir).

| serie | recorrido | ruido | **skew** | % bajo −4σ | % sobre +4σ |
|---|---|---|---|---|---|
| Video_prueba (código viejo) | 1.79 px | 0.114 px | **−2.21** | 3.39% | 0.10% |
| Video_063 (ROI 800–1400, deg 2) | 1.20 px | 0.090 px | **+0.28** | 0.22% | 0.33% |

Calibración con verdad conocida (sintéticos con renderizado **antialiased**; la
primera versión usaba máscara binaria, con lo cual el grosor solo cambiaba en
escalones enteros de píxel y fabricaba una escalera espuria de ~2 px):

| sintético | corr. con el pulso | skew | veredicto |
|---|---|---|---|
| contracción de grosor 1.5 px | **−0.976** | **−1.97** | HAY población |
| traslación vertical 1.5 px | +0.15 | −0.12 | NO hay |
| gel inmóvil | +0.18 | +0.02 | NO hay |

Notar que el sintético de **traslación** da skew ≈ 0 en `thickness_px` — que es
precisamente lo que pasa con el Video_063 real. La pista estaba ahí.

### Hipótesis descartadas en la ronda 2

- **Ritmo enterrado**: un periodograma de una sola realización contra la
  mediana global del espectro sugería un pico de 1.00 Hz a 28× el fondo. Con
  Welch promediado (16 g.l.) y fondo LOCAL queda en 2.4× — no significativo.
- **Compresión del mp4**: mismo sintético sin pérdidas (FFV1) vs comprimido
  (mp4v) → skew −1.97 vs −1.54, p2p 1.78 vs 1.66 px. No borra la señal.
- **Artefacto del ajuste**: en el Video_063 el skew de `residual_top_px`,
  `residual_bottom_px` y `n_outlier_columns` es +0.17, +0.23 y +0.02.

## Bugs corregidos en la ronda 2

1. **Cintura del gel mal medida.** Era el percentil 5 de T sobre todas las
   columnas seguidas; el seguimiento llega al borde de la imagen y más allá
   del poste sigue una hebra de 60–110 px que arrastraba el percentil.
   Reportaba `cintura = 111 px` con un gel de 285 px → 1588 columnas
   descartadas "por grosor" → caída a `solo_nitidez` (12.63% de variación).
   Ahora: escala = mediana de T sobre columnas con ambos bordes nítidos; se
   descarta lo que no esté en [0.6, 1.6]× esa escala; cintura = p5 del resto.
2. **Pendiente del perfil mal calculada.** El grosor de la máscara es entero,
   así que T avanza a saltos de 1 px y `np.gradient` directo daba picos de
   ~1.5 px/px en cada escalón: el criterio de planitud no se cumplía nunca.
   Ahora se promedia sobre una ventana ancha antes de derivar.
3. **Ancho mínimo de ROI mal referenciado.** Era fracción del ancho de la
   imagen; ahora es fracción de las columnas CON GEL (35%). Motivo: el
   criterio estricto daba 875–1039 (164 px, 0.35% de variación) — plano pero
   con las 60 columnas a 2.7 px entre sí, compartiendo ruido de imagen y tile
   de CLAHE, con lo cual el grosor sale MÁS ruidoso. `roi_quality`
   ["alternativas"] ahora lista lo que habría dado cada nivel de la cascada y
   se imprime siempre.

## Herramientas de la ronda 2

- **`scripts/motion_check.py`** — qué se mueve. Mide |I(t)−I(t−1)| en la zona
  del gel con bordes, en el interior sin bordes, y en una franja de fondo de
  control; más desplazamiento vertical y axial subpíxel por correlación
  cruzada (con guardia: si la correlación no engancha devuelve NaN).
  Clave: se compara la **modulación** de |ΔI| contra el fondo, no su nivel
  absoluto (el nivel lo domina el ruido de sensor y da 1.00× siempre).
  Validado: cambio de grosor → 8.3× bordes / 1.0× interior; traslación →
  216× / 217×; inmóvil → 0.9× / 1.0×.
- **`scripts/signal_check.py`** — el test de asimetría sobre cualquier
  `serie_temporal.xlsx`, con gráfico `08_asimetria.png`.
- **`y_top_px` / `y_bottom_px` / `center_px`** en la serie temporal. Esta
  columna es la que terminó resolviendo el caso en la ronda 3.

---

# RONDA 1 — la ROI y el umbral RANSAC estaban sobreajustados

## Evidencia

`ROI x_start = 184`, `x_end = 577` — 393 px de ~1920. No hubo fallo de
detección a la derecha de x=577: no hubo intento. Dentro de esa ROI el grosor
va de 308.85 px a 288.60 px (7%): era el hombro del anclaje izquierdo.

Causa: `auto_detect_roi` tomaba `col.min()`/`col.max()` de la máscara Otsu
(cualquier halo estira la franja y rompe la contigüidad) y definía la gauge
region como "±10% de la mediana del 20% central de la IMAGEN", criterio que
tolera 30 px de variación y no exige planitud.

Residuos contra el modelo de grado 1:

| borde | std residuo | máx \|residuo\| | outliers |
|---|---|---|---|
| superior | 1.18 px | 3.15 px | 9 |
| inferior | 0.48 px | 1.04 px | 0 |

Con `residual_threshold = 1.5 px` fijo reproduce el 9/0 exacto. Los outliers
eran **contiguos** (x=290, 330–356) = curvatura, no burbujas.

Artefacto cuantificado (60 columnas reales, gel inmóvil, solo ruido de
medición de 0.27 px por columna):

| configuración | std artefacto | p2p |
|---|---|---|
| deg=1, umbral fijo 1.5 (la que estaba) | 0.249 px | 1.15 px |
| deg=2, umbral adaptativo 3·MAD | 0.090 px | 0.52 px |

La serie real medía std 0.361 px: ~70% era artefacto de ajuste.

## Correcciones de la ronda 1

1. `auto_detect_roi`: sigue la franja columna a columna desde el centro hacia
   afuera (inmune a halos); gauge region por planitud + cercanía a la cintura;
   nitidez exigida a ambos bordes; override `--x-start`/`--x-end`.
2. Umbral RANSAC adaptativo (3×MAD del propio frame), `ransac_degree` 2, x
   normalizado a [−1,1]. Detección de burbujas: 4.95/5 columnas con 2.3 falsos
   positivos, contra 4.71/5 con 11.5 de la configuración vieja.
3. Bug de `frame_quality`: `n_outlier_columns` suma dos bordes (máx 2N) pero
   se comparaba contra `0.3*N`. Umbral efectivo 15%, no 30%.
4. Todos los parámetros expuestos en la CLI y registrados en la hoja `resumen`.
5. `roi_profile.png` y clasificación automática de outliers contiguos
   (= modelo) vs dispersos (= burbujas).

Verificación con un sintético de 7 contracciones: config vieja 0/7 eventos y
barrido `8,3,0,0,0,0,0,0`; config nueva 7/7 con k=4–5 y barrido
`7,7,7,5,2,0,0,0`. El barrido de la config vieja sobre un video que SÍ
contrae es casi idéntico al que dio el Video_063 (`9,1,0,0,0,0,0,0`).
