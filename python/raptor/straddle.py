"""OCO breakout straddle simulator: a BUY STOP above a range and a SELL STOP below it; the first one that
triggers cancels the other; one position at a time; after the position closes the next setup re-places the
pair (only if both levels are still on the correct side of the market). Management: initial stop, optional
TP in R, trailing stop that follows the price (k x ATR on closed M1 bars), max holding time.

Execution assumptions (conservative, M1 OHLC, bid chart):
* buy stop triggers when ASK (bid+spread) reaches the level; fill at level + slippage, or at the open + spread
  + slippage when the bar gaps through it; sell stop symmetric on BID.
* if BOTH orders trigger inside the same M1 bar the order of events is unknown: the simulator evaluates both
  outcomes and books the WORSE one.
* stop-loss / trailing / TP handled by engine._manage (stop has priority inside a bar).
"""
import numpy as np
import pandas as pd
from numba import njit

from .engine import _manage, Market


@njit(cache=True)
def _stop_fill(o, h, l, sp, dow, mod, i0, iexp, side, price, slip, fri_close):
    for i in range(i0, min(iexp + 1, o.size)):
        if dow[i] == 4 and mod[i] >= fri_close:
            return -1, 0.0
        if side == 1:
            if o[i] + sp[i] >= price:
                return i, o[i] + sp[i] + slip
            if h[i] + sp[i] >= price:
                return i, price + slip
        else:
            if o[i] <= price:
                return i, o[i] - slip
            if l[i] <= price:
                return i, price - slip
    return -1, 0.0


@njit(cache=True)
def _run(o, h, l, c, sp, day, dow, mod, sw_l, sw_s,
         s_avail, s_exp, p_hi, p_lo, sl_hi, sl_lo, s_atr,
         init_bal, lot_mode, fixed_lot, risk_pct, tp_r, trail_atr, max_hold, fri_close, slip, comm, contract,
         leverage, min_lot, lot_step, stop_out_level):
    ns = s_avail.size
    t_fi = np.zeros(ns, np.int64); t_ei = np.zeros(ns, np.int64); t_side = np.zeros(ns, np.int8)
    t_lot = np.zeros(ns); t_entry = np.zeros(ns); t_sl = np.zeros(ns); t_net = np.zeros(ns); t_bal = np.zeros(ns)
    t_mae = np.zeros(ns); t_reason = np.zeros(ns, np.int8); t_tie = np.zeros(ns, np.bool_)
    nt = 0; bal = init_bal; busy = -1; n_skip_margin = 0; dead = False
    for k in range(ns):
        if dead:
            break
        start = max(s_avail[k], busy + 1)
        if start > s_exp[k] or start >= o.size:
            continue
        # both levels must still be on the correct side of the market when (re)placed
        if o[start] + sp[start] >= p_hi[k] or o[start] <= p_lo[k]:
            continue
        fl, pl = _stop_fill(o, h, l, sp, dow, mod, start, s_exp[k], 1, p_hi[k], slip, fri_close)
        fs, ps = _stop_fill(o, h, l, sp, dow, mod, start, s_exp[k], -1, p_lo[k], slip, fri_close)
        if fl < 0 and fs < 0:
            continue
        cand = 0  # 1 long, -1 short, 2 tie
        if fl >= 0 and (fs < 0 or fl < fs):
            cand = 1
        elif fs >= 0 and (fl < 0 or fs < fl):
            cand = -1
        else:
            cand = 2
        best_net = 1e18; b_side = 0; b_fi = 0; b_ei = 0; b_entry = 0.0; b_sl = 0.0; b_lot = 0.0; b_rs = 0; b_mae = 0.0
        for side in (1, -1):
            if cand != 2 and side != cand:
                continue
            fi = fl if side == 1 else fs
            fp = pl if side == 1 else ps
            sl = sl_hi[k] if side == 1 else sl_lo[k]
            rd = (fp - sl) * side
            if not (rd > 0):
                continue
            if lot_mode == 0:
                lot = fixed_lot
            else:
                lot = np.floor(bal * risk_pct / 100.0 / ((rd + slip) * contract + 2 * comm) / lot_step + 1e-9) * lot_step
                if lot < min_lot:
                    continue
            if lot * contract * fp / leverage > bal:
                n_skip_margin += 1
                continue
            ei, pnl, rs, npart, mfe, mae = _manage(o, h, l, c, sp, dow, mod, fi, side, fp, sl, rd, s_atr[k], tp_r,
                                                   0.0, 0.0, 0.0, 0.0, False, True, trail_atr, max_hold, fri_close, slip)
            nights = day[ei] - day[fi]
            pnl += (sw_l if side == 1 else sw_s) * fp * nights / 365.0
            net = pnl * lot * contract - 2 * comm * lot
            if net < best_net:
                best_net = net; b_side = side; b_fi = fi; b_ei = ei; b_entry = fp; b_sl = sl; b_lot = lot; b_rs = rs
                b_mae = mae * rd * lot * contract
        if b_side == 0:
            continue
        t_fi[nt] = b_fi; t_ei[nt] = b_ei; t_side[nt] = b_side; t_lot[nt] = b_lot; t_entry[nt] = b_entry
        t_sl[nt] = b_sl; t_net[nt] = best_net; t_reason[nt] = b_rs; t_tie[nt] = cand == 2
        t_mae[nt] = bal + b_mae
        bal += best_net
        t_bal[nt] = bal
        nt += 1
        busy = b_ei
        if bal <= init_bal * stop_out_level:
            dead = True
    return nt, t_fi, t_ei, t_side, t_lot, t_entry, t_sl, t_net, t_bal, t_mae, t_reason, t_tie, n_skip_margin, dead


