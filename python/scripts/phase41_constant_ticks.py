"""FASE 41 — cerca la COSTANZA: nessun mese bruciato partendo da 5.000 USC ogni mese. Griglie larghe (10-20 $),
martingala morbida (x1,3-x2), copertura presto (2°-4° livello) o assente, TP 0,5-2 $. TICK PER TICK.
Risultati in output/phase32/cesto_tick_costante_*.
usage: python python/scripts/phase41_constant_ticks.py
"""
import itertools
import shutil

import phase32_basket_ticks_all as P

P.GRID = list(itertools.product((10.0, 12.0, 15.0, 20.0), (1.2, 1.3, 1.5), (1.3, 1.5, 2.0), (0.5, 1.0, 2.0), (0, 2, 3, 4),
                                (5.0, 8.0, 12.0)))

if __name__ == "__main__":
    out = P.ROOT / "output" / "phase32"
    for f in ("cesto_tick_mesi.csv", "cesto_tick_tabella.csv"):
        shutil.copy(out / f, out / f"_bak_{f}")
    P.main()
    for f in ("cesto_tick_mesi.csv", "cesto_tick_tabella.csv"):
        (out / f).rename(out / f.replace("cesto_tick", "cesto_tick_costante"))
        (out / f"_bak_{f}").rename(out / f)
