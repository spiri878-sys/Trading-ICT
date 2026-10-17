"""Cancello di qualità (Fase M4): griglie congiunte, selezioni da verificare, calibrazione e metriche.

Divisione degli anni (finestre luglio-giugno): SCELTA 2019-2021 (approccio, dispersione, rho) e VERIFICA 2022-2026.
Calibrazione dell'anno Y stimata solo sulle previsioni fuori campione degli anni < Y.
"""
import numpy as np
from sklearn.isotonic import IsotonicRegression

from .dist import KMAX, pmf
from .markets import masks, masks_hh

SEL_YEARS, VER_YEARS = (2019, 2020, 2021), (2022, 2023, 2024, 2025, 2026)
RHOS = np.round(np.arange(-0.15, 0.051, 0.01), 3)


def grid(mh, ma, phi_h, phi_a, K, rho=0.0):
    """Griglia congiunta (n, K+1, K+1) da due marginali indipendenti, con correzione Dixon-Coles opzionale."""
    ph, pa = pmf(mh, phi_h, K).astype(np.float32), pmf(ma, phi_a, K).astype(np.float32)
    M = ph[:, :, None] * pa[:, None, :]
    if rho:
        lh, la = np.asarray(mh)[:, None], np.asarray(ma)[:, None]
        M[:, 0, 0] *= (1 - lh * la * rho)[:, 0]
        M[:, 0, 1] *= (1 + lh * rho)[:, 0]
        M[:, 1, 0] *= (1 + la * rho)[:, 0]
        M[:, 1, 1] *= 1 - rho
        M /= M.sum((1, 2), keepdims=True)
    return M


def outcome(sel, yh, ya, K):
    """Esito reale (1 vinta, 0 persa) dai conteggi osservati, con la stessa maschera usata per la probabilità."""
    W, _ = masks(sel, K)
    return W[np.minimum(yh.astype(int), K), np.minimum(ya.astype(int), K)]


def outcome_hh(sel, h1, a1, h2, a2, K):
    W, _ = masks_hh(sel, K)
    c = [np.minimum(np.asarray(v, float).astype(int), K) for v in (h1, a1, h2, a2)]
    return W[c[0], c[1], c[2], c[3]]


def _lines(a, b, step=1.0):
    return [x + 0.5 for x in np.arange(a, b + 1e-9, step)]


def selections(stat):
    """Selezioni rappresentative da verificare per ogni statistica (solo linee .5: nessun rimborso)."""
    S = []

    def ou(kind, lo, hi):
        for line in _lines(lo, hi):
            for side in ("over", "under"):
                S.append({"kind": kind, "side": side, "line": line})
    if stat in ("g", "ght", "g2h"):
        top = {"g": 5, "ght": 2, "g2h": 3}[stat]
        ou("ou_tot", 0, top)
        ou("ou_home", 0, min(top, 2))
        ou("ou_away", 0, min(top, 2))
        S += [{"kind": "1x2", "o": o} for o in "HDA"] + [{"kind": "dc", "o": o} for o in ("HD", "HA", "DA")]
        S += [{"kind": "btts", "yes": y} for y in (True, False)] + [{"kind": "oe_tot", "odd": o} for o in (True, False)]
        S += [{"kind": "exact_tot", "n": n, "plus": False} for n in range(0, top + 1)]
        S += [{"kind": "dnb", "o": o} for o in "HA"]
        if stat == "g":
            S += [{"kind": "eh", "o": o, "h": h} for o in "HDA" for h in (-2, -1, 1)]
            S += [{"kind": "range_tot", "lo": lo, "hi": hi} for lo, hi in ((1, 2), (1, 3), (2, 3), (2, 4), (3, 4),
                                                                           (1, 4), (2, 5), (3, 5), (4, 6))]
            S += [{"kind": "ah", "o": o, "h": h} for o in "HA" for h in (-1.5, -0.5, 0.5, 1.5)]
            S += [{"kind": "res_btts", "o": o, "yes": y} for o in "HDA" for y in (True, False)]
            S += [{"kind": "res_tot", "o": o, "side": s, "line": 2.5} for o in "HDA" for s in ("over", "under")]
            S += [{"kind": "tot_btts", "side": s, "yes": y, "line": 2.5} for s in ("over", "under") for y in (True, False)]
            S += [{"kind": k, "yes": y} for k in ("clean_home", "clean_away", "scores_home", "scores_away")
                  for y in (True, False)]
            S += [{"kind": "nil_home", "yes": True}, {"kind": "nil_away", "yes": True}]
            S += [{"kind": "oe_home", "odd": o} for o in (True, False)] + [{"kind": "oe_away", "odd": o} for o in (True, False)]
            S += [{"kind": "cs", "x": x, "y": y} for x in range(4) for y in range(4)]
        return S
    rng = {"cor": ((6, 13), (2, 8), (1, 7)), "crd": ((1, 7), (0, 4), (0, 4)), "yel": ((1, 6), (0, 3), (0, 3)),
           "fou": ((17, 29), (8, 15), (8, 15)), "sh": ((18, 32), (7, 18), (5, 15)), "sot": ((5, 12), (2, 7), (1, 6))}
    if stat not in rng:
        return S
    (a, b), (c, d), (e, f) = rng[stat]
    ou("ou_tot", a, b)
    ou("ou_home", c, d)
    ou("ou_away", e, f)
    S += [{"kind": "1x2", "o": o} for o in "HDA"] + [{"kind": "dc", "o": o} for o in ("HD", "HA", "DA")]
    S += [{"kind": "ah", "o": o, "h": h} for o in "HA" for h in (-2.5, -1.5, -0.5, 0.5, 1.5, 2.5)]
    S += [{"kind": k, "odd": o} for k in ("oe_tot", "oe_home", "oe_away") for o in (True, False)]
    S += [{"kind": "dnb", "o": o} for o in "HA"]
    S += [{"kind": "eh", "o": o, "h": h} for o in "HDA" for h in (-2, -1, 1, 2)]
    if stat == "cor":
        S += [{"kind": "range_tot", "lo": lo, "hi": hi} for lo, hi in ((0, 5), (6, 8), (9, 11), (12, 14), (15, 99))]
    return S


