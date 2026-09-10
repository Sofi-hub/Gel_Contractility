"""
Pipeline de análisis de contractilidad de geles 3D.

Módulos:
    io_utils        -> lectura de video / frames
    preprocessing   -> normalización de iluminación, utilidades de imagen
    edge_detection  -> detección de bordes con precisión subpíxel
    robust_fitting  -> ajuste robusto (RANSAC) resistente a outliers/burbujas
    pipeline        -> orquestador: frame -> grosor(t)
"""
