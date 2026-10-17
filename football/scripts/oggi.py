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
from fb import registro  # noqa: E402
from fb.data import ROOT  # noqa: E402
from fb.picks import (GROUP, MIN_TEAM_N, confidence, describe, level, min_odds, pinnacle_fair,  # noqa: E402
                      reasons)
from fb.predict import evaluate_quote, predict  # noqa: E402
from fb.teams import resolve  # noqa: E402

RESERVE = 10                     # richieste lasciate per i risultati di domani
MAX_DAY, STOP_LOSS, STOP_DAYS = 5, -10.0, 7   # limiti di sicurezza (punto 14.3)
STAT_FIRST = {"E0", "E1", "E2", "E3", "SC0", "D1", "I1", "SP1", "F1", "N1", "P1", "T1", "B1", "G1", "D2", "I2",
              "SP2", "F2", "SC1", "SC2", "SC3", "EC"}          # campionati con angoli/falli/tiri nell'archivio


def gather(day, solo_cache, max_q):
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
        good = [c for c in cands if c["lvl"] != "SOSPETTO"]
        if good:
            c = max(good, key=lambda c: c["valore"])                     # una sola giocata per partita
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
    prov = "" if e["famiglia"] in ("g|1x2|H", "g|1x2|D", "g|1x2|A", "g|ou_tot|over", "g|ou_tot|under") \
        else " · profitto non ancora provato"
    return (f"**{f['ora']} {f['div']} {f['home_api']} - {f['away_api']}**: {g} → quota **{q['best']:.2f}** "
            f"({q['bm']}){pin}, probabilità {e['p']:.0%}, valore {e['valore']:+.0%}, quota minima {min_odds(e['p']):.2f}. "
            f"Livello {c['lvl']}, fiducia {fiducia}{prov}. Valida pre-partita (in corso: usa live.py). Motivi: {mot}."), g


def recent_loss(day):
    r = registro.load()
    r = r[r.utile != ""]
    d = (np.datetime64(day) - r.data.astype("datetime64[D]")).astype(int)
    return float(r.utile[(d >= 0) & (d < STOP_DAYS)].astype(float).sum())


def main(argv):
    day = next((a for a in argv if a[:2] == "20"), str(date.today()))
    solo_cache = "--solo-cache" in argv
    max_q = int(argv[argv.index("--max-quote") + 1]) if "--max-quote" in argv else None
    out = [f"# Giocate del {day}", "", "Importi piccoli e fissi (1 unità), solo singole, mai raddoppiare per recuperare. "
           "Nessuna giocata è sicura.", ""]
    loss = recent_loss(day)
    if loss <= STOP_LOSS:
        out += [f"**PAUSA**: ultimi {STOP_DAYS} giorni {loss:+.1f} unità (limite {STOP_LOSS:+.0f}). "
                "Oggi nessuna giocata: si riparte quando il bilancio della settimana risale."]
        print("\n".join(out))
        (ROOT / "output" / f"giocate_{day}.md").write_text("\n".join(out) + "\n")
        return
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
    good = sorted([c for c in picks if c["lvl"] != "SOSPETTO"], key=lambda c: -c["valore"])
    if len(good) > MAX_DAY:                       # al massimo 5: prima i CECCHINO, poi per valore
        keep = sorted(good, key=lambda c: (c["lvl"] != "CECCHINO", -c["valore"]))[:MAX_DAY]
        good = [c for c in good if any(c is k for k in keep)]
        out += [f"(Limite di sicurezza: mostrate le migliori {MAX_DAY} giocate.)", ""]
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
        for lvl in ("CECCHINO", "VALORE"):
            out += ["", f"## 4. {lvl}", ""]
            g = [c for c in good if c["lvl"] == lvl]
            out += [f"- {txt[id(c)][0]}" for c in g] or ["- nessuna"]
        registro.add([dict(data=day, ora=c["f"]["ora"], campionato=c["f"]["div"], fixture_id=c["f"]["id"],
                           partita=f"{c['f']['home_api']} - {c['f']['away_api']}", mercato=c["famiglia"],
                           giocata=txt[id(c)][1], tipo="pre-partita", livello=c["lvl"], quota=c["q"]["best"],
                           bookmaker=c["q"]["bm"], quota_pinnacle=c["q"].get("pin") or "",
                           prob_modello=round(c["p"], 3), valore=round(c["valore"], 3), bet_id=c["q"]["bet_id"],
                           valore_api=c["q"]["value"], esito="", utile="", quota_chiusura_pin="", note="")
                      for c in good])
    sus = [c for c in picks if c["lvl"] == "SOSPETTO"]
    if sus:
        out += ["", "## Sospetti (NON giocare: troppo belli per essere veri)", ""]
        out += [f"- {c['f']['home_api']} - {c['f']['away_api']}: "
                f"{describe(c['stat'], c['sel'], c['f']['home'], c['f']['away'])} @{c['q']['best']:.2f}, "
                f"modello {c['p']:.0%}: {c['why']}" for c in sus[:15]]
    out += ["", f"Partite analizzate: {len(priced)}. Richieste API usate oggi: {af.used_today()}."]
    if skipped:
        out += ["", "Saltate: " + "; ".join(skipped[:30])]
    fn = ROOT / "output" / f"giocate_{day}.md"
    fn.write_text("\n".join(out) + "\n")
    print("\n".join(out))


if __name__ == "__main__":
    main(sys.argv[1:])
