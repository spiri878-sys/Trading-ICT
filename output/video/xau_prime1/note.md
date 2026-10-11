# ICT RAPTOR AI PRIME - XAUUSD, set "XAUUSD PRIME 1" (live account) - note dal video

Fonte: registrazione muta del Strategy Tester MT5, fotogrammi in `all/` (`p_NNNNN.png` = t (N-1)x3 s; `s_*.png` = cambi scena). Durata video circa 327 s.
Risoluzione dei fotogrammi 1280x720: il testo piccolo è stato letto ritagliando e ingrandendo le zone (2x-4x).

Mappa dei fotogrammi di cambio scena (verificata per confronto pixel con `frames/`):
s_00001 = 0,5 s; s_00002 = 0,6 s; s_00003 = 0,7 s; s_00004 = 1,3 s; s_00005 = 1,4 s; s_00006 = 1,5 s; s_00007 = 1,6 s; **s_00008 = 1,7 s (menu Inputs)**; s_00009 = 1,9 s; s_00010 = circa 324 s.

Struttura del video:
- 0-1,9 s (p_00001, s_00001…s_00009): transizione animata (flip/zoom). Al centro c'è un solo fotogramma quasi nitido del tab **Inputs** (s_00008, t 1,7 s). I fotogrammi p_00001, s_00004, s_00006 (capovolto verticalmente) e s_00007 mostrano la stessa tabella sfocata.
- 3 s (p_00002): tab Graph vuoto con il titolo "ICT RAPTOR AI PRIME".
- 6-318 s (p_00003…p_00107): tab **Graph** che si costruisce durante il test (Balance/Equity e Deposit Load). Non si vede nessun altro tab.
- 321 s (p_00108): tab **Backtest**, cioè il report finale. È l'unico fotogramma con il report e non viene scorso.
- 324-327 s (p_00109, p_00110, s_00010): "SUBSCRIBE" e poi schermo nero.

Non compaiono mai il tab Settings, la lista History/Deals/Orders, il Journal o un grafico di prezzo con oggetti dell'EA.

---

## 1. Menu input

Fotogramma: **all/s_00008.png (t 1,7 s)**. Il frame è leggermente mosso perché in transizione. Le righe fino a "LIVE ACCOUNT > CAPITALE DEL CONTO" sono ben leggibili. Le righe successive hanno etichette sfocate ma valori leggibili. Le ultime righe sono molto sfocate.
Colonne: Variable | Value | Start | Step | Stop. La colonna "Steps" è vuota. In alto: "Select expert..." e "View previous single test results".
L'ordine è quello sullo schermo. I simboli/icone prima delle etichette sono emoji dell'EA e qui sono omessi.

