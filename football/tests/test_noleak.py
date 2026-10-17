"""Nessuna informazione dal futuro: cambiare i risultati dal giorno X in poi non deve cambiare le feature fino a X."""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fb.data import matches  # noqa: E402
from fb.state import STATS, build_state  # noqa: E402


def test_state_no_lookahead():
    m = matches()
    m = m[(m.date >= "2025-08-01") & m.Division.isin(["E0", "I1", "E1"])].reset_index(drop=True)
    cut = m.date.iloc[len(m) // 2]
    a = build_state(m)
    rng = np.random.default_rng(0)
    m2 = m.copy()
    fut = m2.date >= cut
    for h, aw in STATS.values():
        for col in (h, aw):
            m2.loc[fut, col] = rng.integers(0, 9, fut.sum())
    b = build_state(m2)
    upto = (m.date <= cut).to_numpy()
    assert np.allclose(a[upto].to_numpy(), b[upto].to_numpy(), equal_nan=True)
    assert not np.allclose(a[~upto].to_numpy(), b[~upto].to_numpy(), equal_nan=True)
