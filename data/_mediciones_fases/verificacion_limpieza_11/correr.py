"""Reprocesa un video con el codigo actual, contando cuantas veces actua min_gradient."""
import sys, json, time
sys.path.insert(0, '/home/claude/w/repo')
import numpy as np
from src import edge_detection as ed
orig = ed.subpixel_edge_parabolic
C = {"llamadas": 0, "rechazo_min_gradient": 0, "picos": []}
def envuelta(profile, s, e, polarity=1, min_gradient=5.0):
    C["llamadas"] += 1
    w = profile[s:e]
    if w.size >= 3:
        g = np.gradient(w) * polarity; i = int(np.argmax(g))
        if 0 < i < len(g) - 1:
            if g[i] < min_gradient: C["rechazo_min_gradient"] += 1
            if C["llamadas"] % 50 == 0: C["picos"].append(float(g[i]))
    return orig(profile, s, e, polarity=polarity, min_gradient=min_gradient)
ed.subpixel_edge_parabolic = envuelta
video, out, info = sys.argv[1], sys.argv[2], sys.argv[3]
sys.argv = ["main.py", "--video", video, "--output-dir", out, "--base-tiempo", "pts", "--procesos", "1"]
import main
t = time.time(); main.main()
p = np.array(C["picos"])
json.dump({"llamadas": C["llamadas"], "rechazo_min_gradient": C["rechazo_min_gradient"],
           "pico_p01": float(np.percentile(p, 1)), "pico_min_muestra": float(p.min()),
           "segundos": round(time.time() - t)}, open(info, "w"))
