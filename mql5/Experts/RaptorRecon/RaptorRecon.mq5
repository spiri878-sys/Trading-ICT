//+------------------------------------------------------------------+
//|                                                  RaptorRecon.mq5 |
//| XAUUSD-only research EA - independent reconstruction of ICT/SMC   |
//| behaviour publicly described for ICT RAPTOR AI PRIME.             |
//| NOT affiliated with / NOT a copy of the commercial product.       |
//|                                                                  |
//| RESEARCH STATUS (reports/FINAL_REPORT.md): no profile showed a    |
//| robust positive expectancy after costs in the Python research on |
//| XAUUSD M1 2018-2026. Use on DEMO only. Real accounts are refused  |
//| unless InpAllowRealAccount = true.                                |
//+------------------------------------------------------------------+
#property copyright "Raptor Recon research project"
#property version   "0.20"

#include <Trade\Trade.mqh>
#include <RaptorRecon\Defines.mqh>
#include <RaptorRecon\Logger.mqh>
#include <RaptorRecon\MarketModel.mqh>
#include <RaptorRecon\Cells.mqh>
#include <RaptorRecon\Risk.mqh>
#include <RaptorRecon\PositionManager.mqh>
#include <RaptorRecon\Telegram.mqh>

input group "=== GENERALE ==="
input ENUM_RR_PROFILE    InpProfile          = RR_PROFILE_FAITHFUL_M5; // Profilo strategia
input long               InpMagic            = 7701001;                // Magic number
input bool               InpAllowRealAccount = false;                  // Consenti conto REALE (sconsigliato)
input int                InpNyOffsetHours    = 7;                      // Ora server - ora New York (verificare broker)
input string             InpLogPrefix        = "RR";                   // Prefisso file di log CSV

input group "=== STOP LOSS (selettore indipendente) ==="
input ENUM_RR_STOP_MODE  InpStopMode         = RR_STOP_STRUCTURAL;     // Metodo stop
input double             InpStopFixedPrice   = 5.0;                    // FISSO: distanza in PREZZO USD/oz (1.00 = 100 punti a 2 decimali)
input double             InpStopPercent      = 0.25;                   // PERCENTUALE: % del prezzo di ingresso (NON del capitale)
input double             InpStopAtrMult      = 1.5;                    // ATR: multiplo ATR(14) del TF segnale
input double             InpMinStopAtrM15    = 0.0;                    // STRUTTURALE: stop minimo in ATR M15 (0 = spento)

input group "=== LOTTO (selettore indipendente) ==="
input ENUM_RR_LOT_MODE   InpLotMode          = RR_LOT_FIXED;           // Metodo lotto
input double             InpFixedLot         = 0.08;                   // Lotto fisso
input double             InpRiskPercent      = 1.0;                    // Rischio % per trade (modalita' rischio)
input ENUM_RR_RISK_BASE  InpRiskBase         = RR_BASE_BALANCE;        // Base del rischio %
input double             InpMaxRiskPctTrade  = 2.0;                    // Rischio massimo stimato per trade % (vale anche per lotto fisso; 0 = spento)
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
input int                InpMaxPositions     = 1;                      // Posizioni+ordini pendenti massimi dell'EA
input int                InpMaxTradesPerDay  = 3;                      // Ingressi massimi per giorno server (0 = illimitati)
input double             InpMaxSpreadPrice   = 1.0;                    // Spread massimo per entrare (prezzo)
input int                InpDeviationPoints  = 20;                     // Slippage massimo ordini a mercato (punti)
input double             InpDailyLossPct     = 3.0;                    // Stop giornaliero su P&L realizzato % (0 = spento)
input double             InpMaxDdPct         = 25.0;                   // Kill switch drawdown da massimo % (0 = spento)
input bool               InpBreathe          = false;                  // Rischio che respira (solo modalita' rischio %)
input double             InpBreatheDdFull    = 5.0;                    //   pieno fino a DD %
input double             InpBreatheDdMin     = 23.75;                  //   minimo a DD %
input double             InpBreatheMultMin   = 0.25;                   //   moltiplicatore minimo
input int                InpBreatheWins      = 20;                     //   ripresa dopo N trade vincenti
input bool               InpNewsFilter       = false;                  // Filtro notizie (calendario MT5, NON disponibile nel tester)
input int                InpNewsBeforeMin    = 30;                     //   minuti prima
input int                InpNewsAfterMin     = 30;                     //   minuti dopo

