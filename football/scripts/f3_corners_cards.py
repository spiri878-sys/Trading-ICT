"""F3 — angoli e cartellini: modelli LightGBM (Poisson) per angoli casa/ospite e gialli casa/ospite, riaddestrati
ogni stagione sulle stagioni precedenti (solo partite con la statistica). Distribuzione: binomiale negativa con
dispersione stimata sul solo addestramento. Valutazione 2013-2026: log-loss delle linee più giocate contro la
frequenza storica del campionato (stimata solo sul passato).

usage: python football/scripts/f3_corners_cards.py
"""
import json
import sys
import time
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd
from scipy.stats import nbinom

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fb.data import CACHE, ROOT, matches  # noqa: E402

P = dict(learning_rate=0.03, num_leaves=31, min_data_in_leaf=300, feature_fraction=0.7, bagging_fraction=0.8,
         bagging_freq=1, lambda_l2=10.0, verbose=-1, num_threads=4, seed=7, objective="poisson")
TARGETS = {"cor_h": "HomeCorners", "cor_a": "AwayCorners", "yel_h": "HomeYellow", "yel_a": "AwayYellow"}
LINES = {"cor": [8.5, 9.5, 10.5, 11.5], "yel": [2.5, 3.5, 4.5, 5.5]}


def nb_cdf_total(mu, k, line):
    """P(totale > line) con totale ~ binomiale negativa di media mu e dispersione k (var = mu + mu^2/k)."""
    p = k / (k + mu)
    return 1 - nbinom.cdf(np.floor(line), k, p)


def ll_bin(p, y):
    p = np.clip(p, 1e-6, 1 - 1e-6)
    return float(-(y * np.log(p) + (1 - y) * np.log(1 - p)).mean())


def main():
    t0 = time.time()
    m = matches()
    X = pd.read_parquet(CACHE / "f2_features.parquet")
    X["div_code"] = m.Division.astype("category").cat.codes
    feats = list(X.columns)
    pred = pd.DataFrame(index=m.index, columns=list(TARGETS), dtype=float)
    disp = {}
    cached = (CACHE / "f3_preds.parquet").exists() and "--riusa" in sys.argv
    for s in ([] if cached else range(2006, 2027)):
        te = (m.season == s).values
        for t, col in TARGETS.items():
            tr = (m.season < s).values & m[col].notna().values
            tt = te & m[col].notna().values
            if tt.sum() == 0 or tr.sum() < 5000:
                continue
            mdl = lgb.train(P, lgb.Dataset(X.loc[tr, feats], m.loc[tr, col].values), 300)
            pred.loc[tt, t] = mdl.predict(X.loc[tt, feats])
        print(f"[{time.time() - t0:5.0f}s] stagione {s}", flush=True)
    if cached:
        pred = pd.read_parquet(CACHE / "f3_preds.parquet")
    else:
        pred.to_parquet(CACHE / "f3_preds.parquet")
    rep = {}
    for fam, (hc, ac) in {"cor": ("HomeCorners", "AwayCorners"), "yel": ("HomeYellow", "AwayYellow")}.items():
        mu = pred[f"{fam}_h"] + pred[f"{fam}_a"]
        tot = m[hc] + m[ac]
        ok = mu.notna() & tot.notna()
        # dispersione: stimata sulle stagioni 2006-2012 (passato rispetto alla verifica)
        cal = ok & (m.season <= 2012)
        r = (tot[cal] - mu[cal]) ** 2 - mu[cal]
        k = float(max((mu[cal] ** 2).sum() / max(r.sum(), 1e-6), 1.0))
        disp[fam] = k
        ev = ok & (m.season >= 2013)
        out = {"n": int(ev.sum()), "dispersione_k": round(k, 2), "media_prevista": round(float(mu[ev].mean()), 2),
               "media_reale": round(float(tot[ev].mean()), 2),
               "correlazione_prevista_reale": round(float(np.corrcoef(mu[ev], tot[ev])[0, 1]), 3)}
        for line in LINES[fam]:
            y = (tot[ev] > line).astype(float).values
            p = nb_cdf_total(mu[ev].values, k, line)
            base = []
            for d, g in m[ev].groupby("Division"):
                hist = (m[hc] + m[ac])[(m.Division == d) & (m.season < 2013)].dropna()
                fr = float((hist > line).mean()) if len(hist) > 200 else float((tot[cal].dropna() > line).mean())
                base.append(pd.Series(fr, index=g.index))
            b = pd.concat(base).reindex(m[ev].index).values
            out[f"over{line}"] = {"freq_reale": round(float(y.mean()), 3), "prob_media_modello": round(float(p.mean()), 3),
                                  "logloss_modello": round(ll_bin(p, y), 4), "logloss_frequenza_campionato": round(ll_bin(b, y), 4)}
        rep[{"cor": "angoli_totali", "yel": "gialli_totali"}[fam]] = out
    (ROOT / "output" / "f3_corners_cards_eval.json").write_text(json.dumps(rep, indent=1))
    print(json.dumps(rep, indent=1))


if __name__ == "__main__":
    main()
