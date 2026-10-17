# PIANO COMPLETO — "Macchina da guerra" scommesse calcio (pre-partita + live)

Obiettivo: ogni giorno la giocata statisticamente migliore su TUTTI i mercati, scelta perché la quota paga più della
probabilità vera (valore), non perché è l'esito scontato. Costruito bene, verificato sul passato, nessuna scorciatoia.
Non c'è fretta per le partite di oggi: priorità alla qualità.

## 0. Regole di lavoro (obbligatorie)
- Lavora a piccoli passi: file brevi, un passo alla volta, dopo ogni passo scrivi in chat 1-2 righe su cosa hai fatto.
  Mai più di 5 minuti senza un aggiornamento. Lavori lunghi (addestramenti) in background, con log controllati.
- Commit e push frequenti sul branch `claude/gifted-cannon-3ud35m`. Dati grezzi, cache e modelli restano fuori dal
  repository (.gitignore) ma devono essere ricostruibili con uno script unico (punto 11).
- Mai stampare, salvare o committare la chiave API. La chiave arriva dal segreto di rete dell'ambiente "Calcio".
- Quota API: piano gratuito ~100 richieste al giorno. Metti tutto in cache, conta le richieste, non sprecarle. Se il
  piano non basta, dimmelo con i numeri (quante richieste servono al giorno) PRIMA di proporre un piano a pagamento.
- Zero informazioni dal futuro (look-ahead): ogni feature usa solo dati precedenti alla partita.
- Scrivi in italiano, semplice, dal telefono. Risultati onesti, anche se negativi.

## 1. Dati
1. Archivio storico: aggiorna `football/data/raw/Matches.csv` fino a ieri con football-data.co.uk (tutti i campionati
   principali e quelli "extra") e con API-Football. Elimina doppioni, allinea i nomi delle squadre (tabella di
   corrispondenza salvata nel repository), controlla buchi e valori assurdi.
2. Statistiche per partita da API-Football (fixtures/statistics) per i mercati che football-data non ha o ha incompleti:
   falli, tiri, tiri in porta, angoli, cartellini, fuorigioco, possesso; anche arbitro (campo referee) e formazioni.
   Scaricale con criterio (quota limitata): prima le stagioni recenti dei campionati principali.
3. Infortuni/squalifiche (injuries) e formazioni (lineups) per le partite del giorno, quando disponibili.
4. Quote storiche: usa quelle di football-data (1X2, O/U 2.5, handicap asiatico; Bet365, Pinnacle, massimo e media) per
   il backtest dei soldi. Per gli altri mercati le quote storiche non ci sono: vedi punto 4.

## 2. Feature (tutte solo dal passato)
- Forze dinamiche attacco/difesa per gol, tiri, tiri in porta, angoli, falli, cartellini (motore tipo Poisson online).
- Medie mobili 5/10 partite e medie esponenziali, separate casa/fuori, fatti e subiti; media della stagione in corso e
  della precedente; quote "fatto/subito" (es. quota di angoli e tiri sul totale).
- Elo, forma, punti per partita, giorni di riposo, partite ravvicinate (coppe europee infrasettimanali), neopromosse,
  giornata e importanza della partita (lotta titolo/salvezza a fine stagione), derby.
- Arbitro: media cartellini e falli fischiati (fondamentale per cartellini e falli), con pochi dati usa la media.
- Mercato: probabilità implicite pre-partita (soprattutto Pinnacle, il bookmaker più preciso), margine, linea
  handicap; dove l'API dà le linee di angoli/cartellini/falli, usale come informazione.
- Livello del campionato e media del campionato recente.

## 3. Modelli: TUTTI i mercati che hanno quote nell'API
Mercati: 1X2, doppia chance, draw no bet, handicap asiatico ed europeo, Over/Under gol (0.5-5.5), gol per squadra,
Gol/NoGol, multigol, pari/dispari, risultato esatto, primo tempo (1X2, O/U, Gol/NoGol), parziale/finale, angoli
(totali, casa, ospite, handicap, 1X2 angoli, primo tempo), cartellini (totali, per squadra, punti cartellino), falli
(totali, per squadra), tiri e tiri in porta (totali, per squadra), fuorigioco se ci sono quote, e qualsiasi altro mercato
presente nelle risposte dell'API (fai l'elenco completo dei nomi dei mercati che arrivano e coprili tutti).
- Per i conteggi (gol, angoli, falli, tiri, cartellini) stima la DISTRIBUZIONE completa per casa e ospite (Poisson,
  binomiale negativa, bivariata/con correlazione) e ricava tutte le linee e le combinazioni dalla stessa distribuzione,
  così le probabilità sono coerenti tra loro.
- Per ogni mercato confronta almeno 3 approcci (es. modello statistico classico, LightGBM, combinazione dei due /
  combinazione con il mercato) e tieni il migliore sul periodo di verifica, non su quello di addestramento.
- Validazione walk-forward stagione per stagione (addestra sul passato, verifica sulla stagione dopo), come nel trading.
- Calibrazione (isotonica o Platt) stimata solo su previsioni fuori campione.

