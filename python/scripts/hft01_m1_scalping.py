"""HFT-01: M1 scalping families (no grid, no martingale), long and short, isolated per-signal outcomes.
Signals on closed M1 bars, market entry at next M1 open, SL/TP in ATR(M1,14) units, max hold in minutes.
Cost scenarios: ZERO (gross edge), ECN (recorded spread 2023+ regime: fixed 0.10 USD + 7 USD/lot commission +
0.02 slippage), STD (C1: 0.30 spread + 7 USD/lot + 0.05 slippage). Swap ignored (intraday, flat before rollover
not enforced -> negligible for <= 60 min holds)."""
import sys, json, itertools
from dataclasses import replace
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np, pandas as pd
from raptor import pipeline as P, metrics as M
from raptor.engine import label
from raptor.indicators import atr

ROOT = Path(__file__).resolve().parents[2]
m1 = P.m1(); mk = P.market()
o, h, l, c = (m1[k].values for k in ("open", "high", "low", "close"))
a = atr(h, l, c, 14)
idx = m1.index
nyh = (idx - pd.Timedelta(hours=7)).hour.values
nym = nyh * 60 + (idx - pd.Timedelta(hours=7)).minute.values
active = (nyh >= 3) & (nyh < 16)                 # London + NY sessions (avoid thin Asia)
body = c - o
s20 = pd.Series(c).rolling(20)
mid, sd = s20.mean().values, s20.std(ddof=0).values


def fam_signals(name, p):
    if name == "IMPULSE":            # strong M1 candle -> follow
        k = p["k"]
        up = active & (body > k * a); dn = active & (-body > k * a)
    elif name == "MR_BB":             # close beyond Bollinger(20, k) -> fade
        k = p["k"]
        up = active & (c < mid - k * sd); dn = active & (c > mid + k * sd)
    elif name == "MICRO_BO":          # close beyond the previous N-minute range
        n = p["n"]
        hi = pd.Series(h).rolling(n).max().shift(1).values; lo = pd.Series(l).rolling(n).min().shift(1).values
        prev = np.r_[np.nan, c[:-1]]
        up = active & (c > hi) & (prev <= hi); dn = active & (c < lo) & (prev >= lo)
    elif name == "NY_OPEN":           # direction of the first `m` minutes after 09:30 NY
        m = p["m"]
        t = (nym == 570 + m - 1)
        open_px = pd.Series(np.where(nym == 570, o, np.nan)).ffill().values
        up = t & (c > open_px); dn = t & (c < open_px)
    up &= np.isfinite(a); dn &= np.isfinite(a)
    ii = np.flatnonzero(up | dn)
    side = np.where(up[ii], 1, -1)
    sl_k = p["sl"]
    return pd.DataFrame({"bar_i": ii, "bar_time": idx[ii], "side": side, "otype": "market", "price": c[ii],
                         "sl_struct": c[ii] - side * sl_k * a[ii], "atr": a[ii], "expiry_bars": 1, "strategy": name})


GRID = [("IMPULSE", dict(k=k, sl=sl, tp=tp, hold=hd)) for k in (2.0, 3.0) for sl in (1.0, 2.0) for tp in (1.0, 2.0) for hd in (15, 60)] + \
       [("MR_BB", dict(k=k, sl=sl, tp=tp, hold=hd)) for k in (2.5, 3.0) for sl in (1.0, 2.0) for tp in (1.0, 2.0) for hd in (15, 60)] + \
       [("MICRO_BO", dict(n=n, sl=sl, tp=tp, hold=hd)) for n in (15, 30) for sl in (1.0, 2.0) for tp in (1.0, 2.0) for hd in (15, 60)] + \
       [("NY_OPEN", dict(m=m, sl=sl, tp=tp, hold=hd)) for m in (5, 15) for sl in (2.0, 4.0) for tp in (1.0, 2.0) for hd in (30, 120)]
COSTS = {"ZERO": (0.0, 0.0, 0.0), "ECN": (0.10, 3.5, 0.02), "STD": (0.30, 3.5, 0.05)}
rows = []
for name, p in GRID:
    s = fam_signals(name, p)
    if len(s) > 400000:              # keep the label run tractable: deterministic thinning (every k-th signal)
        s = s.iloc[:: int(np.ceil(len(s) / 400000))].reset_index(drop=True)
    for cn, (spr, comm, slip) in COSTS.items():
        raw = mk.sp_raw.copy(); mk.sp_raw[:] = spr
        prm = replace(P.Params(), tp_r=p["tp"], p1_frac=0.0, p2_frac=0.0, be_after_p1=False, max_hold_min=p["hold"],
                      commission_per_lot_side=comm, slippage=slip, spread_floor=0.0, max_spread=5.0,
                      swap_long_annual=0.0, swap_short_annual=0.0)
        lab = label(mk, s, prm, 1)
        mk.sp_raw[:] = raw
        lab = lab[lab.filled]
        st = M.r_stats(lab.r)
        rows.append({"family": name, "params": json.dumps(p), "cost": cn, "n": st["n"], "mean_R": st["mean_R"], "t": st["t_stat"],
                     "win_pct": st["win_pct"], "long_R": round(float(lab[lab.side == 1].r.mean()), 3),
                     "short_R": round(float(lab[lab.side == -1].r.mean()), 3),
                     "trades_per_day": round(len(lab) / 2265, 1), "median_stop_usd": round(float(s.atr.median() * p["sl"]), 2)})
    print("done", name, p, flush=True)
D = pd.DataFrame(rows)
D.to_csv(ROOT / "experiments" / "hft01_m1_scalping.csv", index=False)
pd.set_option("display.width", 230)
piv = D.pivot_table(index=["family", "params"], columns="cost", values="mean_R").round(3)
print(piv.sort_values("ZERO", ascending=False).head(15).to_string())
print(D.groupby(["family", "cost"]).mean_R.agg(["median", "max", lambda x: (x > 0).mean()]).round(3).to_string())
