"""VAL-01: single pre-registered evaluation of candidate A on the validation period (2022-2023).
Candidate A was fixed from EXP-06/07 on dev only. The full grid is re-run on val ONLY to measure
out-of-sample robustness of the neighbourhood; it is not used to pick parameters."""
import sys, json
from dataclasses import replace
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pandas as pd
from raptor import pipeline as P, metrics as M
from raptor.costs import C0, C1, C2, with_cost

def run(k, disp, tp, hold, cm, period):
    strat = {c: {"expiry": 4, "max_r_atr": 30.0, "min_r_atr": 0.3, "market_entry": True, "min_disp": disp} for c in ["PPK", "UNIOF"]}
    ex = dict(tp_r=tp, p1_frac=0.0, p2_frac=0.0, be_after_p1=False, max_hold_min=hold * 60)
    with with_cost(cm) as prm:
        lab, X = P.labelled(strat, replace(prm, **ex), tf="1h", swing_k=k)
    d = P.in_period(lab, period); d = d[d.filled].drop_duplicates(["bar_time", "side"])
    return d

A = dict(k=3, disp=1.2, tp=3.0, hold=48)
out = {"candidate_A": A}
for cname, cm in [("C1", C1), ("C2", C2), ("C0_recorded", C0)]:
    for per in ["dev", "val"]:
        d = run(**A, cm=cm, period=per)
        out[f"{per}_{cname}"] = M.r_stats(d.r)
        out[f"{per}_{cname}_by_year"] = {int(y): M.r_stats(g.r) for y, g in d.groupby(d.bar_time.dt.year)}
grid = []
for k in (2, 3, 4):
    for disp in (0.8, 1.2, 1.6):
        for tp in (2.0, 3.0, 4.0):
            for hold in (24, 48, 96):
                grid.append({"k": k, "disp": disp, "tp": tp, "hold": hold, **M.r_stats(run(k, disp, tp, hold, C1, "val").r)})
g = pd.DataFrame(grid)
out["val_grid_share_positive_C1"] = round(float((g.mean_R > 0).mean()), 3)
out["val_grid_median_meanR_C1"] = round(float(g.mean_R.median()), 4)
g.to_csv(Path(__file__).resolve().parents[2] / "experiments" / "val01_grid.csv", index=False)
print(json.dumps(out, indent=1))
