"""
preprocessing.py
-----------------
Normalización de iluminación y detección automática de la región de
interés (ROI) y de la posición aproximada de los bordes superior/
inferior, a partir del maxProjectStack.

CAMBIOS RESPECTO DE LA VERSIÓN ANTERIOR (por qué)
--------------------------------------------------
La versión anterior localizaba la franja del gel en cada columna como
    top = primer píxel de la máscara Otsu,  bottom = último píxel
y elegía la gauge region como las columnas cuyo grosor no se apartaba
más de un 10% de la mediana del 20% central DE LA IMAGEN.

Eso tiene tres fallas que se manifestaron en el Video_063:

1) `col.min()` / `col.max()` toman el PRIMER y ÚLTIMO píxel encendido
   de toda la columna. Si en esa columna hay un halo del poste, un
   reflejo, o una zona desenfocada brillante, la "franja" se estira
   hasta ahí y el grosor medido salta a un valor absurdo. Esa columna
   queda descartada y se rompe la contigüidad del bloque -> la ROI se
   corta arbitrariamente en el medio del gel.
   AHORA: se toman los TRAMOS CONTIGUOS de máscara por columna y se
   SIGUE la franja del gel desde el centro hacia los dos lados,
   eligiendo en cada columna el tramo compatible en posición y grosor
   con la columna anterior. El halo deja de contaminar.

2) La referencia de grosor se tomaba del 20% central de la IMAGEN, no
   del gel. Si el gel no está centrado, o si esa zona tiene halo, la
   referencia sale mal y todo el criterio se corre.
   AHORA: la referencia es la CINTURA del propio gel (percentil 5 del
   perfil de grosor), que es una propiedad del gel y no de dónde quedó
   encuadrado.

3) "Grosor parecido a la referencia" NO es la definición de gauge
   region: una zona puede estar dentro del ±10% y aun así estar
   cambiando de grosor monótonamente (que es exactamente lo que pasó:
   la ROI elegida iba de 308.9 px a 288.6 px, o sea el hombro del
   anclaje). La gauge region es donde el grosor es PLANO.
   AHORA: el criterio principal es |d(grosor)/dx| por debajo de un
   umbral, más la cercanía a la cintura.

Además: se puede forzar la ROI a mano (x_start / x_end) y el dict
`roi_quality` explica cuántas columnas se descartaron por cada motivo,
para poder auditar la elección en vez de adivinarla.
"""

from __future__ import annotations
import numpy as np
import cv2


# ---------------------------------------------------------------------
# Normalización de imagen (sin cambios de lógica)
# ---------------------------------------------------------------------

def apply_clahe(frame: np.ndarray, clip_limit: float = 2.0, tile_grid: int = 8) -> np.ndarray:
    """
    CLAHE = Contrast Limited Adaptive Histogram Equalization.

    Normaliza el contraste localmente (por tiles) en vez de
    globalmente, lo que compensa viñeteo y variaciones de iluminación.

    CUIDADO EN VIDEOS CON BURBUJAS MÓVILES: CLAHE construye un mapeo de
    intensidad por tile (por defecto 8x8 tiles). Si una burbuja entra o
    sale de un tile, el mapeo de TODO ese tile cambia, y con él la
    posición subpíxel del borde que cae dentro. En ese escenario CLAHE
    puede fabricar variaciones de grosor que no son deformación real.
    Si tu video tiene burbujas que se mueven, compará el resultado con
    `--no-clahe` antes de confiar en la serie temporal.
    """
    clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=(tile_grid, tile_grid))
    return clahe.apply(frame)


def denoise(frame: np.ndarray, h: float = 7.0) -> np.ndarray:
    """
    Suavizado non-local-means: reduce ruido de sensor sin destruir la
    nitidez del borde (a diferencia de un blur gaussiano grande, que
    "corre" artificialmente la posición del borde).
    """
    return cv2.fastNlMeansDenoising(frame, None, h=h, templateWindowSize=7, searchWindowSize=21)


