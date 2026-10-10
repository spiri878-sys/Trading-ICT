//+------------------------------------------------------------------+
//| RaptorRecon - ICT cells + Wyckoff benchmark (mirror of             |
//| python/raptor/strategies/{ict,wyckoff}.py). Evaluated on the LAST  |
//| CLOSED bar i = n-1 of the signal timeframe.                         |
//| Cell rules are an independent reconstruction: only cell NAMES are  |
//| documented by the vendor (see docs/evidence_register.md).          |
//+------------------------------------------------------------------+
#ifndef RAPTORRECON_CELLS_MQH
#define RAPTORRECON_CELLS_MQH

#include "MarketModel.mqh"

struct RRCellParams
  {
   double            min_disp;     // displacement body >= min_disp * ATR
   double            min_fvg;      // FVG size >= min_fvg * ATR
   double            sl_buf_atr;   // structural stop buffer in ATR
   double            min_r_atr;    // reject risk < min_r_atr * ATR
   double            max_r_atr;    // reject risk > max_r_atr * ATR
   double            ote_level;    // OTE retracement
   int               expiry;       // pending validity (bars)
   bool              market_entry; // enter at market instead of the retracement limit
  };

class CRRCells
  {
private:
   bool              RiskOk(const RRSignal &s, const RRCellParams &p)
     {
      double r = (s.price - s.sl_struct) * s.side;
      return r >= p.min_r_atr * s.atr && r <= p.max_r_atr * s.atr;
     }
   bool              Push(RRSignal &out[], RRSignal &s, const RRCellParams &p, const CRRStructure &st)
     {
      if(p.market_entry && s.cell != "OTEOF")
        {
         s.market = true;
         s.price = st.r[st.n - 1].close;
        }
      if(!RiskOk(s, p))
         return false;
      int k = ArraySize(out);
      ArrayResize(out, k + 1);
      out[k] = s;
      return true;
     }
   //--- most recent FVG (bar i, else i-1) in the given direction
   bool              FvgAtBreak(const CRRStructure &st, const int i, const int dir, const double min_fvg, double &top, double &bot)
     {
      double t, b;
      for(int j = i; j >= i - 1; j--)
        {
         bool ok = (dir == 1) ? st.BullFvg(j, t, b) : st.BearFvg(j, t, b);
         if(ok)
           {
            if(t - b >= min_fvg * st.atr[i]) { top = t; bot = b; return true; }
            return false;   // python: the most recent FVG is used; if too small -> no signal
           }
        }
      return false;
     }
   void              Base(RRSignal &s, const CRRStructure &st, const int i, const string cell, const int side, const int expiry)
     {
      s.bar_time = st.r[i].time; s.side = side; s.market = false; s.atr = st.atr[i];
      s.expiry_bars = expiry; s.cell = cell; s.reason = "";
     }

public:
   void              PPK(const CRRStructure &st, const RRCellParams &p, RRSignal &out[])
     {
      int i = st.n - 1;
      if(st.brk[i] == 0 || st.atr[i] == EMPTY_VALUE) return;
      if(st.DispBody(i) < p.min_disp * st.atr[i]) return;
      int d = st.brk[i];
      double top, bot;
      if(!FvgAtBreak(st, i, d, p.min_fvg, top, bot)) return;
      RRSignal s; Base(s, st, i, "PPK", d, p.expiry);
      double buf = p.sl_buf_atr * st.atr[i];
      s.price = (d == 1) ? top : bot;                       // proximal FVG edge = first retracement touch
      s.sl_struct = (d == 1) ? st.leg_lo[i] - buf : st.leg_hi[i] + buf;
      s.reason = StringFormat("break%s disp=%.2fATR fvg=[%.2f,%.2f]", (st.mss[i] ? "(MSS)" : ""), st.DispBody(i) / st.atr[i], bot, top);
      Push(out, s, p, st);
     }

   void              OTEOF(const CRRStructure &st, const RRCellParams &p, RRSignal &out[])
     {
      int i = st.n - 1;
      if(st.brk[i] == 0 || st.atr[i] == EMPTY_VALUE) return;
      if(st.DispBody(i) < p.min_disp * st.atr[i]) return;
      int d = st.brk[i];
      double lo = st.leg_lo[i], hi = st.leg_hi[i], buf = p.sl_buf_atr * st.atr[i];
      RRSignal s; Base(s, st, i, "OTEOF", d, p.expiry);
      s.price = (d == 1) ? hi - p.ote_level * (hi - lo) : lo + p.ote_level * (hi - lo);
      s.sl_struct = (d == 1) ? lo - buf : hi + buf;
      s.reason = StringFormat("OTE %.3f of leg [%.2f,%.2f]", p.ote_level, lo, hi);
      Push(out, s, p, st);
     }

   void              PO3(const CRRStructure &st, const RRCellParams &p, RRSignal &out[], const int ny_offset)
     {
      int i = st.n - 1, win = 24;
      if(st.brk[i] == 0 || !st.mss[i] || st.atr[i] == EMPTY_VALUE) return;
      int nym = RRNyMinutes(st.r[i].time, ny_offset);
      if(nym < 120 || nym >= 660) return;                    // NY 02:00-11:00
      if(st.DispBody(i) < p.min_disp * st.atr[i]) return;
      int d = st.brk[i];
      bool raid = false;
      double ext_lo = DBL_MAX, ext_hi = -DBL_MAX;
      for(int j = MathMax(0, i - win + 1); j <= i; j++)
        {
         RRLiquidity L;
         if(RRLiquidityAt(st, j, L))
            if((d == 1 && L.sweep_asia_lo) || (d == -1 && L.sweep_asia_hi)) raid = true;
         ext_lo = MathMin(ext_lo, st.r[j].low); ext_hi = MathMax(ext_hi, st.r[j].high);
        }
      if(!raid) return;
      double top, bot;
      if(!FvgAtBreak(st, i, d, p.min_fvg, top, bot)) return;
      RRSignal s; Base(s, st, i, "PO3", d, p.expiry);
      double buf = p.sl_buf_atr * st.atr[i];
      s.price = (d == 1) ? top : bot;
      s.sl_struct = (d == 1) ? ext_lo - buf : ext_hi + buf;
      s.reason = "Asia raid + MSS (Judas -> distribution)";
      Push(out, s, p, st);
     }

   void              UNIOF(const CRRStructure &st, const RRCellParams &p, RRSignal &out[])
     {
      int i = st.n - 1;
      if(st.brk[i] == 0 || !st.mss[i] || st.zlo[i] == EMPTY_VALUE || st.atr[i] == EMPTY_VALUE) return;
      int d = st.brk[i];
      double top, bot;
      if(!FvgAtBreak(st, i, d, p.min_fvg, top, bot)) return;
      double ohi = MathMin(top, st.zhi[i]), olo = MathMax(bot, st.zlo[i]);
      if(ohi <= olo) return;
      RRSignal s; Base(s, st, i, "UNIOF", d, p.expiry);
      double buf = p.sl_buf_atr * st.atr[i];
      s.price = (d == 1) ? ohi : olo;
      s.sl_struct = (d == 1) ? st.leg_lo[i] - buf : st.leg_hi[i] + buf;
      s.reason = StringFormat("unicorn breaker[%.2f,%.2f] x fvg[%.2f,%.2f]", st.zlo[i], st.zhi[i], bot, top);
      Push(out, s, p, st);
     }

   void              LS(const CRRStructure &st, const RRCellParams &p, RRSignal &out[])
     {
      int i = st.n - 1;
      if(st.atr[i] == EMPTY_VALUE) return;
      RRLiquidity L;
      if(!RRLiquidityAt(st, i, L)) return;
      double c = st.r[i].close, h = st.r[i].high, l = st.r[i].low;
      double lvl = 0; int d = 0;
      if(L.sweep_hi)
        {
         if(h > L.pdh && c < L.pdh) lvl = L.pdh;
         else if(L.asia_hi > 0 && c < L.asia_hi) lvl = L.asia_hi;
         if(lvl > 0) d = -1;
        }
      if(d == 0 && L.sweep_lo)
        {
         if(l < L.pdl && c > L.pdl) lvl = L.pdl;
         else if(L.asia_lo > 0 && c > L.asia_lo) lvl = L.asia_lo;
         if(lvl > 0) d = 1;
        }
      if(d == 0) return;
      RRSignal s; Base(s, st, i, "LS", d, p.expiry);
      double buf = p.sl_buf_atr * st.atr[i];
      s.price = (lvl + c) / 2.0;
      s.sl_struct = (d == 1) ? l - buf : h + buf;
      s.reason = StringFormat("sweep of %.2f, close back inside", lvl);
      Push(out, s, p, st);
     }

   void              Wyckoff(const CRRStructure &st, const RRCellParams &p, RRSignal &out[], const double h1_atr)
     {
      int i = st.n - 1, nb = 48;
      if(i < nb + 1 || st.atr[i] == EMPTY_VALUE || h1_atr <= 0) return;
      double rh = -DBL_MAX, rl = DBL_MAX;
      for(int j = i - nb; j < i; j++) { rh = MathMax(rh, st.r[j].high); rl = MathMin(rl, st.r[j].low); }
      double height = rh - rl;
      if(height > 3.0 * h1_atr || height < 1.0 * h1_atr) return;
      double a = st.atr[i], pen = 0.2 * a, h = st.r[i].high, l = st.r[i].low, c = st.r[i].close, mid = (h + l) / 2;
      int d = 0;
      if(l <= rl - pen && c > rl && c >= mid) d = 1;
      else if(h >= rh + pen && c < rh && c <= mid) d = -1;
      if(d == 0) return;
      RRSignal s; Base(s, st, i, "WYCKOFF", d, 1);
      s.market = true; s.price = c;
      double buf = p.sl_buf_atr * a;
      s.sl_struct = (d == 1) ? l - buf : h + buf;
      s.reason = StringFormat("%s of range [%.2f,%.2f]", (d == 1 ? "spring" : "upthrust"), rl, rh);
      if(RiskOk(s, p)) { int k = ArraySize(out); ArrayResize(out, k + 1); out[k] = s; }
     }
  };

#endif
//+------------------------------------------------------------------+
