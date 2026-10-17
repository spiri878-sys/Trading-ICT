"""Giocate del giorno (Fase M5, punti 5-6 del piano).

Uso: python football/scripts/oggi.py [YYYY-MM-DD] [--solo-cache] [--max-quote N]
Partite dei campionati coperti -> quote di tutti i bookmaker (1 richiesta per partita) -> modelli -> filtri ->
TOP assoluta, TOP angoli, top per mercato, elenco CECCHINO e VALORE. Una giocata per partita, sempre singole.
Scrive football/output/giocate_<data>.md e aggiunge le giocate al registro.
"""
import sys
from datetime import date
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fb import apifootball as af  # noqa: E402
from fb import oddsapiio as oa  # noqa: E402
from fb import registro  # noqa: E402
from fb.data import ROOT  # noqa: E402
from fb.picks import (GROUP, MAIN_LEVELS, MIN_TEAM_N, confidence, describe, level, min_odds, pinnacle_fair,  # noqa: E402
                      reasons)
from fb.predict import evaluate_quote, predict  # noqa: E402
from fb.teams import resolve  # noqa: E402

RESERVE = 10                     # richieste lasciate per i risultati di domani
STAT_FIRST = {"E0", "E1", "E2", "E3", "SC0", "D1", "I1", "SP1", "F1", "N1", "P1", "T1", "B1", "G1", "D2", "I2",
              "SP2", "F2", "SC1", "SC2", "SC3", "EC"}          # campionati con angoli/falli/tiri nell'archivio


def gather_oddsapiio(day):
    """Fonte odds-api.io: partite del giorno dei campionati coperti e quote (10 partite per richiesta)."""
    tm = af.load_team_map()
    ok, skipped = [], []
    for e in oa.events(day):
        div = oa.league_div(e.get("league") or {})
        if div is None:
            continue
        h = resolve(f"oa:{e.get('homeId')}", e["home"], div, tm)
        a = resolve(f"oa:{e.get('awayId')}", e["away"], div, tm)
        f = {"id": f"oa{e['id']}", "eid": e["id"], "div": div, "date": day, "ora": e["date"][11:16],
             "kickoff": e["date"], "arbitro": "", "home_api": e["home"], "away_api": e["away"]}
        if h and a:
            ok.append(dict(f, home=h, away=a))
        else:
            skipped.append(f"{e['home']} - {e['away']} ({div}): nome squadra incerto")
    odds = oa.odds_multi([f["eid"] for f in ok])
    priced = []
    for f in ok:
        ev = odds.get(f["eid"])
        bms = oa.to_api_football(ev) if ev else []
        if not any(b["bets"] for b in bms):
            skipped.append(f"{f['home_api']} - {f['away_api']}: nessuna quota")
            continue
        f["quotes"] = af.quotes(bms)
        af.snapshot(f["id"], f["quotes"])
        f["mk"] = af.market_inputs(f["quotes"])
        f["nbooks"] = len(bms)
        priced.append(f)
    return priced, skipped


def gather(day, solo_cache, max_q):
    if oa.available() and not solo_cache:
        return gather_oddsapiio(day)
    fx = [f for f in af.fixtures(day) if f["stato"] in ("NS", "TBD")]
    tm = af.load_team_map()
    ok, skipped = [], []
    for f in fx:
        h = resolve(f["home_id"], f["home_api"], f["div"], tm)
        a = resolve(f["away_id"], f["away_api"], f["div"], tm)
        if h and a:
            ok.append(dict(f, home=h, away=a))
        else:
            skipped.append(f"{f['home_api']} - {f['away_api']} ({f['div']}): nome squadra incerto")
    ok.sort(key=lambda f: (f["div"] not in STAT_FIRST, f["kickoff"]))
    left = max_q if max_q is not None else af.BUDGET - af.used_today() - RESERVE
    priced = []
    for f in ok:
        cached = (af.API_CACHE / f"odds_fixture-{f['id']}.json").exists()
        if solo_cache and not cached:
            continue
        if not cached and left <= 0:
            skipped.append(f"{f['home_api']} - {f['away_api']}: richieste API finite per oggi")
            continue
        try:
            bms = af.odds(f["id"])
        except af.BudgetError:
            left = 0
            continue
        left -= 0 if cached else 1
        if not bms:
            skipped.append(f"{f['home_api']} - {f['away_api']}: nessuna quota")
            continue
        f["quotes"] = af.quotes(bms)
        if not cached:
            af.snapshot(f["id"], f["quotes"])            # andamento delle quote (punto 14.11)
        f["mk"] = af.market_inputs(f["quotes"])
        f["nbooks"] = len(bms)
        priced.append(f)
    return priced, skipped


