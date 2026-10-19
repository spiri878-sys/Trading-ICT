//+------------------------------------------------------------------+
//|                                               CestoTopBottom.mq5 |
//| Cesto martingala a 5 strategie, scritto da zero per il progetto. |
//| Stessi NOMI di input di "TopBottom Martingale Basket" (stesse    |
//| impostazioni di cesto/griglia/lotti/trailing): il file .set      |
//| dell'utente si carica direttamente (filtro notizie e licenza     |
//| non ci sono: quei campi vengono ignorati).                       |
//|                                                                  |
//| Il codice dell'originale e' chiuso: le ENTRATE sono mie, 5 modi  |
//| di trovare un minimo (BUY) o un massimo (SELL) sulla barra       |
//| chiusa del timeframe della strategia:                            |
//|  S1 frattale: barra centrale piu' bassa/alta di 5 barre          |
//|  S2 RSI: rientra sopra 30 / sotto 70                             |
//|  S3 Bollinger: chiude fuori banda e poi rientra                  |
//|  S4 Stocastico: incrocio sotto 20 / sopra 80                     |
//|  S5 inversione: nuovo minimo/massimo di 20 barre con candela     |
//|     di colore opposto                                            |
//| Ogni strategia ha un cesto BUY e un cesto SELL indipendenti.     |
//| Livelli: quando il prezzo va contro di "distanza" dall'ultimo    |
//| ingresso (fissa x FixedDistMultiplier a ogni livello, ATR o      |
//| lista); lotto x Multiplier (LotMode 0), + Multiplier (LotMode 1) |
//| o lista. Chiusura del cesto: prezzo medio + BasketTPPips, o      |
//| trailing dopo TrailStartPips; MaxBasketDrawdownPercent chiude il |
//| cesto se la perdita aperta supera quella % del saldo.            |
//| Unita': punti del broker x fattore (DigitDetectMode 0 = auto:    |
//| 10 su simboli a 3/5 decimali, 1 sugli altri, oro Axi = 0,01 $).  |
//| "Pips" del TP/trailing = stessa unita' dei punti.                |
//| MaxTrades = 0 -> nessun limite di livelli.                       |
//| InpEntryMode 1 (continuo HFT): ogni cesto chiuso si riapre       |
//| subito, sul lato scelto dall'entrata intelligente.               |
//| Entrata intelligente (InpSmartEntry): il primo ordine del cesto  |
//| solo dal lato della EMA200 H1 e mai dopo uno strappo M1; i cesti |
//| aperti si gestiscono e rinforzano sempre (fase 25).              |
//| NON compilato dall'autore: compilare in MetaEditor, provare in   |
//| demo/tester "Ogni tick basato su tick reali". Serve un conto     |
//| HEDGING.                                                         |
//+------------------------------------------------------------------+
#property copyright "Progetto Trading-ICT - uso personale"
#property version   "1.00"

#include <Trade\Trade.mqh>
#include <Trade\PositionInfo.mqh>

input group "===== General Settings ====="
input long   InpMagicBuy                 = 100101; // Magic base cesti BUY (+10 x strategia)
input long   InpMagicSell                = 100102; // Magic base cesti SELL (+10 x strategia)
input double InpMaxSpreadPoints          = 30.0;   // Spread massimo (punti) per aprire/rinforzare
input int    InpSlippage                 = 20;     // Slippage massimo (punti)
input bool   InpEnableBuyBasket          = true;   // Cesti BUY attivi
input bool   InpEnableSellBasket         = true;   // Cesti SELL attivi
input bool   InpSilentReinforcement      = true;   // Rinforzo senza nuovo segnale (false = serve il segnale)
input double InpMaxBasketDrawdownPercent = 500.0;  // Chiudi il cesto se la perdita aperta supera % del saldo
input bool   InpHideSLTP_FromBroker      = true;   // TP nascosto al broker (false = TP del cesto sulle posizioni)
input bool   InpShowDashboard            = true;   // Pannello sul grafico

input group "===== Broker Digit Detection ====="
input int    InpDigitDetectMode          = 0;      // 0 = auto, altrimenti fattore fisso (punti x fattore)

input group "===== Trading Time Filter (Server Time) ====="
input bool   InpEnableTimeFilter         = false;  // Filtro orario
input string InpTimeStart                = "01:12";
input string InpTimeEnd                  = "23:30";
input bool   InpTimeBlockNewEntries      = true;   // Fuori orario: niente cesti nuovi
input bool   InpTimeBlockReinforcement   = false;  // Fuori orario: niente rinforzi

input group "===== Strategy Selection ====="
input string InpActiveStrategies         = "1,2,3,4,5";

input group "===== Segnali (parametri delle mie entrate) ====="
input int    InpRsiPeriod   = 14;   // S2 periodo RSI
input double InpRsiLow      = 30;   // S2 livello basso
input double InpRsiHigh     = 70;   // S2 livello alto
input int    InpBandsPeriod = 20;   // S3 periodo Bollinger
input double InpBandsDev    = 2.0;  // S3 deviazioni
input int    InpStochK      = 14;   // S4 %K
input int    InpStochD      = 3;    // S4 %D
input int    InpStochSlow   = 3;    // S4 rallentamento
input double InpStochLow    = 20;   // S4 zona bassa
input double InpStochHigh   = 80;   // S4 zona alta
input int    InpS5Lookback  = 20;   // S5 barre per il nuovo minimo/massimo

