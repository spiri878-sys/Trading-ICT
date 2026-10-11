# Checklist PRIME (sezione 3 della specifica)

Stati: **fatto** · **escluso** (con motivo) · **da fare** (fase prevista).

## 3.1 Sito — RAPTOR Ecosystem, versione PRIME

| # | Voce | Stato | Fase |
|---|---|---|---|
| 1 | Riferimento PRIME (non CORE/PLUS) e priorità delle fonti | **fatto** (`regole.md`) | 1 |
| 2 | Cella Raptor Mode (displacement, ritraccio confermato) | **generatore fatto** (`raptor/prime/cells.py`, test di non-lookahead); varianti da scegliere in validazione | 2 → 3/5 |
| 3 | Cella Order Flow OTE (ritraccio 62–79%) | **generatore fatto** (`raptor/prime/cells.py`, test di non-lookahead); varianti da scegliere in validazione | 2 → 3/5 |
| 4 | Cella PO3 (accumulo, manipolazione, distribuzione) | **generatore fatto** (`raptor/prime/cells.py`, test di non-lookahead); varianti da scegliere in validazione | 2 → 3/5 |
| 5 | Cella Unicorn (breaker + FVG non mitigato) | **generatore fatto** (`raptor/prime/cells.py`, test di non-lookahead); varianti da scegliere in validazione | 2 → 3/5 |
| 6 | Cella Liquidity Sweep | **generatore fatto** (`raptor/prime/cells.py`, test di non-lookahead); varianti da scegliere in validazione | 2 → 3/5 |
| 7 | Cella Breaker Block | **generatore fatto** (`raptor/prime/cells.py`, test di non-lookahead); varianti da scegliere in validazione | 2 → 3/5 |
| 8 | Marchio della cella su ogni ordine | da fare | 8 |
| 9 | Ogni set decide celle attive e soglie AI | da fare | 5, 8 |
| 10 | AI livello 1 — Occhio: 8 reti a maggioranza, soglie 0,60–0,70 | **fatto** (4 LightGBM + 4 MLP); in validazione non migliora | 5 |
| 11 | AI livello 2 — Selettori, soglie 0,78–0,92 | **fatto** (percentile per cella) | 5 |
| 12 | AI livello 3 — Supervisore LiqBias, soglie 0,70–0,72 | **fatto** (M5, AUC 0,53) | 5 |
| 13 | AI livello 4 — Semaforo e percorso: 2 modelli, capitale per trade | **fatto** (R atteso + P(+2R) → ×0,5/1/1,5) | 5 |
| 14 | AI livello 5 — Reparto macro (reti sul calendario) | da fare | 6 |
| 15 | Modelli ONNX in un solo file, nessuna dipendenza esterna | da fare | 8 |
| 16 | Modo Prop Challenge: +10%, poi chiude tutto, cancella i pendenti e si ferma | da fare | 7–8 |
| 17 | Modo Prop Funded: protezioni più severe | da fare | 7–8 |
| 18 | Modo Live Account | da fare | 7–8 |
| 19 | Modo Flip: −15% dimezza, −25% a un quarto, −30% chiude tutto | da fare | 7–8 |
| 20 | Livelli Aggressivo, Equilibrato (default), Prudente | da fare | 7 |
| 21 | Tabella di rischio con Monte Carlo a blocchi (3.000 giri) | da fare | 7 |
| 22 | Motore macro XAU: agenda 08:00, preavviso 10 minuti prima, ordine sul ritraccio previsto, esito | da fare | 6 |
| 23 | Macro alternativo alle celle ICT (in modalità macro le celle sono ferme) | da fare | 6, 8 |
| 24 | Stop, obiettivo, parziale e freni macro per modo e livello | da fare | 6–7 |
| 25 | Premium A / A+ / A++ (ingresso su Fibonacci, vaglio progressivo, A+ con filtro direzionale) | da fare | 7 |
| 26 | Premium attivabile e disattivabile; non tocca il macro | da fare | 8 |
| 27 | Telegram: avvio, agenda, ordini, target (+R e €), protezioni, challenge superata, obiettivo del mese | da fare | 8 |
| 28 | Pareggio, parziali, resto lasciato correre | **fatto in simulazione** (profilo FOTO); EA da fare | 3 → 8 |

## 3.2 Manuale PRO V5

