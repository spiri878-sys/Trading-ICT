"""ICT/SMC cells - INDEPENDENT RECONSTRUCTION.

Only the cell NAMES (PPK, OTEOF, PO3, UNIOF, LS) and the vendor's one-line description of the
main engine ("recognises structure, waits for the decisive move, enters only on the confirmed
retracement") are documented. The rules below are our own definitions of the standard ICT concepts
those names refer to; see docs/evidence_register.md (E-20..E-24) for the classification.

PPK    break of a confirmed swing with displacement leaving an FVG; limit in the FVG (retracement);
       stop beyond the origin of the displacement leg.
OTEOF  same trigger; limit at the Optimal Trade Entry (default 70.5% retracement of the leg).
PO3    Power of Three: Asia range = accumulation, London/NY raid of one side (Judas swing) =
       manipulation, MSS back inside = distribution; limit in the MSS FVG, stop beyond the raid.
UNIOF  Unicorn: MSS whose FVG overlaps the breaker candle of the broken swing; limit at overlap edge.
LS     liquidity sweep (turtle soup): first daily raid of PDH/PDL/Asia level that closes back
       inside; limit at the swept level, stop beyond the raid extreme.
"""
import numpy as np
import pandas as pd


def _frame(f, mask, side, price, sl, strategy, expiry, otype="limit"):
    idx = np.flatnonzero(mask)
    return pd.DataFrame({
        "bar_i": idx, "bar_time": f.index[idx], "side": np.asarray(side)[idx].astype(int),
        "otype": otype, "price": np.asarray(price)[idx], "sl_struct": np.asarray(sl)[idx],
        "atr": f.atr.values[idx], "expiry_bars": expiry, "strategy": strategy})


def _window(f, windows):
    m = np.zeros(len(f), bool)
    for a, b in windows:
        m |= (f.ny_min.values >= a) & (f.ny_min.values < b)
    return m


def _fvg_at_break(f, min_fvg):
    """Most recent FVG (bar i, else i-1) in the break direction."""
    a = f.atr.values
    bt, bb, st, sb = (f[k].values for k in ("fvg_bull_top", "fvg_bull_bot", "fvg_bear_top", "fvg_bear_bot"))
    bt1, bb1, st1, sb1 = (np.r_[np.nan, x[:-1]] for x in (bt, bb, st, sb))
    btop = np.where(np.isfinite(bt), bt, bt1); bbot = np.where(np.isfinite(bt), bb, bb1)
    stop_ = np.where(np.isfinite(st), st, st1); sbot = np.where(np.isfinite(st), sb, sb1)
    ok_up = np.isfinite(btop) & ((btop - bbot) >= min_fvg * a)
    ok_dn = np.isfinite(stop_) & ((stop_ - sbot) >= min_fvg * a)
    return ok_up, ok_dn, btop, bbot, stop_, sbot


def _risk_ok(f, side, price, sl, p):
    a = f.atr.values
    r = (price - sl) * side
    with np.errstate(invalid="ignore"):
        return (r >= p.get("min_r_atr", 0.5) * a) & (r <= p.get("max_r_atr", 15.0) * a)


def _sessions(f, p, up, dn):
    if p.get("sessions"):
        s = _window(f, p["sessions"]); up &= s; dn &= s
    return up, dn


def ppk(f, p):
    a = f.atr.values
    disp = f.disp_body.values >= p.get("min_disp", 1.2) * a
    ok_up, ok_dn, btop, bbot, stop_, sbot = _fvg_at_break(f, p.get("min_fvg", 0.15))
    up = (f.brk.values == 1) & disp & ok_up
    dn = (f.brk.values == -1) & disp & ok_dn
    up, dn = _sessions(f, p, up, dn)
    d = p.get("entry_depth", 0.0)
    buf = p.get("sl_buf_atr", 0.2) * a
    side = np.where(up, 1, -1)
    price = np.where(up, btop - d * (btop - bbot), sbot + d * (stop_ - sbot))
    sl = np.where(up, f.leg_lo.values - buf, f.leg_hi.values + buf)
    m = (up | dn) & _risk_ok(f, side, price, sl, p)
    return _frame(f, m, side, price, sl, "PPK", p.get("expiry", 12))


