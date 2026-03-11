#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Minimalist ICT Trading Bot
- Supports LIVE TRADING on Cross Margin or Paper Trading
- NO Telegram
- Zero Filters
- CSV Tracking
- Console Logging

WARNING: When LIVE_TRADING=True, this bot will trade with REAL MONEY
on Binance Cross Margin. Use at your own risk.
"""

import os
import time
import csv
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import pandas as pd
import ccxt

# ===================== CONFIGURATION =====================
BIAS_TF = "30m"          # Bias timeframe
ENTRY_TF = "5m"          # Entry timeframe
LOOP_SEC = 30            # Main loop interval

LOOKBACK_BIAS = 200      # Candles for bias analysis
LOOKBACK_ENTRY = 300     # Candles for entry analysis

# Swing detection (fractal)
SWING_LR = 2             # Left/Right bars for swing detection

# Sweep detection
SWEEP_BUFFER_PCT = 0.0002  # 0.02% buffer for sweep

# Displacement
AVG_RANGE_LEN = 20       # Period for average range
DISP_RANGE_MULT = 1.5    # Displacement must be > avg_range * mult
DISP_BODY_RATIO = 0.6    # Body must be > 60% of range

# Structural SL/TP
STRUCT_SL_BUFFER_PCT = 0.0005  # 0.05% buffer beyond swing
MIN_SL_PCT = 0.003       # Minimum 0.3% SL

# ===================== TRADING MODE =====================
# WARNING: Set to True for LIVE TRADING with REAL MONEY on Cross Margin
LIVE_TRADING = True      # True = Live Trading | False = Paper Trading

# Live Trading Configuration (Cross Margin)
TRADE_USDC_TARGET = 200.0  # USDC per trade (live trading)
MAX_OPEN_POS = 3           # Maximum concurrent positions
MIN_NOTIONAL_PAD = 1.05    # Padding for minimum notional

# Paper Trading Configuration
PAPER_POSITION_SIZE_USDC = 100.0  # Simulated position size in USDC

# Symbols to trade
SYMBOLS = [
    "BTC/USDT",
    "ETH/USDT",
]

# CSV File
CSV_PATH = "ict_trades.csv"

# ===================== GLOBAL STATE =====================
pending = {}   # Pending setups: {symbol: {...}}
positions = {} # Open positions: {symbol: {...}}

# ===================== LOGGING =====================
def log(msg: str):
    """Console logging with timestamp"""
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {msg}", flush=True)

# ===================== CSV LOGGING =====================
def init_csv():
    """Initialize CSV file with headers if it doesn't exist"""
    if not os.path.exists(CSV_PATH):
        with open(CSV_PATH, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                'timestamp', 'symbol', 'side', 'entry_price', 'sl_price', 
                'tp1_price', 'tp2_price', 'exit_price', 'pnl_gross_pct', 
                'pnl_net_pct', 'duration_min', 'exit_reason'
            ])
        abs_path = os.path.abspath(CSV_PATH)
        log(f"CSV file created: {CSV_PATH}")
        log(f"📁 Full path: {abs_path}")
        log(f"💡 You can open this file with Excel or any spreadsheet program")
    else:
        abs_path = os.path.abspath(CSV_PATH)
        log(f"CSV file exists: {CSV_PATH}")
        log(f"📁 Full path: {abs_path}")

def log_trade_to_csv(trade_data: dict):
    """Append trade to CSV file"""
    with open(CSV_PATH, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            trade_data['timestamp'],
            trade_data['symbol'],
            trade_data['side'],
            trade_data['entry_price'],
            trade_data['sl_price'],
            trade_data['tp1_price'],
            trade_data['tp2_price'],
            trade_data['exit_price'],
            trade_data['pnl_gross_pct'],
            trade_data['pnl_net_pct'],
            trade_data['duration_min'],
            trade_data['exit_reason']
        ])
    log(f"Trade logged to CSV: {trade_data['symbol']} {trade_data['side']} - {trade_data['exit_reason']}")

