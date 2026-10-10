"""Glue: data -> features -> signals -> labels / simulation."""
from functools import lru_cache
from pathlib import Path
import pandas as pd

from . import data as D
from .setups import build_features
from .strategies import REGISTRY
from .engine import Market, Params, run, label
from .features import signal_features

# Pre-registered periods (docs/validation_protocol.md). Frozen before any result was seen.
PERIODS = {
    "dev": ("2018-01-01", "2022-01-01"),
    "val": ("2022-01-01", "2024-01-01"),
    "test": ("2024-01-01", "2026-10-10"),
}
CACHE = D.PROCESSED


@lru_cache(maxsize=1)
def m1():
    return D.load_m1()


@lru_cache(maxsize=1)
def market():
    return Market(m1())


@lru_cache(maxsize=2)
def feats(tf: str = "5min", swing_k: int = 3):
    p = CACHE / f"feat_{tf}_k{swing_k}.parquet"
    if p.exists():
        return pd.read_parquet(p)
    f = build_features(m1(), tf, swing_k)
    f.to_parquet(p)
    return f


def signals(strategies: dict, tf="5min", swing_k=3) -> pd.DataFrame:
    """strategies: {name: params}; dict order = priority when signals share a bar."""
    f = feats(tf, swing_k)
    frames = []
    for prio, (name, p) in enumerate(strategies.items()):
        s = REGISTRY[name](f, p)
        if p.get("market_entry"):
            # enter at the next bar open instead of waiting for the retracement; risk measured from the close
            s["otype"] = "market"
            s["price"] = f.close.values[s.bar_i.values]
            s = s[(s.price - s.sl_struct) * s.side > 0]
        s["priority"] = prio
        frames.append(s)
    s = pd.concat(frames, ignore_index=True)
    s = s.sort_values(["bar_time", "priority"], kind="stable").reset_index(drop=True)
    # duplicate guard: one signal per (cell, side, bar)
    return s.drop_duplicates(["bar_time", "strategy", "side"]).reset_index(drop=True)


def apply_min_stop(sig: pd.DataFrame, f: pd.DataFrame, min_atr_m15: float) -> pd.DataFrame:
    """'STOP MINIMO IN ATR' (input seen in the RAPTOR PRIME tester video, E-12): the structural stop is
    moved out to at least `min_atr_m15` x ATR(M15). Flagged per signal in column `stop_floored`.
    This is a strategy rule chosen in the inputs, never a silent adaptation to broker limits."""
    if not min_atr_m15:
        return sig.assign(stop_floored=False)
    a15 = f.m15_atr.values[sig.bar_i.values]
    risk = (sig.price - sig.sl_struct) * sig.side
    need = min_atr_m15 * a15
    floored = risk < need
    sl = sig.price - sig.side * pd.Series(need, index=sig.index).where(floored, risk)
    return sig.assign(sl_struct=sl, stop_floored=floored)


def in_period(df, period, col="bar_time"):
    a, b = PERIODS[period] if isinstance(period, str) else period
    return df[(df[col] >= a) & (df[col] < b)]


def labelled(strategies: dict, prm: Params, tf="5min", swing_k=3, spread_mult=1.0, min_stop_m15=0.0):
    s = apply_min_stop(signals(strategies, tf, swing_k), feats(tf, swing_k), min_stop_m15)
    lab = label(market(), s, prm, int(pd.Timedelta(tf).total_seconds() // 60), spread_mult)
    X = signal_features(feats(tf, swing_k), s)
    return lab, X


def backtest(sig: pd.DataFrame, prm: Params, take=None, tf="5min", spread_mult=1.0):
    return run(market(), sig, prm, int(pd.Timedelta(tf).total_seconds() // 60), spread_mult, take)
