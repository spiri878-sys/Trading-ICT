"""Traduzione in Python delle 10 strategie TradingView inviate dal cliente (Fase 14), parametri di default.
Ogni funzione riceve le barre (DataFrame open/high/low/close/tickvol, indice = orario server NY+7) e
restituisce i trade chiusi: DataFrame(time = ingresso, side, r).
Semplificazioni dichiarate nei commenti di ciascuna funzione.
"""
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier

from .common import SPREAD, atr, dmi, ema, macd, pivots, rma, rsi, sma, true_range, wma
from .engine import Position, fill_limit_order, fill_stop_order, mkt_entry


def _arr(b):
    return (b.open.values.astype(float), b.high.values.astype(float), b.low.values.astype(float),
            b.close.values.astype(float), b.tickvol.values.astype(float), b.index)


def _nights(t, i0, i1):
    return int((t[i1].normalize() - t[i0].normalize()).days) if i1 is not None else 0


def _rows(rows):
    return pd.DataFrame(rows, columns=["time", "side", "r"])


# ============================================================ 1. Gold Breakout 15M [WillyAlgoTrader]
def gold_breakout(b, range_from=0, range_to=7, close_hour=20, sl_mode="pct", sl_pct=1.0):
    """Range 00:00-06:59 ora broker (= ora server NY+7), poi stop d'ingresso su massimo e minimo (OCA),
    un trade al giorno, stop 1% dall'ingresso (o lato opposto del range), chiusura forzata alle 20:00."""
    o, h, l, c, v, t = _arr(b)
    hour = t.hour.values
    day = t.normalize().values
    rows = []
    pos = None
    rh = rl = np.nan
    traded = False
    cur_day = None
    for i in range(len(o)):
        if day[i] != cur_day:
            cur_day, rh, rl, traded = day[i], np.nan, np.nan, False
        if pos is not None:
            if hour[i] >= close_hour or hour[i] < range_to and day[i] != day[pos.i0]:
                pos.close(o[i], i)
            else:
                pos.step(i, o[i], h[i], l[i], c[i], check_targets=False)
            if pos.closed:
                rows.append((t[pos.i0], pos.side, pos.r(_nights(t, pos.i0, pos.exit_i))))
                pos = None
            continue
        if range_from <= hour[i] < range_to:
            rh = h[i] if np.isnan(rh) else max(rh, h[i])
            rl = l[i] if np.isnan(rl) else min(rl, l[i])
            continue
        if traded or np.isnan(rh) or not (range_to <= hour[i] < close_hour) or rh <= rl:
            continue
        fl = fill_stop_order(1, rh, o[i], h[i], l[i])
        fs = fill_stop_order(-1, rl, o[i], h[i], l[i])
        if fl is not None and fs is not None:      # entrambi nella stessa barra: vale il più vicino all'apertura
            if abs(o[i] - rh) <= abs(o[i] - rl):
                fs = None
            else:
                fl = None
        side, fill = (1, fl) if fl is not None else ((-1, fs) if fs is not None else (0, None))
        if side == 0:
            continue
        stop = fill * (1 - side * sl_pct / 100) if sl_mode == "pct" else (rl if side == 1 else rh)
        pos = Position(side, fill, stop, i)
        traded = True
        if pos.step(i, o[i], h[i], l[i], c[i], check_targets=False):
            rows.append((t[i], side, pos.r()))
            pos = None
    return _rows(rows)


# ============================================================ 2. ICT 10AM First FVG Daily
def ict_10am_fvg(b, start_hour=10, end_hour=16):
    """Ora New York = ora server - 7. Alle 10:00 NY si fissa l'apertura; primo FVG a 3 candele con candela
    centrale dalle 10:00; limite sul bordo dell'FVG, stop all'estremo della candela centrale, target = estremo
    della sessione dalle 10:00 fino al tocco. Un trade al giorno, chiusura alle 16:00, venerdì entro 15:45."""
    o, h, l, c, v, t = _arr(b)
    ny = t - pd.Timedelta(hours=7)
    hr, mn, dow = ny.hour.values, ny.minute.values, ny.dayofweek.values
    nday = ny.normalize().values
    rows = []
    pos = None
    cur = None
    for i in range(2, len(o)):
        if nday[i] != cur:
            cur = nday[i]
            s_open = s_hi = s_lo = np.nan
            found = done = False
            setup = None
        fri_lock = dow[i] == 4 and hr[i] * 60 + mn[i] >= 15 * 60 + 45
        if pos is not None:
            if hr[i] >= end_hour or fri_lock or nday[i] != nday[pos.i0]:
                pos.close(o[i], i)
            else:
                pos.step(i, o[i], h[i], l[i], c[i])
            if pos.closed:
                rows.append((t[pos.i0], pos.side, pos.r(_nights(t, pos.i0, pos.exit_i))))
                pos = None
            continue
        in_win = start_hour <= hr[i] < end_hour
        if hr[i] == start_hour and mn[i] == 0 and np.isnan(s_open):
            s_open, s_hi, s_lo = o[i], h[i], l[i]
        elif in_win and not np.isnan(s_open):
            s_hi, s_lo = max(s_hi, h[i]), min(s_lo, l[i])
        if done or np.isnan(s_open) or not in_win or fri_lock:
            continue
        if setup is not None:          # limite in attesa: riempimento in questa barra?
            side, entry, stop = setup
            fill = fill_limit_order(side, entry, o[i], h[i], l[i])
            tgt = s_hi if side == 1 else s_lo
            if fill is not None:
                tgt_prev = setup_tgt
                if (tgt_prev - fill) * side > 0 and (fill - stop) * side > 0:
                    pos = Position(side, fill, stop, i, targets=[(tgt_prev, None)])
                    done = True
                    if pos.step(i, o[i], h[i], l[i], c[i], check_targets=False):
                        rows.append((t[i], side, pos.r()))
                        pos = None
                else:
                    done = True
                continue
            setup_tgt = tgt
            continue
        gen_ok = (ny[i - 1].hour >= start_hour) and (ny[i - 1].hour < end_hour)
        if not found and gen_ok:
            if h[i] < l[i - 2]:
                found, setup, setup_tgt = True, (-1, h[i], h[i - 1]), s_lo
            elif l[i] > h[i - 2]:
                found, setup, setup_tgt = True, (1, l[i], l[i - 1]), s_hi
    return _rows(rows)


