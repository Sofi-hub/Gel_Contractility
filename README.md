# Pipeline de contractilidad de geles 3D — bordes subpíxel + RANSAC

## Instalación
```bash
pip install -r requirements.txt
```

## Uso
```bash
python main.py \
    --video mi_video.avi \
    --maxproj maxProjectStack.png \
    --px-to-mm 0.0021 \
    --output resultados.csv \
    --plot
```

`--px-to-mm` es OBLIGATORIO calibrarlo con tu propio setup óptico
(regla/retícula en el mismo aumento que usás para grabar). Sin esto
el pipeline reporta grosor en píxeles, no en mm.

## Qué hace cada módulo (ver también los docstrings/comentarios en el código)
- `src/io_utils.py` — lee el video frame a frame (generador, no carga todo en RAM) y el maxProjectStack.
- `src/preprocessing.py` — CLAHE (normalización de contraste local) y auto-detección de ROI/posición aproximada de bordes a partir del maxProjectStack.
- `src/edge_detection.py` — localización subpíxel del borde por columna (interpolación parabólica del gradiente, o sigmoide como alternativa).
- `src/robust_fitting.py` — RANSAC (o mediana+MAD) para descartar columnas corrompidas por burbujas u otros artefactos.
- `src/pipeline.py` — orquesta todo lo anterior y arma la serie temporal de grosor con métricas de calidad por frame.
- `main.py` — CLI.

## Cosas para ajustar con tus datos reales (no van a andar "perfectas" de entrada)
1. **`half_window` en `PipelineConfig`**: tiene que cubrir el rango máximo de deformación esperado en Y. Si tus macro-contracciones son grandes, subilo.
2. **`ransac_residual_threshold`**: empezá en 1.5 px y ajustá mirando cuántas columnas se descartan en frames que SABÉS que están limpios (no debería descartar casi nada ahí).
3. **`min_gradient` en `subpixel_edge_parabolic`**: depende del contraste real de tus videos (no del maxProjectStack). Medilo empíricamente en un par de frames representativos.
4. **Validación cruzada sugerida**: antes de confiar en el pipeline para todo el dataset, corré `edge_method="sigmoid"` en una submuestra de frames y compará contra `"parabolic"` — si divergen mucho, el ruido de tus videos amerita usar sigmoide como método principal (más lento pero más robusto).
5. **DIC como validación**: como discutimos, correr DIC (ej. `py2DIC`/`OpenPIV`) sobre una submuestra de videos para confirmar que el grosor por bordes correlaciona con el campo de deformación completo — buen respaldo metodológico para publicación.

## Qué falta para producción
- Loop batch sobre una carpeta con muchos videos (fácil de agregar sobre `process_video`).
- Export de un frame con los bordes ajustados dibujados encima (control de calidad visual) — útil para auditar rápidamente si el auto-ROI se calculó bien.
- Manejo de casos "REJECTED" (frame completamente degradado): decidir si interpolar, marcar como missing, o excluir el experimento.
