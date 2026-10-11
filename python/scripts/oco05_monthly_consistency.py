"""OCO-05: can monthly rules make months more consistently positive WITHOUT over-fitting?
Variants: monthly loss cap {0,5,10,15}% x monthly profit lock {0,10,20,30}% x session hours {all, 09-19, 14-19 server}
x volatility filter {none, H1 ATR <= 1.5x mean}. Account 1000, fixed 0.10 (user setting), costs C1 + swap.
Selection ONLY on 2018-2022 (fresh 1000 account), score = share of positive months, tie-break total return;
then the chosen variant and the baseline are run ONCE on 2023-2026 (fresh 1000 account)."""
import sys, json, itertools
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np, pandas as pd
from raptor import pipeline as P
from raptor.straddle import run
from raptor.straddle_setups import setups

ROOT = Path(__file__).resolve().parents[2]
mk = P.market(); SP = np.full(len(mk.o), 0.30)
EX = dict(trail_atr=2.0, tp_r=2.0, max_hold_min=1440)
HOURS = {"all": None, "london_ny": list(range(9, 19)), "ny": list(range(14, 19))}


def evaluate(var, a, b):
    s, tfm = setups(kind="SQZ", N=24, stop="range", stop_k=1.5, regime="filter", hours=HOURS[var["hours"]], vol_max=var["vol"])
    s = s[(s.bar_time >= a) & (s.bar_time < b)]
    tr, info = run(mk, s, tf_minutes=tfm, spread=SP, init_bal=1000.0, leverage=100.0, lot_mode=0, fixed_lot=0.10,
                   month_loss_pct=var["mloss"], month_profit_pct=var["mprof"], **EX)
    months = pd.period_range(pd.Timestamp(a), pd.Timestamp(b) - pd.Timedelta(days=1), freq="M")
    mon = tr.groupby(tr.exit_time.dt.to_period("M")).net.sum().reindex(months, fill_value=0.0)
    peak = np.maximum.accumulate(np.r_[1000.0, tr.balance.values])[:-1] if len(tr) else np.array([1000.0])
    dd = float((np.maximum(peak - tr.equity_low.values, peak - tr.balance.values) / peak).max() * 100) if len(tr) else 0.0
    return {"trades": int(len(tr)), "final": round(float(tr.balance.iloc[-1]) if len(tr) else 1000.0, 0),
            "pos_months_pct": round(float((mon > 0).mean() * 100), 1), "neg_months": int((mon < 0).sum()),
            "flat_months": int((mon == 0).sum()), "worst_month": round(float(mon.min()), 0), "max_dd_pct": round(dd, 1)}, mon


rows = []
for mloss, mprof, hrs, vol in itertools.product((0, 5, 10, 15), (0, 10, 20, 30), HOURS, (None, 1.5)):
    var = dict(mloss=mloss, mprof=mprof, hours=hrs, vol=vol)
    r, _ = evaluate(var, "2018-01-01", "2023-01-01")
    rows.append({**var, **r})
D = pd.DataFrame(rows).sort_values(["pos_months_pct", "final"], ascending=False)
D.to_csv(ROOT / "experiments" / "oco05_dev_2018_2022.csv", index=False)
pd.set_option("display.width", 220)
base = D[(D.mloss == 0) & (D.mprof == 0) & (D.hours == "all") & (D.vol.isna())]
print("BASELINE dev:\n", base.to_string(index=False))
print("TOP 10 dev:\n", D.head(10).to_string(index=False))
best = D.iloc[0].to_dict()
chosen = dict(mloss=int(best["mloss"]), mprof=int(best["mprof"]), hours=best["hours"], vol=None if pd.isna(best["vol"]) else best["vol"])
out = {"chosen_on_2018_2022": chosen}
for name, var in (("baseline", dict(mloss=0, mprof=0, hours="all", vol=None)), ("chosen", chosen)):
    for per, (a, b) in {"dev_2018_2022": ("2018-01-01", "2023-01-01"), "TEST_2023_2026": ("2023-01-01", "2026-10-10")}.items():
        r, mon = evaluate(var, a, b)
        out[f"{name}|{per}"] = r
        mon.round(0).to_csv(ROOT / "reports" / f"oco05_monthly_{name}_{per}.csv")
(ROOT / "reports" / "oco05_monthly_consistency.json").write_text(json.dumps(out, indent=1, default=str))
print(json.dumps(out, indent=1, default=str))
