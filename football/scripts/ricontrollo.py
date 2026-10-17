"""Ricontrollo con le formazioni ufficiali (~60 minuti prima), punto 14.13 del piano. DA COLLAUDARE con l'API vera.

Uso: python football/scripts/ricontrollo.py
Per ogni giocata pre-partita di oggi non ancora iniziata:
- formazioni ufficiali (fixtures/lineups) e titolari dell'ultima partita di ogni squadra -> turnover (titolari
  cambiati), modulo cambiato, portiere diverso;
- quote nuove -> probabilità e valore ricalcolati sulla quota attuale;
- esito: CONFERMATA / VALORE SCESO: SALTA / ATTENZIONE TURNOVER (>= 5 titolari cambiati o portiere di riserva).
Costo: circa 5 richieste per partita.
"""
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fb import apifootball as af  # noqa: E402
from fb import registro  # noqa: E402
from fb.picks import level, pinnacle_fair  # noqa: E402
from fb.predict import evaluate_quote, predict  # noqa: E402
from fb.teams import resolve  # noqa: E402

TURNOVER = 5


def lineup(fid):
    r = af.get("fixtures/lineups", max_age=1800, fixture=fid)["response"]
    out = {}
    for t in r:
        xi = [p["player"] for p in t.get("startXI", [])]
        out[t["team"]["id"]] = {"modulo": t.get("formation"), "ids": {p["id"] for p in xi},
                                "portiere": next((p["id"] for p in xi if p.get("pos") == "G"), None)}
    return out


def previous_lineup(team_id):
    last = af.get("fixtures", max_age=12 * 3600, team=team_id, last=1)["response"]
    if not last:
        return None
    return lineup(last[0]["fixture"]["id"]).get(team_id)


def main():
    day = str(date.today())
    r = registro.load()
    todo = r[(r.data == day) & (r.tipo == "pre-partita") & (r.esito == "")]
    fx = {str(f["id"]): f for f in af.fixtures(day)}
    tm = af.load_team_map()
    for fid in sorted(set(todo.fixture_id)):
        f = fx.get(fid)
        if f is None or f["stato"] not in ("NS", "TBD"):
            continue
        print(f"\n# {f['ora']} {f['home_api']} - {f['away_api']}")
        try:
            now = lineup(int(fid))
        except (af.BudgetError, RuntimeError) as e:
            print(f"impossibile leggere le formazioni: {e}")
            continue
        if not now:
            print("formazioni non ancora uscite: riprova più tardi")
            continue
        warn = []
        for side in ("home", "away"):
            tid = f[f"{side}_id"]
            cur, prev = now.get(tid), previous_lineup(tid)
            if not cur or not prev:
                continue
            changed = len(prev["ids"] - cur["ids"])
            name = f[f"{side}_api"]
            if changed >= TURNOVER:
                warn.append(f"{name}: {changed} titolari cambiati rispetto all'ultima partita (turnover)")
            if prev["portiere"] and cur["portiere"] and prev["portiere"] != cur["portiere"]:
                warn.append(f"{name}: portiere diverso dall'ultima partita")
            if prev["modulo"] and cur["modulo"] and prev["modulo"] != cur["modulo"]:
                warn.append(f"{name}: modulo cambiato {prev['modulo']} -> {cur['modulo']}")
        f["home"] = resolve(f["home_id"], f["home_api"], f["div"], tm)
        f["away"] = resolve(f["away_id"], f["away_api"], f["div"], tm)
        qs = af.quotes(af.get("odds", max_age=600, fixture=int(fid))["response"][0]["bookmakers"])
        pred = predict([dict(div=f["div"], date=day, home=f["home"], away=f["away"], arbitro=f["arbitro"],
                             mk=af.market_inputs(qs))])
        for _, g in todo[todo.fixture_id == fid].iterrows():
            q = next((x for x in qs if str(x["bet_id"]) == g.bet_id and x["value"] == g.valore_api), None)
            e = evaluate_quote(pred, 0, q) if q else None
            if e is None:
                verdict = "quota non più disponibile: SALTA"
            else:
                lvl, why = level(e, q, pinnacle_fair(qs, q), True)
                verdict = (f"CONFERMATA ({lvl}, quota {q['best']:.2f}, prob {e['p']:.0%}, valore {e['valore']:+.0%})"
                           if lvl in ("SUPER CECCHINO", "CECCHINO", "VALORE", "CONTROPRONOSTICO") else
                           f"VALORE SCESO: SALTA (quota {q['best']:.2f}, prob {e['p']:.0%}, valore {e['valore']:+.0%}, {why})")
            if warn and verdict.startswith("CONFERMATA"):
                verdict = "ATTENZIONE TURNOVER: " + verdict
            print(f"- {g.giocata}: {verdict}")
        for w in warn:
            print(f"  ! {w}")
    print(f"\nRichieste API usate oggi: {af.used_today()}")


if __name__ == "__main__":
    main()