# ===================== EXCHANGE SETUP =====================
def init_exchange():
    """Initialize CCXT exchange"""
    if LIVE_TRADING:
        log("⚠️  INITIALIZING BINANCE FOR LIVE TRADING (CROSS MARGIN) ⚠️")
        log("WARNING: This will use REAL MONEY!")
        
        api_key = os.getenv("BINANCE_API_KEY")
        api_secret = os.getenv("BINANCE_API_SECRET")
        
        if not api_key or not api_secret:
            log("ERROR: BINANCE_API_KEY and BINANCE_API_SECRET environment variables required for live trading")
            raise ValueError("Missing API credentials for live trading")
        
        log(f"API Key length: {len(api_key)}")
        log(f"API Secret length: {len(api_secret)}")
        
        exchange = ccxt.binance({
            'apiKey': api_key,
            'secret': api_secret,
            'enableRateLimit': True,
            'timeout': 60000,
            'options': {
                'adjustForTimeDifference': True,
                'recvWindow': 60000,
                'fetchCurrencies': False,
            }
        })
    else:
        log("Initializing Binance exchange (paper trading mode)...")
        # For paper trading, we can use public data only (no API keys needed)
        exchange = ccxt.binance({
            'enableRateLimit': True,
            'timeout': 30000,
        })
    
    try:
        exchange.load_markets()
        log(f"Markets loaded successfully: {len(exchange.markets)} markets")
    except Exception as e:
        log(f"ERROR loading markets: {e}")
        raise
    
    return exchange

# ===================== DATA FETCHING =====================
def fetch_ohlcv(exchange, symbol: str, timeframe: str, limit: int) -> pd.DataFrame:
    """Fetch OHLCV data and return as DataFrame"""
    try:
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
        if not ohlcv:
            return pd.DataFrame()
        
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        return df
    except Exception as e:
        log(f"ERROR fetching {symbol} {timeframe}: {e}")
        return pd.DataFrame()

# ===================== CROSS MARGIN ORDER EXECUTION =====================
def to_binance_symbol(symbol: str) -> str:
    """Convert CCXT symbol format to Binance format"""
    return symbol.replace("/", "")

def get_binance_filters(exchange, symbol: str):
    """Get trading filters for symbol"""
    try:
        market = exchange.markets.get(symbol)
        if not market:
            return None, None, None
        
        info = market.get('info', {})
        filters = info.get('filters', [])
        
        step_size = None
        min_qty = None
        min_notional = None
        
        for f in filters:
            if f.get('filterType') == 'LOT_SIZE':
                step_size = float(f.get('stepSize', 0))
                min_qty = float(f.get('minQty', 0))
            elif f.get('filterType') == 'NOTIONAL':
                min_notional = float(f.get('minNotional', 0))
        
        return step_size, min_qty, min_notional
    except Exception as e:
        log(f"ERROR getting filters for {symbol}: {e}")
        return None, None, None

def fmt_qty(exchange, symbol: str, amount: float) -> str:
    """Format quantity according to symbol filters"""
    step_size, min_qty, _ = get_binance_filters(exchange, symbol)
    
    if step_size and step_size > 0:
        import math
        amount = math.floor(amount / step_size) * step_size
    
    if min_qty and amount < min_qty:
        amount = min_qty
    
    # Determine decimal places
    if step_size and step_size > 0:
        decimals = len(str(step_size).rstrip('0').split('.')[-1]) if '.' in str(step_size) else 0
    else:
        decimals = 8
    
    return f"{amount:.{decimals}f}"

def calc_amount_from_usdc(exchange, symbol: str, usdc_target: float, ref_price: float) -> float:
    """Calculate amount from USDC target considering filters"""
    step_size, min_qty, min_notional = get_binance_filters(exchange, symbol)
    
    target = float(usdc_target)
    if min_notional and target < min_notional:
        target = min_notional * MIN_NOTIONAL_PAD
    
    import math
    amt = target / max(ref_price, 1e-12)
    
    if step_size and step_size > 0:
        amt = math.floor(amt / step_size) * step_size
    
    if min_qty and amt < min_qty:
        amt = min_qty
    
    return float(amt)

def get_cross_base_free(exchange, symbol: str) -> float:
    """Get available base asset balance in cross margin account"""
    base = symbol.split("/")[0].strip().upper()
    try:
        data = exchange.sapiGetMarginAccount({
            "timestamp": exchange.milliseconds(),
            "recvWindow": 60000
        })
        assets = data.get("userAssets") or []
        for a in assets:
            if (a.get("asset") or "").upper() == base:
                return float(a.get("free", 0.0) or 0.0)
        return 0.0
    except Exception as e:
        log(f"WARN cannot fetch cross margin balance for {symbol}: {e}")
        return 0.0

