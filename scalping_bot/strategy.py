"""
Scalping Strategy Implementation
Simple RSI-based scalping strategy
"""

import pandas as pd
import numpy as np
from typing import Optional, Dict


class ScalpingStrategy:
    """
    Simple RSI-based scalping strategy.
    
    Entry signals:
    - LONG: RSI crosses above oversold level
    - SHORT: RSI crosses below overbought level
    
    Exit signals:
    - Take profit or stop loss hit
    """
    
    def __init__(self, rsi_period: int = 14, 
                 rsi_oversold: int = 30, 
                 rsi_overbought: int = 70):
        self.rsi_period = rsi_period
        self.rsi_oversold = rsi_oversold
        self.rsi_overbought = rsi_overbought
        self.last_signal = None
    
    def calculate_rsi(self, data: pd.DataFrame) -> pd.Series:
        """Calculate RSI indicator"""
        if 'close' not in data.columns:
            raise ValueError("DataFrame must contain 'close' column")
        
        delta = data['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.rsi_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.rsi_period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def analyze(self, data: pd.DataFrame) -> Optional[Dict]:
        """
        Analyze market data and generate trading signals
        
        Returns:
            Dict with 'action' (BUY/SELL/HOLD) and 'reason'
        """
        if len(data) < self.rsi_period + 1:
            return {'action': 'HOLD', 'reason': 'Insufficient data'}
        
        # Calculate RSI
        data['rsi'] = self.calculate_rsi(data)
        
        # Get current and previous RSI values
        current_rsi = data['rsi'].iloc[-1]
        previous_rsi = data['rsi'].iloc[-2]
        current_price = data['close'].iloc[-1]
        
        if pd.isna(current_rsi) or pd.isna(previous_rsi):
            return {'action': 'HOLD', 'reason': 'RSI calculation incomplete'}
        
        # Long signal: RSI crosses above oversold
        if previous_rsi <= self.rsi_oversold and current_rsi > self.rsi_oversold:
            if self.last_signal != 'BUY':
                self.last_signal = 'BUY'
                return {
                    'action': 'BUY',
                    'reason': f'RSI crossed above {self.rsi_oversold}',
                    'rsi': round(current_rsi, 2),
                    'price': current_price
                }
        
        # Short signal: RSI crosses below overbought
        elif previous_rsi >= self.rsi_overbought and current_rsi < self.rsi_overbought:
            if self.last_signal != 'SELL':
                self.last_signal = 'SELL'
                return {
                    'action': 'SELL',
                    'reason': f'RSI crossed below {self.rsi_overbought}',
                    'rsi': round(current_rsi, 2),
                    'price': current_price
                }
        
        return {
            'action': 'HOLD',
            'reason': 'No signal',
            'rsi': round(current_rsi, 2)
        }
