# Fase 2 — Generatore di segnali delle 6 celle PRIME

- **Codice:** `python/raptor/prime/cells.py` (celle), `python/raptor/prime/data.py` (dati), `python/scripts/phase2_signals.py` (generazione, statistiche e confronto).
- **Test:** `tests/test_prime_cells.py`. Per ogni cella c'è un test di **invarianza al troncamento**: i segnali fino a T sono identici calcolati con o senza i dati successivi, quindi nessun lookahead. Ci sono anche test sul tempo di riempimento e sui filtri. In totale **87 test verdi**.
- **Risultati:** `output/phase2_stats.json`, `output/phase2_match_log.csv`; segnali in `output/cache/signals/default.parquet`.

## 1. Le celle implementate

Definizioni complete in `regole.md` §1–2. Tutte sono causali: il segnale è noto alla **chiusura** della barra e i timeframe superiori si usano solo a barra chiusa.

| Cella | TF | Regola (default) | Ordine | Stop (default) |
|---|---|---|---|---|
| PPK (Raptor Mode) | M5 | BOS + displacement (corpo della candela centrale ≥ 1,2 ATR) + FVG ≥ 0,15 ATR; **ri-armo** su ogni FVG di continuazione nella stessa gamba, fino a 3 ingressi entro 24 barre | Limit sul bordo FVG | Oltre l'origine della gamba |
| OTEOF | M12 | Sweep di liquidità (PDH/PDL, Asia, ultimo swing) negli ultimi 12 bar, poi MSS opposto con FVG | Limit al 70,5% (zona 62–79%) | Oltre lo sweep |
| PO3 | M5 | Range asiatico (03–07 server) → sweep di un lato → MSS opposto con displacement e FVG, nella finestra NY 02:00–11:00 | Limit sul bordo FVG | Oltre la manipolazione |
| UNIOF (Unicorn) | M15 | Sweep, poi MSS; breaker della rottura ∩ FVG non mitigato | Limit sulla sovrapposizione | Oltre sweep e gamba |
| LS (Liquidity Sweep) | M3 | Sweep con chiusura di rientro forte (corpo ≥ 0,8 ATR) | A mercato alla chiusura | Appena oltre l'estremo |
| BB (Breaker Block) | M15 (TF non documentato) | MSS con displacement; l'ultima candela opposta sullo swing rotto diventa breaker | Limit al ritorno | Oltre il breaker e la gamba |

**Filtri comuni:**
- niente segnali nei giorni degradati (Fase 0);
- niente segnali dopo le 22:00 del venerdì;
- rischio fra 0,5 e 15 ATR.

**Varianti già pronte** (da scegliere in validazione, Fase 3 e 5):
- ingresso sul bordo prossimale, al 50% o sul bordo distale della zona;
- stop strutturale oppure **N × ATR M15**;
- PPK con o senza BOS obbligatorio;
- scadenza dell'ordine;
- k degli swing;
- soglie di displacement e di FVG.

## 2. Quanti segnali (solo 2008–2021: addestramento + validazione)

| Cella | Segnali/anno (media) | Min–max per anno | % long | Rischio mediano | Ore server più frequenti |
|---|---|---|---|---|---|
| PPK | **2.445** | 2.079–2.940 | 49,8% | 3,23 $ (3,7 ATR M5) | 15, 9, 8 |
| LS | 2.704 | 2.490–3.134 | 50,6% | 0,98 $ (1,5 ATR M3) | 15, 14, 8 |
| BB (M15) | 455 | 413–495 | 48,8% | 4,11 $ | 15, 16, 9 |
| OTEOF | 279 | 236–324 | 49,8% | 1,68 $ | 15, 9, 10 |
| UNIOF | 155 | 139–190 | 50,0% | 3,34 $ | **1**, 9, 16 |
| PO3 | 39 | 22–68 | 50,5% | 2,49 $ | 9, 10, 11 |

- BB su timeframe alternativi: M5 = 1.332 segnali all'anno, H1 = 116.
- Il numero di segnali è stabile negli anni, quindi la definizione non dipende da un periodo particolare.

