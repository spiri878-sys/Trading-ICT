"""FASE 25 — cesto martingala: quali ENTRATE fanno meno drawdown (barre M1 Axi 2026 dell'utente).
Griglia fissa come il set dell'utente da 50 livelli: distanza 2 $ x1,1, lotto 0,01 x1,5, max 50 livelli, TP del cesto
2 $ oltre il prezzo medio, nessuno stop, H24. Un cesto BUY e uno SELL; un cesto nuovo si apre solo con il segnale.
Unità: $ per 0,01 lotti (= centesimi su un conto cent con lotto 0,01). Deposito 100.000 come il tester dell'utente.
Stop out del broker: equity sotto il 50% del margine (leva 1:1000). Nella barra M1 prima il movimento contrario.

usage: python python/scripts/phase25_basket_entries.py
"""
from pathlib import Path

import numba
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
D, GROW, MULT, NMAX, TP, BAL0 = 2.0, 1.1, 1.5, 50, 2.0, 100000.0


@numba.njit(cache=True)
def sim(op, hi, lo, cl, sp, buy, sell, bal0, D=D, GROW=GROW, TP=TP):
    bal = bal0
    peak = bal0
    mdd = 0.0
    maxlev = 0
    nb = 0
    dead = 0
    lots = np.zeros((2, 64)); px = np.zeros((2, 64)); n = np.zeros(2, np.int64)
    nxt = np.zeros(2); dist = np.zeros(2)
    eqs = np.zeros(hi.size)
    for i in range(1, hi.size):
        flo = 0.0
        marg = 0.0
        for s in range(2):
            d = 1.0 if s == 0 else -1.0
            if n[s] == 0:
                sig = buy[i - 1] if s == 0 else sell[i - 1]          # segnale sulla barra chiusa, entra all'apertura
                if not sig:
                    continue
                p0 = op[i] + (sp[i] if d > 0 else 0.0)
                lots[s, 0] = 1.0; px[s, 0] = p0; n[s] = 1; dist[s] = D; nxt[s] = p0 - d * D
            added = False
            while n[s] < NMAX and ((d > 0 and lo[i] <= nxt[s]) or (d < 0 and hi[i] + sp[i] >= nxt[s])):
                k = n[s]
                lots[s, k] = lots[s, k - 1] * MULT; px[s, k] = nxt[s]; n[s] += 1; added = True
                dist[s] *= GROW; nxt[s] = nxt[s] - d * dist[s]
            L = 0.0; W = 0.0
            for k in range(n[s]):
                L += lots[s, k]; W += lots[s, k] * px[s, k]
            avg = W / L
            if n[s] > maxlev:
                maxlev = n[s]
            worst = (lo[i] - avg) * L if d > 0 else (avg - (hi[i] + sp[i])) * L
            if added:
                hit = (d > 0 and cl[i] >= avg + TP) or (d < 0 and cl[i] + sp[i] <= avg - TP)
            else:
                hit = (d > 0 and hi[i] >= avg + TP) or (d < 0 and lo[i] + sp[i] <= avg - TP)
            if hit:
                bal += TP * L - 0.04 * L; n[s] = 0; nb += 1
                continue
            flo += min(worst, 0.0)
            marg += L * cl[i] * 100.0 / 1000.0 / 100.0           # margine di L x 0,01 lotti con leva 1:1000
        eq = bal + flo
        eqs[i] = eq
        if eq > peak:
            peak = eq
        if (peak - eq) / peak > mdd:
            mdd = (peak - eq) / peak
        if marg > 0 and eq < 0.5 * marg:                          # stop out
            return eq, 1.0, maxlev, nb, 1, eqs
    return bal, mdd, maxlev, nb, 0, eqs


def ema(x, span):
    return pd.Series(x).ewm(span=span, adjust=False).mean().values


