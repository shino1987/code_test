"""
Simple tests for the scalping bot components
"""

import unittest
import pandas as pd
import numpy as np
from scalping_bot.strategy import ScalpingStrategy
from scalping_bot.trader import Position, Trader


class TestScalpingStrategy(unittest.TestCase):
    """Test cases for ScalpingStrategy"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.strategy = ScalpingStrategy(rsi_period=14, rsi_oversold=30, rsi_overbought=70)
    
    def test_rsi_calculation(self):
        """Test RSI calculation"""
        # Create sample data
        dates = pd.date_range('2024-01-01', periods=50, freq='1min')
        prices = np.random.randn(50).cumsum() + 100
        df = pd.DataFrame({
            'close': prices,
            'timestamp': dates
        })
        
        rsi = self.strategy.calculate_rsi(df)
        
        # RSI should be between 0 and 100
        self.assertTrue(all(rsi.dropna() >= 0))
        self.assertTrue(all(rsi.dropna() <= 100))
    
    def test_signal_generation(self):
        """Test signal generation"""
        # Create data with clear RSI pattern
        dates = pd.date_range('2024-01-01', periods=30, freq='1min')
        
        # Create oversold then bounce scenario
        prices = list(range(100, 80, -1)) + list(range(80, 90))
        df = pd.DataFrame({
            'close': prices,
            'timestamp': dates
        })
        
        signal = self.strategy.analyze(df)
        
        # Signal should have required fields
        self.assertIn('action', signal)
        self.assertIn('reason', signal)
        self.assertIn(signal['action'], ['BUY', 'SELL', 'HOLD'])


class TestPosition(unittest.TestCase):
    """Test cases for Position class"""
    
    def test_position_creation(self):
        """Test position initialization"""
        position = Position(
            symbol="BTC/USDT",
            side="LONG",
            entry_price=50000.0,
            size=0.002,
            stop_loss=49750.0,
            take_profit=50400.0
        )
        
        self.assertEqual(position.symbol, "BTC/USDT")
        self.assertEqual(position.side, "LONG")
        self.assertEqual(position.entry_price, 50000.0)
    
    def test_pnl_calculation_long(self):
        """Test PnL calculation for LONG position"""
        position = Position(
            symbol="BTC/USDT",
            side="LONG",
            entry_price=50000.0,
            size=0.002,
            stop_loss=49750.0,
            take_profit=50400.0
        )
        
        # Price goes up 1%
        position.update_pnl(50500.0)
        self.assertAlmostEqual(position.pnl, 1.0, places=1)
        
        # Price goes down 1%
        position.update_pnl(49500.0)
        self.assertAlmostEqual(position.pnl, -1.0, places=1)
    
    def test_pnl_calculation_short(self):
        """Test PnL calculation for SHORT position"""
        position = Position(
            symbol="BTC/USDT",
            side="SHORT",
            entry_price=50000.0,
            size=0.002,
            stop_loss=50250.0,
            take_profit=49600.0
        )
        
        # Price goes down 1% (profit for short)
        position.update_pnl(49500.0)
        self.assertAlmostEqual(position.pnl, 1.0, places=1)
        
        # Price goes up 1% (loss for short)
        position.update_pnl(50500.0)
        self.assertAlmostEqual(position.pnl, -1.0, places=1)
    
    def test_exit_conditions_long(self):
        """Test exit conditions for LONG position"""
        position = Position(
            symbol="BTC/USDT",
            side="LONG",
            entry_price=50000.0,
            size=0.002,
            stop_loss=49750.0,
            take_profit=50400.0
        )
        
        # Take profit hit
        exit_reason = position.check_exit(50450.0)
        self.assertEqual(exit_reason, "TAKE_PROFIT")
        
        # Stop loss hit
        exit_reason = position.check_exit(49700.0)
        self.assertEqual(exit_reason, "STOP_LOSS")
        
        # No exit
        exit_reason = position.check_exit(50100.0)
        self.assertIsNone(exit_reason)


class TestTrader(unittest.TestCase):
    """Test cases for Trader class"""
    
    def test_trader_initialization(self):
        """Test trader initialization"""
        trader = Trader(exchange=None, live_trading=False)
        
        self.assertEqual(trader.get_open_positions_count(), 0)
        self.assertEqual(len(trader.trade_history), 0)
    
    def test_open_position(self):
        """Test opening a position"""
        trader = Trader(exchange=None, live_trading=False)
        
        success = trader.open_position(
            symbol="BTC/USDT",
            side="LONG",
            current_price=50000.0,
            size_usdt=100.0,
            stop_loss_pct=0.5,
            take_profit_pct=0.8
        )
        
        self.assertTrue(success)
        self.assertEqual(trader.get_open_positions_count(), 1)
    
    def test_close_position(self):
        """Test closing a position"""
        trader = Trader(exchange=None, live_trading=False)
        
        # Open position
        trader.open_position(
            symbol="BTC/USDT",
            side="LONG",
            current_price=50000.0,
            size_usdt=100.0,
            stop_loss_pct=0.5,
            take_profit_pct=0.8
        )
        
        # Close position
        trade_record = trader.close_position("BTC/USDT", 50400.0, "TAKE_PROFIT")
        
        self.assertIsNotNone(trade_record)
        self.assertEqual(trader.get_open_positions_count(), 0)
        self.assertEqual(len(trader.trade_history), 1)
    
    def test_statistics(self):
        """Test statistics calculation"""
        trader = Trader(exchange=None, live_trading=False)
        
        # Open and close a winning trade
        trader.open_position("BTC/USDT", "LONG", 50000.0, 100.0, 0.5, 0.8)
        trader.close_position("BTC/USDT", 50400.0, "TAKE_PROFIT")
        
        # Open and close a losing trade
        trader.open_position("ETH/USDT", "LONG", 3000.0, 100.0, 0.5, 0.8)
        trader.close_position("ETH/USDT", 2985.0, "STOP_LOSS")
        
        stats = trader.get_statistics()
        
        self.assertEqual(stats['total_trades'], 2)
        self.assertEqual(stats['winning_trades'], 1)
        self.assertEqual(stats['losing_trades'], 1)
        self.assertAlmostEqual(stats['win_rate'], 50.0, places=1)


if __name__ == '__main__':
    unittest.main()
