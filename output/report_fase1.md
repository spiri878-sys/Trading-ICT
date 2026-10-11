# Fase 1 — Estrazione completa dal materiale

## 1. Cosa è stato letto

| Fonte | Come | Risultato |
|---|---|---|
| Sito, pagina principale (HTML) | `phase1_site_data.py`: testo più dati nascosti delle schede (oggetto JS dei 18 set) e 5 immagini incorporate | `output/sito/` (testo, `dati.json`, `numeri_sito.md`, `img/`) |
| Manuale PRO V5 (10 pagine) | Testo integrale; alcune celle sono troncate nel PDF stesso | `output/documenti/note.md` §A |
| Presentazione prima versione (9 pagine-immagine) | Convertita in PNG e letta pagina per pagina | `output/documenti/note.md` §B |
| 5 video | `phase1_extract_frames.py`: 1 fotogramma ogni 3 s più i cambi di scena (331 in totale); ogni fotogramma letto, con ritagli ingranditi; 3 letture in parallelo | `output/video/<nome>/note.md` |
| 16 foto | Lette tutte, con ritagli | `output/foto/note.md` |
| 4 pagine guida del sito e app Lovable | **Non ricevute** | Lacuna dichiarata |

**Video senza parlato.** I video hanno solo musica e titoli, quindi non c'è audio da trascrivere.

## 2. Prodotti

- **`output/regole.md`**:
  - definizioni operative causali di swing, BOS/MSS, FVG, OB, breaker, sweep, displacement, OTE e PO3;
  - le **6 celle** con regola, fonte, timeframe e stato (regola esatta / AMBIGUO / INFERITO);
  - la catena AI nelle due architetture (sito e V5);
  - gestione, rischio, modi, livelli, Premium, macro;
  - §9: dettagli nuovi da video e foto.
- **`output/menu_input.md`** — il menu PRIME vero, 38 voci, ordine, valori e nomi interni `Inp…`; le voci del V5 da aggiungere; la proposta di menu.
- **`output/trade_riferimento.csv`** — 5 trade XAU (1 completo, 4 parziali) e **16 segnali scartati** con orario, cella, direzione e punteggio.
- **`output/numeri_dichiarati.md`** — tutti i numeri di sito, video, foto e manuale, con le condizioni dei test e le incongruenze.
- **`output/checklist.md`** aggiornata; **`docs/evidence_register.md`** con le voci E-35…E-41.

## 3. Le scoperte più importanti

1. **Il menu PRIME è di alto livello.**
   - Si scelgono MERCATO, MODALITÀ OPERATIVA (Challenge / Funded / Live / Flip), **SET** (XAUUSD PRIME 1/2, PRIME MACRO XAU…), QUANTO SPINGERE e CRESCITA DEL LOTTO.
   - Celle, soglie, stop e target sono **dentro il SET**.
   - Per l'oro quindi bisogna costruire 2 SET (PRIME 1 e 2) più 1 SET macro, ciascuno con le sue celle e le sue soglie scelte in validazione.
2. **Nell'oro operano soprattutto PPK (Raptor Mode) e UNIOF (Unicorn).** Le foto 2026 mostrano solo queste due celle.
   - I segnali sono su **M5**: gli orari sono sempre multipli di 5 minuti.
   - Il supervisore LiqBias è **spento nei set certificati** ("false = come certificato").
3. **La gestione reale dell'oro** (foto): 20% a +0,7R con pareggio, 20% a +2R, 60% a 4R, decisioni sulla barra M1 chiusa.
   - Il manuale V5 dice invece "90% a +1R": in Fase 3 si provano entrambe.
4. **Il fuso dei segnali del venditore coincide con l'ora server dei tuoi dati** (verificato sull'ingresso 4.424,56 dell'8/1/2026 alle 12:20). I segnali di settembre restano ambigui di un'ora.
5. **I test del venditore sono ottimistici:**
   - "1 minute OHLC" ed "esecuzione ideale a latenza zero";
   - lotti composti partendo da 1.000.
6. **Per l'oro i numeri del venditore sono i più deboli dei tre mercati:**
   - video XAU: PF 1,46, drawdown 18,7%, 85% di vincite ma perdita media pari a 3,9 volte la vincita media;
   - sito: PF implicito circa 2,07 con 90 operazioni all'anno (PRIME 1).
   - Le due fonti non coincidono: il video ha circa 240 operazioni all'anno.

## 4. Limiti della Fase 1 (onesti)

- **Il confronto della Fase 2 avrà una base piccola.** Nei video **non si legge nessuna operazione singola**: si vedono solo il grafico del saldo e il report. Le operazioni di riferimento per l'oro sono:
  - 1 trade completo (8/1/2026, PPK BUY 4.424,56, stop 21 $, esito +2,97R);
  - 4 trade con dati parziali;
  - 16 segnali scartati con orario e direzione.
- **Ambiguità rimaste** (`regole.md` §8):
  - timeframe e regole del Breaker Block;
  - "ritraccio confermato";
  - livelli di liquidità della cella Sweep;
  - significato di MAIN e SEC nel Premium;
  - quale architettura AI usare.

  Si risolvono in validazione, non a occhio.
- **Gruppi del menu non visti:** FILTRO NOTIZIE e MESSAGGI GRAFICA si leggono solo in parte; il gruppo Premium e Telegram non si vede.

## 5. Decisioni prese in Fase 0 (correggimi se non va bene)

Ho interpretato il tuo "Ok" come accettazione delle mie proposte:
- **addestramento 2008–2017**, con 2005–2007 solo come contesto H4, D1 e W1;
- **costi C1/C2** (0,30 $ più 3,5 $ per lotto per lato; stress ×2).

## 6. Prossima fase (Fase 2 — generatore di segnali in Python)

- Le 6 celle sui loro timeframe:
  - PPK e PO3 su M5, OTE su M12, Unicorn su M15, Sweep su M3;
  - Breaker Block da scegliere fra M5, M15 e H1.
- Confronto con `trade_riferimento.csv`: quanti segnali ritrovo con stessa data, direzione e prezzo vicino, e come si confronta la frequenza annua con i 73–90 trade all'anno dichiarati.
- Tutto calibrato solo su 2008–2017 e 2018–2021.

**Il confronto con i segnali del venditore richiede di guardare date del 2026, che cadono nel periodo di test.** Propongo di usarle **solo** per verificare che i segnali "assomiglino" a quelli del venditore (orario, cella, direzione), **mai per scegliere parametri di performance**.

**Fine Fase 1. Attendo il tuo ok.**
