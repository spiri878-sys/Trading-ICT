"""FASE 4 — feature per segnale (output/feature.md) + diagnostica SOLO sull'addestramento 2008-2017.

* feature causali per tutti i segnali di default dal 2005 -> output/cache/features/default.parquet
  (unite alle etichette della Fase 3)
* diagnostica 2008-2017: valori mancanti, costanti, coppie con |corr| > 0,95, AUC univariata contro
  big_runner e clean_entry, R medio (FOTO, stop 3 ATR) per quintile. Nessuna selezione definitiva.
* genera output/feature.md e verifica che elenchi esattamente le colonne prodotte.

usage: python python/scripts/phase4_features.py
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from raptor.prime import cells as C  # noqa: E402
from raptor.prime.data import ROOT, degraded_days, master_m1  # noqa: E402
from raptor.prime.features import GROUPS, M1Context, doc_for, prime_features  # noqa: E402

OUT = ROOT / "output"
CACHE = OUT / "cache"
TRAIN = ("2008-01-01", "2018-01-01")
GROUP_NAMES = {"A": "Segnale", "B": "Volatilità", "C": "Struttura", "D": "Momentum ed efficienza", "E": "Volumi",
               "F": "Sessione e tempo", "G": "Costi", "H": "Contesto delle celle"}


def main():
    F = {(tf, 3): pd.read_parquet(CACHE / f"feat_prime_{tf}_k3.parquet") for tf in set(C.TF_OF.values())}
    sig = C.generate(F, degraded=degraded_days())
    sig = sig[sig.known_at >= "2005-01-01"].reset_index(drop=True)
    X = prime_features(sig, F, M1Context(master_m1()))
    lab = pd.read_parquet(CACHE / "labels" / "default.parquet")
    key = ["known_at", "cell", "side", "bar_time"]
    assert len(lab) == len(sig) and (lab[key].values == sig[key].values).all(), "etichette non allineate"
    df = pd.concat([lab.reset_index(drop=True), X.add_prefix("f_")], axis=1)
    (CACHE / "features").mkdir(exist_ok=True)
    df.to_parquet(CACHE / "features" / "default.parquet")
    feats = list(X.columns)

    # ---------------- feature.md
    lines = ["# Feature per segnale (Fase 4)", "",
             f"**{len(feats)} feature**, tutte a soli rapporti/ATR (mai prezzi), direzionali moltiplicate per il "
             "lato (positivo = a favore), note alla chiusura dell'ultima barra prima del segnale. Codice: "
             "`python/raptor/prime/features.py`. Nel file `output/cache/features/default.parquet` hanno il prefisso "
             "`f_`.", "",
             "**Mancante:** *notizia in arrivo* (citata nelle foto) richiede il calendario economico: Fase 6.", ""]
    for gk, gname in GROUP_NAMES.items():
        lines += [f"## {gk}. {gname}", "", "| Feature | Formula | TF | Fonte |", "|---|---|---|---|"]
        for nm in [f for f in feats if GROUPS[f] == gk]:
            d = doc_for(nm)
            lines.append(f"| `{nm}` | {d[1]} | {d[2]} | {d[3]} |" if d else f"| `{nm}` | ? | ? | ? |")
        lines.append("")
    (OUT / "feature.md").write_text("\n".join(lines))
    md = (OUT / "feature.md").read_text()
    missing_doc = [f for f in feats if f"`{f}`" not in md]
    assert not missing_doc and all(doc_for(f) for f in feats), f"feature non documentate: {missing_doc}"

    # ---------------- diagnostics on TRAIN only
    tr = df[(df.known_at >= TRAIN[0]) & (df.known_at < TRAIN[1])]
    Xt = tr[[f"f_{f}" for f in feats]]
    stats = {"n_features": len(feats), "n_signals_total": int(len(df)), "n_train": int(len(tr)),
             "groups": {GROUP_NAMES[g]: sum(1 for f in feats if GROUPS[f] == g) for g in GROUP_NAMES}}
    stats["missing_pct_train"] = {f: round(float(v), 4) for f, v in (Xt.isna().mean() * 100).items() if v > 0}
    stats["constant_train"] = [c[2:] for c in Xt.columns if Xt[c].nunique(dropna=True) <= 1]
    corr = Xt.corr().abs()
    pairs = [(a[2:], b[2:], round(float(corr.loc[a, b]), 3)) for i, a in enumerate(corr.columns)
             for b in corr.columns[i + 1:] if corr.loc[a, b] > 0.95]
    stats["corr_pairs_gt_095"] = pairs
    filled = tr[tr.filled_atr == True]  # noqa: E712
    rows = []
    for f in feats:
        x = filled[f"f_{f}"].values
        ok = np.isfinite(x)
        rec = {"feature": f, "group": GROUP_NAMES[GROUPS[f]]}
        for tgt in ("big_runner_atr", "clean_entry_atr"):
            y = filled[tgt].values.astype(float)
            m = ok & np.isfinite(y)
            try:
                auc = roc_auc_score(y[m], x[m])
            except ValueError:
                auc = np.nan
            rec[f"auc_{tgt.replace('_atr', '')}"] = round(float(auc), 4)
        r = filled["r_foto_atr"].values
        m = ok & np.isfinite(r)
        if m.sum() > 100 and np.unique(x[m]).size > 4:
            q = pd.qcut(pd.Series(x[m]).rank(method="first"), 5, labels=False)
            qm = pd.Series(r[m]).groupby(q.values).mean()
            rec["r_q1"], rec["r_q5"] = round(float(qm.iloc[0]), 4), round(float(qm.iloc[-1]), 4)
            rec["r_spread_q5_q1"] = round(float(qm.iloc[-1] - qm.iloc[0]), 4)
        rows.append(rec)
    info = pd.DataFrame(rows)
    info["auc_dev_big"] = (info.auc_big_runner - 0.5).abs()
    info = info.sort_values("auc_dev_big", ascending=False)
    info.to_csv(OUT / "phase4_univariate_train.csv", index=False)
    stats["top20_by_auc_big_runner"] = info.head(20)[["feature", "group", "auc_big_runner", "auc_clean_entry",
                                                       "r_q1", "r_q5"]].to_dict("records")
    best_r = info.dropna(subset=["r_spread_q5_q1"]).reindex(
        info.r_spread_q5_q1.abs().sort_values(ascending=False).index).head(15)
    stats["top15_by_r_quintile_spread"] = best_r[["feature", "r_q1", "r_q5", "r_spread_q5_q1"]].to_dict("records")
    stats["base_rates_train"] = {"big_runner": round(float(filled.big_runner_atr.mean()), 3),
                                 "clean_entry": round(float(filled.clean_entry_atr.mean()), 3),
                                 "avg_r_foto_atr": round(float(filled.r_foto_atr.mean()), 4)}
    (OUT / "phase4_stats.json").write_text(json.dumps(stats, indent=1, default=str))
    print(json.dumps({k: v for k, v in stats.items() if k not in ("corr_pairs_gt_095",)}, indent=1,
                     default=str)[:9000])
    print("coppie corr>0.95:", len(pairs), pairs[:30])


if __name__ == "__main__":
    main()
