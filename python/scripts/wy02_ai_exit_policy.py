"""WY-02: AI trade management = per-trade choice among 5 exit policies (range TP, range TP + 50% at 1R + BE,
vendor ladder, TP 2R, 50% at 1R + BE + 2ATR trailing) or SKIP, by per-policy LightGBM regressors of net R
trained ONLY on previous years (expanding walk-forward 2020-2026). Signals: union of all Wyckoff-MTF grid
signal sets (deduplicated by bar/side). Compared with each fixed policy and with 'best policy so far'."""
import sys, json, itertools
from dataclasses import replace
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np, pandas as pd, lightgbm as lgb
from raptor import pipeline as P, metrics as M
from raptor.engine import label
from raptor.strategies import REGISTRY
from raptor.features import signal_features
from raptor.costs import C1, with_cost

ROOT = Path(__file__).resolve().parents[2]
EXITS = {
    "range_tp":   (dict(p1_frac=0.0, p2_frac=0.0, be_after_p1=False, max_hold_min=5 * 1440), True),
    "range_be1R": (dict(p1_r=1.0, p1_frac=0.5, p2_frac=0.0, be_after_p1=True, mgmt_on_close=True, max_hold_min=5 * 1440), True),
    "ladder":     (dict(tp_r=4.0, p1_r=0.7, p1_frac=0.2, p2_r=2.0, p2_frac=0.2, be_after_p1=True, mgmt_on_close=True, max_hold_min=4320), False),
    "tp2R":       (dict(tp_r=2.0, p1_frac=0.0, p2_frac=0.0, be_after_p1=False, max_hold_min=2880), False),
    "trail":      (dict(tp_r=6.0, p1_r=1.0, p1_frac=0.5, p2_frac=0.0, be_after_p1=True, mgmt_on_close=True, trail_atr=2.0, max_hold_min=5 * 1440), False),
}
GRID = dict(range_h=[48, 72, 120], event_h=[4, 8], min_tv=[0.0, 1.5], max_pos=[0.35, 0.5], entry=["sos", "lps"])
LGB = dict(objective="regression", learning_rate=0.03, num_leaves=7, min_data_in_leaf=40, feature_fraction=0.7,
           bagging_fraction=0.8, bagging_freq=1, lambda_l2=10.0, verbose=-1, seed=7, num_threads=4)
f = P.feats("15min", 3)
sigs = [REGISTRY["WYCKOFF_MTF"](f, dict(zip(GRID, v))) for v in itertools.product(*GRID.values())]
S = pd.concat(sigs).sort_values(["bar_time", "tp_r"]).drop_duplicates(["bar_time", "side"]).reset_index(drop=True)
X = signal_features(f, S)
R = {}
for en, (ex, use_tp) in EXITS.items():
    s = S if use_tp else S.drop(columns="tp_r")
    with with_cost(C1, replace(P.Params(), **ex)) as prm:
        lab = label(P.market(), s, prm, 15)
    R[en] = lab.r.values
filled = np.isfinite(R["tp2R"])
yr = S.bar_time.dt.year.values
ex_t = lab.exit_time.values
res = {"signals_unique": int(len(S)), "filled": int(filled.sum())}
fixed = {en: [] for en in EXITS}; ai = []; ai_take = []; best_prev = []
per_year = {}
for Y in range(2020, 2027):
    tr = filled & (ex_t < np.datetime64(f"{Y}-01-01"))
    te = filled & (yr == Y)
    if te.sum() == 0:
        continue
    preds = {}
    for en in EXITS:
        y = np.clip(R[en][tr], -1.2, 6)
        m = lgb.train(LGB, lgb.Dataset(X[tr], y), 150)
        preds[en] = m.predict(X[te].values)
    pm = pd.DataFrame(preds)
    choice = pm.idxmax(axis=1).values
    best_val = pm.max(axis=1).values
    realized = np.array([R[c][np.flatnonzero(te)[i]] for i, c in enumerate(choice)])
    take = best_val > 0
    prev_best = max(EXITS, key=lambda en: np.nanmean(R[en][tr]))
    for en in EXITS:
        fixed[en].extend(R[en][te].tolist())
    ai.extend(realized.tolist()); ai_take.extend(realized[take].tolist()); best_prev.extend(R[prev_best][te].tolist())
    per_year[Y] = {"n": int(te.sum()), "ai_all_policy": round(float(realized.mean()), 3),
                   "ai_with_skip": [int(take.sum()), round(float(realized[take].mean()), 3) if take.any() else None],
                   "prev_best_policy": [prev_best, round(float(np.nanmean(R[prev_best][te])), 3)],
                   **{en: round(float(np.nanmean(R[en][te])), 3) for en in EXITS}}
res["OOS_2020_2026"] = {"AI_choose_policy": M.r_stats(pd.Series(ai)), "AI_choose_policy_or_skip": M.r_stats(pd.Series(ai_take)),
                        "best_policy_so_far": M.r_stats(pd.Series(best_prev)),
                        **{f"fixed_{en}": M.r_stats(pd.Series(v)) for en, v in fixed.items()}}
res["per_year"] = per_year
(ROOT / "experiments" / "wy02_ai_exit_policy.json").write_text(json.dumps(res, indent=1, default=str))
print(json.dumps(res["OOS_2020_2026"], indent=1))
print(pd.DataFrame(per_year).T.to_string())
