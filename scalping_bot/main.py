"""
Scalping Trading Bot - Main Entry Point
"""

import os
import time
import logging
import pandas as pd
import ccxt
from datetime import datetime
from typing import Optional

# Import bot modules
from scalping_bot.config import *
from scalping_bot.strategy import ScalpingStrategy
from scalping_bot.trader import Trader


def setup_logging():
    """Configure logging"""
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(LOG_FILE),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)


def initialize_exchange() -> Optional[ccxt.Exchange]:
    """Initialize exchange connection"""
    logger = logging.getLogger(__name__)
    
    if not LIVE_TRADING:
        logger.info("Running in PAPER TRADING mode (no real orders)")
        return None
    
    # Get credentials from environment
    api_key = os.getenv('EXCHANGE_API_KEY')
    api_secret = os.getenv('EXCHANGE_API_SECRET')
    exchange_name = os.getenv('EXCHANGE_NAME', 'binance')
    
    if not api_key or not api_secret:
        logger.error("Exchange credentials not found in environment variables")
        logger.error("Set EXCHANGE_API_KEY and EXCHANGE_API_SECRET")
        return None
    
    try:
        # Initialize exchange
        exchange_class = getattr(ccxt, exchange_name)
        exchange = exchange_class({
            'apiKey': api_key,
            'secret': api_secret,
            'enableRateLimit': True,
            'options': {
                'defaultType': 'future',  # Use futures for scalping
            }
        })
        
        # Test connection
        exchange.load_markets()
        logger.info(f"Successfully connected to {exchange_name}")
        
        return exchange
        
    except Exception as e:
        logger.error(f"Failed to initialize exchange: {e}")
        return None


def fetch_ohlcv(exchange: Optional[ccxt.Exchange], symbol: str, 
                timeframe: str, limit: int = 100) -> pd.DataFrame:
    """
    Fetch OHLCV data from exchange or generate dummy data for paper trading
    """
    logger = logging.getLogger(__name__)
    
    if exchange:
        try:
            ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            df = pd.DataFrame(
                ohlcv, 
                columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
            )
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            return df
        except Exception as e:
            logger.error(f"Failed to fetch OHLCV data: {e}")
            return pd.DataFrame()
    else:
        # Generate dummy data for paper trading (random walk)
        import numpy as np
        
        current_price = 50000.0  # Starting BTC price for demo
        dates = pd.date_range(end=datetime.now(), periods=limit, freq='1min')
        
        # Generate random walk
        returns = np.random.randn(limit) * 0.001  # 0.1% volatility
        prices = current_price * (1 + returns).cumprod()
        
        df = pd.DataFrame({
            'timestamp': dates,
            'open': prices,
            'high': prices * 1.001,
            'low': prices * 0.999,
            'close': prices,
            'volume': np.random.randint(100, 1000, limit)
        })
        
        return df


def send_telegram_notification(message: str):
    """Send notification via Telegram"""
    logger = logging.getLogger(__name__)
    
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    if not token or not chat_id:
        return
    
    try:
        import requests
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        requests.post(url, json={
            'chat_id': chat_id,
            'text': message
        }, timeout=10)
    except Exception as e:
        logger.warning(f"Failed to send Telegram notification: {e}")