def place_entry_market(exchange, symbol: str, side: str, ref_price: float):
    """Place market entry order on cross margin"""
    bsym = to_binance_symbol(symbol)
    
    try:
        if side == "LONG":
            # Buy on cross margin
            params = {
                "symbol": bsym,
                "side": "BUY",
                "type": "MARKET",
                "sideEffectType": "MARGIN_BUY",
                "quoteOrderQty": str(int(TRADE_USDC_TARGET)),
                "timestamp": exchange.milliseconds(),
                "recvWindow": 60000,
            }
            order = exchange.sapiPostMarginOrder(params)
            filled_qty = float(order.get("executedQty", 0.0))
            filled_price = float(order.get("cummulativeQuoteQty", 0.0)) / max(filled_qty, 1e-12)
            return order, filled_qty, filled_price
        
        else:  # SHORT
            # Sell on cross margin (borrow)
            amount = calc_amount_from_usdc(exchange, symbol, TRADE_USDC_TARGET, ref_price)
            params = {
                "symbol": bsym,
                "side": "SELL",
                "type": "MARKET",
                "quantity": fmt_qty(exchange, symbol, amount),
                "sideEffectType": "AUTO_BORROW_REPAY",
                "timestamp": exchange.milliseconds(),
                "recvWindow": 60000,
            }
            order = exchange.sapiPostMarginOrder(params)
            filled_qty = float(order.get("executedQty", amount))
            filled_price = float(order.get("cummulativeQuoteQty", 0.0)) / max(filled_qty, 1e-12)
            return order, filled_qty, filled_price
    
    except Exception as e:
        log(f"ERROR placing entry order for {symbol} {side}: {e}")
        raise

def place_close_market(exchange, symbol: str, side: str, amount: float):
    """Place market close order on cross margin"""
    bsym = to_binance_symbol(symbol)
    
    if amount <= 0:
        raise ValueError(f"Invalid amount for close: {amount}")
    
    try:
        params = {
            "symbol": bsym,
            "type": "MARKET",
            "quantity": fmt_qty(exchange, symbol, amount),
            "sideEffectType": "AUTO_REPAY",
            "timestamp": exchange.milliseconds(),
            "recvWindow": 60000,
        }
        
        # Opposite side to close
        params["side"] = "SELL" if side == "LONG" else "BUY"
        
        order = exchange.sapiPostMarginOrder(params)
        return order
    
    except Exception as e:
        log(f"ERROR placing close order for {symbol} {side}: {e}")
        raise

# ===================== SWING DETECTION =====================
def find_swings(df: pd.DataFrame, lr: int = 2) -> Tuple[List[Tuple[int, float]], List[Tuple[int, float]]]:
    """
    Find swing highs and lows using fractal pattern
    Returns: (swing_highs, swing_lows) where each is [(index, price), ...]
    """
    if len(df) < lr * 2 + 1:
        return [], []
    
    highs = df['high'].values
    lows = df['low'].values
    
    swing_highs = []
    swing_lows = []
    
    for i in range(lr, len(df) - lr):
        # Check if this is a swing high
        is_swing_high = True
        for k in range(1, lr + 1):
            if highs[i] <= highs[i - k] or highs[i] <= highs[i + k]:
                is_swing_high = False
                break
        if is_swing_high:
            swing_highs.append((i, float(highs[i])))
        
        # Check if this is a swing low
        is_swing_low = True
        for k in range(1, lr + 1):
            if lows[i] >= lows[i - k] or lows[i] >= lows[i + k]:
                is_swing_low = False
                break
        if is_swing_low:
            swing_lows.append((i, float(lows[i])))
    
    return swing_highs, swing_lows

