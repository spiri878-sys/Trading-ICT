"""Execution simulator on M1 OHLC bars (bid prices). An APPROXIMATION, not a tick backtest.

Execution model (conservative; see docs/simulator.md):
* Chart prices are BID; ASK = BID + spread, spread per M1 bar = max(recorded, floor) * spread_mult.
* Long: entry at ASK, exits at BID. Short: entry at BID, exits at ASK.
* Limit orders fill at the limit price, or at the bar open when the bar gaps through it.
  Market orders fill at the next M1 open + adverse slippage. Stop exits get adverse slippage.
* On the fill bar only the stop is checked (worst case); no same-bar profit taking.
* Within one M1 bar the path is unknown: if the stop and a profit level are both touched, stop wins.
* Partials / break-even can be decided on the CLOSED M1 bar (mgmt_on_close=True, as shown in the
  Interstellar material: "parziali, pareggio, target 4R, decisi sulla barra chiusa") and are then
  executed at that bar's close. The final target is a resting limit (intrabar).
* One position and one pending order at a time; overlapping signals are logged as skipped.

The same `_manage` routine is used for (a) the portfolio backtest and (b) the per-signal
labelling used to train the ML filter, so labels and backtest follow identical rules.
"""
from dataclasses import dataclass, asdict
import numpy as np
import pandas as pd
from numba import njit

STOP_STRUCT, STOP_FIXED, STOP_PERCENT, STOP_ATR = 0, 1, 2, 3
STOP_NAMES = {0: "STRUCTURAL", 1: "FIXED", 2: "PERCENT", 3: "ATR"}
LOT_FIXED, LOT_RISK = 0, 1
LOT_NAMES = {0: "FIXED", 1: "RISK_PERCENT"}
STATUS = {0: "unprocessed", 1: "filled", 2: "expired", 3: "skipped_busy", 4: "rejected_lot_below_min",
          5: "rejected_margin", 6: "rejected_stop_invalid", 7: "rejected_daily_limit", 8: "halted_max_dd",
          9: "rejected_stop_below_broker_min", 10: "rejected_fixed_lot_invalid", 11: "filtered_ml",
          12: "rejected_risk_too_high_for_min_lot"}
EXIT = {0: "OPEN", 1: "SL", 2: "TP", 3: "BE", 4: "TRAIL", 5: "TIME", 6: "FRIDAY", 7: "END"}


@dataclass
class Params:
    initial_balance: float = 1000.0
    # ---- stop selector (independent from lot selector)
    stop_mode: int = STOP_STRUCT
    stop_fixed_usd: float = 5.0        # FIXED: distance in price units (USD/oz). 1.00 = 100 points
    stop_percent: float = 0.25         # PERCENT: % of the ENTRY PRICE (not % of capital)
    stop_atr_mult: float = 1.5         # ATR: multiple of the signal-timeframe ATR(14)
    # ---- lot selector
    lot_mode: int = LOT_FIXED
    fixed_lot: float = 0.08
    risk_percent: float = 1.0
    risk_base_equity: bool = False     # informational: with one position at a time equity == balance at entry
    # ---- exits
    tp_r: float = 4.0
    p1_r: float = 0.7
    p1_frac: float = 0.2               # fraction of the INITIAL volume
    p2_r: float = 2.0
    p2_frac: float = 0.2
    be_after_p1: bool = True
    mgmt_on_close: bool = True
    trail_atr: float = 0.0             # 0 = off; trails after p1 by trail_atr * signal ATR
    max_hold_min: int = 3 * 24 * 60
    friday_close_min: int = 23 * 60    # server minute-of-day on Friday: flat, no new entries
    # ---- symbol / broker
    contract: float = 100.0
    min_lot: float = 0.01
    lot_step: float = 0.01
    max_lot: float = 50.0
    leverage: float = 100.0
    commission_per_lot_side: float = 3.5
    slippage: float = 0.05             # price units
    spread_floor: float = 0.15         # price units
    max_spread: float = 1.0            # no fill while spread above this (price units)
    stops_level: float = 0.0           # broker minimum stop distance (price units)
    # ---- account protection
    daily_loss_pct: float = 0.0        # 0 = off. Checked on closed P&L of the server day at entry time
    max_dd_pct: float = 0.0            # 0 = off. Kill switch on closed-balance drawdown
    # ---- "breathing" risk (risk-percent mode only): never above base
    breathe: bool = False
    breathe_dd_full: float = 5.0
    breathe_dd_min: float = 23.75
    breathe_mult_min: float = 0.25
    breathe_recover_wins: int = 20

    def describe(self):
        d = asdict(self)
        d["stop_mode"] = STOP_NAMES[self.stop_mode]
        d["lot_mode"] = LOT_NAMES[self.lot_mode]
        return d


