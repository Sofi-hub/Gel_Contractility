"""D1: ¿la diferencia de tamaño intensidad/bordes (0.82-0.88) se da en toda la
tanda EXP5? ¿Es real o es un efecto de cómo se calcula?

Entrada: movimiento_<video>.xlsx que dejó correr_motion_check.sh (motion_check.py
sin cambios) y la serie vigente de cada video. No cambia nada.

El veredicto de motion_check usa la pendiente de mínimos cuadrados de
desp_vert_px (intensidad) contra center_px (bordes), las dos sin deriva (mediana
móvil de 2 s). Esa pendiente SUBESTIMA si center_px tiene ruido propio
("atenuación por regresión"): sale var(señal)/(var(señal)+var(ruido)) veces la
verdadera. Por eso se calcula el mismo cociente de otras formas:

  ols          la de motion_check (dv ~ c)
  ols_inversa  1 / pendiente de (c ~ dv): sesgada hacia ARRIBA por el ruido de dv
  desvios      std(dv)/std(c) (media geométrica de las dos anteriores)
  eventos      mediana, sobre los eventos del reporte, de
               (pico de dv) / (pico de c), cada uno medido como máximo en ±3
               fotogramas del pico menos la mediana de [-1.0, -0.3] s antes:
               no depende del ruido de fondo, solo de las contracciones.

Si `eventos` y `desvios` dan ~1 donde `ols` da 0.8, la diferencia no es del
gel sino del estimador.

    python data/_mediciones_fases/d1_d2_intensidad/medir_d1.py
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
from src.estadistica import detrend_median, mad            # noqa: E402
from src.output_paths import buscar_serie                  # noqa: E402

TANDA = {"Video_prueba": "?", "Video_063_CTRL1_5V": "(CTRL1)", "Video_268_EXP3_FAPS2_40V": "EXP3",
         "Video_466_EXP5_FAPS4_40V": "EXP5", "Video_476": "EXP5", "Video_491_EXP5_CTRL1_36HZ": "EXP5",
         "Video_583_EXP6_CTRL4_40V": "EXP6", "Video_613": "EXP6", "Video_068_hw30": "?",
         "Video_304": "EXP3", "Video_341": "EXP3"}


def main():
    filas = []
    for carpeta in ref.VIDEOS:
        mv = next((AQUI / carpeta).glob("movimiento_*.xlsx"), None)
        if mv is None:
            continue
        m = pd.read_excel(mv, sheet_name="movimiento")
        st = pd.read_excel(buscar_serie(RAIZ / "data/processed_data" / carpeta), sheet_name="diagnostics")
        d = m[["frame", "time_s", "desp_vert_px"]].merge(st[["frame", "center_px"]], on="frame")
        t = d.time_s.to_numpy(float)
        fps = 1 / np.median(np.diff(t))
        c = detrend_median(d.center_px.to_numpy(float), fps)
        dv = detrend_median(d.desp_vert_px.to_numpy(float), fps)
        ok = np.isfinite(c) & np.isfinite(dv)
        c0, v0 = c[ok], dv[ok]
        s = np.sign(np.dot(c0, v0))
        ols = s * np.dot(c0, v0) / np.dot(c0, c0)
        inv = s * np.dot(v0, v0) / np.dot(c0, v0)
        rho = abs(np.corrcoef(c0, v0)[0, 1])
        fila = {"video": carpeta, "tanda": TANDA.get(carpeta, "?"), "ols": ols, "ols_inversa": inv,
                "desvios": np.std(v0) / np.std(c0), "correlacion": rho,
                "ruido_c_px": mad(c0), "ruido_dv_px": mad(v0)}
        contr = next((RAIZ / "data/processed_data" / carpeta).glob("contracciones_*.xlsx"))
        h = pd.read_excel(contr, sheet_name=None)
        cin = next((v for k, v in h.items() if k.startswith("cinetica_")), pd.DataFrame())
        res = next(v for k, v in h.items() if k.startswith("resumen_")).iloc[0]
        fila["reportable"] = bool(res["conteo_reportable"])
        cocs = []
        if fila["reportable"] and len(cin):
            fr = d.frame.to_numpy()
            for _, e in cin.iterrows():
                i = int(np.searchsorted(fr, int(e["frame_pico"])))
                if i <= 0 or i >= len(fr):
                    continue
                pre = (t >= t[i] - 1.0) & (t <= t[i] - 0.3)
                w = slice(max(0, i - 3), i + 4)
                sc = np.sign(np.nanmedian(c[w]) - np.nanmedian(c[pre]))
                pc = np.nanmax(sc * (c[w] - np.nanmedian(c[pre])))
                pv = np.nanmax(s * sc * (dv[w] - np.nanmedian(dv[pre])))
                if pc > 0:
                    cocs.append(pv / pc)
        fila["n_eventos"] = len(cocs)
        fila["eventos"] = float(np.median(cocs)) if cocs else np.nan
        fila["eventos_IQR"] = (f"{np.percentile(cocs, 25):.2f}-{np.percentile(cocs, 75):.2f}"
                               if cocs else "")
        filas.append(fila)
    df = pd.DataFrame(filas)
    df.to_csv(AQUI / "tabla_d1.csv", index=False)
    print(df.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