# ============================================================ 3. Liquidity Sweep Reversal
def sweep_reversal(b, piv=7, max_age=150, min_gap=0.25, sl_mult=1.2, min_risk=0.5, rr=1.5, be_pct=50,
                   vol_mult=1.3, wick_ratio=1.5, sess=(8 * 60, 12 * 60)):
    """Livelli = pivot (7/7) non ancora spazzati; sweep = ombra oltre il livello e chiusura dentro, con volume
    tick > 1,3 x media 20 e ombra >= 1,5 x corpo; conferma alla barra dopo (chiusura oltre la metà dello sweep);
    sessione 12:00-16:00 UTC = 08:00-12:00 New York. Stop 1,2 ATR oltre l'ombra, target 1,5R, pareggio a metà."""
    o, h, l, c, v, t = _arr(b)
    a = atr(h, l, c, 14)
    vs = sma(v, 20)
    ph, pl = pivots(h, l, piv, piv)
    nymin = ((t - pd.Timedelta(hours=7)).hour * 60 + (t - pd.Timedelta(hours=7)).minute).values
    highs, lows = [], []
    rows = []
    pos = None
    pend_l = pend_s = False
    pwick = pmid = np.nan
    be_done = False
    for i in range(len(o)):
        if pos is not None:
            pos.step(i, o[i], h[i], l[i], c[i])
            if not pos.closed and not be_done:
                trig = pos.entry + (pos.targets[0][0] - pos.entry) * be_pct / 100 if pos.targets else None
                if trig is not None and ((pos.side == 1 and h[i] >= trig) or (pos.side == -1 and l[i] <= trig)):
                    pos.stop, be_done = pos.entry, True
            if pos.closed:
                rows.append((t[pos.i0], pos.side, pos.r(_nights(t, pos.i0, pos.exit_i))))
                pos = None
        if np.isnan(a[i]):
            continue
        if not np.isnan(ph[i]) and all(abs(x[0] - ph[i]) >= a[i] * min_gap for x in highs):
            highs.append((ph[i], i - piv))
        if not np.isnan(pl[i]) and all(abs(x[0] - pl[i]) >= a[i] * min_gap for x in lows):
            lows.append((pl[i], i - piv))
        body = abs(c[i] - o[i])
        volok = v[i] > vs[i] * vol_mult if not np.isnan(vs[i]) else False
        sh = sl_ = False
        shw = slw = np.nan
        keep = []
        for lv, bi in highs:
            wk = h[i] - max(c[i], o[i])
            wok = (body > 0 and wk / body >= wick_ratio) or (body == 0 and wk > 0)
            if h[i] > lv and c[i] < lv and volok and wok:
                sh, shw = True, h[i]
            elif i - bi > max_age:
                pass
            else:
                keep.append((lv, bi))
        highs = keep
        keep = []
        for lv, bi in lows:
            wk = min(c[i], o[i]) - l[i]
            wok = (body > 0 and wk / body >= wick_ratio) or (body == 0 and wk > 0)
            if l[i] < lv and c[i] > lv and volok and wok:
                sl_, slw = True, l[i]
            elif i - bi > max_age:
                pass
            else:
                keep.append((lv, bi))
        lows = keep
        if pos is not None or i + 1 >= len(o):
            continue
        sess_ok = sess[0] <= nymin[i] < sess[1]
        do_l = pend_l and c[i] > pmid and sess_ok
        do_s = pend_s and c[i] < pmid and sess_ok
        wick = pwick
        pend_l = pend_s = False
        if sl_:
            pend_l, pwick, pmid = True, slw, (slw + c[i]) / 2
        if sh:
            pend_s, pwick, pmid = True, shw, (shw + c[i]) / 2
        if do_l or do_s:
            side = 1 if do_l else -1
            stop = wick - side * a[i] * sl_mult
            risk = (c[i] - stop) * side
            if risk >= a[i] * min_risk:
                tp = c[i] + side * risk * rr
                e = mkt_entry(side, o[i + 1])
                if (e - stop) * side > 0 and (tp - e) * side > 0:
                    pos = Position(side, e, stop, i + 1, targets=[(tp, None)])
                    be_done = False
    return _rows(rows)


