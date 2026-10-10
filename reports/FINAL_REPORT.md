# Raptor Recon: report finale di ricerca (XAUUSD)

**In una frase:** con i dati e le fonti disponibili **non è stato trovato un vantaggio statistico robusto** dopo i costi.

- Nessuna cella ICT, nessuna combinazione e nemmeno il benchmark Wyckoff ha aspettativa positiva fuori campione.
- Il filtro AI migliora in modo significativo rispetto alla selezione casuale, ma porta l'aspettativa solo a circa 0R.
- L'EA MQL5 è completo nella struttura, ma **non è stato compilato né eseguito** in MT5 (ambiente non disponibile).

Nessun risultato è stato inventato e nessun risultato negativo è stato rimosso.

## 1. Protocollo di validazione

Periodi fissati **prima** dei test (`python/raptor/pipeline.py: PERIODS`):

| Periodo | Intervallo | Uso |
|---|---|---|
| **dev** | 2018-01-01 → 2021-12-31 | Esplorazione e selezione. Walk-forward interno: training 2018–19, early stopping 2020, verifica 2021 |
| **val** | 2022-01-01 → 2023-12-31 | Conferma di candidati pre-registrati |
| **test** | 2024-01-01 → 2026-10-09 | Congelato fino alla fine |

Registro di ogni accesso a val e test (nessuna regola è stata scelta su val o test):

1. **EXP-03**: filtro ML su M5, valutato su val una volta. Fallito.
2. **VAL-01**: candidato A (H1), valutato su val una volta. Fallito.
3. **benchmark_final** (10/10/2026): **prima apertura del test** per i profili A, W e il candidato A.
4. Riletture del test in `benchmark_r`, `research_metrics`, `ai_comparison`: solo misura, nessuna selezione.

Rischio residuo dichiarato: avendo visto i risultati del test della baseline, nessun **nuovo** candidato può più usare questo test come fuori campione puro. Servirebbero dati successivi a ottobre 2026 o lo storico 2005–2017.

## 2. Registro degli esperimenti (tutti conservati in `experiments/` e `reports/`)

| ID | Ipotesi | Esito | Decisione |
|---|---|---|---|
| BASE | 7 celle su M5 (k = 3), gestione a scala | Costo zero ≈ 0R per tutte; con C1 da −0,2 a −0,45R per trade | Nessun edge lordo |
| EXP-01 | Struttura più ampia (k e TF maggiori) riduce il peso dei costi | Migliora; solo PPK/UNIOF H1 > 0 con pochi casi | Prosegue |
| EXP-02 | Stop minimo 1,5–4 ATR M15 (E-12) | Da −0,31 a −0,08R: meno costo, ancora < 0 | Non sufficiente |
| EXP-03 | Filtro ML (LightGBM) su M5 con stop minimo 3 | Early stopping a 3 alberi, correlazione 0,004; i segnali presi in val vanno peggio | Respinto |
| EXP-04 | Celle su 15m / 30m / 1h / 4h ± allineamento D1 | Edge lordo ≈ 0; le sacche positive hanno 20–60 casi (test multipli) | Respinto |
| EXP-05 | Studio degli eventi (rendimento futuro, senza gestione) | Continuazione PPK/UNIOF su 15m/1h a 4–24 h, t ≈ 2 | Ipotesi H8 |
| EXP-06 | Continuazione HTF con ingresso a mercato e uscite lunghe (100 configurazioni) | Migliore +0,15R (t 1,7) su 1h | Candidato |
| EXP-07 | Vicinato dei parametri (81 punti) | 79% > 0 con C1, 38% > 0 con C2 | Edge sottile |
| **VAL-01** | Candidato A pre-registrato su val | **−0,06R** (C1), −0,10R (C0); griglia val 38% > 0 | **Respinto** |
| EXP-08 | H9 solo long nel trend D1; H10 ML su 15m | H9 negativo ogni anno; H10 ranking 0,05–0,10 ma i presi restano < 0 | Respinti |
| EXP-09 | ML × pool × stop minimo × uscite (walk-forward interno a dev) | Il ranking viene dal **costo / stop**: con lo stop minimo la correlazione diventa < 0 | Respinto |
| EXP-10 | Modello MTF sperimentale con esecuzione M1 (bias H4 + H1, raid + MSS M1) | **Negativo anche a costo zero** (da −0,11 a −0,26R, t fra −2 e −3); variante M5: 11–13 trade | Respinto |
| SPREAD | Diagnosi della colonna spread | Unità 2018–22 probabilmente 0,001 (INFERITO) | Aggiunto lo scenario C0R |
| AI | Filtro AI (soglia viva q80/1000) contro nessun filtro e contro casuale | Batte il casuale in val e test, ma è ≈ 0R nel test e < 0 in val | Disabilitato nel profilo finale |

Circa 330 configurazioni valutate su dev: qualsiasi "migliore" scelto fra queste sarebbe ottimistico. Per questo nessuna è stata promossa senza la validazione.

