"""Controllo qualità dell'archivio: doppioni, buchi di date, valori assurdi. Scrive output/f0_check.md.

Uso: python football/scripts/f0_check.py [--fix]   (--fix toglie doppioni e azzera i valori assurdi nel CSV)
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fb.data import RAW, ROOT  # noqa: E402

# limiti plausibili per partita, per squadra (oltre = errore di fonte)
LIMITS = {"FTHome": 13, "HTHome": 9, "HomeShots": 50, "HomeTarget": 25, "HomeFouls": 40, "HomeCorners": 25,
          "HomeYellow": 10, "HomeRed": 4}


def main(fix=False):
    path = RAW / "Matches.csv"
    m = pd.read_csv(path, low_memory=False)
    txt = {"Division", "MatchDate", "MatchTime", "HomeTeam", "AwayTeam", "FTResult", "HTResult"}
    for c in m.columns:
        if c not in txt and m[c].dtype == object or str(m[c].dtype) == "str" and c not in txt:
            m[c] = pd.to_numeric(m[c], errors="coerce")       # es. "x" al posto di una quota
    rep = ["# Controllo archivio", "", f"Partite: {len(m)}, dal {m.MatchDate.min()} al {m.MatchDate.max()}", ""]

    dup = m.duplicated(["Division", "MatchDate", "HomeTeam", "AwayTeam"], keep="last")
    rep.append(f"- Doppioni (stesso campionato, data, squadre): {dup.sum()}")
    bad = pd.Series(False, index=m.index)
    for c, lim in LIMITS.items():
        for col in (c, c.replace("Home", "Away")):
            b = (m[col] < 0) | (m[col] > lim)
            if b.any():
                rep.append(f"- {col}: {b.sum()} valori fuori da 0-{lim} (azzerati con --fix)")
                if fix:
                    m.loc[b, col] = np.nan
            bad |= b
    ht = (m.HTHome > m.FTHome) | (m.HTAway > m.FTAway)
    rep.append(f"- Gol 1° tempo > gol finali: {ht.sum()}")
    sot = (m.HomeTarget > m.HomeShots) | (m.AwayTarget > m.AwayShots)
    rep.append(f"- Tiri in porta > tiri: {sot.sum()}")
    odd = (m.OddHome < 1.01) | (m.OddDraw < 1.01) | (m.OddAway < 1.01)
    rep.append(f"- Quote 1X2 < 1.01: {odd.sum()}")
    if fix:
        m.loc[ht, ["HTHome", "HTAway", "HTResult"]] = np.nan
        m.loc[sot, ["HomeShots", "AwayShots", "HomeTarget", "AwayTarget"]] = np.nan
        m.loc[odd, ["OddHome", "OddDraw", "OddAway"]] = np.nan

    rep += ["", "## Buchi di date (pause > 120 giorni dentro una stagione attiva) e ultima partita", "",
            "| campionato | partite | ultima | buchi |", "|---|---|---|---|"]
    d = pd.to_datetime(m.MatchDate)
    for div, g in d.groupby(m.Division):
        g = g.sort_values()
        gaps = g.diff().dt.days
        big = g[gaps > 120]
        rep.append(f"| {div} | {len(g)} | {g.max():%Y-%m-%d} | "
                   f"{', '.join(f'{x:%Y-%m}' for x in big[big.dt.year >= 2015]) or '-'} |")

    if fix:
        m = m[~dup]
        m.to_csv(path, index=False)
        rep.append(f"\nCorretto: tolti {dup.sum()} doppioni.")
    out = ROOT / "output" / "f0_check.md"
    out.write_text("\n".join(rep) + "\n")
    print("\n".join(rep[:16]))


if __name__ == "__main__":
    main("--fix" in sys.argv)
