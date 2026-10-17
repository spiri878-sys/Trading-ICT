"""Quote extra e arbitro dai CSV originali di football-data.co.uk (stagioni 2012/13 -> oggi).

Pinnacle pre-partita e chiusura (1X2, O/U 2.5), media di mercato, Bet365 chiusura, arbitro (dove c'è).
Salva data/raw/extra_odds.csv, chiave: Division, MatchDate, HomeTeam, AwayTeam. I CSV vanno in cache.
Uso: python football/scripts/f0_odds.py
"""
import io
import sys
import time
import urllib.request
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fb.data import ALIAS, CACHE, COUNTRY, RAW  # noqa: E402

KEEP = {"PSH": "PinH", "PSD": "PinD", "PSA": "PinA", "PSCH": "PinCH", "PSCD": "PinCD", "PSCA": "PinCA",
        "AvgH": "AvgH", "AvgD": "AvgD", "AvgA": "AvgA", "P>2.5": "PinO25", "P<2.5": "PinU25",
        "PC>2.5": "PinCO25", "PC<2.5": "PinCU25", "Avg>2.5": "AvgO25", "Avg<2.5": "AvgU25",
        "PAHH": "PinAHH", "PAHA": "PinAHA", "AHh": "AHh", "Referee": "Referee"}


def get(div, ssn):
    fn = CACHE / "fdco" / f"{ssn}_{div}.csv"
    if not fn.exists():
        fn.parent.mkdir(parents=True, exist_ok=True)
        url = f"https://www.football-data.co.uk/mmz4281/{ssn}/{div}.csv"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        fn.write_bytes(urllib.request.urlopen(req, timeout=30).read())
        time.sleep(0.3)
    raw = fn.read_bytes().decode("utf-8-sig", errors="replace")
    return pd.read_csv(io.StringIO(raw), on_bad_lines="skip") if raw.strip() else pd.DataFrame()


def main():
    out = []
    for y in range(12, 27):
        ssn = f"{y:02d}{y + 1:02d}"
        for div in COUNTRY:
            try:
                d = get(div, ssn)
            except Exception as e:  # noqa: BLE001
                print(f"{ssn} {div}: {e}")
                continue
            if d.empty or "HomeTeam" not in d:
                continue
            d = d.dropna(subset=["HomeTeam", "AwayTeam", "Date"])
            r = pd.DataFrame({"Division": div,
                              "MatchDate": pd.to_datetime(d.Date, dayfirst=True).dt.strftime("%Y-%m-%d"),
                              "HomeTeam": d.HomeTeam.replace(ALIAS), "AwayTeam": d.AwayTeam.replace(ALIAS)})
            for src, dst in KEEP.items():
                r[dst] = d[src].values if src in d else None
            out.append(r)
        print(ssn, sum(len(x) for x in out))
    e = pd.concat(out, ignore_index=True).drop_duplicates(["Division", "MatchDate", "HomeTeam", "AwayTeam"])
    e.to_csv(RAW / "extra_odds.csv", index=False)
    print(f"Salvate {len(e)} righe; Pinnacle presente: {e.PinH.notna().mean():.0%}, arbitro: {e.Referee.notna().mean():.0%}")


if __name__ == "__main__":
    main()
