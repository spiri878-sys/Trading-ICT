"""FASE 31 — prove TICK PER TICK (tick reali Dukascopy, spread fisso Axi 0,09 $) sul conto 5.000 USC.
Bot provati (stessa logica degli EA):
  cesto  : CestoTopBottom con hedging (tendenza EMA200 H1 + niente strappi, distanza D x G, lotto x M, TP T,
           copertura al livello KH, tolta dopo un rimbalzo di R);
  zona   : ZonaRecupero (zona Z, uscita T, NMAX posizioni);
  piramide: aggiunge ogni D a favore (lotto x M, max N), chiude con trailing R dal massimo.
Unità: $ per 0,01 lotti (= centesimi sul conto cent). Stop out al 50% del margine (leva 1:1000).
usage: python python/scripts/phase31_ticks.py
"""
import itertools
import sys
from pathlib import Path

import numba
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
SPREAD = 0.09
COMM = 0.04
DEP = 5000.0


def load_month(fn):
    t = pd.read_parquet(fn)
    t = t[(t.bid > 0)].reset_index(drop=True)
    bid = t.bid.values.astype(np.float64)
    ask = bid + SPREAD
    minute = t.time.values.astype("datetime64[m]")
    # candele M1 dal bid per i segnali (tendenza EMA200 H1 ~ EMA 12.000 M1, strappo 15 barre > 6 ATR14)
    s = pd.Series(bid, index=pd.DatetimeIndex(minute))
    o = s.groupby(level=0).agg(["first", "max", "min", "last"])
    o.columns = ["open", "high", "low", "close"]
    rng = o.high - o.low
    atr = rng.rolling(14).mean()
    ema = o.close.ewm(span=12000, adjust=False).mean()
    calm = (o.high.rolling(15).max() - o.low.rolling(15).min()) < 6 * atr
    trend = o.close > ema
    # segnale della barra chiusa valido per i tick della barra dopo
    bar_idx = np.searchsorted(o.index.values, minute) - 1
    ok = bar_idx >= 0
    calm_t = np.zeros(len(bid), np.bool_); trend_t = np.zeros(len(bid), np.bool_)
    calm_t[ok] = calm.values[bar_idx[ok]]; trend_t[ok] = trend.values[bar_idx[ok]]
    return bid, ask, calm_t, trend_t


@numba.njit(cache=True)
def tick_zone(bid, ask, go, startbuy, bal0, Z, T, NMAX):
    bal = bal0; peak = bal0; mdd = 0.0; nord = 0; nseq = 0
    lb = 0.0; ls = 0.0; wb = 0.0; ws = 0.0; n = 0; last = 0; top = 0.0; bot = 0.0
    eq = bal0
    for i in range(bid.size):
        b = bid[i]; a = ask[i]
        if n == 0:
            if go[i]:
                if startbuy[i]:
                    lb = 1.0; wb = a; top = a; bot = a - Z; last = 1
                else:
                    ls = 1.0; ws = b; bot = b; top = b + Z; last = -1
                n = 1; nord += 1
            continue
        up = top + T; dn = bot - T
        if b >= up or a <= dn:
            pb = (b - wb / lb) * lb if lb > 0 else 0.0
            ps = (ws / ls - a) * ls if ls > 0 else 0.0
            bal += pb + ps - COMM * (lb + ls); nseq += 1
            lb = 0.0; ls = 0.0; wb = 0.0; ws = 0.0; n = 0
            eq = bal
            if eq > peak:
                peak = eq
            continue
        if n < NMAX:
            if last == 1 and b <= bot:
                need = T + lb * (wb / lb - dn) - (ls * (ws / ls - dn) if ls > 0 else 0.0)
                x = max(1.0, np.ceil(need / T - 1e-9))
                ls += x; ws += x * b; last = -1; n += 1; nord += 1
            elif last == -1 and a >= top:
                need = T + ls * (up - ws / ls) - (lb * (up - wb / lb) if lb > 0 else 0.0)
                x = max(1.0, np.ceil(need / T - 1e-9))
                lb += x; wb += x * a; last = 1; n += 1; nord += 1
        pb = (b - wb / lb) * lb if lb > 0 else 0.0
        ps = (ws / ls - a) * ls if ls > 0 else 0.0
        eq = bal + pb + ps
        if eq > peak:
            peak = eq
        if (peak - eq) / peak > mdd:
            mdd = (peak - eq) / peak
        marg = max(lb, ls) * b / 1000.0
        if eq < 0.5 * marg:
            return eq, 1.0, nord, nseq, 1
    return eq, mdd, nord, nseq, 0


