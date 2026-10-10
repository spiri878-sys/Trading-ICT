# Ricostruzione delle strategie e matrice delle funzionalità

Tutte le regole qui sotto sono **definizioni nostre**, operative e prive di look-ahead, dei concetti ICT/SMC il cui **nome** compare nelle fonti (vedi `evidence_register.md`). Il venditore non ha pubblicato le regole interne: nessuna cella va considerata identica a quella del prodotto.

Implementazione di riferimento:

- `python/raptor/strategies/ict.py` e `wyckoff.py`
- specchio MQL5: `mql5/Include/RaptorRecon/Cells.mqh`, con parità dei default verificata da `tools/mql5_static_check.py`

## Elementi di base (causali)

| Elemento | Definizione operativa | Quando è noto |
|---|---|---|
| Swing high/low | Frattale con k barre per lato (k = 3 su M5) | A chiusura della barra pivot + k |
| BOS | Chiusura oltre l'ultimo swing confermato, non ancora rotto | Alla chiusura della barra di rottura |
| MSS / CHoCH | BOS in direzione opposta alla rottura precedente | Come sopra |
| Gamba (leg) | Min/max fra lo swing opposto precedente e la barra di rottura | Come sopra |
| Displacement | Corpo massimo delle ultime 3 barre ≥ `min_disp` × ATR(14) | Chiusura barra |
| FVG | Barre i-2, i-1, i: rialzista se low(i) > high(i-2); ribassista se high(i) < low(i-2) | Chiusura della barra i |
| Breaker | Ultima candela opposta (≤ 6 barre) allo swing rotto | Alla rottura |
| Liquidità esterna | High/low del giorno server precedente (PDH/PDL) | Dall'apertura del giorno |
| Range asiatico | High/low server 03:00–07:00 (= NY 20:00–00:00) | Dalla barra delle 07:00 server |
| Sweep / raid | Prima violazione del giorno di PDH/PDL o del range asiatico | Chiusura barra |
| Contesto HTF | ATR / EMA50 di M15, H1, H4, D1 dalle **sole barre chiuse** (join sull'orario di disponibilità) | Chiusura della barra HTF |
| Orario NY | Server − 7 h (pausa giornaliera del feed 23:55 → 01:01) | — |

## Celle

Per tutte le celle valgono queste regole comuni:

- **Ordine**: limit al livello indicato; Wyckoff entra a mercato.
- **Validità**: espressa in barre del timeframe del segnale.
- **Stop strutturale**: livello indicato ± 0,2 × ATR.
- **Filtri di rischio**: si rifiuta il segnale se il rischio è < 0,5 ATR o > 15 ATR.

| Cella | Nome nelle fonti | Trigger | Ingresso | Stop | Classificazione |
|---|---|---|---|---|---|
| **PPK** | E-20 (solo il nome) + E-03 "Raptor Mode" | BOS + displacement ≥ 1,2 ATR + FVG ≥ 0,15 ATR | Bordo prossimale dell'FVG (ritracciamento) | Oltre la gamba | INFERITA |
| **MSS** | E-06 | Come PPK, ma solo MSS / CHoCH | Bordo FVG | Oltre la gamba | INFERITA |
| **OTEOF** (OTE) | E-06, E-20 | BOS + displacement ≥ 1,2 ATR | 70,5% della gamba | Oltre la gamba | INFERITA |
| **PO3** | E-06, E-20 | Raid del range asiatico (24 barre) + MSS opposto con FVG, NY 02:00–11:00 | Bordo FVG | Oltre il raid | INFERITA |
| **UNIOF** (Unicorn) | E-06, E-20 | MSS + FVG che si sovrappone al breaker | Bordo della sovrapposizione | Oltre la gamba | INFERITA |
| **LS** (Liquidity Sweep / Turtle Soup) | E-06, E-20 | Sweep di PDH/PDL/Asia con chiusura di nuovo dentro | Metà fra livello e chiusura | Oltre l'estremo | INFERITA |
| **SILVER_BULLET** | E-06 | FVG ≥ 0,25 ATR nelle finestre NY 03–04, 10–11, 14–15 | Bordo FVG | Oltre la candela 1 | INFERITA |
| **MTF_M1** | — | Bias H4 + H1, raid di 30 barre e MSS su M1 | Bordo FVG | Oltre il raid | SPERIMENTALE (respinta, EXP-10) |
| **WYCKOFF** | — | Spring/upthrust di un range di 48 barre (altezza 1–3 ATR H1) | Mercato | Oltre lo spring | Benchmark separato |

## Profili

| Profilo | Contenuto | Stato |
|---|---|---|
| **A: FAITHFUL_M5** | Celle su M5 (k = 3). Gestione E-25: 20% a +0,7R + break-even, 20% a +2R, il resto a 4R; decisioni sulla barra M1 chiusa; massimo 3 giorni di durata; chiusura il venerdì alle 23:00 server | Ricostruzione fedele. **Aspettativa negativa** (reports) |
| **B: EXPERIMENTAL** | PPK + UNIOF su H1 (k = 3), ingresso a mercato, TP 3R, nessun parziale, durata massima 48 h | Positivo in dev, **respinto** in validazione (VAL-01) |
| **C: UNICORN_LONG** | Solo UNIOF, solo long, M15 (k = 3), stop = min(stop della cella, ultimo swing low H4 confermato − 0,2 ATR H4), scartato se il rischio > 6 ATR H4; TP 3R, nessun parziale, durata massima 48 h | SPERIMENTALE, sopravvissuto al walk-forward (WF-01). Positivo, ma **dipendente dalla tendenza rialzista dell'oro** (gli short perdono in tutte le varianti) |
| **W: WYCKOFF_BENCH** | Solo Wyckoff, stessa esecuzione | Benchmark, negativo |

## Timeframe usati e motivazione

- **M1**: esecuzione e gestione (fill, SL/TP, decisioni sulla barra M1 chiusa: E-25). La conferma d'ingresso su M1 (MTF_M1) è risultata dannosa anche a costo zero.
- **M5**: timeframe dei segnali del profilo A. Gli orari dei segnali I1–I9 sono multipli di 5 minuti (es. 00:50, 11:15, 12:20): INFERITO.
- **M15, H1**: ATR per lo stop minimo e per le feature "stop in ATR M15/H1" (E-26, E-29).
- **H4, D1**: solo feature e bias. M30 e H4 come timeframe di segnale sono stati testati (EXP-04) senza beneficio, quindi non sono usati.

## Matrice funzionalità osservate → moduli

| Funzionalità (evidenza) | Python | MQL5 | Stato |
|---|---|---|---|
| Celle ICT selezionabili (E-05, E-06, E-20) | `strategies/ict.py`, `REGISTRY` | `Cells.mqh`, input `InpCell*` | Implementato |
| Break-even + parziale (E-11, E-25) | `engine._manage` | `PositionManager.mqh` | Implementato e testato (Python) |
| Target 4R e scala 0,7/2/4 (E-25) | `Params.tp_r/p1/p2` | `InpTpR/InpP1*/InpP2*` | Implementato |
| Decisioni sulla barra M1 chiusa (E-25) | `mgmt_on_close` | `OnNewM1Bar` | Implementato |
| Stop minimo in ATR (E-12) | `apply_min_stop` | `InpMinStopAtrM15` | Implementato (TF dell'ATR inferito) |
| Filtro notizie 30/30 (E-13) | — (nessun calendario storico) | `NewsBlocked`, solo live | Parziale: non disponibile nel tester |
| Motore macro / 93 modelli calendario (E-02) | — | — | NON RIPRODUCIBILE |
| Filtro AI a punteggio + soglia viva (E-23, E-24) | `ml.py` | non incluso | Testato, **disabilitato** (non batte in modo robusto la baseline al netto dei costi) |
| Giornale dei perché (E-26) | `ml.explain_rejections`, status nel simulatore | `Logger.mqh`, `*_signals.csv` | Implementato |
| Rischio che respira (E-27) | `breathe_*` | `CRRAccountGuard.RiskMultiplier` | Implementato, non validato separatamente |
| Monitor fuori scala (E-29) | — | — | Non implementato |
| Monte Carlo a blocchi (E-30) | — | — | Non eseguito (nessuna strategia positiva) |
| Telegram (E-07) | — | `Telegram.mqh` | Scritto, **non testato** |
| Modalità prop / funded / flip (E-10) | — | — | Fuori perimetro |
| Livelli Premium A…A++ (E-11) | `entry_depth` (approssimazione) | — | NON VERIFICATO |
