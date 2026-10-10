//+------------------------------------------------------------------+
//| RaptorRecon - position management on CLOSED M1 bars                |
//| Ladder: p1 (fraction of initial volume) at p1_r R + break-even,    |
//| p2 at p2_r R, remainder to the broker TP at tp_r R.                |
//| Per-position state lives in GlobalVariables keyed by ticket so a   |
//| terminal restart does not lose partial / BE flags.                 |
//+------------------------------------------------------------------+
#ifndef RAPTORRECON_POSMAN_MQH
#define RAPTORRECON_POSMAN_MQH

#include <Trade\Trade.mqh>
#include "Logger.mqh"

struct RRMgmtParams
  {
   double            tp_r, p1_r, p1_frac, p2_r, p2_frac;
   bool              be_after_p1;
   double            trail_atr;
   int               max_hold_min;
   int               friday_close_min;   // server minute of day
  };

class CRRPositionManager
  {
private:
   CTrade           *m_trade;
   CRRLogger        *m_log;
   long              m_magic;
   string            K(const ulong t, const string f) { return StringFormat("RRP_%I64u_%s", t, f); }
   double            G(const ulong t, const string f, const double def)
     {
      string n = K(t, f);
      return GlobalVariableCheck(n) ? GlobalVariableGet(n) : def;
     }
   void              S(const ulong t, const string f, const double v) { GlobalVariableSet(K(t, f), v); }

public:
   void              Init(CTrade *trade, CRRLogger *log, const long magic) { m_trade = trade; m_log = log; m_magic = magic; }

   //--- called once when a position of ours appears (fill detected)
   void              Register(const ulong ticket, const double entry, const double sl, const double vol, const double atr)
     {
      if(GlobalVariableCheck(K(ticket, "r"))) return;   // already registered (restart)
      S(ticket, "r", MathAbs(entry - sl));
      S(ticket, "vol0", vol);
      S(ticket, "stage", 0);
      S(ticket, "atr", atr);
     }

   void              Forget(const ulong ticket)
     {
      string f[4] = {"r", "vol0", "stage", "atr"};
      for(int i = 0; i < 4; i++) GlobalVariableDel(K(ticket, f[i]));
     }

   //--- manage all our positions; call on each new M1 bar (uses the last CLOSED M1 bar)
   void              OnNewM1Bar(const RRMgmtParams &p)
     {
      MqlRates b[];
      if(CopyRates(_Symbol, PERIOD_M1, 1, 1, b) != 1) return;
      double bid_close = b[0].close;
      double spread = SymbolInfoInteger(_Symbol, SYMBOL_SPREAD) * _Point;
      MqlDateTime now; TimeToStruct(TimeCurrent(), now);
      int mod = now.hour * 60 + now.min;
      double vstep = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
      double vmin = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
      for(int i = PositionsTotal() - 1; i >= 0; i--)
        {
         ulong t = PositionGetTicket(i);
         if(t == 0 || PositionGetInteger(POSITION_MAGIC) != m_magic || PositionGetString(POSITION_SYMBOL) != _Symbol)
            continue;
         int side = (PositionGetInteger(POSITION_TYPE) == POSITION_TYPE_BUY) ? 1 : -1;
         double entry = PositionGetDouble(POSITION_PRICE_OPEN);
         double sl = PositionGetDouble(POSITION_SL), tp = PositionGetDouble(POSITION_TP);
         double vol = PositionGetDouble(POSITION_VOLUME);
         string cell = PositionGetString(POSITION_COMMENT);
         double R = G(t, "r", 0);
         if(R <= 0) { Register(t, entry, sl, vol, 0); R = G(t, "r", MathAbs(entry - sl)); }
         double vol0 = G(t, "vol0", vol);
         int stage = (int)G(t, "stage", 0);
         datetime opened = (datetime)PositionGetInteger(POSITION_TIME);
         //--- time-based exits
         bool fri = (now.day_of_week == 5 && mod >= p.friday_close_min);
         bool too_old = (TimeCurrent() - opened) >= p.max_hold_min * 60;
         if(fri || too_old)
           {
            if(m_trade.PositionClose(t))
               m_log.Trade("CLOSE", t, cell, side, vol, bid_close, sl, tp, 0, fri ? "friday cutoff" : "max hold");
            continue;
           }
         //--- profit in R on the closed bar (long exits at bid, short exits at ask)
         double cls = (side == 1) ? bid_close : bid_close + spread;
         double r_now = (cls - entry) * side / R;
         if(stage == 0 && p.p1_frac > 0 && r_now >= p.p1_r)
           {
            double q = MathFloor(vol0 * p.p1_frac / vstep + 1e-9) * vstep;
            if(q >= vmin && vol - q >= vmin - 1e-9)
              {
               if(m_trade.PositionClosePartial(t, q))
                  m_log.Trade("PARTIAL1", t, cell, side, q, cls, sl, tp, 0, StringFormat("%.2fR", r_now));
              }
            stage = 1; S(t, "stage", 1);
            if(p.be_after_p1 && (sl - entry) * side < 0)
              {
               if(m_trade.PositionModify(t, NormalizeDouble(entry, _Digits), tp))
                 { m_log.Trade("MODIFY", t, cell, side, vol, cls, entry, tp, 0, "break-even after p1"); sl = entry; }
               else
                  m_log.Event(StringFormat("BE modify failed ticket %I64u retcode %d", t, m_trade.ResultRetcode()));
              }
           }
         if(stage == 1 && p.p2_frac > 0 && r_now >= p.p2_r)
           {
            if(!PositionSelectByTicket(t)) continue;
            vol = PositionGetDouble(POSITION_VOLUME);
            double q = MathFloor(vol0 * p.p2_frac / vstep + 1e-9) * vstep;
            if(q >= vmin && vol - q >= vmin - 1e-9)
              {
               if(m_trade.PositionClosePartial(t, q))
                  m_log.Trade("PARTIAL2", t, cell, side, q, cls, sl, tp, 0, StringFormat("%.2fR", r_now));
              }
            stage = 2; S(t, "stage", 2);
           }
         //--- trailing after p1 (optional)
         if(p.trail_atr > 0 && stage >= 1)
           {
            double atr = G(t, "atr", 0);
            if(atr > 0)
              {
               double ns = NormalizeDouble(cls - side * p.trail_atr * atr, _Digits);
               if((ns - sl) * side > 0 && m_trade.PositionModify(t, ns, tp))
                  m_log.Trade("MODIFY", t, cell, side, vol, cls, ns, tp, 0, "trail");
              }
           }
        }
     }
  };

#endif
//+------------------------------------------------------------------+
