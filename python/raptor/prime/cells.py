"""Le 6 celle ICT della PRIME (ricostruzione, Fase 2). Regole e fonti: output/regole.md §1-2, §9.

Ogni funzione riceve le feature causali di `raptor.setups.build_features(m1, tf, k)` (riga i = barra chiusa i;
HTF uniti sull'orario di disponibilità) e restituisce un DataFrame standard di segnali:

  bar_i, bar_time (apertura della barra del segnale; il segnale è noto alla sua CHIUSURA = bar_time + tf),
  cell, tf, side (+1/-1), otype ('limit'|'market'), price, sl_struct, atr, expiry_bars,
  leg_lo, leg_hi (gamba di riferimento, per Fibonacci/Premium), zone_lo, zone_hi, reason

Nessun esito viene calcolato qui (Fase 3). I parametri di default sono la definizione ICT standard; le
alternative si scelgono in validazione (2018-2021), mai sul test.
"""
import numpy as np
import pandas as pd

TF_OF = {"PPK": "5min", "OTEOF": "12min", "PO3": "5min", "UNIOF": "15min", "LS": "3min", "BB": "15min"}

DEFAULTS = {
    "PPK": dict(k=3, min_disp=1.2, min_fvg=0.15, rearm_bars=24, max_entries=3, sl_buf_atr=0.2, expiry=12,
                min_r_atr=0.5, max_r_atr=15.0, entry_edge="proximal", stop_mode="struct", stop_atr_tf="m15",
                stop_atr_mult=3.0, need_bos=True),
    "OTEOF": dict(k=3, sweep_bars=12, ote_lo=0.62, ote_hi=0.79, ote_level=0.705, need_fvg=True, min_fvg=0.1,
                  sl_buf_atr=0.2, expiry=20, min_r_atr=0.5, max_r_atr=15.0),
    "PO3": dict(k=3, raid_bars=24, min_disp=1.0, min_fvg=0.1, sessions=[(120, 660)], sl_buf_atr=0.2, expiry=12,
                min_r_atr=0.5, max_r_atr=15.0),
    "UNIOF": dict(k=3, sweep_bars=12, min_fvg=0.1, sl_buf_atr=0.2, expiry=12, min_r_atr=0.5, max_r_atr=15.0,
                  entry_edge="proximal", stop_mode="struct", stop_atr_tf="m15", stop_atr_mult=3.0, need_sweep=True),
    "LS": dict(k=3, min_body=0.8, entry="market", sl_buf_atr=0.2, expiry=6, min_r_atr=0.5, max_r_atr=15.0),
    "BB": dict(k=3, min_disp=1.0, sl_buf_atr=0.2, expiry=24, min_r_atr=0.5, max_r_atr=15.0),
}


# --------------------------------------------------------------------------- helpers
def _out(f, cell, mask, side, price, sl, expiry, otype="limit", leg_lo=None, leg_hi=None, zlo=None, zhi=None,
         reason=""):
    idx = np.flatnonzero(mask)
    pick = lambda x: np.full(idx.size, np.nan) if x is None else np.asarray(x, float)[idx]  # noqa: E731
    return pd.DataFrame({
        "bar_i": idx, "bar_time": f.index[idx], "cell": cell, "tf": f.attrs.get("tf", ""),
        "side": np.asarray(side)[idx].astype(int), "otype": otype,
        "price": np.asarray(price, float)[idx], "sl_struct": np.asarray(sl, float)[idx],
        "atr": f.atr.values[idx], "atr_m15": (f.m15_atr.values[idx] if "m15_atr" in f else np.nan),
        "expiry_bars": expiry,
        "leg_lo": pick(leg_lo), "leg_hi": pick(leg_hi), "zone_lo": pick(zlo), "zone_hi": pick(zhi),
        "reason": reason})


def _edge(up, top_up, bot_up, top_dn, bot_dn, how):
    """Prezzo d'ingresso nella zona: bordo prossimale, 50% (CE) o distale."""
    w = {"proximal": 0.0, "ce": 0.5, "distal": 1.0}[how]
    return np.where(up, top_up - w * (top_up - bot_up), bot_dn + w * (top_dn - bot_dn))