def mss(f, p):
    """Market Structure Shift (one of the six strategies named on the vendor site): a break AGAINST the
    previous break direction (CHoCH) with displacement and FVG; limit at the FVG; stop beyond the leg."""
    a = f.atr.values
    disp = f.disp_body.values >= p.get("min_disp", 1.2) * a
    ok_up, ok_dn, btop, bbot, stop_, sbot = _fvg_at_break(f, p.get("min_fvg", 0.15))
    up = (f.brk.values == 1) & f.is_mss.values & disp & ok_up
    dn = (f.brk.values == -1) & f.is_mss.values & disp & ok_dn
    up, dn = _sessions(f, p, up, dn)
    buf = p.get("sl_buf_atr", 0.2) * a
    side = np.where(up, 1, -1)
    price = np.where(up, btop, sbot)
    sl = np.where(up, f.leg_lo.values - buf, f.leg_hi.values + buf)
    m = (up | dn) & _risk_ok(f, side, price, sl, p)
    return _frame(f, m, side, price, sl, "MSS", p.get("expiry", 12))


def mtf_m1(f, p):
    """EXPERIMENTAL multi-timeframe model (not documented by the vendor): H4 and H1 bias (close vs EMA50 of
    the last CLOSED bars) agree; on the execution timeframe (M1) a liquidity raid of the last 30-bar range is
    followed by an MSS with displacement + FVG in the bias direction; limit at the FVG, stop beyond the raid."""
    a = f.atr.values
    w = p.get("raid_window", 30)
    bias_up = (f.h1_close.values > f.h1_ema.values) & (f.h4_close.values > f.h4_ema.values)
    bias_dn = (f.h1_close.values < f.h1_ema.values) & (f.h4_close.values < f.h4_ema.values)
    lo_w = pd.Series(f.low.values).rolling(w, min_periods=w).min().values
    hi_w = pd.Series(f.high.values).rolling(w, min_periods=w).max().values
    prev_lo = pd.Series(f.low.values).shift(w).rolling(3 * w, min_periods=w).min().values
    prev_hi = pd.Series(f.high.values).shift(w).rolling(3 * w, min_periods=w).max().values
    raid_lo = lo_w < prev_lo; raid_hi = hi_w > prev_hi
    disp = f.disp_body.values >= p.get("min_disp", 1.5) * a
    ok_up, ok_dn, btop, bbot, stop_, sbot = _fvg_at_break(f, p.get("min_fvg", 0.2))
    up = (f.brk.values == 1) & f.is_mss.values & disp & ok_up & raid_lo & bias_up
    dn = (f.brk.values == -1) & f.is_mss.values & disp & ok_dn & raid_hi & bias_dn
    up, dn = _sessions(f, p, up, dn)
    buf = p.get("sl_buf_atr", 0.3) * a
    side = np.where(up, 1, -1)
    price = np.where(up, btop, sbot)
    sl = np.where(up, lo_w - buf, hi_w + buf)
    m = (up | dn) & _risk_ok(f, side, price, sl, p)
    return _frame(f, m, side, price, sl, "MTF_M1", p.get("expiry", 15))


def oteof(f, p):
    a = f.atr.values
    disp = f.disp_body.values >= p.get("min_disp", 1.2) * a
    up = (f.brk.values == 1) & disp
    dn = (f.brk.values == -1) & disp
    up, dn = _sessions(f, p, up, dn)
    lo, hi = f.leg_lo.values, f.leg_hi.values
    lvl = p.get("ote_level", 0.705)
    buf = p.get("sl_buf_atr", 0.2) * a
    side = np.where(up, 1, -1)
    price = np.where(up, hi - lvl * (hi - lo), lo + lvl * (hi - lo))
    sl = np.where(up, lo - buf, hi + buf)
    m = (up | dn) & _risk_ok(f, side, price, sl, p)
    return _frame(f, m, side, price, sl, "OTEOF", p.get("expiry", 24))


