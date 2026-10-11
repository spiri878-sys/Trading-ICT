"""TRAILING OCO entries (user idea v2): when flat, a BUY STOP follows price DOWN staying `d` above the lowest
low since it was armed, and a SELL STOP follows price UP staying `d` below the highest high. The first that
triggers cancels the other; one trade at a time; both are re-armed from the exit bar after the trade closes.
d = k x ATR14(H1) of the last closed H1 bar (known at that time). Optional regime filter (bull: buy side only,
bear: sell side only, mixed: none).

Intrabar order on M1 OHLC is unknown, so per bar the trigger is tested against the level BEFORE this bar's new
extreme updates it (the order cannot follow a low that happens after the high); if both sides trigger in the
same bar, the worse outcome is booked."""
import numpy as np
import pandas as pd
from numba import njit

from .engine import _manage, Market


@njit(cache=True)
def _run(o, h, l, c, sp, day, dow, mod, d_arr, atr_arr, reg, use_reg, sw_l, sw_s, init_bal, lot_mode, fixed_lot,
         risk_pct, sl_k, tp_r, trail_k, max_hold, fri_close, slip, comm, contract, leverage, min_lot, lot_step, start_i):
    n = o.size
    T = 200000
    t_fi = np.zeros(T, np.int64); t_ei = np.zeros(T, np.int64); t_side = np.zeros(T, np.int8); t_lot = np.zeros(T)
    t_entry = np.zeros(T); t_sl = np.zeros(T); t_net = np.zeros(T); t_bal = np.zeros(T); t_low = np.zeros(T)
    t_rs = np.zeros(T, np.int8); t_tie = np.zeros(T, np.bool_)
    nt = 0; bal = init_bal; i = start_i; armed = False; lo_run = 0.0; hi_run = 0.0
    while i < n - 1 and nt < T:
        if dow[i] == 4 and mod[i] >= fri_close:
            armed = False; i += 1; continue
        d = d_arr[i]
        if not (d > 0):
            i += 1; continue
        if not armed:
            lo_run = l[i]; hi_run = h[i]; armed = True; i += 1; continue
        want_l = (not use_reg) or reg[i] == 1
        want_s = (not use_reg) or reg[i] == -1
        lvl_l = lo_run + d          # buy stop level (ask)
        lvl_s = hi_run - d          # sell stop level (bid)
        trig_l = want_l and (h[i] + sp[i] >= lvl_l)
        trig_s = want_s and (l[i] <= lvl_s)
        if trig_l or trig_s:
            best = 1e18; b_side = 0; b_ei = 0; b_fp = 0.0; b_sl = 0.0; b_lot = 0.0; b_rs = 0; b_low = 0.0
            for side in (1, -1):
                if side == 1 and not trig_l:
                    continue
                if side == -1 and not trig_s:
                    continue
                if side == 1:
                    fp = (o[i] + sp[i] + slip) if o[i] + sp[i] >= lvl_l else lvl_l + slip
                else:
                    fp = (o[i] - slip) if o[i] <= lvl_s else lvl_s - slip
                a = atr_arr[i]
                sl = fp - side * sl_k * a
                rd = sl_k * a
                if lot_mode == 0:
                    lot = fixed_lot
                else:
                    lot = np.floor(bal * risk_pct / 100.0 / ((rd + slip) * contract + 2 * comm) / lot_step + 1e-9) * lot_step
                    if lot < min_lot:
                        continue
                if lot * contract * fp / leverage > bal:
                    continue
                ei, pnl, rs, npart, mfe, mae = _manage(o, h, l, c, sp, dow, mod, i, side, fp, sl, rd, a, tp_r, 0.0, 0.0,
                                                       0.0, 0.0, False, True, trail_k / sl_k * sl_k, max_hold, fri_close, slip)
                pnl += (sw_l if side == 1 else sw_s) * fp * (day[ei] - day[i]) / 365.0
                net = pnl * lot * contract - 2 * comm * lot
                if net < best:
                    best = net; b_side = side; b_ei = ei; b_fp = fp; b_sl = sl; b_lot = lot; b_rs = rs
                    b_low = bal + mae * rd * lot * contract
            if b_side != 0:
                t_fi[nt] = i; t_ei[nt] = b_ei; t_side[nt] = b_side; t_lot[nt] = b_lot; t_entry[nt] = b_fp; t_sl[nt] = b_sl
                t_net[nt] = best; bal += best; t_bal[nt] = bal; t_low[nt] = b_low; t_rs[nt] = b_rs
                t_tie[nt] = trig_l and trig_s
                nt += 1
                armed = False
                i = b_ei + 1
                if bal <= 0:
                    break
                continue
        # no trigger: the orders follow the price (extremes updated AFTER the trigger test of this bar)
        if l[i] < lo_run:
            lo_run = l[i]
        if h[i] > hi_run:
            hi_run = h[i]
        i += 1
    return nt, t_fi, t_ei, t_side, t_lot, t_entry, t_sl, t_net, t_bal, t_low, t_rs, t_tie


