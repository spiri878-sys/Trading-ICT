"""FASE 39 — zona "aggressiva" (dove stanno i massimi dei singoli mesi: distanza 2-4 $, copertura tardi, TP 1-2 $),
TICK PER TICK, ogni mese da 5.000 USC: esiste un set che regge tutti i mesi? Risultati in output/phase32/cesto_tick_aggr_*.
usage: python python/scripts/phase39_aggressive_ticks.py
"""
import itertools
import shutil

import phase32_basket_ticks_all as P

P.GRID = list(itertools.product((2.0, 3.0, 4.0), (1.2, 1.3), (1.5, 2.0), (1.0, 1.5, 2.0), (5, 6, 7), (2.0, 3.0, 5.0, 8.0)))

if __name__ == "__main__":
    out = P.ROOT / "output" / "phase32"
    for f in ("cesto_tick_mesi.csv", "cesto_tick_tabella.csv"):
        shutil.copy(out / f, out / f"_bak_{f}")
    P.main()
    for f in ("cesto_tick_mesi.csv", "cesto_tick_tabella.csv"):
        (out / f).rename(out / f.replace("cesto_tick", "cesto_tick_aggr"))
        (out / f"_bak_{f}").rename(out / f)
