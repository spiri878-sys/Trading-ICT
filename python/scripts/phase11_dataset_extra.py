"""FASE 11 — etichette aggiuntive per stop larghi (il venditore usa stop ampi: monitor fino a 28 ATR M15, trade
dell'8/1/2026 con stop 21 $): 10 x ATR M15 ('a10') e stop strutturale con minimo 6 x ATR M15 ('sf6').
Aggiunge colonne a output/cache/phase11/dataset.parquet (stesso ordine dei segnali).

usage: python python/scripts/phase11_dataset_extra.py
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from phase11_dataset import COSTS_C2, OUTD, feats, log  # noqa: E402
from raptor.prime import cells as C  # noqa: E402
from raptor.prime.data import degraded_days, master_m1  # noqa: E402
from raptor.prime.label import M1Arrays, label_signals  # noqa: E402


def main():
    df = pd.read_parquet(OUTD / "dataset.parquet")
    m1 = master_m1()
    F = {(tf, 3): feats(tf) for tf in sorted(set(C.TF_OF.values()) | {"5min", "15min", "1h"})}
    sig = C.generate(F, cells=list(C.ALL_CELLS), degraded=degraded_days())
    sig = sig[sig.known_at >= "2005-01-01"].reset_index(drop=True)
    key = ["known_at", "cell", "side", "bar_time"]
    assert len(sig) == len(df) and (sig[key].values == df[key].values).all()
    f5 = F[("5min", 3)]
    A1, A2 = M1Arrays(m1, f5), M1Arrays(m1, f5, spread=COSTS_C2["spread"])
    sf = sig.copy()
    floor = sf.price - sf.side * 6.0 * sf.atr_m15
    sf["sl_struct"] = np.where(sf.side == 1, np.minimum(sf.sl_struct, floor), np.maximum(sf.sl_struct, floor))
    for tag, s_, kw in (("a10", sig, dict(stop="atr", atr_mult=10.0)), ("sf6", sf, dict(stop="struct"))):
        L1 = label_signals(s_, A1, profiles=("FOTO",), **kw)
        L2 = label_signals(s_, A2, profiles=("FOTO",), costs=COSTS_C2, **kw)
        for col in ("filled", "fill_time", "fill_px", "risk_px", "mfe_r", "mae_before_1r", "r_foto", "exit_foto",
                    "exit_time_foto"):
            df[f"{col}_{tag}"] = L1[col].values
        df[f"r_c2_{tag}"] = L2.r_foto.values
        log(f"etichette {tag}: R medio {L1.r_foto[L1.filled].mean():+.3f}, rischio mediano {L1.risk_px.median():.2f}")
    df.to_parquet(OUTD / "dataset.parquet")


if __name__ == "__main__":
    main()
