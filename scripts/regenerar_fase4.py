#!/usr/bin/env python
"""
regenerar_fase4.py  -  cierre de la Fase 4.

1. Archiva cada resultado vigente en data/processed_data/_superadas/<video>_v7
   (mueve, no borra; se niega si ya existe).
2. Corre main.py y contraction_report.py (0.1 Hz) sobre los seis videos.
3. Compara contra lo archivado y escribe data/fase4_regeneracion.md:
   - serie_temporal.xlsx (hoja diagnostics): tiene que ser IDENTICA (la Fase 4
     no toca la medicion; solo agrega filas a `resumen`).
   - contracciones.xlsx: n_eventos, k, amplitud, periodo, etc. iguales.

USO (desde la raiz del repo):   python scripts/regenerar_fase4.py
Tarda ~6 min por video.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
OK = "data/raw_videos/OK-20260904T142817Z-1-001/OK/"
VIDEOS = {
    "Video_prueba": "data/raw_videos/Video_prueba.mp4",
    "Video_063_CTRL1_5V": OK + "Video_063_CTRL1_5V.mp4",
    "Video_268_EXP3_FAPS2_40V": OK + "Video_268_EXP3_FAPS2_40V.mp4",
    "Video_466_EXP5_FAPS4_40V": OK + "Video_466_EXP5_FAPS4_40V.mp4",
    "Video_583_EXP6_CTRL4_40V": OK + "Video_583_EXP6_CTRL4_40V.mp4",
    "Video_491_EXP5_CTRL1_36HZ": OK + "Video_491_EXP5_CTRL1_36HZ.mp4",
}
CLAVES = ["n_eventos", "k_usado", "conteo_reportable", "meseta_k_rango", "ruido_canal_px",
          "amplitud_traslacion_px", "amplitud_relativa_pct", "win_s_usado",
          "eventos_junto_al_borde"]


def _hoja(x: dict, prefijo: str):
    k = [s for s in x if s.startswith(prefijo)]
    return x[k[0]] if k else None


def main():
    pd_dir = RAIZ / "data/processed_data"
    sup = pd_dir / "_superadas"
    for v in VIDEOS:
        if (sup / f"{v}_v7").exists():
            sys.exit(f"Ya existe {sup / (v + '_v7')}: no se archiva dos veces. Revisar a mano.")
    lineas = ["# Regeneración de la Fase 4\n"]
    for v, ruta in VIDEOS.items():
        viejo = sup / f"{v}_v7"
        shutil.move(str(pd_dir / v), str(viejo))
        print(f"\n=== {v}  (anterior archivado en {viejo})", flush=True)
        out = pd_dir / v
        subprocess.run([sys.executable, "main.py", "--video", ruta, "--output-dir", str(out),
                        "--base-tiempo", "pts"], cwd=RAIZ, check=True)
        subprocess.run([sys.executable, "scripts/contraction_report.py", "--input",
                        str(out / "serie_temporal.xlsx"), "--frecuencia-estimulo", "0.1"],
                       cwd=RAIZ, check=True)

        a = pd.read_excel(viejo / "serie_temporal.xlsx", sheet_name="diagnostics")
        b = pd.read_excel(out / "serie_temporal.xlsx", sheet_name="diagnostics")
        dif = []
        for c in a.columns:
            if c not in b:
                dif.append(f"falta {c}")
            elif a[c].dtype.kind in "fi":
                d = np.nanmax(np.abs(a[c].to_numpy(float) - b[c].to_numpy(float))) if len(a) == len(b) else np.inf
                if not d <= 1e-9:
                    dif.append(f"{c} (dif max {d:.3g})")
            elif not (a[c].astype(str).values == b[c].astype(str).values).all():
                dif.append(c)
        res_b = pd.read_excel(out / "serie_temporal.xlsx", sheet_name="resumen")
        em = res_b[res_b.iloc[:, 0].astype(str).str.contains("error de modelo|outlier_frac")]
        ca = _hoja(pd.read_excel(viejo / "contracciones.xlsx", sheet_name=None), "resumen")
        cb = _hoja(pd.read_excel(out / "contracciones.xlsx", sheet_name=None), "resumen")
        filas = []
        for k in CLAVES:
            va = ca[k].iloc[0] if (ca is not None and k in ca) else "—"
            vb = cb[k].iloc[0] if (cb is not None and k in cb) else "—"
            filas.append(f"| {k} | {va} | {vb} |")
        lineas += [f"## {v}\n",
                   "serie_temporal (diagnostics): " + ("**idéntica**" if not dif else "DIFERENTE: " + ", ".join(dif)),
                   "\n```\n" + em.to_string(index=False) + "\n```\n",
                   "| clave | antes | ahora |", "|---|---|---|", *filas, ""]
        (RAIZ / "data/fase4_regeneracion.md").write_text("\n".join(lineas), encoding="utf-8")
    print(f"\nlisto -> {RAIZ / 'data/fase4_regeneracion.md'}")


if __name__ == "__main__":
    main()
