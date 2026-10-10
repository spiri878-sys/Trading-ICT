"""Wyckoff MULTI-TIMEFRAME model (independent definition, SPERIMENTALE).

Context (HTF): a trading range (TR) = high/low of the `range_h` hours that END `event_h` hours ago,
  height between `min_h` and `max_h` x ATR(H1) and sideways (net move over the range <= `max_trend` x height).
Event (trigger TF, M15): within the last `event_h` hours price traded below TR low by >= `pen` x ATR(H1)
  (SPRING) and is now back inside the range; optional effort filter: tick volume of the spring bar >= `min_tv`
  x its rolling median (selling climax / shakeout).
Confirmation: SOS = bullish break of trigger-TF structure (close through the last confirmed swing high) while
  price is still in the lower part of the TR (close <= TR low + `max_pos` x height).
Entry: 'sos' = market at the next bar; 'lps' = limit at the broken swing level (back-up to the edge of the creek).
Stop: below the spring low - `sl_buf` x ATR(trigger). Target: TR high (opposite side) -> per-signal tp_r;
  signals with reward/risk < `min_rr` are skipped. Distribution (UPTHRUST / SOW / LPSY) is the mirror.
All quantities use closed bars only."""
import numpy as np
import pandas as pd

from .ict import _frame


def wyckoff_mtf(f, p):
    tfm = int((f.index[1] - f.index[0]).total_seconds() // 60) if len(f) > 1 else 15
    tfm = 15 if tfm > 60 else tfm
    nb = lambda hours: max(1, int(hours * 60 // tfm))
    R, E = nb(p.get("range_h", 72)), nb(p.get("event_h", 6))
    h, l, c = f.high.values, f.low.values, f.close.values
    a, ah1 = f.atr.values, f.h1_atr.values
    hs, ls = pd.Series(h), pd.Series(l)
    tr_hi = hs.shift(E).rolling(R, min_periods=R).max().values
    tr_lo = ls.shift(E).rolling(R, min_periods=R).min().values
    c_start = pd.Series(c).shift(E + R - 1).values
    c_end = pd.Series(c).shift(E).values
    height = tr_hi - tr_lo
    with np.errstate(invalid="ignore", divide="ignore"):
        ok_tr = (height >= p.get("min_h", 3.0) * ah1) & (height <= p.get("max_h", 15.0) * ah1) & \
                (np.abs(c_end - c_start) <= p.get("max_trend", 0.5) * height)
        ev_lo = ls.rolling(E, min_periods=E).min().values
        ev_hi = hs.rolling(E, min_periods=E).max().values
        pen = p.get("pen", 0.1) * ah1
        spring = ok_tr & (ev_lo <= tr_lo - pen) & (c > tr_lo)
        upthr = ok_tr & (ev_hi >= tr_hi + pen) & (c < tr_hi)
        mtv = p.get("min_tv", 0.0)
        if mtv > 0:
            tvmax = pd.Series(f.tv_rel.values).rolling(E, min_periods=1).max().values
            spring &= tvmax >= mtv; upthr &= tvmax >= mtv
        pos = (c - tr_lo) / height
        mp = p.get("max_pos", 0.5)
        up = spring & (f.brk.values == 1) & (pos <= mp)
        dn = upthr & (f.brk.values == -1) & (pos >= 1 - mp) & ~up
    if p.get("long_only"):
        dn &= False
    buf = p.get("sl_buf", 0.3) * a
    side = np.where(up, 1, -1)
    entry_mode = p.get("entry", "sos")
    if entry_mode == "lps":
        price = np.where(up, f.swing_hi.shift(1).values if hasattr(f.swing_hi, "shift") else f.swing_hi.values,
                         f.swing_lo.shift(1).values)
        price = np.where(up, np.minimum(price, c), np.maximum(price, c))
    else:
        price = c
    sl = np.where(up, ev_lo - buf, ev_hi + buf)
    target = np.where(up, tr_hi, tr_lo)
    with np.errstate(invalid="ignore", divide="ignore"):
        risk = (price - sl) * side
        rr = (target - price) * side / risk
        valid = (up | dn) & (risk > p.get("min_r_atr", 0.5) * a) & (risk <= p.get("max_r_atr", 40.0) * a) & \
                (rr >= p.get("min_rr", 1.5))
    out = _frame(f, valid, side, price, sl, "WYCKOFF_MTF", p.get("expiry", 8),
                 otype="market" if entry_mode == "sos" else "limit")
    idx = out.bar_i.values
    out["tp_r"] = np.minimum(rr[idx] * p.get("tp_frac", 0.9), p.get("tp_cap", 6.0)) if p.get("tp_mode", "range") == "range" else 0.0
    return out
