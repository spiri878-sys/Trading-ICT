"""Dati partite (Fase F0). Sorgente: github.com/xgabora/Club-Football-Match-Data (Football-Data.co.uk + ClubElo).

Regole anti-futuro:
* le colonne di cluster C_* sono stimate a posteriori sull'intero archivio -> ESCLUSE;
* Elo e Form sono valori PRIMA della partita (dichiarato dalla fonte) -> utilizzabili;
* le quote sono quelle pre-partita (Bet365 e massimo di mercato) -> utilizzabili solo come prezzo di mercato.
"""
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
CACHE = ROOT / "data" / "cache"

COUNTRY = {"E0": "ENG", "E1": "ENG", "E2": "ENG", "E3": "ENG", "EC": "ENG", "SC0": "SCO", "SC1": "SCO",
           "SC2": "SCO", "SC3": "SCO", "D1": "GER", "D2": "GER", "I1": "ITA", "I2": "ITA", "SP1": "ESP",
           "SP2": "ESP", "F1": "FRA", "F2": "FRA", "N1": "NED", "B1": "BEL", "P1": "POR", "T1": "TUR", "G1": "GRE"}


@lru_cache(maxsize=1)
def matches() -> pd.DataFrame:
    m = pd.read_csv(RAW / "Matches.csv", low_memory=False)
    m["date"] = pd.to_datetime(m.MatchDate)
    m = m[[c for c in m.columns if not c.startswith("C_")]]
    m = m.dropna(subset=["FTHome", "FTAway"]).copy()
    m["season"] = np.where(m.date.dt.month >= 7, m.date.dt.year, m.date.dt.year - 1)
    # stagioni a anno solare (campionati estivi): la stagione è l'anno
    solar = ~m.Division.isin(list(COUNTRY))
    m.loc[solar, "season"] = m.loc[solar, "date"].dt.year
    m["country"] = m.Division.map(COUNTRY).fillna(m.Division)
    m["hg"], m["ag"] = m.FTHome.astype(int), m.FTAway.astype(int)
    m = m.sort_values(["date", "Division", "HomeTeam"]).reset_index(drop=True)
    m["mid"] = np.arange(len(m))
    return m


def implied(odds: pd.DataFrame) -> pd.DataFrame:
    """Probabilità implicite normalizzate (margine tolto in proporzione)."""
    inv = 1.0 / odds
    return inv.div(inv.sum(axis=1), axis=0)
