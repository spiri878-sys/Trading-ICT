"""Risultati e statistiche gratis, senza chiave, dalle API pubbliche di ESPN (anche live: minuto, punteggio, angoli,
cartellini, tiri, falli). Uso: esiti delle giocate e dati live quando API-Football non è disponibile.
Attenzione: fonte non ufficiale, senza garanzie; le statistiche ESPN possono differire di poco da quelle dei bookmaker.
"""
import json
import time
import urllib.request

from .data import CACHE
from .teams import norm, similar

BASE = "https://site.api.espn.com/apis/site/v2/sports/soccer"
CACHE_DIR = CACHE / "espn"
LEAGUES = {"E0": "eng.1", "E1": "eng.2", "E2": "eng.3", "E3": "eng.4", "EC": "eng.5", "SC0": "sco.1", "SC1": "sco.2",
           "SC2": "sco.3", "SC3": "sco.4", "D1": "ger.1", "D2": "ger.2", "I1": "ita.1", "I2": "ita.2", "SP1": "esp.1",
           "SP2": "esp.2", "F1": "fra.1", "F2": "fra.2", "N1": "ned.1", "B1": "bel.1", "P1": "por.1", "T1": "tur.1",
           "G1": "gre.1", "ARG": "arg.1", "AUT": "aut.1", "BRA": "bra.1", "CHN": "chn.1", "DEN": "den.1",
           "FIN": "fin.1", "IRL": "irl.1", "JAP": "jpn.1", "MEX": "mex.1", "NOR": "nor.1", "POL": "pol.1",
           "ROM": "rou.1", "RUS": "rus.1", "SUI": "sui.1", "SWE": "swe.1", "USA": "usa.1"}
STATS = {"wonCorners": "cor", "foulsCommitted": "fou", "totalShots": "sh", "shotsOnTarget": "sot",
         "yellowCards": "yel", "redCards": "red"}


def _get(url, max_age):
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    fn = CACHE_DIR / (url.split("/soccer/")[1].replace("/", "_").replace("?", "_").replace("=", "-") + ".json")
    if fn.exists() and time.time() - fn.stat().st_mtime < max_age:
        return json.loads(fn.read_text())
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    for attempt in range(4):                        # rete instabile: riprova con attese crescenti
        try:
            data = json.loads(urllib.request.urlopen(req, timeout=30).read())
            break
        except OSError:
            if attempt == 3:
                raise
            time.sleep(2 ** attempt)
    fn.write_text(json.dumps(data))
    return data


def scoreboard(div, day, max_age=600):
    """Partite di un campionato in un giorno (YYYY-MM-DD)."""
    if div not in LEAGUES:
        return []
    d = _get(f"{BASE}/{LEAGUES[div]}/scoreboard?dates={day.replace('-', '')}", max_age)
    out = []
    for e in d.get("events", []):
        comp = {c["homeAway"]: c for c in e["competitions"][0]["competitors"]}
        out.append({"id": e["id"], "div": div, "stato": e["status"]["type"]["name"],
                    "minuto": e["status"].get("displayClock"), "home": comp["home"]["team"]["displayName"],
                    "away": comp["away"]["team"]["displayName"]})
    return out


def find(div, day, home, away):
    """Partita ESPN che corrisponde a casa/ospite (nomi qualsiasi), oppure None se incerta."""
    best, score = None, 0.0
    for e in scoreboard(div, day):
        s = (similar(norm(home), norm(e["home"])) + similar(norm(away), norm(e["away"]))) / 2
        if s > score:
            best, score = e, s
    return best if score >= 0.7 else None


def counts(div, event_id, max_age=600):
    """Conteggi per statistica {stat: (casa, ospite)} + stato e minuto. Gol del 1° tempo dai parziali."""
    d = _get(f"{BASE}/{LEAGUES[div]}/summary?event={event_id}", max_age)
    comp = d["header"]["competitions"][0]
    side = {c["homeAway"]: c for c in comp["competitors"]}
    h, a = side["home"], side["away"]
    c = {"g": (float(h.get("score") or 0), float(a.get("score") or 0))}
    lh, la = h.get("linescores") or [], a.get("linescores") or []
    if lh and la:
        c["ght"] = (float(lh[0]["displayValue"]), float(la[0]["displayValue"]))
        c["g2h"] = (c["g"][0] - c["ght"][0], c["g"][1] - c["ght"][1])
    teams = {t["team"]["id"]: {s["name"]: s["displayValue"] for s in t.get("statistics", [])}
             for t in d.get("boxscore", {}).get("teams", [])}
    sh, sa = teams.get(h["team"]["id"], {}), teams.get(a["team"]["id"], {})
    for k, stat in STATS.items():
        if k in sh and k in sa:
            c[stat] = (float(sh[k]), float(sa[k]))
    if "yel" in c and "red" in c:
        c["crd"] = (c["yel"][0] + 2 * c["red"][0], c["yel"][1] + 2 * c["red"][1])
    c["_stato"] = comp["status"]["type"]["name"]
    c["_minuto"] = comp["status"].get("displayClock")
    return c
