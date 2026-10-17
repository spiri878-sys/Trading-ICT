"""Tabella finale dei mercati (punto 4 del piano) da models/m4_config.json e models/m4_money.json.
Scrive football/output/m4_mercati.md. Uso: python football/scripts/m4_report.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fb.apifootball import user_books  # noqa: E402
from fb.data import ROOT  # noqa: E402
from fb.picks import PROVEN, STAT_IT  # noqa: E402

APP = {"A": "classico (forze dinamiche)", "B": "LightGBM", "C": "media classico+LightGBM", "D": "mercato (Pinnacle)",
       "E": "LightGBM + mercato"}
KIND = {"ou_tot": "Over/Under totale", "ou_home": "Over/Under casa", "ou_away": "Over/Under ospite", "1x2": "1X2",
        "dc": "doppia chance", "dnb": "draw no bet", "ah": "handicap asiatico", "eh": "handicap europeo",
        "btts": "Gol/NoGol", "oe_tot": "pari/dispari", "oe_home": "pari/dispari casa", "oe_away": "pari/dispari ospite",
        "exact_tot": "numero esatto", "range_tot": "multi (fasce)", "cs": "risultato esatto", "res_btts": "1X2 + Gol/NoGol",
        "res_tot": "1X2 + Over/Under", "tot_btts": "Over/Under + Gol/NoGol", "clean_home": "porta inviolata casa",
        "clean_away": "porta inviolata ospite", "scores_home": "segna la casa", "scores_away": "segna l'ospite",
        "nil_home": "casa vince a zero", "nil_away": "ospite vince a zero", "hh_htft": "parziale/finale",
        "hh_highest": "tempo con più gol", "hh_winboth": "vince entrambi i tempi", "hh_wineither": "vince almeno un tempo",
        "hh_teamboth": "squadra segna in entrambi i tempi", "hh_bttsboth": "Gol in entrambi i tempi",
        "hh_anyboth": "gol in entrambi i tempi"}


def main():
    conf = json.loads((ROOT / "models" / "m4_config.json").read_text())
    money = json.loads((ROOT / "models" / "m4_money.json").read_text())
    books = user_books()
    rows = ["# Mercati: verifica 2022-2026 (mai vista in addestramento)", "",
            "Modello scelto sugli anni 2019-2021. Calibrazione dell'anno Y stimata solo sugli anni prima di Y. "
            "'media' = frequenza dell'evento nello stesso campionato nei 3 anni prima. Stagioni = quota di stagioni "
            "con Brier migliore della media. Fascia 70% = quando dice >= 70%: previsto / uscito.", ""]
    for stat, c in conf["stats"].items():
        rows.append(f"- **{STAT_IT.get(stat, stat)}**: modello {APP.get(c['approach'], c['approach'])}, dispersione "
                    f"casa {c['phi_h']:.2f} / ospite {c['phi_a']:.2f}" + (f", rho {c['rho']:+.2f}" if c["rho"] else ""))
    roi_txt = ", ".join(f"{b}: {v['roi']:+.1%} su {v['giocate']}" for b, v in money.items())
    rows += ["", f"Backtest soldi 1X2 + O/U 2.5 (regole fisse): {roi_txt}. Bookmaker dell'utente: {', '.join(books)}.",
             "", "| mercato | log-loss vs media | calibrazione (errore) | stagioni | fascia 70% | soldi | esito |",
             "|---|---|---|---|---|---|---|"]
    for fam, f in sorted(conf["families"].items()):
        stat, kind, side = fam.split("|")
        name = f"{STAT_IT.get(stat, stat)}: {KIND.get(kind, kind)} {side}".strip()
        top = f"{f['p70']:.0%} / {f['f70']:.0%} ({f['n70']})" if f["n70"] >= 30 else "-"
        if fam in PROVEN:
            ok_money = any(money.get(b, {}).get("roi", -1) > 0 for b in books)
            soldi = "in utile" if ok_money else "in perdita al tuo bookmaker"
        else:
            ok_money, soldi = True, "non provato"
        ok = f["ammesso"] and ok_money
        rows.append(f"| {name} | {f['ll']:.4f} vs {f['ll_media']:.4f} ({1 - f['ll'] / f['ll_media']:+.1%}) | {f['ece']:.3f} | "
                    f"{f['stab']:.0%} | {top} | {soldi} | {'AMMESSO' if ok else 'NON AMMESSO'} |")
    (ROOT / "output" / "m4_mercati.md").write_text("\n".join(rows) + "\n")
    n_ok = sum(1 for r in rows if r.endswith("| AMMESSO |"))
    print(f"{n_ok} famiglie ammesse su {len(conf['families'])}")


if __name__ == "__main__":
    main()
