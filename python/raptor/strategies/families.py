"""Non-ICT strategy families for the comparative study (SPERIMENTALI, our own definitions).
Every function returns signals for BOTH sides; the research evaluates long and short separately.
All signals are decided on a CLOSED bar of the frame `f` and executed at the next bar (market) unless stated.

ASIA_BO     first close beyond the Asian range (server 03:00-07:00 = NY 20:00-00:00) inside a window
EMA_PB      H1+H4 trend (close vs EMA50) + pullback to EMA20 on the signal TF + close back in trend direction
SQUEEZE     Bollinger(20,2) width in the lowest `pct` of its last 120 bars, then close outside the band
DONCHIAN    close beyond the N-bar high/low
MR_BB       close outside Bollinger(20, k) with RSI14 extreme and low efficiency ratio (range regime) -> fade,
            target the middle band (per-signal tp_r)
RSI2        Connors-style: RSI(2) < lo (long) / > hi (short) with the 200-EMA trend filter; short exit target 1.5R
"""
import numpy as np
import pandas as pd

from ..indicators import ema, rsi
from .ict import _frame, _window


def _bb(c, n=20, k=2.0):
    s = pd.Series(c)
    mid = s.rolling(n).mean().values
    sd = s.rolling(n).std(ddof=0).values
    return mid, mid + k * sd, mid - k * sd


def _finish(f, up, dn, sl_up, sl_dn, name, p, tp_r=None, price=None):
    side = np.where(up, 1, -1)
    px = f.close.values if price is None else price
    sl = np.where(up, sl_up, sl_dn)
    a = f.atr.values
    with np.errstate(invalid="ignore"):
        risk = (px - sl) * side
        m = (up | dn) & (risk >= p.get("min_r_atr", 0.3) * a) & (risk <= p.get("max_r_atr", 30.0) * a)
    out = _frame(f, m, side, px, sl, name, p.get("expiry", 1), otype="market")
    if tp_r is not None:
        out["tp_r"] = np.clip(tp_r[out.bar_i.values], 0.5, 6.0)
    return out


def asia_bo(f, p):
    hr = f.index.hour
    a = f.atr.values
    ahi, alo = f.asia_hi.values, f.asia_lo.values
    c = f.close.values
    prev = np.r_[np.nan, c[:-1]]
    w0, w1 = p.get("window", (9, 19))          # server hours in which a breakout is accepted
    inwin = (hr >= w0) & (hr < w1)
    with np.errstate(invalid="ignore"):
        up = inwin & (c > ahi) & (prev <= ahi)
        dn = inwin & (c < alo) & (prev >= alo)
        rng = ahi - alo
        ok = (rng >= p.get("min_rng_atr", 0.5) * f.h1_atr.values) & (rng <= p.get("max_rng_atr", 4.0) * f.h1_atr.values)
    up &= ok; dn &= ok
    # only the first breakout per day and side
    day = f.index.normalize()
    up &= pd.Series(up).groupby(day).cumsum().values == 1
    dn &= pd.Series(dn).groupby(day).cumsum().values == 1
    if p.get("stop", "range") == "range":
        sl_up, sl_dn = alo - 0.1 * a, ahi + 0.1 * a
    else:
        k = p.get("atr_k", 1.5)
        sl_up, sl_dn = c - k * f.m15_atr.values, c + k * f.m15_atr.values
    return _finish(f, up, dn, sl_up, sl_dn, "ASIA_BO", p)


def ema_pb(f, p):
    c, l, h = f.close.values, f.low.values, f.high.values
    e20 = ema(c, p.get("fast", 20))
    up_tr = (f.h1_close.values > f.h1_ema.values) & (f.h4_close.values > f.h4_ema.values)
    dn_tr = (f.h1_close.values < f.h1_ema.values) & (f.h4_close.values < f.h4_ema.values)
    touched_lo = pd.Series(l <= e20).rolling(p.get("touch", 6)).max().values > 0
    touched_hi = pd.Series(h >= e20).rolling(p.get("touch", 6)).max().values > 0
    prev = np.r_[np.nan, c[:-1]]
    pe = np.r_[np.nan, e20[:-1]]
    with np.errstate(invalid="ignore"):
        up = up_tr & touched_lo & (c > e20) & (c > prev) & (prev <= pe * 1.0005)
        dn = dn_tr & touched_hi & (c < e20) & (c < prev) & (prev >= pe * 0.9995)
    a = f.atr.values
    lo6 = pd.Series(l).rolling(p.get("touch", 6)).min().values
    hi6 = pd.Series(h).rolling(p.get("touch", 6)).max().values
    k = p.get("buf", 0.3)
    return _finish(f, up, dn, lo6 - k * a, hi6 + k * a, "EMA_PB", p)


def squeeze(f, p):
    c = f.close.values
    mid, ub, lb = _bb(c, 20, 2.0)
    width = (ub - lb) / mid
    q = pd.Series(width).rolling(120, min_periods=60).quantile(p.get("pct", 0.2)).shift(1).values
    sq = pd.Series(width <= q).rolling(p.get("lookback", 10)).max().values > 0
    prev = np.r_[np.nan, c[:-1]]
    pu, pl = np.r_[np.nan, ub[:-1]], np.r_[np.nan, lb[:-1]]
    with np.errstate(invalid="ignore"):
        up = sq & (c > ub) & (prev <= pu)
        dn = sq & (c < lb) & (prev >= pl)
    k = p.get("atr_k", 2.0); a = f.atr.values
    return _finish(f, up, dn, c - k * a, c + k * a, "SQUEEZE", p)


def donchian(f, p):
    n = p.get("n", 55)
    c, h, l = f.close.values, f.high.values, f.low.values
    hi = pd.Series(h).rolling(n).max().shift(1).values
    lo = pd.Series(l).rolling(n).min().shift(1).values
    prev = np.r_[np.nan, c[:-1]]
    with np.errstate(invalid="ignore"):
        up = (c > hi) & (prev <= hi)
        dn = (c < lo) & (prev >= lo)
    k = p.get("atr_k", 3.0); a = f.atr.values
    return _finish(f, up, dn, c - k * a, c + k * a, "DONCHIAN", p)


def mr_bb(f, p):
    c = f.close.values
    mid, ub, lb = _bb(c, 20, p.get("k", 2.5))
    r14 = rsi(c, 14)
    cs = pd.Series(c)
    er = (cs.diff(24).abs() / cs.diff().abs().rolling(24).sum()).values
    with np.errstate(invalid="ignore"):
        rng = er < p.get("max_er", 0.3)
        up = rng & (c < lb) & (r14 < p.get("rsi_lo", 25))
        dn = rng & (c > ub) & (r14 > 100 - p.get("rsi_lo", 25))
    k = p.get("atr_k", 1.5); a = f.atr.values
    sl_up, sl_dn = c - k * a, c + k * a
    with np.errstate(invalid="ignore", divide="ignore"):
        tp = np.where(up, (mid - c) / (c - sl_up), (c - mid) / (sl_dn - c))
    return _finish(f, up, dn, sl_up, sl_dn, "MR_BB", p, tp_r=tp)


def rsi2(f, p):
    c = f.close.values
    r2 = rsi(c, 2)
    e200 = ema(c, 200)
    with np.errstate(invalid="ignore"):
        up = (r2 < p.get("lo", 10)) & (c > e200)
        dn = (r2 > 100 - p.get("lo", 10)) & (c < e200)
    k = p.get("atr_k", 2.0); a = f.atr.values
    return _finish(f, up, dn, c - k * a, c + k * a, "RSI2", p)
