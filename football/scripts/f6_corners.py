"""F6 — angoli potenziati. Parte dal modello F3 (feature generali F2, LightGBM Poisson) e prova:

* feature specifiche per gli angoli: medie per campo (angoli della squadra di casa nelle ultime partite IN CASA,
  dell'ospite FUORI), medie esponenziali, media della stagione in corso, media della stagione precedente,
  quota di angoli e di tiri sul totale, media angoli del campionato (recente), forza del favorito dal mercato;
* modelli più capaci (più alberi, learning rate più basso) con numero di alberi scelto sulla stagione precedente;
* modello diretto del TOTALE oltre a casa + ospite;
* dispersione della binomiale negativa per campionato.

Tutto walk-forward: per ogni stagione s (2013-2026) si addestra su stagioni < s. Confronto sulle stesse partite
contro F3 e contro la frequenza del campionato. Tetto teorico: anche conoscendo la media vera, il totale degli
angoli ha rumore almeno di Poisson; la correlazione massima ottenibile è stimata e riportata.

usage: python football/scripts/f6_corners.py [--riusa]
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
from fb.corners import corner_feats, market_feats  # noqa: E402
from fb.data import CACHE, ROOT, matches  # noqa: E402

LINES = [7.5, 8.5, 9.5, 10.5, 11.5, 12.5]
P_F3 = dict(learning_rate=0.03, num_leaves=31, min_data_in_leaf=300, feature_fraction=0.7, bagging_fraction=0.8,
            bagging_freq=1, lambda_l2=10.0, verbose=-1, num_threads=4, seed=7, objective="poisson")
P_NEW = dict(learning_rate=0.02, num_leaves=31, min_data_in_leaf=800, feature_fraction=0.5, bagging_fraction=0.8,
             bagging_freq=1, lambda_l2=30.0, verbose=-1, num_threads=4, seed=7, objective="poisson")


def nb_over(mu, k, line):
    k = np.broadcast_to(np.asarray(k, float), np.shape(mu))
    return 1 - nbinom.cdf(np.floor(line), k, k / (k + mu))


def ll(p, y):
    p = np.clip(p, 1e-6, 1 - 1e-6)
    return float(-(y * np.log(p) + (1 - y) * np.log(1 - p)).mean())


def fit_k(mu, y):
    r = ((y - mu) ** 2 - mu).sum()
    return float(np.clip((mu ** 2).sum() / max(r, 1e-6), 2.0, 1e4))


def walk(m, X, feats, params, targets, seasons, rounds=None, tag=""):
    pred = pd.DataFrame(index=m.index, columns=list(targets), dtype=float)
    used = {}
    t0 = time.time()
    for s in seasons:
        te = (m.season == s).values
        for t, y in targets.items():
            ok = y.notna().values
            tr = (m.season < s).values & ok
            tt = te & ok
            if tt.sum() == 0:
                continue
            if rounds is None:
                # alberi scelti sull'ultima stagione disponibile (tenuta fuori), poi riaddestrato su tutto
                va = (m.season == s - 1).values & ok
                tr0 = (m.season < s - 1).values & ok
                b = lgb.train(params, lgb.Dataset(X.loc[tr0, feats], y[tr0].values), 2000,
                              valid_sets=[lgb.Dataset(X.loc[va, feats], y[va].values)],
                              callbacks=[lgb.early_stopping(100, verbose=False)])
                n = max(b.best_iteration, 100)
            else:
                n = rounds
            used[(s, t)] = n
            mdl = lgb.train(params, lgb.Dataset(X.loc[tr, feats], y[tr].values), n)
            pred.loc[tt, t] = mdl.predict(X.loc[tt, feats])
        print(f"[{tag} {time.time() - t0:5.0f}s] stagione {s} alberi {[used.get((s, t)) for t in targets]}",
              flush=True)
    return pred, used


def evaluate(m, mu, tot, ev, cal, k_mode="global"):
    if k_mode == "global":
        k = fit_k(mu[cal].values, tot[cal].values)
        kk = np.full(ev.sum(), k)
    else:
        ks = {d: fit_k(mu[cal & (m.Division == d)].values, tot[cal & (m.Division == d)].values)
              for d in m.Division[ev].unique() if (cal & (m.Division == d)).sum() > 300}
        kg = fit_k(mu[cal].values, tot[cal].values)
        kk = m.Division[ev].map(ks).fillna(kg).values
    e, y = mu[ev].values, tot[ev].values
    out = {"corr": round(float(np.corrcoef(e, y)[0, 1]), 4), "mae": round(float(np.abs(e - y).mean()), 3),
           "k_medio": round(float(np.mean(kk)), 1)}
    for line in LINES:
        out[f"ll_o{line}"] = round(ll(nb_over(e, kk, line), (y > line).astype(float)), 4)
    out["ll_media"] = round(float(np.mean([out[f"ll_o{x}"] for x in LINES])), 4)
    return out


def main():
    m = matches()
    X = pd.read_parquet(CACHE / "f2_features.parquet")
    X["div_code"] = m.Division.astype("category").cat.codes
    base_feats = list(X.columns)
    cf_path = CACHE / "f6_corner_feats.parquet"
    if cf_path.exists():
        C = pd.read_parquet(cf_path)
    else:
        t0 = time.time()
        C = corner_feats(m)
        C.to_parquet(cf_path)
        print(f"feature angoli: {C.shape} in {time.time() - t0:.0f}s", flush=True)
    F = market_feats(m, X)
    XA = pd.concat([X, C, F], axis=1)
    new_feats = base_feats + list(C.columns) + list(F.columns)
    tot = m.HomeCorners + m.AwayCorners
    targets_hs = {"cor_h": m.HomeCorners, "cor_a": m.AwayCorners}
    seasons = range(2010, 2027)

    pp = CACHE / "f6_preds.parquet"
    if pp.exists() and "--riusa" in sys.argv:
        P = pd.read_parquet(pp)
    else:
        P = pd.DataFrame(index=m.index)
        f3 = pd.read_parquet(CACHE / "f3_preds.parquet")
        P["f3"] = f3.cor_h + f3.cor_a
        a, _ = walk(m, XA, new_feats, P_F3, targets_hs, seasons, rounds=300, tag="nuove feature")
        P["nuove_feature"] = a.cor_h + a.cor_a
        P["nuove_feature_h"], P["nuove_feature_a"] = a.cor_h, a.cor_a
        b, used = walk(m, XA, new_feats, P_NEW, targets_hs, seasons, rounds=None, tag="nuove+tuning")
        P["nuove_tuning"] = b.cor_h + b.cor_a
        P["nuove_tuning_h"], P["nuove_tuning_a"] = b.cor_h, b.cor_a
        c, _ = walk(m, XA, new_feats, P_NEW, {"tot": tot}, seasons, rounds=None, tag="totale diretto")
        P["totale_diretto"] = c.tot
        P["media_mix"] = (P.nuove_tuning + P.totale_diretto) / 2
        P.to_parquet(pp)

    ok = tot.notna() & P.f3.notna() & P.nuove_tuning.notna() & P.totale_diretto.notna()
    ev = ok & (m.season >= 2013)
    cal = ok & (m.season.between(2010, 2012))
    rep = {"n_partite_verifica": int(ev.sum())}
    # frequenza di campionato (solo passato)
    base = {}
    for line in LINES:
        fr = pd.Series(np.nan, index=m.index)
        for d in m.Division[ev].unique():
            h = tot[(m.Division == d) & (m.season < 2013)].dropna()
            fr[(m.Division == d) & ev] = (h > line).mean() if len(h) > 200 else (tot[cal] > line).mean()
        base[f"ll_o{line}"] = round(ll(fr[ev].values, (tot[ev] > line).astype(float).values), 4)
    base["ll_media"] = round(float(np.mean([base[f"ll_o{x}"] for x in LINES])), 4)
    rep["frequenza_campionato"] = base
    for col in ("f3", "nuove_feature", "nuove_tuning", "totale_diretto", "media_mix"):
        rep[col] = evaluate(m, P[col], tot, ev, cal)
        rep[col + "_k_campionato"] = evaluate(m, P[col], tot, ev, cal, k_mode="div")
    # tetto teorico: varianza della media vera <= var(totale) - (rumore minimo, Poisson)
    v, mean = float(tot[ev].var()), float(tot[ev].mean())
    rep["tetto_teorico_corr_poisson"] = round(float(np.sqrt(max(v - mean, 0) / v)), 3)
    # per stagione: miglior modello contro F3
    best = min(("nuove_feature", "nuove_tuning", "totale_diretto", "media_mix"), key=lambda c: rep[c]["ll_media"])
    rep["migliore"] = best
    per = {}
    for s in sorted(m.season[ev].unique()):
        es = ev & (m.season == s)
        per[int(s)] = {"f3": evaluate(m, P.f3, tot, es, cal)["ll_media"],
                       best: evaluate(m, P[best], tot, es, cal)["ll_media"]}
    rep["per_stagione_ll_media"] = per
    rep["stagioni_migliori_di_f3"] = f"{sum(v[best] < v['f3'] for v in per.values())}/{len(per)}"
    # calibrazione per decile del totale previsto
    e = P[best][ev]
    q = pd.qcut(e, 10, labels=False)
    rep["decili_previsto_vs_reale"] = [[round(float(e[q == i].mean()), 2), round(float(tot[ev][q == i].mean()), 2)]
                                       for i in range(10)]
    (ROOT / "output" / "f6_corners_eval.json").write_text(json.dumps(rep, indent=1))
    print(json.dumps(rep, indent=1))


if __name__ == "__main__":
    main()
