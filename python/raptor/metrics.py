"""Performance metrics, identical for every version / configuration."""
import numpy as np
import pandas as pd


def max_streak(neg) -> int:
    best = cur = 0
    for x in neg:
        cur = cur + 1 if x else 0
        best = max(best, cur)
    return best


def summarize(tr: pd.DataFrame, initial: float, start=None, end=None) -> dict:
    """Metrics from a portfolio trade list. Drawdown uses closed balance plus each trade's
    worst intratrade excursion (MAE), so it includes open-trade drawdown."""
    if start is not None:
        tr = tr[(tr.entry_time >= pd.Timestamp(start)) & (tr.entry_time < pd.Timestamp(end))]
    n = len(tr)
    if n == 0:
        return {"trades": 0, "net_profit": 0.0}
    t0 = pd.Timestamp(start) if start is not None else tr.entry_time.iloc[0]
    t1 = pd.Timestamp(end) if end is not None else tr.exit_time.iloc[-1]
    months = max((t1 - t0).days / 30.44, 1e-9)
    start_bal = tr.balance.iloc[0] - tr.net.iloc[0]
    wins, losses = tr.net[tr.net > 0], tr.net[tr.net <= 0]
    bal_before = tr.balance - tr.net
    peak = np.maximum.accumulate(np.r_[start_bal, tr.balance.values])[:-1]
    dd_money = np.maximum(peak - tr.equity_low.values, peak - tr.balance.values)
    dd_pct = dd_money / peak * 100
    daily = tr.groupby(tr.exit_time.dt.normalize()).net.sum()
    monthly = tr.groupby(tr.exit_time.dt.to_period("M")).net.sum()
    yearly = tr.groupby(tr.exit_time.dt.year)
    hold = (tr.exit_time - tr.entry_time).dt.total_seconds().sum()
    spread_cost = (tr.spread_at_entry * tr.lot * 100.0).sum()
    return {
        "trades": int(n),
        "net_profit": round(float(tr.net.sum()), 2),
        "gross_before_commission": round(float(tr.gross.sum()), 2),
        "return_pct": round(float(tr.net.sum() / start_bal * 100), 2),
        "profit_factor": round(float(wins.sum() / -losses.sum()), 3) if losses.sum() < 0 else None,
        "win_rate_pct": round(len(wins) / n * 100, 2),
        "trades_per_month": round(n / months, 2),
        "expectancy_money": round(float(tr.net.mean()), 3),
        "expectancy_R": round(float(tr.r_mult.mean()), 4),
        "avg_win": round(float(wins.mean()), 2) if len(wins) else 0.0,
        "avg_loss": round(float(losses.mean()), 2) if len(losses) else 0.0,
        "payoff_ratio": round(float(wins.mean() / -losses.mean()), 3) if len(wins) and len(losses) and losses.mean() < 0 else None,
        "max_dd_money": round(float(dd_money.max()), 2),
        "max_dd_pct": round(float(dd_pct.max()), 2),
        "max_losing_streak": max_streak((tr.net <= 0).values),
        "positive_days_pct": round(float((daily > 0).mean() * 100), 2),
        "positive_months_pct": round(float((monthly > 0).mean() * 100), 2),
        "months_with_trades": int(len(monthly)),
        "yearly_net": {int(k): round(float(v.net.sum()), 2) for k, v in yearly},
        "yearly_R": {int(k): round(float(v.r_mult.sum()), 2) for k, v in yearly},
        "exposure_pct": round(float(hold / max((t1 - t0).total_seconds(), 1) * 100), 2),
        "commission_total": round(float(tr.commission.sum()), 2),
        "spread_cost_est": round(float(spread_cost), 2),
        "avg_risk_money": round(float(tr.risk_money.mean()), 2),
        "avg_risk_pct_of_balance": round(float((tr.risk_money / bal_before).mean() * 100), 3),
        "net_over_avg_risk": round(float(tr.net.sum() / tr.risk_money.mean()), 2) if tr.risk_money.mean() > 0 else None,
        "exit_reasons": {k: int(v) for k, v in tr.exit_reason.value_counts().items()},
        "by_strategy_R": {k: [int(len(v)), round(float(v.r_mult.mean()), 3)] for k, v in tr.groupby("strategy")},
        "final_balance": round(float(tr.balance.iloc[-1]), 2),
    }


def r_stats(r: pd.Series) -> dict:
    """Stats on a series of isolated R outcomes (labels)."""
    r = r.dropna()
    if len(r) == 0:
        return {"n": 0}
    w, lo = r[r > 0], r[r <= 0]
    return {"n": int(len(r)), "mean_R": round(float(r.mean()), 4), "sum_R": round(float(r.sum()), 1),
            "win_pct": round(float((r > 0).mean() * 100), 1),
            "pf": round(float(w.sum() / -lo.sum()), 3) if lo.sum() < 0 else None,
            "t_stat": round(float(r.mean() / (r.std(ddof=1) / np.sqrt(len(r)))), 2) if len(r) > 2 else None}
