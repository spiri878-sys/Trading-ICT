//+------------------------------------------------------------------+
//|                                               XauTrendRegime.mq5 |
//| XAUUSD-only multi-timeframe trend EA selected by the quantitative |
//| research in this repository (reports/FINAL_REPORT_XAU.md).        |
//|                                                                  |
//| Rules (identical to python/scripts/final_candidate.py):          |
//|  H4 : close of the last closed bar > highest high of the 55 bars  |
//|       before it, and the previous close was not above that level |
//|  D1 : last closed D1 close > EMA(50) of D1 closes      (regime)   |
//|  H4 : direction of the last H4 structure break (swing k=2) = up   |
//|  Stop  : signal close - 3 x ATR14(H4, Wilder)                     |
//|  Exit  : trailing stop 3 x ATR14(H4, at entry) on closed M1 bars, |
//|          max holding 5 days of trading bars (7200 M1 bars)        |
//|  SHORT : exact mirror, available but OFF by default: it lost in  |
//|          every tested variant (36/36) on XAUUSD 2018-2026.        |
//|                                                                  |
//| Research results are SIMULATIONS (Python, M1 OHLC). This EA has  |
//| NOT been compiled or run in MT5 by the author: demo test first.  |
//+------------------------------------------------------------------+
#property copyright "Raptor Recon research project"
#property version   "1.00"

#include <Trade\Trade.mqh>
#include <RaptorRecon\Defines.mqh>
#include <RaptorRecon\Logger.mqh>
#include <RaptorRecon\MarketModel.mqh>
#include <RaptorRecon\Risk.mqh>

enum ENUM_XTR_LOT_MODE
  {
   FIXED        = 0, // Lotto fisso
   RISK_PERCENT = 1  // Rischio percentuale
  };

input group "=== GENERALE ==="
input long               InpMagic            = 7702001;          // Magic number
input bool               InpAllowRealAccount = false;            // Consenti conto REALE
input string             InpLogPrefix        = "XTR";            // Prefisso file CSV

input group "=== LOTTO ==="
input ENUM_XTR_LOT_MODE  LotMode             = RISK_PERCENT;     // LotMode: FIXED o RISK_PERCENT
input double             FixedLot            = 0.01;             // FixedLot (modalita' FIXED, mai modificato dall'EA)
input double             RiskPercent         = 1.0;              // RiskPercent per trade (modalita' RISK_PERCENT)
input ENUM_RR_RISK_BASE  RiskBase            = RR_BASE_EQUITY;   // Base del rischio: balance o equity
input double             CommissionLotSide   = 3.5;              // Commissione per lotto per lato (stima rischio)
input double             SlipPrice           = 0.05;             // Slippage stimato sullo stop (prezzo)

input group "=== RISCHIO E PROTEZIONI ==="
input double             MaxAggregateRiskPct = 3.0;              // Rischio aggregato massimo % (tutte le posizioni dell'EA)
input int                MaxPositions        = 1;                // Posizioni contemporanee massime (ricerca: 1)
input double             MaxRiskPctTrade     = 2.0;              // Tetto rischio stimato per trade % (vale anche per lotto fisso)
input double             DailyLossPct        = 3.0;              // Stop nuove entrate dopo perdita giornaliera % (0 = off)
input double             MaxDrawdownPct      = 20.0;             // Stop nuove entrate oltre questo DD da massimo % (0 = off)
input int                MaxConsecLosses     = 0;                // Pausa dopo N perdite consecutive (0 = off; non validato)
input int                PauseHours          = 24;               //   durata della pausa (ore)
input double             MaxSpreadPrice      = 1.0;              // Spread massimo per entrare (prezzo USD)
input int                DeviationPoints     = 30;               // Slippage massimo ordine a mercato (punti)

