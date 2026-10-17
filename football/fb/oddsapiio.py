"""Fonte quote alternativa: odds-api.io (piano gratuito: 100 richieste/ora, 2 bookmaker scelti, solo pre-partita).

Chiave: variabile d'ambiente ODDS_API_IO_KEY (mai nel codice). Bookmaker: Bet365 (dove gioca l'utente) e Betfair
Exchange (riferimento della probabilità 'giusta', al posto di Pinnacle che qui non c'è).
Le quote vengono tradotte nel formato di API-Football (stessi id di mercato di fb.markets.API_BETS e stessi testi dei
valori), così tutto il resto del sistema resta uguale. Handicap: come in API-Football, sul lato ospite si scrive la
linea della CASA ('Away -0.5' = ospite +0.5), che fb.markets.parse già gira.
"""
import json
import os
import time
import urllib.parse
import urllib.request
from datetime import date as _date

from .data import CACHE

BASE = "https://api.odds-api.io/v3"
CACHE_DIR = CACHE / "oddsapiio"
BUDGET = 480                                    # al giorno (limite gratuito 500)
BOOKS = ("Bet365", "Betfair Exchange")
REF_BOOK = "Betfair Exchange"

# mercato odds-api.io -> id API-Football e tipo di quota
LINE = {"Totals": 5, "Goals Over/Under": 5, "Totals HT": 6, "Totals 2H": 26, "Team Total Home": 16,
        "Team Total Away": 17, "Team Total Home HT": 105, "Team Total Away HT": 106, "Team Total Home 2H": 107,
        "Team Total Away 2H": 108, "Corners Totals": 45, "Corners Totals Home": 57, "Corners Totals Away": 58,
        "Number of Cards In Match": 80, "Bookings Totals": 80, "Bookings Totals Home": 82,
        "Bookings Totals Away": 83}
SPREAD = {"Spread": 4, "Spread HT": 19, "Spread 2H": 104, "Corners Spread": 56, "Bookings Spread": 81}
THREE = {"ML": 1, "ML HT": 13, "ML 2H": 3, "Most Shots 3-Way": 340, "Most Shots on Target 3-Way": 176,
         "Most Fouls 3-Way": 175}
EURO = {"European Handicap": 9, "European Handicap HT": 18, "European Handicap 2H": 181}
YESNO = {"Both Teams To Score": 8, "Both Teams To Score HT": 34, "Both Teams To Score 2H": 35,
         "Clean Sheet Home": 27, "Clean Sheet Away": 28, "Goal In Both Halves": 184}
ODDEVEN = {"Odd/Even": 21, "Odd/Even HT": 22, "Odd/Even 2H": 63, "Odd/Even Home": 23, "Odd/Even Away": 60}
DC = {"Double Chance": 12, "Double Chance HT": 20, "Double Chance 2H": 33}


class BudgetError(RuntimeError):
    pass


def available():
    return bool(os.environ.get("ODDS_API_IO_KEY"))


def _counter():
    fn = CACHE_DIR / "contatore.json"
    return fn, (json.loads(fn.read_text()) if fn.exists() else {})


def used_today():
    return _counter()[1].get(str(_date.today()), 0)


def get(path, max_age=3 * 3600, **params):
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    qs = urllib.parse.urlencode(sorted(params.items()))
    fn = CACHE_DIR / (path.strip("/").replace("/", "_") + "_" + qs.replace("&", "_").replace("=", "-")[:180] + ".json")
    if fn.exists() and (max_age is None or time.time() - fn.stat().st_mtime < max_age):
        return json.loads(fn.read_text())
    cfn, c = _counter()
    today = str(_date.today())
    if c.get(today, 0) >= BUDGET:
        raise BudgetError(f"tetto giornaliero odds-api.io di {BUDGET} richieste raggiunto")
    key = os.environ.get("ODDS_API_IO_KEY", "")
    url = f"{BASE}/{path.strip('/')}?{qs}&apiKey={urllib.parse.quote(key)}"
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "calcio"}), timeout=30) as r:
        data = json.loads(r.read())
    c[today] = c.get(today, 0) + 1
    cfn.write_text(json.dumps(c))
    fn.write_text(json.dumps(data))
    return data


def select_books():
    """Imposta una volta i 2 bookmaker del piano gratuito (Bet365 + Betfair Exchange)."""
    return get("bookmakers/selected/select", max_age=0, bookmakers=",".join(BOOKS))


def events(day):
    """Partite di calcio del giorno (UTC)."""
    out, skip = [], 0
    while True:
        r = get("events", sport="football", status="pending", **{"from": f"{day}T00:00:00Z", "to": f"{day}T23:59:59Z"},
                limit=500, skip=skip)
        out += r
        if len(r) < 500:
            return out
        skip += 500


def odds_multi(event_ids):
    """Quote di fino a 10 partite per richiesta: {event_id: risposta}."""
    out = {}
    ids = list(event_ids)
    for i in range(0, len(ids), 10):
        r = get("odds/multi", eventIds=",".join(str(x) for x in ids[i:i + 10]), bookmakers=",".join(BOOKS))
        for ev in r:
            out[ev["id"]] = ev
    return out