input group "===== Entrata intelligente (solo il PRIMO ordine del cesto) ====="
input int    InpEntryMode   = 1;         // 0 = segnali delle 5 strategie, 1 = continuo HFT (rientra subito)
input bool   InpSmartEntry  = true;      // BUY solo sopra la tendenza, SELL solo sotto, mai dopo uno strappo
input ENUM_TIMEFRAMES InpTrendTF = PERIOD_H1; // timeframe della tendenza
input int    InpTrendEMA    = 200;       // EMA della tendenza
input int    InpCalmBars    = 15;        // barre M1 controllate per lo strappo
input double InpCalmATR     = 4.0;       // strappo = escursione di quelle barre >= ATR M1(14) x questo

input group "===== Strategy 1 ====="
input ENUM_TIMEFRAMES InpS1_Timeframe        = PERIOD_M1; // S1 timeframe dei segnali
input double InpS1_Lot                       = 0.01;  // S1 lotto iniziale
input double InpS1_Multiplier                = 0.01;  // S1 moltiplicatore (LotMode 0: x, LotMode 1: +)
input int    InpS1_LotMode                   = 1;     // S1 0 = moltiplica, 1 = somma
input string InpS1_CustomLotList             = "";    // S1 lista lotti (es. 0.01,0.02,0.03)
input bool   InpS1_CustomListMultiplyLast    = false; // S1 finita la lista: moltiplica l'ultimo
input double InpS1_CustomListMultiplier      = 1.5;   // S1 moltiplicatore dopo la lista
input double InpS1_MaxLot                    = 0.0;   // S1 lotto massimo (0 = nessuno)
input int    InpS1_MaxTrades                 = 10;    // S1 livelli massimi (0 = nessun limite)
input int    InpS1_GridMethod                = 0;     // S1 distanza: 0 fissa, 1 ATR, 2 lista
input double InpS1_FixedDistPoints           = 300.0; // S1 distanza fissa (punti)
input double InpS1_FixedDistMultiplier       = 1.1;   // S1 crescita della distanza a ogni livello
input string InpS1_CustomDistList            = "";    // S1 lista distanze (punti)
input ENUM_TIMEFRAMES InpS1_ATRTimeframe     = PERIOD_M1; // S1 timeframe ATR
input int    InpS1_ATRPeriod                 = 14;    // S1 periodo ATR
input double InpS1_ATRMultiplier             = 1.0;   // S1 distanza = ATR x
input double InpS1_BasketTPPips              = 200.0; // S1 TP del cesto oltre il prezzo medio
input bool   InpS1_UseTrailing               = true;  // S1 trailing del cesto
input int    InpS1_TrailMethod               = 1;     // S1 0 classico, 1 a gradini, 2 % del profitto, 3 ATR
input double InpS1_TrailStartPips            = 100.0; // S1 trailing da (oltre il medio)
input double InpS1_TrailStepPips             = 50.0;  // S1 passo/distanza del trailing
input double InpS1_TrailPercent              = 50.0;  // S1 % del profitto bloccata (metodo 2)
input double InpS1_TrailATRMultiplier        = 1.0;   // S1 distanza = ATR x (metodo 3)
input group "===== Strategy 2 ====="
input ENUM_TIMEFRAMES InpS2_Timeframe        = PERIOD_M1; // S2 timeframe dei segnali
input double InpS2_Lot                       = 0.01;  // S2 lotto iniziale
input double InpS2_Multiplier                = 1.5;   // S2 moltiplicatore (LotMode 0: x, LotMode 1: +)
input int    InpS2_LotMode                   = 0;     // S2 0 = moltiplica, 1 = somma
input string InpS2_CustomLotList             = "";    // S2 lista lotti (es. 0.01,0.02,0.03)
input bool   InpS2_CustomListMultiplyLast    = false; // S2 finita la lista: moltiplica l'ultimo
input double InpS2_CustomListMultiplier      = 1.5;   // S2 moltiplicatore dopo la lista
input double InpS2_MaxLot                    = 0.0;   // S2 lotto massimo (0 = nessuno)
input int    InpS2_MaxTrades                 = 20;    // S2 livelli massimi (0 = nessun limite)
input int    InpS2_GridMethod                = 0;     // S2 distanza: 0 fissa, 1 ATR, 2 lista
input double InpS2_FixedDistPoints           = 300.0; // S2 distanza fissa (punti)
input double InpS2_FixedDistMultiplier       = 1.1;   // S2 crescita della distanza a ogni livello
input string InpS2_CustomDistList            = "";    // S2 lista distanze (punti)
input ENUM_TIMEFRAMES InpS2_ATRTimeframe     = PERIOD_M1; // S2 timeframe ATR
input int    InpS2_ATRPeriod                 = 14;    // S2 periodo ATR
input double InpS2_ATRMultiplier             = 1.0;   // S2 distanza = ATR x
input double InpS2_BasketTPPips              = 200.0; // S2 TP del cesto oltre il prezzo medio
input bool   InpS2_UseTrailing               = true;  // S2 trailing del cesto
input int    InpS2_TrailMethod               = 1;     // S2 0 classico, 1 a gradini, 2 % del profitto, 3 ATR
input double InpS2_TrailStartPips            = 100.0; // S2 trailing da (oltre il medio)
input double InpS2_TrailStepPips             = 50.0;  // S2 passo/distanza del trailing
input double InpS2_TrailPercent              = 50.0;  // S2 % del profitto bloccata (metodo 2)
input double InpS2_TrailATRMultiplier        = 1.0;   // S2 distanza = ATR x (metodo 3)
input group "===== Strategy 3 ====="
input ENUM_TIMEFRAMES InpS3_Timeframe        = PERIOD_M1; // S3 timeframe dei segnali
input double InpS3_Lot                       = 0.01;  // S3 lotto iniziale
input double InpS3_Multiplier                = 1.5;   // S3 moltiplicatore (LotMode 0: x, LotMode 1: +)
input int    InpS3_LotMode                   = 0;     // S3 0 = moltiplica, 1 = somma
input string InpS3_CustomLotList             = "";    // S3 lista lotti (es. 0.01,0.02,0.03)
input bool   InpS3_CustomListMultiplyLast    = false; // S3 finita la lista: moltiplica l'ultimo
input double InpS3_CustomListMultiplier      = 1.5;   // S3 moltiplicatore dopo la lista
input double InpS3_MaxLot                    = 0.0;   // S3 lotto massimo (0 = nessuno)
input int    InpS3_MaxTrades                 = 20;    // S3 livelli massimi (0 = nessun limite)
input int    InpS3_GridMethod                = 0;     // S3 distanza: 0 fissa, 1 ATR, 2 lista
input double InpS3_FixedDistPoints           = 300.0; // S3 distanza fissa (punti)
input double InpS3_FixedDistMultiplier       = 1.1;   // S3 crescita della distanza a ogni livello
input string InpS3_CustomDistList            = "";    // S3 lista distanze (punti)
input ENUM_TIMEFRAMES InpS3_ATRTimeframe     = PERIOD_M1; // S3 timeframe ATR
input int    InpS3_ATRPeriod                 = 14;    // S3 periodo ATR
input double InpS3_ATRMultiplier             = 1.0;   // S3 distanza = ATR x
input double InpS3_BasketTPPips              = 200.0; // S3 TP del cesto oltre il prezzo medio
input bool   InpS3_UseTrailing               = true;  // S3 trailing del cesto
input int    InpS3_TrailMethod               = 1;     // S3 0 classico, 1 a gradini, 2 % del profitto, 3 ATR
input double InpS3_TrailStartPips            = 100.0; // S3 trailing da (oltre il medio)
input double InpS3_TrailStepPips             = 50.0;  // S3 passo/distanza del trailing
input double InpS3_TrailPercent              = 50.0;  // S3 % del profitto bloccata (metodo 2)
input double InpS3_TrailATRMultiplier        = 1.0;   // S3 distanza = ATR x (metodo 3)
input group "===== Strategy 4 ====="
input ENUM_TIMEFRAMES InpS4_Timeframe        = PERIOD_M1; // S4 timeframe dei segnali
input double InpS4_Lot                       = 0.01;  // S4 lotto iniziale
input double InpS4_Multiplier                = 1.5;   // S4 moltiplicatore (LotMode 0: x, LotMode 1: +)
input int    InpS4_LotMode                   = 0;     // S4 0 = moltiplica, 1 = somma
input string InpS4_CustomLotList             = "";    // S4 lista lotti (es. 0.01,0.02,0.03)
input bool   InpS4_CustomListMultiplyLast    = false; // S4 finita la lista: moltiplica l'ultimo
input double InpS4_CustomListMultiplier      = 1.5;   // S4 moltiplicatore dopo la lista
input double InpS4_MaxLot                    = 0.0;   // S4 lotto massimo (0 = nessuno)
input int    InpS4_MaxTrades                 = 0;     // S4 livelli massimi (0 = nessun limite)
input int    InpS4_GridMethod                = 0;     // S4 distanza: 0 fissa, 1 ATR, 2 lista
input double InpS4_FixedDistPoints           = 300.0; // S4 distanza fissa (punti)
input double InpS4_FixedDistMultiplier       = 1.1;   // S4 crescita della distanza a ogni livello
input string InpS4_CustomDistList            = "";    // S4 lista distanze (punti)
input ENUM_TIMEFRAMES InpS4_ATRTimeframe     = PERIOD_M1; // S4 timeframe ATR
input int    InpS4_ATRPeriod                 = 14;    // S4 periodo ATR
input double InpS4_ATRMultiplier             = 1.0;   // S4 distanza = ATR x
input double InpS4_BasketTPPips              = 200.0; // S4 TP del cesto oltre il prezzo medio
input bool   InpS4_UseTrailing               = true;  // S4 trailing del cesto
input int    InpS4_TrailMethod               = 1;     // S4 0 classico, 1 a gradini, 2 % del profitto, 3 ATR
input double InpS4_TrailStartPips            = 100.0; // S4 trailing da (oltre il medio)
input double InpS4_TrailStepPips             = 50.0;  // S4 passo/distanza del trailing
input double InpS4_TrailPercent              = 50.0;  // S4 % del profitto bloccata (metodo 2)
input double InpS4_TrailATRMultiplier        = 1.0;   // S4 distanza = ATR x (metodo 3)
input group "===== Strategy 5 ====="
input ENUM_TIMEFRAMES InpS5_Timeframe        = PERIOD_M1; // S5 timeframe dei segnali
input double InpS5_Lot                       = 0.01;  // S5 lotto iniziale
input double InpS5_Multiplier                = 1.5;   // S5 moltiplicatore (LotMode 0: x, LotMode 1: +)
input int    InpS5_LotMode                   = 0;     // S5 0 = moltiplica, 1 = somma
input string InpS5_CustomLotList             = "";    // S5 lista lotti (es. 0.01,0.02,0.03)
input bool   InpS5_CustomListMultiplyLast    = false; // S5 finita la lista: moltiplica l'ultimo
input double InpS5_CustomListMultiplier      = 1.5;   // S5 moltiplicatore dopo la lista
input double InpS5_MaxLot                    = 0.0;   // S5 lotto massimo (0 = nessuno)
input int    InpS5_MaxTrades                 = 20;    // S5 livelli massimi (0 = nessun limite)
input int    InpS5_GridMethod                = 0;     // S5 distanza: 0 fissa, 1 ATR, 2 lista
input double InpS5_FixedDistPoints           = 300.0; // S5 distanza fissa (punti)
input double InpS5_FixedDistMultiplier       = 1.1;   // S5 crescita della distanza a ogni livello
input string InpS5_CustomDistList            = "";    // S5 lista distanze (punti)
input ENUM_TIMEFRAMES InpS5_ATRTimeframe     = PERIOD_M1; // S5 timeframe ATR
input int    InpS5_ATRPeriod                 = 14;    // S5 periodo ATR
input double InpS5_ATRMultiplier             = 1.0;   // S5 distanza = ATR x
input double InpS5_BasketTPPips              = 200.0; // S5 TP del cesto oltre il prezzo medio
input bool   InpS5_UseTrailing               = true;  // S5 trailing del cesto
input int    InpS5_TrailMethod               = 1;     // S5 0 classico, 1 a gradini, 2 % del profitto, 3 ATR
input double InpS5_TrailStartPips            = 100.0; // S5 trailing da (oltre il medio)
input double InpS5_TrailStepPips             = 50.0;  // S5 passo/distanza del trailing
input double InpS5_TrailPercent              = 50.0;  // S5 % del profitto bloccata (metodo 2)
input double InpS5_TrailATRMultiplier        = 1.0;   // S5 distanza = ATR x (metodo 3)

