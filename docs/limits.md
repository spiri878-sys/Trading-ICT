# Limiti noti e attività non completate

1. **MQL5 mai compilato né eseguito**: il container non ha MetaEditor, Wine né lo Strategy Tester. Servono la compilazione e il backtest su Windows (`docs/mt5_guide.md`).
2. **Fonti ufficiali non aperte direttamente**: autotraderforexclubea.com, YouTube e archive.org sono bloccati dalla policy di rete dell'ambiente. Per accedervi va aggiunto il dominio negli *Allowed domains* dell'ambiente cloud. Le regole interne del prodotto restano **NON DISPONIBILI**.
3. **Dati**:
   - mancano le barre M5 2005–2017 dichiarate;
   - nessun tick reale, nessun ask;
   - lo spread 2018–22 ha unità incerta;
   - nessun calendario economico storico, quindi il motore macro PRIME (E-02) è NON RIPRODUCIBILE e il filtro notizie non è backtestabile.
4. **Simulatore OHLC M1**:
   - ordine intrabar ignoto (assunzione pessimistica);
   - nessuna latenza né swap;
   - P&L in USD (il capitale "1000 €" è trattato come 1000 USD).
5. **Uso del test set**: è stato aperto per misurare le baseline. Un nuovo candidato richiede dati nuovi (dopo ottobre 2026) o lo storico 2005–2017.
6. **Non implementati**:
   - monitor fuori scala (E-29);
   - Monte Carlo a blocchi (E-30), non significativo senza un'aspettativa positiva;
   - Order Block come cella autonoma;
   - livelli Premium A…A++;
   - modalità prop / funded / flip.
7. **Parità EA ↔ Python non verificata**: lo strumento esiste, ma mancano i log reali. Differenza nota: l'EA ricostruisce la struttura sulle ultime 1000 barre, il simulatore su tutto lo storico.
8. **Telegram e filtro notizie**: scritti ma non testati; nel tester non possono funzionare.
9. **Ora server**: si assume server = NY + 7 h (come nel feed analizzato). Va verificata sul proprio broker tramite `InpNyOffsetHours`.
10. **Nessuna garanzia di redditività**: i test condotti indicano il contrario per tutte le varianti testate. **Non usare su un conto reale.**
