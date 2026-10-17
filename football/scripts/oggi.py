"""Lista giocate del giorno, pre-partita, in automatico: partite e quote da API-Football, probabilità dal modello.

Per ogni partita dei campionati coperti: quota migliore tra i bookmaker per 1X2 e angoli (totali, casa, ospite),
probabilità del modello, valore = p x quota - 1. In lista solo:
  CECCHINO  probabilità >= 70% e valore >= 5%
  VALORE    probabilità >= 55% e valore >= 8%
Una sola giocata per partita (la migliore), per non sommare scommesse legate tra loro.
Salva football/output/giocate_<data>.md e .csv.

usage: python football/scripts/oggi.py [YYYY-MM-DD]      (richiede la variabile d'ambiente API_FOOTBALL_KEY)
"""
import datetime as dt
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fb.apifootball import best_odds, fixtures, match_team, odds_by_date  # noqa: E402
from fb.card import markets, predict_fixtures  # noqa: E402
from fb.data import ROOT, matches  # noqa: E402

CECCHINO = (0.70, 0.05)
VALORE = (0.55, 0.08)


def main():
    date = sys.argv[1] if len(sys.argv) > 1 else dt.date.today().isoformat()
    m = matches()
    fx = [f for f in fixtures(date) if f["stato"] in ("NS", "TBD")]
    odds = odds_by_date(date)
    rows, todo, skipped = [], [], []
    for f in fx:
        names = set(m.HomeTeam[m.Division == f["div"]]) | set(m.AwayTeam[m.Division == f["div"]])
        h, a = match_team(f["home_api"], names), match_team(f["away_api"], names)
        bo = best_odds(odds.get(f["id"], []))
        if not h or not a or not any(k.startswith("Angoli") for k in bo):
            skipped.append(f"{f['home_api']} - {f['away_api']} ({f['div']}): "
                           f"{'squadra non trovata' if not (h and a) else 'nessuna quota angoli'}")
            continue
        o = {k: bo[k][0] for k in ("1", "X", "2") if k in bo}
        todo.append((f, h, a, bo, dict(home=h, away=a, div=f["div"], date=date, odds=o)))
    res = predict_fixtures([t[4] for t in todo]) if todo else []
    for (f, h, a, bo, _), r in zip(todo, res):
        P, _ = markets(r)
        cand = []
        for k, (q, bm) in bo.items():
            if k.startswith("Angoli") and k in P:
                p = P[k]
                cand.append(dict(data=date, ora=f["ora"], campionato=f["div"], partita=f"{h} - {a}", giocata=k,
                                 quota=q, bookmaker=bm, prob=round(p, 3), valore=round(p * q - 1, 3),
                                 angoli_attesi=f"{r['cor_attesi']['casa']:.1f}-{r['cor_attesi']['ospite']:.1f}"))
        for c in cand:
            c["livello"] = ("CECCHINO" if c["prob"] >= CECCHINO[0] and c["valore"] >= CECCHINO[1] else
                            "VALORE" if c["prob"] >= VALORE[0] and c["valore"] >= VALORE[1] else "")
        good = sorted((c for c in cand if c["livello"]), key=lambda c: (c["livello"] != "CECCHINO", -c["valore"]))
        if good:
            rows.append(good[0])
    out = ROOT / "output"
    df = pd.DataFrame(rows)
    df.to_csv(out / f"giocate_{date}.csv", index=False)
    L = [f"# Giocate angoli del {date}", "",
         f"Partite analizzate: {len(todo)} su {len(fx)} in programma · giocate proposte: {len(rows)}", "",
         "| Ora | Camp. | Partita | Giocata | Quota | Bookmaker | Prob. | Valore | Livello |",
         "|---|---|---|---|---|---|---|---|---|"]
    for c in rows:
        L.append(f"| {c['ora']} | {c['campionato']} | {c['partita']} | {c['giocata']} | {c['quota']} | {c['bookmaker']} | "
                 f"{100 * c['prob']:.0f}% | {100 * c['valore']:+.0f}% | {c['livello']} |")
    if skipped:
        L += ["", "Non analizzate: " + "; ".join(skipped)]
    last = m.date.max().date()
    L += ["", f"Archivio dati fino al {last}. Una giocata per partita, singole (non multiple). Importo fisso e piccolo."]
    (out / f"giocate_{date}.md").write_text("\n".join(L))
    print("\n".join(L))


if __name__ == "__main__":
    main()