def main():
    m = pd.read_parquet(ROOT / "output" / "cache" / "XAUUSD_M1_axi_2026.parquet")
    op, hi, lo, cl = (m[c].values.astype(float) for c in ("open", "high", "low", "close"))
    sp = m.spread.values * 0.01
    s = pd.Series(cl)
    # segnali M1 (le 5 entrate dell'EA)
    l5, h5 = pd.Series(lo), pd.Series(hi)
    frac_b = (l5.shift(2) < l5.shift(1)) & (l5.shift(2) < l5) & (l5.shift(2) < l5.shift(3)) & (l5.shift(2) < l5.shift(4))
    frac_s = (h5.shift(2) > h5.shift(1)) & (h5.shift(2) > h5) & (h5.shift(2) > h5.shift(3)) & (h5.shift(2) > h5.shift(4))
    dlt = s.diff()
    rs = dlt.clip(lower=0).ewm(alpha=1 / 14, adjust=False).mean() / (-dlt.clip(upper=0)).ewm(alpha=1 / 14, adjust=False).mean()
    rsi = 100 - 100 / (1 + rs)
    rsi_b, rsi_s = (rsi.shift(1) < 30) & (rsi >= 30), (rsi.shift(1) > 70) & (rsi <= 70)
    ma, sd = s.rolling(20).mean(), s.rolling(20).std(ddof=0)
    bb_b = (s.shift(1) < (ma - 2 * sd).shift(1)) & (s > ma - 2 * sd)
    bb_s = (s.shift(1) > (ma + 2 * sd).shift(1)) & (s < ma + 2 * sd)
    ll, hh = l5.rolling(14).min(), h5.rolling(14).max()
    k = (100 * (s - ll) / (hh - ll)).rolling(3).mean(); dd_ = k.rolling(3).mean()
    st_b = (k.shift(1) <= dd_.shift(1)) & (k > dd_) & (dd_ < 20)
    st_s = (k.shift(1) >= dd_.shift(1)) & (k < dd_) & (dd_ > 80)
    op_s = pd.Series(op)
    rv_b = (l5 == l5.rolling(20).min()) & (s > op_s)
    rv_s = (h5 == h5.rolling(20).max()) & (s < op_s)
    sigs = {"sempre": (pd.Series(True, index=s.index),) * 2, "S1 frattale": (frac_b, frac_s), "S2 RSI": (rsi_b, rsi_s),
            "S3 Bollinger": (bb_b, bb_s), "S4 stocastico": (st_b, st_s), "S5 inversione": (rv_b, rv_s)}
    # filtri di entrata (NON fermano il bot: scelgono solo il momento/lato del primo ordine)
    tr = s.values > ema(cl, 3000)                                 # tendenza ~ EMA 50 H1
    tr_slow = s.values > ema(cl, 12000)                           # tendenza ~ EMA 200 H1
    atr = (h5 - l5).rolling(14).mean()
    calm = ((h5.rolling(15).max() - l5.rolling(15).min()) < 4 * atr).values   # niente entrate subito dopo uno strappo
    stretch = (s - s.ewm(span=240, adjust=False).mean()) / atr        # quanto è tirato il prezzo (in ATR M1)
    filt = {"nessun filtro": (np.ones_like(tr), np.ones_like(tr)),
            "con la tendenza EMA50 H1": (tr, ~tr), "con la tendenza EMA200 H1": (tr_slow, ~tr_slow),
            "dopo calma": (calm, calm), "prezzo tirato >= 3 ATR": ((stretch <= -3).values, (stretch >= 3).values),
            "tendenza EMA200 + calma": (tr_slow & calm, ~tr_slow & calm)}
    rows, curves = [], {}
    for sn, (b, se) in sigs.items():
        for fn, (fb, fs) in filt.items():
            bb = (b.fillna(False).values & fb).astype(np.bool_)
            ss = (se.fillna(False).values & fs).astype(np.bool_)
            bal, mdd, lev, nb, dead, eqs = sim(op, hi, lo, cl, sp, bb, ss, BAL0)
            rows.append(dict(entrata=sn, filtro=fn, saldo_finale=round(bal), profitto_pct=round((bal / BAL0 - 1) * 100, 1),
                             calo_max_pct=round(mdd * 100, 1), livello_max=lev, cesti=nb, saltato=bool(dead)))
            curves[(sn, fn)] = eqs
    df = pd.DataFrame(rows)
    out = ROOT / "output" / "phase25"
    out.mkdir(parents=True, exist_ok=True)
    df.to_csv(out / "entrate.csv", index=False)
    pd.set_option("display.width", 200)
    print(df.sort_values(["saltato", "calo_max_pct"]).to_string(index=False))
    return df, curves, m.index


if __name__ == "__main__":
    main()
