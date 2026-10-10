"""Cost models (docs/costs.md). The M1 file records ~140-170 point spreads in 2018-2022 and
~0-20 points from 2023 (43-49% zero-spread bars in 2023-24, i.e. a raw/ECN feed). Because the two
regimes are not comparable, every decision is taken under the uniform model C1 and stressed under
C0 (recorded) and C2 (C1 x2).

C1: spread = 0.30 USD fixed (30 points) + commission 3.5 USD/lot/side + slippage 0.05 on stops/market.
C0: spread = recorded per M1 bar (floor 0.05) + same commission/slippage.
"""
from contextlib import contextmanager
from dataclasses import replace
from .engine import Params
from . import pipeline as P

C1 = dict(kind="fixed", spread=0.30, commission_per_lot_side=3.5, slippage=0.05)
C0 = dict(kind="recorded", floor=0.05, commission_per_lot_side=3.5, slippage=0.05)
C2 = dict(kind="fixed", spread=0.60, commission_per_lot_side=7.0, slippage=0.10)
ZERO = dict(kind="fixed", spread=0.0, commission_per_lot_side=0.0, slippage=0.0)


@contextmanager
def with_cost(cm: dict, base: Params | None = None):
    """Temporarily set the market spread array according to the cost model and yield Params."""
    mk = P.market()
    raw = mk.sp_raw.copy()
    prm = replace(base or Params(), commission_per_lot_side=cm["commission_per_lot_side"],
                  slippage=cm["slippage"], max_spread=5.0)
    try:
        if cm["kind"] == "fixed":
            mk.sp_raw[:] = cm["spread"]; prm = replace(prm, spread_floor=0.0)
        else:
            prm = replace(prm, spread_floor=cm["floor"])
        yield prm
    finally:
        mk.sp_raw[:] = raw
