# Menu input della PRIME — come appare nel materiale (Fase 1)

**Fonti:**
- `VID-XAU` = `output/video/xau_prime1/note.md`, fotogramma s_00008 (1,7 s), XAUUSD PRIME 1;
- `VID-EUR` = eur_macro_1k ed eur_dal2005;
- `VID-NASM` = nas_macro, p_00018 (51 s), orologio 20/08/2026;
- `VID-NASS` = nas_steroid, s_00005 (0,5 s), orologio 31/08/2026;
- `E-13` = lettura precedente del video XAU (registro delle evidenze).

Etichette **verbatim**; nelle etichette originali ci sono emoji, qui omesse. Il file dell'EA è `Advisors\ICT RAPTOR AI PRIME - AUTOTRADER FOREX CLUB - 000000.ex5` (VID-NASS, scheda Settings).

**Osservazione chiave:** il menu della PRIME è **di alto livello**. Non ci sono rischio %, lotti, SL/TP, ATR, orari né celle: tutto è "interno" al **SET** (V5: "oltre 160 parametri per cella sigillati").

## A. Menu PRIME osservato (ordine dello schermo)

| # | Gruppo | Etichetta | Valore nei video | Alternative viste (Start/Stop) | Fonte | Nome interno (riga di commento sul grafico) |
|---|---|---|---|---|---|---|
| 0 | (intestazione) | AUTOTRADER FOREX CLUB | atfc@gmail.com | | VID-XAU | — |
| 1 | IMPOSTAZIONI PRINCIPALI | BE + PARZIALE LIBERA IL POSTO (false = conteggio normale) | true | false/true | VID-XAU, EUR, NASM, NASS | InpBEP_LiberaPosto |
| 2 | | PREMIUM (false = celle originali, come ora) | false | false/true | tutti | InpPremium |
| 3 | | PREMIUM: quale livello | PREMIUM A (solo ENTER) | … PREMIUM A++ (ENTER + MAIN + SEC… (troncato) | tutti | InpPremiumLiv (=0) |
| 4 | | MERCATO | XAUUSD | XAUUSD / NAS100 / EURUSD | tutti | InpAIPair (EUR=2, NAS=1) |
| 5 | | MODALITA OPERATIVA | LIVE ACCOUNT | PROP CHALLENGE / PROP FUNDED / LIVE ACCOUNT / FLIP | tutti | InpModalita (LIVE=3) |
| 6 | | SET | XAUUSD PRIME 1 | (interno), XAUUSD PRIME 1/2, NAS PRIME 1/2, EURUSD PRIME 1/2, PRIME MACRO XAU/NAS/EUR | tutti | InpConfig (EUR dal 2005 = 10; NAS PRIME 1 = 0) |
| 7 | | STOP MINIMO IN ATR (0 = spento) | 0.0 | | **solo VID-NASS** (versione più recente) | InpStopMinATR |
| 8 | | LEVA DEL CONTO | 1:100 | 1:100 … 1:30 | VID-XAU, EUR, NASM (assente in NASS) | InpLeva |
| 9 | | VALORE CONTRATTO INDICI | 0.0 | | VID-XAU, NASM, NASS | InpV11_ContrattoIndici |
| 10 | | MAGIC NUMBER | 999000 (NASS: 0) | | tutti | InpMagicNumber |
| 11 | PROP CHALLENGE | CAPITALE DELLA CHALLENGE | 0.0 | | VID-XAU, NASM | InpPF_Capitale (?) |
| 12 | | QUANTO SPINGERE | EQUILIBRATO (NASS: AGGRESSIVO) | AGGRESSIVO / EQUILIBRATO / PRUDENTE | | |
| 13 | | FASE | FASE 1 | FASE 1 / FASE 2 | | |
| 14 | | TRAGUARDO FASE 1 | 10.0 | 10…100, passo 1 | | |
| 15 | | TRAGUARDO FASE 2 | 5.0 | | | |
| 16 | | LIMITE GIORNALIERO PROP | 4.0 | | | |
| 17 | | LIMITE TOTALE PROP | 10.0 | | | |
| 18 | | MISURA DEL TRAGUARDO | EQUITY | EQUITY / SALDO | | |
| 19 | | AL TRAGUARDO | CHIUDI E FERMATI | CHIUDI E FERMATI / CHIUDI E CONTINUA | | |
| 20 | | MARGINE DI SICUREZZA | 0.2 | | | |
| 21 | | LEVA IMPOSTA DALLA PROP | 1:100 | | **solo VID-NASS** | |
| 22 | PROP FUNDED | CAPITALE FINANZIATO | 0.0 | | | |
| 23 | | QUANTO SPINGERE | EQUILIBRATO | | | |
| 24 | | AVVISA AL GUADAGNO DI | 0.0 | | | |
| 25 | LIVE ACCOUNT | CAPITALE DEL CONTO | 0.0 | | | |
| 26 | | QUANTO SPINGERE | **AGGRESSIVO** | | | |
| 27 | | CRESCITA DEL LOTTO | COMPOSTO — i lotti crescono col conto | BASE FISSA — i lotti restano quelli di par… | | |
| 28 | | LEVA DEL CONTO LIVE | 1:500 (come oggi) | | **solo VID-NASS** | |
| 29 | FLIP | CAPITALE DA FLIPPARE | 0.0 | | | |
| 30 | | QUANTO SPINGERE | EQUILIBRATO | | | |
| 31 | | OBIETTIVO | 2X — RADDOPPIO | … 5X | | |
| 32 | | STOP-PIANO | 30.0 | | VID-EUR, NASM | |
| 33 | SUPERVISORE LIQBIAS | SUPERVISORE LIQBIAS (false = come certificato) | false | false/true | VID-XAU (sfocato), E-13 | |
| 34 | | SUPERVISORE: soglia 1..99 (-1 = quella della cella) | 50 (lettura incerta) | | VID-XAU, E-13 | |
| 35 | FILTRO NOTIZIE | NON OPERARE SULLE NOTIZIE | false | | VID-XAU (sfocato), E-13 | |
| 36 | | minuti PRIMA della notizia | 30 | | | |
| 37 | | minuti DOPO la notizia | 30 | | | |
| 38 | MESSAGGI GRAFICA | (contenuto non leggibile) | | | E-10 (solo intestazione) | |

**Gruppi PREMIUM e TELEGRAM:** non visti nei video. Il PREMIUM sta nelle righe 2–3; Telegram è descritto nel V5.

## B. Voci del manuale V5 non viste nel menu PRIME (da aggiungere)

| Gruppo V5 | Voce | Decisione |
|---|---|---|
| CLIENTE | Nome del cliente | Aggiungere (solo testo) |
| GENERALE E SIZING | Balance del conto | Coincide con CAPITALE DEL CONTO / CHALLENGE / FINANZIATO / DA FLIPPARE della PRIME (per modo) |
| | Moltiplicatore contratto (ON/OFF + valore) | = VALORE CONTRATTO INDICI della PRIME |
| | **Metodo sizing: RISCHIO % / LOTTO FISSO** | **Aggiungere** (richiesto dalla specifica, sezione 4) |
| | Lotti per trade | Aggiungere (default del cliente 0,10) |
| | Rischio per trade (%) | Aggiungere come override facoltativo. Default: tabella del modo e del livello |
| SELEZIONE STRATEGIA | MODALITÀ (cella), MERCATO | In PRIME la cella è implicita nel SET. Aggiungere un selettore di celle facoltativo (default: quelle del SET) |
| MACRO NEWS | Interruttore generale, No-trade, minuti prima e dopo | No-trade = FILTRO NOTIZIE della PRIME; aggiungere l'interruttore macro e lo **Scudo** |
| STOP LOSS / TAKE PROFIT | Lunghezza ATR, Moltiplicatore ATR, Target RR | Interni al SET in PRIME. Esporre solo come override avanzato, con default 0 = da SET |
| PROTEZIONE DRAWDOWN GIORNALIERO | Attiva, Unità (%/MONEY), Soglia | Aggiungere |
| FILTRO SESSIONI · GRAFICA · TELEGRAM | Filtro sessioni, Grafica (+ storico), Telegram (attiva, token, chat ID, nome, Analisi, Gestione) | Aggiungere; nessun token nel codice |

## C. Menu della prima versione (PRES p. 8), solo per riferimento

TYPE OF RISK (DYNAMIC/FIXED) · MAGIC NUMBER (7566) · SELECT STRATEGY (Breaker block / Order block / Judas swing / Ote / Po3 / Unicorn model) · USE MARKET BRAIN AI? · USE TRADE MENAGER AI? · USE STRATEGY FILTER AI? · USE MEDIATIONS? · TYPE OF MEDIATIONS (DYNAMIC/FIXED/SETUP ZONES) · MAX TRADE MEDIATIONS · USE FVG CONFIRMATION · TIMEFRAME FVG (M15/30/H1/H2) · USE TREND CONFIRMATION · TIMEFRAME TREND · SELECT TYPE TP & SL (FIXED/DYNAMIC) · POINT FIXED TP/SL · VALUE DYNAMIC TP/SL · USE TRAILING STOP · POINTS TRAILING STOP · USE DAY PROTECTION? · DROWDOWN MAX %.

Le **mediazioni sono escluse** (specifica).

## D. Proposta di menu per la ricostruzione (Fase 8)

L'ordine e le etichette di A restano identici. In coda si aggiungono le voci di B, marcate come "aggiunte V5 / specifica":
- METODO SIZING: RISCHIO % / LOTTO FISSO;
- LOTTI PER TRADE: 0.10;
- RISCHIO PER TRADE: 0 = tabella del modo;
- interruttore MACRO NEWS e SCUDO;
- DRAWDOWN GIORNALIERO;
- FILTRO SESSIONI;
- GRAFICA;
- TELEGRAM con le categorie Analisi e Gestione.

Il SET "XAUUSD PRIME 1/2" e "PRIME MACRO XAU" diventano preset interni costruiti in validazione. Gli altri mercati sono rifiutati all'avvio (fuori perimetro).
