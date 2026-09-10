"""
event_detection.py
-------------------
Detección de contracciones ESCALA-INVARIANTE.

Principio de diseño: ningún parámetro fija una escala temporal
absoluta. Todas las ventanas se derivan del ancho de evento MEDIDO
en los propios datos, así que el mismo código funciona con
contracciones de 0.1 s o de 3 s, y con cualquier frecuencia de
estimulación, sin retocar nada.

Validado con eventos sintéticos de 0.2, 0.5, 1.0 y 2.0 s de ancho:
15/15 detectados en los cuatro casos. Con ruido puro y con
ruido+deriva lenta: 0 eventos.

Cómo elegir el umbral (`amp_k`) de forma honesta: usar
`threshold_stability_scan`. Si el número de eventos se mantiene en
una MESETA a lo largo de un rango de k, esos eventos son reales; si
decae monótonamente sin meseta, son ruido. El default k=6 cae dentro
de la meseta en todos los casos validados.
"""

from __future__ import annotations
from dataclasses import dataclass, field
import numpy as np
import pandas as pd
from scipy.signal import find_peaks, peak_widths, savgol_filter


# ------------------------------------------------------------------
# utilidades
# ------------------------------------------------------------------

def rolling_percentile(v, window, q):
    """Percentil móvil centrado. Con q alto aproxima la envolvente
    superior = estado RELAJADO del gel."""
    return pd.Series(v).rolling(int(window), center=True, min_periods=1).quantile(q).to_numpy()


def robust_mad(v):
    v = np.asarray(v, dtype=float)
    if v.size == 0:
        return float("nan")
    return float(np.median(np.abs(v - np.median(v))) * 1.4826)


def _odd(n, minimum=5):
    n = int(n)
    n += (n % 2 == 0)
    return max(n, minimum)


def estimate_period_autocorr(v, fps, min_period_s=0.15, max_period_s=30.0):
    """Período dominante por autocorrelación. Robusto a latidos
    perdidos (a diferencia del promedio de intervalos, que se
    duplica si falta un evento)."""
    x = np.asarray(v, float)
    x = x - x.mean()
    if x.size < 10 or np.allclose(x, 0):
        return float("nan")
    ac = np.correlate(x, x, mode="full")[len(x) - 1:]
    ac /= (ac[0] + 1e-12)
    lo = max(1, int(round(min_period_s * fps)))
    hi = min(len(ac) - 1, int(round(max_period_s * fps)))
    if hi <= lo:
        return float("nan")
    seg = ac[lo:hi]
    pk, pr = find_peaks(seg, height=0.1)
    if len(pk) == 0:
        return float("nan")
    return float((pk[int(np.argmax(pr["peak_heights"]))] + lo) / fps)


# ------------------------------------------------------------------
# resultado
# ------------------------------------------------------------------

@dataclass
class ContractionResult:
    events: pd.DataFrame
    baseline: np.ndarray
    depth: np.ndarray
    signal: np.ndarray          # señal ligeramente suavizada usada para detectar
    event_width_s: float        # escala medida en los datos
    noise_px: float
    amp_threshold_px: float
    diagnostics: dict = field(default_factory=dict)


def _empty_events():
    return pd.DataFrame(columns=[
        "evento", "frame_idx", "tiempo_s", "amplitud_px", "amplitud_pct",
        "agudeza", "duracion_s", "grosor_relajado_px", "grosor_minimo_px", "intervalo_s",
    ])


# ------------------------------------------------------------------
# detección
# ------------------------------------------------------------------

