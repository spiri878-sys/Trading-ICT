"""FASE 40 — martingala con tetto: 0,01 -> 0,02 -> ... -> tetto (0,16 / 0,32 / 0,64), poi media sempre al tetto.
Con e senza hedging (copertura al livello KH, KH=0 = niente copertura). TICK PER TICK, ogni mese da 5.000 USC.
Base: distanza D x1,3, lotto x2, TP 0,7 $, via a 8 $. Simulazione della fase 37 (smart spento).
usage: python python/scripts/phase40_lot_cap.py
"""
import itertools
from multiprocessing import Pool
from pathlib import Path

import pandas as pd

from phase31_ticks import DEP
from phase36_entries_ticks import signals
from phase37_smart_hedge import sim

ROOT = Path(__file__).resolve().parents[2]
GRID = list(itertools.product((6.0, 8.0), (0, 4, 5, 6, 7, 8), (0.0, 16.0, 32.0, 64.0)))


def run_month(m):
    fn = ROOT / "output" / "cache" / "ticks" / f"XAUUSD_ticks_2026_{m:02d}.parquet"
    bid, ask, calm, trend = signals(fn, 12000, 0.0)
    out = []
    for D, KH, LMAX in GRID:
        r = sim(bid, ask, calm, trend, DEP, D, 1.3, 2.0, 0.7, KH, 8.0, LMAX, 0)
        out.append(dict(mese=m, distanza=D, copertura=("no" if KH == 0 else f"livello {KH}"),
                        tetto=("nessuno" if LMAX == 0 else f"{LMAX / 100:.2f}"), saltato=bool(r[4]),
                        eur=-50 if r[4] else round((r[0] - DEP) / 100), calo=round(r[1] * 100), ordini=r[2]))
    print("fatto mese", m, flush=True)
    return out


def main():
    with Pool(5) as p:
        rows = [r for part in p.map(run_month, range(1, 11)) for r in part]
    df = pd.DataFrame(rows)
    out = ROOT / "output" / "phase40"
    out.mkdir(parents=True, exist_ok=True)
    df.to_csv(out / "tetto_lotto.csv", index=False)
    key = ["distanza", "copertura", "tetto"]
    piv = df.pivot_table(index=key, columns="mese", values="eur", aggfunc="first")
    piv["totale"] = piv.sum(axis=1)
    piv["mesi_neg"] = (piv[list(range(1, 11))] < 0).sum(axis=1)
    piv["calo_max"] = df.groupby(key).calo.max()
    pd.set_option("display.width", 250)
    print(piv.sort_values(["mesi_neg", "totale"], ascending=[True, False]).to_string())


if __name__ == "__main__":
    main()
