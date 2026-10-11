"""MASS-01: brute-force search for 'every month profitable' over ~1,850 strategy sleeves already labelled in this
project (ICT, Wyckoff, breakout, trend, mean reversion, OCO; long/short split) and their combinations:
all singles, all PAIRS (~1.7M), 1,000,000 random TRIPLES. Each sleeve = sum of R per month at equal risk per trade.
SEARCH only on 2018-01..2022-12 (60 months); the best candidates are then checked ONCE on 2023-01..2026-09
(45 months never used for the search)."""
import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np, pandas as pd

ROOT = Path(__file__).resolve().parents[2]
months = pd.period_range("2018-01", "2026-09", freq="M")
DEV = months < pd.Period("2023-01", "M")
series = {}


def add(df, key_cols, rcol, prefix):
    df = df.copy()
    df["m"] = pd.to_datetime(df.exit_time).dt.to_period("M")
    df["key"] = prefix + "|" + df[key_cols].astype(str).agg("|".join, axis=1)
    g = df.groupby(["key", "m"])[rcol].sum().unstack(fill_value=0.0)
    for k, row in g.iterrows():
        series[k] = row.reindex(months, fill_value=0.0).values


f1 = pd.read_parquet(ROOT / "experiments" / "fam01_labels.parquet"); add(f1, ["cfg", "side"], "r", "FAM")
oc = pd.read_parquet(ROOT / "experiments" / "oco02_all_trades.parquet"); add(oc, ["cfg"], "r_mult", "OCO")
wf = pd.read_parquet(ROOT / "data" / "processed" / "wf01_labels.parquet"); add(wf, ["pool", "strategy", "side"], "r", "ICT")
wy = pd.read_parquet(ROOT / "data" / "processed" / "wy01_labels.parquet"); add(wy, ["cfg", "side"], "r", "WYK")
keys = np.array(list(series)); X = np.vstack([series[k] for k in keys])          # sleeves x months
Xd, Xt = X[:, DEV], X[:, ~DEV]
n = len(keys)
print("sleeves:", n, "dev months:", Xd.shape[1], "test months:", Xt.shape[1])


def score(M):  # share of positive months, tie-break mean
    return (M > 0).mean(axis=-1), M.mean(axis=-1)


res = {}
# singles
s_pos, s_mean = score(Xd)
order = np.lexsort((-s_mean, -s_pos))
top = order[:20]
res["singles_best_dev"] = [{"sleeve": keys[i], "dev_pos_pct": round(float(s_pos[i] * 100), 1),
                            "test_pos_pct": round(float((Xt[i] > 0).mean() * 100), 1),
                            "test_mean_R_month": round(float(Xt[i].mean()), 2)} for i in top[:10]]
# pairs: all, chunked
best_pairs = []   # (dev_pos, dev_mean, i, j)
for i in range(n):
    P = Xd[i] + Xd[i + 1:]
    pos = (P > 0).mean(axis=1); mean = P.mean(axis=1)
    k = np.flatnonzero(pos >= 0.65)
    for j in k:
        best_pairs.append((pos[j], mean[j], i, i + 1 + j))
best_pairs.sort(key=lambda x: (-x[0], -x[1]))
n_pairs = n * (n - 1) // 2
res["pairs_tested"] = int(n_pairs)
res["pairs_with_dev_pos_ge_65pct"] = len(best_pairs)
res["pairs_with_dev_pos_100pct"] = int(sum(1 for b in best_pairs if b[0] >= 0.999))
res["pairs_max_dev_pos_pct"] = round(float(best_pairs[0][0] * 100), 1) if best_pairs else None
if best_pairs:
    top_p = best_pairs[:1000]
    tvp = np.array([((Xt[i] + Xt[j]) > 0).mean() * 100 for _, _, i, j in top_p])
    res["top1000_pairs_dev_mean_pos_pct"] = round(float(np.mean([p for p, _, _, _ in top_p]) * 100), 1)
    res["top1000_pairs_TEST_mean_pos_pct"] = round(float(tvp.mean()), 1)
    res["top1000_pairs_TEST_best_pos_pct"] = round(float(tvp.max()), 1)
res["pairs_best_dev"] = [{"sleeves": [keys[i], keys[j]], "dev_pos_pct": round(float(p * 100), 1),
                          "test_pos_pct": round(float(((Xt[i] + Xt[j]) > 0).mean() * 100), 1),
                          "test_mean_R_month": round(float((Xt[i] + Xt[j]).mean()), 2),
                          "test_worst_month_R": round(float((Xt[i] + Xt[j]).min()), 2)} for p, m, i, j in best_pairs[:10]]
# 1,000,000 random triples
rng = np.random.default_rng(11)
T = 1_000_000
best_tr = []
for b in range(0, T, 50_000):
    I = rng.integers(0, n, size=(50_000, 3))
    S = Xd[I[:, 0]] + Xd[I[:, 1]] + Xd[I[:, 2]]
    pos = (S > 0).mean(axis=1); mean = S.mean(axis=1)
    k = np.flatnonzero(pos >= 0.65)
    best_tr.extend([(pos[q], mean[q], tuple(I[q])) for q in k])
best_tr.sort(key=lambda x: (-x[0], -x[1]))
res["triples_tested"] = T
res["triples_with_dev_pos_ge_65pct"] = len(best_tr)
res["triples_max_dev_pos_pct"] = round(float(best_tr[0][0] * 100), 1) if best_tr else None
res["triples_with_dev_pos_100pct"] = int(sum(1 for b in best_tr if b[0] >= 0.999))
def tri_eval(t):
    st = Xt[list(t)].sum(axis=0)
    return round(float((st > 0).mean() * 100), 1), round(float(st.mean()), 2), round(float(st.min()), 2)
res["triples_best_dev"] = [{"sleeves": [keys[i] for i in t], "dev_pos_pct": round(float(p * 100), 1),
                            "test_pos_pct": tri_eval(t)[0], "test_mean_R_month": tri_eval(t)[1], "test_worst_month_R": tri_eval(t)[2]}
                           for p, m, t in best_tr[:10]]
# how well does the dev score predict the test score among the top 1000 triples?
if best_tr:
    top_t = best_tr[:1000]
    dv = np.array([p for p, _, _ in top_t]); tv = np.array([tri_eval(t)[0] for _, _, t in top_t])
    res["top1000_triples_dev_mean_pos_pct"] = round(float(dv.mean() * 100), 1)
    res["top1000_triples_TEST_mean_pos_pct"] = round(float(tv.mean()), 1)
    res["top1000_triples_TEST_best_pos_pct"] = round(float(tv.max()), 1)
    res["top1000_triples_TEST_share_100pct"] = round(float((tv >= 99.9).mean() * 100), 2)
(ROOT / "reports" / "mass01_monthly_search.json").write_text(json.dumps(res, indent=1, default=str))
print(json.dumps({k: v for k, v in res.items() if not k.endswith("best_dev")}, indent=1))
for k in ("singles_best_dev", "pairs_best_dev", "triples_best_dev"):
    print("==", k)
    for r in res[k][:5]:
        print(r)
