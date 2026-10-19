//+------------------------------------------------------------------+
//|                                                 ZonaRecupero.mq5 |
//| Zone recovery (hedging alternato) sull'oro M1, fase 30.          |
//| Una sequenza alla volta:                                         |
//|  - apre BUY (o il lato della tendenza EMA200 H1 se StartMode=1)  |
//|    quando non c'e' uno strappo in corso;                         |
//|  - zona larga ZoneUSD sotto il BUY (sopra il SELL);              |
//|  - se il prezzo attraversa l'altro bordo apre il lato opposto    |
//|    con il lotto che porta tutta la sequenza in guadagno di       |
//|    TargetUSD x lotto iniziale quando il prezzo esce dalla zona   |
//|    di TargetUSD da quel lato; avanti cosi' fino a MaxFlips;      |
//|  - chiude tutto quando il prezzo esce dalla zona di TargetUSD    |
//|    (sopra il bordo alto o sotto il bordo basso).                 |
//| Nessuno stop. Nella simulazione su candele M1 (zona 1 $, uscita  |
//| 8 $, 12 inversioni) tutti i 10 mesi del 2026 positivi su 5.000,  |
//| ma la zona e' piu' piccola di una candela M1: la simulazione non |
//| e' affidabile, decide il tester con "ogni tick su tick reali".   |
//| Serve un conto HEDGING. NON compilato dall'autore.               |
//+------------------------------------------------------------------+
#property copyright "Progetto Trading-ICT - uso personale"
#property version   "1.00"

#include <Trade\Trade.mqh>
#include <Trade\PositionInfo.mqh>

input double InpLot           = 0.01;    // Lotto iniziale
input double InpZoneUSD       = 1.0;     // Larghezza della zona ($)
input double InpTargetUSD     = 8.0;     // Uscita oltre la zona ($)
input int    InpMaxFlips      = 12;      // Posizioni massime della sequenza
input int    InpStartMode     = 0;       // 0 = parte sempre BUY, 1 = lato della tendenza EMA200 H1
input int    InpTrendEMA      = 200;     // EMA della tendenza (H1)
input int    InpCalmBars      = 15;      // Barre M1 controllate per lo strappo
input double InpCalmATR       = 6.0;     // Strappo = escursione >= ATR M1(14) x questo
input double InpMaxSpreadUSD  = 0.30;    // Spread massimo per aprire
input long   InpMagic         = 200301;  // Magic number
input int    InpSlippage      = 20;      // Slippage (punti)

CTrade        trade;
CPositionInfo pos;
int    hEma = INVALID_HANDLE, hAtr = INVALID_HANDLE;
double top = 0, bot = 0;                 // bordi della zona della sequenza in corso
datetime lastWarn = 0;

int OnInit()
{
   if(AccountInfoInteger(ACCOUNT_MARGIN_MODE) != ACCOUNT_MARGIN_MODE_RETAIL_HEDGING)
   {
      Print("ZonaRecupero: serve un conto HEDGING");
      return INIT_FAILED;
   }
   trade.SetExpertMagicNumber(InpMagic);
   trade.SetDeviationInPoints(InpSlippage);
   trade.SetTypeFillingBySymbol(_Symbol);
   hEma = iMA(_Symbol, PERIOD_H1, InpTrendEMA, 0, MODE_EMA, PRICE_CLOSE);
   hAtr = iATR(_Symbol, PERIOD_M1, 14);
   if(hEma == INVALID_HANDLE || hAtr == INVALID_HANDLE) return INIT_FAILED;
   return INIT_SUCCEEDED;
}

void OnDeinit(const int reason)
{
   IndicatorRelease(hEma);
   IndicatorRelease(hAtr);
   Comment("");
}

double NormLot(double v)
{
   double st = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
   double mn = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN), mx = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX);
   v = MathCeil(v / st - 1e-9) * st;                  // per eccesso: il recupero deve bastare
   return NormalizeDouble(MathMax(mn, MathMin(mx, v)), 8);
}

//--- stato della sequenza: lotti e prezzo medio dei BUY e dei SELL, ultimo lato aperto, inversioni
struct SSeq
{
   int      n;
   double   lb, wb, ls, ws;
   int      last;                         // 1 = ultimo BUY, -1 = ultimo SELL
   double   firstPx;
   int      firstType;
};

void Scan(SSeq &q)
{
   q.n = 0; q.lb = 0; q.wb = 0; q.ls = 0; q.ws = 0; q.last = 0; q.firstPx = 0; q.firstType = 0;
   datetime tl = 0, tf = D'3000.01.01';
   for(int k = PositionsTotal() - 1; k >= 0; k--)
   {
      if(!pos.SelectByIndex(k) || pos.Symbol() != _Symbol || pos.Magic() != InpMagic) continue;
      q.n++;
      bool b = pos.PositionType() == POSITION_TYPE_BUY;
      if(b) { q.lb += pos.Volume(); q.wb += pos.Volume() * pos.PriceOpen(); }
      else  { q.ls += pos.Volume(); q.ws += pos.Volume() * pos.PriceOpen(); }
      if(pos.Time() >= tl) { tl = pos.Time(); q.last = b ? 1 : -1; }
      if(pos.Time() < tf) { tf = pos.Time(); q.firstPx = pos.PriceOpen(); q.firstType = b ? 1 : -1; }
   }
}

