"""Quote Pinnacle ATTUALI (1X2 e linea asiatica principale) dall'interfaccia pubblica per i visitatori del sito
(guest.api.arcadia.pinnacle.com: nessuna chiave, nessun login; robots.txt di pinnacle.com vieta solo account/ricerca).
L'apertura non c'è: la registriamo noi. La prima volta che vediamo una partita salviamo le sue quote in
output/pinnacle_apertura.json (nel repository, così l'allerta oraria la ritrova); il movimento è prima vista -> adesso.
Uso con moderazione: 2 richieste per campionato a ogni controllo (al massimo una volta all'ora).
"""
import json
import re
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone

from .data import ROOT

BASE = "https://guest.api.arcadia.pinnacle.com/0.1"
LEAGUES = {"E0": 1980, "E1": 1977, "E2": 1957, "E3": 1958, "EC": 1978, "SC0": 2421, "SC1": 2417, "D1": 1842,
           "D2": 1843, "I1": 2436, "I2": 2438, "SP1": 2196, "SP2": 2432, "F1": 2036, "F2": 2037, "N1": 1928,
           "B1": 1817, "P1": 2386, "T1": 2592, "G1": 2081, "ARG": 210697, "AUT": 1792, "BRA": 1834, "CHN": 6417,
           "DEN": 1913, "FIN": 2024, "IRL": 2120, "JAP": 2157, "MEX": 2242, "NOR": 2333, "POL": 2374, "ROM": 2395,
           "RUS": 2406, "SUI": 2517, "SWE": 1728, "USA": 2663}
STORE = ROOT / "output" / "pinnacle_apertura.json"
SKIP = re.compile(r"Corners|Bookings|Women|Femin|Damallsvenskan|U\d\d|Youth|Reserve|Specials|Friendl|Esports|"
                  r"Regional|Amateur|Eccellenza|Landesliga|Derde|Isthmian|Tercera|Segunda Federacion")


def _get(path):
    req = urllib.request.Request(f"{BASE}/{path}", headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"})
    for attempt in range(3):
        try:
            return json.loads(urllib.request.urlopen(req, timeout=30).read())
        except OSError:
            if attempt == 2:
                raise
            time.sleep(2 ** attempt)


def dec(us):
    """Quota americana -> decimale."""
    return 1 + us / 100 if us > 0 else 1 + 100 / -us


def all_leagues():
    """Tutti i campionati di calcio principali quotati ora da Pinnacle: {codice: id}. I nostri hanno il codice
    dell'archivio (E0, I1, ...), gli altri 'PIN:<nome>' (senza verifica storica)."""
    ours = {v: k for k, v in LEAGUES.items()}
    out = dict(LEAGUES)
    for lg in _get("sports/29/leagues?all=false"):
        if lg.get("matchupCount") and lg["id"] not in ours and not SKIP.search(lg["name"]):
            out[f"PIN:{lg['name']}"] = lg["id"]
    return out


def games(div, lid=None):
    """Partite non iniziate di un campionato con quote 1X2 e linea asiatica principale attuali."""
    lid = lid or LEAGUES[div]
    mus = _get(f"leagues/{lid}/matchups")
    mk = _get(f"leagues/{lid}/markets/straight")
    main = {m["id"]: m for m in mus if m.get("type") == "matchup" and not m.get("parentId") and not m.get("isLive")}
    out = {}
    for x in mk:
        m = main.get(x["matchupId"])
        if m is None or x.get("period") != 0 or x.get("isAlternate"):
            continue
        g = out.setdefault(m["id"], {"id": str(m["id"]), "div": div, "start": m["startTime"],
                                     **{p["alignment"]: p["name"] for p in m["participants"]}})
        pr = {p["designation"]: p for p in x["prices"]}
        if x["type"] == "moneyline" and {"home", "draw", "away"} <= set(pr):
            g["q"] = {k: round(dec(pr[n]["price"]), 3) for k, n in (("H", "home"), ("D", "draw"), ("A", "away"))}
        elif x["type"] == "spread" and "home" in pr:
            g["ah"] = pr["home"]["points"]
    return [g for g in out.values() if "q" in g and "home" in g and "away" in g]


def snapshot(divs=None, tutti=True):
    """Legge tutti i campionati, registra l'apertura delle partite nuove e restituisce le partite con
    apertura e quote attuali. Le partite iniziate da più di 2 giorni escono dall'archivio."""
    store = json.loads(STORE.read_text()) if STORE.exists() else {}
    now = datetime.now(timezone.utc)
    rows = []
    leagues = {d: LEAGUES[d] for d in divs} if divs else (all_leagues() if tutti else LEAGUES)

    def one(item):
        try:
            return games(*item)
        except Exception:  # noqa: BLE001  un campionato che non risponde non ferma gli altri
            return []
    with ThreadPoolExecutor(4) as ex:
        found = [g for gs in ex.map(one, leagues.items()) for g in gs]
    for g in found:
        first = store.setdefault(g["id"], {"visto": now.isoformat(timespec="minutes"), "q": g["q"],
                                           "ah": g.get("ah"), "div": g["div"], "home": g["home"],
                                           "away": g["away"], "start": g["start"]})
        rows.append(dict(g, q_open=first["q"], ah_open=first.get("ah"), visto=first["visto"]))
    limit = now - timedelta(days=2)
    store = {k: v for k, v in store.items()
             if datetime.fromisoformat(v["start"].replace("Z", "+00:00")) > limit}
    STORE.write_text(json.dumps(store, ensure_ascii=False, indent=0))
    return rows
