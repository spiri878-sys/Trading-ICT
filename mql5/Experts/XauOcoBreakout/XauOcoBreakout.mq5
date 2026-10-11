//+------------------------------------------------------------------+
//|                                               XauOcoBreakout.mq5 |
//| XAUUSD OCO breakout straddle (idea of the user, refined by the   |
//| research in python/scripts/oco0*.py, report reports/OCO_REPORT.md)|
//|                                                                  |
//| Every new H1 bar, when the EA is FLAT and has no pending orders: |
//|  range  = high/low of the last 24 CLOSED H1 bars                 |
//|  only if compressed: (hi-lo) <= Compression x ATR14(H1) x sqrt(24)|
//|  and 0.5 <= (hi-lo)/ATR <= 8                                     |
//|  BUY STOP  at hi + 0.1 ATR, SL = sell level, TP = 2R             |
//|  SELL STOP at lo - 0.1 ATR, SL = buy level,  TP = 2R             |
//|  Mode REGIME (default): buy stop only if D1 close > EMA50 and the |
//|  last H4 structure break is up; sell stop only in the mirror bear |
//|  regime; no orders in a mixed regime. Mode BOTH: always both.    |
//|  Orders live for one H1 bar; when one fills the other is deleted |
//|  (OCO). After the position closes the pair is re-placed.         |
//| Management: trailing stop 2 x ATR(H1 of the setup) from the last |
//|  closed M1 close (never loosens), max 1440 M1 bars, flat on      |
//|  Friday 23:00 server.                                            |
//| NOT compiled / NOT run in MT5 by the author: demo test first.    |
//+------------------------------------------------------------------+
#property copyright "Raptor Recon research project"
#property version   "1.00"

#include <Trade\Trade.mqh>
#include <RaptorRecon\Defines.mqh>
#include <RaptorRecon\Logger.mqh>
#include <RaptorRecon\MarketModel.mqh>
#include <RaptorRecon\Risk.mqh>

enum ENUM_XOB_LOT_MODE { FIXED = 0, RISK_PERCENT = 1 };
enum ENUM_XOB_SIDES    { REGIME = 0, BOTH = 1 };

input group "=== GENERALE ==="
input long              InpMagic           = 7703001;       // Magic number
input bool              InpAllowRealAccount= false;         // Consenti conto REALE
input string            InpLogPrefix       = "XOB";         // Prefisso file CSV

input group "=== LOTTO ==="
input ENUM_XOB_LOT_MODE LotMode            = FIXED;         // LotMode: FIXED o RISK_PERCENT
input double            FixedLot           = 0.10;          // FixedLot (mai modificato dall'EA)
input double            RiskPercent        = 1.0;           // RiskPercent per trade
input ENUM_RR_RISK_BASE RiskBase           = RR_BASE_EQUITY;// Base del rischio
input double            CommissionLotSide  = 3.5;           // Commissione per lotto per lato (stima)
input double            SlipPrice          = 0.05;          // Slippage stimato (prezzo)

input group "=== PROTEZIONI ==="
input double            MaxRiskPctTrade    = 0.0;           // Tetto rischio per trade % (0 = off; ATTENZIONE con lotto fisso)
input double            DailyLossPct       = 0.0;           // Stop nuove entrate dopo perdita giornaliera % (0 = off)
input double            MaxDrawdownPct     = 0.0;           // Stop nuove entrate oltre DD % dal massimo (0 = off)
input double            MaxSpreadPrice     = 1.0;           // Spread massimo per piazzare gli ordini (prezzo)
input int               FridayCloseMin     = 1380;          // Venerdi': flat e nessun ordine dopo questo minuto server

input group "=== STRATEGIA (default = configurazione testata) ==="
input ENUM_XOB_SIDES    Sides              = REGIME;        // REGIME (perfezionata) o BOTH (idea originale)
input int               RangeBars          = 24;            // Barre H1 del range
input double            Compression        = 1.0;           // Range <= Compression x ATR x sqrt(RangeBars)
input double            BufferAtr          = 0.1;           // Distanza degli stop oltre il range (ATR)
input double            TpR                = 2.0;           // Take profit in R (0 = nessuno)
input double            TrailAtr           = 2.0;           // Trailing in ATR H1 (0 = off)
input int               MaxHoldM1Bars      = 1440;          // Durata massima (barre M1)
input int               RegimeEmaD1        = 50;            // EMA D1 del regime
input int               H4SwingK           = 2;             // Swing H4 per la struttura

CTrade          g_trade;
CRRLogger       g_log;
CRRAccountGuard g_guard;
datetime        g_last_h1 = 0, g_last_m1 = 0, g_setup_bar = 0;
double          g_setup_atr = 0;
bool            g_setup_used = true;

