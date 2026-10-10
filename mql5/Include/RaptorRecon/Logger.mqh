//+------------------------------------------------------------------+
//| RaptorRecon - CSV logging (signals, trades, events)               |
//| Files are written to <terminal data>/MQL5/Files/RaptorRecon/      |
//| (in the Strategy Tester: <agent>/MQL5/Files/RaptorRecon/).        |
//+------------------------------------------------------------------+
#ifndef RAPTORRECON_LOGGER_MQH
#define RAPTORRECON_LOGGER_MQH

#include "Defines.mqh"

class CRRLogger
  {
private:
   string            m_prefix;
   string            Path(const int kind)
     {
      string names[3] = {"signals", "trades", "events"};
      return "RaptorRecon\\" + m_prefix + "_" + names[kind] + ".csv";
     }
   void              Write(const int kind, const string header, const string line)
     {
      string p = Path(kind);
      int h = FileOpen(p, FILE_READ | FILE_WRITE | FILE_TXT | FILE_ANSI | FILE_SHARE_READ);
      if(h == INVALID_HANDLE)
        {
         PrintFormat("RaptorRecon logger: cannot open %s (err %d)", p, GetLastError());
         return;
        }
      if(FileSize(h) == 0)
         FileWriteString(h, header + "\r\n");
      FileSeek(h, 0, SEEK_END);
      FileWriteString(h, line + "\r\n");
      FileClose(h);
     }
public:
   void              Init(const string prefix) { m_prefix = prefix; }

   //--- every candidate, accepted or rejected, with the reason
   void              Signal(const RRSignal &s, const string status, const string detail,
                            const string stop_mode, const string lot_mode, const double lot,
                            const double sl, const double risk_money, const double spread)
     {
      string line = StringFormat("%s;%s;%s;%s;%d;%s;%.2f;%.2f;%.2f;%d;%s;%s;%s;%s;%.2f;%.2f;%.2f;%.2f;%s",
                                 TimeToString(TimeCurrent(), TIME_DATE | TIME_SECONDS), RR_VERSION, _Symbol,
                                 TimeToString(s.bar_time, TIME_DATE | TIME_MINUTES), s.side, s.cell, s.price,
                                 s.sl_struct, s.atr, s.expiry_bars, (s.market ? "market" : "limit"), status,
                                 stop_mode, lot_mode, lot, sl, risk_money, spread, detail + " | " + s.reason);
      Write(0, "time;version;symbol;bar_time;side;cell;price;sl_struct;atr;expiry;otype;status;stop_mode;lot_mode;lot;sl;risk_money;spread;detail", line);
     }
   //--- position lifecycle: OPEN / PARTIAL / MODIFY / CLOSE
   void              Trade(const string evt, const ulong ticket, const string cell, const int side,
                           const double volume, const double price, const double sl, const double tp,
                           const double profit, const string note)
     {
      string line = StringFormat("%s;%s;%s;%I64u;%s;%d;%.2f;%.2f;%.2f;%.2f;%.2f;%s",
                                 TimeToString(TimeCurrent(), TIME_DATE | TIME_SECONDS), RR_VERSION, evt, ticket,
                                 cell, side, volume, price, sl, tp, profit, note);
      Write(1, "time;version;event;ticket;cell;side;volume;price;sl;tp;profit;note", line);
     }
   void              Event(const string what)
     {
      Write(2, "time;version;event", StringFormat("%s;%s;%s", TimeToString(TimeCurrent(), TIME_DATE | TIME_SECONDS), RR_VERSION, what));
      Print("RaptorRecon: ", what);
     }
  };

#endif
//+------------------------------------------------------------------+
