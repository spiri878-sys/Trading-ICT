"""FASE 43b — i set con entrata a stop senza mesi in perdita: fino a che lotto di partenza reggono su 5.000 USC?
Tutto è proporzionale al lotto, quindi lotto k x 0,01 su 5.000 USC = k volte il risultato con 0,01 su 5.000/k USC.
usage: python python/scripts/phase43b_scale.py
"""
from multiprocessing import Pool
from pathlib import Path

import pandas as pd

from phase36_entries_ticks import signals
from phase43_stop_orders import sim

ROOT = Path(__file__).resolve().parents[2]
tab = pd.read_csv(ROOT / "output" / "phase43" / "stop_tabella.csv")
TOP = tab[tab.neg == 0].sort_values("tot", ascending=False).head(12)[["D", "M", "copri", "entrata_stop", "media_conferma"]]
KS = (1, 2, 3, 5, 8, 10, 15, 20)


def run_month(m):
    fn = ROOT / "output" / "cache" / "ticks" / f"XAUUSD_ticks_2026_{m:02d}.parquet"
    bid, ask, calm, trend = signals(fn, 12000, 0.0)
    out = []
    for _, c in TOP.iterrows():
        for k in KS:
            dep = 5000.0 / k
            r = sim(bid, ask, calm, trend, dep, c.D, 1.3, c.M, 0.7, int(c.copri), 8.0, 0.7, c.entrata_stop, c.media_conferma)
            out.append(dict(mese=m, D=c.D, M=c.M, copri=int(c.copri), E=c.entrata_stop, B=c.media_conferma, lotto=k / 100,
                            usc=-5000 if r[2] else round((r[0] - dep) * k), ordini=r[1]))
    print("fatto mese", m, flush=True)
    return out


def main():
    with Pool(5) as p:
        rows = [r for part in p.map(run_month, range(1, 11)) for r in part]
    df = pd.DataFrame(rows)
    df.to_csv(ROOT / "output" / "phase43" / "stop_lotti.csv", index=False)
    key = ["D", "M", "copri", "E", "B", "lotto"]
    piv = df.pivot_table(index=key, columns="mese", values="usc", aggfunc="first")
    ms = list(range(1, 11))
    piv["neg"] = (piv[ms] < 0).sum(axis=1); piv["tot"] = piv[ms].sum(axis=1); piv["min"] = piv[ms].min(axis=1)
    pd.set_option("display.width", 300)
    print(piv[piv.neg == 0].sort_values("tot", ascending=False).head(20).to_string())


if __name__ == "__main__":
    main()
