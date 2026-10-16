"""FASE 11 — stessa strategia (celle ICT + regime + AI autoallenata + trailing ATR H4) con FINO A K POSIZIONI
insieme, per ottenere >= 3 trade al giorno. Rischio per trade = budget / K. Varianti: soglia AI, durata massima,
stop/trailing. SVILUPPO 2010-2015, CONTROLLO 2016-2026-01.

usage: python python/scripts/phase11_multi.py
"""
import itertools
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from phase11_robust import Base  # noqa: E402
from phase11_trend_exit import OUT  # noqa: E402
from raptor.prime.selftrain import equity_events, k_slots  # noqa: E402

PER = {"dev": ("2010-01-01", "2016-01-01"), "chk": ("2016-01-01", "2026-02-01")}


def log(msg, t0=[time.time()]):
    print(f"[{time.time() - t0[0]:6.0f}s] {msg}", flush=True)


def main():
    B = Base()
    ft = B.idx.values[B.fi]
    rows = []
    for slm, trm, hold in ((1.5, 5.0, 10), (1.5, 5.0, 5), (1.5, 4.0, 3), (2.0, 4.0, 5), (1.5, 3.0, 2), (1.0, 3.0, 2)):
        r, et = B.label(slm, trm, hold)
        r2, _ = B.label(slm, trm, hold, spread=0.60, slip=0.10, comm=0.07)
        sc = B.scores(r, et)
        log(f"etichette e punteggi sl{slm} tr{trm} h{hold}")
        for th, K, budget in itertools.product((None, -0.2, 0.0), (3, 5, 10, 20), (0.02, 0.04)):
            take = B.flt & np.isfinite(r) & (np.ones(len(r), bool) if th is None else (np.nan_to_num(sc, nan=-9) > th))
            take &= B.t >= np.datetime64("2010-01-01")
            op = k_slots(ft, et, take, r, K)
            row = dict(cfg=f"sl{slm}_tr{trm}_h{hold}", ai=("nessuna" if th is None else f"s>{th}"), K=K,
                       risk_trade_pct=round(100 * budget / K, 2))
            for per, (a, b) in PER.items():
                m = op & (B.t >= np.datetime64(a)) & (B.t < np.datetime64(b))
                days = np.busday_count(np.datetime64(a, "D"), np.datetime64(b, "D"))
                d_cnt = pd.Series(1, index=pd.DatetimeIndex(B.t[m]).normalize()).groupby(level=0).sum()
                yrs = pd.Series(r[m], index=pd.DatetimeIndex(B.t[m]).year).groupby(level=0).sum()
                _, cagr, dd = equity_events(r[m], ft[m], et[m], budget / K)
                gp, gl = r[m][r[m] > 0].sum(), -r[m][r[m] < 0].sum()
                row.update({f"{per}_per_day": round(m.sum() / days, 2),
                            f"{per}_days_ge3": round(float((d_cnt >= 3).sum() / days), 2),
                            f"{per}_avg_r": round(float(np.nanmean(r[m])), 3) if m.any() else None,
                            f"{per}_c2_avg_r": round(float(np.nanmean(r2[m])), 3) if m.any() else None,
                            f"{per}_pf": round(float(gp / gl), 2) if gl > 0 else None,
                            f"{per}_years_pos": f"{int((yrs > 0).sum())}/{len(yrs)}",
                            f"{per}_cagr": cagr, f"{per}_maxdd": dd})
            rows.append(row)
        pd.DataFrame(rows).to_csv(OUT / "multi_slots_grid.csv", index=False)
    R = pd.DataFrame(rows)
    pd.set_option("display.width", 280)
    cols = ["cfg", "ai", "K", "risk_trade_pct", "dev_per_day", "dev_avg_r", "dev_years_pos", "dev_cagr", "dev_maxdd",
            "chk_per_day", "chk_days_ge3", "chk_avg_r", "chk_c2_avg_r", "chk_pf", "chk_years_pos", "chk_cagr", "chk_maxdd"]
    q = R[(R.dev_per_day >= 3)]
    print(">= 3 trade/giorno in sviluppo:", len(q), "; positive in entrambi i periodi:",
          int(((q.dev_avg_r > 0) & (q.chk_avg_r > 0)).sum()))
    print(q.sort_values("dev_avg_r", ascending=False)[cols].head(30).to_string())


if __name__ == "__main__":
    main()
