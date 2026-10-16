"""FASE 11 — dataset completo per l'autoallenamento: 10 celle, 2005 -> 2026-01-30, etichette FOTO per 3 stop
(strutturale, 3 e 6 x ATR M15) con costi C1 e C2, 105 feature PRIME. Scrive output/cache/phase11/dataset.parquet.

Ogni etichetta guarda solo il futuro del segnale stesso (esito); le feature solo il passato. Il dataset NON sceglie
nulla: tutte le scelte avvengono in phase11_selftrain.py con walk-forward.

usage: python python/scripts/phase11_dataset.py
"""
import sys
import time
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from raptor.prime import cells as C  # noqa: E402
from raptor.prime.data import ROOT, degraded_days, master_m1  # noqa: E402
from raptor.prime.features import M1Context, prime_features  # noqa: E402
from raptor.prime.label import COSTS_C1, M1Arrays, label_signals  # noqa: E402
from raptor.setups import build_features  # noqa: E402

CACHE = ROOT / "output" / "cache"
OUTD = CACHE / "phase11"
COSTS_C2 = dict(spread=0.60, comm_per_lot_side=7.0, slip=0.10, swap_long=-0.066, swap_short=0.029)
STOPS = {"st": dict(stop="struct"), "a3": dict(stop="atr", atr_mult=3.0), "a6": dict(stop="atr", atr_mult=6.0)}


def log(msg, t0=[time.time()]):
    print(f"[{time.time() - t0[0]:6.0f}s] {msg}", flush=True)


def feats(tf, k=3):
    p = CACHE / f"feat_prime_{tf}_k{k}.parquet"
    if p.exists():
        return pd.read_parquet(p)
    f = build_features(master_m1(), tf, k)
    f.to_parquet(p)
    return f


def main():
    OUTD.mkdir(parents=True, exist_ok=True)
    m1 = master_m1()
    tfs = sorted(set(C.TF_OF.values()) | {"5min", "15min", "1h"})
    F = {}
    for tf in tfs:
        F[(tf, 3)] = feats(tf)
        log(f"feature {tf}: {len(F[(tf, 3)])} barre")
    cells = list(C.ALL_CELLS)
    sig = C.generate(F, cells=cells, degraded=degraded_days())
    sig = sig[sig.known_at >= "2005-01-01"].reset_index(drop=True)
    log(f"segnali: {len(sig)} {sig.cell.value_counts().to_dict()}")
    f5 = F[("5min", 3)]
    A1, A2 = M1Arrays(m1, f5), M1Arrays(m1, f5, spread=COSTS_C2["spread"])
    base = None
    for tag, kw in STOPS.items():
        L1 = label_signals(sig, A1, profiles=("FOTO",), **kw)
        L2 = label_signals(sig, A2, profiles=("FOTO",), costs=COSTS_C2, **kw)
        if base is None:
            base = L1[["bar_time", "known_at", "cell", "tf", "side", "otype", "price"]].copy()
        for col in ("filled", "fill_time", "fill_px", "risk_px", "mfe_r", "mae_before_1r", "r_foto", "exit_foto",
                    "exit_time_foto"):
            base[f"{col}_{tag}"] = L1[col].values
        base[f"r_c2_{tag}"] = L2.r_foto.values
        log(f"etichette stop {tag}: riempiti {L1.filled.mean():.2f}, R medio {L1.r_foto[L1.filled].mean():+.3f}")
    X = prime_features(sig, F, M1Context(m1), onehot=cells)
    df = pd.concat([base, X.add_prefix("f_")], axis=1)
    df.to_parquet(OUTD / "dataset.parquet")
    log(f"dataset: {df.shape} -> {OUTD / 'dataset.parquet'}")


if __name__ == "__main__":
    main()