bool IsXauUsd()
  {
   string n = _Symbol; StringToUpper(n);
   return (StringFind(n, "XAUUSD") >= 0 || StringFind(n, "GOLD") >= 0) && SymbolInfoString(_Symbol, SYMBOL_CURRENCY_PROFIT) == "USD";
  }

int OnInit()
  {
   if(!IsXauUsd()) { Print("XauOcoBreakout: not XAUUSD -> disabled"); return INIT_FAILED; }
   if(AccountInfoInteger(ACCOUNT_TRADE_MODE) == ACCOUNT_TRADE_MODE_REAL && !InpAllowRealAccount)
     { Print("XauOcoBreakout: REAL account and InpAllowRealAccount=false -> disabled"); return INIT_FAILED; }
   if(FixedLot <= 0 || RiskPercent <= 0 || RangeBars < 3 || TrailAtr < 0) return INIT_PARAMETERS_INCORRECT;
   g_log.Init(InpLogPrefix);
   g_trade.SetExpertMagicNumber(InpMagic);
   g_trade.SetTypeFillingBySymbol(_Symbol);
   g_guard.Init(InpMagic);
   g_log.Event(StringFormat("INIT XauOcoBreakout lot=%s fixed=%.2f risk=%.2f%% sides=%s N=%d comp=%.2f tp=%.1fR trail=%.1f hold=%d margin_mode=%d",
                            LotMode == FIXED ? "FIXED" : "RISK_PERCENT", FixedLot, RiskPercent, Sides == REGIME ? "REGIME" : "BOTH",
                            RangeBars, Compression, TpR, TrailAtr, MaxHoldM1Bars, (int)AccountInfoInteger(ACCOUNT_MARGIN_MODE)));
   return INIT_SUCCEEDED;
  }

void OnDeinit(const int r) { g_log.Event(StringFormat("DEINIT %d", r)); }

int OwnPositions()
  {
   int k = 0;
   for(int i = PositionsTotal() - 1; i >= 0; i--)
     { ulong t = PositionGetTicket(i); if(t && PositionGetInteger(POSITION_MAGIC) == InpMagic && PositionGetString(POSITION_SYMBOL) == _Symbol) k++; }
   return k;
  }

void DeletePendings(const string why)
  {
   for(int i = OrdersTotal() - 1; i >= 0; i--)
     {
      ulong t = OrderGetTicket(i);
      if(t == 0 || OrderGetInteger(ORDER_MAGIC) != InpMagic || OrderGetString(ORDER_SYMBOL) != _Symbol) continue;
      if(g_trade.OrderDelete(t)) g_log.Trade("DELETE", t, "OCO", 0, 0, 0, 0, 0, 0, why);
     }
  }

int Pendings()
  {
   int k = 0;
   for(int i = OrdersTotal() - 1; i >= 0; i--)
     { ulong t = OrderGetTicket(i); if(t && OrderGetInteger(ORDER_MAGIC) == InpMagic && OrderGetString(ORDER_SYMBOL) == _Symbol) k++; }
   return k;
  }

int D1Regime()
  {
   MqlRates d[]; ArraySetAsSeries(d, false);
   int n = CopyRates(_Symbol, PERIOD_D1, 1, 600, d);
   if(n < RegimeEmaD1 + 10) return 0;
   double e[]; RREma(d, n, RegimeEmaD1, e);
   return d[n - 1].close > e[n - 1] ? 1 : (d[n - 1].close < e[n - 1] ? -1 : 0);
  }

int H4Trend()
  {
   CRRStructure s;
   if(!s.Load(_Symbol, PERIOD_H4, 1500, H4SwingK)) return 0;
   for(int i = s.n - 1; i >= 0; i--) if(s.brk[i] != 0) return s.brk[i];
   return 0;
  }

bool FridayCutoff()
  {
   MqlDateTime t; TimeToStruct(TimeCurrent(), t);
   return t.day_of_week == 5 && t.hour * 60 + t.min >= FridayCloseMin;
  }

//--- lot for a stop order at `price` with stop `sl`; false + reason if not allowed
bool LotFor(const int side, const double price, const double sl, double &lot, double &risk, string &why)
  {
   double lpl = RRLossPerLot(side, price, sl, SlipPrice, CommissionLotSide);
   if(!RRLot(LotMode == FIXED ? RR_LOT_FIXED : RR_LOT_RISK, FixedLot, RiskPercent, RiskBase, 1.0, lpl, lot, risk, why)) return false;
   if(MaxRiskPctTrade > 0 && risk > AccountInfoDouble(ACCOUNT_EQUITY) * MaxRiskPctTrade / 100.0)
     { why = StringFormat("risk %.2f > %.2f%% equity", risk, MaxRiskPctTrade); return false; }
   return RRMarginOk(side, lot, price, why);
  }

