# 🛡️ Risk Management Professionale - SL Strutturale & TP a 2R

## ✅ Sistema Implementato

Il bot ora utilizza un sistema di **risk management professionale** basato su:
1. **Stop Loss Strutturale** (invalidazione mercato)
2. **Take Profit a 2R** (matematicamente solido)
3. **Position Sizing Adattivo** (basato su risk effettivo)

---

## 📊 Stop Loss Strutturale

### Concetto Base

Lo Stop Loss **NON** è basato su percentuali arbitrarie, ma sulla **invalidazione strutturale** del setup ICT.

Se il prezzo raggiunge lo SL → il setup è **invalido** (struttura rotta).

### Formula LONG

```python
SL = min(sweep_extreme, retrace_low) - (ATR_M15 × 0.05)
```

**Logica:**
1. Identifica il punto più basso tra:
   - `sweep_extreme`: low dello sweep (liquidity grab)
   - `retrace_low`: low della zona retrace
2. Sottrai buffer ATR (5%)
3. Questo è lo SL → se rotto, setup invalido

**Esempio:**
```
Sweep extreme: $49,500
Retrace low: $49,600
ATR M15: $200

SL = min(49500, 49600) - (200 × 0.05)
SL = 49500 - 10 = $49,490
```

### Formula SHORT

```python
SL = max(sweep_extreme, retrace_high) + (ATR_M15 × 0.05)
```

**Logica:**
1. Identifica il punto più alto tra:
   - `sweep_extreme`: high dello sweep
   - `retrace_high`: high della zona retrace
2. Aggiungi buffer ATR (5%)
3. Questo è lo SL → se rotto, setup invalido

**Esempio:**
```
Sweep extreme: $50,500
Retrace high: $50,400
ATR M15: $200

SL = max(50500, 50400) + (200 × 0.05)
SL = 50500 + 10 = $50,510
```

### Caratteristiche SL

- ✅ **Basato su struttura** (non arbitrario)
- ✅ **Adattivo** (usa ATR per volatilità)
- ✅ **Fisso** (non si muove mai)
- ✅ **Logico** (invalidazione setup)
- ✅ **Professionale** (metodologia ICT)

---

## 🎯 Take Profit a 2R

### Concetto Base

Il Take Profit è calcolato come **2R** (2 volte il risk).

Questo crea un **R:R ratio di 1:2** → per ogni $1 rischiato, target $2 di profitto.

### Formula

```python
R = |entry - SL|           # Risk (distanza entry-SL)

TP_LONG = entry + 2R       # Target sopra entry
TP_SHORT = entry - 2R      # Target sotto entry
```

### Esempio LONG

```
Entry: $50,000
SL: $49,490
R = 50000 - 49490 = $510

TP = 50000 + (2 × 510) = $51,020

Risk: $510
Reward: $1,020
R:R = 1:2.00 ✅
```

### Esempio SHORT

```
Entry: $50,000
SL: $50,510
R = 50510 - 50000 = $510

TP = 50000 - (2 × 510) = $48,980

Risk: $510
Reward: $1,020
R:R = 1:2.00 ✅
```

### Perché 2R?

**Matematica:**
- Win rate 40% → (0.4 × 2R) - (0.6 × 1R) = 0.8R - 0.6R = **+0.2R** ✅
- Win rate 50% → (0.5 × 2R) - (0.5 × 1R) = 1.0R - 0.5R = **+0.5R** ✅

**Vantaggi:**
1. ✅ **Semplice** e facile da calcolare
2. ✅ **Simmetrico** (sempre 1:2)
3. ✅ **Matematicamente solido**
4. ✅ **Non interpretativo** (oggettivo)
5. ✅ **Funziona** con win rate 40-60%

**Con 2R:**
- 40% win rate → equity cresce lentamente
- 50% win rate → equity cresce bene
- 60% win rate → equity cresce velocemente

---

## 💰 Position Sizing Adattivo

### Formula

