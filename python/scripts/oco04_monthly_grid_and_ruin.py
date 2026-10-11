"""OCO-04: month-by-month grid for the PERFECTED OCO with 1000 and fixed 0.10 lot, plus 'what if I had started
in month X' (every start month 2018-01..2025-10, 12 months each, fresh 1000 account) and the ruin rate.
Ruin = balance below the margin needed for 0.10 lot at 1:100 (trading stops)."""
import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np, pandas as pd
from raptor import pipeline as P
from raptor.straddle import run
from raptor.straddle_setups import setups

ROOT = Path(__file__).resolve().parents[2]
mk = P.market(); SPREAD = np.full(len(mk.o), 0.30)
EX = dict(trail_atr=2.0, tp_r=2.0, max_hold_min=1440)
s, tfm = setups(kind="SQZ", N=24, stop="range", stop_k=1.5, regime="filter")
tr, info = run(mk, s, tf_minutes=tfm, spread=SPREAD, init_bal=1000.0, leverage=100.0, lot_mode=0, fixed_lot=0.10, **EX)
m = tr.groupby(tr.exit_time.dt.to_period("M")).net.sum()
grid = pd.DataFrame({"y": m.index.year, "m": m.index.month, "net": m.values}).pivot(index="y", columns="m", values="net").round(0)
grid["ANNO"] = grid.sum(axis=1)
grid.to_csv(ROOT / "reports" / "oco_fixed010_month_grid.csv")
print(grid.fillna(0).astype(int).to_string())
res = []
for st in pd.period_range("2018-01", "2025-10", freq="M"):
    a, b = st.start_time, (st + 12).start_time
    t2, inf = run(mk, s[(s.bar_time >= a) & (s.bar_time < b)], tf_minutes=tfm, spread=SPREAD, init_bal=1000.0,
                  leverage=100.0, lot_mode=0, fixed_lot=0.10, **EX)
    if len(t2) == 0:
        res.append({"start": str(st), "final": 1000.0, "min_balance": 1000.0}); continue
    res.append({"start": str(st), "final": round(float(t2.balance.iloc[-1]), 0),
                "min_balance": round(float(min(1000.0, t2.equity_low.min(), t2.balance.min())), 0),
                "skipped_margin": inf["skipped_margin"]})
R = pd.DataFrame(res)
R.to_csv(ROOT / "reports" / "oco_fixed010_rolling_12m.csv", index=False)
out = {"starts": int(len(R)), "share_profitable_after_12m": round(float((R.final > 1000).mean() * 100), 1),
       "median_final": float(R.final.median()), "p10_final": float(R.final.quantile(0.1)), "p90_final": float(R.final.quantile(0.9)),
       "share_equity_below_500": round(float((R.min_balance < 500).mean() * 100), 1),
       "share_blocked_by_margin": round(float((R.skipped_margin > 0).mean() * 100), 1),
       "worst_start": R.loc[R.final.idxmin()].to_dict(), "best_start": R.loc[R.final.idxmax()].to_dict()}
(ROOT / "reports" / "oco_fixed010_ruin.json").write_text(json.dumps(out, indent=1, default=str))
print(json.dumps(out, indent=1, default=str))
print(R.groupby(R.start.str[:4]).final.median())
