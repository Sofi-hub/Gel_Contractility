# Tiempos de cada parte de contraction_report.py (2026-10-10)

`python data/_mediciones_fases/tiempos_reporte/medir_partes.py [carpeta] [procesos...]` (por defecto Video_613 con
1, 2 y 4 procesos). Escribe en una carpeta temporal; no toca `processed_data`.

**Resultado** (máquina de prueba, `salida_maquina_de_prueba.txt`): casi todo es el Monte Carlo de la prueba del
tren (14.0 s de 15.6 s con 1 proceso; 9.1 de 10.6 s con 2; 11.2 de 12.5 s con 4). Por eso se paralelizó (después,
con hilos) y el default quedó en 2. En la notebook: `docs/historia/pendientes-hasta-2026-10-26.md`, B3.
