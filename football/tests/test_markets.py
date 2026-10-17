"""Coerenza delle probabilità e lettura dei mercati API."""
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fb.dist import pmf  # noqa: E402
from fb.markets import API_BETS, parse, prob  # noqa: E402

FIX = Path(__file__).parent / "odds_sample.json"


def grid(mh=1.6, ma=1.1, K=10):
    ph, pa = pmf(np.array([mh]), 1.0, K), pmf(np.array([ma]), 1.0, K)
    return ph[:, :, None] * pa[:, None, :]


def p(sel, M=None):
    return prob(grid() if M is None else M, sel)


def test_sums():
    M = grid()
    assert abs(M.sum() - 1) < 1e-9
    one = sum(p({"kind": "1x2", "o": o})[0][0] for o in "HDA")
    assert abs(one - 1) < 1e-9
    for line in (0.5, 1.5, 2.5, 3.5):
        s = p({"kind": "ou_tot", "side": "over", "line": line})[0] + p({"kind": "ou_tot", "side": "under", "line": line})[0]
        assert abs(s[0] - 1) < 1e-9
    w, pu = p({"kind": "ou_tot", "side": "over", "line": 2.0})
    w2, _ = p({"kind": "ou_tot", "side": "under", "line": 2.0})
    assert abs(w[0] + w2[0] + pu[0] - 1) < 1e-9
    btts = p({"kind": "btts", "yes": True})[0] + p({"kind": "btts", "yes": False})[0]
    assert abs(btts[0] - 1) < 1e-9
    dc = p({"kind": "dc", "o": "HD"})[0][0]
    assert abs(dc - p({"kind": "1x2", "o": "H"})[0][0] - p({"kind": "1x2", "o": "D"})[0][0]) < 1e-9


def test_quarter_line():
    w25, pu25 = p({"kind": "ou_tot", "side": "over", "line": 2.25})
    w2, pu2 = p({"kind": "ou_tot", "side": "over", "line": 2.0})
    w3, _ = p({"kind": "ou_tot", "side": "over", "line": 2.5})
    assert abs(w25[0] - (w2[0] + w3[0]) / 2) < 1e-9 and abs(pu25[0] - pu2[0] / 2) < 1e-9


def test_parse_all_api_values():
    data = json.loads(FIX.read_text())
    unknown, bad = set(), []
    for b in data["response"][0]["bookmakers"]:
        for bet in b["bets"]:
            if bet["id"] not in API_BETS:
                unknown.add((bet["id"], bet["name"]))
                continue
            stat, kind = API_BETS[bet["id"]]
            for v in bet["values"]:
                sel = parse(kind, v["value"])
                if sel is None:
                    bad.append((bet["name"], v["value"]))
                    continue
                sel["kind"] = kind
                if not kind.startswith("hh_"):
                    prob(grid(), sel)
    assert not bad, bad[:20]
    print("mercati non coperti:", sorted(unknown))


def test_halves_coherent():
    K = 6
    p1 = pmf(np.array([0.7]), 1.0, K)[:, :, None] * pmf(np.array([0.5]), 1.0, K)[:, None, :]
    p2 = pmf(np.array([0.9]), 1.0, K)[:, :, None] * pmf(np.array([0.6]), 1.0, K)[:, None, :]
    M4 = p1[:, :, :, None, None] * p2[:, None, None, :, :]
    tot = sum(prob(M4, {"kind": "hh_htft", "o": a, "o2": b})[0][0] for a in "HDA" for b in "HDA")
    assert abs(tot - 1) < 1e-9
    hi = sum(prob(M4, {"kind": "hh_highest", "o": o})[0][0] for o in (0, 1, 2))
    assert abs(hi - 1) < 1e-9


def test_asian_handicap_quarters():
    from fb.markets import masks
    W, P = masks({"kind": "ah", "o": "A", "h": 0.75}, 10)
    assert W[2, 1] == 0 and P[2, 1] == 0.5           # casa vince 2-1: ospite +0.75 = mezza persa, mezza rimborso
    W, P = masks({"kind": "ah", "o": "H", "h": -0.25}, 10)
    assert W[1, 1] == 0 and P[1, 1] == 0.5 and W[2, 1] == 1
    W, P = masks({"kind": "ah", "o": "H", "h": -1}, 10)
    assert P[2, 1] == 1 and W[3, 1] == 1


def test_api_asian_handicap_sign():
    """Nell'API 'Away +0.5' deve valere come ospite -0.5: stessa quota dell'ospite vincente (Bologna-Inter)."""
    from fb.apifootball import quotes
    qs = quotes(json.loads(FIX.read_text())["response"][0]["bookmakers"], mine=["Bet365"])
    q = {(x["bet_id"], x["value"]): x["best"] for x in qs}
    assert q[(4, "Away +0.5")] == q[(1, "Away")]
    sel = parse("ah", "Away +0.5")
    assert sel == {"o": "A", "h": -0.5}
    M = grid()
    assert abs(prob(M, dict(sel, kind="ah"))[0][0] - prob(M, {"kind": "1x2", "o": "A"})[0][0]) < 1e-9
