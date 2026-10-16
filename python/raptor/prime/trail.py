"""Gestione 'TP/SL dinamici' (Fase 11): parziali e pareggio come FOTO, residuo con trailing ATR su timeframe alto.

Per ogni segnale riempito (fill_i, fill_px): stop iniziale = entry - side * sl_mult * ATR_htf (noto all'ingresso);
p1_frac a +p1_r R con stop a pareggio; p2_frac a +p2_r R; il residuo esce sul trailing
SL <- max(SL, close_M1 - side * trail_mult * ATR_htf) (decisione sulla chiusura M1, mai allargato) o a max_hold.
Costi come label.py: spread (ASK = BID + spread), slippage avverso su stop, commissione, swap per notte.
"""
import numpy as np
import pandas as pd
from numba import njit


@njit(cache=True)
def sim_trail(o, h, l, c, sp, day, atr, fill_i, fill_px, side, sl_mult, trail_mult, p1_r, p1_frac, p2_r, p2_frac,
              max_hold, slip, comm_px, sw_l, sw_s, be_on):
    n = o.size
    k = fill_i.size
    r = np.full(k, np.nan)
    exit_i = np.full(k, -1)
    risk = np.full(k, np.nan)
    for j in range(k):
        fi = fill_i[j]
        if fi < 0:
            continue
        sd = side[j]
        a = atr[fi]
        if not (a > 0):
            continue
        e = fill_px[j]
        rd = sl_mult * a
        sl = e - sd * rd
        rem = 1.0
        pnl = 0.0
        p1 = False
        p2 = False
        ei = -1
        for i in range(fi, min(n, fi + max_hold)):
            spi = sp[i]
            if sd == 1:
                adv = l[i]; fav = h[i]; cls = c[i]; op = o[i]
            else:
                adv = h[i] + spi; fav = l[i] + spi; cls = c[i] + spi; op = o[i] + spi
            if (op - sl) * sd <= 0 and i > fi:
                pnl += rem * (op - sd * slip - e) * sd
                ei = i
                break
            if (adv - sl) * sd <= 0:
                pnl += rem * (sl - sd * slip - e) * sd
                ei = i
                break
            if i == fi:
                continue
            # partial levels on the close (as FOTO: decided on closed M1 bar)
            fr = (cls - e) * sd / rd
            if (not p1) and (p1_frac > 0 or be_on) and fr >= p1_r:
                pnl += p1_frac * (cls - e) * sd
                rem -= p1_frac
                p1 = True
                if be_on and (sl - e) * sd < 0:
                    sl = e
            if (not p2) and p2_frac > 0 and fr >= p2_r:
                pnl += p2_frac * (cls - e) * sd
                rem -= p2_frac
                p2 = True
            ts = cls - sd * trail_mult * atr[i]
            if (ts - sl) * sd > 0:
                sl = ts
        if ei < 0:
            ei = min(n, fi + max_hold) - 1
            px = c[ei] if sd == 1 else c[ei] + sp[ei]
            pnl += rem * (px - e) * sd
        nights = day[ei] - day[fi]
        pnl += (sw_l if sd == 1 else sw_s) * e * nights / 365.0
        r[j] = (pnl - 2 * comm_px) / (rd + slip + 2 * comm_px)
        exit_i[j] = ei
        risk[j] = rd
    return r, exit_i, risk


def atr_on_m1(m1_index, htf: pd.DataFrame, n=14):
    """ATR di Wilder del TF alto, visibile su M1 dalla chiusura della barra HTF (nessun lookahead)."""
    h, l, c = htf.high.values, htf.low.values, htf.close.values
    pc = np.concatenate([[c[0]], c[:-1]])
    tr = np.maximum(h - l, np.maximum(np.abs(h - pc), np.abs(l - pc)))
    a = pd.Series(tr).ewm(alpha=1 / n, adjust=False).mean().values
    dur = htf.index[1:] - htf.index[:-1]
    step = pd.Series(dur).mode().iloc[0]
    avail = (htf.index + step).values
    dec = (m1_index + pd.Timedelta("1min")).values
    j = np.searchsorted(avail, dec, side="right") - 1
    return np.where(j >= 0, a[np.maximum(j, 0)], np.nan)
