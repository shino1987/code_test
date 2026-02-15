#!/usr/bin/env python3
"""
Test script for Minimalist ICT Bot
Tests key functions with sample data
"""

import pandas as pd
import numpy as np
from minimalist_ict_bot import (
    find_swings,
    detect_bias,
    detect_sweep,
    detect_displacement,
    calculate_sl,
    calculate_tp_levels
)

def create_sample_df(size=100):
    """Create sample OHLCV dataframe"""
    np.random.seed(42)
    
    # Generate a trending price series
    base = 50000
    trend = np.cumsum(np.random.randn(size) * 50)
    prices = base + trend
    
    df = pd.DataFrame({
        'timestamp': pd.date_range('2024-01-01', periods=size, freq='5min'),
        'open': prices,
        'high': prices + np.random.rand(size) * 100,
        'low': prices - np.random.rand(size) * 100,
        'close': prices + np.random.randn(size) * 50,
        'volume': np.random.rand(size) * 1000
    })
    
    # Ensure high is highest and low is lowest
    df['high'] = df[['open', 'high', 'close']].max(axis=1)
    df['low'] = df[['open', 'low', 'close']].min(axis=1)
    
    return df

def test_swing_detection():
    """Test swing detection"""
    print("\n" + "="*60)
    print("TEST: Swing Detection")
    print("="*60)
    
    df = create_sample_df(100)
    swing_highs, swing_lows = find_swings(df, lr=2)
    
    print(f"✓ Found {len(swing_highs)} swing highs")
    print(f"✓ Found {len(swing_lows)} swing lows")
    
    if swing_highs:
        print(f"  Last swing high: {swing_highs[-1]['price']:.2f} at idx {swing_highs[-1]['idx']}")
    if swing_lows:
        print(f"  Last swing low: {swing_lows[-1]['price']:.2f} at idx {swing_lows[-1]['idx']}")
    
    assert len(swing_highs) > 0, "Should find at least one swing high"
    assert len(swing_lows) > 0, "Should find at least one swing low"
    print("✓ Test passed")

def test_bias_detection():
    """Test bias detection"""
    print("\n" + "="*60)
    print("TEST: Bias Detection")
    print("="*60)
    
    df = create_sample_df(100)
    bias = detect_bias(df)
    
    print(f"✓ Detected bias: {bias}")
    assert bias in ["BULLISH", "BEARISH", "NEUTRAL"], "Bias must be one of three states"
    print("✓ Test passed")

def test_sweep_detection():
    """Test sweep detection"""
    print("\n" + "="*60)
    print("TEST: Sweep Detection")
    print("="*60)
    
    df = create_sample_df(100)
    swing_highs, swing_lows = find_swings(df, lr=2)
    
    # Test LONG sweep
    swept, price, idx = detect_sweep(df, swing_highs, swing_lows, "LONG")
    print(f"✓ LONG sweep detected: {swept}")
    if swept:
        print(f"  Sweep price: {price:.2f}, idx: {idx}")
    
    # Test SHORT sweep
    swept, price, idx = detect_sweep(df, swing_highs, swing_lows, "SHORT")
    print(f"✓ SHORT sweep detected: {swept}")
    if swept:
        print(f"  Sweep price: {price:.2f}, idx: {idx}")
    
    print("✓ Test passed")

def test_displacement_detection():
    """Test displacement detection"""
    print("\n" + "="*60)
    print("TEST: Displacement Detection")
    print("="*60)
    
    # Create df with a clear displacement candle
    df = create_sample_df(50)
    
    # Add a strong bullish candle
    df.loc[45, 'open'] = 50000
    df.loc[45, 'close'] = 50600
    df.loc[45, 'high'] = 50650
    df.loc[45, 'low'] = 49990
    
    displaced, idx = detect_displacement(df, "LONG")
    print(f"✓ LONG displacement detected: {displaced}")
    if displaced:
        print(f"  Displacement at idx: {idx}")
    
    # Add a strong bearish candle
    df.loc[46, 'open'] = 50600
    df.loc[46, 'close'] = 50000
    df.loc[46, 'high'] = 50610
    df.loc[46, 'low'] = 49990
    
    displaced, idx = detect_displacement(df, "SHORT")
    print(f"✓ SHORT displacement detected: {displaced}")
    if displaced:
        print(f"  Displacement at idx: {idx}")
    
    print("✓ Test passed")

