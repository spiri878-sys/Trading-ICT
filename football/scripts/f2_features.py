"""F2 — costruisce le feature pre-partita di tutte le 238.858 partite: data/cache/f2_features.parquet

usage: python football/scripts/f2_features.py
"""
import sys
import time
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fb.data import CACHE, matches  # noqa: E402
from fb.features import build  # noqa: E402

t0 = time.time()
m = matches()
f1 = pd.read_parquet(CACHE / "f1_goals.parquet")
assert (f1.mid.values == m.mid.values).all()
X = build(m, f1)
X.to_parquet(CACHE / "f2_features.parquet")
print(X.shape, f"{time.time() - t0:.0f}s")
print(X.notna().mean().round(2).to_string())
