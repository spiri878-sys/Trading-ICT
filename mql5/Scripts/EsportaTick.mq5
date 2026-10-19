//+------------------------------------------------------------------+
//|                                                  EsportaTick.mq5 |
//| Esporta i tick (bid/ask) del simbolo del grafico, giorno per     |
//| giorno, in file CSV dentro MQL5\Files\Tick\ (un file al giorno). |
//| Uso: trascinalo sul grafico XAUUSD, scegli le date, OK.          |
//| Trovi i file da MetaTrader: File -> Apri cartella dati ->        |
//| MQL5 -> Files -> Tick. Comprimili in zip e mandali.              |
//+------------------------------------------------------------------+
#property copyright "Progetto Trading-ICT - uso personale"
#property version   "1.00"
#property script_show_inputs

input datetime InpFrom = D'2026.01.01 00:00';  // Dal giorno
input datetime InpTo   = D'2026.02.01 00:00';  // Al giorno (escluso)

void OnStart()
{
   FolderCreate("Tick");
   int days = 0;
   long total = 0;
   for(datetime d = InpFrom; d < InpTo; d += 86400)
   {
      MqlTick ticks[];
      ResetLastError();
      int n = -1;
      for(int tries = 0; tries < 10 && n < 0; tries++)   // il terminale a volte deve prima scaricarli dal server
      {
         n = CopyTicksRange(_Symbol, ticks, COPY_TICKS_ALL, (ulong)d * 1000, (ulong)(d + 86400) * 1000 - 1);
         if(n < 0) Sleep(2000);
      }
      if(n <= 0) { PrintFormat("%s: nessun tick (errore %d)", TimeToString(d, TIME_DATE), GetLastError()); continue; }
      MqlDateTime t; TimeToStruct(d, t);
      string sym = _Symbol;
      StringReplace(sym, ".", "_");
      string fn = StringFormat("Tick\\%s_%04d%02d%02d.csv", sym, t.year, t.mon, t.day);
      int h = FileOpen(fn, FILE_WRITE | FILE_ANSI | FILE_TXT);
      if(h == INVALID_HANDLE) { Print("non riesco a scrivere ", fn); continue; }
      FileWriteString(h, "time_msc,bid,ask\n");
      for(int i = 0; i < n; i++)
         FileWriteString(h, StringFormat("%I64d,%s,%s\n", ticks[i].time_msc,
                                         DoubleToString(ticks[i].bid, _Digits), DoubleToString(ticks[i].ask, _Digits)));
      FileClose(h);
      days++;
      total += n;
      PrintFormat("%s: %d tick salvati", TimeToString(d, TIME_DATE), n);
      Comment(StringFormat("EsportaTick: %s fatto (%d giorni, %I64d tick)", TimeToString(d, TIME_DATE), days, total));
   }
   Comment("");
   PrintFormat("EsportaTick finito: %d giorni, %I64d tick, in MQL5\\Files\\Tick", days, total);
   MessageBox(StringFormat("Fatto: %d giorni, %I64d tick.\nFile -> Apri cartella dati -> MQL5 -> Files -> Tick", days, total), "EsportaTick");
}
//+------------------------------------------------------------------+