def _atr_stop(f, side, price, sl_struct, p):
    """stop_mode 'struct' = stop strutturale della cella; 'atr' = ingresso -/+ stop_atr_mult x ATR(14) del TF
    stop_atr_tf (ultima barra CHIUSA, es. m15). Trade di riferimento 08/01/2026: 21 $ = 2,98 x ATR M15."""
    if p.get("stop_mode", "struct") == "struct":
        return sl_struct
    a = f[f"{p['stop_atr_tf']}_atr"].values if p["stop_atr_tf"] != "tf" else f.atr.values
    return np.asarray(price) - np.asarray(side) * p["stop_atr_mult"] * a


def _risk_ok(f, side, price, sl, p):
    a = f.atr.values
    with np.errstate(invalid="ignore"):
        r = (np.asarray(price) - np.asarray(sl)) * np.asarray(side)
        return (r >= p["min_r_atr"] * a) & (r <= p["max_r_atr"] * a)


def _window(f, windows):
    m = np.zeros(len(f), bool)
    for a, b in windows:
        m |= (f.ny_min.values >= a) & (f.ny_min.values < b)
    return m


def _prev(x):
    return np.r_[np.nan, np.asarray(x, float)[:-1]]


def liquidity_sweeps(f):
    """Sweep di liquidità alla chiusura della barra i (causale):
    * lato basso: il minimo supera PDL / minimo asiatico (prima violazione del giorno, da setups) oppure
      l'ultimo swing low confermato, e la CHIUSURA torna sopra il livello;
    * lato alto simmetrico. Restituisce (sweep_lo, sweep_hi, livello_lo, livello_hi)."""
    l, h, c = f.low.values, f.high.values, f.close.values
    psl, psh = _prev(f.swing_lo.values), _prev(f.swing_hi.values)
    with np.errstate(invalid="ignore"):
        sw_swing_lo = (l < psl) & (c > psl)
        sw_swing_hi = (h > psh) & (c < psh)
        pdl, pdh, al, ah = f.pdl.values, f.pdh.values, f.asia_lo.values, f.asia_hi.values
        day_lo = f.sweep_lo.values & (((l < pdl) & (c > pdl)) | ((l < al) & (c > al)))
        day_hi = f.sweep_hi.values & (((h > pdh) & (c < pdh)) | ((h > ah) & (c < ah)))
    lo = sw_swing_lo | day_lo
    hi = sw_swing_hi | day_hi
    lvl_lo = np.where(day_lo, np.where((l < pdl) & (c > pdl), pdl, al), np.where(sw_swing_lo, psl, np.nan))
    lvl_hi = np.where(day_hi, np.where((h > pdh) & (c < pdh), pdh, ah), np.where(sw_swing_hi, psh, np.nan))
    return lo, hi, lvl_lo, lvl_hi


def _recent(flag, n):
    """flag vero in una delle ultime n barre (inclusa la corrente)."""
    return pd.Series(np.asarray(flag, float)).rolling(n, min_periods=1).max().values > 0


def _fvg_now(f, min_fvg):
    a = f.atr.values
    bt, bb, st, sb = (f[k].values for k in ("fvg_bull_top", "fvg_bull_bot", "fvg_bear_top", "fvg_bear_bot"))
    with np.errstate(invalid="ignore"):
        up = np.isfinite(bt) & ((bt - bb) >= min_fvg * a)
        dn = np.isfinite(st) & ((st - sb) >= min_fvg * a)
    return up, dn, bt, bb, st, sb


def _fvg_recent(f, min_fvg, n=2):
    """FVG nella direzione, formato in una delle ultime n barre (bordi dell'FVG più recente)."""
    up, dn, bt, bb, st, sb = _fvg_now(f, min_fvg)
    s = lambda x, m: pd.Series(np.where(m, x, np.nan)).ffill(limit=n - 1).values  # noqa: E731
    return (np.isfinite(s(bt, up)), np.isfinite(s(st, dn)), s(bt, up), s(bb, up), s(st, dn), s(sb, dn))


