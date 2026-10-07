#!/usr/bin/env python
"""
medir_magnitud_px.py  -  Fase 3, tema 7 (H51). SOLO MIDE.

PREGUNTA: en los eventos, la traslacion por correlacion de intensidad
(motion_check: desp_vert_px) vale 0.18 x lo que vale center_px (bordes).
¿Cual de los dos mide bien la magnitud?

METODO: verdad conocida. Se toman fotogramas QUIETOS reales (lejos de
cualquier evento), se los desplaza hacia abajo una cantidad elegida s y se
mide ese desplazamiento con:
    bordes_clahe : pipeline.process_frame tal como lo usa main.py (center_px)
    bordes_crudo : lo mismo sin CLAHE
    correlacion  : motion_check._subpixel_shift con el mismo perfil vertical
                   que usa motion_check (promedio de las columnas de la ROI,
                   de top-40 a bottom+40)
Lo medido se compara con s.

Tres maneras de desplazar (de mas simple a mas realista):
    rigido    : toda la imagen se corre s
    blur      : se corre s DURANTE la exposicion (promedio de las posiciones
                0..s, desenfoque por movimiento). Posicion final s, media s/2
    franja    : solo se mueve la franja del gel; el fondo queda quieto

Control de la interpolacion (las fracciones de pixel se hacen con spline
cubico, que tambien suaviza un poco): ademas de los fotogramas reales se usa
un gel SINTETICO dibujado analiticamente en cada posicion (sin interpolar),
y se compara con el mismo gel desplazado por interpolacion. Y los
corrimientos enteros (1, 2, 3 px) se hacen tambien por copia exacta de filas.

USO (desde cualquier carpeta):
    python scripts/medir_magnitud_px.py
    python scripts/medir_magnitud_px.py --videos Video_prueba
Salida: data/fase3_magnitud/ (mediciones.csv y resumen_magnitud.md)
Tarda ~1-2 min por video (la mayor parte es la imagen de maximos).
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import ndimage
from scipy.special import erf

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "scripts"))

from src import io_utils, preprocessing, pipeline  # noqa: E402
from src.pipeline import PipelineConfig  # noqa: E402
from src.estadistica import detrend_median, mad  # noqa: E402
import motion_check as mc  # noqa: E402

OK = "data/raw_videos/OK-20260904T142817Z-1-001/OK"
VIDEOS = {
    "Video_prueba": "data/raw_videos/Video_prueba.mp4",
    "Video_063_CTRL1_5V": f"{OK}/Video_063_CTRL1_5V.mp4",
    "Video_466_EXP5_FAPS4_40V": f"{OK}/Video_466_EXP5_FAPS4_40V.mp4",
}
DESPLAZ = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.5, 2.0, 3.0]
ENTEROS = [1, 2, 3]
CFG = PipelineConfig()
CFG_CRUDO = PipelineConfig(use_clahe=False)


# ---------------------------------------------------------------------------
# Desplazamientos
# ---------------------------------------------------------------------------
def corrimiento_interp(img, s):
    """Corre la imagen s px hacia abajo (spline cubico)."""
    return ndimage.shift(img.astype(float), (s, 0), order=3, mode="nearest")


def corrimiento_entero(img, s):
    """Corre s px enteros hacia abajo copiando filas (sin interpolar)."""
    out = np.empty_like(img, dtype=float)
    out[s:] = img[:-s]
    out[:s] = img[:1]
    return out


def corrimiento_blur(img, s, n=11):
    """Promedio de las posiciones 0..s: el gel se movio durante la exposicion."""
    return np.mean([corrimiento_interp(img, u) for u in np.linspace(0, s, n)], axis=0)


def mascara_franja(shape, top, bot, xs, xe, margen=25, suave=4.0):
    """1 dentro de la franja (top-margen .. bot+margen), 0 afuera, con una
    transicion suave de ~`suave` px para no crear un borde artificial."""
    H, W = shape
    yy = np.arange(H)[:, None].astype(float)
    t = np.full(W, np.nan); b = np.full(W, np.nan)
    t[:] = np.interp(np.arange(W), np.arange(W), top)
    b[:] = np.interp(np.arange(W), np.arange(W), bot)
    m = 0.5 * (1 + erf((yy - (t - margen)[None, :]) / suave)) * \
        0.5 * (1 + erf(((b + margen)[None, :] - yy) / suave))
    return m


def corrimiento_franja(img, s, m):
    """Solo se mueve la franja (y su mascara con ella); el fondo queda quieto."""
    sh = corrimiento_interp(img, s)
    ms = corrimiento_interp(m, s)
    return ms * sh + (1 - ms) * img.astype(float)


# ---------------------------------------------------------------------------
# Mediciones
# ---------------------------------------------------------------------------
class Medidor:
    def __init__(self, ref, roi, xs, xe):
        self.xpos = np.linspace(xs, xe - 1, CFG.n_columns).astype(int)
        self.tg, self.bg = roi["top_guess"], roi["bottom_guess"]
        self.xs, self.xe = xs, xe
        H = ref.shape[0]
        top = self.tg[xs:xe]; bot = self.bg[xs:xe]
        # mismos limites que motion_check.main
        self.y0v = int(max(0, np.median(top) - 40))
        self.y1v = int(min(H, np.median(bot) + 40))
        self.ref = ref
        self.base = self._bordes(ref)
        self.pref = self._perfil(ref)

    def _a_uint8(self, img):
        return np.clip(np.round(img), 0, 255).astype(np.uint8)

    def _bordes(self, img):
        u = self._a_uint8(img)
        out = {}
        for nom, cfg in (("bordes_clahe", CFG), ("bordes_crudo", CFG_CRUDO)):
            r = pipeline.process_frame(u, self.xpos, self.tg, self.bg, cfg)
            out[nom] = (r["center_px"], r["y_top_px"], r["y_bottom_px"])
        return out

    def _perfil(self, img):
        return img[self.y0v:self.y1v, self.xs:self.xe].astype(np.float32).mean(axis=1)

    def medir(self, img):
        b = self._bordes(img)
        out = {}
        for nom in b:
            out[nom] = b[nom][0] - self.base[nom][0]
            out[nom + "_top"] = b[nom][1] - self.base[nom][1]
            out[nom + "_bot"] = b[nom][2] - self.base[nom][2]
        s, c = mc._subpixel_shift(self.pref, self._perfil(img), max_lag=25)
        out["correlacion"], out["corr_pico"] = s, c
        return out


# ---------------------------------------------------------------------------
# Fotogramas quietos
# ---------------------------------------------------------------------------
def fotogramas_quietos(nombre, n=5):
    p = RAIZ / "data/processed_data" / nombre / "serie_temporal.xlsx"
    d = pd.read_excel(p, sheet_name="diagnostics")
    res = pd.read_excel(p, sheet_name="resumen")
    kv = dict(zip(res.iloc[:, 0].astype(str), res.iloc[:, 1]))
    t = d["time_s"].to_numpy(float)
    fps = 1.0 / np.median(np.diff(t))
    r = detrend_median(d["center_px"].to_numpy(float), fps, 2.0)
    m = mad(r)
    lejos = np.ones(len(r), bool)
    for i in np.where(np.abs(r) > 4 * m)[0]:   # todo lo que se mueve, +-1 s
        lejos[max(0, i - int(fps)):i + int(fps) + 1] = False
    cand = np.where(lejos & (np.abs(r) < m))[0]
    cand = cand[(cand > 30) & (cand < len(r) - 30)]
    elegidos = cand[np.linspace(0, len(cand) - 1, n).astype(int)] if len(cand) else []
    return [int(i) for i in elegidos], int(kv["ROI x_start"]), int(kv["ROI x_end"])


def leer_fotogramas(video, idxs):
    out = {}
    for i in idxs:
        for _, f in io_utils.frame_generator(video, start_frame=i, end_frame=i + 1):
            out[i] = f
    return out


# ---------------------------------------------------------------------------
# Gel sintetico (control de la interpolacion)
# ---------------------------------------------------------------------------
def gel_analitico(s, H=1080, W=1920, top=400.3, bot=685.7, sigma=2.0, ruido=None):
    """Gel claro sobre fondo oscuro con bordes de forma erf, dibujado
    analiticamente en la posicion top+s .. bot+s (sin interpolar). Bordes
    levemente curvos (parabola de 3 px) para que se parezca al real."""
    x = np.arange(W)[None, :]
    curva = 3.0 * ((x - W / 2) / (W / 2)) ** 2
    yy = np.arange(H)[:, None].astype(float)
    t, b = top + s + curva, bot + s + curva
    img = 40 + 160 * 0.5 * (erf((yy - t) / (np.sqrt(2) * sigma)) - erf((yy - b) / (np.sqrt(2) * sigma)))
    if ruido is not None:
        img = img + ruido
    return img


# ---------------------------------------------------------------------------
def resumir(df):
    """Pendiente medido/verdadero por metodo y variante, y error en subpixel."""
    filas = []
    for (caso, var), g in df.groupby(["caso", "variante"]):
        for met in ("bordes_clahe", "bordes_crudo", "correlacion"):
            v = g[[met, "s"]].dropna()
            if len(v) < 2:
                continue
            pend = float(np.sum(v[met] * v["s"]) / np.sum(v["s"] ** 2))
            sub = v[v["s"] < 1]
            filas.append({"caso": caso, "variante": var, "metodo": met,
                          "medido/verdadero (pendiente)": round(pend, 3),
                          "error_medio_px": round(float((v[met] - v["s"]).mean()), 3),
                          "error_max_abs_px": round(float((v[met] - v["s"]).abs().max()), 3),
                          "error_medio_subpixel_px": round(float((sub[met] - sub["s"]).mean()), 3) if len(sub) else None})
    return pd.DataFrame(filas)


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--videos", nargs="+", default=list(VIDEOS))
    p.add_argument("--n-fotogramas", type=int, default=5)
    p.add_argument("--salida", default="data/fase3_magnitud")
    a = p.parse_args()
    salida = RAIZ / a.salida
    salida.mkdir(parents=True, exist_ok=True)
    filas = []

    # ---- 1. sintetico: analitico vs interpolado ----
    t0 = time.time()
    rng = np.random.default_rng(0)
    ruido = rng.normal(0, 3, (1080, 1920))
    ref = gel_analitico(0, ruido=ruido)
    xs, xe = 560, 1360
    roi = preprocessing.auto_detect_roi(np.clip(ref, 0, 255).astype(np.uint8), x_start=xs, x_end=xe)
    med = Medidor(ref, roi, xs, xe)
    for s in DESPLAZ:
        # analitico: el gel se dibuja en la posicion nueva, el ruido NO se mueve
        filas.append({"caso": "sintetico", "fotograma": -1, "variante": "analitico", "s": s,
                      **med.medir(gel_analitico(s, ruido=ruido))})
        filas.append({"caso": "sintetico", "fotograma": -1, "variante": "rigido_interp", "s": s,
                      **med.medir(corrimiento_interp(ref, s))})
    print(f"sintetico: {time.time() - t0:.0f} s", flush=True)

    # ---- 2. videos reales ----
    for nombre in a.videos:
        t0 = time.time()
        video = str(RAIZ / VIDEOS[nombre])
        idxs, xs, xe = fotogramas_quietos(nombre, a.n_fotogramas)
        print(f"\n=== {nombre}  ROI {xs}-{xe}  fotogramas quietos {idxs} ===", flush=True)
        max_proj = io_utils.compute_max_projection(video, stride=5)
        roi = preprocessing.auto_detect_roi(max_proj, x_start=xs, x_end=xe, n_columns=CFG.n_columns)
        frames = leer_fotogramas(video, idxs)
        for i, f in frames.items():
            med = Medidor(f.astype(float), roi, xs, xe)
            m = mascara_franja(f.shape, roi["top_guess"], roi["bottom_guess"], xs, xe)
            base = {"caso": nombre, "fotograma": i}
            for s in DESPLAZ:
                filas.append({**base, "variante": "rigido", "s": s, **med.medir(corrimiento_interp(f, s))})
                filas.append({**base, "variante": "blur", "s": s, **med.medir(corrimiento_blur(f, s))})
                filas.append({**base, "variante": "franja", "s": s, **med.medir(corrimiento_franja(f, s, m))})
            for s in ENTEROS:
                filas.append({**base, "variante": "rigido_entero", "s": float(s),
                              **med.medir(corrimiento_entero(f, s))})
        print(f"  listo en {time.time() - t0:.0f} s", flush=True)

    df = pd.DataFrame(filas)
    df.to_csv(salida / "mediciones.csv", index=False)
    res = resumir(df)
    res.to_csv(salida / "resumen.csv", index=False)

    # tabla compacta: medido por s (mediana entre fotogramas), metodo x variante
    piv = (df.groupby(["caso", "variante", "s"])[["bordes_clahe", "bordes_crudo", "correlacion"]]
             .median().round(3))
    md = ["# Fase 3, tema 7 (H51): desplazamiento conocido\n",
          "Pendiente = medido / verdadero (1.0 = mide bien). En blur la posicion final es s y la media s/2.\n",
          "```\n" + res.to_string(index=False) + "\n```\n",
          "## Medido por desplazamiento (mediana entre fotogramas)\n",
          "```\n" + piv.to_string() + "\n```\n"]
    (salida / "resumen_magnitud.md").write_text("\n".join(md), encoding="utf-8")
    print(res.to_string(index=False))
    print(f"\nResumen: {salida / 'resumen_magnitud.md'}")


if __name__ == "__main__":
    main()
