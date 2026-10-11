# Fase 3 — Etichette e baseline senza filtri (solo 2008–2021)

**Codice:**
- `python/raptor/prime/label.py`: simulatore dei due profili di gestione;
- `python/scripts/phase3_label.py`: etichettatura, baseline, benchmark casuale, edge lordo.

**Test:** `tests/test_prime_label.py`, con parità del profilo FOTO con il simulatore già validato. In totale **93 test verdi**.

**Risultati:** `output/phase3_baseline.json`, `output/phase3_baseline_by_year.csv`; etichette in `output/cache/labels/default.parquet`.

## 1. Cosa è stato simulato

- **Segnali:** 120.643 segnali delle 6 celle dal 2005. Il periodo 2022+ è etichettato per le fasi successive ma **escluso da ogni numero qui sotto**.
- **Due gestioni:**
  - **FOTO**: 20% a +0,7R con stop a pareggio, 20% a +2R, 60% al target 4R;
  - **V5**: 90% a +1R con pareggio, poi trailing sugli swing M5 confermati, blocchi a +1R e +2R, uscita se si forma una struttura contraria su M5.
- **Due stop:** strutturale della cella, oppure **3 × ATR M15** (dal trade dell'8/1/2026).
- **Costi C1:**
  - spread 0,30 $ e commissione 3,5 $/lotto/lato;
  - slittamento 0,05 $ e swap;
  - stop controllato per primo dentro la barra;
  - massimo 3 giorni, chiusura il venerdì sera.
- **Definizioni delle etichette:**
  - **big-runner** = il prezzo arriva a +3R prima di toccare lo stop iniziale (soglia oltre il target intermedio di 2R, vicina al target 4R);
  - **ingresso pulito** = meno di 0,5R contro prima di arrivare a +1R.

## 2. Risultato medio per operazione (R netto)

| Cella | Configurazione | Addestramento 2008–17: R medio · PF | Validazione 2018–21: R medio · PF | Operazioni (add. + val.) |
|---|---|---|---|---|
| PPK (Raptor) | FOTO, stop struttura | −0,142 · 0,72 | −0,165 · 0,67 | 18.967 + 6.763 |
| | FOTO, stop 3 ATR M15 | −0,090 · 0,81 | −0,106 · 0,78 | |
| | V5, stop 3 ATR M15 | −0,089 · 0,84 | −0,109 · 0,80 | |
| UNIOF (Unicorn) | FOTO, 3 ATR | −0,079 · 0,83 | −0,141 · 0,72 | 943 + 380 |
| OTEOF | FOTO, 3 ATR | −0,104 · 0,79 | −0,102 · 0,79 | 1.233 + 503 |
| PO3 | FOTO, 3 ATR | −0,089 · 0,83 | **+0,175 · 1,48** | 196 + **71** |
| LS (Sweep) | FOTO, 3 ATR | −0,078 · 0,84 | −0,106 · 0,78 | 26.165 + 11.644 |
| BB (Breaker) | V5, 3 ATR | −0,098 · 0,82 | −0,097 · 0,82 | 3.589 + 1.464 |

- **Per anno** (FOTO, stop ATR; tabella completa nel CSV): PPK, LS, BB e OTEOF sono negativi in quasi tutti i 14 anni.
- **PO3 è molto irregolare:** +1,16R di media nel 2020, −0,48R nel 2016, con 20–70 operazioni all'anno.
- **Stop 3 × ATR M15 meglio dello stop strutturale in tutte le celle.** Lo stop strutturale su M3–M5 è piccolo (mediana 1–3 $), quindi spread e commissioni pesano 0,1–0,3R per operazione. Con lo stop ATR (circa 4,5 $) pesano la metà. È coerente con lo stop "largo" del venditore.
- **V5 e FOTO sono quasi equivalenti** (differenze di 0,01–0,03R).

## 3. Le celle hanno un vantaggio prima dei costi?

**Edge lordo, a costi zero** (FOTO, 2008–2021):

| | PPK | UNIOF | OTEOF | PO3 | LS | BB |
|---|---|---|---|---|---|---|
| Stop struttura | +0,002 | +0,006 | +0,019 | +0,034 | +0,023 | −0,006 |
| Stop 3 ATR | +0,007 | −0,007 | −0,004 | +0,060 | +0,019 | −0,011 |

**Benchmark casuale** (FOTO, stop struttura, 2008–2021): stessi minuti e stessi prezzi d'ingresso, stessa distanza di stop, **direzione a caso** (50 ripetizioni):

| Cella | Reale | Caso (media) | Ripetizioni casuali ≥ reale |
|---|---|---|---|
| PPK | −0,148 | −0,126 | 100% |
| UNIOF | −0,137 | −0,113 | 80% |
| OTEOF | −0,260 | −0,313 | **2%** |
| PO3 | −0,179 | −0,152 | 56% |
| LS | −0,364 | −0,325 | 100% |
| BB | −0,122 | −0,099 | 98% |

## 4. Conclusione onesta

1. **Senza filtri nessuna cella ha un vantaggio.**
   - Prima dei costi il risultato è circa 0 (da −0,01 a +0,06R per operazione); con costi realistici è da −0,08 a −0,17R.
   - La direzione scelta dalle celle **non è migliore del caso**: per PPK, LS e BB è leggermente peggiore. Solo **OTEOF** batte il caso (2%), ma resta negativa.
2. **Il problema è quello già visto nel lavoro precedente:** i segnali ICT di base sull'oro, a queste frequenze (migliaia all'anno), sono essenzialmente rumore. Tutto il peso è sulla **catena AI**: deve scartarne circa il 90%, come dice il venditore ("1.733 giudicati, 169 presi"), e i segnali tenuti devono valere più di circa +0,1R netti.
3. **Cosa la Fase 5 deve dimostrare in validazione 2018–2021:** che i selettori, addestrati sui big-runner (circa il 21% dei segnali), e il gate, addestrato sugli ingressi puliti (circa il 25%), trovano un sottoinsieme con R medio netto chiaramente positivo e stabile negli anni. Se non ci riescono, la specifica prevede il **Piano B (Fase 10)** prima di guardare il test.
4. **PO3 con stop ATR** è l'unico caso positivo in validazione (+0,175R), ma su **71 operazioni** e negativo nell'addestramento. Non lo considero un vantaggio: lo terrò d'occhio.

## 5. Decisioni per le fasi successive

- **Stop di default: 3 × ATR M15**, migliore in tutte le celle e coerente con il venditore.
- Gestione: FOTO e V5 restano entrambe. La scelta si fa in Fase 5 sui segnali filtrati, perché senza filtro la differenza è minima.
- **Etichette pronte per l'AI:** `big_runner`, `clean_entry`, `r_foto`, `r_v5` (con le varianti `_atr`), MFE e MAE.

**Fine Fase 3. Attendo il tuo ok per la Fase 4 (feature: oltre 100 caratteristiche per segnale, solo dati disponibili in quel momento).**
