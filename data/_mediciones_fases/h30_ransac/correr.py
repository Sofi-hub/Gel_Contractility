import sys
sys.path.insert(0, '/home/claude/w/repo')
var, video, out = sys.argv[1], sys.argv[2], sys.argv[3]
extra = []
if var == "k2": extra = ["--ransac-residual-k", "2.0"]
if var == "k4": extra = ["--ransac-residual-k", "4.0"]
if var == "trials1000":
    from src import robust_fitting as rf, pipeline as pl
    o = rf.fit_edge_ransac
    def f(*a, **k): k["max_trials"] = 1000; return o(*a, **k)
    rf.fit_edge_ransac = f
sys.argv = ["main.py", "--video", video, "--output-dir", out, "--base-tiempo", "pts", "--procesos", "1"] + extra
import main; main.main()
