"""Esiti delle giocate nel registro e bilancio reale (Fase M6, punto 8 del piano).

Uso: python football/scripts/esiti.py [--no-clv]
Per ogni giocata pre-partita aperta di una partita finita: risultato e statistiche (fixtures?id=, 1 richiesta), quota
Pinnacle di chiusura (odds?fixture=, 1 richiesta; se l'API la conserva). Esito con la stessa maschera della
probabilità: vinta, persa, rimborso o mezza (linee a quarti). CLV = quota presa / quota di chiusura Pinnacle - 1.
Scrive football/output/bilancio.md.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fb import apifootball as af  # noqa: E402
from fb import espn, registro  # noqa: E402
from fb.data import ROOT, matches  # noqa: E402
from fb.dist import KMAX  # noqa: E402
from fb.markets import API_BETS, masks, masks_hh, parse  # noqa: E402
from fb.predict import norm_sel  # noqa: E402

FINAL = ("FT", "AET", "PEN")


def counts(fx):
    """Conteggi finali (casa, ospite) per statistica dal dettaglio partita."""
    g, ht = fx["goals"], fx["score"]["halftime"]
    c = {"g": (g["home"], g["away"]), "ght": (ht["home"], ht["away"]),
         "g2h": (g["home"] - ht["home"], g["away"] - ht["away"])}
    keys = {"Corner Kicks": "cor", "Fouls": "fou", "Total Shots": "sh", "Shots on Goal": "sot",
            "Yellow Cards": "yel", "Red Cards": "red"}
    st = {}
    for side, t in zip((0, 1), fx.get("statistics") or []):
        for s in t["statistics"]:
            if s["type"] in keys:
                st.setdefault(keys[s["type"]], [0, 0])[side] = float(s["value"] or 0)
    c.update({k: tuple(v) for k, v in st.items()})
    if "yel" in c:
        r = c.get("red", (0, 0))
        c["crd"] = (c["yel"][0] + 2 * r[0], c["yel"][1] + 2 * r[1])
    return c


def counts_archive(day, home, away):
    """Conteggi dall'archivio football-data (dopo f0_update): per le giocate prese da odds-api.io."""
    m = matches()
    r = m[(m.MatchDate == day) & (m.HomeTeam == home) & (m.AwayTeam == away)]
    if r.empty:
        return None
    r = r.iloc[0]
    c = {"g": (r.hg, r.ag)}
    pairs = {"ght": ("HTHome", "HTAway"), "cor": ("HomeCorners", "AwayCorners"), "fou": ("HomeFouls", "AwayFouls"),
             "sh": ("HomeShots", "AwayShots"), "sot": ("HomeTarget", "AwayTarget"), "yel": ("HomeYellow", "AwayYellow"),
             "red": ("HomeRed", "AwayRed")}
    for k, (h, a) in pairs.items():
        if r[h] == r[h] and r[a] == r[a]:
            c[k] = (r[h], r[a])
    if "ght" in c:
        c["g2h"] = (r.hg - c["ght"][0], r.ag - c["ght"][1])
    if "yel" in c and "red" in c:
        c["crd"] = (c["yel"][0] + 2 * c["red"][0], c["yel"][1] + 2 * c["red"][1])
    return c


def outcome(bet_id, value, c):
    stat, kind = API_BETS[int(bet_id)]
    sel = parse(kind, value)
    if sel is None:
        return None
    sel = norm_sel(kind, sel)
    if stat == "hh":
        W, P = masks_hh(sel, 9)
        x1, y1 = [int(v) for v in c["ght"]]
        x2, y2 = [int(v) for v in c["g2h"]]
        return W[x1, y1, x2, y2], P[x1, y1, x2, y2]
    if stat not in c:
        return None
    K = KMAX[stat] + 20
    x, y = [min(int(v), K) for v in c[stat]]
    W, P = masks(sel, K)
    return W[x, y], P[x, y]


def closing_pin(fid, bet_id, value):
    for b in af.odds(fid):
        if b["name"] == "Pinnacle":
            for bet in b["bets"]:
                if bet["id"] == int(bet_id):
                    for v in bet["values"]:
                        if str(v["value"]) == value:
                            return float(v["odd"])
    return None


