"""
edge_detection.py
------------------
Núcleo matemático del pipeline: localización subpíxel del borde
superior e inferior del gel, columna por columna.

Dos métodos disponibles:
    1. subpixel_edge_parabolic  -> rápido, interpolación parabólica
                                    del gradiente (~microsegundos/columna)
    2. subpixel_edge_sigmoid    -> más lento, ajuste no-lineal, más
                                    robusto si el borde es muy ruidoso
                                    o la rampa es muy ancha/asimétrica

Por defecto usamos el método 1 para todo el pipeline y podés activar
el 2 puntualmente para validar.
"""

from __future__ import annotations
from dataclasses import dataclass
import numpy as np
from scipy.optimize import curve_fit


@dataclass
class EdgePoint:
    """Resultado de localizar un borde en UNA columna."""
    y: float          # posición subpíxel del borde (en píxeles, eje y)
    quality: float     # magnitud del gradiente en el pico -> "qué tan
                       # confiable/nítido" fue este borde. Se usa luego
                       # para descartar columnas ambiguas (ej. burbuja
                       # tapando el borde por completo).
    valid: bool        # False si no se pudo localizar un borde confiable


# ---------------------------------------------------------------------
# Método 1: interpolación parabólica del pico de gradiente
# ---------------------------------------------------------------------

def subpixel_edge_parabolic(
    profile: np.ndarray,
    search_start: int,
    search_end: int,
    polarity: int = 1,
    min_gradient: float = 5.0,
) -> EdgePoint:
    """
    Localiza el borde dentro de profile[search_start:search_end]
    usando interpolación parabólica del gradiente.

    Parameters
    ----------
    profile : perfil de intensidad 1D a lo largo de una columna
               (de arriba hacia abajo), ya como float.
    search_start, search_end : ventana donde buscar el borde. Usamos
               una ventana acotada (en vez de toda la imagen) porque
               así (a) es más rápido y (b) evitamos "engancharnos" con
               otro borde o artefacto lejos de donde esperamos el
               borde real (dato que viene de auto_detect_roi).
    polarity : +1 si el borde pasa de oscuro a claro bajando en y
               (borde superior del gel, fondo negro arriba, gel claro
               abajo), -1 si es al revés (borde inferior).
    min_gradient : gradiente mínimo para considerar el borde "válido".
               Si el máximo gradiente en la ventana es menor a esto,
               asumimos que el borde está oculto/degradado (burbuja,
               desenfoque, etc.) y marcamos el punto como no válido.

    Returns
    -------
    EdgePoint con la posición subpíxel, calidad y validez.
    """
    window = profile[search_start:search_end]
    if window.size < 3:
        return EdgePoint(y=np.nan, quality=0.0, valid=False)

    # Gradiente central: g[i] ~ (I[i+1] - I[i-1]) / 2
    grad = np.gradient(window) * polarity

    idx_max = int(np.argmax(grad))
    peak_val = grad[idx_max]

    # Si el pico está pegado al borde de la ventana no podemos
    # interpolar con sus 2 vecinos -> descartamos el punto.
    if idx_max == 0 or idx_max == len(grad) - 1:
        return EdgePoint(y=np.nan, quality=float(peak_val), valid=False)

    if peak_val < min_gradient:
        return EdgePoint(y=np.nan, quality=float(peak_val), valid=False)

    # --- Interpolación parabólica (el corazón matemático) ---
    # Ajustamos una parábola a 3 puntos (g[-1], g[0], g[1]) alrededor
    # del máximo entero y calculamos el vértice de esa parábola.
    # Fórmula estándar de "peak fitting" de 3 puntos:
    #
    #   delta = 0.5 * (g_minus1 - g_plus1) / (g_minus1 - 2*g0 + g_plus1)
    #
    # delta está en el rango (-0.5, 0.5) y representa el corrimiento
    # subpíxel respecto del índice entero idx_max.
    g_minus1 = grad[idx_max - 1]
    g0 = grad[idx_max]
    g_plus1 = grad[idx_max + 1]

    denom = (g_minus1 - 2 * g0 + g_plus1)
    if abs(denom) < 1e-9:
        delta = 0.0
    else:
        delta = 0.5 * (g_minus1 - g_plus1) / denom
        # Salvaguarda: si la parábola sale rara (denom casi 0, curva
        # casi plana) delta puede explotar. Lo acotamos a [-1, 1] ya
        # que un corrimiento subpíxel mayor a 1 píxel no tiene sentido
        # físico (ahí el máximo entero ya estaría mal ubicado).
        delta = float(np.clip(delta, -1.0, 1.0))

    y_subpixel = search_start + idx_max + delta

    return EdgePoint(y=y_subpixel, quality=float(peak_val), valid=True)


