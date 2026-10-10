# B1: ventana de búsqueda del borde (2026-10-10)

Mide tres maneras de ubicar la ventana de búsqueda del borde en los 11 videos de
`tests/referencia.py`, contra la referencia congelada. Resultado y decisión (a'):
`docs/pendientes.md`, B1.

- `medir.py <carpeta> <max15|max30|med15> <salida>`: corre `pipeline.process_video`
  con la guía del mapa de máximos (±15 o ±30) o de la mediana del video (±15), y
  guarda la serie y, por fotograma, las columnas sin borde (`nan_top/bot`), los
  bordes pegados al límite (`cerca`) y la distancia del borde a la guía (`.pkl`).
  ~1 min por corrida en un núcleo; las 33 corridas, ~35 min con 2 a la vez.
- `analizar.py`: lee `res/*.pkl` (no se guardan en git: pesan) y arma `tabla.csv`.
  Comprueba primero que la configuración de referencia reproduce el hash congelado.
- `tabla.csv`: la tabla de la medición. Columnas: eventos, k, amplitud %, período,
  TTP/RT50 (referencia -> opción), fotogramas que cambian, outliers de RANSAC
  medios en esos fotogramas, cuántos mejoran/empeoran, columnas sin borde, bordes
  en el límite y ruido fuera de los eventos.