# ============================================================ 4. Glow Ribbon Flip
def ribbon_flip(b, base_len=21, atr_len=10, mult=2.0, tp_r=2.0):
    """EMA21 con banda ATR10 x 2 che si muove solo a favore del trend; chiusura oltre la banda = inversione
    (stop-and-reverse); da flat in trend, chiusura che riattraversa la EMA = rientro (pullback); stop = banda
    (aggiornata a ogni barra), target 2R dalla distanza alla banda all'ingresso."""
    o, h, l, c, v, t = _arr(b)
    bas = ema(c, base_len)
    av = atr(h, l, c, atr_len)
    n = len(o)
    lo = np.full(n, np.nan)
    hi = np.full(n, np.nan)
    dr = np.zeros(n, int)
    rows = []
    pos = None
    pending = None
    for i in range(n):
        if pending is not None and pos is None:
            side, dist = pending
            e = mkt_entry(side, o[i])
            stop = lo[i - 1] if side == 1 else hi[i - 1]
            if (e - stop) * side > 0:
                pos = Position(side, e, stop, i, risk=dist, targets=[(e + side * tp_r * dist, None)])
            pending = None
        if pos is not None:
            pos.step(i, o[i], h[i], l[i], c[i])
            if pos.closed:
                rows.append((t[pos.i0], pos.side, pos.r(_nights(t, pos.i0, pos.exit_i))))
                pos = None
        if np.isnan(av[i]):
            continue
        ln, hn = bas[i] - mult * av[i], bas[i] + mult * av[i]
        plo, phi = (lo[i - 1], hi[i - 1]) if i > 0 else (np.nan, np.nan)
        lo[i] = ln if np.isnan(plo) or ln > plo or c[i - 1] < plo else plo
        hi[i] = hn if np.isnan(phi) or hn < phi or c[i - 1] > phi else phi
        pd_ = dr[i - 1] if i > 0 else 0
        d = pd_
        if pd_ == 0:
            d = 1 if c[i] > bas[i] else -1
        elif pd_ == 1 and c[i] < plo:
            d = -1
        elif pd_ == -1 and c[i] > phi:
            d = 1
        dr[i] = d
        flip_b, flip_s = d == 1 and pd_ != 1, d == -1 and pd_ != -1
        stop_line = lo[i] if d == 1 else hi[i]
        if pos is not None:
            pos.stop = lo[i] if pos.side == 1 else hi[i]
            if (flip_b and pos.side == -1) or (flip_s and pos.side == 1):
                if i + 1 < n:
                    pos.close(o[i + 1], i + 1)
                    rows.append((t[pos.i0], pos.side, pos.r(_nights(t, pos.i0, i + 1))))
                    pos = None
        flat = pos is None
        pull_b = d == 1 and pd_ == 1 and c[i] > bas[i] and c[i - 1] <= bas[i - 1] and flat
        pull_s = d == -1 and pd_ == -1 and c[i] < bas[i] and c[i - 1] >= bas[i - 1] and flat
        dist = abs(c[i] - stop_line)
        if flat and dist > 0 and i + 1 < n:
            if flip_b or pull_b:
                pending = (1, dist)
            elif flip_s or pull_s:
                pending = (-1, dist)
    return _rows(rows)