# ===================== BIAS DETECTION (30m) =====================
def detect_bias(df: pd.DataFrame) -> Optional[str]:
    """
    Detect market bias on 30m timeframe using BOS/CHoCH
    Returns: 'BULLISH', 'BEARISH', or None
    """
    if len(df) < 20:
        return None
    
    swing_highs, swing_lows = find_swings(df, SWING_LR)
    
    if len(swing_highs) < 2 or len(swing_lows) < 2:
        return None
    
    # Get last few candles
    last_close = float(df.iloc[-1]['close'])
    
    # Get recent swing highs and lows
    recent_swing_high = swing_highs[-1][1] if swing_highs else None
    prev_swing_high = swing_highs[-2][1] if len(swing_highs) >= 2 else None
    recent_swing_low = swing_lows[-1][1] if swing_lows else None
    prev_swing_low = swing_lows[-2][1] if len(swing_lows) >= 2 else None
    
    # BOS (Break of Structure): price breaks previous swing in trend direction
    # CHoCH (Change of Character): price breaks previous swing against trend
    
    # Check for BULLISH bias: close > previous swing high (BOS in uptrend)
    if prev_swing_high and last_close > prev_swing_high:
        return 'BULLISH'
    
    # Check for BEARISH bias: close < previous swing low (BOS in downtrend)
    if prev_swing_low and last_close < prev_swing_low:
        return 'BEARISH'
    
    # Check for CHoCH (trend reversal)
    if recent_swing_low and prev_swing_high and recent_swing_low > prev_swing_high:
        # Higher lows indicate potential bullish reversal
        return 'BULLISH'
    
    if recent_swing_high and prev_swing_low and recent_swing_high < prev_swing_low:
        # Lower highs indicate potential bearish reversal
        return 'BEARISH'
    
    return None

# ===================== ENTRY SETUP DETECTION (5m) =====================
def detect_sweep(df: pd.DataFrame, bias: str) -> Optional[Tuple[int, float]]:
    """
    Detect liquidity sweep
    For BULLISH: price wicks below recent swing low then closes above
    For BEARISH: price wicks above recent swing high then closes below
    Returns: (candle_index, swept_level) or None
    """
    if len(df) < 10:
        return None
    
    swing_highs, swing_lows = find_swings(df, SWING_LR)
    
    # Look at recent candles (last 10)
    for i in range(len(df) - 10, len(df)):
        if i < 0:
            continue
        
        candle = df.iloc[i]
        low = float(candle['low'])
        high = float(candle['high'])
        close = float(candle['close'])
        
        if bias == 'BULLISH':
            # Look for sweep below recent swing low
            for swing_idx, swing_low in reversed(swing_lows[-5:]):
                if swing_idx >= i:
                    continue
                # Wick below swing low with buffer
                if low < swing_low * (1 - SWEEP_BUFFER_PCT):
                    # But close above swing low
                    if close > swing_low:
                        return (i, swing_low)
        
        elif bias == 'BEARISH':
            # Look for sweep above recent swing high
            for swing_idx, swing_high in reversed(swing_highs[-5:]):
                if swing_idx >= i:
                    continue
                # Wick above swing high with buffer
                if high > swing_high * (1 + SWEEP_BUFFER_PCT):
                    # But close below swing high
                    if close < swing_high:
                        return (i, swing_high)
    
    return None

def detect_displacement(df: pd.DataFrame, bias: str, after_idx: int) -> Optional[int]:
    """
    Detect displacement candle: strong directional move
    Must have large range (> avg) and strong body ratio
    Returns: candle_index or None
    """
    if len(df) < after_idx + 5:
        return None
    
    # Calculate average range
    ranges = []
    for i in range(max(0, len(df) - AVG_RANGE_LEN), len(df)):
        h = float(df.iloc[i]['high'])
        l = float(df.iloc[i]['low'])
        ranges.append(h - l)
    
    if not ranges:
        return None
    
    avg_range = sum(ranges) / len(ranges)
    threshold_range = avg_range * DISP_RANGE_MULT
    
    # Look for displacement after sweep
    for i in range(after_idx + 1, len(df)):
        candle = df.iloc[i]
        open_price = float(candle['open'])
        high = float(candle['high'])
        low = float(candle['low'])
        close = float(candle['close'])
        
        candle_range = high - low
        body = abs(close - open_price)
        body_ratio = body / candle_range if candle_range > 0 else 0
        
        # Check if displacement
        if candle_range > threshold_range and body_ratio > DISP_BODY_RATIO:
            if bias == 'BULLISH' and close > open_price:
                return i
            elif bias == 'BEARISH' and close < open_price:
                return i
    
    return None

