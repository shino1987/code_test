# Minimalist ICT Paper Trading Bot

A clean, minimalist implementation of an ICT (Inner Circle Trading) bot for **paper trading only**.

## Features

✅ **Bias Detection (30m)**: Identifies market direction using BOS/CHoCH on swing structures  
✅ **Entry Logic (5m)**: 4-state machine: SWEEP → DISPLACEMENT → RETRACE → CONFIRM  
✅ **Structural SL/TP**: Stop loss below/above swing points, TPs at internal and external liquidity  
✅ **Paper Trading Only**: No real money at risk (LIVE_TRADING=False)  
✅ **CSV Tracking**: All trades logged to `ict_trades.csv` with detailed metrics  
✅ **Console Logging**: Real-time updates to console (no Telegram)  
✅ **Zero Filters**: Accepts all valid ICT setups without additional filters  

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the bot:
```bash
python ict_bot_minimal.py
```

## How It Works

### Bias Detection (30m Timeframe)
- Detects swing highs and lows using fractal pattern (LR=2)
- Identifies BOS (Break of Structure) when price breaks previous swing
- Identifies CHoCH (Change of Character) for trend reversals
- Determines BULLISH or BEARISH bias

### Entry Setup (5m Timeframe)

The bot uses a 4-state machine:

1. **WAIT_SWEEP**: Looking for liquidity sweep
   - LONG: Price wicks below swing low, closes above it
   - SHORT: Price wicks above swing high, closes below it

2. **WAIT_DISPLACEMENT**: Looking for strong directional move
   - Candle range > average range × 1.5
   - Body > 60% of range
   - Direction matches bias

3. **WAIT_RETRACE**: Looking for pullback
   - LONG: Price retraces below displacement high
   - SHORT: Price retraces above displacement low

4. **WAIT_CONFIRM**: Looking for confirmation
   - LONG: Bullish candle (close > open)
   - SHORT: Bearish candle (close < open)
   - **ENTRY**: Opens position at current close price

### Position Management

**Stop Loss (SL)**:
- Placed below sweep level for LONG (above for SHORT)
- Includes 0.05% buffer beyond structural level
- Minimum 0.3% distance enforced

**Take Profit (TP)**:
- TP1: First swing ahead (internal liquidity)
- TP2: Second/major swing ahead (external liquidity)

**Exit Logic**:
- SL hit → Close position at SL price
- TP1 hit → Move SL to breakeven, continue to TP2
- TP2 hit → Close position at TP2 price

### CSV Trade Log

Every trade is logged to `ict_trades.csv` with:
- Timestamp
- Symbol
- Side (LONG/SHORT)
- Entry price
- SL price
- TP1 price
- TP2 price
- Exit price
- PnL (Gross %)
- PnL (Net %, includes estimated fees)
- Duration (minutes)
- Exit reason (SL_HIT, TP1_HIT, TP2_HIT, BOT_STOPPED)

## Configuration

Edit the configuration section in `ict_bot_minimal.py`:

```python
BIAS_TF = "30m"          # Bias timeframe
ENTRY_TF = "5m"          # Entry timeframe
LOOP_SEC = 30            # Main loop interval (seconds)

SWING_LR = 2             # Left/Right bars for swing detection
SWEEP_BUFFER_PCT = 0.0002  # 0.02% buffer for sweep detection
STRUCT_SL_BUFFER_PCT = 0.0005  # 0.05% buffer beyond swing for SL

SYMBOLS = [              # Symbols to trade
    "BTC/USDT",
    "ETH/USDT",
]

PAPER_POSITION_SIZE_USDC = 100.0  # Simulated position size
```

## Paper Trading

This bot is designed for **paper trading only**:
- No API keys required (uses public data)
- No real orders placed
- Simulated position management
- Educational and testing purposes

## Safety Features

- `LIVE_TRADING = False` hardcoded
- No real exchange orders
- All trades are simulated
- Console logging only (no external notifications)

## Requirements

- Python 3.8+
- ccxt >= 4.0.0
- pandas >= 2.0.0

## License

Open source - use at your own risk. For educational purposes only.

---

**Disclaimer**: This is a paper trading bot for educational purposes. Do not use with real money without proper testing and risk management.
