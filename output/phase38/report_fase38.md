# Fase 38 — varianti di hedging (tick per tick, ogni mese da 5.000 USC, EUR)

Set 8 $ x1,3, lotto x2, TP 0,7 $. 108 varianti (`hedging_varianti*.csv`).
- Copertura al 70% del cesto (livello 4, via a 8 $): +221 +225 +255 +39 -50 +61 +58 +54 +52 +34 = +949 (piena: +923;
  130%: +899). Maggio brucia comunque.
- Togliere la copertura solo con la tendenza tornata dal lato del cesto: 4-5 mesi in perdita.
- Copertura quando la perdita aperta supera il 20-30% del saldo: maggio regge (+0...+13) ma 5-6 mesi in perdita.
- Copertura al 3° livello o rimbalzo 12 $: 3-4 mesi in perdita.
- EA 1.60: InpHedgeRatio = 0,7.