input group "=== STRATEGIE ICT (profilo A) - le sei del sito + PPK ==="
input bool               InpCellUnicorn      = true;                   // Unicorn Model (UNIOF)
input bool               InpCellOTE          = true;                   // OTE (OTEOF)
input bool               InpCellSilverBullet = false;                  // Silver Bullet
input bool               InpCellPO3          = true;                   // Power of Three (PO3)
input bool               InpCellMSS          = false;                  // Market Structure Shift
input bool               InpCellLS           = true;                   // Liquidity Sweep (LS)
input bool               InpCellPPK          = true;                   // PPK (motore principale, definizione INFERITA)

input group "=== TELEGRAM (opzionale, non testato) ==="
input bool               InpTelegram         = false;                  // Invia notifiche Telegram
input string             InpTelegramToken    = "";                     // Bot token (non salvarlo nei sorgenti)
input string             InpTelegramChat     = "";                     // Chat id

CTrade              g_trade;
CRRLogger           g_log;
CRRCells            g_cells;
CRRAccountGuard     g_guard;
CRRPositionManager  g_pm;
CRRStructure        g_st;
CRRTelegram         g_tg;
ENUM_TIMEFRAMES     g_tf;
int                 g_swing_k;
RRMgmtParams        g_mgmt;
datetime            g_last_sig_bar = 0, g_last_m1 = 0;
bool                g_news_warned = false;

//+------------------------------------------------------------------+
//| XAUUSD-only guard: base XAU, profit USD, name contains XAU or GOLD |
//+------------------------------------------------------------------+
bool IsXauUsd(string &why)
  {
   string base = SymbolInfoString(_Symbol, SYMBOL_CURRENCY_BASE);
   string prof = SymbolInfoString(_Symbol, SYMBOL_CURRENCY_PROFIT);
   string name = _Symbol; StringToUpper(name);
   bool name_ok = (StringFind(name, "XAUUSD") >= 0 || StringFind(name, "GOLD") >= 0);
   if(!name_ok || prof != "USD" || (base != "XAU" && base != "USD"))
     {
      why = StringFormat("symbol %s (base %s, profit %s) is not XAUUSD", _Symbol, base, prof);
      return false;
     }
   // some brokers report base=USD for CFD gold: then the name check above is the only identification
   return true;
  }

void CellDefaults(RRCellParams &p, const double disp, const double fvg, const int expiry, const bool market)
  {
   p.min_disp = disp; p.min_fvg = fvg; p.sl_buf_atr = 0.2; p.min_r_atr = 0.5; p.max_r_atr = 15.0;
   p.ote_level = 0.705; p.expiry = expiry; p.market_entry = market;
  }

void Notify(const string text)
  {
   if(g_tg.Enabled()) g_tg.Send("[RaptorRecon " + _Symbol + "] " + text);
  }