def main(argv):
    r = registro.load()
    open_ = r[(r.esito == "") & (r.fixture_id != "") & (r.tipo == "pre-partita")]
    done = 0
    for i in list(open_.index):                       # 1) ESPN, gratis e senza chiave: vale per ogni giocata
        div, home_away = r.at[i, "campionato"], r.at[i, "partita"].split(" - ")
        if div not in espn.LEAGUES or len(home_away) != 2:
            continue
        try:
            ev = espn.find(div, r.at[i, "data"], *home_away)
            c = espn.counts(div, ev["id"]) if ev else None
        except Exception as e:  # noqa: BLE001
            print(f"ESPN non disponibile: {e}")
            break
        if not c or c["_stato"] not in ("STATUS_FULL_TIME", "STATUS_FINAL", "STATUS_FULL_PEN", "STATUS_AET"):
            continue
        o = outcome(r.at[i, "bet_id"], r.at[i, "valore_api"], c)
        if o is None:
            continue
        w, p = float(o[0]), float(o[1])
        q = float(r.at[i, "quota"])
        r.at[i, "esito"] = "VINTA" if w == 1 else "RIMBORSO" if p == 1 else "PERSA" if w == 0 and p == 0 else "MEZZA"
        r.at[i, "utile"] = f"{w * q + p - 1:+.2f}"
        r.at[i, "note"] = (r.at[i, "note"] + " | esito ESPN").strip(" |")
        done += 1
    open_ = open_[r.loc[open_.index, "esito"] == ""]
    for i in open_.index[open_.fixture_id.str.startswith("oa")]:       # giocate odds-api.io: esito dall'archivio
        note = r.at[i, "note"]
        if not note.startswith("arch:"):
            continue
        home, away = note[5:].split("|")[:2]
        c = counts_archive(r.at[i, "data"], home, away)
        o = outcome(r.at[i, "bet_id"], r.at[i, "valore_api"], c) if c else None
        if o is None:
            continue
        w, p = float(o[0]), float(o[1])
        q = float(r.at[i, "quota"])
        r.at[i, "esito"] = "VINTA" if w == 1 else "RIMBORSO" if p == 1 else "PERSA" if w == 0 and p == 0 else "MEZZA"
        r.at[i, "utile"] = f"{w * q + p - 1:+.2f}"
        done += 1
    open_ = open_[~open_.fixture_id.str.startswith("oa")]
    for fid in sorted(set(open_.fixture_id)):
        try:
            res = af.get("fixtures", max_age=6 * 3600, id=int(fid))["response"]
        except (af.BudgetError, RuntimeError) as e:
            print(f"stop: {e}")
            break
        if not res or res[0]["fixture"]["status"]["short"] not in FINAL:
            continue
        c = counts(res[0])
        for i in open_.index[open_.fixture_id == fid]:
            o = outcome(r.at[i, "bet_id"], r.at[i, "valore_api"], c)
            if o is None:
                r.at[i, "note"] = (r.at[i, "note"] + " statistica non disponibile").strip()
                continue
            w, p = float(o[0]), float(o[1])
            q = float(r.at[i, "quota"])
            r.at[i, "esito"] = "VINTA" if w == 1 else "RIMBORSO" if p == 1 else "PERSA" if w == 0 and p == 0 else "MEZZA"
            r.at[i, "utile"] = f"{w * q + p - 1:+.2f}"
            if "--no-clv" not in argv:
                try:
                    cp = closing_pin(int(fid), r.at[i, "bet_id"], r.at[i, "valore_api"])
                    r.at[i, "quota_chiusura_pin"] = f"{cp:.2f}" if cp else ""
                except (af.BudgetError, RuntimeError):
                    pass
            done += 1
    registro.save(r)
    s = r[r.esito.isin(["VINTA", "PERSA", "RIMBORSO", "MEZZA"])]
    clv = s[s.quota_chiusura_pin != ""]
    txt = ["# Bilancio reale (1 unità a giocata)", "", registro.summary(r)]
    if len(clv):
        v = clv.quota.astype(float) / clv.quota_chiusura_pin.astype(float) - 1
        txt += ["", f"CLV medio contro la chiusura Pinnacle: {v.mean():+.1%} su {len(clv)} giocate "
                    f"(positivo con costanza = vantaggio vero anche quando i risultati girano male)."]
    (ROOT / "output" / "bilancio.md").write_text("\n".join(txt) + "\n")
    print(f"Esiti aggiornati: {done}")
    print("\n".join(txt))


if __name__ == "__main__":
    main(sys.argv[1:])