| # | Gruppo | Etichetta (verbatim) | Value | Start | Step | Stop |
|---|---|---|---|---|---|---|
| 1 | (intestazione, senza gruppo) | AUTOTRADER FOREX CLUB | atfc@gmail.com | | | |
| - | **IMPOSTAZIONI PRINCIPALI** | | | | | |
| 2 | IMPOSTAZIONI PRINCIPALI | BE + PARZIALE LIBERA IL POSTO (false = conteggio normale) | true | false | | true |
| 3 | IMPOSTAZIONI PRINCIPALI | PREMIUM (false = celle originali, come ora) | false | false | | true |
| 4 | IMPOSTAZIONI PRINCIPALI | PREMIUM: quale livello | PREMIUM A (solo ENTER) | PREMIUM A (solo ENTER) | | PREMIUM A++ (ENTER + MAIN + SEC... (troncato) |
| 5 | IMPOSTAZIONI PRINCIPALI | MERCATO | XAUUSD | XAUUSD | | EURUSD |
| 6 | IMPOSTAZIONI PRINCIPALI | MODALITA OPERATIVA | LIVE ACCOUNT | PROP CHALLENGE | | FLIP |
| 7 | IMPOSTAZIONI PRINCIPALI | SET | XAUUSD PRIME 1 | (interno) | | PRIME MACRO EUR |
| 8 | IMPOSTAZIONI PRINCIPALI | LEVA DEL CONTO | 1:100 | 1:100 | | 1:30 |
| 9 | IMPOSTAZIONI PRINCIPALI | VALORE CONTRATTO INDICI | 0.0 | 0.0 | 0.0 | 0.0 |
| 10 | IMPOSTAZIONI PRINCIPALI | MAGIC NUMBER | 999000 | 999000 | 1 | 9990000 |
| - | **PROP CHALLENGE** | | | | | |
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
| - | **PROP FUNDED** | | | | | |
| 21 | PROP FUNDED | CAPITALE FINANZIATO | 0.0 | 0.0 | 0.0 | 0.0 |
| 22 | PROP FUNDED | QUANTO SPINGERE | EQUILIBRATO | AGGRESSIVO | | PRUDENTE |
| 23 | PROP FUNDED | AVVISA AL GUADAGNO DI | 0.0 | 0.0 | 0.0 | 0.0 |
| - | **LIVE ACCOUNT** | | | | | |
| 24 | LIVE ACCOUNT | CAPITALE DEL CONTO | 0.0 | 0.0 | 0.0 | 0.0 |
| 25 | LIVE ACCOUNT | QUANTO SPINGERE | **AGGRESSIVO** | AGGRESSIVO | | PRUDENTE |
| 26 | LIVE ACCOUNT | CRESCITA DEL LOTTO | **COMPOSTO — i lotti crescono col conto** | COMPOSTO — i lotti crescono col conto | | BASE FISSA — i lotti restano quelli di par... (troncato) |
| - | **FLIP** (etichetta sfocata, leggo "FLIP") | | | | | |
| 27 | FLIP | CAPITALE DA FLIPPARE (sfocata) | 0.0 | 0.0 | 0.0 | 0.0 |
| 28 | FLIP | QUANTO SPINGERE (sfocata) | EQUILIBRATO | AGGRESSIVO | | PRUDENTE |
| 29 | FLIP | OBIETTIVO (sfocata) | 2X — RADDOPPIO | 2X — RADDOPPIO | | 5X |
| 30 | FLIP | etichetta parzialmente illeggibile, "STOP-…" (forse "STOP-RIANNO"/"STOP-PIANO", non certo) | 30.0 | 30.0 | 3.0 | 300.0 |
| - | **SUPERVISORE …** (gruppo; seconda parola illeggibile, sembra "UCB/AS" o simile) | | | | | |
| 31 | SUPERVISORE | "SUPERVISORE …(false = come certificato)" (parola centrale illeggibile) | false | false | | true |
| 32 | SUPERVISORE | "SUPERVISORE: soglia 1.86 (-1 = quella della cella)" (lettura incerta; "1.86" non sicuro) | 50 | 50 | 5 | 100 |
| - | **FILTRO NOTIZIE** (lettura incerta, molto sfocata) | | | | | |
| 33 | FILTRO NOTIZIE | "NON OPERARE SULLE NOTIZIE" (incerta) | false | false | | true |
| 34 | FILTRO NOTIZIE | "minuti PRIMA della notizia" (incerta) | 30 (incerto) | 30 (incerto) | 1 | 300 (incerto) |
| 35 | FILTRO NOTIZIE | "minuti DOPO la notizia" (incerta) | 30 (incerto) | 30 (incerto) | 1 | 300 (incerto) |
| 36 | (riga successiva, tagliata dal bordo) | illeggibile | illeggibile | | | |

Note sul menu:
- In questo frame **nessuna riga ha la casella di ottimizzazione spuntata**. Le colonne Start/Step/Stop sono quelle predefinite dell'enum o del range.
- Le colonne Start e Stop mostrano alcuni valori alternativi degli enum: PREMIUM A++ "(ENTER + MAIN + SEC…", MERCATO EURUSD, MODALITA PROP CHALLENGE / FLIP, SET "PRIME MACRO EUR", leva 1:30, MISURA DEL TRAGUARDO "SALDO", AL TRAGUARDO "CHIUDI E CONTINUA", CRESCITA DEL LOTTO "BASE FISSA — i lotti restano quelli di par…", OBIETTIVO "5X".
- Nella versione capovolta e sfocata s_00006 (t 1,5 s), la colonna Start della riga VALORE CONTRATTO INDICI sembra "5.0" e non "0.0". La lettura è incerta e prevale s_00008.
- Nella tabella **non compaiono** parametri di rischio in %, lotti, SL/TP, orari o celle (PPK, OTEOF, ecc.): il menu è di alto livello e il resto è "interno" al SET.

## 2. Impostazioni del tester

Il tab Settings **non è mai mostrato**. Si ricava solo quanto segue:

| Campo | Valore | Fonte |
|---|---|---|
| Simbolo | Custom symbol **XAUUSD_2005_TO_MAY 2025** (dal titolo della finestra "[XAUUSD_2005_TO_MAY 2025,M5]"). Report: "Symbols 1" | p_00002…p_00108 (titolo); p_00108 |
| Timeframe | **M5** (nel titolo della finestra e pulsante M5 attivo nella toolbar) | p_00002 |
| Periodo | Il grafico parte da **2007.01.01** (prima etichetta in p_00003/p_00004, t 6-9 s) e l'ultima etichetta visibile è **2026.03.30** (p_00107, t 318 s). Data di fine esatta illeggibile/non mostrata. Nota: il nome del simbolo dice "to MAY 2025", ma le date arrivano al 2026 | p_00003, p_00107 |
| Modellazione | Non mostrata. Report: Ticks 27422139, Bars 1391363, History Quality 98% | p_00108 |
| Ritardi | non mostrato (illeggibile) | - |
| Deposito iniziale | **1 000.00** (report "Initial Deposit"; overlay "1K START BALANCE") | p_00108, p_00003 |
| Leva | Il tab Settings non è visibile. Input "LEVA DEL CONTO" = 1:100 | s_00008 |
| Ottimizzazione | No, è un test singolo (tab Backtest/Graph, nessuna casella di ottimizzazione spuntata) | s_00008, p_00108 |
| Conto/terminale | "25787667 - VantageMarkets-Demo: Demo Account - Hedge - Vantage Markets (Pty) Ltd" | barra del titolo, p_00002 |
| Durata test | Timer "00:07:55 / 00:07:55" a fine test (pulsante "Start" verde) | p_00107, p_00108 |
| Ping / memoria | "123.20 ms"; "12 / 473 Mb" … "27 / 473 Mb" | barra di stato |
| Data registrazione | 25/08/2026, orologio 09:54 → 10:02 | barra di Windows |
| Altre schede grafico aperte | "EURUSD_COMPLETE HISTORY,M5" (più volte), "NAS100_COMPLETE HISTORY,M5", "XAUUSD_2005_TO_MAY 2025,M5" (testo parzialmente tagliato) | p_00107 |

## 3. Report

Fotogramma: **all/p_00108.png (t 321 s)**, tab Backtest. Valori trascritti esattamente:

| Statistica | Valore |
|---|---|
| History Quality | 98% |
| Bars | 1391363 |
| Ticks | 27422139 |
| Symbols | 1 |
| Initial Deposit | 1 000.00 |
| Total Net Profit | 181 133.61 |
| Gross Profit | 573 095.47 |
| Gross Loss | -391 961.86 |
| Profit Factor | 1.46 |
| Expected Payoff | 38.99 |
| Recovery Factor | 4.90 |
| Sharpe Ratio | 2.40 |
| AHPR | 1.0012 (0.12%) |
| GHPR | 1.0011 (0.11%) |
| LR Correlation | 0.93 |
| LR Standard Error | 17 180.95 |
| Margin Level | 973.24% |
| Z-Score | -16.50 (99.74%) |
| OnTester result | 1.46212049815255 |
| Balance Drawdown Absolute | 70.91 |
| Balance Drawdown Maximal | 32 954.75 (18.69%) |
| Balance Drawdown Relative | 18.69% (32 954.75) |
| Equity Drawdown Absolute | 73.19 |
| Equity Drawdown Maximal | 36 949.64 (20.59%) |
| Equity Drawdown Relative | 20.59% (36 949.64) |
| Total Trades | 4646 |
| Total Deals | 6152 |
| Short Trades (won %) | 2133 (88.33%) |
| Long Trades (won %) | 2513 (82.57%) |
| Profit Trades (% of total) | 3959 (85.21%) |
| Loss Trades (% of total) | 687 (14.79%) |
| Largest profit trade | 10 625.63 |
| Largest loss trade | -3 681.88 |
| Average profit trade | 144.76 |
| Average loss trade | -570.54 |
| Maximum consecutive wins ($) | 60 (7 954.83) |
| Maximum consecutive losses ($) | 8 (-15 898.95) |
| Maximal consecutive profit (count) | 21 967.47 (42) |
| Maximal consecutive loss (count) | -15 898.95 (8) |
| Average consecutive wins | 9 |
| Average consecutive losses | 2 |
| Correlation (Profits,MFE) | 0.57 |
| Correlation (Profits,MAE) | 0.31 |
| Correlation (MFE,MAE) | -0.3850 |

Saldo finale implicito: 1 000 + 181 133.61 = 182 133.61.

**Osservazione (deduzione, non testo del video):** Total Deals 6152 - Total Trades 4646 = 1506. In MT5 i "trades" contano le uscite e i "deals" contano ingressi + uscite, quindi ci sono circa **1506 posizioni aperte**, ciascuna chiusa in media in circa 3,1 uscite parziali. Questo è coerente con i 1500-1600 ingressi degli istogrammi sotto e con l'input "BE + PARZIALE LIBERA IL POSTO = true". Il rapporto tra average loss (-570.54) e average win (144.76) è circa 3,9:1, con un win rate dell'85% contato sulle uscite.

### Istogrammi (p_00108; valori stimati dalle barre, scala letta sugli assi)

**Entries by hours (Asia.Europe.USA)**, asse 0-165-330:
ora 0 = 0; **1 ≈ 320 (picco, molto staccato)**; 2 ≈ 50; 3 ≈ 45; 4 ≈ 45; 5 ≈ 42; 6 ≈ 80; 7 ≈ 90; 8 ≈ 72; 9 ≈ 48; 10 ≈ 50; 11 ≈ 68; 12 ≈ 100; 13 ≈ 100; 14 ≈ 35; 15 ≈ 33; 16 ≈ 40; 17 ≈ 52; 18 ≈ 72; 19 ≈ 55; 20 ≈ 37; 21 ≈ 10; 22 ≈ 18; 23 ≈ 40. Colori: ore 1-7 arancio (Asia), 8-14 verde (Europa), 15-23 rosso (USA).

**Profits and losses by hours** (blu = profitti, rosso = perdite; asse 0-80000):
1: ≈80000 / ≈35000; 2: 17k/14k; 3: 10k/15k; 4: 4k/7k; 5: 28k/10k; 6: 23k/21k; 7: 30k/15k; 8: 32k/20k; 9: 31k/21k; 10: 15k/5k; 11: 20k/29k; 12: 44k/30k; 13: 54k/55k; 14: 60k/34k; 15: 29k/23k; 16: 10k/10k; 17: 10k/6k; 18: 16k/5k; 19: 14k/14k; 20: 10k/9k; 21: 3k/3k; 22: 16k/1k; 23: 16k/6k.

**Entries by weekdays** (asse 0-85-170-255-340): Sun 0; Mon ≈ 290; Tue ≈ 280; **Wed ≈ 335 (picco)**; Thu ≈ 283; Fri ≈ 325; Sat 0.
**Profits and losses by weekdays** (asse 0-33750-67500-101250-135000): Mon ≈118k/≈58k; Tue ≈108k/≈73k; Wed ≈110k/≈97k; **Thu ≈135k (picco)/≈77k**; Fri ≈101k/≈86k. La somma è circa 572k / 391k, coerente con Gross Profit e Gross Loss.

**Entries by months** (asse 0-85-170): Jan ≈125; Feb ≈115; **Mar ≈160 (picco)**; Apr ≈142; May ≈125; Jun ≈112; Jul ≈124; Aug ≈111; Sep ≈123; Oct ≈119; Nov ≈136; Dec ≈112.
**Profits and losses by months** (asse 0-11500-…-92000): Jan ≈63k/21k; Feb ≈51k/32k; Mar ≈55k/**69k** (unico mese con perdite > profitti); **Apr ≈92k (picco)**/58k; May ≈47k/35k; Jun ≈34k/22k; Jul ≈29k/21k; Aug ≈27k/22k; Sep ≈31k/27k; Oct ≈37k/24k; Nov ≈56k/26k; Dec ≈52k/36k.

**Scatter Profit vs MFE** (in basso, parzialmente visibile): la maggior parte dei punti sta tra -2200 e +4400. Ci sono punti isolati a circa 8000, 9000 e uno a circa 10600 sull'estrema destra.

### Curva Balance/Equity (tab Graph, p_00003…p_00107)

Forma: crescita **esponenziale e regolare** (lotti composti). Piatta e oscillante nel 2007 (sotto i 1000: minimo circa 927-930 a inizio 2007/2008). Poi c'è una salita costante con correzioni brevi. Si accelera molto dal 2020 e soprattutto dal 2025 in poi. Alla fine c'è un forte drawdown con un picco di equity isolato verso i 190k. La linea di equity (verde) segue quasi sempre la balance (blu scuro). Il pannello Deposit Load mostra barre basse e regolari: scala 0-10% fino a p_00105, poi 0-25% in p_00106/p_00107 (barre più alte a fine 2025-2026).

Prime operazioni (p_00003, t 6 s, intervallo 2007.01.01-2007.05.04): il saldo scende a circa 964-966 dopo 3-4 trade. L'equity tocca circa 1013 per un attimo (asse 964.6-1016.2).

Tappe (ultima data visibile sull'asse X, timer del test, asse Y massimo):

| Frame (t) | Ultima etichetta data | Timer | Asse Y max (≈ picco + margine) |
|---|---|---|---|
| p_00004 (9 s) | 2008.02.06 | 00:00:13 | 1018.3; ultimo saldo visibile ≈ 959 |
| p_00005 (12 s) | 2008.09.15 | 00:00:17 | 1288; ultimo saldo ≈ 1200 |
| p_00006 (15 s) | 2009.03.26 | 00:00:22 | 1514; ultimo ≈ 1420 |
| p_00011 (30 s) | 2010.11.23 | 00:00:44 | 1693 |
| p_00015 (42 s) | 2012.01.04 | 00:01:02 | 2140 |
| p_00021 (60 s) | 2013.04.18 | 00:01:29 | 2975 |
| p_00027 (78 s) | 2014.05.07 | 00:01:56 | 4185 |
| p_00033 (96 s) | 2014.12.22 (poi coperta dalla notifica) | illeggibile (coperto) | 5255 (curva ≈ 4800) |
| p_00038 (111 s) | 2016.10.25 | 00:02:46 | 6546 |
| p_00047 (138 s) | 2018.03.01 | 00:03:26 | 8587 |
| p_00053 (156 s) | 2019.01.08 | 00:03:53 | 9642 |
| p_00061 (180 s) | 2020.03.23 | 00:04:29 | 11868 |
| p_00065 (192 s) | 2020.10.20 | 00:04:47 | 15531 |
| p_00069 (204 s) | 2021.04.06 | 00:05:05 | 24030 |
| p_00074 (219 s) | 2021.10.22 | 00:05:27 | 31675 (in p_00073 l'asse arriva a 28841, curva ≈ 27-28k) |
| p_00078 (231 s) | 2022.08.05 | 00:05:46 | 41801 |
| p_00081 (240 s) | 2023.01.25 | 00:05:59 | 50425 |
| p_00086 (255 s) | 2023.09.21 | 00:06:22 | 65180 |
| p_00090 (267 s) | 2024.04.30 | 00:06:40 | 77620 |
| p_00096 (285 s) | 2024.12.20 | 00:07:06 | 98927 |
| p_00101 (300 s) | 2025.08.28 | 00:07:29 | 126493 |
| p_00104 (309 s) | 2026.01.21 | 00:07:43 | 179644 |
| p_00105 (312 s) | 2026.01.21 (ultima etichetta) | 00:07:47 | 179644; picco curva ≈ 177k, poi calo |
| p_00107 (318 s) | 2026.03.30 | 00:07:55 / 00:07:55 | 200864 (asse da 1428 a 200864) |

Saldo stimato **dai pixel** della curva finale (p_00107, scala 1428-200864, passo 9972 ogni 21,3 px), per ogni etichetta di data. È una stima approssimativa (±1-2k a fine curva). La calibrazione è verificata perché l'ultimo punto (≈ 181-182k) corrisponde al saldo finale 182 133.61.
2007.11.01 ≈ 1.0k | 2010.04.28 ≈ 1.7k | 2011.10.04 ≈ 1.7k | 2012.09.26 ≈ 2.4k | 2013.09.18 ≈ 2.8k | 2014.08.21 ≈ 3.8k | 2015.09.11 ≈ 4.9k | 2016.09.13 ≈ 5.2k | 2017.08.25 ≈ 6.3k | 2018.10.08 ≈ 7.5k | 2019.08.01 ≈ 9.4k | 2020.04.02 ≈ 10.1k | 2020.11.05 ≈ 14.8k | 2021.03.29 ≈ 20.6k | 2021.06.30 ≈ 24.1k | 2022.04.12 ≈ 29.3k | 2022.10.05 ≈ 36.5k | 2023.01.18 ≈ 44.5k | 2023.05.24 ≈ 52.5k | 2023.10.26 ≈ 56.4k | 2024.03.01 ≈ 62.8k | 2024.06.25 ≈ 66.7k | 2024.10.30 ≈ 74.2k | 2025.04.08 ≈ 82.7k | 2025.06.13 ≈ 91.3k | 2025.09.25 ≈ 99.5k | 2025.11.17 ≈ 119.6k | 2026.01.21 ≈ 140k | 2026.03.30 ≈ 152k | fine ≈ 182k.
Picco di balance circa 177-180k intorno a 2026.01-02, seguito da un drawdown fino a circa 143-145k (coerente con un Balance DD max di 32 954.75 = 18.69%). Il picco di equity isolato è circa 190k (spike verde, p_00107, x≈1225), poi c'è un recupero fino alla fine.

## 4. Operazioni

**Nessuna operazione singola è leggibile.** Il video non mostra mai la lista History/Deals/Orders, il Journal o un grafico di prezzo con le frecce delle operazioni. Mostra solo il tab Graph e il report riassuntivo. `trades.csv` contiene quindi **solo l'intestazione**.

## 5. Comportamento sul grafico

- Nessun grafico di prezzo, oggetto, etichetta di cella o pannello dell'EA è visibile: il test gira in modalità non visuale e si vede solo il tab Graph.
- Indizi indiretti:
  - input "BE + PARZIALE LIBERA IL POSTO (false = conteggio normale)" = **true**, quindi break-even più chiusura parziale, che libera lo slot per un nuovo trade;
  - Deals 6152 contro Trades 4646, cioè circa 1506 ingressi e circa 3 uscite per posizione: chiusure parziali multiple;
  - "CRESCITA DEL LOTTO = COMPOSTO — i lotti crescono col conto", coerente con la curva esponenziale;
  - "QUANTO SPINGERE (LIVE ACCOUNT) = AGGRESSIVO".
- Tipo di ingresso (limit/stop/market), trailing e celle (PPK, OTEOF, PO3, …) non sono visibili. L'unico riferimento a una cella è nella notifica Telegram di un altro prodotto (vedi sotto: "EURUSD · PO3").

## 6. Altro testo

- p_00002 (3 s): titolo sovrapposto "**ICT RAPTOR AI PRIME**" ("PRIME" in magenta).
- p_00003 (6 s): overlay "**XAUUSD / SET: PRIME 1 / LIVE ACCOUNT / 1K START BALANCE**".
- p_00004 (9 s): overlay "**BUONA VISIONE / GUARDA TUTTO IL VIDEO**".
- p_00109 (324 s): "**SUBSCRIBE**" (bottone rosso con campanella), poi nero (p_00110, s_00010).
- s_00009 (1,9 s): logo sfocato bianco/magenta (presumibilmente "ICT RAPTOR AI PRIME", illeggibile).
- Notifiche Windows di Telegram ("web.telegram.org", "tramite Microsoft Edge") apparse durante il test:
  - p_00033 (96 s): "ICT RAPTOR AI PRIME @ ICT RAPTOR AI PRIME / AGENDA DI OGGI / XAUUSD · 1 eventi"
  - p_00039 e p_00040 (114-117 s): "ICT RAPTOR AI PRIME @ ICT RAPTOR AI PRIME / AGENDA DI OGGI / NAS100 · 1 eventi"
  - p_00045 (132 s): "ICT RAPTOR AI PRIME @ ICT RAPTOR AI PRIME / ICT RAPTOR AI PRIME ONLINE · EU / EURUSD"
  - p_00046 (135 s): "ICT RAPTOR AI PRIME @ ICT RAPTOR AI PRIME / AGENDA DI OGGI / EURUSD · 1 eventi"
  - p_00073 (216 s): "ICT RAPTOR CORE @ ICT RAPTOR AI CORE / (campanella) Ifo (EUR) · TRA 29' / EURUSD · PO3 / ▸ Orario 10:30 ITA (11:30 srv)". Mostra un prodotto/canale "ICT RAPTOR AI CORE", l'avviso di notizia Ifo (EUR) e il riferimento "PO3" su EURUSD; l'orario server è ITA+1.
- Versione e data dell'EA: **non visibili**. Il nome dell'expert nel tester non è leggibile ("Select expert..." nel tab Inputs). L'input intestazione "AUTOTRADER FOREX CLUB" = "atfc@gmail.com".
- Barra di stato: "For Help, press F1", "Default".
