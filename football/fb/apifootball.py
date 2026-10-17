"""Client API-Football (v3) con cache e contatore delle richieste (piano gratuito: 100 al giorno).

La chiave la inserisce il proxy (segreto di rete dell'ambiente) oppure la variabile API_FOOTBALL_KEY: mai nel codice.
Risposte in data/cache/api/ (valide 3 ore per quote e partite di oggi, per sempre per le partite finite).
"""
import json
import os
import time
import urllib.parse
import urllib.request
from datetime import date as _date
from statistics import median

from .data import CACHE, ROOT

BASE = "https://v3.football.api-sports.io"
API_CACHE = CACHE / "api"
BUDGET = 95                                   # tetto giornaliero (lascia margine sul limite di 100)
TEAM_MAP = ROOT / "data" / "team_map.json"

LEAGUES = {"E0": 39, "E1": 40, "E2": 41, "E3": 42, "EC": 43, "SC0": 179, "SC1": 180, "SC2": 183, "SC3": 184,
           "D1": 78, "D2": 79, "I1": 135, "I2": 136, "SP1": 140, "SP2": 141, "F1": 61, "F2": 62, "N1": 88,
           "B1": 144, "P1": 94, "T1": 203, "G1": 197, "ARG": 128, "AUT": 218, "BRA": 71, "CHN": 169, "DEN": 119,
           "FIN": 244, "IRL": 357, "JAP": 98, "MEX": 262, "NOR": 103, "POL": 106, "ROM": 283, "RUS": 235,
           "SUI": 207, "SWE": 113, "USA": 253}
DIV_OF = {v: k for k, v in LEAGUES.items()}


class BudgetError(RuntimeError):
    pass


def _counter():
    fn = API_CACHE / "contatore.json"
    c = json.loads(fn.read_text()) if fn.exists() else {}
    return fn, c


def used_today():
    return _counter()[1].get(str(_date.today()), 0)


def get(path, max_age=3 * 3600, **params):
    API_CACHE.mkdir(parents=True, exist_ok=True)
    qs = urllib.parse.urlencode(sorted(params.items()))
    fn = API_CACHE / (path.strip("/").replace("/", "_") + ("_" + qs.replace("&", "_").replace("=", "-") if qs else "")
                      + ".json")
    if fn.exists() and (max_age is None or time.time() - fn.stat().st_mtime < max_age):
        return json.loads(fn.read_text())
    cfn, c = _counter()
    today = str(_date.today())
    if c.get(today, 0) >= BUDGET:
        raise BudgetError(f"tetto giornaliero di {BUDGET} richieste raggiunto")
    key = os.environ.get("API_FOOTBALL_KEY")
    req = urllib.request.Request(f"{BASE}/{path.strip('/')}?{qs}", headers={"x-apisports-key": key} if key else {})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.loads(r.read())
    c[today] = c.get(today, 0) + 1
    cfn.write_text(json.dumps(c))
    if data.get("errors"):
        raise RuntimeError(f"API-Football: {data['errors']}")
    fn.write_text(json.dumps(data))
    return data


def fixtures(day):
    """Partite del giorno (YYYY-MM-DD) nei campionati coperti."""
    out = []
    for f in get("fixtures", date=day)["response"]:
        lid = f["league"]["id"]
        if lid not in DIV_OF:
            continue
        out.append({"id": f["fixture"]["id"], "div": DIV_OF[lid], "date": day, "ora": f["fixture"]["date"][11:16],
                    "kickoff": f["fixture"]["date"], "stato": f["fixture"]["status"]["short"],
                    "arbitro": (f["fixture"].get("referee") or "").split(",")[0].strip(),
                    "home_id": f["teams"]["home"]["id"], "away_id": f["teams"]["away"]["id"],
                    "home_api": f["teams"]["home"]["name"], "away_api": f["teams"]["away"]["name"],
                    "gol": (f["goals"]["home"], f["goals"]["away"]),
                    "pt": (f["score"]["halftime"]["home"], f["score"]["halftime"]["away"])})
    return out


def odds(fixture_id):
    r = get("odds", fixture=fixture_id)["response"]
    return r[0]["bookmakers"] if r else []


