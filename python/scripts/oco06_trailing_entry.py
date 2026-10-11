"""OCO-06: trailing OCO entries (orders follow the price). Grid 96 configs at 1% risk (R metrics), nested
walk-forward (yearly, top-3 by in-sample t, n_in >= 100), then the final selection is shown month by month with
1000 / fixed 0.10. Costs C1 + swap."""
import sys, json, itertools
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np, pandas as pd
from raptor import pipeline as P, metrics as M
from raptor.trailing_entry import run, h1_context_on_m1

ROOT = Path(__file__).resolve().parents[2]
mk = P.market(); SP = np.full(len(mk.o), 0.30)
atr, reg = h1_context_on_m1(mk, P.feats("1h", 3))
rows, labs = [], []
for kd, slk, tp, tk, ureg in itertools.product((1.0, 2.0, 3.0, 4.0), (1.0, 1.5, 2.5), (2.0, 100.0), (1.5, 2.5), (True, False)):
    tr = run(mk, SP, atr, reg, k_dist=kd, sl_k=slk, tp_r=tp, trail_k=tk, use_regime=ureg, lot_mode=1, init_bal=10000.0)
    cfg = f"dist={kd},sl={slk},tp={tp},trail={tk},regime={ureg}"
    tr["cfg"] = cfg
    labs.append(tr[["entry_time", "exit_time", "side", "r_mult", "cfg"]])
    rows.append({"cfg": cfg, **M.r_stats(tr.r_mult), "long_R": round(float(tr[tr.side == 1].r_mult.mean()), 3),
                 "short_R": round(float(tr[tr.side == -1].r_mult.mean()), 3)})
G = pd.DataFrame(rows).sort_values("t_stat", ascending=False)
G.to_csv(ROOT / "experiments" / "oco06_trailing_grid.csv", index=False)
pd.set_option("display.width", 220)
print("share>0:", round(float((G.mean_R > 0).mean()), 3), " regime share>0:", round(float((G[G.cfg.str.endswith("True")].mean_R > 0).mean()), 3))
print(G.head(8).to_string(index=False))
L = pd.concat(labs, ignore_index=True)
cv, rv, ev, yv = L.cfg.values, L.r_mult.values, L.exit_time.values, L.entry_time.dt.year.values
masks = {c: cv == c for c in np.unique(cv)}
sel, oos = [], []
for Y in range(2020, 2027):
    ins = ev < np.datetime64(f"{Y}-01-01")
    st = [(rv[m & ins].mean() / (rv[m & ins].std(ddof=1) / np.sqrt((m & ins).sum())), c) for c, m in masks.items()
          if (m & ins).sum() >= 100 and rv[m & ins].mean() > 0]
    st.sort(reverse=True)
    for t, c in st[:3]:
        ro = rv[masks[c] & (yv == Y)]
        sel.append({"year": Y, "cfg": c, "t_in": round(t, 2), "n_oos": len(ro), "meanR_oos": round(float(ro.mean()), 3), "sumR_oos": round(float(ro.sum()), 1)})
        oos.extend(ro.tolist())
S = pd.DataFrame(sel); S.to_csv(ROOT / "experiments" / "oco06_walkforward.csv", index=False)
print(S.to_string(index=False))
print(json.dumps({"WF_OOS": M.r_stats(pd.Series(oos)), "yearly": S.groupby("year").sumR_oos.sum().round(1).to_dict()}, indent=1))
