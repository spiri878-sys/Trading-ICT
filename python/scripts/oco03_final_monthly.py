"""OCO-03: final OCO configuration month by month. Capital 1000 (account currency treated as USD; 1000 EUR is
~1150-1170 USD), leverage 1:100, costs C1 + swap. Sizing: fixed 0.10 lot (user request) vs 1% / 2% risk.
Variants: PERFECTED (regime-filtered, walk-forward survivor) and ORIGINAL (both stops always, best 'both' config).
Periods: 2018-2026 and 2021-2026 (years in which the walk-forward selected this configuration out of sample)."""
import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np, pandas as pd
from raptor import pipeline as P, metrics as M
from raptor.straddle import run
from raptor.straddle_setups import setups

ROOT = Path(__file__).resolve().parents[2]
mk = P.market(); SPREAD = np.full(len(mk.o), 0.30)
EX = dict(trail_atr=2.0, tp_r=2.0, max_hold_min=1440)
VARIANTS = {"PERFECTED_regime": dict(kind="SQZ", N=24, stop="range", stop_k=1.5, regime="filter"),
            "ORIGINAL_both_sides": dict(kind="SQZ", N=24, stop="range", stop_k=1.5, regime="both")}
SIZING = {"fixed_0.10": dict(lot_mode=0, fixed_lot=0.10), "risk_1pct": dict(lot_mode=1, risk_pct=1.0),
          "risk_2pct": dict(lot_mode=1, risk_pct=2.0)}
out, monthly_tables = {}, {}
for vn, vg in VARIANTS.items():
    s, tfm = setups(**vg)
    for start in ("2018-01-01", "2021-01-01"):
        ss = s[s.bar_time >= start]
        for zn, z in SIZING.items():
            tr, info = run(mk, ss, tf_minutes=tfm, spread=SPREAD, init_bal=1000.0, leverage=100.0, **EX, **z)
            key = f"{vn}|{zn}|from_{start[:4]}"
            if len(tr) == 0:
                out[key] = {"trades": 0, **info}; continue
            peak = np.maximum.accumulate(np.r_[1000.0, tr.balance.values])[:-1]
            dd = np.maximum(peak - tr.equity_low.values, peak - tr.balance.values) / peak * 100
            mon = tr.groupby(tr.exit_time.dt.to_period("M")).agg(trades=("net", "size"), net=("net", "sum"), balance=("balance", "last"))
            out[key] = {"trades": int(len(tr)), "final_balance": round(float(tr.balance.iloc[-1]), 2),
                        "return_pct": round(float(tr.balance.iloc[-1] / 10 - 100), 1), "max_dd_pct": round(float(dd.max()), 1),
                        "profit_factor": round(float(tr.net[tr.net > 0].sum() / -tr.net[tr.net < 0].sum()), 3),
                        "win_pct": round(float((tr.net > 0).mean() * 100), 1), "avg_risk_pct_first10": round(float((tr.risk_money / (tr.balance - tr.net)).head(10).mean() * 100), 1),
                        "max_risk_pct": round(float((tr.risk_money / (tr.balance - tr.net)).max() * 100), 1),
                        "months_positive_pct": round(float((mon.net > 0).mean() * 100), 1), "worst_month": round(float(mon.net.min()), 2),
                        "best_month": round(float(mon.net.max()), 2), "long_trades": int((tr.side == 1).sum()), "short_trades": int((tr.side == -1).sum()),
                        "short_net": round(float(tr[tr.side == -1].net.sum()), 2), **info}
            monthly_tables[key] = mon
            mon.to_csv(ROOT / "reports" / f"oco_monthly_{key.replace('|', '_')}.csv")
(ROOT / "reports" / "oco_final.json").write_text(json.dumps(out, indent=1, default=str))
print(json.dumps(out, indent=1, default=str))
