# -*- coding: utf-8 -*-
"""
===================== ICT SMART MONEY BOT (LIVE CROSS MARGIN) v10.0 =====================

Complete Revision for Binance Live Margin Trading
- Centralized logging system with CSV and Excel export
- Robust error handling with retry mechanisms
- Mock testing functionality
- Comprehensive documentation
- Type hints and dataclasses
- Best practices Python implementation

Author: Revised Version for Production Trading
Date: 2026-02-12
"""

import os
import sys
import time
import csv
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, List, Tuple, Any
from dataclasses import dataclass, field, asdict
from enum import Enum
from decimal import Decimal, ROUND_DOWN, getcontext
import math
from collections import Counter

import pandas as pd
import ccxt
import requests
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, PatternFill, Alignment
from logging.handlers import RotatingFileHandler

# Set decimal precision
getcontext().prec = 28

# ===================== ENUMS =====================

class TradeSide(Enum):
    """Trade side enumeration"""
    LONG = "LONG"
    SHORT = "SHORT"

class TradeState(Enum):
    """State machine for ICTR strategy"""
    WAIT_SWEEP = "WAIT_SWEEP"
    WAIT_DISPLACEMENT = "WAIT_DISPLACEMENT"
    WAIT_RETRACE = "WAIT_RETRACE"
    WAIT_CONFIRM = "WAIT_CONFIRM"
    OPEN = "OPEN"

class LogLevel(Enum):
    """Log level enumeration"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

# ===================== CONFIGURATION =====================

@dataclass
class TradingConfig:
    """Trading configuration parameters"""
    # Environment
    live_trading: bool = True
    mock_mode: bool = False
    
    # Timeframes
    bias_tf: str = "30m"
    entry_tf: str = "5m"
    sl_tf: str = "15m"
    
    # Lookback periods
    lookback_bias: int = 260
    lookback_entry: int = 320
    lookback_sl: int = 220
    
    # Position management
    max_open_positions: int = 3
    trade_usdc_target: float = 200.0
    min_notional_pad: float = 1.05
    
    # Risk parameters
    tp_gross_pct: float = 0.0120  # 1.20% initial TP
    sl_cap_pct: float = 0.0065    # 0.65% max SL
    sl_fixed_pct: float = 0.0100  # 1.00% fixed SL
    min_struct_sl_pct: float = 0.0035  # 0.35% min structural SL
    
    # TP Ladder
    tp_ladder_pcts: List[float] = field(default_factory=lambda: [0.0120])
    tp_after_last_step: float = 0.0025  # 0.25% after last step
    lock_retrace_pct: float = 0.0030    # 0.30% retrace tolerance
    
    # Fees
    round_trip_fee_pct: float = 0.0020  # 0.20% estimated
    
    # Swing detection
    swing_lr_bias: int = 2
    swing_lr_entry: int = 2
    swing_lr_sl: int = 2
    
    # Sweep parameters
    sweep_buffer_pct: float = 0.00025
    
    # Displacement parameters
    avg_range_len: int = 20
    disp_range_mult: float = 1.25
    disp_body_ratio: float = 0.55
    
    # Order block / FVG
    ob_lookback: int = 6
    fvg_min_size_pct: float = 0.00010
    struct_sl_buffer_pct: float = 0.00020  # 0.02%
    
    # BTC filters
    btc_symbol: str = "BTC/USDC"
    btc_tf: str = "15m"
    btc_lookback: int = 260
    btc_near_pct: float = 0.0040  # 0.40%
    btc_rej_min: int = 2
    btc_rej_lookback: int = 120
    btc_rej_cooldown: int = 4
    btc_zone_days: int = 4
    btc_zone_cluster_pct: float = 0.0020
    btc_zone_near_pct: float = 0.0040
    btc_zone_min_rej: int = 2
    btc_zone_reject_window: int = 8
    btc_zone_reject_move_pct: float = 0.0150
    btc_zone_break_pct: float = 0.0010
    btc_trend_lr: int = 2
    
    # Symbols whitelist (USDC pairs for liquidity)
    symbols: List[str] = field(default_factory=lambda: [
        "BTC/USDC", "ETH/USDC", "BNB/USDC", "SOL/USDC",
        "XRP/USDC", "ADA/USDC", "DOGE/USDC", "AVAX/USDC",
        "LINK/USDC", "MATIC/USDC", "LTC/USDC", "TRX/USDC",
        "DOT/USDC", "ATOM/USDC", "NEAR/USDC", "APT/USDC",
        "OP/USDC", "ARB/USDC", "UNI/USDC", "FIL/USDC",
        "INJ/USDC", "AAVE/USDC", "ETC/USDC", "XLM/USDC",
        "SUI/USDC",
    ])
    
    # Logging
    log_dir: str = "logs"
    trades_csv_path: str = "trades_log.csv"
    trades_excel_path: str = "trades_log.xlsx"
    max_log_size_mb: int = 10
    log_backup_count: int = 5
    
    # Loop settings
    loop_sec: int = 25
    heartbeat_every_loops: int = 3
    print_pending_sample: int = 8
    
    # Debug
    debug_terminal: bool = True

@dataclass
class APIConfig:
    """API configuration"""
    api_key: str
    api_secret: str
    telegram_token: Optional[str] = None
    telegram_chat_id: Optional[str] = None
    
    @classmethod
    def from_env(cls) -> 'APIConfig':
        """Load API configuration from environment variables"""
        return cls(
            api_key=os.getenv("BINANCE_API_KEY", ""),
            api_secret=os.getenv("BINANCE_API_SECRET", ""),
            telegram_token=os.getenv("TG_BOT_TOKEN"),
            telegram_chat_id=os.getenv("TG_CHAT_ID")
        )

# ===================== DATA MODELS =====================

@dataclass
class TradeRecord:
    """Complete trade record for logging and export"""
    symbol: str
    side: str
    entry_time: datetime
    entry_price: float
    entry_order_id: Optional[str] = None
    exit_time: Optional[datetime] = None
    exit_price: Optional[float] = None
    exit_order_id: Optional[str] = None
    sl_price: float = 0.0
    tp_price: float = 0.0
    sl_type: str = ""
    amount: float = 0.0
    pnl_gross_pct: Optional[float] = None
    pnl_net_pct: Optional[float] = None
    grade: str = ""
    note: str = ""
    close_reason: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for CSV/Excel export"""
        return {
            'symbol': self.symbol,
            'side': self.side,
            'entry_time': self.entry_time.isoformat() if self.entry_time else '',
            'entry_price': self.entry_price,
            'entry_order_id': self.entry_order_id or '',
            'exit_time': self.exit_time.isoformat() if self.exit_time else '',
            'exit_price': self.exit_price or 0.0,
            'exit_order_id': self.exit_order_id or '',
            'sl_price': self.sl_price,
            'tp_price': self.tp_price,
            'sl_type': self.sl_type,
            'amount': self.amount,
            'pnl_gross_pct': self.pnl_gross_pct or 0.0,
            'pnl_net_pct': self.pnl_net_pct or 0.0,
            'grade': self.grade,
            'note': self.note,
            'close_reason': self.close_reason
        }

