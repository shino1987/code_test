"""
Trading Execution Module
Handles order placement, position management, and risk controls
"""

import logging
from typing import Optional, Dict
from datetime import datetime


class Position:
    """Represents an open trading position"""
    
    def __init__(self, symbol: str, side: str, entry_price: float, 
                 size: float, stop_loss: float, take_profit: float):
        self.symbol = symbol
        self.side = side  # LONG or SHORT
        self.entry_price = entry_price
        self.size = size
        self.stop_loss = stop_loss
        self.take_profit = take_profit
        self.entry_time = datetime.now()
        self.pnl = 0.0
        self.status = "OPEN"
    
    def update_pnl(self, current_price: float):
        """Calculate current profit/loss"""
        if self.side == "LONG":
            self.pnl = (current_price - self.entry_price) / self.entry_price * 100
        else:  # SHORT
            self.pnl = (self.entry_price - current_price) / self.entry_price * 100
    
    def check_exit(self, current_price: float) -> Optional[str]:
        """Check if position should be closed (TP/SL hit)"""
        self.update_pnl(current_price)
        
        if self.side == "LONG":
            if current_price >= self.take_profit:
                return "TAKE_PROFIT"
            elif current_price <= self.stop_loss:
                return "STOP_LOSS"
        else:  # SHORT
            if current_price <= self.take_profit:
                return "TAKE_PROFIT"
            elif current_price >= self.stop_loss:
                return "STOP_LOSS"
        
        return None
    
    def __repr__(self):
        return (f"Position({self.symbol}, {self.side}, "
                f"entry={self.entry_price:.2f}, pnl={self.pnl:.2f}%)")


class Trader:
    """Manages trading operations and positions"""
    
    def __init__(self, exchange=None, live_trading: bool = False):
        self.exchange = exchange
        self.live_trading = live_trading
        self.positions: Dict[str, Position] = {}
        self.logger = logging.getLogger(__name__)
        self.trade_history = []
    
    def open_position(self, symbol: str, side: str, current_price: float,
                     size_usdt: float, stop_loss_pct: float, 
                     take_profit_pct: float) -> bool:
        """
        Open a new trading position
        
        Args:
            symbol: Trading pair
            side: LONG or SHORT
            current_price: Current market price
            size_usdt: Position size in USDT
            stop_loss_pct: Stop loss percentage
            take_profit_pct: Take profit percentage
        
        Returns:
            True if position opened successfully
        """
        if symbol in self.positions:
            self.logger.warning(f"Position already exists for {symbol}")
            return False
        
        # Calculate position size
        position_size = size_usdt / current_price
        
        # Calculate stop loss and take profit prices
        if side == "LONG":
            stop_loss = current_price * (1 - stop_loss_pct / 100)
            take_profit = current_price * (1 + take_profit_pct / 100)
        else:  # SHORT
            stop_loss = current_price * (1 + stop_loss_pct / 100)
            take_profit = current_price * (1 - take_profit_pct / 100)
        
        # Create position
        position = Position(
            symbol=symbol,
            side=side,
            entry_price=current_price,
            size=position_size,
            stop_loss=stop_loss,
            take_profit=take_profit
        )
        
        # Execute order if live trading
        if self.live_trading and self.exchange:
            try:
                order_side = 'buy' if side == "LONG" else 'sell'
                order = self.exchange.create_market_order(
                    symbol=symbol,
                    side=order_side,
                    amount=position_size
                )
                self.logger.info(f"Live order executed: {order}")
            except Exception as e:
                self.logger.error(f"Failed to execute order: {e}")
                return False
        
        # Store position
        self.positions[symbol] = position
        
        self.logger.info(
            f"Opened {side} position: {symbol} @ {current_price:.2f} "
            f"| SL: {stop_loss:.2f} | TP: {take_profit:.2f}"
        )
        
        return True
    
    def close_position(self, symbol: str, current_price: float, 
                      reason: str = "MANUAL") -> Optional[Dict]:
        """
        Close an existing position
        
        Returns:
            Dict with trade details
        """
        if symbol not in self.positions:
            self.logger.warning(f"No position to close for {symbol}")
            return None
        
        position = self.positions[symbol]
        position.update_pnl(current_price)
        
        # Execute closing order if live trading
        if self.live_trading and self.exchange:
            try:
                order_side = 'sell' if position.side == "LONG" else 'buy'
                order = self.exchange.create_market_order(
                    symbol=symbol,
                    side=order_side,
                    amount=position.size
                )
                self.logger.info(f"Live close order executed: {order}")
            except Exception as e:
                self.logger.error(f"Failed to close position: {e}")
        
        # Create trade record
        trade_record = {
            'symbol': symbol,
            'side': position.side,
            'entry_price': position.entry_price,
            'exit_price': current_price,
            'size': position.size,
            'pnl_pct': position.pnl,
            'entry_time': position.entry_time,
            'exit_time': datetime.now(),
            'reason': reason
        }
        
        self.logger.info(
            f"Closed {position.side} position: {symbol} @ {current_price:.2f} "
            f"| PnL: {position.pnl:.2f}% | Reason: {reason}"
        )
        
        # Store in history and remove from active positions
        self.trade_history.append(trade_record)
        del self.positions[symbol]
        
        return trade_record
    
    def check_positions(self, current_price: float):
        """Check all positions for exit conditions"""
        positions_to_close = []
        
        for symbol, position in self.positions.items():
            exit_reason = position.check_exit(current_price)
            if exit_reason:
                positions_to_close.append((symbol, exit_reason))
        
        # Close positions that hit TP/SL
        for symbol, reason in positions_to_close:
            self.close_position(symbol, current_price, reason)
    
    def get_open_positions_count(self) -> int:
        """Return number of open positions"""
        return len(self.positions)
    
    def get_statistics(self) -> Dict:
        """Calculate trading statistics"""
        if not self.trade_history:
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0.0,
                'total_pnl': 0.0
            }
        
        winning_trades = [t for t in self.trade_history if t['pnl_pct'] > 0]
        losing_trades = [t for t in self.trade_history if t['pnl_pct'] <= 0]
        
        return {
            'total_trades': len(self.trade_history),
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'win_rate': len(winning_trades) / len(self.trade_history) * 100,
            'total_pnl': sum(t['pnl_pct'] for t in self.trade_history)
        }
