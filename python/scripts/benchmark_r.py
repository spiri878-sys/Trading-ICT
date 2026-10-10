"""Sizing-independent comparison (isolated per-signal outcomes in R) + 1%-risk portfolio run.
Same profiles as benchmark_final.py. Test period already opened once there; re-reading it here does
not change any decision (no parameters are selected in this script)."""
import sys, json
from dataclasses import replace
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pandas as pd
from raptor import pipeline as P, metrics as M
from raptor.costs import C1, C0, C0R, with_cost
from raptor.engine import LOT_RISK
sys.path.insert(0, str(Path(__file__).resolve().parent))
from benchmark_final import PROFILES

ROOT = Path(__file__).resolve().parents[2]
rows = []
for name, pf in PROFILES.items():
    for cname, cm in [("C1", C1), ("C0R_rescaled", C0R), ("C0_recorded", C0)]:
        base = replace(P.Params(), **pf["ex"])
        with with_cost(cm, base) as prm:
            lab, _ = P.labelled(pf["strat"], prm, tf=pf["tf"], swing_k=pf["k"])
        for per in ["dev", "val", "test"]:
            d = P.in_period(lab, per)
            rows.append({"profile": name, "cost": cname, "period": per, "kind": "isolated_R", **M.r_stats(d.r)})
        for per in ["dev", "val", "test"]:
            with with_cost(cm, replace(base, lot_mode=LOT_RISK, risk_percent=1.0, initial_balance=1000.0)) as prm:
                s = P.in_period(P.signals(pf["strat"], pf["tf"], pf["k"]), per).reset_index(drop=True)
                tr, _ = P.backtest(s, prm, tf=pf["tf"])
            a, b = P.PERIODS[per]
            m = M.summarize(tr, 1000.0, a, b)
            rows.append({"profile": name, "cost": cname, "period": per, "kind": "portfolio_risk1pct",
                         "n": m["trades"], "mean_R": m.get("expectancy_R"), "pf": m.get("profit_factor"),
                         "win_pct": m.get("win_rate_pct"), "return_pct": m.get("return_pct"), "max_dd_pct": m.get("max_dd_pct"),
                         "max_losing_streak": m.get("max_losing_streak"), "positive_months_pct": m.get("positive_months_pct")})
df = pd.DataFrame(rows)
df.to_csv(ROOT / "reports" / "benchmark_r.csv", index=False)
pd.set_option("display.width", 250)
print(df.to_string())
