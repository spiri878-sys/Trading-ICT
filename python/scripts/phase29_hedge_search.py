"""FASE 29 — conto 5.000 USC: cesto M1 + hedging, cerca più operazioni e più profitto senza bruciare.
Simulazione della fase 27 (copertura al livello KH, tolta dopo un rimbalzo di R $). Mese per mese da capo,
deposito 5.000 (= 5.000 USC con 0,01 lotti). Scelta su gen-mag 2026, verifica su giu-ott 2026.
usage: python python/scripts/phase29_hedge_search.py
"""
import itertools
from pathlib import Path

import numpy as np
import pandas as pd

from phase27_basket_protect import sim

ROOT = Path(__file__).resolve().parents[2]
DEP = 5000.0


def main():
    m = pd.read_parquet(ROOT / "output" / "cache" / "XAUUSD_M1_axi_2026.parquet")
    op, hi, lo, cl = (m[c].values.astype(float) for c in ("open", "high", "low", "close"))
    sp = m.spread.values * 0.01
    h5, l5 = pd.Series(hi), pd.Series(lo)
    atr = (h5 - l5).rolling(14).mean().bfill()
    tr = cl > pd.Series(cl).ewm(span=12000, adjust=False).mean().values
    calm = ((h5.rolling(15).max() - l5.rolling(15).min()) < 6 * atr).values
    entries = {"tendenza": ((tr & calm).astype(np.bool_), (~tr & calm).astype(np.bool_)),
               "BUY+SELL": (calm.astype(np.bool_), calm.astype(np.bool_))}
    mon = m.index.to_period("M").values
    cuts = [np.where(mon == p)[0] for p in pd.unique(mon)]
    rows = []
    for en, D, G, M, T, KH, R in itertools.product(entries, (2.0, 3.0, 4.0, 5.0, 6.0, 8.0), (1.0, 1.1, 1.2, 1.3),
                                                   (1.1, 1.2, 1.3, 1.5), (0.5, 1.0, 2.0), (3, 4, 5, 6), (2.0, 3.0, 5.0, 8.0)):
        b, s = entries[en]
        res = []
        for sel in cuts:
            a, z = sel[0], sel[-1] + 1
            r = sim(op[a:z], hi[a:z], lo[a:z], cl[a:z], sp[a:z], tr[a:z], b[a:z], s[a:z], DEP, D, G, T, M, 99, 0, KH, R)
            res.append((r[4], -1.0 if r[4] else r[0] / DEP - 1, r[1], r[2]))
        rows.append(dict(entrata=en, distanza=D, crescita=G, lotto=M, tp=T, copri_liv=KH, rimbalzo=R,
                         saltati_A=sum(x[0] for x in res[:5]), resa_A=round(sum(x[1] for x in res[:5]) * 100),
                         saltati_B=sum(x[0] for x in res[5:]), resa_B=round(sum(x[1] for x in res[5:]) * 100),
                         peggior_mese=round(min(x[1] for x in res) * 100), calo_max=round(max(x[2] for x in res) * 100),
                         ordini_mese=round(np.mean([x[3] for x in res]))))
    df = pd.DataFrame(rows)
    out = ROOT / "output" / "phase29"
    out.mkdir(parents=True, exist_ok=True)
    df.to_csv(out / "hedging_5000usc.csv", index=False)
    return df


if __name__ == "__main__":
    df = main()
    pd.set_option("display.width", 250)
    a = df[df.saltati_A == 0].sort_values("resa_A", ascending=False)
    print("0 mesi bruciati a gen-mag:", len(a), "su", len(df))
    print(a.head(30).to_string(index=False))
