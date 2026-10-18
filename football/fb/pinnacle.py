"""Quote Pinnacle ATTUALI (1X2 e linea asiatica principale) dall'interfaccia pubblica per i visitatori del sito
(guest.api.arcadia.pinnacle.com: nessuna chiave, nessun login; robots.txt di pinnacle.com vieta solo account/ricerca).
L'apertura non c'è: la registriamo noi. La prima volta che vediamo una partita salviamo le sue quote in
output/pinnacle_apertura.json (nel repository, così l'allerta oraria la ritrova); il movimento è prima vista -> adesso.
Uso con moderazione: 2 richieste per campionato a ogni controllo.
"""
import json
import time
import urllib.request
from datetime import datetime, timedelta, timezone

from .data import ROOT

BASE = "https://guest.api.arcadia.pinnacle.com/0.1"
LEAGUES = {"E0": 1980, "E1": 1977, "E2": 1957, "E3": 1958, "EC": 1978, "SC0": 2421, "SC1": 2417, "D1": 1842,
           "D2": 1843, "I1": 2436, "I2": 2438, "SP1": 2196, "SP2": 2432, "F1": 2036, "F2": 2037, "N1": 1928,
           "B1": 1817, "P1": 2386, "T1": 2592, "G1": 2081, "ARG": 210697, "AUT": 1792, "BRA": 1834, "CHN": 6417,
           "DEN": 1913, "FIN": 2024, "IRL": 2120, "JAP": 2157, "MEX": 2242, "NOR": 2333, "POL": 2374, "ROM": 2395,
           "RUS": 2406, "SUI": 2517, "SWE": 1728, "USA": 2663}
STORE = ROOT / "output" / "pinnacle_apertura.json"


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


def games(div):
    """Partite non iniziate di un campionato con quote 1X2 e linea asiatica principale attuali."""
    mus = _get(f"leagues/{LEAGUES[div]}/matchups")
    mk = _get(f"leagues/{LEAGUES[div]}/markets/straight")
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


def snapshot(divs=None):
    """Legge tutti i campionati, registra l'apertura delle partite nuove e restituisce le partite con
    apertura e quote attuali. Le partite iniziate da più di 2 giorni escono dall'archivio."""
    store = json.loads(STORE.read_text()) if STORE.exists() else {}
    now = datetime.now(timezone.utc)
    rows = []
    for div in divs or LEAGUES:
        try:
            gs = games(div)
        except Exception:  # noqa: BLE001  un campionato che non risponde non ferma gli altri
            continue
        for g in gs:
            first = store.setdefault(g["id"], {"visto": now.isoformat(timespec="minutes"), "q": g["q"],
                                               "ah": g.get("ah"), "div": div, "home": g["home"],
                                               "away": g["away"], "start": g["start"]})
            rows.append(dict(g, q_open=first["q"], ah_open=first.get("ah"), visto=first["visto"]))
    limit = now - timedelta(days=2)
    store = {k: v for k, v in store.items()
             if datetime.fromisoformat(v["start"].replace("Z", "+00:00")) > limit}
    STORE.write_text(json.dumps(store, ensure_ascii=False, indent=0))
    return rows
