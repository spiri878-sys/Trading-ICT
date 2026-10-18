"""FASE 15 — controlli sulla regola T2 (ritracciamento nel trend): anni, lato, costi doppi, conto da 116 $ a 0,01 lotti.

usage: python python/scripts/phase15_check.py
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import phase15_small_stop as P  # noqa: E402


def sim_side(m1, s, stop, k):
    tr = P.simulate(m1, s, stop, k)
    tr["side"] = s.set_index("time").side.reindex(tr.time).values
    return tr


def account(tr, start=116.0, risk=None, stop=5.0):
    """Conto reale: 0,01 lotti (1 $ per $ di movimento). Con risk: lotti = conto*risk/stop arrotondati a 0,01, min 0,01."""
    eq, peak, mdd, out = start, start, 0.0, []
    for usd in tr.usd.values:
        lots = 1 if risk is None else max(1, int(eq * risk / stop))
        eq += usd * lots
        peak = max(peak, eq)
        mdd = max(mdd, 1 - eq / peak)
        out.append(eq)
        if eq <= stop:
            return {"finale": round(eq, 1), "dd_max": round(mdd * 100, 1), "rovina": True, "trade": len(out)}
    return {"finale": round(eq, 1), "dd_max": round(mdd * 100, 1), "rovina": False, "trade": len(out)}


def main():
    m1, h1, h4, d1 = P.load()
    sig = P.signals(h1, h4, d1, np.random.default_rng(7))
    s = sig[sig.rule == "T2"].sort_values("time")
    rep = {}
    for stop, k in ((5.0, 2.0), (5.0, 3.0), (8.0, 2.0), (3.0, 3.0)):
        tr = sim_side(m1, s, stop, k)
        key = f"stop{stop:g}_k{k:g}"
        y = tr.groupby(tr.time.dt.year).usd.agg(["count", "sum"])
        rep[key] = {"per_anno": {int(a): [int(b), round(c, 1)] for a, (b, c) in y.iterrows()},
                    "long_R": round(tr[tr.side > 0].usd.mean() / stop, 3), "short_R": round(tr[tr.side < 0].usd.mean() / stop, 3),
                    "n_long": int((tr.side > 0).sum()), "n_short": int((tr.side < 0).sum()),
                    "R_costi_doppi": round((tr.usd - P.COST).mean() / stop, 3),
                    "serie_perse_max": int(max((len(list(g)) for v, g in __import__("itertools").groupby(tr.usd < 0) if v), default=0))}
        for start in ("2016-01-01", "2020-01-01", "2024-01-01"):
            x = tr[tr.time >= start]
            rep[key][f"conto_116_da_{start[:4]}_lotto_fisso"] = account(x, stop=stop)
            rep[key][f"conto_116_da_{start[:4]}_rischio_2pct"] = account(x, risk=0.02, stop=stop)
        print(key, json.dumps(rep[key]), flush=True)
    (P.OUT / "t2_checks.json").write_text(json.dumps(rep, indent=1))


if __name__ == "__main__":
    main()