# ============================================================ 5. Trend Analysis Strategy (TAS)
def trend_analysis(b, trk_len=14, trk_mult=2.2, min_score=50, late_max=10, sl_mult=2.0):
    """Tracker ATR (WMA del TR 14 x 2,2) con direzione; punteggio di 6 componenti (tracker, prezzo vs equilibrio
    HMA(linreg 55), pendenza equilibrio, RSI>50, RSI>media, +DI>-DI); ingresso al cambio di trend (o entro 10
    barre) se punteggio >= 50%; stop sul tracker; TP 1,5R (33%), 2,5R (33%), 3,5R resto; pareggio dopo TP1;
    uscita all'inversione del tracker; segnale opposto = inversione."""
    o, h, l, c, v, t = _arr(b)
    n = len(o)
    tra = wma(true_range(h, l, c), trk_len)
    trk = np.full(n, np.nan)
    tdir = np.ones(n, int)
    for i in range(n):
        if np.isnan(tra[i]):
            continue
        up, dn = h[i] + tra[i] * trk_mult, l[i] - tra[i] * trk_mult
        if i == 0 or np.isnan(trk[i - 1]):
            trk[i], tdir[i] = dn, 1
            continue
        d, tk = tdir[i - 1], trk[i - 1]
        if d == 1:
            tk = max(tk, dn)
            if c[i] < tk:
                d, tk = -1, up
        else:
            tk = min(tk, up)
            if c[i] > tk:
                d, tk = 1, dn
        trk[i], tdir[i] = tk, d
    lr = pd.Series(c).rolling(55).apply(lambda y: np.polyval(np.polyfit(np.arange(55), y, 1), 54), raw=True).values
    half = wma(lr, 4)
    full = wma(lr, 9)
    eq = wma(2 * half - full, 3)
    r_ = rsi(c, 14)
    rm = sma(r_, 14)
    pdi, mdi, _ = dmi(h, l, c, 14)
    score = (tdir + np.where(c > eq, 1, -1) + np.where(eq > np.r_[np.nan, eq[:-1]], 1, -1)
             + np.where(r_ > 50, 1, -1) + np.where(r_ > rm, 1, -1) + np.where(pdi > mdi, 1, -1))
    pct = score / 6 * 100
    ra = atr(h, l, c, 14)
    rows = []
    pos = None
    signaled = False
    tstart = 0
    pending = None
    for i in range(1, n):
        if pending is not None:
            kind, side, stop, tps = pending
            if kind == "close" and pos is not None:
                pos.close(o[i], i)
                rows.append((t[pos.i0], pos.side, pos.r(_nights(t, pos.i0, i))))
                pos = None
            elif kind == "entry":
                if pos is not None:
                    pos.close(o[i], i)
                    rows.append((t[pos.i0], pos.side, pos.r(_nights(t, pos.i0, i))))
                e = mkt_entry(side, o[i])
                if (e - stop) * side > 0:
                    risk = abs(c[i - 1] - stop)
                    pos = Position(side, e, stop, i, risk=risk,
                                   targets=[(c[i - 1] + side * risk * k, f) for k, f in ((1.5, .33), (2.5, .33), (3.5, None))],
                                   be_after_first=True)
                else:
                    pos = None
            pending = None
        if pos is not None:
            pos.step(i, o[i], h[i], l[i], c[i])
            if pos.closed:
                rows.append((t[pos.i0], pos.side, pos.r(_nights(t, pos.i0, pos.exit_i))))
                pos = None
        if np.isnan(eq[i]) or np.isnan(ra[i]):
            continue
        bull_flip = tdir[i] == 1 and tdir[i - 1] == -1
        bear_flip = tdir[i] == -1 and tdir[i - 1] == 1
        if bull_flip or bear_flip:
            signaled, tstart = False, i
        inwin = i - tstart <= late_max
        buy = tdir[i] == 1 and (bull_flip or (not signaled and inwin)) and pct[i] >= min_score and not signaled
        sell = tdir[i] == -1 and (bear_flip or (not signaled and inwin)) and pct[i] <= -min_score and not signaled
        if buy or sell:
            signaled = True
        if i + 1 >= n:
            continue
        side = 1 if buy else (-1 if sell else 0)
        if side and (pos is None or pos.side != side):
            st = trk[i]
            if (side == 1 and st >= c[i]) or (side == -1 and st <= c[i]):
                st = c[i] - side * ra[i] * sl_mult
            pending = ("entry", side, st, None)
        elif pos is not None and ((pos.side == 1 and bear_flip) or (pos.side == -1 and bull_flip)):
            pending = ("close", 0, 0, None)
    return _rows(rows)


# ============================================================ 6. XGBoost Mini [The Quant Science]
def xgb_mini(b, thr=0.54, n_samples=50, every=50, trail_pct=10.0):
    """Solo long. Ogni 50 barre addestra un gradient boosting piccolo (10 alberi, profondità 3) sugli ultimi 50
    campioni (etichetta: chiusura 2 barre dopo più alta); ingresso se probabilità > 0,54 e chiusura > SMA15;
    uscita se probabilità < 0,46 con conto in utile, oppure trailing 10% dal massimo. Ordini alla chiusura.
    R misurato rispetto al rischio del trailing (10% dell'ingresso)."""
    o, h, l, c, v, t = _arr(b)
    n = len(o)
    e50 = ema(c, 50)
    f = np.column_stack([rsi(c, 14) / 100, (c - e50) / c,
                         (c / np.r_[np.full(5, np.nan), c[:-5]] - 1) * 100 / 10, atr(h, l, c, 14) / c,
                         np.nan_to_num(v / sma(v, 20)) - 1,
                         np.nan_to_num((c - pd.Series(l).rolling(14).min().values) /
                                       (pd.Series(h).rolling(14).max().values - pd.Series(l).rolling(14).min().values),
                                       nan=0.5)])
    f = np.nan_to_num(f)
    s15 = sma(c, 15)
    model = None
    rows = []
    in_pos = False
    entry = hw = trail = 0.0
    i0 = 0
    last_exit = -999
    cum_r = 0.0
    bar_filter = 0
    for i in range(300, n):
        if i % every == 0:
            idx = [i - (n_samples - k + 10) for k in range(n_samples)]
            y = np.array([1 if c[j + 2] > c[j] else 0 for j in idx])
            if 0 < y.sum() < len(y):
                model = GradientBoostingClassifier(n_estimators=10, max_depth=3, learning_rate=0.1,
                                                   random_state=1).fit(f[idx], y)
        prob = model.predict_proba(f[i:i + 1])[0, 1] if model is not None else 0.5
        if in_pos:
            hw = max(hw, h[i])
            trail = max(trail, hw * (1 - trail_pct / 100))
            ex = None
            if l[i] <= trail:
                ex = min(trail, o[i]) - 0.05
            elif prob < 1 - thr and c[i] > entry and i > bar_filter:
                ex = c[i] - 0.05
            if ex is not None:
                risk = entry * trail_pct / 100
                pnl = ex - entry - 0.07 - 0.066 * entry * (t[i].normalize() - t[i0].normalize()).days / 365
                rows.append((t[i0], 1, pnl / risk))
                in_pos, last_exit = False, i
            continue
        if model is not None and prob > thr and c[i] > s15[i] and i - last_exit > 1:
            entry = c[i] + SPREAD + 0.05
            hw, trail, i0, in_pos, bar_filter = entry, entry * (1 - trail_pct / 100), i, True, i + 3
    return _rows(rows)


