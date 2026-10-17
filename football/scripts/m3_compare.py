"""Prova di feature aggiuntive (punto 14.12: calendario e contesto). Entrano solo se migliorano la verifica.

Feature (solo passato): scarto dell'ultima partita di ogni squadra, giorno della settimana, ora del calcio d'inizio,
rientro da pausa lunga a stagione in corso (>= 12 giorni, es. nazionali).
Confronto: devianza LightGBM fuori campione 2022-2026 con e senza, stesse impostazioni del walk-forward.
Uso: python football/scripts/m3_compare.py [stat ...]   -> output/m3_compare.md
"""
import pickle
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fb.data import CACHE, ROOT, matches  # noqa: E402
from fb.models import TARGETS, add_targets, fit_lgb, poisson_dev  # noqa: E402

YEARS = range(2022, 2027)


def calendar_feats(m, X):
    F = pd.DataFrame(index=m.index)
    rows = []
    for side, team, gf, ga in (("h", m.HomeTeam, m.hg, m.ag), ("a", m.AwayTeam, m.ag, m.hg)):
        rows.append(pd.DataFrame({"i": m.index, "date": m.date, "team": team, "country": m.country, "side": side,
                                  "gd": gf - ga}))
    L = pd.concat(rows).sort_values(["date", "i"])
    L["last_gd"] = L.groupby(["country", "team"]).gd.shift(1)
    for side in ("h", "a"):
        s = L[L.side == side].set_index("i").last_gd
        F[f"{side}_last_gd"] = s.reindex(m.index).to_numpy()
        F[f"{side}_after_break"] = ((X[f"{side}_rest"] >= 12) & (X.ssn_prog > 0.05) & (X.ssn_prog < 0.95)).astype(float)
    F["weekday"] = m.date.dt.weekday.to_numpy()
    hr = pd.to_numeric(m.MatchTime.astype(str).str[:2], errors="coerce") if "MatchTime" in m else np.nan
    F["hour"] = hr
    return F.astype(np.float32)


def main(stats):
    m = add_targets(matches())
    X = pickle.load(open(CACHE / "m2_features.pkl", "rb"))
    X2 = pd.concat([X, calendar_feats(m, X)], axis=1)
    rep = ["# Prova feature calendario/contesto (14.12): devianza fuori campione 2022-2026 (più bassa = meglio)", "",
           "| statistica | anno | senza | con | differenza |", "|---|---|---|---|---|"]
    for stat in stats:
        h, a = TARGETS[stat]
        has = m[h].notna() & m[a].notna()
        tot = {"senza": 0.0, "con": 0.0}
        for y in YEARS:
            start, end = pd.Timestamp(f"{y}-07-01"), pd.Timestamp(f"{y + 1}-07-01")
            tr = np.flatnonzero((has & (m.date >= "2008-07-01") & (m.date < start)).to_numpy())
            te = (has & (m.date >= start) & (m.date < end)).to_numpy()
            cut = int(len(tr) * 0.85)
            res = {}
            for name, XX in (("senza", X), ("con", X2)):
                d = 0.0
                for col in (h, a):
                    b, it = fit_lgb(XX.iloc[tr[:cut]], m[col].iloc[tr[:cut]], XX.iloc[tr[cut:]], m[col].iloc[tr[cut:]])
                    d += poisson_dev(m[col][te].to_numpy(float), b.predict(XX[te], num_iteration=it))
                res[name] = d
                tot[name] += d * te.sum()
            rep.append(f"| {stat} | {y} | {res['senza']:.4f} | {res['con']:.4f} | {res['con'] - res['senza']:+.4f} |")
            print(rep[-1], flush=True)

        rep.append(f"| **{stat} totale** | | | | {(tot['con'] - tot['senza']) / max(tot['senza'], 1e-9):+.2%} |")
    (ROOT / "output" / "m3_compare.md").write_text("\n".join(rep) + "\n")
    print("\n".join(rep[-1:]))



if __name__ == "__main__":
    main(sys.argv[1:] or ["g", "cor"])
