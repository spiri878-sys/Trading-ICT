//+------------------------------------------------------------------+
//|                                          AIGL_Ricostruito.mq5    |
//| Ricostruzione della logica VISIBILE di "AI Golden Life MT5"      |
//| dai report del tester dell'utente (output/phase23):              |
//|  - una sola posizione alla volta (OrdersMax=1);                  |
//|  - si decide all'apertura di ogni barra H1, nelle ore operative  |
//|    (lun-gio 08-22, ven 08-20 ora server);                        |
//|  - direzione CONTRO la media: BUY se l'ultima H1 chiusa e' sotto |
//|    la EMA10, SELL se e' sopra (98,6% delle operazioni originali);|
//|  - ingresso a mercato dopo EntryDelaySec secondi (originale:     |
//|    10-20 s), solo se nei primi secondi il prezzo non si e' mosso |
//|    oltre MaxDeviationUSD dall'apertura (filtro volatilita' 150   |
//|    punti / 10 s dell'originale) e se lo spread e' basso;         |
//|  - TP e SL fissi di 5 $ (TakeProfit=50 / StopLoss=50).           |
//| Filtro notizie: usa il calendario MT5 dal vivo (nel tester il    |
//| calendario non esiste, quindi li' non filtra niente).            |
//| NON ricostruita: la scelta "speciale" delle ore dell'originale,  |
//| che nei dati non segue nessuna regola visibile (vedi report).    |
//+------------------------------------------------------------------+
#property copyright "Ricostruzione per uso personale - progetto Trading-ICT"
#property version   "1.00"
#property strict

#include <Trade\Trade.mqh>
#include <Trade\PositionInfo.mqh>

input double FixedLot        = 0.01;   // Lotto fisso
input double TP_USD          = 5.0;    // Take profit (dollari di prezzo)
input double SL_USD          = 5.0;    // Stop loss (dollari di prezzo)
input int    EmaPeriod       = 10;     // EMA della direzione (H1)
input int    EntryDelaySec   = 10;     // Secondi dopo l'apertura dell'ora prima di entrare
input double MaxDeviationUSD = 1.50;   // Movimento massimo nei primi secondi (filtro volatilita')
input double MaxSpreadUSD    = 0.50;   // Spread massimo (MaxSpread=50 punti)
input int    StartHour       = 8;      // Ora di inizio (server)
input int    EndHour         = 22;     // Ora di fine lun-gio (server)
input int    FridayEndHour   = 20;     // Ora di fine venerdi'
input int    TradeDirection  = 0;      // 0 = buy e sell, 1 = solo buy, 2 = solo sell
input bool   UseNewsFilter   = true;   // Filtro notizie USD/EUR ad alto impatto (solo dal vivo)
input int    NewsBeforeMin   = 90;     // Minuti prima della notizia
input int    NewsAfterMin    = 90;     // Minuti dopo la notizia
input long   MagicNumber     = 439778; // Magic number
input int    SlippagePts     = 10;     // Slippage massimo (punti)

CTrade        trade;
CPositionInfo pos;
int      hEma;
datetime barTime = 0;
double   firstPrice = 0, maxDev = 0;
bool     done = false;

int OnInit()
{
   trade.SetExpertMagicNumber(MagicNumber);
   trade.SetDeviationInPoints(SlippagePts);
   trade.SetTypeFillingBySymbol(_Symbol);
   hEma = iMA(_Symbol, PERIOD_H1, EmaPeriod, 0, MODE_EMA, PRICE_CLOSE);
   return hEma == INVALID_HANDLE ? INIT_FAILED : INIT_SUCCEEDED;
}

void OnDeinit(const int reason) { IndicatorRelease(hEma); }

bool HasPosition()
{
   for(int i = PositionsTotal() - 1; i >= 0; i--)
      if(pos.SelectByIndex(i) && pos.Symbol() == _Symbol && pos.Magic() == MagicNumber) return true;
   return false;
}

bool InSession(datetime t)
{
   MqlDateTime d; TimeToStruct(t, d);
   if(d.day_of_week == 0 || d.day_of_week == 6) return false;
   int end = d.day_of_week == 5 ? FridayEndHour : EndHour;
   return d.hour >= StartHour && d.hour < end;
}

bool NewsNear(datetime now)
{
   if(!UseNewsFilter || MQLInfoInteger(MQL_TESTER)) return false;
   string cur[2] = {"USD", "EUR"};
   for(int c = 0; c < 2; c++)
   {
      MqlCalendarValue v[];
      if(CalendarValueHistory(v, now - NewsAfterMin * 60, now + NewsBeforeMin * 60, NULL, cur[c]) <= 0) continue;
      for(int i = 0; i < ArraySize(v); i++)
      {
         MqlCalendarEvent e;
         if(CalendarEventById(v[i].event_id, e) && e.importance == CALENDAR_IMPORTANCE_HIGH) return true;
      }
   }
   return false;
}

void OnTick()
{
   datetime h1 = iTime(_Symbol, PERIOD_H1, 0);
   double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID), ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
   if(h1 != barTime) { barTime = h1; firstPrice = bid; maxDev = 0; done = false; }
   if(done) return;
   maxDev = MathMax(maxDev, MathAbs(bid - firstPrice));
   datetime now = TimeCurrent();
   if(now < barTime + EntryDelaySec) return;
   done = true;                                       // una sola decisione per ora

   if(!InSession(barTime) || HasPosition()) return;
   if(maxDev > MaxDeviationUSD) { Print("AIGL ricostruito: volatilita' alta, salto"); return; }
   if(ask - bid > MaxSpreadUSD) { Print("AIGL ricostruito: spread alto, salto"); return; }
   if(NewsNear(now)) { Print("AIGL ricostruito: notizia vicina, salto"); return; }

   double e[];
   ArraySetAsSeries(e, true);
   if(CopyBuffer(hEma, 0, 1, 1, e) <= 0) return;
   double c1 = iClose(_Symbol, PERIOD_H1, 1);
   int dir = c1 < e[0] ? 1 : (c1 > e[0] ? -1 : 0);   // contro la media
   if(dir == 0 || (TradeDirection == 1 && dir < 0) || (TradeDirection == 2 && dir > 0)) return;

   if(dir > 0)
      trade.Buy(FixedLot, _Symbol, ask, NormalizeDouble(ask - SL_USD, _Digits), NormalizeDouble(ask + TP_USD, _Digits), "AIGLR BUY");
   else
      trade.Sell(FixedLot, _Symbol, bid, NormalizeDouble(bid + SL_USD, _Digits), NormalizeDouble(bid - TP_USD, _Digits), "AIGLR SELL");
}
//+------------------------------------------------------------------+
