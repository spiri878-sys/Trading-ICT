"""OCO-02: straddle with regime filter on which stop order is placed (bull: buy stop only; bear: sell stop only;
mixed: none) vs the original 'both sides' idea, then nested walk-forward selection over ALL OCO configs
(each year: best 3 by in-sample t-stat, n_in >= 100, mean > 0, trades closed before the year). C1 + swap, 1% risk."""
import sys, json, itertools
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np, pandas as pd
from raptor import pipeline as P, metrics as M
from raptor.straddle import run
from raptor.straddle_setups import setups

ROOT = Path(__file__).resolve().parents[2]
mk = P.market(); SPREAD = np.full(len(mk.o), 0.30)
GRID = []
for kind in ("ASIA", "PDHL"):
    for stop, sk in (("range", 1.5), ("atr", 1.0), ("atr", 2.0)):
        GRID.append(dict(kind=kind, stop=stop, stop_k=sk))
for kind, N in itertools.product(("ROLL", "SQZ"), (6, 12, 24)):
    for stop, sk in (("range", 1.5), ("atr", 1.0), ("atr", 2.0)):
        GRID.append(dict(kind=kind, N=N, stop=stop, stop_k=sk))
EXITS = [dict(trail_atr=t, tp_r=tp, max_hold_min=h) for t in (1.0, 2.0, 3.0) for tp in (100.0, 2.0) for h in (1440, 2880)]
labs, rows = [], []
for g in GRID:
    s, tfm = setups(**g, regime="filter")
    for ex in EXITS:
        tr, _ = run(mk, s, tf_minutes=tfm, spread=SPREAD, init_bal=10000.0, lot_mode=1, risk_pct=1.0, **ex)
        cfg = "regime|" + ",".join(f"{k}={v}" for k, v in g.items()) + "|" + ",".join(f"{k}={v}" for k, v in ex.items())
        tr["cfg"] = cfg
        labs.append(tr[["entry_time", "exit_time", "side", "r_mult", "cfg"]])
        rows.append({"cfg": cfg, **M.r_stats(tr.r_mult), "long_R": round(float(tr[tr.side == 1].r_mult.mean()), 3),
                     "short_R": round(float(tr[tr.side == -1].r_mult.mean()), 3) if (tr.side == -1).any() else None})
R = pd.DataFrame(rows)
R.to_csv(ROOT / "experiments" / "oco02_regime_grid.csv", index=False)
base = pd.read_parquet(ROOT / "experiments" / "oco01_trades.parquet")[["entry_time", "exit_time", "side", "r_mult", "cfg"]]
base["cfg"] = "both|" + base.cfg
L = pd.concat([base] + labs, ignore_index=True)
L.to_parquet(ROOT / "experiments" / "oco02_all_trades.parquet")
print("regime-filtered configs:", len(R), "share mean_R>0:", round(float((R.mean_R > 0).mean()), 3), " median:", round(float(R.mean_R.median()), 3))
print(R.sort_values("t_stat", ascending=False).head(8)[["cfg", "n", "mean_R", "pf", "t_stat", "long_R", "short_R"]].to_string())
# nested walk-forward over both + regime configs
cfgs = L.cfg.unique(); cv = L.cfg.values; rv = L.r_mult.values; ex = L.exit_time.values; yr = L.entry_time.dt.year.values
masks = {c: cv == c for c in cfgs}
sel, oos = [], []
for Y in range(2020, 2027):
    ins = ex < np.datetime64(f"{Y}-01-01")
    st = []
    for c in cfgs:
        r = rv[masks[c] & ins]
        if len(r) >= 100 and r.mean() > 0:
            st.append((r.mean() / (r.std(ddof=1) / np.sqrt(len(r))), c))
    st.sort(reverse=True)
    for t, c in st[:3]:
        ro = rv[masks[c] & (yr == Y)]
        sel.append({"year": Y, "cfg": c, "t_in": round(t, 2), "n_oos": len(ro), "meanR_oos": round(float(ro.mean()), 3), "sumR_oos": round(float(ro.sum()), 1)})
        oos.extend(ro.tolist())
sel = pd.DataFrame(sel); sel.to_csv(ROOT / "experiments" / "oco02_walkforward.csv", index=False)
pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 110)
print(sel.to_string())
print(json.dumps({"WF_OOS_2020_2026": M.r_stats(pd.Series(oos)), "yearly": sel.groupby("year").sumR_oos.sum().round(1).to_dict()}, indent=1))