# ============================================================ 7. Elliott Wave Impulse
def elliott(b, zz=5, min_ret4=0.236, max_ret4=0.618, min_imp=1.5, stop_buf=0.2, min_rr=1.0, tgt_fib=0.5,
            w5_ext=1.0, max_bars=100):
    """ZigZag da pivot (5 a sinistra, 1 a destra). Inversione: impulso a 5 onde completato e svolta -> trade
    opposto, stop oltre l'onda 5, target 50% di ritracciamento. Onda 5: onde 1-4 valide (onda 4 ritraccia
    23,6-61,8% della 3) -> trade a favore, stop oltre l'onda 4, target = onda 1. R:R minimo 1, time stop 100."""
    o, h, l, c, v, t = _arr(b)
    n = len(o)
    a = atr(h, l, c, 14)
    ph, pl = pivots(h, l, zz, 1)
    zy, zdir = [], 0
    rows = []
    pos = None
    for i in range(n):
        if pos is not None:
            if i - pos.i0 >= max_bars:
                pos.close(o[i], i)
            else:
                pos.step(i, o[i], h[i], l[i], c[i])
            if pos.closed:
                rows.append((t[pos.i0], pos.side, pos.r(_nights(t, pos.i0, pos.exit_i))))
                pos = None
        flipped = False
        if not np.isnan(ph[i]):
            y2 = h[i - 1]
            if zdir < 1:
                zy.insert(0, y2)
                zdir, flipped = 1, True
            elif ph[i] > zy[0]:
                zy[0] = y2
        if not np.isnan(pl[i]):
            y2 = l[i - 1]
            if zdir > -1:
                zy.insert(0, y2)
                zdir, flipped = -1, True
            elif pl[i] < zy[0]:
                zy[0] = y2
        zy = zy[:8]
        if not flipped or pos is not None or i + 1 >= n or np.isnan(a[i]):
            continue
        sig = None
        if len(zy) >= 7:
            d = 1 if zdir == -1 else -1
            p0, p1, p2, p3, p4, p5 = zy[6], zy[5], zy[4], zy[3], zy[2], zy[1]
            if d == 1:
                w1, w3, w5 = p1 - p0, p3 - p2, p5 - p4
                ok = w3 != min(w1, w3, w5) and p5 > p3 and p2 > p0 and p4 > p1
            else:
                w1, w3, w5 = p0 - p1, p2 - p3, p4 - p5
                ok = w3 != min(w1, w3, w5) and p3 > p5 and p0 > p2 and p1 > p4
            if ok:
                diff = abs(p5 - p0)
                sgn = -1.0 if d == 1 else 1.0
                sig = (-d, p5 + stop_buf * a[i] if d == 1 else p5 - stop_buf * a[i], p5 + sgn * diff * tgt_fib, diff)
        if sig is None and len(zy) >= 5:
            d = 1 if zdir == -1 else -1
            p4, p3, p2, p1, p0 = zy[0], zy[1], zy[2], zy[3], zy[4]
            if d == 1:
                w1, w3 = p1 - p0, p3 - p2
                ret = (p3 - p4) / w3 if w3 > 0 else np.nan
                ok = w3 > w1 > 0 and p2 > p0 and p4 > p1 and min_ret4 <= ret <= max_ret4
            else:
                w1, w3 = p0 - p1, p2 - p3
                ret = (p4 - p3) / w3 if w3 > 0 else np.nan
                ok = w3 > w1 > 0 and p0 > p2 and p1 > p4 and min_ret4 <= ret <= max_ret4
            if ok:
                sig = (d, p4 - stop_buf * a[i] if d == 1 else p4 + stop_buf * a[i],
                       p4 + w1 * w5_ext if d == 1 else p4 - w1 * w5_ext, w3)
        if sig is None:
            continue
        side, stop, tgt, imp = sig
        risk, reward = (c[i] - stop) * side, (tgt - c[i]) * side
        if risk > 0 and reward > 0 and reward / risk >= min_rr and imp >= min_imp * a[i]:
            e = mkt_entry(side, o[i + 1])
            if (e - stop) * side > 0 and (tgt - e) * side > 0:
                pos = Position(side, e, stop, i + 1, targets=[(tgt, None)])
    return _rows(rows)