@njit(cache=True)
def _floor_step(x, step):
    return np.floor(x / step + 1e-9) * step


@njit(cache=True)
def _find_fill(o, h, l, sp, dow, mod, i0, iexp, side, is_mkt, price, slip, max_spread, fri_close):
    """Return (bar index, fill price) or (-1, 0)."""
    n = o.size
    for i in range(i0, min(iexp + 1, n)):
        if dow[i] == 4 and mod[i] >= fri_close:
            return -1, 0.0
        if sp[i] > max_spread:
            if is_mkt:
                return -1, 0.0
            continue
        if is_mkt:
            return i, (o[i] + sp[i] + slip) if side == 1 else (o[i] - slip)
        if side == 1:
            if o[i] + sp[i] <= price:
                return i, o[i] + sp[i]
            if l[i] + sp[i] <= price:
                return i, price
        else:
            if o[i] >= price:
                return i, o[i]
            if h[i] >= price:
                return i, price
    return -1, 0.0


@njit(cache=True)
def _manage(o, h, l, c, sp, dow, mod, fi, side, entry, sl, rd, atr_sig,
            tp_r, p1_r, p1_frac, p2_r, p2_frac, be_on, on_close, trail_atr, max_hold, fri_close, slip):
    """Manage one position from fill bar `fi`.

    Returns (exit_i, pnl_px, reason, n_partials, mfe_r, mae_r) where pnl_px is the volume-weighted
    price P&L per 1 unit of initial volume (already including spread/slippage, excluding commission).
    """
    n = o.size
    tp = entry + side * tp_r * rd
    lv1 = entry + side * p1_r * rd
    lv2 = entry + side * p2_r * rd
    rem = 1.0; pnl = 0.0; npart = 0; mfe = 0.0; mae = 0.0
    cur_sl = sl
    for i in range(fi, n):
        spi = sp[i]
        if side == 1:
            adv = l[i]; fav = h[i]; cls = c[i]
        else:
            adv = h[i] + spi; fav = l[i] + spi; cls = c[i] + spi
        ef = (fav - entry) * side / rd
        ea = (adv - entry) * side / rd
        if ef > mfe: mfe = ef
        if ea < mae: mae = ea
        if i > fi and ((dow[i] == 4 and mod[i] >= fri_close) or (i - fi) >= max_hold):
            px = o[i] if side == 1 else o[i] + spi
            pnl += rem * (px - entry) * side
            return i, pnl, (6 if dow[i] == 4 and mod[i] >= fri_close else 5), npart, mfe, mae
        # stop (gap or touch) - checked first: worst case
        op = o[i] if side == 1 else o[i] + spi
        if (op - cur_sl) * side <= 0 or (adv - cur_sl) * side <= 0:
            if (op - cur_sl) * side <= 0 and i > fi:
                px = op - side * slip
            else:
                px = cur_sl - side * slip
            pnl += rem * (px - entry) * side
            if npart == 0:
                r = 1
            elif trail_atr > 0:
                r = 4
            else:
                r = 3
            return i, pnl, r, npart, mfe, mae
        if i == fi:
            continue
        # final target: resting limit, intrabar
        if (fav - tp) * side >= 0:
            pnl += rem * (tp - entry) * side
            return i, pnl, 2, npart, mfe, mae
        # partials
        ref = cls if on_close else fav
        if npart == 0 and p1_frac > 0 and (ref - lv1) * side >= 0:
            px = cls if on_close else lv1
            pnl += p1_frac * (px - entry) * side
            rem -= p1_frac; npart = 1
            if be_on:
                cur_sl = entry
        if npart == 1 and p2_frac > 0 and (ref - lv2) * side >= 0:
            px = cls if on_close else lv2
            pnl += p2_frac * (px - entry) * side
            rem -= p2_frac; npart = 2
        if not on_close and npart >= 1 and be_on and (adv - cur_sl) * side <= 0:
            # break-even level also inside this bar: assume it was hit after the partial
            pnl += rem * (cur_sl - side * slip - entry) * side
            return i, pnl, 3, npart, mfe, mae
        if trail_atr > 0 and npart >= 1:
            if side == 1:
                ns = c[i] - trail_atr * atr_sig
                if ns > cur_sl: cur_sl = ns
            else:
                ns = c[i] + spi + trail_atr * atr_sig
                if ns < cur_sl: cur_sl = ns
    i = n - 1
    px = c[i] if side == 1 else c[i] + sp[i]
    pnl += rem * (px - entry) * side
    return i, pnl, 7, npart, mfe, mae


