# code_test

## Minimalist ICT Paper Trading Bot

A clean, minimalist implementation of an ICT (Inner Circle Trading) bot for **paper trading only**.

### Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run the bot
python ict_bot_minimal.py
```

### Features

✅ **Bias Detection (30m)**: BOS/CHoCH on swing structures  
✅ **Entry Logic (5m)**: SWEEP → DISPLACEMENT → RETRACE → CONFIRM  
✅ **Structural SL/TP**: Stop loss and take profits based on swing levels  
✅ **Paper Trading Only**: No real money at risk  
✅ **CSV Tracking**: All trades logged to `ict_trades.csv`  
✅ **Console Logging**: Real-time updates (no Telegram)  
✅ **Zero Filters**: Accepts all valid ICT setups  

### Documentation

- **[ICT_BOT_README.md](ICT_BOT_README.md)** - Complete bot documentation
- **[USAGE_GUIDE.py](USAGE_GUIDE.py)** - Configuration examples and tips
- **[test_ict_bot.py](test_ict_bot.py)** - Unit tests

### Files

- `ict_bot_minimal.py` - Main bot implementation
- `requirements.txt` - Python dependencies
- `example_trades.csv` - Example trade log format
- `test_ict_bot.py` - Unit tests for core functions

### Original Bot

The original complex bot with Telegram integration and filters is in:
- `TRAIL_microbos_btc_filtro_con_zona_vicina_tp1sl1_btctrendfix.PY`