def preprocess_frame(frame: np.ndarray, use_clahe: bool = True, use_denoise: bool = False) -> np.ndarray:
    """Pipeline de preprocesamiento por frame."""
    out = frame.copy()
    if use_denoise:
        out = denoise(out)
    if use_clahe:
        out = apply_clahe(out)
    return out


# ---------------------------------------------------------------------
# Helpers internos para la detección de la franja del gel
# ---------------------------------------------------------------------

def _odd(n: int, minimum: int = 3) -> int:
    n = int(n)
    n += (n % 2 == 0)
    return max(n, minimum)


def _runs_of_true(col_mask: np.ndarray, min_run: int = 3) -> list[tuple[int, int]]:
    """
    Tramos contiguos [inicio, fin] (ambos inclusive) donde `col_mask`
    es True, descartando los más cortos que `min_run`.

    Esto es lo que reemplaza al viejo `col.min()` / `col.max()`: en vez
    de asumir que todo lo encendido en la columna es el gel, tratamos
    cada tramo por separado y después elegimos cuál es el gel.
    """
    m = np.concatenate(([False], col_mask.astype(bool), [False]))
    d = np.diff(m.astype(np.int8))
    starts = np.flatnonzero(d == 1)
    ends = np.flatnonzero(d == -1) - 1
    return [(int(s), int(e)) for s, e in zip(starts, ends) if (e - s + 1) >= min_run]


def _track_gel_band(
    mask: np.ndarray,
    min_run: int = 5,
    max_thickness_ratio: float = 2.0,
    max_center_jump_frac: float = 0.75,
) -> tuple[np.ndarray, np.ndarray] | None:
    """
    Sigue la franja del gel columna por columna, arrancando desde el
    centro de la imagen y caminando hacia los dos bordes.

    En cada columna se elige, entre los tramos contiguos de máscara,
    aquel cuyo CENTRO está más cerca del centro de la columna anterior,
    exigiendo además que su grosor sea compatible (dentro de un factor
    `max_thickness_ratio`) con el grosor que se venía siguiendo.

    Por qué caminar desde el centro: los halos y los postes están en los
    extremos de la imagen. Arrancando del centro (donde el puente de gel
    está limpio) y propagando hacia afuera, la franja correcta actúa como
    "ancla" y los tramos espurios de los extremos nunca se eligen.

    Returns
    -------
    (top_rows, bottom_rows) : arrays de largo w, con NaN en las columnas
    donde no se pudo seguir la franja. O None si ni siquiera se pudo
    sembrar el seguimiento (imagen sin gel visible).
    """
    h, w = mask.shape
    runs = [_runs_of_true(mask[:, x], min_run=min_run) for x in range(w)]

    # --- semilla: columnas centrales, tramo más largo de cada una ---
    centers, thicks = [], []
    for x in range(int(w * 0.35), int(w * 0.65)):
        if runs[x]:
            s, e = max(runs[x], key=lambda r: r[1] - r[0])
            centers.append(0.5 * (s + e))
            thicks.append(e - s + 1)
    if not centers:
        return None

    ref_center = float(np.median(centers))
    ref_thickness = float(np.median(thicks))

    top = np.full(w, np.nan)
    bottom = np.full(w, np.nan)

    def walk(order):
        c, t = ref_center, ref_thickness
        for x in order:
            best = None
            for s, e in runs[x]:
                cc = 0.5 * (s + e)
                tt = e - s + 1
                # el gel no cambia de grosor de golpe entre columnas vecinas
                if tt > max_thickness_ratio * t or tt * max_thickness_ratio < t:
                    continue
                # ni salta verticalmente medio gel de una columna a la otra
                if abs(cc - c) > max_center_jump_frac * t:
                    continue
                d = abs(cc - c)
                if best is None or d < best[0]:
                    best = (d, s, e)
            if best is None:
                continue  # columna sin franja creíble -> NaN, se interpola luego
            _, s, e = best
            top[x], bottom[x] = float(s), float(e)
            # seguimiento suave: el gel es continuo, no queremos que una
            # columna rara arrastre la referencia
            c = 0.7 * c + 0.3 * (0.5 * (s + e))
            t = 0.7 * t + 0.3 * (e - s + 1)

    x0 = int(w * 0.5)
    walk(range(x0, w))
    walk(range(x0, -1, -1))

    if np.all(np.isnan(top)):
        return None
    return top, bottom


