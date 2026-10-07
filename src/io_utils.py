"""
io_utils.py
-----------
Utilidades de entrada/salida: lectura de video frame a frame y
guardado de resultados. Mantenemos esto separado del resto para que
el pipeline no dependa de cómo llegan los frames (video, carpeta de
TIFFs, stack de ImageJ, etc.) — si mañana cambiás la fuente de datos,
solo tocás este archivo.
"""

from __future__ import annotations
from pathlib import Path
from typing import Generator, Optional
import cv2
import numpy as np


def frame_generator(
    video_path: str | Path,
    start_frame: int = 0,
    end_frame: Optional[int] = None,
) -> Generator[tuple[int, np.ndarray], None, None]:
    """
    Generador perezoso de frames en escala de grises.

    Usamos un generador (yield) en vez de cargar todo el video en RAM:
    para videos largos de microscopía esto es la diferencia entre
    correr el pipeline o quedarte sin memoria.

    Yields
    ------
    (frame_index, frame_gray) : tupla con el índice del frame (int)
        y la imagen en escala de grises (np.ndarray, dtype=uint8).
    """
    video_path = str(video_path)
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise IOError(f"No se pudo abrir el video: {video_path}")

    cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
    idx = start_frame

    try:
        while True:
            if end_frame is not None and idx >= end_frame:
                break
            ret, frame = cap.read()
            if not ret:
                break
            if frame.ndim == 3:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            yield idx, frame
            idx += 1
    finally:
        cap.release()


def read_pts_seconds(video_path: str | Path) -> np.ndarray:
    """Timestamp de presentacion de cada frame, en segundos.

    POR QUE HACE FALTA: `time = frame / fps` supone que no falta ningun
    frame. Si la grabacion perdio frames, ese eje se come el hueco y los
    eventos parecen MAS JUNTOS de lo que fueron. Paso en Video_466: su
    periodo de estimulacion medido por indice de frame daba 9.508 s (un
    +5.15% de error contra los 0.1 Hz configurados), y medido sobre los
    timestamps del contenedor da 10.008 s, indistinguible de lo configurado.
    Le faltaba ~4.8% de los frames.

    OJO con el desfasaje: `CAP_PROP_POS_MSEC` leido ANTES de `read()`
    devuelve el timestamp del frame ANTERIOR. Hay que leerlo despues.
    Verificado contra `ffprobe -show_entries packet=pts_time` (ordenado,
    porque los packets vienen en orden de decodificacion y con B-frames no
    son monotonos): coincide exacto, 0.000 ms de diferencia.
    """
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise IOError(f"No se pudo abrir el video: {video_path}")
    out = []
    try:
        while True:
            ret, _ = cap.read()
            if not ret:
                break
            out.append(cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0)
    finally:
        cap.release()
    return np.asarray(out, dtype=float)


def get_video_metadata(video_path: str | Path) -> dict:
    """Devuelve fps, cantidad de frames y resolución. Útil para el eje
    temporal de los gráficos finales (segundos en vez de # de frame)."""
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise IOError(f"No se pudo abrir el video: {video_path}")
    meta = {
        "fps": cap.get(cv2.CAP_PROP_FPS),
        "n_frames": int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
        "width": int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
        "height": int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
    }
    cap.release()
    return meta


def compute_max_projection(
    video_path: str | Path,
    stride: int = 1,
    max_frames: Optional[int] = None,
) -> np.ndarray:
    """
    Calcula el maxProjectStack directamente desde el video, sin pasar
    por ImageJ: para cada píxel, se queda con el valor máximo de
    intensidad observado a lo largo de todos los frames procesados.
    Es exactamente lo que hace ImageJ con "Z Project > Max Intensity",
    solo que acá lo hacemos frame a frame con np.maximum, sin cargar
    el video completo en memoria de una sola vez.

    Parameters
    ----------
    stride : procesa 1 de cada `stride` frames. Para el propósito de
             esto (ubicar dónde hubo movimiento en algún momento del
             video), no hace falta usar TODOS los frames — con
             stride=5 en un video largo ya alcanza y es mucho más
             rápido. Usá stride=1 si el video es corto.
    max_frames : límite opcional de frames a procesar (por si el
             video es muy largo y con los primeros N ya alcanza para
             capturar el rango de movimiento).

    Returns
    -------
    Imagen 2D (uint8) con el mismo alto/ancho que los frames del
    video, lista para pasarle a preprocessing.auto_detect_roi.
    """
    max_proj = None
    n_used = 0

    for idx, frame in frame_generator(video_path):
        if idx % stride != 0:
            continue
        if max_proj is None:
            max_proj = frame.copy()
        else:
            max_proj = np.maximum(max_proj, frame)
        n_used += 1
        if max_frames is not None and n_used >= max_frames:
            break

    if max_proj is None:
        raise IOError(f"No se pudo leer ningún frame de: {video_path}")

    return max_proj


def load_max_projection(image_path: str | Path) -> np.ndarray:
    """
    Carga la imagen maxProjectStack (proyección de máxima intensidad
    en el tiempo). La usamos en el pipeline para AUTO-DETECTAR la ROI
    y la posición aproximada de los bordes superior/inferior, en vez
    de hardcodearlas a mano para cada video.
    """
    # cv2.imread no abre rutas con caracteres no ASCII en Windows ("Análisis"):
    # devuelve None sin explicar por que. Se leen los bytes con numpy y se
    # decodifican en memoria, que funciona con cualquier ruta.
    try:
        datos = np.fromfile(str(image_path), dtype=np.uint8)
    except OSError:
        datos = np.array([], dtype=np.uint8)
    img = cv2.imdecode(datos, cv2.IMREAD_GRAYSCALE) if datos.size else None
    if img is None:
        raise IOError(f"No se pudo leer la imagen: {image_path}")
    return img
