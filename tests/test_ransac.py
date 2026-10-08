"""
test_ransac.py
--------------
El RANSAC propio (src/robust_fitting.py, 2026-10-08) tiene que dar lo MISMO
que el RANSACRegressor de sklearn que reemplazo: mismas columnas inlier y el
mismo borde ajustado (salvo la cifra 12), sobre bordes sinteticos con ruido,
burbujas (outliers) y columnas sin medida (NaN), en grados 1, 2 y 3.

    python tests/test_ransac.py
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from sklearn.linear_model import RANSACRegressor
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import PolynomialFeatures
from src import robust_fitting as rf


def ransac_sklearn(x, y, degree):
    """El camino viejo, tal cual estaba en robust_fitting.fit_edge_ransac."""
    valid = ~np.isnan(y)
    xv, yv = x[valid].astype(float), y[valid].astype(float)
    x0 = xv.mean(); scale = max((xv.max() - xv.min()) / 2.0, 1.0)
    xn = (xv - x0) / scale
    _, mad = rf._trimmed_polyfit(xn, yv, degree)
    thr = max(3.0 * (mad if np.isfinite(mad) and mad > 0 else 0.0), 0.4)
    m = make_pipeline(PolynomialFeatures(degree=degree),
                      RANSACRegressor(residual_threshold=thr, random_state=0, max_trials=200))
    m.fit(xn.reshape(-1, 1), yv)
    mask = np.zeros(len(x), bool); mask[valid] = m.named_steps["ransacregressor"].inlier_mask_
    return mask, m.predict(((x - x0) / scale).reshape(-1, 1))


def main():
    rng = np.random.default_rng(1)
    fallas = 0
    for degree in (1, 2, 3):
        iguales, dif = 0, 0.0
        for i in range(200):
            x = np.linspace(400, 1500, 60).astype(int)
            y = 300 + 0.00002 * (x - 900) ** 2 + rng.normal(0, 0.8, 60)
            if i % 3 == 0:
                y[rng.choice(60, 6, replace=False)] += rng.uniform(3, 10, 6)   # burbujas
            if i % 5 == 0:
                y[rng.choice(60, 3, replace=False)] = np.nan                    # sin medida
            mask_v, yfit_v = ransac_sklearn(x, y, degree)
            nuevo = rf.fit_edge_ransac(x, y, degree=degree)
            iguales += np.array_equal(mask_v, nuevo.inlier_mask)
            dif = max(dif, float(np.max(np.abs(yfit_v - nuevo.y_fitted))))
        ok = iguales == 200 and dif < 1e-9
        fallas += not ok
        print(f"  {'OK ' if ok else 'MAL'} grado {degree}: mismas columnas en {iguales}/200, "
              f"diferencia maxima del borde {dif:.1e} px")
    print("\nTODO OK" if not fallas else f"\n{fallas} FALLA(S)")
    sys.exit(1 if fallas else 0)


if __name__ == "__main__":
    main()