int OnInit()
  {
   string why;
   if(!IsXauUsd(why)) { Print("RaptorRecon: ", why, " -> EA disabled (XAUUSD only)."); return INIT_FAILED; }
   if(AccountInfoInteger(ACCOUNT_TRADE_MODE) == ACCOUNT_TRADE_MODE_REAL && !InpAllowRealAccount)
     { Print("RaptorRecon: REAL account and InpAllowRealAccount=false -> EA disabled."); return INIT_FAILED; }
   if(InpFixedLot <= 0 || InpRiskPercent <= 0 || InpStopFixedPrice <= 0 || InpStopPercent <= 0 || InpStopAtrMult <= 0)
     { Print("RaptorRecon: invalid (non positive) lot/stop input"); return INIT_PARAMETERS_INCORRECT; }
   if(InpP1Frac + InpP2Frac >= 1.0 || InpTpR <= 0 || InpMaxPositions < 1)
     { Print("RaptorRecon: invalid management inputs (p1+p2 must be < 1, tp > 0, max positions >= 1)"); return INIT_PARAMETERS_INCORRECT; }
   g_log.Init(InpLogPrefix);
   g_trade.SetExpertMagicNumber(InpMagic);
   g_trade.SetDeviationInPoints(InpDeviationPoints);
   g_trade.SetTypeFillingBySymbol(_Symbol);
   g_guard.Init(InpMagic);
   g_pm.Init(&g_trade, &g_log, InpMagic);
   g_tg.Init(InpTelegram, InpTelegramToken, InpTelegramChat);
   if(InpProfile == RR_PROFILE_UNICORN_LONG)
     {
      g_tf = PERIOD_M15; g_swing_k = 3;
      g_mgmt.tp_r = 3.0; g_mgmt.p1_r = 0; g_mgmt.p1_frac = 0; g_mgmt.p2_r = 0; g_mgmt.p2_frac = 0;
      g_mgmt.be_after_p1 = false; g_mgmt.trail_atr = 0; g_mgmt.max_hold_min = 2880;
     }
   else if(InpProfile == RR_PROFILE_EXPERIMENTAL)
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
   g_log.Event(StringFormat("INIT v%s %s profile=%s tf=%s k=%d stop=%s lot=%s fixed_lot=%.2f risk=%.2f%% tp=%.1fR p1=%.2f@%.2fR p2=%.2f@%.2fR BE=%s hold=%d digits=%d point=%g tick_size=%g tick_value=%g vol_min=%g vol_step=%g stops_level=%d freeze=%d",
                            RR_VERSION, _Symbol, EnumToString(InpProfile), EnumToString(g_tf), g_swing_k, RRStopModeName(InpStopMode),
                            RRLotModeName(InpLotMode), InpFixedLot, InpRiskPercent, g_mgmt.tp_r, g_mgmt.p1_frac, g_mgmt.p1_r,
                            g_mgmt.p2_frac, g_mgmt.p2_r, (g_mgmt.be_after_p1 ? "on" : "off"), g_mgmt.max_hold_min, _Digits, _Point,
                            SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE), SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE),
                            SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN), SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP),
                            (int)SymbolInfoInteger(_Symbol, SYMBOL_TRADE_STOPS_LEVEL), (int)SymbolInfoInteger(_Symbol, SYMBOL_TRADE_FREEZE_LEVEL)));
   if(InpProfile == RR_PROFILE_EXPERIMENTAL)
      g_log.Event("WARNING: profile B (experimental) FAILED out-of-sample validation in research (VAL-01). Demo only.");
   Notify("EA started, profile " + EnumToString(InpProfile));
   return INIT_SUCCEEDED;
  }

void OnDeinit(const int reason) { g_log.Event(StringFormat("DEINIT reason=%d", reason)); }

//--- positions + pending orders of this EA on this symbol
int OwnExposure()
  {
   int k = 0;
   for(int i = PositionsTotal() - 1; i >= 0; i--)
     {
      ulong t = PositionGetTicket(i);
      if(t != 0 && PositionGetInteger(POSITION_MAGIC) == InpMagic && PositionGetString(POSITION_SYMBOL) == _Symbol) k++;
     }
   for(int i = OrdersTotal() - 1; i >= 0; i--)
     {
      ulong t = OrderGetTicket(i);
      if(t != 0 && OrderGetInteger(ORDER_MAGIC) == InpMagic && OrderGetString(ORDER_SYMBOL) == _Symbol) k++;
     }
   return k;
  }

//--- entries placed today (server day), persisted for restarts
string DayKey() { MqlDateTime t; TimeToStruct(TimeCurrent(), t); return StringFormat("RR_%I64d_n_%04d%02d%02d", InpMagic, t.year, t.mon, t.day); }
int    TradesToday() { return GlobalVariableCheck(DayKey()) ? (int)GlobalVariableGet(DayKey()) : 0; }
void   CountTrade() { GlobalVariableSet(DayKey(), TradesToday() + 1); }

//--- duplicate guard: the same (cell, side, bar) is processed only once, even after a restart
bool AlreadyProcessed(const RRSignal &s)
  {
   string n = StringFormat("RR_%I64d_s_%s_%d_%I64d", InpMagic, s.cell, s.side, (long)s.bar_time);
   if(StringLen(n) > 63) n = StringSubstr(n, 0, 63);
   if(GlobalVariableCheck(n)) return true;
   GlobalVariableSet(n, 1);
   return false;
  }

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
      string cmt = OrderGetString(ORDER_COMMENT);
      if(fri || (exp > 0 && TimeCurrent() >= exp))
        {
         if(g_trade.OrderDelete(t))
           {
            g_log.Trade("EXPIRE", t, cmt, 0, 0, 0, 0, 0, 0, fri ? "friday cutoff" : "expiry");
            GlobalVariableDel(n);
           }
         else
            g_log.Event(StringFormat("OrderDelete %I64u failed retcode %d", t, g_trade.ResultRetcode()));
        }
     }
  }

