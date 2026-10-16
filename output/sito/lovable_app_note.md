# App Lovable (autotraderforexclubia.lovable.app), stampa PDF del 16/10/2026

Fonte: `output/sito/lovable_app_2026-10-16.pdf` (22 pagine), più screenshot della pagina prezzi PRIME.

## Novità rispetto alla Fase 1

- OSSERVATO: CORE, PLUS e PRIME condividono la base: trade singoli, parziali, break-even, TP/SL dinamici, bot Telegram, senza griglie né martingala.
- OSSERVATO: **168 modelli ONNX** su CORE e PLUS, **oltre 220** su PRIME.
- OSSERVATO: PLUS ha "più layer decisionali"; il calendario macro fa solo da **contesto** e non apre operazioni.
- OSSERVATO: PRIME ha **6 celle di strategia**: "sceglie autonomamente tra 6 celle in base al contesto di mercato" (selettore di cella per regime).
- OSSERVATO: **"giudici neurali"**: "ogni trade viene confermato dai giudici neurali prima dell'apertura".
- OSSERVATO: macro execution con finestra evento T−2:00 / evento / T+2:00. Ingressi "fino a due minuti prima dell'evento, durante o dopo".
- OSSERVATO: **ordini pendenti** "quando previsti dalla logica operativa".
- OSSERVATO (screenshot prezzi): Premium A · A+ · A++ ("selezione sui ritracciamenti, solo su PRIME"); **93 modelli macro**; motore notizie con **72 combinazioni tarate** mercato per mercato; **3.846 operazioni di calibrazione**; il macro è **alternativo**: in modalità macro le celle ICT restano ferme. Prezzo 9.997 € una tantum, licenza legata al conto.
- OSSERVATO: mercati NASDAQ, EURUSD, XAUUSD, uno strumento per volta; "4+ anni di sviluppo".

## Inferenze

- INFERITO: 220+ modelli ≈ (celle × direzioni × livelli della catena × mercati) più i 93 macro. Per esempio, 6 celle × 2 direzioni × 3 mercati × circa 3 livelli ≈ 108, più 93 macro più ausiliari. Molti modelli piccoli e specializzati, non un unico modello.
- INFERITO: "giudici neurali" = uno stadio MLP dopo il punteggio gradient boosting (coerente con l'"Occhio" della Fase 5: GBM più MLP).
- Nessun numero di performance nell'app; nessuna regola esatta delle celle.

## Storia Instagram "PRIME LIVE" (16/10/2026, M15 XAUUSD)

- OSSERVATO: BUY 0,91 lotti a 4176,57, SL 4154,69 (rischio 21,88 $ = circa 1.990 $ con 0,91 lotti), flottante +1.214,85 USD con il prezzo a 4189,92.
- OSSERVATO: prima di questo, sul 15–16/10, tre trade precedenti (frecce): buy circa 4150 → uscita circa 4163; buy circa 4152 → uscita circa 4170; uscita circa 4153.
- INFERITO: con un rischio del 1,92% il conto sarebbe di circa 104.000 $. Lo stop di circa 22 $ conferma stop ampi (come l'8/1/2026: 21 $), quindi costi trascurabili in R.
- Limite: i nostri dati finiscono il 30/01/2026 e non permettono di verificarlo.

## Storie Instagram PRIME / PLUS (settembre–ottobre 2026): trade reali leggibili

| Data (server) | Lato · TF | Lotti chiusi / aperti | Ingresso → uscita | Orari | SL al momento | TP | Esito |
|---|---|---|---|---|---|---|---|
| 09/09 | BUY · M5 | 0,53 / 0,54 | 4404,00 → 4425,17 | 11:20:00 → 16:24:24 | 4405,05 | 4483,80 | +1.121,75 $ (comm. −11,82) |
| 09/09 | BUY · M5 | 1,14 (aperto) | 4429,62 | — | 4419,46 | 4443,46 | +399 $ flottante |
| 18/09 | BUY · M5 | 2,17 / 2,19 | 4367,32 → 4376,10 | 08:00:07 → 08:44:41 | 4367,86 | 4401,49 | +1.906,01 $ (comm. −47,65) |
| 28/09 | SELL · M1 | 2,24 | 4249,23 → 4237,55 | 03:30:00 → 03:31:17 | 4248,72 | 4214,51 | +2.615,62 $ (comm. −47,54) |
| ? | ORDER FLOW UNICORN (Telegram) | — | TP 4396,28 | — | — | — | +6.058,91 $; reparto "XAUUSD PRIME 2"; "rischio ora 2,09%" |
| 15/10 | BUY · M15 (PLUS) | 0,01 residuo | 4141,70 → parziale circa 4163 | — | 4142,75 | — | +8,35 $ residuo |

Deduzioni (TP = 4R come da manuale):
- 18/09: TP − ingresso = 34,17 → R = 8,54 $; chiusi 2,17 lotti su 2,19 (99%) a +8,78 = **+1,03R**; SL portato a ingresso + 0,54 (pareggio più costi); 0,02 lotti lasciati verso il TP 4R.
- 09/09: TP − ingresso = 79,80 → R = 19,95 $; chiusi 0,53 su 0,54 (98%) a +21,17 = **+1,06R**; SL a ingresso + 1,05; 0,01 lotti residui.
- 28/09: TP distanza 34,72 → R = 8,68 $; chiuso a +11,68 = +1,35R dopo 77 secondi (barra M1 di una spinta violenta).
- **Gestione reale osservata a settembre 2026 = profilo V5: circa 98–99% chiuso intorno a +1R (decisione sulla barra chiusa), stop a pareggio più costi, residuo minimo al TP 4R.** Non la FOTO 20/20/60 (che si vede invece nella storia del 15/10).
- **Ingressi a mercato sull'apertura di barra** (08:00:07, 11:20:00, 03:30:00 = multipli di 5 minuti), nessun pendente.
- Rischio per trade: 0,54 × 19,95 × 100 ≈ 1.077 $; 2,19 × 8,54 × 100 ≈ 1.870 $; 0,91 × 21,88 × 100 ≈ 1.991 $ (15/10). Con rischio 1,9–2,1% → conto di circa 55–100 mila $.
- Stop di 8,5–22 $ con l'oro a 4.150–4.430: circa 0,2–0,5% del prezzo.
- Il reparto si chiama "XAUUSD PRIME 2" (il SET) e il rischio "ora 2,09%" supera la base 1,92%: il moltiplicatore di rischio può superare 1.
- Testimonianza: "6 celle, 4 livelli di AI che devono dare l'ok; secondo motore per le notizie; filtri Premium sui ritracciamenti A, A+, A++".
