# nas_macro: note del video (set "PRIME MACRO NAS")

Video muto di circa 57 s, 1280x720. Fotogrammi in `all/`: p_00001 = 0 s, poi uno ogni 3 s (p_N = (N-1)*3 s). I fotogrammi s_* sono cambi di scena: s_00002..s_00008 sono la transizione iniziale (0,2-0,8 s), s_00009 = 11,1 s e s_00001/s_00010 = 53,7 s.
Ho controllato tutti i 30 PNG. p_00011..p_00014 (30-39 s) sono identici a p_00010 (stesso report).
Orologio di Windows nel video: 20/08/2026, 23:39-23:40. Conto: "25787667 - VantageMarkets-Demo: Demo Account - Hedge - Vantage Markets (Pty) Ltd".

## 1. Menu input
Il menu compare nella scheda Inputs dello Strategy Tester in p_00001 (0 s, sotto il titolo), p_00002 (3 s, con la tendina MODALITA OPERATIVA aperta), p_00003-p_00005 (6-12 s), s_00009 (11,1 s) e p_00018 (51 s, la vista più nitida). Il contenuto è sempre lo stesso; la riga selezionata (evidenziata) è LIMITE GIORNALIERO PROP. Si vede solo fino al gruppo FLIP: l'intestazione del gruppo successivo è tagliata in fondo ("SUPERVISORE LIQBIAS", lettura parziale da p_00018, vedi il ritaglio della riga a y≈585). Il menu non viene mai scorso, quindi i gruppi FILTRO NOTIZIE, MESSAGGI GRAFICA, PREMIUM ecc. **non sono visibili**.

Colonne: Variable | Value | Start | Step | Stop (ottimizzazione: tutte le caselle sono deselezionate).

