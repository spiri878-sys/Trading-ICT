"""Range definitions for the OCO breakout straddle (used by research scripts and mirrored by the EA)."""
import numpy as np
import pandas as pd
from . import pipeline as P


def setups(kind, buf=0.1, stop="range", stop_k=1.5, N=12, sq=1.0, regime="both"):
    if kind in ("ASIA", "PDHL"):
        f = P.feats("15min", 3); tfm = 15
        hr, mi = f.index.hour, f.index.minute
        if kind == "ASIA":
            m = (hr == 6) & (mi == 45)
            hi, lo = f.asia_hi.shift(-1).values, f.asia_lo.shift(-1).values   # asia range known at the 07:00 bar
            # the 06:45 bar closes at 07:00: compute the range from bars 03:00-06:59 directly (causal)
            day = f.index.normalize()
            asia = (hr >= 3) & (hr < 7)
            ah = f.high.where(asia).groupby(day).transform("max").values
            al = f.low.where(asia).groupby(day).transform("min").values
            hi, lo = ah, al
            valid = 64                                                        # until 23:00 server
        else:
            m = (hr == 1) & (mi == 0)
            hi, lo = f.pdh.values, f.pdl.values
            valid = 87
        a = f.h1_atr.values
    else:
        f = P.feats("1h", 3); tfm = 60
        hi = pd.Series(f.high.values).rolling(N).max().values
        lo = pd.Series(f.low.values).rolling(N).min().values
        a = f.atr.values
        m = np.ones(len(f), bool)
        if kind == "SQZ":
            m &= (hi - lo) <= sq * a * np.sqrt(N)
        valid = 1
    idx = np.flatnonzero(m & np.isfinite(hi) & np.isfinite(lo) & np.isfinite(a))
    hi, lo, a = hi[idx], lo[idx], a[idx]
    p_hi, p_lo = hi + buf * a, lo - buf * a
    if stop == "range":
        sl_hi, sl_lo = p_lo, p_hi
    else:
        sl_hi, sl_lo = p_hi - stop_k * a, p_lo + stop_k * a
    if regime == "filter":
        bull = ((f.d1_close.values > f.d1_ema.values) & (f.h4_trend.values > 0))[idx]
        bear = ((f.d1_close.values < f.d1_ema.values) & (f.h4_trend.values < 0))[idx]
        p_lo = np.where(bull, -1e9, p_lo)          # bull: buy stop only
        p_hi = np.where(bear, 1e9, p_hi)           # bear: sell stop only
        keep = bull | bear                          # mixed regime: no orders
        idx, hi, lo, a, p_hi, p_lo, sl_hi, sl_lo = (x[keep] for x in (idx, hi, lo, a, p_hi, p_lo, sl_hi, sl_lo))
    s = pd.DataFrame({"bar_time": f.index[idx], "valid_bars": valid, "p_hi": p_hi, "p_lo": p_lo, "sl_hi": sl_hi,
                      "sl_lo": sl_lo, "atr": a})
    rng = (hi - lo) / a
    s = s[(rng >= 0.5) & (rng <= 8.0)]       # skip degenerate / huge ranges
    return s, tfm


