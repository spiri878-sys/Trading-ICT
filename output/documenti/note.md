# Documenti: note di lettura (Fase 1)

## A. Manuale "ICT RAPTOR AI PRO V5 — Manuale Operativo Cliente" (10 pagine, testo)

Riferimenti: `M5-pN` = pagina N.

Alcune celle delle tabelle sono **troncate nel PDF stesso**: il testo esce dal riquadro. Le frasi incomplete sono riportate con "…".

### Sintesi (M5-p2)
- Mercati XAUUSD, NAS100, EURUSD.
- 5 strategie ICT, 12 combinazioni certificate.
- 37 reti in 4 famiglie.
- Modulo macro con calendario 2007–2026 integrato e scenario probabilistico.
- Rischio: sizing a rischio %, parziali, pareggio, trailing strutturale, uscita adattiva.
- Protezioni: drawdown giornaliero, filtro notizie prop-ready, astensione AI.
- Tutto dentro un programma: nessun file esterno, nessuna connessione.
- Principio: "non insegue i prezzi — caccia la liquidità".

### Avvio (M5-p3)
1. Copiare in Experts.
2. Aprire il grafico: il timeframe è indifferente, il robot "usa sempre il suo timefra…".
3. Caricare il `.set` della combinazione (es. `NAS_SWEEP_M3_CLIENTE.set`): "tutte…".
4. In alto a destra deve comparire il simbolo del programma attivo; nel diario la riga **'Preset cella applicato'**.

**Tendine:** la sezione SELEZIONE STRATEGIA contiene **MERCATO** (XAUUSD / NAS100 / EURUSD) e **MODALITÀ** (la strategia). Scelta la coppia, il robot carica soglie AI, uscite e parametri.

**12 celle certificate:**

| Modalità (TF) | XAUUSD | NAS100 | EURUSD |
|---|---|---|---|
| Liquidity Sweep (M3) | OK | OK | OK |
| PO3 (M5) | OK | — | OK |
| ICT Raptor Mode (M5) | OK | OK | — |
| Unicorn Order Flow (M15) | OK | OK | — |
| OTE Order Flow (M12) | OK | OK | OK |

"Le combinazioni segnate '—' … il robot, per protezione, rifiuta di avviarle."

### Strategie (M5-p4)
- **Liquidity Sweep:** sfonda un massimo o minimo di riferimento per catturare gli stop e **rientra con forza**; posizione nella direzione del rientro.
- **PO3:** accumulazione (range), manipolazione (falsa rottura contro), distribuzione (vero movimento); entra **all'inizio della distribuzione**.
- **Raptor Mode:** "modalità aggressiva della casa": **displacement** più ritorni sulle **zone di squilibrio**; "più operazioni gestite in sequenza" nelle giornate direzionali.
- **Unicorn Order Flow:** sovrapposizione **Breaker Block + FVG**, armata **solo dopo sweep di liquidità e rottura di struttura**. Pochi segnali.
- **OTE Order Flow:** dopo **sweep e cambio di struttura**, attende il ritracciamento **62–79%** e vi posiziona l'ingresso "a sconto", con conferme di order flow.
- Ogni strategia lavora sul **proprio timeframe interno certificato (M3–M15)**.
- **Catena dei cancelli:** SEGNALE (strategia ICT) → REGIMI (filtro contesto) → AI 1-2 (selettore + Sì/No) → SUPERV. (liquidità) → MACRO (scudo/notizie) → FORECAST (direzione) → TRADE. "Basta un NO e il trade non nasce."

### Intelligenza artificiale (M5-p5)
- 37 reti, addestrate su 20 anni, walk-forward, "replicato bit-per-bit tra ricerca e programma finale".
- **Selettore**: 15 reti, una per cella. Oltre 100 caratteristiche (volatilità, struttura, volumi, sessione, contesto multi-timeframe). Stima la probabilità di **big-runner**; sotto soglia il segnale è scartato.
- **Gate Sì/No**: 16 reti. Valuta la qualità del punto d'ingresso; **doppio consenso** con il selettore.
- **Supervisore di liquidità**: 3 reti, una per mercato. Osserva gli **sweep su M5** e mantiene il **bias di fondo**.
- **Forecaster direzionale**: 3 reti, una per mercato. Prevede la **direzione della prossima barra** con un grado di fiducia:
  - confidente contro il segnale → blocca;
  - confidente a favore → può **aumentare il rischio**;
  - incerto → si astiene.

