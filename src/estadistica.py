"""
estadistica.py
--------------
Las tres operaciones estadisticas que usa todo el proyecto, en UN solo lugar
y tolerantes a fotogramas sin medida (NaN).

POR QUE EXISTE (hallazgos H1, H31, H47 y H53 de la revision de codigo)
----------------------------------------------------------------------
El pipeline deja en NaN los fotogramas `REJECTED`: no inventa una medida
donde no la hubo. Pero la MAD estaba copiada en nueve lugares y la mediana
movil en tres, y ninguna copia toleraba NaN: `np.median` de un vector con un
solo NaN da NaN. Resultado medido: con UN fotograma NaN, Video_prueba pasaba
de 28 eventos a 0, y el reporte decia "no hay meseta", como si el video no
tuviera contracciones.

La regla "no inventar datos" se respeta: aca no se interpola nada. Un
fotograma sin medida simplemente no cuenta: no entra en la mediana, no
puede ser un pico, y no impide que su vecino lo sea.

EQUIVALENCIA CON EL CODIGO ANTERIOR
-----------------------------------
Sin NaN, las tres funciones dan EXACTAMENTE (bit a bit) lo mismo que las
copias que reemplazan: `np.nanmedian` y `np.median` coinciden en vectores
sin NaN (verificado sobre 137 vectores, incluidas las 24 series de los seis
videos vigentes), la mediana movil de pandas ya ignoraba NaN, y
`buscar_picos` solo reemplaza los NaN. Por eso los resultados vigentes no
cambian. Los parametros (ventana `int(win_s*fps) | 1`, etc.) se conservan
tal cual; revisarlos es otro tema (H8, H33, H34).
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.signal import find_peaks

# Factor que convierte la MAD en una estimacion del desvio estandar si el
# ruido es gaussiano (1 / Phi^-1(3/4)).
MAD_A_SIGMA = 1.4826


def mad(v) -> float:
    """Desvio robusto: 1.4826 * mediana(|v - mediana(v)|), ignorando NaN.

    Devuelve NaN solo si no hay ningun valor finito.
    """
    v = np.asarray(v, dtype=float)
    v = v[~np.isnan(v)]
    if v.size == 0:
        return float("nan")
    return float(np.median(np.abs(v - np.median(v))) * MAD_A_SIGMA)


def detrend_median(v, fps: float, win_s: float = 2.0) -> np.ndarray:
    """Quita la deriva lenta restando una MEDIANA movil centrada.

    Ventana: `int(win_s * fps) | 1` muestras (impar), igual que antes. La
    mediana movil de pandas ignora los NaN de la ventana; donde la entrada es
    NaN, la salida tambien lo es.

    No usar pasabanda: convierte cada evento en un valle flanqueado por dos
    picos falsos y arruina la asimetria y el conteo.
    """
    s = pd.Series(np.asarray(v, dtype=float))
    w = int(win_s * fps) | 1
    return (s - s.rolling(w, center=True, min_periods=1).median()).to_numpy()


def buscar_picos(x, **kwargs):
    """`scipy.signal.find_peaks` sin que un NaN estorbe.

    Los NaN se tratan como -inf: un fotograma sin medida nunca es un pico y
    nunca le impide a su vecino serlo. (Con NaN crudos, la comparacion con el
    vecino da False y el pico se pierde.) Sin NaN, el resultado es identico a
    `find_peaks(x, **kwargs)`.

    Ojo con la senal invertida: hay que invertir ANTES de llamar
    (`buscar_picos(-r)`), asi el NaN vuelve a quedar en -inf.
    """
    x = np.asarray(x, dtype=float)
    if np.isnan(x).any():
        x = np.where(np.isnan(x), -np.inf, x)
    return find_peaks(x, **kwargs)
