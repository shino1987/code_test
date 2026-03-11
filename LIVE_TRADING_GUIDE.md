# Live Trading Setup Guide - Cross Margin

## ⚠️ IMPORTANT WARNING ⚠️

**LIVE TRADING USES REAL MONEY ON BINANCE CROSS MARGIN**

Before enabling live trading:
- Understand the risks of margin trading
- Start with small position sizes
- Test thoroughly in paper mode first
- Never risk more than you can afford to lose
- Cross margin means all assets in your margin account can be used as collateral

## Configuration

### Enable Live Trading

In `ict_bot_minimal.py`, set:

```python
LIVE_TRADING = True      # True = Live Trading | False = Paper Trading
```

### Live Trading Parameters

```python
TRADE_USDC_TARGET = 200.0  # USDC per trade (adjust to your risk tolerance)
MAX_OPEN_POS = 3           # Maximum concurrent positions
MIN_NOTIONAL_PAD = 1.05    # Padding for minimum notional (safety margin)
```

### Symbols to Trade

```python
SYMBOLS = [
    "BTC/USDT",
    "ETH/USDT",
]
```

**Note:** Only use liquid symbols with good spreads to avoid slippage issues.

## API Key Setup

### 1. Create Binance API Keys

1. Log in to Binance
2. Go to API Management
3. Create new API key
4. **Important permissions needed:**
   - ✅ Enable Reading
   - ✅ Enable Spot & Margin Trading
   - ❌ Disable Withdrawals (for safety)

### 2. Set Environment Variables

**Linux/Mac:**
```bash
export BINANCE_API_KEY="your_api_key_here"
export BINANCE_API_SECRET="your_api_secret_here"
```

**Windows (Command Prompt):**
```cmd
set BINANCE_API_KEY=your_api_key_here
set BINANCE_API_SECRET=your_api_secret_here
```

**Windows (PowerShell):**
```powershell
$env:BINANCE_API_KEY="your_api_key_here"
$env:BINANCE_API_SECRET="your_api_secret_here"
```

**Using .env file (recommended):**
```bash
# Create .env file
echo 'BINANCE_API_KEY=your_api_key_here' > .env
echo 'BINANCE_API_SECRET=your_api_secret_here' >> .env

# Load before running
export $(cat .env | xargs)
```

### 3. Verify API Keys

The bot will check API key length on startup and show:
```
API Key length: 64
API Secret length: 64
```

## Cross Margin Account Setup

### Prerequisites

1. **Enable Cross Margin Trading** on Binance:
   - Go to Binance > Margin > Cross Margin
   - Complete verification if needed
   - Transfer USDT to Cross Margin account

2. **Transfer Funds**:
   - Transfer USDT from Spot to Cross Margin account
   - Recommended: Start with small amount for testing
   - Formula: `TRADE_USDC_TARGET × MAX_OPEN_POS × 2` (for safety)
   - Example: $200 × 3 × 2 = $1,200 USDT minimum

3. **Understand Cross Margin Risks**:
   - All assets in margin account are collateral
   - Losses can exceed your position size
   - Liquidation risk if margin ratio gets too low
   - Interest charged on borrowed amounts

## How Cross Margin Orders Work

### LONG Entry (Buy)
```python
# Bot executes:
{
    "symbol": "BTCUSDT",
    "side": "BUY",
    "type": "MARKET",
    "sideEffectType": "MARGIN_BUY",  # Buy on margin
    "quoteOrderQty": "200"            # $200 USDT worth
}
```

### SHORT Entry (Sell)
```python
# Bot executes:
{
    "symbol": "BTCUSDT",
    "side": "SELL",
    "type": "MARKET",
    "sideEffectType": "AUTO_BORROW_REPAY",  # Auto borrow BTC and sell
    "quantity": "0.005"                      # Amount calculated from $200
}
```

