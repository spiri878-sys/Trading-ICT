# Fase 5 — Catena AI (architetture V5 e SITO) e autoallenamento

**Codice e risultati:**
- codice: `python/raptor/prime/models.py`, `python/scripts/phase5_ai_chain.py`;
- modelli: `models/prime/` (LightGBM `.txt`, MLP `.pkl`, elenco delle feature);
- risultati: `output/phase5_results.json`, `phase5_levels.csv`, `phase5_grid.csv` (tutte le combinazioni provate), `phase5_selected_config.json`.

**Test:** `tests/test_prime_models.py`. Coprono walk-forward senza futuro con embargo, soglia viva che usa solo il passato, voto dell'Occhio e riproducibilità. In totale **100 test verdi**.

## 1. Cosa è stato costruito

| Livello | Architettura V5 (manuale) | Architettura SITO (PRIME) |
|---|---|---|
| Contesto | **Regime**: modello di solo contesto (60 feature) | — |
| 1 | **Selettore**: P(big-runner), 105 feature | **Occhio**: 8 modelli (4 gradient boosting + 4 reti MLP) che votano a maggioranza |
| 2 | **Gate Sì/No**: P(ingresso pulito), doppio consenso | **Selettori**: percentile **per cella** del punteggio, soglie 0,78–0,92 |
| 3 | **Supervisore di liquidità** (M5): bias a 1 ora dagli sweep | **Supervisore LiqBias**, soglie 0,70–0,72 |
| 4 | **Forecaster** (M5): direzione della barra successiva; blocca o aumenta il rischio ×1,5 | **Semaforo**: R atteso → rischio ×0,5 / ×1 / ×1,5 |

- **Addestramento:** 2008–2017, con previsioni fuori campione anno per anno sul 2011–2017 ed embargo di 5 giorni.
- **Validazione:** 2018–2021, dove si scelgono le soglie.
- **Test:** 2022+ non toccato.
- **Stop e costi:** stop 3 × ATR M15; esiti netti con costi C1.

## 2. Quanto "vedono" i modelli (AUC; 0,50 = niente)

| Modello | Fuori campione 2011–17 | Validazione 2018–21 |
|---|---|---|
| Selettore (big-runner) | 0,532 | 0,516 |
| Gate (ingresso pulito) | 0,540 | 0,522 |
| Regime | 0,529 | 0,519 |
| Supervisore LiqBias M5 | — | 0,531 |
| Forecaster M5 | — | 0,533 |

Il segnale c'è, ma è **molto debole**, e cala dal periodo di addestramento alla validazione.

## 3. Risultati in validazione 2018–2021 (R netto per operazione)

**Baseline senza filtri** (gestione FOTO): 20.825 operazioni, **−0,106R**, PF 0,78, 0 anni positivi su 4.

**Migliore configurazione V5** (gestione FOTO): selettore ≥ 90° percentile, gate ≥ 70°, supervisore 0,6, forecaster 0,55.

| Livello | Operazioni/anno | R medio | PF | Anni positivi |
|---|---|---|---|---|
| Baseline | 5.206 | −0,106 | 0,78 | 0/4 |
| + Selettore ≥ 0,9 | 538 | −0,005 | 0,99 | 3/4 |
| + Gate ≥ 0,7 | 364 | **+0,043** | 1,10 | 3/4 |
| + Supervisore 0,6 | 354 | +0,042 | 1,09 | 3/4 |
| + Forecaster 0,55 | 301 | **+0,046** | 1,10 | 3/4 (2019: −57R) |

**Migliore configurazione SITO:** selettori per cella ≥ 92° percentile più semaforo. 415 operazioni all'anno, **+0,035R**, PF 1,05, 3 anni su 4. In questa configurazione l'Occhio non migliora.

**Gestione V5** (90% a +1R): nessuna combinazione supera i criteri. La gestione **FOTO** (20% / 20% / 60% a 4R) è nettamente migliore con i filtri.

