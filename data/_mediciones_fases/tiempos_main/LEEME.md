# Tiempos de cada parte de main.py (pendientes B3a)

Para saber qué conviene acelerar en la notebook de Franco (4 núcleos): leer el video, elegir la zona o
procesar los fotogramas. Ya se sabe que ahí el paralelo casi no gana (Video_prueba, solo `main.py`:
1 proceso 108 s, 2 → 102 s, 4 → 102 s); falta ver cuánto es lectura y cuánto cálculo.

Cómo correrlo (desde la carpeta del proyecto, con el `.venv` activado; no guarda nada):

    python data/_mediciones_fases/tiempos_main/medir_tiempos.py --video "data/raw_videos/<...>/Video_prueba.mp4"

Imprime cada parte a medida que la mide y al final un bloque "PEGAR ESTO EN EL CHAT".

Cómo se lee:
- `1.ª lectura` y `2.ª lectura SOLA` = lo que cuesta leer el video (en serie; no se paraleliza).
- `2.ª lectura + bordes/RANSAC (N proc.)` = lo que hace `main.py` con `--procesos N`. Si es casi igual a
  la `2.ª lectura SOLA`, el cuello es leer el video y no sirve agregar procesos.
- `bordes/RANSAC sin leer` = el cálculo puro en un núcleo.

Probado (2026-10-11) solo con un video sintético en la máquina de prueba, para ver que corre; los
números de verdad son los de la notebook.

## Resultados
(pendiente: la salida de la notebook)
