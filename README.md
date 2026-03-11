# code_test

## Minimalist ICT Trading Bot

A clean, minimalist implementation of an ICT (Inner Circle Trading) bot with support for **paper trading** and **live trading on Binance Cross Margin**.

### Quick Start

#### Paper Trading (Default - Safe)
```bash
# Install dependencies
pip install -r requirements.txt

# Run the bot (paper trading mode)
python ict_bot_minimal.py
```

#### Live Trading (⚠️ Real Money)
```bash
# Set API keys
export BINANCE_API_KEY="your_key"
export BINANCE_API_SECRET="your_secret"

# Edit ict_bot_minimal.py and set LIVE_TRADING = True

# Run the bot
python ict_bot_minimal.py
```

**⚠️ WARNING:** Live trading uses real money on Binance Cross Margin. Read [LIVE_TRADING_GUIDE.md](LIVE_TRADING_GUIDE.md) before enabling!

### Features

✅ **Bias Detection (30m)**: BOS/CHoCH on swing structures  
✅ **Entry Logic (5m)**: SWEEP → DISPLACEMENT → RETRACE → CONFIRM  
✅ **Structural SL/TP**: Stop loss and take profits based on swing levels  
✅ **Paper Trading**: Safe simulation mode (default)  
✅ **Live Trading**: Real orders on Binance Cross Margin (optional)  
✅ **CSV Tracking**: All trades logged to `ict_trades.csv`  
✅ **Console Logging**: Real-time updates (no Telegram)  
✅ **Zero Filters**: Accepts all valid ICT setups  

### Trading Modes

| Mode | Configuration | API Keys | Risk | Use Case |
|------|---------------|----------|------|----------|
| **Paper** | `LIVE_TRADING = False` | Not needed | None | Testing, learning, backtesting |
| **Live** | `LIVE_TRADING = True` | Required | High | Real trading with real money |

### Documentation

#### Getting Started
- **[README.md](README.md)** - This file (overview)
- **[ICT_BOT_README.md](ICT_BOT_README.md)** - Complete bot documentation
- **[USAGE_GUIDE.py](USAGE_GUIDE.py)** - Configuration examples and tips

#### Live Trading (⚠️ Real Money)
- **[LIVE_TRADING_GUIDE.md](LIVE_TRADING_GUIDE.md)** - Complete live trading setup guide
- **[LIVE_TRADING_QUICKREF.md](LIVE_TRADING_QUICKREF.md)** - Quick reference card

#### Testing
- **[test_ict_bot.py](test_ict_bot.py)** - Unit tests

#### Files & Data
- **[FILE_LOCATIONS.md](FILE_LOCATIONS.md)** - 📁 Where files are saved (Dove scaricare i file)

### Where Are Files Saved? 📁

**Trade Log:** `ict_trades.csv` is saved in the **same folder** as `ict_bot_minimal.py`

**How to find it:**
- **Windows:** Look in the folder where you ran the bot, or use `dir ict_trades.csv`
- **Linux/Mac:** Use `ls ict_trades.csv` or `pwd` to see current directory

**Full details:** See [FILE_LOCATIONS.md](FILE_LOCATIONS.md) for complete guide in Italian and English

**Opening the CSV:**
- Microsoft Excel: File → Open → Select `ict_trades.csv`
- Google Sheets: Import the file
- Text editor: Double-click the file

### Files

- `ict_bot_minimal.py` - Main bot implementation (paper + live)
- `requirements.txt` - Python dependencies
- `example_trades.csv` - Example trade log format
- `test_ict_bot.py` - Unit tests for core functions

### Key Configuration

```python
# Trading Mode (in ict_bot_minimal.py)
LIVE_TRADING = True      # True = Live | False = Paper

# Live Trading Settings
TRADE_USDC_TARGET = 200.0  # USDT per trade
MAX_OPEN_POS = 3           # Max concurrent positions

# Paper Trading Settings
PAPER_POSITION_SIZE_USDC = 100.0  # Simulated size
```

### Safety First

**Before enabling live trading:**
1. ✅ Test in paper mode for 24+ hours
2. ✅ Read [LIVE_TRADING_GUIDE.md](LIVE_TRADING_GUIDE.md)
3. ✅ Understand cross margin risks
4. ✅ Set up API keys correctly
5. ✅ Start with small position sizes
6. ✅ Monitor actively

### Original Bot

The original complex bot with Telegram integration and filters is in:
- `TRAIL_microbos_btc_filtro_con_zona_vicina_tp1sl1_btctrendfix.PY`

---

**Disclaimer:** Trading cryptocurrencies carries risk. This bot is for educational purposes. Use at your own risk. Cross margin trading can result in losses exceeding your initial investment.