def detect_retrace(df: pd.DataFrame, bias: str, disp_idx: int) -> bool:
    """
    Detect retrace: pullback after displacement
    For BULLISH: price pulls back (lower low or close below displacement low)
    For BEARISH: price pulls back (higher high or close above displacement high)
    Returns: True if retracement detected
    """
    if disp_idx >= len(df) - 1:
        return False
    
    disp_candle = df.iloc[disp_idx]
    disp_high = float(disp_candle['high'])
    disp_low = float(disp_candle['low'])
    disp_close = float(disp_candle['close'])
    
    # Check candles after displacement
    for i in range(disp_idx + 1, len(df)):
        candle = df.iloc[i]
        close = float(candle['close'])
        high = float(candle['high'])
        low = float(candle['low'])
        
        if bias == 'BULLISH':
            # Retrace: price pulls back below displacement high
            if close < disp_high * 0.995:  # At least 0.5% retrace
                return True
        elif bias == 'BEARISH':
            # Retrace: price pulls back above displacement low
            if close > disp_low * 1.005:  # At least 0.5% retrace
                return True
    
    return False

def check_confirmation(df: pd.DataFrame, bias: str) -> bool:
    """
    Check for entry confirmation on latest candle
    For BULLISH: bullish close (close > open)
    For BEARISH: bearish close (close < open)
    """
    if len(df) < 1:
        return False
    
    last_candle = df.iloc[-1]
    open_price = float(last_candle['open'])
    close = float(last_candle['close'])
    
    if bias == 'BULLISH':
        return close > open_price
    elif bias == 'BEARISH':
        return close < open_price
    
    return False

# ===================== SL/TP CALCULATION =====================
def calculate_sl_tp(df: pd.DataFrame, side: str, entry_price: float, sweep_level: float) -> dict:
    """
    Calculate structural SL and TP levels
    SL: Below sweep level for LONG, Above sweep level for SHORT (+ buffer)
    TP1: First swing ahead (internal liquidity)
    TP2: Second/major swing ahead (external liquidity)
    """
    swing_highs, swing_lows = find_swings(df, SWING_LR)
    
    if side == 'LONG':
        # SL below sweep level (swing low)
        sl_price = sweep_level * (1 - STRUCT_SL_BUFFER_PCT)
        
        # TP1: First swing high above entry
        tp1_price = None
        for idx, sh in swing_highs:
            if sh > entry_price:
                tp1_price = sh
                break
        
        # TP2: Second swing high above entry (or further away)
        tp2_price = None
        count = 0
        for idx, sh in swing_highs:
            if sh > entry_price:
                count += 1
                if count == 2:
                    tp2_price = sh
                    break
        
        # Fallback: if no swings found, use percentage-based targets
        if not tp1_price:
            tp1_price = entry_price * 1.01  # 1% above
        if not tp2_price:
            tp2_price = entry_price * 1.02  # 2% above
        
    else:  # SHORT
        # SL above sweep level (swing high)
        sl_price = sweep_level * (1 + STRUCT_SL_BUFFER_PCT)
        
        # TP1: First swing low below entry
        tp1_price = None
        for idx, sl in reversed(swing_lows):
            if sl < entry_price:
                tp1_price = sl
                break
        
        # TP2: Second swing low below entry (or further away)
        tp2_price = None
        count = 0
        for idx, sl in reversed(swing_lows):
            if sl < entry_price:
                count += 1
                if count == 2:
                    tp2_price = sl
                    break
        
        # Fallback: if no swings found, use percentage-based targets
        if not tp1_price:
            tp1_price = entry_price * 0.99  # 1% below
        if not tp2_price:
            tp2_price = entry_price * 0.98  # 2% below
    
    # Ensure minimum SL distance
    sl_distance = abs(entry_price - sl_price) / entry_price
    if sl_distance < MIN_SL_PCT:
        if side == 'LONG':
            sl_price = entry_price * (1 - MIN_SL_PCT)
        else:
            sl_price = entry_price * (1 + MIN_SL_PCT)
    
    return {
        'sl_price': sl_price,
        'tp1_price': tp1_price,
        'tp2_price': tp2_price
    }

