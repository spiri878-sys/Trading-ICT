"""Strategy (cell) tests on synthetic data: geometry, causality, registry and MQL5 static check."""
import subprocess, sys
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

from raptor.setups import build_features
from raptor.strategies import REGISTRY, SITE_SIX
from test_no_lookahead import synth_m1

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def feats():
    m1 = synth_m1(n=60 * 24 * 25, seed=3)
    return m1, build_features(m1, "5min", 3)


@pytest.mark.parametrize("cell", sorted(REGISTRY))
def test_cell_geometry(feats, cell):
    _, f = feats
    s = REGISTRY[cell](f, {})
    assert set(["bar_time", "side", "price", "sl_struct", "atr", "expiry_bars", "strategy"]).issubset(s.columns)
    if len(s):
        risk = (s.price - s.sl_struct) * s.side
        assert (risk > 0).all(), f"{cell}: stop on the wrong side"
        assert s.side.isin([1, -1]).all()
        assert (s.strategy == cell).all()


@pytest.mark.parametrize("cell", sorted(REGISTRY))
def test_cell_causal(feats, cell):
    """Signals up to time T must be identical whether or not data after T exist."""
    m1, f = feats
    cut = m1.index[len(m1) * 3 // 4]
    part = build_features(m1[m1.index < cut], "5min", 3)
    a = REGISTRY[cell](f, {}); b = REGISTRY[cell](part, {})
    lim = cut - pd.Timedelta(days=1)   # daily/HTF context must be final for both
    a = a[a.bar_time < lim].reset_index(drop=True)[["bar_time", "side", "price", "sl_struct"]]
    b = b[b.bar_time < lim].reset_index(drop=True)[["bar_time", "side", "price", "sl_struct"]]
    pd.testing.assert_frame_equal(a, b)


def test_site_six_mapped():
    assert set(SITE_SIX.values()).issubset(REGISTRY)


def test_mql5_static_check():
    r = subprocess.run([sys.executable, str(ROOT / "tools" / "mql5_static_check.py")], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
