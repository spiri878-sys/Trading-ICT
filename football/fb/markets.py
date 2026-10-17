"""Mercati (Fase M3): ogni giocata diventa una maschera sulla griglia congiunta (casa x, ospite y) della statistica.

Una selezione è un dict {stat, kind, ...}. win(x, y) e push(x, y) sono pesi in [0, 1] (le linee asiatiche a quarti
dividono la puntata a metà). Valore atteso per 1 unità: P(vinta) * quota + P(rimborso) - 1.
Mercati che servono i due tempi insieme (parziale/finale, vince entrambi i tempi...) usano la griglia 4D
(gol 1° tempo x 2° tempo), con kind che inizia per "hh_".
"""
import numpy as np

# id mercato API -> (statistica, tipo). Statistiche: g gol, ght 1° tempo, g2h 2° tempo, cor angoli, crd cartellini
# (giallo 1, rosso 2), yel gialli, fou falli, sh tiri, sot tiri in porta, hh = due tempi insieme.
API_BETS = {
    1: ("g", "1x2"), 2: ("g", "dnb"), 3: ("g2h", "1x2"), 4: ("g", "ah"), 5: ("g", "ou_tot"), 6: ("ght", "ou_tot"),
    7: ("hh", "hh_htft"), 8: ("g", "btts"), 9: ("g", "eh"), 10: ("g", "cs"), 11: ("hh", "hh_highest"),
    12: ("g", "dc"), 13: ("ght", "1x2"), 16: ("g", "ou_home"), 17: ("g", "ou_away"), 18: ("ght", "eh"),
    19: ("ght", "ah"), 20: ("ght", "dc"), 21: ("g", "oe_tot"), 22: ("ght", "oe_tot"), 23: ("g", "oe_home"),
    24: ("g", "res_btts"), 25: ("g", "res_tot"), 26: ("g2h", "ou_tot"), 27: ("g", "clean_home"),
    28: ("g", "clean_away"), 29: ("g", "nil_home"), 30: ("g", "nil_away"), 31: ("ght", "cs"),
    32: ("hh", "hh_winboth"), 33: ("g2h", "dc"), 34: ("ght", "btts"), 35: ("g2h", "btts"), 36: ("g", "nil"),
    37: ("hh", "hh_winboth_home"), 38: ("g", "exact_tot"), 39: ("hh", "hh_wineither"), 40: ("g", "exact_home"),
    41: ("g", "exact_away"), 42: ("g2h", "exact_tot"), 43: ("g", "scores_home"), 44: ("g", "scores_away"),
    46: ("ght", "exact_tot"), 48: ("hh", "hh_teamboth"), 49: ("g", "tot_btts"), 50: ("g", "ou_tot"),
    53: ("hh", "hh_winboth_away"), 60: ("g", "oe_away"), 62: ("g2h", "cs"), 63: ("g2h", "oe_tot"),
    72: ("ght", "ou_tot"), 105: ("ght", "ou_home"), 106: ("ght", "ou_away"), 107: ("g2h", "ou_home"),
    108: ("g2h", "ou_away"), 110: ("g", "scoring_draw"), 111: ("hh", "hh_teamboth_home"),
    112: ("hh", "hh_teamboth_away"), 113: ("hh", "hh_bttsboth"), 114: ("ght", "scores_home"),
    115: ("g2h", "scores_home"), 116: ("ght", "scores_away"), 117: ("g2h", "scores_away"), 184: ("hh", "hh_anyboth"),
    349: ("g", "range_tot"), 104: ("g2h", "ah"), 181: ("g2h", "eh"),
    45: ("cor", "ou_tot"), 57: ("cor", "ou_home"), 58: ("cor", "ou_away"), 55: ("cor", "1x2"), 56: ("cor", "ah"),
    239: ("cor", "eh"), 85: ("cor", "three_tot"), 295: ("cor", "range_tot"), 338: ("cor", "oe_tot"), 339: ("cor", "dc"),
    80: ("crd", "ou_tot"), 82: ("crd", "ou_home"), 83: ("crd", "ou_away"), 79: ("crd", "eh"), 81: ("crd", "ah"),
    153: ("yel", "ou_tot"), 150: ("yel", "ou_home"), 151: ("yel", "ou_away"), 152: ("yel", "ah"), 154: ("yel", "dc"),
    157: ("yel", "oe_tot"), 158: ("yel", "1x2"),
    173: ("fou", "ou_tot"), 171: ("fou", "ou_home"), 170: ("fou", "ou_away"), 175: ("fou", "1x2"), 174: ("fou", "ah"),
    172: ("fou", "dc"), 343: ("fou", "oe_tot"),
    211: ("sh", "ou_tot"), 340: ("sh", "1x2"), 87: ("sot", "ou_tot"), 176: ("sot", "1x2"), 177: ("sot", "ah"),
}
OUT3 = {"Home": "H", "Draw": "D", "Away": "A", "1": "H", "X": "D", "2": "A"}


