"""FASE 35 — rifinitura tick per tick intorno al set della fase 32 (8 $ x1,3, lotto x2, TP 0,5, copertura 4, via 8 $).
Ogni mese da capo a 5.000 USC. Risultati in output/phase32/cesto_tick_fine_*.csv.
usage: python python/scripts/phase35_basket_ticks_fine.py
"""
import itertools
import shutil

import phase32_basket_ticks_all as P

P.GRID = list(itertools.product((6.0, 7.0, 8.0, 9.0, 10.0), (1.25, 1.3, 1.35), (1.8, 2.0, 2.2), (0.4, 0.5, 0.7), (3, 4),
                                (6.0, 8.0, 10.0)))

if __name__ == "__main__":
    out = P.ROOT / "output" / "phase32"
    for f in ("cesto_tick_mesi.csv", "cesto_tick_tabella.csv"):
        shutil.copy(out / f, out / f"_bak_{f}")
    P.main()
    for f in ("cesto_tick_mesi.csv", "cesto_tick_tabella.csv"):
        (out / f).rename(out / f.replace("cesto_tick", "cesto_tick_fine"))
        (out / f"_bak_{f}").rename(out / f)
