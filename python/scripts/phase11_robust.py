"""FASE 11 — robustezza del candidato 'celle ICT + regime + AI autoallenata + trailing ATR H4'.

1. semi diversi di LightGBM; 2. stop/trailing vicini; 3. frequenza di riaddestramento (6 mesi / trimestre);
4. finestra 3/4/5 anni; 5. selezioni casuali dello stesso numero di trade dentro il filtro di regime (200 estrazioni).
Regola fissata prima: filtro regime + R atteso > 0, training solo sui trade nel regime. Un trade alla volta.

usage: python python/scripts/phase11_robust.py
"""
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from phase11_selftrain import with_memory  # noqa: E402
from phase11_trend_exit import CACHE, OUT, regime_cols, stats  # noqa: E402
from raptor.prime.data import master_m1  # noqa: E402
from raptor.prime.selftrain import one_at_a_time, retrain_dates, walk_forward_selftrain  # noqa: E402
from raptor.prime.trail import atr_on_m1, sim_trail  # noqa: E402

DEV, CHK = ("2010-01-01", "2016-01-01"), ("2016-01-01", "2026-02-01")


def log(msg, t0=[time.time()]):
    print(f"[{time.time() - t0[0]:6.0f}s] {msg}", flush=True)


class Base:
    def __init__(self):
        df = pd.read_parquet(CACHE / "phase11" / "dataset.parquet")
        df = df[df.filled_a6].reset_index(drop=True)
        reg = regime_cols(df)
        df = pd.concat([df, reg.add_prefix("f_rg_")], axis=1)
        self.side = df.side.values.astype(np.int64)
        for k in reg.columns:
            df[f"f_rg_{k}_al"] = (reg[k].values == self.side).astype(float)
        self.df = df
        self.flt = (reg.h4don20.values == self.side) & (reg.d1ema.values == self.side)
        m1 = master_m1()
        self.idx = m1.index
        self.ohlc = tuple(m1[k].values.astype(float) for k in ("open", "high", "low", "close"))
        self.day = self.idx.values.astype("datetime64[D]").astype(np.int64)
        self.a4 = atr_on_m1(self.idx, pd.read_parquet(CACHE / "tf" / "XAUUSD_H4.parquet"))
        self.fi = np.searchsorted(self.idx.values, df.fill_time_a6.values.astype("datetime64[ns]")).astype(np.int64)
        self.fpx = df.fill_px_a6.values.astype(float)
        self.t = df.known_at.values

    def label(self, slm, trm, hold, spread=0.30, slip=0.05, comm=0.035):
        o, h, l, c = self.ohlc
        r, ei, _ = sim_trail(o, h, l, c, np.full(o.size, spread), self.day, self.a4, self.fi, self.fpx, self.side, slm,
                             trm, 0.7, 0.0, 2.0, 0.0, hold * 1380, slip, comm, -0.066, 0.029, False)
        et = np.where(ei >= 0, self.idx.values[np.maximum(ei, 0)], np.datetime64("NaT", "ns"))
        return r, et

    def scores(self, r, et, seed=20261011, every="2QS", window=4):
        d = self.df.copy()
        d["r_foto_X"], d["exit_time_foto_X"] = r, pd.Series(et)
        d = pd.concat([d, with_memory(d, "X")], axis=1)
        feats = [x for x in d.columns if x.startswith("f_")]
        d["y"] = np.clip(r, -1.5, 6.0)
        ok = np.isfinite(r) & ~np.isnat(et) & self.flt
        dd = d[ok]
        s = walk_forward_selftrain(dd, feats, "y", "exit_time_foto_X", retrain_dates("2010-01-01", "2026-01-01", every),
                                   window_years=window, objective="huber", params={"alpha": 1.0}, seed=seed)
        sc = np.full(len(d), np.nan)
        sc[np.where(ok)[0]] = s.values
        return sc

    def evaluate(self, r, et, take):
        op = one_at_a_time(self.idx.values[self.fi], et, take, r)
        out = {}
        for per, (a, b) in (("dev", DEV), ("chk", CHK)):
            m = op & (self.t >= np.datetime64(a)) & (self.t < np.datetime64(b))
            out[per] = {k: v for k, v in stats(r[m], self.t[m]).items() if k != "r_by_year"}
        return out, op