@njit(cache=True)
def _stop_price(stop_mode, fill, side, sl_struct, stop_fixed, stop_pct, stop_atr, atr_sig):
    if stop_mode == 0:
        return sl_struct
    if stop_mode == 1:
        return fill - side * stop_fixed
    if stop_mode == 2:
        return fill * (1.0 - side * stop_pct / 100.0)
    return fill - side * stop_atr * atr_sig


@njit(cache=True)
def _label(o, h, l, c, sp, dow, mod, s_avail, s_exp, s_side, s_mkt, s_price, s_sl, s_atr,
           stop_mode, stop_fixed, stop_pct, stop_atr, tp_r, p1_r, p1_frac, p2_r, p2_frac, be_on, on_close,
           trail_atr, max_hold, fri_close, slip, max_spread, comm_px):
    """Isolated outcome of every signal (as if it were the only trade). R is net of all costs."""
    ns = s_avail.size
    filled = np.zeros(ns, np.bool_); r_out = np.full(ns, np.nan); exit_i = np.full(ns, -1)
    fill_i = np.full(ns, -1); mfe = np.full(ns, np.nan); mae = np.full(ns, np.nan); reason = np.zeros(ns, np.int8)
    for k in range(ns):
        fi, fp = _find_fill(o, h, l, sp, dow, mod, s_avail[k], s_exp[k], s_side[k], s_mkt[k] == 1, s_price[k],
                            slip, max_spread, fri_close)
        if fi < 0:
            continue
        sl = _stop_price(stop_mode, fp, s_side[k], s_sl[k], stop_fixed, stop_pct, stop_atr, s_atr[k])
        rd = (fp - sl) * s_side[k]
        if not (rd > 0):
            continue
        ei, pnl, rs, npart, a, b = _manage(o, h, l, c, sp, dow, mod, fi, s_side[k], fp, sl, rd, s_atr[k], tp_r, p1_r,
                                           p1_frac, p2_r, p2_frac, be_on, on_close, trail_atr, max_hold, fri_close, slip)
        filled[k] = True; fill_i[k] = fi; exit_i[k] = ei; reason[k] = rs
        r_out[k] = (pnl - 2 * comm_px) / (rd + slip + 2 * comm_px)
        mfe[k] = a; mae[k] = b
    return filled, fill_i, exit_i, r_out, mfe, mae, reason


