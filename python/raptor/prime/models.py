"""Catena AI della ricostruzione PRIME (Fase 5): modelli, walk-forward fuori campione, soglia viva, voto.

Nessun dato dopo il periodo di addestramento entra nei modelli; l'embargo elimina dal training i segnali degli
ultimi `embargo_days` giorni prima del periodo predetto (le etichette guardano fino a 3 giorni avanti).
"""
import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

LGB_PARAMS = dict(objective="binary", learning_rate=0.03, num_leaves=15, min_data_in_leaf=300,
                  feature_fraction=0.7, bagging_fraction=0.7, bagging_freq=1, lambda_l2=10.0, verbose=-1,
                  num_threads=4)
N_ROUNDS = 300


def fit_lgbm(X, y, seed=0, params=None, rounds=N_ROUNDS, objective=None):
    p = {**LGB_PARAMS, **(params or {}), "seed": seed}
    if objective:
        p["objective"] = objective
    return lgb.train(p, lgb.Dataset(X, label=y), num_boost_round=rounds)


def fit_mlp(X, y, seed=0):
    m = make_pipeline(SimpleImputer(strategy="median"), StandardScaler(),
                      MLPClassifier(hidden_layer_sizes=(32, 16), alpha=1e-3, max_iter=60, early_stopping=True,
                                    random_state=seed))
    return m.fit(X, y)


def predict(model, X):
    if isinstance(model, lgb.Booster):
        return model.predict(X)
    return model.predict_proba(X)[:, 1]


def train_mask(times, pred_start, embargo_days=5, train_start=None):
    m = times < (pd.Timestamp(pred_start) - pd.Timedelta(days=embargo_days))
    if train_start is not None:
        m &= times >= pd.Timestamp(train_start)
    return m


def walk_forward_oof(df, feats, target, years, fit=fit_lgbm, train_start="2008-01-01", embargo_days=5, seed=0,
                     weight_col=None):
    """Predizioni fuori campione anno per anno: per l'anno Y il modello è addestrato su [train_start, 1/1/Y - embargo).
    Restituisce una Series allineata a df (NaN fuori dagli anni richiesti)."""
    out = pd.Series(np.nan, index=df.index)
    t = df.known_at
    for y in years:
        tr = train_mask(t, f"{y}-01-01", embargo_days, train_start) & df[target].notna()
        te = (t >= f"{y}-01-01") & (t < f"{y + 1}-01-01")
        if te.sum() == 0 or tr.sum() < 500:
            continue
        m = fit(df.loc[tr, feats], df.loc[tr, target].astype(float), seed=seed)
        out[te] = predict(m, df.loc[te, feats])
    return out


def living_threshold(scores, times, window=1000, q=0.8, warm=None):
    """Soglia viva (foto E-24): per ogni segnale, quantile q degli ultimi `window` punteggi PRECEDENTI (ordine
    temporale). Prima di avere `window` punteggi usa quelli disponibili (minimo 50) o `warm` se dato."""
    order = np.argsort(np.asarray(times), kind="stable")
    s = np.asarray(scores, float)[order]
    thr = np.full(s.size, np.nan)
    buf = [] if warm is None else list(np.asarray(warm, float)[-window:])
    for i in range(s.size):
        if len(buf) >= 50:
            thr[i] = np.quantile(buf[-window:], q)
        buf.append(s[i])
        if len(buf) > 4 * window:
            buf = buf[-window:]
    out = np.empty_like(thr)
    out[order] = thr
    return out


def pct_rank(ref, x):
    """Percentile di x rispetto alla distribuzione di riferimento ref (punteggi dell'addestramento)."""
    ref = np.sort(np.asarray(ref, float)[np.isfinite(ref)])
    return np.searchsorted(ref, np.asarray(x, float), side="right") / max(ref.size, 1)


def majority_vote(pcts, thr, k=None):
    """Occhio: ogni modello vota sì se il suo percentile >= thr; passa se almeno k voti (default maggioranza)."""
    P = np.asarray(pcts)
    k = k if k is not None else P.shape[0] // 2 + 1
    return (P >= thr).sum(axis=0) >= k


def perf(r, years=None):
    """Statistiche di una selezione di R (netti)."""
    r = pd.Series(np.asarray(r, float))
    if years is not None:
        years = pd.Series(np.asarray(years))[r.notna().values].values
    r = r.dropna()
    if r.empty:
        return dict(n=0)
    gp, gl = r[r > 0].sum(), -r[r < 0].sum()
    eq = r.cumsum()
    d = dict(n=int(len(r)), avg_r=round(float(r.mean()), 4), pf=round(float(gp / gl), 3) if gl > 0 else None,
             total_r=round(float(r.sum()), 1), max_dd_r=round(float((eq.cummax() - eq).max()), 1),
             win=round(float((r > 0).mean()), 3))
    if years is not None:
        ys = pd.Series(r.values, index=years)
        by = ys.groupby(level=0).sum()
        d["years_pos"] = f"{int((by > 0).sum())}/{len(by)}"
        d["r_by_year"] = {int(k): round(float(v), 1) for k, v in by.items()}
    return d