def choose(priced, pred):
    best, scartate = [], 0
    for i, f in enumerate(priced):
        cands = []
        for q in f["quotes"]:
            e = evaluate_quote(pred, i, q)
            if e is None:
                continue
            nh, na = pred["counts"].get(e["stat"] if e["stat"] != "hh" else "ght", (np.zeros(len(priced)),) * 2)
            counts_ok = min(nh[i], na[i]) >= MIN_TEAM_N
            fair = pinnacle_fair(f["quotes"], q)
            lvl, why = level(e, q, fair, counts_ok)
            if lvl is None:
                scartate += 1
                continue
            cands.append(dict(e, q=q, lvl=lvl, why=why, fair=fair))
        for lv in (MAIN_LEVELS, ("CONTROPRONOSTICO",)):     # una sola per partita, il contropronostico a parte
            good = [c for c in cands if c["lvl"] in lv]
            if good:
                c = max(good, key=lambda c: c["valore"])
                best.append(dict(c, f=f, i=i))
        for c in cands:
            if c["lvl"] == "SOSPETTO":
                best.append(dict(c, f=f, i=i))
    return best, scartate


def line(c, pred):
    f, q, e = c["f"], c["q"], c
    x = pred["X"].iloc[c["i"]].to_dict()
    mu = pred["mu"].get(e["stat"], pred["mu"].get("ght", (np.array([np.nan]),) * 2))
    mu = (float(mu[0][c["i"]]), float(mu[1][c["i"]]))
    g = describe(e["stat"], e["sel"], f["home"], f["away"])
    mot = "; ".join(reasons(e["stat"], e["sel"], x, f["home"], f["away"], mu))
    fiducia = confidence(c["lvl"], e["famiglia"], f["nbooks"])
    pin = f" (Pinnacle {q['pin']:.2f})" if q.get("pin") else ""
    snap = af.first_snapshot(f["id"])
    mov = ""
    if snap and f"{q['bet_id']}|{q['value']}" in snap[1]:
        b0, p0 = snap[1][f"{q['bet_id']}|{q['value']}"]
        ref0, ref1 = (p0, q.get("pin")) if p0 and q.get("pin") else (b0, q["best"])
        if ref0 and ref1 and abs(ref1 / ref0 - 1) >= 0.02:
            mov = (f" Quota alle {snap[0][-4:-2]}:{snap[0][-2:]} UTC {b0:.2f} → ora {q['best']:.2f}: mercato "
                   f"{'A FAVORE' if ref1 < ref0 else 'CONTRO (attenzione)'}.")
    prov = "" if e["famiglia"] in ("g|1x2|H", "g|1x2|D", "g|1x2|A", "g|ou_tot|over", "g|ou_tot|under") \
        else " · profitto non ancora provato"
    return (f"**{f['ora']} {f['div']} {f['home_api']} - {f['away_api']}**: {g} → quota **{q['best']:.2f}** "
            f"({q['bm']}){pin}, probabilità {e['p']:.0%}, valore {e['valore']:+.0%}, quota minima {min_odds(e['p'], e['p_push']):.2f}. "
            f"Livello {c['lvl']}, fiducia {fiducia}{prov}.{mov} Valida pre-partita (in corso: usa live.py). Motivi: {mot}."), g


