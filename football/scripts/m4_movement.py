"""Movimento delle quote come segnale (punto 14.11): verifica sul passato (anni di verifica 2022-2026).

Per le giocate del backtest (regole fisse, quota migliore pre-partita) confronta Pinnacle 'prima' (PSH, raccolta
giorni prima) e Pinnacle chiusura (PSCH): il mercato si è mosso A FAVORE (probabilità implicita salita) o CONTRO.
Se le giocate 'contro' rendono molto peggio, il movimento è un filtro trappole utile.
Scrive football/output/m4_movimento.md.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fb.data import ROOT, matches  # noqa: E402
from m4_money import RULES, backtest, devig, load  # noqa: E402

COLS = {"1": ("PinH", "PinCH"), "X": ("PinD", "PinCD"), "2": ("PinA", "PinCA"), "O": ("PinO25", "PinCO25"),
        "U": ("PinU25", "PinCU25")}


def main():
    P, O = load()
    m = matches().loc[P.index]
    odds = pd.DataFrame({"1": m.MaxHome, "X": m.MaxDraw, "2": m.MaxAway, "O": m.MaxOver25, "U": m.MaxUnder25})
    g = backtest(P, O, odds.apply(pd.to_numeric, errors="coerce"))
    pre = {**devig(m[["PinH", "PinD", "PinA"]].apply(pd.to_numeric, errors="coerce")).set_axis(list("1X2"), axis=1),
           **devig(m[["PinO25", "PinU25"]].apply(pd.to_numeric, errors="coerce")).set_axis(["O", "U"], axis=1)}
    clo = {**devig(m[["PinCH", "PinCD", "PinCA"]].apply(pd.to_numeric, errors="coerce")).set_axis(list("1X2"), axis=1),
           **devig(m[["PinCO25", "PinCU25"]].apply(pd.to_numeric, errors="coerce")).set_axis(["O", "U"], axis=1)}
    g["mov"] = [clo[s].get(i, np.nan) - pre[s].get(i, np.nan) for i, s in zip(g.mid, g.sel)]
    g = g.dropna(subset=["mov"])
    g["dir"] = np.where(g.mov > 0.01, "a favore", np.where(g.mov < -0.01, "contro", "fermo"))
    rep = ["# Movimento delle quote Pinnacle (prima -> chiusura) sulle giocate del backtest", "",
           "Quota usata: la migliore pre-partita. 'a favore' = la probabilità di Pinnacle sulla nostra giocata è salita "
           "di oltre 1 punto prima del via; 'contro' = scesa.", "",
           "| movimento | giocate | vinte | ROI |", "|---|---|---|---|"]
    for d in ("a favore", "fermo", "contro"):
        s = g[g.dir == d]
        if len(s):
            rep.append(f"| {d} | {len(s)} | {s.win.mean():.1%} | {s.pl.mean():+.1%} |")
    for lvl in RULES:
        s = g[g.lvl == lvl]
        if len(s):
            rep.append(f"| ({lvl}) contro | {(s.dir == 'contro').sum()} | {s[s.dir == 'contro'].win.mean():.1%} | "
                       f"{s[s.dir == 'contro'].pl.mean():+.1%} |")
    (ROOT / "output" / "m4_movimento.md").write_text("\n".join(rep) + "\n")
    print("\n".join(rep))


if __name__ == "__main__":
    main()
