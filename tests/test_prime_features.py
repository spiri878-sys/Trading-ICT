import numpy as np
import pandas as pd

from raptor.prime import cells as C
from raptor.prime.features import M1Context, prime_features
from raptor.setups import build_features

from test_prime_cells import _synthetic_m1


def _feats(m1, sig_cut=None):
    F = {(tf, 3): build_features(m1, tf, 3) for tf in set(C.TF_OF.values())}
    sig = C.generate(F, params={"PO3": {"min_disp": 0.5, "min_fvg": 0.02}})
    if sig_cut is not None:
        sig = sig[sig.known_at <= sig_cut].reset_index(drop=True)
    return sig, prime_features(sig, F, M1Context(m1))


def test_feature_truncation_invariance():
    m1 = _synthetic_m1(days=12)
    cut = m1.index[len(m1) // 2]
    lim = cut - pd.Timedelta(hours=26)  # D1/H4 context of the truncated series is complete before this
    s_full, x_full = _feats(m1, sig_cut=lim)
    s_part, x_part = _feats(m1.loc[:cut], sig_cut=lim)
    assert len(s_full) > 20 and len(s_full) == len(s_part)
    pd.testing.assert_frame_equal(x_full.reset_index(drop=True), x_part.reset_index(drop=True))


def test_no_absolute_prices():
    m1 = _synthetic_m1(days=8)
    _, x = _feats(m1)
    m2 = m1.copy()
    m2[["open", "high", "low", "close"]] *= 2.0  # same path, doubled price level (ATR doubles too)
    _, x2 = _feats(m2)
    scale_free = [c for c in x.columns if not c.startswith("spread_")]  # spread is a fixed $ amount (C1)
    np.testing.assert_allclose(x[scale_free].values, x2[scale_free].values, rtol=1e-6, atol=1e-6)


def test_side_applied_to_directional_features():
    m1 = _synthetic_m1(days=8)
    F = {(tf, 3): build_features(m1, tf, 3) for tf in set(C.TF_OF.values())}
    sig = C.generate(F, cells=["LS"]).iloc[:5].reset_index(drop=True)
    flip = sig.copy()
    flip["side"] = -sig.side
    x, xf = (prime_features(s, F, M1Context(m1)) for s in (sig, flip))
    for col in ("push_60m_atr_h1", "dist_h1_ema", "h4_trend_al", "efficiency_4h_signed"):
        np.testing.assert_allclose(xf[col].values, -x[col].values, atol=1e-9)
