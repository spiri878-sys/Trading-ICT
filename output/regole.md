# Regole operative della PRIME (ricostruzione) — Fase 1

**Fonti e sigle:**
- **SITO**: pagina principale salvata, testo in `output/sito/testo.txt`, dati in `output/sito/dati.json`.
- **V5**: manuale PRO V5 (`output/documenti/note.md`, sezione A).
- **PRES**: presentazione della prima versione (sezione B).
- **VID**: video (`output/video/*/note.md`).
- **FOTO**: foto (`output/foto/note.md`).
- **E-xx**: registro delle evidenze (`docs/evidence_register.md`).

**Priorità:** SITO (PRIME) > V5 > PRES. **AMBIGUO** = il materiale non chiarisce, segue l'interpretazione proposta. **INFERITO** = nostra definizione operativa.

**Convenzioni comuni:**
- Ora server = New York + 7 h (`report_fase0.md`). Killzone in ora di New York convertite: Asia NY 20:00–00:00 = server 03:00–07:00; Londra NY 02:00–05:00 = server 09:00–12:00; New York NY 07:00–10:00 = server 14:00–17:00.
- **Nessun lookahead:** ogni elemento è "noto" solo alla chiusura della barra che lo conferma (tabella §1). Le barre HTF si uniscono sull'orario di **disponibilità** (apertura + durata).
- Prezzi BID; ASK = BID + spread dello scenario di costo.

---

## 1. Elementi di base (definizioni operative)

| Elemento | Definizione (INFERITA, causale) | Noto a | Parametri da calibrare in validazione |
|---|---|---|---|
| Swing high/low | Frattale con k barre per lato | Chiusura della barra pivot + k | k ∈ {2, 3, 5} per TF |
| BOS | Chiusura oltre l'ultimo swing confermato non ancora rotto, nella direzione del trend in corso | Chiusura della barra di rottura | — |
| MSS / CHoCH | BOS opposto alla direzione dell'ultima rottura | idem | — |
| Gamba | Dall'estremo opposto (minimo per un BOS rialzista) alla barra di rottura | idem | — |
| Displacement | Corpo ≥ d × ATR(14) del TF, oppure 3 barre consecutive nella stessa direzione con somma dei corpi ≥ d × ATR; spesso lascia un FVG | Chiusura | d ∈ {1,0; 1,5; 2,0} |
| FVG | Rialzista: low(i) > high(i−2); ribassista: high(i) < low(i−2); ampiezza ≥ f × ATR | Chiusura di i | f ∈ {0,1; 0,25} |
| FVG mitigato | Il prezzo ha toccato il bordo prossimale (parziale) o il 50% (CE) | Al tocco | Definizione da scegliere |
| Order block | Ultima candela opposta prima del displacement che rompe la struttura | Alla rottura | — |
| Breaker block | Order block **fallito**: la struttura che proteggeva viene rotta nel senso opposto e la zona cambia segno (SITO cella 6: "quando un ordine istituzionale fallisce, quella zona cambia segno") | Alla rottura che lo invalida | — |
| Liquidità | Massimi e minimi uguali o swing evidenti; PDH/PDL; PWH/PWL; range asiatico; massimo e minimo della sessione precedente | Dalla loro formazione | Set delle fonti di liquidità |
| Sweep | Il prezzo supera il livello di liquidità di almeno ε e la **chiusura** torna dentro (V5: "sfonda … e rientra con forza") | Chiusura della barra che rientra | ε, rientro entro n barre, forza del rientro (corpo ≥ x ATR) |
| OTE | Zona 62–79% di ritracciamento della gamba dopo lo sweep e il cambio di struttura (V5, SITO); livello tipico 70,5% | Alla conferma della gamba | Punto d'ingresso nella zona |
| Premium/discount | Sopra o sotto il 50% del range di riferimento | — | Range di riferimento (giorno, gamba) |
| PO3 | Accumulazione = range compresso; manipolazione = falsa rottura contro; distribuzione = movimento vero | Fasi confermate in chiusura | Durata e ampiezza del range |

## 2. Le sei celle della PRIME (SITO §03) e i timeframe (V5)

Regole comuni:
- ogni cella marca i propri ordini (commento e magic);
- ogni set decide quali celle sono attive e con quali soglie AI (SITO);
- il TF del grafico è indifferente (V5);
- combinazioni non certificate rifiutate all'avvio (V5).