### Macro (M5-p6)
- Calendario USA ed Euro-area dal 2007 (NFP, CPI, Fed, BCE, ISM, occupazione).
- Facoltativo: con il solo interruttore generale osserva e racconta senza toccare i trade.
- **Scenario probabilistico** a 3 stati (Rallentamento, Crescita moderata, Pressione inflazionistica), con fattori e implicazioni per oro, dollaro e indici; autovalutazione a fine mese.
- **Orientamento EURUSD** 36 ore dopo una sorpresa USA confermata dal mercato; "regola certificata su sette anni".
- **Filtro notizie:** nessun nuovo ingresso nei minuti configurabili prima e dopo le notizie USA ad alto impatto; le posizioni aperte restano gestite.
- **Scudo:** in alternativa, riduce il rischio nelle ore prima degli eventi.
- **La Voce:** pannello e Telegram.

### Gestione (M5-p7)
- Ingresso con rischio 1R.
- **Parziale** al primo obiettivo; la figura indica **+1R**.
- **Pareggio** (stop all'ingresso).
- **Trailing strutturale** sui minimi e massimi di struttura, bloccando +1R, +2R…
- **Uscita adattiva** se il trend perde potenza, oppure TP.
- **Drawdown giornaliero** in % o in valuta: fermo fino al giorno dopo.

### Menu: 29 voci, oltre 160 parametri per cella sigillati (M5-p8/9)

| Gruppo | Voce | Significato |
|---|---|---|
| CLIENTE | Nome del cliente | Compilato alla consegna |
| GENERALE E SIZING | Magic Number | 0 = AUTOMATICO, univoco per mercato + strategia |
| | Balance del conto | Capitale di riferimento per rischio e drawdown |
| | Moltiplicatore contratto (ON/OFF + valore) | Solo per indici |
| | Metodo sizing | **RISCHIO %** (consigliato) / **LOTTO FISSO** |
| | Lotti per trade | Solo con lotto fisso |
| | Rischio per trade (%) | "Valore già ottimizzato nel set di ogni cella" |
| SELEZIONE STRATEGIA | MODALITÀ | Una delle 5 strategie |
| | MERCATO | XAUUSD / NAS100 / EURUSD |
| MACRO NEWS | Interruttore generale | OFF = spento; ON = osservazione e racconto |
| | No-trade notizie (ON/OFF) | "necessita del generale O…" |
| | Minuti prima / Minuti dopo | |
| STOP LOSS / TAKE PROFIT | Lunghezza ATR | Barre della volatilità di riferimento |
| | Moltiplicatore ATR | Distanza dello stop in ATR |
| | Target RR | "es. 1.8" |
| PROTEZIONE DRAWDOWN GIORNALIERO | Attiva (ON/OFF) | |
| | Unità | PERCENTUALE / MONEY |
| | Soglia | "es. 3 = 3%, oppure 1000 = 1.000 in valuta" |
| FILTRO SESSIONI · GRAFICA · TELEGRAM | Filtro sessioni | OFF = sempre operativo, "come da certificazione" |
| | Grafica a schermo (+ storico) | |
| | Telegram: attiva / Token / Chat ID / Nome | |
| | Telegram: Analisi | Scarti AI motivati, report giornaliero, macro |
| | Telegram: Gestione | Parziali, pareggio, multipli bloccati |

### Telegram (M5-p10)
- Benvenuto all'avvio.
- Apertura **con screenshot**, prezzo, stop e obiettivo; chiusure con esito e motivo.
- "**Parziale 90% incassata a +1R**", "Stop a pareggio: rischio azzerato", "**+2R bloccato**".
- Stop giornaliero; report settimanale (bilancio, migliori e peggiori).
- Segnali scartati dall'AI **con probabilità e soglia**; report giornaliero; macro.

### FAQ (M5-p10)
- Più celle sullo stesso conto con Magic = 0.
- Timeframe del grafico indifferente.
- Nessuna connessione esterna.
- Prop che vieta il news trading: Macro + No-trade.
- **Ripresa dopo riavvio del VPS.**
- Parametri interni non modificabili.

## B. Presentazione "ICT RAPTOR AI" (prima versione, 9 pagine-immagine; PNG in `output/documenti/presentazione/`)

| Pag. | Contenuto (verbatim o sintesi fedele) |
|---|---|
| 1 | "ICT RAPTOR AI — Pure Artificial Intelligence Trading". L'AI "prende decisioni autonome … selezionando la strategia ICT più efficiente in base al contesto attuale" |
| 2 | **Core features:** Unicorn Model, OTE, Silver Bullet, Power of Three (PO3), Market Structure Shift (MSS), Liquidity Sweep / Liquidity Grab. Tendina strategia: **Breaker block model, Order block model, Judas swing, Ote model, Po3, Unicorn model**. "Nessun settaggio strategico manuale … scelta strategica completamente demandata all'AI … adattamento dinamico a volatilità, struttura e liquidità" |
| 3 | "Prop firm & live broker ready": regole delle prop, stabilità su conto live, rischio "intelligente e adattivo" |
| 4 | Mercati: Index, Gold (XAU/USD), Forex |
| 5 | "Come lavora": le stesse sei strategie; "è l'AI a decidere in modo esclusivo quando, come e quale strategia applicare" |
| 6 | **Modello 1 Market Brain:** fase di mercato (trend, lateralità, volatilità, contesto istituzionale) e scelta della strategia. **Modello 2 Trade Manager:** entry a mercato, gestione dinamica, protezione del capitale, ottimizzazione del rischio, "gestione avanzata delle **mediazioni**". **Modello 3 Strategy Filter:** l'utente sceglie la strategia; l'AI la filtra, ne valuta la qualità, ottimizza l'esecuzione, autorizza l'ingresso solo in condizioni favorevoli |
| 7 | Telegram con foto del grafico all'ingresso e aggiornamenti. **Esempio reale**, bot `bot_simple_ea_` in spagnolo: "Nueva posición con el ticket 144663903 abierta · Símbolo XAUUSD · Dirección Compra · Takeprofit 0.000 · Stoploss 0.000 · Entry price 4826.172 · Tiempo de apertura (hora servidor) 2026.02.03 03:49 · (hora local) 2026.02.02 20:49 · Balance 10519.58". **Nota:** l'operazione d'esempio è senza SL e senza TP; la differenza server − locale è di 7 ore, coerente con server = NY + 7 |
| 8 | **Menu ufficiale (prima versione):** TYPE OF RISK (DYNAMIC/FIXED) · MAGIC NUMBER (7566) · SELECT STRATEGY · USE MARKET BRAIN AI? · USE TRADE MENAGER AI? · USE STRATEGY FILTER AI? (TRUE/FALSE) · USE MEDIATIONS? (YES/NO) · TYPE OF MEDIATIONS (DYNAMIC / FIXED / SETUP ZONES) · MAX TRADE MEDIATIONS · USE FVG CONFIRMATION (YES/NO) · TIMEFRAME FVG (M15/30/H1/H2 ETC) · USE TREND CONFIRMATION (YES/NO) · TIMEFRAME TREND (M15/30/H1 ETC) · SELECT TYPE TP & SL (FIXED/DYNAMIC) · POINT FIXED TP · POINT FIXED SL · VALUE DYNAMIC TP · VALUE DYNAMIC SL · USE TRAILING STOP (TRUE/FALSE) · POINTS TRAILING STOP · USE DAY PROTECTION? (YES/NO) · DROWDOWN MAX % |
| 9 | Chiusura: "Non è solo un robot … Miglior scelta del catalogo" |

Le **mediazioni** (pagine 6 e 8) sono escluse dalla PRIME e vietate dalla specifica.
