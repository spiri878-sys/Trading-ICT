"""Is the H4 Donchian-55 long timing better than RANDOM long entries with identical exits (3 ATR stop, 3 ATR
trailing, 5-day max hold, C1 + swap)? 200 random draws of the same number of entries per year.
Also: portfolio simple (no regime filter) vs regime-filtered, long only, 1% risk."""
import sys, json
from dataclasses import replace
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np, pandas as pd
from raptor import pipeline as P, metrics as M
from raptor.engine import label, LOT_RISK
from raptor.costs import C1, with_cost
sys.path.insert(0, str(Path(__file__).resolve().parent))
import importlib.util
spec = importlib.util.spec_from_file_location("fc", Path(__file__).resolve().parent / "final_candidate.py")

ROOT = Path(__file__).resolve().parents[2]
f4 = P.feats("4h", 2)
EX = dict(tp_r=100.0, p1_frac=0.0, p2_frac=0.0, be_after_p1=False, trail_atr=3.0, max_hold_min=5 * 1440, friday_close_min=24 * 60)


def sig(regime):
    c, h = f4.close.values, f4.high.values
    hi = pd.Series(h).rolling(55).max().shift(1).values
    prev = np.r_[np.nan, c[:-1]]
    with np.errstate(invalid="ignore"):
        up = (c > hi) & (prev <= hi)
        if regime:
            up &= (f4.d1_close.values > f4.d1_ema.values) & (f4.h4_trend.values > 0)
    idx = np.flatnonzero(up & np.isfinite(f4.atr.values))
    return pd.DataFrame({"bar_i": idx, "bar_time": f4.index[idx], "side": 1, "otype": "market", "price": c[idx],
                         "sl_struct": c[idx] - 3 * f4.atr.values[idx], "atr": f4.atr.values[idx], "expiry_bars": 1, "strategy": "T"})


out = {}
with with_cost(C1, replace(P.Params(), **EX)) as prm:
    real = label(P.market(), sig(True), prm, 240); real = real[real.filled]
    rng = np.random.default_rng(3)
    valid = np.flatnonzero(np.isfinite(f4.atr.values) & (f4.index >= "2018-03-01"))
    years = f4.index.year.values
    per_year_counts = real.groupby(real.bar_time.dt.year).size()
    rand_means, rand_year = [], {y: [] for y in per_year_counts.index}
    for _ in range(200):
        idx = np.sort(np.concatenate([rng.choice(valid[years[valid] == y], n, replace=False) for y, n in per_year_counts.items()]))
        s = pd.DataFrame({"bar_i": idx, "bar_time": f4.index[idx], "side": 1, "otype": "market", "price": f4.close.values[idx],
                          "sl_struct": f4.close.values[idx] - 3 * f4.atr.values[idx], "atr": f4.atr.values[idx], "expiry_bars": 1, "strategy": "R"})
        rl = label(P.market(), s, prm, 240); rl = rl[rl.filled]
        rand_means.append(rl.r.mean())
        for y, g in rl.groupby(rl.bar_time.dt.year):
            rand_year[y].append(g.r.mean())
rm = np.array(rand_means)
out["strategy_meanR"] = round(float(real.r.mean()), 4)
out["random_long_meanR_mean_p95_p99"] = [round(float(rm.mean()), 4), round(float(np.percentile(rm, 95)), 4), round(float(np.percentile(rm, 99)), 4)]
out["p_value_vs_random"] = round(float((rm >= real.r.mean()).mean()), 4)
out["by_year_strategy_vs_random_mean"] = {int(y): [round(float(g.r.mean()), 3), round(float(np.mean(rand_year[y])), 3)]
                                         for y, g in real.groupby(real.bar_time.dt.year)}
for name, reg in (("simple", False), ("regime", True)):
    with with_cost(C1, replace(P.Params(), **EX, lot_mode=LOT_RISK, risk_percent=1.0, initial_balance=10000.0)) as prm:
        tr, _ = P.backtest(sig(reg), prm, tf="4h")
    m = M.summarize(tr, 10000.0, "2018-01-01", "2026-10-10")
    out[f"portfolio_long_{name}"] = {k: m[k] for k in ["trades", "return_pct", "profit_factor", "expectancy_R", "max_dd_pct", "max_losing_streak"]}
(ROOT / "reports" / "final_candidate_vs_random.json").write_text(json.dumps(out, indent=1, default=str))
print(json.dumps(out, indent=1, default=str))
