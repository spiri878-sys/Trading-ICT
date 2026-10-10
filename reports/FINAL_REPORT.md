# Raptor Recon: report finale di ricerca (XAUUSD)

> **Aggiornamento: secondo giro di ricerca, solo ICT (sezione 0).** Un selettore walk-forward annidato su 1008 configurazioni ICT ha isolato un candidato debole ma coerente: il **profilo C, Unicorn LONG** (M15, stop oltre lo swing H4, TP 3R / 48h). Con rischio 1%: +58% nel 2018–2026 (PF 1,32, DD max 15%) e +26% nel tratto walk-forward 2022–2026 (PF 1,27, DD 9%). Robusto a costi e parametri vicini, ma **il lato short perde sempre**: gran parte del vantaggio è la tendenza rialzista dell'oro, non l'ICT in sé. Le prime righe qui sotto descrivono il primo giro e restano valide per i profili A e B.

## 0-bis. Terzo giro: Wyckoff multi-timeframe con gestione AI (richiesta del 10/10/2026)

**Modello** (`python/raptor/strategies/wyckoff_mtf.py`, SPERIMENTALE):

- **Contesto**: trading range laterale su 48–120 h (altezza 3–15 ATR H1, deriva ≤ 50% dell'altezza).
- **Evento su M15**: Spring o Upthrust oltre il range con rientro; filtro opzionale sul tick volume.
- **Conferma**: SOS / SOW (rottura della struttura M15).
- **Ingresso**: a mercato sul SOS oppure sul pullback LPS.
- **Stop e target**: stop oltre lo spring; target sul lato opposto del range (R/R ≥ 1,5).

| ID | Test | Esito |
|---|---|---|
| WY-01 | 48 set di segnali × 5 gestioni × {entrambi, long, short} = 720 configurazioni; stesso selettore walk-forward annidato di WF-01 | **OOS 2020–2026: −0,004R/trade su 835 trade (t −0,12)**. Annuale (somma R): +12,8 / +34,6 / +5,0 / −14,9 / −3,8 / −1,4 / −35,9. Sull'intero periodo solo il 28% delle configurazioni è > 0; la migliore ha t 1,6 (solo long, in-sample) |
| WY-02 | **Gestione AI**: per ogni trade un LightGBM per politica (range TP, range TP + 50% a 1R + BE, scala del venditore, TP 2R, 50% a 1R + BE + trailing 2 ATR) sceglie la politica o salta il trade, addestrato solo sugli anni precedenti | AI: **−0,073R** (con salto: −0,051R). Migliore politica fissa (trailing): −0,029R. Politica "migliore finora": −0,068R. **L'AI non migliora la gestione** |

**Verdetto**: il Wyckoff multi-timeframe non ha vantaggio fuori campione su XAUUSD 2020–2026, nemmeno con la gestione AI. Non è stato aggiunto come profilo raccomandato.

File:

- `experiments/wy01_selector.csv`
- `experiments/wy01_full_period_configs.csv`
- `experiments/wy02_ai_exit_policy.json`

## 0. Secondo giro: ricerca solo ICT (Wyckoff escluso)

| ID | Ipotesi | Esito |
|---|---|---|
| WF-01 | Selettore walk-forward annidato. Ogni anno Y dal 2020 al 2026 sceglie le 5 configurazioni con il t-stat più alto, usando solo i dati < Y. Griglia: 7 celle × {M5, M15} × stop {strutturale, min 2 ATR M15, swing H1, swing H4} × uscite {scala del venditore, TP 3R 48h, TP 2R 24h} × bias {nessuno, H1, H4} × {entrambi, solo long} | **OOS 2020–2026: +0,003R/trade su 1989 trade (t 0,12)**. Annuale (somma R): 2020 +15,5, 2021 −20,6, 2022 −52,0, 2023 +19,0, 2024 +15,6, 2025 +17,2, 2026 +11,5. Dal 2022 il selettore converge su Unicorn long M15 con stop H4 |
| WF-02 | Il sopravvissuto contro ingressi long **casuali** con la stessa distribuzione di stop e la stessa uscita | Strategia +0,167R (396 trade, t 2,43). Casuale in media +0,03R, con banda 5–95% annuale circa da −0,3 a +0,5. Nel tratto 2022–26: +0,15R contro +0,06R del casuale. **Vantaggio di timing ~+0,1R, non significativo** |
| WF-03 | Metodo dichiarato dal venditore: gradient boosting **riaddestrato ogni anno** su tutti i segnali delle celle, stop larghi H1/H4, soglia viva q80/1000 | **OOS 2020–2026: −0,055R** (3457 trade, t −3,0; pool primario pre-registrato M5, stop H1, scala), negativo in 6 anni su 7. Varianti: −0,05 / −0,10 / −0,06R |
| C-PORT | Profilo C in portafoglio: 1 posizione, rischio 1%, capitale 10.000 | C1: +58,4% nel 2018–26 (331 trade, PF 1,32, DD 15,1%, 42,6% vincenti); 2022–26: +25,6% (PF 1,27, DD 8,7%). C0R: +68,6%. C2 (costi ×2): +48,6%. Anni negativi: 2018 (−1066 $) e 2026 fino a ottobre (−394 $) |
| C-ROB | Vicinato: k {2, 3, 4} × TP {2, 3, 4} × durata {24, 48, 96 h} × stop {H1, H4}, long e short | Long: 93% delle varianti > 0 (2022–26: 100%), mediana +0,09R. **Short: 0% > 0**, mediana −0,14R |

**Lettura onesta.**

- Il profilo C è la cosa migliore trovata ed è stabile, ma si basa sul presupposto che l'oro continui a salire.
- Rispetto a un long casuale aggiunge poco: circa +0,1R per trade, non significativo.
- Non è stato scelto su dati futuri: dal 2022 il selettore lo indicava usando solo gli anni precedenti.
- Però questo stesso secondo giro di ricerca è stato fatto dopo aver visto i periodi val e test del primo giro. Il vero banco di prova sono i dati successivi a ottobre 2026 e il demo.

File:

- `experiments/wf01_selector.csv`
- `experiments/wf02_unicorn_vs_drift.json`
- `experiments/wf03_ml_walkforward.json`
- `experiments/candidate_c_robustness.csv`
- `reports/candidate_c_portfolio.json`
- `reports/trades_CAND_C_*.csv`

**In una frase (primo giro):** con i dati e le fonti disponibili **non è stato trovato un vantaggio statistico robusto** dopo i costi per i profili A e B. Il profilo C (sezione 0) è positivo, ma dipende dalla tendenza rialzista dell'oro.

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
