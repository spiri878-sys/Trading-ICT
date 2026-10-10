//+------------------------------------------------------------------+
//|                                                  RaptorRecon.mq5 |
//| Independent research reconstruction of an ICT/SMC XAUUSD system. |
//| NOT affiliated with / NOT a copy of ICT RAPTOR AI PRIME.         |
//|                                                                  |
//| RESEARCH STATUS (see reports/FINAL_REPORT.md): no profile of this |
//| EA showed a robust positive expectancy in the Python research on |
//| XAUUSD M1 2018-2026. Use on DEMO only. Real accounts are refused  |
//| unless InpAllowRealAccount = true.                                |
//+------------------------------------------------------------------+
#property copyright "Raptor Recon research project"
#property version   "0.10"
#property strict

#include <Trade\Trade.mqh>
#include <RaptorRecon\Defines.mqh>
#include <RaptorRecon\Logger.mqh>
#include <RaptorRecon\MarketModel.mqh>
#include <RaptorRecon\Cells.mqh>
#include <RaptorRecon\Risk.mqh>
#include <RaptorRecon\PositionManager.mqh>

//--- general
input group "=== GENERALE ==="
input ENUM_RR_PROFILE    InpProfile          = RR_PROFILE_FAITHFUL_M5; // Profilo strategia
input long               InpMagic            = 7701001;                // Magic number
input bool               InpAllowRealAccount = false;                  // Consenti conto REALE (sconsigliato)
input int                InpNyOffsetHours    = 7;                      // Ora server - ora New York (verificare broker)
input string             InpLogPrefix        = "RR";                   // Prefisso file di log CSV

input group "=== STOP LOSS (selettore indipendente) ==="
input ENUM_RR_STOP_MODE  InpStopMode         = RR_STOP_STRUCTURAL;     // Metodo stop
input double             InpStopFixedPrice   = 5.0;                    // FISSO: distanza in PREZZO (XAUUSD 1.00 = 100 punti)
input double             InpStopPercent      = 0.25;                   // PERCENTUALE: % del prezzo di ingresso
input double             InpStopAtrMult      = 1.5;                    // ATR: multiplo ATR(14) del TF segnale
input double             InpMinStopAtrM15    = 0.0;                    // STRUTTURALE: stop minimo in ATR M15 (0 = spento)

input group "=== LOTTO (selettore indipendente) ==="
input ENUM_RR_LOT_MODE   InpLotMode          = RR_LOT_FIXED;           // Metodo lotto
input double             InpFixedLot         = 0.08;                   // Lotto fisso
input double             InpRiskPercent      = 1.0;                    // Rischio % per trade (modalita' rischio)
input ENUM_RR_RISK_BASE  InpRiskBase         = RR_BASE_BALANCE;        // Base del rischio %
input double             InpCommissionLotSide= 3.5;                    // Commissione per lotto per lato (stima per il calcolo rischio)
input double             InpSlipPrice        = 0.05;                   // Slippage stimato sullo stop (prezzo)

input group "=== GESTIONE POSIZIONE (profilo A) ==="
input double             InpTpR              = 4.0;                    // Target finale (R)
input double             InpP1R              = 0.7;                    // Parziale 1 a (R)
input double             InpP1Frac           = 0.20;                   // Parziale 1: frazione del volume iniziale
input double             InpP2R              = 2.0;                    // Parziale 2 a (R)
input double             InpP2Frac           = 0.20;                   // Parziale 2: frazione del volume iniziale
input bool               InpBreakEven        = true;                   // Break-even dopo il parziale 1
input double             InpTrailAtr         = 0.0;                    // Trailing dopo P1 in ATR (0 = spento)
input int                InpMaxHoldMin       = 4320;                   // Durata massima (minuti)
input int                InpFridayCloseMin   = 1380;                   // Venerdi': chiusura dopo minuto server (23:00)

input group "=== PROTEZIONI ==="
input double             InpMaxSpreadPrice   = 1.0;                    // Spread massimo per entrare (prezzo)
input int                InpDeviationPoints  = 20;                     // Slippage massimo ordini a mercato (punti)
input double             InpDailyLossPct     = 3.0;                    // Stop giornaliero su P&L realizzato % (0 = spento)
input double             InpMaxDdPct         = 25.0;                   // Kill switch drawdown da massimo % (0 = spento)
input bool               InpBreathe          = false;                  // Rischio che respira (solo modalita' rischio %)
input double             InpBreatheDdFull    = 5.0;                    //   pieno fino a DD %
input double             InpBreatheDdMin     = 23.75;                  //   minimo a DD %
input double             InpBreatheMultMin   = 0.25;                   //   moltiplicatore minimo
input int                InpBreatheWins      = 20;                     //   ripresa dopo N trade vincenti
input bool               InpNewsFilter       = false;                  // Filtro notizie (calendario MT5, non disponibile nel tester)
input int                InpNewsBeforeMin    = 30;                     //   minuti prima
input int                InpNewsAfterMin     = 30;                     //   minuti dopo