//--- place the OCO pair (or one side) from the setup of the last closed H1 bar
void PlaceSetup()
  {
   if(FridayCutoff() || OwnPositions() > 0 || Pendings() > 0) return;
   if(g_guard.MaxDdHit(MaxDrawdownPct) || g_guard.DailyLimitHit(DailyLossPct)) { g_log.Event("limit reached: no new orders"); return; }
   double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK), bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);
   if(ask - bid > MaxSpreadPrice) { g_log.Event(StringFormat("spread %.2f too high: no orders", ask - bid)); return; }
   MqlRates r[]; ArraySetAsSeries(r, false);
   int n = CopyRates(_Symbol, PERIOD_H1, 1, RangeBars + 450, r);
   if(n < RangeBars + 30) return;
   double a[]; RRAtr(r, n, 14, a);
   double atr = a[n - 1];
   if(atr == EMPTY_VALUE || atr <= 0) return;
   double hi = -DBL_MAX, lo = DBL_MAX;
   for(int j = n - RangeBars; j < n; j++) { hi = MathMax(hi, r[j].high); lo = MathMin(lo, r[j].low); }
   double h = hi - lo;
   if(h > Compression * atr * MathSqrt(RangeBars) || h / atr < 0.5 || h / atr > 8.0) return;
   bool want_buy = true, want_sell = true;
   if(Sides == REGIME)
     {
      int d1 = D1Regime(), h4 = H4Trend();
      want_buy = (d1 == 1 && h4 == 1); want_sell = (d1 == -1 && h4 == -1);
      if(!want_buy && !want_sell) return;
     }
   double p_hi = NormalizeDouble(hi + BufferAtr * atr, _Digits), p_lo = NormalizeDouble(lo - BufferAtr * atr, _Digits);
   long stops = SymbolInfoInteger(_Symbol, SYMBOL_TRADE_STOPS_LEVEL);
   // python rule: both levels must still be on the correct side of the market when (re)placed
   if((want_buy && ask >= p_hi) || (want_sell && bid <= p_lo)) return;
   datetime exp = iTime(_Symbol, PERIOD_H1, 0) + PeriodSeconds(PERIOD_H1);
   g_setup_atr = atr;
   string why; double lot, risk;
   if(want_buy && p_hi - ask >= stops * _Point)
     {
      double sl = p_lo, tp = TpR > 0 ? NormalizeDouble(p_hi + TpR * (p_hi - sl), _Digits) : 0;
      if(LotFor(1, p_hi, sl, lot, risk, why))
        {
         bool ok = g_trade.BuyStop(lot, p_hi, _Symbol, sl, tp, ORDER_TIME_SPECIFIED, exp, "XOB");
         if(!ok) ok = g_trade.BuyStop(lot, p_hi, _Symbol, sl, tp, ORDER_TIME_GTC, 0, "XOB");   // broker without expiry support
         g_log.Trade(ok ? "PLACE_BUYSTOP" : "FAIL_BUYSTOP", g_trade.ResultOrder(), "OCO", 1, lot, p_hi, sl, tp, 0,
                     StringFormat("risk %.2f retcode %d", risk, g_trade.ResultRetcode()));
        }
      else g_log.Event("buy stop rejected: " + why);
     }
   if(want_sell && bid - p_lo >= stops * _Point)
     {
      double sl = p_hi, tp = TpR > 0 ? NormalizeDouble(p_lo - TpR * (sl - p_lo), _Digits) : 0;
      if(LotFor(-1, p_lo, sl, lot, risk, why))
        {
         bool ok = g_trade.SellStop(lot, p_lo, _Symbol, sl, tp, ORDER_TIME_SPECIFIED, exp, "XOB");
         if(!ok) ok = g_trade.SellStop(lot, p_lo, _Symbol, sl, tp, ORDER_TIME_GTC, 0, "XOB");
         g_log.Trade(ok ? "PLACE_SELLSTOP" : "FAIL_SELLSTOP", g_trade.ResultOrder(), "OCO", -1, lot, p_lo, sl, tp, 0,
                     StringFormat("risk %.2f retcode %d", risk, g_trade.ResultRetcode()));
        }
      else g_log.Event("sell stop rejected: " + why);
     }
   g_setup_used = true;
  }

