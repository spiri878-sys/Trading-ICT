"""FASE 26 — cesto martingala M1 'più intelligente': prove con scelta su gen-mag 2026 e verifica su giu-ott 2026.
Idee: TP che scende con i livelli (i cesti pesanti escono prima), distanza ATR (mobile), moltiplicatore che rallenta
dopo K livelli, lotto che cresce con il conto. Lotti arrotondati come il broker (per difetto, minimo 0,01).
Unità: $ per 0,01 lotti = centesimi su un conto cent; deposito 500.000 (5.000 EUR cent). Stop out al 50% del
margine (leva 1:1000). Nella barra M1 prima il movimento contrario.

usage: python python/scripts/phase26_basket_smart.py
"""
import itertools
from pathlib import Path

import numba
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DEP = 500000.0


@numba.njit(cache=True)
def sim(op, hi, lo, cl, sp, atr, buy, sell, bal0, D, G, DA, T, TD, TMIN, M1, M2, K, comp):
    bal = bal0
    peak = bal0
    mdd = 0.0
    nord = 0
    nb = 0
    lots = np.zeros((2, 64)); px = np.zeros((2, 64)); n = np.zeros(2, np.int64)
    nxt = np.zeros(2); base = np.ones(2)
    for i in range(1, hi.size):
        flo = 0.0
        marg = 0.0
        for s in range(2):
            d = 1.0 if s == 0 else -1.0
            if n[s] == 0:
                sig = buy[i - 1] if s == 0 else sell[i - 1]
                if not sig:
                    continue
                base[s] = max(1.0, np.floor(bal / comp)) if comp > 0 else 1.0
                p0 = op[i] + (sp[i] if d > 0 else 0.0)
                lots[s, 0] = base[s]; px[s, 0] = p0; n[s] = 1; nord += 1
                g0 = D if DA <= 0 else max(D, DA * atr[i - 1])
                nxt[s] = p0 - d * g0
            added = False
            while n[s] < 60 and ((d > 0 and lo[i] <= nxt[s]) or (d < 0 and hi[i] + sp[i] >= nxt[s])):
                k = n[s]
                # lotto teorico del livello k, arrotondato per difetto (minimo il lotto base)
                if k < K:
                    raw = base[s] * M1 ** k
                else:
                    raw = base[s] * M1 ** (K - 1) * M2 ** (k - K + 1)
                lots[s, k] = max(base[s], np.floor(raw + 1e-9))
                px[s, k] = nxt[s]; n[s] += 1; added = True; nord += 1
                g = D if DA <= 0 else max(D, DA * atr[i - 1])
                nxt[s] = nxt[s] - d * g * G ** k
            L = 0.0; W = 0.0
            for k in range(n[s]):
                L += lots[s, k]; W += lots[s, k] * px[s, k]
            avg = W / L
            tp = max(TMIN, T * TD ** (n[s] - 1))
            worst = (lo[i] - avg) * L if d > 0 else (avg - (hi[i] + sp[i])) * L
            if added:
                hit = (d > 0 and cl[i] >= avg + tp) or (d < 0 and cl[i] + sp[i] <= avg - tp)
            else:
                hit = (d > 0 and hi[i] >= avg + tp) or (d < 0 and lo[i] + sp[i] <= avg - tp)
            if hit:
                bal += tp * L - 0.04 * L; n[s] = 0; nb += 1
                continue
            flo += min(worst, 0.0)
            marg += L * cl[i] / 1000.0
        eq = bal + flo
        if eq > peak:
            peak = eq
        if (peak - eq) / peak > mdd:
            mdd = (peak - eq) / peak
        if marg > 0 and eq < 0.5 * marg:
            return eq, 1.0, nord, nb, 1, i
    return bal, mdd, nord, nb, 0, hi.size


def ema(x, span):
    return pd.Series(x).ewm(span=span, adjust=False).mean().values


def load():
    m = pd.read_parquet(ROOT / "output" / "cache" / "XAUUSD_M1_axi_2026.parquet")
    op, hi, lo, cl = (m[c].values.astype(float) for c in ("open", "high", "low", "close"))
    sp = m.spread.values * 0.01
    h5, l5 = pd.Series(hi), pd.Series(lo)
    atr = (h5 - l5).rolling(14).mean().bfill().values
    tr = cl > ema(cl, 12000)
    calm = ((h5.rolling(15).max() - l5.rolling(15).min()) < 4 * pd.Series(atr)).values
    entries = {"tendenza": ((tr & calm), (~tr & calm)), "BUY+SELL": (calm, calm)}
    return m, op, hi, lo, cl, sp, atr, entries


def run(arrs, a, z, b, s, p, comp=0.0):
    op, hi, lo, cl, sp, atr = arrs
    return sim(op[a:z], hi[a:z], lo[a:z], cl[a:z], sp[a:z], atr[a:z], b[a:z], s[a:z], DEP, *p, comp)


def main():
    m, op, hi, lo, cl, sp, atr, entries = load()
    arrs = (op, hi, lo, cl, sp, atr)
    split = int(np.searchsorted(m.index.values, np.datetime64("2026-06-01")))
    months = (z := (z_ for z_ in [m.index.to_period("M").values]))
    mon = m.index.to_period("M").values
    nmon_a, nmon_b = len(pd.unique(mon[:split])), len(pd.unique(mon[split:]))
    grid = itertools.product(entries, (1.0, 1.5, 2.0), (1.2, 1.25, 1.3), (0.0, 1.0, 2.0), (1.0, 2.0, 3.0),
                             (1.0, 0.8, 0.6), ((1.5, 1.5, 99), (1.5, 1.3, 8), (1.5, 1.2, 6)))
    rows = []
    for en, D, G, DA, T, TD, (M1, M2, K) in grid:
        b, s = (x.astype(np.bool_) for x in entries[en])
        p = (D, G, DA, T, TD, 0.3, M1, M2, K)
        ra = run(arrs, 0, split, b, s, p)
        rb = run(arrs, split, len(cl), b, s, p)
        rows.append(dict(entrata=en, distanza=D, crescita=G, atr=DA, tp=T, tp_cala=TD, molt=f"{M1}->{M2} dal {K}",
                         A_saltato=bool(ra[4]), A_profitto=round((ra[0] / DEP - 1) * 100), A_calo=round(ra[1] * 100),
                         A_ordini_mese=round(ra[2] / nmon_a),
                         B_saltato=bool(rb[4]), B_profitto=round((rb[0] / DEP - 1) * 100), B_calo=round(rb[1] * 100),
                         B_ordini_mese=round(rb[2] / nmon_b)))
    df = pd.DataFrame(rows)
    out = ROOT / "output" / "phase26"
    out.mkdir(parents=True, exist_ok=True)
    df.to_csv(out / "prove.csv", index=False)
    return df


if __name__ == "__main__":
    df = main()
    pd.set_option("display.width", 250)
    ok = df[~df.A_saltato & (df.A_calo <= 50)].sort_values("A_profitto", ascending=False)
    print("superano gen-mag (calo <= 50%):", len(ok), "su", len(df))
    print(ok.head(30).to_string(index=False))
    print("\ndi quelle, saltate a giu-ott:", int(ok.B_saltato.sum()))