input group "=== CELLE (profilo A) ==="
input bool               InpCellPPK          = true;
input bool               InpCellOTEOF        = true;
input bool               InpCellPO3          = true;
input bool               InpCellUNIOF        = true;
input bool               InpCellLS           = true;

//--- globals
CTrade              g_trade;
CRRLogger           g_log;
CRRCells            g_cells;
CRRAccountGuard     g_guard;
CRRPositionManager  g_pm;
CRRStructure        g_st;
ENUM_TIMEFRAMES     g_tf;
int                 g_swing_k;
RRMgmtParams        g_mgmt;
datetime            g_last_sig_bar = 0, g_last_m1 = 0;
bool                g_news_warned = false;

//+------------------------------------------------------------------+
void CellDefaults(RRCellParams &p, const double disp, const double fvg, const int expiry, const bool market)
  {
   p.min_disp = disp; p.min_fvg = fvg; p.sl_buf_atr = 0.2; p.min_r_atr = 0.5; p.max_r_atr = 15.0;
   p.ote_level = 0.705; p.expiry = expiry; p.market_entry = market;
  }

int OnInit()
  {
   if(AccountInfoInteger(ACCOUNT_TRADE_MODE) == ACCOUNT_TRADE_MODE_REAL && !InpAllowRealAccount)
     {
      Print("RaptorRecon: REAL account detected and InpAllowRealAccount=false -> EA disabled.");
      return INIT_FAILED;
     }
   g_log.Init(InpLogPrefix);
   g_trade.SetExpertMagicNumber(InpMagic);
   g_trade.SetDeviationInPoints(InpDeviationPoints);
   g_trade.SetTypeFillingBySymbol(_Symbol);
   g_guard.Init(InpMagic);
   g_pm.Init(&g_trade, &g_log, InpMagic);
   if(InpProfile == RR_PROFILE_EXPERIMENTAL)
     {
      g_tf = PERIOD_H1; g_swing_k = 3;
      g_mgmt.tp_r = 3.0; g_mgmt.p1_r = 0; g_mgmt.p1_frac = 0; g_mgmt.p2_r = 0; g_mgmt.p2_frac = 0;
      g_mgmt.be_after_p1 = false; g_mgmt.trail_atr = 0; g_mgmt.max_hold_min = 2880;
     }
   else
     {
      g_tf = PERIOD_M5; g_swing_k = 3;
      g_mgmt.tp_r = InpTpR; g_mgmt.p1_r = InpP1R; g_mgmt.p1_frac = InpP1Frac; g_mgmt.p2_r = InpP2R; g_mgmt.p2_frac = InpP2Frac;
      g_mgmt.be_after_p1 = InpBreakEven; g_mgmt.trail_atr = InpTrailAtr; g_mgmt.max_hold_min = InpMaxHoldMin;
     }
   g_mgmt.friday_close_min = InpFridayCloseMin;
   g_log.Event(StringFormat("INIT v%s profile=%s tf=%s k=%d stop=%s lot=%s fixed_lot=%.2f risk=%.2f%% tp=%.1fR p1=%.2f@%.2fR p2=%.2f@%.2fR BE=%s hold=%d",
                            RR_VERSION, EnumToString(InpProfile), EnumToString(g_tf), g_swing_k, RRStopModeName(InpStopMode),
                            RRLotModeName(InpLotMode), InpFixedLot, InpRiskPercent, g_mgmt.tp_r, g_mgmt.p1_frac, g_mgmt.p1_r,
                            g_mgmt.p2_frac, g_mgmt.p2_r, (g_mgmt.be_after_p1 ? "on" : "off"), g_mgmt.max_hold_min));
   if(InpProfile == RR_PROFILE_EXPERIMENTAL)
      g_log.Event("WARNING: profile B (experimental) FAILED out-of-sample validation in research (VAL-01). Demo only.");
   return INIT_SUCCEEDED;
  }

