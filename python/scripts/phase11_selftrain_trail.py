"""FASE 11 — AI con autoallenamento sopra la base 'celle ICT + regime + trailing ATR H4'.

Etichetta: R netto del trade gestito con stop sl x ATR H4, trailing tr x ATR H4, durata massima `hold` giorni.
Modello: LightGBM (Huber) su 105 feature PRIME + regime + memoria ombra, riaddestrato ogni trimestre dal 2010 solo
su esiti già chiusi. Regole: filtro di regime e/o R atteso > soglia. Un trade alla volta.
SVILUPPO 2010-2015 (scelte), CONTROLLO 2016-2026-01 (sola lettura).

usage: python python/scripts/phase11_selftrain_trail.py
"""
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from phase11_selftrain import with_memory  # noqa: E402
from phase11_trend_exit import CACHE, OUT, regime_cols, stats  # noqa: E402
from raptor.prime.data import config, master_m1  # noqa: E402
from raptor.prime.selftrain import one_at_a_time, retrain_dates, walk_forward_selftrain  # noqa: E402
from raptor.prime.trail import atr_on_m1, sim_trail  # noqa: E402

CFGS = {"T1": (1.5, 5.0, 10), "T2": (3.0, 5.0, 10)}
DEV = ("2010-01-01", "2016-01-01")
CHK = ("2016-01-01", "2026-02-01")


def log(msg, t0=[time.time()]):
    print(f"[{time.time() - t0[0]:6.0f}s] {msg}", flush=True)


def main():
    seed = config()["seed"]
    df = pd.read_parquet(CACHE / "phase11" / "dataset.parquet")
    df = df[df.filled_a6].reset_index(drop=True)
    reg = regime_cols(df)
    df = pd.concat([df, reg.add_prefix("f_rg_")], axis=1)
    side = df.side.values.astype(np.int64)
    for k in reg.columns:
        df[f"f_rg_{k}_al"] = (reg[k].values == side).astype(float)
    m1 = master_m1()
    idx = m1.index
    o, h, l, c = (m1[k].values.astype(float) for k in ("open", "high", "low", "close"))
    day = idx.values.astype("datetime64[D]").astype(np.int64)
    a4 = atr_on_m1(idx, pd.read_parquet(CACHE / "tf" / "XAUUSD_H4.parquet"))
    fi = np.searchsorted(idx.values, df.fill_time_a6.values.astype("datetime64[ns]")).astype(np.int64)
    fpx = df.fill_px_a6.values.astype(float)
    flt = (reg.h4don20.values == side) & (reg.d1ema.values == side)
    rows = []
    for name, (slm, trm, hold) in CFGS.items():
        res = {}
        for sc_name, spread, slip, comm in (("c1", 0.30, 0.05, 0.035), ("c2", 0.60, 0.10, 0.07)):
            r, ei, _ = sim_trail(o, h, l, c, np.full(len(m1), spread), day, a4, fi, fpx, side, slm, trm, 0.7, 0.0,
                                 2.0, 0.0, hold * 1380, slip, comm, -0.066, 0.029, False)
            res[sc_name] = (r, ei)
        r, ei = res["c1"]
        d = df.copy()
        d[f"r_{name}"] = r
        d[f"exit_time_{name}"] = pd.Series(np.where(ei >= 0, idx.values[np.maximum(ei, 0)],
                                                    np.datetime64("NaT", "ns")))
        d[f"r_foto_{name}"] = r                       # with_memory legge r_foto_<tag> / exit_time_foto_<tag>
        d[f"exit_time_foto_{name}"] = d[f"exit_time_{name}"]
        M = with_memory(d, name)
        d = pd.concat([d, M], axis=1)
        feats = [x for x in d.columns if x.startswith("f_")]
        d["y"] = d[f"r_{name}"].clip(-1.5, 6.0)
        ok = d.y.notna() & d[f"exit_time_{name}"].notna()
        for win in (None, 4):
            for only_flt in (False, True):
                dd = d[ok & (flt if only_flt else True)].copy()
                s = walk_forward_selftrain(dd, feats, "y", f"exit_time_{name}", retrain_dates("2010-01-01", "2026-01-01"),
                                           window_years=win, objective="huber", params={"alpha": 1.0}, seed=seed)
                sc = pd.Series(np.nan, index=d.index)
                sc[dd.index] = s.values
                tag = f"{name}_w{win or 0}_{'trainflt' if only_flt else 'trainall'}"
                pd.DataFrame({"score": sc}).to_parquet(CACHE / "phase11" / f"trail_scores_{tag}.parquet")
                ft = idx.values[fi]
                et = d[f"exit_time_{name}"].values
                t = d.known_at.values
                for rule, take in {"flt": flt, **{f"flt+s>{th}": flt & (sc.values > th) for th in (0.0, 0.1, 0.2, 0.3)},
                                   **{f"s>{th}": (sc.values > th) for th in (0.1, 0.2, 0.3, 0.5)}}.items():
                    take = take & sc.notna().values
                    op = one_at_a_time(ft, et, take, r)
                    for per, (a, b) in (("dev", DEV), ("chk", CHK)):
                        m = op & (t >= np.datetime64(a)) & (t < np.datetime64(b))
                        st = stats(r[m], t[m])
                        st2 = stats(res["c2"][0][m], t[m])
                        rows.append(dict(cfg=tag, rule=rule, period=per, **{k: v for k, v in st.items() if k != "r_by_year"},
                                         c2_avg_r=st2.get("avg_r"), r_by_year=st.get("r_by_year")))
                log(f"{tag} fatto")
    R = pd.DataFrame(rows)
    R.to_csv(OUT / "selftrain_trail_grid.csv", index=False)
    P = R.pivot_table(index=["cfg", "rule"], columns="period",
                      values=["n", "per_year", "avg_r", "pf", "years_pos", "cagr_1pct", "maxdd_1pct", "c2_avg_r"],
                      aggfunc="first")
    P.columns = [f"{a}_{b}" for a, b in P.columns]
    pd.set_option("display.width", 260)
    cols = ["per_year_dev", "avg_r_dev", "pf_dev", "years_pos_dev", "cagr_1pct_dev", "maxdd_1pct_dev", "avg_r_chk",
            "pf_chk", "years_pos_chk", "cagr_1pct_chk", "maxdd_1pct_chk", "c2_avg_r_chk", "per_year_chk"]
    print(P[P.per_year_dev >= 15].sort_values("avg_r_dev", ascending=False)[cols].head(30).to_string())


if __name__ == "__main__":
    main()
