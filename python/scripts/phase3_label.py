"""FASE 3 — etichettatura dei segnali delle 6 celle e baseline senza filtri.

* rigenera i segnali di default (cells.generate) su tutta la serie e li etichetta su M1 con costi C1:
  profili FOTO e V5, stop strutturale e 3 x ATR M15 -> output/cache/labels/default.parquet
* baseline SOLO 2008-2021 (addestramento 2008-2017, validazione 2018-2021): per cella, anno, lato, profilo
* benchmark casuale: stessi minuti d'ingresso e stessa distanza di stop, direzione casuale (N_RAND ripetizioni)
Il periodo di test (2022+) viene etichettato per le fasi successive ma NON entra in nessuna statistica.

usage: python python/scripts/phase3_label.py
"""
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from numba import njit

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from raptor.prime import cells as C  # noqa: E402
from raptor.prime.data import ROOT, config, degraded_days, master_m1  # noqa: E402
from raptor.prime.label import COSTS_C1, PROFILES, M1Arrays, label_signals, manage  # noqa: E402

OUT = ROOT / "output"
CACHE = OUT / "cache"
TRAIN, VAL = ("2008-01-01", "2018-01-01"), ("2018-01-01", "2022-01-01")
N_RAND = 50


def feats(tf, k):
    return pd.read_parquet(CACHE / f"feat_prime_{tf}_k{k}.parquet")


def summarize(r):
    r = r.dropna()
    if r.empty:
        return {}
    gp, gl = r[r > 0].sum(), -r[r < 0].sum()
    eq = r.cumsum()
    return dict(n=int(len(r)), avg_r=round(float(r.mean()), 4), pf=round(float(gp / gl), 3) if gl > 0 else None,
                win=round(float((r > 0).mean()), 3), total_r=round(float(r.sum()), 1),
                max_dd_r=round(float((eq.cummax() - eq).max()), 1))


@njit(cache=True)
def _random_bench(o, h, l, c, sp, dow, mod, swl, swh, brk5, atr5, fi, fp, rd, sides, prof, max_hold, fri, slip,
                  comm):
    n = fi.size
    out = np.empty(n)
    for k in range(n):
        side = sides[k]
        entry = fp[k] if side == 1 else fp[k]
        sl = entry - side * rd[k]
        ei, pnl, rs = manage(o, h, l, c, sp, dow, mod, swl, swh, brk5, atr5, fi[k], side, entry, sl, rd[k],
                             prof[0], prof[1], prof[2], prof[3], prof[4], prof[5] > 0, prof[6] > 0, prof[7] > 0,
                             max_hold, fri, slip)
        out[k] = (pnl - 2 * comm) / (rd[k] + slip + 2 * comm)
    return out


