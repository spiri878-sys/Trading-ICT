"""Etichettatura dei segnali PRIME (Fase 3): esito isolato di ogni segnale su barre M1 (BID; ASK = BID + spread).

Due profili di gestione (output/regole.md §4, §9):
  FOTO  20% a +0,7R e stop a pareggio, 20% a +2R, residuo al TP 4R (decisioni sulla chiusura M1)
  V5    90% a +1R sulla chiusura M1, pareggio, trailing strutturale sugli swing M5 confermati (-0,2 ATR M5),
        blocchi +1R/+2R (da MFE 2R/3R), uscita adattiva su MSS M5 contrario dopo +1R, residuo al TP

Convenzioni prudenti identiche a raptor.engine: stop controllato per primo nella barra, gap allo stop al prezzo
d'apertura, slippage avverso su stop e mercato, nessun target nella barra di riempimento; massimo 3 giorni;
chiusura il venerdì alle 23 server; swap per notte; R netto = P&L / (rischio + slippage + commissione).
Gli swing/rotture M5 sono visibili su M1 solo dall'orario di DISPONIBILITÀ (chiusura della barra M5 che li
conferma): nessun lookahead.
"""
import numpy as np
import pandas as pd
from numba import njit

from ..engine import _find_fill

PROFILES = {
    "FOTO": dict(p1_r=0.7, p1_frac=0.2, p2_r=2.0, p2_frac=0.2, tp_r=4.0, trail=False, lock=False, adaptive=False),
    "V5": dict(p1_r=1.0, p1_frac=0.9, p2_r=0.0, p2_frac=0.0, tp_r=4.0, trail=True, lock=True, adaptive=True),
}
COSTS_C1 = dict(spread=0.30, comm_per_lot_side=3.5, slip=0.05, swap_long=-0.066, swap_short=0.029)
EXIT = {1: "SL", 2: "TP", 3: "BE", 4: "TRAIL", 5: "TIME", 6: "FRIDAY", 7: "END", 8: "ADAPTIVE", 9: "LOCK"}


@njit(cache=True)
def manage(o, h, l, c, sp, dow, mod, swl, swh, brk5, atr5, fi, side, entry, sl, rd,
           p1_r, p1_frac, p2_r, p2_frac, tp_r, trail, lock, adaptive, max_hold, fri_close, slip):
    """Gestione di una posizione dal minuto di riempimento fi. Restituisce (exit_i, pnl_px per unità, reason)."""
    n = o.size
    tp = entry + side * tp_r * rd
    lv1 = entry + side * p1_r * rd
    lv2 = entry + side * p2_r * rd
    rem = 1.0
    pnl = 0.0
    npart = 0
    cur_sl = sl
    mfe = 0.0
    reason_sl = 1
    for i in range(fi, n):
        spi = sp[i]
        if side == 1:
            adv = l[i]; fav = h[i]; cls = c[i]; op = o[i]
        else:
            adv = h[i] + spi; fav = l[i] + spi; cls = c[i] + spi; op = o[i] + spi
        if i > fi and ((dow[i] == 4 and mod[i] >= fri_close) or (i - fi) >= max_hold):
            pnl += rem * (op - entry) * side
            return i, pnl, (6 if dow[i] == 4 and mod[i] >= fri_close else 5)
        if (op - cur_sl) * side <= 0 or (adv - cur_sl) * side <= 0:
            px = (op - side * slip) if ((op - cur_sl) * side <= 0 and i > fi) else (cur_sl - side * slip)
            pnl += rem * (px - entry) * side
            return i, pnl, (1 if npart == 0 and reason_sl == 1 else reason_sl)
        if i == fi:
            continue
        ef = (fav - entry) * side / rd
        if ef > mfe:
            mfe = ef
        if (fav - tp) * side >= 0:
            pnl += rem * (tp - entry) * side
            return i, pnl, 2
        if npart == 0 and p1_frac > 0 and (cls - lv1) * side >= 0:
            pnl += p1_frac * (cls - entry) * side
            rem -= p1_frac
            npart = 1
            if (entry - cur_sl) * side > 0:
                cur_sl = entry
                reason_sl = 3
        if npart == 1 and p2_frac > 0 and (cls - lv2) * side >= 0:
            pnl += p2_frac * (cls - entry) * side
            rem -= p2_frac
            npart = 2
        if adaptive and npart >= 1 and brk5[i] == -side:
            pnl += rem * (cls - side * slip - entry) * side
            return i, pnl, 8
        if lock and npart >= 1:
            lk = -1e18
            if mfe >= 3.0:
                lk = 2.0
            elif mfe >= 2.0:
                lk = 1.0
            if lk > -1e17:
                ns = entry + side * lk * rd
                if (ns - cur_sl) * side > 0 and (cls - ns) * side > 0:
                    cur_sl = ns
                    reason_sl = 9
        if trail and npart >= 1:
            if side == 1:
                ns = swl[i] - 0.2 * atr5[i]
            else:
                ns = swh[i] + 0.2 * atr5[i]
            if np.isfinite(ns) and (ns - cur_sl) * side > 0 and (cls - ns) * side > 0:
                cur_sl = ns
                reason_sl = 4
    i = n - 1
    px = c[i] if side == 1 else c[i] + sp[i]
    pnl += rem * (px - entry) * side
    return i, pnl, 7