input group "=== STRATEGIA (default = configurazione validata) ==="
input bool               AllowLong           = true;             // Abilita LONG
input bool               AllowShort          = false;            // Abilita SHORT (sconsigliato: negativo nei test)
input int                DonchianBars        = 55;               // Barre H4 del breakout
input int                AtrPeriod           = 14;               // Periodo ATR H4 (Wilder; ricerca = 14)
input double             StopAtr             = 3.0;              // Stop iniziale in ATR H4
input double             TrailAtr            = 3.0;              // Trailing in ATR H4 (0 = off)
input int                MaxHoldM1Bars       = 7200;             // Durata massima in barre M1 (7200 = 5 giorni di trading)
input bool               UseRegimeFilter     = true;             // Filtro regime D1 EMA + struttura H4
input int                RegimeEmaD1         = 50;               // EMA D1 del filtro di regime
input int                H4SwingK            = 2;                // Swing H4 per la struttura (barre per lato)

CTrade          g_trade;
CRRLogger       g_log;
CRRAccountGuard g_guard;
datetime        g_last_h4 = 0, g_last_m1 = 0;
double          g_pending_atr = 0;   // ATR of the order being sent, stored on fill for the trailing stop

//+------------------------------------------------------------------+
bool IsXauUsd()
  {
   string n = _Symbol; StringToUpper(n);
   return (StringFind(n, "XAUUSD") >= 0 || StringFind(n, "GOLD") >= 0) &&
          SymbolInfoString(_Symbol, SYMBOL_CURRENCY_PROFIT) == "USD";
  }

string Gk(const string k) { return StringFormat("XTR_%I64d_%s", InpMagic, k); }
double Gv(const string k, const double d) { return GlobalVariableCheck(Gk(k)) ? GlobalVariableGet(Gk(k)) : d; }
void   Sv(const string k, const double v) { GlobalVariableSet(Gk(k), v); }

int OnInit()
  {
   if(!IsXauUsd()) { Print("XauTrendRegime: symbol ", _Symbol, " is not XAUUSD -> disabled"); return INIT_FAILED; }
   if(AccountInfoInteger(ACCOUNT_TRADE_MODE) == ACCOUNT_TRADE_MODE_REAL && !InpAllowRealAccount)
     { Print("XauTrendRegime: REAL account and InpAllowRealAccount=false -> disabled"); return INIT_FAILED; }
   if(FixedLot <= 0 || RiskPercent <= 0 || StopAtr <= 0 || DonchianBars < 5 || AtrPeriod < 2 || MaxPositions < 1)
     { Print("XauTrendRegime: invalid inputs"); return INIT_PARAMETERS_INCORRECT; }
   g_log.Init(InpLogPrefix);
   g_trade.SetExpertMagicNumber(InpMagic);
   g_trade.SetDeviationInPoints(DeviationPoints);
   g_trade.SetTypeFillingBySymbol(_Symbol);
   g_guard.Init(InpMagic);
   long mm = AccountInfoInteger(ACCOUNT_MARGIN_MODE);
   g_log.Event(StringFormat("INIT XauTrendRegime %s account=%s lot=%s fixed=%.2f risk=%.2f%% base=%s N=%d ATR=%d stop=%.1f trail=%.1f hold=%d regime=%s long=%s short=%s tick_size=%g tick_value=%g vol_min=%g step=%g stops=%d freeze=%d",
                            _Symbol, (mm == ACCOUNT_MARGIN_MODE_RETAIL_HEDGING ? "HEDGING" : "NETTING/EXCHANGE"),
                            (LotMode == FIXED ? "FIXED" : "RISK_PERCENT"), FixedLot, RiskPercent, (RiskBase == RR_BASE_EQUITY ? "equity" : "balance"),
                            DonchianBars, AtrPeriod, StopAtr, TrailAtr, MaxHoldM1Bars, (UseRegimeFilter ? "on" : "off"),
                            (AllowLong ? "on" : "off"), (AllowShort ? "on" : "off"),
                            SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE), SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE),
                            SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN), SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP),
                            (int)SymbolInfoInteger(_Symbol, SYMBOL_TRADE_STOPS_LEVEL), (int)SymbolInfoInteger(_Symbol, SYMBOL_TRADE_FREEZE_LEVEL)));
   if(AllowShort)
      g_log.Event("WARNING: SHORT enabled. In research the short mirror lost in 36/36 tested variants.");
   return INIT_SUCCEEDED;
  }

void OnDeinit(const int r) { g_log.Event(StringFormat("DEINIT %d", r)); }

