//+------------------------------------------------------------------+
//| RaptorRecon - Telegram notifications (separate from trading).     |
//| Uses WebRequest: add https://api.telegram.org to                  |
//| Tools > Options > Expert Advisors > "Allow WebRequest for URL".   |
//| WebRequest does NOT work in the Strategy Tester (MT5 limitation): |
//| messages are then only written to the events log.                 |
//| The bot token is an EA INPUT: never hard-code it in the source.   |
//| STATUS: written, NOT tested (no MT5 terminal in the build env).   |
//+------------------------------------------------------------------+
#ifndef RAPTORRECON_TELEGRAM_MQH
#define RAPTORRECON_TELEGRAM_MQH

class CRRTelegram
  {
private:
   bool              m_enabled;
   string            m_token, m_chat;
   string            UrlEncode(const string s)
     {
      uchar b[]; StringToCharArray(s, b, 0, WHOLE_ARRAY, CP_UTF8);
      string out = "";
      for(int i = 0; i < ArraySize(b) - 1; i++)
        {
         uchar c = b[i];
         if((c >= '0' && c <= '9') || (c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') || c == '-' || c == '_' || c == '.' || c == '~')
            out += CharToString(c);
         else
            out += StringFormat("%%%02X", c);
        }
      return out;
     }
public:
   void              Init(const bool enabled, const string token, const string chat)
     { m_enabled = enabled && StringLen(token) > 0 && StringLen(chat) > 0; m_token = token; m_chat = chat; }
   bool              Enabled() const { return m_enabled; }
   //--- returns false on any failure; trading never depends on this call
   bool              Send(const string text)
     {
      if(!m_enabled || MQLInfoInteger(MQL_TESTER)) return false;
      string url = "https://api.telegram.org/bot" + m_token + "/sendMessage";
      string body = "chat_id=" + m_chat + "&text=" + UrlEncode(text);
      char data[], res[]; string hdr;
      StringToCharArray(body, data, 0, StringLen(body), CP_UTF8);
      ResetLastError();
      int code = WebRequest("POST", url, "Content-Type: application/x-www-form-urlencoded\r\n", 5000, data, res, hdr);
      if(code != 200)
        {
         PrintFormat("RaptorRecon Telegram: send failed http=%d err=%d (is api.telegram.org allowed in WebRequest?)", code, GetLastError());
         return false;
        }
      return true;
     }
  };

#endif