**Contro il caso:** le selezioni battono il 100% di 1.000 selezioni casuali della stessa dimensione (che danno in media −0,105R). **I filtri tolgono davvero circa 0,13–0,15R di perdita per operazione.**

## 4. Il controllo di onestà: soglie scelte prima, applicate dopo

Le soglie scelte solo sul 2011–2017 (fuori campione), applicate al 2018–2021 senza ritocchi:

| | Scelte sul 2011–17 | Stesse soglie sul 2018–21 |
|---|---|---|
| V5, FOTO | +0,057R · PF 1,13 · 6/7 anni | **−0,024R** · PF 0,95 · 1/4 anni |
| SITO, FOTO | +0,091R · PF 1,14 · 5/7 anni | **+0,025R** · PF 1,04 · 3/4 anni |
| V5, gestione V5 | +0,006R | **−0,084R** |

**La stima più pulita del vantaggio è circa +0,03R per operazione, PF circa 1,04, con la SITO.** È positiva, ma troppo sottile.

## 5. Autoallenamento: cosa fa il venditore e cosa conviene

Il venditore (foto) usa **modelli congelati** al 31/12/2025 più una **soglia viva**: prende i trade sopra il quantile 80% degli ultimi 1.000 punteggi. **Non si riaddestra da solo.** Confronto sul 2018–2021 con lo stesso selettore e gestione FOTO:

| Modalità | Operazioni (4 anni) | R medio | Anni positivi |
|---|---|---|---|
| **Congelato** (soglia fissa al 90° percentile del training) | 2.153 | **−0,005** | 3/4 |
| Soglia viva q = 0,7 | 6.318 | −0,094 | 1/4 |
| Soglia viva q = 0,8 (come il venditore) | 4.184 | −0,086 | 1/4 |
| Soglia viva q = 0,9 | 2.108 | −0,048 | 1/4 |
| Riaddestramento annuale | 2.075 | −0,029 | 2/4 |

**Risposta:**
- Sui nostri dati la soglia viva **peggiora** il risultato: si adatta ai periodi in cui tutti i punteggi calano e finisce per prendere trade peggiori.
- Anche il riaddestramento annuale non aiuta.
- **Conviene il modello congelato con soglia fissa.** Nell'EA si potrà comunque aggiornare i modelli con una versione nuova (riaddestrata da me), non in automatico.

## 6. Conclusione e decisione

- La catena AI **funziona come filtro**: porta i segnali da −0,11R a circa 0 / +0,03R e batte nettamente il caso.
- **Ma il vantaggio finale è troppo sottile per essere solido:**
  - stima onesta circa +0,03R, PF circa 1,04;
  - un anno su quattro in perdita;
  - con costi doppi (scenario C2: circa −0,05R per operazione in più) **diventerebbe negativo**;
  - il trading reale di solito peggiora rispetto al backtest.
- Il criterio della specifica ("se in validazione la PRIME non mostra un vantaggio solido, **prima di guardare il test**, Piano B") **è soddisfatto**. Propongo quindi di passare ora alla **Fase 10, Piano B**, prima di costruire macro, Premium ed EA (Fasi 6–9) su un motore così debole:
  1. configurazione del manuale V5 sui suoi timeframe: è già quella testata qui;
  2. aggiunta delle strategie della prima versione: **Silver Bullet, Market Structure Shift, Judas Swing, Order Block model**, e un **Market Brain** che sceglie la strategia secondo la fase di mercato;
  3. **portafoglio di celle**: solo quelle con vantaggio in validazione, ognuna con il suo filtro. In più, la gestione FOTO come default, che con i filtri è nettamente migliore.
- **Alternativa:** proseguire comunque con le Fasi 6–9 sulla configurazione SITO + FOTO, sapendo che il vantaggio è marginale.

**Fine Fase 5. Attendo la tua decisione: Piano B (consigliato) oppure Fasi 6–9 con la configurazione attuale.**
