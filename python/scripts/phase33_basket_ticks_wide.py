"""FASE 33 — come la fase 32 (tick per tick, 5.000 USC, ogni mese da capo), griglia più larga: anche senza hedging
(copri 0), lotto x1,5-2,5, distanza 6-12 $ x1,3-1,5, TP 0,3-1 $, rimbalzo 5-12 $.
usage: python python/scripts/phase33_basket_ticks_wide.py
"""
import itertools

import phase32_basket_ticks_all as P

P.GRID = list(itertools.product((6.0, 8.0, 10.0, 12.0), (1.3, 1.4, 1.5), (1.5, 2.0, 2.5), (0.3, 0.5, 1.0),
                                (0, 3, 4, 5), (5.0, 8.0, 12.0)))

if __name__ == "__main__":
    import pandas as pd
    from pathlib import Path
    out = Path(P.ROOT) / "output" / "phase32"
    P.main()
    for f in ("cesto_tick_mesi.csv", "cesto_tick_tabella.csv"):
        (out / f).rename(out / f.replace("cesto_tick", "cesto_tick_largo"))