## 3. Metriche per cella (R isolata per segnale, costo C1; `reports/research_metrics.csv`)

| Gruppo | dev R (n) | val R (n) | test R (n) | PF test | Costo zero (dev / val / test) |
|---|---|---|---|---|---|
| PPK | −0,24 (1175) | −0,23 (583) | −0,12 (849) | 0,78 | −0,01 / −0,06 / −0,03 |
| MSS | −0,26 (699) | −0,16 (350) | −0,21 (508) | 0,63 | −0,01 / −0,01 / −0,13 |
| OTEOF (OTE) | −0,41 (3331) | −0,36 (1602) | −0,23 (2025) | 0,61 | −0,03 / −0,07 / −0,07 |
| PO3 | −0,16 (76) | −0,23 (35) | +0,31 (43) | 1,78 | −0,03 / −0,19 / +0,32 |
| UNIOF (Unicorn) | −0,20 (1669) | −0,14 (880) | −0,12 (1362) | 0,76 | +0,05 / +0,00 / −0,02 |
| LS (Liquidity Sweep) | −0,45 (703) | −0,40 (376) | −0,19 (525) | 0,69 | +0,01 / +0,08 / +0,01 |
| SILVER_BULLET | −0,23 (2698) | −0,22 (1340) | −0,08 (1978) | 0,84 | −0,00 / −0,05 / +0,01 |
| Combinazione 6 del sito | −0,30 | −0,27 | −0,15 | 0,73 | +0,01 / −0,04 / −0,02 |
| Combinazione fedele 5 | −0,32 | −0,29 | −0,17 | 0,70 | +0,01 / −0,04 / −0,03 |
| **WYCKOFF** (benchmark) | −0,37 | −0,29 | −0,15 | 0,72 | +0,00 / +0,06 / +0,01 |

Il CSV contiene anche:

- risultati long e short separati;
- risultati per anno;
- durata mediana;
- percentili 5 e 95 di R;
- costi C0R e C2.

PO3 nel test (+0,31, 43 trade) è isolato: dev e val sono negativi, quindi non è un segnale affidabile.

## 4. ICT contro Wyckoff, profilo di riferimento (M5, capitale 1000, lotto 0,10, una posizione; `reports/benchmark_final.csv`)

| Profilo | Periodo | Trade | Netto | PF | Win% | DD max | Note |
|---|---|---|---|---|---|---|---|
| ICT fedele | dev / val / test | 342 / 112 / 71 | −891 / −856 / −803 | 0,65 / 0,31 / 0,32 | 35 / 32 / 30 | 89 / 87 / 83% | Il conto viene azzerato; poi i trade sono rifiutati per margine |
| Wyckoff | dev / val / test | 163 / 155 / 130 | −884 / −842 / −805 | 0,32 / 0,47 / 0,36 | 32 / 32 / 38 | 89 / 87 / 80% | idem |

Il profilo di riferimento (lotto 0,10 su 1000 €) rischia il **10–40% del capitale per trade** con stop strutturali da $10 a $40 sull'oro: è incompatibile con un rischio sostenibile, qualunque sia la strategia.

Confronto indipendente dal sizing (R per segnale, C1), test 2024–26:

| Profilo | R medio | PF |
|---|---|---|
| ICT | −0,168 | 0,69 |
| Wyckoff | −0,149 | 0,72 |

Nessuno dei due supera l'altro in modo significativo, ed entrambi sono negativi. Con rischio all'1%, sia ICT sia Wyckoff perdono l'84–96% in ciascun periodo (`benchmark_r.csv`).

## 5. AI (`reports/ai_comparison.json`, `docs/strategies.md`)

- **Obiettivo**: R netta isolata del segnale.
- **Feature**: 44 a soli rapporti.
- **Modello**: LightGBM; training 2018–20, early stopping sul 2021 (58 alberi).
- **Soglia**: viva, quantile 80% degli ultimi 1000 punteggi.

| Periodo | Tutti | AI accettati (~20%) | Casuale stessa taglia (5–95%) |
|---|---|---|---|
| val | −0,260R | **−0,110R** | −0,259 (−0,305 / −0,214) |
| test | −0,148R | **+0,0006R** (n 1468, t 0,02) | −0,148 (−0,192 / −0,102) |

- Il miglioramento rispetto al casuale è reale e fuori campione, ma l'aspettativa netta resta ≤ 0.
- Le feature principali sono `spread_over_stop` e `stop_atr_d1`: il modello impara soprattutto a evitare i trade in cui il costo è alto rispetto allo stop.
- **Verdetto**: non incluso nell'EA.
- **ONNX**: export riuscito (`models/rr_filter.onnx`, LightGBM → ONNX opset 15). Parità con onnxruntime: p99 della differenza assoluta 1e-7; scarti fino a 0,014 solo sullo 0,1% delle righe, dove una feature float32 coincide con una soglia di split. Non è un modello del venditore.