| # | Cella (SITO) | Nome tecnico (FOTO E-20) | TF interno XAU | Regola d'ingresso (fonte → interpretazione operativa) | Stop | Stato |
|---|---|---|---|---|---|---|
| 1 | 🦖 **Raptor Mode** "Prop Pass Killer" | PPK | **M5** (V5) | SITO: "riconosce la struttura, attende lo spostamento deciso ed entra solo sul ritraccio confermato". V5: "displacement + ritorni sulle zone di squilibrio … più operazioni in sequenza". SITO (immagine NAS M1): "tre ingressi in sequenza sullo stesso movimento". → BOS con displacement che lascia un FVG; ordine limit sul bordo prossimale dell'FVG (o CE); **ri-armo** su ogni nuovo FVG di continuazione nella stessa gamba | Oltre l'estremo della gamba / FVG ± buffer, oppure ATR × moltiplicatore (menu V5) | AMBIGUO: "ritraccio confermato" = tocco con chiusura di rifiuto (proposta) oppure semplice tocco del limit |
| 2 | 🦅 **Order Flow OTE** | OTEOF | **M12** (V5) | V5: "dopo lo sweep e il cambio di struttura … ritracciamento 62–79% … conferme di order flow". SITO: "non insegue". → sweep di liquidità, poi MSS, poi limit nella zona OTE 62–79% della gamba (proposta 70,5%) | Oltre l'estremo dello sweep | AMBIGUO: "conferme di order flow" = FVG presente nella gamba (proposta) |
| 3 | 🔋 **PO3** | PO3 | **M5** (V5) | V5: accumulazione (range), manipolazione (falsa rottura contro), ingresso all'inizio della distribuzione. SITO: "dalla parte di chi ha piazzato la trappola". → range asiatico (server 03–07) o range compresso pre-sessione; falsa rottura (sweep) nella finestra di Londra o New York; ingresso sul rientro con MSS e FVG nella direzione opposta alla falsa rottura | Oltre l'estremo della manipolazione | AMBIGUO: range di accumulazione (Asia oppure n barre compresse): da scegliere in validazione |
| 4 | 🦄 **Unicorn** | UNIOF | **M15** (V5) | SITO: "breaker e imbalance non mitigato si sovrappongono". V5: "armata solo dopo sweep di liquidità e rottura di struttura". → sweep, MSS, breaker generato dalla rottura, FVG non mitigato che si sovrappone al breaker: limit nella sovrapposizione | Oltre lo sweep / il breaker | INFERITO (definizione standard ICT) |
| 5 | 🌊 **Liquidity Sweep** | LS | **M3** (V5) | V5: "sfonda un massimo/minimo di riferimento per catturare gli stop e rientra con forza → direzione del rientro". SITO: "spazza la liquidità sotto un minimo, gira e riparte" ed è dove lavora di più il supervisore AI. SITO (immagine NAS M1): "venduto sul rientro, stop appena sopra lo sweep, uscita sul minimo successivo". → livello di liquidità (PDH/PDL, Asia, swing HTF); sweep con chiusura di rientro forte; ingresso sul rientro (a mercato alla chiusura, oppure limit al livello spazzato) | **Appena oltre l'estremo dello sweep** (SITO) | AMBIGUO: livelli di riferimento e tipo d'ordine |
| 6 | 🔨 **Breaker Block** | BB (nome nostro) | **NON DOCUMENTATO** (assente nel V5). Immagine del SITO: NAS100 **H4**. Proposta: M15 per XAU, scelto in validazione fra M5, M15 e H1 | SITO: "quando un ordine istituzionale fallisce, quella zona cambia segno. La cella la marca e aspetta il ritorno". → order block invalidato dalla rottura opposta; limit sul ritorno al breaker | Oltre il breaker | AMBIGUO (TF e regole) |

**Celle della prima versione** (PRES), solo per il Piano B (Fase 10):
- **Silver Bullet:** FVG nelle finestre NY 03–04, 10–11, 14–15.
- **MSS:** BOS opposto più FVG.
- **Judas Swing:** falsa mossa d'apertura contro il bias.
- **Order Block model:** ritorno sull'OB.

