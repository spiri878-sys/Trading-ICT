"""FASE 42 — ricerca casuale larga, TICK PER TICK, ogni mese da 5.000 USC. Spazio: distanza 3-15 $, crescita x1,0-1,5,
lotto x1,3-2,5, TP 0,3-3 $, TRAILING del cesto (parte a TRS $ sul medio, chiude se torna indietro di TRD $; 0 = spento),
copertura al livello 2-6 o assente, quota di copertura 0,5-1,3, via dopo R $, tetto al lotto, filtro strappi on/off.
usage: python python/scripts/phase42_random_ticks.py
"""
from multiprocessing import Pool
from pathlib import Path

import numba
import numpy as np
import pandas as pd

from phase31_ticks import COMM, DEP
from phase36_entries_ticks import signals

ROOT = Path(__file__).resolve().parents[2]


@numba.njit(cache=True)
def sim(bid, ask, calm, trend, bal0, D, G, M, T, KH, R, HR, LMAX, TRS, TRD):
    bal = bal0; nord = 0
    lots = np.zeros((2, 200)); px = np.zeros((2, 200)); n = np.zeros(2, np.int64)
    ref = np.zeros(2); hl = np.zeros(2); hp = np.zeros(2); hx = np.zeros(2); best = np.zeros(2)
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
                    lots[s, 0] = 1.0; px[s, 0] = pin; n[s] = 1; ref[s] = pin; nord += 1; best[s] = -1e9
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
                    hl[s] = 0.0; ref[s] = pin
                else:
                    flo += (pout - avg) * d * L + (hp[s] - hexit) * d * hl[s]
                    marg += max(L, hl[s]) * b / 1000.0
                    continue
            g = (pout - avg) * d
            if g > best[s]:
                best[s] = g
            close = g >= T
            if TRS > 0 and best[s] >= TRS and g <= best[s] - TRD and g > 0:
                close = True
            if close:
                bal += g * L - COMM * L; n[s] = 0
                continue
            dist = D * G ** min(n[s] - 1, 30)
            if (ref[s] - pin) * d >= dist and n[s] < 199:
                lo = np.floor(M ** min(n[s], 40) + 1e-9)
                if LMAX > 0 and lo > LMAX:
                    lo = LMAX
                k = n[s]
                lots[s, k] = lo; px[s, k] = pin; n[s] += 1; nord += 1; ref[s] = pin
                L += lo; W += lo * pin; avg = W / L
                if KH > 0 and n[s] >= KH:
                    hl[s] = max(1.0, np.round(HR * L)); hp[s] = b if d > 0 else a; hx[s] = pout; nord += 1
            flo += (pout - avg) * d * L
            marg += L * b / 1000.0
        eq = bal + flo
        if marg > 0 and eq < 0.5 * marg:
            return eq, nord, 1
    return eq, nord, 0


def configs(n=1500, seed=42):
    rng = np.random.default_rng(seed)
    out = []
    for _ in range(n):
        T = float(rng.choice([0.3, 0.5, 0.7, 1.0, 1.5, 2.0, 3.0]))
        trs = float(rng.choice([0.0, 0.0, 0.5, 1.0, 2.0]))
        out.append(dict(D=float(rng.choice([3, 4, 5, 6, 8, 10, 12, 15])), G=float(rng.choice([1.0, 1.1, 1.2, 1.3, 1.4, 1.5])),
                        M=float(rng.choice([1.3, 1.5, 1.8, 2.0, 2.2, 2.5])), T=max(T, trs + 0.5) if trs else T,
                        KH=int(rng.choice([0, 2, 3, 4, 5, 6])), R=float(rng.choice([3, 5, 8, 12])),
                        HR=float(rng.choice([0.5, 0.7, 1.0, 1.3])), LMAX=float(rng.choice([0, 8, 16, 32, 64])),
                        TRS=trs, TRD=float(rng.choice([0.2, 0.3, 0.5])), CALM=float(rng.choice([0.0, 6.0]))))
    return out


CFG = configs()


def run_month(m):
    fn = ROOT / "output" / "cache" / "ticks" / f"XAUUSD_ticks_2026_{m:02d}.parquet"
    sig = {k: signals(fn, 12000, k) for k in (0.0, 6.0)}
    out = []
    for j, c in enumerate(CFG):
        bid, ask, calm, trend = sig[c["CALM"]]
        r = sim(bid, ask, calm, trend, DEP, c["D"], c["G"], c["M"], c["T"], c["KH"], c["R"], c["HR"], c["LMAX"],
                c["TRS"], c["TRD"])
        out.append(dict(cfg=j, mese=m, usc=-5000 if r[2] else round(r[0] - DEP), ordini=r[1]))
    print("fatto mese", m, flush=True)
    return out


def main():
    with Pool(5) as p:
        rows = [r for part in p.map(run_month, range(1, 11)) for r in part]
    df = pd.DataFrame(rows)
    out = ROOT / "output" / "phase42"
    out.mkdir(parents=True, exist_ok=True)
    df.to_csv(out / "casuale_mesi.csv", index=False)
    piv = df.pivot_table(index="cfg", columns="mese", values="usc", aggfunc="first")
    ms = list(range(1, 11))
    piv["neg"] = (piv[ms] < 0).sum(axis=1); piv["min"] = piv[ms].min(axis=1); piv["tot"] = piv[ms].sum(axis=1)
    piv = piv.join(pd.DataFrame(CFG))
    piv.to_csv(out / "casuale_tabella.csv")
    pd.set_option("display.width", 300)
    print(piv.neg.value_counts().sort_index().head(4))
    print(piv.sort_values(["neg", "tot"], ascending=[True, False]).head(15).to_string())


if __name__ == "__main__":
    main()
