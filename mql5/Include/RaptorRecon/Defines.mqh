//+------------------------------------------------------------------+
//| RaptorRecon - shared enums and structures                         |
//| Independent research reconstruction. NOT ICT RAPTOR AI PRIME.     |
//+------------------------------------------------------------------+
#ifndef RAPTORRECON_DEFINES_MQH
#define RAPTORRECON_DEFINES_MQH

#define RR_VERSION "0.1.0"

//--- stop-loss selector (independent from the lot selector)
enum ENUM_RR_STOP_MODE
  {
   RR_STOP_STRUCTURAL = 0, // Structural (setup invalidation + ATR buffer)
   RR_STOP_FIXED      = 1, // Fixed distance in PRICE units (XAUUSD: 1.00 = 100 points)
   RR_STOP_PERCENT    = 2, // Percent of the ENTRY PRICE (not of capital)
   RR_STOP_ATR        = 3  // Multiple of signal-timeframe ATR(14)
  };

//--- lot selector
enum ENUM_RR_LOT_MODE
  {
   RR_LOT_FIXED   = 0, // Fixed lot
   RR_LOT_RISK    = 1  // Lot from % risk (loss at stop incl. costs)
  };

enum ENUM_RR_RISK_BASE
  {
   RR_BASE_BALANCE = 0, // Balance
   RR_BASE_EQUITY  = 1  // Equity
  };

//--- strategy profile. FAITHFUL and EXPERIMENTAL are kept separate on purpose.
enum ENUM_RR_PROFILE
  {
   RR_PROFILE_FAITHFUL_M5   = 0, // A: evidence-based reconstruction (5 ICT cells, M5, ladder 0.7/2/4R)
   RR_PROFILE_EXPERIMENTAL  = 1, // B: H1 continuation (PPK+UNIOF, market entry, 3R/48h) - FAILED validation
   RR_PROFILE_WYCKOFF_BENCH = 2  // Wyckoff spring/upthrust benchmark (same execution)
  };

//--- candidate signal produced by a cell
struct RRSignal
  {
   datetime          bar_time;     // open time of the closed decision bar
   int               side;         // +1 long / -1 short
   bool              market;       // true: market at next bar, false: limit
   double            price;        // limit price (bid-chart price)
   double            sl_struct;    // structural stop (incl. buffer)
   double            atr;          // ATR(14) of the signal timeframe
   int               expiry_bars;  // validity in signal-timeframe bars
   string            cell;         // PPK/OTEOF/PO3/UNIOF/LS/WYCKOFF
   string            reason;       // human readable trigger description
  };

#endif
//+------------------------------------------------------------------+
