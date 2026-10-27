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
  5. CINETICA DE LA RESPUESTA AL ESTIMULO (2026-10-27, aprobado por Franco).
     TTP y RT50 de cada pulso que responde, con las reglas de src/cinetica.py
     (pico = primer fotograma >= 95 % del maximo; valor solo si la subida -o la
     bajada al 50 %- abarca >= 5 fotogramas, si no la cota), y la MEDIANA de los
     pulsos medibles con IC 95 % por bootstrap. Es un numero APARTE: no es un
     conteo, no cambia el veredicto NO REPORTABLE ni ningun numero existente.
     Se mide PULSO A PULSO y NO sobre la forma promedio: promediar da +42 % de
     TTP en 466, porque los pulsos que no responden y el desfasaje del reloj del
     estimulador (9.98 s medidos contra 10.0018 s) achatan y ensanchan la forma.

Medición y validación: data/_mediciones_fases/respuesta_forzada/LEEME.md
(5 reportables: misma amplitud que el reporte, <= 1.5 %; controles 613 y 068: no pasan)
y data/_mediciones_fases/cinetica_forzada/LEEME.md (la mediana pulso a pulso
reproduce el TTP/RT50 del reporte en los reportables: 466 +1 %/-3 %, 583 +2 %/-1 %).
"""
from __future__ import annotations

import numpy as np

from src.cinetica import cinetica_eventos, ic95_mediana
from src.estadistica import detrend_median

CONTROLES = np.r_[np.linspace(0.55, 0.9, 20), np.linspace(1.15, 1.75, 20)]
BUSQUEDA = np.linspace(0.98, 1.02, 41)   # +-2 % alrededor del periodo nominal
DESDE_S = 8.0
P_MAX = 0.05

LAG_ANTES, LAG_DESPUES = 1.5, 2.5    # s de recorte alrededor de cada pulso
BASE_PULSO = (-1.2, -0.4)            # linea de base de cada pulso (la misma de _amp)
VENTANA_PICO = (-0.4, 0.6)           # donde se busca el maximo del pulso


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


def _cinetica_de_un_pulso(lag, y):
    """TTP / RT50 de UN pulso recortado, con las reglas de src/cinetica.py.
    None si el pulso no sirve (sale del video, o no hay donde buscar el pico)."""
    b = (lag >= BASE_PULSO[0]) & (lag <= BASE_PULSO[1])
    v = (lag >= VENTANA_PICO[0]) & (lag <= VENTANA_PICO[1])
    if b.sum() < 3 or not v.any() or not np.isfinite(y).all():
        return None
    ruido = 1.4826 * float(np.median(np.abs(y[b] - np.median(y[b]))))
    p = int(np.flatnonzero(v)[np.argmax(y[v])])
    try:
        return cinetica_eventos(lag, y, np.array([p]), ruido).iloc[0]
    except (ValueError, IndexError):
        return None


def _ms(x):
    return float(1000 * x) if np.isfinite(x) else None


def cinetica_pulsos(t, r, instantes, sg, dt) -> tuple[dict, list]:
    """Cinetica de la RESPUESTA AL ESTIMULO, pulso a pulso (no es un conteo).

    `instantes` son los pulsos que responden; cada uno se recorta de -1.5 a
    +2.5 s, se le resta su propia linea de base y se mide con las reglas de
    src/cinetica.py. El numero del video es la MEDIANA de los pulsos medibles,
    y solo se emite si lo es al menos la mitad de los que cruzan el nivel (la
    misma regla que `cinetica.resumir`); si no, solo la cota.

    Devuelve (resumen para el reporte, una fila por pulso).
    """
    lag = np.arange(-LAG_ANTES, LAG_DESPUES + 1e-9, dt)
    b = (lag >= BASE_PULSO[0]) & (lag <= BASE_PULSO[1])
    x = np.asarray(r, float)
    filas = []
    for i, t0 in enumerate(instantes, 1):
        y = np.interp(t0 + lag, t, sg * x, left=np.nan, right=np.nan)
        if not np.isfinite(y).all():
            continue                       # el pulso se sale del video
        e = _cinetica_de_un_pulso(lag, y - np.median(y[b]))
        if e is None:
            continue
        filas.append({"pulso": i, "instante_s": float(t0),
                      "amplitud_px": float(e["amplitud_px"]),
                      "ttp_ms": _ms(e["ttp_s"]), "ttp_medible": bool(e["ttp_medible"]),
                      "ttp_cota_ms": _ms(e["ttp_max_s"]),
                      "rt50_ms": _ms(e["rt50_s"]), "rt50_medible": bool(e["rt50_medible"]),
                      "rt50_cota_ms": _ms(e["rt50_max_s"])})

    out = {"forzada_cinetica_n_pulsos": len(filas)}
    for m in ("ttp", "rt50"):
        con = [f for f in filas if f[f"{m}_ms"] is not None]
        med = [f[f"{m}_ms"] for f in con if f[f"{m}_medible"]]
        rep = bool(med and len(med) >= 0.5 * len(con))
        cot = [f[f"{m}_cota_ms"] for f in con if f[f"{m}_cota_ms"] is not None]
        ic = ic95_mediana(np.asarray(med, float)) if rep and len(med) >= 3 else None
        if ic:   # ic95_mediana da 4 cifras; en ms sobran los decimales
            ic = "-".join(f"{float(v):.0f}" for v in ic.split("-"))
        out[f"forzada_{m}_n_con_cruce"] = len(con)
        out[f"forzada_{m}_n_medibles"] = len(med)
        out[f"forzada_{m}_reportable"] = rep
        out[f"forzada_{m}_ms"] = float(np.median(med)) if rep else float("nan")
        out[f"forzada_{m}_ic95_ms"] = ic
        out[f"forzada_{m}_cota_ms"] = float(np.median(cot)) if cot else float("nan")
    return out, filas


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
    out = {
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
    if hay:
        # cinetica de la respuesta al estimulo, solo sobre los pulsos que
        # responden: un instante en el que el gel no se movio no tiene subida
        # ni bajada que medir, y promediarlo ensancha todo (ver el docstring).
        responden = [float(x) for x, v in zip(tn, a) if np.isfinite(v) and v > u95]
        cin, pulsos = cinetica_pulsos(t, r, responden, sg, dt)
        out.update(cin)
        out["_forzada_cinetica"] = pulsos
    return out