//--- our positions on this symbol and their aggregate money risk (distance entry->SL, via OrderCalcProfit)
int OwnPositions(double &risk_money)
  {
   int k = 0; risk_money = 0;
   for(int i = PositionsTotal() - 1; i >= 0; i--)
     {
      ulong t = PositionGetTicket(i);
      if(t == 0 || PositionGetInteger(POSITION_MAGIC) != InpMagic || PositionGetString(POSITION_SYMBOL) != _Symbol) continue;
      k++;
      double sl = PositionGetDouble(POSITION_SL), op = PositionGetDouble(POSITION_PRICE_OPEN), v = PositionGetDouble(POSITION_VOLUME);
      bool buy = PositionGetInteger(POSITION_TYPE) == POSITION_TYPE_BUY;
      double p = 0;
      if(sl > 0 && OrderCalcProfit(buy ? ORDER_TYPE_BUY : ORDER_TYPE_SELL, _Symbol, v, op, sl, p) && p < 0) risk_money += -p;
     }
   return k;
  }

//--- other EAs / manual positions on a NETTING account would merge with ours: refuse to trade then
bool ForeignPositionOnNetting()
  {
   if(AccountInfoInteger(ACCOUNT_MARGIN_MODE) == ACCOUNT_MARGIN_MODE_RETAIL_HEDGING) return false;
   if(!PositionSelect(_Symbol)) return false;
   return PositionGetInteger(POSITION_MAGIC) != InpMagic;
  }

//--- direction of the last H4 structure break (+1/-1/0), closed bars only
int H4Trend()
  {
   CRRStructure s;
   if(!s.Load(_Symbol, PERIOD_H4, 1500, H4SwingK)) return 0;
   for(int i = s.n - 1; i >= 0; i--)
      if(s.brk[i] != 0) return s.brk[i];
   return 0;
  }

//--- D1 regime: +1 if last closed D1 close > EMA, -1 if below, 0 if unknown
int D1Regime()
  {
   MqlRates d[]; ArraySetAsSeries(d, false);
   int n = CopyRates(_Symbol, PERIOD_D1, 1, 600, d);
   if(n < RegimeEmaD1 + 10) return 0;
   double e[]; RREma(d, n, RegimeEmaD1, e);
   return d[n - 1].close > e[n - 1] ? 1 : (d[n - 1].close < e[n - 1] ? -1 : 0);
  }

//--- signal on the last CLOSED H4 bar: +1 long breakout, -1 short breakout, 0 none; returns ATR and close
int Signal(double &atr, double &close)
  {
   MqlRates r[]; ArraySetAsSeries(r, false);
   int need = DonchianBars + AtrPeriod + 400;              // long window: Wilder ATR converges to the full-history value
   int n = CopyRates(_Symbol, PERIOD_H4, 1, need, r);    // r[n-1] = last closed H4 bar
   if(n < DonchianBars + AtrPeriod + 5) return 0;
   double a[]; RRAtr(r, n, AtrPeriod, a);
   int i = n - 1;
   double hi = -DBL_MAX, lo = DBL_MAX;
   for(int j = i - DonchianBars; j < i; j++) { hi = MathMax(hi, r[j].high); lo = MathMin(lo, r[j].low); }
   atr = a[i]; close = r[i].close;
   if(atr == EMPTY_VALUE || atr <= 0) return 0;
   if(r[i].close > hi && r[i - 1].close <= hi) return 1;
   if(r[i].close < lo && r[i - 1].close >= lo) return -1;
   return 0;
  }

void Reject(const string why, const int side)
  {
   RRSignal s; s.bar_time = iTime(_Symbol, PERIOD_H4, 1); s.side = side; s.market = true; s.price = 0; s.sl_struct = 0;
   s.atr = 0; s.expiry_bars = 1; s.cell = "TREND_REGIME"; s.reason = "";
   g_log.Signal(s, "rejected", why, "ATR", (LotMode == FIXED ? "FIXED" : "RISK_PERCENT"), 0, 0, 0,
                SymbolInfoDouble(_Symbol, SYMBOL_ASK) - SymbolInfoDouble(_Symbol, SYMBOL_BID));
  }

