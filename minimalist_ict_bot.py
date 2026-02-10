#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Minimalist ICT Trading Bot
==========================
✅ Bias 30m (BOS/CHoCH on swings)
✅ Entry 5m (SWEEP → DISPLACEMENT → RETRACE → CONFIRM)
✅ SL Structural: Below swing_low (LONG) / Above swing_high (SHORT) + 0.02% buffer
✅ TP Structural: TP1=internal liquidity (first swing), TP2=external liquidity (major swing)
✅ Exit Logic: SL→close, TP1→move SL to BE, TP2→close
✅ Paper Trading ONLY (LIVE_TRADING=False)
✅ Excel/CSV Tracking
✅ Telegram notifications
✅ No filters - accept all trades
"""

import os
import time
import csv
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
import ccxt
import requests

# ===================== CONFIG =====================
BIAS_TF = "30m"          # Bias timeframe
ENTRY_TF = "5m"          # Entry timeframe
LOOP_SEC = 30            # Loop delay in seconds

# Swing detection (fractal LR=2)
SWING_LR = 2

# Sweep buffer
SWEEP_BUFFER_PCT = 0.0002  # 0.02%

# Displacement detection
AVG_RANGE_LEN = 20
DISP_RANGE_MULT = 1.3
DISP_BODY_RATIO = 0.6

# Structural SL buffer
STRUCT_SL_BUFFER_PCT = 0.0002  # 0.02%

# Lookback periods
LOOKBACK_BIAS = 200
LOOKBACK_ENTRY = 300

# Trading settings
LIVE_TRADING = False  # Paper trading only
MAX_POSITIONS = 3

# Symbols to trade
SYMBOLS = [
    "BTC/USDT", "ETH/USDT", "BNB/USDT", "SOL/USDT",
    "XRP/USDT", "ADA/USDT", "DOGE/USDT", "AVAX/USDT"
]

# CSV path
TRADES_CSV_PATH = "ict_trades.csv"

# Telegram
TG_TOKEN = os.getenv("TG_BOT_TOKEN")
TG_CHAT_ID = os.getenv("TG_CHAT_ID")

# ===================== GLOBAL STATE =====================
pending = {}    # {symbol: {state, side, ...}}
positions = {}  # {symbol: {entry, sl, tp1, tp2, ...}}

# ===================== TELEGRAM =====================
def tg_send(msg: str):
    """Send Telegram notification"""
    try:
        if not TG_TOKEN or not TG_CHAT_ID:
            print(f"[TG] Skipping (no credentials): {msg[:50]}...")
            return False
        url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
        r = requests.post(url, json={"chat_id": TG_CHAT_ID, "text": msg}, timeout=10)
        return r.status_code == 200
    except Exception as e:
        print(f"[TG] Error: {e}")
        return False

# ===================== EXCHANGE =====================
exchange = None  # Global exchange instance

def init_exchange():
    """Initialize CCXT Binance exchange"""
    global exchange
    
    if exchange is not None:
        return exchange
    
    print("Initializing Binance (CCXT)...")
    
    # Check for testnet environment variable
    use_testnet = os.getenv("BINANCE_TESTNET", "false").lower() == "true"
    
    config = {
        "apiKey": os.getenv("BINANCE_API_KEY", ""),
        "secret": os.getenv("BINANCE_API_SECRET", ""),
        "enableRateLimit": True,
        "timeout": 30000,
        "options": {
            "adjustForTimeDifference": True,
            "defaultType": "spot",
        }
    }
    
    if use_testnet:
        config["urls"] = {
            "api": {
                "public": "https://testnet.binance.vision/api/v3",
                "private": "https://testnet.binance.vision/api/v3",
            }
        }
        print("Using Binance TESTNET")
    
    ex = ccxt.binance(config)
    
    # Load markets
    for attempt in range(3):
        try:
            ex.load_markets()
            print(f"Markets loaded: {len(ex.markets)} symbols")
            exchange = ex
            return ex
        except Exception as e:
            print(f"load_markets attempt {attempt+1}/3 failed: {e}")
            time.sleep(2)
    
    raise Exception("Failed to load markets")

# ===================== DATA FETCHING =====================
def fetch_df(symbol: str, timeframe: str, limit: int) -> pd.DataFrame:
    """Fetch OHLCV data and return DataFrame"""
    global exchange
    
    if exchange is None:
        raise Exception("Exchange not initialized. Call init_exchange() first.")
    
    try:
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
        if not ohlcv:
            return pd.DataFrame()
        
        df = pd.DataFrame(ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"])
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
        return df
    except Exception as e:
        print(f"[{symbol}] fetch_df error: {e}")
        return pd.DataFrame()

# ===================== SWING DETECTION =====================
def find_swings(df: pd.DataFrame, lr: int = 2):
    """
    Find swing highs and lows using fractal method
    lr = look radius (e.g., lr=2 means check 2 candles before and after)
    Returns: lists of swing highs and swing lows
    """
    swing_highs = []
    swing_lows = []
    
    if len(df) < (2 * lr + 1):
        return swing_highs, swing_lows
    
    for i in range(lr, len(df) - lr):
        # Swing high: high[i] > all highs in [i-lr, i+lr]
        is_swing_high = True
        for j in range(i - lr, i + lr + 1):
            if j != i and df.iloc[j]["high"] >= df.iloc[i]["high"]:
                is_swing_high = False
                break
        
        if is_swing_high:
            swing_highs.append({
                "idx": i,
                "price": df.iloc[i]["high"],
                "timestamp": df.iloc[i]["timestamp"]
            })
        
        # Swing low: low[i] < all lows in [i-lr, i+lr]
        is_swing_low = True
        for j in range(i - lr, i + lr + 1):
            if j != i and df.iloc[j]["low"] <= df.iloc[i]["low"]:
                is_swing_low = False
                break
        
        if is_swing_low:
            swing_lows.append({
                "idx": i,
                "price": df.iloc[i]["low"],
                "timestamp": df.iloc[i]["timestamp"]
            })
    
    return swing_highs, swing_lows

# ===================== BIAS DETECTION (30m) =====================
def detect_bias(df: pd.DataFrame) -> str:
    """
    Detect bias on 30m timeframe using BOS/CHoCH
    BOS = Break of Structure (continuation)
    CHoCH = Change of Character (reversal)
    Returns: "BULLISH", "BEARISH", or "NEUTRAL"
    """
    if len(df) < 50:
        return "NEUTRAL"
    
    swing_highs, swing_lows = find_swings(df, SWING_LR)
    
    if len(swing_highs) < 3 or len(swing_lows) < 3:
        return "NEUTRAL"
    
    # Get last few swings
    recent_highs = swing_highs[-3:]
    recent_lows = swing_lows[-3:]
    
    # Check for BOS (Break of Structure)
    # BULLISH BOS: price breaks above previous swing high
    last_close = df.iloc[-1]["close"]
    
    # Simple logic: if recent swing highs are ascending → BULLISH
    # if recent swing lows are descending → BEARISH
    
    if len(recent_highs) >= 2:
        if recent_highs[-1]["price"] > recent_highs[-2]["price"]:
            # Higher high → potential bullish
            if len(recent_lows) >= 2 and recent_lows[-1]["price"] > recent_lows[-2]["price"]:
                # Higher low too → BULLISH
                return "BULLISH"
    
    if len(recent_lows) >= 2:
        if recent_lows[-1]["price"] < recent_lows[-2]["price"]:
            # Lower low → potential bearish
            if len(recent_highs) >= 2 and recent_highs[-1]["price"] < recent_highs[-2]["price"]:
                # Lower high too → BEARISH
                return "BEARISH"
    
    return "NEUTRAL"

# ===================== ENTRY LOGIC (5m) =====================
def avg_range(df: pd.DataFrame, n: int = 20) -> float:
    """Calculate average range of last n candles"""
    if len(df) < n:
        return 0
    recent = df.tail(n)
    return (recent["high"] - recent["low"]).mean()

def detect_sweep(df: pd.DataFrame, swing_highs, swing_lows, side: str):
    """
    Detect if recent candles swept a swing level
    Returns: (swept, sweep_price, sweep_idx)
    """
    if len(df) < 10:
        return False, None, None
    
    recent_candles = df.tail(10)
    
    if side == "LONG":
        # Look for sweep of swing low
        if not swing_lows:
            return False, None, None
        
        # Get last swing low
        last_swing = swing_lows[-1]
        sweep_level = last_swing["price"] * (1 - SWEEP_BUFFER_PCT)
        
        # Check if any recent candle wicked below it
        for idx, row in recent_candles.iterrows():
            if row["low"] <= sweep_level:
                return True, last_swing["price"], last_swing["idx"]
    
    else:  # SHORT
        # Look for sweep of swing high
        if not swing_highs:
            return False, None, None
        
        last_swing = swing_highs[-1]
        sweep_level = last_swing["price"] * (1 + SWEEP_BUFFER_PCT)
        
        for idx, row in recent_candles.iterrows():
            if row["high"] >= sweep_level:
                return True, last_swing["price"], last_swing["idx"]
    
    return False, None, None

def detect_displacement(df: pd.DataFrame, side: str):
    """
    Detect displacement (strong move away from sweep)
    Returns: (displaced, disp_idx)
    """
    if len(df) < AVG_RANGE_LEN + 5:
        return False, None
    
    avg_rng = avg_range(df, AVG_RANGE_LEN)
    if avg_rng == 0:
        return False, None
    
    # Check last 5 candles for displacement
    for i in range(len(df) - 5, len(df)):
        row = df.iloc[i]
        candle_range = row["high"] - row["low"]
        body = abs(row["close"] - row["open"])
        
        # Strong candle: range > threshold and body ratio
        if candle_range > avg_rng * DISP_RANGE_MULT:
            if body / candle_range > DISP_BODY_RATIO:
                # Check direction
                if side == "LONG" and row["close"] > row["open"]:
                    return True, i
                elif side == "SHORT" and row["close"] < row["open"]:
                    return True, i
    
    return False, None

def detect_retrace(df: pd.DataFrame, disp_idx: int, side: str):
    """
    Detect retrace to zone after displacement
    Returns: (retraced, zone_low, zone_high)
    """
    if disp_idx is None or disp_idx >= len(df) - 1:
        return False, None, None
    
    disp_candle = df.iloc[disp_idx]
    
    # Define zone based on displacement candle
    if side == "LONG":
        # Bullish displacement: zone is the body/wick area
        zone_low = min(disp_candle["open"], disp_candle["close"])
        zone_high = disp_candle["high"]
    else:
        # Bearish displacement: zone is the body/wick area
        zone_low = disp_candle["low"]
        zone_high = max(disp_candle["open"], disp_candle["close"])
    
    # Check if recent candles retraced into zone
    for i in range(disp_idx + 1, len(df)):
        row = df.iloc[i]
        if row["low"] <= zone_high and row["high"] >= zone_low:
            return True, zone_low, zone_high
    
    return False, None, None

def detect_confirm(df: pd.DataFrame, side: str):
    """
    Detect confirmation candle
    Returns: (confirmed, entry_price)
    """
    if len(df) < 2:
        return False, None
    
    last = df.iloc[-1]
    
    if side == "LONG":
        # Bullish confirmation: close > open
        if last["close"] > last["open"]:
            return True, last["close"]
    else:
        # Bearish confirmation: close < open
        if last["close"] < last["open"]:
            return True, last["close"]
    
    return False, None

# ===================== SL/TP CALCULATION =====================
def calculate_sl(sweep_price: float, side: str) -> float:
    """Calculate structural SL with buffer"""
    if side == "LONG":
        # SL below sweep low
        sl = sweep_price * (1 - STRUCT_SL_BUFFER_PCT)
    else:
        # SL above sweep high
        sl = sweep_price * (1 + STRUCT_SL_BUFFER_PCT)
    return sl

def calculate_tp_levels(df: pd.DataFrame, entry: float, side: str, swing_highs, swing_lows):
    """
    Calculate TP1 (internal liquidity) and TP2 (external liquidity)
    TP1 = first swing ahead
    TP2 = major swing ahead (further out)
    """
    if side == "LONG":
        # Look for swing highs above entry
        targets = [s for s in swing_highs if s["price"] > entry]
        if len(targets) >= 2:
            targets_sorted = sorted(targets, key=lambda x: x["price"])
            tp1 = targets_sorted[0]["price"]
            tp2 = targets_sorted[1]["price"]
            return tp1, tp2
        elif len(targets) == 1:
            tp1 = targets[0]["price"]
            tp2 = tp1 * 1.015  # +1.5% as fallback
            return tp1, tp2
        else:
            # No swings ahead, use percentage
            tp1 = entry * 1.010  # +1%
            tp2 = entry * 1.020  # +2%
            return tp1, tp2
    else:  # SHORT
        # Look for swing lows below entry
        targets = [s for s in swing_lows if s["price"] < entry]
        if len(targets) >= 2:
            targets_sorted = sorted(targets, key=lambda x: x["price"], reverse=True)
            tp1 = targets_sorted[0]["price"]
            tp2 = targets_sorted[1]["price"]
            return tp1, tp2
        elif len(targets) == 1:
            tp1 = targets[0]["price"]
            tp2 = tp1 * 0.985  # -1.5% as fallback
            return tp1, tp2
        else:
            tp1 = entry * 0.990  # -1%
            tp2 = entry * 0.980  # -2%
            return tp1, tp2

# ===================== CSV TRACKING =====================
def init_csv():
    """Initialize CSV file with headers"""
    if not Path(TRADES_CSV_PATH).exists():
        with open(TRADES_CSV_PATH, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                "entry_ts", "symbol", "side", "entry", "sl", "tp1", "tp2",
                "exit_price", "pnl_pct", "duration_min", "exit_reason"
            ])
        print(f"Created CSV: {TRADES_CSV_PATH}")

def write_trade_to_csv(trade_data: dict):
    """Write trade to CSV"""
    try:
        with open(TRADES_CSV_PATH, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                trade_data.get("entry_ts", ""),
                trade_data.get("symbol", ""),
                trade_data.get("side", ""),
                trade_data.get("entry", ""),
                trade_data.get("sl", ""),
                trade_data.get("tp1", ""),
                trade_data.get("tp2", ""),
                trade_data.get("exit_price", ""),
                trade_data.get("pnl_pct", ""),
                trade_data.get("duration_min", ""),
                trade_data.get("exit_reason", "")
            ])
    except Exception as e:
        print(f"Error writing to CSV: {e}")

# ===================== POSITION MANAGEMENT =====================
def open_position(symbol: str, side: str, entry: float, sl: float, tp1: float, tp2: float):
    """Open a new position"""
    if len(positions) >= MAX_POSITIONS:
        print(f"[{symbol}] Max positions reached, skipping")
        return
    
    entry_ts = datetime.now().isoformat()
    
    positions[symbol] = {
        "side": side,
        "entry": entry,
        "sl": sl,
        "tp1": tp1,
        "tp2": tp2,
        "entry_ts": entry_ts,
        "entry_dt": datetime.now()
    }
    
    # Telegram notification
    msg = (
        f"🟢 OPEN {side} {symbol}\n"
        f"Entry: {entry:.6f}\n"
        f"SL: {sl:.6f} ({((sl-entry)/entry*100):.2f}%)\n"
        f"TP1: {tp1:.6f} ({((tp1-entry)/entry*100):.2f}%)\n"
        f"TP2: {tp2:.6f} ({((tp2-entry)/entry*100):.2f}%)"
    )
    tg_send(msg)
    print(f"[{symbol}] {msg}")

def close_position(symbol: str, exit_price: float, reason: str):
    """Close a position"""
    if symbol not in positions:
        return
    
    pos = positions[symbol]
    entry = pos["entry"]
    side = pos["side"]
    
    # Calculate PnL
    if side == "LONG":
        pnl_pct = ((exit_price - entry) / entry) * 100
    else:
        pnl_pct = ((entry - exit_price) / entry) * 100
    
    # Duration
    duration = datetime.now() - pos["entry_dt"]
    duration_min = duration.total_seconds() / 60
    
    # Write to CSV
    write_trade_to_csv({
        "entry_ts": pos["entry_ts"],
        "symbol": symbol,
        "side": side,
        "entry": entry,
        "sl": pos["sl"],
        "tp1": pos["tp1"],
        "tp2": pos["tp2"],
        "exit_price": exit_price,
        "pnl_pct": f"{pnl_pct:.2f}",
        "duration_min": f"{duration_min:.1f}",
        "exit_reason": reason
    })
    
    # Telegram notification
    msg = (
        f"🔴 CLOSE {side} {symbol} ({reason})\n"
        f"Exit: {exit_price:.6f}\n"
        f"PnL: {pnl_pct:+.2f}%\n"
        f"Duration: {duration_min:.1f} min"
    )
    tg_send(msg)
    print(f"[{symbol}] {msg}")
    
    del positions[symbol]

def manage_position(symbol: str, df: pd.DataFrame):
    """Manage open position - check SL/TP levels"""
    if symbol not in positions:
        return
    
    pos = positions[symbol]
    last = df.iloc[-1]
    high = last["high"]
    low = last["low"]
    
    side = pos["side"]
    sl = pos["sl"]
    tp1 = pos["tp1"]
    tp2 = pos["tp2"]
    
    if side == "LONG":
        # Check SL
        if low <= sl:
            close_position(symbol, sl, "SL_HIT")
            return
        
        # Check TP2 first (full exit)
        if high >= tp2:
            close_position(symbol, tp2, "TP2_CLOSE")
            return
        
        # Check TP1 (move SL to BE)
        if high >= tp1 and pos.get("be_moved") != True:
            pos["sl"] = pos["entry"]  # Move SL to break-even
            pos["be_moved"] = True
            msg = f"🟡 TP1_BE {symbol}\nTP1 hit, SL moved to BE: {pos['entry']:.6f}"
            tg_send(msg)
            print(f"[{symbol}] {msg}")
    
    else:  # SHORT
        # Check SL
        if high >= sl:
            close_position(symbol, sl, "SL_HIT")
            return
        
        # Check TP2 first (full exit)
        if low <= tp2:
            close_position(symbol, tp2, "TP2_CLOSE")
            return
        
        # Check TP1 (move SL to BE)
        if low <= tp1 and pos.get("be_moved") != True:
            pos["sl"] = pos["entry"]
            pos["be_moved"] = True
            msg = f"🟡 TP1_BE {symbol}\nTP1 hit, SL moved to BE: {pos['entry']:.6f}"
            tg_send(msg)
            print(f"[{symbol}] {msg}")

# ===================== STATE MACHINE =====================
def process_symbol(symbol: str):
    """Process a symbol through the state machine"""
    try:
        # Fetch data
        df_bias = fetch_df(symbol, BIAS_TF, LOOKBACK_BIAS)
        df_entry = fetch_df(symbol, ENTRY_TF, LOOKBACK_ENTRY)
        
        if df_bias.empty or df_entry.empty:
            return
        
        # Check if we have an open position
        if symbol in positions:
            manage_position(symbol, df_entry)
            return
        
        # Get or initialize pending state
        if symbol not in pending:
            pending[symbol] = {"state": "WAIT_SWEEP", "side": None}
        
        state = pending[symbol]["state"]
        
        # Get bias
        bias = detect_bias(df_bias)
        if bias == "NEUTRAL":
            return
        
        # Determine trade direction based on bias
        if bias == "BULLISH":
            side = "LONG"
        else:
            side = "SHORT"
        
        # Update side if changed
        if pending[symbol]["side"] != side:
            pending[symbol] = {"state": "WAIT_SWEEP", "side": side}
            return
        
        # Find swings
        swing_highs, swing_lows = find_swings(df_entry, SWING_LR)
        
        # State machine
        if state == "WAIT_SWEEP":
            swept, sweep_price, sweep_idx = detect_sweep(df_entry, swing_highs, swing_lows, side)
            if swept:
                pending[symbol]["state"] = "WAIT_DISPLACEMENT"
                pending[symbol]["sweep_price"] = sweep_price
                pending[symbol]["sweep_idx"] = sweep_idx
        
        elif state == "WAIT_DISPLACEMENT":
            displaced, disp_idx = detect_displacement(df_entry, side)
            if displaced:
                pending[symbol]["state"] = "WAIT_RETRACE"
                pending[symbol]["disp_idx"] = disp_idx
        
        elif state == "WAIT_RETRACE":
            disp_idx = pending[symbol].get("disp_idx")
            retraced, zone_low, zone_high = detect_retrace(df_entry, disp_idx, side)
            if retraced:
                pending[symbol]["state"] = "WAIT_CONFIRM"
                pending[symbol]["zone_low"] = zone_low
                pending[symbol]["zone_high"] = zone_high
        
        elif state == "WAIT_CONFIRM":
            confirmed, entry_price = detect_confirm(df_entry, side)
            if confirmed:
                # Calculate SL and TP
                sweep_price = pending[symbol].get("sweep_price")
                sl = calculate_sl(sweep_price, side)
                tp1, tp2 = calculate_tp_levels(df_entry, entry_price, side, swing_highs, swing_lows)
                
                # Open position
                open_position(symbol, side, entry_price, sl, tp1, tp2)
                
                # Reset pending state
                del pending[symbol]
    
    except Exception as e:
        print(f"[{symbol}] Error: {e}")

# ===================== MAIN LOOP =====================
def main():
    """Main trading loop"""
    # Initialize exchange first
    init_exchange()
    
    print("\n" + "="*60)
    print("Minimalist ICT Bot Started")
    print("="*60)
    print(f"Bias TF: {BIAS_TF}")
    print(f"Entry TF: {ENTRY_TF}")
    print(f"Paper Trading: {not LIVE_TRADING}")
    print(f"Max Positions: {MAX_POSITIONS}")
    print(f"Symbols: {len(SYMBOLS)}")
    print("="*60 + "\n")
    
    # Initialize CSV
    init_csv()
    
    # Send startup notification
    tg_send("🚀 Minimalist ICT Bot Started\n" + 
            f"Paper Trading: {not LIVE_TRADING}\n" +
            f"Tracking {len(SYMBOLS)} symbols")
    
    loop_count = 0
    
    while True:
        try:
            loop_count += 1
            
            # Process each symbol
            for symbol in SYMBOLS:
                process_symbol(symbol)
            
            # Heartbeat
            if loop_count % 10 == 0:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] "
                      f"Heartbeat | Positions: {len(positions)} | "
                      f"Pending: {len(pending)}")
            
            time.sleep(LOOP_SEC)
        
        except KeyboardInterrupt:
            print("\nShutting down...")
            tg_send("🛑 Minimalist ICT Bot Stopped")
            break
        
        except Exception as e:
            print(f"Error in main loop: {e}")
            time.sleep(LOOP_SEC)

if __name__ == "__main__":
    main()
