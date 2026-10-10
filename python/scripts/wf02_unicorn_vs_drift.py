"""WF-02: is the walk-forward survivor (UNIOF, M15, H4-swing stop, TP 3R / 48h, long only) better than
random LONG entries with the same stop-size distribution and the same exits (gold drift baseline)?"""
import sys, json
from dataclasses import replace
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np, pandas as pd
from raptor import pipeline as P, metrics as M
from raptor.engine import label
from raptor.costs import C1, with_cost

ROOT = Path(__file__).resolve().parents[2]
EX = dict(tp_r=3.0, p1_frac=0.0, p2_frac=0.0, be_after_p1=False, max_hold_min=2880)
f = P.feats("15min", 3)
with with_cost(C1, replace(P.Params(), **EX)) as prm:
    lab, _ = P.labelled({"UNIOF": {"expiry": 4, "max_r_atr": 40.0}}, prm, tf="15min", swing_k=3, htf_stop="h4")
    lab = lab[lab.filled & (lab.side == 1)].copy()
    risk_h4 = ((lab.price - lab.sl_struct) / f.h4_atr.values[lab.bar_i.values]).values
    rng = np.random.default_rng(0)
    res = {"strategy_by_year": {int(y): M.r_stats(g.r) for y, g in lab.groupby(lab.bar_time.dt.year)}}
    base = {}
    for rep in range(30):
        idx = []
        for y, g in lab.groupby(lab.bar_time.dt.year):
            pool = np.flatnonzero((f.index.year == y) & np.isfinite(f.h4_atr.values) & (f.ny_min.values % 60 == 0) | False)
            pool = np.flatnonzero((f.index.year == y) & np.isfinite(f.h4_atr.values))
            idx.extend(rng.choice(pool, len(g), replace=False))
        idx = np.sort(np.array(idx))
        d = rng.choice(risk_h4, len(idx)) * f.h4_atr.values[idx]
        s = pd.DataFrame({"bar_i": idx, "bar_time": f.index[idx], "side": 1, "otype": "market",
                          "price": f.close.values[idx], "sl_struct": f.close.values[idx] - d, "atr": f.atr.values[idx],
                          "expiry_bars": 2, "strategy": "RANDOM_LONG"})
        rl = label(P.market(), s, prm, 15)
        rl = rl[rl.filled]
        for y, g in rl.groupby(rl.bar_time.dt.year):
            base.setdefault(int(y), []).append(g.r.mean())
res["random_long_by_year_mean_and_p05_p95"] = {y: [round(float(np.mean(v)), 3), round(float(np.quantile(v, .05)), 3),
                                                   round(float(np.quantile(v, .95)), 3)] for y, v in sorted(base.items())}
res["strategy_all"] = M.r_stats(lab.r)
print(json.dumps(res, indent=1))
(ROOT / "experiments" / "wf02_unicorn_vs_drift.json").write_text(json.dumps(res, indent=1))
