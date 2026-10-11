"""FASE 1: estrae dal salvataggio HTML del sito del venditore il testo visibile, i dati nascosti delle schede
(oggetto JS `D`: 18 set x statistiche/modi/combinazioni, `LIVELLI`, operazioni d'esempio `OP`) e le immagini
incorporate. Nessun numero viene ricopiato a mano.

usage: python python/scripts/phase1_site_data.py <pagina.html>
out:   output/sito/testo.txt, output/sito/dati.json, output/sito/img/*.jpg, output/sito/numeri_sito.md
"""
import base64
import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "output" / "sito"

SET_COLS = ["set", "operazioni", "operazioni_anno", "win_rate", "rapporto", "tenuta", "challenge_prob_giorni"]


def js_literal(src, name):
    """Extract `const|var NAME = {...};` or [...] and convert the JS object literal to JSON."""
    m = re.search(r"(?:const|var|let)\s+" + name + r"\s*=\s*", src)
    i = m.end()
    open_c = src[i]
    close_c = {"{": "}", "[": "]"}[open_c]
    depth, j, in_s, q = 0, i, False, ""
    while True:
        ch = src[j]
        if in_s:
            if ch == "\\":
                j += 2
                continue
            if ch == q:
                in_s = False
        elif ch in "'\"":
            in_s, q = True, ch
        elif ch == open_c:
            depth += 1
        elif ch == close_c:
            depth -= 1
            if depth == 0:
                break
        j += 1
    lit = src[i:j + 1]
    lit = re.sub(r"'((?:[^'\\]|\\.)*)'", lambda mm: json.dumps(mm.group(1).replace("\\'", "'")), lit)
    lit = re.sub(r"([{,]\s*)([A-Za-z_]\w*)\s*:", r'\1"\2":', lit)
    lit = re.sub(r",(\s*[}\]])", r"\1", lit)
    return json.loads(lit)


def main(path):
    OUT.mkdir(parents=True, exist_ok=True)
    s = Path(path).read_text(encoding="utf-8", errors="replace")
    # visible text
    t = re.sub(r"(?is)<(script|style|svg)[^>]*>.*?</\1>", " ", s)
    t = re.sub(r"(?i)<br\s*/?>|</(p|div|h\d|li|tr|section|td|th)>", "\n", t)
    t = html.unescape(re.sub(r"<[^>]+>", " ", t))
    t = "\n".join(re.sub(r"[ \t]+", " ", x).strip() for x in t.split("\n") if x.strip())
    (OUT / "testo.txt").write_text(t)
    scripts = re.findall(r"(?is)<script[^>]*>(.*?)</script>", s)
    big = max(scripts, key=len)
    D = js_literal(big, "D")
    LIV = js_literal(big, "LIVELLI")
    i = big.find("var OP=") + 7
    OP, _ = json.JSONDecoder().raw_decode(big[i:])
    imgs = re.findall(r"data:image/(\w+);base64,([A-Za-z0-9+/=]+)", big)
    (OUT / "img").mkdir(exist_ok=True)
    names = []
    for k, (ext, b) in enumerate(imgs):
        nm = OP[k]["f"] if k < len(OP) else f"img_{k}.{ext}"
        (OUT / "img" / nm).write_bytes(base64.b64decode(b))
        names.append(nm)
    data = {"versioni": D, "livelli_challenge": LIV, "operazioni_esempio": OP, "immagini": names}
    (OUT / "dati.json").write_text(json.dumps(data, indent=1, ensure_ascii=False))
    # markdown tables
    md = ["# Numeri del sito (estratti automaticamente da `phase1_site_data.py`)", "",
          "Fonte: pagina principale salvata dal cliente. Colonne del set: operazioni totali, operazioni/anno, win rate, "
          "rapporto (vincita media/perdita media, \"ogni vincita vale una volta e mezza una sconfitta\" per 1,45), "
          "tenuta (% simulazioni che non violano i limiti), probabilità/giorni della challenge.", ""]
    for v, d in D.items():
        md += [f"## {d['label']}", "", "| " + " | ".join(SET_COLS) + " |", "|" + "---|" * len(SET_COLS)]
        md += ["| " + " | ".join(r) + " |" for r in d["sets"]]
        md += ["", "Combinazioni (rendimento, drawdown):", "", "| combinazione | rendimento | drawdown |", "|---|---|---|"]
        md += ["| " + " | ".join(r) + " |" for r in d["combo"]]
        md += ["", "| set | challenge: rischio | prob. | giorni attesi | giorni minimi |", "|---|---|---|---|---|"]
        md += ["| " + " | ".join(r) + " |" for r in d["challenge"]]
        md += ["", "| set | funded: rischio | rendimento |", "|---|---|---|"] + ["| " + " | ".join(r) + " |" for r in d["funded"]]
        md += ["", "| set | live: rischio | rendimento |", "|---|---|---|"] + ["| " + " | ".join(r) + " |" for r in d["live"]]
        md += ["", "| set | flip: rischio | prob. | giorni |", "|---|---|---|---|"] + ["| " + " | ".join(r) + " |" for r in d["flip"]]
        md += [""]
    md += ["## Livelli (challenge, % e giorni per Aggressivo / Equilibrato / Prudente)", "", "```",
           json.dumps(LIV, ensure_ascii=False), "```", "", "## Operazioni d'esempio sul terminale", ""]
    md += [f"- **{o['mkt']} · {o['tf']} · {o['cella']}** — {o['tit']}: {o['d']} (immagine `img/{o['f']}`)" for o in OP]
    (OUT / "numeri_sito.md").write_text("\n".join(md) + "\n")
    print(len(D), "versioni,", sum(len(d["sets"]) for d in D.values()), "set,", len(OP), "operazioni,", len(names), "immagini")


if __name__ == "__main__":
    main(sys.argv[1])