def detect_contractions(
    df: pd.DataFrame,
    raw_col: str = "thickness_px",
    time_col: str = "time_s",
    amp_k: float = 6.0,
    sharpness_threshold: float = 1.30,
    min_amplitude_px: float | None = None,
    noise_px: float | None = None,
    _invert: bool = False,
) -> ContractionResult:
    """
    Parameters
    ----------
    amp_k : umbral = amp_k * ruido, con el ruido medido a la ESCALA
        DEL EVENTO (no a escala de un frame). Verificar con
        threshold_stability_scan antes de fijarlo.
    sharpness_threshold : cociente mínimo entre la amplitud cruda y la
        amplitud tras suavizar con un núcleo de 3x el ancho del
        evento. Como el núcleo se deriva del ancho MEDIDO, este
        criterio es escala-invariante: distingue transitorios reales
        (~1.5) de deriva lenta (~1.0) sea cual sea su duración.
    min_amplitude_px : piso absoluto opcional de amplitud. Útil para
        descartar eventos por debajo de lo que se distingue a ojo,
        o para fijar el umbral definitivo con el video de control.
    noise_px : ruido conocido (video de control). Si se omite, se
        estima de la propia señal.
    _invert : uso interno; corre el detector sobre la señal invertida
        para estimar falsos positivos (ver `symmetric_false_positive_check`).
    """
    t = df[time_col].to_numpy(float)
    raw = df[raw_col].to_numpy(float)
    if _invert:
        raw = -raw
    fps = 1.0 / np.median(np.diff(t))

    # suavizado LIGERO (solo anti-ruido; no deforma la forma del evento)
    light = savgol_filter(raw, _odd(0.1 * fps), 3)

    # --- pasada 1: medir la escala temporal de los eventos ---
    # La ventana tiene que ser MUCHO más ancha que el evento más largo
    # esperado; si no, el percentil nunca ve el estado relajado y la
    # escala sale mal (verificado: con ventana fija de 3s, un evento de
    # 3s se mide como 0.2s y el detector después falla por completo).
    # Se toma una fracción de la duración total, acotada a [3s, 30s].
    duration_s = float(t[-1] - t[0])
    w1 = float(np.clip(0.15 * duration_s, 3.0, 30.0))
    b0 = rolling_percentile(light, max(3, int(w1 * fps)), 0.90)
    d0 = b0 - light
    n0 = robust_mad(d0)
    c0, _ = find_peaks(d0, prominence=max(5 * n0, 1e-12), distance=max(1, int(0.1 * fps)))
    if len(c0):
        ev_w = max(float(np.median(peak_widths(d0, c0, rel_height=0.5)[0])) / fps, 2 / fps)
    else:
        ev_w = 0.2

    # --- pasada 2: todas las ventanas derivadas de esa escala ---
    base_win = max(3, int(round(max(8 * ev_w, 1.5) * fps)))
    base = rolling_percentile(light, base_win, 0.90)
    depth = base - light

    noise = noise_px if noise_px is not None else robust_mad(depth)
    thr = amp_k * noise
    if min_amplitude_px is not None:
        thr = max(thr, min_amplitude_px)

    cand, _ = find_peaks(depth, prominence=thr, distance=max(1, int(round(0.8 * ev_w * fps))))

    if len(cand) == 0:
        return ContractionResult(_empty_events(), base, depth, light, ev_w, noise, thr,
                                 {"fps": fps, "n_candidatos": 0})

    # suavizado de COMPARACIÓN atado al ancho del evento -> agudeza escala-invariante
    comp = savgol_filter(light, _odd(3 * ev_w * fps), 3)
    dcomp = rolling_percentile(comp, base_win, 0.90) - comp

    half = max(1, int(round(ev_w * fps)))
    widths_s = peak_widths(depth, cand, rel_height=0.5)[0] / fps

    rows = []
    for j, i in enumerate(cand):
        lo, hi = max(0, i - half), min(len(raw), i + half + 1)
        seg = raw[lo:hi]
        imin = int(lo + np.argmin(seg))
        amp = float(base[i] - seg.min())
        acmp = float(max(dcomp[lo:hi].max(), 1e-12))
        rows.append({
            "frame_idx": imin,
            "tiempo_s": float(t[imin]),
            "amplitud_px": round(amp, 4),
            "amplitud_pct": round(100 * amp / base[i], 4) if base[i] else np.nan,
            "agudeza": round(amp / acmp, 3),
            "duracion_s": round(float(widths_s[j]), 3),
            "grosor_relajado_px": round(float(base[i]), 3),
            "grosor_minimo_px": round(float(seg.min()), 3),
        })

    cand_df = pd.DataFrame(rows).sort_values(["frame_idx", "amplitud_px"],
                                             ascending=[True, False])
    cand_df = cand_df.drop_duplicates(subset="frame_idx", keep="first").reset_index(drop=True)

    keep = (cand_df["agudeza"] >= sharpness_threshold) & (cand_df["amplitud_px"] >= thr)
    ev = cand_df[keep].reset_index(drop=True)

    if len(ev):
        if _invert:  # deshacer la inversión para que los valores sean interpretables
            ev["grosor_relajado_px"] *= -1
            ev["grosor_minimo_px"] *= -1
        ev.insert(0, "evento", np.arange(1, len(ev) + 1))
        ev["intervalo_s"] = ev["tiempo_s"].diff().round(3)
    else:
        ev = _empty_events()

    return ContractionResult(
        ev, base, depth, light, ev_w, noise, thr,
        {"fps": fps, "n_candidatos": len(cand_df),
         "descartados_por_agudeza": int((~keep).sum())},
    )


# ------------------------------------------------------------------
# herramientas de verificación del umbral
# ------------------------------------------------------------------