# --------------------------------------------------------------------------- cells
def ppk(f, p):
    """Raptor Mode / PPK (M5). BOS con displacement che lascia un FVG; limit sul bordo prossimale dell'FVG.
    Ri-armo: dopo il BOS, ogni nuovo FVG di continuazione con displacement (barra centrale dell'FVG con corpo
    >= min_disp ATR) entro rearm_bars barre e finché il trend non si inverte genera un nuovo ingresso, fino a
    max_entries per gamba ("tre ingressi in sequenza sullo stesso movimento", sito). Stop oltre l'origine della
    gamba del BOS."""
    a = f.atr.values
    n = len(f)
    brk = f.brk.values
    body_mid = _prev(np.abs(f.close.values - f.open.values))  # candela centrale del pattern FVG (i-1)
    up_fvg, dn_fvg, bt, bb, st, sb = _fvg_now(f, p["min_fvg"])
    with np.errstate(invalid="ignore"):
        disp = body_mid >= p["min_disp"] * a
    trend = np.zeros(n, np.int8); since = np.full(n, 10 ** 9); origin = np.full(n, np.nan)
    cnt = np.zeros(n, np.int16)
    t, s_, o_, c_ = 0, 10 ** 9, np.nan, 0
    leg_lo, leg_hi = f.leg_lo.values, f.leg_hi.values
    for i in range(n):
        if brk[i] != 0:
            if brk[i] != t:
                c_ = 0
            t, s_ = brk[i], 0
            o_ = leg_lo[i] if brk[i] == 1 else leg_hi[i]
        else:
            s_ += 1
        trend[i], since[i], origin[i], cnt[i] = t, s_, o_, c_
        if p.get("need_bos", True):
            fire = (t == 1 and up_fvg[i] and disp[i]) or (t == -1 and dn_fvg[i] and disp[i])
            if fire and s_ <= p["rearm_bars"] and c_ < p["max_entries"]:
                c_ += 1
                cnt[i] = -c_  # marca il segnale (numero d'ingresso nella gamba)
        elif (up_fvg[i] or dn_fvg[i]) and disp[i]:
            # variante "solo spostamento": ogni FVG con displacement, direzione = FVG, origine = minimo/massimo
            # delle 3 barre del pattern
            trend[i] = 1 if up_fvg[i] else -1
            origin[i] = min(f.low.values[i - 2:i + 1]) if up_fvg[i] else max(f.high.values[i - 2:i + 1])
            cnt[i] = -1
    sig = cnt < 0
    up = sig & (trend == 1)
    dn = sig & (trend == -1)
    buf = p["sl_buf_atr"] * a
    side = np.where(up, 1, -1)
    price = _edge(up, bt, bb, st, sb, p["entry_edge"])
    sl = _atr_stop(f, side, price, np.where(up, origin - buf, origin + buf), p)
    m = (up | dn) & _risk_ok(f, side, price, sl, p) if p["stop_mode"] == "struct" else (up | dn) & np.isfinite(sl)
    zlo = np.where(up, bb, sb); zhi = np.where(up, bt, st)
    out = _out(f, "PPK", m, side, price, sl, p["expiry"], leg_lo=np.where(up, origin, f.low.values),
               leg_hi=np.where(up, f.high.values, origin), zlo=zlo, zhi=zhi, reason="BOS+disp+FVG")
    out["entry_n"] = -cnt[np.flatnonzero(m)]
    return out