# ============================================================ 8. MACD Pullback Sniper
def macd_sniper(b, trend_len=200, adx_min=20, sl_mult=2.0, rr=2.0):
    """Incrocio MACD/segnale; long solo sopra EMA200, con MACD sotto zero e ADX > 20 (short speculare);
    stop 2 ATR, target 2R dal prezzo d'ingresso; uscita all'incrocio opposto."""
    o, h, l, c, v, t = _arr(b)
    n = len(o)
    m, s, _ = macd(c)
    te = ema(c, trend_len)
    _, _, adx = dmi(h, l, c, 14)
    a = atr(h, l, c, 14)
    bull = (m > s) & (np.r_[False, m[:-1] <= s[:-1]])
    bear = (m < s) & (np.r_[False, m[:-1] >= s[:-1]])
    rows = []
    pos = None
    pending = None
    for i in range(n):
        if pending is not None:
            kind, side, ea = pending
            if pos is not None:
                pos.close(o[i], i)
                rows.append((t[pos.i0], pos.side, pos.r(_nights(t, pos.i0, i))))
                pos = None
            if kind == "entry":
                e = mkt_entry(side, o[i])
                pos = Position(side, e, e - side * ea * sl_mult, i, targets=[(e + side * ea * sl_mult * rr, None)])
            pending = None
        if pos is not None:
            pos.step(i, o[i], h[i], l[i], c[i])
            if pos.closed:
                rows.append((t[pos.i0], pos.side, pos.r(_nights(t, pos.i0, pos.exit_i))))
                pos = None
        if i < trend_len or i + 1 >= n:
            continue
        ls = bull[i] and c[i] > te[i] and m[i] < 0 and adx[i] > adx_min
        ss = bear[i] and c[i] < te[i] and m[i] > 0 and adx[i] > adx_min
        if ls and (pos is None or pos.side == -1):
            pending = ("entry", 1, a[i])
        elif ss and (pos is None or pos.side == 1):
            pending = ("entry", -1, a[i])
        elif pos is not None and ((pos.side == 1 and bear[i]) or (pos.side == -1 and bull[i])):
            pending = ("close", 0, 0)
    return _rows(rows)