## 6. Tabella dei requisiti

Legenda della colonna "Verifica":

- **SCRITTO**: codice scritto;
- **CONTROLLATO**: controllo statico o revisione;
- **COMPILATO**: compilato in MetaEditor;
- **TEST AUTO**: pytest;
- **SIM PY**: simulazione Python eseguita;
- **MT5 BT**: vero backtest MT5;
- **OOS**: risultato fuori campione.

| # | Requisito | Stato | File / modulo | Verifica | Risultato / limite |
|---|---|---|---|---|---|
| 1 | Solo XAUUSD, controllo del simbolo | Completato (codice) | `RaptorRecon.mq5: IsXauUsd` | SCRITTO, CONTROLLATO | Non COMPILATO |
| 2 | Fonti e registro delle evidenze | Parziale | `docs/evidence_register.md` | — | Sito e YouTube bloccati dalla rete: usati solo estratti di ricerca, 5 video e 16 screenshot |
| 2.2 | Profili fedele / sperimentale separati | Completato | `ENUM_RR_PROFILE`, `strategies.md` | SIM PY, OOS | |
| 3 | Matrice funzionalità → moduli | Completato | `docs/strategies.md` | — | |
| 4 | Sei strategie del sito + PPK, moduli indipendenti selezionabili | Completato | `strategies/ict.py`, `Cells.mqh` | TEST AUTO (geometria, causalità), SIM PY, OOS | Tutte negative dopo i costi |
| 4.2 | Elementi di struttura senza look-ahead | Completato | `indicators.py`, `setups.py` | TEST AUTO (troncamento) | Order Block "puro" non implementato (solo il breaker) |
| 5 | Multi-timeframe | Completato | `setups.py` (M5 + M15/H1/H4/D1), `MarketModel.mqh` | TEST AUTO, SIM PY | Esecuzione M1 testata: dannosa (EXP-10) |
| 6 | Verifica dati e aggregazione | Completato | `data.py`, manifest | SIM PY | M5 2005 non fornito |
| 6.1 | Diagnosi dello spread | Completato | `spread_diagnosis.py` | SIM PY | Unità 2018–22 INFERITA |
| 7 | AI verificabile, baseline, casuale, ONNX | Completato (ricerca) | `ml.py`, `ai_comparison.py`, `models/` | SIM PY, OOS | Disabilitata: nessun guadagno netto |
| 8 | Ciclo di vita del trade, parziali, BE, runner, ripresa dopo riavvio | Completato | `engine._manage`, `PositionManager.mqh` | TEST AUTO (Python) | Lato MQL5 non COMPILATO né MT5 BT |
| 9 | Lotto fisso 0,08 / rischio % | Completato | `Risk.mqh: RRLot`, `engine` | TEST AUTO, SIM PY | |
| 10 | Stop fisso / percentuale (+ strutturale / ATR) e 4 combinazioni | Completato | `Risk.mqh: RRStopPrice`, `engine` | TEST AUTO (8 combinazioni), SIM PY | |
| 11 | Risk management (DD, perdita giornaliera, margine, spread, trade/giorno, posizioni, tetto di rischio) | Completato (codice) | `Risk.mqh`, `RaptorRecon.mq5` | SCRITTO, CONTROLLATO; TEST AUTO per l'equivalente Python | Il filtro notizie funziona solo live |
| 11b | Rischio che respira (E-27), niente martingala | Completato | `engine`, `CRRAccountGuard` | TEST AUTO (Python) | |
| 12 | Telegram separato | Parziale | `Telegram.mqh` | SCRITTO, CONTROLLATO | **Non testato** |
| 13 | Diagnosi e miglioramento dei backtest, protocollo, metriche | Completato | `experiments/`, `reports/` | SIM PY, OOS | Nessun edge robusto |
| 14 | Verifica degli stop più ampi | Completato | `exp02`, `stop_width_vs_lot.csv` | SIM PY | Riduce il costo, ma l'aspettativa resta < 0 |
| 15 | Wyckoff come benchmark separato | Completato | `strategies/wyckoff.py`, profilo W | SIM PY, OOS | Negativo come ICT |
| 16 | Qualità del codice MQL5 | Parziale | `mql5/` | CONTROLLATO | **Non COMPILATO**, nessun MT5 BT |
| 16b | Confronto EA ↔ simulatore | Strumento pronto | `raptor/compare.py` | TEST AUTO (logica) | In attesa dei log del vero tester |
| 17 | Struttura del progetto e documentazione | Completato | `README.md`, `docs/` | — | |

Contatori: 49 test automatici superati (`python -m pytest tests`). Il controllo statico MQL5 è superato. Compilazioni MQL5 eseguite: **0**. Backtest MT5 eseguiti: **0**.

## 7. Limiti noti e attività non completate

Vedi `docs/limits.md`.