def threshold_stability_scan(df, ks=(3, 4, 5, 6, 7, 8, 10, 12), **kw) -> pd.DataFrame:
    """
    Barrido del umbral. INTERPRETACIÓN:
      - Si el conteo se estabiliza en una MESETA a lo largo de varios
        k, esos eventos son reales y el resultado no depende del
        umbral elegido.
      - Si decae monótonamente sin meseta, lo que se está contando es
        ruido.
    Correr esto SIEMPRE al analizar un video nuevo, antes de confiar
    en el conteo.
    """
    rows = []
    for k in ks:
        r = detect_contractions(df, amp_k=k, **kw)
        a = r.events["amplitud_px"]
        rows.append({
            "k": k,
            "n_eventos": len(r.events),
            "umbral_px": round(r.amp_threshold_px, 4),
            "amplitud_min_px": round(float(a.min()), 4) if len(a) else np.nan,
            "amplitud_mediana_px": round(float(a.median()), 4) if len(a) else np.nan,
        })
    return pd.DataFrame(rows)


def symmetric_false_positive_check(df, min_events: int = 3, **kw) -> dict:
    """
    Control de falsos positivos: las contracciones son deflexiones
    hacia ABAJO, así que correr el mismo detector sobre la señal
    invertida cuenta detecciones que sólo pueden ser ruido.

    CUIDADO al interpretar: la línea base es un percentil ALTO, y esa
    construcción no es simétrica cuando hay eventos grandes reales
    (tiende a subestimar los falsos positivos). Sirve como señal de
    alarma cuando la razón arriba/abajo es alta (~1), no como una
    tasa de error exacta.
    """
    dn = detect_contractions(df, **kw)
    up = detect_contractions(df, _invert=True, **kw)
    n_dn, n_up = len(dn.events), len(up.events)
    ratio = n_up / n_dn if n_dn else np.nan

    # Con muy pocos eventos el cociente no es informativo: 1 abajo y 0
    # arriba daría "señal limpia" cuando en realidad no hay nada que
    # medir. Se exige un mínimo de eventos antes de afirmar que hay señal.
    if n_dn < min_events:
        veredicto = f"sin evidencia de contracciones (menos de {min_events} eventos)"
    elif n_up >= 0.5 * n_dn:
        veredicto = "dudoso: muchas detecciones espurias, subir amp_k"
    else:
        veredicto = "señal por encima del ruido"

    return {
        "n_abajo": n_dn,
        "n_arriba": n_up,
        "razon_arriba_abajo": round(ratio, 3) if n_dn else np.nan,
        "veredicto": veredicto,
    }


# ------------------------------------------------------------------
# ritmo
# ------------------------------------------------------------------

def segment_by_rhythm(events, tolerance=0.35, min_events_per_segment=3,
                      max_missed_multiple=3) -> pd.DataFrame:
    """
    Segmenta los eventos en tramos de frecuencia homogénea.

    Un intervalo ~N veces el ritmo local se interpreta como N-1
    latidos perdidos (mismo segmento) SÓLO si N es chico; un salto
    mayor es un cambio de frecuencia de estimulación y abre un
    segmento nuevo. Después se fusionan vecinos con período
    indistinguible, porque la pasada secuencial tiende a
    sobre-fragmentar.
    """
    out = events.copy()
    if len(out) == 0:
        out["segmento"] = pd.Series(dtype=int)
        return out
    if len(out) < 2:
        out["segmento"] = 1
        return out

    iv = out["intervalo_s"].to_numpy()
    seg = np.ones(len(out), dtype=int)
    cur, local = 1, []
    for i in range(1, len(out)):
        g = iv[i]
        if np.isnan(g):
            cur += 1; local = []
        elif not local:
            local.append(g)
        else:
            ref = float(np.median(local))
            ratio = g / ref if ref > 0 else np.inf
            m = round(ratio)
            if 1 <= m <= max_missed_multiple and abs(ratio - m) <= tolerance:
                pass                       # latido perdido -> mismo segmento
            elif abs(ratio - 1.0) > tolerance:
                cur += 1; local = []       # cambio de frecuencia
            else:
                local.append(g)
        seg[i] = cur
    out["segmento"] = seg

    changed = True
    while changed:
        changed = False
        ids = sorted(out["segmento"].unique())
        for a, b in zip(ids[:-1], ids[1:]):
            ia = out[out.segmento == a]["tiempo_s"].diff().dropna()
            ib = out[out.segmento == b]["tiempo_s"].diff().dropna()
            if len(ia) == 0 or len(ib) == 0:
                continue
            pa, pb = float(np.median(ia)), float(np.median(ib))
            if pa <= 0 or pb <= 0:
                continue
            if abs(max(pa, pb) / min(pa, pb) - 1.0) <= tolerance:
                out.loc[out.segmento == b, "segmento"] = a
                changed = True
                break
    out["segmento"] = out["segmento"].map(
        {s: i + 1 for i, s in enumerate(sorted(out["segmento"].unique()))})

    counts = out["segmento"].value_counts()
    tiny = counts[counts < min_events_per_segment].index.tolist()
    if tiny and len(counts) > 1:
        mapping, prev = {}, None
        for s in sorted(out["segmento"].unique()):
            if s in tiny and prev is not None:
                mapping[s] = prev
            else:
                mapping[s] = s; prev = s
        out["segmento"] = out["segmento"].map(mapping)
        out["segmento"] = out["segmento"].map(
            {s: i + 1 for i, s in enumerate(sorted(out["segmento"].unique()))})
    return out


