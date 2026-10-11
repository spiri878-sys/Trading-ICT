"""Simulate a follower of a Telegram XAUUSD signal channel on M1 bid bars.

One signal = several equal or weighted "legs" opened at the same price; each leg has its own target (TP index,
or -1 = runner with no TP). All legs share the stop: initial SL from the signal, moved to break-even (or to an
earlier TP) when a given TP is reached, as the channel instructs ("ad ogni TP chiudo qualche profitto e SL a BE").

Conservative conventions:
* buy entries pay ASK = bid + spread (+ slippage for market orders); buy exits at BID; sells symmetric;
* inside a bar the stop is checked before the targets;
* a stop moved because of a TP hit becomes active from the next bar;
* a stop gapped through fills at the bar open; a forced time exit fills at the bar close (bid/ask).
"""
import numpy as np
from numba import njit


@njit(cache=True)
def sim_signal(o, h, l, c, i0, n_max, side, entry, sl, tps, leg_tp, leg_w, be_k, be_off, step, spread, slip):
    """Return (pnl_per_unit_price, n_tp_hit, exit_bar, mae, any_sl_full_loss).

    tps: target prices (len K). leg_tp[j]: index into tps (or -1 runner). leg_w[j]: weight (sum 1).
    be_k: after TP index be_k (0-based) is hit, stop -> entry + be_off*side; -1 = never.
    step: if True, after TP k (k>=1) is hit, stop -> tps[k-1].
    """
    nl = leg_tp.size
    open_ = np.ones(nl, np.bool_)
    pnl = 0.0
    cur_sl = sl
    pend_sl = sl
    k_hit = -1
    last = min(i0 + n_max, o.size - 1)
    mae = 0.0
    for i in range(i0, last + 1):
        cur_sl = pend_sl
        # exit side prices: buy closes on bid; sell closes on ask
        if side == 1:
            lo = l[i]; hi = h[i]; op = o[i]
        else:
            lo = l[i] + spread; hi = h[i] + spread; op = o[i] + spread
        adverse = (entry - lo) if side == 1 else (hi - entry)
        if adverse > mae:
            mae = adverse
        # stop first
        hit_sl = (lo <= cur_sl) if side == 1 else (hi >= cur_sl)
        if hit_sl:
            gap = (op <= cur_sl) if side == 1 else (op >= cur_sl)
            px = op if gap else cur_sl
            px = px - slip * side
            for j in range(nl):
                if open_[j]:
                    pnl += leg_w[j] * (px - entry) * side
                    open_[j] = False
            return pnl, k_hit + 1, i, mae, cur_sl == sl
        # targets in order
        for k in range(k_hit + 1, tps.size):
            reached = (hi >= tps[k]) if side == 1 else (lo <= tps[k])
            if not reached:
                break
            k_hit = k
            for j in range(nl):
                if open_[j] and leg_tp[j] == k:
                    pnl += leg_w[j] * (tps[k] - entry) * side
                    open_[j] = False
            if be_k >= 0 and k >= be_k:
                nb = entry + be_off * side
                if (nb - pend_sl) * side > 0:
                    pend_sl = nb
            if step and k >= 1:
                ns = tps[k - 1]
                if (ns - pend_sl) * side > 0:
                    pend_sl = ns
        any_open = False
        for j in range(nl):
            if open_[j]:
                any_open = True
        if not any_open:
            return pnl, k_hit + 1, i, mae, False
    # time exit at close of last bar
    px = c[last] if side == 1 else c[last] + spread
    px = px - slip * side
    for j in range(nl):
        if open_[j]:
            pnl += leg_w[j] * (px - entry) * side
    return pnl, k_hit + 1, last, mae, False


@njit(cache=True)
def limit_fill(o, h, l, i0, i1, side, price, spread):
    """First bar in [i0, i1] where a buy limit (ASK <= price) / sell limit (BID >= price) fills; fill price."""
    for i in range(i0, min(i1, o.size - 1) + 1):
        if side == 1:
            if o[i] + spread <= price:
                return i, o[i] + spread
            if l[i] + spread <= price:
                return i, price
        else:
            if o[i] >= price:
                return i, o[i]
            if h[i] >= price:
                return i, price
    return -1, 0.0
