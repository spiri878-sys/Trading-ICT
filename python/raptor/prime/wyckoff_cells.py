"""Celle WYCKOFF per la stessa architettura PRIME (Fase 12): stesso formato di segnali di cells.py, così feature,
etichette, AI autoallenata, Market Brain e gestione restano identici. Definizioni indipendenti, solo barre chiuse.

* WSPR  Spring / Upthrust di un range locale (M15): il minimo della barra rompe il minimo del range di
        `range_bars` barre (altezza 1-4 ATR H1) e la barra CHIUDE di nuovo dentro, nella metà alta; ingresso a
        mercato; stop oltre l'estremo dello spring.
* WSOS  Range multi-timeframe (M15, range 72 h che finisce `event_h` ore prima, laterale), spring nelle ultime
        `event_h` ore, poi SOS = rottura rialzista della struttura M15 nella parte bassa del range; a mercato.
* WLPS  Come WSOS ma ingresso al LPS: limite sul livello di swing appena rotto (back-up to the edge of the creek).
* WH1   Come WSOS su H1 (range 120 h): eventi più rari e più ampi.
Distribuzione (Upthrust / SOW / LPSY) = specchio.
"""
import numpy as np
import pandas as pd

from .cells import _out, _risk_ok


def wspr(f, p):
    n = p["range_bars"]
    a, ah1 = f.atr.values, f.h1_atr.values
    h, l, c = f.high.values, f.low.values, f.close.values
    rh = pd.Series(h).rolling(n).max().shift(1).values
    rl = pd.Series(l).rolling(n).min().shift(1).values
    height = rh - rl
    with np.errstate(invalid="ignore"):
        ok = (height >= p["min_h"] * ah1) & (height <= p["max_h"] * ah1)
        pen = p["pen"] * a
        mid = (h + l) / 2
        up = ok & (l <= rl - pen) & (c > rl) & (c >= mid)
        dn = ok & (h >= rh + pen) & (c < rh) & (c <= mid) & ~up
    side = np.where(up, 1, -1)
    buf = p["sl_buf_atr"] * a
    sl = np.where(up, l - buf, h + buf)
    m = (up | dn) & _risk_ok(f, side, c, sl, p)
    return _out(f, "WSPR", m, side, c, sl, 1, otype="market", leg_lo=rl, leg_hi=rh, zlo=rl, zhi=rh,
                reason="spring/upthrust")


def _wmtf(f, p, cell, lps=False):
    tfm = max(1, int(pd.Timedelta(f.attrs.get("tf", "15min")).total_seconds() // 60))
    R = max(1, int(p["range_h"] * 60 // tfm))
    E = max(1, int(p["event_h"] * 60 // tfm))
    h, l, c = f.high.values, f.low.values, f.close.values
    a, ah1 = f.atr.values, f.h1_atr.values
    hs, ls_ = pd.Series(h), pd.Series(l)
    tr_hi = hs.shift(E).rolling(R, min_periods=R).max().values
    tr_lo = ls_.shift(E).rolling(R, min_periods=R).min().values
    c0 = pd.Series(c).shift(E + R - 1).values
    c1 = pd.Series(c).shift(E).values
    height = tr_hi - tr_lo
    with np.errstate(invalid="ignore", divide="ignore"):
        ok = (height >= p["min_h"] * ah1) & (height <= p["max_h"] * ah1) & (np.abs(c1 - c0) <= p["max_trend"] * height)
        ev_lo = ls_.rolling(E, min_periods=E).min().values
        ev_hi = hs.rolling(E, min_periods=E).max().values
        pen = p["pen"] * ah1
        spring = ok & (ev_lo <= tr_lo - pen) & (c > tr_lo)
        upthr = ok & (ev_hi >= tr_hi + pen) & (c < tr_hi)
        pos = (c - tr_lo) / height
        up = spring & (f.brk.values == 1) & (pos <= p["max_pos"])
        dn = upthr & (f.brk.values == -1) & (pos >= 1 - p["max_pos"]) & ~up
    side = np.where(up, 1, -1)
    buf = p["sl_buf_atr"] * a
    sl = np.where(up, ev_lo - buf, ev_hi + buf)
    if lps:
        psh = np.r_[np.nan, f.swing_hi.values[:-1]]
        psl = np.r_[np.nan, f.swing_lo.values[:-1]]
        price = np.where(up, np.minimum(psh, c), np.maximum(psl, c))
        otype = "limit"
    else:
        price, otype = c, "market"
    m = (up | dn) & np.isfinite(price) & _risk_ok(f, side, price, sl, p)
    return _out(f, cell, m, side, price, sl, p["expiry"], otype=otype, leg_lo=tr_lo, leg_hi=tr_hi, zlo=tr_lo,
                zhi=tr_hi, reason="spring+SOS" if not lps else "spring+SOS+LPS")


def wsos(f, p):
    return _wmtf(f, p, "WSOS")


def wlps(f, p):
    return _wmtf(f, p, "WLPS", lps=True)


def wh1(f, p):
    return _wmtf(f, p, "WH1")


WY_CELLS = {"WSPR": wspr, "WSOS": wsos, "WLPS": wlps, "WH1": wh1}
WY_TF = {"WSPR": "15min", "WSOS": "15min", "WLPS": "15min", "WH1": "1h"}
WY_DEFAULTS = {
    "WSPR": dict(k=3, range_bars=48, min_h=1.0, max_h=4.0, pen=0.2, sl_buf_atr=0.2, min_r_atr=0.5, max_r_atr=15.0),
    "WSOS": dict(k=3, range_h=72, event_h=6, min_h=3.0, max_h=15.0, max_trend=0.5, pen=0.1, max_pos=0.5,
                 sl_buf_atr=0.3, expiry=1, min_r_atr=0.5, max_r_atr=40.0),
    "WLPS": dict(k=3, range_h=72, event_h=6, min_h=3.0, max_h=15.0, max_trend=0.5, pen=0.1, max_pos=0.5,
                 sl_buf_atr=0.3, expiry=16, min_r_atr=0.5, max_r_atr=40.0),
    "WH1": dict(k=3, range_h=120, event_h=12, min_h=3.0, max_h=20.0, max_trend=0.5, pen=0.1, max_pos=0.5,
                sl_buf_atr=0.3, expiry=1, min_r_atr=0.3, max_r_atr=20.0),
}


def register():
    """Aggiunge le celle Wyckoff al generatore PRIME (cells.generate)."""
    from . import cells as C
    C.ALL_CELLS.update(WY_CELLS)
    C.TF_OF.update(WY_TF)
    C.DEFAULTS.update(WY_DEFAULTS)