@numba.njit(cache=True)
def tick_basket(bid, ask, calm, trend, bal0, D, G, M, T, KH, R):
    bal = bal0; peak = bal0; mdd = 0.0; nord = 0; nb = 0
    lots = np.zeros((2, 80)); px = np.zeros((2, 80)); n = np.zeros(2, np.int64)
    ref = np.zeros(2); hl = np.zeros(2); hp = np.zeros(2); hx = np.zeros(2)
    eq = bal0
    for i in range(bid.size):
        b = bid[i]; a = ask[i]
        flo = 0.0; marg = 0.0
        for s in range(2):
            d = 1.0 if s == 0 else -1.0
            pin = a if d > 0 else b                      # prezzo di entrata del lato
            pout = b if d > 0 else a                     # prezzo di uscita del lato
            if n[s] == 0:
                if calm[i] and ((d > 0 and trend[i]) or (d < 0 and not trend[i])):
                    lots[s, 0] = 1.0; px[s, 0] = pin; n[s] = 1; ref[s] = pin; nord += 1
                continue
            L = 0.0; W = 0.0
            for k in range(n[s]):
                L += lots[s, k]; W += lots[s, k] * px[s, k]
            avg = W / L
            if hl[s] > 0:                                 # copertura attiva: cesto fermo
                if (pout - hx[s]) * d < 0:
                    hx[s] = pout
                if (pout - hx[s]) * d >= R:               # rimbalzo: toglie la copertura
                    hexit = a if d > 0 else b             # la copertura è del lato opposto
                    bal += (hp[s] - hexit) * d * hl[s] - COMM * hl[s]
                    hl[s] = 0.0; ref[s] = pin
                else:
                    hexit = a if d > 0 else b
                    flo += (pout - avg) * d * L + (hp[s] - hexit) * d * hl[s]
                    marg += max(L, hl[s]) * b / 1000.0
                    continue
            if (pout - avg) * d >= T:                     # TP del cesto
                bal += (pout - avg) * d * L - COMM * L; n[s] = 0; nb += 1
                continue
            dist = D * G ** (n[s] - 1)
            if (ref[s] - pin) * d >= dist and n[s] < 79:  # nuovo livello
                k = n[s]
                lots[s, k] = max(1.0, np.floor(M ** k + 1e-9)); px[s, k] = pin; n[s] += 1; nord += 1; ref[s] = pin
                L += lots[s, k]; W += lots[s, k] * pin; avg = W / L
                if KH > 0 and n[s] >= KH:
                    hl[s] = L; hp[s] = b if d > 0 else a; hx[s] = pout; nord += 1
            flo += (pout - avg) * d * L
            marg += L * b / 1000.0
        eq = bal + flo
        if eq > peak:
            peak = eq
        if (peak - eq) / peak > mdd:
            mdd = (peak - eq) / peak
        if marg > 0 and eq < 0.5 * marg:
            return eq, 1.0, nord, nb, 1
    return eq, mdd, nord, nb, 0


@numba.njit(cache=True)
def tick_pyramid(bid, ask, calm, trend, both, bal0, D, M, R, NMAX):
    bal = bal0; peak = bal0; mdd = 0.0; nord = 0; nb = 0
    lots = np.zeros((2, 64)); px = np.zeros((2, 64)); n = np.zeros(2, np.int64); nxt = np.zeros(2); ext = np.zeros(2)
    eq = bal0
    for i in range(bid.size):
        b = bid[i]; a = ask[i]
        flo = 0.0; marg = 0.0
        for s in range(2):
            d = 1.0 if s == 0 else -1.0
            pin = a if d > 0 else b
            pout = b if d > 0 else a
            if n[s] == 0:
                if calm[i] and (both or (d > 0 and trend[i]) or (d < 0 and not trend[i])):
                    lots[s, 0] = 1.0; px[s, 0] = pin; n[s] = 1; nord += 1; nxt[s] = pin + d * D; ext[s] = pout
                continue
            if (pout - ext[s]) * d > 0:
                ext[s] = pout
            L = 0.0; W = 0.0
            for k in range(n[s]):
                L += lots[s, k]; W += lots[s, k] * px[s, k]
            if (ext[s] - pout) * d >= R:
                bal += (pout - W / L) * d * L - COMM * L; n[s] = 0; nb += 1
                continue
            if n[s] < NMAX and (pin - nxt[s]) * d >= 0:
                k = n[s]
                lots[s, k] = max(1.0, np.floor(M ** k + 1e-9)); px[s, k] = pin; n[s] += 1; nord += 1
                L += lots[s, k]; W += lots[s, k] * pin
                nxt[s] = pin + d * D
            flo += (pout - W / L) * d * L
            marg += L * b / 1000.0
        eq = bal + flo
        if eq > peak:
            peak = eq
        if (peak - eq) / peak > mdd:
            mdd = (peak - eq) / peak
        if marg > 0 and eq < 0.5 * marg:
            return eq, 1.0, nord, nb, 1
    return eq, mdd, nord, nb, 0