struct SCfg
{
   bool            active;
   ENUM_TIMEFRAMES tf;
   double          lot, mult;
   int             lotMode;
   double          lotList[];
   bool            listMulLast;
   double          listMul, maxLot;
   int             maxTrades, gridMethod;
   double          fixDist, fixDistMul;
   double          distList[];
   ENUM_TIMEFRAMES atrTf;
   int             atrPer;
   double          atrMul, tp;
   bool            trail;
   int             trailMethod;
   double          trailStart, trailStep, trailPct, trailAtrMul;
   int             hAtr, hSig;
   datetime        lastBar;
};

struct SBasket
{
   int    n;
   double lots, wsum, lastPx, lastLot, profit;
};

CTrade        trade;
CPositionInfo pos;
SCfg          cfg[6];               // indice 1..5
double        trBest[6][2];         // miglior prezzo dal trailing attivo [strategia][0 buy, 1 sell]
bool          trOn[6][2];
double        unit;                 // 1 "punto" del set in prezzo
datetime      lastWarn = 0;
int           hTrend = INVALID_HANDLE, hCalm = INVALID_HANDLE;

void ParseList(string s, double &arr[])
{
   ArrayResize(arr, 0);
   StringReplace(s, " ", "");
   if(s == "") return;
   string p[];
   int k = StringSplit(s, ',', p);
   for(int i = 0; i < k; i++)
      if(p[i] != "") { int m = ArraySize(arr); ArrayResize(arr, m + 1); arr[m] = StringToDouble(p[i]); }
}