def main():
    B = Base()
    res = {}
    r, et = B.label(1.5, 5.0, 10)
    base_sc = B.scores(r, et)
    take = B.flt & (np.nan_to_num(base_sc, nan=-9) > 0)
    res["candidato"], op = B.evaluate(r, et, take)
    log(f"candidato {res['candidato']}")
    # 5. selezioni casuali: stesso numero di candidati per semestre, dentro il filtro, poi un trade alla volta
    rng = np.random.default_rng(7)
    half = pd.DatetimeIndex(B.t).year * 2 + (pd.DatetimeIndex(B.t).month > 6)
    elig = B.flt & np.isfinite(r) & (B.t >= np.datetime64("2010-01-01"))
    rand = []
    for k in range(200):
        tk = np.zeros(len(r), bool)
        for hcode in np.unique(half[take]):
            pool = np.where(elig & (half == hcode))[0]
            n = int((take & (half == hcode)).sum())
            if len(pool) and n:
                tk[rng.choice(pool, size=min(n, len(pool)), replace=False)] = True
        ev, _ = B.evaluate(r, et, tk)
        rand.append((ev["dev"].get("avg_r", np.nan), ev["chk"].get("avg_r", np.nan)))
    rand = np.array(rand)
    res["casuale"] = {"dev_mean": round(float(np.nanmean(rand[:, 0])), 3), "dev_p95": round(float(np.nanpercentile(rand[:, 0], 95)), 3),
                      "chk_mean": round(float(np.nanmean(rand[:, 1])), 3), "chk_p95": round(float(np.nanpercentile(rand[:, 1], 95)), 3),
                      "p_dev": round(float((rand[:, 0] >= res["candidato"]["dev"]["avg_r"]).mean()), 3),
                      "p_chk": round(float((rand[:, 1] >= res["candidato"]["chk"]["avg_r"]).mean()), 3)}
    log(f"casuale {res['casuale']}")
    # 1. semi
    for seed in (1, 2, 3):
        sc = B.scores(r, et, seed=seed)
        res[f"seme_{seed}"], _ = B.evaluate(r, et, B.flt & (np.nan_to_num(sc, nan=-9) > 0))
        log(f"seme {seed} {res[f'seme_{seed}']}")
    # 3./4. frequenza e finestra
    for every, win in (("QS", 4), ("2QS", 3), ("2QS", 5), ("YS", 4)):
        sc = B.scores(r, et, every=every, window=win)
        res[f"riaddestra_{every}_finestra_{win}"], _ = B.evaluate(r, et, B.flt & (np.nan_to_num(sc, nan=-9) > 0))
        log(f"{every} w{win} {res[f'riaddestra_{every}_finestra_{win}']}")
    # 2. stop / trailing vicini
    for slm, trm, hold in ((1.5, 4.0, 10), (2.0, 5.0, 10), (1.5, 5.0, 5), (2.0, 4.0, 10), (3.0, 5.0, 10)):
        r2, et2 = B.label(slm, trm, hold)
        sc = B.scores(r2, et2)
        res[f"sl{slm}_tr{trm}_h{hold}"], _ = B.evaluate(r2, et2, B.flt & (np.nan_to_num(sc, nan=-9) > 0))
        log(f"sl{slm} tr{trm} h{hold} {res[f'sl{slm}_tr{trm}_h{hold}']}")
    # costi doppi sul candidato
    r3, _ = B.label(1.5, 5.0, 10, spread=0.60, slip=0.10, comm=0.07)
    res["candidato_costi_x2"], _ = B.evaluate(r3, et, take)
    (OUT / "robust.json").write_text(json.dumps(res, indent=1, default=str))
    log("fatto")


if __name__ == "__main__":
    main()
