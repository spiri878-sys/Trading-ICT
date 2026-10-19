"""FASE 32 — cesto HFT M1 con hedging, TICK PER TICK su tutti i mesi 2026 (tick HistData, spread fisso Axi 0,09 $),
conto 5.000 USC. Scelta su gen-mag, verifica su giu-ott. Ogni mese riparte da 5.000.
usage: python python/scripts/phase32_basket_ticks_all.py
"""
import itertools
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

from phase31_ticks import DEP, load_month, tick_basket

ROOT = Path(__file__).resolve().parents[2]
GRID = list(itertools.product((3.0, 5.0, 8.0), (1.2, 1.3), (1.3, 1.5, 2.0), (0.5, 1.0, 2.0), (3, 4, 5, 6),
                              (2.0, 3.0, 5.0, 8.0)))


def run_month(mo):
    fn = ROOT / "output" / "cache" / "ticks" / f"XAUUSD_ticks_2026_{mo:02d}.parquet"
    bid, ask, calm, trend = load_month(fn)
    out = []
    for D, G, M, T, KH, R in GRID:
        r = tick_basket(bid, ask, calm, trend, DEP, D, G, M, T, KH, R)
        out.append(dict(mese=mo, D=D, G=G, M=M, TP=T, copri=KH, R=R, saltato=bool(r[4]),
                        resa=-100 if r[4] else round((r[0] / DEP - 1) * 100), calo=round(r[1] * 100), ordini=r[2]))
    print("fatto mese", mo, flush=True)
    return out


def main():
    months = [m for m in range(1, 11) if (ROOT / "output" / "cache" / "ticks" / f"XAUUSD_ticks_2026_{m:02d}.parquet").exists()]
    with Pool(min(5, len(months))) as p:
        rows = [r for part in p.map(run_month, months) for r in part]
    df = pd.DataFrame(rows)
    out = ROOT / "output" / "phase32"
    out.mkdir(parents=True, exist_ok=True)
    df.to_csv(out / "cesto_tick_mesi.csv", index=False)
    key = ["D", "G", "M", "TP", "copri", "R"]
    A = df[df.mese <= 5].groupby(key).agg(bruciati_A=("saltato", "sum"), peggio_A=("resa", "min"), somma_A=("resa", "sum"),
                                          calo_A=("calo", "max"), ordini_A=("ordini", "mean"))
    B = df[df.mese >= 6].groupby(key).agg(bruciati_B=("saltato", "sum"), peggio_B=("resa", "min"), somma_B=("resa", "sum"),
                                          calo_B=("calo", "max"), ordini_B=("ordini", "mean"))
    w = A.join(B).reset_index()
    w.to_csv(out / "cesto_tick_tabella.csv", index=False)
    pd.set_option("display.width", 250)
    sel = w[w.bruciati_A == 0].sort_values(["peggio_A", "somma_A"], ascending=False)
    print("set senza mesi bruciati a gen-mag:", len(sel), "su", len(w))
    print(sel.head(25).to_string(index=False))
    cur = w[(w.D == 8) & (w.G == 1.2) & (w.M == 1.3) & (w.TP == 1.0) & (w.copri == 5) & (w.R == 5.0)]
    print("\nset attuale dell'utente:\n", cur.to_string(index=False))


if __name__ == "__main__":
    main()
