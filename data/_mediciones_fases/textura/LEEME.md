# Medición por desplazamiento de textura (2026-10-16): implementada como opción

Para los videos de Andrés (por bordes dan 0 eventos). Decidido con Franco: `main.py --metodo textura` (también en la ventana, "Método de medición", y en `procesar_carpeta.py --metodo textura`). Escribe la misma `serie_temporal`: `center_px` es la posición de la franja medida por textura y el grosor es aproximado y constante (ancho de la franja a media altura de brillo). **El default sigue siendo bordes: los 11 de referencia no cambian** (tests, regresión y `--completo` iguales). Código: `src/textura.py`; test: `tests/test_textura.py`.

## Método (`src/textura.py`)
- Gel horizontal (misma rotación automática que `main.py`). La referencia es el promedio de los 30 primeros fotogramas, suavizado con σ = 1.5 px.
- Franja, sin bordes: perfil de brillo por filas en la mitad central de las columnas. Es el tramo seguido más largo que queda por encima de la mitad entre los percentiles 5 y 95, con un margen del 15 % del grosor.
- Corrimiento vertical: la parte entera sale de la correlación de fase y la fracción de mínimos cuadrados del gradiente (Lucas–Kanade 1-D, iterado: se corre el fotograma lo ya medido, con interpolación cúbica, y se vuelve a medir).
- Versiones descartadas (siguen en `textura_medir.py`):
  - `medir`, solo correlación de fase: tira los corrimientos chicos hacia el entero (0.25 px se mide como 0.04 px en 063).
  - `medir_lk`, sin iterar: sesgo de hasta 7 % en 0.5 px.
- Figura de control: `00_franja_textura_<video>.png` (la referencia con la zona usada y el perfil).

## 1. Sintético de corrimiento conocido (`sintetico.py`, `sintetico_final_salida.txt`)
Imagen real corrida en Fourier, con ruido σ 2 y compresión mp4. Cociente medido/real, método final:

| real (px) | 466 | 063 | 40V/1 (x0.5) | 063 sin compresión |
|---|---|---|---|---|
| 0.25 | 0.69 | 0.73 | 0.64 | 0.83 |
| 0.5 | 0.95 | 0.96 | 0.95 | 1.00 |
| 1 | 1.01 | 1.01 | 1.01 | 1.00 |
| 2 | 0.99 | 1.00 | 0.99 | 1.00 |
| 4 | 1.00 | 1.00 | 1.00 | 1.00 |
| −1 | 1.01 | 1.01 | 1.00 | 1.00 |

- Desde 0.5 px mide a ±5 %. Por debajo de ~0.5 px subestima; la compresión empeora el caso (`sintetico_sin_compresion.py`).
- El ruido es de 0.001–0.002 px, contra 0.007–0.015 de la correlación de fase sola.
- `tests/test_textura.py` hace lo mismo con una franja generada (gel vertical): pendiente medido/real por pulso, 0.98–1.02.

## 2. Contra `center_px` (bordes) en los 7 reportables (`validar.py <tmp> final`, `validacion_final.csv`)

| video | eventos bordes → textura | reportable | ruido px (b → t) | ampl. % (b → t) | textura/bordes por evento: mediana [mín–máx] |
|---|---|---|---|---|---|
| prueba | 29 → 29 | sí | 0.085 → 0.075 | 2.31 → 2.34 | 0.98 [0.90–1.05] |
| 063 | 6 → 6 | **no** (ventana 1.5 s sin meseta) | 0.024 → 0.007 | 0.56 → 0.49 | 0.88 [0.59–0.92] |
| 268 | 6 → 6 | **no** (ídem) | 0.049 → 0.011 | 0.57 → 0.49 | 0.89 [0.86–0.92] |
| 466 | 5 → 6 | **no** | 0.18 → 0.10 | 2.16 → 1.67 | 0.87 [0.79–0.93] |
| 583 | 6 → 39 | **no** | 0.072 → 0.014 | 1.31 → 1.16 | 0.97 [0.94–1.01] |
| 491 | 2 → 2 | sí | 0.068 → 0.040 | 0.40 → 0.38 | 0.97 [0.93–1.01] |
| 476 | 6 → 6 | sí | 0.115 → 0.057 | 0.64 → 0.56 | 0.91 [0.89–0.97] |

- **Eventos y tiempos:** en los 7, todos los eventos de bordes aparecen por textura en el mismo instante (±0.3 s), y el período del tren da 10.000 ± 0.002 s.
- **Ruido y verdicto:** la textura tiene 1.1 a 5 veces menos ruido y por eso ve más movimiento chico.
  - 583: ve la vibración conocida y queda NO REPORTABLE.
  - 466: un evento se parte en dos (34.18 y 34.31 s).
  - 063 y 268: con la ventana de 1.5 s ya no hay meseta, así que el conteo deja de ser estable y no es reportable. Con la primera versión (`medir_lk`, `validacion.csv`) sí eran reportables.
  - **Pendiente (Franco): estudiar 583/466 (y 063/268).**