def test_sl_calculation():
    """Test SL calculation"""
    print("\n" + "="*60)
    print("TEST: SL Calculation")
    print("="*60)
    
    sweep_price = 50000
    
    # LONG SL
    sl_long = calculate_sl(sweep_price, "LONG")
    print(f"✓ LONG SL: {sl_long:.2f} (below sweep {sweep_price})")
    assert sl_long < sweep_price, "LONG SL must be below sweep"
    
    # SHORT SL
    sl_short = calculate_sl(sweep_price, "SHORT")
    print(f"✓ SHORT SL: {sl_short:.2f} (above sweep {sweep_price})")
    assert sl_short > sweep_price, "SHORT SL must be above sweep"
    
    print("✓ Test passed")

def test_tp_calculation():
    """Test TP calculation"""
    print("\n" + "="*60)
    print("TEST: TP Calculation")
    print("="*60)
    
    df = create_sample_df(100)
    swing_highs, swing_lows = find_swings(df, lr=2)
    
    entry = 50000
    
    # LONG TPs
    tp1, tp2 = calculate_tp_levels(df, entry, "LONG", swing_highs, swing_lows)
    print(f"✓ LONG TP1: {tp1:.2f}, TP2: {tp2:.2f}")
    assert tp1 > entry, "LONG TP1 must be above entry"
    assert tp2 > tp1, "LONG TP2 must be above TP1"
    
    # SHORT TPs
    tp1, tp2 = calculate_tp_levels(df, entry, "SHORT", swing_highs, swing_lows)
    print(f"✓ SHORT TP1: {tp1:.2f}, TP2: {tp2:.2f}")
    assert tp1 < entry, "SHORT TP1 must be below entry"
    assert tp2 < tp1, "SHORT TP2 must be below TP1"
    
    print("✓ Test passed")

def test_csv_structure():
    """Test CSV functionality"""
    print("\n" + "="*60)
    print("TEST: CSV Structure")
    print("="*60)
    
    from minimalist_ict_bot import init_csv, write_trade_to_csv
    import os
    
    test_csv = "test_trades.csv"
    
    # Override path
    import minimalist_ict_bot
    minimalist_ict_bot.TRADES_CSV_PATH = test_csv
    
    # Initialize CSV
    init_csv()
    assert os.path.exists(test_csv), "CSV file should be created"
    print("✓ CSV file created")
    
    # Write test trade
    trade = {
        "entry_ts": "2024-01-01T12:00:00",
        "symbol": "BTC/USDT",
        "side": "LONG",
        "entry": 50000,
        "sl": 49900,
        "tp1": 50500,
        "tp2": 51000,
        "exit_price": 50500,
        "pnl_pct": "1.00",
        "duration_min": "45.5",
        "exit_reason": "TP1_BE"
    }
    write_trade_to_csv(trade)
    print("✓ Trade written to CSV")
    
    # Verify
    df = pd.read_csv(test_csv)
    assert len(df) == 1, "Should have 1 trade"
    assert df.iloc[0]["symbol"] == "BTC/USDT", "Symbol should match"
    print("✓ CSV data verified")
    
    # Cleanup
    os.remove(test_csv)
    print("✓ Test cleanup complete")
    print("✓ Test passed")

def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("MINIMALIST ICT BOT - TEST SUITE")
    print("="*60)
    
    tests = [
        test_swing_detection,
        test_bias_detection,
        test_sweep_detection,
        test_displacement_detection,
        test_sl_calculation,
        test_tp_calculation,
        test_csv_structure
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"\n✗ Test failed: {e}")
            failed += 1
    
    print("\n" + "="*60)
    print(f"TEST RESULTS: {passed} passed, {failed} failed")
    print("="*60 + "\n")
    
    return failed == 0

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
