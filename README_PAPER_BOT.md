# Paper Trading Bot - ICT Methodology

Bot di trading simulato (paper trading) per criptovalute che implementa la metodologia ICT (Inner Circle Trader).

## 🎯 Caratteristiche

- **Paper Trading**: Nessun rischio reale, capitale simulato
- **Metodologia ICT**: Implementazione step-by-step della strategia ICT
- **Multi-Timeframe**: HTF (15m) per BIAS, LTF (5m) per ENTRY
- **Risk Management**: Gestione posizioni con Stop Loss e Take Profit

## 📊 Implementazione ICT

### STEP 1: BIAS Detection ✅
Determina la direzione del mercato su HTF (15m):
- **Swing Detection**: Identifica swing highs/lows con logica frattale
- **Liquidità**: Analizza pool di liquidità (external highs/lows)
- **Struttura**: Verifica break strutturali
- **Compressione**: Detect range compression tramite ATR
- **Output**: `UP`, `DOWN`, o `NONE`

### STEP 2: SWEEP Detection ✅
Identifica liquidity grab coerente con il bias:
- **Sell-side Sweep** (per BIAS UP): Wick sotto pool_low + reclaim sopra
- **Buy-side Sweep** (per BIAS DOWN): Wick sopra pool_high + reclaim sotto
- **Filtri qualità**:
  - Wick dominance (wick >= body * 1.2)
  - Pool significance (distanza > ATR * 0.5)
- **Invalidazioni**:
  - Sweep senza reclaim (breakdown/breakup)
  - Violazione troppo piccola
  - Sweep opposto al bias

### STEP 3: DISPLACEMENT Detection ✅
Rileva cambio di regime dopo sweep (M15):
- **Break of Structure (BOS)**: 
  - UP: close > swing_high + (ATR * 0.02)
  - DOWN: close < swing_low - (ATR * 0.02)
- **Impulso anomalo**: candle_range >= ATR * 0.80
- **Body dominance**: body >= range * 0.55
- **FVG (Fair Value Gap)**: Pattern 3 candele
  - UP: low[i] > high[i-2]
  - DOWN: high[i] < low[i-2]
- **Grading**:
  - Grade A: Displacement + FVG coerente
  - Grade B: Displacement senza FVG
- **Output**: dir, bos_level, fvg, grade

### STEP 4: RETRACE Detection ✅
Rileva pullback ordinato dopo displacement (M15):
- **Zona retrace**:
  - Caso A: FVG zone (se presente)
  - Caso B: Fallback 50%-79% del displacement range
- **Hit detection**: Intersezione wick con zona (basta toccare)
- **Filtri**:
  - Timeout: Max 8 barre M15
  - Invalidation: Close oltre displacement ± (ATR * 0.05)
- **Depth & Grading**:
  - Grade A: Depth 0.50-0.79 (ideale)
  - Grade B: Depth fuori range (valido)
- **Status**: HIT, WAIT, EXPIRED, INVALIDATED
- **Output**: zone, retrace_point, depth, grade

### STEP 5: CONFIRMATION Detection ✅
Conferma setup su M5 dopo retrace:
- **Context Gate**: Prezzo vicino zona retrace ± (ATR M5 * 0.25)
- **Micro BOS su M5**:
  - UP: close > swing_high_m5 + (ATR M5 * 0.02)
  - DOWN: close < swing_low_m5 - (ATR M5 * 0.02)
- **Impulse M5**: candle_range >= ATR M5 * 0.60 (più leggero)
- **Body dominance**: body >= range * 0.50
- **Mini FVG M5**: Pattern 3 candele (opzionale)
- **Filtri**:
  - Timeout: Max 12 barre M5 (~60 minuti)
  - Fuori zona: WAIT
- **Grading**:
  - Grade A: Confirm + mini FVG coerente
  - Grade B: Confirm senza FVG
- **Status**: CONFIRMED, WAIT, EXPIRED
- **Output**: dir, micro_bos_level, fvg, grade

