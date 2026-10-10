"""ML signal filter (independent reconstruction of the idea shown in the Interstellar material:
gradient boosting scores every cell signal; a 'living threshold' = 80% quantile of the last 1000
scores keeps the best 20%).

Leakage controls:
* features are computed at the decision-bar close (raptor.features); labels are the isolated
  outcome of the signal under the SAME execution rules used by the backtest (engine._label);
* purge/embargo: a training row is dropped if its exit_time is >= the start of the next fold;
* early stopping uses a later, disjoint time slice (inner validation), never the evaluated period;
* the living threshold is causal: the quantile at signal t uses only scores of signals before t
  (seeded with the scores of the inner-validation slice).
"""
from dataclasses import dataclass
import numpy as np
import pandas as pd
import lightgbm as lgb

DEFAULT_PARAMS = dict(objective="regression", learning_rate=0.02, num_leaves=15, min_data_in_leaf=80,
                      feature_fraction=0.7, bagging_fraction=0.8, bagging_freq=1, lambda_l2=5.0,
                      verbose=-1, seed=7, num_threads=4)


@dataclass
class FitResult:
    model: lgb.Booster
    features: list
    seed_scores: np.ndarray
    best_iter: int
    inner_valid_corr: float


def _xy(lab, X, clip=(-1.2, 4.0)):
    m = lab.filled.values & np.isfinite(lab.r.values)
    return X[m], lab.r.values[m].clip(*clip), lab[m]


def fit(lab: pd.DataFrame, X: pd.DataFrame, train_end: str, inner_valid_start: str, params=None,
        max_rounds=3000) -> FitResult:
    """Train on [.., inner_valid_start) and early-stop on [inner_valid_start, train_end)."""
    p = dict(DEFAULT_PARAMS, **(params or {}))
    tr = (lab.bar_time < inner_valid_start) & (lab.exit_time < pd.Timestamp(inner_valid_start))
    va = (lab.bar_time >= inner_valid_start) & (lab.bar_time < train_end) & (lab.exit_time < pd.Timestamp(train_end))
    Xt, yt, _ = _xy(lab[tr], X[tr]); Xv, yv, _ = _xy(lab[va], X[va])
    dt = lgb.Dataset(Xt, yt); dv = lgb.Dataset(Xv, yv, reference=dt)
    bst = lgb.train(p, dt, max_rounds, valid_sets=[dv], callbacks=[lgb.early_stopping(200, verbose=False)])
    sv = bst.predict(Xv, num_iteration=bst.best_iteration)
    corr = float(np.corrcoef(sv, yv)[0, 1]) if len(yv) > 2 else float("nan")
    # refit on the full training window (train + inner valid) with the chosen number of rounds
    full = (lab.bar_time < train_end) & (lab.exit_time < pd.Timestamp(train_end))
    Xf, yf, _ = _xy(lab[full], X[full])
    bst2 = lgb.train(p, lgb.Dataset(Xf, yf), max(50, bst.best_iteration))
    seed = bst2.predict(X[va].values)
    return FitResult(bst2, list(X.columns), seed, bst.best_iteration, corr)


def living_threshold(scores: np.ndarray, seed: np.ndarray, window=1000, q=0.80) -> np.ndarray:
    """Threshold for each signal = q-quantile of the previous `window` scores (causal)."""
    buf = list(seed[-window:])
    thr = np.empty(len(scores))
    for i, s in enumerate(scores):
        thr[i] = np.quantile(buf, q) if len(buf) else -np.inf
        buf.append(s)
        if len(buf) > window:
            buf.pop(0)
    return thr


def explain_rejections(model: lgb.Booster, X: pd.DataFrame, top=3) -> list:
    """Top-k features pushing the score DOWN (SHAP contributions) - the 'journal of reasons'."""
    contrib = model.predict(X.values, pred_contrib=True)[:, :-1]
    cols = np.array(X.columns)
    order = np.argsort(contrib, axis=1)[:, :top]
    return [", ".join(f"{cols[j]}({contrib[i, j]:+.3f})" for j in order[i]) for i in range(len(X))]
