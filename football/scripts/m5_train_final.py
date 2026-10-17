"""Modelli finali per l'uso giornaliero (Fase M5): LightGBM per ogni statistica e lato su tutte le partite dal 2008.
Numero di alberi: arresto anticipato sull'ultimo 15% (in ordine di data), poi riaddestramento su tutto.
Salva models/m5_<stat>_<h|a>.txt e models/m5_features.json (ordine delle colonne).
Uso: python football/scripts/m5_train_final.py [stat ...]
"""
import json
import pickle
import sys
from pathlib import Path

import lightgbm as lgb
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fb.data import CACHE, ROOT, matches  # noqa: E402
from fb.models import PARAMS, TARGETS, add_targets, fit_lgb  # noqa: E402

MODELS = ROOT / "models"


def main(stats):
    m = add_targets(matches())
    X = pickle.load(open(CACHE / "m2_features.pkl", "rb"))
    MODELS.mkdir(exist_ok=True)
    (MODELS / "m5_features.json").write_text(json.dumps(list(X.columns)))
    for stat in stats:
        h, a = TARGETS[stat]
        has = (m[h].notna() & m[a].notna() & (m.date >= "2008-07-01")).to_numpy()
        idx = np.flatnonzero(has)
        cut = int(len(idx) * 0.85)
        for side, col in (("h", h), ("a", a)):
            _, it = fit_lgb(X.iloc[idx[:cut]], m[col].iloc[idx[:cut]], X.iloc[idx[cut:]], m[col].iloc[idx[cut:]])
            b = lgb.train(PARAMS, lgb.Dataset(X.iloc[idx], m[col].iloc[idx]), max(int(it * 1.1), 50))
            b.save_model(str(MODELS / f"m5_{stat}_{side}.txt"))
            print(f"{stat} {side}: {len(idx)} partite, {b.num_trees()} alberi", flush=True)


if __name__ == "__main__":
    main(sys.argv[1:] or list(TARGETS))
