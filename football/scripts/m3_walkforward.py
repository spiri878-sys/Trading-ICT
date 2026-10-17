"""Walk-forward dei modelli dei conteggi (Fase M3).

Per ogni anno di verifica Y (finestra 1 luglio Y -> 30 giugno Y+1): LightGBM addestrato su tutte le partite
PRIMA del 1 luglio Y (dal 2008), arresto anticipato sull'ultimo 15% (in ordine di data) dell'addestramento.
Salva per ogni statistica le previsioni fuori campione di tutti gli approcci in data/cache/m3/<stat>.pkl.
Uso: python football/scripts/m3_walkforward.py [stat ...]   (default: tutte)
"""
import pickle
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fb.data import CACHE, matches  # noqa: E402
from fb.models import TARGETS, add_targets, candidates, fit_lgb, poisson_dev  # noqa: E402

YEARS = range(2019, 2027)
OUT = CACHE / "m3"


def run(stat, m, X):
    h, a = TARGETS[stat]
    has = m[h].notna() & m[a].notna()
    rows = []
    for y in YEARS:
        t0 = time.time()
        start, end = pd.Timestamp(f"{y}-07-01"), pd.Timestamp(f"{y + 1}-07-01")
        tr = has & (m.date >= "2008-07-01") & (m.date < start)
        te = has & (m.date >= start) & (m.date < end)
        if te.sum() == 0:
            continue
        tr_idx = np.flatnonzero(tr.to_numpy())
        cut = int(len(tr_idx) * 0.85)
        fit, va = tr_idx[:cut], tr_idx[cut:]
        pred = {}
        for side, col in (("h", h), ("a", a)):
            b, it = fit_lgb(X.iloc[fit], m[col].iloc[fit], X.iloc[va], m[col].iloc[va])
            pred[side] = b.predict(X[te], num_iteration=it)
        Xt = X[te]
        cand = candidates(Xt, stat, pred["h"], pred["a"])
        df = pd.DataFrame({"year": y, "yh": m.loc[te, h].to_numpy(float), "ya": m.loc[te, a].to_numpy(float)},
                          index=Xt.index)
        for k, (ph, pa) in cand.items():
            df[f"{k}_h"], df[f"{k}_a"] = ph, pa
        rows.append(df)
        dv = {k: round(poisson_dev(df.yh, df[f"{k}_h"]) + poisson_dev(df.ya, df[f"{k}_a"]), 4) for k in cand}
        print(f"{stat} {y}: n={te.sum()} train={tr.sum()} iter={it} devianza={dv} ({time.time() - t0:.0f}s)",
              flush=True)
    res = pd.concat(rows)
    OUT.mkdir(parents=True, exist_ok=True)
    pickle.dump(res, open(OUT / f"{stat}.pkl", "wb"))


def main(stats):
    m = add_targets(matches())
    X = pickle.load(open(CACHE / "m2_features.pkl", "rb"))
    for s in stats:
        run(s, m, X)


if __name__ == "__main__":
    main(sys.argv[1:] or list(TARGETS))
