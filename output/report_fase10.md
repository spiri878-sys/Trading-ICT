# Fase 10 (anticipata) — Piano B: nuove strategie, Market Brain, portafoglio di celle

**Codice e risultati:**
- codice: `python/scripts/phase10_planb.py`; nuove celle in `python/raptor/prime/cells.py` (SB, MSS, JUDAS, OB, con test di non-lookahead);
- risultati: `output/phase10_results.json`, `output/phase10_cell_grid_oof.csv`.

**Regole:**
- ogni scelta (soglie per cella, celle ammesse, tabella del Market Brain) è fatta **solo sul fuori campione 2011–2017**;
- la validazione 2018–2021 è applicata **senza ritocchi**;
- test 2022+ non usato;
- stop 3 × ATR M15, gestione FOTO, costi C1 (e C2 = doppi per lo stress).

**Criterio di "vantaggio solido"**, fissato prima dei risultati: in validazione R medio ≥ +0,08, PF ≥ 1,15, almeno 3 anni positivi su 4, ancora positivo con costi C2.

## 1. Le 10 celle

**Segnali 2005–2021:**

| Cella | Segnali |
|---|---|
| LS | 40.623 |
| PPK | 37.576 |
| SB | 8.301 |
| OB | 7.388 |
| BB | 7.087 |
| MSS | 5.995 |
| OTEOF | 4.327 |
| UNIOF | 2.388 |
| PO3 | 616 |
| JUDAS | 465 |

**Senza filtri** sono tutte negative: tutte le celle insieme danno −0,088R sul 2011–17 e −0,102R sul 2018–21.

**Con il filtro AI della cella** (selettore e gate, soglie scelte sul 2011–2017). Sono ammesse le celle positive in almeno 5 anni su 7 con almeno 20 operazioni all'anno:

| Cella | Soglie (sel / gate) | 2011–17 fuori campione | **2018–21 validazione** | Anni + | Con costi C2 |
|---|---|---|---|---|---|
| **LS (Liquidity Sweep)** | 0,9 / 0,7 | +0,122R | **+0,113R · PF 1,27 · 702 op. (175/anno)** | **3/4** | **+0,015R** |
| PPK (Raptor) | 0,8 / 0,5 | +0,055R | −0,024R | 2/4 | −0,101R |
| SB (Silver Bullet) | 0,9 / 0 | +0,094R | +0,006R | 2/4 | −0,026R |
| OB (Order Block) | 0,9 / 0 | +0,073R | −0,042R | 2/4 | −0,177R |
| OTEOF | 0,7 / 0,5 | +0,077R | −0,074R | 2/4 | −0,169R |
| PO3, UNIOF, BB, MSS, JUDAS | — | non ammesse (nessuna soglia stabile sul 2011–17) | — | — | — |

## 2. Portafoglio e Market Brain (validazione 2018–2021)

| Motore | 2011–17 | **2018–21** | Anni + | C2 | Operazioni/anno |
|---|---|---|---|---|---|
| Portafoglio delle 5 celle ammesse | +0,079R · PF 1,18 | **+0,016R** · PF 1,04 | 3/4 (2019: −104R) | −0,068R | 567 |
| Portafoglio + Market Brain | +0,169R · PF 1,40 | **−0,002R** | 2/4 | −0,085R | 336 |
| Market Brain senza AI | +0,109R | **−0,072R** | 2/4 | −0,150R | 133 |
| **Solo LS filtrata** | +0,122R | **+0,113R · PF 1,27** | 3/4 | **+0,015R** | 175 |

**Lettura:**
- **Il Market Brain è un'illusione da adattamento.** Sul 2011–17 raddoppia il risultato (+0,17R), sul 2018–21 lo azzera. La tabella "quale cella in quale fase" non si ripete negli anni successivi.
- **Il portafoglio completo non regge:** +0,016R è come la Fase 5 e diventa negativo con costi doppi.
- **Una sola cella regge da sola: la Liquidity Sweep filtrata dall'AI.**
  - Scelta sul 2011–17 (+0,12R) e **confermata sul 2018–21 senza ritocchi** (+0,11R, PF 1,27).
  - È l'unica configurazione di tutto il progetto che **supera il criterio di vantaggio solido**, anche se di poco con costi doppi (+0,015R).
  - È la cella dove, secondo il sito del venditore, "lavora di più il supervisore AI".
- **Cautela:**
  - 5 celle ammesse sul 2011–17 e una sola confermata: una parte del risultato può essere fortuna;
  - il 2019 è negativo (−24R);
  - con costi doppi il margine è quasi zero.

## 3. Verdetto

| Motore | Supera il criterio? |
|---|---|
| Catena PRIME completa (Fase 5) | No (+0,025R onesto) |
| Portafoglio Piano B | No |
| Portafoglio + Market Brain | No |
| **Solo Liquidity Sweep + AI (selettore ≥ 90°, gate ≥ 70°)** | **Sì, al limite** |

## 4. Proposta per proseguire

1. **Motore operativo dell'EA** per le Fasi 6–9: **cella Liquidity Sweep (M3) con selettore e gate AI**, stop 3 × ATR M15 e gestione FOTO. Circa 175 operazioni all'anno, cioè circa 3–4 a settimana. Le altre celle restano nel codice e nel menu, ma **spente di default** (come i set certificati del venditore, che attivano solo alcune celle).
2. **Prima di costruire macro, Premium ed EA,** due controlli di robustezza sulla sola LS, ancora **senza toccare il test**:
   - variazione delle soglie e dei parametri della cella (sensibilità);
   - costi realistici del tuo broker (con spread reale 0,15–0,20 $ il margine migliora).
3. Poi Fasi 6–9 sulla LS, e **una sola prova finale sul test 2022–2026** (Fase 9).

**Fine Fase 10 (Piano B). Attendo il tuo ok.**
