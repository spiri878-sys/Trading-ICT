"""CONTROPRONOSTICO DOPPIA CHANCE sul movimento delle quote (gratis, senza chiavi).

Idea (dal metodo del tipster "apre a X, chiude favorita"): quando il mercato sposta i soldi sulla SFAVORITA, la doppia
chance della sfavorita (1X se è la casa, X2 se è l'ospite) è in valore SOLO finché il bookmaker dell'utente (Bet365)
non ha ancora abbassato la quota.

Verifica sul passato (output/contro_dc.md, 2019-2026, 22 campionati europei, probabilità DC della sfavorita che sale
di almeno 7 punti tra apertura e chiusura Pinnacle): 1329 giocate, vinte 58%, quota media 2.01, ROI +10.6% alla quota
Bet365 di APERTURA (7 stagioni su 7 in utile); alla quota a metà movimento +2%; alla quota di chiusura -6%.
Quindi conta solo prendere la quota VECCHIA: per questo lo script dà la QUOTA MINIMA a cui giocarla, calcolata sulla
probabilità di adesso (quote attuali senza margine) con il 5% di valore. Se Bet365 paga meno: niente giocata.

Fonti: quote di apertura e attuali DraftKings dalle API pubbliche ESPN (come riferimento al posto di Pinnacle,
che muove di più e prima: segnale più debole). Uso: python football/scripts/contro_dc.py [giorni, default 3]
"""
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fb import espn  # noqa: E402
from fb.data import ROOT  # noqa: E402

SALITA = 0.07        # punti di probabilità DC guadagnati dalla sfavorita (regola verificata: >= 7)
AVVISO = 0.05        # 5-7 punti: in osservazione (ROI storico +6%, 6/7 stagioni)
VALORE = 0.05        # valore minimo sulla quota Bet365 rispetto alla probabilità attuale
# campionati con la verifica (europei con quote Pinnacle storiche); gli altri: solo in osservazione
VERIFICATI = {"E0", "E1", "E2", "E3", "EC", "SC0", "SC1", "SC2", "SC3", "D1", "D2", "I1", "I2", "SP1", "SP2", "F1",
              "F2", "N1", "B1", "P1", "T1", "G1"}


def dec(us):
    """Quota americana ('+135', '-125', 210.0) -> decimale."""
    if us in (None, "", "OFF", "EVEN"):
        return 2.0 if us == "EVEN" else None
    x = float(str(us).replace("+", ""))
    return 1 + x / 100 if x > 0 else 1 + 100 / -x


def fair(h, d, a):
    inv = [1 / h, 1 / d, 1 / a]
    s = sum(inv)
    return [x / s for x in inv]


def ora_it(iso):
    """Orario d'inizio in ora italiana (HH:MM) dall'ISO UTC di ESPN."""
    try:
        return datetime.fromisoformat(iso.replace("Z", "+00:00")).astimezone(ZoneInfo("Europe/Rome")).strftime("%H:%M")
    except (AttributeError, ValueError):
        return ""


def moves(day, tutte=False, max_age=1800):
    with ThreadPoolExecutor(8) as ex:                   # un campionato per thread: scansione in pochi minuti
        parts = ex.map(lambda div: _moves_div(div, day, tutte, max_age), espn.LEAGUES)
    return [r for p in parts for r in p]


def _moves_div(div, day, tutte, max_age):
    out = []
    try:
        evs = espn.scoreboard(div, day, max_age=min(max_age, 600))
    except Exception:  # noqa: BLE001
        return out
    for ev in evs:
        if ev["stato"] != "STATUS_SCHEDULED" and not tutte:
            continue
        try:
            d = espn._get(f"{espn.BASE}/{espn.LEAGUES[div]}/summary?event={ev['id']}", max_age)
            ml = (d.get("pickcenter") or [{}])[0].get("moneyline") or {}
            q = {t: {k: dec((ml.get(s) or {}).get(t, {}).get("odds")) for k, s in
                     (("H", "home"), ("D", "draw"), ("A", "away"))} for t in ("open", "close")}
        except Exception:  # noqa: BLE001
            continue
        if any(v is None or v <= 1 for t in q.values() for v in t.values()):
            continue
        po, pc = fair(q["open"]["H"], q["open"]["D"], q["open"]["A"]), fair(q["close"]["H"], q["close"]["D"],
                                                                             q["close"]["A"])
        dog = 0 if q["open"]["H"] > q["open"]["A"] else 2          # sfavorita all'apertura
        up = (pc[dog] + pc[1]) - (po[dog] + po[1])
        if up < AVVISO:
            continue
        p_now = pc[dog] + pc[1]
        esito = ""
        if ev["stato"] in ("STATUS_FULL_TIME", "STATUS_FINAL", "STATUS_FINAL_AET", "STATUS_FINAL_PEN"):
            c = (d.get("header") or {}).get("competitions", [{}])[0].get("competitors", [])
            sc = {x["homeAway"]: int(x.get("score") or 0) for x in c}
            ok = sc["home"] >= sc["away"] if dog == 0 else sc["away"] >= sc["home"]
            esito = f"{sc['home']}-{sc['away']} {'VINTA' if ok else 'PERSA'}"
        out.append(dict(day=day, ora=ora_it(ev.get("inizio")), div=div, home=ev["home"], away=ev["away"], dog=dog, up=up, p=p_now,
                        p_open=po[dog] + po[1], minq=(1 + VALORE) / p_now,
                        dk=1 / (1 / q["close"]["H" if dog == 0 else "A"] + 1 / q["close"]["D"]),
                        dk_open=1 / (1 / q["open"]["H" if dog == 0 else "A"] + 1 / q["open"]["D"]), esito=esito))
    return out


