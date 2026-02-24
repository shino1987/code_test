"""
Simple demo script to show the scalping bot in action (paper trading mode)
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scalping_bot.main import main

if __name__ == "__main__":
    print("╔══════════════════════════════════════════════════════════╗")
    print("║         SCALPING BOT - DEMO MODE (Paper Trading)        ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print()
    print("This demo runs the bot in paper trading mode using")
    print("simulated market data. No real trades will be executed.")
    print()
    print("Press Ctrl+C to stop the bot at any time.")
    print()
    input("Press ENTER to start the demo...")
    print()
    
    main()
