"""Plegado de una señal a un período, con controles (medición, no del análisis).
Usado en data/_mediciones_fases (b7, andres)."""
import numpy as np


def _snr(p):
    p = p[np.isfinite(p)]
    med = np.median(p)
    r = 1.4826 * np.median(np.abs(p - med))
    return float(np.max(np.abs(p - med)) / r) if r > 0 else float("nan")


def plegar(t, r, T, desde=8.0):
    m = np.isfinite(r) & (t >= desde)
    dt = float(np.median(np.diff(t)))
    nb = int(round(T / dt))
    idx = np.minimum((np.mod(t[m], T) / dt).astype(int), nb - 1)
    s = np.bincount(idx, weights=r[m], minlength=nb)
    c = np.bincount(idx, minlength=nb)
    return np.where(c > 0, s / np.maximum(c, 1), np.nan)


def plegar_snr(t, r, T, controles=(0.73, 0.81, 0.89, 1.13, 1.21, 1.37)):
    return _snr(plegar(t, r, T)), [_snr(plegar(t, r, T * f)) for f in controles]
