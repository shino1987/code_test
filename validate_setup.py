#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Validation script for ICT Smart Money Bot
Checks environment variables and basic configuration
"""

import os
import sys

def check_env_var(name, description):
    """Check if environment variable is set"""
    value = os.getenv(name)
    if value:
        print(f"✓ {name}: Set (length: {len(value)} chars)")
        return True
    else:
        print(f"✗ {name}: NOT SET - {description}")
        return False

def main():
    print("=" * 70)
    print("ICT Smart Money Bot - Setup Validation")
    print("=" * 70)
    print()
    
    all_ok = True
    
    print("Checking required environment variables:")
    print("-" * 70)
    
    # Required variables
    required = {
        "BINANCE_API_KEY": "Required for Binance API access",
        "BINANCE_API_SECRET": "Required for Binance API access",
    }
    
    for var_name, description in required.items():
        if not check_env_var(var_name, description):
            all_ok = False
    
    print()
    print("Checking optional environment variables:")
    print("-" * 70)
    
    # Optional variables
    optional = {
        "TG_BOT_TOKEN": "Optional - for Telegram notifications",
        "TG_CHAT_ID": "Optional - for Telegram notifications",
    }
    
    for var_name, description in optional.items():
        check_env_var(var_name, description)
    
    print()
    print("=" * 70)
    
    if all_ok:
        print("✓ All required environment variables are set!")
        print("You can now run the trading bot.")
        return 0
    else:
        print("✗ Some required environment variables are missing!")
        print("Please set them before running the bot.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