@njit(cache=True)
def path_stats(o, h, l, sp, fi, side, entry, sl, rd, max_hold):
    """Statistiche del percorso indipendenti dalla gestione, fino allo stop INIZIALE o a max_hold:
    MFE (R) prima dello stop iniziale, MAE (R) prima di toccare +1R, minuti fino allo stop o alla fine."""
    n = o.size
    mfe = 0.0
    mae_b1 = 0.0
    reached1 = False
    for i in range(fi, min(n, fi + max_hold)):
        spi = sp[i]
        if side == 1:
            adv = l[i]; fav = h[i]
        else:
            adv = h[i] + spi; fav = l[i] + spi
        ea = (adv - entry) * side / rd
        if not reached1 and ea < mae_b1:
            mae_b1 = ea
        if (adv - sl) * side <= 0:
            return mfe, mae_b1, i - fi
        if i > fi:
            ef = (fav - entry) * side / rd
            if ef > mfe:
                mfe = ef
            if ef >= 1.0:
                reached1 = True
    return mfe, mae_b1, min(n, fi + max_hold) - fi


@njit(cache=True)
def label_all(o, h, l, c, sp, dow, mod, day, swl, swh, brk5, atr5, s_i0, s_i1, s_side, s_mkt, s_price, s_sl,
              s_tpr, prof, max_hold, fri_close, slip, comm_px, max_spread, sw_l, sw_s):
    """prof: array [n_prof, 8] = p1_r, p1_frac, p2_r, p2_frac, tp_r, trail, lock, adaptive."""
    ns = s_i0.size
    npf = prof.shape[0]
    fill_i = np.full(ns, -1)
    fill_px = np.full(ns, np.nan)
    rd_out = np.full(ns, np.nan)
    r = np.full((ns, npf), np.nan)
    ex_i = np.full((ns, npf), -1)
    reason = np.zeros((ns, npf), np.int8)
    mfe = np.full(ns, np.nan); mae1 = np.full(ns, np.nan); dur = np.full(ns, -1)
    for k in range(ns):
        fi, fp = _find_fill(o, h, l, sp, dow, mod, s_i0[k], s_i1[k], s_side[k], s_mkt[k], s_price[k], slip,
                            max_spread, fri_close)
        if fi < 0:
            continue
        rd = (fp - s_sl[k]) * s_side[k]
        if not (rd > 0):
            continue
        fill_i[k] = fi; fill_px[k] = fp; rd_out[k] = rd
        a, b, d = path_stats(o, h, l, sp, fi, s_side[k], fp, s_sl[k], rd, max_hold)
        mfe[k] = a; mae1[k] = b; dur[k] = d
        for p in range(npf):
            tpr = s_tpr[k] if s_tpr[k] > 0 else prof[p, 4]
            ei, pnl, rs = manage(o, h, l, c, sp, dow, mod, swl, swh, brk5, atr5, fi, s_side[k], fp, s_sl[k], rd,
                                 prof[p, 0], prof[p, 1], prof[p, 2], prof[p, 3], tpr, prof[p, 5] > 0,
                                 prof[p, 6] > 0, prof[p, 7] > 0, max_hold, fri_close, slip)
            nights = day[ei] - day[fi]
            pnl += (sw_l if s_side[k] == 1 else sw_s) * fp * nights / 365.0
            r[k, p] = (pnl - 2 * comm_px) / (rd + slip + 2 * comm_px)
            ex_i[k, p] = ei
            reason[k, p] = rs
    return fill_i, fill_px, rd_out, r, ex_i, reason, mfe, mae1, dur


