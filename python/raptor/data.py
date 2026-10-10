"""Loading, validation and resampling of MT5-exported bar data.

The MT5 "Export bars" format is tab separated with header
<DATE> <TIME> <OPEN> <HIGH> <LOW> <CLOSE> <TICKVOL> <VOL> <SPREAD>.
Timestamps are broker *server time* (no timezone information in the file).
SPREAD is in symbol points (XAUUSD with 2 digits: 1 point = 0.01 USD) and, in MT5
exports, is the spread recorded for that bar (not an average over every tick).
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, asdict
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"

POINT_XAUUSD = 0.01


def sha256(path: Path, chunk: int = 1 << 22) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while b := f.read(chunk):
            h.update(b)
    return h.hexdigest()


def load_mt5_csv(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, sep="\t", dtype={"<DATE>": str, "<TIME>": str})
    df.columns = [c.strip("<>").lower() for c in df.columns]
    df.index = pd.to_datetime(df["date"] + " " + df["time"], format="%Y.%m.%d %H:%M:%S")
    df.index.name = "time"
    df = df.drop(columns=["date", "time"])
    return df.astype({"open": float, "high": float, "low": float, "close": float,
                      "tickvol": np.int64, "vol": np.int64, "spread": np.int64})


def load_m1(cache: bool = True) -> pd.DataFrame:
    """Load XAUUSD M1 (parquet cache if present)."""
    pq = PROCESSED / "XAUUSD_M1.parquet"
    if cache and pq.exists():
        return pd.read_parquet(pq)
    df = load_mt5_csv(RAW / "XAUUSD_M1.csv")
    df = clean(df)[0]
    if cache:
        PROCESSED.mkdir(parents=True, exist_ok=True)
        df.to_parquet(pq)
    return df


@dataclass
class QualityReport:
    rows: int
    first: str
    last: str
    duplicates: int
    non_monotonic: int
    ohlc_inconsistent: int
    non_positive: int
    zero_range_bars: int
    spread_zero_bars: int
    spread_quantiles_points: dict
    big_jumps_gt_2pct: int
    gaps_intraweek_gt_10min: int
    weekly_open_hour_mode: int
    weekly_close_hour_mode: int
    bars_per_year: dict
    median_daily_bars: float
    removed_rows: int


def clean(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Drop exact duplicate timestamps (keep last), sort, drop impossible OHLC rows.

    Returns the cleaned frame and number of removed rows. Nothing is interpolated.
    """
    n0 = len(df)
    df = df[~df.index.duplicated(keep="last")].sort_index()
    bad = (df.high < df[["open", "close", "low"]].max(axis=1)) | (df.low > df[["open", "close", "high"]].min(axis=1)) | (df[["open", "high", "low", "close"]] <= 0).any(axis=1)
    df = df[~bad]
    return df, n0 - len(df)


def quality(df_raw: pd.DataFrame) -> QualityReport:
    idx = df_raw.index
    dup = int(idx.duplicated().sum())
    nonmono = int((np.diff(idx.values.astype("int64")) <= 0).sum())
    o, h, l, c = (df_raw[k] for k in ("open", "high", "low", "close"))
    incons = int(((h < np.maximum(o, c)) | (l > np.minimum(o, c)) | (h < l)).sum())
    nonpos = int((df_raw[["open", "high", "low", "close"]] <= 0).any(axis=1).sum())
    df, removed = clean(df_raw)
    ret = df.close.pct_change().abs()
    gaps = df.index.to_series().diff()
    # intra-week gaps: not crossing a weekend (Fri->Sun/Mon)
    prev = df.index.to_series().shift()
    same_week = (df.index.isocalendar().week.values == prev.dt.isocalendar().week.values)
    big_gap = (gaps > pd.Timedelta(minutes=10)) & same_week
    wk_first = df.groupby([df.index.isocalendar().year, df.index.isocalendar().week]).apply(lambda x: x.index[0].hour)
    wk_last = df.groupby([df.index.isocalendar().year, df.index.isocalendar().week]).apply(lambda x: x.index[-1].hour)
    daily = df.groupby(df.index.date).size()
    return QualityReport(
        rows=len(df_raw), first=str(df_raw.index.min()), last=str(df_raw.index.max()),
        duplicates=dup, non_monotonic=nonmono, ohlc_inconsistent=incons, non_positive=nonpos,
        zero_range_bars=int((df.high == df.low).sum()),
        spread_zero_bars=int((df.spread == 0).sum()),
        spread_quantiles_points={str(q): float(df.spread.quantile(q)) for q in (0.01, 0.25, 0.5, 0.75, 0.95, 0.99)},
        big_jumps_gt_2pct=int((ret > 0.02).sum()),
        gaps_intraweek_gt_10min=int(big_gap.sum()),
        weekly_open_hour_mode=int(wk_first.mode().iloc[0]), weekly_close_hour_mode=int(wk_last.mode().iloc[0]),
        bars_per_year={str(k): int(v) for k, v in df.groupby(df.index.year).size().items()},
        median_daily_bars=float(daily.median()), removed_rows=removed,
    )


def resample(m1: pd.DataFrame, rule: str) -> pd.DataFrame:
    """Resample M1 to a higher timeframe. Bars are labelled by their OPEN time (MT5 convention)
    and only formed from M1 bars that exist (no synthetic bars for gaps)."""
    agg = {"open": "first", "high": "max", "low": "min", "close": "last", "tickvol": "sum", "spread": "max"}
    out = m1.resample(rule, label="left", closed="left").agg(agg).dropna(subset=["open"])
    return out


def write_manifest(path: Path, report: QualityReport, out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"file": path.name, "source": "user upload: barre_xauusd_m1_2017.part1/2.rar (RAR5 multivolume)",
                               "sha256": sha256(path), "bytes": path.stat().st_size,
                               "format": "MT5 Export Bars, TAB separated, CRLF, server time",
                               "symbol": "XAUUSD (per filename and price level)", "timeframe": "M1",
                               "quality": asdict(report)}, indent=2))
