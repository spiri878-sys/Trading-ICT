"""WF-03: yearly re-trained ML filter (the vendor's claimed method: gradient boosting on all cell signals,
living threshold = q80 of last 1000 scores) in an expanding walk-forward 2020-2026. ICT only.
Pre-registered PRIMARY pool: M5 cells, H1-swing stop, vendor ladder exits (closest to E-25/E-29).
Other pools are reported as sensitivity only. Each year Y: train on signals with exit < Y-1-01 minus the
last year (inner early-stopping year = Y-1), score year Y, causal threshold."""
import sys, json
from dataclasses import replace
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np, pandas as pd
from raptor import pipeline as P, metrics as M, ml
from raptor.costs import C1, with_cost

ROOT = Path(__file__).resolve().parents[2]
CELLS = ["PPK", "MSS", "OTEOF", "PO3", "UNIOF", "LS", "SILVER_BULLET"]
LADDER = dict(tp_r=4.0, p1_r=0.7, p1_frac=0.2, p2_r=2.0, p2_frac=0.2, be_after_p1=True, mgmt_on_close=True, max_hold_min=4320)
TP3 = dict(tp_r=3.0, p1_frac=0.0, p2_frac=0.0, be_after_p1=False, max_hold_min=2880)
POOLS = {"PRIMARY_m5_h1stop_ladder": ("5min", 3, dict(htf_stop="h1"), LADDER),
         "m5_h4stop_ladder": ("5min", 3, dict(htf_stop="h4"), LADDER),
         "m5_struct_ladder": ("5min", 3, dict(), LADDER),
         "m15_h4stop_tp3": ("15min", 3, dict(htf_stop="h4"), TP3)}
out = {}
for name, (tf, k, skw, ex) in POOLS.items():
    tfm = int(pd.Timedelta(tf).total_seconds() // 60)
    strat = {c: {"expiry": max(3, 60 // tfm), "max_r_atr": 40.0} for c in CELLS}
    with with_cost(C1, replace(P.Params(), **ex)) as prm:
        lab, X = P.labelled(strat, prm, tf=tf, swing_k=k, **skw)
    accepted, allr, per_year = [], [], {}
    for Y in range(2020, 2027):
        fr = ml.fit(lab, X, train_end=f"{Y}-01-01", inner_valid_start=f"{Y-1}-01-01")
        m = (lab.bar_time.dt.year == Y).values
        sc = fr.model.predict(X[m].values)
        thr = ml.living_threshold(sc, fr.seed_scores)
        d = lab[m].assign(accept=sc > thr)
        d = d[d.filled]
        per_year[Y] = {"all": M.r_stats(d.r)["mean_R"], "accepted": M.r_stats(d[d.accept].r), "iters": fr.best_iter}
        accepted.append(d[d.accept].r); allr.append(d.r)
    a = pd.concat(accepted); b = pd.concat(allr)
    out[name] = {"OOS_accepted": M.r_stats(a), "OOS_all": M.r_stats(b), "per_year": per_year}
    print(name, json.dumps(out[name]["OOS_accepted"]), "all:", out[name]["OOS_all"]["mean_R"], flush=True)
(ROOT / "experiments" / "wf03_ml_walkforward.json").write_text(json.dumps(out, indent=1, default=str))
for n, v in out.items():
    print(n, {y: (v["per_year"][y]["accepted"]["mean_R"], v["per_year"][y]["accepted"]["n"]) for y in v["per_year"]})