@njit(cache=True)
def _portfolio(o, h, l, c, sp, day, dow, mod, s_avail, s_exp, s_side, s_mkt, s_price, s_sl, s_atr, s_take,
               init_bal, stop_mode, stop_fixed, stop_pct, stop_atr, lot_mode, fixed_lot, risk_pct,
               tp_r, p1_r, p1_frac, p2_r, p2_frac, be_on, on_close, trail_atr, max_hold, fri_close,
               contract, min_lot, lot_step, max_lot, leverage, comm, slip, max_spread, stops_level,
               daily_loss, max_dd, breathe, b_full, b_min, b_mult_min, b_wins):
    ns = s_avail.size
    status = np.zeros(ns, np.int8)
    t_sig = np.zeros(ns, np.int64); t_fi = np.zeros(ns, np.int64); t_ei = np.zeros(ns, np.int64)
    t_lot = np.zeros(ns); t_entry = np.zeros(ns); t_sl = np.zeros(ns); t_pnl = np.zeros(ns); t_comm = np.zeros(ns)
    t_reason = np.zeros(ns, np.int8); t_npart = np.zeros(ns, np.int8); t_rd = np.zeros(ns); t_riskm = np.zeros(ns)
    t_bal = np.zeros(ns); t_mfe = np.zeros(ns); t_mae = np.zeros(ns); t_eqlow = np.zeros(ns); t_mult = np.zeros(ns)
    t_sp = np.zeros(ns)
    nt = 0
    bal = init_bal; peak = init_bal; halted = False
    busy_until = -1
    cur_day = -1; day_pnl = 0.0; day_start = init_bal
    reduced = False; wins_since = 0
    for k in range(ns):
        if not s_take[k]:
            status[k] = 11; continue
        if halted:
            status[k] = 8; continue
        if s_avail[k] <= busy_until:
            status[k] = 3; continue
        fi, fp = _find_fill(o, h, l, sp, dow, mod, s_avail[k], s_exp[k], s_side[k], s_mkt[k] == 1, s_price[k],
                            slip, max_spread, fri_close)
        if fi < 0:
            status[k] = 2
            # a pending order occupies the slot until it expires
            busy_until = max(busy_until, s_exp[k])
            continue
        if day[fi] != cur_day:
            cur_day = day[fi]; day_pnl = 0.0; day_start = bal
        if daily_loss > 0 and day_pnl <= -day_start * daily_loss / 100.0:
            status[k] = 7; busy_until = fi; continue
        side = s_side[k]
        sl = _stop_price(stop_mode, fp, side, s_sl[k], stop_fixed, stop_pct, stop_atr, s_atr[k])
        rd = (fp - sl) * side
        if not (rd > 0):
            status[k] = 6; busy_until = fi; continue
        if rd < stops_level:
            status[k] = 9; busy_until = fi; continue
        loss_per_lot = (rd + slip) * contract + 2 * comm
        mult = 1.0
        if lot_mode == 0:
            lot = fixed_lot
            if lot < min_lot - 1e-9 or abs(_floor_step(lot, lot_step) - lot) > 1e-7 or lot > max_lot + 1e-9:
                status[k] = 10; busy_until = fi; continue
        else:
            if breathe:
                dd = (peak - bal) / peak * 100.0
                if dd > b_full:
                    m = 1.0 - (1.0 - b_mult_min) * min(1.0, (dd - b_full) / (b_min - b_full))
                    if not reduced:
                        reduced = True; wins_since = 0
                    mult = m if wins_since < b_wins else 1.0
            lot = _floor_step(bal * risk_pct * mult / 100.0 / loss_per_lot, lot_step)
            if lot > max_lot:
                lot = max_lot
            if lot < min_lot - 1e-9:
                status[k] = 12; busy_until = fi; continue
        if lot * contract * fp / leverage > bal:
            status[k] = 5; busy_until = fi; continue
        ei, pnl, rs, npart, a, b = _manage(o, h, l, c, sp, dow, mod, fi, side, fp, sl, rd, s_atr[k], tp_r, p1_r,
                                           p1_frac, p2_r, p2_frac, be_on, on_close, trail_atr, max_hold, fri_close, slip)
        money = pnl * lot * contract
        cm = 2 * comm * lot
        net = money - cm
        status[k] = 1
        t_sig[nt] = k; t_fi[nt] = fi; t_ei[nt] = ei; t_lot[nt] = lot; t_entry[nt] = fp; t_sl[nt] = sl
        t_pnl[nt] = money; t_comm[nt] = cm; t_reason[nt] = rs; t_npart[nt] = npart; t_rd[nt] = rd
        t_riskm[nt] = lot * loss_per_lot; t_mfe[nt] = a; t_mae[nt] = b
        t_eqlow[nt] = bal + min(0.0, b) * rd * lot * contract - cm
        t_mult[nt] = mult; t_sp[nt] = sp[fi]
        bal += net; day_pnl += net
        t_bal[nt] = bal
        if reduced and net > 0:
            wins_since += 1
        if bal >= peak:
            peak = bal; reduced = False; wins_since = 0
        if max_dd > 0 and bal <= peak * (1 - max_dd / 100.0):
            halted = True
        nt += 1
        busy_until = ei
    return (status, nt, t_sig, t_fi, t_ei, t_lot, t_entry, t_sl, t_pnl, t_comm, t_reason, t_npart, t_rd, t_riskm,
            t_bal, t_mfe, t_mae, t_eqlow, t_mult, t_sp)


