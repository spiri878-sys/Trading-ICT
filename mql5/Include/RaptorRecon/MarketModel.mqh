//+------------------------------------------------------------------+
//| RaptorRecon - market structure, FVG, liquidity, HTF context        |
//| Mirrors python/raptor/{indicators,setups}.py. Uses CLOSED bars only|
//| (CopyRates from shift 1). Arrays are chronological: [0] = oldest.  |
//+------------------------------------------------------------------+
#ifndef RAPTORRECON_MARKETMODEL_MQH
#define RAPTORRECON_MARKETMODEL_MQH

#include "Defines.mqh"

//--- Wilder ATR (same formula as python raptor.indicators.atr)
void RRAtr(const MqlRates &r[], const int n, const int period, double &out[])
  {
   ArrayResize(out, n);
   ArrayInitialize(out, EMPTY_VALUE);
   if(n < period + 1)
      return;
   double tr[];
   ArrayResize(tr, n);
   tr[0] = r[0].high - r[0].low;
   for(int i = 1; i < n; i++)
      tr[i] = MathMax(r[i].high - r[i].low, MathMax(MathAbs(r[i].high - r[i - 1].close), MathAbs(r[i].low - r[i - 1].close)));
   double s = 0;
   for(int i = 0; i < period; i++)
      s += tr[i];
   out[period - 1] = s / period;
   for(int i = period; i < n; i++)
      out[i] = (out[i - 1] * (period - 1) + tr[i]) / period;
  }

void RREma(const MqlRates &r[], const int n, const int period, double &out[])
  {
   ArrayResize(out, n);
   if(n == 0)
      return;
   double a = 2.0 / (period + 1);
   out[0] = r[0].close;
   for(int i = 1; i < n; i++)
      out[i] = a * r[i].close + (1 - a) * out[i - 1];
  }

//+------------------------------------------------------------------+
//| Structure engine on one timeframe                                 |
//+------------------------------------------------------------------+
class CRRStructure
  {
public:
   MqlRates          r[];
   int               n;
   double            atr[];
   double            ema50[];
   int               brk[];       // +1 / -1 close through last confirmed swing
   bool              mss[];       // break against previous break direction
   double            leg_lo[], leg_hi[];
   int               brk_swing[];
   double            zlo[], zhi[]; // breaker candle zone at a break

   bool              Load(const string sym, const ENUM_TIMEFRAMES tf, const int bars, const int k)
     {
      ArraySetAsSeries(r, false);
      n = CopyRates(sym, tf, 1, bars, r);   // closed bars only, oldest first
      if(n < 3 * k + 30)
         return false;
      RRAtr(r, n, 14, atr);
      RREma(r, n, 50, ema50);
      Structure(k);
      return true;
     }

   //--- most recent swing confirmed at bar i (pivot p = i-k with k bars on each side)
   void              Structure(const int k)
     {
      ArrayResize(brk, n); ArrayInitialize(brk, 0);
      ArrayResize(mss, n); ArrayInitialize(mss, false);
      ArrayResize(leg_lo, n); ArrayInitialize(leg_lo, EMPTY_VALUE);
      ArrayResize(leg_hi, n); ArrayInitialize(leg_hi, EMPTY_VALUE);
      ArrayResize(brk_swing, n); ArrayInitialize(brk_swing, -1);
      ArrayResize(zlo, n); ArrayInitialize(zlo, EMPTY_VALUE);
      ArrayResize(zhi, n); ArrayInitialize(zhi, EMPTY_VALUE);
      double sh = 0, sl = 0;
      int shi = -1, sli = -1;
      double p_sh = 0, p_sl = 0;
      int p_shi = -1, p_sli = -1;       // values as of bar i-1
      int last_dir = 0, broken_h = -1, broken_l = -1;
      for(int i = 0; i < n; i++)
        {
         // 1) structure break at bar i uses swings known at i-1
         if(i >= 1)
           {
            if(p_shi >= 0 && p_shi != broken_h && r[i].close > p_sh)
              {
               brk[i] = 1; broken_h = p_shi; brk_swing[i] = p_shi;
               int st = (p_sli >= 0 && p_sli < i) ? p_sli : MathMax(0, i - 24);
               Leg(st, i);
               mss[i] = (last_dir == -1); last_dir = 1;
              }
            else if(p_sli >= 0 && p_sli != broken_l && r[i].close < p_sl)
              {
               brk[i] = -1; broken_l = p_sli; brk_swing[i] = p_sli;
               int st = (p_shi >= 0 && p_shi < i) ? p_shi : MathMax(0, i - 24);
               Leg(st, i);
               mss[i] = (last_dir == 1); last_dir = -1;
              }
           }
         // 2) confirm pivot i-k
         int p = i - k;
         if(p >= k)
           {
            bool is_h = true, is_l = true;
            for(int j = p - k; j <= p + k; j++)
              {
               if(j == p) continue;
               if(r[j].high >= r[p].high && (j > p || r[j].high > r[p].high)) is_h = false;
               if(r[j].low <= r[p].low && (j > p || r[j].low < r[p].low)) is_l = false;
              }
            if(is_h) { sh = r[p].high; shi = p; }
            if(is_l) { sl = r[p].low; sli = p; }
           }
         p_sh = sh; p_shi = shi; p_sl = sl; p_sli = sli;
         // 3) breaker zone (last opposite candle at/just before the broken swing)
         if(brk[i] != 0 && brk_swing[i] >= 0)
           {
            int s = brk_swing[i];
            for(int j = s; j > MathMax(-1, s - 6); j--)
              {
               bool bull = r[j].close > r[j].open;
               if((brk[i] == 1 && bull) || (brk[i] == -1 && !bull && r[j].close < r[j].open))
                 { zlo[i] = r[j].low; zhi[i] = r[j].high; break; }
              }
           }
        }
     }

   void              Leg(const int st, const int i)
     {
      double lo = DBL_MAX, hi = -DBL_MAX;
      for(int j = st; j <= i; j++)
        { lo = MathMin(lo, r[j].low); hi = MathMax(hi, r[j].high); }
      leg_lo[i] = lo; leg_hi[i] = hi;
     }

   double            Body(const int i) const { return MathAbs(r[i].close - r[i].open); }
   double            DispBody(const int i) const
     {
      double m = 0;
      for(int j = MathMax(0, i - 2); j <= i; j++) m = MathMax(m, Body(j));
      return m;
     }
   //--- FVG formed by bars i-2,i-1,i
   bool              BullFvg(const int i, double &top, double &bot) const
     {
      if(i < 2) return false;
      if(r[i].low > r[i - 2].high) { top = r[i].low; bot = r[i - 2].high; return true; }
      return false;
     }
   bool              BearFvg(const int i, double &top, double &bot) const
     {
      if(i < 2) return false;
      if(r[i].high < r[i - 2].low) { top = r[i - 2].low; bot = r[i].high; return true; }
      return false;
     }
  };