void ManagePositions()
  {
   MqlRates b[]; ArraySetAsSeries(b, false);
   if(CopyRates(_Symbol, PERIOD_M1, 1, 1, b) != 1) return;
   double spread = SymbolInfoInteger(_Symbol, SYMBOL_SPREAD) * _Point;
   long lim = MathMax(SymbolInfoInteger(_Symbol, SYMBOL_TRADE_STOPS_LEVEL), SymbolInfoInteger(_Symbol, SYMBOL_TRADE_FREEZE_LEVEL));
   for(int i = PositionsTotal() - 1; i >= 0; i--)
     {
      ulong t = PositionGetTicket(i);
      if(t == 0 || PositionGetInteger(POSITION_MAGIC) != InpMagic || PositionGetString(POSITION_SYMBOL) != _Symbol) continue;
      int side = PositionGetInteger(POSITION_TYPE) == POSITION_TYPE_BUY ? 1 : -1;
      double sl = PositionGetDouble(POSITION_SL), tp = PositionGetDouble(POSITION_TP);
      int held = iBarShift(_Symbol, PERIOD_M1, (datetime)PositionGetInteger(POSITION_TIME), false);
      if(FridayCutoff() || (MaxHoldM1Bars > 0 && held >= MaxHoldM1Bars))
        {
         if(g_trade.PositionClose(t)) g_log.Trade("CLOSE", t, "OCO", side, PositionGetDouble(POSITION_VOLUME), b[0].close, sl, tp, 0, FridayCutoff() ? "friday" : "max hold");
         continue;
        }
      string k = StringFormat("XOB_%I64u_atr", t);
      double atr = GlobalVariableCheck(k) ? GlobalVariableGet(k) : 0;
      if(TrailAtr <= 0 || atr <= 0) continue;
      double ref = side == 1 ? b[0].close : b[0].close + spread;
      double ns = NormalizeDouble(ref - side * TrailAtr * atr, _Digits);
      if((ns - sl) * side <= 0) continue;
      double cur = side == 1 ? SymbolInfoDouble(_Symbol, SYMBOL_BID) : SymbolInfoDouble(_Symbol, SYMBOL_ASK);
      if(MathAbs(cur - ns) < lim * _Point) continue;
      if(g_trade.PositionModify(t, ns, tp)) g_log.Trade("TRAIL", t, "OCO", side, PositionGetDouble(POSITION_VOLUME), ref, ns, tp, 0, "");
     }
  }

void OnTick()
  {
   datetime m1 = iTime(_Symbol, PERIOD_M1, 0);
   if(m1 != 0 && m1 != g_last_m1)
     {
      g_last_m1 = m1;
      ManagePositions();
      if(FridayCutoff()) DeletePendings("friday cutoff");
     }
   datetime h1 = iTime(_Symbol, PERIOD_H1, 0);
   if(h1 != 0 && h1 != g_last_h1)
     {
      g_last_h1 = h1;
      DeletePendings("expired: new H1 setup");       // orders live for one H1 bar (as in the research)
      g_setup_used = false;
     }
   if(!g_setup_used && OwnPositions() == 0 && Pendings() == 0)
      PlaceSetup();                                   // first placement of the hour or re-placement after a close
  }

void OnTradeTransaction(const MqlTradeTransaction &tr, const MqlTradeRequest &rq, const MqlTradeResult &rs)
  {
   if(tr.type != TRADE_TRANSACTION_DEAL_ADD || !HistoryDealSelect(tr.deal)) return;
   if(HistoryDealGetInteger(tr.deal, DEAL_MAGIC) != InpMagic) return;
   long entry = HistoryDealGetInteger(tr.deal, DEAL_ENTRY);
   ulong pos = (ulong)HistoryDealGetInteger(tr.deal, DEAL_POSITION_ID);
   double px = HistoryDealGetDouble(tr.deal, DEAL_PRICE), vol = HistoryDealGetDouble(tr.deal, DEAL_VOLUME);
   if(entry == DEAL_ENTRY_IN)
     {
      DeletePendings("OCO: other side cancelled");
      GlobalVariableSet(StringFormat("XOB_%I64u_atr", pos), g_setup_atr);
      g_log.Trade("OPEN", pos, "OCO", HistoryDealGetInteger(tr.deal, DEAL_TYPE) == DEAL_TYPE_BUY ? 1 : -1, vol, px, 0, 0, 0, "");
     }
   else if(entry == DEAL_ENTRY_OUT || entry == DEAL_ENTRY_OUT_BY)
     {
      double net = HistoryDealGetDouble(tr.deal, DEAL_PROFIT) + HistoryDealGetDouble(tr.deal, DEAL_COMMISSION) + HistoryDealGetDouble(tr.deal, DEAL_SWAP);
      g_log.Trade("CLOSED", pos, "OCO", 0, vol, px, 0, 0, net, "");
      g_guard.OnClosedTrade(net);
      GlobalVariableDel(StringFormat("XOB_%I64u_atr", pos));
      g_setup_used = false;                          // re-place the pair after the trade (same H1 setup)
     }
  }
//+------------------------------------------------------------------+
