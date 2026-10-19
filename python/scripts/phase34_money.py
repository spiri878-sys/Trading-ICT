"""FASE 34 — gestione dei soldi sul cesto HFT con hedging (set fase 32), TICK PER TICK, gen -> ott 2026 DI FILA.
Il conto parte da 5.000 USC (50 EUR). Lotto base = 0,01 ogni COMP USC di saldo (COMP=0: sempre 0,01).
Prelievo: quando non ci sono cesti aperti e il saldo supera SOGLIA, si ritira fino a tornare a RESTA.
Se il conto brucia (stop out) si rimettono 5.000 USC e si riparte. Risultato in EUR: ritirato + saldo finale - versato.
usage: python python/scripts/phase34_money.py
"""
import itertools
from pathlib import Path

import numba
import numpy as np
import pandas as pd

from phase31_ticks import COMM, SPREAD

ROOT = Path(__file__).resolve().parents[2]
DEP = 5000.0


def load_all():
    parts = []
    for m in range(1, 11):
        fn = ROOT / "output" / "cache" / "ticks" / f"XAUUSD_ticks_2026_{m:02d}.parquet"
        parts.append(pd.read_parquet(fn))
    t = pd.concat(parts, ignore_index=True).sort_values("time", kind="stable")
    t = t[t.bid > 0]
    bid = t.bid.values.astype(np.float64)
    minute = t.time.values.astype("datetime64[m]")
    s = pd.Series(bid, index=pd.DatetimeIndex(minute))
    o = s.groupby(level=0).agg(["max", "min", "last"])
    o.columns = ["high", "low", "close"]
    atr = (o.high - o.low).rolling(14).mean()
    calm = ((o.high.rolling(15).max() - o.low.rolling(15).min()) < 6 * atr).values
    trend = (o.close > o.close.ewm(span=12000, adjust=False).mean()).values
    idx = np.searchsorted(o.index.values, minute) - 1
    ok = idx >= 0
    c = np.zeros(bid.size, np.bool_); tr = np.zeros(bid.size, np.bool_)
    c[ok] = calm[idx[ok]]; tr[ok] = trend[idx[ok]]
    month = pd.DatetimeIndex(t.time.values).month.values.astype(np.int64)
    return bid, bid + SPREAD, c, tr, month


@numba.njit(cache=True)
def run(bid, ask, calm, trend, month, D, G, M, T, KH, R, COMP, SOGLIA, RESTA):
    bal = DEP; deposited = DEP; withdrawn = 0.0; blown = 0; nord = 0
    lots = np.zeros((2, 80)); px = np.zeros((2, 80)); n = np.zeros(2, np.int64)
    ref = np.zeros(2); hl = np.zeros(2); hp = np.zeros(2); hx = np.zeros(2); base = np.ones(2)
    mon_w = np.zeros(13); mon_dep = np.zeros(13); mon_eq = np.zeros(13)
    for i in range(bid.size):
        b = bid[i]; a = ask[i]
        flo = 0.0; marg = 0.0
        for s in range(2):
            d = 1.0 if s == 0 else -1.0
            pin = a if d > 0 else b
            pout = b if d > 0 else a
            if n[s] == 0:
                if calm[i] and ((d > 0 and trend[i]) or (d < 0 and not trend[i])):
                    base[s] = max(1.0, np.floor(bal / COMP)) if COMP > 0 else 1.0
                    lots[s, 0] = base[s]; px[s, 0] = pin; n[s] = 1; ref[s] = pin; nord += 1
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
                    bal += (hp[s] - hexit) * d * hl[s] - COMM * hl[s]
                    hl[s] = 0.0; ref[s] = pin
                else:
                    flo += (pout - avg) * d * L + (hp[s] - hexit) * d * hl[s]
                    marg += max(L, hl[s]) * b / 1000.0
                    continue
            if (pout - avg) * d >= T:
                bal += (pout - avg) * d * L - COMM * L; n[s] = 0
                continue
            dist = D * G ** (n[s] - 1)
            if (ref[s] - pin) * d >= dist and n[s] < 79:
                k = n[s]
                lots[s, k] = base[s] * np.floor(M ** k + 1e-9); px[s, k] = pin; n[s] += 1; nord += 1; ref[s] = pin
                L += lots[s, k]; W += lots[s, k] * pin; avg = W / L
                if KH > 0 and n[s] >= KH:
                    hl[s] = L; hp[s] = b if d > 0 else a; hx[s] = pout; nord += 1
            flo += (pout - avg) * d * L
            marg += L * b / 1000.0
        eq = bal + flo
        mon_eq[month[i]] = eq
        if marg > 0 and eq < 0.5 * marg:                 # bruciato: si chiude tutto e si rimettono 5.000
            blown += 1
            n[:] = 0; hl[:] = 0.0
            bal = DEP; deposited += DEP; mon_dep[month[i]] += DEP
            continue
        if n[0] == 0 and n[1] == 0 and SOGLIA > 0 and bal >= SOGLIA:
            w = bal - RESTA
            withdrawn += w; mon_w[month[i]] += w; bal = RESTA
    return bal, deposited, withdrawn, blown, nord, mon_w, mon_dep, mon_eq


def main():
    bid, ask, calm, trend, month = load_all()
    print(f"{bid.size:,} tick gen-ott")
    sets = {"TP 0,5": (8.0, 1.3, 2.0, 0.5, 4, 8.0), "TP 0,3": (8.0, 1.3, 2.0, 0.3, 4, 8.0)}
    rows = []
    for (sn, p), COMP, (SOGLIA, RESTA) in itertools.product(
            sets.items(), (0.0, 5000.0, 2500.0),
            ((10000.0, 5000.0), (20000.0, 10000.0), (40000.0, 20000.0), (100000.0, 50000.0), (0.0, 0.0))):
        if COMP == 0 and SOGLIA in (40000.0, 100000.0):
            continue
        bal, dep, wd, bl, no, mw, md, me = run(bid, ask, calm, trend, month, *p, COMP, SOGLIA, RESTA)
        net = wd + bal - dep
        rows.append(dict(set=sn, lotto=("fisso 0,01" if COMP == 0 else f"0,01 ogni {COMP / 100:.0f} EUR"),
                         prelievo=("mai" if SOGLIA == 0 else f"a {SOGLIA / 100:.0f} EUR torna a {RESTA / 100:.0f}"),
                         bruciato_volte=bl, versati_eur=round(dep / 100), ritirati_eur=round(wd / 100),
                         saldo_finale_eur=round(bal / 100), guadagno_netto_eur=round(net / 100),
                         mesi=" ".join(f"{(mw[m] - md[m]) / 100:+.0f}" for m in range(1, 11))))
    df = pd.DataFrame(rows).sort_values("guadagno_netto_eur", ascending=False)
    out = ROOT / "output" / "phase34"
    out.mkdir(parents=True, exist_ok=True)
    df.to_csv(out / "gestione_soldi.csv", index=False)
    pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 120)
    print(df.to_string(index=False))


if __name__ == "__main__":
    main()