EXIT = {1: "SL", 2: "TP", 3: "BE", 4: "TRAIL", 5: "TIME", 6: "FRIDAY", 7: "END"}


def run(mk: Market, setups: pd.DataFrame, *, tf_minutes: int, spread: np.ndarray, init_bal=1000.0, lot_mode=0,
        fixed_lot=0.10, risk_pct=1.0, tp_r=100.0, trail_atr=2.0, max_hold_min=2880, fri_close=23 * 60,
        slip=0.05, comm=3.5, contract=100.0, leverage=100.0, swap_long=-0.066, swap_short=0.029,
        min_lot=0.01, lot_step=0.01, stop_out_level=0.0):
    """setups columns: bar_time (decision bar open time), valid_bars, p_hi, p_lo, sl_hi, sl_lo, atr."""
    s = setups.sort_values("bar_time").reset_index(drop=True)
    avail_t = s.bar_time.values + np.timedelta64(tf_minutes, "m")
    s_avail = np.searchsorted(mk.index.values, avail_t).astype(np.int64)
    exp_t = avail_t + (s.valid_bars.values.astype("int64") * tf_minutes).astype("timedelta64[m]")
    s_exp = (np.searchsorted(mk.index.values, exp_t) - 1).astype(np.int64)
    r = _run(mk.o, mk.h, mk.l, mk.c, spread, mk.day, mk.dow, mk.mod, swap_long, swap_short,
             s_avail, s_exp, s.p_hi.values.astype(float), s.p_lo.values.astype(float), s.sl_hi.values.astype(float),
             s.sl_lo.values.astype(float), s.atr.values.astype(float), init_bal, lot_mode, fixed_lot, risk_pct, tp_r,
             trail_atr, max_hold_min, fri_close, slip, comm, contract, leverage, min_lot, lot_step, stop_out_level)
    nt, fi, ei, side, lot, entry, sl, net, bal, eqlow, rs, tie, skip_margin, dead = r
    sl_ = slice(0, nt)
    tr = pd.DataFrame({"entry_time": mk.index[fi[sl_]], "exit_time": mk.index[ei[sl_]], "side": side[sl_], "lot": lot[sl_],
                       "entry": entry[sl_], "sl0": sl[sl_], "net": net[sl_], "balance": bal[sl_], "equity_low": eqlow[sl_],
                       "exit_reason": [EXIT[x] for x in rs[sl_]], "same_bar_tie": tie[sl_]})
    tr["risk_money"] = (tr.entry - tr.sl0).abs() * tr.lot * contract
    tr["r_mult"] = tr.net / tr.risk_money
    return tr, {"skipped_margin": int(skip_margin), "account_dead": bool(dead)}
