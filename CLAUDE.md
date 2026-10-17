# Passaggio di consegne (leggere per primo)

L'utente scrive in italiano, dal telefono. Vuole risposte dirette e pratiche, senza farlo lavorare: le cose le fai tu.
Il lavoro attivo è il progetto **calcio** (`football/`). Il progetto trading (oro, `python/`, `mql5/`) è in pausa.
Branch di lavoro: `claude/gifted-cannon-3ud35m` (commit e push lì, niente PR se non chiesta).

## Cosa vuole l'utente (calcio)
- Ogni giorno, PRE-PARTITA, **la giocata top**: in primo luogo sugli **angoli** (totali, casa, ospite, Over/Under),
  se serve anche altri mercati. Deve trovare tu partite e quote (API-Football), lui va e gioca.
- Stile "cecchino": poche giocate, solo quando probabilità alta E quota con valore. Una giocata per partita,
  singole (mai multiple di giocate legate). Importi piccoli e fissi: ricordaglielo, ha già perso soldi nel trading.
- Onestà: nessun modello "non sbaglia mai". Dai sempre probabilità e valore (p x quota - 1).

## Stato attuale (17/10/2026)
- Archivio partite: `football/data/raw/Matches.csv` (fonte e hash in `football/data/manifest.json`), FINISCE il
  2026-09-03. Da aggiornare con football-data.co.uk (CSV stagione 2627, es. mmz4281/2627/I1.csv) o con API-Football.
- `football/data/raw`, `football/data/cache`, `football/models` NON sono nel repository: in una sessione nuova vanno
  ricreati (vedi sotto).
- Ambiente cloud **"Calcio"**: rete aperta + segreto di rete per `v3.football.api-sports.io` (header
  `x-apisports-key`, il proxy lo inserisce). Prima prova: `curl https://v3.football.api-sports.io/status`. Se risponde
  errore di autenticazione, il segreto è stato salvato con prefisso "Bearer": dillo all'utente (prefisso va vuoto).
  MAI scrivere la chiave nel repository o nei log.

## Ricostruire tutto in una sessione nuova (ordine)
1. Scarica `Matches.csv` (e `EloRatings.csv`) dall'URL in `football/data/manifest.json` in `football/data/raw/`.
2. (Se possibile) aggiungi le partite dal 2026-09-03 a oggi da football-data.co.uk o API-Football.
3. `python football/scripts/f1_goals_eval.py` → cache motore gol
4. `python football/scripts/f2_features.py` → feature
5. `python football/scripts/f2_model.py` → previsioni walk-forward (servono alla calibrazione)
6. `python football/scripts/f3_corners_cards.py` → angoli/gialli base
7. `python football/scripts/f5_train_final.py` → modelli finali + calibratori in `football/models/`
8. `python football/scripts/f6_corners.py` → feature angoli + valutazione (lungo, ~15 min; in background)
9. `python football/scripts/f6_train_final.py` → modelli angoli F6 (casa, ospite, totale)
10. `python football/scripts/f7_team_corners.py` → dispersioni e correzione di scala per angoli casa/ospite

## Strumenti pronti
- `football/scripts/oggi.py [data]`: partite del giorno + quote migliori (API-Football) → modello → lista giocate
  (CECCHINO p>=70% e valore>=5%; VALORE p>=55% e valore>=8%), una per partita. Salva `football/output/giocate_<data>.md`.
  Mai testato con l'API vera: verifica i nomi dei mercati angoli restituiti da /odds (funzione `best_odds` in
  `football/fb/apifootball.py`) e il collegamento nomi squadre (`match_team`).
- `football/scripts/scheda.py "Casa" "Ospite" DIV data [1=.. X=.. 2=.. ang_o9.5=.. casa_u4.5=.. osp_o3.5=..]`: scheda
  completa di una partita con valore delle quote inserite.
- `football/scripts/listino.py data "DIV:Casa:Ospite" ...`: quote minime angoli senza quote (fallback).
- Registro previsioni vs risultati: `football/output/registro_partite.csv` (aggiornalo con i risultati che manda).

## Risultati chiave (onesti)
- 1X2/gol: il modello è quasi al livello di Bet365 ma non lo batte da solo; il valore c'era solo con la quota
  migliore tra molti bookmaker.
- Angoli: per squadra (corr ~0.31-0.32) molto più prevedibili del totale (~0.19). Probabilità ben calibrate
  (`football/output/f7_team_corners_eval.json`). Con p>=70% le giocate escono ~75-78% storicamente.
- Giocate dal vivo del 17/10 da verificare: Ipswich O2.5, Fulham O8.5, Brentford O6.5, Elche O2.5,
  Villarreal U5.5 angoli; pre-partita Bologna-Inter: Inter Under 5.5 angoli @1.72.