| # | Gruppo | Etichetta (verbatim) | Value | Start | Step | Stop | Frame |
|---|---|---|---|---|---|---|---|
| 0 | (intestazione) | AUTOTRADER FOREX CLUB | atfc@gmail.com | | | | p_00018 (51 s) |
| 1 | IMPOSTAZIONI PRINCIPALI | BE + PARZIALE LIBERA IL POSTO (false = conteggio normale) | true | false | | true | p_00018 |
| 2 | IMPOSTAZIONI PRINCIPALI | PREMIUM (false = celle originali, come ora) | false | false | | true | p_00018 |
| 3 | IMPOSTAZIONI PRINCIPALI | PREMIUM: quale livello | PREMIUM A    (solo ENTER) | PREMIUM A    (solo ENTER) | | PREMIUM A++    (ENTER + MAIN + SEC... (troncato) | p_00018 |
| 4 | IMPOSTAZIONI PRINCIPALI | MERCATO | NAS100 | XAUUSD | | EURUSD | p_00018 |
| 5 | IMPOSTAZIONI PRINCIPALI | MODALITA OPERATIVA | LIVE ACCOUNT | PROP CHALLENGE | | FLIP | p_00018; tendina aperta in p_00002 (3 s) con le opzioni: PROP CHALLENGE, PROP FUNDED, LIVE ACCOUNT (selezionata), FLIP |
| 6 | IMPOSTAZIONI PRINCIPALI | SET | PRIME MACRO NAS | (interno) | | PRIME MACRO EUR | p_00018 |
| 7 | IMPOSTAZIONI PRINCIPALI | LEVA DEL CONTO | 1:100 | 1:100 | | 1:30 | p_00018 |
| 8 | IMPOSTAZIONI PRINCIPALI | VALORE CONTRATTO INDICI | 0.0 | 0.0 | 0.0 | 0.0 | p_00018 |
| 9 | IMPOSTAZIONI PRINCIPALI | MAGIC NUMBER | 999000 | 999000 | 1 | 9990000 | p_00018 |
| 10 | PROP CHALLENGE | CAPITALE DELLA CHALLENGE | 0.0 | 0.0 | 0.0 | 0.0 | p_00018 |
| 11 | PROP CHALLENGE | QUANTO SPINGERE | EQUILIBRATO | AGGRESSIVO | | PRUDENTE | p_00018 |
| 12 | PROP CHALLENGE | FASE | FASE 1 | FASE 1 | | FASE 2 | p_00018 |
| 13 | PROP CHALLENGE | TRAGUARDO FASE 1 | 10.0 | 10.0 | 1.0 | 100.0 | p_00018 |
| 14 | PROP CHALLENGE | TRAGUARDO FASE 2 | 5.0 | 5.0 | 0.5 | 50.0 | p_00018 |
| 15 | PROP CHALLENGE | LIMITE GIORNALIERO PROP | 4.0 | 4.0 | 0.4 | 40.0 | p_00018 (riga evidenziata) |
| 16 | PROP CHALLENGE | LIMITE TOTALE PROP | 10.0 | 10.0 | 1.0 | 100.0 | p_00018 |
| 17 | PROP CHALLENGE | MISURA DEL TRAGUARDO | EQUITY | EQUITY | | SALDO | p_00018 |
| 18 | PROP CHALLENGE | AL TRAGUARDO | CHIUDI E FERMATI | CHIUDI E FERMATI | | CHIUDI E CONTINUA | p_00018 |
| 19 | PROP CHALLENGE | MARGINE DI SICUREZZA | 0.2 | 0.2 | 0.02 | 2.0 | p_00018 |
| 20 | PROP FUNDED | CAPITALE FINANZIATO | 0.0 | 0.0 | 0.0 | 0.0 | p_00018 |
| 21 | PROP FUNDED | QUANTO SPINGERE | EQUILIBRATO | AGGRESSIVO | | PRUDENTE | p_00018 |
| 22 | PROP FUNDED | AVVISA AL GUADAGNO DI | 0.0 | 0.0 | 0.0 | 0.0 | p_00018 |
| 23 | LIVE ACCOUNT | CAPITALE DEL CONTO | 0.0 | 0.0 | 0.0 | 0.0 | p_00018 |
| 24 | LIVE ACCOUNT | QUANTO SPINGERE | AGGRESSIVO | AGGRESSIVO | | PRUDENTE | p_00018 |
| 25 | LIVE ACCOUNT | CRESCITA DEL LOTTO | COMPOSTO — i lotti crescono col conto | COMPOSTO — i lotti crescono col conto | | BASE FISSA — i lotti restano quelli di par... (troncato) | p_00018 |
| 26 | FLIP | CAPITALE DA FLIPPARE | 0.0 | 0.0 | 0.0 | 0.0 | p_00018 |
| 27 | FLIP | QUANTO SPINGERE | EQUILIBRATO | AGGRESSIVO | | PRUDENTE | p_00018 |
| 28 | FLIP | OBIETTIVO | 2X — RADDOPPIO | 2X — RADDOPPIO | | 5X | p_00018 |
| 29 | FLIP | STOP-PIANO | 30.0 | 30.0 | 3.0 | 300.0 | p_00018 |
| 30 | SUPERVISORE LIQBIAS (intestazione tagliata) | righe non visibili | | | | | p_00018 |

Note:
- In questa versione del menu **non compare** la riga "STOP MINIMO IN ATR", e "LEVA DEL CONTO" si trova in IMPOSTAZIONI PRINCIPALI (nel video nas_steroid, invece, ci sono "LEVA IMPOSTA DALLA PROP" e "LEVA DEL CONTO LIVE").
- Le icone accanto alle etichette (lucchetto, ingranaggio, fulmine, clessidra ecc.) sono emoji/simboli piccoli, non trascrivibili con certezza.

## 2. Impostazioni del tester
La scheda Settings **non viene mai mostrata** in questo video. Quello che si deduce da altri elementi:
- Grafico/simbolo: durante il test il tab attivo è "EURUSD COMPLETE HISTORY,M5" (p_00002-p_00008), con un'altra scheda "EURUSD COMPLETE HISTORY,M5". A fine test compare un nuovo tab "NAS100_COMPLETE HYSTORY,M5" (sic, p_00009 a 24 s e successivi) e la barra del titolo diventa "[NAS100_COMPLETE HYSTORY,M5]". Il simbolo testato è quindi NAS100_COMPLETE HYSTORY, timeframe M5.
- Periodo: il grafico parte da "2018.01.01" (p_00006, 15 s) e l'asse finale va da 2018.03.01 a 2026.02.27 (ultima etichetta, p_00009). La data finale esatta è illeggibile.
- Deposito iniziale: 1 000.00 (dal report). Valuta e leva del tester non sono visibili (input LEVA DEL CONTO = 1:100). Il titolo in sovraimpressione dice "START 1K".
- Modellazione e ritardi: non visibili. History Quality 98%, Bars 568065, Ticks 11347606 (gli stessi valori del video nas_steroid, che usa "1 minute OHLC").
- Tempo di test: "00:00:11 / 00:00:11" (p_00009-p_00018).

## 3. Report (scheda Backtest)
Fonte: p_00010 (27 s) = p_00011..p_00014 = p_00017 (48 s); ritagli ingranditi verificati.

| Statistica | Valore |
|---|---|
| History Quality | 98% |
| Bars | 568065 |
| Ticks | 11347606 |
| Symbols | 1 |
| Initial Deposit | 1 000.00 |
| Total Net Profit | 2 829 898.41 |
| Gross Profit | 4 196 042.90 |
| Gross Loss | -1 366 144.49 |
| Balance Drawdown Absolute | 23.42 |
| Balance Drawdown Maximal | 157 418.18 (7.03%) |
| Balance Drawdown Relative | 11.25% (541.18) |
| Equity Drawdown Absolute | 33.61 |
| Equity Drawdown Maximal | 187 425.85 (7.66%) |
| Equity Drawdown Relative | 13.51% (665.73) |
| Profit Factor | 3.07 |
| Recovery Factor | 15.10 |
| AHPR | 1.0081 (0.81%) |
| GHPR | 1.0079 (0.79%) |
| Expected Payoff | 2815.82 |
| Sharpe Ratio | 30.97 |
| LR Correlation | 0.84 |
| LR Standard Error | 457 816.53 |
| Margin Level | 1035.55% |
| Z-Score | -4.82 (99.74%) |
| OnTester result | 15.09876257730723 |
| Total Trades | 1005 |
| Total Deals | 1607 |
| Short Trades (won %) | 575 (78.96%) |
| Long Trades (won %) | 430 (83.49%) |
| Profit Trades (% of total) | 813 (80.90%) |
| Loss Trades (% of total) | 192 (19.10%) |
| Largest profit trade | 65 340.13 |
| Largest loss trade | -46 990.00 |
| Average profit trade | 5 161.18 |
| Average loss trade | -7 115.34 |
| Maximum consecutive wins ($) | 22 (293 756.62) |
| Maximum consecutive losses ($) | 7 (-140 593.93) |
| Maximal consecutive profit (count) | 293 756.62 (22) |
| Maximal consecutive loss (count) | -147 503.10 (6) |
| Average consecutive wins | 6 |
| Average consecutive losses | 1 |
| Correlation (Profits,MFE) | 0.77 |
| Correlation (Profits,MAE) | 0.29 |
| Correlation (MFE,MAE) | -0.2868 |
| Minimal position holding time | 0:00:19 |
| Maximal position holding time | 37:48:40 |
| Average position holding time | 1:58:16 |

(Gli ultimi tre valori vengono da p_00016, 45 s.) Saldo finale dedotto: 1 000 + 2 829 898.41 = 2 830 898.41 (calcolato, non mostrato).
Nota: 1607 deal per 1005 trade, cioè circa 1,6 deal per trade, compatibile con chiusure parziali (deduzione).

### Grafici
- **Curva balance/equity** (scheda Graph, frame mentre il test gira):
  - p_00006 (15 s): grafico vuoto che parte da 2018.01.01, asse a circa 958-1097.
  - p_00007 (18 s): asse X da 2018.02.15 a 2020.01.29, asse Y fino a 15058. Crescita regolare con un plateau/ritracciamento intorno a metà 2019 e un massimo vicino a 15 000 all'inizio del 2020.
  - p_00008 (21 s): asse X da 2018.03.01 a 2023.06.30, Y fino a 417803. Curva piatta fino al 2021 circa, poi esponenziale; ritracciamenti visibili intorno a 2022-2023.
  - p_00009 (24 s, finale): asse X da 2018.03.01 a 2026.02.27. Etichette Y: 3104390, 2923956, 2743521, 2563087, 2382652, 2202218, 2021784, 1841349, 1660915, 1480480, 1300046, 1119611, 939177, 758742, 578308, 397873, 217439, 37004, minimo -14?430 (parzialmente illeggibile). Curva piatta fino al 2021-22, poi crescita esponenziale; ritracciamenti visibili circa a 2.2M e a 2.4M (zona 2025); termina vicino a 2.8M con un piccolo calo finale.
  - Deposit Load: scala massima 25.0%, barre verdi fitte; il carico più alto sembra intorno al 2019-2020.
  - Etichette X complete in p_00009: 2018.03.01, 2018.07.06, 2018.09.25, 2018.11.28, 2019.02.01, 2019.04.05, 2019.07.01, 2019.09.06, 2019.11.26, 2020.01.15, 2020.12.22, 2021.03.30, 2021.07.16, 2021.12.02, 2022.03.1?, 2022.07.01, 2022.11.10, 2023.02.23, 2023.05.18, 2023.09.07, 2023.12.01, 2024.02.29, 2024.06.05, 2024.09.27, 2025.01.15, 2025.05.02, 2025.08.01, 2025.12.01, 2026.02.27.
- **Entries by hours (Asia,Europe,USA)** (p_00010): scala 0-300. Barre solo tra le 14 e le 23. Picco alle **15** (circa 290), poi 16 (circa 110), 17 (circa 75), 18 (circa 35), 19 (circa 40), 20 (circa 30), 21-23 piccole (meno di 10); 14 quasi zero. Le barre sono rosse (sessione USA). I valori sono stime visive.
- **Profits and losses by hours**: scala fino a 1026000 (la prima cifra è tagliata, si legge "026000"). Profitti (blu) massimi alle 15 e 16, poi 17, 18, 19; perdite (rosse) più alte alle 15-17. Piccole barre anche alle ore 1-8 (pochi trade).
- **Entries by weekdays**: scala 0-250. Gio è il picco (circa 245), poi Ven (circa 130), Mer (circa 110), Mar (circa 100), Lun (circa 20); Sab e Dom zero.
- **Profits and losses by weekdays**: scala fino a 1743000; picco di profitto il giovedì.
- **Entries by months**: scala 0-70. Dic è il picco (circa 67), poi Gen (circa 58) e Feb (circa 55); Set è il minimo (circa 39). Distribuzione abbastanza uniforme.
- **Profits and losses by months**: scala fino a 493000. Profitti alti da Feb a Mag; a Dic le perdite superano leggermente i profitti (barra rossa circa 200k contro blu circa 185k); ad Ago perdite quasi pari ai profitti.
- **Scatter Profit/MFE e Profit/MAE** (p_00015-p_00016): asse MFE 0-77000, asse MAE da -52000 a 0, asse profitto da -65600 a 82000.
- **Holding time scatter** (p_00016): la maggior parte dei punti è nelle prime ore.

## 4. Operazioni
Nessuna operazione singola leggibile: le schede History/Deals non vengono mai aperte e il visual mode non viene mostrato. `trades.csv` contiene solo l'intestazione.

## 5. Comportamento sul grafico
Il grafico dei prezzi con oggetti o pannelli dell'EA non viene mai mostrato. Indizi indiretti:
- L'input "BE + PARZIALE LIBERA IL POSTO (false = conteggio normale)" = true indica break-even e chiusura parziale.
- Il rapporto deal/trade (1607/1005) è coerente con chiusure parziali (deduzione).
Nessun testo sul grafico da trascrivere.

## 6. Altro testo
- p_00001 (0 s): titolo in sovraimpressione "ICT RAPTOR AI PRIME" ("PRIME" in magenta).
- p_00003 (6 s): "NASDAQ / SET: PRIME MACRO NAS / START 1K / LIVE ACCOUNT".
- p_00004 (9 s): "TIENITI FORTE / BUONA VISIONE / TRADER!".
- s_00002..s_00008 (0,2-0,8 s): transizione con frammenti di schermata che volano (vi si intravedono le righe del menu input).
- p_00019 (54 s): pulsante "Subscribe" (YouTube); p_00020 (57 s): nero.
- Market Watch 00:39:46-00:40:56, barra di stato "117.76 ms"; status bar "For Help, press F1"; "Default".
- La versione o la data dell'EA non sono visibili (Settings non mostrata). Data di sistema 20/08/2026.