# ===================== POSITION MANAGEMENT =====================
def open_position(exchange, symbol: str, side: str, entry_price: float, sl_tp: dict):
    """Open a position (paper or live trading)"""
    if LIVE_TRADING:
        # Live trading on cross margin
        try:
            log(f"🔥 OPENING LIVE POSITION: {symbol} {side}")
            order, filled_qty, filled_price = place_entry_market(exchange, symbol, side, entry_price)
            
            position = {
                'symbol': symbol,
                'side': side,
                'entry_price': filled_price,
                'sl_price': sl_tp['sl_price'],
                'tp1_price': sl_tp['tp1_price'],
                'tp2_price': sl_tp['tp2_price'],
                'tp1_hit': False,
                'entry_time': datetime.utcnow(),
                'amount': filled_qty,
                'size_usdc': TRADE_USDC_TARGET
            }
            
            positions[symbol] = position
            
            log(f"✅ LIVE POSITION OPENED: {symbol} {side}")
            log(f"   Entry: ${filled_price:.4f} (Qty: {filled_qty:.6f})")
            log(f"   SL: ${sl_tp['sl_price']:.4f} ({((sl_tp['sl_price']/filled_price - 1) * 100):.2f}%)")
            log(f"   TP1: ${sl_tp['tp1_price']:.4f} ({((sl_tp['tp1_price']/filled_price - 1) * 100):.2f}%)")
            log(f"   TP2: ${sl_tp['tp2_price']:.4f} ({((sl_tp['tp2_price']/filled_price - 1) * 100):.2f}%)")
        
        except Exception as e:
            log(f"❌ ERROR opening live position: {e}")
            return
    else:
        # Paper trading
        position = {
            'symbol': symbol,
            'side': side,
            'entry_price': entry_price,
            'sl_price': sl_tp['sl_price'],
            'tp1_price': sl_tp['tp1_price'],
            'tp2_price': sl_tp['tp2_price'],
            'tp1_hit': False,
            'entry_time': datetime.utcnow(),
            'size_usdc': PAPER_POSITION_SIZE_USDC
        }
        
        positions[symbol] = position
        
        log(f"📈 PAPER TRADE OPENED: {symbol} {side}")
        log(f"   Entry: ${entry_price:.4f}")
        log(f"   SL: ${sl_tp['sl_price']:.4f} ({((sl_tp['sl_price']/entry_price - 1) * 100):.2f}%)")
        log(f"   TP1: ${sl_tp['tp1_price']:.4f} ({((sl_tp['tp1_price']/entry_price - 1) * 100):.2f}%)")
        log(f"   TP2: ${sl_tp['tp2_price']:.4f} ({((sl_tp['tp2_price']/entry_price - 1) * 100):.2f}%)")

def close_position(exchange, symbol: str, exit_price: float, exit_reason: str):
    """Close a position (paper or live trading) and log to CSV"""
    if symbol not in positions:
        return
    
    pos = positions[symbol]
    entry_price = pos['entry_price']
    entry_time = pos['entry_time']
    exit_time = datetime.utcnow()
    duration_min = (exit_time - entry_time).total_seconds() / 60
    
    if LIVE_TRADING:
        # Close live position
        try:
            # For LONG, get actual base balance
            if pos['side'] == 'LONG':
                amount = get_cross_base_free(exchange, symbol)
                if amount <= 0:
                    amount = pos.get('amount', 0.0)
            else:
                amount = pos.get('amount', 0.0)
            
            log(f"🔥 CLOSING LIVE POSITION: {symbol} {pos['side']} (Amount: {amount:.6f})")
            order = place_close_market(exchange, symbol, pos['side'], amount)
            
            # Get actual exit price from order
            filled_qty = float(order.get("executedQty", amount))
            filled_quote = float(order.get("cummulativeQuoteQty", 0.0))
            if filled_qty > 0:
                exit_price = filled_quote / filled_qty
            
            log(f"✅ LIVE POSITION CLOSED: {symbol} at ${exit_price:.4f}")
        
        except Exception as e:
            log(f"❌ ERROR closing live position: {e}")
            # Continue to log the trade even if close failed
    
    # Calculate PnL
    if pos['side'] == 'LONG':
        pnl_gross_pct = ((exit_price / entry_price) - 1) * 100
    else:  # SHORT
        pnl_gross_pct = ((entry_price / exit_price) - 1) * 100
    
    # Fee estimation (0.1% for paper, 0.2% for live)
    fee_pct = 0.2 if LIVE_TRADING else 0.1
    pnl_net_pct = pnl_gross_pct - fee_pct
    
    # Log to CSV
    trade_data = {
        'timestamp': exit_time.strftime('%Y-%m-%d %H:%M:%S'),
        'symbol': symbol,
        'side': pos['side'],
        'entry_price': f"{entry_price:.4f}",
        'sl_price': f"{pos['sl_price']:.4f}",
        'tp1_price': f"{pos['tp1_price']:.4f}",
        'tp2_price': f"{pos['tp2_price']:.4f}",
        'exit_price': f"{exit_price:.4f}",
        'pnl_gross_pct': f"{pnl_gross_pct:.2f}",
        'pnl_net_pct': f"{pnl_net_pct:.2f}",
        'duration_min': f"{duration_min:.1f}",
        'exit_reason': exit_reason
    }
    
    log_trade_to_csv(trade_data)
    
    # Console log
    mode = "LIVE" if LIVE_TRADING else "PAPER"
    log(f"🔴 {mode} TRADE CLOSED: {symbol} {pos['side']}")
    log(f"   Exit: ${exit_price:.4f}")
    log(f"   PnL: {pnl_net_pct:.2f}% (Net)")
    log(f"   Duration: {duration_min:.1f} min")
    log(f"   Reason: {exit_reason}")
    
    # Remove position
    del positions[symbol]

