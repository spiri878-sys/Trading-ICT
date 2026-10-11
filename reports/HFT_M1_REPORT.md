# Scalping / "HFT" su M1, XAUUSD 2018–2026: risultato

**Script:** `python/scripts/hft01_m1_scalping.py`. **Dati:** `experiments/hft01_m1_scalping.csv`.

**Cosa è stato testato:** 4 famiglie, long e short, attive solo nelle sessioni di Londra e New York, con ingresso a mercato alla barra M1 successiva, SL e TP in ATR(M1), durata massima 15–120 minuti. Niente griglia né martingala: 56 configurazioni × 3 scenari di costo.

**Avvertenza:** il vero HFT (millisecondi, tick, server vicino al broker) **non è simulabile** con barre M1. Qui si misura lo scalping ad alta frequenza, nell'ordine di decine di trade al giorno.

| Famiglia | Senza costi (R mediano) | ECN: spread 0,10 + 7 $/lotto + slippage 0,02 | Standard: spread 0,30 + 7 $/lotto + slippage 0,05 |
|---|---|---|---|
| Impulso (segue la candela forte) | −0,096 | −0,290 | −0,460 |
| Micro-breakout 15/30 minuti | −0,045 | −0,259 | −0,438 |
| Mean reversion Bollinger M1 | **+0,039** (75% delle varianti > 0; massimo +0,067) | −0,173 (0% > 0) | −0,363 |
| Apertura di New York | −0,022 | −0,090 | −0,167 |

**Lettura:**

- Su M1 l'oro è leggermente **mean-reverting**: seguire impulsi e rotture perde anche senza costi.
- La reversione alla media ha un piccolo vantaggio lordo, +0,04–0,07R, cioè pochi centesimi di dollaro a trade.
- Spread e commissioni costano 0,15–0,45R per trade, quindi 3–10 volte quel vantaggio.
- **Nessuna configurazione è positiva con costi retail**, neppure ECN.
- Per andare in pareggio servirebbe un costo totale sotto circa 0,03–0,05 $ per oncia a giro, cioè livelli istituzionali.

**Verdetto:** lo scalping/HFT su M1 non è profittevole per un conto retail. Non è stato sviluppato un EA.
