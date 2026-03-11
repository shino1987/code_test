# ICT Smart Money Bot v10.0 - Live Cross Margin Trading

## Overview

This is a completely revised implementation of the ICTR (Inner Circle Trader) strategy for Binance live margin trading. The bot includes:

- ✅ **Centralized Logging System**: All events logged through `log_event()` function
- ✅ **Automatic CSV and Excel Export**: Trades exported with full metadata
- ✅ **Robust Error Handling**: Retry mechanisms with exponential backoff
- ✅ **Mock Testing Mode**: Validate order flow without real trades
- ✅ **Type-Safe Implementation**: Full type hints and dataclasses
- ✅ **Production-Ready Code**: Following Python best practices

## Features

### 1. Centralized Logging
All logging goes through the `TradingLogger` class:
- Console output with timestamps
- Rotating file logs (10MB max, 5 backups)
- CSV export for trade records
- Excel export with formatted columns
- Structured logging with context data

### 2. Configuration Management
All parameters are managed through dataclasses:
- `TradingConfig`: Trading parameters (timeframes, risk, symbols, etc.)
- `APIConfig`: API credentials (from environment variables)
- Easy to modify and extend

### 3. Margin Trading Support
Full support for Binance Cross Margin trading:
- MARGIN_BUY for LONG positions
- AUTO_BORROW_REPAY for SHORT positions
- AUTO_REPAY for closing positions
- Proper quantity and quote formatting according to Binance filters

### 4. Error Handling
Comprehensive error handling:
- Retry with exponential backoff for network errors
- Graceful degradation on API failures
- Detailed error logging with context
- Try/catch blocks around all critical operations

### 5. Mock Testing
Test the bot without risking real money:
```python
config = TradingConfig()
config.mock_mode = True  # Enable mock mode
```

## Installation

### Prerequisites
```bash
pip install ccxt pandas requests openpyxl
```

### Required Packages
- `ccxt`: Binance exchange connection
- `pandas`: Data manipulation
- `requests`: HTTP requests for Telegram
- `openpyxl`: Excel file handling

## Configuration

### Environment Variables
Set the following environment variables before running:

```bash
# Binance API credentials
export BINANCE_API_KEY="your_api_key_here"
export BINANCE_API_SECRET="your_api_secret_here"

# Telegram notifications (optional)
export TG_BOT_TOKEN="your_telegram_bot_token"
export TG_CHAT_ID="your_telegram_chat_id"
```

### Trading Parameters
Edit the `TradingConfig` dataclass to customize:

```python
@dataclass
class TradingConfig:
    # Core settings
    live_trading: bool = True
    mock_mode: bool = False
    
    # Timeframes
    bias_tf: str = "30m"    # Bias timeframe
    entry_tf: str = "5m"    # Entry timeframe
    sl_tf: str = "15m"      # Stop loss timeframe
    
    # Risk management
    max_open_positions: int = 3
    trade_usdc_target: float = 200.0
    tp_gross_pct: float = 0.0120  # 1.20% TP
    sl_fixed_pct: float = 0.0100  # 1.00% SL
    
    # Symbols
    symbols: List[str] = [...]  # List of trading pairs
```

## Usage

### Basic Usage
```bash
python3 GPT_NUOVO_TEST_ICT_LIVE.py
```

### Mock Testing Mode
To test the bot without placing real orders:

```python
# In the main() function or create a test script:
config = TradingConfig()
config.mock_mode = True
config.live_trading = False

# Then run normally
```

Or use the built-in test function:
```python
from GPT_NUOVO_TEST_ICT_LIVE import test_mock_order_flow, TradingConfig, APIConfig, TradingLogger

config = TradingConfig()
api_config = APIConfig.from_env()
logger = TradingLogger(config)

test_mock_order_flow(config, api_config, logger)
```

## File Structure

```
GPT_NUOVO_TEST_ICT_LIVE.py         # Main trading bot
logs/                               # Log files directory
  trading_YYYYMMDD.log             # Daily log files
trades_log.csv                      # CSV trade records
trades_log.xlsx                     # Excel trade records
```

## Logging System

### Console Logs
Real-time logs printed to console:
```
2026-02-12 14:12:06 | INFO     | Exchange initialized
2026-02-12 14:12:08 | INFO     | Markets loaded successfully
2026-02-12 14:12:10 | INFO     | Starting main trading loop...
```

### File Logs
Detailed logs saved to rotating files in `logs/` directory:
```
2026-02-12 14:12:06 | INFO     | _init_exchange | Exchange initialized | api_key_len=64 | has_secret=True
```

### CSV Export
Trade records automatically exported to `trades_log.csv`:
```csv
symbol,side,entry_time,entry_price,exit_time,exit_price,pnl_gross_pct,pnl_net_pct,grade,note,close_reason
BTC/USDC,LONG,2026-02-12T14:15:30,50000.0,2026-02-12T14:45:30,50600.0,1.20,1.00,WIN,ICT LONG confirm,TP_HIT
```

### Excel Export
Trade records with formatted columns in `trades_log.xlsx`:
- Colored headers
- Auto-adjusted column widths
- All trade metadata included

## Position Management

The `PositionManager` class handles all position operations:

### Opening Positions
```python
position_mgr.open_position(
    symbol="BTC/USDC",
    side="LONG",
    entry_ref=50000.0,
    sl_price=49500.0,
    sl_type="FIXED_1%",
    tp_price=50600.0,
    note="ICT LONG confirmation"
)
```