def main():
    t0 = time.time()
    seed = config()["seed"]
    m1 = master_m1()
    f5 = feats("5min", 3)
    A = M1Arrays(m1, f5)
    F = {(C.TF_OF[c], C.DEFAULTS[c]["k"]): feats(C.TF_OF[c], C.DEFAULTS[c]["k"]) for c in C.CELLS}
    sig = C.generate(F, degraded=degraded_days())
    sig = sig[sig.known_at >= "2005-01-01"].reset_index(drop=True)
    print(f"segnali {len(sig)}")
    Ls = label_signals(sig, A, stop="struct")
    La = label_signals(sig, A, stop="atr", atr_mult=3.0)
    lab = Ls.copy()
    for col in ("filled", "fill_px", "risk_px", "mfe_r", "mae_before_1r", "big_runner", "clean_entry", "r_foto",
                "r_v5", "exit_foto", "exit_v5"):
        lab[f"{col}_atr"] = La[col].values
    (CACHE / "labels").mkdir(exist_ok=True)
    lab.to_parquet(CACHE / "labels" / "default.parquet")
    print(f"etichettati in {time.time() - t0:.0f}s")

    # ------------- baseline 2008-2021 only
    base = lab[(lab.known_at >= TRAIN[0]) & (lab.known_at < VAL[1])].copy()
    base["period"] = np.where(base.known_at < TRAIN[1], "train_2008_2017", "val_2018_2021")
    base["year"] = base.known_at.dt.year
    rows, stats = [], {"by_cell": {}}
    for cell, g in base.groupby("cell"):
        d = {"signals": int(len(g)), "fill_rate": round(float(g.filled.mean()), 3),
             "fill_rate_atr": round(float(g.filled_atr.mean()), 3),
             "big_runner_rate": round(float(g.big_runner.mean()), 3),
             "clean_entry_rate": round(float(g.clean_entry.mean()), 3),
             "median_risk_usd": round(float(g.risk_px.median()), 2),
             "median_risk_usd_atr": round(float(g.risk_px_atr.median()), 2)}
        for per, gp in g.groupby("period"):
            for prof in ("foto", "v5"):
                d[f"{per}_{prof}_struct"] = summarize(gp[f"r_{prof}"])
                d[f"{per}_{prof}_atr"] = summarize(gp[f"r_{prof}_atr"])
            for side, gs in gp.groupby("side"):
                d[f"{per}_foto_struct_{'long' if side == 1 else 'short'}"] = summarize(gs["r_foto"])
        stats["by_cell"][cell] = d
        for (yr, ), gy in g.groupby(["year"]):
            rows.append({"cell": cell, "year": yr, "signals": len(gy), "filled": int(gy.filled.sum()),
                         **{f"{p}_{s}_{k}": v for p in ("foto", "v5") for s, col in (("struct", f"r_{p}"),
                                                                                       ("atr", f"r_{p}_atr"))
                            for k, v in summarize(gy[col]).items() if k in ("avg_r", "pf", "total_r")},
                         "big_runner": round(float(gy.big_runner.mean()), 3)})
    yr = pd.DataFrame(rows)
    yr.to_csv(OUT / "phase3_baseline_by_year.csv", index=False)

    # ------------- random-direction benchmark (same fill minute & stop distance), FOTO + struct
    rng = np.random.default_rng(seed)
    prof = np.array([PROFILES["FOTO"][k] for k in ("p1_r", "p1_frac", "p2_r", "p2_frac", "tp_r")] + [0, 0, 0], float)
    bench = {}
    idx = A.index.values
    for cell, g in base[base.filled].groupby("cell"):
        fi = np.searchsorted(idx, g.fill_time.values.astype("datetime64[ns]")).astype(np.int64)
        fp, rd = g.fill_px.values.astype(float), g.risk_px.values.astype(float)
        real = float(g.r_foto.mean())
        means = []
        for _ in range(N_RAND):
            sides = rng.choice(np.array([-1, 1]), size=len(g)).astype(np.int64)
            r = _random_bench(A.o, A.h, A.l, A.c, A.sp, A.dow, A.mod, A.swl, A.swh, A.brk5, A.atr5, fi, fp, rd,
                              sides, prof, 3 * 24 * 60, 23 * 60, COSTS_C1["slip"], COSTS_C1["comm_per_lot_side"] / 100)
            means.append(r.mean())
        means = np.array(means)
        bench[cell] = {"real_avg_r_foto": round(real, 4), "random_mean": round(float(means.mean()), 4),
                       "random_p95": round(float(np.percentile(means, 95)), 4),
                       "share_random_ge_real": round(float((means >= real).mean()), 3), "n": int(len(g))}
    stats["random_benchmark_foto_struct_2008_2021"] = bench
    stats["notes"] = {"costs": COSTS_C1, "big_runner": "MFE >= 3R prima dello stop iniziale",
                      "clean_entry": "MAE > -0.5R prima di toccare +1R", "n_random": N_RAND,
                      "test_period": "etichettato ma escluso da ogni statistica"}
    stats["runtime_s"] = round(time.time() - t0)
    (OUT / "phase3_baseline.json").write_text(json.dumps(stats, indent=1, default=str))
    pd.set_option("display.width", 250)
    for cell, d in stats["by_cell"].items():
        print(cell, {k: v for k, v in d.items() if not isinstance(v, dict)})
        for k, v in d.items():
            if isinstance(v, dict):
                print("   ", k, v)
    print(json.dumps(bench, indent=1))


if __name__ == "__main__":
    main()
