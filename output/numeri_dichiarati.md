# Numeri dichiarati dal venditore (da confrontare in Fase 9)

**Condizioni dei test del venditore:**
- Tutti i numeri del sito vengono da "Strategy Tester e Monte Carlo, non da conto reale".
- Nella scheda Settings del video NAS steroid: **"1 minute OHLC" e "Zero latency, ideal execution"**, leva 1:500.
- I backtest dei video usano **lotti composti** (CRESCITA DEL LOTTO = COMPOSTO) e modo LIVE / AGGRESSIVO, partendo da 1.000. I rendimenti in valuta sono quindi enormi e non si confrontano 1:1 con un rischio fisso.

## 1. Sito (estrazione automatica: `output/sito/numeri_sito.md`, `output/sito/dati.json`)

- **Totali:** 18 set misurati, 34.788 operazioni analizzate, 168 modelli AI in un file, 504 righe di rischio, 6 celle.
- **Versioni:**
  - CORE: 8.300 operazioni, win rate migliore 77,9% (EUR CORE 1), challenge più rapida 27 giorni, drawdown della combinazione 16,3%.
  - PLUS: 13.315 operazioni, miglior rapporto 1,45 (XAU PLUS 2), challenge più rapida 13 giorni, 374 operazioni/anno.
  - PRIME: 3 livelli Premium, 93 modelli macro, 72 combinazioni tarate, 3.846 operazioni di calibrazione. "100%: due set del PRIME arrivano al traguardo della challenge in tutte le simulazioni".
- **Set XAU della PRIME:**

| Set | Operazioni | Op./anno | Win rate | Rapporto (vincita / perdita media) | Tenuta | Challenge (prob. / giorni) |
|---|---|---|---|---|---|---|
| XAUUSD PRIME 1 | 1.913 | 90 | 63,7% | 1,18 | 86% | 76% / 165 gg |
| XAUUSD PRIME 2 | 1.557 | 73 | 66,3% | 1,05 | 100% | 96% / 89 gg |

  Profit factor implicito = win × rapporto / (1 − win): **PRIME 1 ≈ 2,07; PRIME 2 ≈ 2,06**. È un calcolo nostro.

- **Modi, set XAU della PRIME:**

| Set | Funded (rischio, rendimento) | Live (rischio, rendimento) | Flip (rischio, prob., giorni) |
|---|---|---|---|
| XAUUSD PRIME 1 | 0,35% · 13% | 1,22% · 55% | 4,95% · 47% · 75 gg |
| XAUUSD PRIME 2 | 0,90% · 28% | 2,09% · 72% | 6,00% · 58% · 85 gg |

- **Calibrazione Prop Challenge, oro:**

| Livello | Rischio | Prob. +10% | Giorni |
|---|---|---|---|
| Aggressivo | 2,40% | 95,4% | 6 |
| Equilibrato | 1,60% | 99,3% | 10 |
| Prudente | 1,00% | 99,9% | 17 |

  Metodo: Monte Carlo, 3.000 giri a blocchi, 3.846 operazioni 2018–2026, "sulla metà di periodo vista meno dalla taratura".
- **Livelli della PRIME (challenge sui 6 set):**

| Livello | Prob. | Giorni tipici | Set più rapido (giorni) | Quarto valore |
|---|---|---|---|---|
| Aggressivo | 88% | 24 | 15 | 44 (significato non dichiarato) |
| Equilibrato | 98% | 81 | 72 | 96 |
| Prudente | 93% | 124 | 111 | 151 |

- **Combinazioni PRIME:** la migliore è XAUUSD PRIME 1 + NAS PRIME 2 + EURUSD PRIME 2, con +500,6% e drawdown 19,2%.

## 2. Video (`output/video/*/note.md`)