### Close Position
```python
# Bot executes (opposite side):
{
    "symbol": "BTCUSDT",
    "side": "SELL" or "BUY",
    "type": "MARKET",
    "sideEffectType": "AUTO_REPAY",  # Automatically repay borrowed amount
    "quantity": "actual_position_size"
}
```

## Running the Bot

### 1. Paper Trading Test (Recommended First)

```bash
# Set to paper mode in ict_bot_minimal.py
LIVE_TRADING = False

# Run the bot
python ict_bot_minimal.py
```

Test for at least 24-48 hours to verify:
- Entry signals are correct
- SL/TP levels are appropriate
- No errors in execution logic

### 2. Live Trading

```bash
# Set environment variables
export BINANCE_API_KEY="your_key"
export BINANCE_API_SECRET="your_secret"

# Set to live mode in ict_bot_minimal.py
LIVE_TRADING = True

# Run the bot
python ict_bot_minimal.py
```

### Console Output

**Live Trading Mode:**
```
⚠️  ⚠️  ⚠️  LIVE TRADING MODE - CROSS MARGIN  ⚠️  ⚠️  ⚠️
WARNING: This bot will trade with REAL MONEY!
============================================================
Max Positions: 3
Trade Size: $200.0 USDT per trade
Symbols: BTC/USDT, ETH/USDT
Bias TF: 30m | Entry TF: 5m
============================================================
```

**When Opening Position:**
```
🔥 OPENING LIVE POSITION: BTC/USDT LONG
✅ LIVE POSITION OPENED: BTC/USDT LONG
   Entry: $41523.45 (Qty: 0.004814)
   SL: $40479.75 (-2.51%)
   TP1: $42100.00 (1.39%)
   TP2: $42650.00 (2.71%)
```

**When Closing Position:**
```
🔥 CLOSING LIVE POSITION: BTC/USDT LONG (Amount: 0.004814)
✅ LIVE POSITION CLOSED: BTC/USDT at $42100.00
🔴 LIVE TRADE CLOSED: BTC/USDT LONG
   Exit: $42100.00
   PnL: 1.19% (Net)
   Duration: 45.3 min
   Reason: TP1_HIT
```

## Trade Logging

All trades (paper and live) are logged to `ict_trades.csv`:

**File Location:** `ict_trades.csv` is saved in the **same directory** where you run the bot.

**How to find it:**
- Windows: `dir ict_trades.csv` or look in the bot folder
- Linux/Mac: `ls ict_trades.csv` or `pwd` to see current directory
- See [FILE_LOCATIONS.md](FILE_LOCATIONS.md) for complete guide

**CSV Format:**
```csv
timestamp,symbol,side,entry_price,sl_price,tp1_price,tp2_price,exit_price,pnl_gross_pct,pnl_net_pct,duration_min,exit_reason
2026-02-11 15:30:00,BTC/USDT,LONG,41523.45,40479.75,42100.00,42650.00,42100.00,1.39,1.19,45.3,TP1_HIT
```

**Opening the file:**
- Excel: File → Open → `ict_trades.csv`
- Google Sheets: File → Import
- Text editor: Double-click the file

## Position Limits

The bot enforces maximum concurrent positions:

```python
MAX_OPEN_POS = 3  # Maximum 3 positions at once
```

If limit is reached:
```
⚠️  BTC/USDT: SKIP - Max positions (3) reached
```

## Risk Management

### Position Sizing

**Conservative (Recommended for beginners):**
```python
TRADE_USDC_TARGET = 50.0   # $50 per trade
MAX_OPEN_POS = 2           # Max 2 positions
# Total exposure: $100
```

**Moderate:**
```python
TRADE_USDC_TARGET = 200.0  # $200 per trade
MAX_OPEN_POS = 3           # Max 3 positions
# Total exposure: $600
```

**Aggressive (Use with caution):**
```python
TRADE_USDC_TARGET = 500.0  # $500 per trade
MAX_OPEN_POS = 5           # Max 5 positions
# Total exposure: $2,500
```

