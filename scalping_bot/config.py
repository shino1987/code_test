"""
Configuration module for the Scalping Trading Bot
"""

# Trading Configuration
SYMBOL = "BTC/USDT"
TIMEFRAME = "1m"  # Scalping typically uses 1-minute or 5-minute timeframes
LOOP_INTERVAL = 10  # seconds

# Strategy Parameters
RSI_PERIOD = 14
RSI_OVERSOLD = 30
RSI_OVERBOUGHT = 70

# Risk Management
POSITION_SIZE_USDT = 100.0  # Amount in USDT per trade
STOP_LOSS_PERCENTAGE = 0.5  # 0.5%
TAKE_PROFIT_PERCENTAGE = 0.8  # 0.8% - scalping targets small profits
MAX_OPEN_POSITIONS = 1

# Exchange Configuration (set via environment variables)
# EXCHANGE_API_KEY
# EXCHANGE_API_SECRET
# EXCHANGE_NAME (default: binance)

# Telegram Configuration (optional, set via environment variables)
# TELEGRAM_BOT_TOKEN
# TELEGRAM_CHAT_ID

# Logging
LOG_LEVEL = "INFO"
LOG_FILE = "scalping_bot.log"

# Trading Mode
LIVE_TRADING = False  # Set to True for live trading, False for paper trading/testing
