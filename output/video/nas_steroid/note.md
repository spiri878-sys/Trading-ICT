# nas_steroid: note del video ("NAS PRIME 1" on steroid)

Video muto di circa 99 s, 1280x720. Fotogrammi in `all/`: p_00001 = 0 s, poi uno ogni 3 s (p_N = (N-1)*3 s). s_00001..s_00005 = transizione iniziale (0,2-0,5 s), s_00006 = 14,1 s, s_00007 = 99,3 s (nero finale).
Ho controllato tutti i 40 PNG. p_00005 è uguale a p_00004; p_00031 è uguale a p_00030. p_00012-p_00028 sono stati intermedi della curva di equity.
Orologio di Windows: **31/08/2026**, 21:10-21:11. Market Watch 22:10:17-22:10:30. Conto "25787667 - VantageMarkets-Demo: Demo Account - Hedge - Vantage Markets (Pty) Ltd". Titolo finestra "[NAS100_COMPLETE HYSTORY,M5]".

## 1. Menu input
Il menu si vede in p_00001 (0 s, sotto il titolo), in s_00004 (0,4 s, inclinato) e in **s_00005 (0,5 s, vista pulita, fonte principale)**. La riga evidenziata è LIVE ACCOUNT > QUANTO SPINGERE. Il menu termina in basso nel gruppo FLIP e non viene mai scorso: i gruppi SUPERVISORE LIQBIAS, FILTRO NOTIZIE, MESSAGGI GRAFICA, PREMIUM ecc. **non sono visibili**.
In questa versione compare la riga **"STOP MINIMO IN ATR (0 = spento)"**. La data 31/08/2026 è quella dell'orologio di sistema durante la registrazione: nel menu non c'è un'etichetta di versione con quella data.

