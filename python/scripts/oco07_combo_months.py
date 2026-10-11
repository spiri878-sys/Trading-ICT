"""OCO-07: monthly consistency of OCO-SQZ-REGIME alone, TREND-REGIME alone and the two combined (each sleeve at
1% risk, monthly sums in R, cost C1 + swap). Shows share of positive months, worst month, correlation."""
import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np, pandas as pd
from raptor import pipeline as P
from raptor.straddle import run
from raptor.straddle_setups import setups

ROOT = Path(__file__).resolve().parents[2]
mk = P.market(); SP = np.full(len(mk.o), 0.30)
s, tfm = setups(kind="SQZ", N=24, stop="range", stop_k=1.5, regime="filter")
oco, _ = run(mk, s, tf_minutes=tfm, spread=SP, init_bal=1e6, lot_mode=1, risk_pct=1.0, trail_atr=2.0, tp_r=2.0, max_hold_min=1440)
trend = pd.read_csv(ROOT / "reports" / "trades_TREND_REGIME_long_only.csv", parse_dates=["entry_time", "exit_time"])
months = pd.period_range("2018-01", "2026-09", freq="M")
mo = oco.groupby(oco.exit_time.dt.to_period("M")).r_mult.sum().reindex(months, fill_value=0)
mt = trend.groupby(trend.exit_time.dt.to_period("M")).r_mult.sum().reindex(months, fill_value=0)
out = {}
for name, ser in (("OCO_SQZ_REGIME", mo), ("TREND_REGIME_H4", mt), ("COMBINED_50_50", 0.5 * mo + 0.5 * mt), ("COMBINED_1pct_each", mo + mt)):
    out[name] = {"pos_months_pct": round(float((ser > 0).mean() * 100), 1), "neg_months": int((ser < 0).sum()),
                 "zero_months": int((ser == 0).sum()), "worst_month_R": round(float(ser.min()), 2),
                 "mean_month_R": round(float(ser.mean()), 3), "pos_quarters_pct": round(float((ser.groupby(ser.index.asfreq("Q")).sum() > 0).mean() * 100), 1),
                 "pos_years": int((ser.groupby(ser.index.year).sum() > 0).sum())}
out["monthly_corr"] = round(float(np.corrcoef(mo, mt)[0, 1]), 3)
(ROOT / "reports" / "oco07_combo_months.json").write_text(json.dumps(out, indent=1))
print(json.dumps(out, indent=1))