| Video | Set / modo | Periodo | Trade / deal | PF | Win % | DD max (saldo) | Utile netto (da 1.000, lotti composti) | Note |
|---|---|---|---|---|---|---|---|---|
| **XAU** | XAUUSD PRIME 1, LIVE, AGGRESSIVO | simbolo "XAUUSD_2005_TO_MAY 2025", grafico 2007 → 2026-03, M5, Vantage demo | **4.646 / 6.152** | **1,46** | **85,21%** (short 88,33%, long 82,57%) | **18,69%** (equity 20,59%) | 181.133,61 | Payoff medio: vincita 144,76 / perdita −570,54 (rapporto 0,25); serie massime 60 vincite / 8 perdite; picco d'ingressi all'**ora server 01**; marzo unico mese negativo; Sharpe 2,40, Recovery Factor 4,90 |
| EUR macro | PRIME MACRO EUR, LIVE, AGGRESSIVO | circa 2018-01 → 2026-02 | 1.653 / 2.656 | 2,66 | 78,04% | 1,69% (relativo 13,93%) | 4.830.006,92 | Ingressi alle **15** (circa 650) e 16 server; giovedì |
| EUR dal 2005 | EURUSD PRIME 2 | 2005-01-31 → 2025-12-08 | 8.059 / 11.876 | 2,08 | 83,03% | relativo 9,35% | 36.024.514,10 | Durata media 10 h 40 min |
| NAS macro | PRIME MACRO NAS | dal 2018-01-01 | 1.005 / 1.607 | 3,07 | 80,90% | 7,03% (relativo 11,25%) | 2.829.898,41 | Ingressi alle 15–23 server |
| NAS steroid | NAS PRIME 1 | 2018-01-01 → 2026-08-30, 1 minute OHLC, zero latency | 1.786 / 2.409 | 2,84 | 85,78% | 6,48% (relativo 17,55%) | 1.081.854,28 | Leva 1:500 |

**Osservazioni sul video XAU:**
- Win rate 85% ma perdita media circa 3,9 volte la vincita media. È tipico di una gestione con parziali e pareggio: molte piccole vincite e poche perdite piene.
- Deal / trade = 1,32: in media un'uscita parziale ogni 3 trade circa (inferenza).
- Circa 240 operazioni all'anno sul 2007–2026, contro le 90 all'anno di "XAUUSD PRIME 1" nella tabella del sito. **Incongruenza** da segnalare: forse versioni o periodi diversi.

## 3. Foto (`output/foto/note.md`), "tester 2026", modelli congelati al 31/12/2025

- **XAUUSD 2026:**
  - 169 trade, PF 1,7, conto +99% al 24/09/2026 (rischio base 1,92%, che "respira");
  - 172 trade nel Monte Carlo: 5° percentile +31%, mediana +107%, 95° percentile +241%, 99% dei percorsi in utile.
- **Segnali XAU 2026:**
  - 1.733 giudicati, 169 presi (10%) al 21/09; 1.751 e 175 al 23/09;
  - 1.607 rifiuti; 1.788 segnali, di cui 52 "seri".
- **Tre mercati sullo stesso conto:** +126% senza composizione (oro +99%, NAS +11%, EUR +1?%).
- **Costi:** 0,019R per trade su oro e NAS, 0,074R su EUR; swap XAU −79,48 $ / +34,41 $ per lotto e notte.
- **Modello:** "VEDE-25", gradient boosting, 1.500 alberi, 127 foglie, 49.000 segnali (oro ed EUR dal 2005, NAS dal 2018), 92 ingressi.
  - Soglia viva = quantile 80% degli ultimi 1.000 punteggi; soglia fissa r39 = 0,2426.

## 4. Manuale V5

- 5 strategie, 12 celle certificate, 37 reti (15 + 16 + 3 + 3), calendario dal 2007.
- Nessun numero di performance.

## 5. Incongruenze fra le fonti (da tenere presenti)

1. **Celle:** 6 nella PRIME (SITO), 5 nel V5 (manca Breaker Block), 5 nelle foto (PPK, OTEOF, PO3, UNIOF, LS).
2. **Modelli AI:** 168 (SITO), 37 (V5), 3 nominati nelle foto (VEDE-25, G_CELLA, MODELLO8). Sono generazioni diverse.
3. **Gestione:** parziale "90% a +1R" (V5) contro "20% a 0,7R, 20% a 2R, 60% a 4R" (foto).
4. **Frequenza XAU:** 90 operazioni all'anno (sito PRIME 1), circa 240 all'anno (video XAU 2007–2026), circa 230 all'anno (foto 2026, 169 trade in 9 mesi).
5. **Dati del venditore:** test con "1 minute OHLC" ed esecuzione ideale, quindi ottimistici. Il nostro simulatore è prudente.
