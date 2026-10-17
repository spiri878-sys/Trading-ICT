"""F1 — valutazione del motore gol: log-loss di 1X2 e Over/Under 2,5 contro le probabilità del bookmaker
(Bet365, margine tolto). Scelta del passo di aggiornamento SOLO sulle stagioni 2000-2012; verifica 2013+.

usage: python football/scripts/f1_goals_eval.py
"""
import itertools
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fb.data import ROOT, implied, matches  # noqa: E402
from fb.goals import probs_vectorized, run_ratings  # noqa: E402

OUT = ROOT / "output"


def logloss_1x2(P, res):
    idx = res.map({"H": 0, "D": 1, "A": 2}).values
    return -np.log(np.clip(P[np.arange(len(P)), idx], 1e-9, 1)).mean()


def logloss_bin(p, y):
    p = np.clip(p, 1e-9, 1 - 1e-9)
    return -(y * np.log(p) + (1 - y) * np.log(1 - p)).mean()


def main():
    m = matches()
    res = {}
    best = None
    for lr, lrg, pen in itertools.product([0.008, 0.012, 0.02], [0.001, 0.002], [0.25, 0.4]):
        lh, la = run_ratings(m, lr=lr, lr_glob=lrg, promo_pen=pen)
        P, _ = probs_vectorized(lh, la)
        tr = (m.season <= 2012).values & (m.groupby("Division").cumcount().values > 300)
        ll = logloss_1x2(P[["p1", "pX", "p2"]].values[tr], m.FTResult[tr])
        res[f"lr{lr}_g{lrg}_pen{pen}"] = round(float(ll), 5)
        if best is None or ll < best[0]:
            best = (ll, lr, lrg, pen)
        print(lr, lrg, pen, round(ll, 5), flush=True)
    _, lr, lrg, pen = best
    lh, la = run_ratings(m, lr=lr, lr_glob=lrg, promo_pen=pen)
    P, _ = probs_vectorized(lh, la)
    m = m.assign(lh=lh, la=la, **{c: P[c].values for c in P.columns})
    m.to_parquet(ROOT / "data" / "cache" / "f1_goals.parquet") if (ROOT / "data" / "cache").mkdir(parents=True, exist_ok=True) is None else None
    te = (m.season >= 2013) & (m.OddHome > 1) & (m.OddDraw > 1) & (m.OddAway > 1)
    t = m[te]
    bk = implied(t[["OddHome", "OddDraw", "OddAway"]]).values
    ours = t[["p1", "pX", "p2"]].values
    rep = {"parametri_scelti_2000_2012": dict(lr=lr, lr_glob=lrg, promo_pen=pen), "griglia": res,
           "test_2013_2026_1X2": {"n": int(len(t)), "logloss_modello": round(float(logloss_1x2(ours, t.FTResult)), 5),
                                  "logloss_bet365": round(float(logloss_1x2(bk, t.FTResult)), 5),
                                  "logloss_uniforme": round(float(np.log(3)), 5)}}
    ou = t[(t.Over25 > 1) & (t.Under25 > 1)]
    y = ((ou.hg + ou.ag) > 2.5).astype(float).values
    bko = implied(ou[["Over25", "Under25"]]).values[:, 0]
    rep["test_2013_2026_OU25"] = {"n": int(len(ou)), "logloss_modello": round(float(logloss_bin(ou["over2.5"].values, y)), 5),
                                  "logloss_bet365": round(float(logloss_bin(bko, y)), 5)}
    # per divisione
    per = {}
    for d, g in t.groupby("Division"):
        b = implied(g[["OddHome", "OddDraw", "OddAway"]]).values
        per[d] = (round(float(logloss_1x2(g[["p1", "pX", "p2"]].values, g.FTResult)), 4),
                  round(float(logloss_1x2(b, g.FTResult)), 4), int(len(g)))
    rep["per_divisione_modello_vs_bet365"] = per
    OUT.mkdir(exist_ok=True)
    (OUT / "f1_goals_eval.json").write_text(json.dumps(rep, indent=1))
    print(json.dumps({k: v for k, v in rep.items() if k != "griglia"}, indent=1))


if __name__ == "__main__":
    main()
