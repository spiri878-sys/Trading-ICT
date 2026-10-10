"""Wyckoff benchmark: Spring / Upthrust of a trading range (reproducible, independent definition).

Range at bar i = high/low of the previous `range_bars` bars (bar i excluded) with height between
`min_height_atr` and `max_height_atr` times the H1 ATR. Spring: bar i trades below the range low by
>= `min_pen_atr` * ATR(M5), closes back inside the range and in the upper half of its own bar.
Entry: market at the next bar open. Stop: spring low - buffer. Upthrust: mirror.
"""
import numpy as np
import pandas as pd

from .ict import _frame


def wyckoff_spring(f, p):
    n = p.get("range_bars", 48)
    a = f.atr.values
    h, l, c = f.high.values, f.low.values, f.close.values
    rh = pd.Series(h).rolling(n).max().shift(1).values
    rl = pd.Series(l).rolling(n).min().shift(1).values
    height = rh - rl
    ah1 = f.h1_atr.values
    with np.errstate(invalid="ignore"):
        ok = (height <= p.get("max_height_atr", 3.0) * ah1) & (height >= p.get("min_height_atr", 1.0) * ah1)
        pen = p.get("min_pen_atr", 0.2) * a
        mid = (h + l) / 2
        spring = ok & (l <= rl - pen) & (c > rl) & (c >= mid)
        upthr = ok & (h >= rh + pen) & (c < rh) & (c <= mid) & ~spring
    if p.get("sessions"):
        m = np.zeros(len(f), bool)
        for x, y in p["sessions"]:
            m |= (f.ny_min.values >= x) & (f.ny_min.values < y)
        spring &= m; upthr &= m
    buf = p.get("sl_buf_atr", 0.2) * a
    side = np.where(spring, 1, -1)
    sl = np.where(spring, l - buf, h + buf)
    risk = (c - sl) * side
    valid = (spring | upthr) & (risk >= p.get("min_r_atr", 0.5) * a) & (risk <= p.get("max_r_atr", 15.0) * a)
    return _frame(f, valid, side, c, sl, "WYCKOFF", 1, otype="market")