void TryEntry()
  {
   double atr = 0, close = 0;
   int sig = Signal(atr, close);
   if(sig == 0) return;
   if((sig == 1 && !AllowLong) || (sig == -1 && !AllowShort)) { Reject("direction disabled", sig); return; }
   if(UseRegimeFilter)
     {
      int d1 = D1Regime(), h4 = H4Trend();
      if(d1 != sig || h4 != sig) { Reject(StringFormat("regime filter: D1=%d H4trend=%d", d1, h4), sig); return; }
     }
   double open_risk = 0;
   int npos = OwnPositions(open_risk);
   if(npos >= MaxPositions) { Reject("max positions", sig); return; }
   if(ForeignPositionOnNetting()) { Reject("netting account: foreign position on symbol", sig); return; }
   if(g_guard.MaxDdHit(MaxDrawdownPct)) { Reject("max drawdown limit", sig); return; }
   if(g_guard.DailyLimitHit(DailyLossPct)) { Reject("daily loss limit", sig); return; }
   if(MaxConsecLosses > 0 && TimeCurrent() < (datetime)Gv("pause_until", 0)) { Reject("pause after consecutive losses", sig); return; }
   double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK), bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);
   if(ask - bid > MaxSpreadPrice) { Reject(StringFormat("spread %.2f", ask - bid), sig); return; }
   double entry = (sig == 1) ? ask : bid;
   double sl = NormalizeDouble(close - sig * StopAtr * atr, _Digits);   // same absolute level as the simulator
   string why;
   if(!RRStopValid(sig, entry, sl, why)) { Reject(why, sig); return; }
   double lpl = RRLossPerLot(sig, entry, sl, SlipPrice, CommissionLotSide);
   double lot = 0, risk = 0;
   if(!RRLot(LotMode == FIXED ? RR_LOT_FIXED : RR_LOT_RISK, FixedLot, RiskPercent, RiskBase, 1.0, lpl, lot, risk, why))
     { Reject(why, sig); return; }
   double eq = AccountInfoDouble(ACCOUNT_EQUITY);
   if(MaxRiskPctTrade > 0 && risk > eq * MaxRiskPctTrade / 100.0)
     { Reject(StringFormat("trade risk %.2f > %.2f%% of equity", risk, MaxRiskPctTrade), sig); return; }
   if(MaxAggregateRiskPct > 0 && open_risk + risk > eq * MaxAggregateRiskPct / 100.0)
     { Reject(StringFormat("aggregate risk %.2f > %.2f%%", open_risk + risk, MaxAggregateRiskPct), sig); return; }
   if(!RRMarginOk(sig, lot, entry, why)) { Reject(why, sig); return; }
   g_pending_atr = atr;
   bool ok = (sig == 1) ? g_trade.Buy(lot, _Symbol, 0, sl, 0, "XTR") : g_trade.Sell(lot, _Symbol, 0, sl, 0, "XTR");
   RRSignal s; s.bar_time = iTime(_Symbol, PERIOD_H4, 1); s.side = sig; s.market = true; s.price = close; s.sl_struct = sl;
   s.atr = atr; s.expiry_bars = 1; s.cell = "TREND_REGIME"; s.reason = StringFormat("Donchian%d breakout", DonchianBars);
   g_log.Signal(s, ok ? "placed" : "order_failed", StringFormat("retcode %d", g_trade.ResultRetcode()), "ATR",
                (LotMode == FIXED ? "FIXED" : "RISK_PERCENT"), lot, sl, risk, ask - bid);
  }