### Entry Logic ✅
Calcolo entry price dopo confirmation:
- **Entry al 50% della candela confirm**:
  - LONG: `entry_price = confirm_low + (confirm_range × 0.50)`
  - SHORT: `entry_price = confirm_high - (confirm_range × 0.50)`
- **Timeout**: Max 6 barre M5 dopo confirmation
- **Output**: side, entry_price

**Entry finale**: Richiede tutti i 5 STEP coerenti + Entry Logic Ready

## 🛡️ Risk Management

### Stop Loss Strutturale
Lo Stop Loss è basato sull'**invalidazione strutturale** del setup:

**LONG:**
```python
SL = min(sweep_extreme, retrace_low) - (ATR_M15 × 0.05)
```
- SL sotto il punto più basso tra sweep e retrace
- Buffer ATR per evitare stop out prematuri
- **SL è FISSO**, non si muove mai

**SHORT:**
```python
SL = max(sweep_extreme, retrace_high) + (ATR_M15 × 0.05)
```
- SL sopra il punto più alto tra sweep e retrace
- **SL è FISSO**, non si muove mai

### Take Profit a 2R
Il Take Profit è calcolato con **risk multiple fisso a 2R**:

**Formula:**
```python
R = |entry - SL|  # Risk
TP = entry + 2R   # LONG
TP = entry - 2R   # SHORT
```

**Vantaggi 2R:**
- ✅ Win rate 40% → quasi break even
- ✅ Win rate 50% → equity cresce
- ✅ Matematicamente solido
- ✅ Non dipende da interpretazioni
- ✅ Risk/Reward ratio sempre 1:2

## 🚀 Utilizzo

### Installazione dipendenze
```bash
pip install -r requirements.txt
```

### Avvio bot
```bash
python3 paper_trading_bot.py
```

Il bot si connetterà a Binance (modalità pubblica, senza API keys) e inizierà ad analizzare i mercati configurati.

## ⚙️ Configurazione

Modifica i parametri in `CONFIG` nel file `paper_trading_bot.py`:

```python
CONFIG = {
    "INITIAL_CAPITAL": 10000.0,      # Capitale iniziale simulato
    "SYMBOLS": ["BTC/USDT", "ETH/USDT"],  # Mercati da monitorare
    "HTF": "15m",                    # Higher TimeFrame
    "LTF": "5m",                     # Lower TimeFrame
    "SWING_LEFT_RIGHT": 2,           # Parametro swing detection
    "ATR_PERIOD": 14,                # Periodo ATR
    "RISK_PER_TRADE": 0.02,          # 2% per trade
    "MAX_POSITIONS": 2,              # Max posizioni contemporanee
    ...
}
```

### Parametri Sweep Detection
```python
"SWEEP_MIN_DIST_MULT": 0.10,      # Distanza minima = ATR * 0.10
"SWEEP_RECLAIM_MULT": 0.02,       # Buffer reclaim = ATR * 0.02
"SWEEP_WICK_RATIO": 1.2,          # Wick >= body * 1.2
"SWEEP_POOL_SIGNIFICANCE": 0.5,   # Pool distante > ATR * 0.5
```

### Parametri Displacement Detection
```python
"DISPLACEMENT_BOS_BUFFER": 0.02,    # BOS buffer = ATR * 0.02
"DISPLACEMENT_IMPULSE_MULT": 0.80,  # Impulso = range >= ATR * 0.80
"DISPLACEMENT_BODY_RATIO": 0.55,    # Body dominance >= 55%
"MAX_BARS_AFTER_SWEEP": 6,          # Timeout dopo sweep
```

### Parametri Retrace Detection
```python
"MAX_RETRACE_BARS": 8,              # Max barre M15 per retrace
"RETRACE_INVALIDATION_MULT": 0.05,  # Invalidation buffer = ATR * 0.05
"RETRACE_ZONE_MIN": 0.50,           # 50% displacement range
"RETRACE_ZONE_MAX": 0.79,           # 79% displacement range
```

