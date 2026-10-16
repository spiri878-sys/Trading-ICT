"""FASE 14 — test delle 10 strategie TradingView del cliente sull'oro 2005 -> 2026-01, parametri di default,
costi C1 (spread 0,30 $, commissione 3,5 $/lotto/lato, slittamento 0,05 $), un trade alla volta.
Risultati: output/phase14/pine_results.json e .csv

usage: python python/scripts/phase14_pine.py [filtro_nome]
"""
import json
import sys
import time
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from raptor.pine.common import bars, summarize  # noqa: E402
from raptor.pine.strategies import STRATEGIES  # noqa: E402
from raptor.prime.data import ROOT  # noqa: E402

OUT = ROOT / "output" / "phase14"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    flt = sys.argv[1] if len(sys.argv) > 1 else ""
    p = OUT / "pine_results.json"
    res = json.loads(p.read_text()) if p.exists() else {}
    cache = {}
    for name, (fn, tfs, kw) in STRATEGIES.items():
        if flt and flt not in name:
            continue
        for tf in tfs:
            t0 = time.time()
            if tf not in cache:
                cache[tf] = bars(tf)
            tr = fn(cache[tf], **kw)
            s = summarize(tr)
            res[f"{name} | {tf}"] = s
            a, d, k = s.get("tutto", {}), s.get("2005-2015", {}), s.get("2016-2026", {})
            print(f"{name:34s} {tf:4s} trade {a.get('n', 0):5d} ({a.get('per_anno', 0)}/anno) win {a.get('win')} "
                  f"R {a.get('r_medio')} PF {a.get('pf')} anni+ {a.get('anni_pos')} | 05-15 R {d.get('r_medio')} "
                  f"| 16-26 R {k.get('r_medio')} | rischio1%: {a.get('crescita_annua_rischio1')}%/anno DD {a.get('dd_max')}%"
                  f"  [{time.time() - t0:.0f}s]", flush=True)
            tr.to_csv(OUT / f"trades_{name.split()[0]}_{tf}.csv", index=False)
            p.write_text(json.dumps(res, indent=1, default=str))


if __name__ == "__main__":
    main()
