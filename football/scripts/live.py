"""Live delle partite in corso analizzate oggi (punto 7 del piano). Uso: python football/scripts/live.py
Per ogni partita del registro di oggi già iniziata: minuto, punteggio, statistiche e probabilità sul tempo che resta
(fb.live; NON verificato sul passato). Costo: 1 richiesta per partita (dettaglio con statistiche)."""
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fb import apifootball as af  # noqa: E402
from fb import registro  # noqa: E402
from scripts.analizza import LIVE, live_mode  # noqa: E402
from fb.teams import resolve  # noqa: E402


def main():
    day = str(date.today())
    r = registro.load()
    ids = set(r.fixture_id[(r.data == day) & (r.fixture_id != "")])
    tm = af.load_team_map()
    for f in af.fixtures(day):
        if str(f["id"]) in ids and f["stato"] in LIVE:
            f["home"] = resolve(f["home_id"], f["home_api"], f["div"], tm)
            f["away"] = resolve(f["away_id"], f["away_api"], f["div"], tm)
            print(f"\n# {f['home_api']} - {f['away_api']}")
            for _, g in r[(r.fixture_id == str(f["id"]))].iterrows():
                print(f"giocata pre-partita: {g.giocata} @{g.quota}")
            live_mode(f)


if __name__ == "__main__":
    main()
