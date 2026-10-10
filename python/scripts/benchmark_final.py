"""FINAL BENCHMARK (run once; the 2024-2026 test period is opened here for the first and only time).

Reference profile (spec section 15): XAUUSD M5, initial capital 1000, fixed lot 0.10, one position.
Profiles compared under identical execution/costs:
  ICT_FAITHFUL  5 cells (PPK, OTEOF, PO3, UNIOF, LS) on M5 structure, ladder exits 20%@0.7R+BE, 20%@2R, 60%@4R
  WYCKOFF       spring/upthrust benchmark, same exits
  CAND_A_H1     rejected candidate (H1 continuation) for the record
Account currency: P&L is computed in USD; capital 1000 is treated as 1000 USD-equivalent (no EURUSD
series available to convert EUR, see docs/limits.md).
"""
import sys, json
from dataclasses import replace
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pandas as pd
from raptor import pipeline as P, metrics as M
from raptor.costs import C0, C0R, C1, C2, with_cost
from raptor.engine import LOT_FIXED

ROOT = Path(__file__).resolve().parents[2]
LADDER = dict(tp_r=4.0, p1_r=0.7, p1_frac=0.2, p2_r=2.0, p2_frac=0.2, be_after_p1=True, mgmt_on_close=True, max_hold_min=4320)
PROFILES = {
    "ICT_FAITHFUL": dict(strat={c: {} for c in ["PPK", "OTEOF", "PO3", "UNIOF", "LS"]}, tf="5min", k=3, ex=LADDER),
    "WYCKOFF": dict(strat={"WYCKOFF": {}}, tf="5min", k=3, ex=LADDER),
    "CAND_A_H1": dict(strat={c: {"expiry": 4, "max_r_atr": 30.0, "min_r_atr": 0.3, "market_entry": True, "min_disp": 1.2}
                             for c in ["PPK", "UNIOF"]}, tf="1h", k=3,
                      ex=dict(tp_r=3.0, p1_frac=0.0, p2_frac=0.0, be_after_p1=False, max_hold_min=2880)),
}
def main():
    KEYS = ["trades", "net_profit", "return_pct", "profit_factor", "win_rate_pct", "trades_per_month", "expectancy_R",
            "payoff_ratio", "max_dd_money", "max_dd_pct", "max_losing_streak", "positive_months_pct", "commission_total",
            "spread_cost_est", "avg_risk_pct_of_balance", "final_balance", "yearly_net"]
    res = {}
    for name, pf in PROFILES.items():
        for cname, cm in [("C1", C1), ("C0R_rescaled", C0R), ("C0_recorded", C0), ("C2", C2)]:
            for per in ["dev", "val", "test"]:
                with with_cost(cm, replace(P.Params(), **pf["ex"], lot_mode=LOT_FIXED, fixed_lot=0.10, initial_balance=1000.0)) as prm:
                    s = P.signals(pf["strat"], pf["tf"], pf["k"])
                    s = P.in_period(s, per).reset_index(drop=True)
                    tr, st = P.backtest(s, prm, tf=pf["tf"])
                a, b = P.PERIODS[per]
                m = M.summarize(tr, 1000.0, a, b)
                res[f"{name}|{cname}|{per}"] = {k: m.get(k) for k in KEYS} | {"signals": len(s), "status": st.status.value_counts().to_dict()}
                if cname == "C1":
                    tr.to_csv(ROOT / "reports" / f"trades_{name}_{per}_C1.csv", index=False)
    (ROOT / "reports" / "benchmark_final.json").write_text(json.dumps(res, indent=1, default=str))
    rows = [{"profile": k.split("|")[0], "cost": k.split("|")[1], "period": k.split("|")[2],
             **{x: v[x] for x in ["trades", "net_profit", "return_pct", "profit_factor", "win_rate_pct", "expectancy_R",
                                  "max_dd_pct", "max_losing_streak", "trades_per_month", "positive_months_pct", "final_balance"]}}
            for k, v in res.items()]
    df = pd.DataFrame(rows)
    df.to_csv(ROOT / "reports" / "benchmark_final.csv", index=False)
    pd.set_option("display.width", 250)
    print(df.to_string())


if __name__ == "__main__":
    main()
