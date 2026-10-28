"""FASE 46c — capitale minimo dal punto più alto con i LOTTI VERI dell'EA (floor(K x M^n), tetto x K), mese per mese,
per i set migliori della fase 46b e lotti K = 1..15. usage: python python/scripts/phase46c_scale_check.py
"""
from multiprocessing import Pool
from pathlib import Path

import numba
import numpy as np
import pandas as pd

from phase31_ticks import COMM
from phase36_entries_ticks import signals

ROOT = Path(__file__).resolve().parents[2]
SETS = {255: (15.0, 1.0, 1.2, 0.5, 4, 5.0, 0.7, 64.0, 0.0, 0.5, 0.0),
        1: (10.0, 1.2, 1.5, 0.5, 4, 8.0, 1.0, 0.0, 0.0, 0.2, 6.0),
        1830: (20.0, 1.0, 1.3, 1.5, 6, 8.0, 1.0, 16.0, 0.0, 0.2, 6.0),
        900: (8.0, 1.1, 1.3, 2.5, 5, 3.0, 0.7, 0.0, 2.0, 0.5, 6.0),
        1108: (3.0, 1.4, 1.8, 0.5, 5, 3.0, 1.0, 32.0, 0.0, 0.2, 0.0),
        0: (8.0, 1.3, 2.0, 0.7, 4, 8.0, 0.7, 0.0, 0.0, 0.2, 0.0)}
KS = (1, 2, 3, 4, 6, 8, 10, 12, 15)


@numba.njit(cache=True)
def sim(bid, ask, calm, trend, K, D, G, M, T, KH, R, HR, LMAX, TRS, TRD):
    bal = 0.0; need = 0.0; peak = 0.0
    lots = np.zeros((2, 200)); px = np.zeros((2, 200)); n = np.zeros(2, np.int64)
    ref = np.zeros(2); hl = np.zeros(2); hp = np.zeros(2); hx = np.zeros(2); best = np.zeros(2)
    eq = 0.0
    for i in range(bid.size):
        b = bid[i]; a = ask[i]
        flo = 0.0; marg = 0.0
        for s in range(2):
            d = 1.0 if s == 0 else -1.0
            pin = a if d > 0 else b
            pout = b if d > 0 else a
            if n[s] == 0:
                if calm[i] and ((d > 0 and trend[i]) or (d < 0 and not trend[i])):
                    lots[s, 0] = K; px[s, 0] = pin; n[s] = 1; ref[s] = pin; best[s] = -1e9
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
                lots[s, k] = lo; px[s, k] = pin; n[s] += 1; ref[s] = pin
                L += lo; W += lo * pin; avg = W / L
                if KH > 0 and n[s] >= KH:
                    hl[s] = max(1.0, np.round(HR * L)); hp[s] = b if d > 0 else a; hx[s] = pout
            flo += (pout - avg) * d * L
            marg += L * b / 1000.0
        eq = bal + flo
        if eq > peak:
            peak = eq
        u = peak - eq + 0.5 * marg
        if u > need:
            need = u
    return eq, need


def run_month(m):
    fn = ROOT / "output" / "cache" / "ticks" / f"XAUUSD_ticks_2026_{m:02d}.parquet"
    sig = {k: signals(fn, 12000, k) for k in (0.0, 6.0)}
    out = []
    for cfg, p in SETS.items():
        bid, ask, calm, trend = sig[p[10]]
        for K in KS:
            pr, need = sim(bid, ask, calm, trend, float(K), *p[:10])
            out.append(dict(cfg=cfg, K=K, mese=m, profitto=round(pr), capitale=round(need)))
    return out


def main():
    with Pool(5) as p:
        rows = [x for part in p.map(run_month, range(1, 11)) for x in part]
    df = pd.DataFrame(rows)
    out = ROOT / "output" / "phase46"
    df.to_csv(out / "scala_lotti_mesi.csv", index=False)
    g = df.groupby(["cfg", "K"]).agg(profitto=("profitto", "sum"), peggior=("profitto", "min"), capitale=("capitale", "max")).reset_index()
    g.to_csv(out / "scala_lotti.csv", index=False)
    pd.set_option("display.width", 250)
    for C in (5000, 10000, 20000, 50000, 100000):
        ok = g[g.capitale * 1.5 <= C].sort_values("profitto", ascending=False).head(3)
        print(f"\n== {C} USC (con margine 1,5)\n", ok.to_string(index=False))
        ok2 = g[g.capitale <= C].sort_values("profitto", ascending=False).head(2)
        print(" senza margine:\n", ok2.to_string(index=False))


if __name__ == "__main__":
    main()
