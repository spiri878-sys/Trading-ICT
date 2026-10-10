"""Causal market-structure, liquidity, FVG and multi-timeframe context on the signal timeframe (M5).

Every column at row i uses only bars that are CLOSED when bar i closes. Higher-timeframe values are
joined with `merge_asof` on their availability time (HTF bar open + HTF length), never on open time.
"""
import numpy as np
import pandas as pd
from numba import njit

from .indicators import atr, ema, confirmed_swings
from . import timeutil
from . import data as D


@njit(cache=True)
def _structure(o, h, l, c, sh, shi, slv, sli):
    n = h.size
    brk = np.zeros(n, np.int8)          # +1 close through last swing high, -1 through last swing low
    is_mss = np.zeros(n, np.bool_)      # break against the previous break direction (MSS / CHoCH)
    leg_lo = np.full(n, np.nan); leg_hi = np.full(n, np.nan)
    brk_swing = np.full(n, -1)          # index of the swing that was broken
    last_dir = 0
    broken_h = -1; broken_l = -1
    for i in range(1, n):
        lvl_h, ih = sh[i - 1], shi[i - 1]
        lvl_l, il = slv[i - 1], sli[i - 1]
        if ih >= 0 and ih != broken_h and c[i] > lvl_h:
            brk[i] = 1; broken_h = ih; brk_swing[i] = ih
            st = il if (il >= 0 and il < i) else max(0, i - 24)
            lo = 1e18; hi = -1e18
            for j in range(st, i + 1):
                lo = min(lo, l[j]); hi = max(hi, h[j])
            leg_lo[i] = lo; leg_hi[i] = hi
            is_mss[i] = last_dir == -1
            last_dir = 1
        elif il >= 0 and il != broken_l and c[i] < lvl_l:
            brk[i] = -1; broken_l = il; brk_swing[i] = il
            st = ih if (ih >= 0 and ih < i) else max(0, i - 24)
            lo = 1e18; hi = -1e18
            for j in range(st, i + 1):
                lo = min(lo, l[j]); hi = max(hi, h[j])
            leg_lo[i] = lo; leg_hi[i] = hi
            is_mss[i] = last_dir == 1
            last_dir = -1
    return brk, is_mss, leg_lo, leg_hi, brk_swing


@njit(cache=True)
def _breaker_zone(o, h, l, c, brk, brk_swing, look):
    """Breaker candle at a break: for a bullish break, the last BULLISH candle at/just before the broken
    swing high (the failed supply); for a bearish break, the last BEARISH candle at the broken swing low."""
    n = h.size
    zlo = np.full(n, np.nan); zhi = np.full(n, np.nan)
    for i in range(n):
        if brk[i] == 0 or brk_swing[i] < 0:
            continue
        s = brk_swing[i]
        for j in range(s, max(-1, s - look), -1):
            if (brk[i] == 1 and c[j] > o[j]) or (brk[i] == -1 and c[j] < o[j]):
                zlo[i] = l[j]; zhi[i] = h[j]
                break
    return zlo, zhi


def _htf(m1: pd.DataFrame, rule: str, minutes: int, prefix: str, swing_k: int = 2) -> pd.DataFrame:
    b = D.resample(m1, rule)
    o, h, l, c = (b[k].values for k in ("open", "high", "low", "close"))
    a = atr(h, l, c, 14)
    e = ema(c, 50)
    # HTF structure: last confirmed swings and direction of the last break (both known at bar close)
    sh, shi, slv, sli = confirmed_swings(h, l, swing_k)
    brk = _structure(o, h, l, c, sh, shi, slv, sli)[0]
    trend = pd.Series(np.where(brk != 0, brk, np.nan)).ffill().fillna(0).values
    out = pd.DataFrame({f"{prefix}_atr": a, f"{prefix}_ema": e, f"{prefix}_close": c,
                        f"{prefix}_atr_rel": a / pd.Series(a).rolling(100, min_periods=20).mean().values,
                        f"{prefix}_swing_hi": sh, f"{prefix}_swing_lo": slv, f"{prefix}_trend": trend},
                       index=b.index + pd.Timedelta(minutes=minutes))
    out.index.name = "t"
    return out