def oteof(f, p):
    """OTE Order Flow (M12). Sweep di liquidità nelle ultime sweep_bars barre, poi MSS nella direzione opposta
    allo sweep; limit al livello OTE (default 70,5%) della gamba sweep -> rottura (zona 62-79%); conferma di
    order flow = FVG nella gamba (opzionale). Stop oltre l'estremo dello sweep."""
    a = f.atr.values
    sw_lo, sw_hi, _, _ = liquidity_sweeps(f)
    n = p["sweep_bars"]
    raid_lo, raid_hi = _recent(sw_lo, n), _recent(sw_hi, n)
    ext_lo = pd.Series(f.low.values).rolling(n, min_periods=1).min().values
    ext_hi = pd.Series(f.high.values).rolling(n, min_periods=1).max().values
    mss = f.is_mss.values
    up = (f.brk.values == 1) & mss & raid_lo
    dn = (f.brk.values == -1) & mss & raid_hi
    if p["need_fvg"]:
        fu, fd, *_ = _fvg_recent(f, p["min_fvg"], n=3)
        up &= fu; dn &= fd
    hi_leg = f.leg_hi.values; lo_leg = f.leg_lo.values
    lo_leg = np.where(up, np.minimum(lo_leg, ext_lo), lo_leg)
    hi_leg = np.where(dn, np.maximum(hi_leg, ext_hi), hi_leg)
    lv = p["ote_level"]
    side = np.where(up, 1, -1)
    price = np.where(up, hi_leg - lv * (hi_leg - lo_leg), lo_leg + lv * (hi_leg - lo_leg))
    buf = p["sl_buf_atr"] * a
    sl = np.where(up, lo_leg - buf, hi_leg + buf)
    zlo = np.where(up, hi_leg - p["ote_hi"] * (hi_leg - lo_leg), lo_leg + p["ote_lo"] * (hi_leg - lo_leg))
    zhi = np.where(up, hi_leg - p["ote_lo"] * (hi_leg - lo_leg), lo_leg + p["ote_hi"] * (hi_leg - lo_leg))
    m = (up | dn) & _risk_ok(f, side, price, sl, p)
    return _out(f, "OTEOF", m, side, price, sl, p["expiry"], leg_lo=lo_leg, leg_hi=hi_leg, zlo=zlo, zhi=zhi,
                reason="sweep+MSS+OTE")


def po3(f, p):
    """Power of Three (M5). Accumulazione = range asiatico (server 03-07); manipolazione = prima violazione
    di un lato del range (sweep) nelle ultime raid_bars barre, nella finestra Londra/NY; distribuzione = MSS
    nella direzione opposta con displacement e FVG. Limit sul bordo dell'FVG; stop oltre la manipolazione."""
    a = f.atr.values
    n = p["raid_bars"]
    raid_hi = _recent(f.sweep_asia_hi.values, n)
    raid_lo = _recent(f.sweep_asia_lo.values, n)
    fu, fd, bt, bb, st, sb = _fvg_recent(f, p["min_fvg"], n=2)
    with np.errstate(invalid="ignore"):
        disp = f.disp_body.values >= p["min_disp"] * a
    mss = f.is_mss.values
    up = (f.brk.values == 1) & mss & raid_lo & fu & disp
    dn = (f.brk.values == -1) & mss & raid_hi & fd & disp
    s = _window(f, p["sessions"])
    up &= s; dn &= s
    ext_lo = pd.Series(f.low.values).rolling(n, min_periods=1).min().values
    ext_hi = pd.Series(f.high.values).rolling(n, min_periods=1).max().values
    buf = p["sl_buf_atr"] * a
    side = np.where(up, 1, -1)
    price = np.where(up, bt, sb)
    sl = np.where(up, ext_lo - buf, ext_hi + buf)
    m = (up | dn) & _risk_ok(f, side, price, sl, p)
    return _out(f, "PO3", m, side, price, sl, p["expiry"], leg_lo=np.where(up, ext_lo, f.leg_lo.values),
                leg_hi=np.where(up, f.leg_hi.values, ext_hi), zlo=np.where(up, bb, sb), zhi=np.where(up, bt, st),
                reason="asia+raid+MSS")


