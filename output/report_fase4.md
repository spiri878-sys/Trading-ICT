# Fase 4 — Feature per segnale

**Codice e risultati:**
- codice: `python/raptor/prime/features.py`, `python/scripts/phase4_features.py`;
- elenco completo delle feature: `output/feature.md`, generato e verificato dallo script;
- diagnostica: `output/phase4_stats.json`, `output/phase4_univariate_train.csv`;
- dati: `output/cache/features/default.parquet`, 120.643 segnali con etichette e feature.

**Test:** `tests/test_prime_features.py`, in totale **96 test verdi**.
- **Invarianza al troncamento:** le feature sono identiche calcolate con o senza i dati successivi, quindi nessun lookahead.
- **Scala:** raddoppiando i prezzi le feature non cambiano, quindi nessun prezzo assoluto entra nel modello.
- **Lato:** invertendo il lato, le feature direzionali cambiano segno.

## 1. Le 105 feature

| Gruppo | N. | Esempi |
|---|---|---|
| Segnale | 20 | Cella, lato, tipo d'ordine, ingresso n. in sequenza, stop in ATR (TF, M15, H1, H4, D1), profondità del ritracciamento, ampiezza della zona e della gamba, posizione di Fibonacci |
| Volatilità | 18 | ATR relativo su 5 timeframe, rapporti fra ATR, volatilità realizzata M1 (30, 60, 240 minuti), range 4h e 24h, displacement |
| Struttura | 37 | Rotture a favore e contro, MSS, trend M15/H1/H4/D1 allineato, distanza da EMA e swing, posizione nel range 4h/24h/giorno/settimana, distanza da PDH/PDL, PWH/PWL e Asia, FVG e sweep recenti |
| Momentum ed efficienza | 9 | Spinta a 15, 60, 180 minuti e 1 giorno, **efficienza 4h e 24h**, barre consecutive |
| Volumi | 2 | Volume tick relativo (TF e ultima ora) |
| Sessione e tempo | 10 | Ora di New York, killzone, giorno, mese |
| Costi | 3 | Spread / stop, spread / ATR |
| Contesto delle celle | 6 | Segnali precedenti in 30 minuti, 1 ora e 24 ore (stessa cella, tutte, concordi, discordi) |

- **Corrispondenza con il venditore:** sono incluse quasi tutte le feature citate nelle foto (range 4h/24h, ora, efficienza 4h, spinta 60 minuti / 3 ore, stop in ATR M15/H1, spread rispetto alla volatilità, rotture a favore/contro, distanza dalla media). Quelle del V5 (volatilità, struttura, volumi, sessione, multi-timeframe) sono tutte coperte.
- **Manca "notizia in arrivo":** serve il calendario economico (Fase 6).

## 2. Qualità (solo addestramento 2008–2017, 60.587 segnali)

- **Valori mancanti:** solo le 3 feature del range asiatico (25%: segnali prima delle 07:00 server, quando il range non è ancora chiuso). Per questo esiste il flag `asia_known`.
- **Feature costanti:** nessuna.
- **8 coppie quasi identiche** (|correlazione| > 0,95), per esempio `cell_LS` con `is_market`, e `push_1440m` con `efficiency_24h_signed`. Si gestiscono nella Fase 5: gli alberi ne sono poco disturbati e le reti le riducono.

## 3. Quanto dicono, da sole, sul risultato (solo addestramento)

**Base:**
- 22,8% di big-runner;
- 28,4% di ingressi puliti;
- R medio −0,086 (FOTO, stop 3 ATR).

**AUC univariata contro "big-runner":** massimo **0,53 / 0,47** (0,5 = nessuna informazione). Le più informative:

| Feature | AUC big-runner | R medio, quintile peggiore → migliore |
|---|---|---|
| `dist_pwh_atr_d1` (distanza dal massimo della settimana precedente, a favore) | 0,466 | −0,19 → **−0,01** |
| `range_24h_atr_h1` (range delle 24 ore) | 0,469 | −0,16 → **+0,01** (range stretto) |
| `pos_week` (posizione nel range settimanale, con lato) | 0,530 | −0,18 → −0,02 |
| `dist_h4_ema` (a favore della EMA50 H4) | 0,526 | −0,16 → −0,04 |
| `dist_h1_ema` | 0,522 | −0,19 → −0,06 |
| `efficiency_24h` | 0,474 | −0,15 → −0,03 |

**Lettura:**
- Le feature più utili sono di **contesto**: trend H1/H4/D1, posizione nella settimana e nel giorno, range e volatilità delle 24 ore.
- Le caratteristiche ICT del segnale stesso (FVG, sweep, displacement) dicono poco.
- I trade **a favore del trend superiore e con volatilità contenuta** sono molto meno negativi.
- Nessun quintile di una singola feature è chiaramente positivo: il miglior gruppo arriva a circa 0R.
- **Avvertenza:** questa è informazione univariata sull'addestramento, non un vantaggio dimostrato. La selezione delle feature e delle soglie avverrà **solo dentro il walk-forward** della Fase 5, con verifica sul 2018–2021.

## 4. Prossima fase (Fase 5 — catena AI)

- **Due architetture:**
  - **SITO** (Occhio a 8 modelli in voto, Selettori, Supervisore LiqBias, Semaforo);
  - **V5** (Selettore per cella sui big-runner, Gate Sì/No sugli ingressi puliti, Supervisore di liquidità su M5, Forecaster della barra successiva).
- **Addestramento:** walk-forward con purging ed embargo dentro il 2008–2017.
- **Soglie:** scelte solo sul 2018–2021, con alternativa "soglia viva" (quantile 80% degli ultimi 1.000 punteggi, come nelle foto).
- **Misura:** per ogni livello della catena, quanto migliora rispetto alla baseline (PF, R medio, drawdown, numero di operazioni).
- **Formato:** modelli esportabili in ONNX (Fase 8).

**Fine Fase 4. Attendo il tuo ok.**
