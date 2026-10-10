"""Static checks for the MQL5 sources (NOT a compiler; MetaEditor is not available in the build env).
Checks: balanced (), [], {} outside strings/comments; included files exist; every `input` is used;
no MQL4-only constructs; no TODO/placeholder markers; cell defaults identical to the python reconstruction."""
import re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = sorted((ROOT / "mql5").rglob("*.mq*"))
errors = []


TOKEN = re.compile(r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])\'|//[^\n]*|/\*.*?\*/', re.S)


def strip(code: str) -> str:
    """Remove comments and blank out string/char literals in a single left-to-right pass."""
    return TOKEN.sub(lambda m: '""' if m.group(0)[0] in "\"'" else "", code)


for f in SRC:
    raw = f.read_text()
    code = strip(raw)
    for o, c in ["()", "[]", "{}"]:
        if code.count(o) != code.count(c):
            errors.append(f"{f.name}: unbalanced {o}{c} ({code.count(o)} vs {code.count(c)})")
    for inc in re.findall(r'#include\s+<RaptorRecon\\(\w+\.mqh)>', raw) + re.findall(r'#include\s+"(\w+\.mqh)"', raw):
        if not (ROOT / "mql5" / "Include" / "RaptorRecon" / inc).exists():
            errors.append(f"{f.name}: missing include {inc}")
    for bad in ["#property strict", "OrderSend(", "MarketInfo(", "Bars(Symbol", "extern ", "TODO", "FIXME", "placeholder"]:
        if bad in raw:
            errors.append(f"{f.name}: forbidden construct '{bad}'")
    for name in re.findall(r"^\s*input\s+[\w:]+\s+(\w+)\s*=", raw, flags=re.M):
        if len(re.findall(r"\b" + name + r"\b", code)) < 2:
            errors.append(f"{f.name}: input {name} declared but never used")
ea = (ROOT / "mql5" / "Experts" / "RaptorRecon" / "RaptorRecon.mq5").read_text()
# cell defaults vs python (min_disp, min_fvg, expiry) - python/raptor/strategies/ict.py
expected = {"PPK": (1.2, 0.15, 12), "MSS": (1.2, 0.15, 12), "OTEOF": (1.2, 0.0, 24), "PO3": (1.0, 0.1, 12),
            "UNIOF": (1.2, 0.1, 12), "LS": (1.2, 0.15, 6), "SilverBullet": (1.2, 0.25, 6)}
for cell, (d, fv, ex) in expected.items():
    m = re.search(r"CellDefaults\(p, ([\d.]+), ([\d.]+), (\d+), false\);\s+g_cells\." + cell + r"\(", ea)
    if not m:
        errors.append(f"EA: no profile-A call for cell {cell}")
    elif (float(m.group(1)), float(m.group(2)), int(m.group(3))) != (d, fv, ex):
        errors.append(f"EA: cell {cell} defaults {m.groups()} != python {(d, fv, ex)}")
print(f"checked {len(SRC)} files")
print("\n".join(errors) if errors else "OK: no static issues found")
sys.exit(1 if errors else 0)
