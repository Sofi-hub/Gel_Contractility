"""main.py --metodo textura (src/textura.py, 2026-10-16).

1. Sintético de corrimiento CONOCIDO: una franja con textura (generada acá, no
   hace falta ningún video), corrida en vertical por desplazamiento subpíxel
   exacto (Fourier), con ruido y compresión mp4. Gel VERTICAL en el video, para
   probar también la rotación. Exige el corrimiento a +-5 % desde 0.5 px
   (pendiente medido/real en los fotogramas de cada pulso).
2. main.py --metodo textura escribe una serie que contraction_report lee, y
   encuentra los pulsos en su lugar.
3. La ventana/carpeta pasa --metodo textura, y el paso 3 no se permite con textura.

    python tests/test_textura.py
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

import cv2
import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
from src import textura  # noqa: E402
import interfaz  # noqa: E402

FPS, PER = 30.0, 4.0
AMPS = [0.5, 1.0, 2.0, 4.0, -1.0]


def imagen_franja(h=360, w=480, seed=1, z=1):
    """Franja horizontal brillante con textura granulada, fondo oscuro con textura.
    z = cuantas veces mas grande (z=2: el mismo gel visto a doble resolucion)."""
    h, w = h * z, w * z
    rng = np.random.default_rng(seed)
    tex = cv2.GaussianBlur(rng.normal(0, 1, (h, w)).astype(np.float32), (0, 0), 2.0 * z)
    y = np.arange(h)[:, None]
    banda = 1 / (1 + np.exp(-(y - 110 * z) / (6.0 * z))) - 1 / (1 + np.exp(-(y - 250 * z) / (6.0 * z)))
    return 40 + 110 * banda + 25 * tex * (0.4 + banda)


def video_sintetico(ruta: Path, z=1):
    img = imagen_franja(z=z)
    h, w = img.shape
    n = int(FPS * PER * (len(AMPS) + 1))
    t = np.arange(n) / FPS
    forma = lambda s: np.where(s < 0, 0, np.where(s < 0.1, s / 0.1, np.exp(-(s - 0.1) / 0.3)))
    d = z * sum(A * forma(t - PER * (j + 1)) for j, A in enumerate(AMPS))
    F = np.fft.fft(img, axis=0)
    ky = np.fft.fftfreq(h)[:, None]
    rng = np.random.default_rng(0)
    vw = cv2.VideoWriter(str(ruta), cv2.VideoWriter_fourcc(*"mp4v"), FPS, (h, w), False)
    for i in range(n):
        g = np.real(np.fft.ifft(F * np.exp(-2j * np.pi * ky * d[i]), axis=0)) + rng.normal(0, 2, (h, w))
        # gel VERTICAL en el video: se guarda girado 90° antihorario
        vw.write(cv2.rotate(np.clip(g, 0, 255).astype(np.uint8), cv2.ROTATE_90_COUNTERCLOCKWISE))
    vw.release()
    return d / z     # corrimiento en px de la imagen z=1 (lo que se compara)


def main():
    fallos = []
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        v = tmp / "sint_textura.mp4"
        d = video_sintetico(v)

        # 1. corrimiento conocido
        m = textura.medir(v, rotacion=90)
        dy = m["dy"] - np.median(m["dy"][: int(FPS * 3)])
        # por pulso: pendiente medido/real sobre los fotogramas del pulso (|real| > 20 % de A),
        # asi el ruido de un solo fotograma (compresion) no decide
        for j, A in enumerate(AMPS):
            t0 = PER * (j + 1)
            sel = (np.arange(len(d)) / FPS >= t0) & (np.arange(len(d)) / FPS < t0 + 1.5) & (np.abs(d) > 0.2 * abs(A))
            coc = float(np.sum(dy[sel] * d[sel]) / np.sum(d[sel] ** 2))
            ok = abs(coc - 1) <= 0.05
            print(f"  corrimiento {A:+.2f} px: medido/real {coc:.3f} ({sel.sum()} fotogramas) {'OK' if ok else 'FALLA'}")
            if not ok:
                fallos.append(f"corrimiento {A}: cociente {coc:.3f}")
        # 1b. video "grande" (el mismo gel a doble resolucion, 960 px): con LADO_MAX = 480
        # se mide achicado a la mitad y se informa en px del ORIGINAL (el doble)
        v2 = tmp / "sint_grande.mp4"
        d2 = 2 * video_sintetico(v2, z=2)            # px del video grande
        viejo = textura.LADO_MAX
        textura.LADO_MAX = 480
        try:
            mm = textura.medir(v2, rotacion=90)
        finally:
            textura.LADO_MAX = viejo
        dd = mm["dy"] - np.median(mm["dy"][: int(FPS * 3)])
        sel = np.abs(d2) > 1.0
        coc = float(np.sum(dd[sel] * d2[sel]) / np.sum(d2[sel] ** 2))
        print(f"  video grande, medido achicado x{mm['escala']:.2f}: medido/real {coc:.3f}, "
              f"grosor {mm['grosor_px']:.0f} px (esperado ~280)")
        textura.LADO_MAX = 480
        try:
            mc = textura.medir(v2, rotacion=90, resolucion_completa=True)
        finally:
            textura.LADO_MAX = viejo
        dc = mc["dy"] - np.median(mc["dy"][: int(FPS * 3)])
        cc = float(np.sum(dc[sel] * d2[sel]) / np.sum(d2[sel] ** 2))
        print(f"  el mismo con --resolucion-completa (escala {mc['escala']:.0f}): medido/real {cc:.3f}")
        if mc["escala"] != 1.0 or abs(cc - 1) > 0.05:
            fallos.append(f"resolucion completa: escala {mc['escala']}, cociente {cc:.3f}")
        if mm["escala"] != 0.5 or abs(coc - 1) > 0.05 or abs(mm["grosor_px"] - 280) > 30:
            fallos.append(f"achicado: escala {mm['escala']}, cociente {coc:.3f}, grosor {mm['grosor_px']:.0f}")
        if not (abs(m["grosor_px"] - 140) < 15):
            fallos.append(f"grosor aproximado {m['grosor_px']:.0f} (esperado ~140)")

        # 2. main.py --metodo textura + contraction_report (gel vertical: rotación automática)
        out = tmp / "res"
        r1 = subprocess.run([sys.executable, str(RAIZ / "main.py"), "--video", str(v),
                             "--metodo", "textura", "--output-dir", str(out)],
                            capture_output=True, text=True)
        if r1.returncode != 0:
            fallos.append("main.py --metodo textura fallo: " + r1.stderr[-400:])
        else:
            serie = out / "serie_temporal_sint_textura.xlsx"
            h = pd.read_excel(serie, sheet_name=None)
            meta = dict(zip(h["resumen"]["Métrica"], h["resumen"]["Valor"]))
            if meta.get("metodo") != "textura" or int(meta.get("rotacion (grados)")) != 90:
                fallos.append(f"resumen: metodo {meta.get('metodo')}, rotacion {meta.get('rotacion (grados)')}")
            if not (out / "00_franja_textura_sint_textura.png").is_file():
                fallos.append("falta la figura 00_franja_textura")
            r2 = subprocess.run([sys.executable, str(RAIZ / "scripts" / "contraction_report.py"),
                                 "--input", str(serie)], capture_output=True, text=True)
            if r2.returncode != 0:
                fallos.append("contraction_report fallo: " + r2.stderr[-400:])
            else:
                xl = pd.read_excel(next(out.glob("contracciones_*.xlsx")), sheet_name=None)
                ev = next(v_ for k, v_ in xl.items() if k.startswith("eventos"))
                esperados = [PER * (j + 1) + 0.1 for j, A in enumerate(AMPS) if A > 0]
                t = ev["tiempo_s"].to_numpy(float)
                hallados = sum(np.min(np.abs(t - e)) < 0.2 for e in esperados) if len(t) else 0
                print(f"  reporte: {len(t)} eventos; de los {len(esperados)} pulsos positivos, {hallados} en su lugar")
                if hallados != len(esperados):
                    fallos.append(f"pulsos encontrados {hallados} de {len(esperados)}")

        # 3. comandos de la ventana / carpeta
        cmds = interfaz.armar_comandos(str(v), str(out), True, True, False, metodo="textura")
        if "--metodo" not in cmds[0][1] or cmds[0][1][cmds[0][1].index("--metodo") + 1] != "textura":
            fallos.append("armar_comandos no pasa --metodo textura")
        if "--metodo" in interfaz.armar_comandos(str(v), str(out), True, True, False)[0][1]:
            fallos.append("con bordes (default) no tiene que pasar --metodo")
        try:
            interfaz.armar_comandos(str(v), str(out), True, True, True, metodo="textura")
            fallos.append("paso 3 con textura deberia dar error")
        except ValueError:
            pass
        c = interfaz.armar_comando_carpeta(str(tmp), str(out), True, True, False, metodo="textura")
        if c[0][1][-2:] != ["--metodo", "textura"]:
            fallos.append("armar_comando_carpeta no pasa --metodo textura")

    # 4. aviso de respuesta chica (2026-10-19; solo texto, no cambia numeros)
    sys.path.insert(0, str(RAIZ / "scripts"))
    import contraction_report as cr
    casos = [  # (reportable, amp px, ruido px, aviso?)  medidos: 20V_3, 10V_1, 40V_3
        (True, 1.64, 0.059, False), (True, 1.16, 0.058, True), (True, 0.76, 0.081, True),
        (True, 2.0, 0.3, True), (False, 0.5, 0.1, False)]
    for rep, amp, ru, esp in casos:
        av = cr.aviso_textura_chica({"conteo_reportable": rep, "amplitud_px": amp, "ruido_canal_px": ru})
        if bool(av) != esp:
            fallos.append(f"aviso textura chica: {amp} px / ruido {ru} -> {bool(av)} (esperado {esp})")
    print("  aviso de respuesta chica: " + ("OK" if not any("aviso" in f for f in fallos) else "FALLA"))

    if fallos:
        print("FALLA:\n  " + "\n  ".join(fallos))
        sys.exit(1)
    print("OK: textura (corrimiento conocido, main.py, reporte y comandos)")


if __name__ == "__main__":
    main()
