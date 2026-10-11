# eur_macro_1k: note di trascrizione

Video muto, 17 frame periodici (p_00001…p_00017, uno ogni 3 s, p_N = (N-1)*3 s) più 4 frame di cambio scena (s_00001…s_00004). Ho letto tutti i frame; quelli identici al precedente (p_00009, p_00010 e p_00011 rispetto a p_00008, p_00017 rispetto a p_00016) li ho saltati. Piattaforma: MetaTrader 5, titolo della finestra "25787667 - VantageMarkets-Demo: Demo Account - Hedge - Vantage Markets (Pty) Ltd - [EURUSD COMPLETE HISTORY,M5]".

Ordine della registrazione: menu Inputs (0–3 s), poi il grafico Graph durante il test (6–21 s), il report Backtest (21–33 s), di nuovo Inputs (33–42 s), infine la schermata "SUBSCRIBE" e il nero (42–48 s).

## 1. Menu input
Le righe compaiono in p_00002 (3 s, parzialmente coperte dall'overlay) e sono pienamente leggibili in p_00012 (33 s), p_00013 (36 s) e p_00014 (39 s). Colonne: Variable / Value / Start / Step / Stop. Le righe sono riportate nell'ordine in cui appaiono a schermo.

| # | Gruppo | Etichetta (verbatim) | Value | Start | Step | Stop |
|---|---|---|---|---|---|---|
| 1 | (nessun gruppo) | AUTOTRADER FOREX CLUB | atfc@gmail.com | | | |
| 2 | IMPOSTAZIONI PRINCIPALI | BE + PARZIALE LIBERA IL POSTO (false = conteggio normale) | true | false | | true |
| 3 | IMPOSTAZIONI PRINCIPALI | PREMIUM (false = celle originali, come ora) | false | false | | true |
| 4 | IMPOSTAZIONI PRINCIPALI | PREMIUM: quale livello | PREMIUM A    (solo ENTER) | PREMIUM A (solo ENTER) | | PREMIUM A++ (ENTER + MAIN + SEC… (troncato) |
| 5 | IMPOSTAZIONI PRINCIPALI | MERCATO | EURUSD | XAUUSD | | EURUSD |
| 6 | IMPOSTAZIONI PRINCIPALI | MODALITA OPERATIVA | LIVE ACCOUNT | PROP CHALLENGE | | FLIP |
| 7 | IMPOSTAZIONI PRINCIPALI | SET | PRIME MACRO EUR | (interno) | | PRIME MACRO EUR |
| 8 | IMPOSTAZIONI PRINCIPALI | LEVA DEL CONTO | 1:100 | 1:100 | | 1:30 |
| 9 | IMPOSTAZIONI PRINCIPALI | VALORE CONTRATTO INDICI | 0.0 | 0.0 | 0.0 | 0.0 |
| 10 | IMPOSTAZIONI PRINCIPALI | MAGIC NUMBER | 999000 | 999000 | 1 | 9990000 |
| 11 | PROP CHALLENGE | CAPITALE DELLA CHALLENGE | 0.0 | 0.0 | 0.0 | 0.0 |
| 12 | PROP CHALLENGE | QUANTO SPINGERE | EQUILIBRATO | AGGRESSIVO | | PRUDENTE |
| 13 | PROP CHALLENGE | FASE | FASE 1 | FASE 1 | | FASE 2 |
| 14 | PROP CHALLENGE | TRAGUARDO FASE 1 | 10.0 | 10.0 | 1.0 | 100.0 |
| 15 | PROP CHALLENGE | TRAGUARDO FASE 2 | 5.0 | 5.0 | 0.5 | 50.0 |
| 16 | PROP CHALLENGE | LIMITE GIORNALIERO PROP | 4.0 | 4.0 | 0.4 | 40.0 |
| 17 | PROP CHALLENGE | LIMITE TOTALE PROP | 10.0 | 10.0 | 1.0 | 100.0 |
| 18 | PROP CHALLENGE | MISURA DEL TRAGUARDO | EQUITY | EQUITY | | SALDO |
| 19 | PROP CHALLENGE | AL TRAGUARDO | CHIUDI E FERMATI | CHIUDI E FERMATI | | CHIUDI E CONTINUA |
| 20 | PROP CHALLENGE | MARGINE DI SICUREZZA | 0.2 | 0.2 | 0.02 | 2.0 |
| 21 | PROP FUNDED | CAPITALE FINANZIATO | 0.0 | 0.0 | 0.0 | 0.0 |
| 22 | PROP FUNDED | QUANTO SPINGERE | EQUILIBRATO | AGGRESSIVO | | PRUDENTE |
| 23 | PROP FUNDED | AVVISA AL GUADAGNO DI | 0.0 | 0.0 | 0.0 | 0.0 |
| 24 | LIVE ACCOUNT | CAPITALE DEL CONTO | 0.0 | 0.0 | 0.0 | 0.0 |
| 25 | LIVE ACCOUNT | QUANTO SPINGERE | AGGRESSIVO | AGGRESSIVO | | PRUDENTE |
| 26 | LIVE ACCOUNT | CRESCITA DEL LOTTO | COMPOSTO — i lotti crescono col conto | COMPOSTO — i lotti crescono col conto | | BASE FISSA — i lotti restano quelli di par… (troncato) |
| 27 | FLIP | CAPITALE DA FLIPPARE | 0.0 | 0.0 | 0.0 | 0.0 |
| 28 | FLIP | QUANTO SPINGERE | EQUILIBRATO | AGGRESSIVO | | PRUDENTE |
| 29 | FLIP | OBIETTIVO | 2X — RADDOPPIO | 2X — RADDOPPIO | | 5X |
| 30 | FLIP | STOP-PIANO | 30.0 | 30.0 | 3.0 | 300.0 |
| 31 | SUPERVISORE LIQUIAS (intestazione tagliata al bordo inferiore; lettura incerta, forse "LIQUIDAS"/"LIQUIDITÀ") | — | righe non visibili | | | |

Dettagli:
- Nella lista a tendina di CRESCITA DEL LOTTO, aperta in p_00014 (39 s), ci sono due opzioni: "COMPOSTO — i lotti crescono col conto" (selezionata) e "BASE FISSA — i lotti restano quelli di partenza" (lettura dell'ultima parola incerta).
- In p_00013 (36 s) la casella SET è in modalità di modifica (freccia della tendina) e mostra "PRIME MACRO EUR".
- Il menu non scorre oltre la riga STOP-PIANO, quindi i parametri del gruppo SUPERVISORE… e degli eventuali gruppi successivi non sono visibili. Il capitale iniziale non compare tra gli input (CAPITALE DEL CONTO = 0.0); il deposito di 1 000.00 viene dal report.

## 2. Impostazioni del tester
La scheda Settings non viene mai mostrata. Ricostruzione dagli altri frame:
- Simbolo e timeframe: EURUSD COMPLETE HISTORY, M5 (titolo della finestra e del grafico; simbolo custom). Fonte: p_00002…p_00014.
- Periodo: l'asse del grafico parte da 2018.01.01 in p_00003 (6 s); nel grafico finale va da 2018.03.01 a 2026.02.26 (p_00007, 18 s). Le date esatte di inizio e fine impostate nel tester non sono visibili.
- Modellazione, ritardi e leva del tester: non visibili. Il parametro EA LEVA DEL CONTO vale 1:100.
- Deposito iniziale: 1 000.00 (report, p_00008). Valuta non visibile.
- Durata del test: "00:00:14 / 00:00:15" (p_00007). Il test è avvenuto con l'Optimization disattivata (singolo test).
- History Quality: 100%. Bars: 629170. Ticks: 12415124. Symbols: 1.

## 3. Report
Fonte: p_00008 (21 s), identico in p_00009, p_00010 e p_00011.

| Statistica | Valore |
|---|---|
| History Quality | 100% |
| Bars | 629170 |
| Ticks | 12415124 |
| Symbols | 1 |
| Initial Deposit | 1 000.00 |
| Total Net Profit | 4 830 006.92 |
| Gross Profit | 7 747 123.32 |
| Gross Loss | -2 917 116.40 |
| Profit Factor | 2.66 |
| Expected Payoff | 2921.96 |
| Recovery Factor | 54.87 |
| Sharpe Ratio | 13.90 |
| AHPR | 1.0053 (0.53%) |
| GHPR | 1.0051 (0.51%) |
| LR Correlation | 0.97 |
| LR Standard Error | 405 400.15 |
| Z-Score | -5.32 (99.74%) |
| OnTester result | 54.87397091570097 |
| Margin Level | 172.59% |
| Balance Drawdown Absolute | 0.00 |
| Balance Drawdown Maximal | 79 125.00 (1.69%) |
| Balance Drawdown Relative | 13.93% (524.23) |
| Equity Drawdown Absolute | 9.00 |
| Equity Drawdown Maximal | 88 020.00 (1.88%) |
| Equity Drawdown Relative | 16.46% (636.19) |
| Total Trades | 1653 |
| Total Deals | 2656 |
| Short Trades (won %) | 775 (80.90%) |
| Long Trades (won %) | 878 (75.51%) |
| Profit Trades (% of total) | 1290 (78.04%) |
| Loss Trades (% of total) | 363 (21.96%) |
| Largest profit trade | 42 079.25 |
| Largest loss trade | -30 525.00 |
| Average profit trade | 6 005.52 |
| Average loss trade | -8 036.13 |
| Maximum consecutive wins ($) | 28 (343 351.50) |
| Maximum consecutive losses ($) | 5 (-67 825.00) |
| Maximal consecutive profit (count) | 343 351.50 (28) |
| Maximal consecutive loss (count) | -67 825.00 (5) |
| Average consecutive wins | 5 |
| Average consecutive losses | 1 |
| Correlation (Profits,MFE) | 0.73 |
| Correlation (Profits,MAE) | 0.37 |
| Correlation (MFE,MAE) | -0.2101 |

Nota: Total Deals 2656 è maggiore di Total Trades 1653. La differenza (circa 1003 deal in più) è compatibile con chiusure parziali; questa è un'inferenza, non un dato letto.

I tempi di detenzione minimo, medio e massimo non sono visibili: il report non viene scrollato.

### Grafici
**Curva Balance/Equity** (p_00004…p_00007, 9–18 s; finale in p_00007):
- Asse Y finale (verbatim): 5191413, 4889640, 4587866, 4286093, 3984319, 3682546, 3380772, 3078999, 2777225, 2475452, 2173678, 1871905, 1570131, 1268358, 966584, 664811, 363037, 61264, -240510 (ultima lettura incerta).
- Asse X finale: 2018.03.01, 2018.08.07, 2018.11.02, 2019.02.04, 2019.04.29, 2019.07.16, 2019.10.09, 2020.01.03, 2020.12.11, 2021.03.05, 2021.06.07, 2021.09.16, 2021.12.16, 2022.03.24, 2022.06.23, 2022.09.13, 2022.12.13, 2023.03.16, 2023.06.14, 2023.09.22, 2023.12.14, 2024.03.28, 2024.07.01, 2024.10.01, 2025.01.07, 2025.03.28, 2025.07.03, 2025.11.25, 2026.02.26.
- Forma: piatta, vicina allo zero, dal 2018 a circa il 2019; poi una crescita esponenziale e liscia. Dal 2021 sale in modo marcato (circa 0.5M a metà 2021), con la pendenza più ripida tra il 2022 e il 2023. Arriva a circa 3.6M a fine 2023, a circa 4.3M a fine 2024 e a circa 4.9M nel 2026; nell'ultimo tratto (2025–2026) rallenta. Non si vedono drawdown visibili sulla scala del grafico. I valori intermedi sono stime visive dalla griglia.
- Valore massimo dell'asse Y durante il test (angolo in alto): 1097 (p_00003), 10796 (p_00004), 1393704 (p_00005), 4616908 (p_00006), 5191413 (p_00007).
- Deposit Load: barre verdi alte e fitte dal 2018 a circa il 2021; dal 2021 in poi il carico si riduce progressivamente fino a quasi zero (coerente con la crescita del conto). Scala 0.0%–100.0%.

**Entries by hours (Asia,Europe,USA)**, scala 0–660:
- Picco nettissimo alle ore 15, circa 650. Seconda barra alle 16 (circa 280), terza alle 20 (circa 50). Quasi niente nelle altre ore (forse 1–2 alle 14 e 17).
- Profits and losses by hours (scala illeggibile in parte: 747000 / 310250 / 873500 / 436750 / 0): i profitti più alti sono alle 16 (il massimo), poi alle 15 e alle 17, poi alle 18 e alle 19. Barre piccole anche a 0–8 e a 20–23: sono le ore di chiusura dei trade.

**Entries by weekdays**, scala 0–390:
- Picco il Thu (circa 390). Tue, Wed e Fri circa 190 ciascuno (Fri leggermente meno). Mon circa 50. Sun e Sat 0.
- Profits and losses by weekdays (scala 0–2993000): profitti massimi il Thu (circa 2.99M), poi Fri (circa 1.7M), Wed (circa 1.3M), Tue (circa 1.1M) e Mon (circa 0.55M). Le perdite più alte sono il Thu (circa 1.2M).

**Entries by months**, scala 0–100: tutti i mesi tra circa 73 e 97. I più alti sono Dec (circa 97) e Mar (circa 95); i più bassi Oct (circa 73) e Nov (circa 75).
- Profits and losses by months (scala 0–835000): il massimo è Mar (circa 835k), seguito da Jul (circa 700k). Le perdite più alte sono a Dec (circa 340k) e Sep (circa 310k).

## 4. Operazioni
Nel video non compaiono né la lista dei deal/ordini né la scheda History del tester, quindi non ci sono operazioni singole leggibili. trades.csv contiene solo l'intestazione.

## 5. Comportamento sul grafico
- Non c'è alcun grafico prezzo in visual mode. In cima si vede solo una piccola striscia del grafico "EURUSD COMPLETE HISTORY,M5: Euro vs US Dollar 1.16304 1.16312 1.16291 1.16310 252" (p_00008, testo piccolo, letto in parte).
- Il parametro "BE + PARZIALE LIBERA IL POSTO" = true indica break-even e chiusura parziale attivi; il rapporto tra deal e trade è coerente con questo. Le chiusure parziali non sono osservate direttamente.
- Non sono visibili oggetti o pannelli disegnati dall'EA.

## 6. Altro testo
- p_00001 (0 s) e s_00001…s_00003: titolo overlay "ICT RAPTOR AI PRIME" ("PRIME" in magenta) sopra il menu input sfocato.
- p_00002 (3 s), overlay testuale: "EURUSD / SET: PRIME MACRO EUR / AGGRESSIVO / START 1K / LIVE ACCOUNT".
- p_00003 (6 s): overlay sfocato in movimento, illeggibile. Somiglia a "BUONA VISIONE TRADER", che compare in eur_dal2005, ma qui non è confermabile.
- p_00015 (42 s): grafica "SUBSCRIBE" con la campanella. p_00016 e p_00017 (45–48 s): schermo nero.
- Ora di sistema nella taskbar: 23:37–23:38, data 20/08/2026. Account 25787667, VantageMarkets-Demo, Hedge.
- La versione e la data dell'EA non sono visibili.