//+------------------------------------------------------------------+
//| Session helper: server time = New York + 7h on the data audited    |
//| (daily break 23:55->01:01 server). Verify on your broker!          |
//+------------------------------------------------------------------+
int RRNyMinutes(const datetime server_time, const int ny_offset_hours)
  {
   MqlDateTime t;
   TimeToStruct(server_time - ny_offset_hours * 3600, t);
   return t.hour * 60 + t.min;
  }

bool RRInWindows(const int ny_min, const int &from[], const int &to[])
  {
   for(int i = 0; i < ArraySize(from); i++)
      if(ny_min >= from[i] && ny_min < to[i]) return true;
   return false;
  }

//+------------------------------------------------------------------+
//| Liquidity levels of the server day of bar i                         |
//+------------------------------------------------------------------+
struct RRLiquidity
  {
   double            pdh, pdl;      // previous server-day high/low
   double            asia_hi, asia_lo; // server 03:00-07:00 range (valid after 07:00)
   bool              sweep_hi, sweep_lo, sweep_asia_hi, sweep_asia_lo; // first raid of the day at bar i
  };

bool RRLiquidityAt(const CRRStructure &s, const int i, RRLiquidity &L)
  {
   MqlDateTime ti; TimeToStruct(s.r[i].time, ti);
   datetime day0 = s.r[i].time - (ti.hour * 3600 + ti.min * 60 + ti.sec);
   L.pdh = 0; L.pdl = 0; L.asia_hi = 0; L.asia_lo = 0;
   L.sweep_hi = L.sweep_lo = L.sweep_asia_hi = L.sweep_asia_lo = false;
   // previous server day: scan back
   double ph = -DBL_MAX, pl = DBL_MAX; bool have_prev = false;
   datetime prev_day0 = 0;
   int j = i;
   while(j >= 0 && s.r[j].time >= day0) j--;
   if(j < 0) return false;
   MqlDateTime tj; TimeToStruct(s.r[j].time, tj);
   prev_day0 = s.r[j].time - (tj.hour * 3600 + tj.min * 60 + tj.sec);
   for(int q = j; q >= 0 && s.r[q].time >= prev_day0; q--)
     { ph = MathMax(ph, s.r[q].high); pl = MathMin(pl, s.r[q].low); have_prev = true; }
   if(!have_prev) return false;
   L.pdh = ph; L.pdl = pl;
   // today's bars before i and Asia range
   double run_hi = -DBL_MAX, run_lo = DBL_MAX, post_hi = -DBL_MAX, post_lo = DBL_MAX;
   double ah = -DBL_MAX, al = DBL_MAX;
   for(int q = j + 1; q < i; q++)
     {
      MqlDateTime tq; TimeToStruct(s.r[q].time, tq);
      run_hi = MathMax(run_hi, s.r[q].high); run_lo = MathMin(run_lo, s.r[q].low);
      if(tq.hour >= 3 && tq.hour < 7) { ah = MathMax(ah, s.r[q].high); al = MathMin(al, s.r[q].low); }
      if(tq.hour >= 7) { post_hi = MathMax(post_hi, s.r[q].high); post_lo = MathMin(post_lo, s.r[q].low); }
     }
   bool after_asia = (ti.hour >= 7) && ah > -DBL_MAX;
   if(after_asia) { L.asia_hi = ah; L.asia_lo = al; }
   L.sweep_hi = (s.r[i].high > L.pdh && run_hi <= L.pdh);
   L.sweep_lo = (s.r[i].low < L.pdl && run_lo >= L.pdl);
   if(after_asia)
     {
      L.sweep_asia_hi = (s.r[i].high > ah && post_hi <= ah);
      L.sweep_asia_lo = (s.r[i].low < al && post_lo >= al);
      L.sweep_hi = L.sweep_hi || L.sweep_asia_hi;
      L.sweep_lo = L.sweep_lo || L.sweep_asia_lo;
     }
   return true;
  }

//--- ATR(14) of the last CLOSED bar of a higher timeframe (Wilder, same as python)
double RRHtfAtr(const string sym, const ENUM_TIMEFRAMES tf)
  {
   MqlRates h[];
   ArraySetAsSeries(h, false);
   int n = CopyRates(sym, tf, 1, 300, h);
   if(n < 30) return 0;
   double a[];
   RRAtr(h, n, 14, a);
   return a[n - 1];
  }

#endif
//+------------------------------------------------------------------+
