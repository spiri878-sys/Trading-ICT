# Registro delle evidenze

Categorie:

- **DOCUMENTATO**: dichiarato esplicitamente da una fonte ufficiale.
- **OSSERVATO**: visibile in un video o in uno screenshot.
- **INFERITO**: interpretazione plausibile, non confermata.
- **SPERIMENTALE**: soluzione nostra, non attribuibile al prodotto.
- **NON VERIFICATO**: non è stato possibile controllarlo.
- **NON DISPONIBILE**: informazione necessaria assente dai materiali accessibili.

Nessuna voce INFERITA o SPERIMENTALE va letta come regola del prodotto originale. Il codice proprietario di ICT RAPTOR AI PRIME **non** è disponibile: questo progetto è una ricostruzione indipendente.

## Fonti consultate

| ID | Fonte | Accesso reale | Note |
|---|---|---|---|
| S1 | https://autotraderforexclubea.com/ (e /en/…) | **NO**: la policy di rete del container restituisce 403 e il DNS non risolve; stesso esito per WebFetch | Mai aperto direttamente |
| S2 | Riassunti del motore di ricerca sulla pagina S1 (WebSearch, 10/10/2026) | Sì, ma solo come estratti di terza mano | Usati con affidabilità ridotta |
| S3 | https://www.youtube.com/@autotraderforexclub | **NO** (bloccato); visto solo nei risultati di ricerca | |
| S4 | web.archive.org | **NO** (bloccato) | |
| V1 | `Backtest_ICT_RAPTOR_AI_PRIME_live_account_balance_1K_EURUSD` (.mkv, 50 s) | Sì: fotogrammi estratti con ffmpeg | Nessun parlato (solo musica/titoli) |
| V2 | `…_NASDAQ` (.mkv, 59 s) | Sì | |
| V3 | `Backtest_live_…_XAUUSD` (.mkv, 329 s) | Sì: un fotogramma ogni 4 s | |
| V4 | `…_ON_STEROID_NASDAQ` (.mkv, 100 s) | Sì | Contiene la scheda *Settings* del tester |
| V5 | `…_DAL_2005_Eurusd` (.mkv, 329 s) | Sì | |
| I1–I16 | 16 screenshot da YouTube Shorts "INTERSTELLAR · XAUUSD" (caricati il 10/10/2026) | Sì | |
| D1 | `barre_xauusd_m1_2017.part1/2.rar` | Sì: RAR5 multivolume estratto con libarchive; dimensione dichiarata = estratta | CSV in formato MT5, 3.086.760 righe |
| U1 | Testo dell'utente (prompt): "sei strategie selezionabili" del sito | Sì (come testo riportato) | Non verificato su S1 |

## Evidenze

