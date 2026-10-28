"""FASE 44 — per ogni set: guadagno per 0,01 di lotto e CAPITALE MINIMO per 0,01 che non brucia mai (tick per tick,
gen-ott 2026). Con lotto fisso le operazioni non dipendono dal saldo: si simula con un conto enorme e si registra, per
ogni mese, il punto più basso di (equity - 50% del margine) rispetto all'inizio del mese = capitale che serve.
Poi con un capitale C: lotto = floor(C / capitale minimo) x 0,01 e guadagno = lotto x guadagno per 0,01.
usage: python python/scripts/phase44_capital_needed.py
"""
from multiprocessing import Pool
from pathlib import Path

import numba
import numpy as np
import pandas as pd

from phase31_ticks import COMM
from phase36_entries_ticks import signals

ROOT = Path(__file__).resolve().parents[2]
BIG = 1e12


@numba.njit(cache=True)
def sim(bid, ask, calm, trend, D, G, M, T, KH, R, HR, LMAX, TRS, TRD):
    bal = BIG; nord = 0; need = 0.0
    lots = np.zeros((2, 200)); px = np.zeros((2, 200)); n = np.zeros(2, np.int64)
    ref = np.zeros(2); hl = np.zeros(2); hp = np.zeros(2); hx = np.zeros(2); best = np.zeros(2)
    eq = BIG
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
            if (ref[s] - pin) * d >= dist and n[s] < 60:
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
        u = BIG - (eq - 0.5 * marg)
        if u > need:
            need = u
    return eq - BIG, need, nord


def configs(n=2000, seed=7):
    rng = np.random.default_rng(seed)
    out = [dict(D=8.0, G=1.3, M=2.0, T=0.7, KH=4, R=8.0, HR=0.7, LMAX=0.0, TRS=0.0, TRD=0.2, CALM=0.0),    # bot 1.61
           dict(D=10.0, G=1.2, M=1.5, T=0.5, KH=4, R=8.0, HR=1.0, LMAX=0.0, TRS=0.0, TRD=0.2, CALM=6.0),   # costante
           dict(D=4.0, G=1.2, M=2.0, T=1.0, KH=6, R=8.0, HR=1.0, LMAX=0.0, TRS=0.0, TRD=0.2, CALM=6.0)]    # aggressivo
    for _ in range(n):
        T = float(rng.choice([0.3, 0.5, 0.7, 1.0, 1.5, 2.0, 3.0]))
        trs = float(rng.choice([0.0, 0.0, 0.0, 0.5, 1.0, 2.0]))
        out.append(dict(D=float(rng.choice([2, 3, 4, 5, 6, 8, 10, 12, 15, 20])),
                        G=float(rng.choice([1.0, 1.1, 1.2, 1.3, 1.4, 1.5])),
                        M=float(rng.choice([1.0, 1.2, 1.3, 1.5, 1.8, 2.0, 2.5])), T=max(T, trs + 0.5) if trs else T,
                        KH=int(rng.choice([0, 0, 2, 3, 4, 5, 6])), R=float(rng.choice([3, 5, 8, 12])),
                        HR=float(rng.choice([0.5, 0.7, 1.0, 1.3])), LMAX=float(rng.choice([0, 0, 4, 8, 16, 32, 64])),
                        TRS=trs, TRD=float(rng.choice([0.2, 0.3, 0.5])), CALM=float(rng.choice([0.0, 6.0]))))
    return out


CFG = configs()


def run_month(m):
    fn = ROOT / "output" / "cache" / "ticks" / f"XAUUSD_ticks_2026_{m:02d}.parquet"
    sig = {k: signals(fn, 12000, k) for k in (0.0, 6.0)}
    out = []
    for j, c in enumerate(CFG):
        bid, ask, calm, trend = sig[c["CALM"]]
        p, need, no = sim(bid, ask, calm, trend, c["D"], c["G"], c["M"], c["T"], c["KH"], c["R"], c["HR"], c["LMAX"],
                          c["TRS"], c["TRD"])
        out.append(dict(cfg=j, mese=m, profitto=p, capitale=need, ordini=no))
    print("fatto mese", m, flush=True)
    return out


def main():
    with Pool(5) as p:
        rows = [r for part in p.map(run_month, range(1, 11)) for r in part]
    df = pd.DataFrame(rows)
    out = ROOT / "output" / "phase44"
    out.mkdir(parents=True, exist_ok=True)
    df.to_csv(out / "capitale_mesi.csv", index=False)
    g = df.groupby("cfg").agg(profitto=("profitto", "sum"), peggior_mese=("profitto", "min"), capitale=("capitale", "max"),
                              ordini=("ordini", "mean"))
    g = g.join(pd.DataFrame(CFG))
    g["resa_su_capitale"] = g.profitto / g.capitale
    g.to_csv(out / "capitale_tabella.csv")
    pd.set_option("display.width", 300)
    ok = g[g.peggior_mese > 0]
    print("set con tutti i mesi positivi:", len(ok), "su", len(g))
    print(ok.sort_values("resa_su_capitale", ascending=False).head(20).to_string())
    print(g.loc[[0, 1, 2]].to_string())


if __name__ == "__main__":
    main()
