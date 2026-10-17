"""Registro delle giocate e bilancio reale (Fase M6, punto 8 del piano). 1 unità a giocata.

Colonne: chiave unica = fixture_id + giocata. esito: VINTA / PERSA / RIMBORSO / MEZZA (linee a quarti; vuoto = da verificare).
"""
import numpy as np
import pandas as pd

from .data import ROOT

PATH = ROOT / "output" / "registro_giocate.csv"
COLS = ["data", "ora", "campionato", "fixture_id", "partita", "mercato", "giocata", "tipo", "livello", "quota",
        "bookmaker", "quota_pinnacle", "prob_modello", "valore", "bet_id", "valore_api", "esito", "utile",
        "quota_chiusura_pin", "note"]


def load():
    if not PATH.exists():
        return pd.DataFrame(columns=COLS)
    r = pd.read_csv(PATH, dtype=str).fillna("")
    for c in COLS:
        if c not in r:
            r[c] = ""
    return r[COLS]


def save(r):
    r[COLS].to_csv(PATH, index=False)


def add(rows):
    """Aggiunge giocate nuove (dict con le COLS); non duplica la stessa giocata sulla stessa partita."""
    r = load()
    have = set(zip(r.fixture_id, r.giocata))
    new = [x for x in rows if (str(x["fixture_id"]), x["giocata"]) not in have]
    if new:
        r = pd.concat([r, pd.DataFrame(new).astype(str)], ignore_index=True)
        save(r)
    return len(new)


def settle(r, i, esito):
    q = float(r.at[i, "quota"])
    r.at[i, "esito"] = esito
    r.at[i, "utile"] = f"{(q - 1) if esito == 'VINTA' else 0.0 if esito == 'RIMBORSO' else -1.0:+.2f}"


def summary(r=None):
    """Bilancio a 1 unità: totale e per mercato, livello, campionato, fascia di valore."""
    r = load() if r is None else r
    s = r[r.esito.isin(["VINTA", "PERSA", "RIMBORSO", "MEZZA"])].copy()
    if s.empty:
        return "Nessuna giocata chiusa nel registro."
    q = pd.to_numeric(s.quota, errors="coerce")
    calc = np.where(s.esito == "VINTA", q - 1, np.where(s.esito == "PERSA", -1.0, 0.0))
    s["utile"] = pd.to_numeric(s.utile, errors="coerce").fillna(pd.Series(calc, index=s.index))
    for c in ("mercato", "livello", "campionato", "tipo"):
        s[c] = s[c].replace("", "n.d.")
    s["v"] = pd.to_numeric(s.valore, errors="coerce")
    s["fascia"] = pd.cut(s.v, [-1, 0.05, 0.08, 0.15, 1], labels=["<5%", "5-8%", "8-15%", ">15%"])
    s["fascia_p"] = pd.cut(pd.to_numeric(s.prob_modello, errors="coerce"), [0, 0.70, 0.75, 0.80, 1.01],
                           labels=["<70%", "70-75%", "75-80%", ">=80%"], right=False)
    lines = [f"**Totale**: {len(s)} giocate, vinte {(s.esito == 'VINTA').mean():.0%}, "
             f"utile {s.utile.sum():+.2f} u, ROI {s.utile.mean():+.1%}"]
    for col, name in (("mercato", "mercato"), ("livello", "livello"), ("campionato", "campionato"),
                      ("fascia", "fascia di valore"), ("fascia_p", "fascia di probabilità"), ("tipo", "tipo")):
        s["vinta"] = (s.esito == "VINTA").astype(float)
        s["q"] = pd.to_numeric(s.quota, errors="coerce")
        g = s.groupby(col, observed=True).agg(n=("utile", "size"), u=("utile", "sum"), roi=("utile", "mean"),
                                              vinte=("vinta", "mean"), qm=("q", "mean"))
        g = g[g["n"] > 0]
        if len(g):
            lines.append(f"\nPer {name}: " + "; ".join(
                f"{k}: {int(v['n'])} giocate, vinte {v['vinte']:.0%}, ROI {v['roi']:+.0%}, quota media {v['qm']:.2f}"
                for k, v in g.iterrows()))
    return "\n".join(lines)