```python
risk_amount = balance × RISK_PER_TRADE      # Es: $10,000 × 0.02 = $200
risk_per_unit = |entry - SL|                # Risk per unità asset
position_size = risk_amount / risk_per_unit
```

### Esempio

```
Balance: $10,000
Risk per trade: 2% = $200
Entry: $50,000
SL: $49,490
Risk per unit: $510

Position Size = 200 / 510 = 0.392 BTC

Se BTC scende a $49,490 (SL):
Loss = 0.392 × 510 = $200 (esattamente 2%) ✅
```

### Vantaggi

- ✅ **Sempre 2% a rischio** (indipendente da volatilità)
- ✅ **Adattivo** (size varia con SL distance)
- ✅ **Protezione capitale** (max loss controllato)
- ✅ **Professionale** (standard industria)

---

## 🔧 Implementazione Tecnica

### Funzione `calculate_structural_sl()`

```python
def calculate_structural_sl(side, sweep_extreme, 
                           retrace_low, retrace_high, atr_m15):
    """
    Calcola SL strutturale basato su invalidazione
    
    LONG: SL = min(sweep, retrace_low) - ATR × 0.05
    SHORT: SL = max(sweep, retrace_high) + ATR × 0.05
    """
    sl_buffer = atr_m15 * 0.05
    
    if side == "LONG":
        sl_base = min(sweep_extreme, retrace_low)
        return sl_base - sl_buffer
    else:
        sl_base = max(sweep_extreme, retrace_high)
        return sl_base + sl_buffer
```

### Funzione `calculate_tp_from_risk()`

```python
def calculate_tp_from_risk(side, entry_price, stop_loss):
    """
    Calcola TP basato su 2R
    
    R = |entry - SL|
    LONG: TP = entry + 2R
    SHORT: TP = entry - 2R
    """
    risk = abs(entry_price - stop_loss)
    tp_multiple = 2.0
    
    if side == "LONG":
        return entry_price + (tp_multiple * risk)
    else:
        return entry_price - (tp_multiple * risk)
```

### Integrazione Entry

```python
# Calcola SL strutturale
stop_loss = calculate_structural_sl(
    signal,
    sweep_detected['extreme'],
    retrace_detected['zone_low'],
    retrace_detected['zone_high'],
    atr_m15
)

# Calcola TP a 2R
take_profit = calculate_tp_from_risk(
    signal,
    entry_price,
    stop_loss
)

# Position sizing adattivo
risk_amount = balance × 0.02
risk_per_unit = abs(entry_price - stop_loss)
position_size = risk_amount / risk_per_unit

# Apri posizione
open_position(symbol, signal, entry_price, position_size, stop_loss, take_profit)
```

---

## 📊 Confronto Sistemi

### Sistema Vecchio (Percentuale)

```
Entry: $50,000
SL: -1.5% = $49,250 (arbitrario)
TP: +3.0% = $51,500 (arbitrario)

Risk: $750
Reward: $1,500
R:R = 1:2.00

❌ SL non basato su struttura
❌ Percentuali arbitrarie
❌ Non adattivo a mercato
```

### Sistema Nuovo (Strutturale)

```
Entry: $50,000
SL: $49,490 (min(sweep, retrace) - ATR buffer)
TP: $51,020 (entry + 2R)

Risk: $510
Reward: $1,020
R:R = 1:2.00

✅ SL basato su struttura mercato
✅ Matematicamente solido
✅ Adattivo (ATR)
✅ Professionale (ICT)
```

---

## 📈 Statistiche Win Rate

### Con R:R 1:2

| Win Rate | Expectancy | Result |
|----------|------------|--------|
| 30% | -0.4R | ❌ Losing |
| 35% | -0.3R | ❌ Losing |
| 40% | -0.2R | ⚠️ Almost BE |
| 45% | -0.1R | ⚠️ Small loss |
| **50%** | **0R** | ✅ **Break even** |
| 55% | +0.1R | ✅ Profitable |
| 60% | +0.2R | ✅ Good |
| 65% | +0.3R | ✅ Excellent |

