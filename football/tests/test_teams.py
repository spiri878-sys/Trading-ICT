"""Corrispondenza nomi squadra: casi noti, compresi quelli pericolosi (squadre con nome simile)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fb.teams import resolve  # noqa: E402

CASES = [("ARG", "Gimnasia M.", "Gimnasia Mendoza"), ("ARG", "Gimnasia L.P.", "Gimnasia L.P."),
         ("E0", "Manchester City", "Man City"), ("E0", "Manchester United", "Man United"),
         ("SP1", "Atletico Madrid", "Ath Madrid"), ("SP1", "Athletic Club", "Ath Bilbao"),
         ("D1", "Bayern München", "Bayern Munich"), ("E2", "Sheffield Wednesday", "Sheffield Weds"),
         ("JAP", "Kyoto Sanga", "Kyoto"), ("I1", "AS Roma", "Roma"), ("I1", "Inter", "Inter")]


def test_known_names():
    for i, (div, api, want) in enumerate(CASES):
        assert resolve(-1000 - i, api, div, tm={}, save=False) == want, (api, want)
