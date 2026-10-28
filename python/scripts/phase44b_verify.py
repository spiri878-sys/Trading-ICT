"""FASE 44b — verifica dei set migliori della fase 44 con il LOTTO VERO per ogni capitale (lotti come l'EA:
floor(K x M^n) in 0,01, tetto x K), simulando il conto reale (stop out al 50% del margine), ogni mese da capo.
Lotto K x 0,01 scelto con margine di sicurezza: K = floor(capitale / (1,5 x capitale minimo per 0,01)).
usage: python python/scripts/phase44b_verify.py
"""
from multiprocessing import Pool
from pathlib import Path

import numba
import numpy as np
import pandas as pd

from phase31_ticks import COMM
from phase36_entries_ticks import signals

ROOT = Path(__file__).resolve().parents[2]
CAPS = (5000.0, 10000.0, 20000.0, 50000.0, 100000.0)
SAFE = 1.5


@numba.njit(cache=True)
def sim(bid, ask, calm, trend, bal0, K, D, G, M, T, KH, R, HR, LMAX, TRS, TRD):
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
                    lots[s, 0] = K; px[s, 0] = pin; n[s] = 1; ref[s] = pin; nord += 1; best[s] = -1e9
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
            if (ref[s] - pin) * d >= dist and n[s] < 60:
                lo = np.floor(K * M ** min(n[s], 40) + 1e-9)
                if LMAX > 0 and lo > LMAX * K:
                    lo = LMAX * K
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


tab = pd.read_csv(ROOT / "output" / "phase44" / "capitale_tabella.csv")
CAND = tab[tab.peggior_mese > 0].sort_values("resa_su_capitale", ascending=False).head(40)
JOBS = []
for _, c in CAND.iterrows():
    for C in CAPS:
        K = int(C // (SAFE * c.capitale))
        if K >= 1:
            JOBS.append((int(c.cfg), C, K, c))


def run_month(m):
    fn = ROOT / "output" / "cache" / "ticks" / f"XAUUSD_ticks_2026_{m:02d}.parquet"
    sig = {k: signals(fn, 12000, k) for k in (0.0, 6.0)}
    out = []
    for cfg, C, K, c in JOBS:
        bid, ask, calm, trend = sig[c.CALM]
        r = sim(bid, ask, calm, trend, C, float(K), float(c["D"]), float(c["G"]), float(c["M"]), float(c["T"]), int(c["KH"]), float(c["R"]), float(c["HR"]), float(c["LMAX"]), float(c["TRS"]), float(c["TRD"]))
        out.append(dict(cfg=cfg, capitale=C, lotto=K / 100, mese=m, usc=-C if r[2] else round(r[0] - C), ordini=r[1]))
    print("fatto mese", m, flush=True)
    return out


def main():
    with Pool(5) as p:
        rows = [r for part in p.map(run_month, range(1, 11)) for r in part]
    df = pd.DataFrame(rows)
    df.to_csv(ROOT / "output" / "phase44" / "verifica_mesi.csv", index=False)
    piv = df.pivot_table(index=["capitale", "cfg", "lotto"], columns="mese", values="usc", aggfunc="first")
    ms = list(range(1, 11))
    piv["neg"] = (piv[ms] < 0).sum(axis=1); piv["min"] = piv[ms].min(axis=1); piv["tot"] = piv[ms].sum(axis=1)
    piv.to_csv(ROOT / "output" / "phase44" / "verifica_tabella.csv")
    pd.set_option("display.width", 300)
    for C, g in piv.groupby(level="capitale"):
        print(f"\n== capitale {C:.0f} USC")
        print(g[g.neg == 0].sort_values("tot", ascending=False).head(5).to_string())


if __name__ == "__main__":
    main()
