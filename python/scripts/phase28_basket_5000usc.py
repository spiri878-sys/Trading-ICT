"""FASE 28 — cesto martingala M1 per il conto VERO dell'utente: 5.000 USC (50 $), lotto minimo 0,01 cent.
Nel tester (simbolo normale) = deposito 5.000 con 0,01 lotti. Stessa simulazione della fase 26 (tendenza EMA200 H1 +
niente strappi, lotti arrotondati, stop out 50% del margine con leva 1:1000, nella barra prima il movimento contrario).
Mese per mese da capo: scelta su gen-mag 2026, verifica su giu-ott 2026.
usage: python python/scripts/phase28_basket_5000usc.py
"""
import itertools
from pathlib import Path

import numpy as np
import pandas as pd

from phase26_basket_smart import load, sim

ROOT = Path(__file__).resolve().parents[2]
DEP = 5000.0


def main():
    m, op, hi, lo, cl, sp, atr, _ = load()
    h5, l5 = pd.Series(hi), pd.Series(lo)
    tr = cl > pd.Series(cl).ewm(span=12000, adjust=False).mean().values
    calm = ((h5.rolling(15).max() - l5.rolling(15).min()) < 6 * pd.Series(atr)).values
    b, s = (tr & calm).astype(np.bool_), (~tr & calm).astype(np.bool_)
    mon = m.index.to_period("M").values
    cuts = [np.where(mon == p)[0] for p in pd.unique(mon)]
    rows = []
    for D, G, M, T in itertools.product((1.0, 2.0, 3.0, 5.0, 8.0), (1.0, 1.2, 1.3, 1.5), (1.0, 1.1, 1.2, 1.3, 1.5),
                                        (1.0, 2.0, 3.0, 5.0)):
        res = []
        for sel in cuts:
            a, z = sel[0], sel[-1] + 1
            r = sim(op[a:z], hi[a:z], lo[a:z], cl[a:z], sp[a:z], atr[a:z], b[a:z], s[a:z], DEP,
                    D, G, 0.0, T, 1.0, 0.3, M, M, 99, 0.0)
            res.append((r[4], -1.0 if r[4] else r[0] / DEP - 1, r[1], r[2]))
        rows.append(dict(distanza=D, crescita=G, molt=M, tp=T,
                         saltati_genmag=sum(x[0] for x in res[:5]), resa_genmag=round(sum(x[1] for x in res[:5]) * 100),
                         saltati_giuott=sum(x[0] for x in res[5:]), resa_giuott=round(sum(x[1] for x in res[5:]) * 100),
                         calo_max=round(max(x[2] for x in res) * 100), ordini_mese=round(np.mean([x[3] for x in res]))))
    df = pd.DataFrame(rows)
    out = ROOT / "output" / "phase28"
    out.mkdir(parents=True, exist_ok=True)
    df.to_csv(out / "prove_5000usc.csv", index=False)
    pd.set_option("display.width", 250)
    ok = df[(df.saltati_genmag == 0)].sort_values("resa_genmag", ascending=False)
    print("senza mesi saltati a gen-mag:", len(ok), "su", len(df))
    print(ok.head(30).to_string(index=False))


if __name__ == "__main__":
    main()
