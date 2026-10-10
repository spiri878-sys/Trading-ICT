"""EXP-09 (dev only, walk-forward inside dev): ML filter x candidate pool x min stop x exit model.
Model trained on 2018-2019, early-stopped on 2020, scored on 2021 with the causal living threshold."""
import sys, json
from dataclasses import replace
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np, pandas as pd
from raptor import pipeline as P, metrics as M, ml
from raptor.costs import C1, with_cost

CELLS = ["PPK", "OTEOF", "PO3", "UNIOF", "LS", "SILVER_BULLET", "WYCKOFF"]
EXITS = {"ladder": dict(tp_r=4.0, p1_r=0.7, p1_frac=0.2, p2_r=2.0, p2_frac=0.2, be_after_p1=True, mgmt_on_close=True, max_hold_min=4320),
         "tp3R_48h": dict(tp_r=3.0, p1_frac=0.0, p2_frac=0.0, be_after_p1=False, max_hold_min=2880),
         "tp2R_24h": dict(tp_r=2.0, p1_frac=0.0, p2_frac=0.0, be_after_p1=False, max_hold_min=1440)}
rows = []
for tf, k in [("5min", 8), ("15min", 3)]:
    for ms in (0.0, 2.0, 3.0):
        for en, ex in EXITS.items():
            strat = {c: {"expiry": 8, "max_r_atr": 30.0, "min_r_atr": 0.3} for c in CELLS}
            with with_cost(C1) as prm:
                lab, X = P.labelled(strat, replace(prm, **ex), tf=tf, swing_k=k, min_stop_m15=ms)
            fr = ml.fit(lab, X, train_end="2021-01-01", inner_valid_start="2020-01-01")
            v = (lab.bar_time >= "2021-01-01") & (lab.bar_time < "2022-01-01") & lab.filled
            sc = fr.model.predict(X[v].values)
            thr = ml.living_threshold(sc, fr.seed_scores)
            lv = lab[v].assign(accept=sc > thr)
            a = M.r_stats(lv[lv.accept].r)
            rows.append({"tf": tf, "k": k, "min_stop": ms, "exit": en, "iters": fr.best_iter,
                         "corr2020": round(fr.inner_valid_corr, 3), "corr2021": round(float(np.corrcoef(sc, lv.r)[0, 1]), 3),
                         "all_2021": M.r_stats(lv.r)["mean_R"], "acc_n": a["n"], "acc_2021": a["mean_R"], "acc_t": a["t_stat"]})
df = pd.DataFrame(rows)
df.to_csv(Path(__file__).resolve().parents[2] / "experiments" / "exp09_ml_grid.csv", index=False)
pd.set_option("display.width", 220)
print(df.to_string())