def selections_hh():
    S = [{"kind": "hh_htft", "o": a, "o2": b} for a in "HDA" for b in "HDA"]
    S += [{"kind": "hh_highest", "o": o} for o in (0, 1, 2)]
    S += [{"kind": "hh_winboth", "o": o} for o in "HA"] + [{"kind": "hh_wineither", "o": o} for o in "HA"]
    S += [{"kind": "hh_teamboth", "o": o} for o in "HA"]
    S += [{"kind": k, "yes": y} for k in ("hh_bttsboth", "hh_anyboth") for y in (True, False)]
    return S


def family(stat, sel):
    """Famiglia di calibrazione: stesso tipo di giocata (linee diverse insieme)."""
    k = sel["kind"]
    side = sel.get("side") or sel.get("o") or ("yes" if sel.get("yes") else "no" if "yes" in sel else "")
    if k.startswith("oe_"):
        side = "odd" if sel["odd"] else "even"
    if k in ("cs", "exact_tot", "range_tot", "hh_htft", "hh_highest"):
        side = ""
    return f"{stat}|{k}|{side}"


def label(stat, sel):
    keys = [f"{k}={v}" for k, v in sel.items() if k != "kind"]
    return f"{stat} {sel['kind']} " + " ".join(keys)


class Calibrator:
    """Calibrazione robusta: fasce per quantili (>= min_n casi ciascuna), media prevista vs frequenza, resa monotona
    (isotonica sulle fasce) e interpolata. Fuori dalle fasce estreme: solo lo spostamento della fascia estrema."""

    def __init__(self, p, y, w=None, min_n=1000, max_bins=60):
        p, y = np.asarray(p, float), np.asarray(y, float)
        w = np.ones(len(p)) if w is None else np.asarray(w, float)
        nb = int(np.clip(len(p) // min_n, 2, max_bins))
        q = np.quantile(p, np.linspace(0, 1, nb + 1))
        idx = np.clip(np.searchsorted(q, p, side="right") - 1, 0, nb - 1)
        cnt = np.bincount(idx, w, minlength=nb)
        ok = cnt > 0
        xp = (np.bincount(idx, w * p, nb)[ok] / cnt[ok])
        yp = (np.bincount(idx, w * y, nb)[ok] / cnt[ok])
        ir = IsotonicRegression(out_of_bounds="clip").fit(xp, yp, sample_weight=cnt[ok])
        self.x, self.y = xp, ir.predict(xp)

    def predict(self, p):
        p = np.asarray(p, float)
        out = np.interp(p, self.x, self.y)
        lo, hi = p < self.x[0], p > self.x[-1]
        out[lo] = p[lo] + (self.y[0] - self.x[0])
        out[hi] = p[hi] + (self.y[-1] - self.x[-1])
        return np.clip(out, 1e-3, 1 - 1e-3)


def calibrator(p, y, years=None, ref=None):
    """Anni più recenti pesano di più (peso dimezzato per ogni anno indietro rispetto a ref): segue la deriva
    (es. meno falli fischiati negli anni)."""
    w = None if years is None else 0.5 ** (ref - 1 - np.asarray(years))
    return Calibrator(p, y, w)


def ece(p, y, bins=10):
    edges = np.linspace(0, 1, bins + 1)
    idx = np.clip(np.digitize(p, edges) - 1, 0, bins - 1)
    e = 0.0
    for b in range(bins):
        s = idx == b
        if s.any():
            e += s.mean() * abs(p[s].mean() - y[s].mean())
    return e


def logloss(p, y):
    p = np.clip(p, 1e-4, 1 - 1e-4)
    return float(-np.mean(y * np.log(p) + (1 - y) * np.log(1 - p)))


def brier(p, y):
    return float(np.mean((p - y) ** 2))


def kmax(stat):
    return KMAX[stat]
