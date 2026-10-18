# Metodo "movimento della linea asiatica" (verifica 2019-2026, football-data.co.uk, 48.135 partite)

| Come si gioca | Giocate | ROI Bet365 | Anni positivi |
|---|---|---|---|
| Linea spostata >= 0,25, si segue la squadra DOPO (chiusura) | 18.072 | circa -3% | 0/7 |
| Linea spostata >= 0,25, si segue la squadra PRIMA (quota vecchia) | 18.072 | +5,7% | 7/7 |
| Linea spostata >= 0,5, PRIMA | 1.086 | +20% (massimo teorico) | 7/7 |
| Linea spostata >= 0,5, DOPO | 1.086 | circa 0% | 3-4/7 |
| Contro il movimento | - | da -2% a -9% | quasi mai |

Conclusione: il movimento è un segnale vero, ma il valore esiste solo prendendo la quota vecchia su un bookmaker lento
(Bet365) mentre i mercati veloci (Pinnacle, Betfair, asiatici) si sono già mossi. Serve una fonte in tempo reale con
Bet365 + un riferimento veloce (odds-api.io: Bet365 + Betfair Exchange; oppure API Betfair). Il +20% è un limite
superiore: sul passato il movimento è noto in anticipo, nella realtà si prende a metà strada.

## Miglioramenti provati (2019-2026, quota d'apertura Bet365, 20.509 giocate)
- Dimensione dello spostamento: 0,25 -> +4,4% (19.277); 0,5 -> +18,5% (1.146); 0,75+ -> +34,6% (86, pochi casi). Leva principale.
- Verso favorita o sfavorita: nessuna differenza (+5,1% / +5,4%).
- Top 5 campionati o altri: nessuna differenza vera (+4,8% / +5,4%).
- Con il modello AI d'accordo: +6,3% (contro +4,4% in disaccordo); AI d'accordo + spostamento >= 0,5: +21,1% su 707, 8/8 anni.
Regola proposta per il livello MOVIMENTO: spostamento >= 0,5 della linea asiatica sul mercato veloce (Pinnacle/Betfair/
asiatici) + Bet365 ancora alla linea vecchia + modello AI d'accordo. Valori = limite superiore (prezzo d'apertura).
