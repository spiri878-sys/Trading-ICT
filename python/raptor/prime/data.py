"""Dati della ricostruzione PRIME: serie M1 master 2004-2026 e maschera dei giorni degradati (Fase 0)."""
from functools import lru_cache
from pathlib import Path

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[3]


@lru_cache(maxsize=1)
def config() -> dict:
    return yaml.safe_load((ROOT / "configs" / "config.yaml").read_text())


@lru_cache(maxsize=1)
def master_m1() -> pd.DataFrame:
    return pd.read_parquet(ROOT / config()["data"]["master_m1"])


@lru_cache(maxsize=1)
def degraded_days() -> pd.DatetimeIndex:
    dq = pd.read_parquet(ROOT / config()["data"]["day_quality"])
    return pd.DatetimeIndex(dq.index[dq.degraded])