### Parametri Confirmation Detection
```python
"MAX_CONFIRM_BARS": 12,             # Max barre M5 per confirmation
"CONFIRM_ZONE_BUFFER": 0.25,        # Zone buffer = ATR M5 * 0.25
"CONFIRM_BOS_BUFFER": 0.02,         # Micro BOS buffer = ATR M5 * 0.02
"CONFIRM_IMPULSE_MULT": 0.60,       # Impulso M5 >= ATR M5 * 0.60
"CONFIRM_BODY_RATIO": 0.50,         # Body dominance >= 50%
```

### Parametri Entry Logic
```python
"MAX_ENTRY_BARS": 6,                # Max barre M5 per entry dopo confirm
"ENTRY_RETRACE_PCT": 0.50,          # Entry al 50% della candela confirm
```

### Parametri Risk Management
```python
"RISK_PER_TRADE": 0.02,             # 2% del capitale per trade
"SL_ATR_BUFFER": 0.05,              # Stop Loss buffer = ATR M15 * 0.05
"TP_RISK_MULTIPLE": 2.0,            # Take Profit = 2R (2x risk)
```

## 📈 Output

Il bot stampa in tempo reale:
- **BIAS HTF**: Direzione determinata su 15m
- **SWEEP Detection**: Quando rileva liquidity grab
- **DISPLACEMENT Detection**: Cambio regime con grade A/B
- **RETRACE Detection**: Pullback a zona valore con depth e grade
- **CONFIRMATION Detection**: Micro BOS su M5 con grade
- **ENTRY LOGIC**: Entry price al 50% della candela confirm
- **Posizioni**: Apertura/chiusura trades (solo con setup completo)
- **Performance**: Win rate, ROI, PnL

### Log files
- `paper_trades.csv`: Storico trades chiusi
- `paper_balance.csv`: Evoluzione capitale (futuro)
- `paper_bias_log.csv`: Log bias detection (futuro)

## 🧪 Testing

```bash
# Test swing detection
python3 -c "
import paper_trading_bot
import pandas as pd

data = {'high': [...], 'low': [...], 'close': [...], 'open': [...]}
df = pd.DataFrame(data)
swing_highs, swing_lows = paper_trading_bot.find_swing_highs_lows(df, lr=2)
print('Swing Highs:', swing_highs)
print('Swing Lows:', swing_lows)
"

# Test sweep detection
python3 -c "
import paper_trading_bot

result = paper_trading_bot.detect_sweep(
    bias='UP', 
    pool_high=52000, 
    pool_low=50000,
    o=50500, h=50600, l=49950, c=50550,
    atr=200, 
    current_price=50500
)
print(result)
"
```

## 📚 Metodologia ICT

Questo bot implementa la metodologia di trading ICT (Inner Circle Trader) basata su:

1. **Market Structure**: Analisi dei swing highs/lows
2. **Liquidity**: Pool di liquidità e liquidity grabs
3. **Smart Money Concepts**: Sweep, Displacement, Order Blocks
4. **Multi-Timeframe**: Bias su HTF, entry su LTF

## ⚠️ Disclaimer

Questo è un **paper trading bot** per scopi educativi e di testing. Non utilizza capitale reale.

Per trading reale, consulta sempre un professionista e comprendi i rischi del trading.

## 📝 Versioni

- **v5.2** - Risk Management: SL strutturale e TP a 2R implementati
- **v5.1** - Entry Logic: Entry al 50% della candela confirm implementato
- **v5.0** - STEP 5: Confirmation Detection implementato - **STRATEGIA ICT COMPLETA** 🎉
- **v4.0** - STEP 4: Retrace Detection implementato
- **v3.0** - STEP 3: Displacement Detection implementato
- **v2.0** - STEP 2: Sweep Detection implementato
- **v1.0** - STEP 1: Bias Detection implementato
- **v0.1** - Struttura base e paper account

## 🤝 Contributi

Sviluppato step-by-step seguendo la metodologia ICT.

---

**Status**: ✅ **STRATEGIA ICT COMPLETA + ENTRY LOGIC - Pronto per il trading!** 🎉🚀
