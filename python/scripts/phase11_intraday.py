"""FASE 11 — versione INTRADAY (obiettivo cliente: almeno 3 trade al giorno, un trade alla volta).

Stadio 1 (senza AI): celle ICT a mercato/limite come nel dataset, filtro di regime (vari), stop k x ATR (M15/H1),
trailing m x ATR, durata massima corta. Misura trade/giorno e R con un trade alla volta.
SVILUPPO 2010-2015, CONTROLLO 2016-2026-01.

usage: python python/scripts/phase11_intraday.py
"""
import itertools
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from phase11_robust import Base  # noqa: E402
from phase11_trend_exit import CACHE, OUT, stats  # noqa: E402
from raptor.prime.selftrain import one_at_a_time  # noqa: E402
from raptor.prime.trail import atr_on_m1, sim_trail  # noqa: E402

TRADING_DAYS = 260


def h1_regime(B):
    """Stato Donchian H1 a 20 barre ed EMA50 H1 al momento del segnale (noti a barra chiusa)."""
    h1 = pd.read_parquet(CACHE / "tf" / "XAUUSD_H1.parquet")
    hh = h1.high.rolling(20).max().shift(1)
    ll = h1.low.rolling(20).min().shift(1)
    st = pd.Series(np.where(h1.close > hh, 1, np.where(h1.close < ll, -1, np.nan)), index=h1.index).ffill().fillna(0)
    ema = h1.close.ewm(span=50, adjust=False).mean()
    avail = (h1.index + pd.Timedelta("1h")).values
    j = np.searchsorted(avail, B.t, side="right") - 1
    jj = np.maximum(j, 0)
    return st.values[jj], np.sign(h1.close.values[jj] - ema.values[jj])


def main():
    B = Base()
    A = {"m15": atr_on_m1(B.idx, pd.read_parquet(CACHE / "tf" / "XAUUSD_M15.parquet")),
         "h1": atr_on_m1(B.idx, pd.read_parquet(CACHE / "tf" / "XAUUSD_H1.parquet"))}
    h1st, h1ema = h1_regime(B)
    s = B.side
    df = B.df
    filters = {"none": np.ones(len(s), bool),
               "h4d1": B.flt,
               "h1": (h1st == s) & (h1ema == s),
               "h1+d1": (h1st == s) & (df.f_rg_d1ema.values == s),
               "h1+h4d1": (h1st == s) & B.flt}
    o, h, l, c = B.ohlc
    sp = np.full(o.size, 0.30)
    rows = []
    for atf, slm, trm, hold_h, be in itertools.product(["m15", "h1"], [1.0, 1.5, 2.0, 3.0], [1.5, 2.0, 3.0, 4.0],
                                                      [2, 4, 8, 24], [False, True]):
        r, ei, _ = sim_trail(o, h, l, c, sp, B.day, A[atf], B.fi, B.fpx, s, slm, trm, 1.0, 0.0, 99.0, 0.0,
                             hold_h * 60, 0.05, 0.035, -0.066, 0.029, be)
        et = np.where(ei >= 0, B.idx.values[np.maximum(ei, 0)], np.datetime64("NaT", "ns"))
        ft = B.idx.values[B.fi]
        for fn, fm in filters.items():
            op = one_at_a_time(ft, et, fm, r)
            row = dict(cfg=f"{atf}_sl{slm}_tr{trm}_h{hold_h}{'_be' if be else ''}", flt=fn)
            for per, (a, b) in (("dev", ("2010-01-01", "2016-01-01")), ("chk", ("2016-01-01", "2026-02-01"))):
                m = op & (B.t >= np.datetime64(a)) & (B.t < np.datetime64(b))
                st = stats(r[m], B.t[m])
                row.update({f"{per}_{k}": v for k, v in st.items() if k in ("avg_r", "pf", "years_pos", "cagr_1pct",
                                                                             "maxdd_1pct")})
                row[f"{per}_per_day"] = round(st.get("per_year", 0) / TRADING_DAYS, 2)
                row[f"{per}_iso_avg_r"] = round(float(np.nanmean(r[fm & (B.t >= np.datetime64(a)) &
                                                                  (B.t < np.datetime64(b))])), 4)
            rows.append(row)
    R = pd.DataFrame(rows)
    R.to_csv(OUT / "intraday_grid.csv", index=False)
    pd.set_option("display.width", 260)
    cols = ["cfg", "flt", "dev_per_day", "dev_avg_r", "dev_iso_avg_r", "dev_pf", "dev_years_pos", "chk_per_day",
            "chk_avg_r", "chk_iso_avg_r", "chk_pf", "chk_years_pos", "chk_cagr_1pct", "chk_maxdd_1pct"]
    q = R[R.dev_per_day >= 3]
    print("con >= 3 trade/giorno in sviluppo:", len(q), "configurazioni; positive in entrambi:",
          int(((q.dev_avg_r > 0) & (q.chk_avg_r > 0)).sum()))
    print(q.sort_values("dev_iso_avg_r", ascending=False)[cols].head(25).to_string())
    print("\nmigliori per R isolato (qualsiasi frequenza):")
    print(R.sort_values("dev_iso_avg_r", ascending=False)[cols].head(15).to_string())


if __name__ == "__main__":
    main()
