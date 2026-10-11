# Audit di un canale segnali Telegram XAUUSD (marzo–settembre 2026)

Fonte: export JSON del canale fornito dall'utente (11.261 messaggi, 9 mar → 9 set 2026). I segnali sono stati verificati sulle barre M1 reali XAUUSD dello stesso periodo. L'export non è salvato nel repository.

Script: `python/scripts/tg01_signal_channel.py` (griglia), `tg02_baselines.py` (esecuzione ideale e confronti casuali), `tg03_profile.py` (profilo dei segnali). Parser e simulatore: `python/raptor/signals/`.

## 1. Come sono fatti i segnali

- **Sequenza:**
  1. un avviso secco, "Gold buy" / "Gold sell";
  2. circa 90 secondi dopo (mediana) il segnale completo: zona (es. `5186-5180`), `SL`, 4–8 TP numerati e un ultimo "TP" aperto.
- **Numero:** 671 segnali utilizzabili, circa 100 al mese, quasi tutti tra le 10 e le 18 ora server (tra le 9 e le 17 ora italiana).
- **Geometria:**
  - stop mediano 12 $ (120 pip);
  - **TP1 mediano 3 $ (30 pip)**, cioè TP1 vale circa 0,25 R;
  - TP successivi ogni 2–5 $.
- **Gestione dichiarata:** "per ogni TP chiudo qualche profitto e SL a BE". Nei fatti ci sono anche molte decisioni manuali non replicabili: "allargo stop", "buy senza stop per la notte", "chiudo tutto", ri-ingressi.
- **Orario:** l'ora di Telegram è 1 ora indietro rispetto al server dei dati. Con questo allineamento, il primo prezzo della zona coincide con il mercato al momento del messaggio: differenza mediana 0,35 $, 95% dei segnali entro 5 $.
- **Errori di battitura:** 41 segnali avevano numeri sbagliati (es. `SL 4114` invece di `4214`), corretti automaticamente con la sostituzione di una sola cifra.

## 2. Cosa dichiara il canale e cosa ha fatto il mercato

| | Canale | Mercato (prezzo del canale, costi zero) |
|---|---|---|
| Messaggi "TP1 ✅" | 468 (70% dei segnali) | TP1 raggiunto prima dello SL nel 78% dei segnali |
| Messaggi "Stop 🛑" | 73 (11%) | **SL pieno nel 22% dei segnali** (circa 145) |
| Pip annunciati | +112.255 (somma dei "+N pips") | Gestione "1 posizione per TP + runner, BE dopo TP1": **−1.986 $** con 0,10 lotti |

- Circa metà degli stop non viene annunciata.
- I "+pips" annunciati sono cumulativi per TP e non sono un P&L reale.
- I profitti si annunciano, le perdite molto meno.

## 3. Il follower reale: tutte le combinazioni

Sono state testate **1.188 combinazioni**, risultato di ingresso × latenza × gestione × durata massima × costi:

- **ingressi:**
  - mercato all'avviso;
  - mercato al segnale (+0, +1 o +3 minuti);
  - limit sul primo prezzo, sul centro o sul fondo della zona (scadenza 60 o 240 minuti);
  - metà a mercato e metà limit in fondo alla zona.
- **gestione:**
  - tutto a TP1, …, TP6 (con o senza BE dopo TP1);
  - una posizione per ogni TP, con o senza runner, con BE dopo TP1 o TP2, con o senza stop a gradini;
  - 50/50 (TP1 + ultimo TP, oppure TP1 + runner);
  - terzi su TP1, TP2 e TP3.
- **durata massima:** 1 ora, 4 ore, 24 ore.
- **costi:**
  - "RAW": spread 0,10 $, slippage 0,02 $;
  - "STD": spread 0,30 $, slippage 0,05 $;
  - commissione 7 $/lotto in entrambi i casi.

Risultati con 0,10 lotti per segnale, su 7 mesi:

| | Costi RAW | Costi STD |
|---|---|---|
| Combinazioni in profitto | 73 / 594 (12%) | **19 / 594 (3%)** |
| Risultato mediano | −2.359 $ | −3.468 $ |
| Combinazioni con 7 mesi su 7 positivi | 0 | 0 |
| Migliore in assoluto | +1.737 $ (PF 1,10) | +787 $ (PF 1,05) |

**Come lo seguirebbe una persona** (mercato 1 minuto dopo il segnale, una posizione per TP più un runner, BE dopo TP1, costi STD):

- 666 trade, 61% in profitto, **24% chiusi allo SL pieno**;
- **−4.320 $**, PF 0,78, drawdown massimo 4.868 $;
- **1 mese positivo su 7.**

| Mese | Trade | $ (0,10 lotti) |
|---|---|---|
| mar 2026 | 69 | −1.188 |
| apr 2026 | 95 | +362 |
| mag 2026 | 109 | −1.218 |
| giu 2026 | 125 | −294 |
| lug 2026 | 123 | −870 |
| ago 2026 | 105 | −614 |
| set 2026 (fino al 9) | 40 | −498 |

Mediana per tipo di ingresso (costi STD):

| Ingresso | Mediana |
|---|---|
| Mercato al segnale | −5.289 $ |
| Mercato all'avviso | −4.626 $ |
| Limit sul primo prezzo | −2.244 $ |
| Limit in fondo alla zona | −752 $ |

Entrare peggio del canale costa molto. Anche spostare l'orario di 2 minuti cambia il risultato da −1.840 $ a −4.940 $.

## 4. I segnali hanno un vantaggio?

- **Esecuzione ideale** (prezzo esatto del canale, all'avviso, costi zero): −1.986 $ con 0,10 lotti.
- **Lato invertito** (stessa geometria, direzione opposta): −4.312 $. Né i buy né i sell indovinano la direzione in modo utile.
- **Ingressi casuali** (stessa geometria SL/TP, minuto e direzione casuali, 300 ripetizioni): media +860 $, intervallo 5–95% da −2.815 $ a +4.453 $. **Il canale fa peggio dell'89% dei tentativi casuali.**
- **Profilo per lato:**
  - buy −5.153 $, sell +834 $ (follower, costi STD);
  - in un periodo in cui l'oro è sceso da circa 5.200 a circa 4.100, il risultato dei sell si spiega con la direzione del mercato più che con un'abilità;
  - con solo 7 mesi non si può isolare un filtro affidabile.

## 5. Conclusioni

1. **Non è profittevole da seguire.** Su 1.188 modi di seguirlo, il 97% perde con costi normali e nessuno è positivo in tutti i mesi. Le poche varianti positive hanno PF 1,05–1,10: sono le migliori su 594 tentativi, quindi in linea con il caso.
2. **La geometria è sfavorevole.** TP1 a 0,25 R con stop a 1 R richiede di vincere più dell'80% dei trade dopo i costi. Il TP1 si raggiunge il 78% delle volte, e le perdite piene (circa il 22%) cancellano i guadagni.
3. **Il canale riporta i risultati in modo parziale.** Gli stop annunciati sono circa la metà di quelli reali; i "+pips" sono cumulativi e non corrispondono al P&L di chi segue.
4. **Ricreare la strategia** come regola meccanica non ha senso: i segnali in sé non hanno un vantaggio misurabile rispetto a ingressi casuali con la stessa gestione. La parte discrezionale (allargare lo stop, tenere senza stop, chiusure manuali) non si può replicare e aumenta il rischio.
5. **Se si vuole comunque seguire,** il modo meno dannoso testato è:
   - ordini limit in fondo alla zona (scadenza 60 minuti);
   - una posizione per TP, con BE dopo TP1.

   Il risultato è circa ±0, con drawdown di oltre 1.500 $ a 0,10 lotti. Non è consigliato.

Limiti: 7 mesi di dati, feed del broker dei dati (non quello del canale), gestione manuale non replicabile, prezzi M1 OHLC con convenzione prudente (stop prima dei target nella stessa barra).