def _edge_sharpness(max_projection: np.ndarray, top: np.ndarray, bottom: np.ndarray,
                    margin: int = 4) -> np.ndarray:
    """
    Nitidez del borde en cada columna: el MENOR de los dos gradientes
    verticales máximos medidos en un entorno del borde superior y del
    inferior.

    Se toma el MENOR a propósito: para medir grosor necesitamos los DOS
    bordes nítidos. La versión anterior tomaba el máximo de toda la
    columna, con lo cual un borde superior nítido "tapaba" un borde
    inferior desenfocado y la columna pasaba el filtro igual.
    """
    g = np.abs(np.gradient(max_projection.astype(np.float64), axis=0))
    h, w = max_projection.shape
    out = np.full(w, np.nan)
    for x in range(w):
        if np.isnan(top[x]) or np.isnan(bottom[x]):
            continue
        t, b = int(round(top[x])), int(round(bottom[x]))
        gt = g[max(0, t - margin):min(h, t + margin + 1), x]
        gb = g[max(0, b - margin):min(h, b + margin + 1), x]
        if gt.size == 0 or gb.size == 0:
            continue
        out[x] = float(min(gt.max(), gb.max()))
    return out


def _nan_interp(y: np.ndarray) -> np.ndarray:
    """Interpola linealmente los NaN internos y extiende los extremos."""
    y = np.asarray(y, dtype=float).copy()
    ok = np.isfinite(y)
    if ok.sum() < 2:
        return y
    xs = np.arange(len(y))
    y[~ok] = np.interp(xs[~ok], xs[ok], y[ok])
    return y


def _rolling_median(y: np.ndarray, k: int) -> np.ndarray:
    """Mediana móvil centrada, sin dependencias extra."""
    k = _odd(k)
    pad = k // 2
    yp = np.pad(y, pad, mode="edge")
    view = np.lib.stride_tricks.sliding_window_view(yp, k)
    return np.median(view, axis=1)


def _longest_true_block(flags: np.ndarray) -> tuple[int, int] | None:
    """(inicio, fin_exclusivo) del bloque contiguo de True más largo."""
    idx = np.flatnonzero(flags)
    if idx.size == 0:
        return None
    blocks = np.split(idx, np.flatnonzero(np.diff(idx) != 1) + 1)
    best = max(blocks, key=len)
    return int(best.min()), int(best.max()) + 1


# ---------------------------------------------------------------------
# Detección de la ROI (gauge region)
# ---------------------------------------------------------------------