**Confronto con il venditore:**
- Nel 2026 il venditore dichiara **circa 1.733 segnali "giudicati"** per PPK e UNIOF in circa 9 mesi (foto), cioè circa 2.300 all'anno, di cui circa il 10% preso: 169 trade.
- I nostri PPK + UNIOF di default sono **circa 2.600 all'anno**: lo stesso ordine di grandezza. I filtri AI della Fase 5 dovranno tenerne circa il 4–10% per arrivare ai 90–240 trade all'anno dichiarati per l'oro.

## 3. Confronto con i segnali del venditore (solo somiglianza)

**Riferimenti datati:**
- 15 segnali PPK: 2 trade presi e 13 scartati;
- 3 segnali UNIOF scartati;
- tutti del 2026, quindi nel periodo di test: **li ho usati solo per la somiglianza, nessuna performance è stata calcolata**.

**Metodo:**
- un riferimento è "ritrovato" se esiste un nostro segnale della stessa cella e direzione il cui ordine si riempie entro ±5 minuti dall'orario del riferimento;
- variante: il segnale stesso entro ±1 barra;
- offset orario 0 e ±60 minuti;
- **384 varianti di definizione** provate (`phase2_match_log.csv`).

| | PPK (15 riferimenti) | UNIOF (3) |
|---|---|---|
| Definizione di default | 0 | 0 |
| Migliore fra le 384 varianti | 2 (con offset −60 minuti) / 3 (sul tempo del segnale, variante senza BOS e molto più frequente) | 0 |
| **Livello del caso** (stessi segnali contro riferimenti spostati di 1,5–5 ore) | media 0,3, massimo 2 | 0 |

**Conclusione onesta:** la corrispondenza è **al livello del caso**. Con 15 riferimenti e regole interne non pubblicate, **non è possibile ricostruire esattamente i segnali del venditore**. Per questo ho interrotto l'iterazione: aumentare la corrispondenza oltre il caso significherebbe solo adattarsi a 15 punti del periodo di test.

**Cosa si impara dal trade di riferimento** (8/1/2026, PPK BUY a 4.424,56, stop 21 $):
- Alle 10:50–10:55 una spinta rialzista ha lasciato un FVG fra 4.424,44 e 4.425,82. Il prezzo è tornato sul **bordo distale** dell'FVG (4.424,44) alle 12:15–12:20, **1 ora e 25 minuti dopo**: l'ingresso del venditore è lì, quindi un ordine limit sul bordo distale con scadenza lunga (oltre 16 barre M5).
- **Lo stop di 21 $ è 2,98 × ATR(14) M15** (7,05 $ in quel momento). È coerente con uno stop "N × ATR" (il manuale V5 nel menu ha "Lunghezza ATR / Moltiplicatore ATR").
- **Non c'era un BOS** dello swing M5 precedente (4.433,24): la spinta rompeva solo un massimo minore.
- In questo caso il venditore entra quindi su FVG da displacement con conferma di struttura più debole della nostra. Le varianti "bordo distale", "stop 3 × ATR M15" e "PPK senza BOS" sono pronte e verranno **scelte in validazione 2018–2021**, non su questo esempio.

## 4. Differenze non risolte

1. Regole esatte di PPK e UNIOF del venditore: non identificabili (vedi §3).
2. Timeframe del Breaker Block: M15 di default; M5 e H1 come alternative.
3. Stop strutturale contro N × ATR M15: si decide in Fase 3 con le etichette e in validazione.
4. La UNIOF del venditore scatta anche all'**01:00–01:55 server** (riferimenti di settembre e picco all'ora 01 del video XAU). Anche la nostra UNIOF ha il picco all'ora **01**: è una somiglianza di profilo, non di singoli segnali.

## 5. Prossima fase (Fase 3 — etichette e baseline)

- Simulare l'esito di ogni segnale 2008–oggi con la gestione completa, nei due profili da confrontare:
  - foto: 20% a 0,7R + BE, 20% a 2R, 60% a 4R;
  - V5: 90% a +1R, pareggio e trailing strutturale.
- Costi C1; salvare R, MFE/MAE, durata, big-runner (proposta: MFE ≥ 3R) e qualità d'ingresso.
- Risultati per cella e per anno **solo 2008–2021**, senza filtri.

**Fine Fase 2. Attendo il tuo ok.**