def allerta():
    """Solo le giocate NUOVE di oggi (regola verificata, partita non iniziata), in un messaggio corto per il telefono.
    Le giocate già segnalate sono in output/allerta_<giorno>.json (nel repository: ogni esecuzione lo aggiorna)."""
    day = str(date.today())
    fn = ROOT / "output" / f"allerta_{day}.json"
    seen = json.loads(fn.read_text()) if fn.exists() else []
    new = []
    for r in sorted(moves(day, max_age=120), key=lambda r: r["ora"]):
        key = f"{r['home']} - {r['away']}"
        if r["up"] >= SALITA and r["div"] in VERIFICATI and key not in seen:
            seen.append(key)
            new.append(r)
    fn.write_text(json.dumps(seen, ensure_ascii=False, indent=1))
    if not new:
        print("NIENTE DI NUOVO")
        return
    for r in new:
        dc, who = ("1X", r["home"]) if r["dog"] == 0 else ("X2", r["away"])
        print(f"{r['ora']} {r['home']}-{r['away']}: {dc} ({who} o pareggio). Gioca su Bet365 SOLO se la doppia chance "
              f"paga almeno {r['minq']:.2f} (DraftKings {r['dk_open']:.2f} -> {r['dk']:.2f}). Singola, importo fisso.")


def main(argv):
    if argv and argv[0] == "--allerta":
        allerta()
        return
    if argv and "-" in argv[0]:                      # una data precisa (anche passata, con i risultati)
        days, tutte = [argv[0]], True
    else:
        days, tutte = [str(date.today() + timedelta(days=k)) for k in range(int(argv[0]) if argv else 3)], False
    rows = []
    for day in days:
        rows += moves(day, tutte)
    rows.sort(key=lambda r: -r["up"])
    lines = [f"# Contropronostici doppia chance sul movimento quote ({days[0]})", "",
             "Regola: la sfavorita prende soldi (probabilità della sua doppia chance salita di almeno 7 punti). "
             "Gioca SOLO se la quota Bet365 della doppia chance è almeno la quota minima: il valore c'è solo sulla "
             "quota vecchia. Storico: vince ~6 volte su 10 a quota ~2, ROI +10% alla quota di apertura, in perdita "
             "alla quota di chiusura. Importi piccoli e fissi.", ""]
    for lvl, test in (("CONTRO DC (regola verificata)", lambda r: r["up"] >= SALITA and r["div"] in VERIFICATI),
                      ("In osservazione (salita 5-7 punti o campionato non verificato)",
                       lambda r: not (r["up"] >= SALITA and r["div"] in VERIFICATI))):
        sel = [r for r in rows if test(r)]
        lines += [f"## {lvl}", ""]
        if not sel:
            lines += ["Nessuna partita.", ""]
            continue
        for r in sel:
            dc, who = ("1X", r["home"]) if r["dog"] == 0 else ("X2", r["away"])
            lines.append(f"- {r['day']} {r['ora']} {r['div']} {r['home']} - {r['away']}: **{dc}** ({who} o pareggio) · "
                         f"probabilità {r['p_open']:.0%} -> {r['p']:.0%} (+{r['up'] * 100:.0f} punti) · "
                         f"gioca se Bet365 paga almeno **{r['minq']:.2f}** (DraftKings {r['dk_open']:.2f} -> {r['dk']:.2f})"
                         + (f" · **{r['esito']}**" if r["esito"] else ""))
        lines.append("")
    txt = "\n".join(lines)
    fn = ROOT / "output" / f"contro_dc_{days[0]}.md"
    fn.write_text(txt)
    print(txt)
    print(f"\nScritto {fn}")


if __name__ == "__main__":
    main(sys.argv[1:])