# ============================================================ 9. QuantumForexTrader SniperFusion v2 (solo long)
def quantum_sniper(b, hist=72, conf_thr=0.54, mom_thr=0.08, decay=0.88, mem_thr=0.05, score_min=8, edge_min=2,
                   sl_mult=1.5, tsl_mult=1.5, tsl_act=0.5, min_hold=3, sniper_min=57.0, strong_diff=40.0,
                   interval_bars=1, min_move=0.30):
    """Versione fedele ma compatta: probabilità 'quantum' dalle ultime 72 variazioni pesate, memoria con
    decadimento, punteggio ibrido (trend EMA34, MTF = stesso TF con barra precedente, volume, ATR, corpo,
    VWAP giornaliero, MACD, ADX, RSI), bias 'sniper' a 7 voci. Solo long (default). Stop 1,5 ATR, 5 TP del
    20% a 1-5R, trailing 1,5 ATR dopo 0,5 ATR di profitto; uscite anticipate (EMA9, RSI, engulfing) solo dopo
    TP1 e 3 barre. Ordini alla chiusura della barra."""
    o, h, l, c, v, t = _arr(b)
    n = len(o)
    e9, e21, e34 = ema(c, 9), ema(c, 21), ema(c, 34)
    a = atr(h, l, c, 14)
    ab = sma(a, 21)
    r_ = rsi(c, 14)
    r5 = np.r_[np.nan, r_[:-1]]
    m, s, _ = macd(c)
    _, _, adx = dmi(h, l, c, 14)
    vav = sma(v, 20)
    vs24 = sma(v, 24)
    day = t.normalize().values
    tp_ = (h + l + c) / 3
    vw = np.zeros(n)
    cum_pv = cum_v = 0.0
    for i in range(n):
        if i == 0 or day[i] != day[i - 1]:
            cum_pv = cum_v = 0.0
        cum_pv += tp_[i] * v[i]
        cum_v += v[i]
        vw[i] = cum_pv / cum_v if cum_v > 0 else c[i]
    chg = np.diff(c, prepend=c[0])
    mtf_bull = np.r_[False, ((c > e34) & (e34 > np.r_[np.nan, e34[:-1]]))[:-1]]
    rows = []
    q = 0.0
    pos = None
    last_sig_i = -10 ** 9
    last_px = np.nan
    w = 1.0 + (hist - np.arange(1, hist + 1)) / hist
    for i in range(hist + 2, n):
        seg = chg[i - hist:i][::-1]          # chg[i-1] ... chg[i-hist] = close[k]-close[k+1], k = 1..hist
        up = (w * (seg > 0)).sum()
        dn = (w * (seg < 0)).sum()
        tot = up + dn
        bp, sp = (up / tot, dn / tot) if tot > 0 else (0.0, 0.0)
        tdir = 1 if bp > sp else (-1 if sp > bp else 0)
        mom = abs(bp - sp)
        conf = max(bp, sp)
        mem_in = (0.18 + mom * 0.30) * tdir
        q = max(-1.0, min(1.0, q * decay + mem_in))
        mb = 1 if q > mem_thr else (-1 if q < -mem_thr else 0)
        pref = tdir if tdir != 0 else mb
        bull = (int(c[i] > vw[i]) + int(r_[i] > 50) + int(m[i] > s[i]) + int(e9[i] > e21[i])
                + int(adx[i] > 25 and c[i] > e9[i]) + int(v[i] > vav[i] and c[i] > o[i]) + int(r5[i] > 50))
        bear = (int(c[i] < vw[i]) + int(r_[i] < 50) + int(m[i] < s[i]) + int(e9[i] < e21[i])
                + int(adx[i] > 25 and c[i] < e9[i]) + int(v[i] > vav[i] and c[i] < o[i]) + int(r5[i] < 50))
        bpct, spct = bull / 7 * 100, bear / 7 * 100
        rng = max(h[i] - l[i], 0.01)
        bull_c = c[i] > o[i] and abs(c[i] - o[i]) / rng >= 0.35
        ema_bull = c[i] > e34[i] and e34[i] > e34[i - 1]
        atr_ok = not np.isnan(ab[i]) and a[i] >= ab[i] * 0.95
        vol_ok = not np.isnan(vs24[i]) and v[i] > vs24[i]
        bear_c = c[i] < o[i] and abs(c[i] - o[i]) / rng >= 0.35
        ema_bear = c[i] < e34[i] and e34[i] < e34[i - 1]
        mtf_bear = c[i - 1] < e34[i - 1] and e34[i - 1] < e34[i - 2]
        ls = (2 * (pref == 1) + (tdir == 1) + (mb == 1) + (conf >= conf_thr) + (mom >= mom_thr) + ema_bull
              + mtf_bull[i] + vol_ok + atr_ok + bull_c + 2 * (bpct > spct) + (bpct - spct >= strong_diff)
              + (c[i] > vw[i]) + (m[i] > s[i]) + (adx[i] > 25) + (r5[i] > 50))
        ss = (2 * (pref == -1) + (tdir == -1) + (mb == -1) + (conf >= conf_thr) + (mom >= mom_thr) + ema_bear
              + mtf_bear + vol_ok + atr_ok + bear_c + 2 * (spct > bpct) + (spct - bpct >= strong_diff)
              + (c[i] < vw[i]) + (m[i] < s[i]) + (adx[i] > 25) + (r5[i] < 50))
        long_bias = (bpct > spct and bpct >= sniper_min) or (bpct - spct >= strong_diff)
        short_bias = (spct > bpct and spct >= sniper_min) or (spct - bpct >= strong_diff)
        rearm = np.isnan(last_px) or c[i] >= last_px + a[i] * min_move
        raw_long = (i - last_sig_i >= interval_bars and rearm and long_bias and ls >= score_min and ls - ss >= edge_min)
        cross = e9[i] > e21[i] and e9[i - 1] <= e21[i - 1]
        raw_long = raw_long or (cross and long_bias and c[i] > vw[i] and m[i] > s[i] and r5[i] > 50)
        raw_short = (short_bias and ss >= score_min and ss - ls >= edge_min)
        if pos is not None:
            pos.step(i, o[i], h[i], l[i], c[i])
            if not pos.closed:
                pos.hw = max(pos.hw, h[i])
                if pos.hw - pos.entry >= a[i] * tsl_act:
                    pos.stop = max(pos.stop, pos.hw - a[i] * tsl_mult)
                held = i - pos.i0 >= min_hold
                early = (c[i] < e9[i] and c[i - 1] >= e9[i - 1]) or (r_[i - 1] > 75 and r_[i] < 75) or \
                        (c[i] < o[i] and c[i - 1] > o[i - 1] and c[i] < o[i - 1] and o[i] > c[i - 1])
                if held and ((early and pos.hits >= 1) or raw_short):
                    pos.close(c[i], i)
            if pos.closed:
                rows.append((t[pos.i0], 1, pos.r(_nights(t, pos.i0, pos.exit_i))))
                pos = None
            continue
        if raw_long and not np.isnan(a[i]):
            e = c[i] + SPREAD + 0.05
            risk = a[i] * sl_mult
            pos = Position(1, e, e - risk, i, targets=[(e + risk * k, 0.2) for k in (1, 2, 3, 4)] + [(e + risk * 5, None)])
            pos.hw = h[i]
            last_sig_i, last_px = i, c[i]
    return _rows(rows)


