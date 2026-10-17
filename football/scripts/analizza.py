"""Analisi di UNA partita su richiesta (punto 6 bis del piano).

Uso: python football/scripts/analizza.py "Inter"   oppure   "Roma-Genoa"   [YYYY-MM-DD]
Cerca la partita oggi e nei 3 giorni successivi. Prima del via: probabilità chiave, giocata migliore (o niente),
alternative, quota minima, motivi. In corso: modalità live sul tempo che resta. Finita: previsione contro risultato.
"""
import sys
from datetime import date, timedelta
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fb import apifootball as af  # noqa: E402
from fb.live import final_grid  # noqa: E402
from fb.markets import prob  # noqa: E402
from fb.picks import MINQ, describe, level, min_odds, pinnacle_fair, reasons  # noqa: E402
from fb.predict import evaluate_quote, predict  # noqa: E402
from fb.teams import norm, resolve, similar  # noqa: E402

LIVE = ("1H", "HT", "2H", "ET", "BT", "P", "LIVE")
FINAL = ("FT", "AET", "PEN")


def find(query, start):
    parts = [norm(p) for p in query.replace(" vs ", "-").split("-") if p.strip()]
    for d in range(4):
        day = str(start + timedelta(days=d))
        try:
            fx = af.fixtures(day)
        except (af.BudgetError, RuntimeError) as e:
            print(f"API non disponibile: {e}")
            return None
        scored = []
        for f in fx:
            h, a = norm(f["home_api"]), norm(f["away_api"])
            s = max(similar(p, h) for p in parts) + (max(similar(p, a) for p in parts) if len(parts) > 1 else 0)
            s = max(s, max(similar(p, a) for p in parts)) if len(parts) == 1 else s
            scored.append((s, f))
        scored.sort(key=lambda x: -x[0])
        if scored and scored[0][0] >= 0.75 * len(parts):
            return scored[0][1]
    return None


def key_probs(pred, f):
    g = pred["grid"]
    out = []
    if "g" in g:
        M = g["g"]
        p = [prob(M, {"kind": "1x2", "o": o})[0][0] for o in "HDA"]
        o25 = prob(M, {"kind": "ou_tot", "side": "over", "line": 2.5})[0][0]
        gg = prob(M, {"kind": "btts", "yes": True})[0][0]
        out.append(f"1X2: {p[0]:.0%} / {p[1]:.0%} / {p[2]:.0%} · Over 2.5 {o25:.0%} · Gol {gg:.0%}")
    for stat, name in (("cor", "angoli"), ("crd", "cartellini (giallo 1, rosso 2)"), ("fou", "falli"), ("sh", "tiri"),
                       ("sot", "tiri in porta")):
        if stat in pred["mu"]:
            mh, ma = pred["mu"][stat][0][0], pred["mu"][stat][1][0]
            out.append(f"{name}: attesi {f['home']} {mh:.1f}, {f['away']} {ma:.1f}, totale {mh + ma:.1f}")
    return out


def pre_match(f):
    bms = af.odds(f["id"])
    qs = af.quotes(bms) if bms else []
    pred = predict([dict(div=f["div"], date=f["date"], home=f["home"], away=f["away"], arbitro=f["arbitro"],
                         mk=af.market_inputs(qs) if qs else {})])
    print("\n".join(f"- {x}" for x in key_probs(pred, f)))
    if not qs:
        print("Nessuna quota disponibile: solo probabilità.")
        return
    cands = []
    for q in qs:
        e = evaluate_quote(pred, 0, q)
        if e is None or not e["ammesso"] or q["best"] < MINQ:
            continue
        lvl, why = level(e, q, pinnacle_fair(qs, q), True)
        cands.append(dict(e, q=q, lvl=lvl, why=why))
    good = sorted([c for c in cands if c["lvl"] in ("CECCHINO", "VALORE")], key=lambda c: -c["valore"])
    alt = sorted([c for c in cands if c["lvl"] is None and c["p"] >= 0.55], key=lambda c: -c["valore"])[:3]
    x = pred["X"].iloc[0].to_dict()

    def txt(c):
        mu = pred["mu"].get(c["stat"], pred["mu"]["g"])
        r = "; ".join(reasons(c["stat"], c["sel"], x, f["home"], f["away"], (mu[0][0], mu[1][0])))
        return (f"{describe(c['stat'], c['sel'], f['home'], f['away'])} @{c['q']['best']:.2f} ({c['q']['bm']}), "
                f"prob {c['p']:.0%}, valore {c['valore']:+.0%}, quota minima {min_odds(c['p']):.2f}. {r}")
    print("\nGIOCATA: " + (f"{good[0]['lvl']} — {txt(good[0])}" if good else "niente da giocare (nessun valore)"))
    if alt or good[1:]:
        print("Alternative (sotto soglia o seconde scelte):")
        for c in (good[1:3] + alt)[:3]:
            print(f"- {txt(c)}")


