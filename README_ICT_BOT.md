# Minimalist ICT Trading Bot

A clean, focused implementation of an Inner Circle Trader (ICT) bot with essential features.

## Features

✅ **Bias Detection (30m)**: Identifies market bias using BOS (Break of Structure) and CHoCH (Change of Character) on swing points

✅ **Entry Logic (5m)**: State machine following ICT methodology:
- WAIT_SWEEP → Price sweeps a swing level
- WAIT_DISPLACEMENT → Strong directional move
- WAIT_RETRACE → Pullback to displacement zone
- WAIT_CONFIRM → Confirmation candle triggers entry

✅ **Structural Stop Loss**: 
- LONG: Below sweep swing_low + 0.02% buffer
- SHORT: Above sweep swing_high + 0.02% buffer

✅ **Structural Take Profits**:
- TP1: Internal liquidity (first swing ahead)
- TP2: External liquidity (major swing ahead)

✅ **Exit Management**:
- SL hit → Close position
- TP1 hit → Move SL to Break-Even
- TP2 hit → Close position

✅ **Paper Trading Only**: Safe testing environment (LIVE_TRADING=False)

✅ **CSV Tracking**: Complete trade history with:
- Entry timestamp, symbol, side, entry price
- SL, TP1, TP2 levels
- Exit price, PnL%, duration, exit reason

✅ **Telegram Notifications**:
- 🟢 OPEN: New position details
- 🟡 TP1_BE: TP1 hit, SL moved to break-even
- 🔴 CLOSE: Position closed (TP2/SL)

✅ **No Filters**: Accepts all valid trade setups

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables:
```bash
export BINANCE_API_KEY="your_api_key"
export BINANCE_API_SECRET="your_api_secret"
export TG_BOT_TOKEN="your_telegram_bot_token"  # Optional
export TG_CHAT_ID="your_telegram_chat_id"      # Optional
export BINANCE_TESTNET="true"                  # Optional, for testnet
```

## Usage

Run the bot:
```bash
python minimalist_ict_bot.py
```

The bot will:
1. Monitor configured symbols (BTC/USDT, ETH/USDT, etc.)
2. Detect 30m bias (BULLISH/BEARISH)
3. Track 5m entry conditions
4. Manage positions with structural SL/TP
5. Log all trades to `ict_trades.csv`
6. Send Telegram notifications (if configured)

## Configuration

Edit the config section in `minimalist_ict_bot.py`:

```python
BIAS_TF = "30m"          # Bias timeframe
ENTRY_TF = "5m"          # Entry timeframe
LOOP_SEC = 30            # Loop delay

SWING_LR = 2             # Swing detection fractal radius
SWEEP_BUFFER_PCT = 0.0002    # 0.02% sweep buffer
STRUCT_SL_BUFFER_PCT = 0.0002  # 0.02% SL buffer

LIVE_TRADING = False     # Paper trading only
MAX_POSITIONS = 3        # Maximum concurrent positions

SYMBOLS = [              # Symbols to trade
    "BTC/USDT", "ETH/USDT", "BNB/USDT", "SOL/USDT",
    "XRP/USDT", "ADA/USDT", "DOGE/USDT", "AVAX/USDT"
]
```

## Output

### CSV File (`ict_trades.csv`)
Contains complete trade history:
```csv
entry_ts,symbol,side,entry,sl,tp1,tp2,exit_price,pnl_pct,duration_min,exit_reason
2026-02-10T12:30:00,BTC/USDT,LONG,50000.0,49900.0,50500.0,51000.0,50500.0,1.00,45.5,TP1_BE
```

### Telegram Notifications

**Position Open:**
```
🟢 OPEN LONG BTC/USDT
Entry: 50000.0
SL: 49900.0 (-0.20%)
TP1: 50500.0 (+1.00%)
TP2: 51000.0 (+2.00%)
```

**TP1 Hit:**
```
🟡 TP1_BE BTC/USDT
TP1 hit, SL moved to BE: 50000.0
```

**Position Close:**
```
🔴 CLOSE LONG BTC/USDT (TP2_CLOSE)
Exit: 51000.0
PnL: +2.00%
Duration: 45.5 min
```

## ICT Concepts

### Break of Structure (BOS)
- Continuation pattern
- Price breaks above previous swing high (bullish)
- Price breaks below previous swing low (bearish)

### Change of Character (CHoCH)
- Reversal pattern
- Failure to make new high/low
- Opposite bias starts forming

### Swing Detection
- Uses fractal method with LR=2
- Identifies local highs/lows
- Used for bias, sweep, and TP detection

### Displacement
- Strong directional move
- Candle range > 1.3x average range
- Body ratio > 60%

### Sweep
- Price wicks through swing level
- Traps liquidity
- Sets up reversal/continuation

## Safety Features

- **Paper Trading Only**: No real trades executed
- **Position Limits**: Maximum 3 concurrent positions
- **Structural SL**: Always set based on swing levels
- **No Overtrading**: One pending state per symbol
- **Error Handling**: Graceful failure recovery

## Testnet Usage

To use Binance testnet:
```bash
export BINANCE_TESTNET="true"
export BINANCE_API_KEY="testnet_api_key"
export BINANCE_API_SECRET="testnet_api_secret"
```

Get testnet credentials from: https://testnet.binance.vision/

## Monitoring

The bot prints heartbeat messages every 10 loops:
```
[12:30:45] Heartbeat | Positions: 2 | Pending: 5
```

Check `ict_trades.csv` for complete trade history.

## Support

For issues or questions, check the code comments or review the ICT trading methodology.

## Disclaimer

This bot is for educational purposes only. Paper trading mode is enforced. Use at your own risk.
