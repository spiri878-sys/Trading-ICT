"""FASE 38 — varianti di HEDGING sul cesto HFT (8 $ x1,3, lotto x2, TP 0,7 $), TICK PER TICK, ogni mese da 5.000 USC.
  HR : copertura = HR x lotti del cesto (0,7 parziale, 1 piena, 1,3 sovra-copertura)
  REL: 0 = toglie la copertura dopo un rimbalzo di R $; 1 = rimbalzo di R $ E tendenza EMA200 H1 tornata dal lato del cesto
  KH : copertura al livello KH; EQH > 0: copertura quando la perdita aperta del cesto supera EQH% del saldo (al posto
       del livello)
usage: python python/scripts/phase38_hedge_variants.py
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
BASE = (8.0, 1.3, 2.0, 0.7)


@numba.njit(cache=True)
def sim(bid, ask, calm, trend, bal0, D, G, M, T, KH, R, HR, REL, EQH):
    bal = bal0; peak = bal0; mdd = 0.0; nord = 0
    lots = np.zeros((2, 200)); px = np.zeros((2, 200)); n = np.zeros(2, np.int64)
    ref = np.zeros(2); hl = np.zeros(2); hp = np.zeros(2); hx = np.zeros(2)
    eq = bal0
    for i in range(bid.size):
        b = bid[i]; a = ask[i]
        flo = 0.0; marg = 0.0
        for s in range(2):
            d = 1.0 if s == 0 else -1.0
            pin = a if d > 0 else b
            pout = b if d > 0 else a
            side_ok = (d > 0 and trend[i]) or (d < 0 and not trend[i])
            if n[s] == 0:
                if calm[i] and side_ok:
                    lots[s, 0] = 1.0; px[s, 0] = pin; n[s] = 1; ref[s] = pin; nord += 1
                continue
            L = 0.0; W = 0.0
            for k in range(n[s]):
                L += lots[s, k]; W += lots[s, k] * px[s, k]
            avg = W / L
            hexit = a if d > 0 else b
            if hl[s] > 0:
                if (pout - hx[s]) * d < 0:
                    hx[s] = pout
                if (pout - hx[s]) * d >= R and (REL == 0 or side_ok):
                    bal += (hp[s] - hexit) * d * hl[s] - COMM * hl[s]
                    hl[s] = 0.0; ref[s] = pin
                else:
                    flo += (pout - avg) * d * L + (hp[s] - hexit) * d * hl[s]
                    marg += max(L, hl[s]) * b / 1000.0
                    continue
            if (pout - avg) * d >= T:
                bal += (pout - avg) * d * L - COMM * L; n[s] = 0
                continue
            dist = D * G ** min(n[s] - 1, 30)
            added = False
            if (ref[s] - pin) * d >= dist and n[s] < 199:
                k = n[s]
                lots[s, k] = np.floor(M ** min(k, 40) + 1e-9); px[s, k] = pin; n[s] += 1; nord += 1; ref[s] = pin
                L += lots[s, k]; W += lots[s, k] * pin; avg = W / L
                added = True
            v = (pout - avg) * d * L
            trig = (EQH > 0 and v < -EQH / 100.0 * bal) or (EQH <= 0 and added and n[s] >= KH)
            if trig and hl[s] == 0:
                hl[s] = max(1.0, np.round(HR * L)); hp[s] = b if d > 0 else a; hx[s] = pout; nord += 1
                flo += v + (hp[s] - hexit) * d * hl[s]
                marg += max(L, hl[s]) * b / 1000.0
                continue
            flo += v
            marg += L * b / 1000.0
        eq = bal + flo
        if eq > peak:
            peak = eq
        if (peak - eq) / peak > mdd:
            mdd = (peak - eq) / peak
        if marg > 0 and eq < 0.5 * marg:
            return eq, 1.0, nord, 1
    return eq, mdd, nord, 0


GRID = list(itertools.product((3, 4), (5.0, 8.0, 12.0), (0.7, 1.0, 1.3), (0, 1), (0.0, 20.0, 30.0)))
GRID = [g for g in GRID if not (g[4] > 0 and g[0] == 4)]          # con EQH il livello non conta: una sola volta


def run_month(m):
    fn = ROOT / "output" / "cache" / "ticks" / f"XAUUSD_ticks_2026_{m:02d}.parquet"
    bid, ask, calm, trend = signals(fn, 12000, 0.0)
    out = []
    for KH, R, HR, REL, EQH in GRID:
        r = sim(bid, ask, calm, trend, DEP, *BASE, KH, R, HR, REL, EQH)
        out.append(dict(mese=m, copri=("perdita %d%%" % EQH) if EQH > 0 else f"livello {KH}", R=R, HR=HR,
                        via=("rimbalzo+tendenza" if REL else "rimbalzo"), saltato=bool(r[3]),
                        eur=-50 if r[3] else round((r[0] - DEP) / 100), calo=round(r[1] * 100), ordini=r[2]))
    print("fatto mese", m, flush=True)
    return out


def main():
    with Pool(5) as p:
        rows = [r for part in p.map(run_month, range(1, 11)) for r in part]
    df = pd.DataFrame(rows)
    out = ROOT / "output" / "phase38"
    out.mkdir(parents=True, exist_ok=True)
    df.to_csv(out / "hedging_varianti.csv", index=False)
    key = ["copri", "R", "HR", "via"]
    piv = df.pivot_table(index=key, columns="mese", values="eur", aggfunc="first")
    piv["totale"] = piv.sum(axis=1)
    piv["mesi_neg"] = (piv[list(range(1, 11))] < 0).sum(axis=1)
    piv["calo_max"] = df.groupby(key).calo.max()
    piv.to_csv(out / "hedging_varianti_tabella.csv")
    pd.set_option("display.width", 250)
    print(piv.sort_values(["mesi_neg", "totale"], ascending=[True, False]).head(25).to_string())


if __name__ == "__main__":
    main()