def main():
    """Main bot loop"""
    logger = setup_logging()
    logger.info("=" * 60)
    logger.info("Starting Scalping Trading Bot")
    logger.info("=" * 60)
    logger.info(f"Symbol: {SYMBOL}")
    logger.info(f"Timeframe: {TIMEFRAME}")
    logger.info(f"Trading Mode: {'LIVE' if LIVE_TRADING else 'PAPER'}")
    logger.info("=" * 60)
    
    # Initialize components
    exchange = initialize_exchange()
    strategy = ScalpingStrategy(
        rsi_period=RSI_PERIOD,
        rsi_oversold=RSI_OVERSOLD,
        rsi_overbought=RSI_OVERBOUGHT
    )
    trader = Trader(exchange=exchange, live_trading=LIVE_TRADING)
    
    # Send startup notification
    send_telegram_notification(
        f"🤖 Scalping Bot Started\n"
        f"Symbol: {SYMBOL}\n"
        f"Mode: {'LIVE' if LIVE_TRADING else 'PAPER'}"
    )
    
    loop_count = 0
    
    try:
        while True:
            loop_count += 1
            logger.info(f"\n--- Loop {loop_count} ---")
            
            # Fetch market data
            df = fetch_ohlcv(exchange, SYMBOL, TIMEFRAME, limit=100)
            
            if df.empty:
                logger.warning("No data received, skipping iteration")
                time.sleep(LOOP_INTERVAL)
                continue
            
            current_price = df['close'].iloc[-1]
            logger.info(f"Current price: {current_price:.2f}")
            
            # Check existing positions for TP/SL
            trader.check_positions(current_price)
            
            # Analyze market and generate signals
            signal = strategy.analyze(df)
            logger.info(f"Signal: {signal['action']} | {signal['reason']} | RSI: {signal.get('rsi', 'N/A')}")
            
            # Execute trades based on signals
            if trader.get_open_positions_count() < MAX_OPEN_POSITIONS:
                if signal['action'] == 'BUY':
                    success = trader.open_position(
                        symbol=SYMBOL,
                        side="LONG",
                        current_price=current_price,
                        size_usdt=POSITION_SIZE_USDT,
                        stop_loss_pct=STOP_LOSS_PERCENTAGE,
                        take_profit_pct=TAKE_PROFIT_PERCENTAGE
                    )
                    
                    if success:
                        msg = (f"📈 LONG Entry\n"
                               f"Price: {current_price:.2f}\n"
                               f"RSI: {signal.get('rsi')}\n"
                               f"SL: -{STOP_LOSS_PERCENTAGE}%\n"
                               f"TP: +{TAKE_PROFIT_PERCENTAGE}%")
                        send_telegram_notification(msg)
                
                elif signal['action'] == 'SELL':
                    success = trader.open_position(
                        symbol=SYMBOL,
                        side="SHORT",
                        current_price=current_price,
                        size_usdt=POSITION_SIZE_USDT,
                        stop_loss_pct=STOP_LOSS_PERCENTAGE,
                        take_profit_pct=TAKE_PROFIT_PERCENTAGE
                    )
                    
                    if success:
                        msg = (f"📉 SHORT Entry\n"
                               f"Price: {current_price:.2f}\n"
                               f"RSI: {signal.get('rsi')}\n"
                               f"SL: +{STOP_LOSS_PERCENTAGE}%\n"
                               f"TP: -{TAKE_PROFIT_PERCENTAGE}%")
                        send_telegram_notification(msg)
            
            # Display statistics every 10 loops
            if loop_count % 10 == 0:
                stats = trader.get_statistics()
                logger.info("\n" + "=" * 60)
                logger.info("STATISTICS")
                logger.info(f"Total Trades: {stats['total_trades']}")
                logger.info(f"Winning: {stats['winning_trades']} | Losing: {stats['losing_trades']}")
                logger.info(f"Win Rate: {stats['win_rate']:.1f}%")
                logger.info(f"Total PnL: {stats['total_pnl']:.2f}%")
                logger.info("=" * 60 + "\n")
            
            # Wait before next iteration
            time.sleep(LOOP_INTERVAL)
    
    except KeyboardInterrupt:
        logger.info("\n⚠️ Bot stopped by user")
        send_telegram_notification("🛑 Scalping Bot Stopped")
    
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        send_telegram_notification(f"❌ Bot Error: {e}")
    
    finally:
        # Final statistics
        stats = trader.get_statistics()
        logger.info("\n" + "=" * 60)
        logger.info("FINAL STATISTICS")
        logger.info(f"Total Trades: {stats['total_trades']}")
        logger.info(f"Win Rate: {stats['win_rate']:.1f}%")
        logger.info(f"Total PnL: {stats['total_pnl']:.2f}%")
        logger.info("=" * 60)


if __name__ == "__main__":
    main()
