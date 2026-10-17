"""F7 — angoli per squadra (casa / ospite) e totali: quanto sono affidabili le probabilità e quante volte escono.

Usa le previsioni walk-forward di F6 (addestrate solo sul passato): casa = nuove_tuning_h, ospite = nuove_tuning_a,
totale = media_mix. Dispersione (binomiale negativa) stimata sul 2010-2012, verifica 2013-2026.

Per ogni linea: frequenza reale, probabilità media del modello, log-loss contro la frequenza del campionato,
calibrazione per fasce di probabilità (quando il modello dice 70%, esce davvero il 70%?) e la modalità "cecchino":
quante volte esce la giocata quando il modello è molto sicuro (probabilità >= 70%, 75%, 80%).

usage: python football/scripts/f7_team_corners.py
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import nbinom

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fb.data import CACHE, ROOT, matches  # noqa: E402

LINES = {"totale": [7.5, 8.5, 9.5, 10.5, 11.5, 12.5], "casa": [2.5, 3.5, 4.5, 5.5, 6.5],
         "ospite": [1.5, 2.5, 3.5, 4.5, 5.5]}


def fit_k(mu, y):
    r = ((y - mu) ** 2 - mu).sum()
    return float(np.clip((mu ** 2).sum() / max(r, 1e-6), 2.0, 1e4))


def p_over(mu, k, line):
    return 1 - nbinom.cdf(np.floor(line), k, k / (k + mu))


def ll(p, y):
    p = np.clip(p, 1e-6, 1 - 1e-6)
    return float(-(y * np.log(p) + (1 - y) * np.log(1 - p)).mean())


def main():
    m = matches()
    P = pd.read_parquet(CACHE / "f6_preds.parquet")
    series = {"totale": (P.media_mix, m.HomeCorners + m.AwayCorners),
              "casa": (P.nuove_tuning_h, m.HomeCorners), "ospite": (P.nuove_tuning_a, m.AwayCorners)}
    rep, ks = {}, {}
    for name, (mu, y) in series.items():
        ok = mu.notna() & y.notna()
        cal, ev = ok & m.season.between(2010, 2012), ok & (m.season >= 2013)
        k = fit_k(mu[cal].values, y[cal].values)
        ks[name] = round(k, 1)
        e, t, div = mu[ev].values, y[ev].values, m.Division[ev].values
        out = {"n": int(ev.sum()), "k": round(k, 1), "media_prevista": round(float(e.mean()), 2),
               "media_reale": round(float(t.mean()), 2), "corr": round(float(np.corrcoef(e, t)[0, 1]), 3)}
        for line in LINES[name]:
            po = p_over(e, k, line)
            yo = (t > line).astype(float)
            # frequenza del campionato, solo passato
            hist = pd.Series(y[ok & (m.season < 2013)].values, index=m.Division[ok & (m.season < 2013)].values)
            fr = hist.groupby(level=0).apply(lambda s: (s > line).mean())
            base = pd.Series(div).map(fr).fillna(float((hist > line).mean())).values
            r = {"esce_%": round(100 * yo.mean(), 1), "prob_media_modello_%": round(100 * po.mean(), 1),
                 "ll_modello": round(ll(po, yo), 4), "ll_campionato": round(ll(base, yo), 4)}
            # calibrazione per fasce
            bins = np.clip((po * 10).astype(int), 0, 9)
            r["calibrazione"] = {f"{10 * b}-{10 * b + 10}%": [int((bins == b).sum()), round(100 * yo[bins == b].mean(), 1)]
                                 for b in range(10) if (bins == b).sum() >= 200}
            # cecchino: solo quando il modello è molto sicuro (Over o Under)
            cc = {}
            for th in (0.65, 0.70, 0.75, 0.80):
                so, su = po >= th, (1 - po) >= th
                cc[f">={int(100 * th)}%"] = {
                    "over": [int(so.sum()), round(100 * yo[so].mean(), 1) if so.sum() else None,
                             round(100 * so.mean(), 1)],
                    "under": [int(su.sum()), round(100 * (1 - yo[su]).mean(), 1) if su.sum() else None,
                              round(100 * su.mean(), 1)]}
            r["cecchino_[partite, esce_%, quota_partite_%]"] = cc
            out[f"over_{line}"] = r
        rep[name] = out
    rep["k"] = ks
    # correzione di scala (il modello sovrastima di poco: media reale / prevista sul 2013-2026)
    rep["scala"] = {n: round(rep[n]["media_reale"] / rep[n]["media_prevista"], 4) for n in LINES}
    meta_p = ROOT / "models" / "meta.json"
    if meta_p.exists() and "cor6" in (meta := json.loads(meta_p.read_text())):
        meta["cor6"].update(k_casa=ks["casa"], k_ospite=ks["ospite"], k=ks["totale"], scala=rep["scala"])
        meta_p.write_text(json.dumps(meta, indent=1))
    (ROOT / "output" / "f7_team_corners_eval.json").write_text(json.dumps(rep, indent=1))
    for name in LINES:
        print(f"== {name}: corr {rep[name]['corr']} media {rep[name]['media_prevista']}/{rep[name]['media_reale']} k {ks[name]}")
        for line in LINES[name]:
            r = rep[name][f"over_{line}"]
            c = r["cecchino_[partite, esce_%, quota_partite_%]"][">=70%"]
            print(f"  O{line}: esce {r['esce_%']}% modello {r['prob_media_modello_%']}% ll {r['ll_modello']} vs "
                  f"{r['ll_campionato']} | >=70% over {c['over']} under {c['under']}")


if __name__ == "__main__":
    main()
