# Glosario de la revisión (se va ampliando etapa por etapa)

Para leer `hallazgos-revision-codigo.md` sin conocer la jerga. Cada término dice dónde se ve en el código o en los archivos.

## Video y tiempo
- **Fotograma (frame):** una imagen del video. **fps:** fotogramas por segundo. Tus videos se graban a 30 fps.
- **Timestamp / PTS:** la hora de cada fotograma escrita en el archivo (a diferencia de calcularla como `fotograma ÷ fps`).
- **Hueco:** un salto en los timestamps mayor a 1.5 veces el intervalo normal. Puede ser una interrupción real (8 a 13 fotogramas perdidos) o simple temblor de la hora.
- **Jitter:** el temblor de las horas: los fotogramas llegan un poco antes o después de lo debido (unos 5 ms típicos en tus videos).

## El gel y la zona de medición
- **Anclajes / postes:** los dos extremos donde el gel está sujeto. Cerca de ellos manda la tensión del anclaje, no la contracción de las células.
- **Gauge region (zona útil o ROI):** el tramo central del gel, de grosor parejo, donde se mide.
- **Cintura:** el grosor mínimo típico del gel (percentil 5 del perfil de grosor). Es la referencia para saber si una columna está "cerca de la cintura".
- **Columna x / fila y:** `x` es la posición horizontal en la imagen, `y` la vertical (crece hacia abajo).
- **Imagen de máximos:** una imagen donde cada píxel guarda el brillo más alto que tuvo durante todo el video. Sirve para ubicar el gel sin depender de un fotograma en particular.
- **Máscara / Otsu:** convertir la imagen en blanco y negro con un umbral que el método de Otsu elige solo. Lo claro (gel) queda en blanco.
- **Perfil de grosor:** el grosor del gel en cada columna x, de izquierda a derecha.
- **Pendiente del grosor:** cuántos píxeles cambia el grosor por cada píxel de x. `0.02` = 2 px cada 100 px. "Plano" = pendiente baja.
- **Variación de grosor dentro de la ROI:** (máximo − mínimo) / mínimo. El criterio de aceptación exige menos de 6 %.
- **Cascada:** la lista de criterios de la zona útil, del más exigente al más laxo. Gana el primero que da una zona de al menos 180 px.
- **Rescate:** si el criterio ganador no cumple 6 %, se busca la ventana más ancha que sí lo cumpla.

## Imagen y bordes
- **Nitidez del borde:** cuán brusco es el cambio de brillo en el borde del gel. Se mide como el gradiente vertical (diferencia de brillo entre filas vecinas, en niveles de gris por píxel). Un borde borroso tiene nitidez baja.
- **Umbral de nitidez (`roi_min_gradient`=10, `min_gradient`=5):** nitidez mínima para usar una columna. Es un número de niveles de gris por píxel.
- **Suavizado / mediana móvil:** reemplazar cada valor por la mediana de sus vecinos, para quitar saltos y ruido. En la ROI: ventana de 33 columnas para el grosor y de 77 para la pendiente.
- **Mediana:** el valor del medio cuando se ordenan los datos. No se deja arrastrar por valores extremos, a diferencia del promedio.
- **Percentil 5:** el valor debajo del cual queda el 5 % de los datos. Es un "mínimo robusto".
- **CLAHE:** mejora de contraste local. Divide la imagen en 8 × 8 rectángulos (tiles; de 240 × 135 px en 1920 × 1080) y en cada uno reparte el brillo para aprovechar todo el rango, con un límite para no amplificar el ruido. Se aplica a cada fotograma antes de buscar los bordes. Riesgo: si algo cambia dentro de un tile (una burbuja), cambia el reparto de todo el tile.
- **Subpíxel:** resolución de fracciones de píxel (se ve en la Etapa 3).

## Ajuste y calidad (se profundiza en las Etapas 3 y 4)
- **Medición de borde:** en cada fotograma se mide la altura de cada borde en 60 columnas de la ROI: 60 × 2 bordes = **120 mediciones por fotograma**.
- **Ajuste robusto (RANSAC):** una curva de grado 2 que pasa por la mayoría de esas mediciones e ignora las que no encajan.
- **Outlier:** una medición de borde que no encaja con la curva del resto (burbuja, reflejo, ruido). Se descarta.
- **`outlier_frac`:** fracción de las 120 mediciones de un fotograma que se descartaron. 0.0773 = 7.7 %. La media sobre todo el video debe ser menor a 10 %.
- **Residuo:** distancia entre cada medición y la curva ajustada. `residual_top_px` / `residual_bottom_px` resumen su dispersión (con la MAD, una medida robusta de dispersión) para cada borde.
- **Calidad del fotograma:** `OK`, `LOW_QUALITY` (30 % o más de descartes) o `REJECTED` (no se pudo medir).


