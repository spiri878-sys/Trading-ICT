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
