# Rapporto finale — macchina scommesse calcio (17/10/2026)

Piano: `football/PIANO_MACCHINA.md`, punti 0-14. Legenda: FATTO / PARZIALE / ESCLUSO (con il perché).

## 0. Regole di lavoro — FATTO
Piccoli passi, commit frequenti, chiave mai nel repository, contatore richieste (95/giorno API-Football,
480/giorno odds-api.io), nessuna informazione dal futuro (test automatico `tests/test_noleak.py`).

## 1. Dati
- 1.1 Archivio — FATTO: 248.059 partite fino al 16/10/2026, 38 campionati (22 europei con angoli/tiri/falli/
  cartellini; 16 extra solo gol). Doppioni 0, valori assurdi corretti, tabella nomi `data/team_alias.json`.
  Russia ferma al 2/8 (fonte).
- 1.2 Statistiche da API — ESCLUSO: piano gratuito solo 2022-2024 e 1 richiesta a partita (mesi di quota per una
  stagione). Non serve: football-data ha già angoli, tiri, falli, cartellini.
- 1.3 Infortuni/formazioni — PARZIALE: `ricontrollo.py` (formazioni ufficiali, turnover, portiere) pronto ma non
  collaudato (account API sospeso). Peso dei singoli assenti: escluso (troppe richieste nel piano gratuito).
- 1.4 Quote storiche — FATTO: Bet365, massima, media, Pinnacle prima e chiusura, arbitro (Inghilterra/Scozia).

## 2. Feature — FATTO
Forze dinamiche per 8 statistiche, medie veloci/lente/campo/stagione/stagione precedente, classifica e distanze,
riposo, partite ravvicinate, neopromosse, arbitro, Pinnacle, Elo, motore gol: 233 feature, solo passato.

## 3. Modelli — FATTO
10 statistiche (gol, 1° e 2° tempo, angoli, falli, gialli, rossi, cartellini giallo1/rosso2, tiri, tiri in porta),
3-5 approcci ciascuna, walk-forward 2019-2026. Vince LightGBM ovunque; per i gol LightGBM + mercato. Distribuzioni
complete (Poisson/binomiale negativa/binomiale) -> ~90 mercati API dalla stessa distribuzione, coerenti tra loro.
Calibrazione per fasce, solo fuori campione, pesata sugli anni recenti.

## 4. Cancello di qualità — FATTO
Tabella completa: `output/m4_mercati.md`. **197 tipi di giocata ammessi su 248.**
- NON ammessi: quasi tutti i pari/dispari (non battono la media), falli ospite O/U (calibrazione 1,7% > 1,5%),
  tiri handicap europeo ospite, "tempo con più gol", e **1X2 + Over/Under 2,5 gol perché il backtest a quote
  Bet365 non è in utile** (−0,9% su 161 giocate; utile solo alla quota massima del mercato, +3,6% su 1.191).
- Precisione 1X2 alla pari con Pinnacle (non lo batte).
- Angoli, cartellini, falli, tiri: calibrati e migliori della media in tutte o quasi le stagioni, ma "profitto
  non ancora provato" (nessuna quota storica): li giudica il registro reale.

## 5. Regole di scelta — FATTO
SUPER CECCHINO (p≥80%, v≥5%), CECCHINO (p≥70%, v≥5%), VALORE (p≥55%, v≥8%), +2 punti sui mercati non provati,
quota ≥1,30, una per partita, singole. Trappole: valore >25%, distanza >10 punti dal riferimento (Pinnacle /
Betfair Exchange, escluso il rimborso), squadre con pochi dati. Valore SOLO su Bet365 (scelta dell'utente).
Fasce dal backtest (quota massima): 70-75% +4,7%, 75-80% +0,7%, ≥80% +8,5% (solo 33 giocate). A Bet365 nessuna
fascia è chiaramente in utile: **soglia consigliata: restare a CECCHINO 70%**; il SUPER CECCHINO ha troppi pochi
casi per dire che è meglio.

## 6. Uscita giornaliera — FATTO (collaudo completo con dati salvati)
`oggi.py` (top assoluta, top angoli, top per mercato, elenchi per livello, sospetti, motivi, quota minima,
andamento quota), `analizza.py "Squadra"` (pre-partita / live / finita).

## 7. Live — PARZIALE
Modello sul tempo che resta (ritmo, punteggio, espulsioni) in `live.py`/`analizza.py`. NON verificabile sul
passato (mancano dati minuto per minuto) e senza dati live finché l'API è sospesa (odds-api.io non dà il live gratis).

## 8. Registro e bilancio — FATTO
Registro automatico, esiti (vinta/persa/rimborso/mezza), CLV contro la chiusura, bilancio per mercato, livello,
campionato, fascia di valore e di probabilità (`esiti.py`, `output/bilancio.md`).

## 9. Automazione — DA FARE
Attività pianificate mattina/sera con notifica: le creo appena una fonte quote funziona e tu confermi.

## 10. Controlli del codice — FATTO
9 test: anti-futuro, coerenza probabilità (somme, Over+Under, linee a quarti, handicap asiatico con quote vere),
lettura di tutti i mercati API, nomi squadra pericolosi (es. Gimnasia Mendoza / La Plata). Semi fissi.

## 11. Ricostruzione — FATTO
`bash football/scripts/rebuild_all.sh` (circa 2 ore) e `CLAUDE.md` aggiornato.

## 12. Rapporto finale — questo documento.

## 13. Informazioni extra
- xG — ESCLUSO per ora: solo da questa stagione (2 mesi), non verificabile.
- Movimento quote — FATTO: storico Pinnacle prima/chiusura: mercato a favore ROI +9,1% (217 giocate), fermo −4,7%,
  contro +4,8%: segnale debole; mostrato come avviso, non come filtro.
- Assenti pesati, pressione live, meteo — ESCLUSI: servono dati API non disponibili gratis.

## 14. Revisione finale
1. Bookmaker utente (Bet365) — FATTO. 2. Coppe — ESCLUSO: nessuna partita di coppa nell'archivio per verificarle.
3. Limiti di sicurezza — RIMOSSI su richiesta. 4. Notifiche — con le attività pianificate (punto 9).
5. Messaggi chiari se qualcosa fallisce — FATTO. 6. Regole di conteggio — FATTO per i cartellini (giallo 1,
rosso 2; i mercati "gialli" contano solo i gialli); da confermare sugli esiti reali (su Bologna-Inter il modello
vedeva più cartellini di Pinnacle: il filtro li ha bloccati). 7. Extra API (H2H, allenatore, ecc.) — ESCLUSO per
ora (API). 8. Mercati sui giocatori — ESCLUSO (servono statistiche dei giocatori). 9. SUPER CECCHINO e fasce —
FATTO. 10. Pari/dispari su tutti i conteggi — FATTO (verificato: non ammesso, non batte la media).
11. Andamento quote — FATTO (istantanee + avviso). 12. Calendario/contesto — PROVATO: nessun miglioramento
(gol −0,01%, angoli −0,01%): NON entra. 13. Ricontrollo formazioni — PRONTO, da collaudare.

## Fonte quote
API-Football: account sospeso. Alternativa pronta: odds-api.io (gratis, 500 richieste/giorno, Bet365 + Betfair
Exchange, angoli e cartellini). Serve la chiave nella variabile `ODDS_API_IO_KEY` dell'ambiente "Calcio".

## Promemoria
Importi piccoli e fissi, solo singole. Nessuna giocata è sicura: il vantaggio, se c'è, è di pochi punti percentuali
e si vede solo su centinaia di giocate.
