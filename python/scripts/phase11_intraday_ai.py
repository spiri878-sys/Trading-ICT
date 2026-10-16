"""FASE 11 — INTRADAY con AI autoallenata (>= 3 trade al giorno).

Etichette intraday (stop k x ATR H1/M15, trailing, durata corta); LightGBM Huber riaddestrato ogni 6 mesi
(finestra 4 anni, solo esiti chiusi) + memoria ombra; presa = punteggio sopra la soglia viva (quantile q degli
ultimi 1000 punteggi, come il venditore) e/o filtro di regime. Un trade alla volta.
Si riportano solo le regole con >= 3 trade/giorno in SVILUPPO 2010-2015; CONTROLLO 2016-2026-01.

usage: python python/scripts/phase11_intraday_ai.py
"""
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from phase11_intraday import TRADING_DAYS, h1_regime  # noqa: E402
from phase11_robust import Base  # noqa: E402
from phase11_trend_exit import CACHE, OUT, stats  # noqa: E402
from raptor.prime.models import living_threshold  # noqa: E402
from raptor.prime.selftrain import one_at_a_time  # noqa: E402
from raptor.prime.trail import atr_on_m1, sim_trail  # noqa: E402

CFGS = [("h1", 3.0, 3.0, 4), ("h1", 3.0, 4.0, 8), ("h1", 2.0, 3.0, 8), ("m15", 3.0, 3.0, 4), ("h1", 3.0, 3.0, 24),
        ("m15", 2.0, 2.0, 2)]


def log(msg, t0=[time.time()]):
    print(f"[{time.time() - t0[0]:6.0f}s] {msg}", flush=True)


def main():
    B = Base()
    A = {"m15": atr_on_m1(B.idx, pd.read_parquet(CACHE / "tf" / "XAUUSD_M15.parquet")),
         "h1": atr_on_m1(B.idx, pd.read_parquet(CACHE / "tf" / "XAUUSD_H1.parquet"))}
    h1st, h1ema = h1_regime(B)
    s = B.side
    B.df["f_rg_h1don20_al"] = (h1st == s).astype(float)
    B.df["f_rg_h1ema_al"] = (h1ema == s).astype(float)
    filters = {"none": np.ones(len(s), bool), "h1": (h1st == s) & (h1ema == s), "h4d1": B.flt}
    o, h, l, c = B.ohlc
    rows = []
    for atf, slm, trm, hold_h in CFGS:
        sim = lambda sp_, sl_, cm_: sim_trail(o, h, l, c, np.full(o.size, sp_), B.day, A[atf], B.fi, B.fpx, s,  # noqa
                                              slm, trm, 1.0, 0.0, 99.0, 0.0, hold_h * 60, sl_, cm_, -0.066, 0.029, False)
        r, ei, _ = sim(0.30, 0.05, 0.035)
        r2, _, _ = sim(0.60, 0.10, 0.07)
        et = np.where(ei >= 0, B.idx.values[np.maximum(ei, 0)], np.datetime64("NaT", "ns"))
        flt_all = B.flt
        B.flt = np.ones(len(s), bool)          # addestra su tutti i segnali (il filtro entra come feature)
        sc = B.scores(r, et)
        B.flt = flt_all
        name = f"{atf}_sl{slm}_tr{trm}_h{hold_h}"
        ft = B.idx.values[B.fi]
        ok = np.isfinite(sc)
        for q in (0.0, 0.3, 0.5, 0.6, 0.7, 0.8, 0.9):
            thr = living_threshold(np.where(ok, sc, np.nan)[ok], B.t[ok], window=1000, q=q) if q > 0 else None
            take_q = np.zeros(len(s), bool)
            if q > 0:
                take_q[np.where(ok)[0]] = sc[ok] > np.nan_to_num(thr, nan=np.inf)
            else:
                take_q = ok & (sc > 0)
            for fn, fm in filters.items():
                take = take_q & fm
                op = one_at_a_time(ft, et, take, r)
                row = dict(cfg=name, rule=("s>0" if q == 0 else f"viva_q{q}"), flt=fn)
                for per, (a, b) in (("dev", ("2010-01-01", "2016-01-01")), ("chk", ("2016-01-01", "2026-02-01"))):
                    m = op & (B.t >= np.datetime64(a)) & (B.t < np.datetime64(b))
                    st = stats(r[m], B.t[m])
                    row.update({f"{per}_{k}": v for k, v in st.items() if k in ("avg_r", "pf", "years_pos",
                                                                                 "cagr_1pct", "maxdd_1pct")})
                    row[f"{per}_per_day"] = round(st.get("per_year", 0) / TRADING_DAYS, 2)
                    row[f"{per}_c2_avg_r"] = round(float(np.nanmean(r2[m])), 4) if m.any() else None
                rows.append(row)
        log(f"{name} fatto")
        pd.DataFrame(rows).to_csv(OUT / "intraday_ai_grid.csv", index=False)
    R = pd.DataFrame(rows)
    pd.set_option("display.width", 260)
    cols = ["cfg", "rule", "flt", "dev_per_day", "dev_avg_r", "dev_pf", "dev_years_pos", "chk_per_day", "chk_avg_r",
            "chk_pf", "chk_years_pos", "chk_c2_avg_r", "chk_cagr_1pct", "chk_maxdd_1pct"]
    q = R[R.dev_per_day >= 3]
    print(">= 3/giorno:", len(q), "regole; positive in entrambi:", int(((q.dev_avg_r > 0) & (q.chk_avg_r > 0)).sum()))
    print(q.sort_values("dev_avg_r", ascending=False)[cols].head(25).to_string())
    print("\nmigliori con >= 1/giorno:")
    print(R[R.dev_per_day >= 1].sort_values("dev_avg_r", ascending=False)[cols].head(15).to_string())


if __name__ == "__main__":
    main()
