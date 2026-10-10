"""Trade-by-trade comparison between the MT5 EA logs and the python simulator (spec 16).

EA log: MQL5/Files/RaptorRecon/<prefix>_trades.csv (';' separated) with events OPEN / PARTIAL1 /
PARTIAL2 / MODIFY / CLOSE_DEAL / CLOSED. Python: trades DataFrame from raptor.engine.run.
Matching: same side and cell, EA open time within `tol_min` minutes of the python entry time.
Every unmatched trade and every difference is reported; nothing is silently dropped.
"""
import pandas as pd


def load_ea_trades(path) -> pd.DataFrame:
    ev = pd.read_csv(path, sep=";")
    ev["time"] = pd.to_datetime(ev["time"], format="%Y.%m.%d %H:%M:%S")
    opens = ev[ev.event == "OPEN"].rename(columns={"time": "entry_time", "price": "entry", "sl": "sl0", "volume": "lot"})
    closed = ev[ev.event == "CLOSED"][["ticket", "time", "profit", "note"]].rename(
        columns={"time": "exit_time", "profit": "net", "note": "exit_reason"})
    parts = ev[ev.event.isin(["PARTIAL1", "PARTIAL2"])].groupby("ticket").size().rename("partials")
    t = opens.merge(closed, on="ticket", how="left").merge(parts, on="ticket", how="left")
    t["partials"] = t.partials.fillna(0).astype(int)
    t["strategy"] = t.cell.str.replace("RR|", "", regex=False)
    return t[["ticket", "entry_time", "exit_time", "side", "strategy", "lot", "entry", "sl0", "tp", "net", "partials", "exit_reason"]]


def compare(ea: pd.DataFrame, py: pd.DataFrame, tol_min: int = 2) -> dict:
    py = py.copy().reset_index(drop=True)
    py["matched"] = False
    rows = []
    for _, e in ea.iterrows():
        cand = py[(~py.matched) & (py.side == e.side) & (py.strategy == e.strategy) &
                  ((py.entry_time - e.entry_time).abs() <= pd.Timedelta(minutes=tol_min))]
        if cand.empty:
            rows.append({"ticket": e.ticket, "status": "EA_only", "entry_time": e.entry_time})
            continue
        j = (cand.entry_time - e.entry_time).abs().idxmin()
        py.loc[j, "matched"] = True
        p = py.loc[j]
        rows.append({"ticket": e.ticket, "status": "matched", "entry_time": e.entry_time,
                     "d_entry": e.entry - p.entry, "d_sl": e.sl0 - p.sl0, "d_lot": e.lot - p.lot,
                     "d_net": (e.net - p.net) if pd.notna(e.net) else None,
                     "d_partials": e.partials - p.partials, "ea_exit": e.exit_reason, "py_exit": p.exit_reason})
    for _, p in py[~py.matched].iterrows():
        rows.append({"ticket": None, "status": "python_only", "entry_time": p.entry_time})
    df = pd.DataFrame(rows)
    m = df[df.status == "matched"]
    return {"table": df, "matched": int(len(m)), "ea_only": int((df.status == "EA_only").sum()),
            "python_only": int((df.status == "python_only").sum()),
            "median_abs_d_entry": float(m.d_entry.abs().median()) if len(m) else None,
            "median_abs_d_net": float(pd.to_numeric(m.d_net, errors="coerce").abs().median()) if len(m) else None}