- **Amplitud:** la textura da 0.87–0.98 de lo que miden los bordes. En 268 y 466 la diferencia es la misma que vio la intensidad en D1 (0.86–0.88), y el sintético indica que la textura mide bien el corrimiento. El grosor por textura sale además 3–10 % mayor, así que el % baja un poco más.

## 3. Andrés 40V/1, copia x0.5 (`main.py --metodo textura` + reporte a 0.1 Hz)
- **Señal:** ruido 0.018 px; 5 contracciones nítidas a 16.8, 26.9, 37.0, 47.1 y 57.2 s, de ~0.84 px (≈1.7 px en 4K, ~0.09 % de un grosor de 982 px). Tren a 0.1 Hz enganchado: 5/5, p = 0.001 (figura `09_contracciones_40V1_textura.png`, de la primera versión; da igual).
- **Por qué NO REPORTABLE:** el primer segundo del video es ruidoso y con la ventana de 1.5 s aparece un 6.º candidato.
- **Período:** da 10.10 s (−1 %), pero es de la copia, que tiene los timestamps inventados; no es del equipo.

## 4. Velocidad (2026-10-17)
- **Problema:** en la notebook, un video 4K tardaba más de 1 h con textura, porque se procesaba cada fotograma a 3840×2160.
- **Cambio:**
  - Si el lado mayor pasa de 1920 px, los fotogramas se achican a la mitad (INTER_AREA, igual que `scripts/achicar_video.py`). Todo se informa en píxeles del video original (× 1/escala).
  - Además, solo se suaviza la franja y no la imagen entera: da lo mismo (diferencia < 5e-5 px en 063 y en la copia de 40V/1) y ~10 % más rápido.
- **Validación:**
  - A media resolución ya estaba medido: es exactamente la copia x0.5 de 40V/1 (ruido 0.018 px, las 5 contracciones).
  - `tests/test_textura.py` tiene un sintético "grande" (960 px) medido achicado: pendiente medido/real 1.01 y grosor correcto.
- **Límite visto:** con una franja de menos de ~100 filas en la imagen medida (sintético de 180×240), la correlación de fase pierde el entero y la serie se va (también sin achicar). No pasa en ningún video real (la franja más chica es 466: 287 filas).
- **Control pendiente (Franco, una noche):** medir 1 o 2 videos con `main.py --metodo textura --resolucion-completa` y compararlos con la corrida normal (achicada) usando `comparar_resolucion.py` (los comandos están en su encabezado). Sirve para confirmar con un video real que achicar no cambia los resultados.

## 5. Carpeta de Andrés, 4K con `--metodo textura` (2026-10-17, corrida en la notebook, achicado x0.5)

| video | eventos | reportable | período (s) | ampl. % | ampl. px | lo que se ve en la figura 09 |
|---|---|---|---|---|---|---|
| 10V_1 | 6 | sí | 10.098 | 0.06 | 1.16 | tren limpio |
| 10V_2 | 0 | no | — | — | — | picos de ~0.4 px cada 10 s (10.5, 20.6, 30.7, 40.8, 50.8, 61 s), apenas sobre el ruido (0.08 px) |
| 10V_3 | 8 | no | 10.100 | 0.26 | 5.88 | 6 respuestas grandes (~5.7 px) cada 10 s + una sacudida hacia los dos lados en 15.4–15.8 s (2 falsos de control) |
| 20V_1 | 0 | no | — | — | — | respuestas de ~2 px cada 10 s (12, 22 … 62 s), pero ruido alto (0.33 px) y bifásicas (suben y bajan) |
| 20V_2 | 0 | no | — | — | — | (sin revisar) |
| 20V_3 | 6 | sí | 10.099 | 0.08 | 1.64 | tren limpio; vibración al final (63–65 s) |
| 40V_1 | 5 | sí | 10.102 | 0.08 | 1.67 | tren limpio (en 4K sí reportable; la copia x0.5 no, por el primer segundo) |
| 40V_2 | 1 | no | — | 0.04 | 0.81 | picos de 0.5–0.8 px cada 10 s (24, 34, 44, 54, 64 s); solo uno pasa el umbral |
| 40V_3 | 6 | sí | 10.098 | 0.03 | 0.76 | tren |

- **Respuesta al estímulo en casi todos.** 4 de 9 son reportables. A ojo, en la figura hay respuesta cada 10 s también en 10V_2, 10V_3, 20V_1 y 40V_2. Lo que los deja afuera es el ruido o una sacudida, no que falten las respuestas.
- **Período 10.10 s en todos (−1 %).** Los timestamps de estos archivos son inventados (100 % de intervalos iguales). O la cámara graba a ~29.7 fps aunque declare 30, o el estimulador está a 0.099 Hz: **preguntar a Andrés**.
- **Siguiente paso posible:** para los que tienen respuesta débil o ruidosa, la "respuesta forzada" (medir en cada instante esperado de pulso, contra controles) que ya estaba anotada como idea en `pendientes.md`.
