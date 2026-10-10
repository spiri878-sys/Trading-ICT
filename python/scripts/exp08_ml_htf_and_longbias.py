"""EXP-08 (dev only): H10 ML filter on 15m candidate pool with continuation exits; H9 long-only in D1 uptrend."""
import sys, json
from dataclasses import replace
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np, pandas as pd
from raptor import pipeline as P, metrics as M, ml
from raptor.costs import C1, with_cost

CELLS = ["PPK", "OTEOF", "PO3", "UNIOF", "LS", "SILVER_BULLET", "WYCKOFF"]
ex = dict(tp_r=3.0, p1_frac=0.0, p2_frac=0.0, be_after_p1=False, max_hold_min=2880)
out = {}
for tf, k in [("15min", 3), ("5min", 8)]:
    strat = {c: {"expiry": 8, "max_r_atr": 30.0, "min_r_atr": 0.3} for c in CELLS}
    with with_cost(C1) as prm:
        lab, X = P.labelled(strat, replace(prm, **ex), tf=tf, swing_k=k)
    # ML: train 2018-2020, early-stop/inner-validate on 2021 (still inside dev)
    fr = ml.fit(lab, X, train_end="2022-01-01", inner_valid_start="2021-01-01")
    # honest inner check: model trained only on 2018-2019, scored on 2021 (embargo 2020)
    fr2 = ml.fit(lab, X, train_end="2021-01-01", inner_valid_start="2020-01-01")
    v = (lab.bar_time >= "2021-01-01") & (lab.bar_time < "2022-01-01") & lab.filled
    sc = fr2.model.predict(X[v].values)
    thr = ml.living_threshold(sc, fr2.seed_scores)
    lv = lab[v].assign(score=sc, accept=sc > thr)
    out[f"{tf}_k{k}"] = {"best_iter_2021es": fr.best_iter, "corr_2021_es": round(fr.inner_valid_corr, 4),
                         "best_iter_2020es": fr2.best_iter, "corr_2020_es": round(fr2.inner_valid_corr, 4),
                         "2021_all": M.r_stats(lv.r), "2021_accepted": M.r_stats(lv[lv.accept].r),
                         "2021_corr": round(float(np.corrcoef(sc, lv.r.values)[0, 1]), 4)}
    # H9 long only, D1 uptrend (close above D1 EMA50), dev
    d = P.in_period(lab.join(X.drop(columns="side")), "dev"); d = d[d.filled]
    lo = d[(d.side == 1) & (d.dist_ema_d1 > 0)]
    out[f"{tf}_k{k}"]["H9_long_d1up_dev"] = M.r_stats(lo.r)
    out[f"{tf}_k{k}"]["H9_by_year"] = {int(y): M.r_stats(g.r)["mean_R"] for y, g in lo.groupby(lo.bar_time.dt.year)}
print(json.dumps(out, indent=1))
