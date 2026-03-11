#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
USAGE EXAMPLE: Minimalist ICT Bot Configuration and Customization

This file demonstrates how to configure and run the ICT bot with different settings.
"""

# ============================================================================
# QUICK START GUIDE
# ============================================================================
"""
1. Install dependencies:
   pip install -r requirements.txt

2. Run the bot:
   python ict_bot_minimal.py

3. Check trades:
   cat ict_trades.csv
   # Or open in Excel/Google Sheets

4. Stop the bot:
   Press Ctrl+C
"""

# ============================================================================
# CONFIGURATION EXAMPLES
# ============================================================================

# Example 1: Conservative Settings (Lower Risk)
CONSERVATIVE_CONFIG = {
    'SWING_LR': 3,                    # More swing points (more conservative)
    'SWEEP_BUFFER_PCT': 0.0003,       # Larger sweep buffer (0.03%)
    'DISP_RANGE_MULT': 2.0,           # Require stronger displacement
    'DISP_BODY_RATIO': 0.7,           # Require stronger body (70%)
    'STRUCT_SL_BUFFER_PCT': 0.0003,   # Larger SL buffer
    'MIN_SL_PCT': 0.005,              # Minimum 0.5% SL
}

# Example 2: Aggressive Settings (Higher Risk)
AGGRESSIVE_CONFIG = {
    'SWING_LR': 2,                    # Standard swing points
    'SWEEP_BUFFER_PCT': 0.0001,       # Smaller sweep buffer (0.01%)
    'DISP_RANGE_MULT': 1.2,           # Accept weaker displacement
    'DISP_BODY_RATIO': 0.5,           # Accept weaker body (50%)
    'STRUCT_SL_BUFFER_PCT': 0.0001,   # Smaller SL buffer
    'MIN_SL_PCT': 0.002,              # Minimum 0.2% SL
}

# Example 3: Multiple Symbols (Diversified)
DIVERSIFIED_SYMBOLS = [
    "BTC/USDT",
    "ETH/USDT",
    "BNB/USDT",
    "SOL/USDT",
    "XRP/USDT",
    "ADA/USDT",
]

# Example 4: Major Pairs Only (Focused)
MAJOR_SYMBOLS = [
    "BTC/USDT",
    "ETH/USDT",
]

# Example 5: Timeframe Variations
TIMEFRAME_CONFIGS = {
    'standard': {
        'BIAS_TF': '30m',
        'ENTRY_TF': '5m',
        'LOOKBACK_BIAS': 200,
        'LOOKBACK_ENTRY': 300,
    },
    'faster': {
        'BIAS_TF': '15m',
        'ENTRY_TF': '3m',
        'LOOKBACK_BIAS': 300,
        'LOOKBACK_ENTRY': 400,
    },
    'slower': {
        'BIAS_TF': '1h',
        'ENTRY_TF': '15m',
        'LOOKBACK_BIAS': 150,
        'LOOKBACK_ENTRY': 200,
    },
}

# ============================================================================
# HOW TO APPLY CUSTOM CONFIGURATION
# ============================================================================
"""
To apply a custom configuration:

1. Edit ict_bot_minimal.py
2. Find the CONFIGURATION section (near the top)
3. Replace the values with your chosen settings
4. Save and run the bot

Example - Applying Conservative Settings:

# In ict_bot_minimal.py, change:
SWING_LR = 2             # Default
# To:
SWING_LR = 3             # Conservative

MIN_SL_PCT = 0.003       # Default
# To:
MIN_SL_PCT = 0.005       # Conservative
"""

# ============================================================================
# MONITORING YOUR BOT
# ============================================================================
"""
Console Output:
- Real-time logs with timestamps
- State transitions (SWEEP → DISPLACEMENT → RETRACE → CONFIRM)
- Position entries and exits
- PnL calculations

CSV Log (ict_trades.csv):
- Complete trade history
- Entry/exit prices
- SL/TP levels
- PnL (gross and net)
- Trade duration
- Exit reason

Analysis Tips:
1. Import CSV into Excel/Google Sheets
2. Calculate win rate: Count(exit_reason != 'SL_HIT') / Total Trades
3. Calculate average PnL: Average(pnl_net_pct)
4. Identify best performing symbols
5. Track trade duration patterns
"""

# ============================================================================
# EXAMPLE: ANALYZING TRADES IN PYTHON
# ============================================================================
"""
import pandas as pd

# Load trades
df = pd.read_csv('ict_trades.csv')

# Calculate statistics
print(f"Total trades: {len(df)}")
print(f"Win rate: {(df['exit_reason'] != 'SL_HIT').sum() / len(df) * 100:.1f}%")
print(f"Average PnL: {df['pnl_net_pct'].mean():.2f}%")
print(f"Best trade: {df['pnl_net_pct'].max():.2f}%")
print(f"Worst trade: {df['pnl_net_pct'].min():.2f}%")

# By symbol
print("\nPer Symbol:")
print(df.groupby('symbol')['pnl_net_pct'].agg(['count', 'mean', 'sum']))

# By side
print("\nPer Side:")
print(df.groupby('side')['pnl_net_pct'].agg(['count', 'mean', 'sum']))
"""

# ============================================================================
# SAFETY NOTES
# ============================================================================
"""
IMPORTANT: This is a PAPER TRADING bot

✅ Safe:
- No real money at risk
- No API keys needed for basic operation
- All trades are simulated
- Good for learning and testing strategies

⚠️ Before Using with Real Money:
- Thoroughly test with paper trading for weeks/months
- Understand all parameters and their effects
- Implement proper risk management
- Never risk more than you can afford to lose
- Consider market conditions and volatility
- Monitor the bot continuously
- Have stop-loss procedures in place

📚 Learn More:
- Study ICT concepts (Inner Circle Trading)
- Understand market structure
- Learn about liquidity sweeps
- Practice identifying setups manually first
"""

# ============================================================================
# CUSTOMIZATION IDEAS
# ============================================================================
"""
1. Add More Symbols:
   - Edit SYMBOLS list in ict_bot_minimal.py
   - Test with lower-volume pairs carefully

2. Adjust Position Size:
   - Edit PAPER_POSITION_SIZE_USDC
   - Scale based on your paper trading capital

3. Change Timeframes:
   - Higher timeframes = fewer trades, potentially more reliable
   - Lower timeframes = more trades, faster feedback

4. Modify Loop Interval:
   - LOOP_SEC controls how often the bot checks for setups
   - Lower = faster reaction, higher API usage
   - Higher = slower reaction, lower API usage

5. Add Filters (Advanced):
   - Volume filters
   - Time-of-day filters
   - Volatility filters
   - Multiple timeframe confirmation
   
6. Enhance Logging:
   - Add more detailed console output
   - Create separate log files
   - Add email/SMS notifications (without Telegram)
   
7. Optimize Parameters:
   - Run backtests with different settings
   - Use the test_ict_bot.py as a starting point
   - Track which settings perform best
"""

if __name__ == "__main__":
    print("This is a usage example file.")
    print("Run 'python ict_bot_minimal.py' to start the bot.")
    print("\nSee the comments in this file for configuration examples.")