**Formula:**
```
Expectancy = (WR × 2R) - (LR × 1R)
dove WR = win rate, LR = loss rate = 1 - WR
```

### Conclusione

Con **win rate 40-50%** e **R:R 1:2**:
- Equity cresce costantemente
- Risk controllato
- Sistema sostenibile

---

## 🎯 Regole Operative

### SL - Regole Ferree

1. ✅ **SL è FISSO** - non si muove mai
2. ✅ **SL non si allarga** - mai spostare più lontano
3. ✅ **SL non si anticipa** - aspetta hit naturale
4. ✅ **SL è strutturale** - basato su invalidazione
5. ✅ **SL usa ATR buffer** - adattivo a volatilità

### TP - Regole Ferree

1. ✅ **TP a 2R** - sempre doppio del risk
2. ✅ **TP è FISSO** - non trailing (v1.0)
3. ✅ **TP è matematico** - non interpretativo
4. ✅ **TP sempre 1:2** - R:R costante
5. ✅ **TP non si muove** - target fisso

### Position Sizing

1. ✅ **Sempre 2% capitale** a rischio
2. ✅ **Size adattivo** al risk effettivo
3. ✅ **Mai over-leverage**
4. ✅ **Calcolo preciso** basato su SL distance

---

## 🚀 Entry Signal Completo

```
======================================================================
🎯 [ENTRY SIGNAL] LONG - COMPLETE ICT SETUP!
======================================================================
  ✅ BIAS: UP
  ✅ SWEEP: Detected
  ✅ DISPLACEMENT: Grade A
  ✅ RETRACE: Grade A
  ✅ CONFIRMATION: Grade A
  ✅ ENTRY PRICE: $50,000.00
     Confirm Range: $49,800.00 - $50,000.00
     Entry @ 50% retrace of confirm candle
     
  💰 RISK MANAGEMENT:
     Stop Loss: $49,490.00
     Take Profit: $51,020.00
     Risk (R): $510.00
     Reward: $1,020.00
     R:R Ratio: 1:2.00
     Position Size: 0.392157 BTC
======================================================================
```

---

## 📝 Configurazione

```python
CONFIG = {
    # Risk Management (Structural)
    "RISK_PER_TRADE": 0.02,      # 2% capitale per trade
    "SL_ATR_BUFFER": 0.05,       # SL buffer = ATR × 5%
    "TP_RISK_MULTIPLE": 2.0,     # TP = 2R
}
```

---

## ✅ Checklist Pre-Entry

Prima di aprire posizione, verifica:

### Setup ICT
- [ ] BIAS determinato (UP/DOWN)
- [ ] SWEEP rilevato
- [ ] DISPLACEMENT valido (Grade A/B)
- [ ] RETRACE hit (Grade A/B)
- [ ] CONFIRMATION valida (Grade A/B)
- [ ] ENTRY LOGIC ready

### Risk Management
- [ ] SL strutturale calcolato
- [ ] TP a 2R calcolato
- [ ] R:R = 1:2.00
- [ ] Position size corretto
- [ ] Risk = 2% capitale
- [ ] SL < entry < TP (LONG)
- [ ] TP < entry < SL (SHORT)

**Solo se TUTTI i check sono ✅ → OPEN POSITION**

---

## 🎉 Conclusione

Il sistema di risk management è ora **completo e professionale**:

✅ **SL Strutturale** basato su invalidazione mercato
✅ **TP a 2R** matematicamente solido
✅ **Position Sizing** adattivo
✅ **Protezione Capitale** con max 2% risk
✅ **R:R 1:2** costante
✅ **Win rate 40-50%** = equity cresce

**Sistema pronto per paper trading!** 🚀

---

**Version**: v5.2
**Date**: 2026-02-11
**Status**: ✅ RISK MANAGEMENT COMPLETO