def uniof(f, p):
    """Unicorn (M15). Sweep di liquidità, poi MSS; il breaker generato dalla rottura (ultima candela opposta
    sullo swing rotto) si sovrappone a un FVG non mitigato nella direzione della rottura. Limit sul bordo
    prossimale della sovrapposizione; stop oltre lo sweep/gamba."""
    a = f.atr.values
    sw_lo, sw_hi, _, _ = liquidity_sweeps(f)
    n = p["sweep_bars"]
    raid_lo, raid_hi = _recent(sw_lo, n), _recent(sw_hi, n)
    fu, fd, bt, bb, st, sb = _fvg_recent(f, p["min_fvg"], n=3)
    zlo, zhi = f.brk_zlo.values, f.brk_zhi.values
    with np.errstate(invalid="ignore"):
        ou_hi, ou_lo = np.minimum(bt, zhi), np.maximum(bb, zlo)
        od_hi, od_lo = np.minimum(st, zhi), np.maximum(sb, zlo)
        if not p.get("need_sweep", True):
            raid_lo = raid_hi = np.ones(len(f), bool)
        up = (f.brk.values == 1) & f.is_mss.values & raid_lo & fu & (ou_hi > ou_lo)
        dn = (f.brk.values == -1) & f.is_mss.values & raid_hi & fd & (od_hi > od_lo)
    ext_lo = pd.Series(f.low.values).rolling(n, min_periods=1).min().values
    ext_hi = pd.Series(f.high.values).rolling(n, min_periods=1).max().values
    lo_leg = np.minimum(f.leg_lo.values, ext_lo); hi_leg = np.maximum(f.leg_hi.values, ext_hi)
    buf = p["sl_buf_atr"] * a
    side = np.where(up, 1, -1)
    price = _edge(up, ou_hi, ou_lo, od_hi, od_lo, p["entry_edge"])
    sl = _atr_stop(f, side, price, np.where(up, lo_leg - buf, hi_leg + buf), p)
    m = (up | dn) & _risk_ok(f, side, price, sl, p) if p["stop_mode"] == "struct" else (up | dn) & np.isfinite(sl)
    return _out(f, "UNIOF", m, side, price, sl, p["expiry"], leg_lo=lo_leg, leg_hi=hi_leg,
                zlo=np.where(up, ou_lo, od_lo), zhi=np.where(up, ou_hi, od_hi), reason="sweep+MSS+breaker∩FVG")


def ls(f, p):
    """Liquidity Sweep (M3). Sweep di PDH/PDL, range asiatico o ultimo swing confermato con chiusura di
    rientro "forte" (corpo >= min_body ATR nella direzione del rientro). Ingresso a mercato alla chiusura
    (default) o limit al livello spazzato; stop appena oltre l'estremo dello sweep."""
    a = f.atr.values
    o, c, h, l = f.open.values, f.close.values, f.high.values, f.low.values
    sw_lo, sw_hi, lvl_lo, lvl_hi = liquidity_sweeps(f)
    with np.errstate(invalid="ignore"):
        strong_up = (c - o) >= p["min_body"] * a
        strong_dn = (o - c) >= p["min_body"] * a
    up = sw_lo & strong_up
    dn = sw_hi & strong_dn & ~up
    buf = p["sl_buf_atr"] * a
    side = np.where(up, 1, -1)
    if p["entry"] == "market":
        price, otype = c, "market"
    else:
        price, otype = np.where(up, lvl_lo, lvl_hi), "limit"
    sl = np.where(up, l - buf, h + buf)
    m = (up | dn) & _risk_ok(f, side, price, sl, p)
    return _out(f, "LS", m, side, price, sl, p["expiry"], otype=otype, leg_lo=l, leg_hi=h,
                zlo=np.where(up, lvl_lo, c), zhi=np.where(up, c, lvl_hi), reason="sweep+rientro")