| # | Voce | Stato | Fase |
|---|---|---|---|
| 29 | Timeframe del grafico indifferente, timeframe interno per cella | da fare | 8 |
| 30 | Tendine MERCATO e MODALITÀ; riga "Preset cella applicato"; combinazioni non certificate rifiutate | da fare | 8 |
| 31 | Timeframe interni: Sweep M3, PO3 M5, Raptor M5, Unicorn M15, OTE M12 | **fatto (dati)**: timeframe costruiti da M1, M3 e M12 ancorati all'ora; logica da fare | 0 → 2 |
| 32 | Catena: segnale → regimi → AI 1-2 → supervisore → macro → forecast → trade | **fatto** tranne il macro (Fase 6) | 5 |
| 33 | Selettore: 15 reti, una per cella, oltre 100 caratteristiche, probabilità di "big-runner" | **fatto** (modello unico, soglie per cella) | 5 |
| 34 | Gate Sì/No: 16 reti, qualità dell'ingresso, doppio consenso | **fatto** (livello più utile) | 5 |
| 35 | Supervisore di liquidità su M5 | **fatto** | 5 |
| 36 | Forecaster della direzione della barra successiva (blocca, aumenta, si astiene) | **fatto** | 5 |
| 37 | Calendario USA ed Euro-area dal 2007 | da fare (serve la fonte) | 6 |
| 38 | Scenario a tre stati con autovalutazione mensile | da fare | 6 |
| 39 | Orientamento EURUSD a 36 ore (solo documentato, non serve per XAU) | da fare | 6 |
| 40 | Filtro notizie (minuti prima e dopo) | da fare | 6, 8 |
| 41 | Scudo (riduzione del rischio prima degli eventi) | da fare | 6, 8 |
| 42 | La Voce (pannello e Telegram con contesto macro) | da fare | 8 |
| 43 | Gestione: 1R, parziale (90%) a +1R, pareggio, trailing strutturale, uscita adattiva | **fatto in simulazione** (`prime/label.py`, profili V5 e FOTO); EA da fare | 3 → 8 |
| 44 | Drawdown giornaliero in % o in valuta | da fare | 8 |
| 45 | Menu V5 (29 voci): sizing a rischio % o lotto fisso, ATR, RR, sessioni, grafica, Telegram | **documentato** (`menu_input.md` B, D); implementazione | 8 |
| 46 | Telegram V5: screenshot, chiusure, parziali, "+2R bloccato", report settimanale, scarti AI | da fare | 8 |
| 47 | Magic automatici per cella; ripresa dopo riavvio del VPS | da fare | 8 |

## 3.3 Presentazione prima versione

| # | Voce | Stato | Fase |
|---|---|---|---|
| 48 | Silver Bullet, MSS, Judas Swing, Order Block model | da fare (solo Piano B) | 10 |
| 49 | Market Brain, Trade Manager, Strategy Filter | da fare (solo Piano B o come riferimento) | 10 |
| 50 | Mediazioni | **escluso**: vietate dalla specifica (la PRIME è a operazioni singole) | — |

## 3.4 Video e foto

| # | Voce | Stato | Fase |
|---|---|---|---|
| 51 | Menu reale, operazioni sul grafico, trade dei backtest, messaggi Telegram | **fatto**: menu (`menu_input.md`); report dei 5 video; 5 trade e 16 segnali scartati XAU (`trade_riferimento.csv`); **nei video nessuna operazione singola è leggibile** | 1 |

## Dati (Fase 0)

| # | Voce | Stato |
|---|---|---|
| D1 | Inventario, duplicati, buchi, fuso, spread, coerenza tra fonti | **fatto** (`report_fase0.md`) |
| D2 | Cache Parquet e timeframe derivati M3, M5, M12, M15, M30, H1, H4, D1, W1 | **fatto** (`output/cache/`) |
| D3 | Anno di inizio dell'addestramento | **decisione cliente** (vedi report) |

## Fase 1

| # | Voce | Stato |
|---|---|---|
| F1 | `regole.md`, `menu_input.md`, `trade_riferimento.csv`, `numeri_dichiarati.md` | **fatto** |
| F2 | 4 pagine guida del sito e app Lovable | **non ricevute**: lacuna dichiarata |
| F3 | Trascrizione dell'audio dei video | **non necessaria**: i video non hanno parlato (solo musica e titoli) |
| F4 | Fase 2: generatore delle 6 celle, frequenze 2008–2021, confronto con i riferimenti | **fatto**; corrispondenza con i segnali del venditore al livello del caso (`report_fase2.md`) |
| F5 | Fase 3: etichette (big-runner, ingresso pulito, R) e baseline 2008–2021 | **fatto**: nessuna cella con vantaggio senza filtri (`report_fase3.md`) |
| F6 | Fase 4: 105 feature causali documentate, diagnostica sull'addestramento | **fatto** (`report_fase4.md`) |
| F7 | Fase 5: catena AI V5 + SITO, autoallenamento (congelato / soglia viva / annuale) | **fatto**: vantaggio onesto circa +0,03R (marginale) → proposta Piano B (`report_fase5.md`) |