def live_mode(f):
    d = af.get("fixtures", max_age=60, id=f["id"])["response"][0]
    minute = d["fixture"]["status"]["elapsed"] or 0
    score = (d["goals"]["home"] or 0, d["goals"]["away"] or 0)
    st = {}
    for side, t in enumerate(d.get("statistics") or []):
        for s in t["statistics"]:
            st.setdefault(s["type"], [0, 0])[side] = float(str(s["value"] or 0).rstrip("%"))
    reds = tuple(int(v) for v in st.get("Red Cards", [0, 0]))
    print(f"IN CORSO: {minute}' {score[0]}-{score[1]} · angoli {st.get('Corner Kicks', ['?', '?'])} · "
          f"tiri {st.get('Total Shots', ['?', '?'])} · gialli {st.get('Yellow Cards', ['?', '?'])} · rossi {reds}")
    pred = predict([dict(div=f["div"], date=f["date"], home=f["home"], away=f["away"], arbitro=f["arbitro"], mk={})])
    conf = pred["conf"]["stats"]
    for stat, key, lines in (("g", None, (0.5, 1.5, 2.5, 3.5)), ("cor", "Corner Kicks", (7.5, 8.5, 9.5, 10.5, 11.5))):
        obs = score if stat == "g" else st.get(key)
        if obs is None or stat not in pred["mu"]:
            continue
        mh, ma = pred["mu"][stat][0][0], pred["mu"][stat][1][0]
        c = conf[stat]
        M, (rh, ra) = final_grid(mh, ma, minute, obs, stat, (c["phi_h"], c["phi_a"]), 24 if stat == "cor" else 10,
                                 score, reds)
        ps = [f"Over {ln:g}: {prob(M, {'kind': 'ou_tot', 'side': 'over', 'line': ln})[0][0]:.0%} "
              f"(quota minima {min_odds(prob(M, {'kind': 'ou_tot', 'side': 'over', 'line': ln})[0][0]):.2f})"
              for ln in lines if ln > sum(obs)]
        print(f"- {'gol' if stat == 'g' else 'angoli'}: nel resto attesi {rh:.1f} + {ra:.1f} · " + " · ".join(ps))
    print("Live NON verificato sul passato: usa importi minimi.")


def main(argv):
    q = argv[0]
    start = date.fromisoformat(argv[1]) if len(argv) > 1 else date.today()
    f = find(q, start)
    if f is None:
        print(f"Partita '{q}' non trovata nei prossimi 4 giorni nei campionati coperti.")
        return
    tm = af.load_team_map()
    f["home"] = resolve(f["home_id"], f["home_api"], f["div"], tm)
    f["away"] = resolve(f["away_id"], f["away_api"], f["div"], tm)
    print(f"# {f['home_api']} - {f['away_api']} ({f['div']}, {f['date']} {f['ora']} UTC, stato {f['stato']})")
    if not (f["home"] and f["away"]):
        print("Nome squadra incerto nell'archivio: analisi non affidabile, salto.")
        return
    if f["stato"] in LIVE:
        live_mode(f)
    elif f["stato"] in FINAL:
        pred = predict([dict(div=f["div"], date=f["date"], home=f["home"], away=f["away"], arbitro=f["arbitro"], mk={})])
        print("FINITA: " + f"{f['gol'][0]}-{f['gol'][1]}. Previsione: " + " | ".join(key_probs(pred, f)))
    else:
        pre_match(f)
    print(f"\nRichieste API usate oggi: {af.used_today()}. Importi piccoli e fissi: nessuna giocata è sicura.")



if __name__ == "__main__":
    main(sys.argv[1:])