### Closing Positions
```python
position_mgr.close_position(
    symbol="BTC/USDC",
    exit_price=50600.0,
    reason="TP_HIT"
)
```

## Binance-Specific Functions

### Quantity Formatting
```python
# Format quantity according to exchange filters
formatted_qty = format_quantity(exchange, "BTC/USDC", 0.001234)

# Format quote (USDC) amount
formatted_quote = format_quote(exchange, "BTC/USDC", 200.0)
```

### Margin Orders
```python
# Place margin order
order = client.place_margin_order(
    symbol="BTC/USDC",
    side="buy",
    order_type="market",
    amount=0.001,
    params={'isMargin': True}
)
```

## Safety Features

### 1. Pre-Flight Checks
- Time synchronization check
- Market data availability check
- API credentials validation

### 2. Order Validation
- Quantity quantization to exchange step size
- Minimum notional check
- Maximum position limit check

### 3. Error Recovery
- Automatic retry with backoff
- Graceful degradation on failures
- Comprehensive error logging

### 4. Mock Mode
- Test all logic without real orders
- Validate configurations
- Debug trading strategy

## Telegram Notifications

The bot sends notifications for:
- Bot startup/shutdown
- Position opening
- Position closing
- Errors and warnings

Example notification:
```
🟢 OPEN LONG BTC/USDC
ICT LONG confirmation
Entry 50000.000000 (ref 49995.500000)
TP 50600.000000 (1.20%)
SL 49500.000000 (1.00%) | FIXED_1%
Size target 200 USDC
```

## Advanced Configuration

### Custom Logging Level
```python
logger = TradingLogger(config)
logger.logger.setLevel(logging.DEBUG)  # More verbose logging
```

### Custom Symbols
```python
config = TradingConfig()
config.symbols = ["BTC/USDC", "ETH/USDC"]  # Trade only BTC and ETH
```

### Custom Risk Parameters
```python
config = TradingConfig()
config.tp_gross_pct = 0.0200  # 2% TP
config.sl_fixed_pct = 0.0150  # 1.5% SL
config.max_open_positions = 5  # Allow 5 concurrent positions
```

## Troubleshooting

### Issue: "Failed to load markets"
**Solution**: Check your API credentials and internet connection.
```bash
# Verify credentials are set
echo $BINANCE_API_KEY
echo $BINANCE_API_SECRET
```

### Issue: "Time sync error"
**Solution**: The bot automatically adjusts for time differences, but large differences (>5s) are warned about.

### Issue: "Order failed: -1013 Filter failure LOT_SIZE"
**Solution**: The bot automatically handles this by quantizing quantities. If it persists, check the market filters.

### Issue: "Telegram notifications not working"
**Solution**: Verify Telegram credentials are set:
```bash
echo $TG_BOT_TOKEN
echo $TG_CHAT_ID
```

## Development

### Running Tests
```python
# Run mock order flow test
python3 -c "
from GPT_NUOVO_TEST_ICT_LIVE import test_mock_order_flow, TradingConfig, APIConfig, TradingLogger

config = TradingConfig()
config.mock_mode = True
api_config = APIConfig.from_env()
logger = TradingLogger(config)

test_mock_order_flow(config, api_config, logger)
"
```

### Adding New Features
1. Add configuration to `TradingConfig` dataclass
2. Implement logic in appropriate class
3. Add logging with `logger.log_event()`
4. Test in mock mode first
5. Document in this README

## Security Best Practices

1. **Never commit API keys**: Always use environment variables
2. **Start with mock mode**: Test thoroughly before live trading
3. **Use small amounts**: Start with minimum `trade_usdc_target`
4. **Monitor logs**: Regularly check `logs/` directory
5. **Set position limits**: Use `max_open_positions` to limit risk
6. **Review trades**: Check `trades_log.xlsx` regularly

## Comparison with Original

### Improvements Over Original Code

| Feature | Original | New Implementation |
|---------|----------|-------------------|
| Logging | Scattered `print()` statements | Centralized `log_event()` |
| Configuration | Global variables | Dataclasses with type hints |
| Error Handling | Basic try/catch | Retry with exponential backoff |
| Testing | No mock mode | Full mock testing support |
| Documentation | Minimal comments | Comprehensive docstrings |
| Code Style | Mixed conventions | PEP 8 compliant |
| Data Models | Dictionaries | Type-safe dataclasses |
| State Management | String-based | Enum-based |
| Export | CSV only | CSV + Excel with formatting |
| Type Safety | No type hints | Full type annotations |

## License

This code is a revised version for production use. Ensure you have proper authorization to use it for live trading.

## Disclaimer

**Trading cryptocurrencies carries significant risk. This bot is provided as-is without any warranty. Always test thoroughly in mock mode before using real money. Past performance does not guarantee future results.**

## Support

For issues or questions:
1. Check the logs in `logs/` directory
2. Review this README
3. Test in mock mode to isolate issues
4. Check Binance API documentation for margin trading

## Changelog

### v10.0 (2026-02-12)
- Complete code revision
- Centralized logging system
- CSV and Excel export
- Mock testing mode
- Type-safe implementation
- Robust error handling
- Comprehensive documentation
- Production-ready code structure