void OnDeinit(const int reason) { g_log.Event(StringFormat("DEINIT reason=%d", reason)); }

//--- busy = one position or one pending order of ours on this symbol
bool Busy()
  {
   for(int i = PositionsTotal() - 1; i >= 0; i--)
     {
      ulong t = PositionGetTicket(i);
      if(t != 0 && PositionGetInteger(POSITION_MAGIC) == InpMagic && PositionGetString(POSITION_SYMBOL) == _Symbol) return true;
     }
   for(int i = OrdersTotal() - 1; i >= 0; i--)
     {
      ulong t = OrderGetTicket(i);
      if(t != 0 && OrderGetInteger(ORDER_MAGIC) == InpMagic && OrderGetString(ORDER_SYMBOL) == _Symbol) return true;
     }
   return false;
  }

//--- delete our pending orders whose validity expired (also on Friday cutoff)
void ExpirePending()
  {
   MqlDateTime now; TimeToStruct(TimeCurrent(), now);
   bool fri = (now.day_of_week == 5 && now.hour * 60 + now.min >= InpFridayCloseMin);
   for(int i = OrdersTotal() - 1; i >= 0; i--)
     {
      ulong t = OrderGetTicket(i);
      if(t == 0 || OrderGetInteger(ORDER_MAGIC) != InpMagic || OrderGetString(ORDER_SYMBOL) != _Symbol) continue;
      string n = StringFormat("RRO_%I64u_exp", t);
      datetime exp = GlobalVariableCheck(n) ? (datetime)GlobalVariableGet(n) : 0;
      if(fri || (exp > 0 && TimeCurrent() >= exp))
        {
         if(g_trade.OrderDelete(t))
           {
            g_log.Trade("EXPIRE", t, OrderGetString(ORDER_COMMENT), 0, 0, 0, 0, 0, 0, fri ? "friday cutoff" : "expiry");
            GlobalVariableDel(n);
           }
        }
     }
  }

//--- high-impact USD events within the window (live only; calendar is unavailable in the tester)
bool NewsBlocked(string &why)
  {
   if(!InpNewsFilter) return false;
   if(MQLInfoInteger(MQL_TESTER))
     {
      if(!g_news_warned) { g_log.Event("news filter requested but MT5 calendar is not available in the Strategy Tester: filter INACTIVE in this test"); g_news_warned = true; }
      return false;
     }
   MqlCalendarValue v[];
   datetime from = TimeCurrent() - InpNewsAfterMin * 60, to = TimeCurrent() + InpNewsBeforeMin * 60;
   if(CalendarValueHistory(v, from, to, NULL, "USD") <= 0) return false;
   for(int i = 0; i < ArraySize(v); i++)
     {
      MqlCalendarEvent e;
      if(CalendarEventById(v[i].event_id, e) && e.importance == CALENDAR_IMPORTANCE_HIGH)
        { why = "news: " + e.name; return true; }
     }
   return false;
  }

//--- collect candidates of the active profile on the last closed signal-TF bar
int Candidates(RRSignal &out[])
  {
   ArrayResize(out, 0);
   if(!g_st.Load(_Symbol, g_tf, 1000, g_swing_k)) return 0;
   RRCellParams p;
   if(InpProfile == RR_PROFILE_WYCKOFF_BENCH)
     {
      CellDefaults(p, 0, 0, 1, true);
      g_cells.Wyckoff(g_st, p, out, RRHtfAtr(_Symbol, PERIOD_H1));
      return ArraySize(out);
     }
   if(InpProfile == RR_PROFILE_EXPERIMENTAL)
     {
      CellDefaults(p, 1.2, 0.15, 4, true); p.min_r_atr = 0.3; p.max_r_atr = 30.0;
      g_cells.PPK(g_st, p, out);
      CellDefaults(p, 1.2, 0.1, 4, true); p.min_r_atr = 0.3; p.max_r_atr = 30.0;
      g_cells.UNIOF(g_st, p, out);
      return ArraySize(out);
     }
   // profile A (python defaults, see strategies/ict.py)
   if(InpCellPPK)   { CellDefaults(p, 1.2, 0.15, 12, false); g_cells.PPK(g_st, p, out); }
   if(InpCellOTEOF) { CellDefaults(p, 1.2, 0.0, 24, false);  g_cells.OTEOF(g_st, p, out); }
   if(InpCellPO3)   { CellDefaults(p, 1.0, 0.1, 12, false);  g_cells.PO3(g_st, p, out, InpNyOffsetHours); }
   if(InpCellUNIOF) { CellDefaults(p, 1.2, 0.1, 12, false);  g_cells.UNIOF(g_st, p, out); }
   if(InpCellLS)    { CellDefaults(p, 1.2, 0.15, 6, false);  g_cells.LS(g_st, p, out); }
   return ArraySize(out);
  }