def check_position_exit(exchange, symbol: str, df: pd.DataFrame):
    """Check if position should be exited based on current candle"""
    if symbol not in positions:
        return
    
    pos = positions[symbol]
    last_candle = df.iloc[-1]
    high = float(last_candle['high'])
    low = float(last_candle['low'])
    close = float(last_candle['close'])
    
    if pos['side'] == 'LONG':
        # Check SL hit
        if low <= pos['sl_price']:
            close_position(exchange, symbol, pos['sl_price'], 'SL_HIT')
            return
        
        # Check TP2 hit first (full exit)
        if high >= pos['tp2_price']:
            close_position(exchange, symbol, pos['tp2_price'], 'TP2_HIT')
            return
        
        # Check TP1 hit (move SL to BE)
        if high >= pos['tp1_price'] and not pos['tp1_hit']:
            pos['tp1_hit'] = True
            pos['sl_price'] = pos['entry_price']  # Move SL to breakeven
            log(f"✅ TP1 HIT: {symbol} - SL moved to BE (${pos['entry_price']:.4f})")
            return
    
    else:  # SHORT
        # Check SL hit
        if high >= pos['sl_price']:
            close_position(exchange, symbol, pos['sl_price'], 'SL_HIT')
            return
        
        # Check TP2 hit first (full exit)
        if low <= pos['tp2_price']:
            close_position(exchange, symbol, pos['tp2_price'], 'TP2_HIT')
            return
        
        # Check TP1 hit (move SL to BE)
        if low <= pos['tp1_price'] and not pos['tp1_hit']:
            pos['tp1_hit'] = True
            pos['sl_price'] = pos['entry_price']  # Move SL to breakeven
            log(f"✅ TP1 HIT: {symbol} - SL moved to BE (${pos['entry_price']:.4f})")
            return

# ===================== MAIN LOGIC =====================
def scan_symbol(exchange, symbol: str, df_bias: pd.DataFrame, df_entry: pd.DataFrame):
    """Scan a symbol for ICT setups"""
    
    # Skip if position already open
    if symbol in positions:
        check_position_exit(exchange, symbol, df_entry)
        return
    
    # Step 1: Detect bias on 30m
    bias = detect_bias(df_bias)
    if not bias:
        return
    
    # Check if we have a pending setup
    if symbol not in pending:
        # Initialize new pending setup
        pending[symbol] = {
            'state': 'WAIT_SWEEP',
            'bias': bias,
            'sweep_idx': None,
            'sweep_level': None,
            'disp_idx': None
        }
    
    setup = pending[symbol]
    
    # Update bias if changed
    if setup['bias'] != bias:
        # Reset if bias changed
        setup['state'] = 'WAIT_SWEEP'
        setup['bias'] = bias
        setup['sweep_idx'] = None
        setup['sweep_level'] = None
        setup['disp_idx'] = None
    
    # State machine for entry
    if setup['state'] == 'WAIT_SWEEP':
        sweep_result = detect_sweep(df_entry, bias)
        if sweep_result:
            sweep_idx, sweep_level = sweep_result
            setup['sweep_idx'] = sweep_idx
            setup['sweep_level'] = sweep_level
            setup['state'] = 'WAIT_DISPLACEMENT'
            log(f"🔍 {symbol}: SWEEP detected at ${sweep_level:.4f} (bias: {bias})")
    
    elif setup['state'] == 'WAIT_DISPLACEMENT':
        disp_idx = detect_displacement(df_entry, bias, setup['sweep_idx'])
        if disp_idx:
            setup['disp_idx'] = disp_idx
            setup['state'] = 'WAIT_RETRACE'
            log(f"🚀 {symbol}: DISPLACEMENT detected (bias: {bias})")
    
    elif setup['state'] == 'WAIT_RETRACE':
        if detect_retrace(df_entry, bias, setup['disp_idx']):
            setup['state'] = 'WAIT_CONFIRM'
            log(f"↩️  {symbol}: RETRACE detected (bias: {bias})")
    
    elif setup['state'] == 'WAIT_CONFIRM':
        if check_confirmation(df_entry, bias):
            # Entry confirmed! Open position
            entry_price = float(df_entry.iloc[-1]['close'])
            side = 'LONG' if bias == 'BULLISH' else 'SHORT'
            
            # Check max positions limit for live trading
            if LIVE_TRADING and len(positions) >= MAX_OPEN_POS:
                log(f"⚠️  {symbol}: SKIP - Max positions ({MAX_OPEN_POS}) reached")
                return
            
            # Calculate SL/TP
            sl_tp = calculate_sl_tp(df_entry, side, entry_price, setup['sweep_level'])
            
            # Open position
            open_position(exchange, symbol, side, entry_price, sl_tp)
            
            # Clear pending setup
            del pending[symbol]
            
            log(f"✅ {symbol}: CONFIRM detected - Position opened!")

