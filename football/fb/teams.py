"""Corrispondenza nomi squadra API-Football -> archivio (Fase M5).

Ordine: tabella salvata (data/team_map.json, per id API) -> nome uguale -> nome normalizzato -> somiglianza tra le
squadre del campionato nelle ultime 2 stagioni. Abbinamenti nuovi con somiglianza >= 0.75 vengono salvati come
"auto"; sotto soglia la squadra resta senza abbinamento (la partita viene saltata, mai indovinata).
"""
import difflib
import re
import unicodedata

from .apifootball import load_team_map, save_team_map
from .data import matches

DROP = r"\b(fc|afc|cf|sc|ac|as|ss|us|fk|sk|bk|if|ik|cd|ud|sd|rc|rcd|club|de|calcio|1\.|sv|vfl|vfb|tsg|fsv|spvgg|" \
       r"ssc|ogc|stade|sporting|real|athletic|atletico|deportivo|united|city|town)\b"
MANUAL = {"Manchester City": "Man City", "Manchester United": "Man United", "Nottingham Forest": "Nott'm Forest",
          "Wolverhampton Wanderers": "Wolves", "Sheffield Utd": "Sheffield United", "AC Milan": "Milan",
          "AS Roma": "Roma", "Hellas Verona": "Verona", "Atletico Madrid": "Ath Madrid", "Athletic Club": "Ath Bilbao",
          "Real Betis": "Betis", "Celta Vigo": "Celta", "Espanyol": "Espanol", "Bayern München": "Bayern Munich",
          "Borussia Mönchengladbach": "M'gladbach", "Borussia Dortmund": "Dortmund", "1. FC Köln": "FC Koln",
          "Eintracht Frankfurt": "Ein Frankfurt", "Bayer Leverkusen": "Leverkusen", "Paris Saint Germain": "Paris SG",
          "Saint Etienne": "St Etienne", "Sporting CP": "Sp Lisbon", "FC Porto": "Porto", "SL Benfica": "Benfica",
          "Inter": "Inter", "Stade Brestois 29": "Brest", "Estac Troyes": "Troyes", "Hamburger SV": "Hamburg",
          "FSV Mainz 05": "Mainz", "FC Schalke 04": "Schalke 04", "SC Paderborn 07": "Paderborn",
          "Dundee Utd": "Dundee United", "ST Mirren": "St Mirren", "ST Johnstone": "St Johnstone",
          "Tokyo Verdy": "Verdy", "Turku PS": "TPS", "Queen of the South": "Queen of Sth",
          "Independ. Rivadavia": "Ind. Rivadavia", "Atletico Paranaense": "Athletico-PR",
          "Shandong Luneng": "Shandong Taishan", "Hangzhou Greentown": "Zhejiang Professional",
          "Qingdao Jonoon": "Qingdao Hainiu"}


def norm(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    s = re.sub(DROP, " ", s)
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def similar(a, b):
    """Somiglianza 0-1: sequenza di caratteri, oppure abbreviazioni (ogni parola di uno è l'inizio di una parola
    dell'altro: 'gimnasia m' ~ 'gimnasia mendoza', 'kyoto' ~ 'kyoto sanga')."""
    ta, tb = a.split(), b.split()
    if not ta or not tb:
        return 0.0

    def cover(x, y):
        return sum(any(w.startswith(t) or t.startswith(w) and len(w) >= 3 for w in y) for t in x) / len(x)
    seq = difflib.SequenceMatcher(None, a, b).ratio()
    pref = max(cover(ta, tb) * min(1, len(tb) / len(ta) + 0.5), cover(tb, ta) * min(1, len(ta) / len(tb) + 0.5))
    return max(seq, min(pref, 0.95))


def candidates(div):
    m = matches()
    m = m[(m.Division == div) & (m.season >= m.season.max() - 2)]
    return sorted(set(m.HomeTeam) | set(m.AwayTeam))


def resolve(api_id, api_name, div, tm=None, save=True):
    """Nome archivio per una squadra API, oppure None se incerto."""
    tm = load_team_map() if tm is None else tm
    key = str(api_id)
    if key in tm:
        return tm[key]["name"]
    names = candidates(div)
    hit, score = None, 0.0
    if api_name in names:
        hit, score = api_name, 1.0
    elif MANUAL.get(api_name) in names:
        hit, score = MANUAL[api_name], 1.0
    else:
        nm = {norm(n): n for n in names}
        a = norm(api_name)
        if a in nm:
            hit, score = nm[a], 0.99
        else:
            sc = sorted(((similar(a, norm(n)), n) for n in names), reverse=True)
            if sc:
                score = sc[0][0]
                margin = score - (sc[1][0] if len(sc) > 1 else 0)
                hit = sc[0][1] if score >= 0.75 and margin >= 0.1 else None     # incerto -> nessun abbinamento
    if hit and save:
        tm[key] = {"name": hit, "api": api_name, "div": div, "score": round(score, 2),
                   "auto": score < 1.0}
        save_team_map(tm)
    return hit