## 4. Cancello di qualità: un mercato entra nella classifica SOLO se
1. è calibrato: quando dice X%, sul passato esce ~X% (tabella per fasce, errore di calibrazione basso);
2. batte la media del campionato (log-loss e Brier) e, dove ci sono quote storiche, si avvicina o batte Pinnacle;
3. è stabile: migliore della media in almeno il 70% delle stagioni di verifica;
4. dove esistono quote storiche: backtest dei soldi positivo nel periodo di verifica (regole del punto 5 decise su un
   periodo precedente, poi applicate senza ritocchi) usando le quote reali, non la quota giusta.
Mercati senza quote storiche (angoli, falli, tiri, cartellini): ammessi solo se superano 1-3, marcati "profitto non
ancora provato", con soglie più severe, e valutati dal registro reale (punto 8).
Alla fine dammi una tabella: mercato, modello scelto, calibrazione, confronto con la media e con il mercato, stagioni
positive, ROI del backtest (se possibile), AMMESSO / NON AMMESSO.

## 5. Regole di scelta delle giocate
- Per ogni partita e ogni giocata: probabilità del modello, quota MIGLIORE tra tutti i bookmaker dell'API, valore =
  probabilità x quota - 1, quota minima = 1.05 / probabilità.
- CECCHINO: probabilità >= 70% e valore >= 5%. VALORE: probabilità >= 55% e valore >= 8%. Quota minima assoluta 1.30.
- Filtro trappole: valore > 25% = SOSPETTO (non va in top); forte disaccordo con Pinnacle = sospetto; squadre con
  pochi dati recenti o neopromosse senza storico = escluse; infortuni/squalifiche importanti o formazioni anomale
  (turnover) = ricalcola o escludi.
- Una sola giocata per partita (la migliore), sempre singole, mai combinare giocate legate tra loro.
- Verifica sul backtest che le soglie scelte rendano davvero; se una fascia (mercato, campionato, valore) perde,
  restringila.

## 6. Uscita giornaliera (script unico, es. `python football/scripts/oggi.py`)
- Partite del giorno di tutti i campionati coperti, quote di tutti i bookmaker, modelli, filtri.
- Messaggio in chat + file `football/output/giocate_<data>.md` con:
  1. TOP ASSOLUTA del giorno (qualsiasi mercato);
  2. TOP ANGOLI;
  3. top per ogni altro mercato ammesso (gol, 1X2, cartellini, falli, tiri...);
  4. elenco completo CECCHINO e VALORE.
  Per ogni giocata: ora, campionato, partita, cosa giocare, quota migliore e bookmaker, probabilità, valore, quota
  minima, validità live ("valida fino al 10' se 0-0 e angoli Inter <= 1"), 2-3 motivi chiave in parole semplici
  (es. "Inter in trasferta fa pochi angoli, il Bologna in casa ne concede pochi, arbitro severo"), livello di fiducia.
- Se non c'è niente con valore: scrivi "oggi nessuna giocata", non forzare.

## 7. Live
- Per le partite analizzate pre-partita e ora in corso: minuto, punteggio, angoli, cartellini, falli, tiri,
  espulsioni dall'API (fixtures live, statistics); ricalcola le probabilità sul tempo che resta (previsione pre-partita
  + ritmo osservato con peso moderato + effetto punteggio); confronta con le quote live se il piano le dà, altrimenti
  dai la quota minima. Comando semplice tipo `python football/scripts/live.py`.

## 8. Registro e bilancio reale
- Salva automaticamente ogni giocata proposta (con quota e bookmaker al momento) in `football/output/registro_giocate.csv`.
- Il giorno dopo scarica i risultati dall'API e segna vinta/persa.
- Calcola il CLV: la quota presa contro la quota di chiusura Pinnacle (se battiamo la chiusura con costanza, il
  vantaggio è vero anche quando i risultati vanno male per sfortuna).
- Bilancio a importo fisso (1 unità): totale, per mercato, per livello, per campionato, per fascia di valore; ogni
  settimana un riepilogo. Restringi automaticamente ciò che perde dopo un numero sufficiente di giocate.

## 9. Automazione
- Attività pianificata ogni mattina (ora italiana, es. 10:00) che aggiorna dati e quote, lancia oggi.py e mi manda la
  lista; una la sera (es. 23:30) che controlla i risultati e aggiorna il bilancio. Riaddestramento completo ogni
  settimana. Chiedimi conferma prima di creare le attività pianificate.

## 10. Controlli di qualità del codice
- Test per: lettura delle quote dell'API (tutti i nomi dei mercati), corrispondenza nomi squadre, assenza di
  informazioni dal futuro, coerenza delle probabilità (somme a 1, Over+Under = 1).
- Semi casuali fissi, risultati riproducibili.

## 11. Ricostruzione e passaggio di consegne
- Script unico `football/scripts/rebuild_all.sh` che ricostruisce da zero dati, feature e modelli nell'ordine giusto.
- Aggiorna `CLAUDE.md` alla fine di ogni fase con stato, risultati e comandi.

## 12. Rapporto finale (quando tutto è pronto)
- Tabella dei mercati (punto 4), risultati del backtest, prima lista giornaliera reale, cosa manca e perché.
- Promemoria all'utente: importi piccoli e fissi, singole, nessuna giocata è sicura.