def _f(x):
    try:
        v = float(x)
        return v if v > 1 else None
    except (TypeError, ValueError):
        return None


def _g(x):
    return f"{float(x):g}"


def to_api_football(ev):
    """Risposta odds-api.io di una partita -> lista bookmaker nel formato di API-Football (per fb.apifootball.quotes)."""
    books = []
    for bm, markets in (ev.get("bookmakers") or {}).items():
        bets = {}

        def add(bid, name, value, odd):
            q = _f(odd)
            if q:
                bets.setdefault(bid, {"id": bid, "name": name, "values": []})["values"].append({"value": value, "odd": q})
        for mk in markets:
            name = mk.get("name")
            for o in mk.get("odds") or []:
                if name in LINE and o.get("max") is not None:
                    add(LINE[name], name, f"Over {_g(o['max'])}", o.get("over"))
                    add(LINE[name], name, f"Under {_g(o['max'])}", o.get("under"))
                elif name in SPREAD and o.get("hdp") is not None:
                    h = float(o["hdp"])                          # handicap della casa
                    add(SPREAD[name], name, f"Home {h:+g}", o.get("home"))
                    add(SPREAD[name], name, f"Away {h:+g}", o.get("away"))   # convenzione API-Football: linea casa
                elif name in THREE and o.get("hdp") in (None, 0, 0.0):
                    add(THREE[name], name, "Home", o.get("home"))
                    add(THREE[name], name, "Draw", o.get("draw"))
                    add(THREE[name], name, "Away", o.get("away"))
                elif name in EURO and o.get("hdp") is not None:
                    h = float(o["hdp"])
                    for side, k in (("Home", "home"), ("Draw", "draw"), ("Away", "away")):
                        add(EURO[name], name, f"{side} {h:+g}", o.get(k))
                elif name in YESNO:
                    add(YESNO[name], name, "Yes", o.get("yes"))
                    add(YESNO[name], name, "No", o.get("no"))
                elif name in ODDEVEN:
                    add(ODDEVEN[name], name, "Odd", o.get("odd"))
                    add(ODDEVEN[name], name, "Even", o.get("even"))
                elif name in DC:
                    for lab, keys in (("Home/Draw", ("homeDraw", "home_draw", "1X")),
                                      ("Home/Away", ("homeAway", "home_away", "12")),
                                      ("Draw/Away", ("drawAway", "draw_away", "X2"))):
                        add(DC[name], name, lab, next((o[k] for k in keys if k in o), None))
                elif name == "Draw No Bet":
                    add(2, name, "Home", o.get("home"))
                    add(2, name, "Away", o.get("away"))
        books.append({"name": "Pinnacle" if bm == REF_BOOK else bm, "bets": list(bets.values())})
    return books


# campionato dell'archivio -> parole che devono comparire nel nome/slug della lega odds-api.io (paese, lega)
LEAGUES = {"E0": ("england", "premier league"), "E1": ("england", "championship"), "E2": ("england", "league one"),
           "E3": ("england", "league two"), "EC": ("england", "national league"),
           "SC0": ("scotland", "premiership"), "SC1": ("scotland", "championship"), "SC2": ("scotland", "league one"),
           "SC3": ("scotland", "league two"), "D1": ("germany", "bundesliga"), "D2": ("germany", "2. bundesliga"),
           "I1": ("italy", "serie a"), "I2": ("italy", "serie b"), "SP1": ("spain", "laliga"),
           "SP2": ("spain", "laliga2"), "F1": ("france", "ligue 1"), "F2": ("france", "ligue 2"),
           "N1": ("netherlands", "eredivisie"), "B1": ("belgium", "pro league"), "P1": ("portugal", "liga portugal"),
           "T1": ("turkey", "super lig"), "G1": ("greece", "super league"), "ARG": ("argentina", "liga profesional"),
           "AUT": ("austria", "bundesliga"), "BRA": ("brazil", "serie a"), "CHN": ("china", "super league"),
           "DEN": ("denmark", "superliga"), "FIN": ("finland", "veikkausliiga"), "IRL": ("ireland", "premier division"),
           "JAP": ("japan", "j1"), "MEX": ("mexico", "liga mx"), "NOR": ("norway", "eliteserien"),
           "POL": ("poland", "ekstraklasa"), "ROM": ("romania", "liga 1"), "RUS": ("russia", "premier league"),
           "SUI": ("switzerland", "super league"), "SWE": ("sweden", "allsvenskan"), "USA": ("usa", "mls")}
EXCLUDE = ("women", "u19", "u21", "u23", "youth", "reserve", "cup", "copa", "coppa", "play", "friend")


def league_div(league):
    """Lega odds-api.io -> codice archivio (None se non coperta). Prova nome e slug, tolleranti a trattini/spazi."""
    txt = " ".join(str(league.get(k, "")) for k in ("name", "slug")).lower().replace("-", " ")
    if any(w in txt for w in EXCLUDE):
        return None
    hits = [d for d, (c, l) in LEAGUES.items() if c in txt and l.replace("-", " ") in txt]
    if len(hits) > 1:                            # es. 'bundesliga' e '2. bundesliga': vince la più specifica
        hits.sort(key=lambda d: -len(LEAGUES[d][1]))
    return hits[0] if hits else None
