"""Modelli dei conteggi (Fase M3): valore atteso per casa e ospite di ogni statistica.

Approcci: A classico (forze dinamiche / motore gol), B LightGBM Poisson, C media geometrica A-B,
D mercato (solo gol: lambda ricavati dalle quote 1X2 + O/U 2.5 senza margine), E media geometrica B-D.
"""
import lightgbm as lgb
import numpy as np
from scipy.stats import poisson
from sklearn.neighbors import KDTree

from .goals import MAXG

# statistica -> colonne bersaglio (casa, ospite) e stima classica
TARGETS = {"g": ("hg", "ag"), "ght": ("HTHome", "HTAway"), "g2h": ("H2H", "A2H"),
           "cor": ("HomeCorners", "AwayCorners"), "fou": ("HomeFouls", "AwayFouls"),
           "yel": ("HomeYellow", "AwayYellow"), "red": ("HomeRed", "AwayRed"), "crd": ("HomeCards", "AwayCards"),
           "sh": ("HomeShots", "AwayShots"), "sot": ("HomeTarget", "AwayTarget")}
PARAMS = dict(objective="poisson", learning_rate=0.04, num_leaves=31, min_data_in_leaf=300, feature_fraction=0.6,
              bagging_fraction=0.8, bagging_freq=1, lambda_l2=5.0, verbose=-1, num_threads=4, seed=7)
ROUNDS = 700


def add_targets(m):
    m = m.copy()
    m["H2H"], m["A2H"] = m.hg - m.HTHome, m.ag - m.HTAway
    m["HomeCards"], m["AwayCards"] = m.HomeYellow + 2 * m.HomeRed, m.AwayYellow + 2 * m.AwayRed   # giallo 1, rosso 2
    return m


def classic(X, stat):
    """Approccio A: per i gol il motore Dixon-Coles, per il 1° tempo quota fissa del totale; altrimenti le forze."""
    if stat == "g":
        return X.f1_lh.to_numpy(float), X.f1_la.to_numpy(float)
    if stat in ("ght", "g2h"):
        rh = (X.lg_h_ght / X.lg_h_g).clip(0.3, 0.6).to_numpy(float)
        ra = (X.lg_a_ght / X.lg_a_g).clip(0.3, 0.6).to_numpy(float)
        if stat == "ght":
            return X.f1_lh.to_numpy(float) * rh, X.f1_la.to_numpy(float) * ra
        return X.f1_lh.to_numpy(float) * (1 - rh), X.f1_la.to_numpy(float) * (1 - ra)
    if stat == "crd":
        return (X.exp_h_yel + 2 * X.exp_h_red).to_numpy(float), (X.exp_a_yel + 2 * X.exp_a_red).to_numpy(float)
    return X[f"exp_h_{stat}"].to_numpy(float), X[f"exp_a_{stat}"].to_numpy(float)


def fit_lgb(Xtr, ytr, Xva=None, yva=None):
    ds = lgb.Dataset(Xtr, ytr, free_raw_data=True)
    if Xva is not None and len(Xva) > 500:
        dv = lgb.Dataset(Xva, yva, reference=ds)
        b = lgb.train(PARAMS, ds, ROUNDS, valid_sets=[dv], callbacks=[lgb.early_stopping(50, verbose=False)])
        return b, b.best_iteration
    return lgb.train(PARAMS, ds, ROUNDS), ROUNDS


# ---- D: lambda dal mercato -------------------------------------------------------------------------------
_TREE = None


def _grid():
    global _TREE
    if _TREE is None:
        lam = np.arange(0.15, 4.01, 0.025)
        LH, LA = np.meshgrid(lam, lam, indexing="ij")
        LH, LA = LH.ravel(), LA.ravel()
        g = np.arange(MAXG + 1)
        ph, pa = poisson.pmf(g[None], LH[:, None]), poisson.pmf(g[None], LA[:, None])
        M = ph[:, :, None] * pa[:, None, :]
        diff, tot = g[:, None] - g[None, :], g[:, None] + g[None, :]
        P = np.column_stack([(M * (diff > 0)).sum((1, 2)), (M * (diff < 0)).sum((1, 2)), (M * (tot > 2.5)).sum((1, 2))])
        _TREE = (KDTree(P), LH, LA)
    return _TREE


def market_lambdas(X):
    """Gol attesi coerenti con le quote (1, 2, Over 2.5 senza margine). NaN dove manca il mercato O/U."""
    tree, LH, LA = _grid()
    P = X[["mk_1", "mk_2", "mk_o25"]].to_numpy(float)
    ok = ~np.isnan(P).any(1)
    lh, la = np.full(len(X), np.nan), np.full(len(X), np.nan)
    if ok.any():
        idx = tree.query(P[ok], k=1, return_distance=False)[:, 0]
        lh[ok], la[ok] = LH[idx], LA[idx]
    return lh, la


def geo(a, b):
    return np.where(np.isnan(b), a, np.sqrt(a * np.where(np.isnan(b), 1, b)))


def candidates(X, stat, bh, ba):
    """Tutti gli approcci per una statistica, dati i valori LightGBM (bh, ba)."""
    ah, aa = classic(X, stat)
    c = {"A": (ah, aa), "B": (bh, ba), "C": (geo(bh, ah), geo(ba, aa))}
    if stat == "g":
        dh, da = market_lambdas(X)
        c["D"] = (np.where(np.isnan(dh), bh, dh), np.where(np.isnan(da), ba, da))
        c["E"] = (geo(bh, dh), geo(ba, da))
    return c


def poisson_dev(y, mu):
    mu = np.clip(mu, 1e-6, None)
    return float(np.mean(2 * (np.where(y > 0, y * np.log(np.where(y > 0, y, 1) / mu), 0) - (y - mu))))

