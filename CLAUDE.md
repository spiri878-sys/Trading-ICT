# Passaggio di consegne (leggere per primo)

L'utente scrive in italiano, dal telefono. Vuole risposte dirette e pratiche, senza farlo lavorare: le cose le fai tu.
Il lavoro attivo è il progetto **calcio** (`football/`). Il progetto trading (oro, `python/`, `mql5/`) è in pausa.
Branch di lavoro: `claude/gifted-cannon-3ud35m` (commit e push lì, niente PR se non chiesta). Piano completo:
`football/PIANO_MACCHINA.md` (punti 0-14): seguilo, piccoli passi, aggiornamento in chat dopo ogni passo.

## Cosa vuole l'utente
- Ogni giorno la giocata statisticamente migliore su TUTTI i mercati (angoli in primo piano), pre-partita, con valore
  (p x quota - 1) e probabilità; livelli SUPER CECCHINO (p>=80%, v>=5%), CECCHINO (p>=70%, v>=5%), VALORE (p>=55%,
  v>=8%); mercati senza quote storiche: soglie +2 punti. Una giocata per partita, singole. Importo fisso (1 unità).
  Limiti di sicurezza (max giocate/stop) RIMOSSI su sua richiesta.
- Gioca SOLO su **Bet365** (`football/data/bookmakers.json`): il valore si calcola sulla quota Bet365; Pinnacle e gli
  altri servono come riferimento e filtro trappole.
- Onestà: risultati veri anche se negativi.

## Stato (17/10/2026 sera)
- **API-Football: account SOSPESO** dalle ~15:40 del 17/10 ("Your account is suspended", dashboard.api-football.com).
  L'utente deve sistemarlo. Prova: `curl https://v3.football.api-sports.io/status`. Piano gratuito: partite solo
  ieri/oggi/domani, stagioni storiche 2022-2024, quote 1 richiesta per partita, 100 richieste/giorno (tetto 95 nel
  codice, contatore in data/cache/api/contatore.json). MAI scrivere la chiave nel repository o nei log.
- **Fonte quote alternativa odds-api.io** (`fb/oddsapiio.py`): gratis, 100 richieste/ora (500/giorno), 2 bookmaker
  (Bet365 + Betfair Exchange come riferimento al posto di Pinnacle), 138 mercati calcio (angoli, cartellini, più
  tiri/falli...), solo pre-partita. Chiave nella variabile d'ambiente `ODDS_API_IO_KEY` (ambiente "Calcio"): se c'è,
  `oggi.py` la usa da sola. Al primo uso: `python -c "import sys; sys.path.insert(0,'football'); from fb import
  oddsapiio as o; print(o.select_books())"` e verifica i nomi delle leghe (`league_div`) e dei mercati sulla risposta
  vera (DA COLLAUDARE). Esiti delle sue giocate: dall'archivio football-data (dopo `f0_update.py`).
- **Risultati e statistiche (anche live) gratis da ESPN** (`fb/espn.py`, nessuna chiave): `esiti.py` lo usa per
  primo; `analizza.py` lo usa per stato/minuto/angoli live e per trovare la partita se API-Football non risponde.
  Fonte non ufficiale: statistiche ESPN possono differire di poco da quelle dei bookmaker.
- Archivio aggiornato al 16/10/2026: 248.059 partite, 38 campionati (22 europei con angoli/tiri/falli/cartellini, 16
  extra solo gol). Pinnacle/media/arbitro da football-data (`data/raw/extra_odds.csv`).
- `data/raw`, `data/cache`, `models` NON sono nel repository: si ricreano con `bash football/scripts/rebuild_all.sh`
  (~2 ore, log in football/output/rebuild.log).

## Sistema (nuovo, fasi M2-M7)
- `fb/state.py` feature di squadra in un passaggio (solo passato, test in tests/test_noleak.py); `fb/feats.py`
  tabella completa (arbitro, Pinnacle, Elo, motore gol).
- `fb/models.py` approcci A classico / B LightGBM / C media / D mercato / E LightGBM+mercato; `scripts/m3_walkforward.py`
  walk-forward 2019-2026 per finestre luglio-giugno.
- `fb/dist.py` distribuzioni (Poisson / binomiale negativa / binomiale); `fb/markets.py` traduttore di ~90 mercati
  API (ATTENZIONE: handicap asiatico API lato ospite = linea della casa, già corretto e testato).
- `fb/gate.py` + `scripts/m4_gate.py` cancello: scelta 2019-21, verifica 2022-26, calibrazione per fasce pesata sugli
  anni recenti, confronto con la media del campionato, stabilità >= 70% stagioni, miglioramento minimo 0,2%.
  `scripts/m4_money.py` backtest soldi 1X2/OU2.5 (ROI per bookmaker in models/m4_money.json);
  `scripts/m4_movement.py` andamento quote; `scripts/m4_report.py` -> output/m4_mercati.md (tabella dei mercati).
- `scripts/m5_train_final.py` modelli finali; `fb/predict.py`, `fb/picks.py`, `fb/teams.py` (nomi, data/team_map.json).

## Comandi giornalieri
- `python football/scripts/oggi.py [data]` giocate del giorno -> output/giocate_<data>.md + registro.
- `python football/scripts/analizza.py "Inter"` una partita (pre-partita / live / finita).
- `python football/scripts/ricontrollo.py` ~60' prima: formazioni ufficiali, turnover, valore ricalcolato.
- `python football/scripts/live.py` partite del registro in corso (live NON verificato sul passato).
- `python football/scripts/esiti.py` esiti, CLV, bilancio -> output/bilancio.md.
- Mai collaudati con l'API attiva: oggi.py completo, ricontrollo.py, live.py, esiti.py.

## Risultati chiave (onesti, verifica 2022-2026)
- 1X2/gol: il modello è alla pari con Pinnacle (log-loss 0,9990 vs 0,9993). Backtest: +6% solo alla quota massima del
  mercato (e in calo: 2025-26 negativi), -10% a Bet365 -> per l'utente 1X2 e O/U 2,5 NON ammessi.
- Angoli, falli, gialli, cartellini, tiri: calibrati e migliori della media in tutte le stagioni, ma "profitto non
  ancora provato" (nessuna quota storica): li giudica il registro reale.
- Pari/dispari: quasi sempre NON ammesso (non batte la media).
- Movimento quote Pinnacle a favore: ROI +9% contro ~0% (campione piccolo): usato come avviso.

## Da fare
- Riattivare l'API e collaudare tutta la catena giornaliera; attività pianificate mattina/sera con notifica (chiedere
  conferma all'utente prima di crearle).
- Coppe (manca storico per verificarle), xG (solo da questa stagione), extra API (H2H, allenatore, giocatori,
  infortuni pesati), mercati sui giocatori, calendario/contesto (14.12): entrano solo se migliorano la verifica.
