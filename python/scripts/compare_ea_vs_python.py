"""Usage: python compare_ea_vs_python.py <EA trades csv> <python trades csv> [tol_minutes]
Writes reports/ea_vs_python_<name>.csv and prints the summary."""
import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pandas as pd
from raptor.compare import load_ea_trades, compare

ea = load_ea_trades(sys.argv[1])
py = pd.read_csv(sys.argv[2], parse_dates=["entry_time", "exit_time"])
res = compare(ea, py, int(sys.argv[3]) if len(sys.argv) > 3 else 2)
out = Path(__file__).resolve().parents[2] / "reports" / f"ea_vs_python_{Path(sys.argv[1]).stem}.csv"
res.pop("table").to_csv(out, index=False)
print(json.dumps(res, indent=1))