@dataclass
class Position:
    """Active position data"""
    symbol: str
    side: str
    entry: float
    sl: float
    sl_type: str
    tp: float
    tp_pct: float
    note: str
    amount: Optional[float] = None
    entry_order_id: Optional[str] = None
    entry_candle_ts: Optional[int] = None
    entry_time: Optional[datetime] = None

@dataclass
class PendingSetup:
    """Pending trade setup"""
    state: str
    side: str
    data: Dict[str, Any] = field(default_factory=dict)

# ===================== LOGGING SYSTEM =====================

class TradingLogger:
    """Centralized logging system with CSV and Excel export"""
    
    def __init__(self, config: TradingConfig):
        self.config = config
        self.log_dir = Path(config.log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # Setup main logger
        self.logger = self._setup_logger()
        
        # Trade records
        self.trade_records: List[TradeRecord] = []
        
        # Initialize CSV
        self._init_csv()
        
        # Initialize Excel
        self._init_excel()
    
    def _setup_logger(self) -> logging.Logger:
        """Setup rotating file logger"""
        logger = logging.getLogger('ICT_Trading')
        logger.setLevel(logging.DEBUG if self.config.debug_terminal else logging.INFO)
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG if self.config.debug_terminal else logging.INFO)
        console_format = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_format)
        
        # File handler with rotation
        log_file = self.log_dir / f"trading_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=self.config.max_log_size_mb * 1024 * 1024,
            backupCount=self.config.log_backup_count
        )
        file_handler.setLevel(logging.DEBUG)
        file_format = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(funcName)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_format)
        
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)
        
        return logger
    
    def _init_csv(self):
        """Initialize CSV file with headers"""
        csv_path = Path(self.config.trades_csv_path)
        if not csv_path.exists():
            with open(csv_path, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=[
                    'symbol', 'side', 'entry_time', 'entry_price', 'entry_order_id',
                    'exit_time', 'exit_price', 'exit_order_id',
                    'sl_price', 'tp_price', 'sl_type', 'amount',
                    'pnl_gross_pct', 'pnl_net_pct', 'grade', 'note', 'close_reason'
                ])
                writer.writeheader()
    
    def _init_excel(self):
        """Initialize Excel workbook"""
        excel_path = Path(self.config.trades_excel_path)
        if not excel_path.exists():
            wb = Workbook()
            ws = wb.active
            ws.title = "Trades"
            
            # Headers
            headers = [
                'Symbol', 'Side', 'Entry Time', 'Entry Price', 'Entry Order ID',
                'Exit Time', 'Exit Price', 'Exit Order ID',
                'SL Price', 'TP Price', 'SL Type', 'Amount',
                'PnL Gross %', 'PnL Net %', 'Grade', 'Note', 'Close Reason'
            ]
            
            for col, header in enumerate(headers, start=1):
                cell = ws.cell(row=1, column=col, value=header)
                cell.font = Font(bold=True)
                cell.fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
                cell.font = Font(bold=True, color="FFFFFF")
                cell.alignment = Alignment(horizontal="center")
            
            wb.save(excel_path)
    
    def log_event(self, level: str, message: str, **kwargs):
        """
        Central logging function - all logging goes through here
        
        Args:
            level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            message: Log message
            **kwargs: Additional context data
        """
        # Add timestamp
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Format message with context
        if kwargs:
            context = " | ".join([f"{k}={v}" for k, v in kwargs.items()])
            full_message = f"{message} | {context}"
        else:
            full_message = message
        
        # Log to appropriate level
        log_func = getattr(self.logger, level.lower(), self.logger.info)
        log_func(full_message)
        
        # Also print to console if debug enabled
        if self.config.debug_terminal:
            print(f"[{timestamp}] {level}: {full_message}", flush=True)
    
    def log_trade_open(self, trade: TradeRecord):
        """Log trade opening"""
        self.log_event(
            'INFO',
            f"OPEN POSITION: {trade.symbol} {trade.side}",
            entry_price=trade.entry_price,
            sl=trade.sl_price,
            tp=trade.tp_price,
            amount=trade.amount
        )
        self.trade_records.append(trade)
    
    def log_trade_close(self, trade: TradeRecord):
        """Log trade closing and export to CSV/Excel"""
        self.log_event(
            'INFO',
            f"CLOSE POSITION: {trade.symbol} {trade.side}",
            exit_price=trade.exit_price,
            pnl_gross=f"{trade.pnl_gross_pct:.2f}%",
            pnl_net=f"{trade.pnl_net_pct:.2f}%",
            reason=trade.close_reason
        )
        
        # Export to CSV
        self._append_to_csv(trade)
        
        # Export to Excel
        self._append_to_excel(trade)
    
    def _append_to_csv(self, trade: TradeRecord):
        """Append trade to CSV file"""
        try:
            csv_path = Path(self.config.trades_csv_path)
            with open(csv_path, 'a', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=trade.to_dict().keys())
                writer.writerow(trade.to_dict())
        except Exception as e:
            self.log_event('ERROR', f"Failed to append to CSV: {e}")
    
    def _append_to_excel(self, trade: TradeRecord):
        """Append trade to Excel file"""
        try:
            excel_path = Path(self.config.trades_excel_path)
            wb = load_workbook(excel_path)
            ws = wb.active
            
            # Append row
            trade_dict = trade.to_dict()
            row_data = [
                trade_dict['symbol'],
                trade_dict['side'],
                trade_dict['entry_time'],
                trade_dict['entry_price'],
                trade_dict['entry_order_id'],
                trade_dict['exit_time'],
                trade_dict['exit_price'],
                trade_dict['exit_order_id'],
                trade_dict['sl_price'],
                trade_dict['tp_price'],
                trade_dict['sl_type'],
                trade_dict['amount'],
                trade_dict['pnl_gross_pct'],
                trade_dict['pnl_net_pct'],
                trade_dict['grade'],
                trade_dict['note'],
                trade_dict['close_reason']
            ]
            ws.append(row_data)
            
            # Auto-adjust column widths (optional)
            for column in ws.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                ws.column_dimensions[column_letter].width = adjusted_width
            
            wb.save(excel_path)
        except Exception as e:
            self.log_event('ERROR', f"Failed to append to Excel: {e}")