def _num(s):
    return float(str(s).replace(",", ".").strip())


def parse(kind, value):
    """Valore API (es. 'Over 2.5', 'Home -1', 'Draw/Away') -> parametri della selezione, None se non gestito."""
    v = str(value).strip()
    try:
        if kind.startswith("ou_") or kind == "three_tot":
            side, line = v.split()[:2]
            if side not in ("Over", "Under", "Exactly"):
                return None
            return {"side": side.lower(), "line": _num(line)}
        if kind == "1x2":
            return {"o": OUT3[v]} if v in OUT3 else None
        if kind == "dnb":
            return {"o": OUT3[v]} if v in ("Home", "Away") else None
        if kind == "dc":
            a, b = v.split("/")
            return {"o": OUT3[a] + OUT3[b]}
        if kind in ("ah", "eh"):
            who, h = v.split()
            return {"o": OUT3[who], "h": _num(h)}
        if kind in ("btts", "scoring_draw") or kind.startswith(("clean_", "nil_", "scores_")) or \
                kind in ("hh_winboth_home", "hh_winboth_away", "hh_teamboth_home", "hh_teamboth_away",
                         "hh_bttsboth", "hh_anyboth"):
            return {"yes": v == "Yes"} if v in ("Yes", "No") else None
        if kind.startswith("oe_"):
            return {"odd": v == "Odd"} if v in ("Odd", "Even") else None
        if kind == "cs":
            a, b = v.split(":")
            return {"x": int(a), "y": int(b)}
        if kind.startswith("exact_"):
            return {"n": int(v.split()[-1]), "plus": True} if v.startswith("more") else {"n": int(v), "plus": False}
        if kind == "range_tot":
            if " or " in v:                               # '2 or 3 goals'
                a, b = v.replace("goals", "").split(" or ")
                return {"lo": int(a), "hi": int(b)}
            if " - " in v:
                a, b = v.split(" - ")
                return {"lo": int(a), "hi": int(b)}
            w = v.replace("goals", "").split()
            n = int(w[1])
            return {"lo": 0, "hi": n - 1} if w[0] == "Under" else {"lo": n + 1, "hi": 999}
        if kind == "res_btts":
            a, b = v.split("/")
            return {"o": OUT3[a], "yes": b == "Yes"}
        if kind == "res_tot":
            a, b = v.split("/")
            side, line = b.split()
            return {"o": OUT3[a], "side": side.lower(), "line": _num(line)}
        if kind == "tot_btts":                            # 'o/yes 2.5'
            a, line = v.split()
            s, y = a.split("/")
            return {"side": "over" if s == "o" else "under", "yes": y == "yes", "line": _num(line)}
        if kind == "nil":
            return {"o": OUT3[v]} if v in ("Home", "Away") else None
        if kind in ("hh_winboth", "hh_wineither", "hh_teamboth"):
            return {"o": OUT3[v]} if v in ("Home", "Away") else None
        if kind == "hh_htft":
            a, b = v.split("/")
            return {"o": OUT3[a], "o2": OUT3[b]}
        if kind == "hh_highest":
            return {"o": {"1st Half": 1, "2nd Half": 2, "Draw": 0, "Equal": 0}[v]}
    except (ValueError, KeyError, IndexError):
        return None
    return None


def _line(a, line, side, push_ok=True):
    """Peso vincita/rimborso per 'a vs line' con linee .5, intere (rimborso) e a quarti (metà e metà)."""
    if abs(line * 4 - round(line * 4)) < 1e-9 and round(line * 4) % 2 == 1:   # x.25 / x.75
        w1, p1 = _line(a, line - 0.25, side)
        w2, p2 = _line(a, line + 0.25, side)
        return (w1 + w2) / 2, (p1 + p2) / 2
    win = (a > line) if side == "over" else (a < line)
    push = (a == line) if push_ok else np.zeros_like(win)
    return win.astype(float), push.astype(float)