//--- trailing on the closed M1 bar (never loosens the stop), max holding period in M1 bars
void ManagePositions()
  {
   MqlRates b[]; ArraySetAsSeries(b, false);
   if(CopyRates(_Symbol, PERIOD_M1, 1, 1, b) != 1) return;
   double spread = SymbolInfoInteger(_Symbol, SYMBOL_SPREAD) * _Point;
   long freeze = SymbolInfoInteger(_Symbol, SYMBOL_TRADE_FREEZE_LEVEL), stops = SymbolInfoInteger(_Symbol, SYMBOL_TRADE_STOPS_LEVEL);
   for(int i = PositionsTotal() - 1; i >= 0; i--)
     {
      ulong t = PositionGetTicket(i);
      if(t == 0 || PositionGetInteger(POSITION_MAGIC) != InpMagic || PositionGetString(POSITION_SYMBOL) != _Symbol) continue;
      int side = PositionGetInteger(POSITION_TYPE) == POSITION_TYPE_BUY ? 1 : -1;
      double sl = PositionGetDouble(POSITION_SL), tp = PositionGetDouble(POSITION_TP);
      datetime opened = (datetime)PositionGetInteger(POSITION_TIME);
      int held = iBarShift(_Symbol, PERIOD_M1, opened, false);
      if(MaxHoldM1Bars > 0 && held >= MaxHoldM1Bars)
        {
         if(g_trade.PositionClose(t)) g_log.Trade("CLOSE", t, "TREND_REGIME", side, PositionGetDouble(POSITION_VOLUME), b[0].close, sl, tp, 0, "max hold");
         continue;
        }
      double atr = GlobalVariableCheck(StringFormat("XTR_%I64u_atr", t)) ? GlobalVariableGet(StringFormat("XTR_%I64u_atr", t)) : 0;
      if(TrailAtr <= 0 || atr <= 0) continue;
      double ref = (side == 1) ? b[0].close : b[0].close + spread;       // long exits at bid, short at ask
      double ns = NormalizeDouble(ref - side * TrailAtr * atr, _Digits);
      if((ns - sl) * side <= 0) continue;                                 // never loosen
      double cur = (side == 1) ? SymbolInfoDouble(_Symbol, SYMBOL_BID) : SymbolInfoDouble(_Symbol, SYMBOL_ASK);
      if(MathAbs(cur - ns) < MathMax(stops, freeze) * _Point) continue;   // broker distance: retry next bar
      if(g_trade.PositionModify(t, ns, tp))
         g_log.Trade("MODIFY", t, "TREND_REGIME", side, PositionGetDouble(POSITION_VOLUME), ref, ns, tp, 0, "trail");
      else
         g_log.Event(StringFormat("trail modify failed #%I64u retcode %d", t, g_trade.ResultRetcode()));
     }
  }

void OnTick()
  {
   datetime m1 = iTime(_Symbol, PERIOD_M1, 0);
   if(m1 != 0 && m1 != g_last_m1) { g_last_m1 = m1; ManagePositions(); }
   datetime h4 = iTime(_Symbol, PERIOD_H4, 0);
   if(h4 == 0 || h4 == g_last_h4) return;
   g_last_h4 = h4;
   if(Gv("last_h4", 0) == (double)h4) return;        // restart safety: one decision per H4 bar
   Sv("last_h4", (double)h4);
   TryEntry();
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
      int side = HistoryDealGetInteger(tr.deal, DEAL_TYPE) == DEAL_TYPE_BUY ? 1 : -1;
      if(g_pending_atr > 0 && !GlobalVariableCheck(StringFormat("XTR_%I64u_atr", pos)))
         GlobalVariableSet(StringFormat("XTR_%I64u_atr", pos), g_pending_atr);
      g_log.Trade("OPEN", pos, "TREND_REGIME", side, vol, px, 0, 0, 0, "");
     }
   else if(entry == DEAL_ENTRY_OUT || entry == DEAL_ENTRY_OUT_BY)
     {
      double net = HistoryDealGetDouble(tr.deal, DEAL_PROFIT) + HistoryDealGetDouble(tr.deal, DEAL_COMMISSION) + HistoryDealGetDouble(tr.deal, DEAL_SWAP);
      long reason = HistoryDealGetInteger(tr.deal, DEAL_REASON);
      g_log.Trade("CLOSED", pos, "TREND_REGIME", 0, vol, px, 0, 0, net, reason == DEAL_REASON_SL ? "SL/trail" : "EA/other");
      g_guard.OnClosedTrade(net);
      GlobalVariableDel(StringFormat("XTR_%I64u_atr", pos));
      if(MaxConsecLosses > 0)
        {
         int streak = net < 0 ? (int)Gv("losses", 0) + 1 : 0;
         Sv("losses", streak);
         if(streak >= MaxConsecLosses) { Sv("pause_until", (double)(TimeCurrent() + PauseHours * 3600)); Sv("losses", 0);
                                         g_log.Event(StringFormat("pause %d h after %d consecutive losses", PauseHours, streak)); }
        }
     }
  }
//+------------------------------------------------------------------+
