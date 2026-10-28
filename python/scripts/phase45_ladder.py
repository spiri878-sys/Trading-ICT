"""FASE 45 — "scala": si parte con 5.000 USC e, quando non ci sono cesti aperti, si passa al set NoBrucia del capitale
raggiunto (fase 44): <10.000 set 503 x0,01; <20.000 set 503 x0,02; <50.000 set 1726 x0,03; <100.000 set 1830 x0,07;
oltre set 1830 x0,14 ogni 100.000 USC. TICK PER TICK, gen -> 16 ott 2026 di fila, senza prelievi.
usage: python python/scripts/phase45_ladder.py
"""
from pathlib import Path

import numba
import numpy as np
import pandas as pd

from phase31_ticks import COMM, SPREAD

ROOT = Path(__file__).resolve().parents[2]
SETS = {"503": (20.0, 1.0, 1.3, 2.5, 4, 8.0, 0.7, 8.0, 2.0, 0.2, 6.0),
        "1726": (20.0, 1.0, 1.3, 2.5, 3, 8.0, 0.5, 16.0, 2.0, 0.5, 0.0),
        "1830": (20.0, 1.0, 1.3, 1.5, 6, 8.0, 1.0, 16.0, 0.0, 0.2, 6.0)}


def tier(bal):
    if bal < 10000: return "503", 1, 0.0, 10000.0
    if bal < 20000: return "503", 2, 10000.0, 20000.0
    if bal < 50000: return "1726", 3, 20000.0, 50000.0
    if bal < 100000: return "1830", 7, 50000.0, 100000.0
    k = int(bal // 100000)
    return "1830", 14 * k, 100000.0 * k, 100000.0 * (k + 1)


def load():
    parts = [pd.read_parquet(ROOT / "output" / "cache" / "ticks" / f"XAUUSD_ticks_2026_{m:02d}.parquet") for m in range(1, 11)]
    t = pd.concat(parts, ignore_index=True).sort_values("time", kind="stable")
    t = t[t.bid > 0]
    bid = t.bid.values.astype(np.float64)
    minute = t.time.values.astype("datetime64[m]")
    s = pd.Series(bid, index=pd.DatetimeIndex(minute))
    o = s.groupby(level=0).agg(["max", "min", "last"]); o.columns = ["high", "low", "close"]
    atr = (o.high - o.low).rolling(14).mean()
    calm6 = ((o.high.rolling(15).max() - o.low.rolling(15).min()) < 6 * atr).values
    trend = (o.close > o.close.ewm(span=12000, adjust=False).mean()).values
    idx = np.searchsorted(o.index.values, minute) - 1
    ok = idx >= 0
    c6 = np.zeros(bid.size, np.bool_); tr = np.zeros(bid.size, np.bool_)
    c6[ok] = calm6[idx[ok]]; tr[ok] = trend[idx[ok]]
    month = pd.DatetimeIndex(t.time.values).month.values.astype(np.int64)
    return bid, bid + SPREAD, c6, np.ones(bid.size, np.bool_), tr, month


@numba.njit(cache=True)
def seg(bid, ask, calm, trend, month, i0, bal, K, D, G, M, T, KH, R, HR, LMAX, TRS, TRD, lo_b, hi_b, mon_eq):
    lots = np.zeros((2, 200)); px = np.zeros((2, 200)); n = np.zeros(2, np.int64)
    ref = np.zeros(2); hl = np.zeros(2); hp = np.zeros(2); hx = np.zeros(2); best = np.zeros(2)
    for i in range(i0, bid.size):
        b = bid[i]; a = ask[i]
        flo = 0.0; marg = 0.0
        if n[0] == 0 and n[1] == 0 and i > i0 and (bal >= hi_b or bal < lo_b):
            return i, bal, 0
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
        mon_eq[month[i]] = eq
        if marg > 0 and eq < 0.5 * marg:
            return i, eq, 1
    return bid.size, bal, 0


def main():
    bid, ask, c6, c0, tr, month = load()
    mon_eq = np.zeros(13)
    i, bal, log = 0, 5000.0, []
    while i < bid.size:
        name, K, lo_b, hi_b = tier(bal)
        p = SETS[name]
        calm = c6 if p[10] > 0 else c0
        i, bal, burned = seg(bid, ask, calm, tr, month, i, bal, float(K), *p[:10], lo_b, hi_b, mon_eq)
        log.append((name, K, int(month[min(i, bid.size - 1)]), round(bal)))
        if burned:
            print("BRUCIATO", log[-1]); break
    nomi = ["", "gen", "feb", "mar", "apr", "mag", "giu", "lug", "ago", "set", "ott"]
    prev = 5000.0
    for m in range(1, 11):
        e = mon_eq[m] or prev
        print(f"{nomi[m]}: fine mese {e / 100:9.0f} EUR  ({(e - prev) / 100:+.0f} EUR)")
        prev = e
    cambi = [(l[0], l[1], nomi[l[2]]) for j, l in enumerate(log) if j == 0 or l[:2] != log[j - 1][:2]]
    print("livelli usati:", cambi[:20], "... totale cambi", len(log))


if __name__ == "__main__":
    main()
