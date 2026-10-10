"""Strategy ("cell") registry. Each cell maps the causal feature table to a signal table.

Signal columns: bar_time (open time of the closed decision bar), side (+1/-1), otype ('limit'|'market'),
price (BID-chart limit price), sl_struct (structural invalidation incl. buffer), atr (signal-TF ATR14),
expiry_bars, strategy, plus context columns copied by `raptor.features`.
"""
from .ict import ppk, mss, oteof, po3, uniof, ls, silver_bullet, mtf_m1
from .wyckoff import wyckoff_spring
from .wyckoff_mtf import wyckoff_mtf

REGISTRY = {
    "PPK": ppk,
    "MSS": mss,
    "MTF_M1": mtf_m1,
    "OTEOF": oteof,
    "PO3": po3,
    "UNIOF": uniof,
    "LS": ls,
    "SILVER_BULLET": silver_bullet,
    "WYCKOFF": wyckoff_spring,
    "WYCKOFF_MTF": wyckoff_mtf,
}
# The five cells named in the Interstellar material (screenshot "La cascata dei modelli").
ICT_CELLS = ["PPK", "OTEOF", "PO3", "UNIOF", "LS"]
# The six strategies named on the vendor site (as relayed by the user; site blocked from this environment)
# mapped to our modules: Unicorn->UNIOF, OTE->OTEOF, Silver Bullet->SILVER_BULLET, Power of Three->PO3,
# Market Structure Shift->MSS, Liquidity Sweep->LS. PPK has no documented definition (inferred main engine).
SITE_SIX = {"Unicorn Model": "UNIOF", "OTE": "OTEOF", "Silver Bullet": "SILVER_BULLET", "Power of Three": "PO3",
            "Market Structure Shift": "MSS", "Liquidity Sweep": "LS"}