**Ordini e validità** (INFERITO):
- limit validi per N barre del TF di cella (da calibrare), cancellati se il prezzo raggiunge prima il TP1 teorico o invalida la struttura;
- **operazioni singole**, nessuna mediazione;
- la PRIME permette ingressi "in sequenza" della stessa cella (Raptor Mode) e più celle sullo stesso conto con magic diversi.

## 3. Catena AI

Due descrizioni dello stesso sistema in due generazioni. Si implementano **entrambe le architetture** (specifica, Fase 5) e la scelta si fa in validazione.

| Livello | SITO (PRIME, 168 modelli) | V5 (37 reti) | Ricostruzione proposta |
|---|---|---|---|
| Regimi | — | "REGIMI: filtro contesto" | Classificatore di contesto (trend, laterale, volatilità) da HTF; blocca contesti non ammessi per la cella |
| 1 | **Occhio**: 8 reti votano, decide la maggioranza, soglie 0,60–0,70 | — | Ensemble di 8 modelli (semi o algoritmi diversi); voto a maggioranza con soglia per cella in [0,60; 0,70] |
| 2 | **Selettori**: "scartano i segnali che sembrano buoni", soglie 0,78–0,92 | **Selettore** (15 reti, una per cella): probabilità di **big-runner**, oltre 100 feature | Un modello per cella che stima P(big-runner); soglia per cella in [0,78; 0,92] o quantile equivalente |
| 2b | — | **Gate Sì/No** (16 reti): qualità del punto d'ingresso; doppio consenso | Un modello per cella che stima P(ingresso pulito, cioè MAE prima di +1R ≤ x) |
| 3 | **Supervisore LiqBias**: "può dire no quando tutti dicono sì", soglie 0,70–0,72 | **Supervisore di liquidità** (una rete per mercato): sweep su **M5**, bias di fondo | Modello per XAU su M5 che stima il bias rialzista o ribassista dagli sweep recenti; blocca il segnale contrario con fiducia ≥ soglia [0,70; 0,72]. VID (E-13): "SUPERVISORE LIQBIAS (false = come certificato)", soglia 1..99 (−1 = quella della cella) |
| — | — | **Forecaster** (una rete per mercato): direzione della barra successiva più fiducia; blocca, aumenta il rischio o si astiene | Classificatore della direzione della barra successiva del TF di cella; tre esiti (contro forte → blocca; a favore forte → moltiplicatore di rischio > 1; incerto → nessun effetto) |
| 4 | **Semaforo e percorso**: 2 modelli, "decide quanto capitale merita il trade" | — | Due modelli di regressione o classificazione (qualità attesa in R; probabilità di percorso favorevole) che mappano su un moltiplicatore di rischio, per esempio {0,5; 1; 1,5} |
| 5 | **Reparto macro**: 93 reti sul calendario | Macro (scudo e notizie) | Fase 6 (serve il calendario) |

**Big-runner:** soglia da motivare in Fase 3. Proposta: MFE ≥ 3R prima dello stop.

**Feature** (V5): "oltre cento caratteristiche: volatilità, struttura, volumi, sessione, contesto multi-timeframe". FOTO (E-22): "92 ingressi … solo rapporti, mai prezzi" (Fase 4).

**Soglia viva** (FOTO E-24): "il robot ricorda gli ultimi 1000 punteggi: prende solo il 20% migliore". È un'alternativa alle soglie fisse, da confrontare in validazione.

## 4. Gestione del trade

| Elemento | Fonti | Conflitto | Proposta |
|---|---|---|---|
| Rischio 1R | V5 | — | Stop = strutturale oppure ATR(lunghezza) × moltiplicatore (menu V5), stop minimo in ATR (VID E-12) |
| Parziale | V5: "**Parziale 90% incassata a +1R**". FOTO E-25 (Interstellar): 20% a +0,7R, 20% a +2R, resto a 4R. SITO: chiusure parziali scaglionate (XAU M1 OTE) | V5 contro FOTO | Due profili da confrontare in validazione: **V5** (90% a +1R, resto a pareggio più trailing) e **FOTO** (scala 0,7/2/4R). Priorità alla fonte più vicina alla PRIME: il SITO dice solo "chiusure parziali, resto lasciato correre", quindi è **AMBIGUO** |
| Pareggio | V5, SITO (NAS H4: "raggiunto il primo obiettivo, stop al prezzo d'ingresso"); VID E-11 "BE + PARZIALE LIBERA IL POSTO" | — | Stop all'ingresso (più i costi) dopo il primo obiettivo |
| Trailing strutturale | V5: segue minimi e massimi di struttura e blocca +1R, +2R… ("+2R bloccato") | — | Dopo +2R lo stop si sposta sull'ultimo swing confermato del TF di cella, mai sotto +1R, poi +2R… |
| Uscita adattiva | V5: "se il trend perde potenza … chiude" | — | INFERITO: chiusura se è confermato un MSS contrario sul TF di cella, oppure se il momentum (ATR o corpo) crolla dopo +1R |
| Target | V5: "Target RR (es. 1,8)" | — | TP = RR × rischio per la parte residua (default da calibrare) |
| Decisioni | FOTO E-25: "decisi sulla barra chiusa" (M1) | — | Gestione sulla chiusura M1 |
| "BE + parziale libera il posto" | VID E-11 | — | Una posizione a pareggio non conta più come "occupata": la cella può aprire un nuovo ingresso (sequenza Raptor) |