def fmt(r):
    return "BRUCIATO" if r[4] else f"{(r[0] / DEP - 1) * 100:+.0f}% (calo {r[1] * 100:.0f}%, {r[2]} ordini)"


def main(months):
    data = {mo: load_month(ROOT / "output" / "cache" / "ticks" / f"XAUUSD_ticks_2026_{mo:02d}.parquet") for mo in months}
    rows = []
    for mo, (bid, ask, calm, trend) in data.items():
        print(f"mese {mo}: {bid.size:,} tick")
        ones = np.ones(bid.size, np.bool_)
        for Z, T, N in itertools.product((0.5, 1.0, 2.0, 3.0), (2.0, 5.0, 8.0, 12.0), (4, 6, 8, 12)):
            for st, sb in (("BUY", ones), ("tendenza", trend)):
                r = tick_zone(bid, ask, calm, sb, DEP, Z, T, N)
                rows.append(dict(mese=mo, bot="zona", impostazioni=f"Z{Z} T{T} max{N} {st}", saltato=bool(r[4]),
                                 resa=round((r[0] / DEP - 1) * 100), calo=round(r[1] * 100), ordini=r[2]))
        for D, G, M, T, KH, R in itertools.product((3.0, 5.0, 8.0), (1.2, 1.3), (1.3, 1.5), (0.5, 1.0, 2.0), (0, 4, 5, 6),
                                                   (3.0, 5.0)):
            r = tick_basket(bid, ask, calm, trend, DEP, D, G, M, T, KH, R)
            rows.append(dict(mese=mo, bot="cesto", impostazioni=f"D{D} G{G} M{M} TP{T} copri{KH} R{R}", saltato=bool(r[4]),
                             resa=round((r[0] / DEP - 1) * 100), calo=round(r[1] * 100), ordini=r[2]))
        for D, M, R, N, both in itertools.product((0.5, 1.0, 2.0, 3.0), (1.0, 1.5), (1.0, 2.0, 3.0, 5.0), (5, 10, 20), (False, True)):
            r = tick_pyramid(bid, ask, calm, trend, both, DEP, D, M, R, N)
            rows.append(dict(mese=mo, bot="piramide", impostazioni=f"D{D} M{M} R{R} max{N} {'BUY+SELL' if both else 'tendenza'}",
                             saltato=bool(r[4]), resa=round((r[0] / DEP - 1) * 100), calo=round(r[1] * 100), ordini=r[2]))
    df = pd.DataFrame(rows)
    out = ROOT / "output" / "phase31"
    out.mkdir(parents=True, exist_ok=True)
    df.to_csv(out / "tick_prove.csv", index=False)
    w = df.pivot_table(index=["bot", "impostazioni"], columns="mese", values=["resa", "calo", "ordini"], aggfunc="first")
    w.columns = [f"{a}_{b}" for a, b in w.columns]
    w = w.reset_index()
    rc = [c for c in w.columns if c.startswith("resa_")]
    w["min_resa"] = w[rc].min(axis=1); w["somma"] = w[rc].sum(axis=1)
    w.to_csv(out / "tick_tabella.csv", index=False)
    pd.set_option("display.width", 250)
    for bot, g in w.groupby("bot"):
        print(f"\n== {bot}: migliori per il mese peggiore (resa -100 = bruciato o quasi)")
        print(g.sort_values(["min_resa", "somma"], ascending=False).head(10).to_string(index=False))


if __name__ == "__main__":
    main([int(x) for x in sys.argv[1:]] or [1, 6])
