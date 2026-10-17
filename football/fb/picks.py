"""Regole di scelta delle giocate e testo in italiano (Fase M5, punto 5 del piano)."""
import json

import numpy as np

from .data import ROOT

RULES = {"SUPER CECCHINO": (0.80, 0.05), "CECCHINO": (0.70, 0.05), "VALORE": (0.55, 0.08)}   # in ordine
STRICT = 0.02                 # mercati senza quote storiche ("profitto non provato"): soglie più severe
PROVEN = {"g|1x2|H", "g|1x2|D", "g|1x2|A", "g|ou_tot|over", "g|ou_tot|under"}
MINQ, MAXV, MAX_PIN_GAP, MIN_TEAM_N = 1.30, 0.25, 0.10, 15
STAT_IT = {"g": "gol", "ght": "gol 1° tempo", "g2h": "gol 2° tempo", "cor": "angoli", "crd": "cartellini",
           "yel": "gialli", "fou": "falli", "sh": "tiri", "sot": "tiri in porta", "hh": "gol (due tempi)"}
GROUP = {"cor": "ANGOLI", "g": "GOL / 1X2", "ght": "GOL / 1X2", "g2h": "GOL / 1X2", "hh": "GOL / 1X2",
         "crd": "CARTELLINI", "yel": "CARTELLINI", "fou": "FALLI", "sh": "TIRI", "sot": "TIRI"}


def pinnacle_fair(quotes, q):
    """Probabilità senza margine di Pinnacle per la stessa giocata (stesso mercato e stessa linea)."""
    if not q.get("pin"):
        return None
    w = q["value"].split()
    hcp = q["bet_id"] in (4, 19, 56, 81, 152, 174, 177, 104, 9, 239, 79, 18, 181)   # handicap: gruppo = stesso numero
    line = w[-1] if w[0] in ("Over", "Under") or (hcp and len(w) == 2) else None
    same = [x for x in quotes if x["bet_id"] == q["bet_id"] and x.get("pin")
            and (line is None or x["value"].split()[-1] == line)]
    if line is None and q["bet_id"] not in (1, 8, 21, 55, 158, 175, 176, 340):
        return None                            # mercati dove non si sa ricostruire il gruppo completo
    s = sum(1 / x["pin"] for x in same)
    return (1 / q["pin"]) / s if s > 1.0 else None


def money_ok(bookmaker):
    """Mercati con quote storiche (1X2, O/U 2.5): ammessi solo se il backtest al bookmaker dell'utente è in utile."""
    fn = ROOT / "models" / "m4_money.json"
    if not fn.exists():
        return False
    return json.loads(fn.read_text()).get(bookmaker, {}).get("roi", -1) > 0


def level(e, q, fair, counts_ok):
    """Livello della giocata o motivo dello scarto."""
    if not e["ammesso"]:
        return None, "mercato non ammesso"
    if e["famiglia"] in PROVEN and not money_ok(q["bm"]):
        return None, f"backtest in perdita alle quote {q['bm']}"
    if not counts_ok:
        return None, "pochi dati sulla squadra"
    if q["best"] < MINQ:
        return None, "quota < 1.30"
    if e["valore"] > MAXV:
        return "SOSPETTO", "valore > 25%"
    if fair is not None and abs(e["p"] - fair) > MAX_PIN_GAP:
        return "SOSPETTO", f"lontano da Pinnacle ({fair:.0%})"
    extra = 0 if e["famiglia"] in PROVEN else STRICT
    for lvl, (pmin, vmin) in RULES.items():
        if e["p"] >= pmin + extra and e["valore"] >= vmin + extra:
            return lvl, ""
    return None, "senza valore"


def describe(stat, sel, home, away):
    """Giocata in parole semplici."""
    k, o = sel["kind"], sel.get("o")
    who = {"H": home, "A": away, "D": "pareggio"}
    s = STAT_IT[stat]
    if k.startswith("ou_"):
        side = "Over" if sel["side"] == "over" else "Under"
        tgt = {"ou_tot": "", "ou_home": f"{home} ", "ou_away": f"{away} "}[k]
        return f"{tgt}{side} {sel['line']:g} {s}"
    if k == "1x2":
        return f"{'1' if o == 'H' else 'X' if o == 'D' else '2'} ({who[o]}) {s if stat != 'g' else ''}".strip()
    if k == "dc":
        return f"doppia chance {o.replace('H', '1').replace('D', 'X').replace('A', '2')} {s if stat != 'g' else ''}".strip()
    if k == "dnb":
        return f"{who[o]} draw no bet {s if stat != 'g' else ''}".strip()
    if k == "ah":
        return f"{who[o]} handicap asiatico {sel['h']:+g} {s}"
    if k == "eh":
        return f"handicap europeo casa {sel['h']:+g}: {who[o]} {s}"
    if k == "btts":
        return f"{'Gol' if sel['yes'] else 'NoGol'}{'' if stat == 'g' else ' ' + s}"
    if k.startswith("oe_"):
        return f"{'dispari' if sel['odd'] else 'pari'} {s}"
    if k == "range_tot":
        return f"multi{s} {sel['lo']}-{sel['hi'] if sel['hi'] < 99 else '+'}"
    if k == "exact_tot":
        return f"esattamente {sel['n']}{'+' if sel['plus'] else ''} {s}"
    return f"{s}: {k} " + " ".join(f"{a}={b}" for a, b in sel.items() if a != "kind")


def reasons(stat, sel, x, home, away, mu):
    """2-3 motivi chiave dalle feature (medie recenti, avversario, arbitro)."""
    out = []
    base = {"crd": "yel"}.get(stat, stat)
    if base in ("g", "ght", "g2h"):
        base = "g"
    lh, la = x.get(f"lg_h_{base}"), x.get(f"lg_a_{base}")
    mh, ma = mu
    side = sel["kind"]
    if base not in ("hh",) and lh == lh and lh:
        hf, aa = x.get(f"h_{base}_vf"), x.get(f"a_{base}_va")
        af, ha = x.get(f"a_{base}_vf"), x.get(f"h_{base}_va")
        nm = STAT_IT.get(base, base)
        if side in ("ou_home", "1x2", "ah", "dnb", "eh", "dc") or side == "ou_tot":
            out.append(f"{home} in casa fa {hf:.1f} {nm} di media (campionato {lh:.1f}), {away} fuori ne concede {aa:.1f}")
        if side in ("ou_away", "1x2", "ah", "dnb", "eh", "dc") or side == "ou_tot":
            out.append(f"{away} fuori fa {af:.1f} {nm} (campionato {la:.1f}), {home} in casa ne concede {ha:.1f}")
    out.append(f"attesi: {home} {mh:.2f}, {away} {ma:.2f} (totale {mh + ma:.2f})")
    ry = x.get("ref_yel")
    if stat in ("crd", "yel", "fou") and ry == ry and ry is not None:
        out.append(f"arbitro: {ry:.1f} gialli a partita nelle sue gare recenti")
    return out[:3]


def confidence(lvl, fam, nbooks):
    if "CECCHINO" in lvl and fam in PROVEN and nbooks >= 4:
        return "alta"
    if "CECCHINO" in lvl or (fam in PROVEN and nbooks >= 4):
        return "media"
    return "bassa"


def min_odds(p, push=0.0):
    """Quota sotto la quale non c'è almeno il 5% di valore (con il rimborso delle linee intere / a quarti)."""
    return (1.05 - push) / max(p, 1e-6)


def fmt_pct(x):
    return "-" if x is None or (isinstance(x, float) and np.isnan(x)) else f"{x:.0%}"
