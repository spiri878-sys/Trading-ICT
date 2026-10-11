import numpy as np
import pandas as pd

from raptor.prime import models as M


def _df(n=4000, seed=0):
    rng = np.random.default_rng(seed)
    t = pd.Series(pd.date_range("2008-01-01", "2017-12-31", periods=n))
    x = rng.normal(size=(n, 3))
    y = (x[:, 0] + rng.normal(size=n) > 0.5).astype(float)
    return pd.DataFrame({"known_at": t, "f_a": x[:, 0], "f_b": x[:, 1], "f_c": x[:, 2], "y": y})


def test_oof_never_trains_on_future_or_embargo():
    df = _df()
    seen = []

    def spy(X, y, seed=0):
        seen.append(df.loc[X.index, "known_at"].max())
        return M.fit_lgbm(X, y, seed=seed, rounds=20)

    oof = M.walk_forward_oof(df, ["f_a", "f_b", "f_c"], "y", [2012, 2013], fit=spy, embargo_days=5)
    assert seen[0] < pd.Timestamp("2012-01-01") - pd.Timedelta(days=5)
    assert seen[1] < pd.Timestamp("2013-01-01") - pd.Timedelta(days=5)
    yrs = df.known_at.dt.year
    assert oof[yrs.isin([2012, 2013])].notna().all() and oof[~yrs.isin([2012, 2013])].isna().all()


def test_living_threshold_uses_only_past_scores():
    times = pd.date_range("2020-01-01", periods=300, freq="h").values
    s = np.r_[np.zeros(200), np.ones(100)]
    thr = M.living_threshold(s, times, window=100, q=0.8)
    assert np.isnan(thr[:50]).all()            # fewer than 50 past scores
    assert thr[200] == 0.0                      # only zeros in the past at the first 1
    s2 = s.copy(); s2[250:] = 5.0               # changing future scores must not change earlier thresholds
    thr2 = M.living_threshold(s2, times, window=100, q=0.8)
    np.testing.assert_array_equal(thr[:251], thr2[:251])


def test_majority_vote():
    P = np.array([[0.9, 0.1, 0.7], [0.8, 0.2, 0.5], [0.1, 0.9, 0.7], [0.7, 0.1, 0.1]])
    np.testing.assert_array_equal(M.majority_vote(P, 0.65), [True, False, False])  # 3 of 4 vs 1/4 vs 2/4


def test_pct_rank_and_reproducibility():
    assert M.pct_rank([1, 2, 3, 4], [0, 2.5, 4]).tolist() == [0.0, 0.5, 1.0]
    df = _df(2000)
    a = M.fit_lgbm(df[["f_a", "f_b", "f_c"]], df.y, seed=7, rounds=30).predict(df[["f_a", "f_b", "f_c"]])
    b = M.fit_lgbm(df[["f_a", "f_b", "f_c"]], df.y, seed=7, rounds=30).predict(df[["f_a", "f_b", "f_c"]])
    np.testing.assert_array_equal(a, b)
