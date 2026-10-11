"""FASE 0 — inventario e dati.

* carica XAU_1m_data.csv (2004 -> 2026-01-30, separatore ';', senza spread) e il vecchio M1 MT5 (2018 -> 2026-10,
  con spread); qualità, copertura per anno, fuso orario, coerenza tra fonti;
* costruisce la serie M1 master (nuovo file fino al 2026-01-30, vecchio file dopo) e tutti i timeframe derivati
  (M3 M5 M12 M15 M30 H1 H4 D1 W1) in output/cache/;
* confronta i derivati con i file 30m / 4h / 1w forniti;
* profilo di spread per ora dal vecchio M1 nel regime affidabile (da 2023-02);
* scrive output/phase0_stats.json (letto dal report).

usage: python python/scripts/phase0_data.py
"""
import json
import sys
from dataclasses import asdict
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from raptor.data import (RAW, ROOT, clean, load_mt5_csv, load_semicolon_csv, quality, resample,  # noqa: E402
                         sha256)

OUT = ROOT / "output"
CACHE = OUT / "cache"
TF = CACHE / "tf"
NEW_CSV = RAW / "m1_new" / "XAU_1m_data.csv"
OLD_CSV = RAW / "XAUUSD_M1.csv"
HTF = RAW / "htf"
MINUTES_PER_DAY = 23 * 60  # 01:00 -> 24:00 server time; 00:00-01:00 is the daily break
TFS = {"M3": "3min", "M5": "5min", "M12": "12min", "M15": "15min", "M30": "30min", "H1": "1h", "H4": "4h",
       "D1": "1D"}


def cached(path, fn):
    if path.exists():
        return pd.read_parquet(path)
    df = fn()
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path)
    return df


def weekly(m1):
    """Weekly bars starting Sunday 00:00 server time (as the vendor's 1w file)."""
    wk_start = (m1.index - pd.to_timedelta((m1.index.dayofweek + 1) % 7, unit="D")).normalize()
    agg = {"open": "first", "high": "max", "low": "min", "close": "last", "tickvol": "sum", "spread": "max"}
    out = m1.groupby(wk_start).agg(agg)
    out.index.name = "time"
    return out


def remove_bad_ticks(m1):
    """Remove (never interpolate) obvious bad ticks, judged against the centred median of 11 closes:
    * isolated bars entirely more than 1% away from it (single-tick prints such as 578.1 inside 598);
    * isolated wicks more than 3% away while the body stays within 0.3% (e.g. 2011-07-18 08:06 low 1495 at 1597).
    Real fast markets (2015-07-20, 2020-03, 2026-01-29) move the body too and are kept."""
    med = m1.close.rolling(11, center=True, min_periods=5).median()
    dev = m1[["open", "high", "low", "close"]].sub(med, axis=0).abs().div(med, axis=0)
    body = m1[["open", "close"]].sub(med, axis=0).abs().div(med, axis=0).max(axis=1)
    whole = dev.min(axis=1) > 0.01
    wick = (dev[["high", "low"]].max(axis=1) > 0.03) & (body < 0.003)
    bad = whole | wick
    return m1[~bad], m1[bad]


def day_quality(m1):
    """Per server day: bars, coverage, longest intraday gap, flag 'degraded' (<50% of the 1380 expected minutes,
    e.g. 2012-03-09 stored with only 22 hourly-like bars). Signals on degraded days must be skipped."""
    g = m1.groupby(m1.index.normalize())
    gaps = m1.index.to_series().diff().dt.total_seconds().div(60)
    gaps[gaps.index.normalize() != gaps.index.to_series().shift().dt.normalize()] = np.nan  # first bar of a day
    dq = pd.DataFrame({"bars": g.size(), "max_gap_min": gaps.groupby(gaps.index.normalize()).max(),
                       "tickvol": g.tickvol.sum()})
    dq["coverage"] = (dq.bars / MINUTES_PER_DAY).clip(upper=1)
    dq["weekday"] = dq.index.dayofweek < 5
    dq["degraded"] = dq.weekday & (dq.coverage < 0.5)
    dq.index.name = "day"
    return dq


def coverage(m1):
    days = m1.groupby(m1.index.normalize()).size()
    days = days[days.index.dayofweek < 5]
    cov = (days / MINUTES_PER_DAY).clip(upper=1)
    by_year = pd.DataFrame({"bars": m1.groupby(m1.index.year).size(),
                            "trading_days": days.groupby(days.index.year).size(),
                            "coverage_pct": (100 * cov.groupby(cov.index.year).mean()).round(1),
                            "days_below_50pct": (cov < 0.5).groupby(cov.index.year).sum(),
                            "median_bars_per_day": days.groupby(days.index.year).median()})
    hours = m1.groupby([m1.index.year, m1.index.hour]).size().unstack(fill_value=0)
    days_y = by_year.trading_days
    hour_cov = (100 * hours.div(days_y * 60, axis=0)).clip(upper=100).round(0)
    return by_year, hour_cov


