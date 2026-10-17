"""Client minimo per API-Football (api-sports.io, v3): partite del giorno e quote angoli.

La chiave si legge SOLO dalla variabile d'ambiente API_FOOTBALL_KEY (mai scritta nel codice o nel repository).
Le risposte vengono salvate in football/data/cache/api/ per non sprecare richieste (piano gratuito: ~100 al giorno).
"""
import difflib
import json
import os
import time
import urllib.parse
import urllib.request

from .data import CACHE

BASE = "https://v3.football.api-sports.io"
API_CACHE = CACHE / "api"

# campionati dell'archivio -> id lega API-Football
LEAGUES = {"E0": 39, "E1": 40, "E2": 41, "E3": 42, "SC0": 179, "D1": 78, "D2": 79, "I1": 135, "I2": 136,
           "SP1": 140, "SP2": 141, "F1": 61, "F2": 62, "N1": 88, "B1": 144, "P1": 94, "T1": 203, "G1": 197}
DIV_OF = {v: k for k, v in LEAGUES.items()}


def get(path, **params):
    key = os.environ.get("API_FOOTBALL_KEY")
    if not key:
        raise RuntimeError("manca la variabile d'ambiente API_FOOTBALL_KEY")
    API_CACHE.mkdir(parents=True, exist_ok=True)
    qs = urllib.parse.urlencode(sorted(params.items()))
    fn = API_CACHE / (path.strip("/").replace("/", "_") + ("_" + qs.replace("&", "_").replace("=", "-") if qs else "") + ".json")
    if fn.exists() and time.time() - fn.stat().st_mtime < 3 * 3600:
        return json.loads(fn.read_text())
    req = urllib.request.Request(f"{BASE}/{path.strip('/')}?{qs}", headers={"x-apisports-key": key})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.loads(r.read())
    if data.get("errors"):
        raise RuntimeError(f"API-Football: {data['errors']}")
    fn.write_text(json.dumps(data))
    return data


def fixtures(date):
    """Partite del giorno (YYYY-MM-DD) nei campionati coperti dal modello."""
    out = []
    for f in get("fixtures", date=date)["response"]:
        lid = f["league"]["id"]
        if lid in DIV_OF:
            out.append({"id": f["fixture"]["id"], "div": DIV_OF[lid], "date": date, "ora": f["fixture"]["date"][11:16],
                        "home_api": f["teams"]["home"]["name"], "away_api": f["teams"]["away"]["name"],
                        "stato": f["fixture"]["status"]["short"]})
    return out


def odds_by_date(date):
    """Tutte le quote pre-partita del giorno, paginate: {fixture_id: [bookmaker, ...]}."""
    res, page = {}, 1
    while True:
        d = get("odds", date=date, page=page)
        for r in d["response"]:
            res[r["fixture"]["id"]] = r["bookmakers"]
        if page >= d.get("paging", {}).get("total", 1):
            return res
        page += 1


def _side(name):
    n = name.lower()
    if "home" in n:
        return "casa"
    if "away" in n:
        return "ospite"
    return "totale"


def best_odds(bookmakers):
    """Quota migliore tra i bookmaker per ogni mercato: 1X2 e angoli (totale / casa / ospite, Over/Under linea).
    Restituisce {nome_mercato: (quota, bookmaker)} con i nomi usati dalla scheda (es. 'Angoli Casa Over 4.5')."""
    best = {}

    def put(k, odd, bm):
        if odd > best.get(k, (0, ""))[0]:
            best[k] = (odd, bm)

    for b in bookmakers:
        bm = b["name"]
        for bet in b["bets"]:
            name = bet["name"].lower()
            if name == "match winner":
                for v in bet["values"]:
                    put({"Home": "1", "Draw": "X", "Away": "2"}.get(v["value"], v["value"]), float(v["odd"]), bm)
            elif "corner" in name and ("over" in name or "under" in name) and "half" not in name \
                    and "1st" not in name and "2nd" not in name:
                pref = {"totale": "Angoli", "casa": "Angoli Casa", "ospite": "Angoli Ospite"}[_side(name)]
                for v in bet["values"]:
                    parts = str(v["value"]).split()
                    if len(parts) == 2 and parts[0] in ("Over", "Under"):
                        put(f"{pref} {parts[0]} {float(parts[1]):g}", float(v["odd"]), bm)
    return best


def match_team(api_name, names):
    """Nome squadra API -> nome dell'archivio (stesso campionato)."""
    alias = {"Manchester City": "Man City", "Manchester United": "Man United", "Nottingham Forest": "Nott'm Forest",
             "Wolverhampton Wanderers": "Wolves", "Newcastle": "Newcastle", "Sheffield Utd": "Sheffield United",
             "Inter": "Inter", "AC Milan": "Milan", "AS Roma": "Roma", "Hellas Verona": "Verona",
             "Atletico Madrid": "Ath Madrid", "Athletic Club": "Ath Bilbao", "Real Betis": "Betis",
             "Celta Vigo": "Celta", "Espanyol": "Espanol", "Deportivo La Coruna": "La Coruna",
             "Bayern München": "Bayern Munich", "Borussia Mönchengladbach": "M'gladbach", "1. FC Köln": "FC Koln",
             "Eintracht Frankfurt": "Ein Frankfurt", "Bayer Leverkusen": "Leverkusen", "Paris Saint Germain": "Paris SG",
             "Saint Etienne": "St Etienne", "PSV Eindhoven": "PSV Eindhoven", "Sporting CP": "Sp Lisbon",
             "FC Porto": "Porto", "SL Benfica": "Benfica"}
    if alias.get(api_name) in names:
        return alias[api_name]
    if api_name in names:
        return api_name
    m = difflib.get_close_matches(api_name, list(names), n=1, cutoff=0.6)
    return m[0] if m else None
