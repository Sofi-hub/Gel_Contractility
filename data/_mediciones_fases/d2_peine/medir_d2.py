"""D2 / H52: ¿el "peine" de compresión (salto de |dI| cada 5-10 fotogramas) aparece
en todos los videos? ¿Lo arrastran los bordes?

Entradas (no se recalcula el análisis):
  - movimiento_<video>.xlsx de d1_d2_intensidad/ (motion_check.py sin cambios):
    mov_fondo = |I(t)-I(t-1)| medio en una franja de FONDO (sin gel).
  - tipos_<video>.csv: tipo de cada fotograma comprimido (I, P o B) y su tamaño,
    sacados con ffprobe (ffprobe -select_streams v:0 -show_entries
    frame=pkt_size,pict_type -of csv=p=0).
  - la serie vigente (center_px), para ver si el peine pasa a los bordes.

Por video:
  periodo_peine     retardo (2..15 fotogramas) con la autocorrelación más alta de
                    la DIFERENCIA de mov_fondo (sin lo lento)
  autocorr_peine    esa autocorrelación (0 = sin peine)
  P_sobre_B_fondo   mov_fondo medio en fotogramas P (e I) / en fotogramas B
  P_sobre_B_center  lo mismo con |dcenter_px| (¿los bordes ven el peine?)
  periodo_P         cada cuántos fotogramas hay un P o I (mediana)

    python data/_mediciones_fases/d2_peine/medir_d2.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[2]
sys.path.insert(0, str(RAIZ)); sys.path.insert(0, str(RAIZ / "tests"))
import referencia as ref                                   # noqa: E402
from src.estadistica import detrend_median                 # noqa: E402
from src.output_paths import buscar_serie                  # noqa: E402

MOV = RAIZ / "data/_mediciones_fases/d1_d2_intensidad"


def acf(x, lag):
    x = x[np.isfinite(x)]
    x = x - x.mean()
    return float(np.dot(x[:-lag], x[lag:]) / np.dot(x, x))


def main():
    filas = []
    for carpeta, (video, _, _) in ref.VIDEOS.items():
        stem = Path(video).stem
        mv = MOV / carpeta / f"movimiento_{stem}.xlsx"
        tp = AQUI / f"tipos_{stem}.csv"
        if not (mv.exists() and tp.exists()):
            print("falta", carpeta); continue
        m = pd.read_excel(mv, sheet_name="movimiento")
        tipos = pd.read_csv(tp, header=None, usecols=[0, 1], names=["bytes", "tipo"]).reset_index()
        tipos = tipos.rename(columns={"index": "frame"})
        tipos["tipo"] = tipos["tipo"].astype(str).str.strip()
        st = pd.read_excel(buscar_serie(RAIZ / "data/processed_data" / carpeta),
                           sheet_name="diagnostics")[["frame", "center_px"]]
        d = m.merge(tipos, on="frame", how="left").merge(st, on="frame", how="left")
        fps = 1 / np.median(np.diff(d.time_s))
        f = d.mov_fondo.to_numpy(float)
        fr = f - detrend_median(f, fps)
        lags = range(2, 16)
        ac = [acf(np.diff(fr), L) for L in lags]   # sobre la diferencia: saca lo lento
        k = int(np.argmax(ac))
        dc = np.abs(np.diff(d.center_px.to_numpy(float), prepend=np.nan))
        es_p = d.tipo.isin(["P", "I"]).to_numpy()
        es_b = (d.tipo == "B").to_numpy()
        pos_p = np.flatnonzero(es_p)
        # fase dentro del patron: fotogramas desde el ultimo P/I
        fase = np.zeros(len(d), int); ult = -10**9
        for i in range(len(d)):
            if es_p[i]:
                ult = i
            fase[i] = min(i - ult, 9)
        cr = d.center_px.to_numpy(float)
        cr = cr - detrend_median(cr, fps, 0.5)      # solo lo rapido
        prom_c = pd.Series(cr).groupby(fase).mean()
        prom_f = pd.Series(fr).groupby(fase).mean()
        ruido_c = float(np.nanstd(cr))
        fila = {
            "video": carpeta, "grupo": "RARITOS" if "RARITOS" in video else ("OK" if "OK" in video else "prueba"),
            "n_frames_mov": len(m), "n_frames_ffprobe": len(tipos),
            "tipos": " ".join(f"{t}:{n}" for t, n in tipos.tipo.value_counts().items()),
            "periodo_P": float(np.median(np.diff(pos_p))) if len(pos_p) > 2 else np.nan,
            "periodo_peine": list(lags)[k], "autocorr_peine": ac[k],
            "P_sobre_B_fondo": np.nanmean(f[es_p]) / np.nanmean(f[es_b]),
            "P_sobre_B_gel": np.nanmean(d.mov_gel.to_numpy(float)[es_p]) / np.nanmean(d.mov_gel.to_numpy(float)[es_b]),
            "P_sobre_B_center": np.nanmedian(dc[es_p]) / np.nanmedian(dc[es_b]),
            "bytes_P_sobre_B": d.bytes[es_p].mean() / d.bytes[es_b].mean(),
            # cuanto se mueve center_px en promedio segun la fase del patron P/B (px),
            # comparado con su ruido rapido: si el peine pasara a los bordes, se veria aca
            "center_peine_pp_px": float(prom_c.max() - prom_c.min()),
            "center_ruido_rapido_px": ruido_c,
            "center_peine_sobre_ruido": float(prom_c.max() - prom_c.min()) / ruido_c,
            "fondo_peine_pp": float(prom_f.max() - prom_f.min()),
            "fondo_ruido": float(np.nanstd(fr)),
        }
        filas.append(fila)
        print({k: (round(v, 3) if isinstance(v, float) else v) for k, v in fila.items()}, flush=True)
    df = pd.DataFrame(filas)
    df.to_csv(AQUI / "tabla_d2.csv", index=False)
    print(df.round(3).drop(columns=["tipos"]).to_string(index=False))


if __name__ == "__main__":
    main()