def main(argv):
    day = next((a for a in argv if a[:2] == "20"), str(date.today()))
    solo_cache = "--solo-cache" in argv
    max_q = int(argv[argv.index("--max-quote") + 1]) if "--max-quote" in argv else None
    out = [f"# Giocate del {day}", "", "Importi piccoli e fissi (1 unità), solo singole. "
           "Nessuna giocata è sicura.", ""]
    try:
        priced, skipped = gather(day, solo_cache, max_q)
    except Exception as e:  # noqa: BLE001
        out += [f"**ERRORE: non riesco a leggere partite/quote dall'API** ({e}). Nessuna giocata oggi: non sono "
                "in grado di darle complete."]
        print("\n".join(out))
        return
    if any("nome squadra incerto" in x for x in skipped):
        out += [f"Attenzione: {sum('nome squadra incerto' in x for x in skipped)} partite saltate per nome squadra "
                "non riconosciuto (elenco in fondo).", ""]
    if any("richieste API finite" in x for x in skipped):
        out += ["Attenzione: richieste API del giorno finite, alcune partite non sono state analizzate.", ""]
    picks = []
    if priced:
        pred = predict([dict(div=f["div"], date=day, home=f["home"], away=f["away"], arbitro=f["arbitro"],
                             mk=f["mk"]) for f in priced])
        picks, scartate = choose(priced, pred)
    good = sorted([c for c in picks if c["lvl"] in MAIN_LEVELS], key=lambda c: -c["valore"])
    contro = sorted([c for c in picks if c["lvl"] == "CONTROPRONOSTICO"], key=lambda c: -c["valore"])
    if not good:
        out.append("**Oggi nessuna giocata con valore.** Non forzare.")
    else:
        txt = {id(c): line(c, pred) for c in good}
        out += ["## 1. TOP ASSOLUTA", "", txt[id(good[0])][0], ""]
        ang = [c for c in good if c["stat"] == "cor"]
        out += ["## 2. TOP ANGOLI", "", txt[id(ang[0])][0] if ang else "Nessuna giocata angoli con valore oggi.", ""]
        out += ["## 3. Migliore per mercato", ""]
        for grp in ("GOL / 1X2", "CARTELLINI", "FALLI", "TIRI"):
            g = [c for c in good if GROUP[c["stat"]] == grp]
            out.append(f"- {grp}: " + (txt[id(g[0])][0] if g else "niente con valore"))
        for lvl in ("SUPER CECCHINO", "CECCHINO", "VALORE"):
            out += ["", f"## 4. {lvl}", ""]
            g = [c for c in good if c["lvl"] == lvl]
            out += [f"- {txt[id(c)][0]}" for c in g] or ["- nessuna"]
        registro.add([dict(data=day, ora=c["f"]["ora"], campionato=c["f"]["div"], fixture_id=c["f"]["id"],
                           partita=f"{c['f']['home_api']} - {c['f']['away_api']}", mercato=c["famiglia"],
                           giocata=txt[id(c)][1], tipo="pre-partita", livello=c["lvl"], quota=c["q"]["best"],
                           bookmaker=c["q"]["bm"], quota_pinnacle=c["q"].get("pin") or "",
                           prob_modello=round(c["p"], 3), valore=round(c["valore"], 3), bet_id=c["q"]["bet_id"],
                           valore_api=c["q"]["value"], esito="", utile="", quota_chiusura_pin="",
                           note=f"arch:{c['f']['home']}|{c['f']['away']}")
                      for c in good])
    if contro:
        ctxt = {id(c): line(c, pred) for c in contro}
        out += ["", "## 5. CONTROPRONOSTICI (sperimentale: vincono circa 1 volta su 3, quota alta; normali serie di "
                "perse)", ""]
        out += [f"- {ctxt[id(c)][0]}" for c in contro]
        registro.add([dict(data=day, ora=c["f"]["ora"], campionato=c["f"]["div"], fixture_id=c["f"]["id"],
                           partita=f"{c['f']['home_api']} - {c['f']['away_api']}", mercato=c["famiglia"],
                           giocata=ctxt[id(c)][1], tipo="pre-partita", livello=c["lvl"], quota=c["q"]["best"],
                           bookmaker=c["q"]["bm"], quota_pinnacle=c["q"].get("pin") or "",
                           prob_modello=round(c["p"], 3), valore=round(c["valore"], 3), bet_id=c["q"]["bet_id"],
                           valore_api=c["q"]["value"], esito="", utile="", quota_chiusura_pin="",
                           note=f"arch:{c['f']['home']}|{c['f']['away']}") for c in contro])
    sus = [c for c in picks if c["lvl"] == "SOSPETTO"]
    if sus:
        out += ["", "## Sospetti (NON giocare: troppo belli per essere veri)", ""]
        out += [f"- {c['f']['home_api']} - {c['f']['away_api']}: "
                f"{describe(c['stat'], c['sel'], c['f']['home'], c['f']['away'])} @{c['q']['best']:.2f}, "
                f"modello {c['p']:.0%}: {c['why']}" for c in sus[:15]]
    out += ["", f"Partite analizzate: {len(priced)}. Richieste usate oggi: API-Football {af.used_today()}, "
            f"odds-api.io {oa.used_today()}."]
    if skipped:
        out += ["", "Saltate: " + "; ".join(skipped[:30])]
    fn = ROOT / "output" / f"giocate_{day}.md"
    fn.write_text("\n".join(out) + "\n")
    print("\n".join(out))


if __name__ == "__main__":
    main(sys.argv[1:])
