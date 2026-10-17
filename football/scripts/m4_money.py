"""Confronto con Pinnacle e backtest dei soldi (Fase M4) sui mercati con quote storiche: 1X2 e Over/Under 2.5.

Probabilità: quelle calibrate fuori campione di m4_gate (anni di verifica 2022-2026). Regole del punto 5 del piano,
fissate PRIMA di guardare i risultati: CECCHINO p>=0.70 e valore>=0.05; VALORE p>=0.55 e valore>=0.08;
quota >= 1.30; valore > 0.25 = sospetto (escluso); una sola giocata per partita (valore più alto). 1 unità a giocata.
Quote: massima di mercato (football-data 'Max'), Pinnacle pre-partita, Bet365.
Scrive output/m4_soldi.md.
"""
import json
import pickle
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fb.data import CACHE, ROOT, matches  # noqa: E402
from fb.gate import VER_YEARS, logloss  # noqa: E402

RULES = {"SUPER CECCHINO": (0.80, 0.05), "CECCHINO": (0.70, 0.05), "VALORE": (0.55, 0.08)}
MINQ, MAXV = 1.30, 0.25
BANDS = ((0.55, 0.70), (0.70, 0.75), (0.75, 0.80), (0.80, 1.01))
BOOKS = {"massima": (["MaxHome", "MaxDraw", "MaxAway"], ["MaxOver25", "MaxUnder25"]),
         "Pinnacle": (["PinH", "PinD", "PinA"], ["PinO25", "PinU25"]),
         "Bet365": (["OddHome", "OddDraw", "OddAway"], ["Over25", "Under25"])}


def load():
    d = pickle.load(open(CACHE / "m4" / "g.pkl", "rb"))
    sels = d["sels"]

    def col(**kw):
        return next(j for j, s in enumerate(sels) if all(s.get(k) == v for k, v in kw.items()))
    j = {"1": col(kind="1x2", o="H"), "X": col(kind="1x2", o="D"), "2": col(kind="1x2", o="A"),
         "O": col(kind="ou_tot", side="over", line=2.5), "U": col(kind="ou_tot", side="under", line=2.5)}
    v = np.isin(d["year"], VER_YEARS)
    P = pd.DataFrame({k: d["PC"][v, i] for k, i in j.items()}, index=d["index"][v])
    O = pd.DataFrame({k: d["O"][v, i] for k, i in j.items()}, index=d["index"][v])
    P[["1", "X", "2"]] = P[["1", "X", "2"]].div(P[["1", "X", "2"]].sum(axis=1), axis=0)
    P[["O", "U"]] = P[["O", "U"]].div(P[["O", "U"]].sum(axis=1), axis=0)
    P["year"] = d["year"][v]
    return P, O


def devig(o):
    inv = 1 / o.where(o > 1)
    return inv.div(inv.sum(axis=1), axis=0)


def backtest(P, O, odds):
    """odds: DataFrame colonne 1, X, 2, O, U. Restituisce le giocate fatte."""
    picks = []
    for k in ("1", "X", "2", "O", "U"):
        q = odds[k]
        v = P[k] * q - 1
        for lvl, (pmin, vmin) in RULES.items():
            ok = (P[k] >= pmin) & (v >= vmin) & (q >= MINQ) & (v <= MAXV)
            picks.append(pd.DataFrame({"mid": P.index[ok], "sel": k, "lvl": lvl, "p": P[k][ok], "q": q[ok],
                                       "v": v[ok], "win": O[k][ok], "year": P.year[ok]}))
    g = pd.concat(picks)
    g = g.sort_values("v", ascending=False).drop_duplicates("mid")       # una per partita
    g["pl"] = np.where(g.win > 0, g.q - 1, -1.0)
    return g


def main():
    P, O = load()
    m = matches().loc[P.index]
    rep = ["# Confronto con Pinnacle e backtest dei soldi (verifica 2022-2026, mai vista)", ""]
    roi = {}
    pin = devig(m[["PinH", "PinD", "PinA"]].apply(pd.to_numeric, errors="coerce"))
    ok = pin.notna().all(axis=1)
    y1 = O.loc[ok, ["1", "X", "2"]].to_numpy()
    ll_m = -np.mean(np.log(np.clip((P.loc[ok, ["1", "X", "2"]].to_numpy() * y1).sum(axis=1), 1e-6, 1)))
    ll_p = -np.mean(np.log(np.clip((pin[ok].to_numpy() * y1).sum(axis=1), 1e-6, 1)))
    pino = devig(m[["PinO25", "PinU25"]].apply(pd.to_numeric, errors="coerce"))
    ok2 = pino.notna().all(axis=1)
    ll_mo, ll_po = logloss(P.O[ok2].to_numpy(), O.O[ok2].to_numpy()), logloss(pino.iloc[:, 0][ok2].to_numpy(),
                                                                                O.O[ok2].to_numpy())
    rep += ["## Precisione contro Pinnacle (stesse partite)", "",
            "| mercato | partite | log-loss modello | log-loss Pinnacle |", "|---|---|---|---|",
            f"| 1X2 | {ok.sum()} | {ll_m:.4f} | {ll_p:.4f} |", f"| O/U 2.5 | {ok2.sum()} | {ll_mo:.4f} | {ll_po:.4f} |",
            "", "## Backtest a 1 unità (regole fisse del piano)", ""]
    for book, (c1, c2) in BOOKS.items():
        odds = pd.DataFrame({"1": m[c1[0]], "X": m[c1[1]], "2": m[c1[2]], "O": m[c2[0]], "U": m[c2[1]]})
        odds = odds.apply(pd.to_numeric, errors="coerce")
        g = backtest(P, O, odds)
        roi[book] = {"giocate": int(len(g)), "roi": float(g.pl.mean()) if len(g) else 0.0}
        rep += [f"### Quota {book}", "", "| gruppo | giocate | vinte | ROI | utile (u) | quota media |",
                "|---|---|---|---|---|---|"]
        for name, s in [("TOTALE", g)] + [(f"anno {y}", g[g.year == y]) for y in VER_YEARS] + \
                [(lv, g[g.lvl == lv]) for lv in RULES] + [(f"mercato {k}", g[g.sel == k]) for k in "1X2OU"] + \
                [(f"fascia {a:.0%}-{b:.0%}", g[(g.p >= a) & (g.p < b)]) for a, b in BANDS]:
            if len(s):
                rep.append(f"| {name} | {len(s)} | {s.win.mean():.1%} | {s.pl.mean():+.1%} | {s.pl.sum():+.1f} | "
                           f"{s.q.mean():.2f} |")
        rep.append("")
    (ROOT / "output" / "m4_soldi.md").write_text("\n".join(rep) + "\n")
    (ROOT / "models" / "m4_money.json").write_text(json.dumps(roi, indent=1))
    print("\n".join(rep))


if __name__ == "__main__":
    main()