def build_features(m1: pd.DataFrame, tf: str = "5min", swing_k: int = 3) -> pd.DataFrame:
    tfm = int(pd.Timedelta(tf).total_seconds() // 60)
    b = D.resample(m1, tf)
    o, h, l, c = (b[k].values for k in ("open", "high", "low", "close"))
    a = atr(h, l, c, 14)
    sh, shi, slv, sli = confirmed_swings(h, l, swing_k)
    brk, mss, leg_lo, leg_hi, brk_sw = _structure(o, h, l, c, sh, shi, slv, sli)
    zlo, zhi = _breaker_zone(o, h, l, c, brk, brk_sw, 6)
    f = pd.DataFrame(index=b.index)
    f["open"], f["high"], f["low"], f["close"] = o, h, l, c
    f["atr"] = a
    f["atr_rel"] = a / pd.Series(a).rolling(100, min_periods=20).mean().values
    f["ema50"] = ema(c, 50)
    f["body"] = np.abs(c - o)
    f["brk"], f["is_mss"], f["leg_lo"], f["leg_hi"] = brk, mss, leg_lo, leg_hi
    f["brk_zlo"], f["brk_zhi"] = zlo, zhi
    f["swing_hi"], f["swing_lo"] = sh, slv
    h2, l2 = np.roll(h, 2), np.roll(l, 2)
    h2[:2] = np.nan; l2[:2] = np.nan
    bull, bear = l > h2, h < l2
    f["fvg_bull_top"] = np.where(bull, l, np.nan); f["fvg_bull_bot"] = np.where(bull, h2, np.nan)
    f["fvg_bear_top"] = np.where(bear, l2, np.nan); f["fvg_bear_bot"] = np.where(bear, h, np.nan)
    f["disp_body"] = pd.Series(f["body"].values).rolling(3, min_periods=1).max().values
    # breaks in the last 48 bars (4h on M5)
    w4h = max(1, 240 // tfm)
    f["brk_up_48"] = pd.Series((brk == 1).astype(float)).rolling(w4h, min_periods=1).sum().values
    f["brk_dn_48"] = pd.Series((brk == -1).astype(float)).rolling(w4h, min_periods=1).sum().values
    # ranges 4h / 24h (positions computed per side in the feature step)
    nb = lambda minutes: max(1, minutes // tfm)
    for hrs in (4, 24):
        f[f"rng_hi_{hrs}h"] = pd.Series(h).rolling(nb(hrs * 60), min_periods=1).max().values
        f[f"rng_lo_{hrs}h"] = pd.Series(l).rolling(nb(hrs * 60), min_periods=1).min().values
    f["ret_60m"] = c - pd.Series(c).shift(nb(60)).values
    f["ret_3h"] = c - pd.Series(c).shift(nb(180)).values
    # ---- liquidity: previous server day H/L and Asian range (NY 20:00-00:00 = server 03:00-07:00)
    day = b.index.normalize()
    dh, dl = b.high.groupby(day).max(), b.low.groupby(day).min()
    f["pdh"] = dh.shift(1).reindex(day).values
    f["pdl"] = dl.shift(1).reindex(day).values
    hr = b.index.hour
    asia = (hr >= 3) & (hr < 7)
    after_asia = hr >= 7
    ah = b.high.where(asia).groupby(day).max(); al = b.low.where(asia).groupby(day).min()
    f["asia_hi"] = np.where(after_asia, ah.reindex(day).values, np.nan)
    f["asia_lo"] = np.where(after_asia, al.reindex(day).values, np.nan)
    first = ~pd.Series(day).duplicated().values
    run_hi = b.high.groupby(day).cummax().shift(1).values.copy(); run_hi[first] = -np.inf
    run_lo = b.low.groupby(day).cummin().shift(1).values.copy(); run_lo[first] = np.inf
    post_hi = b.high.where(after_asia).groupby(day).cummax().shift(1).values.copy()
    post_lo = b.low.where(after_asia).groupby(day).cummin().shift(1).values.copy()
    post_hi[first] = -np.inf; post_lo[first] = np.inf
    post_hi = np.where(np.isnan(post_hi), -np.inf, post_hi); post_lo = np.where(np.isnan(post_lo), np.inf, post_lo)
    pdh, pdl, ahv, alv = f.pdh.values, f.pdl.values, f.asia_hi.values, f.asia_lo.values
    with np.errstate(invalid="ignore"):
        f["sweep_hi"] = ((h > pdh) & (run_hi <= pdh)) | ((h > ahv) & (post_hi <= ahv))
        f["sweep_lo"] = ((l < pdl) & (run_lo >= pdl)) | ((l < alv) & (post_lo >= alv))
        f["sweep_asia_hi"] = (h > ahv) & (post_hi <= ahv)
        f["sweep_asia_lo"] = (l < alv) & (post_lo >= alv)
    f["day_hi"] = b.high.groupby(day).cummax().values
    f["day_lo"] = b.low.groupby(day).cummin().values
    # ---- higher timeframes, joined on availability time
    dec = pd.DataFrame({"t": b.index + pd.Timedelta(minutes=tfm)})
    for rule, mins, p in (("15min", 15, "m15"), ("1h", 60, "h1"), ("4h", 240, "h4"), ("1D", 1440, "d1")):
        ctx = _htf(m1, rule, mins, p).reset_index()
        m = pd.merge_asof(dec, ctx, on="t", direction="backward")
        for col in ctx.columns:
            if col != "t":
                f[col] = m[col].values
    f["ny_min"] = timeutil.ny_minutes_of_day(b.index)
    f["dow"] = b.index.dayofweek
    f["spread_px"] = b.spread.values * D.POINT_XAUUSD
    return f
