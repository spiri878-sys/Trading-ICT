//+------------------------------------------------------------------+
//| RaptorRecon - stop selector, lot selector, account protection      |
//| No martingale, no grid, no lot progression after losses.           |
//+------------------------------------------------------------------+
#ifndef RAPTORRECON_RISK_MQH
#define RAPTORRECON_RISK_MQH

#include "Defines.mqh"

string RRStopModeName(const ENUM_RR_STOP_MODE m)
  {
   switch(m)
     {
      case RR_STOP_STRUCTURAL: return "STRUCTURAL";
      case RR_STOP_FIXED:      return "FIXED";
      case RR_STOP_PERCENT:    return "PERCENT";
      case RR_STOP_ATR:        return "ATR";
     }
   return "?";
  }
string RRLotModeName(const ENUM_RR_LOT_MODE m) { return m == RR_LOT_FIXED ? "FIXED" : "RISK_PERCENT"; }

//--- Stop price from the selected mode. Formulas (docs/stop_and_lot.md):
//    FIXED:      sl = entry - side * dist                (dist in price units; XAUUSD 2 digits: 1.00 = 100 points)
//    PERCENT:    sl = entry * (1 - side * pct / 100)     (percentage of the ENTRY PRICE)
//    ATR:        sl = entry - side * mult * ATR(14, signal TF)
//    STRUCTURAL: sl = setup invalidation level +/- buffer (from the cell)
double RRStopPrice(const ENUM_RR_STOP_MODE mode, const int side, const double entry, const double sl_struct,
                   const double fixed_dist, const double pct, const double atr_mult, const double atr, string &formula)
  {
   double sl = 0;
   switch(mode)
     {
      case RR_STOP_FIXED:
         sl = entry - side * fixed_dist;
         formula = StringFormat("FIXED: %.2f %s %.2f", entry, (side == 1 ? "-" : "+"), fixed_dist);
         break;
      case RR_STOP_PERCENT:
         sl = entry * (1.0 - side * pct / 100.0);
         formula = StringFormat("PERCENT: %.2f x (1 %s %.3f%%)", entry, (side == 1 ? "-" : "+"), pct);
         break;
      case RR_STOP_ATR:
         sl = entry - side * atr_mult * atr;
         formula = StringFormat("ATR: %.2f %s %.2f x %.2f", entry, (side == 1 ? "-" : "+"), atr_mult, atr);
         break;
      default:
         sl = sl_struct;
         formula = StringFormat("STRUCTURAL: %.2f", sl_struct);
     }
   return NormalizeDouble(sl, _Digits);
  }

//--- broker constraints on the stop: we NEVER widen the stop to fit the broker; we reject.
bool RRStopValid(const int side, const double entry, const double sl, string &why)
  {
   if((entry - sl) * side <= 0) { why = "stop on the wrong side of entry"; return false; }
   long lvl = SymbolInfoInteger(_Symbol, SYMBOL_TRADE_STOPS_LEVEL);
   double min_dist = lvl * _Point;
   if(MathAbs(entry - sl) < min_dist)
     { why = StringFormat("stop distance %.2f < broker stops level %.2f", MathAbs(entry - sl), min_dist); return false; }
   return true;
  }

//--- money lost per 1.0 lot if the stop is hit (account currency, via OrderCalcProfit) + round-turn commission
double RRLossPerLot(const int side, const double entry, const double sl, const double slip, const double comm_per_lot_side)
  {
   double profit = 0;
   ENUM_ORDER_TYPE t = (side == 1) ? ORDER_TYPE_BUY : ORDER_TYPE_SELL;
   double exit_px = sl - side * slip;
   if(!OrderCalcProfit(t, _Symbol, 1.0, entry, exit_px, profit))
      return -1;
   return MathAbs(profit) + 2.0 * comm_per_lot_side;
  }

double RRFloorStep(const double x, const double step) { return MathFloor(x / step + 1e-9) * step; }

//--- lot selector. Returns false (with reason) instead of silently changing the requested lot.
bool RRLot(const ENUM_RR_LOT_MODE mode, const double fixed_lot, const double risk_pct, const ENUM_RR_RISK_BASE base,
           const double risk_mult, const double loss_per_lot, double &lot, double &risk_money, string &why)
  {
   double vmin = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
   double vmax = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX);
   double vstep = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
   if(loss_per_lot <= 0) { why = "cannot compute loss per lot"; return false; }
   if(mode == RR_LOT_FIXED)
     {
      lot = fixed_lot;
      if(lot < vmin - 1e-9 || lot > vmax + 1e-9 || MathAbs(RRFloorStep(lot, vstep) - lot) > 1e-7)
        { why = StringFormat("fixed lot %.2f not allowed (min %.2f max %.2f step %.2f)", lot, vmin, vmax, vstep); return false; }
     }
   else
     {
      double b = (base == RR_BASE_EQUITY) ? AccountInfoDouble(ACCOUNT_EQUITY) : AccountInfoDouble(ACCOUNT_BALANCE);
      double allowed = b * risk_pct / 100.0 * risk_mult;
      lot = RRFloorStep(allowed / loss_per_lot, vstep);
      if(lot > vmax) lot = RRFloorStep(vmax, vstep);
      if(lot < vmin - 1e-9)
        { why = StringFormat("min lot %.2f would risk %.2f > allowed %.2f", vmin, vmin * loss_per_lot, allowed); return false; }
     }
   risk_money = lot * loss_per_lot;
   return true;
  }

