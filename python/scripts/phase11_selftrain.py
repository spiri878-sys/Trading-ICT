"""FASE 11 — autoallenamento sempre attivo: punteggi fuori campione 2010 -> 2026-01 con riaddestramento periodico.

Per ogni configurazione (stop, finestra, decadimento, target, memoria ombra) il modello è rifatto a ogni data di
riaddestramento usando SOLO esiti già chiusi a quella data. I punteggi sono salvati in
output/cache/phase11/scores_<cfg>.parquet; la scelta di soglia/configurazione avviene in phase11_eval.py.

usage: python python/scripts/phase11_selftrain.py [every=QS]
"""
import itertools
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from raptor.prime.data import ROOT, config  # noqa: E402
from raptor.prime.selftrain import retrain_dates, session_of, shadow_memory, walk_forward_selftrain  # noqa: E402

D = ROOT / "output" / "cache" / "phase11"
EVERY = sys.argv[1] if len(sys.argv) > 1 else "QS"
START, END = "2010-01-01", "2026-01-01"


def log(msg, t0=[time.time()]):
    print(f"[{time.time() - t0[0]:6.0f}s] {msg}", flush=True)


def with_memory(df, tag):
    r, ex = f"r_foto_{tag}", f"exit_time_foto_{tag}"
    d = df.copy()
    d["sess"] = session_of(d.known_at)
    m = [shadow_memory(d, r, ex, ["cell", "side"], prefix="mem_cs"),
         shadow_memory(d, r, ex, ["cell", "side", "sess"], prefix="mem_css", n_last=(30,), days=(365,)),
         shadow_memory(d, r, ex, ["side"], prefix="mem_s", n_last=(100, 300), days=(90, 365)),
         shadow_memory(d, r, ex, ["cell"], prefix="mem_c", n_last=(100,), days=(365, 730))]
    return pd.concat(m, axis=1).add_prefix("f_")


def main():
    seed = config()["seed"]
    df = pd.read_parquet(D / "dataset.parquet")
    base_feats = [c for c in df.columns if c.startswith("f_")]
    dates = retrain_dates(START, END, EVERY)
    grid = list(itertools.product(["a6", "a3", "st"], [None, 3], [None, 1.5], ["reg"], [True]))
    grid += [("a6", None, None, "cls", True), ("a6", None, None, "reg", False)]
    for tag, win, hl, tgt, mem in grid:
        name = f"{tag}_w{win or 0}_h{hl or 0}_{tgt}_{'mem' if mem else 'nomem'}_{EVERY}"
        p = D / f"scores_{name}.parquet"
        if p.exists():
            continue
        d = df[df[f"filled_{tag}"]].copy()
        feats = list(base_feats)
        if mem:
            M = with_memory(d, tag)
            d = pd.concat([d, M], axis=1)
            feats += list(M.columns)
        r = d[f"r_foto_{tag}"]
        d["y"] = r.clip(-1.5, 4.0) if tgt == "reg" else (r > 0).astype(float)
        obj = "huber" if tgt == "reg" else "binary"
        s = walk_forward_selftrain(d, feats, "y", f"exit_time_foto_{tag}", dates, window_years=win,
                                   half_life_years=hl, objective=obj, params={"alpha": 1.0} if tgt == "reg" else None,
                                   seed=seed)
        out = d[["known_at", "cell", "side", f"fill_time_{tag}", f"exit_time_foto_{tag}", f"r_foto_{tag}",
                 f"r_c2_{tag}"]].copy()
        out.columns = ["known_at", "cell", "side", "fill_time", "exit_time", "r", "r_c2"]
        out["score"] = s.values
        if mem:
            out["mem_cs_d730"] = d["f_mem_cs_d730"].values
            out["mem_cs_d365"] = d["f_mem_cs_d365"].values
            out["mem_cs_n100"] = d["f_mem_cs_n100"].values
        out.to_parquet(p)
        log(f"{name}: {out.score.notna().sum()} punteggi")


if __name__ == "__main__":
    main()