//--- try to place one candidate; every outcome is logged
bool TryPlace(RRSignal &s)
  {
   string why = "", formula = "";
   double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK), bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);
   double spread = ask - bid;
   string sm = RRStopModeName(InpStopMode), lm = RRLotModeName(InpLotMode);
   if(Busy())                                { g_log.Signal(s, "skipped_busy", "one position/pending at a time", sm, lm, 0, 0, 0, spread); return false; }
   if(g_guard.MaxDdHit(InpMaxDdPct))        { g_log.Signal(s, "halted_max_dd", "kill switch", sm, lm, 0, 0, 0, spread); return false; }
   if(g_guard.DailyLimitHit(InpDailyLossPct)){ g_log.Signal(s, "rejected_daily_limit", "", sm, lm, 0, 0, 0, spread); return false; }
   if(spread > InpMaxSpreadPrice)            { g_log.Signal(s, "rejected_spread", StringFormat("spread %.2f", spread), sm, lm, 0, 0, 0, spread); return false; }
   if(NewsBlocked(why))                      { g_log.Signal(s, "rejected_news", why, sm, lm, 0, 0, 0, spread); return false; }
   //--- entry type: limit already through the market -> market (python: fill at open when gapped)
   bool market = s.market || (s.side == 1 && ask <= s.price) || (s.side == -1 && bid >= s.price);
   double entry = market ? (s.side == 1 ? ask : bid) : (s.side == 1 ? s.price + spread : s.price);
   // NOTE: for a buy limit the trigger is the ASK; s.price is a bid-chart level, so the order price is s.price+spread
   //--- optional minimum structural stop in ATR(M15)
   double sl_struct = s.sl_struct;
   if(InpStopMode == RR_STOP_STRUCTURAL && InpMinStopAtrM15 > 0)
     {
      double a15 = RRHtfAtr(_Symbol, PERIOD_M15);
      double need = InpMinStopAtrM15 * a15;
      if((entry - sl_struct) * s.side < need) { sl_struct = entry - s.side * need; s.reason += StringFormat(" | stop floored to %.2fxATR(M15)", InpMinStopAtrM15); }
     }
   double sl = RRStopPrice(InpStopMode, s.side, entry, sl_struct, InpStopFixedPrice, InpStopPercent, InpStopAtrMult, s.atr, formula);
   if(!RRStopValid(s.side, entry, sl, why)) { g_log.Signal(s, "rejected_stop_invalid", why + " | " + formula, sm, lm, 0, sl, 0, spread); return false; }
   double R = MathAbs(entry - sl);
   double tp = NormalizeDouble(entry + s.side * g_mgmt.tp_r * R, _Digits);
   double lpl = RRLossPerLot(s.side, entry, sl, InpSlipPrice, InpCommissionLotSide);
   double mult = (InpLotMode == RR_LOT_RISK) ? g_guard.RiskMultiplier(InpBreathe, InpBreatheDdFull, InpBreatheDdMin, InpBreatheMultMin, InpBreatheWins) : 1.0;
   double lot = 0, risk_money = 0;
   if(!RRLot(InpLotMode, InpFixedLot, InpRiskPercent, InpRiskBase, mult, lpl, lot, risk_money, why))
     { g_log.Signal(s, "rejected_lot", why, sm, lm, lot, sl, 0, spread); return false; }
   if(!RRMarginOk(s.side, lot, entry, why)) { g_log.Signal(s, "rejected_margin", why, sm, lm, lot, sl, risk_money, spread); return false; }
   string comment = "RR|" + s.cell;
   bool ok;
   if(market)
      ok = (s.side == 1) ? g_trade.Buy(lot, _Symbol, 0, sl, tp, comment) : g_trade.Sell(lot, _Symbol, 0, sl, tp, comment);
   else
     {
      double px = NormalizeDouble(entry, _Digits);
      ok = (s.side == 1) ? g_trade.BuyLimit(lot, px, _Symbol, sl, tp, ORDER_TIME_GTC, 0, comment)
                         : g_trade.SellLimit(lot, px, _Symbol, sl, tp, ORDER_TIME_GTC, 0, comment);
      if(ok)
        {
         datetime exp = s.bar_time + PeriodSeconds(g_tf) * (1 + s.expiry_bars);
         GlobalVariableSet(StringFormat("RRO_%I64u_exp", g_trade.ResultOrder()), (double)exp);
        }
     }
   string detail = StringFormat("%s | %s | R=%.2f tp=%.2f mult=%.2f retcode=%d", (market ? "market" : "limit"), formula, R, tp, mult, g_trade.ResultRetcode());
   g_log.Signal(s, ok ? "placed" : "order_failed", detail, sm, lm, lot, sl, risk_money, spread);
   return ok;
  }

