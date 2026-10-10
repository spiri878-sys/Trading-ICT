"""WY-01: Wyckoff MTF - full grid labelled, then the SAME nested walk-forward selector as WF-01
(top-5 by in-sample t-stat, n_in >= 60, mean > 0; evaluated in the following year). Cost model C1.
Also reports, for transparency, every config's full-period stats (in-sample by construction)."""
import sys, json, itertools
from dataclasses import replace
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np, pandas as pd
from raptor import pipeline as P, metrics as M
from raptor.engine import label
from raptor.strategies import REGISTRY
from raptor.costs import C1, with_cost

ROOT = Path(__file__).resolve().parents[2]
EXITS = {
    "range_tp":   (dict(p1_frac=0.0, p2_frac=0.0, be_after_p1=False, max_hold_min=5 * 1440), True),
    "range_be1R": (dict(p1_r=1.0, p1_frac=0.5, p2_frac=0.0, be_after_p1=True, mgmt_on_close=True, max_hold_min=5 * 1440), True),
    "ladder":     (dict(tp_r=4.0, p1_r=0.7, p1_frac=0.2, p2_r=2.0, p2_frac=0.2, be_after_p1=True, mgmt_on_close=True, max_hold_min=4320), False),
    "tp2R":       (dict(tp_r=2.0, p1_frac=0.0, p2_frac=0.0, be_after_p1=False, max_hold_min=2880), False),
    "trail":      (dict(tp_r=6.0, p1_r=1.0, p1_frac=0.5, p2_frac=0.0, be_after_p1=True, mgmt_on_close=True, trail_atr=2.0, max_hold_min=5 * 1440), False),
}
GRID = dict(range_h=[48, 72, 120], event_h=[4, 8], min_tv=[0.0, 1.5], max_pos=[0.35, 0.5], entry=["sos", "lps"])
f = P.feats("15min", 3)
frames = []
for vals in itertools.product(*GRID.values()):
    prm_s = dict(zip(GRID.keys(), vals))
    sig = REGISTRY["WYCKOFF_MTF"](f, prm_s)
    if len(sig) < 30:
        continue
    for en, (ex, use_range_tp) in EXITS.items():
        s = sig if use_range_tp else sig.drop(columns="tp_r")
        with with_cost(C1, replace(P.Params(), **ex)) as prm:
            lab = label(P.market(), s.sort_values("bar_time").reset_index(drop=True), prm, 15)
        lab = lab[lab.filled]
        lab["cfg"] = "|".join(f"{k}={v}" for k, v in prm_s.items()) + "|" + en
        frames.append(lab[["bar_time", "exit_time", "side", "r", "cfg"]])
L = pd.concat(frames, ignore_index=True)
L.to_parquet(ROOT / "data" / "processed" / "wy01_labels.parquet")
cfgs = []
for cfg in L.cfg.unique():
    for side in ["both", "long", "short"]:
        cfgs.append((cfg, side))
masks = {}
for cfg, side in cfgs:
    m = (L.cfg == cfg).values.copy()
    if side == "long": m &= L.side.values == 1
    if side == "short": m &= L.side.values == -1
    masks[(cfg, side)] = m
full = []
for c, m in masks.items():
    r = L.r.values[m]
    if len(r) >= 30:
        full.append({"cfg": c[0], "side": c[1], **M.r_stats(pd.Series(r))})
full = pd.DataFrame(full).sort_values("t_stat", ascending=False)
full.to_csv(ROOT / "experiments" / "wy01_full_period_configs.csv", index=False)
yb = L.bar_time.dt.year.values
rows, oos = [], []
for Y in range(2020, 2027):
    ins = L.exit_time.values < np.datetime64(f"{Y}-01-01")
    st = []
    for c, m in masks.items():
        r = L.r.values[m & ins]
        if len(r) >= 60 and r.mean() > 0:
            st.append((r.mean() / (r.std(ddof=1) / np.sqrt(len(r))), c, r.mean(), len(r)))
    st.sort(reverse=True, key=lambda x: x[0])
    for t, c, mu, n in st[:5]:
        ro = L.r.values[masks[c] & (yb == Y)]
        rows.append({"year": Y, "cfg": c[0] + "|" + c[1], "t_in": round(t, 2), "meanR_in": round(mu, 3), "n_in": n,
                     "n_oos": len(ro), "meanR_oos": round(float(ro.mean()), 3) if len(ro) else None, "sumR_oos": round(float(ro.sum()), 2)})
        oos.extend(ro.tolist())
sel = pd.DataFrame(rows)
sel.to_csv(ROOT / "experiments" / "wy01_selector.csv", index=False)
pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 90)
print(sel.to_string())
print(json.dumps({"configs": len(cfgs), "OOS_2020_2026": M.r_stats(pd.Series(oos)),
                  "yearly_sumR": sel.groupby("year").sumR_oos.sum().round(1).to_dict(),
                  "share_full_period_configs_positive": round(float((full.mean_R > 0).mean()), 3),
                  "full_period_top5": full.head(5)[["cfg", "side", "n", "mean_R", "t_stat"]].to_dict("records")}, indent=1, default=str))
