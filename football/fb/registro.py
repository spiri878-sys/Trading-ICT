"""Registro delle giocate e bilancio reale (Fase M6, punto 8 del piano). 1 unità a giocata.

Colonne: chiave unica = fixture_id + giocata. esito: VINTA / PERSA / RIMBORSO / MEZZA (linee a quarti; vuoto = da verificare).
"""
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
    s["utile"] = s.utile.astype(float)
    for c in ("mercato", "livello", "campionato", "tipo"):
        s[c] = s[c].replace("", "n.d.")
    s["v"] = pd.to_numeric(s.valore, errors="coerce")
    s["fascia"] = pd.cut(s.v, [-1, 0.05, 0.08, 0.15, 1], labels=["<5%", "5-8%", "8-15%", ">15%"])
    lines = [f"**Totale**: {len(s)} giocate, vinte {(s.esito == 'VINTA').mean():.0%}, "
             f"utile {s.utile.sum():+.2f} u, ROI {s.utile.mean():+.1%}"]
    for col, name in (("mercato", "mercato"), ("livello", "livello"), ("campionato", "campionato"),
                      ("fascia", "fascia di valore"), ("tipo", "tipo")):
        g = s.groupby(col, observed=True).utile.agg(["size", "sum", "mean"])
        g = g[g["size"] > 0]
        if len(g):
            lines.append(f"\nPer {name}: " + "; ".join(f"{k} {int(v['size'])} giocate {v['sum']:+.2f} u"
                                                      for k, v in g.iterrows()))
    return "\n".join(lines)