class M1Arrays:
    """Array M1 per la simulazione + swing/rotture M5 mappati all'orario di disponibilità."""

    def __init__(self, m1: pd.DataFrame, f5: pd.DataFrame, spread: float = COSTS_C1["spread"]):
        self.index = m1.index
        self.o, self.h, self.l, self.c = (m1[k].values.astype(float) for k in ("open", "high", "low", "close"))
        self.sp = np.full(len(m1), spread)
        self.dow = m1.index.dayofweek.values.astype(np.int64)
        self.mod = (m1.index.hour * 60 + m1.index.minute).values.astype(np.int64)
        self.day = m1.index.values.astype("datetime64[D]").astype(np.int64)
        # M5 values known at the close of M5 bar j (= f5.index[j] + 5min); M1 bar i is decided at its close
        avail = (f5.index + pd.Timedelta("5min")).values
        dec = (m1.index + pd.Timedelta("1min")).values
        j = np.searchsorted(avail, dec, side="right") - 1
        ok = j >= 0
        jj = np.where(ok, j, 0)
        self.swl = np.where(ok, f5.swing_lo.values[jj], np.nan)
        self.swh = np.where(ok, f5.swing_hi.values[jj], np.nan)
        self.atr5 = np.where(ok, f5.atr.values[jj], np.nan)
        # break direction only on the minute in which the M5 bar closes
        exact = ok & (avail[jj] == dec)
        self.brk5 = np.where(exact, f5.brk.values[jj], 0).astype(np.int64)


def label_signals(sig: pd.DataFrame, A: M1Arrays, stop="struct", atr_mult=3.0, profiles=("FOTO", "V5"),
                  max_hold_min=3 * 24 * 60, fri_close=23 * 60, costs=COSTS_C1, max_spread=10.0):
    s = sig.reset_index(drop=True)
    idx = A.index.values
    i0 = np.searchsorted(idx, s.known_at.values.astype("datetime64[ns]"))
    dur = (s.expiry_bars.values * pd.to_timedelta(s.tf).values).astype("timedelta64[ns]")
    i1 = np.searchsorted(idx, (s.known_at.values + dur).astype("datetime64[ns]")) - 1
    sl = s.sl_struct.values.astype(float)
    if stop == "atr":
        sl = s.price.values - s.side.values * atr_mult * s.atr_m15.values
    prof = np.array([[PROFILES[p][k] for k in ("p1_r", "p1_frac", "p2_r", "p2_frac", "tp_r")] +
                     [float(PROFILES[p]["trail"]), float(PROFILES[p]["lock"]), float(PROFILES[p]["adaptive"])]
                     for p in profiles], float)
    comm_px = costs["comm_per_lot_side"] / 100.0
    out = label_all(A.o, A.h, A.l, A.c, A.sp, A.dow, A.mod, A.day, A.swl, A.swh, A.brk5, A.atr5,
                    i0.astype(np.int64), i1.astype(np.int64), s.side.values.astype(np.int64),
                    (s.otype.values == "market"), s.price.values.astype(float), sl, np.zeros(len(s)), prof,
                    max_hold_min, fri_close, costs["slip"], comm_px, max_spread, costs["swap_long"],
                    costs["swap_short"])
    fill_i, fill_px, rd, r, ex_i, reason, mfe, mae1, dur_m = out
    res = s[["bar_time", "known_at", "cell", "tf", "side", "otype", "price"]].copy()
    res["sl"] = sl
    res["filled"] = fill_i >= 0
    res["fill_time"] = pd.NaT
    res.loc[res.filled, "fill_time"] = idx[fill_i[fill_i >= 0]]
    res["fill_px"], res["risk_px"] = fill_px, rd
    res["mfe_r"], res["mae_before_1r"], res["path_minutes"] = mfe, mae1, dur_m
    res["big_runner"] = np.where(res.filled, mfe >= 3.0, np.nan)
    res["clean_entry"] = np.where(res.filled, mae1 > -0.5, np.nan)
    for p, name in enumerate(profiles):
        res[f"r_{name.lower()}"] = r[:, p]
        res[f"exit_{name.lower()}"] = [EXIT.get(int(x), "") if f else "" for x, f in zip(reason[:, p], res.filled)]
        ex = ex_i[:, p]
        res[f"exit_time_{name.lower()}"] = pd.NaT
        res.loc[ex >= 0, f"exit_time_{name.lower()}"] = idx[ex[ex >= 0]]
    return res
