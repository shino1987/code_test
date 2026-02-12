#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for ICT Live Trading Bot

This script validates the bot functionality in mock mode without placing real orders.
"""

import sys
import os

# Ensure we can import the main module
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from GPT_NUOVO_TEST_ICT_LIVE import (
    TradingConfig,
    APIConfig,
    TradingLogger,
    BinanceMarginClient,
    test_mock_order_flow
)

def test_configuration():
    """Test configuration loading"""
    print("=" * 60)
    print("TEST 1: Configuration Loading")
    print("=" * 60)
    
    try:
        config = TradingConfig()
        print(f"✓ Trading config loaded successfully")
        print(f"  - Symbols: {len(config.symbols)}")
        print(f"  - Max positions: {config.max_open_positions}")
        print(f"  - Trade size: ${config.trade_usdc_target}")
        
        api_config = APIConfig.from_env()
        print(f"✓ API config loaded successfully")
        print(f"  - Has API key: {bool(api_config.api_key)}")
        print(f"  - Has API secret: {bool(api_config.api_secret)}")
        print(f"  - Has Telegram: {bool(api_config.telegram_token)}")
        
        return True
    except Exception as e:
        print(f"✗ Configuration test failed: {e}")
        return False

def test_logging_system():
    """Test logging system"""
    print("\n" + "=" * 60)
    print("TEST 2: Logging System")
    print("=" * 60)
    
    try:
        config = TradingConfig()
        logger = TradingLogger(config)
        
        print("✓ Logger initialized successfully")
        
        # Test log_event
        logger.log_event('INFO', 'Test message', test_param='test_value')
        print("✓ log_event() works")
        
        # Test CSV initialization
        from pathlib import Path
        csv_path = Path(config.trades_csv_path)
        if csv_path.exists():
            print(f"✓ CSV file exists: {config.trades_csv_path}")
        
        # Test Excel initialization
        excel_path = Path(config.trades_excel_path)
        if excel_path.exists():
            print(f"✓ Excel file exists: {config.trades_excel_path}")
        
        return True
    except Exception as e:
        print(f"✗ Logging test failed: {e}")
        return False

def test_mock_orders():
    """Test mock order functionality"""
    print("\n" + "=" * 60)
    print("TEST 3: Mock Order Flow")
    print("=" * 60)
    
    try:
        config = TradingConfig()
        config.mock_mode = True
        api_config = APIConfig.from_env()
        logger = TradingLogger(config)
        
        result = test_mock_order_flow(config, api_config, logger)
        
        if result:
            print("✓ Mock order flow test PASSED")
            return True
        else:
            print("✗ Mock order flow test FAILED")
            return False
    except Exception as e:
        print(f"✗ Mock order test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_import_original_functions():
    """Test that we can import and use original functions"""
    print("\n" + "=" * 60)
    print("TEST 4: Import Original Functions")
    print("=" * 60)
    
    try:
        from GPT_NUOVO_TEST_ICT_LIVE import (
            find_swings,
            candle_stats,
            detect_trend,
            quantize_quantity,
            get_binance_filters,
            format_quantity
        )
        
        print("✓ All required functions imported successfully")
        return True
    except Exception as e:
        print(f"✗ Import test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("\n" + "=" * 80)
    print(" ICT LIVE TRADING BOT - TEST SUITE")
    print("=" * 80)
    
    results = []
    
    # Run tests
    results.append(("Configuration", test_configuration()))
    results.append(("Logging System", test_logging_system()))
    results.append(("Import Functions", test_import_original_functions()))
    results.append(("Mock Orders", test_mock_orders()))
    
    # Summary
    print("\n" + "=" * 80)
    print(" TEST SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print("-" * 80)
    print(f"Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