def bb(f, p):
    """Breaker Block (TF da scegliere; default M15). Alla rottura di struttura che cambia direzione (MSS) con
    displacement, l'ultima candela opposta sullo swing rotto è un order block fallito: la zona "cambia segno"
    (sito). Limit sul ritorno al bordo prossimale del breaker; stop oltre il bordo distale (o la gamba)."""
    a = f.atr.values
    zlo, zhi = f.brk_zlo.values, f.brk_zhi.values
    with np.errstate(invalid="ignore"):
        disp = f.disp_body.values >= p["min_disp"] * a
        ok = np.isfinite(zlo) & np.isfinite(zhi) & (zhi > zlo)
    up = (f.brk.values == 1) & f.is_mss.values & disp & ok
    dn = (f.brk.values == -1) & f.is_mss.values & disp & ok
    buf = p["sl_buf_atr"] * a
    side = np.where(up, 1, -1)
    price = np.where(up, zhi, zlo)
    sl = np.where(up, np.minimum(zlo, f.leg_lo.values) - buf, np.maximum(zhi, f.leg_hi.values) + buf)
    m = (up | dn) & _risk_ok(f, side, price, sl, p)
    return _out(f, "BB", m, side, price, sl, p["expiry"], leg_lo=f.leg_lo.values, leg_hi=f.leg_hi.values,
                zlo=zlo, zhi=zhi, reason="MSS+breaker")


CELLS = {"PPK": ppk, "OTEOF": oteof, "PO3": po3, "UNIOF": uniof, "LS": ls, "BB": bb}


def generate(feats_by_tf: dict, cells=None, params=None, degraded=None, fri_close_hour=22) -> pd.DataFrame:
    """feats_by_tf: {tf: features}. params: {cell: overrides}. Filtri comuni: niente segnali nei giorni
    degradati (Fase 0) e niente segnali dopo fri_close_hour del venerdì (ora server)."""
    out = []
    for cell in cells or CELLS:
        p = {**DEFAULTS[cell], **(params or {}).get(cell, {})}
        tf = p.get("tf", TF_OF[cell])
        f = feats_by_tf[(tf, p["k"])]
        f.attrs["tf"] = tf
        s = CELLS[cell](f, p)
        s["tf"] = tf
        s["known_at"] = s.bar_time + pd.Timedelta(tf)
        out.append(s)
    s = pd.concat(out, ignore_index=True)
    if degraded is not None and len(s):
        s = s[~s.bar_time.dt.normalize().isin(degraded)]
    if len(s):
        late_fri = (s.known_at.dt.dayofweek == 4) & (s.known_at.dt.hour >= fri_close_hour)
        s = s[~late_fri]
    return s.sort_values(["known_at", "cell"]).reset_index(drop=True)


def fill_times(sig: pd.DataFrame, m1: pd.DataFrame) -> pd.Series:
    """Primo minuto M1 (dopo known_at, entro expiry_bars x TF) in cui il limit viene toccato sul BID
    (buy: low <= prezzo; sell: high >= prezzo); i market si riempiono alla prima barra disponibile.
    Serve al confronto con i riferimenti del venditore, i cui orari sono quelli del tocco/ingresso."""
    from numba import njit

    @njit(cache=True)
    def _ft(lo, hi, i0, i1, side, price, mkt):
        out = np.full(i0.size, -1)
        for k in range(i0.size):
            if mkt[k]:
                out[k] = i0[k]
                continue
            for i in range(i0[k], min(i1[k], lo.size)):
                if (side[k] == 1 and lo[i] <= price[k]) or (side[k] == -1 and hi[i] >= price[k]):
                    out[k] = i
                    break
        return out

    idx = m1.index.values
    i0 = np.searchsorted(idx, sig.known_at.values.astype("datetime64[ns]"))
    dur = (sig.expiry_bars.values * pd.to_timedelta(sig.tf).values).astype("timedelta64[ns]")
    i1 = np.searchsorted(idx, (sig.known_at.values + dur).astype("datetime64[ns]"))
    fi = _ft(m1.low.values, m1.high.values, i0.astype(np.int64), i1.astype(np.int64), sig.side.values.astype(np.int64),
             sig.price.values.astype(float), (sig.otype.values == "market"))
    t = pd.Series(pd.NaT, index=sig.index, dtype="datetime64[ns]")
    ok = fi >= 0
    t[ok] = idx[fi[ok]]
    return t