void OnTick()
  {
   datetime m1 = iTime(_Symbol, PERIOD_M1, 0);
   if(m1 != g_last_m1)
     {
      g_last_m1 = m1;
      ExpirePending();
      g_pm.OnNewM1Bar(g_mgmt);
     }
   datetime sb = iTime(_Symbol, g_tf, 0);
   if(sb == g_last_sig_bar) return;
   g_last_sig_bar = sb;
   MqlDateTime now; TimeToStruct(TimeCurrent(), now);
   if(now.day_of_week == 5 && now.hour * 60 + now.min >= InpFridayCloseMin) return;
   RRSignal c[];
   int n = Candidates(c);
   for(int i = 0; i < n; i++)
      TryPlace(c[i]);      // the first placed order makes the others "skipped_busy" (same rule as python)
  }

//--- fills / closes: register positions and feed the account guard
void OnTradeTransaction(const MqlTradeTransaction &tr, const MqlTradeRequest &rq, const MqlTradeResult &rs)
  {
   if(tr.type != TRADE_TRANSACTION_DEAL_ADD) return;
   if(!HistoryDealSelect(tr.deal)) return;
   if(HistoryDealGetInteger(tr.deal, DEAL_MAGIC) != InpMagic) return;
   long entry = HistoryDealGetInteger(tr.deal, DEAL_ENTRY);
   ulong pos = (ulong)HistoryDealGetInteger(tr.deal, DEAL_POSITION_ID);
   string cmt = HistoryDealGetString(tr.deal, DEAL_COMMENT);
   double px = HistoryDealGetDouble(tr.deal, DEAL_PRICE), vol = HistoryDealGetDouble(tr.deal, DEAL_VOLUME);
   if(entry == DEAL_ENTRY_IN && PositionSelectByTicket(pos))
     {
      double sl = PositionGetDouble(POSITION_SL);
      g_pm.Register(pos, px, sl, vol, g_st.n > 0 ? g_st.atr[g_st.n - 1] : 0);
      int side = PositionGetInteger(POSITION_TYPE) == POSITION_TYPE_BUY ? 1 : -1;
      g_log.Trade("OPEN", pos, PositionGetString(POSITION_COMMENT), side, vol, px, sl, PositionGetDouble(POSITION_TP), 0, "");
     }
   else if(entry == DEAL_ENTRY_OUT || entry == DEAL_ENTRY_OUT_BY)
     {
      double net = HistoryDealGetDouble(tr.deal, DEAL_PROFIT) + HistoryDealGetDouble(tr.deal, DEAL_COMMISSION) + HistoryDealGetDouble(tr.deal, DEAL_SWAP);
      long reason = HistoryDealGetInteger(tr.deal, DEAL_REASON);
      string why = reason == DEAL_REASON_SL ? "SL" : (reason == DEAL_REASON_TP ? "TP" : "EA/other");
      g_log.Trade("CLOSE_DEAL", pos, cmt, 0, vol, px, 0, 0, net, why);
      if(!PositionSelectByTicket(pos))
        {
         // position fully closed: total net of the position for the guard
         double total = 0;
         if(HistorySelectByPosition(pos))
            for(int i = 0; i < HistoryDealsTotal(); i++)
              {
               ulong d = HistoryDealGetTicket(i);
               total += HistoryDealGetDouble(d, DEAL_PROFIT) + HistoryDealGetDouble(d, DEAL_COMMISSION) + HistoryDealGetDouble(d, DEAL_SWAP);
              }
         g_guard.OnClosedTrade(total);
         g_pm.Forget(pos);
         g_log.Trade("CLOSED", pos, cmt, 0, 0, px, 0, 0, total, why);
        }
     }
  }
//+------------------------------------------------------------------+
