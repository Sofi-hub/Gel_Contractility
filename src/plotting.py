"""
plotting.py
------------
Cada gráfico principal se guarda como un PNG independiente. La única
figura multipanel es la comparación entre fragmentos temporales
(zoom de distintas zonas del video), donde ver los tramos juntos es
justamente el objetivo.

Todas las funciones devuelven la ruta del archivo escrito.
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


def plot_events(df, result, events, out_dir, unit_label="px",
                time_col="time_s", raw_col="thickness_px",
                name="02_eventos_detectados") -> Path:
    """Señal con cada contracción marcada, coloreada por segmento."""
    t = df[time_col].to_numpy()
    fig, ax = plt.subplots(figsize=(12, 4.2))
    ax.plot(t, df[raw_col], color="lightgray", lw=0.7, label="Grosor crudo")
    ax.plot(t, result.signal, color="crimson", lw=1.0, alpha=0.85, label="Suavizado")
    ax.plot(t, result.baseline, color="steelblue", lw=0.9, ls="--", alpha=0.75,
            label="Estado relajado")
    if len(events):
        seg_col = "segmento" if "segmento" in events.columns else None
        if seg_col:
            cmap = plt.get_cmap("tab10")
            for i, s in enumerate(sorted(events[seg_col].unique())):
                sub = events[events[seg_col] == s]
                ax.scatter(sub.tiempo_s, sub.grosor_minimo_px, s=40, marker="v",
                           color=cmap(i % 10), edgecolor="black", linewidth=0.4,
                           zorder=5, label=f"Segmento {s} (n={len(sub)})")
        else:
            ax.scatter(events.tiempo_s, events.grosor_minimo_px, s=40, marker="v",
                       color="black", zorder=5, label="Contracción")
    ax.set_xlabel("Tiempo (s)")
    ax.set_ylabel(f"Grosor ({unit_label})")
    ax.set_title(f"{len(events)} contracciones detectadas "
                 f"(umbral {result.amp_threshold_px:.3f} {unit_label})")
    ax.legend(fontsize=7, ncol=3)
    return _save(fig, out_dir, name)


def plot_amplitudes(events, result, out_dir, unit_label="px",
                    name="03_amplitudes") -> Path:
    """Amplitud de cada evento en el tiempo + histograma.
    Dos poblaciones separadas aquí indican eventos de distinto tipo."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 3.6),
                                   gridspec_kw={"width_ratios": [3, 1]})
    if len(events):
        ax1.vlines(events.tiempo_s, 0, events.amplitud_px, color="steelblue", lw=1)
        ax1.scatter(events.tiempo_s, events.amplitud_px, s=26, color="crimson", zorder=5)
        ax2.hist(events.amplitud_px, bins=max(6, len(events) // 3),
                 orientation="horizontal", color="steelblue", edgecolor="white")
    ax1.axhline(result.amp_threshold_px, color="gray", ls=":", lw=1,
                label=f"umbral ({result.amp_threshold_px:.3f})")
    ax1.set_xlabel("Tiempo (s)"); ax1.set_ylabel(f"Amplitud ({unit_label})")
    ax1.set_title("Amplitud por contracción"); ax1.legend(fontsize=7)
    ax2.set_xlabel("N eventos"); ax2.set_title("Distribución", fontsize=9)
    return _save(fig, out_dir, name)


def plot_frequency_profile(freq_df, out_dir, name="04_perfil_frecuencia",
                           window_s=None) -> Path:
    """Período dominante en ventana móvil (independiente de la
    detección de eventos)."""
    fig, ax = plt.subplots(figsize=(11, 3.4))
    ax.plot(freq_df.tiempo_s, freq_df.periodo_s, color="darkgreen", lw=1.2)
    ax.set_yscale("log")
    ax.set_xlabel("Tiempo (s)"); ax.set_ylabel("Período (s, escala log)")
    title = "Período dominante en ventana móvil"
    if window_s:
        title += f"  (ventana {window_s:g}s — no resuelve períodos > {window_s/2:g}s)"
    ax.set_title(title, fontsize=10)
    return _save(fig, out_dir, name)


def plot_threshold_stability(scan_df, out_dir, amp_k_used=None,
                             name="05_estabilidad_umbral") -> Path:
    """Conteo de eventos vs umbral. Una MESETA indica que los eventos
    son reales; un decaimiento monótono indica ruido."""
    fig, ax = plt.subplots(figsize=(7, 3.6))
    ax.plot(scan_df.k, scan_df.n_eventos, marker="o", color="darkslateblue")
    if amp_k_used is not None:
        ax.axvline(amp_k_used, color="crimson", ls="--", lw=1,
                   label=f"k usado = {amp_k_used:g}")
        ax.legend(fontsize=8)
    ax.set_xlabel("k (umbral = k × ruido)"); ax.set_ylabel("N eventos detectados")
    ax.set_title("Estabilidad del umbral — una meseta indica eventos reales", fontsize=10)
    ax.grid(alpha=0.3)
    return _save(fig, out_dir, name)


def plot_segment_comparison(df, result, events, out_dir, windows,
                            unit_label="px", time_col="time_s",
                            raw_col="thickness_px", name="06_comparacion_tramos") -> Path:
    """
    ÚNICA figura multipanel: compara fragmentos temporales del video
    lado a lado. Acá agrupar SÍ tiene sentido, porque el objetivo es
    la comparación visual entre tramos.

    `windows` : lista de (t0, t1).
    """
    t = df[time_col].to_numpy()
    n = len(windows)
    fig, axes = plt.subplots(n, 1, figsize=(11, 2.4 * n), squeeze=False)
    for ax, (x0, x1) in zip(axes[:, 0], windows):
        ax.plot(t, df[raw_col], color="lightgray", lw=0.8)
        ax.plot(t, result.signal, color="crimson", lw=1.2)
        ax.plot(t, result.baseline, color="steelblue", lw=0.9, ls="--", alpha=0.7)
        sub = events[(events.tiempo_s >= x0) & (events.tiempo_s <= x1)] if len(events) else events
        if len(sub):
            ax.scatter(sub.tiempo_s, sub.grosor_minimo_px, s=50, marker="v",
                       color="black", zorder=5)
        ax.set_xlim(x0, x1)
        ax.set_ylabel(f"Grosor ({unit_label})")
        ax.set_title(f"Tramo {x0:.1f}–{x1:.1f}s  ({len(sub)} eventos)", fontsize=9)
    axes[-1, 0].set_xlabel("Tiempo (s)")
    return _save(fig, out_dir, name)


def auto_windows_from_segments(seg_df, pad_frac=0.1, max_windows=4):
    """Elige una ventana de zoom por segmento detectado, para la
    figura de comparación de tramos."""
    ws = []
    for _, s in seg_df.head(max_windows).iterrows():
        span = max(s.t_fin_s - s.t_inicio_s, 1.0)
        pad = span * pad_frac
        ws.append((max(0.0, s.t_inicio_s - pad), s.t_fin_s + pad))
    return ws