void SetCfg(int i, ENUM_TIMEFRAMES tf, double lot, double mult, int lotMode, string lotList, bool mulLast,
            double listMul, double maxLot, int maxTrades, int gridMethod, double fd, double fdm, string distList,
            ENUM_TIMEFRAMES atf, int atrPer, double atrMul, double tp, bool trail, int tm, double ts, double tst,
            double tpc, double tam)
{
   cfg[i].tf = tf; cfg[i].lot = lot; cfg[i].mult = mult; cfg[i].lotMode = lotMode;
   ParseList(lotList, cfg[i].lotList);
   cfg[i].listMulLast = mulLast; cfg[i].listMul = listMul; cfg[i].maxLot = maxLot; cfg[i].maxTrades = maxTrades;
   cfg[i].gridMethod = gridMethod; cfg[i].fixDist = fd; cfg[i].fixDistMul = fdm;
   ParseList(distList, cfg[i].distList);
   cfg[i].atrTf = atf; cfg[i].atrPer = atrPer; cfg[i].atrMul = atrMul; cfg[i].tp = tp; cfg[i].trail = trail;
   cfg[i].trailMethod = tm; cfg[i].trailStart = ts; cfg[i].trailStep = tst; cfg[i].trailPct = tpc;
   cfg[i].trailAtrMul = tam; cfg[i].hAtr = INVALID_HANDLE; cfg[i].hSig = INVALID_HANDLE; cfg[i].lastBar = 0;
   cfg[i].active = false;
}

