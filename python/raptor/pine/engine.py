"""Gestore di posizione barra per barra per le strategie Pine (Fase 14). Un trade alla volta.

Su barre BID: per un long avverso = minimo, favorevole = massimo; per uno short si confronta l'ASK
(BID + spread) con stop e target. Stop prima del target nella stessa barra; gap oltre lo stop = uscita
all'apertura. Le parziali sono ordini limite sul livello.
"""
import numpy as np

from .common import COMM, SLIP, SPREAD


class Position:
    def __init__(self, side, entry, stop, i, risk=None, targets=(), be_after_first=False, day=None):
        self.side, self.entry, self.stop, self.i0 = side, entry, stop, i
        self.risk = risk if risk is not None else abs(entry - stop)
        self.targets = list(targets)            # [(prezzo, frazione)] in ordine; frazione None = resto
        self.rem, self.pnl = 1.0, 0.0
        self.be_after_first = be_after_first
        self.hits = 0
        self.day0 = day
        self.closed = False
        self.exit_i = None

    def _px(self, o, h, l, c):
        if self.side == 1:
            return o, l, h, c
        return o + SPREAD, h + SPREAD, l + SPREAD, c + SPREAD   # ASK: open, avverso, favorevole, close

    def close(self, px, i):
        """Chiusura a mercato al prezzo BID px (per gli short si paga l'ASK)."""
        ex = px - SLIP if self.side == 1 else px + SPREAD + SLIP
        self.pnl += self.rem * (ex - self.entry) * self.side
        self.rem = 0.0
        self.closed, self.exit_i = True, i

    def step(self, i, o, h, l, c, check_targets=True):
        """Aggiorna la posizione sulla barra i. Restituisce True se chiusa in questa barra."""
        if self.closed:
            return True
        op, adv, fav, cl = self._px(o, h, l, c)
        sd = self.side
        if self.stop is not None:
            if (op - self.stop) * sd <= 0 and i > self.i0:
                self.pnl += self.rem * (op - sd * SLIP - self.entry) * sd
                self.rem, self.closed, self.exit_i = 0.0, True, i
                return True
            if (adv - self.stop) * sd <= 0:
                self.pnl += self.rem * (self.stop - sd * SLIP - self.entry) * sd
                self.rem, self.closed, self.exit_i = 0.0, True, i
                return True
        if check_targets:
            while self.targets and (fav - self.targets[0][0]) * sd >= 0:
                tp, frac = self.targets.pop(0)
                q = self.rem if (frac is None or not self.targets) else min(frac, self.rem)
                self.pnl += q * (tp - self.entry) * sd
                self.rem -= q
                self.hits += 1
                if self.be_after_first and self.hits == 1:
                    self.stop = self.entry if self.stop is None else (max(self.stop, self.entry) if sd == 1
                                                                      else min(self.stop, self.entry))
                if self.rem <= 1e-9:
                    self.closed, self.exit_i = True, i
                    return True
        return False

    def r(self, nights=0):
        pnl = self.pnl - 2 * COMM + (-0.066 if self.side == 1 else 0.029) * self.entry * nights / 365.0
        return pnl / max(self.risk + SLIP + 2 * COMM, 1e-9)


def mkt_entry(side, open_px):
    """Ingresso a mercato all'apertura (BID): long ASK + slippage, short BID - slippage."""
    return open_px + SPREAD + SLIP if side == 1 else open_px - SLIP


def fill_stop_order(side, level, o, h, l):
    """Ordine stop d'ingresso su barra BID: buy-stop scatta quando l'ASK tocca il livello; sell-stop quando il
    BID lo tocca. Restituisce il prezzo pagato o None."""
    if side == 1:
        if h + SPREAD >= level:
            return max(level, o + SPREAD) + SLIP
    else:
        if l <= level:
            return min(level, o) - SLIP
    return None


def fill_limit_order(side, level, o, h, l):
    """Limite d'ingresso: buy-limit quando l'ASK scende al livello; sell-limit quando il BID sale al livello."""
    if side == 1:
        if l + SPREAD <= level:
            return min(level, o + SPREAD)
    else:
        if h >= level:
            return max(level, o)
    return None