def main():
    """Main bot loop"""
    log("=" * 60)
    if LIVE_TRADING:
        log("⚠️  ⚠️  ⚠️  LIVE TRADING MODE - CROSS MARGIN  ⚠️  ⚠️  ⚠️")
        log("WARNING: This bot will trade with REAL MONEY!")
        log("=" * 60)
        log(f"Max Positions: {MAX_OPEN_POS}")
        log(f"Trade Size: ${TRADE_USDC_TARGET} USDT per trade")
    else:
        log("MINIMALIST ICT PAPER TRADING BOT")
        log("=" * 60)
        log(f"Paper Trading Mode: Active (No real money)")
        log(f"Position Size: ${PAPER_POSITION_SIZE_USDC} USDT per trade")
    
    log(f"Symbols: {', '.join(SYMBOLS)}")
    log(f"Bias TF: {BIAS_TF} | Entry TF: {ENTRY_TF}")
    log("=" * 60)
    
    # Initialize CSV
    init_csv()
    
    # Initialize exchange
    exchange = init_exchange()
    
    if LIVE_TRADING:
        log("\n🔥 LIVE TRADING ACTIVE - Bot will execute real orders!")
    else:
        log("\n🤖 PAPER TRADING - Bot will simulate trades only.")
    
    log("Press Ctrl+C to stop.\n")
    
    loop_count = 0
    
    try:
        while True:
            loop_count += 1
            log(f"\n--- Loop {loop_count} ---")
            
            for symbol in SYMBOLS:
                try:
                    # Fetch data
                    df_bias = fetch_ohlcv(exchange, symbol, BIAS_TF, LOOKBACK_BIAS)
                    df_entry = fetch_ohlcv(exchange, symbol, ENTRY_TF, LOOKBACK_ENTRY)
                    
                    if df_bias.empty or df_entry.empty:
                        log(f"⚠️  {symbol}: No data available")
                        continue
                    
                    # Scan for setups
                    scan_symbol(exchange, symbol, df_bias, df_entry)
                    
                except Exception as e:
                    log(f"❌ ERROR processing {symbol}: {e}")
            
            # Status summary
            mode = "LIVE" if LIVE_TRADING else "PAPER"
            log(f"\n📊 {mode} Status: {len(positions)} open positions, {len(pending)} pending setups")
            
            if positions:
                for sym, pos in positions.items():
                    log(f"   • {sym} {pos['side']} @ ${pos['entry_price']:.4f}")
            
            # Wait before next loop
            time.sleep(LOOP_SEC)
            
    except KeyboardInterrupt:
        log("\n\n🛑 Bot stopped by user")
        
        # Close any open positions
        if positions:
            log("\nClosing open positions...")
            for symbol in list(positions.keys()):
                pos = positions[symbol]
                # Use last known price for exit
                try:
                    df = fetch_ohlcv(exchange, symbol, ENTRY_TF, 10)
                    if not df.empty:
                        exit_price = float(df.iloc[-1]['close'])
                        close_position(exchange, symbol, exit_price, 'BOT_STOPPED')
                except Exception as e:
                    log(f"Error closing position for {symbol}: {e}")
        
        log("\n✅ Bot shutdown complete")

if __name__ == "__main__":
    main()