bool NewsBlocked(string &why)
  {
   if(!InpNewsFilter) return false;
   if(MQLInfoInteger(MQL_TESTER))
     {
      if(!g_news_warned) { g_log.Event("news filter requested but the MT5 calendar is not available in the Strategy Tester: filter INACTIVE in this test"); g_news_warned = true; }
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

int Candidates(RRSignal &out[])
  {
   ArrayResize(out, 0);
   if(!g_st.Load(_Symbol, g_tf, 1000, g_swing_k))
     { g_log.Event("not enough closed bars for the structure engine"); return 0; }
   RRCellParams p;
   if(InpProfile == RR_PROFILE_WYCKOFF_BENCH)
     {
      CellDefaults(p, 0, 0, 1, true);
      g_cells.Wyckoff(g_st, p, out, RRHtfAtr(_Symbol, PERIOD_H1));
      return ArraySize(out);
     }
   if(InpProfile == RR_PROFILE_UNICORN_LONG)
     {
      // mirror of python/scripts/candidate_c_portfolio.py: UNIOF on M15, long only, stop = min(own stop,
      // last confirmed H4 swing low - 0.2 ATR(H4)), dropped if risk > 6 ATR(H4)
      RRSignal raw[];
      CellDefaults(p, 1.2, 0.1, 4, false); p.max_r_atr = 40.0;
      g_cells.UNIOF(g_st, p, raw);
      CRRStructure h4;
      if(!h4.Load(_Symbol, PERIOD_H4, 400, 2) || h4.last_sl == EMPTY_VALUE) return 0;
      double a4 = h4.atr[h4.n - 1];
      for(int i = 0; i < ArraySize(raw); i++)
        {
         if(raw[i].side != 1) continue;
         raw[i].sl_struct = MathMin(raw[i].sl_struct, h4.last_sl - 0.2 * a4);
         double risk = raw[i].price - raw[i].sl_struct;
         if(risk <= 0 || risk > 6.0 * a4) continue;
         raw[i].reason += StringFormat(" | H4 swing stop %.2f", raw[i].sl_struct);
         int k = ArraySize(out); ArrayResize(out, k + 1); out[k] = raw[i];
        }
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
   // profile A: same defaults as python/raptor/strategies/ict.py; dict order there = priority here
   if(InpCellPPK)          { CellDefaults(p, 1.2, 0.15, 12, false); g_cells.PPK(g_st, p, out); }
   if(InpCellMSS)          { CellDefaults(p, 1.2, 0.15, 12, false); g_cells.MSS(g_st, p, out); }
   if(InpCellOTE)          { CellDefaults(p, 1.2, 0.0, 24, false);  g_cells.OTEOF(g_st, p, out); }
   if(InpCellPO3)          { CellDefaults(p, 1.0, 0.1, 12, false);  g_cells.PO3(g_st, p, out, InpNyOffsetHours); }
   if(InpCellUnicorn)      { CellDefaults(p, 1.2, 0.1, 12, false);  g_cells.UNIOF(g_st, p, out); }
   if(InpCellLS)           { CellDefaults(p, 1.2, 0.15, 6, false);  g_cells.LS(g_st, p, out); }
   if(InpCellSilverBullet) { CellDefaults(p, 1.2, 0.25, 6, false);  g_cells.SilverBullet(g_st, p, out, InpNyOffsetHours); }
   return ArraySize(out);
  }

//--- one candidate -> checks -> order. Every outcome is logged with its reason.
bool TryPlace(RRSignal &s)
  {
   string why = "", formula = "";
   double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK), bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);
   double spread = ask - bid;
   string sm = RRStopModeName(InpStopMode), lm = RRLotModeName(InpLotMode);
   if(AlreadyProcessed(s))                    { return false; }
   if(OwnExposure() >= InpMaxPositions)       { g_log.Signal(s, "skipped_busy", "max positions/pending reached", sm, lm, 0, 0, 0, spread); return false; }
   if(InpMaxTradesPerDay > 0 && TradesToday() >= InpMaxTradesPerDay) { g_log.Signal(s, "rejected_max_trades_day", "", sm, lm, 0, 0, 0, spread); return false; }
   if(g_guard.MaxDdHit(InpMaxDdPct))         { g_log.Signal(s, "halted_max_dd", "kill switch", sm, lm, 0, 0, 0, spread); return false; }
   if(g_guard.DailyLimitHit(InpDailyLossPct)) { g_log.Signal(s, "rejected_daily_limit", "", sm, lm, 0, 0, 0, spread); return false; }
   if(spread > InpMaxSpreadPrice)             { g_log.Signal(s, "rejected_spread", StringFormat("spread %.2f", spread), sm, lm, 0, 0, 0, spread); return false; }
   if(NewsBlocked(why))                       { g_log.Signal(s, "rejected_news", why, sm, lm, 0, 0, 0, spread); return false; }
   //--- entry. Limit levels are chart levels: MT5 triggers BUY LIMIT on ASK and SELL LIMIT on BID,
   //    exactly like the python simulator (long fill when ask <= price, short fill when bid >= price).
   bool market = s.market || (s.side == 1 && ask <= s.price) || (s.side == -1 && bid >= s.price);
   double entry = market ? (s.side == 1 ? ask : bid) : s.price;
   double sl_struct = s.sl_struct;
   if(InpStopMode == RR_STOP_STRUCTURAL && InpMinStopAtrM15 > 0)
     {
      double need = InpMinStopAtrM15 * RRHtfAtr(_Symbol, PERIOD_M15);
      if((entry - sl_struct) * s.side < need)
        { sl_struct = entry - s.side * need; s.reason += StringFormat(" | stop floored to %.2fxATR(M15)", InpMinStopAtrM15); }
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
   double eq = AccountInfoDouble(ACCOUNT_EQUITY);
   if(InpMaxRiskPctTrade > 0 && risk_money > eq * InpMaxRiskPctTrade / 100.0)
     { g_log.Signal(s, "rejected_risk_cap", StringFormat("estimated risk %.2f > %.2f%% of equity", risk_money, InpMaxRiskPctTrade), sm, lm, lot, sl, risk_money, spread); return false; }
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
   if(ok)
     {
      CountTrade();
      Notify(StringFormat("%s %s %s lot %.2f entry %.2f SL %.2f TP %.2f risk %.2f | %s", s.cell, (s.side == 1 ? "BUY" : "SELL"),
                          (market ? "market" : "limit"), lot, entry, sl, tp, risk_money, s.reason));
     }
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
   if(sb == 0 || sb == g_last_sig_bar) return;
   g_last_sig_bar = sb;
   MqlDateTime now; TimeToStruct(TimeCurrent(), now);
   if(now.day_of_week == 5 && now.hour * 60 + now.min >= InpFridayCloseMin) return;
   RRSignal c[];
   int n = Candidates(c);
   for(int i = 0; i < n; i++)
      TryPlace(c[i]);
  }

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
      Notify(StringFormat("OPEN #%I64u %s vol %.2f @ %.2f SL %.2f", pos, PositionGetString(POSITION_COMMENT), vol, px, sl));
     }
   else if(entry == DEAL_ENTRY_OUT || entry == DEAL_ENTRY_OUT_BY)
     {
      double net = HistoryDealGetDouble(tr.deal, DEAL_PROFIT) + HistoryDealGetDouble(tr.deal, DEAL_COMMISSION) + HistoryDealGetDouble(tr.deal, DEAL_SWAP);
      long reason = HistoryDealGetInteger(tr.deal, DEAL_REASON);
      string why = reason == DEAL_REASON_SL ? "SL" : (reason == DEAL_REASON_TP ? "TP" : "EA/other");
      g_log.Trade("CLOSE_DEAL", pos, cmt, 0, vol, px, 0, 0, net, why);
      if(!PositionSelectByTicket(pos))
        {
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
         Notify(StringFormat("CLOSED #%I64u net %.2f (%s)", pos, total, why));
        }
     }
  }
//+------------------------------------------------------------------+