| # | Gruppo | Etichetta (verbatim) | Value | Start | Step | Stop | Frame |
|---|---|---|---|---|---|---|---|
| 0 | (intestazione) | AUTOTRADER FOREX CLUB | atfc@gmail.com | | | | s_00005 (0,5 s) |
| 1 | IMPOSTAZIONI PRINCIPALI | BE + PARZIALE LIBERA IL POSTO (false = conteggio normale) | true | false | | true | s_00005 |
| 2 | IMPOSTAZIONI PRINCIPALI | PREMIUM (false = celle originali, come ora) | false | false | | true | s_00005 |
| 3 | IMPOSTAZIONI PRINCIPALI | PREMIUM: quale livello | PREMIUM A    (solo ENTER) | PREMIUM A    (solo ENTER) | | PREMIUM A++    (ENTER + MAIN + SEC... (troncato) | s_00005 |
| 4 | IMPOSTAZIONI PRINCIPALI | MERCATO | NAS100 | XAUUSD | | EURUSD | s_00005 |
| 5 | IMPOSTAZIONI PRINCIPALI | MODALITA OPERATIVA | LIVE ACCOUNT | PROP CHALLENGE | | FLIP | s_00005 |
| 6 | IMPOSTAZIONI PRINCIPALI | SET | NAS PRIME 1 | (interno) | | PRIME MACRO EUR | s_00005 |
| 7 | IMPOSTAZIONI PRINCIPALI | VALORE CONTRATTO INDICI | 0.0 | 0.0 | 0.0 | 0.0 | s_00005 |
| 8 | IMPOSTAZIONI PRINCIPALI | MAGIC NUMBER | 0 | 0 | 1 | 10 | s_00005 |
| 9 | IMPOSTAZIONI PRINCIPALI | STOP MINIMO IN ATR (0 = spento) | 0.0 | 0.0 | 0.0 | 0.0 | s_00005 |
| 10 | PROP CHALLENGE | LEVA IMPOSTA DALLA PROP | 1:100 | 1:100 | | 1:30 | s_00005 |
| 11 | PROP CHALLENGE | CAPITALE DELLA CHALLENGE | 0.0 | 0.0 | 0.0 | 0.0 | s_00005 |
| 12 | PROP CHALLENGE | QUANTO SPINGERE | AGGRESSIVO | AGGRESSIVO | | PRUDENTE | s_00005 |
| 13 | PROP CHALLENGE | FASE | FASE 1 | FASE 1 | | FASE 2 | s_00005 |
| 14 | PROP CHALLENGE | TRAGUARDO FASE 1 | 10.0 | 10.0 | 1.0 | 100.0 | s_00005 |
| 15 | PROP CHALLENGE | TRAGUARDO FASE 2 | 5.0 | 5.0 | 0.5 | 50.0 | s_00005 |
| 16 | PROP CHALLENGE | LIMITE GIORNALIERO PROP | 4.0 | 4.0 | 0.4 | 40.0 | s_00005 |
| 17 | PROP CHALLENGE | LIMITE TOTALE PROP | 10.0 | 10.0 | 1.0 | 100.0 | s_00005 |
| 18 | PROP CHALLENGE | MISURA DEL TRAGUARDO | EQUITY | EQUITY | | SALDO | s_00005 |
| 19 | PROP CHALLENGE | AL TRAGUARDO | CHIUDI E FERMATI | CHIUDI E FERMATI | | CHIUDI E CONTINUA | s_00005 |
| 20 | PROP CHALLENGE | MARGINE DI SICUREZZA | 0.2 | 0.2 | 0.02 | 2.0 | s_00005 |
| 21 | PROP FUNDED | CAPITALE FINANZIATO | 0.0 | 0.0 | 0.0 | 0.0 | s_00005 |
| 22 | PROP FUNDED | QUANTO SPINGERE | EQUILIBRATO | AGGRESSIVO | | PRUDENTE | s_00005 |
| 23 | PROP FUNDED | AVVISA AL GUADAGNO DI | 0.0 | 0.0 | 0.0 | 0.0 | s_00005 |
| 24 | LIVE ACCOUNT | CAPITALE DEL CONTO | 0 | 0.0 | 0.0 | 0.0 | s_00005 |
| 25 | LIVE ACCOUNT | QUANTO SPINGERE | AGGRESSIVO | AGGRESSIVO | | PRUDENTE | s_00005 (riga evidenziata) |
| 26 | LIVE ACCOUNT | CRESCITA DEL LOTTO | COMPOSTO — i lotti crescono col conto | COMPOSTO — i lotti crescono col conto | | BASE FISSA — i lotti restano quelli di par... (troncato) | s_00005 |
| 27 | LIVE ACCOUNT | LEVA DEL CONTO LIVE | 1:500  (come oggi) | 1:30 | | 1:500  (come oggi) | s_00005 |
| 28 | FLIP | CAPITALE DA FLIPPARE | 0.0 | 0.0 | 0.0 | 0.0 | s_00005 |
| 29 | FLIP | QUANTO SPINGERE | EQUILIBRATO | AGGRESSIVO | | PRUDENTE | s_00005 |
| — | FLIP (seguito) e gruppi successivi | non visibili | | | | | — |

Differenze rispetto a nas_macro: SET = NAS PRIME 1 (contro PRIME MACRO NAS); MAGIC NUMBER 0 (contro 999000); nuova riga STOP MINIMO IN ATR; "LEVA DEL CONTO" sparisce da IMPOSTAZIONI PRINCIPALI e diventa "LEVA IMPOSTA DALLA PROP" (PROP CHALLENGE) e "LEVA DEL CONTO LIVE" (LIVE ACCOUNT, 1:500); PROP CHALLENGE > QUANTO SPINGERE = AGGRESSIVO (contro EQUILIBRATO); LIVE ACCOUNT > CAPITALE DEL CONTO "0" (contro "0.0").

### Nomi interni degli input (commento del grafico NAS100 in alto)
Riga di testo sul grafico prezzi in p_00001-p_00004 (ritaglio da p_00003, 6 s), con lettura parziale per via della bassa risoluzione:
`ICT RAPTOR AI PRIME - AUTOTRADER FOREX CLUB - 000000 [InpClientEmail=atfc@gmail.com;  ...IMPOSTAZIONI PRINCIPALI=; InpBEP_LiberaPosto=true; InpPremium=t?ue (illeggibile, true/false); InpPremiumLiv=0; InpAIPair=1; InpModalita=3; InpConfig=0; InpV11_ContrattoIndici=0.0; InpMagicNumber=0; InpStopMinATR=0.0;  ...PROP CHALLENGE=; InpLeva=0; InpPF_Capitale=(illeggibile); InpPF...` (il resto è troncato).
Quindi MERCATO NAS100 corrisponde a InpAIPair=1, LIVE ACCOUNT a InpModalita=3 e SET NAS PRIME 1 a InpConfig=0 (corrispondenza dedotta dall'ordine). Riga sopra: "NAS100_COMPLETE HYSTORY, M5: NAS100 Cash 30334.42 30337.92 30323.83 30329.31" (lettura approssimativa).

## 2. Impostazioni del tester
Fonte: scheda Settings in p_00002 (3 s, sotto la sovraimpressione) e p_00003 (6 s, nitida).
- Expert: `Advisors\ICT RAPTOR AI PRIME - AUTOTRADER FOREX CLUB - 000000.ex5`
- Symbol: NAS100_COMPLETE HYSTORY; timeframe M5
- Date: Custom period, 2018.01.01 - 2026.08.30
- Forward: No (1970.01.01)
- Delays: Zero latency, ideal execution
- Modelling: 1 minute OHLC; "profit in pips for faster calculations" deselezionato
- Deposit: 1000 USD; leverage 1:500
- Optimization: Disabled; "visual mode with the display of charts, indicators and trades" deselezionato
- Tempo di test: 00:01:17 / 00:01:19 (p_00030)
- Navigator: "ICT RAPTOR AI CORE -", "ICT RAPTOR AI PLUS" (parzialmente coperto); schede grafico: 4 x "NAS100_COMPLETE HYSTORY,M5".

## 3. Report (scheda Backtest)
Fonte: p_00030 (87 s) = p_00033 (96 s); ritagli ingranditi verificati.

| Statistica | Valore |
|---|---|
| History Quality | 98% |
| Bars | 568065 |
| Ticks | 11347606 |
| Symbols | 1 |
| Initial Deposit | 1 000.00 |
| Total Net Profit | 1 081 854.28 |
| Gross Profit | 1 670 085.97 |
| Gross Loss | -588 231.69 |
| Balance Drawdown Absolute | 155.72 |
| Balance Drawdown Maximal | 36 857.05 (6.48%) |
| Balance Drawdown Relative | 17.55% (179.77) |
| Equity Drawdown Absolute | 157.59 |
| Equity Drawdown Maximal | 52 872.20 (5.31%) |
| Equity Drawdown Relative | 18.42% (190.17) |
| Profit Factor | 2.84 |
| Recovery Factor | 20.46 |
| AHPR | 1.0040 (0.40%) |
| GHPR | 1.0039 (0.39%) |
| Expected Payoff | 605.74 |
| Sharpe Ratio | 6.31 |
| LR Correlation | 0.85 |
| LR Standard Error | 145 102.08 |
| Margin Level | 6880.48% |
| Z-Score | -9.15 (99.74%) |
| OnTester result | 2.83916354455504 |
| Total Trades | 1786 |
| Total Deals | 2409 |
| Short Trades (won %) | 612 (91.01%) |
| Long Trades (won %) | 1174 (83.05%) |
| Profit Trades (% of total) | 1532 (85.78%) |
| Loss Trades (% of total) | 254 (14.22%) |
| Largest profit trade | 23 806.42 |
| Largest loss trade | -29 051.00 |
| Average profit trade | 1 090.13 |
| Average loss trade | -2 315.87 |
| Maximum consecutive wins ($) | 61 (254 091.59) |
| Maximum consecutive losses ($) | 7 (-59.46) |
| Maximal consecutive profit (count) | 254 091.59 (61) |
| Maximal consecutive loss (count) | -29 973.20 (3) |
| Average consecutive wins | 9 |
| Average consecutive losses | 1 |
| Correlation (Profits,MFE) | 0.72 |
| Correlation (Profits,MAE) | 0.15 |
| Correlation (MFE,MAE) | -0.4783 |
| Minimal position holding time | 0:03:40 |
| Maximal position holding time | 573:25:40 |
| Average position holding time | 31:05:53 |

(Holding time da p_00032, 93 s.) Saldo finale calcolato: 1 082 854.28 (non mostrato). 2409 deal per 1786 trade, circa 1,35 deal per trade (compatibile con chiusure parziali; deduzione).

### Grafici
- **Curva balance/equity** (scheda Graph, test in corso; valori indicativi letti dalle etichette dell'asse Y):
  - p_00004/p_00006 (9-15 s): grafico vuoto, 2018.01.01.
  - p_00007 (18 s): 2018.01.01-2018.05.23. Balance da 1000 a circa 1032, poi drawdown fino a circa **917** a metà maggio 2018.
  - p_00008 (21 s): fino a circa 2018.08. Minimo circa 855-864 (luglio-agosto 2018).
  - p_00009 (24 s): fino a 2018.11.27. Nuovo minimo circa **845** a fine novembre 2018, poi risalita a circa 1003-1013 a fine 2018.
  - p_00010 (27 s): fino al 2019.01.30, circa 1069.
  - p_00011 (30 s): fino al 2019.08.02, picco circa 1269, chiusura circa 1180.
  - p_00013 (36 s): fino al 2020.04.07, circa 1400-1426.
  - p_00016 (45 s): fino al 2021.05.14, circa 5400-5600.
  - p_00019 (54 s): fino al 2022.07.04, circa 23 000.
  - p_00022 (63 s): fino al 2023.06.28, circa 78 000.
  - p_00025 (72 s): fino al 2024.10.24, circa 230 000.
  - p_00027 (78 s): fino al 2025.07.28, circa 496 000.
  - p_00028 (81 s): fino al 2026.02.27, circa 918 000.
  - p_00029 (84 s, finale): asse X 2018.02.12 → 2026.04.29 (ultima etichetta). Y: 1174364, 1115823, 1057282, 998741, 940201, 881660, 823119, 764578, 706037, 647496, 588955, 530415, 471874, 413333, 354792, 296251, 237710, 179169, 120628, 62088, 3547, -5499? (illeggibile). Fine circa 1.11M, piatta nell'ultimo tratto.
  - In sintesi: circa un anno (2018) in perdita e laterale sotto i 1000, poi crescita composta. Ritracciamenti visibili circa a fine 2023, nel 2024-25 (zona 300-350k) e nel 2025 (circa 530k).
  - Deposit Load: scala 1.0% all'inizio e 10.0% nel grafico finale.
- **Entries by hours (Asia,Europe,USA)** (p_00030): scala 0-130. Barre arancioni (Asia) alle ore 1-7, verdi (Europa) alle 8-14, rosse (USA) alle 15-23. Picco alle **13** (circa 125), poi 14 (circa 105), 7 (circa 62), 15 (circa 55), 12 (circa 50), 1 e 8 (circa 37), 9 (circa 28), 6 (circa 25), 2 (circa 18); le altre ore sono basse; 0, 17 e 22 sono zero. I valori sono stime visive.
- **Profits and losses by hours**: scala fino a 373000. Profitto massimo alle 14 (circa 373k), poi 13 (circa 320k), 15 (circa 230k), 12 (circa 180k); perdite più alte alle 14 (circa 190k) e alle 15 (circa 100k).
- **Entries by weekdays**: scala 0-140. Lun circa 135, Ven circa 133, Mar circa 120, Gio circa 120, Mer circa 118; Sab e Dom zero.
- **Profits and losses by weekdays**: scala fino a 396000. Lunedì il più alto (circa 396k); Mar, Mer, Gio e Ven tra circa 300 e 320k; perdite massime martedì (circa 160k).
- **Entries by months**: scala 0-70. Mag circa 66, Ott circa 65, Mar circa 62, Giu circa 55, Feb circa 53, Apr circa 52, Gen circa 49, Set circa 47, Nov circa 46, Lug circa 45, Ago circa 44; minimo Dic circa 39.
- **Profits and losses by months**: scala fino a 256000. Picco a Maggio (circa 256k, perdite circa 140k), poi Feb (circa 235k), Mar (circa 180k), Ott (circa 165k).
- Scatter Profit/MFE: asse MFE 0-30000; scatter Profit/MAE da -55000 a 0; scatter durata con asse "Time (days)" 0-24 giorni (p_00032).

## 4. Operazioni
Nessuna operazione singola leggibile: il visual mode è disattivato e le schede deals/orders non vengono mai aperte. `trades.csv` contiene solo l'intestazione.

## 5. Comportamento sul grafico
Il grafico NAS100 in alto (p_00001-p_00004) mostra solo candele M5 del 10 Dec 2024 e la riga di commento con gli input (vedi sezione 1). Non ci sono oggetti, pannelli o livelli dell'EA visibili. Indizi indiretti: "BE + PARZIALE LIBERA IL POSTO" = true; holding time massimo di 573 ore (circa 24 giorni), quindi alcune posizioni restano aperte a lungo.

## 6. Altro testo
- p_00001 (0 s): "ICT RAPTOR AI PRIME" ("PRIME" in magenta).
- p_00002 (3 s): "NASDAQ / NAS LIVE STEROID PRIME / LIVE ACCOUNT 1K BALANCE".
- s_00001..s_00004: transizione (schermata inclinata).
- s_00006 (14,1 s): transizione tra due grafici vuoti.
- s_00007 (99,3 s): nero.
- Versione EA: il file è "...AUTOTRADER FOREX CLUB - 000000.ex5"; nessun numero di versione visibile. L'unica data è l'orologio di sistema 31/08/2026 (fine periodo di test 2026.08.30).
