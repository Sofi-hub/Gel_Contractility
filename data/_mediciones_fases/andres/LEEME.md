# Videos de Andrés (2026-10-15/16) — situación

**Dónde:** `data/raw_videos/Videos_Andres/{10V,20V,40V}/{1,2,3}.mp4` (9 videos, ~520 MB c/u, 4K 3840×2160, 30 fps, ~65 s, sin timestamps reales: 100 % intervalos idénticos). Gel **vertical**, más zoom, sin anclajes, borde = rampa granulada (banda azulada) entre fondo y gel. Estimulación: voltaje en el nombre de la carpeta → 0.1 Hz (regla del equipo).

**Hecho:**
- Rotación automática (`main.py --rotar auto`): 40V/1 se giró solo (cociente 0.054). Ver `../orientacion/LEEME.md`.
- Nombre de la carpeta de resultados con la subcarpeta (`40V_1`), porque los videos se llaman 1, 2, 3 (`interfaz.nombre_resultado`).
- `scripts/achicar_video.py`: copia a menor resolución, gris, primeros 70 s (para traerla a Claude: límite 400 MB por archivo). Copia hecha: `data/raw_videos/_copias_chicas/40V_1_x0.5.mp4` (24 MB, 1920×1080).
- Arreglado: con un punto en el nombre (`_x0.5`) la serie se guardaba como `..._x0.xlsx` y el paso 2 fallaba (`qc_visualization.save_diagnostics` usaba `with_suffix`). El script ahora nombra `_x50`.

**Resultado con el método actual (bordes): NO sirve en estos videos.**
- 40V/1 en 4K: nitidez del borde 2.5 (validados 18–51), ruido de `center_px` 2.5 px (validados 0.03–0.18), 0 eventos, NO REPORTABLE; ROI "franja_completa" con 15.8 % de variación; bordes pegados al límite de la ventana (±30) en el 90 %.
- A media resolución (copia x0.5): nitidez 5, mismos problemas. Achicar no alcanza.
- Franco: "a ojo no parecen haber contracciones".

**Medición por textura (sin bordes), `movimiento_textura.py`:** correlación de fase de cada fotograma contra el promedio de los 30 primeros, sobre la franja del gel (con 60 px de margen), y la señal plegada a 10 s contra 6 períodos de control (`src/forzado_util.py`).
- 40V/1 (copia x0.5): desplazamiento perpendicular al gel con ruido 0.028 px y máximo 0.93 px (≈1.9 px en 4K); **plegado a 10 s SNR 22.7 contra 6.3–14.3 en los controles** → hay respuesta periódica al estímulo, chica. A lo largo del gel: SNR 5.8 (controles 4.8–8.2), nada.
- En 466 (gel horizontal, franja = toda la imagen) el script se desarma (corrimientos de miles de px): la elección de la franja por brillo no sirve ahí; el script está pensado solo para estos videos.

**Próximo paso propuesto (no empezado):** medir la contracción en estos videos por **desplazamiento de la textura** (correlación de fase por fotograma, en la franja del gel, perpendicular al gel) en vez de por bordes; validar primero con un video sintético de desplazamiento conocido y con los 11 videos de referencia (comparar contra `center_px`, como `motion_check`). Ojo con la regla del proyecto "geometría, no intensidad": esto mide geometría (desplazamiento), no brillo. Decidir con Franco antes de implementar. Probar con copias chicas (`achicar_video.py`), no con los originales (memoria: no cargar el video entero).
