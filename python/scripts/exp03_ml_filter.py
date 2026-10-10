"""EXP-03: ML filter. Train on dev (2018-2021; early stop on 2021), evaluate ONCE on val (2022-2023).
Candidates: all cells, M5 swing_k=8, minimum stop 3 x ATR(M15), cost model C1. Living threshold q80/1000."""
import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np, pandas as pd
from raptor import pipeline as P, metrics as M, ml
from raptor.costs import C1, with_cost

CFG = dict(tf="5min", swing_k=int(sys.argv[1]) if len(sys.argv) > 1 else 8,
           min_stop=float(sys.argv[2]) if len(sys.argv) > 2 else 3.0)
CELLS = ["PPK", "OTEOF", "PO3", "UNIOF", "LS", "SILVER_BULLET", "WYCKOFF"]
strat = {c: {"expiry": 12} for c in CELLS}
with with_cost(C1) as prm:
    lab, X = P.labelled(strat, prm, tf=CFG["tf"], swing_k=CFG["swing_k"], min_stop_m15=CFG["min_stop"])
fr = ml.fit(lab, X, train_end="2022-01-01", inner_valid_start="2021-01-01")
val = (lab.bar_time >= "2022-01-01") & (lab.bar_time < "2024-01-01")
sc = fr.model.predict(X[val].values)
thr = ml.living_threshold(sc, fr.seed_scores)
lv = lab[val].assign(score=sc, thr=thr, accept=sc > thr)
res = {"cfg": CFG, "best_iter": fr.best_iter, "inner_valid_corr": round(fr.inner_valid_corr, 4),
       "val_all": M.r_stats(lv.r), "val_taken": M.r_stats(lv[lv.accept].r), "val_rejected": M.r_stats(lv[~lv.accept].r),
       "val_corr": round(float(pd.Series(sc[lv.filled.values]).corr(pd.Series(lv.r.values[lv.filled.values]))), 4)}
lv["dec"] = pd.qcut(lv.score, 10, labels=False)
res["val_by_score_decile_meanR"] = lv.groupby("dec").r.mean().round(3).to_dict()
res["val_taken_by_cell"] = {k: M.r_stats(v.r) for k, v in lv[lv.accept].groupby("strategy")}
print(json.dumps(res, indent=1, default=str))
imp = pd.Series(fr.model.feature_importance("gain"), index=fr.features).sort_values(ascending=False)
print(imp.head(15).round(0).to_string())
