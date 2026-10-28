"""FASE 46 — capitale minimo VERO per 0,01 di lotto: gen -> 16 ott 2026 DI FILA, conto enorme e lotto fisso, misura il
calo più grande dal punto più alto dell'equity (più il 50% del margine, livello di stop out) = capitale che serve
partendo in QUALUNQUE momento. Corregge la fase 44 (che misurava dall'inizio di ogni mese).
Set provati: i 380 della fase 44 con tutti i mesi positivi + bot 1.61 + set costante.
usage: python python/scripts/phase46_true_capital.py
"""
from multiprocessing import Pool
from pathlib import Path

import numba
import numpy as np
import pandas as pd

from phase31_ticks import COMM
from phase45_ladder import load

ROOT = Path(__file__).resolve().parents[2]
BIG = 1e12


@numba.njit(cache=True)
def sim(bid, ask, calm, trend, month, D, G, M, T, KH, R, HR, LMAX, TRS, TRD, mon_eq):
    bal = BIG; need = 0.0; peak = BIG; nord = 0
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
                    lots[s, 0] = 1.0; px[s, 0] = pin; n[s] = 1; ref[s] = pin; best[s] = -1e9; nord += 1
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
                lots[s, k] = lo; px[s, k] = pin; n[s] += 1; ref[s] = pin; nord += 1
                L += lo; W += lo * pin; avg = W / L
                if KH > 0 and n[s] >= KH:
                    hl[s] = max(1.0, np.round(HR * L)); hp[s] = b if d > 0 else a; hx[s] = pout
            flo += (pout - avg) * d * L
            marg += L * b / 1000.0
        eq = bal + flo
        mon_eq[month[i]] = eq
        if eq > peak:
            peak = eq
        u = peak - eq + 0.5 * marg
        if u > need:
            need = u
    return eq - BIG, need, nord


tab = pd.read_csv(ROOT / "output" / "phase44" / "capitale_tabella.csv")
CAND = pd.concat([tab[tab.peggior_mese > 0], tab[tab.cfg.isin([0, 1])]]).drop_duplicates("cfg")
DATA = None


def init():
    global DATA
    DATA = load()


def one(row):
    bid, ask, c6, c0, tr, month = DATA
    calm = c6 if row["CALM"] > 0 else c0
    me = np.zeros(13)
    p, need, no = sim(bid, ask, calm, tr, month, float(row["D"]), float(row["G"]), float(row["M"]), float(row["T"]),
                      int(row["KH"]), float(row["R"]), float(row["HR"]), float(row["LMAX"]), float(row["TRS"]),
                      float(row["TRD"]), me)
    prev = 1e12; mesi = []
    for m in range(1, 11):
        mesi.append(round(me[m] - prev)); prev = me[m]
    return dict(cfg=int(row["cfg"]), profitto=round(p), capitale_vero=round(need), ordini=no,
                **{f"m{m}": mesi[m - 1] for m in range(1, 11)})


def main():
    rows = [r for _, r in CAND.iterrows()]
    with Pool(3, initializer=init) as p:
        res = p.map(one, rows, chunksize=4)
    df = pd.DataFrame(res).merge(tab[["cfg", "D", "G", "M", "T", "KH", "R", "HR", "LMAX", "TRS", "TRD", "CALM"]], on="cfg")
    df["resa_su_capitale"] = df.profitto / df.capitale_vero
    out = ROOT / "output" / "phase46"
    out.mkdir(parents=True, exist_ok=True)
    df.to_csv(out / "capitale_vero.csv", index=False)
    pd.set_option("display.width", 300)
    print(df.sort_values("resa_su_capitale", ascending=False).head(20).to_string(index=False))
    print(df[df.cfg.isin([0, 1, 503, 1726, 1830])].to_string(index=False))


if __name__ == "__main__":
    main()
