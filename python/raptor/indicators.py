"""Causal indicators. Every value at index i uses only bars <= i (closed bars)."""
import numpy as np
from numba import njit


@njit(cache=True)
def atr(h, l, c, n):
    out = np.full(h.size, np.nan)
    tr = np.empty(h.size)
    tr[0] = h[0] - l[0]
    for i in range(1, h.size):
        tr[i] = max(h[i] - l[i], abs(h[i] - c[i - 1]), abs(l[i] - c[i - 1]))
    if h.size < n:
        return out
    s = tr[:n].sum()
    out[n - 1] = s / n
    for i in range(n, h.size):  # Wilder smoothing
        out[i] = (out[i - 1] * (n - 1) + tr[i]) / n
    return out


@njit(cache=True)
def ema(x, n):
    out = np.full(x.size, np.nan)
    a = 2.0 / (n + 1)
    out[0] = x[0]
    for i in range(1, x.size):
        out[i] = a * x[i] + (1 - a) * out[i - 1]
    return out


@njit(cache=True)
def confirmed_swings(h, l, k):
    """Fractal swing points with k bars each side.

    Returns arrays (last_sh, last_sh_idx, last_sl, last_sl_idx) giving, at bar i, the most recent
    swing high/low whose confirmation (pivot index + k) is <= i. No look-ahead.
    """
    n = h.size
    last_sh = np.full(n, np.nan); last_sh_i = np.full(n, -1)
    last_sl = np.full(n, np.nan); last_sl_i = np.full(n, -1)
    sh, shi, sl, sli = np.nan, -1, np.nan, -1
    for i in range(n):
        p = i - k  # candidate pivot, confirmed now
        if p >= k:
            is_h = True; is_l = True
            for j in range(p - k, p + k + 1):
                if j == p:
                    continue
                if h[j] >= h[p] and (j > p or h[j] > h[p]):
                    is_h = False
                if l[j] <= l[p] and (j > p or l[j] < l[p]):
                    is_l = False
            if is_h:
                sh, shi = h[p], p
            if is_l:
                sl, sli = l[p], p
        last_sh[i], last_sh_i[i], last_sl[i], last_sl_i[i] = sh, shi, sl, sli
    return last_sh, last_sh_i, last_sl, last_sl_i


def rsi(c, n):
    """Wilder RSI, causal."""
    d = np.diff(c, prepend=c[0])
    up = np.where(d > 0, d, 0.0); dn = np.where(d < 0, -d, 0.0)
    au = np.full(c.size, np.nan); ad = np.full(c.size, np.nan)
    if c.size <= n:
        return au
    au[n] = up[1:n + 1].mean(); ad[n] = dn[1:n + 1].mean()
    for i in range(n + 1, c.size):
        au[i] = (au[i - 1] * (n - 1) + up[i]) / n
        ad[i] = (ad[i - 1] * (n - 1) + dn[i]) / n
    rs = au / np.where(ad == 0, np.nan, ad)
    out = 100 - 100 / (1 + rs)
    return np.where(ad == 0, 100.0, out)
