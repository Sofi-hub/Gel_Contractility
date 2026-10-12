# Tiempos de cada parte de main.py (pendientes B3a)

Para saber qué conviene acelerar en la notebook de Franco (4 núcleos): leer el video, elegir la zona o
procesar los fotogramas. Ya se sabe que ahí el paralelo casi no gana (Video_prueba, solo `main.py`:
1 proceso 108 s, 2 → 102 s, 4 → 102 s); falta ver cuánto es lectura y cuánto cálculo.

Cómo correrlo (desde la carpeta del proyecto, con el `.venv` activado; no guarda nada):

    python data/_mediciones_fases/tiempos_main/medir_tiempos.py

(busca solo `Video_prueba.mp4` en `data/raw_videos`; para otro video, `--video "ruta"`)

Imprime cada parte a medida que la mide y al final un bloque "PEGAR ESTO EN EL CHAT".

Cómo se lee:
- `1.ª lectura` y `2.ª lectura SOLA` = lo que cuesta leer el video (en serie; no se paraleliza).
- `2.ª lectura + bordes/RANSAC (N proc.)` = lo que hace `main.py` con `--procesos N`. Si es casi igual a
  la `2.ª lectura SOLA`, el cuello es leer el video y no sirve agregar procesos.
- `bordes/RANSAC sin leer` = el cálculo puro en un núcleo.

Probado (2026-10-11) solo con un video sintético en la máquina de prueba, para ver que corre; los
números de verdad son los de la notebook.

## Resultados

**Notebook de Franco (Windows 11, 8 núcleos, Video_prueba, 2007 fotogramas 1920×1080), código de antes:**

| parte | s |
|---|---|
| cargar librerías | 4.3 |
| 1.ª lectura (timestamps + mapa de máximos) | 21.0 |
| 2.ª lectura sola | 22.3 |
| 2.ª lectura + bordes/RANSAC, 1 proceso | 62.4 |
| 2.ª lectura + bordes/RANSAC, 2 procesos | 62.2 |
| bordes/RANSAC sin leer (estimado) | 61.5 (sobreestimado: 1 proc. da 62.4 con la lectura incluida) |

Lectura: leer el video dos veces cuesta ~43 s; el cálculo, ~40 s; y el paralelo no ganaba
**nada** porque cada fotograma (2 MB) viajaba copiado entre procesos.

**Cambios (2026-10-11), todos sin cambiar ningún número** (Video_prueba y 466 bit a bit
iguales al código viejo con 1 y 2 procesos; tests, regresión y `--completo` iguales):
1. Paralelo con **memoria compartida**: los fotogramas ya no viajan por la tubería.
2. 1.ª lectura: los fotogramas que no van al mapa de máximos solo se "agarran" (`grab`).
3. Bordes: solo las columnas medidas pasan a decimal (antes, la imagen entera); sin la copia
   previa al CLAHE.

**Máquina de prueba (2 núcleos), Video_prueba:**

| parte | antes | después |
|---|---|---|
| 1.ª lectura | 13.0 | 9.2 |
| 2.ª lectura + cálculo, 1 proceso | 38.8 | 33.9 |
| 2.ª lectura + cálculo, 2 procesos | 40.2 | 30.3 |

**Notebook de Franco, después (2026-10-11):**

| parte | antes | después |
|---|---|---|
| cargar librerías | 4.3 | 3.2 |
| 1.ª lectura | 21.0 | **5.6** |
| 2.ª lectura sola | 22.3 | 21.9 |
| fotogramas, 1 proceso | 62.4 | 55.2 |
| fotogramas, 2 procesos | 62.2 | **40.2** |
| fotogramas, 4 procesos | — | 44.6 |

`main.py` completo pasa de ~90 s a ~50 s. El default `--procesos 2` queda (4 es peor: los
procesos compiten con la lectura del video, que usa varios núcleos). Lo que queda: leer el
video en la 2.ª pasada (~22 s, en serie) y el CLAHE.
Lo que queda, sin tocar números, es la lectura del video (2 pasadas) y el CLAHE (~35 % del
cálculo; recortarlo cambia números, medido y descartado el 2026-10-08).