# ---------------------------------------------------------------------
# Método 2: ajuste de sigmoide (más robusto a ruido, más lento)
# ---------------------------------------------------------------------

def _sigmoid(y, a, b, y0, s):
    """I(y) = a + b / (1 + exp(-(y - y0) / s))
    a: nivel de fondo, b: amplitud del salto, y0: centro (= borde),
    s: "suavidad" de la rampa (relacionado al desenfoque óptico)."""
    return a + b / (1 + np.exp(-(y - y0) / s))


def subpixel_edge_sigmoid(
    profile: np.ndarray,
    search_start: int,
    search_end: int,
    polarity: int = 1,
) -> EdgePoint:
    """
    Alternativa más robusta: ajusta una sigmoide a TODO el perfil de
    la ventana (no solo 3 puntos), y el punto de inflexión (y0) es la
    posición subpíxel del borde. Más costoso (usa optimización
    no-lineal iterativa) pero menos sensible al ruido punto-a-punto
    porque usa toda la información de la rampa.

    Usalo para validar el método parabólico en una submuestra, o si
    el video tiene mucho ruido de cámara.
    """
    window = profile[search_start:search_end].astype(np.float64)
    y_axis = np.arange(len(window), dtype=np.float64)

    if polarity < 0:
        window = window[::-1]  # normalizamos siempre a "rampa ascendente"

    a0 = float(np.min(window))
    b0 = float(np.max(window) - np.min(window))
    y0_0 = float(len(window) / 2)
    s0 = 1.5

    try:
        popt, _ = curve_fit(
            _sigmoid, y_axis, window,
            p0=[a0, b0, y0_0, s0],
            maxfev=2000,
        )
        _, _, y0, s = popt
        quality = abs(b0) / (abs(s) + 1e-6)  # salto grande + rampa angosta = alta calidad
    except RuntimeError:
        return EdgePoint(y=np.nan, quality=0.0, valid=False)

    if polarity < 0:
        y0 = (len(window) - 1) - y0  # deshacer el flip

    y_subpixel = search_start + y0
    valid = 0 <= y0 <= len(window)
    return EdgePoint(y=float(y_subpixel), quality=float(quality), valid=bool(valid))


# ---------------------------------------------------------------------
# Extracción de bordes en TODAS las columnas de un frame
# ---------------------------------------------------------------------

def extract_edges_for_frame(
    frame: np.ndarray,
    x_positions: np.ndarray,
    top_guess: np.ndarray,
    bottom_guess: np.ndarray,
    half_window: int = 15,
    method: str = "parabolic",
    min_gradient: float = 5.0,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Recorre las columnas indicadas y localiza el borde superior e
    inferior en cada una.

    top_guess / bottom_guess vienen de auto_detect_roi (posición
    aproximada por columna, calculada sobre el maxProjectStack).
    half_window define cuánto margen alrededor de esa posición
    aproximada buscamos el borde real en ESTE frame — tiene que ser
    lo bastante grande para cubrir el rango de deformación esperado,
    pero lo bastante chico para no "engancharse" con otra estructura.

    Returns
    -------
    x_positions, y_top, y_bottom, quality
        arrays alineados por índice; y_top/y_bottom tienen NaN en las
        columnas donde no se pudo localizar el borde con confianza
        (posible burbuja / artefacto).
    """
    frame_f = frame.astype(np.float64)
    h = frame.shape[0]

    edge_fn = subpixel_edge_parabolic if method == "parabolic" else subpixel_edge_sigmoid

    y_top = np.full(len(x_positions), np.nan)
    y_bottom = np.full(len(x_positions), np.nan)
    quality = np.full(len(x_positions), 0.0)

    for i, x in enumerate(x_positions):
        col_profile = frame_f[:, x]

        t_guess = top_guess[x]
        b_guess = bottom_guess[x]

        top_start = max(0, int(t_guess - half_window))
        top_end = min(h, int(t_guess + half_window))
        bot_start = max(0, int(b_guess - half_window))
        bot_end = min(h, int(b_guess + half_window))

        # Borde superior: fondo oscuro -> gel claro (polarity +1)
        # Borde inferior: gel claro -> fondo oscuro (polarity -1)
        if method == "parabolic":
            top_pt = edge_fn(col_profile, top_start, top_end, polarity=1, min_gradient=min_gradient)
            bot_pt = edge_fn(col_profile, bot_start, bot_end, polarity=-1, min_gradient=min_gradient)
        else:
            top_pt = edge_fn(col_profile, top_start, top_end, polarity=1)
            bot_pt = edge_fn(col_profile, bot_start, bot_end, polarity=-1)

        if top_pt.valid:
            y_top[i] = top_pt.y
        if bot_pt.valid:
            y_bottom[i] = bot_pt.y
        quality[i] = min(top_pt.quality, bot_pt.quality)

    return x_positions, y_top, y_bottom, quality
