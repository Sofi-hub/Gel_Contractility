"""
plotting.py
------------
Figura 01 (la serie temporal de main.py). Las figuras 02, 03, 04 y 06 eran
del detector viejo (event_detection.py) y se borraron junto con él el 2026-10-01; la
05 (escaneo del umbral) y las 09-11 las genera scripts/contraction_report.py.

Devuelve la ruta del archivo escrito.
"""

from __future__ import annotations
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def _save(fig, out_dir: Path, name: str, dpi=140) -> Path:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    p = out_dir / f"{name}.png"
    fig.tight_layout()
    fig.savefig(p, dpi=dpi)
    plt.close(fig)
    return p


def plot_timeseries(df, out_dir, unit_label="px", calibrated=False,
                    time_col="time_s", raw_col="thickness_px",
                    smooth_col="thickness_mm_smooth", name="01_serie_temporal") -> Path:
    """Curva de grosor vs tiempo, sin anotaciones."""
    t = df[time_col].to_numpy()
    fig, ax = plt.subplots(figsize=(11, 4))
    ax.plot(t, df[raw_col], color="lightgray", lw=0.7, label="Grosor crudo")
    if smooth_col in df.columns:
        ax.plot(t, df[smooth_col], color="crimson", lw=1.1, label="Suavizado")
    ax.set_xlabel("Tiempo (s)")
    ax.set_ylabel(f"Grosor ({unit_label})")
    ax.set_title("Grosor del gel vs tiempo" + ("" if calibrated else "  —  SIN CALIBRAR (píxeles)"))
    ax.legend(fontsize=8)
    return _save(fig, out_dir, name)