long MagicOf(int i, int side) { return (side == 0 ? InpMagicBuy : InpMagicSell) + 10 * i; }

int OnInit()
{
   if(AccountInfoInteger(ACCOUNT_MARGIN_MODE) != ACCOUNT_MARGIN_MODE_RETAIL_HEDGING)
   {
      Print("CestoTopBottom: serve un conto HEDGING");
      return INIT_FAILED;
   }
   int f = InpDigitDetectMode > 0 ? InpDigitDetectMode : ((_Digits == 3 || _Digits == 5) ? 10 : 1);
   unit = _Point * f;
   trade.SetDeviationInPoints((ulong)(InpSlippage * f));
   trade.SetTypeFillingBySymbol(_Symbol);

   SetCfg(1, InpS1_Timeframe, InpS1_Lot, InpS1_Multiplier, InpS1_LotMode, InpS1_CustomLotList,
          InpS1_CustomListMultiplyLast, InpS1_CustomListMultiplier, InpS1_MaxLot, InpS1_MaxTrades,
          InpS1_GridMethod, InpS1_FixedDistPoints, InpS1_FixedDistMultiplier, InpS1_CustomDistList,
          InpS1_ATRTimeframe, InpS1_ATRPeriod, InpS1_ATRMultiplier, InpS1_BasketTPPips, InpS1_UseTrailing,
          InpS1_TrailMethod, InpS1_TrailStartPips, InpS1_TrailStepPips, InpS1_TrailPercent,
          InpS1_TrailATRMultiplier);
   SetCfg(2, InpS2_Timeframe, InpS2_Lot, InpS2_Multiplier, InpS2_LotMode, InpS2_CustomLotList,
          InpS2_CustomListMultiplyLast, InpS2_CustomListMultiplier, InpS2_MaxLot, InpS2_MaxTrades,
          InpS2_GridMethod, InpS2_FixedDistPoints, InpS2_FixedDistMultiplier, InpS2_CustomDistList,
          InpS2_ATRTimeframe, InpS2_ATRPeriod, InpS2_ATRMultiplier, InpS2_BasketTPPips, InpS2_UseTrailing,
          InpS2_TrailMethod, InpS2_TrailStartPips, InpS2_TrailStepPips, InpS2_TrailPercent,
          InpS2_TrailATRMultiplier);
   SetCfg(3, InpS3_Timeframe, InpS3_Lot, InpS3_Multiplier, InpS3_LotMode, InpS3_CustomLotList,
          InpS3_CustomListMultiplyLast, InpS3_CustomListMultiplier, InpS3_MaxLot, InpS3_MaxTrades,
          InpS3_GridMethod, InpS3_FixedDistPoints, InpS3_FixedDistMultiplier, InpS3_CustomDistList,
          InpS3_ATRTimeframe, InpS3_ATRPeriod, InpS3_ATRMultiplier, InpS3_BasketTPPips, InpS3_UseTrailing,
          InpS3_TrailMethod, InpS3_TrailStartPips, InpS3_TrailStepPips, InpS3_TrailPercent,
          InpS3_TrailATRMultiplier);
   SetCfg(4, InpS4_Timeframe, InpS4_Lot, InpS4_Multiplier, InpS4_LotMode, InpS4_CustomLotList,
          InpS4_CustomListMultiplyLast, InpS4_CustomListMultiplier, InpS4_MaxLot, InpS4_MaxTrades,
          InpS4_GridMethod, InpS4_FixedDistPoints, InpS4_FixedDistMultiplier, InpS4_CustomDistList,
          InpS4_ATRTimeframe, InpS4_ATRPeriod, InpS4_ATRMultiplier, InpS4_BasketTPPips, InpS4_UseTrailing,
          InpS4_TrailMethod, InpS4_TrailStartPips, InpS4_TrailStepPips, InpS4_TrailPercent,
          InpS4_TrailATRMultiplier);
   SetCfg(5, InpS5_Timeframe, InpS5_Lot, InpS5_Multiplier, InpS5_LotMode, InpS5_CustomLotList,
          InpS5_CustomListMultiplyLast, InpS5_CustomListMultiplier, InpS5_MaxLot, InpS5_MaxTrades,
          InpS5_GridMethod, InpS5_FixedDistPoints, InpS5_FixedDistMultiplier, InpS5_CustomDistList,
          InpS5_ATRTimeframe, InpS5_ATRPeriod, InpS5_ATRMultiplier, InpS5_BasketTPPips, InpS5_UseTrailing,
          InpS5_TrailMethod, InpS5_TrailStartPips, InpS5_TrailStepPips, InpS5_TrailPercent,
          InpS5_TrailATRMultiplier);

   string p[];
   string act = InpActiveStrategies;
   StringReplace(act, " ", "");
   int k = StringSplit(act, ',', p);
   for(int j = 0; j < k; j++)
   {
      int i = (int)StringToInteger(p[j]);
      if(i >= 1 && i <= 5) cfg[i].active = true;
   }
   if(InpSmartEntry)
   {
      hTrend = iMA(_Symbol, InpTrendTF, InpTrendEMA, 0, MODE_EMA, PRICE_CLOSE);
      hCalm = iATR(_Symbol, PERIOD_M1, 14);
      if(hTrend == INVALID_HANDLE || hCalm == INVALID_HANDLE) return INIT_FAILED;
   }
   for(int i = 1; i <= 5; i++)
   {
      trOn[i][0] = trOn[i][1] = false;
      if(!cfg[i].active) continue;
      if(i == 2) cfg[i].hSig = iRSI(_Symbol, cfg[i].tf, InpRsiPeriod, PRICE_CLOSE);
      if(i == 3) cfg[i].hSig = iBands(_Symbol, cfg[i].tf, InpBandsPeriod, 0, InpBandsDev, PRICE_CLOSE);
      if(i == 4) cfg[i].hSig = iStochastic(_Symbol, cfg[i].tf, InpStochK, InpStochD, InpStochSlow, MODE_SMA, STO_LOWHIGH);
      if((i == 2 || i == 3 || i == 4) && cfg[i].hSig == INVALID_HANDLE) return INIT_FAILED;
      if(cfg[i].gridMethod == 1 || (cfg[i].trail && cfg[i].trailMethod == 3))
      {
         cfg[i].hAtr = iATR(_Symbol, cfg[i].atrTf, cfg[i].atrPer);
         if(cfg[i].hAtr == INVALID_HANDLE) return INIT_FAILED;
      }
   }
   return INIT_SUCCEEDED;
}

