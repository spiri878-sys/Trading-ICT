"""Candidate C (walk-forward survivor WF-01): UNIOF long only, M15 structure (k=3), stop beyond the last
confirmed H4 swing low (+0.2 ATR H4, max 6 ATR H4), market... no: limit entry at the unicorn overlap,
TP 3R, max hold 48h, no partials. Portfolio simulation, 1 position, risk 1% of balance, capital 10,000.
Periods: full 2018-2026, legit walk-forward OOS stretch 2022-2026; costs C1 / C0R / C2."""
import sys, json
from dataclasses import replace
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pandas as pd
from raptor import pipeline as P, metrics as M
from raptor.costs import C1, C0R, C2, with_cost
from raptor.engine import LOT_RISK

ROOT = Path(__file__).resolve().parents[2]
EX = dict(tp_r=3.0, p1_frac=0.0, p2_frac=0.0, be_after_p1=False, max_hold_min=2880)
f = P.feats("15min", 3)
s = P.signals({"UNIOF": {"expiry": 4, "max_r_atr": 40.0}}, "15min", 3)
s = P.apply_htf_stop(s, f, "h4")
s = s[s.side == 1].reset_index(drop=True)
out = {}
for cname, cm in [("C1", C1), ("C0R", C0R), ("C2", C2)]:
    for per, (a, b) in {"2018_2026": ("2018-01-01", "2026-10-10"), "OOS_2022_2026": ("2022-01-01", "2026-10-10")}.items():
        with with_cost(cm, replace(P.Params(), **EX, lot_mode=LOT_RISK, risk_percent=1.0, initial_balance=10000.0)) as prm:
            ss = s[(s.bar_time >= a) & (s.bar_time < b)].reset_index(drop=True)
            tr, st = P.backtest(ss, prm, tf="15min")
        m = M.summarize(tr, 10000.0, a, b)
        out[f"{cname}|{per}"] = {k: m.get(k) for k in ["trades", "net_profit", "return_pct", "profit_factor", "win_rate_pct",
                                                      "expectancy_R", "max_dd_pct", "max_losing_streak", "trades_per_month",
                                                      "positive_months_pct", "yearly_net", "exit_reasons"]}
        if cname == "C1":
            tr.to_csv(ROOT / "reports" / f"trades_CAND_C_unicorn_long_{per}_C1.csv", index=False)
(ROOT / "reports" / "candidate_c_portfolio.json").write_text(json.dumps(out, indent=1, default=str))
print(json.dumps(out, indent=1, default=str))
