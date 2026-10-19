//+------------------------------------------------------------------+
//|                                       BRT_Pro_Migliorato.mq5     |
//| Breakout Retest Pro v2.0 MIGLIORATO (ricerca: output/phase21).   |
//| Grafico H1, XAUUSD. Solo ACQUISTI, solo con trend rialzista      |
//| (D1 e H4 sopra la EMA50, su barre chiuse).                       |
//|  1. swing high confermato (5 barre per lato) su una barra con     |
//|     ampiezza >= 1,5 ATR14 = neckline;                            |
//|  2. rottura: 2 chiusure consecutive sopra la neckline;           |
//|  3. retest entro 40 barre: minimo entro 1 ATR dalla neckline,    |
//|     candela rialzista che chiude sopra -> BUY a mercato;         |
//|  4. SL 1 ATR, TP 8 ATR, chiusura dopo 72 barre H1. Una posizione. |
//| Correzioni rispetto all'originale: scadenza del retest che       |
//| funziona, niente uscita "inversione" (peggiorava), slippage       |
//| tollerato 30 punti, riempimento automatico, lotto fisso.         |
//| Simulazione 2016-2026 positiva, 2010-2015 leggermente negativa:  |
//| dipende molto dal rialzo dell'oro. NON compilato dall'autore:     |
//| prima prova in DEMO.                                              |
//+------------------------------------------------------------------+
#property copyright "Ricostruzione e test: progetto Trading-ICT"
#property version   "1.00"
#property strict

#include <Trade\Trade.mqh>
#include <Trade\PositionInfo.mqh>

input int    SwingLength    = 5;      // Barre per lato dello swing
input double ImpulseMult    = 1.5;    // Ampiezza minima della barra pivot (ATR)
input int    BreakConfirm   = 2;      // Chiusure sopra la neckline per la rottura
input double RetestATR      = 1.0;    // Zona di retest (ATR)
input int    RetestBars     = 40;     // Barre massime per il retest
input double SL_ATR         = 1.0;    // Stop loss (ATR)
input double TP_ATR         = 8.0;    // Take profit (ATR)
input int    MaxHoldBars    = 72;     // Chiusura dopo N barre del grafico
input double FixedLot       = 0.01;   // Lotto fisso
input int    SlippagePts    = 30;     // Slippage massimo (punti)
input double MaxSpreadPrice = 0.50;   // Spread massimo per entrare (prezzo)
input long   MagicNumber    = 2026101;// Magic number
input bool   AllowReal      = false;  // Consenti conto REALE (prima la demo)

CTrade        trade;
CPositionInfo pos;
int    hATR, hEmaD1, hEmaH4;
double neck = 0;
bool   broke = false, waiting = false;
int    brokeAge = 0;

int OnInit()
{
   if(!AllowReal && AccountInfoInteger(ACCOUNT_TRADE_MODE) == ACCOUNT_TRADE_MODE_REAL)
   {
      Print("BRT migliorato: conto REALE bloccato (AllowReal=false). Prova prima in demo.");
      return INIT_FAILED;
   }
   trade.SetExpertMagicNumber(MagicNumber);
   trade.SetDeviationInPoints(SlippagePts);
   trade.SetTypeFillingBySymbol(_Symbol);
   hATR   = iATR(_Symbol, PERIOD_CURRENT, 14);
   hEmaD1 = iMA(_Symbol, PERIOD_D1, 50, 0, MODE_EMA, PRICE_CLOSE);
   hEmaH4 = iMA(_Symbol, PERIOD_H4, 50, 0, MODE_EMA, PRICE_CLOSE);
   if(hATR == INVALID_HANDLE || hEmaD1 == INVALID_HANDLE || hEmaH4 == INVALID_HANDLE) return INIT_FAILED;
   return INIT_SUCCEEDED;
}

void OnDeinit(const int reason)
{
   IndicatorRelease(hATR); IndicatorRelease(hEmaD1); IndicatorRelease(hEmaH4);
}

double Buf(int h, int shift)
{
   double b[];
   ArraySetAsSeries(b, true);
   if(CopyBuffer(h, 0, shift, 1, b) <= 0) return 0;
   return b[0];
}

bool MyPosition(ulong &ticket)
{
   for(int i = PositionsTotal() - 1; i >= 0; i--)
      if(pos.SelectByIndex(i) && pos.Symbol() == _Symbol && pos.Magic() == MagicNumber)
      { ticket = pos.Ticket(); return true; }
   return false;
}

bool BullRegime()
{
   double ed = Buf(hEmaD1, 1), eh = Buf(hEmaH4, 1);
   if(ed <= 0 || eh <= 0) return false;
   return iClose(_Symbol, PERIOD_D1, 1) > ed && iClose(_Symbol, PERIOD_H4, 1) > eh;
}

void OnTick()
{
   static datetime last = 0;
   datetime cur = iTime(_Symbol, PERIOD_CURRENT, 0);
   if(cur == last) return;
   last = cur;

   // uscita per tempo
   ulong tk;
   if(MyPosition(tk))
   {
      int age = iBarShift(_Symbol, PERIOD_CURRENT, (datetime)pos.Time());
      if(age >= MaxHoldBars) trade.PositionClose(tk);
   }

   double atr = Buf(hATR, 1);
   if(atr <= 0) return;
   int L = SwingLength;

   // 1. nuova neckline: pivot alla barra L+1 (confermata dalle L barre successive, tutte chiuse)
   double ph = iHigh(_Symbol, PERIOD_CURRENT, L + 1);
   bool pivot = true;
   for(int k = 1; k <= 2 * L + 1 && pivot; k++)
      if(k != L + 1 && iHigh(_Symbol, PERIOD_CURRENT, k) > ph) pivot = false;
   if(pivot && ph - iLow(_Symbol, PERIOD_CURRENT, L + 1) >= atr * ImpulseMult)
   { neck = ph; broke = false; waiting = false; }

   // 2. rottura confermata
   if(neck > 0 && !broke)
   {
      int above = 0;
      for(int k = 1; k <= BreakConfirm; k++) if(iClose(_Symbol, PERIOD_CURRENT, k) > neck) above++;
      if(above >= BreakConfirm) { broke = true; waiting = true; brokeAge = -1; }   // il retest può arrivare già su questa barra
   }

   // 3. retest e ingresso
   if(waiting && neck > 0)
   {
      brokeAge++;
      if(brokeAge > RetestBars) { waiting = false; neck = 0; return; }
      double l1 = iLow(_Symbol, PERIOD_CURRENT, 1), c1 = iClose(_Symbol, PERIOD_CURRENT, 1), o1 = iOpen(_Symbol, PERIOD_CURRENT, 1);
      bool inZone = l1 >= neck - atr * RetestATR && l1 <= neck + atr * RetestATR;
      if(inZone && c1 > neck && c1 > o1)
      {
         waiting = false; neck = 0;
         if(MyPosition(tk) || !BullRegime()) return;
         double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK), bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);
         if(ask - bid > MaxSpreadPrice) { Print("BRT migliorato: spread troppo alto, salto"); return; }
         double sl = NormalizeDouble(ask - atr * SL_ATR, _Digits);
         double tp = NormalizeDouble(ask + atr * TP_ATR, _Digits);
         if(!trade.Buy(FixedLot, _Symbol, ask, sl, tp, "BRT migliorato"))
            Print("BRT migliorato: ordine rifiutato ", trade.ResultRetcode());
      }
   }
}
//+------------------------------------------------------------------+
