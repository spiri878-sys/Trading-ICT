"""TF-02: pre-registered literature rule (not chosen from results): H4 Donchian-55 breakout (Turtle system 2
style), initial stop 3 ATR(20), trailing 3 ATR from entry, no TP, max hold 60 days, no Friday close, one
position, 1% risk, capital 10,000, cost C1 (+ C2 stress). Long+short and long-only. Buy & hold for reference."""
import sys, json
from dataclasses import replace
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np, pandas as pd
from raptor import pipeline as P, metrics as M, data as D
from raptor.indicators import atr
from raptor.engine import LOT_RISK
from raptor.costs import C1, C2, with_cost

ROOT = Path(__file__).resolve().parents[2]
b = D.resample(P.m1(), "4h")
h, l, c = b.high.values, b.low.values, b.close.values
a = atr(h, l, c, 20)
N = 55
hi = pd.Series(h).rolling(N).max().shift(1).values; lo = pd.Series(l).rolling(N).min().shift(1).values
prev = pd.Series(c).shift(1).values
up = (c > hi) & (prev <= hi); dn = (c < lo) & (prev >= lo)
frames = []
for m, side in ((up, 1), (dn, -1)):
    idx = np.flatnonzero(m & np.isfinite(a))
    frames.append(pd.DataFrame({"bar_i": idx, "bar_time": b.index[idx], "side": side, "otype": "market", "price": c[idx],
                                "sl_struct": c[idx] - side * 3 * a[idx], "atr": a[idx], "expiry_bars": 1, "strategy": "TURTLE_H4_55"}))
S = pd.concat(frames).sort_values("bar_time").reset_index(drop=True)
EX = dict(tp_r=100.0, p1_frac=0.0, p2_frac=0.0, be_after_p1=False, trail_atr=3.0, max_hold_min=60 * 1440,
          friday_close_min=24 * 60, lot_mode=LOT_RISK, risk_percent=1.0, initial_balance=10000.0)
out = {}
for cname, cm in [("C1", C1), ("C2", C2)]:
    for variant, ss in [("long_short", S), ("long_only", S[S.side == 1].reset_index(drop=True))]:
        for per, (x, y) in {"2018_2026": ("2018-01-01", "2026-10-10"), "2022_2026": ("2022-01-01", "2026-10-10")}.items():
            with with_cost(cm, replace(P.Params(), **EX)) as prm:
                s2 = ss[(ss.bar_time >= x) & (ss.bar_time < y)].reset_index(drop=True)
                tr, st = P.backtest(s2, prm, tf="4h")
            mm = M.summarize(tr, 10000.0, x, y)
            out[f"{cname}|{variant}|{per}"] = {k: mm.get(k) for k in ["trades", "return_pct", "profit_factor", "win_rate_pct",
                                                                      "expectancy_R", "max_dd_pct", "max_losing_streak",
                                                                      "yearly_net", "by_strategy_R"]}
            if cname == "C1" and per == "2018_2026":
                tr.to_csv(ROOT / "reports" / f"trades_TURTLE_H4_55_{variant}_C1.csv", index=False)
                sh = tr[tr.side == -1]
                out[f"{cname}|{variant}|{per}"]["short_trades_R"] = round(float(sh.r_mult.mean()), 3) if len(sh) else None
                out[f"{cname}|{variant}|{per}"]["long_trades_R"] = round(float(tr[tr.side == 1].r_mult.mean()), 3)
m1 = P.m1()
bh = {str(yy): round(float(g.close.iloc[-1] / g.close.iloc[0] * 100 - 100), 1) for yy, g in m1.groupby(m1.index.year)}
out["buy_and_hold_gold_pct_by_year"] = bh
out["buy_and_hold_2018_2026_pct"] = round(float(m1.close.iloc[-1] / m1.close.iloc[0] * 100 - 100), 1)
(ROOT / "reports" / "turtle_portfolio.json").write_text(json.dumps(out, indent=1, default=str))
print(json.dumps(out, indent=1, default=str))