## 5. Rischio, modi e livelli

- **Sizing:** RISCHIO % (consigliato) oppure LOTTO FISSO (V5); default del cliente 0,10 o rischio %.
- **Modi** (SITO):
  - **Prop Challenge**: obiettivo +10%, poi chiude tutto, cancella i pendenti e si ferma.
  - **Funded**: protezioni più severe, lavora per il prelievo.
  - **Live**: limite dell'utente, rischio più alto, lascia correre di più.
  - **Flip**: −15% dimezza il rischio, −25% lo porta a un quarto, −30% chiude tutto.
- **Livelli:** Aggressivo / Equilibrato (default) / Prudente, ciascuno con una tabella di rischio per set. Oro (Prop Challenge): 2,40% · 1,60% · 1,00%.
- **Monte Carlo** (SITO): 3.000 giri a blocchi su 3.846 operazioni 2018–2026, sulla metà meno vista dalla taratura.
- **Rischio che respira** (FOTO E-27): pieno fino a −5% di DD, poi in discesa fino a ×0,25 a −23,75%; ripristino dopo 20 trade vincenti. È un'alternativa al Flip, da confrontare.
- **Drawdown giornaliero** (V5): in % o in valuta, fermo fino al giorno dopo.

## 6. Premium A / A+ / A++ (SITO)

- **Ingresso sui ritracciamenti di Fibonacci:** attende il ritorno nella zona favorevole e lo stop è più vicino a parità di obiettivo.
- **A** = ottimizza l'ingresso e mantiene il numero di operazioni.
- **A+** = aggiunge un vaglio sulla direzione.
- **A++** = solo quando ogni criterio concorda.
- VID (E-11): "PREMIUM: quale livello (PREMIUM A solo ENTER … A++ ENTER+MAIN+SEC…)".
- **Proposta:**
  - A = ingresso spostato al livello Fibonacci (50% o 61,8% della candela o della gamba del segnale);
  - A+ = A più il filtro direzionale (forecaster o bias HTF concordi);
  - A++ = A+ più tutti i modelli sopra soglia piena.
  - Il significato di "MAIN" e "SEC" è **AMBIGUO**.
- Il SITO ammette: "non abbiamo misurato Premium acceso contro spento".

## 7. Motore macro (SITO, V5) — Fase 6

- **Sequenza:** 08:00 agenda → 10 minuti prima preavviso con previsione → dato → ordine sul **ritraccio previsto** → esito.
- Il macro è **alternativo**: in modalità macro le celle ICT sono ferme.
- 72 combinazioni tarate (3 mercati × 4 modi × 3 livelli × …).
- Da VID (E-16): ingressi concentrati alle 15–16 server il giovedì (EUR), coerente con i dati USA delle 8:30 NY = 15:30 server.
- **Serve il calendario storico.**

## 8. Ambiguità principali (da decidere in validazione o con te)

1. TF e regole della cella **Breaker Block**: il V5 non la ha.
2. Gestione **V5** (90% a +1R) contro **FOTO** (scala 0,7/2/4R).
3. Cosa sia un "ritraccio confermato" (Raptor) e le "conferme di order flow" (OTE).
4. Livelli di liquidità della cella Sweep e tipo d'ordine.
5. Architettura AI: catena SITO (Occhio, Selettori, LiqBias, Semaforo) contro V5 (Selettore, Gate, Supervisore, Forecaster). Si costruiscono entrambe e si sceglie in validazione.
6. Significato di "MAIN" e "SEC" nel Premium.

