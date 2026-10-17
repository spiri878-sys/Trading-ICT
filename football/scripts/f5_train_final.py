"""F5 — addestra i modelli finali su TUTTA la storia (per la scheda partita) e salva in football/models/.

usage: python football/scripts/f5_train_final.py
"""
import json
import sys
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fb.card import MODELS  # noqa: E402
from fb.data import CACHE, ROOT, matches  # noqa: E402

P = dict(learning_rate=0.03, num_leaves=31, min_data_in_leaf=400, feature_fraction=0.7, bagging_fraction=0.8,
         bagging_freq=1, lambda_l2=10.0, verbose=-1, num_threads=4, seed=7)
MARKET = ["mk_1", "mk_X", "mk_2", "mk_margin", "mk_over25", "ah_line"]


def main():
    MODELS.mkdir(exist_ok=True)
    m = matches()
    X = pd.read_parquet(CACHE / "f2_features.parquet")
    cats = list(m.Division.astype("category").cat.categories)
    X["div_code"] = pd.Categorical(m.Division, categories=cats).codes
    feats = {"calcio_mercato": list(X.columns), "calcio": [c for c in X.columns if c not in MARKET]}
    y1 = m.FTResult.map({"H": 0, "D": 1, "A": 2}).values
    yo = ((m.hg + m.ag) > 2.5).astype(int).values
    yg = ((m.hg > 0) & (m.ag > 0)).astype(int).values
    for v, fs in feats.items():
        lgb.train({**P, "objective": "multiclass", "num_class": 3}, lgb.Dataset(X[fs], y1), 400).save_model(str(MODELS / f"{v}_1x2.txt"))
        lgb.train({**P, "objective": "binary"}, lgb.Dataset(X[fs], yo), 400).save_model(str(MODELS / f"{v}_over.txt"))
        lgb.train({**P, "objective": "binary"}, lgb.Dataset(X[fs], yg), 400).save_model(str(MODELS / f"{v}_gg.txt"))
        lgb.train({**P, "objective": "poisson"}, lgb.Dataset(X[fs], m.hg.values), 400).save_model(str(MODELS / f"{v}_mu_h.txt"))
        lgb.train({**P, "objective": "poisson"}, lgb.Dataset(X[fs], m.ag.values), 400).save_model(str(MODELS / f"{v}_mu_a.txt"))
        print(v, "fatto", flush=True)
    disp = {}
    for fam, (hc, ac) in {"cor": ("HomeCorners", "AwayCorners"), "yel": ("HomeYellow", "AwayYellow")}.items():
        for side, col in (("h", hc), ("a", ac)):
            ok = m[col].notna().values
            lgb.train({**P, "objective": "poisson", "min_data_in_leaf": 300}, lgb.Dataset(X.loc[ok, feats["calcio"]], m.loc[ok, col].values),
                      300).save_model(str(MODELS / f"{fam}_{side}.txt"))
        ev = json.loads((ROOT / "output" / "f3_corners_cards_eval.json").read_text())
        disp[fam] = ev[{"cor": "angoli_totali", "yel": "gialli_totali"}[fam]]["dispersione_k"]
    f1p = json.loads((ROOT / "output" / "f1_goals_eval.json").read_text())["parametri_scelti_2000_2012"]
    (MODELS / "meta.json").write_text(json.dumps({"features": feats, "div_categories": cats, "dispersion": disp,
                                                  "f1_params": f1p}, indent=1))
    # calibrazione isotonica delle probabilità 1X2 / Over / Gol sulle previsioni FUORI CAMPIONE 2010-2026
    import pickle
    from sklearn.isotonic import IsotonicRegression
    pr = pd.read_parquet(CACHE / "f2_preds.parquet")
    ok = (m.season >= 2010).values
    cal = {}
    for v in feats:
        for col, y in (("p1", y1 == 0), ("pX", y1 == 1), ("p2", y1 == 2), ("pover", yo == 1), ("pgg", yg == 1)):
            x = pr[f"{v}_{col}"].values
            sel = ok & np.isfinite(x)
            cal[f"{v}_{col}"] = IsotonicRegression(out_of_bounds="clip", y_min=0.01, y_max=0.99).fit(x[sel], y[sel])
    (MODELS / "calibratori.pkl").write_bytes(pickle.dumps(cal))
    print("modelli salvati in", MODELS)


if __name__ == "__main__":
    main()