def tz_check(m1):
    idx = m1.index
    iso = idx.isocalendar()
    s = pd.Series(idx, index=idx)
    g = s.groupby([iso.year.values, iso.week.values])
    first, last = g.first(), g.last()
    df = pd.DataFrame({"year": first.dt.year.values, "first_dow": first.dt.dayofweek.values,
                       "first_hour": first.dt.hour.values, "last_dow": last.dt.dayofweek.values,
                       "last_hour": last.dt.hour.values})
    mode = df.groupby("year").agg(lambda x: int(x.mode().iloc[0]))
    hour0 = m1.groupby(m1.index.year).apply(lambda x: round(100 * (x.index.hour == 0).mean(), 3))
    mode["share_bars_in_hour00_pct"] = hour0
    return mode


def compare(a, b, label_a, label_b):
    j = a[["open", "high", "low", "close"]].join(b[["open", "high", "low", "close"]], how="inner", rsuffix="_b")
    out = {"bars_" + label_a: int(len(a)), "bars_" + label_b: int(len(b)), "common": int(len(j)),
           "only_" + label_a: int(len(a.index.difference(b.index))),
           "only_" + label_b: int(len(b.index.difference(a.index)))}
    for c in ("open", "high", "low", "close"):
        d = j[c] - j[c + "_b"]
        out[c] = {"median_abs": round(float(d.abs().median()), 4), "mean_signed": round(float(d.mean()), 4),
                  "p99_abs": round(float(d.abs().quantile(0.99)), 4),
                  "share_within_0.10": round(float((d.abs() <= 0.10).mean()), 4),
                  "share_within_0.50": round(float((d.abs() <= 0.50).mean()), 4)}
    return out


def load_vendor_htf(name):
    d = pd.read_csv(HTF / name, sep=";", dtype={"Date": str})
    d.index = pd.to_datetime(d.pop("Date"), format="%Y.%m.%d %H:%M")
    d.index.name = "time"
    d.columns = [c.lower() for c in d.columns]
    return d


