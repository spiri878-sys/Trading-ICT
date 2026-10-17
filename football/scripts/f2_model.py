"""F2 — modello AI pre-partita, riaddestrato ogni stagione (walk-forward): per la stagione S si allena su tutte
le partite delle stagioni < S (tutti i campionati), poi predice S.

Modelli LightGBM: 1X2 (multiclasse), Over 2,5, Gol/NoGol, gol casa e gol ospite (Poisson).
Due varianti: SENZA quote (solo calcio) e CON quote (calcio + mercato).
Valutazione: log-loss contro le probabilità Bet365 senza margine, stagioni 2013-2026.
Output: data/cache/f2_preds.parquet, output/f2_model_eval.json

usage: python football/scripts/f2_model.py
"""
import json
import sys
import time
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fb.data import CACHE, ROOT, implied, matches  # noqa: E402

P = dict(learning_rate=0.03, num_leaves=31, min_data_in_leaf=400, feature_fraction=0.7, bagging_fraction=0.8,
         bagging_freq=1, lambda_l2=10.0, verbose=-1, num_threads=4, seed=7)
ROUNDS = 400
MARKET = ["mk_1", "mk_X", "mk_2", "mk_margin", "mk_over25", "ah_line"]


def log(msg, t0=[time.time()]):
    print(f"[{time.time() - t0[0]:6.0f}s] {msg}", flush=True)


def ll_multi(P_, y):
    return float(-np.log(np.clip(P_[np.arange(len(y)), y], 1e-9, 1)).mean())


def ll_bin(p, y):
    p = np.clip(p, 1e-9, 1 - 1e-9)
    return float(-(y * np.log(p) + (1 - y) * np.log(1 - p)).mean())


def main():
    m = matches()
    X = pd.read_parquet(CACHE / "f2_features.parquet")
    X["div_code"] = m.Division.astype("category").cat.codes
    y1x2 = m.FTResult.map({"H": 0, "D": 1, "A": 2}).values
    yo = ((m.hg + m.ag) > 2.5).astype(int).values
    ygg = ((m.hg > 0) & (m.ag > 0)).astype(int).values
    feats_all = list(X.columns)
    feats_nomk = [c for c in feats_all if c not in MARKET]
    preds = pd.DataFrame(index=m.index)
    for variant, feats in (("calcio", feats_nomk), ("calcio_mercato", feats_all)):
        for c in ("p1", "pX", "p2", "pover", "pgg", "mu_h", "mu_a"):
            preds[f"{variant}_{c}"] = np.nan
        for s in range(2008, 2027):
            tr = (m.season < s).values
            te = (m.season == s).values
            if te.sum() == 0:
                continue
            Xtr, Xte = X.loc[tr, feats], X.loc[te, feats]
            mdl = lgb.train({**P, "objective": "multiclass", "num_class": 3}, lgb.Dataset(Xtr, y1x2[tr]), ROUNDS)
            pr = mdl.predict(Xte)
            preds.loc[te, [f"{variant}_p1", f"{variant}_pX", f"{variant}_p2"]] = pr
            for tgt, col in ((yo, "pover"), (ygg, "pgg")):
                mdl = lgb.train({**P, "objective": "binary"}, lgb.Dataset(Xtr, tgt[tr]), ROUNDS)
                preds.loc[te, f"{variant}_{col}"] = mdl.predict(Xte)
            for tgt, col in ((m.hg.values, "mu_h"), (m.ag.values, "mu_a")):
                mdl = lgb.train({**P, "objective": "poisson"}, lgb.Dataset(Xtr, tgt[tr]), ROUNDS)
                preds.loc[te, f"{variant}_{col}"] = mdl.predict(Xte)
            log(f"{variant} stagione {s}: addestrato su {tr.sum()} partite, predette {te.sum()}")
    preds["mid"] = m.mid.values
    preds.to_parquet(CACHE / "f2_preds.parquet")
    # ---------------- valutazione 2013+
    ok = (m.season >= 2013) & (m.OddHome > 1) & (m.OddDraw > 1) & (m.OddAway > 1)
    bk = implied(m.loc[ok, ["OddHome", "OddDraw", "OddAway"]]).values
    y = y1x2[ok.values]
    f1 = pd.read_parquet(CACHE / "f1_goals.parquet")
    rep = {"1X2_logloss_2013_2026": {"n": int(ok.sum()), "bet365": ll_multi(bk, y),
                                     "motore_gol_F1": ll_multi(f1.loc[ok, ["p1", "pX", "p2"]].values, y)}}
    for v in ("calcio", "calcio_mercato"):
        rep["1X2_logloss_2013_2026"][f"AI_{v}"] = ll_multi(preds.loc[ok, [f"{v}_p1", f"{v}_pX", f"{v}_p2"]].values, y)
    ok2 = ok & (m.Over25 > 1) & (m.Under25 > 1)
    bko = implied(m.loc[ok2, ["Over25", "Under25"]]).values[:, 0]
    rep["OU25_logloss_2013_2026"] = {"n": int(ok2.sum()), "bet365": ll_bin(bko, yo[ok2.values]),
                                     "motore_gol_F1": ll_bin(f1.loc[ok2, "over2.5"].values, yo[ok2.values])}
    for v in ("calcio", "calcio_mercato"):
        rep["OU25_logloss_2013_2026"][f"AI_{v}"] = ll_bin(preds.loc[ok2, f"{v}_pover"].values, yo[ok2.values])
    gg = (m.season >= 2013).values
    rep["GG_logloss_2013_2026"] = {"n": int(gg.sum()), "frequenza_base": ll_bin(np.full(gg.sum(), ygg[m.season < 2013].mean()), ygg[gg]),
                                   "motore_gol_F1": ll_bin(f1.loc[gg, "gg"].values, ygg[gg])}
    for v in ("calcio", "calcio_mercato"):
        rep["GG_logloss_2013_2026"][f"AI_{v}"] = ll_bin(preds.loc[gg, f"{v}_pgg"].values, ygg[gg])
    (ROOT / "output" / "f2_model_eval.json").write_text(json.dumps(rep, indent=1))
    print(json.dumps(rep, indent=1))


if __name__ == "__main__":
    main()