def masks(sel, K):
    """Maschere (win, push) di forma (K+1, K+1) per le selezioni a griglia 2D."""
    x, y = np.meshgrid(np.arange(K + 1), np.arange(K + 1), indexing="ij")
    t, k = x + y, sel["kind"]
    z = np.zeros((K + 1, K + 1))
    res = np.where(x > y, "H", np.where(x == y, "D", "A"))
    if k.startswith("ou_"):
        a = {"ou_tot": t, "ou_home": x, "ou_away": y}[k]
        return _line(a, sel["line"], sel["side"])
    if k == "three_tot":
        if sel["side"] == "exactly":
            return (t == sel["line"]).astype(float), z
        return _line(t, sel["line"], sel["side"], push_ok=False)
    if k == "1x2":
        return (res == sel["o"]).astype(float), z
    if k == "dc":
        return np.isin(res, list(sel["o"])).astype(float), z
    if k == "dnb":
        return (res == sel["o"]).astype(float), (res == "D").astype(float)
    if k == "ah":
        diff = (x - y) if sel["o"] == "H" else (y - x)
        return _line(diff, -sel["h"], "over")             # vince se diff + h > 0 (linee a quarti divise)
    if k == "eh":                                         # handicap europeo sul totale della squadra di casa
        d = x + sel["h"] - y
        r = np.where(d > 0, "H", np.where(d == 0, "D", "A"))
        return (r == sel["o"]).astype(float), z
    if k.startswith("oe_"):
        a = {"oe_tot": t, "oe_home": x, "oe_away": y}[k]
        return ((a % 2 == 1) == sel["odd"]).astype(float), z
    if k == "cs":
        return ((x == sel["x"]) & (y == sel["y"])).astype(float), z
    if k.startswith("exact_"):
        a = {"exact_tot": t, "exact_home": x, "exact_away": y}[k]
        return ((a >= sel["n"]) if sel["plus"] else (a == sel["n"])).astype(float), z
    if k == "range_tot":
        return ((t >= sel["lo"]) & (t <= sel["hi"])).astype(float), z
    if k == "btts":
        return (((x > 0) & (y > 0)) == sel["yes"]).astype(float), z
    if k == "scoring_draw":
        return (((x == y) & (x > 0)) == sel["yes"]).astype(float), z
    if k.startswith("clean_"):
        opp = y if k == "clean_home" else x
        return ((opp == 0) == sel["yes"]).astype(float), z
    if k.startswith("nil_") or k == "nil":
        side = {"nil_home": "H", "nil_away": "A"}.get(k, sel.get("o"))
        ev = (x > y) & (y == 0) if side == "H" else (y > x) & (x == 0)
        return (ev == sel.get("yes", True)).astype(float), z
    if k.startswith("scores_"):
        a = x if k == "scores_home" else y
        return ((a > 0) == sel["yes"]).astype(float), z
    if k == "res_btts":
        return ((res == sel["o"]) & (((x > 0) & (y > 0)) == sel["yes"])).astype(float), z
    if k == "res_tot":
        w, _ = _line(t, sel["line"], sel["side"], push_ok=False)
        return ((res == sel["o"]) & (w > 0)).astype(float), z
    if k == "tot_btts":
        w, _ = _line(t, sel["line"], sel["side"], push_ok=False)
        return ((w > 0) & (((x > 0) & (y > 0)) == sel["yes"])).astype(float), z
    raise ValueError(k)


def masks_hh(sel, K):
    """Maschere 4D (x1, y1, x2, y2): gol casa/ospite nel 1° e nel 2° tempo."""
    x1, y1, x2, y2 = np.meshgrid(*[np.arange(K + 1)] * 4, indexing="ij")
    X, Y = x1 + x2, y1 + y2
    k = sel["kind"]
    z = np.zeros(X.shape)

    def r(a, b):
        return np.where(a > b, "H", np.where(a == b, "D", "A"))
    yes = sel.get("yes", True)
    if k == "hh_htft":
        ev = (r(x1, y1) == sel["o"]) & (r(X, Y) == sel["o2"])
    elif k == "hh_highest":
        g1, g2 = x1 + y1, x2 + y2
        ev = np.where(g1 > g2, 1, np.where(g1 < g2, 2, 0)) == sel["o"]
    elif k in ("hh_winboth", "hh_winboth_home", "hh_winboth_away"):
        o = sel.get("o") or ("H" if k.endswith("home") else "A")
        ev = ((r(x1, y1) == o) & (r(x2, y2) == o)) == (yes if "o" not in sel else True)
    elif k == "hh_wineither":
        ev = (r(x1, y1) == sel["o"]) | (r(x2, y2) == sel["o"])
    elif k in ("hh_teamboth", "hh_teamboth_home", "hh_teamboth_away"):
        o = sel.get("o") or ("H" if k.endswith("home") else "A")
        ev = (((x1 > 0) & (x2 > 0)) if o == "H" else ((y1 > 0) & (y2 > 0))) == (yes if "o" not in sel else True)
    elif k == "hh_bttsboth":
        ev = ((x1 > 0) & (y1 > 0) & (x2 > 0) & (y2 > 0)) == yes
    elif k == "hh_anyboth":
        ev = ((x1 + y1 > 0) & (x2 + y2 > 0)) == yes
    else:
        raise ValueError(k)
    return ev.astype(float), z


def prob(M, sel):
    """M: (n, K+1, K+1) griglia congiunta, oppure (n, K+1, K+1, K+1, K+1) per i due tempi.
    Restituisce (p_vinta, p_rimborso) per ogni partita."""
    K = M.shape[1] - 1
    W, P = masks_hh(sel, K) if sel["kind"].startswith("hh_") else masks(sel, K)
    n = M.shape[0]
    flat = M.reshape(n, -1)
    return flat @ W.ravel(), flat @ P.ravel()
