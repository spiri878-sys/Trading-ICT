import pandas as pd
from raptor.compare import load_ea_trades, compare


def test_compare_matching(tmp_path):
    p = tmp_path / "RR_trades.csv"
    p.write_text("time;version;event;ticket;cell;side;volume;price;sl;tp;profit;note\n"
                 "2024.01.02 10:05:00;0.1.0;OPEN;11;RR|PPK;1;0.08;2000.00;1995.00;2020.00;0;\n"
                 "2024.01.02 10:30:00;0.1.0;PARTIAL1;11;RR|PPK;1;0.01;2003.50;1995.00;2020.00;0;0.7R\n"
                 "2024.01.02 11:00:00;0.1.0;CLOSED;11;RR|PPK;0;0;2020.00;0;0;120.0;TP\n"
                 "2024.01.03 10:05:00;0.1.0;OPEN;12;RR|LS;-1;0.08;2010.00;2015.00;1990.00;0;\n")
    ea = load_ea_trades(p)
    py = pd.DataFrame({"entry_time": pd.to_datetime(["2024-01-02 10:06", "2024-01-05 09:00"]), "side": [1, 1],
                       "strategy": ["PPK", "PPK"], "entry": [2000.1, 1990], "sl0": [1995.0, 1985], "lot": [0.08, 0.08],
                       "net": [118.0, -40.0], "partials": [1, 0], "exit_reason": ["TP", "SL"]})
    r = compare(ea, py)
    assert r["matched"] == 1 and r["ea_only"] == 1 and r["python_only"] == 1
    t = r["table"].set_index("status")
    assert abs(t.loc["matched", "d_entry"] + 0.1) < 1e-9
