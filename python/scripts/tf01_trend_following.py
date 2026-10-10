"""TF-01: classic trend following on XAUUSD (time-series momentum literature), long AND short.
Donchian breakout (close beyond the N-bar high/low) on H4 and D1, stop = k x ATR, exits: trailing k x ATR
(no TP) or TP at m R; one position at a time. Nested walk-forward selection as in WF-01 (top-3 by in-sample
t-stat, n_in >= 30). Cost C1. Signals at bar close, market entry at next M1 open."""
import sys, json, itertools
from dataclasses import replace
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np, pandas as pd
from raptor import pipeline as P, metrics as M, data as D
from raptor.engine import label
from raptor.indicators import atr
from raptor.costs import C1, with_cost

ROOT = Path(__file__).resolve().parents[2]
m1 = P.m1()
rows_lab = []
for tf, tfm in [("4h", 240), ("1D", 1440)]:
    b = D.resample(m1, tf)
    h, l, c = b.high.values, b.low.values, b.close.values
    a = atr(h, l, c, 20)
    for N in (20, 55, 100):
        hi = pd.Series(h).rolling(N).max().shift(1).values
        lo = pd.Series(l).rolling(N).min().shift(1).values
        up = (c > hi) & (pd.Series(c).shift(1).values <= hi)
        dn = (c < lo) & (pd.Series(c).shift(1).values >= lo)
        for kstop in (2.0, 3.0):
            for side_mask, side in ((up, 1), (dn, -1)):
                idx = np.flatnonzero(side_mask & np.isfinite(a))
                s = pd.DataFrame({"bar_i": idx, "bar_time": b.index[idx], "side": side, "otype": "market",
                                  "price": c[idx], "sl_struct": c[idx] - side * kstop * a[idx], "atr": a[idx],
                                  "expiry_bars": 1, "strategy": "DONCHIAN"})
                for en, ex in {"trail": dict(tp_r=50.0, p1_r=0.0001, p1_frac=0.0, p2_frac=0.0, be_after_p1=False,
                                             trail_atr=kstop, max_hold_min=60 * 1440, friday_close_min=24 * 60),
                               "tp3R": dict(tp_r=3.0, p1_frac=0.0, p2_frac=0.0, be_after_p1=False, max_hold_min=30 * 1440,
                                            friday_close_min=24 * 60)}.items():
                    with with_cost(C1, replace(P.Params(), **ex)) as prm:
                        lab = label(P.market(), s, prm, tfm)
                    lab = lab[lab.filled]
                    lab["cfg"] = f"{tf}|N={N}|stop={kstop}ATR|{en}|{'long' if side == 1 else 'short'}"
                    rows_lab.append(lab[["bar_time", "exit_time", "side", "r", "cfg"]])
L = pd.concat(rows_lab, ignore_index=True)
full = L.groupby("cfg").r.apply(lambda r: pd.Series(M.r_stats(r))).unstack()
full.to_csv(ROOT / "experiments" / "tf01_full_period.csv")
yb = L.bar_time.dt.year.values
sel, oos = [], []
cfgs = L.cfg.unique()
for Y in range(2020, 2027):
    ins = L.exit_time.values < np.datetime64(f"{Y}-01-01")
    st = []
    for cfg in cfgs:
        r = L.r.values[(L.cfg.values == cfg) & ins]
        if len(r) >= 30 and r.mean() > 0:
            st.append((r.mean() / (r.std(ddof=1) / np.sqrt(len(r))), cfg))
    st.sort(reverse=True)
    for t, cfg in st[:3]:
        ro = L.r.values[(L.cfg.values == cfg) & (yb == Y)]
        sel.append({"year": Y, "cfg": cfg, "t_in": round(t, 2), "n_oos": len(ro), "sumR_oos": round(float(ro.sum()), 2)})
        oos.extend(ro.tolist())
sel = pd.DataFrame(sel)
sel.to_csv(ROOT / "experiments" / "tf01_selector.csv", index=False)
pd.set_option("display.width", 200)
print(full.sort_values("t_stat", ascending=False).head(12).to_string())
print("long share>0:", round(float((full[full.index.str.endswith("long")].mean_R > 0).mean()), 2),
      "short share>0:", round(float((full[full.index.str.endswith("short")].mean_R > 0).mean()), 2))
print(sel.to_string())
print(json.dumps({"OOS_2020_2026": M.r_stats(pd.Series(oos)), "yearly_sumR": sel.groupby("year").sumR_oos.sum().round(1).to_dict()}, indent=1))
