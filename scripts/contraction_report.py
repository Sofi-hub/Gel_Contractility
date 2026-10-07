"""
scripts/contraction_report.py
------------------------------
Detecta las contracciones usando el observable CORRECTO y mide el
adelgazamiento aunque este por debajo del ruido frame a frame.

POR QUE ESTE SCRIPT EXISTE
---------------------------
Medido sobre dos videos reales del proyecto (Video_prueba, que "funciona",
y Video_063, que "no funcionaba"), la contraccion NO se manifiesta
principalmente como adelgazamiento: se manifiesta como un DESPLAZAMIENTO
VERTICAL de toda la franja. Los dos bordes se mueven juntos, en el mismo
sentido, y solo una parte chica de ese movimiento es un cambio de grosor.

    canal                     Video_prueba     Video_063
    traslacion (center_px)       6.82 px        1.49 px
    adelgazamiento (grosor)      1.26 px        0.28 px
    cociente adelg./trasl.       18.5 %         19.0 %

El cociente es practicamente el MISMO en los dos videos: la mecanica de la
contraccion es igual, lo que cambia es la amplitud (Video_063 contrae ~4.6
veces mas debil). Como el grosor es un observable atenuado ~5x respecto de
la traslacion, en el video debil el adelgazamiento cae por debajo del ruido
por frame y el detector no lo ve. La traslacion, en cambio, sigue estando
44 sigma por encima del ruido.

Consecuencia practica:

  * DETECTAR sobre `center_px` (la posicion media de la franja), no sobre
    `thickness_px`. Prueba de estabilidad del umbral sobre Video_063:

        center_px      k=10..20 -> 5 eventos, 0 falsos    (meseta limpia)
        thickness_px   k=3..4   -> 7 eventos, 5-11 falsos (=ruido)
                       k>=6     -> 0 eventos

  * MEDIR el adelgazamiento promediando los eventos alineados en el tiempo
    (event-locked average). Con 5 eventos el ruido del promedio baja
    sqrt(5) veces y el adelgazamiento de Video_063 pasa de invisible
    (~1 sigma por frame) a 9.7 sigma. El grosor sigue siendo la variable
    biomecanicamente interesante; lo que no sirve es usarlo para DETECTAR.

Uso:
    python scripts/contraction_report.py --input data/processed_data/mi_video/serie_temporal.xlsx
    python scripts/contraction_report.py --input A.xlsx --compare B.xlsx
"""

from __future__ import annotations
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src import rhythm_split as rs
from src import cinetica as cin
# MAD, mediana movil y busqueda de picos viven en src/estadistica.py y toleran
# fotogramas sin medida (NaN). Se re-exportan con el mismo nombre porque el
# cuaderno y otros scripts llaman a `cr.mad` y `cr.detrend_median`.
from src.estadistica import mad, detrend_median, buscar_picos


# --------------------------------------------------------------------------
def _signo_evento(r: np.ndarray) -> int:
    """+1 si los eventos son excursiones hacia arriba, -1 si hacia abajo.

    Se decide por la cola de la distribucion, no por un supuesto: el signo
    de `center_px` depende de la convencion de la imagen y de si el gel
    sube o baja al contraerse, y eso cambia entre montajes.
    """
    m = mad(r)
    if m <= 0:
        return 1
    arriba = float(np.mean(r > 4 * m))
    abajo = float(np.mean(r < -4 * m))
    return 1 if arriba >= abajo else -1


# Grilla de k: geometrica, pasos de x1.1, de 3 a ~24 (Fase 2.2, H34). La vieja
# (3, 4, 6, 8, 10, 12, 15, 20) tenia pasos de x1.2 a x1.5 y "2 puntos seguidos"
# significaba mesetas de anchos muy distintos.
K_GRILLA = tuple(round(3.0 * 1.1 ** n, 3) for n in range(23))
# Una meseta tiene que abarcar al menos este factor en k (no "N puntos de la grilla").
FACTOR_MESETA = 1.25


def detectar(r: np.ndarray, umbral: float, fps: float, sep_s: float | None = None):
    """QUE ES UN EVENTO (Fase 2.2): un pico que sube al menos `umbral` sobre el
    reposo (altura) Y sobresale al menos `umbral` sobre el valle que lo separa
    de su vecino mas alto (prominencia).

    La prominencia reemplaza a la separacion minima `sep_s`, que era un tiempo
    absoluto y fallaba de las dos maneras (medido, ver
    claude/propuesta-fase-2-2.md):
      - fundia eventos reales cercanos: en Video_prueba borraba la contraccion
        de 15.278 s (19.5 MAD) por estar a 0.27 s de otra, aunque la senal
        vuelve al reposo entre las dos (H8);
      - contaba como evento un repunte de ruido en la cola de un evento lento
        (H55): tiene altura, pero prominencia de ruido.
    `sep_s` queda solo como opcion manual (None = no se usa).
    """
    kw = {"height": umbral, "prominence": umbral}
    if sep_s:
        kw["distance"] = max(1, int(round(sep_s * fps)))
    return buscar_picos(r, **kw)[0]


def escaneo_estabilidad(r: np.ndarray, fps: float, ks=K_GRILLA,
                        sep_s: float | None = None) -> pd.DataFrame:
    """Conteo de eventos vs umbral, con control simetrico de falsos positivos.

    El control: correr el mismo detector sobre la senal INVERTIDA. Una
    contraccion solo puede ir en un sentido, asi que todo lo que aparece
    del lado invertido es ruido. Si el conteo real no despega del conteo
    invertido, no hay eventos.
    """
    m = mad(r)
    filas = []
    for k in ks:
        pk = detectar(r, k * m, fps, sep_s)
        pn = detectar(-r, k * m, fps, sep_s)
        filas.append({"k": k, "umbral_px": round(k * m, 4),
                      "eventos": len(pk), "falsos_control": len(pn)})
    return pd.DataFrame(filas)