void CloseAll()
{
   for(int k = PositionsTotal() - 1; k >= 0; k--)
      if(pos.SelectByIndex(k) && pos.Symbol() == _Symbol && pos.Magic() == InpMagic)
         trade.PositionClose(pos.Ticket());
}

bool Open(int dir, double lot, string c)
{
   double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK), bid = SymbolInfoDouble(_Symbol, SYMBOL_BID), m;
   ENUM_ORDER_TYPE t = dir > 0 ? ORDER_TYPE_BUY : ORDER_TYPE_SELL;
   if(!OrderCalcMargin(t, _Symbol, lot, dir > 0 ? ask : bid, m) || m > AccountInfoDouble(ACCOUNT_MARGIN_FREE))
   {
      if(TimeCurrent() - lastWarn > 600) { Print("ZonaRecupero: margine insufficiente per ", lot); lastWarn = TimeCurrent(); }
      return false;
   }
   return dir > 0 ? trade.Buy(lot, _Symbol, ask, 0, 0, c) : trade.Sell(lot, _Symbol, bid, 0, 0, c);
}

//--- 1 = parte BUY, -1 = parte SELL, 0 = aspetta (strappo o spread)
int StartSide()
{
   double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK), bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);
   if(ask - bid > InpMaxSpreadUSD) return 0;
   double a[], e[];
   if(CopyBuffer(hAtr, 0, 1, 1, a) < 1) return 0;
   int hi = iHighest(_Symbol, PERIOD_M1, MODE_HIGH, InpCalmBars, 1), lo = iLowest(_Symbol, PERIOD_M1, MODE_LOW, InpCalmBars, 1);
   if(hi < 0 || lo < 0) return 0;
   if(iHigh(_Symbol, PERIOD_M1, hi) - iLow(_Symbol, PERIOD_M1, lo) >= InpCalmATR * a[0]) return 0;
   if(InpStartMode == 0) return 1;
   if(CopyBuffer(hEma, 0, 1, 1, e) < 1) return 0;
   return bid > e[0] ? 1 : -1;
}

void OnTick()
{
   double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK), bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);
   SSeq q;
   Scan(q);
   if(q.n == 0)
   {
      int dir = StartSide();
      if(dir != 0 && Open(dir, NormLot(InpLot), "ZR 1"))
      {
         if(dir > 0) { top = ask; bot = top - InpZoneUSD; }
         else        { bot = bid; top = bot + InpZoneUSD; }
      }
      Comment("ZonaRecupero: in attesa");
      return;
   }
   if(top == 0)                                       // ripartenza dell'EA con una sequenza aperta
   {
      if(q.firstType > 0) { top = q.firstPx; bot = top - InpZoneUSD; }
      else                { bot = q.firstPx; top = bot + InpZoneUSD; }
   }
   double up = top + InpTargetUSD, dn = bot - InpTargetUSD;
   if(bid >= up || ask <= dn) { CloseAll(); top = 0; bot = 0; return; }

   double lot0 = NormLot(InpLot);
   if(q.n < InpMaxFlips)
   {
      if(q.last > 0 && bid <= bot)                    // scende sotto la zona: SELL che recupera all'uscita in basso
      {
         double need = InpTargetUSD * lot0 + q.lb * (q.wb / q.lb - dn) - (q.ls > 0 ? q.ls * (q.ws / q.ls - dn) : 0);
         Open(-1, NormLot(MathMax(lot0, need / InpTargetUSD)), StringFormat("ZR %d", q.n + 1));
      }
      else if(q.last < 0 && ask >= top)               // sale sopra la zona: BUY che recupera all'uscita in alto
      {
         double need = InpTargetUSD * lot0 + q.ls * (up - q.ws / q.ls) - (q.lb > 0 ? q.lb * (up - q.wb / q.lb) : 0);
         Open(1, NormLot(MathMax(lot0, need / InpTargetUSD)), StringFormat("ZR %d", q.n + 1));
      }
   }
   Comment(StringFormat("ZonaRecupero: %d posizioni, BUY %.2f lotti, SELL %.2f lotti\nzona %s - %s, uscite %s / %s",
                        q.n, q.lb, q.ls, DoubleToString(bot, _Digits), DoubleToString(top, _Digits),
                        DoubleToString(dn, _Digits), DoubleToString(up, _Digits)));
}
//+------------------------------------------------------------------+