## Etapa 3 — términos nuevos

- **Gradiente:** cuánto cambia el brillo de un píxel al siguiente (aquí, la diferencia entre sus dos vecinos dividida por 2). En un borde el brillo salta y el gradiente tiene un pico.
- **Ventana de búsqueda (`half_window`):** tramo de la columna, de ±15 px alrededor de la posición aproximada, donde se busca el pico.
- **Polaridad:** sentido del salto de brillo. +1 = de oscuro a claro bajando (borde superior); −1 = de claro a oscuro (borde inferior).
- **Vértice de la parábola / `delta`:** se dibuja la parábola que pasa por el pico y sus dos vecinos; su cima da la fracción de píxel (entre −0.5 y 0.5) que se suma al píxel entero. Así sale, por ejemplo, 412.17.
- **Sigmoide:** método alternativo: ajusta una curva en "S" a todo el tramo del borde; no se usa por defecto.
- **`min_gradient`:** si el pico es menor que este valor (5), la columna se descarta por "borde no confiable".
- **Corrimiento de CLAHE:** diferencia entre la posición del borde medida con y sin CLAHE; preocupa cuando cambia de fotograma a fotograma.


## Etapa 4 — términos nuevos

- **Polinomio de grado 2 (parábola):** la curva `a + b·x + c·x²` con la que se modela el borde a lo largo de la ROI. Grado 1 sería una recta.
- **Mínimos cuadrados (MCO):** el ajuste "normal": la curva que minimiza la suma de los errores al cuadrado, usando TODOS los puntos por igual. Una burbuja lo arrastra.
- **RANSAC:** ajuste robusto. Prueba muchas veces con unos pocos puntos al azar, arma una curva y cuenta cuántos puntos caen cerca; se queda con la curva que reúne más y descarta el resto.
- **Inlier / outlier:** punto que cae cerca de la curva (se usa) / lejos (se descarta).
- **Umbral de residuo:** distancia máxima a la curva para ser inlier; aquí 3×MAD del fotograma, con piso de 0.4 px.
- **Ajuste recortado:** ajuste que se repite descartando los puntos raros para estimar sólo la escala del ruido.
- **Extrapolar:** usar la curva ajustada fuera de la zona donde hay puntos aceptados (aquí, en las columnas descartadas).
- **`REJECTED` / `LOW_QUALITY` / `OK`:** etiquetas del fotograma: sin ajuste posible / 30 % o más de columnas descartadas / el resto.
- **Outliers contiguos vs dispersos:** dispersos = burbujas sueltas; contiguos (varios seguidos) = el modelo no representa el borde.


## Etapa 5 — términos nuevos

- **Orquestador (`pipeline.py`):** el código que encadena las etapas anteriores y repite el ciclo en cada fotograma.
- **`DataFrame` / tabla:** la tabla de datos (una fila por fotograma) que sale del pipeline; se guarda como hoja `diagnostics` del xlsx.
- **Hoja `resumen`:** segunda hoja del xlsx con una lista de datos de la corrida (ROI usada, parámetros, frames perdidos…).
- **Savitzky–Golay:** suavizado que ajusta una curva a una ventana de 11 fotogramas; sólo se usa para el gráfico del grosor.
- **`REJECTED`:** fotograma sin ajuste posible; sus valores quedan vacíos (NaN). **NaN:** "sin dato".
- **Trazabilidad:** poder reconstruir qué código, qué parámetros y qué versión produjeron un resultado.


## Etapa 6 — términos nuevos

- **Quitar la deriva (detrend):** restar a la señal su "nivel lento" (mediana móvil de 2 s) para que quede sólo lo rápido: los eventos y el ruido.
- **MAD (aquí, "ruido"):** desviación típica robusta: mediana de las distancias a la mediana × 1.4826; no se deja engañar por los picos grandes.
- **`k`:** multiplicador del umbral: se cuenta como evento un pico mayor que `k × ruido`.
- **`find_peaks` y `distance`:** busca máximos locales; si dos están a menos de `distance` muestras, se queda con el más alto.
- **`sep_s`:** separación mínima entre eventos (0.3 s ≈ 9 fotogramas).
- **Escaneo de estabilidad:** contar eventos para varios `k`; si el conteo deja de cambiar es una **meseta** (el resultado no depende del umbral).
- **Falsos de control:** picos que aparecen al dar vuelta la señal; se toman como ruido. **Conteo reportable:** hay meseta con 0 falsos.
- **Promedio alineado:** promedio de los trozos de señal alrededor de cada evento, superpuestos en su pico; baja el ruido y deja ver la forma.
- **Bootstrap de bloques:** armar series nuevas pegando trozos al azar de una serie real; se usó como "serie sin eventos" para calibrar.


## Etapa 7 — términos nuevos