def po3(f, p):
    a = f.atr.values
    win = p.get("raid_window", 24)
    raid_hi = pd.Series(f.sweep_asia_hi.values.astype(float)).rolling(win, min_periods=1).max().values > 0
    raid_lo = pd.Series(f.sweep_asia_lo.values.astype(float)).rolling(win, min_periods=1).max().values > 0
    ok_up, ok_dn, btop, bbot, stop_, sbot = _fvg_at_break(f, p.get("min_fvg", 0.1))
    disp = f.disp_body.values >= p.get("min_disp", 1.0) * a
    # distribution against the raid: raid of Asia LOW then bullish MSS (and vice-versa)
    up = (f.brk.values == 1) & f.is_mss.values & raid_lo & ok_up & disp
    dn = (f.brk.values == -1) & f.is_mss.values & raid_hi & ok_dn & disp
    s = _window(f, p.get("sessions", [(120, 660)]))  # NY 02:00-11:00 (London + NY AM)
    up &= s; dn &= s
    ext_lo = pd.Series(f.low.values).rolling(win, min_periods=1).min().values
    ext_hi = pd.Series(f.high.values).rolling(win, min_periods=1).max().values
    buf = p.get("sl_buf_atr", 0.2) * a
    side = np.where(up, 1, -1)
    price = np.where(up, btop, sbot)
    sl = np.where(up, ext_lo - buf, ext_hi + buf)
    m = (up | dn) & _risk_ok(f, side, price, sl, p)
    return _frame(f, m, side, price, sl, "PO3", p.get("expiry", 12))


def uniof(f, p):
    a = f.atr.values
    ok_up, ok_dn, btop, bbot, stop_, sbot = _fvg_at_break(f, p.get("min_fvg", 0.1))
    zlo, zhi = f.brk_zlo.values, f.brk_zhi.values
    ov_up_hi = np.minimum(btop, zhi); ov_up_lo = np.maximum(bbot, zlo)
    ov_dn_hi = np.minimum(stop_, zhi); ov_dn_lo = np.maximum(sbot, zlo)
    with np.errstate(invalid="ignore"):
        up = (f.brk.values == 1) & f.is_mss.values & ok_up & (ov_up_hi > ov_up_lo)
        dn = (f.brk.values == -1) & f.is_mss.values & ok_dn & (ov_dn_hi > ov_dn_lo)
    up, dn = _sessions(f, p, up, dn)
    buf = p.get("sl_buf_atr", 0.2) * a
    side = np.where(up, 1, -1)
    price = np.where(up, ov_up_hi, ov_dn_lo)
    sl = np.where(up, f.leg_lo.values - buf, f.leg_hi.values + buf)
    m = (up | dn) & _risk_ok(f, side, price, sl, p)
    return _frame(f, m, side, price, sl, "UNIOF", p.get("expiry", 12))


def ls(f, p):
    a = f.atr.values
    c, h, l = f.close.values, f.high.values, f.low.values
    pdh, pdl, ah, al = f.pdh.values, f.pdl.values, f.asia_hi.values, f.asia_lo.values
    with np.errstate(invalid="ignore"):
        lvl_hi = np.where(f.sweep_hi.values & (h > pdh) & (c < pdh), pdh, np.where(f.sweep_hi.values & (c < ah), ah, np.nan))
        lvl_lo = np.where(f.sweep_lo.values & (l < pdl) & (c > pdl), pdl, np.where(f.sweep_lo.values & (c > al), al, np.nan))
    dn = np.isfinite(lvl_hi)
    up = np.isfinite(lvl_lo) & ~dn
    up, dn = _sessions(f, p, up, dn)
    buf = p.get("sl_buf_atr", 0.2) * a
    side = np.where(up, 1, -1)
    # limit at the midpoint between the swept level and the close (retest of the level)
    price = np.where(up, (lvl_lo + c) / 2, (lvl_hi + c) / 2)
    sl = np.where(up, l - buf, h + buf)
    m = (up | dn) & _risk_ok(f, side, price, sl, p)
    return _frame(f, m, side, price, sl, "LS", p.get("expiry", 6))


def silver_bullet(f, p):
    a = f.atr.values
    s = _window(f, p.get("windows", [(180, 240), (600, 660), (840, 900)]))
    mf = p.get("min_fvg", 0.25)
    bt, bb, st, sb = (f[k].values for k in ("fvg_bull_top", "fvg_bull_bot", "fvg_bear_top", "fvg_bear_bot"))
    with np.errstate(invalid="ignore"):
        up = s & ((bt - bb) >= mf * a)
        dn = s & ((st - sb) >= mf * a) & ~up
    l2 = np.r_[np.nan, np.nan, f.low.values[:-2]]; h2 = np.r_[np.nan, np.nan, f.high.values[:-2]]
    buf = p.get("sl_buf_atr", 0.2) * a
    side = np.where(up, 1, -1)
    price = np.where(up, bt, sb)
    sl = np.where(up, l2 - buf, h2 + buf)
    m = (up | dn) & _risk_ok(f, side, price, sl, p)
    return _frame(f, m, side, price, sl, "SILVER_BULLET", p.get("expiry", 6))