def main():
    stats = {}
    # ---------------- load ----------------
    new = cached(CACHE / "src_new_m1.parquet", lambda: load_semicolon_csv(NEW_CSV))
    old = cached(CACHE / "src_old_m1.parquet", lambda: load_mt5_csv(OLD_CSV))
    stats["files"] = {
        "new_m1": {"path": str(NEW_CSV.relative_to(ROOT)), "sha256": sha256(NEW_CSV), "bytes": NEW_CSV.stat().st_size,
                   "source": "user upload barre.part01-03.rar (RAR multivolume)"},
        "old_m1": {"path": str(OLD_CSV.relative_to(ROOT)), "sha256": sha256(OLD_CSV), "bytes": OLD_CSV.stat().st_size},
        **{f"vendor_{n}": {"path": f"data/raw/htf/{n}", "sha256": sha256(HTF / n), "bytes": (HTF / n).stat().st_size}
           for n in ("XAU_30m.csv", "XAU_4h.csv", "XAU_1w.csv")}}

    # ---------------- quality ----------------
    q_new = quality(new)
    stats["quality_new"] = asdict(q_new)
    new_c, removed = clean(new)
    new_c, bad = remove_bad_ticks(new_c)
    stats["quality_new"]["removed_rows"] = removed
    stats["bad_ticks_removed"] = [{"time": str(t), **{k: float(r[k]) for k in ("open", "high", "low", "close")},
                                   "tickvol": int(r.tickvol)} for t, r in bad.iterrows()]
    dq = day_quality(new_c)
    dq.to_parquet(CACHE / "day_quality.parquet")
    wd = dq[dq.weekday]
    stats["degraded_days_by_year"] = {int(y): int(v) for y, v in wd.degraded.groupby(wd.index.year).sum().items()}
    stats["degraded_days_examples"] = [str(d.date()) for d in wd.index[wd.degraded & (wd.index.year >= 2008)]][:40]
    big = new_c.close.pct_change().abs()
    stats["big_jumps_new"] = [str(t) for t in new_c.index[(big > 0.02).values]][:50]
    cov, hour_cov = coverage(new_c)
    stats["coverage_new_by_year"] = cov.reset_index(names="year").to_dict("records")
    stats["hour_coverage_new_pct"] = {int(k): v for k, v in hour_cov.T.to_dict().items()}
    stats["tz_new"] = tz_check(new_c).reset_index().to_dict("records")
    stats["tz_old"] = tz_check(old).reset_index().to_dict("records")

    # ---------------- consistency between sources ----------------
    lo, hi = max(new_c.index[0], old.index[0]), min(new_c.index[-1], old.index[-1])
    stats["new_vs_old_m1_overlap"] = {"from": str(lo), "to": str(hi),
                                      **compare(new_c.loc[lo:hi], old.loc[lo:hi], "new", "old")}
    by_year = {}
    for y in range(lo.year, hi.year + 1):
        a, b = new_c.loc[str(y)], old.loc[str(y)]
        j = a.close.to_frame().join(b.close.rename("o"), how="inner")
        by_year[y] = {"median_abs_close": round(float((j.close - j.o).abs().median()), 3),
                      "mean_signed_close": round(float((j.close - j.o).mean()), 3), "common": int(len(j))}
    stats["new_vs_old_close_by_year"] = by_year

    # ---------------- master series ----------------
    cut = new_c.index[-1]
    tail = old.loc[old.index > cut]
    master = pd.concat([new_c, tail]).sort_index()
    master = master[~master.index.duplicated(keep="first")]
    # recorded spread (points) from the MT5 export where it exists (2018 ->); -1 = unknown. Units: see docs/data_and_costs.md
    sp = old.spread.reindex(master.index)
    master["spread"] = np.where(sp.notna(), sp, master.spread).astype(np.int64)
    j_last = new_c.close.iloc[-1]
    j_first = tail.open.iloc[0] if len(tail) else np.nan
    same_day = old.loc[str(cut.date())]
    jd = (new_c.loc[str(cut.date())].close - same_day.close).dropna()
    stats["junction"] = {"new_last_bar": str(cut), "old_first_bar_after": str(tail.index[0]) if len(tail) else None,
                         "new_last_close": float(j_last), "old_first_open_after": float(j_first),
                         "gap_usd": round(float(j_first - j_last), 2),
                         "same_day_close_diff_median": round(float(jd.abs().median()), 3) if len(jd) else None,
                         "bars_appended_from_old": int(len(tail))}
    master.to_parquet(CACHE / "XAUUSD_M1_master.parquet")
    stats["master"] = {"rows": int(len(master)), "first": str(master.index[0]), "last": str(master.index[-1]),
                       "spread_known_from": str(master.index[master.spread >= 0][0]) if (master.spread >= 0).any()
                       else None}

    # ---------------- derived timeframes ----------------
    TF.mkdir(parents=True, exist_ok=True)
    tf_rows = {}
    for name, rule in TFS.items():
        df = resample(master, rule)
        df.to_parquet(TF / f"XAUUSD_{name}.parquet")
        tf_rows[name] = {"rows": int(len(df)), "first": str(df.index[0]), "last": str(df.index[-1])}
    w1 = weekly(master)
    w1.to_parquet(TF / "XAUUSD_W1.parquet")
    tf_rows["W1"] = {"rows": int(len(w1)), "first": str(w1.index[0]), "last": str(w1.index[-1])}
    stats["timeframes"] = tf_rows
    m3 = pd.read_parquet(TF / "XAUUSD_M3.parquet")
    m12 = pd.read_parquet(TF / "XAUUSD_M12.parquet")
    stats["alignment"] = {"M3_minute_mod3_zero": bool((m3.index.minute % 3 == 0).all()),
                          "M12_minute_mod12_zero": bool((m12.index.minute % 12 == 0).all())}

    # ---------------- vs vendor HTF files (same vendor as new M1) ----------------
    vend = {}
    for name, f, rule in (("M30", "XAU_30m.csv", "30min"), ("H4", "XAU_4h.csv", "4h"), ("W1", "XAU_1w.csv", None)):
        v = load_vendor_htf(f)
        mine = weekly(new_c) if rule is None else resample(new_c, rule)
        vend[name] = compare(mine.loc[: v.index[-1]], v, "mine", "vendor")
    stats["derived_vs_vendor"] = vend

    # ---------------- spread profile (old M1, reliable regime from 2023-02) ----------------
    s = old.loc["2023-02-01":, "spread"] * 0.01
    prof = s.groupby(s.index.hour).agg(["median", "mean", lambda x: x.quantile(0.9)])
    prof.columns = ["median_usd", "mean_usd", "p90_usd"]
    stats["spread_profile_by_hour_usd"] = prof.round(3).reset_index(names="hour").to_dict("records")
    stats["spread_overall_2023plus_usd"] = {"median": round(float(s.median()), 3), "mean": round(float(s.mean()), 3),
                                           "share_zero": round(float((s == 0).mean()), 3)}
    prof.round(3).to_csv(CACHE / "spread_profile_by_hour.csv")

    (OUT / "phase0_stats.json").write_text(json.dumps(stats, indent=1, default=str))
    print(json.dumps({k: v for k, v in stats.items() if k not in ("hour_coverage_new_pct", "big_jumps_new")},
                     indent=1, default=str)[:20000])


if __name__ == "__main__":
    main()