def elegir_k_meseta(estab: pd.DataFrame, min_puntos: int = 2,
                    factor_min: float = FACTOR_MESETA) -> dict:
    """Elige k dentro de la MESETA del escaneo de estabilidad.

    La regla es la del protocolo, no una heuristica nueva: sirve un k tal que
    (a) el conteo de eventos no cambia al subir el umbral -- o sea el
    resultado no depende de donde se puso el umbral -- y (b) el control de
    falsos sobre la senal invertida da 0 en toda esa meseta.

    CUAL meseta, cuando hay varias: la de k MAS BAJO. Al subir el umbral se
    van perdiendo eventos reales, asi que la primera meseta con 0 falsos es
    la que ya elimino el ruido y todavia no empezo a comerse senal. Elegir
    "la meseta mas larga" da la respuesta EQUIVOCADA: en Video_063 el escaneo
    tiene una meseta de 6 eventos en k=6..8 (2 puntos) y otra de 5 eventos en
    k=10..20 (4 puntos); la validada es la de 6.

    Se exigen al menos `min_puntos` valores de k consecutivos con el mismo
    conteo, y que la meseta abarque al menos un factor `factor_min` en k
    (Fase 2.2: el ancho se mide en k, no en puntos de una grilla dada).

    Que k se usa DENTRO de la meseta: el del centro geometrico (Fase 2.2, H34).
    El conteo es el mismo en toda la meseta; el centro queda lejos del borde
    donde empiezan los falsos. Se devuelven TODAS las mesetas, para que un
    video con dos (Video_063: 6 y 5 eventos) lo diga en vez de esconderlo.

    Con la deteccion por prominencia, la regla "la de k mas bajo" no eligio
    mal en ninguna de 300 series sinteticas de conteo conocido (con la
    deteccion vieja fallaba: H55).

    POR QUE AUTOMATIZARLO: con el k=8 por defecto, Video_583 daba 9 eventos
    (1 falso) y rhythm_split NO encontraba el tren, porque los eventos
    espurios ensuciaban el ajuste de la grilla. Su meseta real estaba en
    k=12..20 con 6 eventos y 0 falsos. El fallo no era ruidoso: no avisaba
    nada, simplemente hacia desaparecer el tren.

    Devuelve dict con k, n_eventos, k_rango, hay_meseta y motivo.
    """
    if estab is None or len(estab) == 0:
        return {"k": None, "hay_meseta": False, "motivo": "escaneo vacio"}

    e = estab.sort_values("k").reset_index(drop=True)

    # Primero se descartan los umbrales con falsos positivos, y RECIEN
    # DESPUES se buscan tramos de conteo constante entre los que quedaron.
    # El orden importa: agrupar por conteo y despues exigir 0 falsos en todo
    # el grupo es demasiado estricto, porque un tramo de conteo constante
    # suele empezar unos k antes de que los falsos lleguen a cero y eso
    # invalida la meseta entera (paso con Video_466: 5 eventos en k=6..15
    # pero con 1 falso en k=6, y la meseta real es k=8..15).
    limpio = e[e["falsos_control"] == 0]
    mesetas = []
    idx = list(limpio.index)
    i = 0
    while i < len(idx):
        j = i
        while (j + 1 < len(idx)
               and idx[j + 1] == idx[j] + 1
               and int(limpio.loc[idx[j + 1], "eventos"]) == int(limpio.loc[idx[i], "eventos"])):
            j += 1
        n_ev = int(limpio.loc[idx[i], "eventos"])
        k_i, k_j = float(limpio.loc[idx[i], "k"]), float(limpio.loc[idx[j], "k"])
        # Un conteo de 0 eventos tambien es "estable", pero no es un
        # resultado: significa que el umbral se comio todo.
        if n_ev > 0 and (j - i + 1) >= min_puntos and k_j / k_i >= factor_min - 1e-9:
            mesetas.append((float(limpio.loc[idx[i], "k"]),
                            float(limpio.loc[idx[j], "k"]), n_ev, j - i + 1))
        i = j + 1

    if not mesetas:
        if (e["falsos_control"] == 0).sum() == 0:
            motivo = "ningun umbral da 0 falsos sobre la senal invertida"
        else:
            motivo = ("el conteo no se estabiliza en ningun tramo con 0 falsos: "
                      "no hay meseta")
        return {"k": None, "hay_meseta": False, "motivo": motivo}

    k_lo, k_hi, n_ev, n_pts = mesetas[0]      # la de k mas bajo
    # k en el centro geometrico de la meseta, tomado de la grilla.
    ks_meseta = e["k"][(e["k"] >= k_lo) & (e["k"] <= k_hi)].to_numpy(float)
    k_centro = float(ks_meseta[np.argmin(np.abs(np.log(ks_meseta) - 0.5 * np.log(k_lo * k_hi)))])
    otras = ""
    if len(mesetas) > 1:
        otras = ("; OTRAS MESETAS: "
                 + ", ".join(f"{m[2]} ev en k={m[0]:g}..{m[1]:g}" for m in mesetas[1:]))
    return {"k": k_centro, "n_eventos": n_ev, "k_rango": (k_lo, k_hi),
            "hay_meseta": True, "n_puntos_meseta": n_pts,
            "mesetas": [(m[0], m[1], m[2]) for m in mesetas],
            "motivo": f"meseta de {n_ev} eventos en k={k_lo:g}..{k_hi:g} "
                      f"(x{k_hi / k_lo:.2f}) con 0 falsos de control" + otras}


def promedio_alineado(r: np.ndarray, picos: np.ndarray, fps: float,
                      half_s: float = 1.5):
    """Promedia la senal alineando todos los eventos en su pico."""
    h = int(half_s * fps)
    segs = [r[p - h:p + h + 1] for p in picos if p - h >= 0 and p + h + 1 <= len(r)]
    if not segs:
        return None, None, 0
    segs = np.asarray(segs)
    lag = np.arange(-h, h + 1) / fps
    # nanmean: un fotograma sin medida dentro de la ventana de UN evento no
    # anula ese punto del promedio; se promedia con los eventos que si lo tienen.
    return lag, np.nanmean(segs, axis=0), len(segs)


def _poblaciones(tiempos: np.ndarray, amplitudes: np.ndarray):
    """Separa los eventos en dos poblaciones por amplitud, si las hay.

    Un mismo video puede tener contracciones espontaneas (chicas y rapidas) y
    contracciones estimuladas (grandes y lentas). Promediar las dos juntas da
    una amplitud y un intervalo que no describen a ninguna. El corte se pone
    en el hueco mas grande de las amplitudes ordenadas en escala log, y solo
    se acepta si separa de verdad (razon de medianas >= 2 y al menos 3 eventos
    de cada lado).
    """
    if len(amplitudes) < 6:
        return None
    orden = np.argsort(amplitudes)
    a = amplitudes[orden]
    huecos = np.diff(np.log(np.maximum(a, 1e-9)))
    i = int(np.argmax(huecos))
    if i < 2 or i > len(a) - 4:
        return None
    chica, grande = a[:i + 1], a[i + 1:]
    if np.median(grande) / max(np.median(chica), 1e-9) < 2.0:
        return None

    corte = 0.5 * (a[i] + a[i + 1])
    out = []
    for nombre, sel in (("chicos", amplitudes <= corte), ("grandes", amplitudes > corte)):
        tt = tiempos[sel]
        iv = float(np.median(np.diff(tt))) if len(tt) > 1 else float("nan")
        out.append({"grupo": nombre, "n": int(sel.sum()),
                    "amplitud_mediana_px": float(np.median(amplitudes[sel])),
                    "intervalo_mediano_s": iv,
                    "frecuencia_Hz": (1 / iv) if iv and np.isfinite(iv) and iv > 0 else float("nan"),
                    "t_inicio_s": float(tt.min()), "t_fin_s": float(tt.max())})
    return out


# --------------------------------------------------------------------------
WIN_MIN_S = 2.0           # ventana minima del detrend (s)
WIN_FACTOR = 3.0          # la ventana mide al menos 3 veces el evento mas largo
WIN_ESTABILIDAD = (0.75, 1.0, 1.5)   # el conteo tiene que ser el mismo con estas ventanas


def duracion_eventos(v: np.ndarray, fps: float, win_largo_s: float = 10.0,
                     k_claro: float = 10.0) -> dict:
    """Cuanto duran los eventos CLAROS, medido sin depender de la ventana que
    se va a elegir.

    Se quita la deriva con una ventana LARGA (10 s: no se come eventos de hasta
    ~3 s), se toman los picos con altura y prominencia >= 10 MAD, y para cada
    uno se mide el tramo contiguo en que la senal esta por encima del 10 % del
    pico y de 3 MAD (la misma idea que el onset/offset de la cinetica; el piso
    de 3 MAD evita que el ruido estire el tramo). Un fotograma sin medida corta
    el tramo.
    """
    r = detrend_median(v, fps, win_largo_s)
    r = _signo_evento(r) * r
    m = mad(r)
    if not np.isfinite(m) or m <= 0:
        return {"duracion_max_s": float("nan"), "n_eventos_claros": 0}
    pk = detectar(r, k_claro * m, fps)
    dur = []
    for p in pk:
        nivel = max(0.1 * r[p], 3 * m)
        a = p
        while a - 1 >= 0 and np.isfinite(r[a - 1]) and r[a - 1] > nivel:
            a -= 1
        b = p
        while b + 1 < len(r) and np.isfinite(r[b + 1]) and r[b + 1] > nivel:
            b += 1
        dur.append((b - a + 1) / fps)
    return {"duracion_max_s": float(max(dur)) if dur else float("nan"),
            "n_eventos_claros": len(dur)}