---

## 9. Dettagli da video e foto (integrano i §2–6)

| Tema | Evidenza | Effetto sulla ricostruzione |
|---|---|---|
| Timeframe di segnale delle celle oro | FOTO: orari dei segnali PPK e UNIOF sempre multipli di 5 minuti (12:20, 11:15, 01:55, 06:30…). Simbolo dei video in M5 | PPK su M5 (coerente con V5). Per UNIOF i minuti visti (06:30, 13:15, 00:30) sono compatibili sia con M5 sia con M15: si decide in Fase 2 |
| Celle attive in XAUUSD PRIME 1 | FOTO: solo **PPK** e **UNIOF** compaiono nell'oro 2026 | Probabile composizione del SET XAU PRIME 1 = PPK + UNIOF (INFERITO). Da verificare in Fase 2 sulla frequenza |
| Fuso dei segnali | FOTO: "UTC" in etichetta, ma l'ingresso 4424,56 dell'8/1/2026 12:20 cade nel range della barra delle 12:20 **ora server** (non delle 14:20) | Confronti della Fase 2 in ora server. Settembre è **AMBIGUO** (lunedì 00:30 è fuori orario sul server): si provano offset di 0 e ±1 h |
| Ingressi in sequenza | VID: "BE + PARZIALE LIBERA IL POSTO = true (false = conteggio normale)". SITO: "tre ingressi in sequenza" | Una posizione a pareggio dopo il parziale non conta nel limite di posizioni: si può aprire un nuovo ingresso |
| Gestione del set oro | FOTO: 20% a +0,7R e BE, 20% a +2R, 60% a 4R, "decisi sulla barra chiusa". VID XAU: payoff 0,25 con 85% di vincite | Profilo **FOTO** come candidato principale per l'oro; profilo **V5** (90% a +1R) come alternativa da confrontare |
| Prop Challenge | VID: TRAGUARDO FASE 1 = 10, FASE 2 = 5, LIMITE GIORNALIERO 4, LIMITE TOTALE 10, MISURA = EQUITY, AL TRAGUARDO = CHIUDI E FERMATI / CHIUDI E CONTINUA, MARGINE DI SICUREZZA 0,2, LEVA IMPOSTA DALLA PROP | Parametri del modo Challenge. Il margine di sicurezza (0,2) è INFERITO come distanza minima dai limiti, in punti percentuali |
| Funded | CAPITALE FINANZIATO, QUANTO SPINGERE, AVVISA AL GUADAGNO DI | Avviso Telegram al raggiungimento del guadagno (prelievo) |
| Live | CRESCITA DEL LOTTO: COMPOSTO / BASE FISSA | Base del rischio = equity corrente (composto) oppure capitale iniziale (fissa) |
| Flip | OBIETTIVO 2X…5X, STOP-PIANO 30 | Coerente con il SITO (−30% chiude tutto); obiettivo di moltiplicazione del capitale |
| Supervisore | "SUPERVISORE LIQBIAS (**false = come certificato**)", soglia 1..99 (−1 = quella della cella) | Il supervisore è **spento di default** nei set certificati: è un filtro extra attivabile. È in linea con la catena V5 ma va verificato in validazione |
| Filtro notizie | NON OPERARE SULLE NOTIZIE = false, 30/30 minuti | Default spento |
| Stop minimo | "STOP MINIMO IN ATR (0 = spento)" (solo nella versione più recente) | Input facoltativo |
| AI | FOTO: punteggio di un gradient boosting (92 feature a soli rapporti) contro una **soglia viva** (quantile 80% degli ultimi 1.000 punteggi). Ogni rifiuto riporta i 3 motivi contro (contributi per sostituzione con la mediana) | Fase 5: modello a punteggio con soglia viva come alternativa alle soglie fisse del SITO. "Giornale dei perché" in Telegram e nel log |
| Rischio | FOTO: base 1,92%, "respira" (pieno fino a −5% di DD, ×0,25 a −23,75%, ripristino dopo 20 trade in utile, mai aumenti) | Variante del rischio adattivo per il modo Live |
| Orari XAU | VID XAU: picco d'ingressi all'**ora server 01** (apertura asiatica) | Nessuna killzone restrittiva nei set XAU (V5: "Filtro sessioni OFF = come da certificazione") |