| ID | Fonte / punto | Caratteristica | Evidenza | Categoria | Effetto sul progetto | Test necessario |
|---|---|---|---|---|---|---|
| E-01 | S2 | Linea prodotti | CORE / PLUS / PRIME, EA MT5, ICT/SMC, modelli ONNX, oro / Nasdaq / EURUSD | DOCUMENTATO (via S2) | Solo XAUUSD per scelta del committente | — |
| E-02 | S2 | Motore macro PRIME | Unico livello che opera sulle notizie; "93 modelli addestrati solo sul calendario economico"; 3 set macro | DOCUMENTATO (via S2) | **NON RIPRODUCIBILE**: nessun calendario storico disponibile | Servirebbe un calendario con orari e valori 2018–2026 |
| E-03 | S2 | Raptor Mode | "riconosce la struttura, attende lo spostamento deciso ed entra solo sul ritraccio confermato" | DOCUMENTATO (via S2) | Base della cella PPK (rottura + displacement + FVG + ingresso limit sul ritracciamento) | EXP-01..07 |
| E-04 | S2 | Premium | Filtra i setup in modo più severo, prezzo migliore, attende il pullback | DOCUMENTATO (via S2) | Parametro `entry_depth` (0 = bordo FVG, 0,5 = CE) | Non testato in modo sistematico |
| E-05 | S2 | Sei celle di strategia sullo stesso grafico | "Le sei celle di strategia" | DOCUMENTATO (via S2) | Registro delle strategie | — |
| E-06 | U1 | Le sei strategie | Unicorn, OTE, Silver Bullet, Power of Three, MSS, Liquidity Sweep | DOCUMENTATO (riportato dall'utente; non verificato su S1) | Moduli UNIOF, OTEOF, SILVER_BULLET, PO3, MSS, LS | research_metrics.csv |
| E-07 | S2 | Telegram | Invia decisioni di trading e agende macro | DOCUMENTATO (via S2) | Modulo `Telegram.mqh` separato, spento di default | Non testabile qui |
| E-08 | S2 | Il robot non scarica nulla e non interroga server; 168 modelli in un file; 34.788 operazioni analizzate | Dichiarazioni di marketing | DOCUMENTATO (via S2) / NON VERIFICATO | Nessuno | — |
| E-10 | V1–V5 fotogrammi Inputs | Gruppi di input | IMPOSTAZIONI PRINCIPALI, PROP CHALLENGE, PROP FUNDED, LIVE ACCOUNT, FLIP, SUPERVISORE LIQBIAS, FILTRO NOTIZIE, MESSAGGI GRAFICA | OSSERVATO | Modalità capitale non replicate (prop/flip): fuori dal perimetro | — |
| E-11 | V1, V5 (Inputs) | Input principali | `BE + PARZIALE LIBERA IL POSTO` (true), `PREMIUM` (false = celle originali), `PREMIUM: quale livello` (PREMIUM A solo ENTER … A++ ENTER+MAIN+SEC…), `MERCATO`, `MODALITA OPERATIVA`, `SET` (interno, XAUUSD PRIME 1/2, NAS PRIME 1/2, EURUSD PRIME 1/2, PRIME MACRO XAU/NAS/EUR), `LEVA DEL CONTO`, `MAGIC NUMBER` | OSSERVATO | Break-even + parziale implementati; set e livelli Premium non replicabili (contenuto interno) | — |
| E-12 | V4 (Inputs, versione del 31/08/2026) | Stop minimo | `STOP MINIMO IN ATR (0 = spento)`; `LEVA IMPOSTA DALLA PROP`; `LEVA DEL CONTO LIVE` | OSSERVATO | Input `InpMinStopAtrM15` / `min_stop_m15` (timeframe dell'ATR **INFERITO**: M15) | EXP-02, stop_width_vs_lot.csv |
| E-13 | V3 (t≈0 s) | Supervisore e notizie | `SUPERVISORE LIQBIAS (false = come certificato)`, `SUPERVISORE: soglia 1..99 (-1 = quella della cella)`, `NON OPERARE SULLE NOTIZIE`, minuti PRIMA/DOPO = 30/30 | OSSERVATO | Filtro notizie 30/30 (solo live: il calendario MT5 non esiste nel tester); soglia per cella → soglia del filtro AI | — |
| E-14 | V4 (Settings) | Condizioni del tester | Simbolo personalizzato `NAS100_COMPLETE HYSTORY`, M5, 2018.01.01–2026.08.30, **Modelling: 1 minute OHLC**, **Delays: Zero latency, ideal execution**, deposito 1000 USD, leva 1:500 | OSSERVATO | I backtest del venditore usano un'esecuzione ideale e barre M1 OHLC: risultati ottimistici | Rieseguire in modalità "Every tick based on real ticks" |
| E-15 | V5 (report) | EURUSD 2005–2025, PRIME 2 | 1.603.114 barre, 31,7 M tick, 8059 trade, 11.876 deal, PF 2,08, 83% di vincite, saldo da 1000 a 36 M (compounding) | OSSERVATO | Deal/trade = 1,47 → **parziali** confermati | — |
| E-16 | V1 (report) | EURUSD set PRIME MACRO EUR, start 1K | 1653 trade, 2656 deal, PF 2,66; ingressi concentrati tra le 15 e le 16 ora server, soprattutto il **giovedì** | OSSERVATO | Coerente con il motore macro (dati USA delle 8:30 ET = 15:30 server) | NON RIPRODUCIBILE (E-02) |
| E-17 | V2 / V4 (report) | NAS100 | PRIME MACRO NAS: 1005 trade, PF 3,07; NAS PRIME 1 "on steroid": 1786 trade, PF 2,84 | OSSERVATO | Fuori perimetro (solo XAUUSD) | — |
| E-18 | V3 (report) | XAUUSD 2005→maggio 2025, set XAUUSD PRIME 1, start 1K, LIVE ACCOUNT, compounding | 4646 trade, 6152 deal, PF 1,46, 85% di vincite, DD 18,7%, da 1000 a 182 k; ingressi con picco all'ora server **01** | OSSERVATO | Picco all'apertura asiatica annotato (feature `ny_hour`) | — |
| E-19 | V3 (grafico, 2007–2011) | Curva XAUUSD dei primi anni | Laterale con drawdown di circa il 13% (da ~1650 a ~1430) prima della crescita | OSSERVATO | Anche il prodotto mostra anni piatti | — |
| E-20 | I-cascata | Celle Interstellar | "5 CELLE ICT: PPK · OTEOF · PO3 · UNIOF · LS: i punti d'ingresso precisi" | OSSERVATO | Moduli con gli stessi nomi; **le regole interne sono INFERITE** | — |
| E-21 | I-cascata | Dataset | "49.000 segnali, oro ed EUR dal 2005, NAS dal 2018: ogni segnale con il suo esito vero" | OSSERVATO | Etichettatura per segnale isolato (`engine.label`) | — |
| E-22 | I-cascata | Feature | "92 ingressi: struttura, volatilità, sessione, spread, stop, probabilità delle celle: solo rapporti, mai prezzi" | OSSERVATO | 44 feature a soli rapporti (`raptor/features.py`), **SPERIMENTALE** nella scelta | ai_comparison.json |
| E-23 | I2 / I-cascata | Modello | "VEDE-25 · G_CELLA · MODELLO8: gradient boosting, 1500 alberi, 127 foglie, allenato fino al 31/12/2025 e congelato" | OSSERVATO | VEDE-25 è il **nome del venditore**. Il nostro modello (`models/rr_filter_*`) è un LightGBM indipendente, non VEDE-25 | — |
| E-24 | I5–I7 | Soglia viva | "il robot ricorda gli ultimi 1000 punteggi: prende solo il 20% migliore" (quantile 80%); soglia fissa r39 = 0,2426; 1733 segnali giudicati nel 2026, 169 presi | OSSERVATO | `ml.living_threshold(window=1000, q=0.8)` | ai_comparison.json |
| E-25 | I8 | Gestione su barre M1 | PPK BUY 08/01/2026: stop $21 = 1R; 20% chiuso a +0,7R con stop a pareggio; 20% a +2R; il resto al target 4R; "decisi sulla barra chiusa" | OSSERVATO | Profilo A: scala 0,7R / 2R / 4R (20/20/60), BE dopo P1, decisione sulla chiusura M1 | test_ladder_partials_and_breakeven |
| E-26 | I9 | Giornale dei perché | Motivi di rifiuto: visione del grafico asse, spread troppo alto per la volatilità, volatilità fuori norma, stop fuori misura (M15/H1), cella non convinta, notizia in arrivo, rotture contro / poche a favore, spinta a 60 min / 3 h, posizione nel range 4h/24h, distanza dalla media | OSSERVATO | Feature omonime; il log CSV registra il motivo di ogni rifiuto; `ml.explain_rejections` (contributi SHAP) | — |
| E-27 | I-rischio | Rischio che respira | Base 1,92%; pieno fino a −5% di DD, poi scende fino a ×0,25 a −23,75%; ripresa piena dopo 20 trade in utile; mai aumenti | OSSERVATO | `breathe_*` (Python) e `InpBreathe*` (EA) | test di unità mancante (vedi limiti) |
| E-28 | I-costi | Costi | Costo per trade in R = spread/stop + A·bp + B·f (swap); oro 0,019R; swap XAU −79,48 / +34,41 $ per lotto e notte | OSSERVATO | Lo swap **non** è modellato nel simulatore (vedi limits.md) | — |
| E-29 | I-monitor | Monitor fuori scala | Feature confrontate con la banda 1–99% dello storico 2005–25; "stop in ATR M15 storico 1,964..27,87" | OSSERVATO | Gli stop originali sono ampi (≥ ~2 ATR M15): ipotesi H1, testata in EXP-01/02/07 | — |
| E-30 | I-monte carlo | Monte Carlo | 3000 percorsi, blocchi di 10 trade, rischio 1,92% | OSSERVATO | Non applicato: nessuna strategia con aspettativa positiva da ricampionare | — |
| E-31 | I-tre mercati / I-trade | Risultati 2026 dichiarati | XAU 2026: 169 trade, PF 1,7, +99%; tre mercati +126% | OSSERVATO (dichiarazione del venditore) | NON VERIFICATO | — |
| E-32 | D1 | Dati | MT5 Export Bars, server time, 2018-01-02 10:00 → 2026-10-09 23:54; il nome dice "2017" ma i dati partono dal 2018; **M5 dal 2005 non fornito** | OSSERVATO | Periodi di ricerca limitati al 2018–2026 | data_quality.md |
| E-33 | D1 | Spread | 2018–2022: 100–240 punti, sempre multipli di 10, maggiori dell'intero range M1 nel 92% delle barre; 2023+: 0–20 punti (43–49% di zeri) | OSSERVATO; unità 2018–22 = 0,001 **INFERITA** | Modelli di costo C1 / C0 / C0R / C2 | spread_diagnosis.json |
| E-34 | D1 | Ora server | Pausa giornaliera 23:55 → 01:01 e apertura settimanale alle 01:00 → server = New York + 7h | INFERITO (forte) | `NY_OFFSET_H = 7`, input `InpNyOffsetHours` | Verificare sul broker |

## Contraddizioni rilevate

- Il sito (via S2) parla di **sei** celle, gli Shorts "Interstellar" (I-cascata) di **cinque**: PPK, OTEOF, PO3, UNIOF, LS.
  - MSS e Silver Bullet compaiono solo nella lista del sito.
  - PPK compare solo negli Shorts.
  - Le abbiamo implementate tutte, ciascuna disattivabile.
- La versione del 20/08/2026 (V1, V5) non ha `STOP MINIMO IN ATR`; quella del 31/08/2026 (V4) sì. Le versioni del prodotto cambiano nel tempo.
- I report del venditore usano **Zero latency, ideal execution** e **1 minute OHLC** (E-14). Il nostro simulatore usa ipotesi conservative: SL prioritario nella stessa barra, slippage, costi fissi. I numeri non sono confrontabili 1:1.