### Stop Loss Buffer

Current configuration:
```python
STRUCT_SL_BUFFER_PCT = 0.0005  # 0.05% buffer beyond swing
MIN_SL_PCT = 0.003             # Minimum 0.3% SL
```

This means:
- SL is placed at structural swing ± 0.05%
- Minimum distance of 0.3% from entry
- Actual SL typically 0.5% - 2% depending on structure

### Margin Requirements

**Cross Margin Maintenance:**
- Keep margin ratio above 1.5 (150%)
- Bot uses ~2x leverage per trade
- Monitor Binance margin ratio regularly
- Add funds if ratio drops below 2.0

**Calculation:**
```
Account Value = Assets - Liabilities
Margin Ratio = Account Value / (Liabilities + Open Orders)
```

## Monitoring

### What to Monitor

1. **Console Output:**
   - Position entries/exits
   - Error messages
   - API connection status

2. **Binance App/Website:**
   - Margin ratio
   - Open positions
   - Account balance
   - Interest accrued

3. **CSV Log:**
   - Trade performance
   - Win rate
   - PnL tracking

### Red Flags

Stop the bot immediately if:
- ❌ Repeated API errors
- ❌ Margin ratio below 1.5
- ❌ Unexpected position sizes
- ❌ Orders not executing
- ❌ Multiple SL hits in a row

## Troubleshooting

### Common Issues

**1. "Missing API credentials"**
```
Solution: Set BINANCE_API_KEY and BINANCE_API_SECRET environment variables
```

**2. "Filter failure LOT_SIZE"**
```
Solution: Binance filters are handled automatically. If persists, reduce TRADE_USDC_TARGET
```

**3. "Insufficient margin"**
```
Solution: Transfer more USDT to Cross Margin account or reduce position size
```

**4. "Order would trigger immediately"**
```
Solution: This is normal - bot uses market orders, not limit orders
```

**5. Connection errors**
```
Solution: Check internet connection and Binance API status
```

### Testing Checklist

Before running live:
- [ ] Tested in paper mode for 24+ hours
- [ ] Verified API keys are correct
- [ ] Transferred funds to Cross Margin account
- [ ] Set appropriate position size
- [ ] Understand cross margin risks
- [ ] Have plan for monitoring
- [ ] Know how to stop the bot quickly

## Emergency Stop

**To stop the bot:**
1. Press `Ctrl+C` in terminal
2. Bot will attempt to close all open positions
3. Check Binance to verify all positions closed
4. Manually close any remaining positions if needed

**Force stop (if needed):**
1. Kill the process: `kill -9 <PID>`
2. Manually close positions on Binance
3. Check for any borrowed amounts and repay

## Best Practices

1. **Start Small:** Begin with minimum position sizes
2. **Monitor Actively:** Check the bot regularly, especially first few days
3. **Set Alerts:** Use Binance mobile app for position notifications
4. **Keep Buffer:** Maintain 2x minimum margin requirement
5. **Review Logs:** Analyze `ict_trades.csv` daily
6. **Gradual Scaling:** Only increase size after consistent profitability
7. **Risk Limits:** Never risk more than 1-2% of account per trade
8. **Have Exit Plan:** Know when to stop (drawdown limits, win targets)

## Support

If you encounter issues:
1. Check console output for error messages
2. Verify API keys and permissions
3. Check Binance Cross Margin account status
4. Review recent commits in repository
5. Test in paper mode to isolate issue

## Disclaimer

**USE AT YOUR OWN RISK**

- This bot is for educational purposes
- No warranty or guarantee of profits
- You are responsible for all trades executed
- Understand margin trading risks before using
- Past performance doesn't guarantee future results
- The developer is not liable for any losses

---

**Remember:** Trading cryptocurrencies on margin carries significant risk. Only trade with money you can afford to lose completely.