void OnDeinit(const int reason)
{
   if(hTrend != INVALID_HANDLE) IndicatorRelease(hTrend);
   if(hCalm != INVALID_HANDLE) IndicatorRelease(hCalm);
   for(int i = 1; i <= 5; i++)
   {
      if(cfg[i].hSig != INVALID_HANDLE) IndicatorRelease(cfg[i].hSig);
      if(cfg[i].hAtr != INVALID_HANDLE) IndicatorRelease(cfg[i].hAtr);
   }
   Comment("");
}

//--- segnali sulla barra chiusa: 1 = minimo (BUY), -1 = massimo (SELL), 0 = niente
int Signal(int i)
{
   ENUM_TIMEFRAMES tf = cfg[i].tf;
   double a[], b[];
   ArraySetAsSeries(a, true);
   ArraySetAsSeries(b, true);
   if(i == 1)
   {
      if(Bars(_Symbol, tf) < 10) return 0;
      double lo3 = iLow(_Symbol, tf, 3), hi3 = iHigh(_Symbol, tf, 3);
      bool bot = true, top = true;
      for(int s = 1; s <= 5; s++)
      {
         if(s == 3) continue;
         if(iLow(_Symbol, tf, s) <= lo3) bot = false;
         if(iHigh(_Symbol, tf, s) >= hi3) top = false;
      }
      return bot && !top ? 1 : (top && !bot ? -1 : 0);
   }
   if(i == 2)
   {
      if(CopyBuffer(cfg[i].hSig, 0, 1, 2, a) < 2) return 0;
      if(a[1] < InpRsiLow && a[0] >= InpRsiLow) return 1;
      if(a[1] > InpRsiHigh && a[0] <= InpRsiHigh) return -1;
      return 0;
   }
   if(i == 3)
   {
      double c1 = iClose(_Symbol, tf, 1), c2 = iClose(_Symbol, tf, 2);
      if(CopyBuffer(cfg[i].hSig, 2, 1, 2, a) < 2 || CopyBuffer(cfg[i].hSig, 1, 1, 2, b) < 2) return 0;
      if(c2 < a[1] && c1 > a[0]) return 1;           // sotto la banda bassa e poi dentro
      if(c2 > b[1] && c1 < b[0]) return -1;          // sopra la banda alta e poi dentro
      return 0;
   }
   if(i == 4)
   {
      if(CopyBuffer(cfg[i].hSig, 0, 1, 2, a) < 2 || CopyBuffer(cfg[i].hSig, 1, 1, 2, b) < 2) return 0;
      if(a[1] <= b[1] && a[0] > b[0] && b[0] < InpStochLow) return 1;
      if(a[1] >= b[1] && a[0] < b[0] && b[0] > InpStochHigh) return -1;
      return 0;
   }
   if(i == 5)
   {
      if(Bars(_Symbol, tf) < InpS5Lookback + 3) return 0;
      int lo = iLowest(_Symbol, tf, MODE_LOW, InpS5Lookback, 1);
      int hi = iHighest(_Symbol, tf, MODE_HIGH, InpS5Lookback, 1);
      double o1 = iOpen(_Symbol, tf, 1), c1 = iClose(_Symbol, tf, 1);
      if(lo == 1 && c1 > o1) return 1;
      if(hi == 1 && c1 < o1) return -1;
      return 0;
   }
   return 0;
}

