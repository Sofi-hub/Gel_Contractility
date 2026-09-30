"""
cinetica.py
-----------
Cinetica de cada contraccion: onset, TTP, RT50, duracion y amplitud relativa.

Se calcula SOBRE LA DETECCION YA VALIDADA (los picos que elige
`contraction_report.analizar` dentro de la meseta del umbral), sobre la senal
del canal de deteccion sin deriva y con el signo ya corregido: los eventos van
hacia arriba y el reposo es 0.

DEFINICIONES
------------
Sea A = r[pico] la amplitud (la misma `amplitud_px` que ya se reporta: la
linea de base es la mediana movil que quita la deriva).

  onset   primer cruce del 10 % de A caminando HACIA ATRAS desde el pico.
  TTP     t(pico) - t(onset).
  RT50    t(cruce del 50 % de A despues del pico) - t(pico). Es el tiempo hasta
          caer a la MITAD DE LA AMPLITUD, como lo define el paper (eLife). No es
          "la mitad de la duracion de la relajacion", que es lo que calculaba
          `Half_Relax_Time` en Contraction_Analysis.mlx (ver
          claude/metricas-cinetica-TTP-RT50.md, error a).
  offset  primer cruce del 10 % de A despues del pico.
  amplitud_relativa_pct  100 * A / grosor en reposo. El grosor en reposo es
          la mediana movil del grosor crudo en el fotograma del pico. NO se
          divide por el valor crudo del canal (el script de MATLAB dividia por
          la senal ya centrada, que oscila alrededor de 0: error b). En este
          pipeline el valor crudo de `center_px` es una FILA de la imagen, que
          depende de donde quedo el gel en el campo y no significa nada; el
          grosor si es una escala propia del gel, y el cociente no depende del
          aumento, que es justo lo que hace falta para comparar entre videos
          sin calibrar px -> mm.

Los cruces se interpolan linealmente entre fotogramas para el valor puntual.
No hay ningun corrimiento fijo del onset (el `Idx_Before - 5` del script de
MATLAB, error c).

POR QUE UN INTERVALO Y NO SOLO UN NUMERO
----------------------------------------
A 30 fps la subida entera de una contraccion rapida ocupa 1-2 fotogramas. La
interpolacion da un numero con decimales, pero lo que se sabe de verdad es un
intervalo, y sale de dos fuentes de incertidumbre:

1. Muestreo. Un cruce de nivel entre los fotogramas i e i+1 ocurrio en algun
   instante de (t[i], t[i+1]).
2. Donde esta el pico. El maximo muestreado no es el maximo verdadero: este
   puede caer en cualquier punto de (t[p-1], t[p+1]). Y si el evento tiene
   MESETA (Video_466, Video_583: varios fotogramas al 96-100 %), todos los
   fotogramas que quedan a menos de `Z_PICO` veces el ruido del maximo son
   indistinguibles de el. El pico puede estar en cualquiera: [p_lo, p_hi].

Con eso:
    TTP  en [ t[p_lo-1] - t[on+1] ,  t[p_hi+1] - t[on] ]
    RT50 en [ t[j50-1]  - t[p_hi+1],  t[j50]  - t[p_lo-1] ]
(recortados a >= 0).

CUANDO SE REPORTA
-----------------
Un TTP de 2 fotogramas no mide la biologia, mide el intervalo de muestreo.
Regla (propuesta 3 del documento de viabilidad): la metrica es reportable
para un evento si abarca al menos `min_frames` fotogramas (default 5, que da
~20 % de error de cuantizacion). Para el video: si la MEDIANA de fotogramas
llega a `min_frames` y ademas el conteo de eventos es reportable (meseta del
umbral con 0 falsos). Si no, el valor puntual queda en NaN y se reporta solo
la cota superior: "TTP < X ms", nunca "TTP = X ms".

Nada de esto necesita calibracion: TTP y RT50 estan en segundos y la
amplitud relativa en %.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

NIVEL_ONSET = 0.10     # fraccion de A que define onset y offset
NIVEL_RT = 0.50        # fraccion de A que define RT50
Z_PICO = 2.0           # fotogramas a menos de Z_PICO*ruido del maximo = meseta del pico
MIN_FRAMES = 5         # fotogramas minimos para que TTP / RT50 sean medibles


def _cruce_atras(r: np.ndarray, p: int, nivel: float, lim: int):
    """Indice `i` < p tal que r[i] <= nivel < r[i+1..p], o None si no cruza
    antes de `lim` (el pico anterior o el borde de la ventana).

    Tambien None si antes del cruce aparece un fotograma sin medida (NaN): el
    cruce pudo estar en el hueco, asi que la metrica de ese evento no se mide.
    Sin esto, la busqueda saltaba el NaN y "encontraba" un cruce del otro lado.
    """
    i = p - 1
    while i >= lim:
        if np.isnan(r[i]):
            return None
        if r[i] <= nivel:
            return i
        i -= 1
    return None


def _cruce_adelante(r: np.ndarray, p: int, nivel: float, lim: int):
    """Indice `j` > p tal que r[j] <= nivel < r[p..j-1], o None (tambien si
    antes del cruce hay un fotograma sin medida; ver `_cruce_atras`)."""
    j = p + 1
    while j <= lim:
        if np.isnan(r[j]):
            return None
        if r[j] <= nivel:
            return j
        j += 1
    return None


def _interp(t: np.ndarray, r: np.ndarray, a: int, b: int, nivel: float) -> float:
    """Instante en que la recta entre (t[a], r[a]) y (t[b], r[b]) cruza `nivel`."""
    if r[b] == r[a]:
        return float(t[a])
    return float(t[a] + (nivel - r[a]) / (r[b] - r[a]) * (t[b] - t[a]))


def _meseta_pico(r: np.ndarray, p: int, umbral: float, lo: int, hi: int):
    """Tramo contiguo alrededor de p con r >= umbral (fotogramas indistinguibles
    del maximo dadas las fluctuaciones del ruido)."""
    a = p
    while a - 1 >= lo and r[a - 1] >= umbral:
        a -= 1
    b = p
    while b + 1 <= hi and r[b + 1] >= umbral:
        b += 1
    return a, b


def cinetica_eventos(t: np.ndarray, r: np.ndarray, picos: np.ndarray, ruido: float,
                     grosor_reposo: np.ndarray | None = None,
                     ventana_s: float = 1.5,
                     min_frames: int = MIN_FRAMES) -> pd.DataFrame:
    """Una fila por evento con onset, TTP, RT50, offset, duracion y amplitud
    relativa, cada metrica temporal con su intervalo [min, max].

    t      : tiempos (s) de cada fotograma (idealmente de los PTS)
    r      : canal sin deriva, con los eventos hacia arriba y reposo en 0
    picos  : indices de los eventos (los de la deteccion validada)
    ruido  : MAD del canal (px), para delimitar la meseta del pico
    grosor_reposo : grosor en reposo por fotograma (px), para la amplitud relativa
    ventana_s : cuanto se busca un cruce a cada lado del pico, como maximo. Ademas
                la busqueda nunca pasa el pico vecino.
    """
    t = np.asarray(t, float)
    r = np.asarray(r, float)
    picos = np.asarray(picos, int)
    n = len(r)
    dt = float(np.median(np.diff(t))) if n > 1 else float("nan")
    w = max(1, int(round(ventana_s / dt))) if np.isfinite(dt) and dt > 0 else 45

    filas = []
    for e, p in enumerate(picos):
        A = float(r[p])
        lo = max(0, p - w, int(picos[e - 1]) if e > 0 else 0)
        hi = min(n - 1, p + w, int(picos[e + 1]) if e + 1 < len(picos) else n - 1)
        f = {"evento": e + 1, "frame_pico": int(p), "tiempo_s": float(t[p]),
             "amplitud_px": A}

        if grosor_reposo is not None and np.isfinite(grosor_reposo[p]) and grosor_reposo[p] > 0:
            f["grosor_reposo_px"] = float(grosor_reposo[p])
            f["amplitud_relativa_pct"] = 100.0 * A / float(grosor_reposo[p])
        else:
            f["grosor_reposo_px"] = np.nan
            f["amplitud_relativa_pct"] = np.nan

        p_lo, p_hi = _meseta_pico(r, p, A - Z_PICO * ruido, lo + 1, hi - 1)
        f["meseta_pico_frames"] = int(p_hi - p_lo + 1)

        # --- subida: onset y TTP ----------------------------------------
        on = _cruce_atras(r, p, NIVEL_ONSET * A, lo)
        if on is not None:
            t_on = _interp(t, r, on, on + 1, NIVEL_ONSET * A)
            f["onset_s"] = t_on
            f["ttp_frames"] = int(p - on)
            f["ttp_s"] = float(t[p] - t_on)
            f["ttp_min_s"] = max(0.0, float(t[max(p_lo - 1, 0)] - t[on + 1]))
            f["ttp_max_s"] = float(t[min(p_hi + 1, n - 1)] - t[on])
            f["ttp_medible"] = bool(p - on >= min_frames)
        else:
            f.update(onset_s=np.nan, ttp_frames=np.nan, ttp_s=np.nan,
                     ttp_min_s=np.nan, ttp_max_s=np.nan, ttp_medible=False)

        # --- bajada: RT50 y offset --------------------------------------
        j50 = _cruce_adelante(r, p, NIVEL_RT * A, hi)
        if j50 is not None:
            t50 = _interp(t, r, j50 - 1, j50, NIVEL_RT * A)
            f["rt50_frames"] = int(j50 - p)
            f["rt50_s"] = float(t50 - t[p])
            f["rt50_min_s"] = max(0.0, float(t[j50 - 1] - t[min(p_hi + 1, n - 1)]))
            f["rt50_max_s"] = float(t[j50] - t[max(p_lo - 1, 0)])
            f["rt50_medible"] = bool(j50 - p >= min_frames)
        else:
            f.update(rt50_frames=np.nan, rt50_s=np.nan, rt50_min_s=np.nan,
                     rt50_max_s=np.nan, rt50_medible=False)

        off = _cruce_adelante(r, p, NIVEL_ONSET * A, hi)
        if off is not None:
            f["offset_s"] = _interp(t, r, off - 1, off, NIVEL_ONSET * A)
            f["duracion_frames"] = int(off - on) if on is not None else np.nan
            f["duracion_s"] = (float(f["offset_s"] - f["onset_s"])
                               if on is not None else np.nan)
        else:
            f.update(offset_s=np.nan, duracion_frames=np.nan, duracion_s=np.nan)
        filas.append(f)

    cols = ["evento", "frame_pico", "tiempo_s", "amplitud_px", "grosor_reposo_px",
            "amplitud_relativa_pct", "meseta_pico_frames",
            "onset_s", "ttp_frames", "ttp_s", "ttp_min_s", "ttp_max_s", "ttp_medible",
            "rt50_frames", "rt50_s", "rt50_min_s", "rt50_max_s", "rt50_medible",
            "offset_s", "duracion_frames", "duracion_s"]
    return pd.DataFrame(filas, columns=cols)


def _iqr(x: np.ndarray) -> str | None:
    x = x[np.isfinite(x)]
    if len(x) < 2:
        return None
    q1, q3 = np.percentile(x, [25, 75])
    return f"{q1:.4g}-{q3:.4g}"


def resumir(ev: pd.DataFrame, conteo_reportable: bool,
            min_frames: int = MIN_FRAMES) -> dict:
    """Resumen por video. El valor puntual de TTP / RT50 solo se emite si es
    medible; si no, queda NaN y se da la cota superior."""
    out: dict = {"cinetica_min_frames": int(min_frames)}
    if ev is None or len(ev) == 0:
        out["cinetica_motivo"] = "sin eventos"
        return out

    ar = ev["amplitud_relativa_pct"].to_numpy(float)
    out["amplitud_relativa_pct"] = (float(np.nanmedian(ar)) if np.isfinite(ar).any()
                                    else float("nan"))
    out["amplitud_relativa_iqr_pct"] = _iqr(ar)

    motivos = []
    for m in ("ttp", "rt50"):
        fr = ev[f"{m}_frames"].to_numpy(float)
        ok = np.isfinite(fr)
        out[f"{m}_n_eventos"] = int(ok.sum())
        if not ok.any():
            out[f"{m}_reportable"] = False
            out[f"{m}_s"] = float("nan")
            motivos.append(f"{m.upper()}: ningun evento cruza el nivel dentro de la ventana")
            continue
        fr_med = float(np.median(fr[ok]))
        out[f"{m}_frames_mediana"] = fr_med
        reportable = bool(conteo_reportable and fr_med >= min_frames)
        out[f"{m}_reportable"] = reportable
        val = ev[f"{m}_s"].to_numpy(float)[ok]
        out[f"{m}_s"] = float(np.median(val)) if reportable else float("nan")
        out[f"{m}_iqr_s"] = _iqr(val) if reportable else None
        out[f"{m}_cota_inf_s"] = float(np.median(ev[f"{m}_min_s"].to_numpy(float)[ok]))
        out[f"{m}_cota_sup_s"] = float(np.median(ev[f"{m}_max_s"].to_numpy(float)[ok]))
        if not conteo_reportable:
            motivos.append(f"{m.upper()}: el conteo de eventos no es reportable")
        elif fr_med < min_frames:
            motivos.append(f"{m.upper()}: {fr_med:g} fotogramas (< {min_frames}); "
                           f"solo cota {m.upper()} < {1000 * out[f'{m}_cota_sup_s']:.0f} ms")
    out["cinetica_motivo"] = "; ".join(motivos) if motivos else "TTP y RT50 medibles"
    return out
