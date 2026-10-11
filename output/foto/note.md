# Foto INTERSTELLAR · XAUUSD — trascrizione e note (ICT RAPTOR AI PRIME, Autotrader Forex Club)

Fonte: 16 screenshot iPhone (1125x2436) di YouTube Shorts del canale @autotraderforexclub, ore 13:43–13:45.
Ritagli ingranditi usati per la lettura: `output/foto/crops/`.

Elementi comuni a quasi tutti i frame (sovrimpressione del video, parzialmente coperta dall'interfaccia YouTube):
- Logo "AF / AUTOTRADER FOREX CLUB" in alto a sinistra; in alto a destra "INTERSTELLAR · XAUUSD" (oppure "INTERSTELLAR · XAU · NAS · EUR").
- In basso: "✓ Official product" e "NN / 06 · dati veri, te[ster] 2026" oppure "NN / 12 · dati veri, te[ster] 2026" (parzialmente coperto dall'icona dell'audio).
- Riga sotto, coperta dal campo commento: "[@autot]raderforexclub · i modelli sono allenati fino al 31/12/2025, il 2026 non l'hanno mai [visto]" (la parola finale è coperta; "visto" è INFERITO).
- Il testo dell'interfaccia YouTube (Mi piace, Salva, Condividi, "Cornfield Chase · Hans Zimmer", "798K" ecc.) non è contenuto del venditore e lo riporto solo dove serve.

Legenda: **OSSERVATO** = scritto o mostrato alla lettera nella foto; **INFERITO** = mia interpretazione.

---

## fc6fb6f3 — La cascata dei modelli (12/12)

Trascrizione:
- Intestazione: "INTERSTELLAR · XAU · NAS · EUR"
- Titolo: **LA CASCATA DEI MODELLI**
- Sottotitolo: "dal segnale della cella alla posizione sul conto: otto passi, tutti misura[ti]" (troncato a destra)
- 01 **5 CELLE ICT** — "PPK · OTEOF · PO3 · UNIOF · LS: i punti d'ingresso precisi"
- 02 **49.000 SEGNALI** — "oro ed EUR dal 2005, NAS dal 2018: ogni segnale con il suo esito vero"
- 03 **92 INGRESSI** — "struttura, volatilità, sessione, spread, stop, probabilità delle celle: solo rapporti, mai prezzi"
- 04 **VEDE-25 · G_CELLA · MODELLO8** — "gradient boosting, 1500 alberi, allenato fino al 31/12/2025 e congelato"
- 05 **SOGLIA VIVA** — "quantile 80% degli ultimi 1000 punteggi: prende il 20% migliore"
- 06 **GESTIONE IN BARRE M1** — "parziali, pareggio, target 4R, decisi sulla barra chiusa"
- 07 **RISCHIO CHE RESPIRA** — "di[nam]ico sul conto, calibrato a Monte Carlo per challenge, funded, live, flip" (parte coperta dall'avatar)
- 08 **COSTI E MONITOR** — "spread, swap e commissioni letti dal broker · ingressi fuori scala segnalati"
- Didascalia YouTube: "Unstoppable, check my link in bio trad…"; audio "Unstoppable · Sia"; 6,7 Mln
- In basso: "12 / 12 · dati veri, te[ster] 2026"

Cosa ci dice sul robot:
- OSSERVATO: la pipeline ha 8 passi: 5 celle ICT (PPK, OTEOF, PO3, UNIOF, LS), poi 92 feature, poi 3 modelli (VEDE-25, G_CELLA, MODELLO8), poi soglia viva, gestione M1, rischio dinamico, costi/monitor.
- OSSERVATO: modelli gradient boosting con 1500 alberi, addestrati fino al 31/12/2025 e poi congelati; dataset di 49.000 segnali (oro ed EUR dal 2005, NAS dal 2018).
- OSSERVATO: le feature sono "solo rapporti, mai prezzi" (struttura, volatilità, sessione, spread, stop, probabilità delle celle).
- INFERITO: "VEDE-25 · G_CELLA · MODELLO8" è probabilmente un ensemble o una catena di 3 modelli; G_CELLA sembra un modello per singola cella (fa pensare a "probabilità si/no della cella").
- INFERITO: il 2026 è presentato come out-of-sample, ma si tratta di "tester 2026" (backtest nel tester MT5), non di un conto live.

## 1802dd6f — Monitor fuori scala (08/12, versione con testo completo)

Trascrizione:
- Titolo: **MONITOR FUORI SCALA**
- Sottotitolo: "ogni ingresso confrontato con la storia su cui il modello ha imparato"
- Grafico: "segnale del 2026.01.29 17:15 · 92 ingressi grezzi · banda = 1-99% della storia 2005-25" (punti azzurri dentro la banda, alcuni rossi e uno giallo sotto la banda inferiore)
- **7** FUORI 1-99% · **6** MAI VISTI IN 20 ANNI
- "i peggiori: stop in ATR M15 = 0.4421 [1.964..27.87 MAI VISTO] · stop in ATR H1 = 0.2666 [0.9842..13.93 MAI VISTO] · stop[…] ATR = 0.4421 [2.245..59.09 MAI VISTO]" (il nome della terza feature è troncato: "stop…ATR")
- "Nel 2026 sull'oro: 1788 segnali · 52 seri (3%) · 21 con un ingresso mai vis[to]" (coperto da "Condividi")
- "Il rob[ot no]n cambia decisione: lo scrive (IS_SCALA) e lo dice nel giornale. Se il mondo esce dalla storia, […]" (troncato)
- "Un modello che tace davanti al mai visto, mente."
- Didascalia: "La trasparenza come non l'hai mai vist…"
- "08 / 12 · dati veri, te[ster] 2026"

Cosa ci dice sul robot:
- OSSERVATO: per ogni segnale c'è un controllo out-of-distribution che confronta le 92 feature con la banda dei percentili 1–99% dello storico 2005-25.
- OSSERVATO: il controllo non cambia la decisione del modello: scrive solo un flag (IS_SCALA) nel giornale.
- OSSERVATO: nel 2026 sull'oro ci sono stati 1788 segnali, 52 "seri" (3%) e 21 con un ingresso mai visto.
- OSSERVATO: tra le feature ci sono stop in ATR M15, stop in ATR H1 e un terzo "stop … ATR". Nel segnale del 29/01/2026 hanno valori (0.4421 e 0.2666) sotto il minimo storico.
- INFERITO: lo stop in quel segnale era molto stretto rispetto all'ATR, cioè fuori dal range di addestramento.

## cd3c5503 — Monitor fuori scala (08/12, stesso frame senza testo in basso)

Trascrizione: identica a 1802dd6f per titolo, sottotitolo, grafico ("segnale del 2026.01.29 17:15 · 92 ingressi grezzi · banda = 1-99% della storia 2005-25"), "7 FUORI 1-99%", "6 MAI VISTI IN 20 ANNI" e la riga "i peggiori: stop in ATR M15 = 0.4421 [1.964..27.87 MAI VISTO] · stop in ATR H1 = 0.2666 [0.9842..13.93 MAI VISTO] · stop[…] ATR = 0.4421 [2.245..59.09 MAI VISTO]". Le righe "Nel 2026 sull'oro…" e seguenti non sono ancora comparse (animazione). Didascalia "La trasparenza come non l'hai mai vist…". "08 / 12 · dati veri, te[ster] 2026".

Cosa ci dice sul robot:
- OSSERVATO: è lo stesso contenuto di 1802dd6f, in un frame precedente.
- OSSERVATO: 7 delle 92 feature sono fuori dalla banda 1–99% e 6 non sono mai state viste in 20 anni.

## 248edcdc — Il giornale dei perché (10/12)

Trascrizione:
- Titolo: **IL GIORNALE DEI PERCHÉ**
- Sottotitolo: "ogni segnale scartato lascia scritti i suoi motivi: niente scatole nere"
- Tabella (data ora · cella direzione · punteggio < soglia · 2 motivi):

| data/ora | cella | punteggio < soglia | motivi |
|---|---|---|---|
| 25/09 01:55 | PPK BUY | -0.38 < -0.02 | volatilità fuori norma · stop fuori misura |
| 25/09 06:30 | UNIOF SELL | -0.35 < -0.02 | rotture contro · stop fuori misura |
| 25/09 07:30 | PPK BUY | -0.35 < -0.02 | visione del grafico asse · notizia in arrivo |
| 25/09 11:35 | PPK BUY | -0.02 < -0.02 | stop fuori misura (H1) · spinta a 60 minuti |
| 25/09 13:15 | UNIOF BUY | -0.35 < -0.02 | la cella è al limite · stop fuori misura |
| 25/09 14:45 | PPK SELL | -0.42 < -0.02 | la cella è al limite · visione del grafico asse |
| 25/09 16:35 | PPK BUY | -0.27 < -0.02 | la cella è al limite · notizia in arrivo |
| 25/09 17:40 | PPK BUY | -0.57 < -0.02 | la cella non è convinta · visione del grafico asse |
| 28/09 00:30 | UNIOF SELL | -0.28 < -0.02 | distanza dalla media (se · posizione nel range del (troncato) |
| 28/09 00:35 | PPK SELL | -0.12 < -0.02 | volatilità fuori norma · posizione nel range 4h |
| 28/09 09:55 | PPK SELL | -0.43 < -0.02 | poche rotture a favore · stop fuori misura (M15) |
| 28/09 11:20 | PPK SELL | -0.77 < -0.02 | poche rotture a favore · volatilità fuori norma |
| 28/09 11:30 | PPK SELL | -0.10 < -0.02 | volatilità fuori norma · poche rotture a favore |
| 28/09 13:50 | PPK SELL | -0.78 < -0.02 | poche rotture a favore · spinta a 3 ore |

- Nota sotto la tabella: "settembre 2026 · gli ultimi scartati · punteggio < soglia · i 2 motivi principali"
- Grafico a barre: "i motivi più frequenti nei 1607 rifiuti del 2026":
  - visione de[l] gra[f]ico ass[e]: valore illeggibile (barra ≈ 830 sulla scala 0–1000; valore INFERITO dalla lunghezza)
  - spread troppo alto per la volatili[tà]: 417
  - volatilità fuori norma: 356
  - stop fuori misura: 309
  - [la cella non è c]onvinta: 276
  - stop fuori misura (H1): 166
  - motivo della cella debole: 161
- Asse: 0, 200, 400, 600, 800, 1000
- "Ogni motivo è un ingresso rimesso al suo valore mediano: la differenza di punteggio è il suo peso."
- Didascalia: "Trader check my link in bio 👈 #daytr…"; "10 / 12 · dati veri, te[ster] 2026"

Cosa ci dice sul robot:
- OSSERVATO: a fine settembre 2026 la soglia viva era -0.02. Nella tabella compaiono solo le celle PPK e UNIOF.
- OSSERVATO: i motivi di rifiuto sono calcolati rimettendo ogni feature al suo valore mediano e misurando di quanto cambia il punteggio (spiegazione per sostituzione, simile a SHAP/ablazione).
- OSSERVATO: nel 2026 ci sono stati 1607 rifiuti. Motivi principali: "visione del grafico asse", spread troppo alto per la volatilità (417), volatilità fuori norma (356), stop fuori misura (309), "la cella non è convinta" (276).
- OSSERVATO: tra le feature ci sono notizia in arrivo (filtro news), spinta a 60 minuti / 3 ore, posizione nel range 4h, rotture a favore/contro, distanza dalla media.
- INFERITO: il segnale delle 11:35 ha punteggio -0.02, uguale alla soglia, ed è scartato: la regola sembra "prende se punteggio > soglia" (stretto), oppure i valori sono arrotondati.

## 4ec6d52b — 92 ingressi, un punteggio (02/06)

Trascrizione:
- Titolo: **92 INGRESSI, UN PUNTEGGIO**
- Sottotitolo: "un segnale vero: PPK BUY dell'8 gennaio 2026, 12:20"
- Grafico: "i 92 ingressi del segnale, ognuno sulla scala della storia 2005-25" (barre gialle positive, barre azzurre negative)
- Riquadro: **VEDE-25** — "gra[d]ient boosting · 1500 alberi · 127 foglie · allenato su 49.000 segnali"
- **punteggio 0.6081**
- "soglia viva -0.0932 (quantile 80% degli ultimi punteggi)"
- **PRESO** · "esito reale: +2,97R" (la cifra "9" è parzialmente coperta dall'icona Condividi; confermato da 28c5753c "+2,97R")
- "perch[é]: 3 contro (rosso), 3 a favore (verde) · contributo al punteggio" (parzialmente coperto; "3 contro/3 a favore" letto su cda831aa)
- Barre dei contributi (asse -0.8, -0.4, 0.0, 0.4, 0.8):
  - rosso: "posizione nel range 24h (segno…" (≈ -0.16)
  - rosso: "[or]a del giorno" (≈ -0.15)
  - rosso: "ex3_60m" (≈ -0.14)
  - verde: "probabilità si/no della [cell]a" (≈ +0.80, la più grande)
  - verde: "margine sulla soglia di target" (≈ +0.18)
  - verde: "effi[cienza] 4h" (parzialmente coperto, ≈ +0.13)
- "02 / 06 · dati veri, te[ster] 2026"

Cosa ci dice sul robot:
- OSSERVATO: VEDE-25 è un gradient boosting con 1500 alberi e 127 foglie (tipico parametro num_leaves di LightGBM), addestrato su 49.000 segnali.
- OSSERVATO: il segnale PPK BUY dell'8/1/2026 alle 12:20 aveva punteggio 0.6081 contro una soglia viva di -0.0932. È stato preso, con esito reale +2,97R.
- OSSERVATO: la feature più pesante è "probabilità si/no della cella". Altre feature: posizione nel range 24h, ora del giorno, ex3_60m, margine sulla soglia di target, efficienza 4h.
- INFERITO: il punteggio è in scala log-odds o margine (può essere negativo; soglie intorno a -0.1/0), non una probabilità 0–1.
- INFERITO: "probabilità si/no della cella" è l'output di un modello di primo livello (G_CELLA) usato come feature di VEDE-25: un modello a cascata (stacking).

## cda831aa — 92 ingressi, un punteggio (02/06, frame quasi identico)

Trascrizione: identica a 4ec6d52b ("92 INGRESSI, UN PUNTEGGIO"; "un segnale vero: PPK BUY dell'8 gennaio 2026, 12:20"; "VEDE-25 · gradient boosting · 1500 alberi · 127 foglie · allenato su 49.000 segnali"; "punteggio 0.6081"; "soglia viva -0.0932 (quantile 80% degli ultimi punteggi)"; "PRESO"; "esito reale: +2,97R"). Riga parzialmente leggibile: "perch[é] 3 contro (rosso), 3 a favore (verde) · contributo al punteggio". Stesse 6 barre di contributo (posizione nel range 24h (segno…; [or]a del giorno; ex3_60m; probabilità si/no della cella; margine sulla soglia di target; effi[cienza] 4h). Overlay "Utilizza modello" al posto di "Usa questa traccia".

Cosa ci dice sul robot:
- OSSERVATO: la spiegazione mostra 3 feature contro e 3 a favore, cioè le prime 3+3 per contributo.
- OSSERVATO: conferma i parametri di VEDE-25 (1500 alberi, 127 foglie, 49.000 segnali).

## 28c5753c — Un trade, gestito in barre (06/06)

Trascrizione:
- Titolo: **UN TRADE, GESTITO IN BARRE**
- Sottotitolo: "PPK BUY dell'8 gennaio 2026: parziali, pareggio, target, in barre M1"
- Grafico: "XAUUSD M1 · 09/01 15:09 UTC · stop 21 $ = 1R"
- Linee: "+2R · 20% · fatto"; "+0,7R · 20% + pareggio · fatto"; "ingresso 4424.56"; "stop a pareggio"
- **+3.56R** PREZZO ADESSO, IN R · **60%** POSIZIONE ANCORA APERTA
- Checklist:
  - ✓ "20% chiuso a +0,7R e stop a pareggio: da qui il trade non può più perdere"
  - ✓ "[20%] chiuso a +2R" (percentuale coperta dall'avatar; 20% INFERITO dalla linea del grafico)
  - ○ "[60]% che resta va al target 4R" (cifra coperta; 60% INFERITO da "60% posizione ancora aperta")
- "esito: +2,97R in 29 ore. Nel 2026: 169 trade, PF 1,7, il 65% i[…]" (troncato)
- Didascalia: "Un trade gestito in barre 🤖 #forextr…"; "06 / 06 · dati veri, te[ster] 2026"

Cosa ci dice sul robot:
- OSSERVATO: gestione con chiusura del 20% a +0,7R e stop spostato a pareggio, poi un altro 20% a +2R, poi il resto (60%) con target a 4R. Le decisioni sono prese sulle barre M1 chiuse.
- OSSERVATO: in questo trade lo stop era di 21 $ di prezzo = 1R, con ingresso a 4424.56. Esito +2,97R in 29 ore.
- OSSERVATO: nel 2026 (tester) XAUUSD conta 169 trade con PF 1,7. La frase "il 65% i…" è troncata.
- INFERITO: +2,97R è coerente con 0,2·0,7 + 0,2·2 + 0,6·4 = 2,94R più qualche aggiustamento (o costi, o arrotondamenti). Il trade sembra aver raggiunto il target 4R sul 60% residuo.
- INFERITO: alle 09/01 15:09 il prezzo era a +3.56R, quindi circa 4424.56 + 3.56·21 ≈ 4499.3.

## 653ae130 — Ogni segnale viene giudicato: PPK SELL scartato (01/06)

Trascrizione:
- Titolo: **OGNI SEGNALE VIENE GIUDICATO** (in parte coperto dall'interfaccia Shorts "Iscrizioni / Live / Lens")
- Sottotitolo: "il modello vede 92 ingressi e decide: PRESO o SCARTATO, e dice perché"
- Grafico: "16/01/2026 01:50 UTC" · "PPK SELL · punteggio -0.23 · soglia -0.07" · **SCARTATO: posizione nel range 4h**
- Etichette nel grafico: "-1.00R" (due volte, su linee orizzontali gialle, vicino a ingressi verdi/rossi); molti punti rossi (scartati) e alcuni verdi (presi)
- **92** SEGNALI GIUDICATI · **11** PRESI · **81** SCARTATI
- "Sog[lia]: quantile 80% dei punteggi · ogni rifiuto ha i suoi 3 motivi contro scritti nel giornale"
- Riga magenta coperta: "Modelli allenati fino al 31/12/2025. Quest[o è] il 20[26 … ma]i[…]ima." (in gran parte illeggibile)
- "01 / 06 · dati veri, te[ster] 2026"

Cosa ci dice sul robot:
- OSSERVATO: a metà gennaio 2026 il contatore indica 92 segnali giudicati, 11 presi e 81 scartati (≈12%).
- OSSERVATO: il 16/01/2026 alle 01:50 un PPK SELL con punteggio -0.23 sotto la soglia -0.07 è stato scartato per "posizione nel range 4h".
- OSSERVATO: due trade presi visibili nel grafico sono marcati -1.00R (stop pieno).
- INFERITO: la soglia viva a gennaio (-0.07) è diversa da quella di settembre (-0.02), coerente con la "soglia che respira".

## 8ed5759d — Ogni segnale viene giudicato: PPK BUY preso (01/06)

Trascrizione:
- Titolo: **OGNI SEGNALE VIENE GIUDICATO**
- Sottotitolo: "il modello vede 92 ingressi e decide: PRESO o SCARTATO, e dice perché"
- Grafico: "12/01/2026 11:15 UTC" · "PPK BUY · punteggio -0.01 · soglia -0.07" · **PRESO**
- Etichette: "+2.98R" (verde, accanto a una linea gialla di ingresso con linea di stop rossa tratteggiata sotto); in basso un'etichetta verde tagliata "0.07R" (cifra iniziale illeggibile; probabilmente "+0.07R")
- **57** SEGNALI GIUDICATI · **5** PRESI · **52** SCARTATI
- "Sog[lia]: quantile 80% dei punteggi · ogni rifiuto ha i suoi 3 motivi contro scritti nel giornale"
- "01 / 06 · dati veri, te[ster] 2026"

Cosa ci dice sul robot:
- OSSERVATO: un PPK BUY del 12/01/2026 alle 11:15 con punteggio -0.01 sopra la soglia -0.07 è stato preso.
- OSSERVATO: al 12/01 il contatore indica 57 giudicati, 5 presi e 52 scartati.
- INFERITO: l'etichetta +2.98R si riferisce al trade precedente (ingresso a sinistra) o a questo; l'attribuzione è incerta. Vicino al marker del 12/01 compare "…0.07R", forse l'esito del trade corrente.
- INFERITO: con il marker verde sul massimo a +2.98R, un PPK BUY precedente sembra arrivato al target.

## a73dd514 — Ogni segnale viene giudicato: PPK BUY scartato (01/06)

Trascrizione:
- Titolo: **OGNI SEGNALE VIENE GIUDICATO**
- Sottotitolo: "il modello vede 92 ingressi e decide: PRESO o SCARTATO, e dice perché"
- Grafico: "07/01/2026 00:50 UTC" · "PPK BUY · punteggio -0.34 · soglia 0.24" · **SCARTATO: probabilita' si/no della cella**
- Etichetta: "+0.18R" (verde, su un ingresso verde preso)
- **27** SEGNALI GIUDICATI · **2** PRESI · **25** SCARTATI
- "Sog[lia]: quantile 80% dei punteggi · ogni rifiuto ha i suoi 3 motivi contro scritti nel giornale"
- "01 / 06 · dati veri, te[ster] 2026"

Cosa ci dice sul robot:
- OSSERVATO: a inizio gennaio la soglia era 0.24, molto più alta. Un PPK BUY del 07/01 alle 00:50 con punteggio -0.34 è stato scartato per "probabilità si/no della cella".
- OSSERVATO: al 07/01 il contatore indica 27 giudicati, 2 presi e 25 scartati. Un trade preso è chiuso a +0.18R.
- INFERITO: all'avvio la soglia parte dal valore fisso (0,2426 ≈ 0.24, vedi 33a02717) finché il buffer non ha abbastanza punteggi. Questo spiega 0.24 a gennaio contro -0.07 pochi giorni dopo.
- INFERITO: un esito di +0.18R è coerente con il parziale del 20% a +0,7R seguito dallo stop a pareggio (0,2·0,7 = 0,14R) più un piccolo extra, o con un'uscita intermedia.

## 33a02717 — La soglia che respira, 23/09/2026 (03/06)

Trascrizione:
- Titolo: **LA SOGLIA CHE RESPIRA**
- Sottotitolo: "il robot ricorda gli ultimi 1000 punteggi: prende solo il 20% migliore"
- Grafico 1: "punteggio di ogni segnale giudicato · 23/09/2026"; linea tratteggiata "soglia fissa r39 0,2426"; linea magenta (soglia viva) sotto; asse X 0–1600 "segnali giudicati nel 2026, da gennaio a settembre"
- Grafico 2: "gli ultimi 1000 punteggi ricordati · il 20% verde passa"; **soglia viva -0.018**; asse -1.0, -0.5, 0.0, 0.5, 1.0
- "**1751 giudicati · 175 presi (10%)**" (in parte coperto dalla didascalia; la percentuale "10%" è parzialmente coperta)
- "Se il mercato cambia e i punteggi scendono, la soglia scende con loro: il robot non resta fermo me[…]"
- Didascalia: "La soglia che respira nell'ecosistema. …"
- "03 / 06 · dati veri, te[ster] 2026"

Cosa ci dice sul robot:
- OSSERVATO: la soglia viva è il quantile 80% degli ultimi 1000 punteggi (passa il 20% migliore). La soglia fissa di riferimento "r39" è 0,2426.
- OSSERVATO: al 23/09/2026 la soglia viva era -0.018, con 1751 segnali giudicati e 175 presi (10%).
- INFERITO: la soglia viva si stabilizza subito intorno a -0.02/-0.1, molto sotto la soglia fissa 0,2426. Il robot accetta segnali con punteggio negativo, cioè la soglia adattiva è molto più permissiva di quella originale.
- INFERITO: presi il 10% e non il 20% perché i presi vengono filtrati anche dopo il punteggio (posizioni aperte, rischio, sessione…) oppure perché il quantile si riferisce a una popolazione diversa.

## b8f90168 — La soglia che respira, 21/09/2026 (03/06)

Trascrizione:
- Stesso layout di 33a02717. Grafico 1: "punteggio di ogni segnale giudicato · 21/09/2026"; "soglia fissa r39 0,2426".
- Grafico 2: "gli ultimi 1000 punteggi ricordati · il 20% verde passa"; **soglia viva -0.024**
- "**1733 giudicati · 169 presi (10%)**" (parzialmente coperto)
- "Se il mercato cambia e i punteggi scendono, la soglia scende con loro: il robot non resta fermo me[…]"
- "03 / 06 · dati veri, te[ster] 2026"

Cosa ci dice sul robot:
- OSSERVATO: al 21/09/2026: 1733 giudicati, 169 presi (10%), soglia viva -0.024.
- INFERITO: tra il 21/09 e il 23/09: +18 giudicati, +6 presi, soglia salita da -0.024 a -0.018. I 169 presi corrispondono ai "169 trade" XAUUSD 2026 di 28c5753c/ef39d12e.

## ef39d12e — Il rischio che respira (05/06)

Trascrizione:
- Titolo: **IL RISCHIO CHE RESPIRA**
- Sottotitolo: "scende da solo quando il conto perde, torna pieno da solo"
- Grafico equity: "XAUUSD 2026 · 169 trade chiusi · 24/09/2026"; "rosso = discesa dal massimo: ade[sso] 1,9%" (parzialmente coperto; "1,9%" leggibile come "…9%", prima cifra coperta)
- Grafico del moltiplicatore (verde, con 2 cali evidenti e 2 piccoli)
- "moltiplicatore del rischio: pieno fino a −5%, poi scende fino a ×0,25 a −23,75%; RIPRESA: 20 trade in utile [→] pieno" (simbolo prima di "pieno" coperto)
- **1,92%** RISCHIO SUL PROSSIMO TRADE (base 1,92%) · **+99%** CONTO DAL 1° GENNAIO
- "Mai un aumento: il rischio della tabella è il massimo. Nelle serie nere il robot si fa piccolo da solo."
- Didascalia: "Il rischio che respira nell'ecosistema e…"; "05 / 06 · dati veri, te[ster] 2026"

Cosa ci dice sul robot:
- OSSERVATO: rischio base 1,92% per trade su XAUUSD. Il moltiplicatore è pieno fino a un drawdown del -5%, poi scende fino a ×0,25 a un drawdown del -23,75%. Dopo 20 trade in utile torna pieno.
- OSSERVATO: non c'è mai un aumento del rischio oltre la base (niente martingala o anti-martingala al rialzo).
- OSSERVATO: XAUUSD 2026 (tester): 169 trade chiusi al 24/09/2026, conto +99% dal 1° gennaio, drawdown attuale circa 1,9% (prima cifra parzialmente coperta).
- INFERITO: il moltiplicatore è sceso solo 2 volte in modo significativo, quindi il drawdown ha superato il -5% almeno due volte nel 2026.
- INFERITO: la riduzione tra -5% e -23,75% sembra lineare (da ×1 a ×0,25).

## b3a20526 — Monte Carlo a blocchi (11/12)

Trascrizione:
- Titolo: **MONTE CARLO A BLOCCHI**
- Sottotitolo: "3000 futuri possibili costruiti dai trade veri del 2026"
- Grafico: "conto da 100 · rischio 1,92% · 172 trade dell'oro 2026 ricampionati a blocchi di 10"; "giallo = la sequenza vera · verde = mediana e fasce 25-75% e 5-95%"
- Istogramma: "finale a fine percorso (%): 5% 31 · mediana 107 · 95% 241"; asse -50, 0, 50, 100, 150, 200, 250; "risultato in % · su 3000 p[ercorsi]"
- **2[?]%** DISCESA MASSIMA AL 95° PERCENTILE (seconda cifra coperta dall'avatar: illeggibile; si vede "2…%")
- **99%** PERCORSI IN UTILE
- "Il rischio per obiettivo (challenge, funded, live, flip) è scelto così: il più alto che regge le fasce peggiori."
- Didascalia: "Check my link in bio trader 👈 #daytr…"; audio "S.T.A.Y. · Hans Zimmer"; 40K
- "11 / 12 · dati veri, te[ster] 2026"

Cosa ci dice sul robot:
- OSSERVATO: Monte Carlo con bootstrap a blocchi di 10 trade, 3000 percorsi, sui 172 trade dell'oro 2026, rischio 1,92%, conto 100.
- OSSERVATO: risultato finale: 5° percentile +31%, mediana +107%, 95° percentile +241%. Il 99% dei percorsi chiude in utile. Drawdown massimo al 95° percentile "2?%" (cifra coperta).
- OSSERVATO: il rischio per tipo di conto (challenge, funded, live, flip) è calibrato come "il più alto che regge le fasce peggiori".
- INFERITO: qui i trade sono 172 contro i 169 di ef39d12e: i video sono di date diverse (dataset aggiornato).
- INFERITO: il Monte Carlo ricampiona solo trade del 2026 (in-sample rispetto alla scelta della soglia e del rischio), quindi non misura il rischio di modello o di regime.

## c42a42fc — Costi universali (07/12)

Trascrizione:
- Intestazione: "INTERSTELLAR · XAU · NAS · EUR"
- Titolo: **COSTI UNIVERSALI**
- Sottotitolo: "spread, commissione e swap letti dal broker: il costo di ogni trade in R" (troncato)
- Legenda: spread · commissione · swap x notti
- "costo atteso medio dei trade aperti nel 2026 (tester r46, demo: swap veri del simbolo, zero commissioni)"
- Barre: ORO **0.019 R** · NAS **0.019 R** · EUR **0.074 R**
- "swap letti dal simbolo ($ per lotto e notte, long / short):"
- "ORO -79,48 / +34,41" · "NAS -6,08 / +1,12" · "EUR -6,41 / +1,83"
- Formula: "**costo / trade = spread/stop + A·bp + B·f**"
- "bp = commissione in punti base · f = finanziamento annuo (lo swap) · vale per qualunque br[oker]"
- Grafico: "PF 2026 al crescere dello swap: l'oro non lo sente, l'EUR sì" (linee ORO gialla quasi piatta, NAS rossa quasi piatta, EUR verde in discesa; asse X 0–10)
- "Il lotto si calcola su stop + costi attesi: la perdita allo stop, costi compresi, è il rischio voluto."
- Didascalia: "Check my link in bio trader 🤖 #forext…"; "S.T.A.Y. · Hans Zimmer"; 40K
- "07 / 12 · dati veri, te[ster] 2026"

Cosa ci dice sul robot:
- OSSERVATO: il tester è "r46", su demo, con swap reali del simbolo e zero commissioni.
- OSSERVATO: costo medio per trade: 0.019R su oro e NAS, 0.074R su EUR. Swap oro -79,48 $ long / +34,41 $ short per lotto e notte.
- OSSERVATO: il lotto è dimensionato su stop + costi attesi, così la perdita allo stop (costi inclusi) è uguale al rischio voluto.
- OSSERVATO: modello dei costi: costo/trade = spread/stop + A·bp + B·f.
- INFERITO: nel backtest le commissioni sono a zero, quindi su un broker ECN reale i costi saranno più alti. Sull'oro lo swap long è pesante (-79,48 $/lotto/notte) per trade che durano molte ore (es. 29 ore).

## 779c21a8 — Tre mercati, un conto (09/12)

Trascrizione:
- Intestazione: "INTERSTELLAR · XAU · NAS · EUR"
- Titolo: **TRE MERCATI, UN CONTO**
- Sottotitolo: "oro, NAS ed EUR insieme: tre robot scorrelati sullo stesso saldo"
- Legenda: ORO · NAS · EUR · conto unico (somma); asse gen, mar, mag, lug, set; data finale "24/09/2026"
- **+126%** CONTO UNICO, SENZA COMPOSIZIONE FRA I TRE · **+99%** ORO · **+11%** NAS · **+1?%** EUR (seconda cifra coperta dall'icona Salva: illeggibile; "+16%" plausibile ma non certo)
- "correlazione dei guadagni giornalieri: oro-NAS 0.03 · oro-EUR -0.00 · NAS-EUR -0.0[…]" (ultima cifra coperta)
- "Quasi zero: quando uno perde, gli altri non lo sanno. Misurato: da 1 a 3 mercati la disce[sa …]" (troncato)
- "1 p[osizion]e per mercato · budget di rischio condiviso · rischio dinamico sul saldo di tutti e […]" (parzialmente coperto)
- "09 / 12 · dati veri, te[ster] 2026"

Cosa ci dice sul robot:
- OSSERVATO: 3 robot (oro, NAS, EUR) sullo stesso conto. Il conto unico fa +126% senza composizione: oro +99%, NAS +11%, EUR +1?%.
- OSSERVATO: correlazioni giornaliere vicine a 0. Massimo 1 posizione per mercato, budget di rischio condiviso, rischio dinamico calcolato sul saldo complessivo.
- INFERITO: +99 + 11 + 1x ≈ 126, quindi EUR ≈ +16% (somma aritmetica senza composizione). Quasi tutto il risultato viene dall'oro.

---

# Sintesi

## Celle e regole d'ingresso
- OSSERVATO: 5 celle ICT: **PPK, OTEOF, PO3, UNIOF, LS** ("i punti d'ingresso precisi") (fc6fb6f3). Nei frame XAUUSD compaiono solo **PPK** (BUY/SELL) e **UNIOF** (BUY/SELL) (248edcdc, 4ec6d52b, 653ae130, 8ed5759d, a73dd514).
- OSSERVATO: ogni segnale di cella viene descritto da **92 ingressi**: "struttura, volatilità, sessione, spread, stop, probabilità delle celle: solo rapporti, mai prezzi".
- OSSERVATO: decisione binaria PRESO/SCARTATO: preso se il punteggio supera la soglia viva. Ogni rifiuto riporta i 3 motivi contro più forti nel "giornale".
- OSSERVATO: motivi o feature nominati: visione del grafico asse; spread troppo alto per la volatilità; volatilità fuori norma; stop fuori misura (M15, H1); la cella è al limite / non è convinta; motivo della cella debole; notizia in arrivo; spinta a 60 minuti / a 3 ore; posizione nel range 4h / 24h (segno…); ora del giorno; ex3_60m; probabilità si/no della cella; margine sulla soglia di target; efficienza 4h; rotture contro / poche rotture a favore; distanza dalla media; stop in ATR M15 / H1.
- OSSERVATO: monitor fuori scala (IS_SCALA): confronto di ogni feature con la banda dei percentili 1–99% dello storico 2005-25. **Non cambia la decisione**, la registra soltanto.
- OSSERVATO: massimo 1 posizione per mercato (779c21a8).

## Gestione (parziali, BE, trailing, target)
- OSSERVATO: gestione **in barre M1, decisa sulla barra chiusa** (fc6fb6f3, 28c5753c).
- OSSERVATO: **20% chiuso a +0,7R + stop a pareggio**; **20% chiuso a +2R**; **60% residuo al target 4R** (le percentuali 20% e 60% della 2ª e 3ª riga sono in parte coperte, ma coerenti con "60% posizione ancora aperta").
- OSSERVATO: nessun trailing menzionato: dopo +0,7R lo stop resta a pareggio fino al target 4R.
- OSSERVATO: esempio con stop 21 $ = 1R su XAUUSD.

## Catena AI (modelli, soglie, feature, soglia viva)
- OSSERVATO: modelli **VEDE-25 · G_CELLA · MODELLO8**: gradient boosting, **1500 alberi**, **127 foglie** (VEDE-25), addestrati su **49.000 segnali** (oro ed EUR dal 2005, NAS dal 2018), **allenati fino al 31/12/2025 e congelati**.
- OSSERVATO: **soglia viva = quantile 80% degli ultimi 1000 punteggi** (passa il 20% migliore). **Soglia fissa r39 = 0,2426**.
- OSSERVATO: valori della soglia viva: 0.24 il 07/01/2026; -0.07 il 12/01 e il 16/01; -0.0932 (contesto dell'8/1 alle 12:20); -0.02 a fine settembre (giornale); -0.024 il 21/09; -0.018 il 23/09.
- OSSERVATO: punteggi d'esempio: 0.6081 (preso), -0.01 (preso, soglia -0.07), -0.23 (scartato), -0.34 (scartato, soglia 0.24), da -0.02 a -0.78 (scartati a settembre).
- OSSERVATO: spiegazioni ottenute rimettendo ogni feature al suo valore mediano (differenza di punteggio = peso).
- INFERITO: G_CELLA produce la "probabilità si/no della cella" usata come feature di VEDE-25 (stacking). Il punteggio è in scala margine/log-odds.
- INFERITO: la soglia viva (circa -0.02/-0.1) è molto più bassa della soglia fissa 0,2426.

## Rischio (rischio base, rischio che respira, Monte Carlo)
- OSSERVATO: **rischio base 1,92%** per trade (XAUUSD).
- OSSERVATO: **moltiplicatore: pieno fino a DD -5%, poi scende fino a ×0,25 a DD -23,75%; ripresa: 20 trade in utile → pieno**. "Mai un aumento: il rischio della tabella è il massimo."
- OSSERVATO: lotto calcolato su **stop + costi attesi**.
- OSSERVATO: multi-mercato: budget di rischio condiviso, rischio dinamico sul saldo di tutti i mercati.
- OSSERVATO: **Monte Carlo a blocchi**: 3000 percorsi, blocchi di 10, 172 trade dell'oro 2026, conto 100, rischio 1,92%. Finale: 5° percentile +31%, mediana +107%, 95° percentile +241%. **99% dei percorsi in utile**. DD massimo al 95° percentile "2?%" (seconda cifra illeggibile).
- OSSERVATO: rischio per obiettivo (challenge, funded, live, flip) = il più alto che regge le fasce peggiori del Monte Carlo.

## Costi
- OSSERVATO: tester r46 su demo, swap veri del simbolo, **zero commissioni**.
- OSSERVATO: costo medio per trade: **ORO 0.019R, NAS 0.019R, EUR 0.074R**.
- OSSERVATO: swap ($ per lotto e notte, long/short): **ORO -79,48 / +34,41; NAS -6,08 / +1,12; EUR -6,41 / +1,83**.
- OSSERVATO: formula: costo/trade = spread/stop + A·bp + B·f (bp = commissione in punti base; f = finanziamento annuo).
- OSSERVATO: il PF 2026 dell'oro è insensibile allo swap, quello dell'EUR cala.
- OSSERVATO: tra i rifiuti, "spread troppo alto per la volatilità" ricorre 417 volte.

## Numeri dichiarati (periodo e condizioni)
Tutti i numeri sono marcati "dati veri, tester 2026" e "modelli allenati fino al 31/12/2025" (backtest out-of-sample nel tester, **non un conto live**).
- XAUUSD 2026: **169 trade, PF 1,7, "il 65% i[…]"** (troncato) e +2,97R nell'esempio (28c5753c). **169 trade chiusi al 24/09/2026, conto +99% dal 1° gennaio**, rischio base 1,92%, DD attuale circa 1,9% (ef39d12e).
- Monte Carlo: 172 trade dell'oro 2026 (data non indicata).
- Soglia: 1733 giudicati / 169 presi (10%) al 21/09/2026; 1751 / 175 presi (10%) al 23/09/2026.
- Monitor: "Nel 2026 sull'oro: 1788 segnali · 52 seri (3%) · 21 con un ingresso mai visto".
- Rifiuti 2026: 1607.
- Contatori di inizio gennaio: 27/2/25 (07/01), 57/5/52 (12/01), 92/11/81 (16/01).
- Tre mercati al 24/09/2026: conto unico **+126%** senza composizione; oro +99%, NAS +11%, EUR +1?% (cifra coperta). Correlazioni giornaliere: oro-NAS 0.03, oro-EUR -0.00, NAS-EUR -0.0?.

## Menu/input visibili
- Nessun pannello di input MT5 è visibile. Nomi tecnici che compaiono: **r39** (soglia fissa 0,2426), **r46** (versione del tester), **IS_SCALA** (flag fuori scala), **VEDE-25, G_CELLA, MODELLO8**, **ex3_60m** (nome di feature).
- Parametri impliciti: quantile 80%, finestra 1000 punteggi, rischio 1,92%, DD -5% / -23,75% / ×0,25, ripresa 20 trade, parziali 20% a 0,7R e 20% a 2R, target 4R, banda OOD 1–99%.

## Operazioni leggibili
- PPK BUY XAUUSD, 08/01/2026 12:20: ingresso 4424.56, stop 21 $ (=1R), punteggio 0.6081, soglia -0.0932. 20% a +0,7R + BE, 20% a +2R, 60% al target 4R. Esito **+2,97R in 29 ore** (28c5753c, 4ec6d52b, cda831aa).
- PPK BUY XAUUSD, 12/01/2026 11:15: punteggio -0.01, soglia -0.07, PRESO. Etichette "+2.98R" e "…0.07R" sul grafico, attribuzione incerta (8ed5759d).
- Trade preso a inizio gennaio 2026 (data/ora illeggibile) chiuso a +0.18R (a73dd514).
- Due trade presi intorno a metà gennaio 2026 chiusi a -1.00R (data/ora illeggibili) (653ae130).
- Segnali scartati (non sono trade): 07/01 00:50 PPK BUY; 16/01 01:50 PPK SELL; 14 scartati del 25–28/09 nella tabella del giornale (248edcdc). Non sono inclusi in trades.csv.