class Market:
    """Pre-computed M1 arrays."""

    def __init__(self, m1: pd.DataFrame, point: float = 0.01):
        self.index = m1.index
        self.o, self.h, self.l, self.c = (m1[k].values.astype(np.float64) for k in ("open", "high", "low", "close"))
        self.sp_raw = m1.spread.values.astype(np.float64) * point
        self.day = (m1.index.normalize().values.astype("int64") // 86_400_000_000_000).astype(np.int64)
        self.dow = m1.index.dayofweek.values.astype(np.int64)
        self.mod = (m1.index.hour * 60 + m1.index.minute).values.astype(np.int64)

    def spread(self, prm: "Params", mult: float = 1.0):
        return np.maximum(self.sp_raw, prm.spread_floor) * mult


def _sig_arrays(mk: Market, sig: pd.DataFrame, tf_minutes: int):
    avail_t = sig.bar_time.values + np.timedelta64(tf_minutes, "m")
    s_avail = np.searchsorted(mk.index.values, avail_t, side="left").astype(np.int64)
    exp_t = avail_t + (sig.expiry_bars.values.astype("int64") * tf_minutes).astype("timedelta64[m]")
    s_exp = (np.searchsorted(mk.index.values, exp_t, side="left") - 1).astype(np.int64)
    return (s_avail, s_exp, sig.side.values.astype(np.int64), (sig.otype.values == "market").astype(np.int64),
            sig.price.values.astype(np.float64), sig.sl_struct.values.astype(np.float64), sig.atr.values.astype(np.float64))


def label(mk: Market, sig: pd.DataFrame, prm: Params, tf_minutes: int = 5, spread_mult: float = 1.0) -> pd.DataFrame:
    """Per-signal isolated outcome in R (net of spread, slippage, commission)."""
    sp = mk.spread(prm, spread_mult)
    a = _sig_arrays(mk, sig, tf_minutes)
    comm_px = prm.commission_per_lot_side / prm.contract
    filled, fi, ei, r, mfe, mae, rs = _label(mk.o, mk.h, mk.l, mk.c, sp, mk.dow, mk.mod, *a,
                                             prm.stop_mode, prm.stop_fixed_usd, prm.stop_percent, prm.stop_atr_mult,
                                             prm.tp_r, prm.p1_r, prm.p1_frac, prm.p2_r, prm.p2_frac, prm.be_after_p1,
                                             prm.mgmt_on_close, prm.trail_atr, prm.max_hold_min, prm.friday_close_min,
                                             prm.slippage * spread_mult, prm.max_spread, comm_px)
    out = sig.copy()
    out["filled"] = filled
    out["fill_time"] = pd.NaT
    out.loc[filled, "fill_time"] = mk.index[fi[filled]]
    out["exit_time"] = pd.NaT
    out.loc[filled, "exit_time"] = mk.index[ei[filled]]
    out["r"] = r; out["mfe_r"] = mfe; out["mae_r"] = mae
    out["exit_reason"] = [EXIT[x] for x in rs]
    return out


def run(mk: Market, sig: pd.DataFrame, prm: Params, tf_minutes: int = 5, spread_mult: float = 1.0, take=None):
    """Portfolio backtest. `sig` sorted by (bar_time, priority). `take`: optional boolean ML mask."""
    sig = sig.reset_index(drop=True)
    sp = mk.spread(prm, spread_mult)
    a = _sig_arrays(mk, sig, tf_minutes)
    tk = np.ones(len(sig), np.bool_) if take is None else np.asarray(take, np.bool_)
    out = _portfolio(mk.o, mk.h, mk.l, mk.c, sp, mk.day, mk.dow, mk.mod, *a, tk,
                     prm.initial_balance, prm.stop_mode, prm.stop_fixed_usd, prm.stop_percent, prm.stop_atr_mult,
                     prm.lot_mode, prm.fixed_lot, prm.risk_percent, prm.tp_r, prm.p1_r, prm.p1_frac, prm.p2_r,
                     prm.p2_frac, prm.be_after_p1, prm.mgmt_on_close, prm.trail_atr, prm.max_hold_min,
                     prm.friday_close_min, prm.contract, prm.min_lot, prm.lot_step, prm.max_lot, prm.leverage,
                     prm.commission_per_lot_side, prm.slippage * spread_mult, prm.max_spread, prm.stops_level,
                     prm.daily_loss_pct, prm.max_dd_pct, prm.breathe, prm.breathe_dd_full, prm.breathe_dd_min,
                     prm.breathe_mult_min, prm.breathe_recover_wins)
    (status, nt, t_sig, t_fi, t_ei, t_lot, t_entry, t_sl, t_pnl, t_comm, t_reason, t_npart, t_rd, t_riskm,
     t_bal, t_mfe, t_mae, t_eqlow, t_mult, t_sp) = out
    s = slice(0, nt)
    tr = pd.DataFrame({
        "signal": t_sig[s], "entry_time": mk.index[t_fi[s]], "exit_time": mk.index[t_ei[s]],
        "side": sig.side.values[t_sig[s]], "strategy": sig.strategy.values[t_sig[s]],
        "lot": t_lot[s], "entry": t_entry[s], "sl0": t_sl[s], "r_dist": t_rd[s],
        "gross": t_pnl[s], "commission": t_comm[s], "exit_reason": [EXIT[x] for x in t_reason[s]],
        "partials": t_npart[s], "risk_money": t_riskm[s], "risk_mult": t_mult[s], "balance": t_bal[s],
        "mfe_r": t_mfe[s], "mae_r": t_mae[s], "equity_low": t_eqlow[s], "spread_at_entry": t_sp[s]})
    tr["net"] = tr.gross - tr.commission
    tr["r_mult"] = tr.net / tr.risk_money.replace(0, np.nan)
    sig = sig.assign(status=[STATUS[x] for x in status])
    return tr, sig
