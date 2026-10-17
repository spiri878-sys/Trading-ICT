"""Listino pre-partita delle quote minime sugli angoli: per ogni partita e ogni mercato angoli (totale, casa, ospite,
Over/Under) la quota sotto la quale NON conviene giocare (quota giusta + 5% di margine). L'utente confronta da solo con
il suo bookmaker: se la quota offerta è uguale o più alta della minima, la giocata ha valore secondo il modello.
In lista solo i mercati con probabilità >= 55%; quelli >= 70% sono marcati CECCHINO.

usage: python football/scripts/listino.py 2026-10-18 "I1:Roma:Genoa" "E0:Arsenal:Chelsea" ...
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fb.card import markets, predict_fixtures  # noqa: E402
from fb.data import ROOT  # noqa: E402

MARGINE = 0.05


def main():
    date, specs = sys.argv[1], sys.argv[2:]
    fx = []
    for s in specs:
        div, h, a = s.split(":")
        fx.append(dict(home=h, away=a, div=div, date=date))
    L = [f"# Listino angoli del {date}", "",
         "Gioca solo se la quota del tuo bookmaker è **uguale o più alta** della quota minima. Una giocata per partita.", ""]
    for r in predict_fixtures(fx):
        P, _ = markets(r)
        c = r["cor_attesi"]
        h, a = r["match"]["HomeTeam"], r["match"]["AwayTeam"]
        L += [f"## {h} - {a} ({r['match']['Division']})",
              f"Angoli attesi: {h} {c['casa']:.1f} · {a} {c['ospite']:.1f} · totale {c.get('totale', c['casa'] + c['ospite']):.1f}", "",
              "| Giocata | Probabilità | Quota minima | |", "|---|---|---|---|"]
        rows = sorted(((p, k) for k, p in P.items() if k.startswith("Angoli") and p >= 0.55), reverse=True)
        for p, k in rows:
            nome = k.replace("Angoli Casa", f"Angoli {h}").replace("Angoli Ospite", f"Angoli {a}")
            L.append(f"| {nome} | {100 * p:.0f}% | **{(1 + MARGINE) / p:.2f}** | {'CECCHINO' if p >= 0.70 else ''} |")
        L.append("")
    out = ROOT / "output" / f"listino_{date}.md"
    out.write_text("\n".join(L))
    print("\n".join(L))


if __name__ == "__main__":
    main()
