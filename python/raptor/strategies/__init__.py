"""Strategy ("cell") registry. Each cell maps the causal feature table to a signal table.

Signal columns: bar_time (open time of the closed decision bar), side (+1/-1), otype ('limit'|'market'),
price (BID-chart limit price), sl_struct (structural invalidation incl. buffer), atr (signal-TF ATR14),
expiry_bars, strategy, plus context columns copied by `raptor.features`.
"""
from .ict import ppk, oteof, po3, uniof, ls, silver_bullet
from .wyckoff import wyckoff_spring

REGISTRY = {
    "PPK": ppk,
    "OTEOF": oteof,
    "PO3": po3,
    "UNIOF": uniof,
    "LS": ls,
    "SILVER_BULLET": silver_bullet,
    "WYCKOFF": wyckoff_spring,
}
# The five cells named in the Interstellar material (screenshot "La cascata dei modelli").
ICT_CELLS = ["PPK", "OTEOF", "PO3", "UNIOF", "LS"]
