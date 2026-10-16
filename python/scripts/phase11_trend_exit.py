"""FASE 11 — celle ICT + Market Brain di regime + 'TP/SL dinamici' (trailing ATR), un trade alla volta.

Regime (noto prima del segnale): stato Donchian H4 a 20 barre (ultima rottura del massimo/minimo) e D1 sopra/sotto
la EMA50 dell'ultima chiusura giornaliera. Allineato = entrambi nella direzione del segnale.
Scelte SOLO su SVILUPPO 2005-2015; CONTROLLO 2016-2026-01 in sola lettura.

usage: python python/scripts/phase11_trend_exit.py
"""
import itertools
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from raptor.prime.data import ROOT, master_m1  # noqa: E402
from raptor.prime.selftrain import equity, one_at_a_time  # noqa: E402
from raptor.prime.trail import atr_on_m1, sim_trail  # noqa: E402

CACHE = ROOT / "output" / "cache"
OUT = ROOT / "output" / "phase11"
DEV_END = "2016-01-01"


def regime_cols(df):
    h4 = pd.read_parquet(CACHE / "tf" / "XAUUSD_H4.parquet")
    d1 = pd.read_parquet(CACHE / "tf" / "XAUUSD_D1.parquet")
    t = df.known_at.values

    def at(series, bars, step):
        avail = (bars.index + pd.Timedelta(step)).values
        j = np.searchsorted(avail, t, side="right") - 1
        return np.where(j >= 0, series[np.maximum(j, 0)], 0)

    def don(b, n):
        hh = b.high.rolling(n).max().shift(1)
        ll = b.low.rolling(n).min().shift(1)
        s = pd.Series(np.where(b.close > hh, 1, np.where(b.close < ll, -1, np.nan)), index=b.index)
        return s.ffill().fillna(0).values

    out = pd.DataFrame(index=df.index)
    for n in (20, 55):
        out[f"h4don{n}"] = at(don(h4, n), h4, "4h")
        out[f"d1don{n}"] = at(don(d1, n), d1, "1D")
    ema = d1.close.ewm(span=50, adjust=False).mean().values
    out["d1ema"] = at(np.sign(d1.close.values - ema), d1, "1D")
    return out


def stats(r, t, start=10_000.0, risk=0.01):
    r = np.asarray(r, float)
    ok = np.isfinite(r)
    r, t = r[ok], np.asarray(t)[ok]
    if r.size < 5:
        return dict(n=int(r.size))
    gp, gl = r[r > 0].sum(), -r[r < 0].sum()
    yrs = pd.Series(r, index=pd.DatetimeIndex(t).year).groupby(level=0).sum()
    _, e = equity(r, t, risk=risk, start=start)
    span = max((pd.Timestamp(t.max()) - pd.Timestamp(t.min())).days / 365.25, 0.5)
    return dict(n=int(r.size), per_year=round(r.size / span, 1), avg_r=round(float(r.mean()), 3),
                pf=round(float(gp / gl), 2), win=round(float((r > 0).mean()), 3),
                years_pos=f"{int((yrs > 0).sum())}/{len(yrs)}", cagr_1pct=e["cagr"], maxdd_1pct=e["max_dd"],
                r_by_year={int(k): round(float(v), 1) for k, v in yrs.items()})


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    df = pd.read_parquet(CACHE / "phase11" / "dataset.parquet")
    df = df[df.filled_a6].reset_index(drop=True)
    df = pd.concat([df, regime_cols(df)], axis=1)
    m1 = master_m1()
    idx = m1.index
    o, h, l, c = (m1[k].values.astype(float) for k in ("open", "high", "low", "close"))
    day = idx.values.astype("datetime64[D]").astype(np.int64)
    A = {"h1": atr_on_m1(idx, pd.read_parquet(CACHE / "tf" / "XAUUSD_H1.parquet")),
         "h4": atr_on_m1(idx, pd.read_parquet(CACHE / "tf" / "XAUUSD_H4.parquet"))}
    fi = np.searchsorted(idx.values, df.fill_time_a6.values.astype("datetime64[ns]")).astype(np.int64)
    fpx = df.fill_px_a6.values.astype(float)
    side = df.side.values.astype(np.int64)
    t = df.known_at.values
    dev = t < np.datetime64(DEV_END)
    filters = {
        "all": np.ones(len(df), bool),
        "h4d20+d1ema": (df.h4don20.values == side) & (df.d1ema.values == side),
        "h4d55+d1ema": (df.h4don55.values == side) & (df.d1ema.values == side),
        "d1d20+d1ema": (df.d1don20.values == side) & (df.d1ema.values == side),
        "h4d20": df.h4don20.values == side,
    }
    rows, keep = [], {}
    for (tf, slm, trm, hold, mg), spread in itertools.product(
            itertools.product(["h1", "h4"], [1.5, 2.0, 3.0], [2.0, 3.0, 4.0, 5.0], [3, 5, 10],
                              ["none", "be", "foto"]), [0.30]):
        p = {"none": (0.7, 0.0, 2.0, 0.0, False), "be": (1.0, 0.0, 2.0, 0.0, True),
             "foto": (0.7, 0.2, 2.0, 0.2, True)}[mg]
        sp = np.full(len(m1), spread)
        r, ei, rk = sim_trail(o, h, l, c, sp, day, A[tf], fi, fpx, side, slm, trm, p[0], p[1], p[2], p[3],
                              hold * 1380, 0.05, 0.035, -0.066, 0.029, p[4])
        et = np.where(ei >= 0, idx.values[np.maximum(ei, 0)], np.datetime64("NaT"))
        ft = idx.values[fi]
        for fn, fm in filters.items():
            op = one_at_a_time(ft, et, fm, r)
            sd, sc = stats(r[op & dev], t[op & dev]), stats(r[op & ~dev], t[op & ~dev])
            name = f"{tf}_sl{slm}_tr{trm}_h{hold}_{mg}_{fn}"
            rows.append(dict(cfg=name, tf=tf, sl=slm, tr=trm, hold=hold, mg=mg, flt=fn,
                             **{f"dev_{k}": v for k, v in sd.items() if k != "r_by_year"},
                             **{f"chk_{k}": v for k, v in sc.items() if k != "r_by_year"}))
            keep[name] = (r, et, op)
    R = pd.DataFrame(rows)
    R.to_csv(OUT / "trend_exit_grid.csv", index=False)
    pd.set_option("display.width", 250)
    cols = ["cfg", "dev_n", "dev_per_year", "dev_avg_r", "dev_pf", "dev_years_pos", "dev_cagr_1pct", "dev_maxdd_1pct",
            "chk_n", "chk_avg_r", "chk_pf", "chk_years_pos", "chk_cagr_1pct", "chk_maxdd_1pct"]
    print("TOP 25 per SVILUPPO (R medio, >= 20 trade/anno):")
    print(R[R.dev_per_year >= 20].sort_values("dev_avg_r", ascending=False)[cols].head(25).to_string())
    print("\nquota di configurazioni positive in sviluppo e in controllo, per filtro:")
    print(R.groupby("flt").apply(lambda g: pd.Series(dict(n=len(g), dev_pos=(g.dev_avg_r > 0).mean(),
                                                          chk_pos=(g.chk_avg_r > 0).mean(),
                                                          both=((g.dev_avg_r > 0) & (g.chk_avg_r > 0)).mean()))).round(2))


if __name__ == "__main__":
    main()
