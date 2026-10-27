"""Cinética (TTP / RT50) desde la RESPUESTA FORZADA (2026-10-26). Solo medición:
no toca el análisis ni escribe en data/processed_data.

Pregunta: en los videos NO REPORTABLES la respuesta forzada (src/forzada.py) dice
si hay respuesta y cuánto, pero no da TTP ni RT50 porque no hay contracciones
detectadas. ¿Se pueden sacar de la FORMA PROMEDIO de los pulsos?

Método (las reglas son las de src/cinetica.py, no se inventa ninguna):
  1. Señal: center_px sin deriva (mediana móvil de 2 s), igual que forzada.
  2. Período, fase y sentido: los que calcula src.forzada.respuesta_forzada con
     el período nominal 1/0.1 Hz y búsqueda a +-2 %, igual que el reporte.
  3. Forma promedio: cada pulso se recorta de -1.5 a +2.5 s alrededor de su
     instante, se le resta su propia línea de base (mediana de -1.2 a -0.4 s,
     la misma ventana que usa forzada para la amplitud) y se promedian.
  4. TTP y RT50 sobre esa forma con cinetica_eventos: pico = primer fotograma
     >= 95 % del máximo; valor solo si la subida (o la bajada al 50 %) abarca
     >= 5 fotogramas; si no, la cota.
  5. IC 95 %: bootstrap de los PULSOS (se re-sortean con reposición, se vuelve a
     promediar y a medir; percentiles 2.5 y 97.5), como ic95_mediana.
  6. También TTP / RT50 pulso por pulso (mediana de los medibles), para ver si
     el promedio esconde algo.
  7. Control: lo mismo en videos reportables, contra el TTP/RT50 del reporte.
  8. Dos sensibilidades: usar TODOS los pulsos esperados o solo los que
     responden (forzada ya marca cuáles), y quitar la deriva con 2 s o con 4 s
     (una mediana de 2 s podría comerse parte de la relajación y acortar RT50).

    python data/_mediciones_fases/cinetica_forzada/cinetica_forzada.py
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(RAIZ))
from src.cinetica import cinetica_eventos, ic95_mediana   # noqa: E402
from src.estadistica import detrend_median                # noqa: E402
from src.forzada import respuesta_forzada                 # noqa: E402

AQUI = Path(__file__).resolve().parent
P = RAIZ / "data" / "processed_data"
FREC_HZ = 0.1
LAG_ANTES, LAG_DESPUES = 1.5, 2.5     # s de recorte alrededor de cada pulso
BASE = (-1.2, -0.4)                   # línea de base de cada pulso (la de forzada)
VENTANA_PICO = (-0.4, 0.6)            # dónde se busca el máximo del pulso
N_BOOT = 2000
WIN_DETREND = 2.0                     # s (el de forzada); la sensibilidad usa 4 s

VIDEOS = [
    # (carpeta, nombre corto, grupo)
    ("10V_2", "10V_2", "NO REPORTABLE"),
    ("10V_3", "10V_3", "NO REPORTABLE"),
    ("20V_1", "20V_1", "NO REPORTABLE"),
    ("20V_2", "20V_2", "NO REPORTABLE"),
    ("40V_2", "40V_2", "NO REPORTABLE"),
    ("10V_1", "10V_1", "control reportable"),
    ("20V_3", "20V_3", "control reportable"),
    ("40V_1", "40V_1", "control reportable"),
    ("40V_3", "40V_3", "control reportable"),
    ("Video_466_EXP5_FAPS4_40V", "466", "control reportable"),
    ("Video_583_EXP6_CTRL4_40V", "583", "control reportable"),
]


# ---------------------------------------------------------------- lectura
def leer(carpeta):
    s = next((P / carpeta).glob("serie_temporal_*.xlsx"))
    h = pd.read_excel(s, sheet_name=None)
    d = h["diagnostics"]
    meta = dict(zip(h["resumen"].iloc[:, 0].astype(str), h["resumen"].iloc[:, 1]))
    g = float(meta.get("grosor medio (px)", np.nan))
    if not np.isfinite(g):
        g = float(np.nanmedian(d["thickness_px"]))
    return d["time_s"].to_numpy(float), d["center_px"].to_numpy(float), g


def resumen_reporte(carpeta):
    """Lo que ya informa el reporte de ese video (para el control)."""
    con = sorted((P / carpeta).glob("contracciones_*.xlsx"))
    if not con:
        return {}
    h = pd.read_excel(con[0], sheet_name=None)
    hojas = [k for k in h if k.startswith("resumen")]
    if not hojas:
        return {}
    return h[hojas[0]].iloc[0].to_dict()


# ------------------------------------------------- forma promedio y cinética
def recortes(t, r, instantes, sg, dt):
    """Un recorte por pulso, alineado en su instante y sin su línea de base."""
    lag = np.arange(-LAG_ANTES, LAG_DESPUES + 1e-9, dt)
    base = (lag >= BASE[0]) & (lag <= BASE[1])
    out = []
    for t0 in instantes:
        y = np.interp(t0 + lag, t, sg * r, left=np.nan, right=np.nan)
        if not np.isfinite(y).all():
            continue                      # el pulso se sale del video
        out.append(y - np.median(y[base]))
    return lag, np.asarray(out)


def medir_forma(lag, y, dt):
    """TTP / RT50 de UNA forma con las reglas de src/cinetica.py."""
    base = (lag >= BASE[0]) & (lag <= BASE[1])
    ruido = 1.4826 * float(np.median(np.abs(y[base] - np.median(y[base]))))
    v = (lag >= VENTANA_PICO[0]) & (lag <= VENTANA_PICO[1])
    p = int(np.flatnonzero(v)[np.argmax(y[v])])
    ev = cinetica_eventos(lag, y, np.array([p]), ruido).iloc[0]
    return ev, float(y[p]), ruido


def ic_bootstrap(lag, ys, dt, semilla=0):
    """IC 95 % de TTP y RT50 re-sorteando los pulsos (con reposición)."""
    if len(ys) < 3:
        return {}
    rng = np.random.default_rng(semilla)
    ttp, rt50 = [], []
    for _ in range(N_BOOT):
        s = ys[rng.integers(0, len(ys), len(ys))].mean(axis=0)
        try:
            ev, _, _ = medir_forma(lag, s, dt)
        except (ValueError, IndexError):
            continue
        ttp.append(ev["ttp_s"])
        rt50.append(ev["rt50_s"])
    out = {}
    for nom, v in (("ttp", ttp), ("rt50", rt50)):
        v = np.asarray(v, float)
        v = v[np.isfinite(v)]
        if len(v) >= 0.5 * N_BOOT:
            lo, hi = np.percentile(v, [2.5, 97.5])
            out[f"{nom}_ic95_ms"] = f"{1000 * lo:.0f}-{1000 * hi:.0f}"
        else:
            out[f"{nom}_ic95_ms"] = None
    return out


def analizar(carpeta, nombre, grupo, win_detrend=WIN_DETREND, solo_responden=False):
    t, x, grosor = leer(carpeta)
    dt = float(np.median(np.diff(t)))
    fps = 1.0 / dt
    f = respuesta_forzada(t, x, grosor, 1.0 / FREC_HZ, buscar=True)
    sg = 1.0 if f["forzada_sentido"] == "abajo" else -1.0
    r = detrend_median(x, fps, win_detrend)
    # un pulso "responde" si su amplitud supera el percentil 95 de los controles
    # (lo decide forzada). Los que no responden son instantes en los que el gel
    # no se movió: promediarlos achata y ensancha la forma.
    instantes = [p[0] for p in f["_forzada_pulsos"] if p[2] or not solo_responden]
    lag, ys = recortes(t, r, instantes, sg, dt)
    if len(ys) < 2:
        return None, None, None, None
    forma = ys.mean(axis=0)
    ev, amp, ruido = medir_forma(lag, forma, dt)
    fila = {
        "video": nombre, "grupo": grupo, "win_detrend_s": win_detrend,
        "pulsos_usados": "solo los que responden" if solo_responden else "todos",
        "periodo_s": round(f["forzada_periodo_s"], 3), "p_forzada": round(f["forzada_p"], 4),
        "hay_respuesta": bool(f["forzada_hay_respuesta"]),
        "n_pulsos": len(ys), "n_pulsos_forzada": f["forzada_n_pulsos"],
        "amplitud_px": round(amp, 3),
        "amplitud_pct": round(100 * amp / grosor, 4) if grosor else np.nan,
        "amplitud_forzada_px": (round(f["forzada_amplitud_px"], 3)
                                if np.isfinite(f["forzada_amplitud_px"]) else None),
        "ruido_forma_px": round(ruido, 4),
        "ttp_frames": ev["ttp_frames"], "ttp_medible": bool(ev["ttp_medible"]),
        "ttp_ms": round(1000 * ev["ttp_s"], 1) if np.isfinite(ev["ttp_s"]) else None,
        "ttp_cota_ms": round(1000 * ev["ttp_max_s"], 1) if np.isfinite(ev["ttp_max_s"]) else None,
        "rt50_frames": ev["rt50_frames"], "rt50_medible": bool(ev["rt50_medible"]),
        "rt50_ms": round(1000 * ev["rt50_s"], 1) if np.isfinite(ev["rt50_s"]) else None,
        "rt50_cota_ms": round(1000 * ev["rt50_max_s"], 1) if np.isfinite(ev["rt50_max_s"]) else None,
    }
    fila.update(ic_bootstrap(lag, ys, dt))

    # --- pulso por pulso -------------------------------------------------
    pulsos = []
    for i, y in enumerate(ys, 1):
        try:
            e, a, _ = medir_forma(lag, y, dt)
        except (ValueError, IndexError):
            continue
        pulsos.append({"video": nombre, "grupo": grupo, "win_detrend_s": win_detrend,
                       "pulsos_usados": fila["pulsos_usados"],
                       "pulso": i, "instante_s": round(instantes[i - 1], 2),
                       "amplitud_px": round(a, 3),
                       "ttp_frames": e["ttp_frames"], "ttp_medible": bool(e["ttp_medible"]),
                       "ttp_ms": round(1000 * e["ttp_s"], 1) if np.isfinite(e["ttp_s"]) else None,
                       "rt50_frames": e["rt50_frames"], "rt50_medible": bool(e["rt50_medible"]),
                       "rt50_ms": round(1000 * e["rt50_s"], 1) if np.isfinite(e["rt50_s"]) else None})
    # mediana pulso a pulso, con las mismas reglas del reporte: solo los
    # medibles, y solo se emite si lo es al menos la mitad de los pulsos
    for m in ("ttp", "rt50"):
        v = [p[f"{m}_ms"] for p in pulsos if p[f"{m}_medible"] and p[f"{m}_ms"] is not None]
        con_cruce = [p for p in pulsos if p[f"{m}_ms"] is not None]
        fila[f"{m}_pulsos_n_medibles"] = len(v)
        fila[f"{m}_pulsos_n_con_cruce"] = len(con_cruce)
        fila[f"{m}_pulsos_mitad"] = bool(v and len(v) >= 0.5 * len(con_cruce))
        fila[f"{m}_pulsos_mediana_ms"] = round(float(np.median(v)), 1) if v else None
        ic = ic95_mediana(np.array(v, float) / 1000.0) if len(v) >= 3 else None
        fila[f"{m}_pulsos_ic95_ms"] = ("-".join(f"{1000 * float(x):.0f}" for x in ic.split("-"))
                                       if ic else None)
    return fila, pulsos, lag, (forma, ys)


# ------------------------------------------------------------------- salida
def comparar_con_reporte(fila, carpeta):
    """Para los controles: ¿coincide con el TTP/RT50 que ya informa el reporte?"""
    d = resumen_reporte(carpeta)
    for m in ("ttp", "rt50"):
        rep = d.get(f"{m}_s")
        rep_ok = bool(d.get(f"{m}_reportable", False))
        fila[f"{m}_reporte_ms"] = round(1000 * float(rep), 1) if rep_ok and pd.notna(rep) else None
        fila[f"{m}_reporte_cota_ms"] = (round(1000 * float(d[f"{m}_cota_sup_s"]), 1)
                                        if pd.notna(d.get(f"{m}_cota_sup_s")) else None)
        for col, v in (("coincide", fila.get(f"{m}_ms")),
                       ("coincide_pulsos", fila.get(f"{m}_pulsos_mediana_ms"))):
            b = fila[f"{m}_reporte_ms"]
            fila[f"{m}_{col}"] = "—" if v is None or b is None else f"{100 * (v - b) / b:+.0f} %"
    fila["conteo_reportable"] = bool(d.get("conteo_reportable", False))
    fila["n_eventos_reporte"] = d.get("n_eventos")
    return fila


def figura(datos, destino):
    import matplotlib
    matplotlib.use("Agg")
    from matplotlib.figure import Figure
    n = len(datos)
    cols = 4
    filas = int(np.ceil(n / cols))
    fig = Figure(figsize=(3.4 * cols, 2.6 * filas), dpi=130)
    for k, (nombre, grupo, lag, forma, ys, fila) in enumerate(datos):
        ax = fig.add_subplot(filas, cols, k + 1)
        for y in ys:
            ax.plot(lag, y, color="#b9c3cf", lw=0.7)
        ax.plot(lag, forma, color="#d62728", lw=1.8)
        ax.axvline(0, color="#999", lw=0.6, ls=":")
        ax.axhline(0, color="#999", lw=0.5)
        ttp = f"{fila['ttp_ms']:.0f} ms" if fila["ttp_medible"] else f"< {fila['ttp_cota_ms']:.0f}"
        rt = f"{fila['rt50_ms']:.0f} ms" if fila["rt50_medible"] else f"< {fila['rt50_cota_ms']:.0f}"
        ax.set_title(f"{nombre} ({grupo})\n{fila['n_pulsos']} pulsos · TTP {ttp} · RT50 {rt}",
                     fontsize=8)
        ax.tick_params(labelsize=7)
        ax.grid(alpha=0.25)
        if k % cols == 0:
            ax.set_ylabel("px (sentido del pulso)", fontsize=7)
        if k >= n - cols:
            ax.set_xlabel("s desde el instante del estimulador", fontsize=7)
    fig.suptitle("Forma promedio de los pulsos que responden (gris: cada pulso) · deriva de 2 s",
                 fontsize=10)
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    fig.savefig(destino)
    return destino


COMBOS = [(WIN_DETREND, False), (WIN_DETREND, True), (4.0, False), (4.0, True)]
PRINCIPAL = (WIN_DETREND, True)      # el que se recomienda: deriva de 2 s, solo los que responden


def main():
    filas, pulsos, para_figura = [], [], []
    for carpeta, nombre, grupo in VIDEOS:
        if not (P / carpeta).is_dir():
            print(f"{nombre}: no está"); continue
        for win, solo in COMBOS:
            fila, pul, lag, fy = analizar(carpeta, nombre, grupo, win, solo)
            if fila is None:
                print(f"{nombre}: menos de 2 pulsos enteros"); break
            fila = comparar_con_reporte(fila, carpeta)
            filas.append(fila)
            pulsos += pul
            if (win, solo) == PRINCIPAL:
                para_figura.append((nombre, grupo, lag, fy[0], fy[1], fila))
                ttp = (f"{fila['ttp_ms']:.0f} ms" if fila["ttp_medible"]
                       else f"< {fila['ttp_cota_ms']:.0f} ms (cota)")
                rt = (f"{fila['rt50_ms']:.0f} ms" if fila["rt50_medible"]
                      else f"< {fila['rt50_cota_ms']:.0f} ms (cota)")
                print(f"{nombre:7s} {grupo:19s} {fila['n_pulsos']}/{fila['n_pulsos_forzada']} pulsos | "
                      f"ampl {fila['amplitud_px']:5.2f} px | promedio: TTP {ttp:18s} "
                      f"IC {str(fila.get('ttp_ic95_ms')):9s} RT50 {rt:18s} IC {str(fila.get('rt50_ic95_ms')):9s}"
                      f" | por pulso: TTP {str(fila['ttp_pulsos_mediana_ms']):6s} "
                      f"({fila['ttp_pulsos_n_medibles']} medibles) RT50 {str(fila['rt50_pulsos_mediana_ms']):6s} "
                      f"({fila['rt50_pulsos_n_medibles']})"
                      + (f" | REPORTE TTP {fila['ttp_reporte_ms']} RT50 {fila['rt50_reporte_ms']}"
                         f" -> promedio {fila['ttp_coincide']}/{fila['rt50_coincide']}, "
                         f"por pulso {fila['ttp_coincide_pulsos']}/{fila['rt50_coincide_pulsos']}"
                         if grupo.startswith("control") else ""))
    pd.DataFrame(filas).to_csv(AQUI / "cinetica_forzada.csv", index=False)
    pd.DataFrame(pulsos).to_csv(AQUI / "pulsos.csv", index=False)
    figura(para_figura, AQUI / "formas.png")
    print(f"\ntablas: cinetica_forzada.csv ({len(filas)} filas), pulsos.csv ({len(pulsos)}); figura: formas.png")


if __name__ == "__main__":
    main()