//--- entrata intelligente: 1 = solo BUY, -1 = solo SELL, 0 = niente cesti nuovi adesso (strappo in corso)
//    Fase 25 (barre M1 2026, mese per mese, 500.000): mesi saltati 5 su 10 -> 1 su 10, ma guadagno ~1/3.
int SmartSide()
{
   if(!InpSmartEntry) return 2;                      // 2 = entrambi i lati
   double e[], a[];
   if(CopyBuffer(hTrend, 0, 1, 1, e) < 1 || CopyBuffer(hCalm, 0, 1, 1, a) < 1) return 0;
   int hi = iHighest(_Symbol, PERIOD_M1, MODE_HIGH, InpCalmBars, 1), lo = iLowest(_Symbol, PERIOD_M1, MODE_LOW, InpCalmBars, 1);
   if(hi < 0 || lo < 0) return 0;
   if(iHigh(_Symbol, PERIOD_M1, hi) - iLow(_Symbol, PERIOD_M1, lo) >= InpCalmATR * a[0]) return 0;
   return SymbolInfoDouble(_Symbol, SYMBOL_BID) > e[0] ? 1 : -1;
}

void Scan(long magic, SBasket &b)
{
   b.n = 0; b.lots = 0; b.wsum = 0; b.lastPx = 0; b.lastLot = 0; b.profit = 0;
   datetime last = 0;
   for(int k = PositionsTotal() - 1; k >= 0; k--)
   {
      if(!pos.SelectByIndex(k) || pos.Symbol() != _Symbol || pos.Magic() != magic) continue;
      b.n++;
      b.lots += pos.Volume();
      b.wsum += pos.Volume() * pos.PriceOpen();
      b.profit += pos.Profit() + pos.Swap();
      if(pos.Time() >= last) { last = pos.Time(); b.lastPx = pos.PriceOpen(); b.lastLot = pos.Volume(); }
   }
}

void CloseBasket(long magic, string why)
{
   for(int k = PositionsTotal() - 1; k >= 0; k--)
      if(pos.SelectByIndex(k) && pos.Symbol() == _Symbol && pos.Magic() == magic)
         trade.PositionClose(pos.Ticket());
   PrintFormat("CestoTopBottom: cesto %I64d chiuso (%s)", magic, why);
}

double NormLot(double v)
{
   double st = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
   double mn = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN), mx = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX);
   v = MathFloor(v / st + 1e-9) * st;
   return NormalizeDouble(MathMax(mn, MathMin(mx, v)), 8);
}

//--- lotto del livello n (0 = primo ordine)
double LotFor(int i, int n)
{
   double v;
   int m = ArraySize(cfg[i].lotList);
   if(m > 0)
      v = n < m ? cfg[i].lotList[n] : cfg[i].lotList[m - 1] * (cfg[i].listMulLast ? MathPow(cfg[i].listMul, n - m + 1) : 1.0);
   else if(cfg[i].lotMode == 1)
      v = cfg[i].lot + cfg[i].mult * n;
   else
      v = cfg[i].lot * MathPow(cfg[i].mult, n);
   if(cfg[i].maxLot > 0) v = MathMin(v, cfg[i].maxLot);
   return NormLot(v);
}

double AtrNow(int i)
{
   double a[];
   if(cfg[i].hAtr == INVALID_HANDLE || CopyBuffer(cfg[i].hAtr, 0, 1, 1, a) < 1) return 0;
   return a[0];
}

//--- distanza in prezzo per aggiungere il livello n (n = livelli gia' aperti, >= 1)
double DistFor(int i, int n)
{
   if(cfg[i].gridMethod == 1) return AtrNow(i) * cfg[i].atrMul;
   int m = ArraySize(cfg[i].distList);
   if(cfg[i].gridMethod == 2 && m > 0) return cfg[i].distList[MathMin(n - 1, m - 1)] * unit;
   return cfg[i].fixDist * MathPow(cfg[i].fixDistMul, n - 1) * unit;
}

bool InTime()
{
   if(!InpEnableTimeFilter) return true;
   MqlDateTime d; TimeToStruct(TimeCurrent(), d);
   int now = d.hour * 60 + d.min;
   string a[], b[];
   if(StringSplit(InpTimeStart, ':', a) < 2 || StringSplit(InpTimeEnd, ':', b) < 2) return true;
   int s = (int)StringToInteger(a[0]) * 60 + (int)StringToInteger(a[1]);
   int e = (int)StringToInteger(b[0]) * 60 + (int)StringToInteger(b[1]);
   return s <= e ? (now >= s && now < e) : (now >= s || now < e);
}

bool Open(int i, int side, double lot, string tag)
{
   double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK), bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);
   double margin;
   ENUM_ORDER_TYPE t = side == 0 ? ORDER_TYPE_BUY : ORDER_TYPE_SELL;
   if(!OrderCalcMargin(t, _Symbol, lot, side == 0 ? ask : bid, margin) || margin > AccountInfoDouble(ACCOUNT_MARGIN_FREE))
   {
      if(TimeCurrent() - lastWarn > 600) { Print("CestoTopBottom: margine insufficiente per ", lot, " lotti"); lastWarn = TimeCurrent(); }
      return false;
   }
   trade.SetExpertMagicNumber(MagicOf(i, side));
   string c = StringFormat("CTB S%d %s", i, tag);
   return side == 0 ? trade.Buy(lot, _Symbol, ask, 0, 0, c) : trade.Sell(lot, _Symbol, bid, 0, 0, c);
}