def statistics(fixture_id):
    """Statistiche finali per squadra: {'home': {...}, 'away': {...}} con angoli, falli, tiri, tiri in porta, cartellini."""
    keys = {"Corner Kicks": "cor", "Fouls": "fou", "Total Shots": "sh", "Shots on Goal": "sot",
            "Yellow Cards": "yel", "Red Cards": "red", "Offsides": "off", "Ball Possession": "pos"}
    res = get("fixtures/statistics", max_age=None, fixture=fixture_id)["response"]
    out = {}
    for side, t in zip(("home", "away"), res):
        d = {}
        for s in t["statistics"]:
            if s["type"] in keys:
                v = s["value"]
                v = float(str(v).rstrip("%")) if v not in (None, "") else 0.0
                d[keys[s["type"]]] = v
        out[side] = d
    return out


def user_books():
    return json.loads((ROOT / "data" / "bookmakers.json").read_text())["utente"]


def quotes(bookmakers, stale=1.12, mine=None):
    """Per ogni (mercato, valore): quota migliore tra i bookmaker dell'UTENTE ('best', 'bm'; None se nessuno dei suoi
    la offre), migliore in assoluto ('best_all'), quota Pinnacle, mediana e numero di bookmaker.
    Una quota più alta della mediana di oltre il 12% è considerata fuori mercato (vecchia o errata) e scartata."""
    mine = user_books() if mine is None else mine
    allq = {}
    for b in bookmakers:
        for bet in b["bets"]:
            for v in bet["values"]:
                try:
                    q = float(v["odd"])
                except (TypeError, ValueError):
                    continue
                allq.setdefault((bet["id"], bet["name"], str(v["value"])), []).append((q, b["name"]))
    out = []
    for (bid, name, val), lst in allq.items():
        qs = [q for q, _ in lst]
        med = median(qs)
        good = [(q, bm) for q, bm in lst if len(lst) < 3 or q <= med * stale]
        best_all, bm_all = max(good)
        own = [(q, bm) for q, bm in good if bm in mine]
        best, bm = max(own) if own else (None, None)
        pin = next((q for q, n in lst if n == "Pinnacle"), None)
        out.append({"bet_id": bid, "bet": name, "value": val, "best": best, "bm": bm, "best_all": best_all,
                    "bm_all": bm_all, "pin": pin, "med": med, "n": len(lst), "scartate": len(lst) - len(good)})
    return out


def market_inputs(qs):
    """Colonne di mercato del modello dalle quote del giorno (Pinnacle se c'è, altrimenti mediana)."""
    def q(bid, val, pin=True):
        r = next((x for x in qs if x["bet_id"] == bid and x["value"] == val), None)
        if r is None:
            return float("nan")
        return r["pin"] if pin and r["pin"] else r["med"]
    o = {"PinH": q(1, "Home"), "PinD": q(1, "Draw"), "PinA": q(1, "Away"),
         "PinO25": q(5, "Over 2.5"), "PinU25": q(5, "Under 2.5"),
         "OddHome": q(1, "Home", False), "OddDraw": q(1, "Draw", False), "OddAway": q(1, "Away", False),
         "Over25": q(5, "Over 2.5", False), "Under25": q(5, "Under 2.5", False)}
    ah = [x for x in qs if x["bet_id"] == 4 and x["value"].startswith("Home")]
    if ah:                                       # linea asiatica più vicina alla parità
        pair = min(ah, key=lambda x: abs(x["med"] - 1.95))
        o["HandiSize"] = float(pair["value"].split()[1])
    return o


def load_team_map():
    return json.loads(TEAM_MAP.read_text()) if TEAM_MAP.exists() else {}


def save_team_map(tm):
    TEAM_MAP.write_text(json.dumps(tm, indent=1, ensure_ascii=False, sort_keys=True))


def snapshot(fixture_id, qs):
    """Istantanea delle quote (migliore dell'utente e Pinnacle per ogni giocata) con ora: per l'andamento."""
    d = API_CACHE / "snap" / str(fixture_id)
    d.mkdir(parents=True, exist_ok=True)
    ts = time.strftime("%Y%m%d-%H%M", time.gmtime())
    (d / f"{ts}.json").write_text(json.dumps({f"{q['bet_id']}|{q['value']}": [q["best"], q["pin"]] for q in qs}))


def first_snapshot(fixture_id):
    """(ora, quote) della prima istantanea salvata, o None."""
    d = API_CACHE / "snap" / str(fixture_id)
    files = sorted(d.glob("*.json")) if d.exists() else []
    return (files[0].stem, json.loads(files[0].read_text())) if files else None
