"""FINAL CANDIDATE deep dive: 'TREND-REGIME' = H4 Donchian-N breakout + higher-timeframe regime filter.
Long: H4 close > previous N-bar high AND D1 close > D1 EMA50 AND last H4 structure break up.
Short (mirror): H4 close < previous N-bar low AND D1 close < D1 EMA50 AND last H4 structure break down.
Stop k x ATR14(H4, Wilder; column `atr` of the 4h feature frame), trailing k x ATR from entry, no TP, max hold 5 days, weekend held (swap charged).
1) simple vs regime-filtered; 2) long vs short; 3) sensitivity grid; 4) costs x2; 5) portfolio 1% risk;
6) Monte Carlo (block bootstrap) of drawdown. Cost model C1 + swap."""
import sys, json, itertools
from dataclasses import replace
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np, pandas as pd
from raptor import pipeline as P, metrics as M
from raptor.engine import label, LOT_RISK
from raptor.costs import C1, C2, with_cost

ROOT = Path(__file__).resolve().parents[2]
f4 = P.feats("4h", 2)


def signals(n=55, k=3.0, regime=True, ema_col="d1_ema"):
    c, h, l = f4.close.values, f4.high.values, f4.low.values
    a = f4.atr.values
    hi = pd.Series(h).rolling(n).max().shift(1).values
    lo = pd.Series(l).rolling(n).min().shift(1).values
    prev = np.r_[np.nan, c[:-1]]
    with np.errstate(invalid="ignore"):
        up = (c > hi) & (prev <= hi)
        dn = (c < lo) & (prev >= lo)
        if regime:
            up &= (f4.d1_close.values > f4[ema_col].values) & (f4.h4_trend.values > 0)
            dn &= (f4.d1_close.values < f4[ema_col].values) & (f4.h4_trend.values < 0)
    rows = []
    for m, side in ((up, 1), (dn, -1)):
        idx = np.flatnonzero(m & np.isfinite(a))
        rows.append(pd.DataFrame({"bar_i": idx, "bar_time": f4.index[idx], "side": side, "otype": "market", "price": c[idx],
                                  "sl_struct": c[idx] - side * k * a[idx], "atr": a[idx], "expiry_bars": 1, "strategy": "TREND_REGIME"}))
    return pd.concat(rows).sort_values("bar_time").reset_index(drop=True)


def ex(k=3.0, hold_d=5):
    return dict(tp_r=100.0, p1_frac=0.0, p2_frac=0.0, be_after_p1=False, trail_atr=k, max_hold_min=hold_d * 1440,
                friday_close_min=24 * 60)


def lab(s, cm=C1, **kw):
    with with_cost(cm, replace(P.Params(), **ex(**kw))) as prm:
        x = label(P.market(), s, prm, 240)
    return x[x.filled]


out = {}
# 1-2) simple vs filtered, long vs short, per period
for name, reg in [("simple", False), ("regime", True)]:
    x = lab(signals(regime=reg))
    for side, g in x.groupby("side"):
        key = f"{name}_{'long' if side == 1 else 'short'}"
        out[key] = {per: M.r_stats(P.in_period(g, per).r) for per in P.PERIODS}
        out[key]["all"] = M.r_stats(g.r)
        out[key]["by_year_meanR"] = g.groupby(g.bar_time.dt.year).r.mean().round(3).to_dict()
# 3) sensitivity (regime, long and short), 4) costs x2
grid = []
for n, k, hold, emac in itertools.product((40, 55, 70), (2.0, 2.5, 3.0, 3.5), (3, 5, 10), ("d1_ema",)):
    x = lab(signals(n=n, k=k), k=k, hold_d=hold)
    for side, g in x.groupby("side"):
        grid.append({"n": n, "k": k, "hold_d": hold, "side": "long" if side == 1 else "short", "N": len(g),
                     "meanR": round(g.r.mean(), 3), "meanR_2022_2026": round(g[g.bar_time >= "2022"].r.mean(), 3)})
G = pd.DataFrame(grid)
G.to_csv(ROOT / "experiments" / "final_candidate_sensitivity.csv", index=False)
for sd in ("long", "short"):
    gg = G[G.side == sd]
    out[f"sensitivity_{sd}"] = {"points": len(gg), "share_pos": round(float((gg.meanR > 0).mean()), 3),
                                "median_R": round(float(gg.meanR.median()), 3), "min_R": float(gg.meanR.min()), "max_R": float(gg.meanR.max())}
x2 = lab(signals(), cm=C2)
out["costs_x2_long"] = M.r_stats(x2[x2.side == 1].r); out["costs_x2_short"] = M.r_stats(x2[x2.side == -1].r)
# 5) portfolio: 1% risk, 10k, one position; long-only and long+short
port = {}
for variant in ("long_only", "long_short"):
    s = signals()
    if variant == "long_only":
        s = s[s.side == 1].reset_index(drop=True)
    for per, (a, b) in {"2018_2026": ("2018-01-01", "2026-10-10"), "2022_2026": ("2022-01-01", "2026-10-10")}.items():
        for cname, cm in (("C1", C1), ("C2", C2)):
            with with_cost(cm, replace(P.Params(), **ex(), lot_mode=LOT_RISK, risk_percent=1.0, initial_balance=10000.0)) as prm:
                ss = s[(s.bar_time >= a) & (s.bar_time < b)].reset_index(drop=True)
                tr, _ = P.backtest(ss, prm, tf="4h")
            m = M.summarize(tr, 10000.0, a, b)
            keep = ["trades", "net_profit", "return_pct", "profit_factor", "win_rate_pct", "expectancy_R", "payoff_ratio",
                    "max_dd_money", "max_dd_pct", "max_losing_streak", "trades_per_month", "positive_months_pct", "yearly_net", "exposure_pct"]
            port[f"{variant}|{per}|{cname}"] = {k: m.get(k) for k in keep}
            if cname == "C1" and per == "2018_2026":
                tr.to_csv(ROOT / "reports" / f"trades_TREND_REGIME_{variant}.csv", index=False)
                if variant == "long_only":
                    final_tr = tr
out["portfolio"] = port
# 6) Monte Carlo: block bootstrap (blocks of 10 trades) of the long-only R sequence at 1% risk, 5000 paths
r = final_tr.r_mult.values
rng = np.random.default_rng(1)
dds, finals = [], []
for _ in range(5000):
    blocks = [r[i:i + 10] for i in rng.integers(0, max(1, len(r) - 10), size=len(r) // 10 + 1)]
    seq = np.concatenate(blocks)[:len(r)]
    eq = 10000 * np.cumprod(1 + 0.01 * seq)
    peak = np.maximum.accumulate(np.r_[10000, eq])[1:]
    dds.append(float(((peak - eq) / peak).max() * 100)); finals.append(float(eq[-1] / 10000 * 100 - 100))
out["monte_carlo_long_only_1pct"] = {"paths": 5000, "trades_per_path": int(len(r)),
                                    "return_pct_p5_p50_p95": [round(float(np.percentile(finals, q)), 1) for q in (5, 50, 95)],
                                    "maxDD_pct_p50_p95_p99": [round(float(np.percentile(dds, q)), 1) for q in (50, 95, 99)],
                                    "prob_loss_pct": round(float(np.mean(np.array(finals) < 0) * 100), 1)}
(ROOT / "reports" / "final_candidate.json").write_text(json.dumps(out, indent=1, default=str))
print(json.dumps(out, indent=1, default=str))
