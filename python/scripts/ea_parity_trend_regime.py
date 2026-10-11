"""Parity check (Phase I): recompute the TREND_REGIME decision exactly as the EA does - truncated windows of
CLOSED bars (H4: last DonchianBars+AtrPeriod+400 bars for ATR/Donchian, last 1500 H4 bars for the structure
trend, last 600 D1 bars for EMA50 seeded at the window start) - and compare with the full-history research
features for every H4 bar 2019-2026. Mismatches are listed, not hidden."""
import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np, pandas as pd
from raptor import pipeline as P, data as D
from raptor.indicators import atr, ema, confirmed_swings
from raptor.setups import _structure

ROOT = Path(__file__).resolve().parents[2]
m1 = P.m1()
h4 = D.resample(m1, "4h"); d1 = D.resample(m1, "1D")
f4 = P.feats("4h", 2)
H, L_, C = h4.high.values, h4.low.values, h4.close.values
O = h4.open.values
N, AP, WIN_ATR, WIN_TR, WIN_D1 = 55, 14, 55 + 14 + 400, 1500, 600
d1_avail = d1.index + pd.Timedelta(days=1)
idxs = np.flatnonzero(h4.index >= "2019-01-01")
mism = {"signal": 0, "regime_d1": 0, "trend_h4": 0, "atr_rel_diff_gt_1pct": 0}
examples = []
full_hi = pd.Series(H).rolling(N).max().shift(1).values
for i in idxs:
    # EA: CopyRates(H4, shift 1, need) -> bars [i-need+1 .. i]
    s0 = max(0, i - WIN_ATR + 1)
    a_ea = atr(H[s0:i + 1], L_[s0:i + 1], C[s0:i + 1], AP)[-1]
    a_full = f4.atr.values[i]
    if abs(a_ea / a_full - 1) > 0.01:
        mism["atr_rel_diff_gt_1pct"] += 1
    hi = H[i - N:i].max()
    sig_ea = C[i] > hi and C[i - 1] <= hi
    sig_full = C[i] > full_hi[i] and C[i - 1] <= full_hi[i]
    if sig_ea != sig_full:
        mism["signal"] += 1
    t_dec = h4.index[i] + pd.Timedelta(hours=4)
    nd = np.searchsorted(d1_avail.values, t_dec.to_datetime64(), side="right")
    w = d1.close.values[max(0, nd - WIN_D1):nd]
    reg_ea = np.sign(w[-1] - ema(w, 50)[-1])
    reg_full = np.sign(f4.d1_close.values[i] - f4.d1_ema.values[i])
    if reg_ea != reg_full:
        mism["regime_d1"] += 1
    if sig_full:   # the structure trend is only needed when a breakout occurs (costly: compute only then)
        t0 = max(0, i - WIN_TR + 1)
        sh, shi, slv, sli = confirmed_swings(H[t0:i + 1], L_[t0:i + 1], 2)
        brk = _structure(O[t0:i + 1], H[t0:i + 1], L_[t0:i + 1], C[t0:i + 1], sh, shi, slv, sli)[0]
        nz = brk[brk != 0]
        tr_ea = nz[-1] if len(nz) else 0
        tr_full = np.sign(f4.h4_trend.values[i])
        if tr_ea != tr_full:
            mism["trend_h4"] += 1
            examples.append(str(h4.index[i]))
res = {"h4_bars_checked": int(len(idxs)), "breakout_bars": int(np.nansum([C[i] > full_hi[i] and C[i - 1] <= full_hi[i] for i in idxs])),
       "mismatches": mism, "trend_mismatch_examples": examples[:10]}
(ROOT / "reports" / "ea_parity_trend_regime.json").write_text(json.dumps(res, indent=1))
print(json.dumps(res, indent=1))
