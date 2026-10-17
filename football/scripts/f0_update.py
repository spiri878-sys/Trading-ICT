"""Aggiorna data/raw/Matches.csv con le partite recenti da football-data.co.uk (CSV di stagione).

Uso: python football/scripts/f0_update.py [stagione=2627]
Aggiunge solo partite con data successiva all'ultima dell'archivio per quel campionato.
Elo: ultimo valore disponibile in EloRatings.csv prima della partita; Form3/Form5: punti nelle
ultime 3/5 partite calcolati dall'archivio (stessa definizione di fb/card.py).
"""
import io
import sys
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fb.data import COUNTRY, RAW  # noqa: E402

MAP = {"FTHG": "FTHome", "FTAG": "FTAway", "FTR": "FTResult", "HTHG": "HTHome", "HTAG": "HTAway",
       "HTR": "HTResult", "HS": "HomeShots", "AS": "AwayShots", "HST": "HomeTarget", "AST": "AwayTarget",
       "HF": "HomeFouls", "AF": "AwayFouls", "HC": "HomeCorners", "AC": "AwayCorners", "HY": "HomeYellow",
       "AY": "AwayYellow", "HR": "HomeRed", "AR": "AwayRed", "B365H": "OddHome", "B365D": "OddDraw",
       "B365A": "OddAway", "MaxH": "MaxHome", "MaxD": "MaxDraw", "MaxA": "MaxAway", "B365>2.5": "Over25",
       "B365<2.5": "Under25", "Max>2.5": "MaxOver25", "Max<2.5": "MaxUnder25", "AHh": "HandiSize",
       "B365AHH": "HandiHome", "B365AHA": "HandiAway"}


# campionati extra (solo gol e quote 1X2 di chiusura): codice archivio -> file football-data.co.uk/new/
EXTRA = {"ARG": "ARG", "AUT": "AUT", "BRA": "BRA", "CHN": "CHN", "DEN": "DNK", "FIN": "FIN", "IRL": "IRL",
         "JAP": "JPN", "MEX": "MEX", "NOR": "NOR", "POL": "POL", "ROM": "ROU", "RUS": "RUS", "SUI": "SWZ",
         "SWE": "SWE", "USA": "USA"}
MAP_EXTRA = {"Home": "HomeTeam", "Away": "AwayTeam", "HG": "FTHG", "AG": "FTAG", "Res": "FTR"}


def fetch(div, season):
    url = (f"https://www.football-data.co.uk/new/{EXTRA[div]}.csv" if div in EXTRA
           else f"https://www.football-data.co.uk/mmz4281/{season}/{div}.csv")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    raw = urllib.request.urlopen(req, timeout=30).read().decode("utf-8-sig", errors="replace")
    return pd.read_csv(io.StringIO(raw)) if raw.strip() else pd.DataFrame()


def main(season="2627"):
    path = RAW / "Matches.csv"
    old = pd.read_csv(path, low_memory=False)
    cols = list(old.columns)
    last = pd.to_datetime(old.MatchDate).groupby(old.Division).max()
    new = []
    for div in list(COUNTRY) + list(EXTRA):
        try:
            d = fetch(div, season)
            if div in EXTRA:
                d = d.rename(columns=MAP_EXTRA)
                d["B365H"], d["B365D"], d["B365A"] = d.AvgCH, d.AvgCD, d.AvgCA   # come l'archivio: media mercato
                d["MaxH"], d["MaxD"], d["MaxA"] = d.MaxCH, d.MaxCD, d.MaxCA
        except Exception as e:  # noqa: BLE001
            print(f"{div}: errore {e}")
            continue
        if d.empty or "FTHG" not in d:
            print(f"{div}: vuoto")
            continue
        d = d.dropna(subset=["HomeTeam", "AwayTeam", "FTHG", "FTAG"]).copy()
        d["date"] = pd.to_datetime(d.Date, dayfirst=True)
        d = d[d.date > last.get(div, pd.Timestamp("1900-01-01"))]
        if d.empty:
            continue
        out = d.rename(columns=MAP)
        out["Division"] = div
        out["MatchDate"] = out.date.dt.strftime("%Y-%m-%d")
        out["MatchTime"] = out.get("Time", pd.Series("", index=out.index)).astype(str) + ":00"
        new.append(out)
        print(f"{div}: +{len(out)} (fino al {out.date.max():%Y-%m-%d})")
    if not new:
        print("Nessuna partita nuova.")
        return
    add = pd.concat(new, ignore_index=True)

    elo = pd.read_csv(RAW / "EloRatings.csv", parse_dates=["date"]).sort_values("date")
    for side in ("Home", "Away"):
        k = add[[f"{side}Team", "date"]].rename(columns={f"{side}Team": "club"}).reset_index()
        k = pd.merge_asof(k.sort_values("date"), elo[["date", "club", "elo"]], on="date", by="club")
        add.loc[k["index"], f"{side}Elo"] = k.elo.values

    # forma dai risultati (archivio + nuove), in ordine cronologico
    hist = pd.concat([old.assign(date=pd.to_datetime(old.MatchDate)), add], ignore_index=True)
    hist = hist.dropna(subset=["FTHome", "FTAway"]).sort_values("date", kind="stable")
    pts = {}
    is_new = set(add.index + len(old))
    hist_idx = hist.index
    for i, r in zip(hist_idx, hist.itertuples()):
        h, a = r.HomeTeam, r.AwayTeam
        if i in is_new:
            j = i - len(old)
            for side, t in (("Home", h), ("Away", a)):
                p = pts.get(t, [])
                add.loc[j, f"Form3{side}"] = float(sum(p[-3:]))
                add.loc[j, f"Form5{side}"] = float(sum(p[-5:]))
        s = np.sign(r.FTHome - r.FTAway)
        pts.setdefault(h, []).append(3 if s > 0 else 1 if s == 0 else 0)
        pts.setdefault(a, []).append(3 if s < 0 else 1 if s == 0 else 0)

    for c in cols:
        if c not in add:
            add[c] = np.nan
    allm = pd.concat([old, add[cols]], ignore_index=True)
    allm.to_csv(path, index=False)
    print(f"Aggiunte {len(add)} partite. Archivio fino al {allm.MatchDate.max()}.")


if __name__ == "__main__":
    main(*sys.argv[1:])