- **Estimulada vs espontánea:** estimulada = provocada por el estimulador eléctrico, que dispara cada `T` segundos como un reloj; espontánea = la célula se contrae sola, sin horario.
- **Enganche de fase:** los eventos caen siempre en los instantes `fase + n·T` del reloj (con un error chico).
- **Grilla / ranura:** la grilla son los instantes esperados del reloj; cada instante esperado es una ranura.
- **Captura:** porcentaje de ranuras que tienen un evento dentro de la tolerancia.
- **Tolerancia y jitter:** cuánto puede desviarse un evento de su ranura (aquí ±3 fotogramas ≈ 0.1 s) y cuánto se desvían de hecho.
- **Armónico:** una grilla de T/2 o T/3 que también contiene a los eventos reales pero con ranuras vacías; hay que evitar elegirla.
- **z-score:** cuántas "desviaciones" por encima de lo esperado por azar está el número de ranuras ocupadas.
- **Monte Carlo / p-valor:** repetir el mismo análisis en muchas series inventadas "sin reloj" y ver qué fracción de veces da un z tan alto; esa fracción es el p. Con 200 repeticiones el p mínimo es 1/201 ≈ 0.005.
- **Theil–Sen:** ajuste de recta robusto: la mediana de las pendientes entre todos los pares de puntos; unos pocos puntos malos no lo mueven.
- **Dudoso:** evento cercano a una ranura pero fuera de tolerancia: se informa aparte.

## Etapa 8 — términos nuevos

- **Amplitud (A):** cuánto se mueve el centro del gel en un evento (px), medida en el pico.
- **Onset / offset:** instante en que la señal sube / vuelve a bajar al 10 % de A (inicio y fin del evento).
- **TTP (time to peak):** tiempo de subida: del onset al pico.
- **RT50:** tiempo de relajación: del pico hasta que la señal cae al 50 % de A.
- **Amplitud relativa:** 100 · A / grosor en reposo; un porcentaje sin unidades para comparar videos (no es strain).
- **Intervalo [mín, máx]:** con muestreo de 33 ms, el cruce real está entre dos fotogramas; se informa el rango posible.
- **Medible:** el evento ocupa ≥ 5 fotogramas en ese tramo; si no, solo hay una cota superior.
- **Meseta del pico:** fotogramas a menos de 2 × ruido del máximo; si el pico es plano, "¿dónde está el pico?" es ambiguo.

## Etapa 9 — términos nuevos

- **Motor `ed` / motor del reporte:** dos programas distintos que detectan contracciones: `event_detection.py` (el original, que usa el cuaderno) y `contraction_report.py` (el que produce `contracciones.xlsx`).
- **Línea base por percentil 90 móvil:** el "estado relajado" se estima como el valor por debajo del cual está el 90 % de la señal en una ventana móvil; supone que el gel pasa casi todo el tiempo relajado.
- **Profundidad:** línea base menos señal; las contracciones aparecen como picos hacia arriba.
- **Prominencia:** cuánto sobresale un pico respecto de su entorno; se usa como umbral.
- **Agudeza:** cuánto pierde un evento al suavizarlo con una ventana ancha; un evento real pierde mucho (≈ 1.5), una deriva lenta casi nada (≈ 1).
- **Ancho de evento:** duración a media altura medida en los datos; de ahí salen todas las ventanas del motor.
- **Savitzky–Golay:** suavizado que ajusta un polinomio local; reduce ruido sin aplastar picos.
- **Autocorrelación:** comparar la señal consigo misma corrida en el tiempo; el corrimiento con mayor parecido es el período.
- **Tramo de ritmo (segmento):** grupo de eventos con frecuencia local parecida; no es lo mismo que "estimulado".
- **fps declarado vs fps de PTS:** el primero lo escribe el archivo (promedio); el segundo sale de los timestamps de cada fotograma (30.000).

## Etapa 10 — términos nuevos

- **Correlación cruzada:** deslizar un perfil sobre otro y ver con qué corrimiento se parecen más; el corrimiento con mayor parecido es el desplazamiento medido.
- **Traslación vertical / desplazamiento axial:** movimiento de todo el gel hacia arriba o abajo (vertical) o a lo largo de su eje (axial).
- **|I(t) − I(t−1)|:** cuánto cambió cada píxel entre dos fotogramas; es el proxy de movimiento que usan métodos como MuscleMotion.
- **Fondo de control:** una franja sin gel, para ver cuánto cambia la imagen sólo por ruido.
- **Skew (asimetría):** si la distribución tiene una cola larga hacia un lado; positivo = hacia valores altos, negativo = hacia bajos. Depende del signo con que se mida la señal.
- **Peine:** fila regular de picos chicos y parejos; aquí, cada 10 fotogramas en las diferencias entre fotogramas.
