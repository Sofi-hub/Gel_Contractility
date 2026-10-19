"""
src/forzada.py
--------------
RESPUESTA FORZADA a una frecuencia de estímulo conocida (2026-10-19, aprobado por Franco).

Cuándo: solo si se pasó `--frecuencia-estimulo` y el conteo salió NO REPORTABLE.
No cuenta contracciones: pregunta "¿la franja se mueve en los instantes en que
dispara el estimulador, más que en cualquier otro momento?". No cambia el veredicto
del conteo ni ningún otro número.

  1. Señal: center_px sin deriva (mediana móvil de 2 s).
  2. Período: el del tren si el reporte lo encontró; si no, se prueba 1/f +-2 %
     (pasos de 0.1 %) y se queda el que más sobresale. Los videos de Andrés dan
     10.10 s con 0.1 Hz configurado (timestamps inventados).
  3. ¿Hay respuesta? Señal plegada al período (promedio de los ciclos desde 8 s):
     cuánto sobresale el pico (SNR). Lo mismo con 40 períodos de control
     (0.55-0.9 y 1.15-1.75 veces), con la MISMA búsqueda de +-2 %.
     p = (1 + controles >= real) / 41 (mínimo 0.024). Hay respuesta si p <= 0.05.
  4. ¿Cuánto? En cada pulso: pico en +-0.2 s menos la mediana de 1.2-0.4 s antes,
     en el sentido del pico plegado. Controles: lo mismo 2-8 s después de cada
     pulso (cada 0.5 s); un pulso "responde" si supera su percentil 95.
     Amplitud = mediana de los pulsos (px y % del grosor).

Medición y validación: data/_mediciones_fases/respuesta_forzada/LEEME.md
(5 reportables: misma amplitud que el reporte, <= 1.5 %; controles 613 y 068: no pasan).
"""
from __future__ import annotations

import numpy as np

from src.estadistica import detrend_median

CONTROLES = np.r_[np.linspace(0.55, 0.9, 20), np.linspace(1.15, 1.75, 20)]
BUSQUEDA = np.linspace(0.98, 1.02, 41)   # +-2 % alrededor del periodo nominal
DESDE_S = 8.0
P_MAX = 0.05


def _plegar(t, r, T):
    m = np.isfinite(r) & (t >= DESDE_S)
    dt = float(np.median(np.diff(t)))
    nb = max(2, int(round(T / dt)))
    idx = np.minimum((np.mod(t[m], T) / dt).astype(int), nb - 1)
    s = np.bincount(idx, weights=r[m], minlength=nb)
    c = np.bincount(idx, minlength=nb)
    return np.where(c > 0, s / np.maximum(c, 1), np.nan)


def _snr(p):
    p = p[np.isfinite(p)]
    if len(p) < 3:
        return float("nan")
    med = np.median(p)
    s = 1.4826 * np.median(np.abs(p - med))
    return float(np.max(np.abs(p - med)) / s) if s > 0 else float("nan")


def _mejor(t, r, T, buscar):
    if not buscar:
        return T, _snr(_plegar(t, r, T))
    v = [(_snr(_plegar(t, r, T * f)), T * f) for f in BUSQUEDA]
    s, Tm = max(v, key=lambda x: -np.inf if not np.isfinite(x[0]) else x[0])
    return Tm, s


def _amp(t, r, t0, sg):
    w = (t >= t0 - 0.2) & (t <= t0 + 0.2)
    b = (t >= t0 - 1.2) & (t <= t0 - 0.4)
    if w.sum() < 3 or b.sum() < 5:
        return np.nan
    return float(np.nanmax(sg * r[w]) - np.nanmedian(sg * r[b]))


def respuesta_forzada(t, center, grosor_px, periodo_s, buscar=True) -> dict:
    """t (s), center_px, grosor en reposo (px), período nominal (s).
    buscar=True: período a +-2 % (cuando no lo fijó un tren)."""
    t = np.asarray(t, float)
    fps = 1.0 / float(np.median(np.diff(t)))
    r = detrend_median(np.asarray(center, float), fps, 2.0)
    T, snr = _mejor(t, r, periodo_s, buscar)
    ctrl = np.array([_mejor(t, r, periodo_s * f, buscar)[1] for f in CONTROLES])
    ctrl = ctrl[np.isfinite(ctrl)]
    p = float((1 + np.sum(ctrl >= snr)) / (len(ctrl) + 1))
    pl = _plegar(t, r, T)
    med = np.nanmedian(pl)
    i = int(np.nanargmax(np.abs(pl - med)))
    sg = 1.0 if pl[i] >= med else -1.0
    dt = float(np.median(np.diff(t)))
    tn = np.arange(i * dt, t[-1], T)
    tn = tn[(tn >= DESDE_S) & (tn <= t[-1] - 0.5)]
    a = np.array([_amp(t, r, x, sg) for x in tn])
    tc = [x + o for x in tn for o in np.arange(2.0, 8.01, 0.5) if x + o <= t[-1] - 0.5]
    ac = np.array([_amp(t, r, x, sg) for x in tc])
    ac = ac[np.isfinite(ac)]
    u95 = float(np.percentile(ac, 95)) if len(ac) else float("nan")
    hay = bool(p <= P_MAX)
    amp = float(np.nanmedian(a)) if hay and len(a) else float("nan")
    return {
        "forzada_periodo_s": float(T), "forzada_snr": snr,
        "forzada_snr_control_max": float(np.max(ctrl)) if len(ctrl) else float("nan"),
        "forzada_p": p, "forzada_hay_respuesta": hay,
        "forzada_sentido": "abajo" if sg > 0 else "arriba",
        "forzada_n_pulsos": int(len(tn)), "forzada_n_responden": int(np.sum(a > u95)),
        "forzada_control_p95_px": u95,
        "forzada_amplitud_px": amp,
        "forzada_amplitud_pct": 100 * amp / grosor_px if grosor_px else float("nan"),
        "_forzada_pulsos": [(float(x), float(v), bool(v > u95)) for x, v in zip(tn, a)],
    }
