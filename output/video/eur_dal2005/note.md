# eur_dal2005: note di trascrizione

Video muto, 110 frame periodici (p_00001…p_00110, uno ogni 3 s, p_N = (N-1)*3 s) più 10 frame di cambio scena (s_00001…s_00010). Ho letto tutti i frame distinti:
- p_00009…p_00100 (24–297 s) mostrano solo la generazione progressiva del grafico. Li ho controllati tramite montaggio delle strisce di asse e di avanzamento.
- s_00001…s_00007 sono la sigla animata iniziale (un blocco di ghiaccio, poi la scritta "RAPTOR AI PRIME" sfocata).

Piattaforma: MetaTrader 5, titolo della finestra "25787667 - VantageMarkets-Demo: Demo Account - Hedge - Vantage Markets (Pty) Ltd" (con "[EURUSD COMPLETE HISTORY,M5]" dal frame p_00101).

## 1. Menu input
Fonti: p_00002 (3 s), p_00003 (6 s, con la tendina SET aperta), p_00005 (12 s, menu scrollato fino a LIVE ACCOUNT / FLIP) e p_00006 (15 s). Colonne: Variable / Value / Start / Step / Stop. Le righe sono nell'ordine in cui appaiono a schermo.

| # | Gruppo | Etichetta (verbatim) | Value | Start | Step | Stop |
|---|---|---|---|---|---|---|
| 1 | (nessun gruppo) | AUTOTRADER FOREX CLUB | atfc@gmail.com | | | |
| 2 | IMPOSTAZIONI PRINCIPALI | BE + PARZIALE LIBERA IL POSTO (false = conteggio normale) | true | false | | true |
| 3 | IMPOSTAZIONI PRINCIPALI | PREMIUM (false = celle originali, come ora) | false | false | | true |
| 4 | IMPOSTAZIONI PRINCIPALI | PREMIUM: quale livello | PREMIUM A    (solo ENTER) | PREMIUM A (solo ENTER) | | PREMIUM A++ (ENTER + MAIN + SEC… (troncato) |
| 5 | IMPOSTAZIONI PRINCIPALI | MERCATO | EURUSD | XAUUSD | | EURUSD |
| 6 | IMPOSTAZIONI PRINCIPALI | MODALITA OPERATIVA | LIVE ACCOUNT | PROP CHALLENGE | | FLIP |
| 7 | IMPOSTAZIONI PRINCIPALI | SET | EURUSD PRIME 2 | (interno) | | PRIME MACRO EUR |
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

I gruppi successivi (gli altri parametri FLIP, SUPERVISORE…) non sono visibili in questo video.

Opzioni della tendina SET (p_00003, 6 s), nell'ordine in cui appaiono:
1. (interno)
2. XAUUSD PRIME 1
3. XAUUSD PRIME 2
4. NAS PRIME 1
5. NAS PRIME 2
6. EURUSD PRIME 1 (evidenziata dal passaggio del mouse)
7. EURUSD PRIME 2
8. PRIME MACRO XAU
9. PRIME MACRO NAS
10. PRIME MACRO EUR

Il valore scelto è "EURUSD PRIME 2" (p_00005 e p_00006).

Parametri dell'EA trasmessi nell'intestazione del grafico (p_00101, 300 s; testo piccolo e sovrapposto alle candele, letto in parte): "ICT RAPTOR AI PRIME - AUTOTRADER FOREX CLUB - 999000 [InpClienteEmail=atfc@gmail.com; ' ☺ IMPOSTAZIONI PRINCIPALI='; InpBE…(illeggibile)…Posto=true; InpPremium=false; InpPremiumLiv=0; InpAIPair=2; InpModalita=2(?); InpConfig=10; InpLev(?)=0(?); InpV11_ContrattoIndici=0.0; InpMagicNumber=999000; ' ⧗ PROP CHALLENGE='; InpPF_C…(troncato)".

Nomi interni dedotti: InpAIPair = MERCATO (2 = EURUSD?), InpConfig = SET (10 = EURUSD PRIME 2?). La corrispondenza tra nomi e parametri è un'inferenza.

## 2. Impostazioni del tester
La scheda Settings non viene mostrata.
- Simbolo e timeframe: EURUSD COMPLETE HISTORY, M5 (simbolo custom; p_00101). La riga del grafico mostra "EURUSD COMPLETE HISTORY, M5: Euro vs US Dollar 1.16304 1.16312 1.16291 1.16310 252".
- Periodo: l'asse X del grafico finale (p_00101) va da 2005.01.31 a 2025.12.08, quindi dal 2005. Le date esatte impostate non sono visibili.
- Modellazione, ritardi e leva del tester: non visibili. Il parametro EA LEVA DEL CONTO vale 1:100.
- Deposito iniziale: 1 000.00 (report).
- Durata del test: "00:07:04 / 00:07:08" (p_00101). Prima dell'avvio, nei frame degli input, il contatore mostra "00:08:49 / 00:08:54", cioè un test precedente.
- History Quality: 100%. Bars: 1603114. Ticks: 31775868. Symbols: 1.

## 3. Report
Fonte: p_00102 e p_00104 (303–309 s), con crop ingranditi su p_00107 (318 s).

| Statistica | Valore |
|---|---|
| History Quality | 100% |
| Bars | 1603114 |
| Ticks | 31775868 |
| Symbols | 1 |
| Initial Deposit | 1 000.00 |
| Total Net Profit | 36 024 514.10 |
| Gross Profit | 69 296 011.65 |
| Gross Loss | -33 271 497.55 |
| Profit Factor | 2.08 |
| Expected Payoff | 4470.10 |
| Recovery Factor | 76.64 |
| Sharpe Ratio | 5.90 |
| AHPR | 1.0013 (0.13%) |
| GHPR | 1.0013 (0.13%) |
| LR Correlation | 0.98 |
| LR Standard Error | 2 479 321.86 |
| Z-Score | -18.82 (99.74%) |
| OnTester result | 2.082743992688118 |
| Margin Level | 843.18% |
| Balance Drawdown Absolute | 0.00 |
| Balance Drawdown Maximal | 432 895.00 (1.34%) |
| Balance Drawdown Relative | 9.35% (220.74) |
| Equity Drawdown Absolute | 6.30 |
| Equity Drawdown Maximal | 470 020.00 (1.45%) |
| Equity Drawdown Relative | 10.82% (6 416.20) |
| Total Trades | 8059 |
| Total Deals | 11876 |
| Short Trades (won %) | 4043 (84.49%) |
| Long Trades (won %) | 4016 (81.55%) |
| Profit Trades (% of total) | 6691 (83.03%) |
| Loss Trades (% of total) | 1368 (16.97%) |
| Largest profit trade | 105 100.00 |
| Largest loss trade | -87 559.44 |
| Average profit trade | 10 356.60 |
| Average loss trade | -24 321.27 |
| Maximum consecutive wins ($) | 83 (335 734.42) |
| Maximum consecutive losses ($) | 7 (-231 195.00) |
| Maximal consecutive profit (count) | 574 843.33 (60) |
| Maximal consecutive loss (count) | -283 997.65 (6) |
| Average consecutive wins | 7 |
| Average consecutive losses | 2 |
| Correlation (Profits,MFE) | 0.71 |
| Correlation (Profits,MAE) | 0.52 |
| Correlation (MFE,MAE) | -0.0486 |
| Minimal position holding time | 0:03:40 |
| Maximal position holding time | 170:19:40 |
| Average position holding time | 10:39:56 |

Fonte dei tempi di detenzione: p_00106 (315 s).

Nota: Total Deals 11876 contro 8059 trade, cioè circa 3817 deal in più. Questo è compatibile con chiusure parziali (inferenza).

### Grafici
**Curva Balance/Equity** (p_00101, 300 s; costruzione progressiva da p_00009 a p_00100):
- Asse Y (verbatim): 39501079, 36747521, 33993963, 31240406, 28486848, 25733290, 22979732, 20226175, 17472617, 14719059, 11965501, 9211944, 6458386, 3704828, 951270, -1802287 (ultimo incerto).
- Asse X: 2005.01.31, 2006.01.23, 2007.03.30, 2008.04.14, 2009.01.16, 2009.07.27, 2010.06.15, 2011.04.25, 2012.01.16, 2012.12.31, 2013.10.14, 2014.03.18, 2014.11.27, 2015.08.14, 2016.07.0x, 2017.03.29, 2017.11.15, 2018.07.26, 2019.01.23, 2019.10.11, 2020.06.02, 2021.03.17, 2021.07.19, 2022.05.02, 2023.02.21, 2023.12.04, 2024.06.21, 2025.04.18, 2025.12.08.
- Forma: piatta, vicina allo zero, dal 2005 al 2008. Da metà 2009 al 2013 sale rapidamente: la fase più ripida, fino a circa 13–14M a fine 2012. Poi la crescita continua quasi lineare con leggere ondulazioni: circa 21M nel 2016, circa 28M nel 2019, circa 33M nel 2021, circa 35.5M nel 2024, circa 37M a fine 2025. Nel 2023–2024 c'è un piccolo tratto piatto o in lieve calo. I valori intermedi sono stime visive.
- Deposit Load: barre verdi alte e fitte dal 2005 a circa il 2009–2010, poi il carico scende quasi a zero (lotto composto contro saldo molto grande).

**Entries by hours (Asia,Europe,USA)**, scala 0–380:
- Picco alle ore 7 (circa 370), poi alle 6 (circa 290) e alle 8 (circa 275). Dalle 9 alle 13 circa 210–245 (picco locale alle 12, circa 245). Ore 1: circa 210. Ore 14–20: tra circa 90 e 145. Ore 21–23: basse (circa 40, 10, 40). Ore 0, 3, 4 e 5: circa 80–120.
- Profits and losses by hours (scala illeggibile in parte, top 797000): profitti massimi alle 12, 13 e 14, poi alle 7 e alle 8.

**Entries by weekdays**, scala 0–790: Mon–Fri quasi uniformi, tra circa 740 e 790; Wed e Thu sono i più alti, Mon il più basso. Sun e Sat 0.
- Profits and losses by weekdays (scala 0–14673000): profitti tra circa 13M (Mon) e circa 14.7M (Thu). Perdite: circa 4.8M il Mon, circa 7.5–7.7M Tue e Wed, circa 7M il Thu, circa 6.4M il Fri.

**Entries by months**, scala 0–340: tutti i mesi tra circa 290 e 340. Massimi a May e Oct (circa 340), minimo a Dec (circa 290).
- Profits and losses by months (scala 0–6233000): profitti tra circa 5.2M (Feb) e circa 6.2M (May–Aug). Perdite tra circa 2.3M (Jul) e circa 3.3M (Oct).

**Scatter** (p_00105–p_00106):
- Profits vs MFE: nuvola blu lungo una diagonale crescente, MFE fino a circa 205000. C'è una banda separata di perdite a circa -30000, con MFE tra 0 e circa 40000.
- Profits vs MAE: nuvola rossa concentrata tra MAE 0 e circa -45000.
- Holding time vs profit: punti verdi concentrati sui tempi brevi.

## 4. Operazioni
Nel video non compaiono la lista dei deal/ordini né la scheda History, quindi non ci sono operazioni singole leggibili. trades.csv contiene solo l'intestazione.

## 5. Comportamento sul grafico
- Si vede solo la striscia superiore del grafico M5 (candele e griglia, 6 Jan 2020 dalle 08:15 alle 15:35), senza ordini né oggetti dell'EA leggibili. Non è visual mode.
- "BE + PARZIALE LIBERA IL POSTO" = true indica break-even e chiusura parziale attivi; il rapporto deal/trade è coerente. Le chiusure parziali non sono osservate direttamente.

## 6. Altro testo
- s_00001…s_00007 e p_00001 (0 s): sigla animata con il logo "ICT RAPTOR AI PRIME" ("PRIME" in magenta).
- p_00002 (3 s), overlay: "EURUSD / SET: PRIME 2".
- p_00004 (9 s), overlay: "BUONA VISIONE TRADER".
- p_00109 (324 s): grafica "SUBSCRIBE" con la campanella. p_00110 (327 s): nero.
- Orologio della taskbar: 23:27 nei frame degli input e 23:35 nel report, data 20/08/2026. Account 25787667 VantageMarkets-Demo, Hedge. Market Watch: EURUSD Bid 1.16761, Ask 1.16808 (o 1.16805), Daily Change -0.02%.
- La versione e la data dell'EA non sono visibili. Nell'intestazione del grafico compare il nome completo "ICT RAPTOR AI PRIME - AUTOTRADER FOREX CLUB - 999000".
