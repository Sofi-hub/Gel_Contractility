"""Prueba (sin tocar el programa): suavizar cada fotograma A LO LARGO del borde
(eje x, ya girado) con una gaussiana de sigma S px antes de buscar bordes.
    python probar_suavizado.py video.mp4 salida S
"""
import runpy, sys
import cv2
sys.path.insert(0, ".")
from src import io_utils
S = float(sys.argv[3])
_rot = io_utils.rotar
def rotar_y_suavizar(img, r):
    out = _rot(img, r)
    return cv2.GaussianBlur(out, (0, 0), sigmaX=S, sigmaY=0.5) if S > 0 else out
io_utils.rotar = rotar_y_suavizar
sys.argv = ["main.py", "--video", sys.argv[1], "--output-dir", sys.argv[2]]
runpy.run_path("main.py", run_name="__main__")
