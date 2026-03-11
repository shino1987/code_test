# 🤖 Minimalist ICT Paper Trading Bot - Quick Reference

## 📁 What Was Delivered

### Main Bot File
- **ict_bot_minimal.py** (700 lines, 17 functions)
  - Complete ICT trading logic
  - Paper trading only (LIVE_TRADING=False)
  - No Telegram integration
  - CSV trade logging
  - Console output only

### Documentation
1. **README.md** - Project overview and quick start
2. **ICT_BOT_README.md** - Complete bot documentation
3. **IMPLEMENTATION_SUMMARY.md** - Technical implementation details
4. **USAGE_GUIDE.py** - Configuration examples and customization tips

### Testing & Examples
- **test_ict_bot.py** - Unit tests (6/6 passing ✅)
- **example_trades.csv** - Sample trade log format
- **requirements.txt** - Python dependencies

### Configuration
- **.gitignore** - Excludes cache and CSV files

## 🚀 Quick Start (3 Steps)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the bot
python ict_bot_minimal.py

# 3. View trades (in another terminal)
tail -f ict_trades.csv
```

## ✅ All Requirements Met

| Requirement | Status | Implementation |
|------------|--------|----------------|
| Bias 30m (BOS/CHoCH) | ✅ | `detect_bias()` function |
| Entry 5m (SWEEP→DISPLACEMENT→RETRACE→CONFIRM) | ✅ | 4-state machine in `scan_symbol()` |
| Structural SL | ✅ | Below/above swing + 0.05% buffer |
| Structural TP1/TP2 | ✅ | Internal/external liquidity (swings) |
| Exit Logic | ✅ | SL→close, TP1→BE, TP2→close |
| Paper Trading ONLY | ✅ | `LIVE_TRADING = False` |
| CSV Tracking | ✅ | `ict_trades.csv` with all metrics |
| Console Logging | ✅ | NO Telegram, console only |
| Zero Filters | ✅ | Pure ICT logic, no filters |

## 📊 Trade Log Format

CSV columns in `ict_trades.csv`:
- timestamp
- symbol
- side (LONG/SHORT)
- entry_price
- sl_price
- tp1_price
- tp2_price
- exit_price
- pnl_gross_pct
- pnl_net_pct
- duration_min
- exit_reason (SL_HIT, TP1_HIT, TP2_HIT, BOT_STOPPED)

## 🔧 Configuration

Edit these in `ict_bot_minimal.py`:

```python
BIAS_TF = "30m"          # Bias timeframe
ENTRY_TF = "5m"          # Entry timeframe
LOOP_SEC = 30            # Check interval

SWING_LR = 2             # Swing detection sensitivity
SWEEP_BUFFER_PCT = 0.0002  # 0.02% sweep buffer
STRUCT_SL_BUFFER_PCT = 0.0005  # 0.05% SL buffer

SYMBOLS = [              # Trading pairs
    "BTC/USDT",
    "ETH/USDT",
]

PAPER_POSITION_SIZE_USDC = 100.0  # Position size
```

## 🎯 How It Works

### 1. Bias Detection (30m)
```
Swings found → BOS/CHoCH detected → BULLISH or BEARISH bias
```

### 2. Entry Setup (5m)
```
WAIT_SWEEP → Liquidity sweep detected
    ↓
WAIT_DISPLACEMENT → Strong move detected
    ↓
WAIT_RETRACE → Pullback detected
    ↓
WAIT_CONFIRM → Confirmation candle
    ↓
OPEN POSITION → Enter at current close price
```

### 3. Position Management
```
Monitor each candle:
- Low ≤ SL → Close at SL (LONG)
- High ≥ TP1 → Move SL to BE
- High ≥ TP2 → Close at TP2 (full exit)
```

## 📈 Testing Results

All 6 unit tests passing:
- ✅ Swing Detection
- ✅ Bias Detection  
- ✅ Sweep Detection
- ✅ Displacement Detection
- ✅ SL/TP Calculation
- ✅ State Machine Flow

## 🎓 Learning Resources

### Read First
1. Start with **README.md**
2. Read **ICT_BOT_README.md** for details
3. Check **USAGE_GUIDE.py** for examples

### Understand the Code
- Core logic: `ict_bot_minimal.py`
- Tests: `test_ict_bot.py`
- See function names: `grep "^def " ict_bot_minimal.py`

### Analyze Trades
```python
import pandas as pd
df = pd.read_csv('ict_trades.csv')
print(df.describe())
print(df.groupby('symbol')['pnl_net_pct'].mean())
```

## ⚠️ Important Notes

### This is PAPER TRADING
- ✅ No real money
- ✅ Educational purposes
- ✅ Test strategies safely
- ✅ Learn ICT concepts

### Before Live Trading
- ⚠️ Test for weeks/months
- ⚠️ Understand all parameters
- ⚠️ Add proper risk management
- ⚠️ Never risk what you can't lose
- ⚠️ Monitor continuously

## 🆚 Comparison

| Feature | Original Complex Bot | This Minimalist Bot |
|---------|---------------------|-------------------|
| Lines of code | ~1500 | ~700 |
| Filters | Many (BTC OB, zones, etc.) | Zero |
| Telegram | Yes | No (console only) |
| Live Trading | Yes (Cross Margin) | No (paper only) |
| API Keys | Required | Not required* |
| Complexity | High | Minimal |

*API keys only needed if you want to use Binance testnet

## 🛠️ Customization

### Add More Symbols
```python
SYMBOLS = [
    "BTC/USDT", "ETH/USDT", "BNB/USDT",
    "SOL/USDT", "XRP/USDT", "ADA/USDT",
]
```

### Change Timeframes
```python
BIAS_TF = "1h"   # Slower, fewer trades
ENTRY_TF = "15m"
```

### Adjust Sensitivity
```python
SWING_LR = 3              # More conservative (larger swings)
DISP_RANGE_MULT = 2.0     # Require stronger displacement
```

## 📞 Support

- Read documentation in repository
- Check unit tests for examples
- Review code comments
- Analyze example trades

## 🎉 Ready to Go!

The bot is fully implemented, tested, and documented. Just run:

```bash
python ict_bot_minimal.py
```

Happy paper trading! 📊

---

**Disclaimer**: For educational and paper trading purposes only. Not financial advice.
