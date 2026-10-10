"""Spec 10 + 14: the four stop x lot combinations (plus structural/ATR) and stop width vs fixed/percent lot.
Signals: site-six combination on M5, ladder management, cost C1, validation period. Reports effective
money risk per trade. No parameter is selected here."""
import sys
from dataclasses import replace
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pandas as pd
from raptor import pipeline as P, metrics as M
from raptor.costs import C1, with_cost
from raptor.engine import STOP_FIXED, STOP_PERCENT, STOP_STRUCT, STOP_ATR, LOT_FIXED, LOT_RISK, STOP_NAMES, LOT_NAMES

ROOT = Path(__file__).resolve().parents[2]
LADDER = dict(tp_r=4.0, p1_r=0.7, p1_frac=0.2, p2_r=2.0, p2_frac=0.2, be_after_p1=True, mgmt_on_close=True, max_hold_min=4320)
SIX = {c: {} for c in ["UNIOF", "OTEOF", "SILVER_BULLET", "PO3", "MSS", "LS"]}
rows = []
for cap in (1000.0, 10000.0):
    for sm, skw in [(STOP_FIXED, dict(stop_fixed_usd=5.0)), (STOP_PERCENT, dict(stop_percent=0.25)),
                    (STOP_STRUCT, {}), (STOP_ATR, dict(stop_atr_mult=1.5))]:
        for lm in (LOT_FIXED, LOT_RISK):
            for per in ["dev", "val"]:
                base = replace(P.Params(), **LADDER, **skw, stop_mode=sm, lot_mode=lm, fixed_lot=0.08, risk_percent=1.0,
                               initial_balance=cap)
                with with_cost(C1, base) as prm:
                    s = P.in_period(P.signals(SIX, "5min", 3), per).reset_index(drop=True)
                    tr, st = P.backtest(s, prm)
                a, b = P.PERIODS[per]
                m = M.summarize(tr, cap, a, b)
                bal_before = (tr.balance - tr.net) if len(tr) else pd.Series(dtype=float)
                rows.append({"capital": cap, "stop": STOP_NAMES[sm], "lot": LOT_NAMES[lm], "period": per,
                             "trades": m.get("trades"), "avg_risk_money": m.get("avg_risk_money"),
                             "avg_risk_pct": m.get("avg_risk_pct_of_balance"),
                             "max_risk_pct": round(float((tr.risk_money / bal_before).max() * 100), 2) if len(tr) else None,
                             "expectancy_R": m.get("expectancy_R"), "return_pct": m.get("return_pct"), "max_dd_pct": m.get("max_dd_pct"),
                             "rejected": {k: v for k, v in st.status.value_counts().items() if k.startswith("rejected")}})
df = pd.DataFrame(rows)
df.to_csv(ROOT / "reports" / "stop_lot_combinations.csv", index=False)
pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 80)
print(df.to_string())

# stop width (min stop in ATR M15) with fixed lot vs 1% risk
rows = []
for ms in (0.0, 1.0, 2.0, 3.0, 4.0):
    for lm in (LOT_FIXED, LOT_RISK):
        base = replace(P.Params(), **LADDER, lot_mode=lm, fixed_lot=0.08, risk_percent=1.0, initial_balance=10000.0)
        with with_cost(C1, base) as prm:
            s = P.apply_min_stop(P.signals(SIX, "5min", 3), P.feats("5min", 3), ms)
            s = P.in_period(s, "dev").reset_index(drop=True)
            tr, st = P.backtest(s, prm)
        m = M.summarize(tr, 10000.0, *P.PERIODS["dev"])
        rows.append({"min_stop_atr_m15": ms, "lot": LOT_NAMES[lm], "trades": m["trades"], "median_stop_usd": round(float(tr.r_dist.median()), 2),
                     "avg_risk_money": m["avg_risk_money"], "avg_risk_pct": m["avg_risk_pct_of_balance"],
                     "expectancy_R": m["expectancy_R"], "return_pct": m["return_pct"], "max_dd_pct": m["max_dd_pct"]})
w = pd.DataFrame(rows)
w.to_csv(ROOT / "reports" / "stop_width_vs_lot.csv", index=False)
print(w.to_string())
