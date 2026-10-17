"""Scheda partita a 360 gradi.

usage:
  python football/scripts/scheda.py "Inter" "Milan" I1 2026-10-20 [1=2.10 X=3.40 2=3.60 over25=1.85 under25=1.95]
      [ang_o9.5=1.85 ang_u9.5=1.95 casa_o4.5=1.80 casa_u4.5=2.00 osp_o3.5=1.90 osp_u3.5=1.90 gialli_o4.5=2.0]
  python football/scripts/scheda.py --squadre I1        (elenco dei nomi delle squadre del campionato)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fb.card import predict_fixtures, render, team_names  # noqa: E402

if sys.argv[1] == "--squadre":
    print("\n".join(team_names(sys.argv[2] if len(sys.argv) > 2 else None)))
    sys.exit()
home, away, div, date = sys.argv[1:5]
odds = {}
for kv in sys.argv[5:]:
    k, v = kv.split("=")
    odds[k] = float(v)
res = predict_fixtures([dict(home=home, away=away, div=div, date=date, odds=odds)])
print(render(res[0]))
