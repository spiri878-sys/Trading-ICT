"""FASE 37 — cesto HFT con hedging "intelligente", TICK PER TICK, ogni mese da 5.000 USC. Obiettivo: nessun mese in
perdita. Novità rispetto alla fase 32:
  SMART: quando la copertura si toglie, il suo guadagno chiude gli ordini più vecchi del cesto (quelli più in perdita)
         finché basta: il cesto si rimpicciolisce invece di crescere a ogni giro;
  LMAX : tetto al lotto di un livello (in 0,01): la martingala raddoppia fino a LMAX e poi aggiunge sempre LMAX.
Entrata come l'EA 1.40 (lato della tendenza EMA200 H1, nessun filtro strappi).
usage: python python/scripts/phase37_smart_hedge.py
"""
import itertools
from multiprocessing import Pool
from pathlib import Path

import numba
import numpy as np
import pandas as pd

from phase31_ticks import COMM, DEP
from phase36_entries_ticks import signals

ROOT = Path(__file__).resolve().parents[2]


@numba.njit(cache=True)
def sim(bid, ask, calm, trend, bal0, D, G, M, T, KH, R, LMAX, SMART):
    bal = bal0; peak = bal0; mdd = 0.0; nord = 0; nb = 0
    lots = np.zeros((2, 200)); px = np.zeros((2, 200)); n = np.zeros(2, np.int64); lev = np.zeros(2, np.int64)
    ref = np.zeros(2); hl = np.zeros(2); hp = np.zeros(2); hx = np.zeros(2)
    eq = bal0
    for i in range(bid.size):
        b = bid[i]; a = ask[i]
        flo = 0.0; marg = 0.0
        for s in range(2):
            d = 1.0 if s == 0 else -1.0
            pin = a if d > 0 else b
            pout = b if d > 0 else a
            if n[s] == 0:
                if calm[i] and ((d > 0 and trend[i]) or (d < 0 and not trend[i])):
                    lots[s, 0] = 1.0; px[s, 0] = pin; n[s] = 1; lev[s] = 1; ref[s] = pin; nord += 1
                continue
            L = 0.0; W = 0.0
            for k in range(n[s]):
                L += lots[s, k]; W += lots[s, k] * px[s, k]
            avg = W / L
            if hl[s] > 0:
                if (pout - hx[s]) * d < 0:
                    hx[s] = pout
                hexit = a if d > 0 else b
                if (pout - hx[s]) * d >= R:
                    gain = (hp[s] - hexit) * d * hl[s] - COMM * hl[s]
                    if SMART and gain > 0:
                        # il guadagno della copertura chiude gli ordini più vecchi finché basta
                        while n[s] > 1:
                            loss0 = (pout - px[s, 0]) * d * lots[s, 0] - COMM * lots[s, 0]
                            if loss0 >= 0 or -loss0 > gain:
                                break
                            gain += loss0
                            bal += loss0
                            for k in range(n[s] - 1):
                                lots[s, k] = lots[s, k + 1]; px[s, k] = px[s, k + 1]
                            n[s] -= 1
                        bal += (hp[s] - hexit) * d * hl[s] - COMM * hl[s]
                    else:
                        bal += gain
                    hl[s] = 0.0; ref[s] = pin
                else:
                    flo += (pout - avg) * d * L + (hp[s] - hexit) * d * hl[s]
                    marg += max(L, hl[s]) * b / 1000.0
                    continue
                L = 0.0; W = 0.0
                for k in range(n[s]):
                    L += lots[s, k]; W += lots[s, k] * px[s, k]
                avg = W / L
            if (pout - avg) * d >= T:
                bal += (pout - avg) * d * L - COMM * L; n[s] = 0; nb += 1
                continue
            dist = D * G ** min(lev[s] - 1, 30)
            if (ref[s] - pin) * d >= dist and n[s] < 199:
                lo = np.floor(M ** min(lev[s], 40) + 1e-9)
                if LMAX > 0 and lo > LMAX:
                    lo = LMAX
                k = n[s]
                lots[s, k] = lo; px[s, k] = pin; n[s] += 1; lev[s] += 1; nord += 1; ref[s] = pin
                L += lo; W += lo * pin; avg = W / L
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


GRID = list(itertools.product((6.0, 8.0, 10.0), (1.3,), (1.5, 2.0), (0.7,), (3, 4, 5), (5.0, 8.0), (0.0, 8.0, 16.0),
                              (0, 1)))


def run_month(m):
    fn = ROOT / "output" / "cache" / "ticks" / f"XAUUSD_ticks_2026_{m:02d}.parquet"
    bid, ask, calm, trend = signals(fn, 12000, 0.0)
    out = []
    for D, G, M, T, KH, R, LMAX, SMART in GRID:
        r = sim(bid, ask, calm, trend, DEP, D, G, M, T, KH, R, LMAX, SMART)
        out.append(dict(mese=m, D=D, G=G, M=M, TP=T, copri=KH, R=R, lmax=LMAX, smart=SMART, saltato=bool(r[4]),
                        eur=-50 if r[4] else round((r[0] - DEP) / 100), calo=round(r[1] * 100), ordini=r[2]))
    print("fatto mese", m, flush=True)
    return out


def main():
    with Pool(5) as p:
        rows = [r for part in p.map(run_month, range(1, 11)) for r in part]
    df = pd.DataFrame(rows)
    out = ROOT / "output" / "phase37"
    out.mkdir(parents=True, exist_ok=True)
    df.to_csv(out / "smart_hedge.csv", index=False)
    key = ["D", "G", "M", "TP", "copri", "R", "lmax", "smart"]
    piv = df.pivot_table(index=key, columns="mese", values="eur", aggfunc="first")
    piv["totale"] = piv.sum(axis=1)
    piv["mesi_neg"] = (piv[list(range(1, 11))] < 0).sum(axis=1)
    piv["peggio"] = piv[list(range(1, 11))].min(axis=1)
    piv.to_csv(out / "smart_hedge_tabella.csv")
    pd.set_option("display.width", 250)
    print(piv.sort_values(["mesi_neg", "totale"], ascending=[True, False]).head(25).to_string())


if __name__ == "__main__":
    main()
