"""FASE 12 — dataset con celle ICT (10) + WYCKOFF (4) nello stesso formato: segnali 2005 -> 2026-01, riempimento
(stop 6 x ATR M15, solo per orario e prezzo d'ingresso) e 105+ feature PRIME. output/cache/phase12/dataset.parquet

usage: python python/scripts/phase12_dataset.py
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from phase11_dataset import feats, log  # noqa: E402
from raptor.prime import cells as C  # noqa: E402
from raptor.prime import wyckoff_cells as W  # noqa: E402
from raptor.prime.data import ROOT, degraded_days, master_m1  # noqa: E402
from raptor.prime.features import M1Context, prime_features  # noqa: E402
from raptor.prime.label import M1Arrays, label_signals  # noqa: E402

OUTD = ROOT / "output" / "cache" / "phase12"


def main():
    W.register()
    OUTD.mkdir(parents=True, exist_ok=True)
    m1 = master_m1()
    F = {(tf, 3): feats(tf) for tf in sorted(set(C.TF_OF.values()) | {"5min", "15min", "1h"})}
    cells = list(C.ALL_CELLS)
    sig = C.generate(F, cells=cells, degraded=degraded_days())
    sig = sig[sig.known_at >= "2005-01-01"].reset_index(drop=True)
    log(f"segnali {len(sig)}: {sig.cell.value_counts().to_dict()}")
    L = label_signals(sig, M1Arrays(m1, F[("5min", 3)]), stop="atr", atr_mult=6.0, profiles=("FOTO",))
    base = L[["bar_time", "known_at", "cell", "tf", "side", "otype", "price"]].copy()
    for col in ("filled", "fill_time", "fill_px"):
        base[f"{col}_a6"] = L[col].values
    X = prime_features(sig, F, M1Context(m1), onehot=cells)
    df = pd.concat([base, X.add_prefix("f_")], axis=1)
    df.to_parquet(OUTD / "dataset.parquet")
    log(f"dataset {df.shape}")


if __name__ == "__main__":
    main()
