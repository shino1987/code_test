#!/usr/bin/env python3
"""
Demo script for Minimalist ICT Bot
Shows a dry-run without actual exchange connection
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Import functions to demonstrate
from minimalist_ict_bot import (
    find_swings,
    detect_bias,
    detect_sweep,
    detect_displacement,
    calculate_sl,
    calculate_tp_levels
)

def create_trending_data(size=200, trend='bullish'):
    """Create sample trending price data"""
    np.random.seed(42)
    
    base = 50000
    if trend == 'bullish':
        trend_component = np.linspace(0, 2000, size)
    else:
        trend_component = np.linspace(0, -2000, size)
    
    noise = np.cumsum(np.random.randn(size) * 30)
    prices = base + trend_component + noise
    
    df = pd.DataFrame({
        'timestamp': [datetime.now() - timedelta(minutes=5*(size-i)) for i in range(size)],
        'open': prices,
        'high': prices + np.random.rand(size) * 100,
        'low': prices - np.random.rand(size) * 100,
        'close': prices + np.random.randn(size) * 50,
        'volume': np.random.rand(size) * 1000
    })
    
    # Ensure high/low are correct
    df['high'] = df[['open', 'high', 'close']].max(axis=1)
    df['low'] = df[['open', 'low', 'close']].min(axis=1)
    
    return df

def demo_swing_detection():
    """Demo: Find swing points"""
    print("\n" + "="*70)
    print("DEMO 1: SWING DETECTION")
    print("="*70)
    
    df = create_trending_data(100, 'bullish')
    swing_highs, swing_lows = find_swings(df, lr=2)
    
    print(f"✓ Analyzed {len(df)} candles")
    print(f"✓ Found {len(swing_highs)} swing highs")
    print(f"✓ Found {len(swing_lows)} swing lows")
    
    if swing_highs:
        last_sh = swing_highs[-1]
        print(f"\nLast Swing High:")
        print(f"  Price: ${last_sh['price']:.2f}")
        print(f"  Index: {last_sh['idx']}")
        print(f"  Time: {last_sh['timestamp']}")
    
    if swing_lows:
        last_sl = swing_lows[-1]
        print(f"\nLast Swing Low:")
        print(f"  Price: ${last_sl['price']:.2f}")
        print(f"  Index: {last_sl['idx']}")
        print(f"  Time: {last_sl['timestamp']}")

def demo_bias_detection():
    """Demo: Detect market bias"""
    print("\n" + "="*70)
    print("DEMO 2: BIAS DETECTION (30m)")
    print("="*70)
    
    # Test with bullish data
    df_bull = create_trending_data(100, 'bullish')
    bias_bull = detect_bias(df_bull)
    print(f"✓ Bullish data → Bias: {bias_bull}")
    
    # Test with bearish data
    df_bear = create_trending_data(100, 'bearish')
    bias_bear = detect_bias(df_bear)
    print(f"✓ Bearish data → Bias: {bias_bear}")

def demo_entry_conditions():
    """Demo: Entry condition detection"""
    print("\n" + "="*70)
    print("DEMO 3: ENTRY CONDITIONS (5m)")
    print("="*70)
    
    df = create_trending_data(100, 'bullish')
    swing_highs, swing_lows = find_swings(df, lr=2)
    
    # Check sweep
    swept, price, idx = detect_sweep(df, swing_highs, swing_lows, "LONG")
    print(f"✓ LONG Sweep detected: {swept}")
    if swept:
        print(f"  Sweep price: ${price:.2f} at index {idx}")
    
    # Check displacement
    displaced, disp_idx = detect_displacement(df, "LONG")
    print(f"✓ LONG Displacement detected: {displaced}")
    if displaced:
        print(f"  Displacement at index: {disp_idx}")

def demo_risk_calculation():
    """Demo: SL and TP calculation"""
    print("\n" + "="*70)
    print("DEMO 4: RISK MANAGEMENT")
    print("="*70)
    
    entry = 50000.0
    sweep_price = 49900.0
    
    # Calculate SL
    sl_long = calculate_sl(sweep_price, "LONG")
    sl_short = calculate_sl(sweep_price, "SHORT")
    
    print(f"Entry Price: ${entry:.2f}")
    print(f"Sweep Price: ${sweep_price:.2f}")
    print(f"\nLONG Trade:")
    print(f"  SL: ${sl_long:.2f} ({((sl_long-entry)/entry*100):.2f}%)")
    print(f"\nSHORT Trade:")
    print(f"  SL: ${sl_short:.2f} ({((sl_short-entry)/entry*100):.2f}%)")
    
    # Calculate TP
    df = create_trending_data(100, 'bullish')
    swing_highs, swing_lows = find_swings(df, lr=2)
    
    tp1_long, tp2_long = calculate_tp_levels(df, entry, "LONG", swing_highs, swing_lows)
    print(f"\nLONG Targets:")
    print(f"  TP1: ${tp1_long:.2f} ({((tp1_long-entry)/entry*100):.2f}%)")
    print(f"  TP2: ${tp2_long:.2f} ({((tp2_long-entry)/entry*100):.2f}%)")

def demo_trade_simulation():
    """Demo: Simulate a full trade"""
    print("\n" + "="*70)
    print("DEMO 5: TRADE SIMULATION")
    print("="*70)
    
    print("\nScenario: LONG position on BTC/USDT")
    print("-" * 70)
    
    # Entry conditions
    entry = 50000.0
    sweep_price = 49900.0
    
    # Calculate levels
    sl = calculate_sl(sweep_price, "LONG")
    
    df = create_trending_data(100, 'bullish')
    swing_highs, swing_lows = find_swings(df, lr=2)
    tp1, tp2 = calculate_tp_levels(df, entry, "LONG", swing_highs, swing_lows)
    
    # Display trade setup
    print(f"\n📊 TRADE SETUP:")
    print(f"  Symbol: BTC/USDT")
    print(f"  Side: LONG")
    print(f"  Entry: ${entry:.2f}")
    print(f"  SL: ${sl:.2f} ({((sl-entry)/entry*100):.2f}%)")
    print(f"  TP1: ${tp1:.2f} ({((tp1-entry)/entry*100):.2f}%)")
    print(f"  TP2: ${tp2:.2f} ({((tp2-entry)/entry*100):.2f}%)")
    
    # Simulate TP1 hit
    print(f"\n✅ TP1 HIT at ${tp1:.2f}")
    print(f"  → Move SL to Break-Even: ${entry:.2f}")
    print(f"  → Risk eliminated, position now risk-free")
    
    # Simulate TP2 hit
    print(f"\n✅ TP2 HIT at ${tp2:.2f}")
    pnl = ((tp2 - entry) / entry) * 100
    print(f"  → Close position")
    print(f"  → PnL: +{pnl:.2f}%")
    print(f"  → Trade duration: ~45 min")

def main():
    """Run all demos"""
    print("\n" + "="*70)
    print("MINIMALIST ICT BOT - DEMONSTRATION")
    print("="*70)
    print("\nThis demo shows the bot's functionality without live exchange connection")
    
    try:
        demo_swing_detection()
        demo_bias_detection()
        demo_entry_conditions()
        demo_risk_calculation()
        demo_trade_simulation()
        
        print("\n" + "="*70)
        print("DEMO COMPLETE")
        print("="*70)
        print("\n✅ All functions demonstrated successfully")
        print("\nTo run the actual bot:")
        print("  1. Set up environment variables (see .env.example)")
        print("  2. Run: python minimalist_ict_bot.py")
        print("\nFor testing: python test_ict_bot.py")
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error in demo: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