//--- TP del cesto anche sul server (solo con InpHideSLTP_FromBroker = false)
void SyncBrokerTP(long magic, double tp)
{
   tp = NormalizeDouble(tp, _Digits);
   for(int k = PositionsTotal() - 1; k >= 0; k--)
      if(pos.SelectByIndex(k) && pos.Symbol() == _Symbol && pos.Magic() == magic && MathAbs(pos.TakeProfit() - tp) > _Point)
         trade.PositionModify(pos.Ticket(), pos.StopLoss(), tp);
}

//--- chiusure: TP, trailing, perdita massima. true = cesto chiuso
bool ManageExit(int i, int side, SBasket &b)
{
   long   magic = MagicOf(i, side);
   double d = side == 0 ? 1.0 : -1.0;
   double px = side == 0 ? SymbolInfoDouble(_Symbol, SYMBOL_BID) : SymbolInfoDouble(_Symbol, SYMBOL_ASK);
   double avg = b.wsum / b.lots;
   double gain = (px - avg) * d;                       // prezzo oltre il medio, a favore

   if(InpMaxBasketDrawdownPercent > 0 && b.profit < 0 &&
      -b.profit >= InpMaxBasketDrawdownPercent / 100.0 * AccountInfoDouble(ACCOUNT_BALANCE))
   { CloseBasket(magic, "perdita massima"); return true; }

   if(cfg[i].tp > 0 && gain >= cfg[i].tp * unit) { CloseBasket(magic, "TP"); return true; }

   if(cfg[i].trail)
   {
      if(!trOn[i][side] && gain >= cfg[i].trailStart * unit) { trOn[i][side] = true; trBest[i][side] = px; }
      if(trOn[i][side])
      {
         if((px - trBest[i][side]) * d > 0) trBest[i][side] = px;
         double best = (trBest[i][side] - avg) * d, lock;
         double st = cfg[i].trailStep * unit, s0 = cfg[i].trailStart * unit;
         switch(cfg[i].trailMethod)
         {
            case 0:  lock = best - st; break;
            case 1:  lock = s0 - st + (st > 0 ? MathFloor((best - s0) / st) * st : 0); break;
            case 2:  lock = best * cfg[i].trailPct / 100.0; break;
            default: lock = best - AtrNow(i) * cfg[i].trailAtrMul; break;
         }
         if(gain <= lock && lock > 0) { CloseBasket(magic, "trailing"); return true; }
      }
   }
   if(!InpHideSLTP_FromBroker && cfg[i].tp > 0) SyncBrokerTP(magic, avg + d * cfg[i].tp * unit);
   return false;
}

void OnTick()
{
   double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK), bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);
   bool spreadOk = (ask - bid) <= InpMaxSpreadPoints * unit;
   bool timeOk = InTime();
   bool newOk = spreadOk && (timeOk || !InpTimeBlockNewEntries);
   bool addOk = spreadOk && (timeOk || !InpTimeBlockReinforcement);
   string dash = "CestoTopBottom\n";
   int smart = SmartSide();

   for(int i = 1; i <= 5; i++)
   {
      if(!cfg[i].active) continue;
      int sig = 0;
      datetime t = iTime(_Symbol, cfg[i].tf, 0);
      if(t != cfg[i].lastBar && t > 0) { cfg[i].lastBar = t; sig = Signal(i); }
      int want = InpEntryMode == 1 ? 2 : sig;          // continuo: un cesto chiuso si riapre subito

      for(int side = 0; side < 2; side++)
      {
         if((side == 0 && !InpEnableBuyBasket) || (side == 1 && !InpEnableSellBasket)) continue;
         int dir = side == 0 ? 1 : -1;
         SBasket b;
         Scan(MagicOf(i, side), b);
         if(b.n == 0)
         {
            trOn[i][side] = false;
            if((want == dir || want == 2) && newOk && (smart == 2 || smart == dir)) Open(i, side, LotFor(i, 0), "L1");
            continue;
         }
         if(ManageExit(i, side, b)) { trOn[i][side] = false; continue; }

         bool room = cfg[i].maxTrades == 0 || b.n < cfg[i].maxTrades;
         if(room && addOk && (InpSilentReinforcement || sig == dir))
         {
            double dist = DistFor(i, b.n);
            double px = side == 0 ? ask : bid;
            if(dist > 0 && (b.lastPx - px) * dir >= dist)
               Open(i, side, LotFor(i, b.n), StringFormat("L%d", b.n + 1));
         }
         if(InpShowDashboard)
            dash += StringFormat("S%d %s: %d livelli, %.2f lotti, medio %s, %+.2f\n", i, side == 0 ? "BUY" : "SELL",
                                 b.n, b.lots, DoubleToString(b.wsum / b.lots, _Digits), b.profit);
      }
   }
   if(InpShowDashboard) Comment(dash);
}
//+------------------------------------------------------------------+