def ventana_deriva(v: np.ndarray, fps: float) -> dict:
    """Ventana de la mediana movil que quita la deriva (Fase 2.2).

    REGLA: al menos 3 veces la duracion del evento mas largo, y nunca menos de
    2 s. La mediana ignora un evento solo si ocupa menos de la mitad de la
    ventana; con 3x queda margen. Si la ventana es corta, la mediana "baja con
    el evento" y al restarla se come la contraccion: medido en Video_491, cuyos
    eventos duran ~1 s, la mediana de 2 s se comia la mitad (H33). En los
    otros cinco videos (eventos de <= 0.6 s) da 2 s, como antes.
    """
    d = duracion_eventos(v, fps)
    dmax = d["duracion_max_s"]
    win = WIN_MIN_S if not np.isfinite(dmax) else max(WIN_MIN_S, WIN_FACTOR * dmax)
    win = float(np.ceil(win * 10) / 10)          # a la decima de segundo, hacia arriba
    return {"win_s": win, **d}


def _contar(v, fps, win_s, sep_s):
    """Conteo con meseta para una ventana dada (control de estabilidad)."""
    r = detrend_median(v, fps, win_s)
    r = _signo_evento(r) * r
    sel = elegir_k_meseta(escaneo_estabilidad(r, fps, sep_s=sep_s))
    return sel["n_eventos"] if sel["hay_meseta"] else None