//--- margin check (fixed lot is NOT reduced if margin is insufficient)
bool RRMarginOk(const int side, const double lot, const double price, string &why)
  {
   double m = 0;
   if(!OrderCalcMargin(side == 1 ? ORDER_TYPE_BUY : ORDER_TYPE_SELL, _Symbol, lot, price, m))
     { why = "OrderCalcMargin failed"; return false; }
   double free = AccountInfoDouble(ACCOUNT_MARGIN_FREE);
   if(m > free) { why = StringFormat("margin %.2f > free margin %.2f", m, free); return false; }
   return true;
  }

//+------------------------------------------------------------------+
//| Account protection and "breathing" risk (risk-% mode only).        |
//| Multiplier: 1 until DD >= dd_full; linear down to mult_min at      |
//| dd_min; back to 1 after `recover_wins` winning trades or a new     |
//| balance high. Never above 1 (base risk is the maximum).            |
//| State persisted in GlobalVariables (survives terminal restarts).   |
//+------------------------------------------------------------------+
class CRRAccountGuard
  {
private:
   string            m_key;
   double            Gv(const string k, const double def)
     {
      string n = m_key + k;
      if(!GlobalVariableCheck(n)) GlobalVariableSet(n, def);
      return GlobalVariableGet(n);
     }
   void              Set(const string k, const double v) { GlobalVariableSet(m_key + k, v); }
public:
   void              Init(const long magic) { m_key = StringFormat("RR_%I64d_%s_", magic, _Symbol); Gv("peak", AccountInfoDouble(ACCOUNT_BALANCE)); }
   double            Peak() { return Gv("peak", AccountInfoDouble(ACCOUNT_BALANCE)); }
   void              OnClosedTrade(const double net)
     {
      double bal = AccountInfoDouble(ACCOUNT_BALANCE);
      if(Gv("reduced", 0) > 0 && net > 0) Set("wins", Gv("wins", 0) + 1);
      if(bal >= Peak()) { Set("peak", bal); Set("reduced", 0); Set("wins", 0); }
      // daily realised P&L
      MqlDateTime t; TimeToStruct(TimeCurrent(), t);
      double day = t.year * 10000 + t.mon * 100 + t.day;
      if(Gv("day", 0) != day) { Set("day", day); Set("day_pnl", 0); }
      Set("day_pnl", Gv("day_pnl", 0) + net);
     }
   double            RiskMultiplier(const bool enabled, const double dd_full, const double dd_min, const double mult_min, const int recover_wins)
     {
      if(!enabled) return 1.0;
      double peak = Peak(), bal = AccountInfoDouble(ACCOUNT_BALANCE);
      double dd = (peak - bal) / peak * 100.0;
      if(dd <= dd_full) return 1.0;
      if(Gv("reduced", 0) == 0) { Set("reduced", 1); Set("wins", 0); }
      if(Gv("wins", 0) >= recover_wins) return 1.0;
      double m = 1.0 - (1.0 - mult_min) * MathMin(1.0, (dd - dd_full) / (dd_min - dd_full));
      return MathMax(mult_min, MathMin(1.0, m));
     }
   bool              DailyLimitHit(const double daily_loss_pct)
     {
      if(daily_loss_pct <= 0) return false;
      MqlDateTime t; TimeToStruct(TimeCurrent(), t);
      double day = t.year * 10000 + t.mon * 100 + t.day;
      if(Gv("day", 0) != day) { Set("day", day); Set("day_pnl", 0); Set("day_start", AccountInfoDouble(ACCOUNT_BALANCE)); }
      double start = Gv("day_start", AccountInfoDouble(ACCOUNT_BALANCE));
      return Gv("day_pnl", 0) <= -start * daily_loss_pct / 100.0;
     }
   bool              MaxDdHit(const double max_dd_pct)
     {
      if(max_dd_pct <= 0) return false;
      double eq = AccountInfoDouble(ACCOUNT_EQUITY);
      return eq <= Peak() * (1.0 - max_dd_pct / 100.0);
     }
  };

#endif
//+------------------------------------------------------------------+
