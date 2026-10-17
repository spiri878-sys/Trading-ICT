"""F6 — modelli angoli finali (feature angoli + tuning) su TUTTA la storia, usati dalla scheda partita.
Previsione = media tra (casa + ospite) e il modello del totale, come 'media_mix' nella valutazione F6.

usage: python football/scripts/f6_train_final.py
"""
import json
import sys
from pathlib import Path

import lightgbm as lgb
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fb.card import MODELS  # noqa: E402
from fb.corners import corner_feats, market_feats  # noqa: E402
from fb.data import CACHE, ROOT, matches  # noqa: E402
sys.path.insert(0, str(Path(__file__).resolve().parent))
from f6_corners import P_NEW  # noqa: E402

ROUNDS = {"h": 450, "a": 650, "tot": 350}   # tipici dalla scelta per stagione in F6


def main():
    m = matches()
    meta = json.loads((MODELS / "meta.json").read_text())
    X = pd.read_parquet(CACHE / "f2_features.parquet")
    X["div_code"] = pd.Categorical(m.Division, categories=meta["div_categories"]).codes
    C = pd.read_parquet(CACHE / "f6_corner_feats.parquet")
    XA = pd.concat([X, C, market_feats(m, X)], axis=1)
    feats = list(XA.columns)
    ys = {"h": m.HomeCorners, "a": m.AwayCorners, "tot": m.HomeCorners + m.AwayCorners}
    for k, y in ys.items():
        ok = y.notna().values
        lgb.train(P_NEW, lgb.Dataset(XA.loc[ok, feats], y[ok].values), ROUNDS[k]).save_model(
            str(MODELS / f"cor6_{k}.txt"))
        print("angoli", k, "fatto", flush=True)
    ev = json.loads((ROOT / "output" / "f6_corners_eval.json").read_text())
    meta["cor6"] = {"features": feats, "k": ev["media_mix"]["k_medio"]}
    (MODELS / "meta.json").write_text(json.dumps(meta, indent=1))


if __name__ == "__main__":
    main()