def analizar(df: pd.DataFrame, canal: str, k: float | None, win_s: float,
             sep_s: float, half_s: float, separar: bool = True,
             min_captura: float = 0.75,
             min_frames_cinetica: int = cin.MIN_FRAMES,
             frecuencia_estimulo=None) -> dict:
    t = df["time_s"].to_numpy(float)
    fps = 1.0 / float(np.median(np.diff(t)))

    if canal not in df.columns:
        raise SystemExit(
            f"La serie no tiene la columna '{canal}'. Si el xlsx es de una version "
            f"vieja del pipeline, hay que reprocesar el video: 'center_px' se agrego "
            f"despues.")

    v = df[canal].to_numpy(float)
    # win_s = None -> regla automatica (ventana >= 3 x evento mas largo, min 2 s).
    vent = ventana_deriva(v, fps)
    win_auto = win_s is None
    if win_auto:
        win_s = vent["win_s"]
    r = detrend_median(v, fps, win_s)
    signo = _signo_evento(r)
    r = signo * r                       # ahora los eventos van hacia ARRIBA
    m = mad(r)

    estab = escaneo_estabilidad(r, fps, sep_s=sep_s)

    # k = None significa "elegilo vos, con la regla del protocolo".
    sel = elegir_k_meseta(estab)
    if k is None:
        if not sel["hay_meseta"]:
            # Regla 4 del protocolo: sin meseta no se reporta conteo. Se sigue
            # adelante para poder graficar y auditar, pero queda marcado.
            k = float(estab["k"].iloc[len(estab) // 2])
        else:
            k = sel["k"]
        k_auto = True
    else:
        k_auto = False

    picos = detectar(r, k * m, fps, sep_s)

    # --- control de estabilidad frente a la ventana (Fase 2.2) --------------
    # Mismo criterio que la meseta de k: un conteo que cambia con una eleccion
    # arbitraria (la ventana del detrend) no es un resultado.
    conteos_win = {round(f * win_s, 2): _contar(v, fps, f * win_s, sep_s) for f in WIN_ESTABILIDAD}
    estable_win = (len(set(conteos_win.values())) == 1
                   and None not in conteos_win.values())

    # --- grosor: se mide, no se usa para detectar -------------------------
    rg = detrend_median(df["thickness_px"].to_numpy(float), fps, win_s)
    mg = mad(rg)
    lag, prom_g, n_ev = promedio_alineado(rg, picos, fps, half_s)
    _, prom_c, _ = promedio_alineado(r, picos, fps, half_s)

    res = {
        "canal": canal, "fps": fps, "n_frames": len(t), "duracion_s": float(t[-1] - t[0]),
        "signo": signo, "ruido_canal_px": m, "ruido_grosor_px": mg,
        "n_eventos": len(picos), "estabilidad": estab,
        "k_usado": float(k), "k_automatico": bool(k_auto),
        "hay_meseta": bool(sel["hay_meseta"]),
        "meseta_motivo": sel["motivo"],
        "meseta_k_rango": (f"{sel['k_rango'][0]:g}-{sel['k_rango'][1]:g}"
                           if sel.get("k_rango") else None),
        "conteo_reportable": bool(sel["hay_meseta"]) and estable_win,
        "_k_rango": sel.get("k_rango"),
        "_mesetas": sel.get("mesetas", []),
        "_t": t, "_r": r, "_picos": picos, "_lag": lag,
        "_prom_g": prom_g, "_prom_c": prom_c, "_n_prom": n_ev,
    }

    _SEPARAR, _MINCAP = separar, min_captura
    # (El aviso de fusion "picos_con_sep_menor" se quito en la Fase 2.2: con la
    # deteccion por prominencia ya no hay separacion minima que funda eventos.)

    # --- cinetica por evento: TTP, RT50, amplitud relativa -----------------
    # Se calcula ANTES del ritmo porque el ritmo usa el INICIO de cada
    # contraccion (onset, cruce del 10 %) como su instante (Fase 3, R1). El
    # grosor en reposo es la misma mediana movil que quita la deriva, evaluada
    # sobre el grosor crudo.
    grosor_crudo = df["thickness_px"].to_numpy(float)
    grosor_reposo = grosor_crudo - rg
    ev = cin.cinetica_eventos(t, r, picos, m, grosor_reposo=grosor_reposo,
                              ventana_s=half_s, min_frames=min_frames_cinetica)

    if len(picos):
        res["tiempos_s"] = t[picos]
        res["intervalo_mediano_s"] = (float(np.median(np.diff(t[picos])))
                                      if len(picos) > 1 else float("nan"))
        res["amplitud_traslacion_px"] = float(np.median(r[picos]))
        res["poblaciones"] = _poblaciones(t[picos], r[picos])
        if _SEPARAR and len(picos) >= 4:
            # R1: el instante de cada latido es su INICIO; si no tiene inicio
            # medible (hueco, o no cruza el 10 % antes del pico vecino), su pico.
            onset = ev["onset_s"].to_numpy(float)
            t_ritmo = np.where(np.isfinite(onset), onset, t[picos])
            res["ritmo"] = rs.separar(t_ritmo, r[picos], duracion_s=float(t[-1] - t[0]),
                                      resolucion_s=1.0 / fps, min_captura=_MINCAP,
                                      frecuencia_configurada_Hz=frecuencia_estimulo)
            res["ritmo"]["fuente_tiempo"] = (f"inicio (onset 10 %) en {int(np.isfinite(onset).sum())} "
                                             f"de {len(picos)} eventos; pico en el resto")
            res["fps_medido"] = fps
    if prom_g is not None and n_ev:
        ruido_prom = mg / np.sqrt(n_ev)
        i = int(np.argmin(prom_g))
        i0 = int(np.argmin(np.abs(lag)))          # frame del pico de traslacion
        pico_c = float(np.max(prom_c)) if prom_c is not None else float("nan")

        res["adelgazamiento_px"] = float(-prom_g[i])
        res["adelgazamiento_sigma"] = float(abs(prom_g[i]) / ruido_prom) if ruido_prom else float("nan")
        res["retardo_adelgazamiento_s"] = float(lag[i])
        # CON SIGNO, a proposito. `adelgazamiento_px` vale -prom_g[i]: es
        # positivo cuando el gel adelgaza y NEGATIVO cuando engruesa. Si el
        # cociente toma la magnitud, un engrosamiento se lee en la tabla como
        # un adelgazamiento del mismo tamano. Paso con Video_268 (-0.0815 px
        # reportado como +6.11%) y Video_466 (-0.4063 px como +11.08%).
        res["cociente_adelg_trasl_pct"] = (100 * (-prom_g[i]) / pico_c) if pico_c else float("nan")

        # Medida ROBUSTA: promedio de los 3 frames posteriores al pico.
        # POR QUE: justo en el frame de maxima velocidad el grosor medido da un
        # salto POSITIVO (el borde se emborrona por el movimiento y los dos
        # bordes se "abren"). Ese frame no es adelgazamiento, es un artefacto de
        # motion blur, y contamina el minimo si cae cerca. Promediar la cola
        # posterior lo evita.
        j0, j1 = i0 + 1, min(i0 + 4, len(prom_g))
        cola = prom_g[j0:j1]
        if len(cola):
            res["adelgazamiento_robusto_px"] = float(-cola.mean())
            res["adelgazamiento_robusto_sigma"] = (
                float(abs(cola.mean()) / (ruido_prom / np.sqrt(len(cola)))) if ruido_prom else float("nan"))
            # Con signo, por el mismo motivo que arriba.
            res["cociente_robusto_pct"] = (100 * (-cola.mean()) / pico_c) if pico_c else float("nan")

        # Aviso de motion blur: excursion POSITIVA del grosor cerca del pico.
        ven = prom_g[max(0, i0 - 2):min(len(prom_g), i0 + 2)]
        if len(ven) and ven.max() > 3 * ruido_prom:
            res["blur_px"] = float(ven.max())
            res["blur_sigma"] = float(ven.max() / ruido_prom)

    # --- grupo de cada evento (del ritmo) en la tabla de cinetica ------------
    if len(ev) and res.get("ritmo") is not None:
        ev.insert(1, "grupo", res["ritmo"]["grupo_por_evento"])
        ev.insert(2, "tren", res["ritmo"]["tren_por_evento"])
    res["_cinetica"] = ev
    # Resumen POR GRUPO (C1, H40). La cifra principal (las claves sueltas de
    # `res`, que van a la hoja resumen) es la de los estimulados si hay tren, y
    # la de todos los eventos si no lo hay. Los dudosos solo entran en "todos".
    conjuntos = [("todos", ev)]
    if len(ev) and "grupo" in ev:
        for g in ("estimulados", "espontaneos"):
            sub = ev[ev["grupo"] == g]
            if len(sub):
                conjuntos.append((g, sub))
    filas_cin = []
    for nombre, sub in conjuntos:
        rr = cin.resumir(sub, conteo_reportable=res["conteo_reportable"],
                         min_frames=min_frames_cinetica)
        filas_cin.append({"grupo": nombre, **rr})
    res["_cinetica_grupos"] = pd.DataFrame(filas_cin)
    principal = ("estimulados" if res.get("ritmo") is not None and res["ritmo"]["hay_estimulacion"]
                 else "todos")
    res["cinetica_grupo_principal"] = principal
    res.update({k: v for k, v in next(f for f in filas_cin if f["grupo"] == principal).items()
                if k != "grupo"})

    # --- fotogramas sin medida ----------------------------------------------
    # Van al final para no reordenar las columnas existentes. Un fotograma NaN
    # (REJECTED) no se inventa ni anula el analisis (src/estadistica.py), pero
    # tiene que quedar a la vista: si faltan muchos, o justo en un evento, el
    # conteo y la cinetica de ese tramo no son confiables.
    sin_medida = ~np.isfinite(v)
    res["fotogramas_sin_medida"] = int(sin_medida.sum())
    res["fotogramas_sin_medida_pct"] = float(100.0 * sin_medida.mean()) if len(v) else 0.0
    if "frame_quality" in df.columns:
        res["fotogramas_low_quality"] = int((df["frame_quality"] == "LOW_QUALITY").sum())
    # Un evento con un fotograma sin medida en su pico o al lado tiene el
    # instante (y la amplitud) inciertos: el maximo verdadero pudo estar en el
    # hueco. Se detecta igual, pero queda marcado. Medido: un hueco de 15
    # fotogramas sobre el evento de 24.32 s de Video_466 lo corre a 24.08 s.
    junto = np.array([bool(sin_medida[max(0, p - 1):p + 2].any()) for p in picos], dtype=bool)
    res["_junto_a_hueco"] = junto
    res["eventos_junto_a_hueco"] = int(junto.sum())
    # Fase 4 (H11): un evento a menos de media ventana del detrend del inicio o
    # del fin del video tiene la linea base estimada con media ventana. Se
    # detecta igual (en 063, t = 0.31 s es una contraccion real: se ve en la
    # senal cruda y por intensidad), pero queda marcado.
    t_ok = t[np.isfinite(t)]
    borde = np.array([bool(t[p] - t_ok[0] < win_s / 2 or t_ok[-1] - t[p] < win_s / 2)
                      for p in picos], dtype=bool)
    res["_junto_al_borde"] = borde
    res["eventos_junto_al_borde"] = int(borde.sum())

    # --- Fase 2.2: ventana, estabilidad y todas las mesetas ------------------
    res["win_s_usado"] = float(win_s)
    res["win_s_automatico"] = bool(win_auto)
    res["duracion_evento_max_s"] = vent["duracion_max_s"]
    res["ventana_corta"] = bool(np.isfinite(vent["duracion_max_s"])
                                and win_s < WIN_FACTOR * vent["duracion_max_s"])
    res["conteo_por_ventana"] = " | ".join(
        f"{w:g} s: {'sin meseta' if n is None else n}" for w, n in conteos_win.items())
    res["conteo_estable_ventana"] = bool(estable_win)
    res["mesetas"] = "; ".join(f"{m[2]} ev en k={m[0]:g}-{m[1]:g}" for m in res["_mesetas"]) or None
    if not res["conteo_reportable"]:
        if not sel["hay_meseta"]:
            res["motivo_no_reportable"] = "no hay meseta en el escaneo de k"
        else:
            res["motivo_no_reportable"] = ("el conteo depende de la ventana del detrend ("
                                           + res["conteo_por_ventana"] + ")")

    # --- H54 (Fase 3): ruido de cada borde por separado ----------------------
    # El centro promedia los dos bordes 50/50. Si uno es mucho mas ruidoso que
    # el otro (medido: 063 inferior 3x, 268 superior 2x), un borde solo puede
    # tener mas SNR que el centro. No cambia el observable (los dos bordes se
    # mueven casi lo mismo y el conteo no cambia), pero un borde mucho mas
    # ruidoso suele senalar un problema de ROI o de ese borde: queda a la vista.
    for col, clave in (("y_top_px", "ruido_borde_sup_px"), ("y_bottom_px", "ruido_borde_inf_px")):
        res[clave] = (float(mad(detrend_median(df[col].to_numpy(float), fps, win_s)))
                      if col in df.columns else float("nan"))
    rs_, ri_ = res["ruido_borde_sup_px"], res["ruido_borde_inf_px"]
    res["cociente_ruido_bordes"] = (float(max(rs_, ri_) / min(rs_, ri_))
                                    if np.isfinite(rs_) and np.isfinite(ri_) and min(rs_, ri_) > 0
                                    else float("nan"))
    return res


def imprimir(nombre: str, a: dict) -> None:
    print("=" * 74)
    print(f"{nombre}   ({a['n_frames']} frames, {a['duracion_s']:.1f} s, {a['fps']:.2f} fps)")
    print(f"  canal de deteccion: {a['canal']}  "
          f"(eventos hacia {'arriba' if a['signo'] > 0 else 'abajo'} en la imagen)")
    print(f"  ruido del canal: {a['ruido_canal_px']:.4f} px | "
          f"ruido del grosor: {a['ruido_grosor_px']:.4f} px")
    if np.isfinite(a.get("cociente_ruido_bordes", float("nan"))):
        print(f"  ruido por borde: sup {a['ruido_borde_sup_px']:.4f} px | "
              f"inf {a['ruido_borde_inf_px']:.4f} px (cociente {a['cociente_ruido_bordes']:.2f})")
    if a.get("fotogramas_sin_medida"):
        print(f"  AVISO: {a['fotogramas_sin_medida']} fotograma(s) sin medida "
              f"({a['fotogramas_sin_medida_pct']:.2f} %, NaN / REJECTED). No se interpolan: no "
              f"cuentan para el ruido ni pueden ser picos. Si caen dentro de un evento, su "
              f"TTP/RT50 queda sin medir.")
    if a.get("eventos_junto_a_hueco"):
        print(f"  AVISO: {a['eventos_junto_a_hueco']} evento(s) con un fotograma sin medida en el "
              f"pico o al lado: su instante y su amplitud son inciertos (columna "
              f"'junto_a_hueco' de la hoja eventos_*).")
    if a.get("eventos_junto_al_borde"):
        print(f"  nota: {a['eventos_junto_al_borde']} evento(s) a menos de media ventana del "
              f"detrend del inicio o del fin del video: su linea base se estima con media "
              f"ventana (columna 'junto_al_borde' de la hoja eventos_*).")
    if a.get("fotogramas_low_quality"):
        print(f"  nota: {a['fotogramas_low_quality']} fotograma(s) LOW_QUALITY entran al analisis "
              f"como los demas.")
    print()
    print("  estabilidad del umbral (falsos = mismo detector sobre la senal invertida)")
    print("      %5s %12s %10s %16s" % ("k", "umbral_px", "eventos", "falsos_control"))
    for _, f in a["estabilidad"].iterrows():
        print("      %5g %12.4f %10d %16d" % (f.k, f.umbral_px, f.eventos, f.falsos_control))
    print()
    if not a["n_eventos"]:
        print("  NO se detectaron eventos con el umbral elegido.")
        return
    origen = "elegido automaticamente" if a.get("k_automatico") else "fijado a mano"
    dmax = a.get("duracion_evento_max_s", float("nan"))
    print(f"  VENTANA del detrend: {a['win_s_usado']:g} s "
          f"({'automatica' if a.get('win_s_automatico') else 'fijada a mano'}; evento claro "
          f"mas largo {dmax:.2f} s)" if np.isfinite(dmax) else
          f"  VENTANA del detrend: {a['win_s_usado']:g} s (no hay eventos claros para medir su duracion)")
    if a.get("ventana_corta"):
        print(f"    AVISO: la ventana es menor que 3 x el evento mas largo: la mediana puede "
              f"comerse parte de la contraccion.")
    print(f"    conteo con otras ventanas: {a['conteo_por_ventana']}"
          + ("" if a.get("conteo_estable_ventana") else "   <- CAMBIA CON LA VENTANA"))
    print(f"  UMBRAL: k = {a['k_usado']:g}  ({origen})")
    print(f"    {a['meseta_motivo']}")
    if not a.get("conteo_reportable"):
        print(f"    >>> NO REPORTABLE: {a.get('motivo_no_reportable', '')}.")
        print("        Los eventos de abajo son para auditar, no para tabular.")
    print(f"  EVENTOS: {a['n_eventos']}"
          + ("" if a.get("conteo_reportable") else "   [NO REPORTABLE]"))
    print("    tiempos (s): " + ", ".join(f"{x:.2f}" for x in a["tiempos_s"]))
    if a["n_eventos"] > 1:
        iv = a["intervalo_mediano_s"]
        print(f"    intervalo mediano: {iv:.3f} s  ({1 / iv:.4f} Hz)")
    print(f"    traslacion (amplitud mediana): {a['amplitud_traslacion_px']:.3f} px")
    if a.get("poblaciones"):
        print("    DOS POBLACIONES de eventos (separadas por amplitud):")
        print("        %-8s %4s %14s %14s %10s %14s" % (
            "grupo", "n", "amplitud_px", "intervalo_s", "Hz", "ventana_s"))
        for g in a["poblaciones"]:
            print("        %-8s %4d %14.3f %14.3f %10.2f %6.1f - %-6.1f" % (
                g["grupo"], g["n"], g["amplitud_mediana_px"], g["intervalo_mediano_s"],
                g["frecuencia_Hz"], g["t_inicio_s"], g["t_fin_s"]))
    rit = a.get("ritmo")
    if rit is not None:
        print()
        print(f"    RITMO (busqueda {rit['modo_busqueda']}; instante = {rit.get('fuente_tiempo')})")
        for _, f in rit["trenes"].iterrows():
            extra = (f"  [z={f['z']:.1f}, p={f['p_valor']:.4f}, {int(f['n_eventos_tren'])}/"
                     f"{int(f['n_ranuras'])} ranuras]" if "z" in f and np.isfinite(f.get("z", np.nan)) else "")
            print(f"       tren {int(f['tren'])} ({f['busqueda']}): {f['veredicto']}{extra}")
        if not rit["hay_estimulacion"]:
            print("       -> todos los eventos se toman como espontaneos.")
        else:
            print(f"    TREN ESTIMULADO (enganche de fase, z={rit['z']:.1f}, p={rit['p_valor']:.4f})")
            print(f"       periodo    : {rit['periodo_s']:.5f} +- {rit['periodo_err_s']:.5f} s")
            print(f"       frecuencia : {rit['frecuencia_Hz']:.5f} +- {rit['frecuencia_err_Hz']:.6f} Hz")
            print(f"       jitter     : {rit['jitter_s']*1000:.1f} ms"
                  + ("  (por debajo de un fotograma: es el piso de resolucion)"
                     if rit.get("jitter_limitado_por_resolucion") else ""))
            print(f"       captura    : {rit['tasa_captura_pct']:.0f}%  "
                  f"({rit['n_estimulados']}/{rit['n_ranuras']} ranuras), "
                  f"tren de {rit['tren_inicio_s']:.1f} a {rit['tren_fin_s']:.1f} s")
            for _, x in rit["sacados_tiempo_amplitud"].iterrows():
                print(f"       SACADO DEL TREN: evento en {x['tiempo_s']:.3f} s, desvio "
                      f"{1000 * x['desvio_s']:+.0f} ms y amplitud {x['amplitud']:.2f} px contra "
                      f"{x['amplitud_mediana_tren']:.2f} px del tren (falla en tiempo Y amplitud)")
            if rit.get("n_estimulados_dudosos"):
                print(f"       DUDOSOS    : {rit['n_estimulados_dudosos']} evento(s) cerca de una "
                      f"ranura pero fuera de tolerancia, con amplitud compatible: probablemente "
                      f"latidos del tren con el instante corrido.")
        print("    Grupos (la amplitud NO se uso para clasificar; que difiera es evidencia aparte):")
        if "resumen_grupos" not in rit or rit["resumen_grupos"] is None:
            # Pasa cuando no se detecto tren y no hay grupos que resumir: es
            # justo el caso de un video sin eventos, donde mas importa que el
            # reporte salga igual en vez de abortar.
            print("    (sin resumen de grupos: no se separo en estimulados/espontaneos)")
            imprimir_cinetica(a)
            return
        for ln in rit["resumen_grupos"].to_string(index=False).split("\n"):
            print("       " + ln)
    if "picos_con_sep_menor" in a:
        print(f"    AVISO: con una separacion minima menor apareceria(n) "
              f"{a['picos_con_sep_menor']} pico(s) en vez de {a['n_eventos']}. "
              f"--sep-s se queda con el pico MAS ALTO de cada ventana, asi que si hay "
              f"un tren rapido lo esta borrando. Baja --sep-s.")
    if "adelgazamiento_px" in a:
        print(f"    adelgazamiento (promedio de {a['_n_prom']} eventos alineados)")
        print(f"       minimo:  {a['adelgazamiento_px']:.4f} px  "
              f"({a['adelgazamiento_sigma']:.1f} sigma, a {a['retardo_adelgazamiento_s']:+.2f} s del pico)"
              f"   = {a['cociente_adelg_trasl_pct']:.1f}% de la traslacion")
        if "adelgazamiento_robusto_px" in a:
            print(f"       robusto: {a['adelgazamiento_robusto_px']:.4f} px  "
                  f"({a['adelgazamiento_robusto_sigma']:.1f} sigma, 3 frames post-pico)"
                  f"   = {a['cociente_robusto_pct']:.1f}% de la traslacion")
        if "blur_sigma" in a:
            print(f"    AVISO: el grosor da un salto POSITIVO de {a['blur_px']:.3f} px "
                  f"({a['blur_sigma']:.1f} sigma) en el frame mas rapido. Eso no es "
                  f"engrosamiento: es motion blur (el borde se emborrona y los dos bordes "
                  f"se abren). Usa la medida robusta, no el minimo.")
    imprimir_cinetica(a)


def imprimir_cinetica(a: dict) -> None:
    ev = a.get("_cinetica")
    if ev is None or not len(ev):
        return
    print()
    print(f"    CINETICA (nivel onset/offset {cin.NIVEL_ONSET:.0%} de A, RT50 al "
          f"{cin.NIVEL_RT:.0%}; medible si >= {a['cinetica_min_frames']} fotogramas)")
    print(f"       cifra principal: {a.get('cinetica_grupo_principal', 'todos')} "
          f"({a.get('n_eventos_cinetica', len(ev))} eventos)")
    for m, nom in (("ttp", "TTP "), ("rt50", "RT50")):
        if not a.get(f"{m}_n_eventos"):
            print(f"       {nom}: no se pudo medir en ningun evento")
            continue
        fr = a[f"{m}_frames_mediana"]
        lo, hi = 1000 * a[f"{m}_cota_inf_s"], 1000 * a[f"{m}_cota_sup_s"]
        if a[f"{m}_reportable"]:
            print(f"       {nom}: {1000 * a[f'{m}_s']:.0f} ms (mediana de {a[f'{m}_n_medibles']} "
                  f"medibles, IQR {a[f'{m}_iqr_s']} s)"
                  f"  | {fr:g} fotogramas | intervalo mediano [{lo:.0f}, {hi:.0f}] ms")
        elif not a.get("conteo_reportable"):
            print(f"       {nom}: NO REPORTABLE -> el conteo de eventos no es reportable "
                  f"(sin meseta); {fr:g} fotogramas, intervalo mediano [{lo:.0f}, {hi:.0f}] ms "
                  f"solo para auditar")
        else:
            print(f"       {nom}: NO MEDIBLE -> {nom.strip()} < {hi:.0f} ms"
                  f"  ({fr:g} fotogramas: es el intervalo de muestreo, no la biologia)")
    if np.isfinite(a.get("amplitud_relativa_pct", np.nan)):
        print(f"       amplitud relativa: {a['amplitud_relativa_pct']:.2f} % del grosor en reposo"
              + (f"  (IQR {a['amplitud_relativa_iqr_pct']} %)"
                 if a.get("amplitud_relativa_iqr_pct") else ""))
    if a["cinetica_motivo"] != "TTP y RT50 medibles":
        print(f"       motivo: {a['cinetica_motivo']}")
    cg = a.get("_cinetica_grupos")
    if cg is not None and len(cg) > 1:
        def _ms(x):
            return f"{1000 * x:.0f}" if np.isfinite(x) else "-"
        print("       por grupo:   grupo         n   TTP ms  RT50 ms  amplitud relativa %")
        for _, f in cg.iterrows():
            print(f"                    {f['grupo']:12s} {int(f['n_eventos_cinetica']):3d}  "
                  f"{_ms(f['ttp_s']):>6s}  {_ms(f['rt50_s']):>7s}  {f['amplitud_relativa_pct']:.2f}")


def graficar(resultados, out_png: Path) -> None:
    n = len(resultados)
    fig, axes = plt.subplots(n, 2, figsize=(13, 3.1 * n), squeeze=False,
                             gridspec_kw={"width_ratios": [2.4, 1]})
    for i, (nombre, a) in enumerate(resultados):
        ax, ax2 = axes[i, 0], axes[i, 1]
        ax.plot(a["_t"], a["_r"], color="#1f77b4", lw=0.7, label=a["canal"])
        if a["n_eventos"]:
            ax.plot(a["_t"][a["_picos"]], a["_r"][a["_picos"]], "v", color="crimson",
                    ms=7, label=f"{a['n_eventos']} eventos")
        ax.axhline(0, color="gray", lw=0.6)
        ax.set_ylabel(f"{a['canal']} (sin deriva, px)")
        ax.set_title(nombre, fontsize=10)
        ax.legend(fontsize=8, loc="upper right")
        ax.grid(alpha=0.3)

        if a["_lag"] is not None:
            ax2.plot(a["_lag"], a["_prom_c"], color="#1f77b4", lw=1.4, label="traslacion")
            ax2b = ax2.twinx()
            ax2b.plot(a["_lag"], a["_prom_g"], color="crimson", lw=1.4, label="grosor")
            ax2b.axhline(0, color="crimson", lw=0.5, ls=":")
            ax2.set_xlabel("t respecto del pico (s)")
            ax2.set_ylabel("traslacion (px)", color="#1f77b4")
            ax2b.set_ylabel("grosor (px)", color="crimson")
            ax2.set_title(f"promedio de {a['_n_prom']} eventos", fontsize=9)
            ax2.grid(alpha=0.3)
    axes[-1, 0].set_xlabel("Tiempo (s)")
    fig.tight_layout()
    fig.savefig(out_png, dpi=140)
    plt.close(fig)


def graficar_ritmo(resultados, out_png: Path):
    """Una fila por serie: eventos coloreados por grupo, y el error de cada
    latido estimulado respecto de su ranura."""
    filas = [(n, a) for n, a in resultados if a.get("ritmo") is not None]
    if not filas:
        return None
    fig, axes = plt.subplots(len(filas), 2, figsize=(13, 3.0 * len(filas)), squeeze=False,
                             gridspec_kw={"width_ratios": [3, 1]})
    for i, (nombre, a) in enumerate(filas):
        rit, ax, ax2 = a["ritmo"], axes[i, 0], axes[i, 1]
        t, r, pk = a["_t"], a["_r"], a["_picos"]
        ax.plot(t, r, color="#bdc3c7", lw=0.6, zorder=1)
        colores = {"estimulados": "#c0392b", "estimulados_dudosos": "#e67e22",
                   "espontaneos": "#2980b9"}
        for grupo, col in colores.items():
            idx = rit.get(grupo if grupo != "espontaneos" else "espontaneos",
                          np.array([], int))
            if len(idx) == 0:
                continue
            ax.plot(t[pk][idx], r[pk][idx], "v", color=col, ms=8, zorder=5,
                    label=f"{grupo} (n={len(idx)})")
        if rit["hay_estimulacion"]:
            for _, g in rit["grilla"].iterrows():
                ax.axvline(g.t_esperado_s, color="#c0392b", lw=0.8, ls="--", alpha=0.5, zorder=0)
        ax.set_title(f"{nombre}" + (f"   tren a {rit['frecuencia_Hz']:.4f} Hz "
                                    f"(T={rit['periodo_s']:.4f} s), captura "
                                    f"{rit['tasa_captura_pct']:.0f}%"
                                    if rit["hay_estimulacion"] else "   sin tren periodico"),
                     fontsize=10)
        ax.set_ylabel("senal sin deriva (px)", fontsize=8)
        ax.legend(fontsize=7, loc="upper right"); ax.grid(alpha=0.25)

        if rit["hay_estimulacion"] and len(rit["grilla"]):
            ax2.axhline(0, color="gray", lw=0.8)
            for tr_id, g in rit["grilla"].groupby("tren"):
                ax2.plot(g.ranura, 1000 * g.error_s, "o-", ms=4, label=f"tren {tr_id}")
            if rit["grilla"]["tren"].nunique() > 1:
                ax2.legend(fontsize=7)
            ax2.axhspan(-1000 * rit["tolerancia_s"], 1000 * rit["tolerancia_s"],
                        color="#c0392b", alpha=0.10)
            ax2.set_xlabel("ranura del tren"); ax2.set_ylabel("error (ms)", fontsize=8)
            ax2.set_title("desvio de cada latido", fontsize=9); ax2.grid(alpha=0.25)
        else:
            ax2.axis("off")
    axes[-1, 0].set_xlabel("Tiempo (s)")
    fig.tight_layout(); fig.savefig(out_png, dpi=140); plt.close(fig)
    return out_png


def graficar_estabilidad(resultados, out_png: Path):
    """Figura 05: el escaneo del umbral que DECIDE el conteo (chequeo de
    aceptacion 3), una fila por serie.

    Azul: eventos detectados para cada k. Rojo: "falsos", el mismo detector
    sobre la senal invertida. Franja verde: la meseta elegida (conteo
    constante con 0 falsos). Vertical: el k usado. Sin meseta, el titulo dice
    NO REPORTABLE.

    Reemplaza a la 05 que generaba analyze_contractions.py, que graficaba el
    escaneo de OTRO detector (event_detection.py, borrado el 2026-10-01) y no
    mostraba los falsos de control.
    """
    fig, axes = plt.subplots(len(resultados), 1, figsize=(7.5, 3.2 * len(resultados)),
                             squeeze=False)
    for i, (nombre, a) in enumerate(resultados):
        ax = axes[i, 0]
        e = a["estabilidad"]
        ax.plot(e["k"], e["eventos"], "o-", color="#1f77b4", lw=1.5, label="eventos")
        ax.plot(e["k"], e["falsos_control"], "s--", color="#c0392b", lw=1.2, ms=5,
                label="falsos (senal invertida)")
        if a.get("_k_rango"):
            ax.axvspan(a["_k_rango"][0], a["_k_rango"][1], color="#27ae60", alpha=0.15,
                       label=f"meseta k={a['_k_rango'][0]:g}-{a['_k_rango'][1]:g}")
        etiqueta = (f"k usado = {a['k_usado']:g}" if a.get("conteo_reportable")
                    else f"k solo para auditar = {a['k_usado']:g}")
        ax.axvline(a["k_usado"], color="black", ls=":", lw=1, label=etiqueta)
        ax.set_xscale("log")
        ticks = [3, 4, 5, 6, 8, 10, 12, 15, 20, 24]
        ax.set_xticks(ticks); ax.set_xticklabels([f"{k:g}" for k in ticks]); ax.minorticks_off()
        ax.set_xlabel("k (umbral = k x ruido)"); ax.set_ylabel("numero de picos")
        veredicto = (f"{a['n_eventos']} eventos, reportable" if a.get("conteo_reportable")
                     else f"NO REPORTABLE: {a.get('motivo_no_reportable', '')}")
        if len(a.get("_mesetas", [])) > 1:
            for (k0, k1, n) in a["_mesetas"][1:]:
                ax.axvspan(k0, k1, color="#f39c12", alpha=0.12)
            veredicto += f"  (otra meseta: {a['_mesetas'][1][2]} ev, en naranja)"
        ax.set_title(f"{nombre}   {veredicto}", fontsize=9)
        ax.grid(alpha=0.3, which="both"); ax.legend(fontsize=7, loc="upper right")
    fig.tight_layout(); fig.savefig(out_png, dpi=140); plt.close(fig)
    return out_png


def graficar_cinetica(resultados, out_png: Path):
    """Diagnostico visual de TTP/RT50 (regla "cero cajas negras").

    Izquierda: cada evento normalizado por su amplitud, en FOTOGRAMAS respecto
    del pico y con un punto por fotograma, para que se vea cuantas muestras
    tiene la subida. Lineas en el 10 % y el 50 %.
    Derecha: TTP y RT50 de cada evento con su intervalo [min, max]; la franja
    gris es la zona "no medible" (menos de min_frames fotogramas).
    """
    filas = [(n, a) for n, a in resultados
             if a.get("_cinetica") is not None and len(a["_cinetica"])]
    if not filas:
        return None
    fig, axes = plt.subplots(len(filas), 2, figsize=(13, 3.2 * len(filas)), squeeze=False,
                             gridspec_kw={"width_ratios": [1.6, 1]})
    for i, (nombre, a) in enumerate(filas):
        ax, ax2 = axes[i, 0], axes[i, 1]
        r, pk, ev = a["_r"], a["_picos"], a["_cinetica"]
        h = 15
        lags = np.arange(-h, h + 1)
        trazas = []
        for p in pk:
            if p - h < 0 or p + h >= len(r) or r[p] <= 0:
                continue
            y = r[p - h:p + h + 1] / r[p]
            trazas.append(y)
            ax.plot(lags, y, "-", color="#95a5a6", lw=0.6, alpha=0.7)
        if trazas:
            ax.plot(lags, np.median(trazas, axis=0), "o-", color="#1f77b4", lw=1.6, ms=3.5,
                    label="mediana de eventos")
        ax.axhline(cin.NIVEL_ONSET, color="#27ae60", ls="--", lw=0.9, label="10 % (onset/offset)")
        ax.axhline(cin.NIVEL_RT, color="#c0392b", ls="--", lw=0.9, label="50 % (RT50)")
        ax.axvline(0, color="gray", lw=0.6)
        ax.set_xlabel("fotogramas respecto del pico")
        ax.set_ylabel("senal / amplitud")
        ax.set_ylim(-0.4, 1.3)
        txt = []
        for m, nom in (("ttp", "TTP"), ("rt50", "RT50")):
            if not a.get(f"{m}_n_eventos"):
                continue
            if a[f"{m}_reportable"]:
                txt.append(f"{nom} = {1000 * a[f'{m}_s']:.0f} ms")
            else:
                txt.append(f"{nom} < {1000 * a[f'{m}_cota_sup_s']:.0f} ms (no medible)")
        ax.set_title(f"{nombre}   " + "   ".join(txt), fontsize=9)
        ax.legend(fontsize=7, loc="upper right"); ax.grid(alpha=0.25)

        mf = a["cinetica_min_frames"] / a["fps"]
        ax2.axhspan(0, 1000 * mf, color="gray", alpha=0.15, label=f"< {a['cinetica_min_frames']} fotogramas")
        for m, col, dx in (("ttp", "#1f77b4", -0.12), ("rt50", "#c0392b", 0.12)):
            x = ev["evento"].to_numpy(float) + dx
            y = 1000 * ev[f"{m}_s"].to_numpy(float)
            lo = 1000 * ev[f"{m}_min_s"].to_numpy(float)
            hi = 1000 * ev[f"{m}_max_s"].to_numpy(float)
            ok = np.isfinite(y)
            ax2.errorbar(x[ok], y[ok], yerr=[y[ok] - lo[ok], hi[ok] - y[ok]], fmt="o",
                         color=col, ms=4, capsize=2, lw=0.9, label=m.upper())
        ax2.set_xlabel("evento"); ax2.set_ylabel("ms")
        ax2.set_title("cada evento con su intervalo [min, max]", fontsize=9)
        ax2.legend(fontsize=7, loc="upper left", bbox_to_anchor=(1.01, 1.0)); ax2.grid(alpha=0.25)
    fig.tight_layout(); fig.savefig(out_png, dpi=140); plt.close(fig)
    return out_png


def _leer(path: str) -> pd.DataFrame:
    p = Path(path)
    return pd.read_csv(p) if p.suffix == ".csv" else pd.read_excel(p, sheet_name="diagnostics")


def parse_args():
    p = argparse.ArgumentParser(
        description="Detecta contracciones sobre center_px y mide el adelgazamiento "
                    "por promedio de eventos alineados.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    p.add_argument("--input", required=True)
    p.add_argument("--compare", default=None,
                   help="Segunda serie, como control (ideal: un video que ya sabes que contrae).")
    p.add_argument("--canal", default="center_px",
                   help="Observable de DETECCION. 'center_px' = posicion media de la franja "
                        "(sensible a traslacion). 'thickness_px' solo si ya verificaste que "
                        "en tu montaje la contraccion es adelgazamiento puro.")
    p.add_argument("--k", default="auto",
                   help="Umbral en multiplos del ruido. 'auto' (default) lo elige "
                        "dentro de la meseta del escaneo de estabilidad, que es la "
                        "regla del protocolo. Un numero lo fija a mano.")
    p.add_argument("--win-s", default="auto",
                   help="Ventana (s) de la mediana movil que quita la deriva. 'auto' (default): "
                        "al menos 3 veces la duracion del evento mas largo, minimo 2 s. Un numero "
                        "la fija a mano.")
    p.add_argument("--sep-s", type=float, default=None,
                   help="Separacion minima entre eventos (s). APAGADA por defecto: desde la "
                        "Fase 2.2 un evento se separa del vecino por su PROMINENCIA (la senal "
                        "tiene que bajar entre los dos), no por tiempo. Si se da, find_peaks se "
                        "queda con el pico MAS ALTO de cada ventana y borra eventos reales "
                        "seguidos.")
    p.add_argument("--half-s", type=float, default=1.5,
                   help="Semiventana (s) del promedio de eventos alineados.")
    p.add_argument("--frecuencia-estimulo", default=None,
                   nargs="+", type=float,
                   help="Frecuencia(s) (Hz) configurada(s) en el estimulador. Con ella, el tren "
                        "se busca SOLO cerca de esa frecuencia (+-10 %%) y el reporte dice "
                        "'enganchado' o 'no hay enganche'. Si el protocolo cambia de frecuencia, "
                        "pasar todas (ej. 0.1 0.2). Sin ella, busqueda libre de un tren.")
    p.add_argument("--min-captura", type=float, default=0.75,
                   help="Fraccion minima de ranuras de la grilla que tienen que estar ocupadas. "
                        "Bajarlo solo si se sospecha bloqueo (captura 2:1 o peor).")
    p.add_argument("--min-frames-cinetica", type=int, default=cin.MIN_FRAMES,
                   help="Fotogramas minimos de subida (TTP) o de bajada al 50%% (RT50) "
                        "para que la metrica se reporte como valor. Por debajo se "
                        "reporta solo la cota superior.")
    p.add_argument("--sin-separar", action="store_true",
                   help="No intentar separar estimuladas de espontaneas.")
    p.add_argument("--output-dir", default=None)
    return p.parse_args()


def main():
    a = parse_args()
    entradas = [(Path(a.input).parent.name or Path(a.input).stem, _leer(a.input))]
    if a.compare:
        entradas.append((Path(a.compare).parent.name or Path(a.compare).stem, _leer(a.compare)))

    resultados = []
    for nombre, df in entradas:
        k_arg = None if str(a.k).strip().lower() == "auto" else float(a.k)
        win_arg = None if str(a.win_s).strip().lower() == "auto" else float(a.win_s)
        r = analizar(df, a.canal, k_arg, win_arg, a.sep_s, a.half_s,
                     separar=not a.sin_separar, min_captura=a.min_captura,
                     min_frames_cinetica=a.min_frames_cinetica,
                     frecuencia_estimulo=a.frecuencia_estimulo)
        imprimir(nombre, r)
        resultados.append((nombre, r))

    print()
    print("  Como leer el escaneo: si 'eventos' tiene una MESETA (no cambia al subir k)")
    print("  y 'falsos_control' es 0 en esa meseta, los eventos son reales. Si el conteo")
    print("  cae monotonamente y hay falsos parecidos al conteo real, es ruido.")

    if a.frecuencia_estimulo:
        print()
        for nombre, r in resultados:
            rit = r.get("ritmo")
            if rit is None:
                continue
            if not rit.get("hay_estimulacion"):
                continue
            fc = min(a.frecuencia_estimulo, key=lambda x: abs(rit["frecuencia_Hz"] - x))
            c = rs.comparar_con_equipo(rit, fc, fps_nominal=r.get("fps_medido"))
            print(f"  {nombre[:26]:26s} equipo vs medido")
            for kk, vv in c.items():
                print(f"       {kk:28s} {vv}")

    out = Path(a.output_dir) if a.output_dir else Path(a.input).parent
    out.mkdir(parents=True, exist_ok=True)
    nombre_video = resultados[0][0]
    png_contracciones = out / f"09_contracciones_{nombre_video}.png"
    graficar(resultados, png_contracciones)
    png_ritmo = graficar_ritmo(resultados, out / f"10_ritmo_{nombre_video}.png")
    png_cinetica = graficar_cinetica(resultados, out / f"11_cinetica_{nombre_video}.png")
    png_estab = graficar_estabilidad(resultados, out / f"05_estabilidad_umbral_{nombre_video}.png")

    with pd.ExcelWriter(out / "contracciones.xlsx", engine="openpyxl") as w:
        for nombre, r in resultados:
            r["estabilidad"].to_excel(w, sheet_name=f"estab_{nombre[:20]}", index=False)
            fila = {kk: vv for kk, vv in r.items()
                    if not kk.startswith("_") and kk not in ("estabilidad", "tiempos_s", "poblaciones")}
            pd.DataFrame([fila]).to_excel(w, sheet_name=f"resumen_{nombre[:18]}", index=False)
            rit = r.get("ritmo")
            if rit is not None:
                rit["resumen_grupos"].to_excel(w, sheet_name=f"ritmo_{nombre[:19]}", index=False)
                rit["trenes"].to_excel(w, sheet_name=f"trenes_{nombre[:18]}", index=False)
                if len(rit.get("sacados_tiempo_amplitud", [])):
                    rit["sacados_tiempo_amplitud"].to_excel(w, sheet_name=f"sacados_{nombre[:18]}", index=False)
                if len(rit.get("dudosos", [])):
                    rit["dudosos"].to_excel(w, sheet_name=f"dudosos_{nombre[:18]}", index=False)
                if len(rit.get("grilla", [])):
                    rit["grilla"].to_excel(w, sheet_name=f"grilla_{nombre[:18]}", index=False)
                if len(rit.get("espontaneas_instantanea", [])):
                    rit["espontaneas_instantanea"].to_excel(
                        w, sheet_name=f"espont_{nombre[:18]}", index=False)
            if r.get("poblaciones"):
                pd.DataFrame(r["poblaciones"]).to_excel(w, sheet_name=f"poblac_{nombre[:19]}", index=False)
            if r["n_eventos"]:
                pd.DataFrame({"evento": np.arange(1, r["n_eventos"] + 1),
                              "tiempo_s": r["tiempos_s"],
                              "amplitud_px": r["_r"][r["_picos"]],
                              "junto_a_hueco": r["_junto_a_hueco"],
                              "junto_al_borde": r["_junto_al_borde"]}
                             ).to_excel(w, sheet_name=f"eventos_{nombre[:18]}", index=False)
            if r.get("_cinetica") is not None and len(r["_cinetica"]):
                r["_cinetica"].to_excel(w, sheet_name=f"cinetica_{nombre[:18]}", index=False)
                r["_cinetica_grupos"].to_excel(w, sheet_name=f"cin_grupos_{nombre[:16]}", index=False)

    print(f"\nGrafico: {png_contracciones}")
    if png_ritmo:
        print(f"Grafico: {png_ritmo}")
    if png_cinetica:
        print(f"Grafico: {png_cinetica}")
    print(f"Grafico: {png_estab}")
    print(f"Tabla:   {out / 'contracciones.xlsx'}")


if __name__ == "__main__":
    main()