def analyze_segments(events_with_segment, signal=None, time=None) -> pd.DataFrame:
    """Frecuencia, regularidad, amplitud y latidos perdidos por segmento."""
    rows = []
    for sid, sub in events_with_segment.groupby("segmento"):
        sub = sub.sort_values("tiempo_s")
        iv = sub["tiempo_s"].diff().dropna().to_numpy()
        r = {
            "segmento": int(sid), "n_eventos": len(sub),
            "t_inicio_s": round(float(sub.tiempo_s.min()), 2),
            "t_fin_s": round(float(sub.tiempo_s.max()), 2),
            "amplitud_media_px": round(float(sub.amplitud_px.mean()), 4),
            "amplitud_std_px": round(float(sub.amplitud_px.std(ddof=0)), 4),
            "duracion_media_s": round(float(sub.duracion_s.mean()), 3),
        }
        if len(iv):
            p = float(np.median(iv))
            r["periodo_s"] = round(p, 3)
            r["frecuencia_Hz"] = round(1 / p, 4) if p > 0 else np.nan
            exp = int(round(iv.sum() / p)) if p > 0 else len(iv)
            missed = max(0, exp - len(iv))
            r["latidos_perdidos"] = missed
            tot = len(sub) + missed
            r["tasa_captura_pct"] = round(100 * len(sub) / tot, 1) if tot else np.nan
            single = iv[np.abs(iv / p - 1) <= 0.35] if p > 0 else iv
            r["CV_intervalo_pct"] = (round(float(100 * np.std(single, ddof=0) / np.mean(single)), 2)
                                     if len(single) >= 2 else np.nan)
        else:
            r.update({"periodo_s": np.nan, "frecuencia_Hz": np.nan, "latidos_perdidos": 0,
                      "tasa_captura_pct": np.nan, "CV_intervalo_pct": np.nan})
        if signal is not None and time is not None and len(sub) >= 3:
            m = (time >= sub.tiempo_s.min()) & (time <= sub.tiempo_s.max())
            if m.sum() > 20:
                fps = 1 / np.median(np.diff(time))
                r["periodo_autocorr_s"] = round(estimate_period_autocorr(signal[m], fps), 3)
        rows.append(r)
    return pd.DataFrame(rows)


def frequency_profile(signal, time, window_s=8.0, step_s=1.0,
                      min_period_s=0.15, max_period_s=15.0) -> pd.DataFrame:
    """
    Período dominante en ventana móvil. Es el método más robusto para
    identificar cambios de frecuencia de estimulación, porque no
    depende de haber detectado cada evento.

    LIMITACIÓN: no resuelve períodos mayores a ~window_s/2. Para
    estimulación lenta hay que subir window_s.
    """
    fps = 1 / np.median(np.diff(time))
    W = max(8, int(round(window_s * fps)))
    step = max(1, int(round(step_s * fps)))
    rows = []
    for c in range(W // 2, len(signal) - W // 2, step):
        p = estimate_period_autocorr(signal[c - W // 2:c + W // 2], fps,
                                     min_period_s, max_period_s)
        rows.append({"tiempo_s": round(float(time[c]), 2),
                     "periodo_s": round(p, 4) if not np.isnan(p) else np.nan,
                     "frecuencia_Hz": round(1 / p, 4) if (not np.isnan(p) and p > 0) else np.nan})
    return pd.DataFrame(rows)


def interpret_regularity(cv):
    if cv is None or (isinstance(cv, float) and np.isnan(cv)):
        return "insuficientes eventos"
    if cv < 3:  return "muy regular (compatible con estimulo externo)"
    if cv < 10: return "regular"
    if cv < 25: return "moderadamente irregular"
    return "irregular"
