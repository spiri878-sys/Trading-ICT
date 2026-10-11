"""Parse a Telegram channel export (result.json) of XAUUSD signals of the form

    Gold buy 5186-5180            (sometimes preceded by a bare "Gold buy" alert a minute earlier)
    SL 5172
    TP 5190 / TP 5193 / ... / TP  (last TP open)

Returns one row per signal: post time (export local time), side, zone (first = near-market level, second = deeper),
SL, list of TPs, alert time (bare "Gold buy/sell" message just before, if any), edit lag.
"""
import json
import re

import pandas as pd

NUM = r"(\d{4}(?:[.,]\d+)?)"
HEAD = re.compile(r"^\s*(?:gold|xau(?:usd)?)\s+(buy|sell)\b(.*)$", re.I | re.S)


def _text(m):
    t = m.get("text", "")
    if isinstance(t, list):
        t = "".join(x if isinstance(x, str) else x.get("text", "") for x in t)
    return t


def _f(s):
    return float(s.replace(",", "."))


def _repair(v, ref, want_sign, max_dist=60.0):
    """Fix single-digit typos (e.g. SL 4114 for 4214): if v is not within max_dist of ref on the wanted side
    (want_sign=+1 above ref, -1 below, 0 either), try every single-digit substitution and keep the closest valid."""
    def ok(x):
        dd = (x - ref) * (want_sign or 1)
        return abs(x - ref) <= max_dist and (want_sign == 0 or dd > 0)
    if v is None or ok(v):
        return v, False
    s = f"{v:.2f}"
    best = None
    for i, ch in enumerate(s[:4]):
        for d in "0123456789":
            if d == ch:
                continue
            x = float(s[:i] + d + s[i + 1:])
            if ok(x) and (best is None or abs(x - ref) < abs(best - ref)):
                best = x
    return (best, True) if best is not None else (None, True)


def parse_export(path):
    d = json.load(open(path, encoding="utf-8"))
    msgs = [m for m in d["messages"] if m.get("type") == "message"]
    rows, last_alert = [], {}
    for m in msgs:
        t = _text(m).strip()
        h = HEAD.match(t)
        if not h:
            continue
        side = 1 if h.group(1).lower() == "buy" else -1
        rest = h.group(2)
        ts = pd.Timestamp(m["date"])
        lines = [x.strip() for x in rest.split("\n")]
        first = lines[0]
        nums_first = [_f(x) for x in re.findall(NUM, first)]
        sl = None
        tps = []
        for ln in lines[1:]:
            if re.match(r"^s\s*l\b", ln, re.I):
                v = re.findall(NUM, ln)
                if v and sl is None:
                    sl = _f(v[0])
                continue
            if re.match(r"^(?:last\s+)?t[po]\b|^tp\d", ln, re.I):
                v = re.findall(NUM, ln)
                if v:
                    tps.append(_f(v[0]))
        if sl is None and not tps:
            # bare alert ("Gold buy" or "Gold buy 5175")
            last_alert[side] = (ts, nums_first[0] if nums_first else None, m["id"])
            continue
        if not nums_first:
            continue
        z1 = nums_first[0]
        z2 = nums_first[-1] if len(nums_first) > 1 else z1
        # shorthand like "5176/5-5170": second token < 100 -> ignore
        nfix = 0
        z2, f = _repair(z2, z1, -side, 20.0); nfix += f
        z2 = z1 if z2 is None else z2
        sl, f = _repair(sl, z1, -side, 60.0); nfix += f
        fixed = []
        for tp in tps:
            tp2, f = _repair(tp, z1, side, 150.0); nfix += f
            if tp2 is not None:
                fixed.append(tp2)
        tps = fixed
        al = last_alert.get(side)
        alert_t, alert_px = (al[0], al[1]) if al and 0 <= (ts - al[0]).total_seconds() <= 900 else (pd.NaT, None)
        ed = pd.Timestamp(m["edited"]) if m.get("edited") else pd.NaT
        # drop obviously mistyped TPs (wrong side or >300 away, e.g. 5115 instead of 5215)
        good = tps
        rows.append(dict(msg_id=m["id"], post_time=ts, alert_time=alert_t, alert_px=alert_px, side=side, z1=z1, z2=z2,
                         sl=sl, tps=good, n_fixed=nfix, n_tps=len(good), n_tps_raw=len(tps),
                         edit_lag_s=(ed - ts).total_seconds() if ed is not pd.NaT else 0.0, text=t))
    return pd.DataFrame(rows)
