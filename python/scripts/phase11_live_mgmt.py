"""FASE 11 — gestione 'live' osservata a settembre 2026: ingresso A MERCATO all'apertura del minuto successivo al
segnale, 98% chiuso quando una barra M1 chiude a >= +1R, stop a pareggio + costi, residuo con TP 4R (approssimato
dal trailing assente), durata massima 3 giorni. Stop = k x ATR M15 oppure strutturale. Un trade alla volta.
SVILUPPO 2005-2015, CONTROLLO 2016-2026-01.

usage: python python/scripts/phase11_live_mgmt.py
"""
import itertools
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from phase11_trend_exit import CACHE, OUT, regime_cols, stats  # noqa: E402
from raptor.prime.data import master_m1  # noqa: E402
from raptor.prime.selftrain import one_at_a_time  # noqa: E402
from raptor.prime.trail import atr_on_m1, sim_trail  # noqa: E402


def main():
    df = pd.read_parquet(CACHE / "phase11" / "dataset.parquet")
    df = pd.concat([df, regime_cols(df)], axis=1)
    m1 = master_m1()
    idx = m1.index
    o, h, l, c = (m1[k].values.astype(float) for k in ("open", "high", "low", "close"))
    day = idx.values.astype("datetime64[D]").astype(np.int64)
    A = {"m15": atr_on_m1(idx, pd.read_parquet(CACHE / "tf" / "XAUUSD_M15.parquet")),
         "h1": atr_on_m1(idx, pd.read_parquet(CACHE / "tf" / "XAUUSD_H1.parquet"))}
    side = df.side.values.astype(np.int64)
    ki = np.searchsorted(idx.values, df.known_at.values.astype("datetime64[ns]")).astype(np.int64)
    ok = ki < len(idx) - 1
    fi = np.where(ok, ki, -1).astype(np.int64)
    sp = np.full(len(m1), 0.30)
    fpx = np.where(ok, o[np.minimum(ki, len(o) - 1)] + np.where(side == 1, 0.30 + 0.05, -0.05), np.nan)
    t = df.known_at.values
    dev = t < np.datetime64("2016-01-01")
    flt = {"all": np.ones(len(df), bool),
           "trend": (df.h4don20.values == side) & (df.d1ema.values == side),
           "d1ema": df.d1ema.values == side}
    rows = []
    for (atf, slm), (p1r, frac) in itertools.product(
            [("m15", 1.0), ("m15", 1.5), ("m15", 2.0), ("m15", 3.0), ("h1", 1.0), ("h1", 1.5), ("h1", 2.0)],
            [(1.0, 0.98), (1.0, 0.9), (0.7, 0.98), (1.5, 0.98)]):
        # trail_mult enorme = nessun trailing; il residuo esce al pareggio o a fine durata (TP 4R ignorato: 2%)
        r, ei, rk = sim_trail(o, h, l, c, sp, day, A[atf], fi, fpx, side, slm, 1e9, p1r, frac, 99.0, 0.0,
                              3 * 1380, 0.05, 0.035, -0.066, 0.029, True)
        et = np.where(ei >= 0, idx.values[np.maximum(ei, 0)], np.datetime64("NaT", "ns"))
        ft = np.where(fi >= 0, idx.values[np.maximum(fi, 0)], np.datetime64("NaT", "ns"))
        for cellset in ("ALL", "PPK", "UNIOF", "LS", "PPK+UNIOF"):
            cm = np.ones(len(df), bool) if cellset == "ALL" else df.cell.isin(cellset.split("+")).values
            for fn, fm in flt.items():
                op = one_at_a_time(ft, et, fm & cm, r)
                sd, sc = stats(r[op & dev], t[op & dev]), stats(r[op & ~dev], t[op & ~dev])
                rows.append(dict(cfg=f"{atf}x{slm}_p{p1r}_{int(frac * 100)}", cells=cellset, flt=fn,
                                 win_iso=round(float(np.nanmean(r[fm & cm] > 0)), 3),
                                 **{f"dev_{k}": v for k, v in sd.items() if k != "r_by_year"},
                                 **{f"chk_{k}": v for k, v in sc.items() if k != "r_by_year"}))
    R = pd.DataFrame(rows)
    R.to_csv(OUT / "live_mgmt_grid.csv", index=False)
    pd.set_option("display.width", 250)
    cols = ["cfg", "cells", "flt", "win_iso", "dev_n", "dev_avg_r", "dev_win", "dev_pf", "dev_years_pos", "chk_n",
            "chk_avg_r", "chk_win", "chk_pf", "chk_years_pos", "chk_cagr_1pct", "chk_maxdd_1pct"]
    print(R.sort_values("dev_avg_r", ascending=False)[cols].head(25).to_string())
    print("\nconfigurazioni positive in entrambi i periodi:", int(((R.dev_avg_r > 0) & (R.chk_avg_r > 0)).sum()), "su", len(R))


if __name__ == "__main__":
    main()