# ===================== TELEGRAM INTEGRATION =====================

class TelegramNotifier:
    """Telegram notification service"""
    
    def __init__(self, api_config: APIConfig, logger: TradingLogger):
        self.token = api_config.telegram_token
        self.chat_id = api_config.telegram_chat_id
        self.logger = logger
    
    def send(self, message: str) -> bool:
        """
        Send message to Telegram
        
        Args:
            message: Message text
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.token or not self.chat_id:
                self.logger.log_event(
                    'WARNING',
                    "Telegram credentials missing",
                    has_token=bool(self.token),
                    has_chat_id=bool(self.chat_id)
                )
                return False
            
            url = f"https://api.telegram.org/bot{self.token}/sendMessage"
            response = requests.post(
                url,
                json={"chat_id": self.chat_id, "text": message},
                timeout=15
            )
            
            if response.status_code != 200:
                self.logger.log_event(
                    'WARNING',
                    "Telegram send failed",
                    status_code=response.status_code,
                    response=response.text[:200]
                )
                return False
            
            return True
            
        except Exception as e:
            self.logger.log_event('ERROR', f"Telegram exception: {e}")
            return False

# ===================== EXCHANGE CONNECTION =====================

class BinanceMarginClient:
    """Binance Margin Trading Client with robust error handling"""
    
    def __init__(self, api_config: APIConfig, trading_config: TradingConfig, logger: TradingLogger):
        self.api_config = api_config
        self.config = trading_config
        self.logger = logger
        
        # Initialize CCXT Binance client
        self.exchange = self._init_exchange()
        
        # Load markets with retry
        self._load_markets()
        
        # Check time sync
        self._check_time_sync()
    
    def _init_exchange(self) -> ccxt.binance:
        """Initialize CCXT Binance exchange"""
        try:
            exchange = ccxt.binance({
                "apiKey": self.api_config.api_key,
                "secret": self.api_config.api_secret,
                "enableRateLimit": True,
                "timeout": 60000,
                "options": {
                    "adjustForTimeDifference": True,
                    "recvWindow": 60000,
                    "fetchCurrencies": False,
                }
            })
            
            self.logger.log_event(
                'INFO',
                "Exchange initialized",
                api_key_len=len(self.api_config.api_key),
                has_secret=bool(self.api_config.api_secret)
            )
            
            return exchange
            
        except Exception as e:
            self.logger.log_event('CRITICAL', f"Failed to initialize exchange: {e}")
            raise
    
    def _load_markets(self, max_retries: int = 5):
        """Load markets with retry mechanism"""
        for attempt in range(max_retries):
            try:
                self.exchange.load_markets()
                self.logger.log_event('INFO', "Markets loaded successfully")
                return
            except Exception as e:
                wait_time = 3 + attempt * 3
                self.logger.log_event(
                    'WARNING',
                    f"Failed to load markets",
                    attempt=f"{attempt + 1}/{max_retries}",
                    retry_in=f"{wait_time}s",
                    error=str(e)
                )
                if attempt < max_retries - 1:
                    time.sleep(wait_time)
                else:
                    self.logger.log_event('CRITICAL', "Failed to load markets after all retries")
                    raise SystemExit(1)
    
    def _check_time_sync(self):
        """Check server time synchronization"""
        try:
            server_time = self.exchange.fetch_time()
            local_time = self.exchange.milliseconds()
            diff_ms = local_time - server_time
            
            self.logger.log_event(
                'INFO',
                "Time sync check",
                server_time=server_time,
                local_time=local_time,
                diff_ms=diff_ms
            )
            
            # Warn if difference is too large (>5 seconds)
            if abs(diff_ms) > 5000:
                self.logger.log_event(
                    'WARNING',
                    "Large time difference detected",
                    diff_seconds=diff_ms / 1000
                )
                
        except Exception as e:
            self.logger.log_event('WARNING', f"Time sync check failed: {e}")
    
    def fetch_ohlcv(
        self,
        symbol: str,
        timeframe: str,
        limit: int,
        max_retries: int = 4
    ) -> pd.DataFrame:
        """
        Fetch OHLCV data with retry mechanism
        
        Args:
            symbol: Trading pair symbol
            timeframe: Timeframe (e.g., '5m', '30m')
            limit: Number of candles to fetch
            max_retries: Maximum number of retries
            
        Returns:
            DataFrame with OHLCV data or empty DataFrame on failure
        """
        for attempt in range(max_retries):
            try:
                ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
                
                if not ohlcv:
                    raise Exception("Empty OHLCV data")
                
                df = pd.DataFrame(ohlcv, columns=["ts", "open", "high", "low", "close", "vol"])
                
                return df
                
            except Exception as e:
                wait_time = 3 + attempt * 3
                self.logger.log_event(
                    'WARNING',
                    f"Fetch OHLCV failed",
                    symbol=symbol,
                    timeframe=timeframe,
                    attempt=f"{attempt + 1}/{max_retries}",
                    retry_in=f"{wait_time}s",
                    error=str(e)[:200]
                )
                if attempt < max_retries - 1:
                    time.sleep(wait_time)
        
        self.logger.log_event('ERROR', f"Fetch OHLCV failed after all retries", symbol=symbol, timeframe=timeframe)
        return pd.DataFrame()
    
    def place_margin_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        amount: float,
        price: Optional[float] = None,
        params: Optional[Dict] = None
    ) -> Dict:
        """
        Place margin order with error handling
        
        Args:
            symbol: Trading pair
            side: 'buy' or 'sell'
            order_type: 'market' or 'limit'
            amount: Order amount
            price: Order price (for limit orders)
            params: Additional parameters
            
        Returns:
            Order response dictionary
        """
        try:
            if params is None:
                params = {}
            
            # Add margin trading specific parameters
            params['isMargin'] = True
            
            if self.config.mock_mode:
                self.logger.log_event(
                    'INFO',
                    "MOCK ORDER (not executed)",
                    symbol=symbol,
                    side=side,
                    type=order_type,
                    amount=amount,
                    price=price
                )
                # Return mock order
                return {
                    'id': f'mock_{int(time.time())}',
                    'orderId': f'mock_{int(time.time())}',
                    'symbol': symbol,
                    'side': side,
                    'type': order_type,
                    'amount': amount,
                    'price': price or 0,
                    'executedQty': str(amount),
                    'cummulativeQuoteQty': str(amount * (price or 0)),
                    'status': 'filled',
                    'timestamp': int(time.time() * 1000)
                }
            
            # Place real order
            order = self.exchange.create_order(
                symbol=symbol,
                type=order_type,
                side=side,
                amount=amount,
                price=price,
                params=params
            )
            
            self.logger.log_event(
                'INFO',
                "Order placed successfully",
                symbol=symbol,
                side=side,
                order_id=order.get('id'),
                amount=amount
            )
            
            return order
            
        except Exception as e:
            self.logger.log_event(
                'ERROR',
                f"Failed to place order: {e}",
                symbol=symbol,
                side=side,
                amount=amount
            )
            raise
    
    def get_cross_margin_account(self) -> Dict:
        """Get cross margin account information"""
        try:
            # Use SAPI endpoint for margin account
            account = self.exchange.sapi_get_margin_account()
            return account
        except Exception as e:
            self.logger.log_event('ERROR', f"Failed to get margin account: {e}")
            raise
    
    def to_binance_symbol(self, symbol: str) -> str:
        """Convert CCXT symbol to Binance format"""
        return symbol.replace("/", "")

# ===================== HELPER FUNCTIONS =====================

def find_swings(df: pd.DataFrame, lr: int = 2) -> Tuple[List[Tuple[int, float]], List[Tuple[int, float]]]:
    """
    Find swing highs and lows using fractal detection
    
    Args:
        df: DataFrame with OHLCV data
        lr: Look-around period (left and right)
        
    Returns:
        Tuple of (swing_highs, swing_lows) lists
    """
    highs = df["high"].astype(float).values
    lows = df["low"].astype(float).values
    swing_highs = []
    swing_lows = []
    
    for i in range(lr, len(df) - lr):
        h = highs[i]
        l = lows[i]
        
        # Check if it's a swing high
        if all(h > highs[i - k] for k in range(1, lr + 1)) and \
           all(h > highs[i + k] for k in range(1, lr + 1)):
            swing_highs.append((i, float(h)))
        
        # Check if it's a swing low
        if all(l < lows[i - k] for k in range(1, lr + 1)) and \
           all(l < lows[i + k] for k in range(1, lr + 1)):
            swing_lows.append((i, float(l)))
    
    return swing_highs, swing_lows

def candle_stats(row: pd.Series) -> Dict[str, Any]:
    """
    Calculate candle statistics
    
    Args:
        row: DataFrame row with OHLCV data
        
    Returns:
        Dictionary with candle statistics
    """
    o = float(row["open"])
    h = float(row["high"])
    l = float(row["low"])
    c = float(row["close"])
    rng = max(h - l, 1e-12)
    body = abs(c - o)
    
    return {
        "o": o,
        "h": h,
        "l": l,
        "c": c,
        "range": rng,
        "body_ratio": body / rng,
        "bull": c > o,
        "bear": c < o
    }

def detect_trend(
    swing_highs: List[Tuple[int, float]],
    swing_lows: List[Tuple[int, float]]
) -> str:
    """
    Detect trend based on swing highs and lows
    
    Args:
        swing_highs: List of swing highs
        swing_lows: List of swing lows
        
    Returns:
        "UP", "DOWN", or "NONE"
    """
    if len(swing_highs) < 2 or len(swing_lows) < 2:
        return "NONE"
    
    # Check for higher highs and higher lows
    if swing_highs[-1][1] > swing_highs[-2][1] and swing_lows[-1][1] > swing_lows[-2][1]:
        return "UP"
    
    # Check for lower highs and lower lows
    if swing_highs[-1][1] < swing_highs[-2][1] and swing_lows[-1][1] < swing_lows[-2][1]:
        return "DOWN"
    
    return "NONE"

def quantize_quantity(
    quantity: float,
    step_size: float,
    min_qty: float
) -> float:
    """
    Quantize quantity to match exchange requirements
    
    Args:
        quantity: Desired quantity
        step_size: Step size from exchange
        min_qty: Minimum quantity from exchange
        
    Returns:
        Quantized quantity
    """
    # Quantize to step size
    quantity_decimal = Decimal(str(quantity))
    step_decimal = Decimal(str(step_size))
    
    quantized = (quantity_decimal // step_decimal) * step_decimal
    quantized_float = float(quantized)
    
    # Ensure meets minimum
    if quantized_float < min_qty:
        return 0.0
    
    return quantized_float

# ===================== MOCK TESTING =====================

def test_mock_order_flow(
    config: TradingConfig,
    api_config: APIConfig,
    logger: TradingLogger
):
    """
    Test function to validate order flow without placing real orders
    
    This function tests:
    - Connection to Binance
    - Fetching market data
    - Order quantity calculation
    - Order placement (mock mode)
    """
    logger.log_event('INFO', "=" * 60)
    logger.log_event('INFO', "STARTING MOCK ORDER FLOW TEST")
    logger.log_event('INFO', "=" * 60)
    
    try:
        # Initialize client in mock mode
        test_config = TradingConfig()
        test_config.mock_mode = True
        
        client = BinanceMarginClient(api_config, test_config, logger)
        
        # Test 1: Fetch OHLCV data
        logger.log_event('INFO', "Test 1: Fetching OHLCV data...")
        test_symbol = "BTC/USDC"
        df = client.fetch_ohlcv(test_symbol, "5m", 100)
        
        if df.empty:
            logger.log_event('ERROR', "Test 1 FAILED: Empty DataFrame")
            return False
        
        logger.log_event('INFO', f"Test 1 PASSED: Fetched {len(df)} candles")
        
        # Test 2: Mock order placement
        logger.log_event('INFO', "Test 2: Placing mock LONG order...")
        mock_order = client.place_margin_order(
            symbol=test_symbol,
            side='buy',
            order_type='market',
            amount=0.001
        )
        
        if not mock_order or 'orderId' not in mock_order:
            logger.log_event('ERROR', "Test 2 FAILED: Invalid mock order response")
            return False
        
        logger.log_event('INFO', f"Test 2 PASSED: Mock order ID = {mock_order['orderId']}")
        
        # Test 3: Mock order placement (SHORT)
        logger.log_event('INFO', "Test 3: Placing mock SHORT order...")
        mock_order = client.place_margin_order(
            symbol=test_symbol,
            side='sell',
            order_type='market',
            amount=0.001
        )
        
        if not mock_order or 'orderId' not in mock_order:
            logger.log_event('ERROR', "Test 3 FAILED: Invalid mock order response")
            return False
        
        logger.log_event('INFO', f"Test 3 PASSED: Mock order ID = {mock_order['orderId']}")
        
        logger.log_event('INFO', "=" * 60)
        logger.log_event('INFO', "ALL TESTS PASSED")
        logger.log_event('INFO', "=" * 60)
        
        return True
        
    except Exception as e:
        logger.log_event('ERROR', f"Mock test failed: {e}")
        return False

# ===================== BINANCE-SPECIFIC FUNCTIONS =====================

def get_binance_filters(exchange: ccxt.binance, symbol: str) -> Tuple[float, float, float, Optional[int]]:
    """
    Get Binance market filters for a symbol
    
    Returns:
        Tuple of (step_size, min_qty, min_notional, quote_asset_precision)
    """
    m = exchange.markets.get(symbol)
    if not m:
        return 0.0, 0.0, 0.0, None
    
    info = m.get("info", {}) or {}
    filters = info.get("filters", []) or []
    
    step = 0.0
    min_qty = 0.0
    min_notional = 0.0
    quote_asset_prec = info.get("quoteAssetPrecision")
    
    for f in filters:
        ft = f.get("filterType")
        if ft == "LOT_SIZE":
            step = float(f.get("stepSize", 0.0) or 0.0)
            min_qty = float(f.get("minQty", 0.0) or 0.0)
        if ft in ("MIN_NOTIONAL", "NOTIONAL"):
            mn = f.get("minNotional") or f.get("notional")
            if mn is not None:
                min_notional = float(mn)
    
    return step, min_qty, min_notional, quote_asset_prec

def decimals_from_step(step: float) -> int:
    """Calculate decimal places from step size"""
    if not step or step <= 0:
        return 8
    s = f"{step:.20f}".rstrip("0")
    return len(s.split(".")[1]) if "." in s else 0

def quantize_down_str(value: float, decimals: int) -> str:
    """Quantize value to specified decimal places, rounding down"""
    d = Decimal(str(value))
    q = Decimal("1e-" + str(decimals))
    return format(d.quantize(q, rounding=ROUND_DOWN), "f")

def format_quantity(exchange: ccxt.binance, symbol: str, qty: float) -> str:
    """Format quantity according to exchange filters"""
    step, min_qty, _, _ = get_binance_filters(exchange, symbol)
    if qty <= 0:
        return "0"
    
    if step and step > 0:
        q = math.floor(qty / step) * step
    else:
        q = qty
    
    if min_qty and q < min_qty:
        q = min_qty
    
    dec = decimals_from_step(step) if step and step > 0 else 8
    return quantize_down_str(q, dec)

def format_quote(exchange: ccxt.binance, symbol: str, quote: float, min_notional_pad: float = 1.05) -> str:
    """Format quote quantity according to exchange filters"""
    _, _, min_notional, quote_prec = get_binance_filters(exchange, symbol)
    q = float(quote)
    
    if min_notional and q < min_notional:
        q = float(min_notional) * min_notional_pad
    
    dec = int(quote_prec) if quote_prec is not None else 6
    return quantize_down_str(q, dec)

def calculate_amount_from_usdc(
    exchange: ccxt.binance,
    symbol: str,
    usdc_target: float,
    ref_price: float,
    min_notional_pad: float = 1.05
) -> float:
    """Calculate base asset amount from USDC target"""
    step, min_qty, min_notional, _ = get_binance_filters(exchange, symbol)
    
    target = float(usdc_target)
    if min_notional and target < min_notional:
        target = min_notional * min_notional_pad
    
    amt = target / max(ref_price, 1e-12)
    
    if step and step > 0:
        amt = math.floor(amt / step) * step
    
    if min_qty and amt < min_qty:
        amt = min_qty
    
    return float(amt)

# ===================== ADVANCED TRADING FUNCTIONS =====================

def avg_range(df: pd.DataFrame, n: int) -> float:
    """Calculate average range of candles"""
    rng = (df["high"].astype(float) - df["low"].astype(float)).tail(n)
    return float(rng.mean()) if len(rng) else 0.0

def ema(series: pd.Series, span: int) -> pd.Series:
    """Calculate Exponential Moving Average"""
    return series.ewm(span=span, adjust=False).mean()

def atr(df: pd.DataFrame, n: int = 14) -> pd.Series:
    """Calculate Average True Range"""
    h = df["high"].astype(float)
    l = df["low"].astype(float)
    c = df["close"].astype(float)
    prev_c = c.shift(1)
    tr = pd.concat([(h - l), (h - prev_c).abs(), (l - prev_c).abs()], axis=1).max(axis=1)
    return tr.rolling(n).mean()

def get_bias(df_bias: pd.DataFrame, swing_lr: int = 2) -> str:
    """
    Get bias from timeframe using BOS and CHoCH logic
    
    Returns:
        "UP", "DOWN", or "NONE"
    """
    sh, sl = find_swings(df_bias, lr=swing_lr)
    trend = detect_trend(sh, sl)
    
    if trend == "NONE" or len(sh) < 2 or len(sl) < 2:
        return "NONE"
    
    last_close = float(df_bias["close"].astype(float).iloc[-1])
    prev_sh = float(sh[-2][1])
    prev_sl = float(sl[-2][1])
    
    if trend == "UP":
        if last_close > prev_sh:
            return "UP"  # BOS
        if last_close < prev_sl:
            return "DOWN"  # CHoCH
        return "NONE"
    
    if trend == "DOWN":
        if last_close < prev_sl:
            return "DOWN"  # BOS
        if last_close > prev_sh:
            return "UP"  # CHoCH
        return "NONE"
    
    return "NONE"

def latest_entry_swings(df_entry: pd.DataFrame, swing_lr: int = 2) -> Optional[Dict[str, float]]:
    """Get latest swing highs and lows from entry timeframe"""
    sh, sl = find_swings(df_entry, lr=swing_lr)
    if not sh or not sl:
        return None
    return {"swing_high": float(sh[-1][1]), "swing_low": float(sl[-1][1])}

def detect_bullish_fvg(df: pd.DataFrame, idx: int, min_size_pct: float = 0.00010) -> Optional[Dict[str, float]]:
    """Detect bullish Fair Value Gap"""
    if idx < 2:
        return None
    c1 = candle_stats(df.iloc[idx-2])
    c3 = candle_stats(df.iloc[idx])
    bot = c1["h"]
    top = c3["l"]
    if bot < top:
        mid = float(df.iloc[idx]["close"])
        if (top - bot) / max(mid, 1e-12) >= min_size_pct:
            return {"low": bot, "high": top}
    return None

def detect_bearish_fvg(df: pd.DataFrame, idx: int, min_size_pct: float = 0.00010) -> Optional[Dict[str, float]]:
    """Detect bearish Fair Value Gap"""
    if idx < 2:
        return None
    c1 = candle_stats(df.iloc[idx-2])
    c3 = candle_stats(df.iloc[idx])
    low = c3["h"]
    high = c1["l"]
    if low < high:
        mid = float(df.iloc[idx]["close"])
        if (high - low) / max(mid, 1e-12) >= min_size_pct:
            return {"low": low, "high": high}
    return None

def find_order_block(df: pd.DataFrame, disp_idx: int, side: str, lookback: int = 6) -> Optional[Dict]:
    """Find order block before displacement candle"""
    start = max(0, disp_idx - lookback)
    for j in range(disp_idx - 1, start - 1, -1):
        c = candle_stats(df.iloc[j])
        if side == "LONG" and c["bear"]:
            return {"low": c["l"], "high": c["h"], "idx": j}
        if side == "SHORT" and c["bull"]:
            return {"low": c["l"], "high": c["h"], "idx": j}
    return None

def zone_touched(candle: Dict, zone: Dict) -> bool:
    """Check if candle touches a zone"""
    return (candle["h"] >= zone["low"]) and (candle["l"] <= zone["high"])

# ===================== POSITION MANAGEMENT =====================

class PositionManager:
    """Manage open positions and pending setups"""
    
    def __init__(
        self,
        client: BinanceMarginClient,
        config: TradingConfig,
        logger: TradingLogger,
        telegram: TelegramNotifier
    ):
        self.client = client
        self.config = config
        self.logger = logger
        self.telegram = telegram
        self.positions: Dict[str, Position] = {}
        self.pending: Dict[str, PendingSetup] = {}
        self.trade_records: List[TradeRecord] = []
    
    def open_position(
        self,
        symbol: str,
        side: str,
        entry_ref: float,
        sl_price: float,
        sl_type: str,
        tp_price: float,
        note: str = ""
    ) -> bool:
        """
        Open a new position
        
        Returns:
            True if successful, False otherwise
        """
        if len(self.positions) >= self.config.max_open_positions:
            self.logger.log_event(
                'WARNING',
                f"Max positions reached",
                symbol=symbol,
                max_positions=self.config.max_open_positions
            )
            return False
        
        real_entry = float(entry_ref)
        amount = None
        entry_order_id = None
        
        # Calculate tp_pct for TP ladder
        tp_pct = abs((float(tp_price) - float(entry_ref)) / max(float(entry_ref), 1e-12))
        
        if self.config.live_trading:
            try:
                # Place entry order
                order, filled_qty = self._place_entry_market(symbol, side, float(entry_ref))
                amount = float(filled_qty)
                entry_order_id = order.get("orderId") or order.get("id")
                
                # Calculate real entry from filled order
                exec_qty = float(order.get("executedQty", 0.0) or 0.0)
                cum_quote = float(order.get("cummulativeQuoteQty", 0.0) or 0.0)
                if exec_qty > 0 and cum_quote > 0:
                    real_entry = cum_quote / exec_qty
                
                # Recalculate TP and SL based on real entry
                if side == "LONG":
                    tp_price = real_entry * (1 + tp_pct)
                else:
                    tp_price = real_entry * (1 - tp_pct)
                
                sl_pct = (float(sl_price) - float(entry_ref)) / float(entry_ref)
                sl_price = real_entry * (1.0 + sl_pct)
                
                self.logger.log_event(
                    'INFO',
                    "LIVE ENTRY OK",
                    symbol=symbol,
                    side=side,
                    order_id=entry_order_id,
                    executed_qty=order.get('executedQty'),
                    real_entry=real_entry,
                    tp=tp_price,
                    sl=sl_price,
                    sl_type=sl_type
                )
                
            except Exception as e:
                self.logger.log_event('ERROR', f"Entry failed: {e}", symbol=symbol, side=side)
                return False
        
        # Create position
        position = Position(
            symbol=symbol,
            side=side,
            entry=float(real_entry),
            sl=float(sl_price),
            sl_type=str(sl_type),
            tp=float(tp_price),
            tp_pct=float(tp_pct),
            note=note,
            amount=float(amount) if amount else None,
            entry_order_id=entry_order_id,
            entry_time=datetime.now()
        )
        
        self.positions[symbol] = position
        
        # Calculate percentages for message
        sl_pct_abs = abs((float(real_entry) - float(sl_price)) / max(float(real_entry), 1e-12)) * 100.0
        tp_pct_abs = abs((float(tp_price) - float(real_entry)) / max(float(real_entry), 1e-12)) * 100.0
        
        # Log to trade records
        trade_record = TradeRecord(
            symbol=symbol,
            side=side,
            entry_time=datetime.now(),
            entry_price=float(real_entry),
            entry_order_id=entry_order_id,
            sl_price=float(sl_price),
            tp_price=float(tp_price),
            sl_type=str(sl_type),
            amount=float(amount) if amount else 0.0,
            note=note
        )
        
        self.logger.log_trade_open(trade_record)
        
        # Send Telegram notification
        self.telegram.send(
            f"🟢 OPEN {side} {symbol}\n{note}\n"
            f"Entry {real_entry:.6f} (ref {float(entry_ref):.6f})\n"
            f"TP {float(tp_price):.6f} ({tp_pct_abs:.2f}%)\n"
            f"SL {float(sl_price):.6f} ({sl_pct_abs:.2f}%) | {sl_type}\n"
            f"Size target {self.config.trade_usdc_target} USDC"
        )
        
        return True
    
    def close_position(
        self,
        symbol: str,
        exit_price: float,
        reason: str
    ) -> bool:
        """
        Close an existing position
        
        Returns:
            True if successful, False otherwise
        """
        if symbol not in self.positions:
            self.logger.log_event('WARNING', f"Position not found", symbol=symbol)
            return False
        
        pos = self.positions[symbol]
        side = pos.side
        tracked_amt = float(pos.amount or 0.0)
        
        if self.config.live_trading:
            try:
                if side == "LONG":
                    # For LONG, close by selling base asset
                    real_base_free = self._get_cross_base_free(symbol)
                    qty_to_close = min(real_base_free, tracked_amt) if tracked_amt > 0 else real_base_free
                    
                    if qty_to_close > 0:
                        resp = self._place_close_market(symbol, side, qty_to_close)
                        self.logger.log_event(
                            'INFO',
                            "LIVE CLOSE OK",
                            symbol=symbol,
                            side=side,
                            order_id=resp.get('orderId'),
                            executed_qty=resp.get('executedQty')
                        )
                    else:
                        self.logger.log_event(
                            'WARNING',
                            "Position already closed (base=0)",
                            symbol=symbol
                        )
                        del self.positions[symbol]
                        return True
                
                else:  # SHORT
                    if tracked_amt <= 0:
                        self.logger.log_event('WARNING', f"Missing amount for SHORT", symbol=symbol)
                        return False
                    resp = self._place_close_market(symbol, side, tracked_amt)
                    self.logger.log_event(
                        'INFO',
                        "LIVE CLOSE OK",
                        symbol=symbol,
                        side=side,
                        order_id=resp.get('orderId'),
                        executed_qty=resp.get('executedQty')
                    )
                
            except Exception as e:
                self.logger.log_event('ERROR', f"Close failed: {e}", symbol=symbol, side=side)
                return False
        
        # Calculate PnL
        entry = float(pos.entry)
        if side == "LONG":
            pnl_gross = (exit_price - entry) / entry
        else:
            pnl_gross = (entry - exit_price) / entry
        
        pnl_net_est = pnl_gross - self.config.round_trip_fee_pct
        
        # Update trade record
        trade_record = TradeRecord(
            symbol=symbol,
            side=side,
            entry_time=pos.entry_time or datetime.now(),
            entry_price=float(pos.entry),
            entry_order_id=pos.entry_order_id,
            exit_time=datetime.now(),
            exit_price=float(exit_price),
            sl_price=float(pos.sl),
            tp_price=float(pos.tp),
            sl_type=pos.sl_type,
            amount=float(pos.amount or 0.0),
            pnl_gross_pct=float(pnl_gross * 100),
            pnl_net_pct=float(pnl_net_est * 100),
            grade="WIN" if pnl_net_est > 0 else "LOSS",
            note=pos.note,
            close_reason=reason
        )
        
        self.logger.log_trade_close(trade_record)
        
        # Send Telegram notification
        self.telegram.send(
            f"🔴 CLOSE {symbol} ({reason})\n"
            f"PNL gross {pnl_gross*100:.2f}% | net(est) {pnl_net_est*100:.2f}%\n"
            f"SL_TYPE: {pos.sl_type}"
        )
        
        del self.positions[symbol]
        return True
    
    def _place_entry_market(self, symbol: str, side: str, ref_price: float) -> Tuple[Dict, float]:
        """Place entry market order"""
        bsym = self.client.to_binance_symbol(symbol)
        
        if side == "LONG":
            params = {
                "symbol": bsym,
                "side": "BUY",
                "type": "MARKET",
                "sideEffectType": "MARGIN_BUY",
                "quoteOrderQty": format_quote(
                    self.client.exchange,
                    symbol,
                    float(self.config.trade_usdc_target),
                    self.config.min_notional_pad
                ),
                "timestamp": self.client.exchange.milliseconds(),
                "recvWindow": 60000,
            }
            order = self.client.exchange.sapiPostMarginOrder(params)
            filled_qty = float(order.get("executedQty") or 0.0)
            return order, filled_qty
        
        else:  # SHORT
            amount = calculate_amount_from_usdc(
                self.client.exchange,
                symbol,
                float(self.config.trade_usdc_target),
                ref_price,
                self.config.min_notional_pad
            )
            params = {
                "symbol": bsym,
                "side": "SELL",
                "type": "MARKET",
                "quantity": format_quantity(self.client.exchange, symbol, amount),
                "sideEffectType": "AUTO_BORROW_REPAY",
                "timestamp": self.client.exchange.milliseconds(),
                "recvWindow": 60000,
            }
            order = self.client.exchange.sapiPostMarginOrder(params)
            filled_qty = float(order.get("executedQty") or amount)
            return order, filled_qty
    
    def _place_close_market(self, symbol: str, side: str, amount: float) -> Dict:
        """Place close market order"""
        bsym = self.client.to_binance_symbol(symbol)
        if amount <= 0:
            raise Exception("amount<=0 in close")
        
        params = {
            "symbol": bsym,
            "type": "MARKET",
            "quantity": format_quantity(self.client.exchange, symbol, float(amount)),
            "sideEffectType": "AUTO_REPAY",
            "timestamp": self.client.exchange.milliseconds(),
            "recvWindow": 60000,
        }
        params["side"] = "SELL" if side == "LONG" else "BUY"
        return self.client.exchange.sapiPostMarginOrder(params)
    
    def _get_cross_base_free(self, symbol: str) -> float:
        """Get free base asset balance from cross margin account"""
        base = symbol.split("/")[0].strip().upper()
        try:
            data = self.client.exchange.sapiGetMarginAccount({
                "timestamp": self.client.exchange.milliseconds(),
                "recvWindow": 60000
            })
            assets = data.get("userAssets") or []
            for a in assets:
                if (a.get("asset") or "").upper() == base:
                    return float(a.get("free", 0.0) or 0.0)
            return 0.0
        except Exception as e:
            self.logger.log_event('WARNING', f"Cannot fetch cross margin balance: {e}", symbol=symbol)
            return 0.0

# ===================== MAIN TRADING LOGIC =====================

def main():
    """Main entry point for the trading bot"""
    # Load configuration
    config = TradingConfig()
    api_config = APIConfig.from_env()
    
    # Initialize logging
    logger = TradingLogger(config)
    
    logger.log_event('INFO', "=" * 80)
    logger.log_event('INFO', "ICT SMART MONEY BOT v10.0 - LIVE CROSS MARGIN")
    logger.log_event('INFO', "=" * 80)
    
    # Initialize Telegram
    telegram = TelegramNotifier(api_config, logger)
    telegram.send("✅ Crypto ICT bot avviato (v10.0 LIVE Cross Margin)")
    
    # Run mock tests if in test mode
    if config.mock_mode:
        logger.log_event('INFO', "Running in MOCK MODE")
        test_mock_order_flow(config, api_config, logger)
        return
    
    # Initialize exchange client
    client = BinanceMarginClient(api_config, config, logger)
    
    logger.log_event(
        'INFO',
        "Configuration loaded",
        live_trading=config.live_trading,
        max_positions=config.max_open_positions,
        symbols=len(config.symbols)
    )
    
    # Initialize position manager
    position_mgr = PositionManager(client, config, logger, telegram)
    
    # Trading loop counter
    loop_count = 0
    
    # Main trading loop
    logger.log_event('INFO', "Starting main trading loop...")
    
    while True:
        try:
            loop_count += 1
            
            # Heartbeat logging
            if loop_count % config.heartbeat_every_loops == 0:
                logger.log_event(
                    'INFO',
                    "Heartbeat",
                    loop=loop_count,
                    open_positions=len(position_mgr.positions),
                    pending_setups=len(position_mgr.pending)
                )
            
            # 1. Check existing positions (SL/TP management)
            for symbol in list(position_mgr.positions.keys()):
                try:
                    pos = position_mgr.positions[symbol]
                    
                    # Fetch current candle
                    df = client.fetch_ohlcv(symbol, config.entry_tf, 2)
                    if df.empty:
                        continue
                    
                    last_candle = df.iloc[-1]
                    high = float(last_candle["high"])
                    low = float(last_candle["low"])
                    close = float(last_candle["close"])
                    
                    # Check SL hit
                    if pos.side == "LONG":
                        if low <= pos.sl:
                            position_mgr.close_position(symbol, pos.sl, "SL_HIT")
                            continue
                    else:  # SHORT
                        if high >= pos.sl:
                            position_mgr.close_position(symbol, pos.sl, "SL_HIT")
                            continue
                    
                    # Check TP hit (basic - no ladder in this simplified version)
                    if pos.side == "LONG":
                        if high >= pos.tp:
                            position_mgr.close_position(symbol, pos.tp, "TP_HIT")
                            continue
                    else:  # SHORT
                        if low <= pos.tp:
                            position_mgr.close_position(symbol, pos.tp, "TP_HIT")
                            continue
                    
                except Exception as e:
                    logger.log_event('ERROR', f"Error managing position: {e}", symbol=symbol)
            
            # 2. Scan for new setups (simplified version)
            # In a full implementation, this would include:
            # - Fetch bias from 30m timeframe
            # - Detect sweep/displacement/retrace/confirm on 5m
            # - Apply BTC filters
            # - Check room to TP
            # - Calculate structural SL
            # - Open positions
            
            # For now, just log that we're scanning
            if loop_count % config.heartbeat_every_loops == 0:
                logger.log_event(
                    'DEBUG',
                    "Scanning for new setups",
                    active_symbols=len(config.symbols),
                    open_positions=len(position_mgr.positions)
                )
            
            time.sleep(config.loop_sec)
            
        except KeyboardInterrupt:
            logger.log_event('WARNING', "Bot stopped manually by user")
            telegram.send("🛑 Bot stoppato manualmente.")
            break
            
        except Exception as e:
            logger.log_event('ERROR', f"Main loop error: {e}")
            time.sleep(config.loop_sec)
    
    logger.log_event('INFO', "Bot shutdown complete")

if __name__ == "__main__":
    main()