def auto_detect_roi(
    max_projection: np.ndarray,
    thickness_tolerance: float = 0.05,
    min_gradient_for_roi: float = 10.0,
    max_thickness_slope: float = 0.02,
    min_roi_width_frac: float = 0.35,
    fallback_margin_x_frac: float = 0.05,
    x_start: int | None = None,
    x_end: int | None = None,
    smooth_px: int | None = None,
) -> dict:
    """
    A partir del maxProjectStack, estima la gauge region y la posición
    aproximada de los bordes superior/inferior por columna.

    Parameters
    ----------
    thickness_tolerance : cuánto puede exceder el grosor de una columna
        a la CINTURA del gel (percentil 5 del perfil de grosor) para
        seguir considerándose gauge region. 0.05 = 5%.
        OJO: el significado cambió respecto de la versión anterior. Antes
        era "±10% de la mediana del centro de la imagen"; ahora es
        "hasta +5% por encima de la cintura del propio gel". Es un
        criterio más estricto y más físico.
    min_gradient_for_roi : nitidez mínima exigida a AMBOS bordes.
    max_thickness_slope : |d(grosor)/dx| máximo, en píxeles de grosor por
        píxel de x. 0.02 significa que el grosor no puede cambiar más de
        2 px cada 100 px de recorrido horizontal. Éste es el criterio que
        realmente define "zona de grosor uniforme".
    min_roi_width_frac : ancho mínimo aceptable de la ROI, como fracción de
        las columnas QUE CONTIENEN GEL (no del ancho de la imagen, que depende
        del encuadre). Si el criterio estricto devuelve un tramo más corto que
        esto, se relaja al siguiente nivel — un tramo muy corto es plano pero
        mide peor, porque las columnas quedan tan juntas que comparten ruido.
        `roi_quality["alternativas"]` lista lo que habría dado cada nivel.
    x_start, x_end : override MANUAL. Si se pasan, se usan tal cual y se
        saltea toda la selección automática (método = "manual"). Útil
        cuando ya mirás el perfil de grosor y sabés dónde querés medir.
    smooth_px : ancho de la mediana móvil con la que se suaviza el perfil
        de grosor antes de calcular la pendiente. Por defecto ~w/60.

    Returns
    -------
    dict con:
        x_start, x_end        : rango de columnas de la gauge region
        top_guess, bottom_guess : arrays indexados por columna x
        roi_quality           : dict auditable (método usado, cintura,
                                variación de grosor dentro de la ROI,
                                y cuántas columnas cayó cada criterio)
        thickness_profile     : grosor suavizado por columna (para graficar)
        sharpness_profile     : nitidez por columna (para graficar)
        valid_columns         : bool por columna (se pudo seguir la franja)
    """
    h, w = max_projection.shape

    # Un blur suave antes de Otsu evita que el ruido de sensor pique la
    # máscara y fragmente la franja en tramos cortos.
    blurred = cv2.GaussianBlur(max_projection, (5, 5), 0)
    _, mask_img = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    mask = mask_img > 0

    band = _track_gel_band(mask)

    fallback = {
        "x_start": int(w * fallback_margin_x_frac),
        "x_end": int(w * (1 - fallback_margin_x_frac)),
    }

    if band is None:
        top_rows = np.full(w, h * 0.4)
        bottom_rows = np.full(w, h * 0.6)
        return {
            "x_start": fallback["x_start"],
            "x_end": fallback["x_end"],
            "top_guess": top_rows,
            "bottom_guess": bottom_rows,
            "roi_quality": {
                "method": "fallback_margin",
                "motivo": "no se pudo ubicar la franja del gel en el maxProjection",
            },
            "thickness_profile": np.full(w, np.nan),
            "sharpness_profile": np.full(w, np.nan),
            "valid_columns": np.zeros(w, dtype=bool),
        }

    top_rows, bottom_rows = band
    valid = np.isfinite(top_rows) & np.isfinite(bottom_rows)

    sharpness = _edge_sharpness(max_projection, top_rows, bottom_rows)

    thickness = np.where(valid, bottom_rows - top_rows, np.nan)
    k = smooth_px if smooth_px is not None else max(5, w // 60)
    T = _rolling_median(_nan_interp(thickness), k)

    # Pendiente del perfil de grosor.
    # El grosor de la máscara es ENTERO, así que T avanza a saltos de 1 px y
    # np.gradient() directo sobre él da picos espurios de ~1 px/px en cada
    # escalón — con eso el criterio de planitud nunca se cumple aunque el gel
    # sea perfectamente uniforme (pasó en el Video_063: pendiente_max=1.5).
    # Por eso se promedia sobre una ventana ancha antes de derivar: el escalón
    # de 1 px se reparte y queda la pendiente real.
    d = max(10, w // 50)
    Tf = np.convolve(np.pad(T, d, mode="edge"), np.ones(2 * d + 1) / (2 * d + 1),
                     mode="same")[d:-d]
    slope = np.abs(np.gradient(Tf))

    # --- Cintura del gel (referencia de grosor) ---
    # BUG CORREGIDO (Video_063): antes esto era percentil 5 de T sobre TODAS
    # las columnas seguidas. El seguimiento llega hasta el borde de la imagen,
    # y más allá del poste sigue una hebra fina y desenfocada de ~60-110 px.
    # Esa cola arrastraba el percentil 5 a 111 px cuando el gel real mide
    # ~285 px, con lo cual `near_waist` no lo cumplía casi ninguna columna
    # (1588 descartadas "por grosor") y la selección caía a `solo_nitidez`.
    #
    # Ahora la cintura se mide en dos pasos, solo sobre columnas con AMBOS
    # bordes nítidos (que es donde hay gel de verdad):
    #   1. escala de referencia = mediana de T ahí,
    #   2. se descartan las columnas cuyo T no está en [0.6, 1.6] x esa
    #      escala (hebras finas más allá del poste, o picos del halo),
    #   3. cintura = percentil 5 de lo que queda.
    sharp_for_waist = np.isfinite(sharpness) & (sharpness >= min_gradient_for_roi)
    base_mask = valid & sharp_for_waist
    if base_mask.sum() < 20:
        base_mask = valid.copy()
    if base_mask.any():
        escala = float(np.nanmedian(T[base_mask]))
        gel_like = base_mask & np.isfinite(T) & (T > 0.6 * escala) & (T < 1.6 * escala)
        if gel_like.sum() < 20:
            gel_like = base_mask
        waist = float(np.nanpercentile(T[gel_like], 5))
    else:
        escala, gel_like = float("nan"), np.zeros(w, dtype=bool)
        waist = float("nan")

    # --- Bordes suavizados para usarlos como centro de la ventana de
    #     búsqueda en cada frame ---
    top_guess = _rolling_median(_nan_interp(top_rows), k)
    bottom_guess = _rolling_median(_nan_interp(bottom_rows), k)
    top_guess = np.clip(top_guess, 0, h - 1)
    bottom_guess = np.clip(bottom_guess, 0, h - 1)

    profiles = {
        "thickness_profile": T,
        "sharpness_profile": sharpness,
        "valid_columns": valid,
    }

    # --- Override manual ---
    if x_start is not None or x_end is not None:
        xs = int(x_start) if x_start is not None else 0
        xe = int(x_end) if x_end is not None else w
        xs, xe = max(0, min(xs, w - 2)), min(w, max(xe, xs + 2))
        seg = T[xs:xe]
        return {
            "x_start": xs, "x_end": xe,
            "top_guess": top_guess, "bottom_guess": bottom_guess,
            "roi_quality": {
                "method": "manual",
                "criterio": "rango forzado por el usuario (--x-start/--x-end)",
                "cintura_px": round(waist, 2),
                "roi_width_px": xe - xs,
                "roi_width_frac": round((xe - xs) / w, 3),
                "grosor_min_en_roi_px": round(float(np.nanmin(seg)), 2),
                "grosor_max_en_roi_px": round(float(np.nanmax(seg)), 2),
                "variacion_en_roi_pct": round(
                    100 * (np.nanmax(seg) - np.nanmin(seg)) / max(np.nanmin(seg), 1e-9), 2),
            },
            **profiles,
        }

    sharp_ok = np.isfinite(sharpness) & (sharpness >= min_gradient_for_roi)
    near_waist = np.isfinite(T) & (T <= waist * (1 + thickness_tolerance))
    flat = np.isfinite(slope) & (slope <= max_thickness_slope)

    # Ancho mínimo exigido a la ROI, medido sobre las columnas QUE TIENEN GEL,
    # no sobre el ancho de la imagen (que depende del encuadre).
    #
    # Por qué importa: el criterio más estricto puede devolver un tramo
    # cortísimo. En el Video_063 daba x=875..1039, apenas 164 px con 0.35% de
    # variación de grosor. Perfectamente plano, sí, pero con 60 columnas en
    # 164 px los puntos quedan a 2.7 px entre sí: comparten el mismo ruido de
    # imagen y el mismo tile de CLAHE, así que aportan mucha menos información
    # independiente y el grosor medido sale MÁS ruidoso, no menos. Un tramo
    # ancho con 5% de variación de grosor promedia mejor, y esa variación
    # afecta la INTERPRETACIÓN (dónde se mide) más que la DETECCIÓN (si hay
    # cambio en el tiempo).
    n_gel = int(gel_like.sum()) if np.any(gel_like) else int(valid.sum())
    min_width = max(40, int(min_roi_width_frac * max(n_gel, 1)))

    # Cascada de criterios, del más estricto al más laxo. El primero que
    # produzca un bloque contiguo suficientemente ancho, gana. `method`
    # dice cuál se usó, así que nunca queda oculto que hubo que relajar.
    levels = [
        ("gauge_plana",        valid & sharp_ok & near_waist & flat,
         "grosor plano + cerca de la cintura + ambos bordes nitidos"),
        ("gauge_cintura",      valid & sharp_ok & near_waist,
         "cerca de la cintura + ambos bordes nitidos (se relajo la planitud)"),
        ("gauge_relajada",     valid & sharp_ok & np.isfinite(T) & (T <= waist * (1 + 2 * thickness_tolerance)),
         "tolerancia de grosor duplicada"),
        ("solo_nitidez",       valid & sharp_ok,
         "solo se exigio nitidez de ambos bordes"),
        ("franja_completa",    valid,
         "toda la franja seguida, sin filtros"),
    ]

    alternativas = []
    chosen = None
    for name, flags, desc in levels:
        blk = _longest_true_block(flags)
        if blk is None:
            continue
        a, b = blk
        seg_i = T[a:b]
        var = (100 * (np.nanmax(seg_i) - np.nanmin(seg_i)) / max(float(np.nanmin(seg_i)), 1e-9)
               if seg_i.size else None)
        alternativas.append({
            "metodo": name, "x_start": int(a), "x_end": int(b),
            "ancho_px": int(b - a),
            "variacion_pct": round(var, 2) if var is not None else None,
            "elegida": False,
        })
        if chosen is None and (b - a) >= min_width:
            chosen = (name, blk, desc)
            alternativas[-1]["elegida"] = True

    if chosen is None:
        xs, xe, method, desc = fallback["x_start"], fallback["x_end"], "fallback_margin", \
            "ningun criterio dio un bloque suficientemente ancho"
    else:
        method, (xs, xe), desc = chosen

    seg = T[xs:xe]
    quality = {
        "method": method,
        "criterio": desc,
        "cintura_px": round(waist, 2) if np.isfinite(waist) else None,
        "escala_grosor_px": round(escala, 2) if np.isfinite(escala) else None,
        "n_columnas_con_gel": int(gel_like.sum()),
        "roi_width_px": int(xe - xs),
        "roi_width_frac": round((xe - xs) / w, 3),
        "grosor_min_en_roi_px": round(float(np.nanmin(seg)), 2) if seg.size else None,
        "grosor_max_en_roi_px": round(float(np.nanmax(seg)), 2) if seg.size else None,
        "variacion_en_roi_pct": (round(100 * (np.nanmax(seg) - np.nanmin(seg))
                                       / max(float(np.nanmin(seg)), 1e-9), 2) if seg.size else None),
        "pendiente_max_en_roi": round(float(np.nanmax(slope[xs:xe])), 4) if seg.size else None,
        # conteos para auditar por qué se descartó cada columna
        "n_columnas_imagen": int(w),
        "n_franja_seguida": int(valid.sum()),
        "n_desc_por_nitidez": int((valid & ~sharp_ok).sum()),
        "n_desc_por_grosor": int((valid & sharp_ok & ~near_waist).sum()),
        "n_desc_por_pendiente": int((valid & sharp_ok & near_waist & ~flat).sum()),
        "ancho_minimo_exigido_px": int(min_width),
        "alternativas": alternativas,
    }

    return {
        "x_start": int(xs),
        "x_end": int(xe),
        "top_guess": top_guess,
        "bottom_guess": bottom_guess,
        "roi_quality": quality,
        **profiles,
    }