# ============================================================ 10. Simple Harmonic Pattern
def harmonic(b, zig=4, tol=0.10, min_match=3, stop_buf=0.25, rr=2.0, cooldown=5):
    """ZigZag da pivot 4/4; XABCD con almeno 3 rapporti su 4 di Gartley / Bat / Butterfly / Crab (tolleranza 0,10);
    ingresso a mercato alla conferma del pivot D (4 barre dopo), stop oltre X di 0,25 ATR, target 2R."""
    o, h, l, c, v, t = _arr(b)
    n = len(o)
    a = atr(h, l, c, 14)
    ph, pl = pivots(h, l, zig, zig)
    pp, pdir = [], []
    rows = []
    pos = None
    last_e = -10 ** 9

    def inr(x, lo, hi):
        return lo - tol <= x <= hi + tol

    for i in range(n):
        if pos is not None:
            pos.step(i, o[i], h[i], l[i], c[i])
            if pos.closed:
                rows.append((t[pos.i0], pos.side, pos.r(_nights(t, pos.i0, pos.exit_i))))
                pos = None
        newp = False
        for val, d in ((ph[i], 1), (pl[i], -1)):
            if np.isnan(val):
                continue
            newp = True
            if pdir and pdir[-1] == d:
                if (d == 1 and val > pp[-1]) or (d == -1 and val < pp[-1]):
                    pp[-1] = val
            else:
                pp.append(val)
                pdir.append(d)
        pp, pdir = pp[-20:], pdir[-20:]
        if not newp or len(pp) < 5 or pos is not None or i + 1 >= n or i - last_e < cooldown:
            continue
        X, A, B, C, D = pp[-5:]
        bull = pdir[-1] == -1
        XA, AB, BC, CD, XD = abs(A - X), abs(B - A), abs(C - B), abs(D - C), abs(D - X)
        if XA <= 0 or AB <= 0 or BC <= 0:
            continue
        ab, bc, cd, xd = AB / XA, BC / AB, CD / BC, XD / XA
        sc = max(
            inr(ab, .618, .618) + inr(bc, .382, .886) + inr(cd, 1.13, 1.618) + inr(xd, .786, .786),
            inr(ab, .382, .5) + inr(bc, .382, .886) + inr(cd, 1.618, 2.618) + inr(xd, .886, .886),
            inr(ab, .786, .786) + inr(bc, .382, .886) + inr(cd, 1.618, 2.618) + inr(xd, 1.27, 1.618),
            inr(ab, .382, .618) + inr(bc, .382, .886) + inr(cd, 2.24, 3.618) + inr(xd, 1.618, 1.618))
        if sc < min_match:
            continue
        side = 1 if bull else -1
        stop = X - stop_buf * a[i] if bull else X + stop_buf * a[i]
        risk = abs(D - stop)
        tgt = D + side * rr * risk
        e = mkt_entry(side, o[i + 1])
        if (e - stop) * side > 0 and (tgt - e) * side > 0:
            pos = Position(side, e, stop, i + 1, targets=[(tgt, None)])
            last_e = i
    return _rows(rows)


# ============================================================ 11. Flow Algo Pro - Deep Flow Tap V3
def flow_tap(b, fast=20, slow=50, stop_pct=0.143, tgt_pct=0.31):
    """Zona tra EMA20 e EMA50; long se EMA20 > EMA50, la candela tocca la zona e chiude sopra, rialzista
    (short speculare). Stop/target fissi in punti sul NASDAQ (30 / 65 su MNQ circa 21.000 = 0,143% / 0,31%):
    sull'oro li usiamo in percentuale del prezzo. Ordini alla chiusura della barra."""
    o, h, l, c, v, t = _arr(b)
    n = len(o)
    e20, e50 = ema(c, fast), ema(c, slow)
    zh, zl = np.maximum(e20, e50), np.minimum(e20, e50)
    rows = []
    pos = None
    for i in range(slow, n):
        if pos is not None:
            pos.step(i, o[i], h[i], l[i], c[i])
            if pos.closed:
                rows.append((t[pos.i0], pos.side, pos.r(_nights(t, pos.i0, pos.exit_i))))
                pos = None
            continue
        tap = h[i] >= zl[i] and l[i] <= zh[i]
        lg = e20[i] > e50[i] and tap and c[i] > zh[i] and c[i] > o[i]
        sh = e20[i] < e50[i] and tap and c[i] < zl[i] and c[i] < o[i]
        if lg or sh:
            side = 1 if lg else -1
            e = c[i] + SPREAD + 0.05 if side == 1 else c[i] - 0.05
            pos = Position(side, e, e * (1 - side * stop_pct / 100), i, targets=[(e * (1 + side * tgt_pct / 100), None)])
    return _rows(rows)


STRATEGIES = {
    "1 Gold Breakout 15M (Willy)": (gold_breakout, ["M15", "M5"], {}),
    "1b Gold Breakout, stop sul range": (gold_breakout, ["M15"], dict(sl_mode="range")),
    "2 ICT 10AM First FVG": (ict_10am_fvg, ["M1", "M5"], {}),
    "3 Liquidity Sweep Reversal": (sweep_reversal, ["M5", "M15", "H1"], {}),
    "4 Glow Ribbon Flip": (ribbon_flip, ["M15", "H1", "H4"], {}),
    "5 Trend Analysis Strategy": (trend_analysis, ["M15", "H1", "H4"], {}),
    "6 XGBoost Mini": (xgb_mini, ["H1", "H4"], {}),
    "7 Elliott Wave Impulse": (elliott, ["M15", "H1", "H4"], {}),
    "8 MACD Pullback Sniper": (macd_sniper, ["M15", "H1", "H4"], {}),
    "9 Quantum SniperFusion (long)": (quantum_sniper, ["M5", "M15", "H1"], {}),
    "10 Harmonic Patterns": (harmonic, ["M15", "H1", "H4"], {}),
    "11 Flow Algo Deep Flow Tap": (flow_tap, ["M5", "M15"], {}),
}