EXIT = {1: "SL", 2: "TP", 3: "BE", 4: "TRAIL", 5: "TIME", 6: "FRIDAY", 7: "END"}


def h1_context_on_m1(mk: Market, f1h: pd.DataFrame):
    """ATR14(H1) and regime of the last CLOSED H1 bar, forward-filled onto M1 bars (available at H1 close)."""
    avail = f1h.index + pd.Timedelta(hours=1)
    reg = np.where((f1h.d1_close > f1h.d1_ema) & (f1h.h4_trend > 0), 1, np.where((f1h.d1_close < f1h.d1_ema) & (f1h.h4_trend < 0), -1, 0))
    ctx = pd.DataFrame({"atr": f1h.atr.values, "reg": reg}, index=avail)
    pos = np.searchsorted(ctx.index.values, mk.index.values, side="right") - 1
    ok = pos >= 0
    atr = np.where(ok, ctx.atr.values[np.clip(pos, 0, None)], np.nan)
    rg = np.where(ok, ctx.reg.values[np.clip(pos, 0, None)], 0).astype(np.int64)
    return atr, rg


def run(mk, spread, atr_h1, reg, *, k_dist=2.0, sl_k=1.5, tp_r=2.0, trail_k=2.0, use_regime=True, max_hold_min=1440,
        init_bal=1000.0, lot_mode=0, fixed_lot=0.10, risk_pct=1.0, start=None, end=None, fri_close=23 * 60, slip=0.05,
        comm=3.5, contract=100.0, leverage=100.0, swap_long=-0.066, swap_short=0.029):
    i0 = 0 if start is None else int(np.searchsorted(mk.index.values, np.datetime64(pd.Timestamp(start))))
    i1 = len(mk.o) if end is None else int(np.searchsorted(mk.index.values, np.datetime64(pd.Timestamp(end))))
    sl_ = slice(0, i1)
    r = _run(mk.o[sl_], mk.h[sl_], mk.l[sl_], mk.c[sl_], spread[sl_], mk.day[sl_], mk.dow[sl_], mk.mod[sl_],
             k_dist * atr_h1[sl_], atr_h1[sl_], reg[sl_], use_regime, swap_long, swap_short, init_bal, lot_mode, fixed_lot,
             risk_pct, sl_k, tp_r, trail_k, max_hold_min, fri_close, slip, comm, contract, leverage, 0.01, 0.01, i0)
    nt, fi, ei, side, lot, entry, sl, net, bal, low, rs, tie = r
    s = slice(0, nt)
    tr = pd.DataFrame({"entry_time": mk.index[fi[s]], "exit_time": mk.index[ei[s]], "side": side[s], "lot": lot[s],
                       "entry": entry[s], "sl0": sl[s], "net": net[s], "balance": bal[s], "equity_low": low[s],
                       "exit_reason": [EXIT[x] for x in rs[s]], "same_bar_tie": tie[s]})
    tr["risk_money"] = (tr.entry - tr.sl0).abs() * tr.lot * contract
    tr["r_mult"] = tr.net / tr.risk_money
    return tr
