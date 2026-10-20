"""FASE 43 — varianti con ordini STOP, TICK PER TICK, ogni mese da 5.000 USC.
  ENTRATA: 0 = a mercato dal lato della tendenza (come l'EA); E > 0 = breakout: quando il cesto è vuoto si fissa un
           prezzo di riferimento; BUY STOP a +E $ e SELL STOP a -E $ (ognuno apre il suo cesto)
  B      : media con conferma: un livello si aggiunge solo quando il prezzo è andato contro di almeno la distanza E POI
           rimbalza di B $ dal punto peggiore (buy stop / sell stop); 0 = media subito come prima
Hedging come l'EA 1.61 (copertura al livello KH, quota HR, via dopo R $).
usage: python python/scripts/phase43_stop_orders.py
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
def sim(bid, ask, calm, trend, bal0, D, G, M, T, KH, R, HR, E, B):
    bal = bal0; nord = 0
    lots = np.zeros((2, 200)); px = np.zeros((2, 200)); n = np.zeros(2, np.int64)
    ref = np.zeros(2); hl = np.zeros(2); hp = np.zeros(2); hx = np.zeros(2)
    anchor = np.zeros(2); low = np.zeros(2)
    eq = bal0
    for i in range(bid.size):
        b = bid[i]; a = ask[i]
        flo = 0.0; marg = 0.0
        for s in range(2):
            d = 1.0 if s == 0 else -1.0
            pin = a if d > 0 else b
            pout = b if d > 0 else a
            if n[s] == 0:
                if E > 0:
                    if anchor[s] == 0.0:
                        anchor[s] = pin
                    go = (pin - anchor[s]) * d >= E
                else:
                    go = calm[i] and ((d > 0 and trend[i]) or (d < 0 and not trend[i]))
                if go:
                    lots[s, 0] = 1.0; px[s, 0] = pin; n[s] = 1; ref[s] = pin; nord += 1; low[s] = pin; anchor[s] = 0.0
                continue
            L = 0.0; W = 0.0
            for k in range(n[s]):
                L += lots[s, k]; W += lots[s, k] * px[s, k]
            avg = W / L
            hexit = a if d > 0 else b
            if hl[s] > 0:
                if (pout - hx[s]) * d < 0:
                    hx[s] = pout
                if (pout - hx[s]) * d >= R:
                    bal += (hp[s] - hexit) * d * hl[s] - COMM * hl[s]
                    hl[s] = 0.0; ref[s] = pin; low[s] = pin
                else:
                    flo += (pout - avg) * d * L + (hp[s] - hexit) * d * hl[s]
                    marg += max(L, hl[s]) * b / 1000.0
                    continue
            if (pout - avg) * d >= T:
                bal += (pout - avg) * d * L - COMM * L; n[s] = 0
                continue
            if (pin - low[s]) * d < 0:
                low[s] = pin                                    # punto peggiore dall'ultimo livello
            dist = D * G ** min(n[s] - 1, 30)
            far = (ref[s] - low[s]) * d >= dist
            ok = far and ((B <= 0 and (ref[s] - pin) * d >= dist) or (B > 0 and (pin - low[s]) * d >= B))
            if ok and n[s] < 199:
                k = n[s]
                lots[s, k] = np.floor(M ** min(k, 40) + 1e-9); px[s, k] = pin; n[s] += 1; nord += 1
                ref[s] = pin; low[s] = pin
                L += lots[s, k]; W += lots[s, k] * pin; avg = W / L
                if KH > 0 and n[s] >= KH:
                    hl[s] = max(1.0, np.round(HR * L)); hp[s] = b if d > 0 else a; hx[s] = pout; nord += 1
            flo += (pout - avg) * d * L
            marg += L * b / 1000.0
        eq = bal + flo
        if marg > 0 and eq < 0.5 * marg:
            return eq, nord, 1
    return eq, nord, 0


GRID = list(itertools.product((5.0, 8.0), (1.5, 2.0), (0, 4, 5), (0.0, 1.0, 2.0), (0.0, 0.5, 1.0, 2.0, 3.0)))


def run_month(m):
    fn = ROOT / "output" / "cache" / "ticks" / f"XAUUSD_ticks_2026_{m:02d}.parquet"
    bid, ask, calm, trend = signals(fn, 12000, 0.0)
    out = []
    for D, M, KH, E, B in GRID:
        r = sim(bid, ask, calm, trend, DEP, D, 1.3, M, 0.7, KH, 8.0, 0.7, E, B)
        out.append(dict(mese=m, D=D, M=M, copri=KH, entrata_stop=E, media_conferma=B,
                        usc=-5000 if r[2] else round(r[0] - DEP), ordini=r[1]))
    print("fatto mese", m, flush=True)
    return out


def main():
    with Pool(5) as p:
        rows = [r for part in p.map(run_month, range(1, 11)) for r in part]
    df = pd.DataFrame(rows)
    out = ROOT / "output" / "phase43"
    out.mkdir(parents=True, exist_ok=True)
    df.to_csv(out / "stop_mesi.csv", index=False)
    key = ["D", "M", "copri", "entrata_stop", "media_conferma"]
    piv = df.pivot_table(index=key, columns="mese", values="usc", aggfunc="first")
    ms = list(range(1, 11))
    piv["neg"] = (piv[ms] < 0).sum(axis=1); piv["tot"] = piv[ms].sum(axis=1)
    piv.to_csv(out / "stop_tabella.csv")
    pd.set_option("display.width", 300)
    print(piv.neg.value_counts().sort_index().head(4))
    print(piv.sort_values(["neg", "tot"], ascending=[True, False]).head(20).to_string())


if __name__ == "__main__":
    main()
