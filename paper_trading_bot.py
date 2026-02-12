#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Paper Trading Bot - Simulatore di Trading per Criptovalute
Versione: 2.0 - ICT Bias Detection System
Descrizione: Bot per trading simulato con logica ICT avanzata
"""

import os
import time
import json
import csv
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_DOWN
import ccxt
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import xlsxwriter
from collections import defaultdict

# ===================== CONFIGURAZIONE =====================
CONFIG = {
    # Capitale iniziale
    "INITIAL_CAPITAL": 10000.0,  # $10,000 USDC simulati
    
    # Exchange e Mercati
    "EXCHANGE": "binance",
    "SYMBOLS": [
        # Top coppie USDC per liquidità e market cap
        "BTC/USDC",   # Bitcoin
        "ETH/USDC",   # Ethereum
        "BNB/USDC",   # Binance Coin
        "SOL/USDC",   # Solana
        "XRP/USDC",   # Ripple
        "ADA/USDC",   # Cardano
        "DOGE/USDC",  # Dogecoin
        "AVAX/USDC",  # Avalanche
        "DOT/USDC",   # Polkadot
        "MATIC/USDC", # Polygon
        "LTC/USDC",   # Litecoin
        "LINK/USDC",  # Chainlink
        "UNI/USDC",   # Uniswap
        "ATOM/USDC",  # Cosmos
    ],  # 14 coppie USDC alta liquidità
    
    # API Keys (per LIVE mode)
    "API_KEY": "",  # Inserire API key Binance per live trading
    "API_SECRET": "",  # Inserire API secret Binance per live trading
    
    # Trading Mode
    "MODE": "PAPER",  # "PAPER" (simulazione) o "LIVE" (real trading)
    "LIVE_TRADING_ENABLED": False,  # Flag sicurezza per live trading
    "REQUIRE_CONFIRMATION": True,  # Richiedi conferma prima di ogni trade in LIVE
    
    # Margin Trading Settings
    "MARGIN_TYPE": "cross",  # "cross" o "isolated"
    "MAX_LEVERAGE": 3.0,  # Leverage massimo (3x = conservativo)
    "MIN_MARGIN_LEVEL": 1.5,  # Margin level minimo (1.5 = 150% collateral)
    "LIQUIDATION_BUFFER_PCT": 0.10,  # Buffer % per alert liquidazione
    "DAILY_INTEREST_RATE": 0.0002,  # ~0.02% daily interest (varia per coin)
    
    # Timeframes ICT
    "HTF": "15m",  # Higher TimeFrame per BIAS
    "LTF": "5m",   # Lower TimeFrame per ENTRY
    
    # Swing Detection (Fractal)
    "SWING_LEFT_RIGHT": 2,  # Barre a sinistra e destra per frattale
    
    # HTF Lookback
    "HTF_LOOKBACK": 100,  # Barre HTF da analizzare
    "LTF_LOOKBACK": 200,  # Barre LTF da analizzare
    
    # Bias Determination
    "COMPRESSION_THRESHOLD": 1.2,  # Soglia ATR per compressione
    "ATR_PERIOD": 14,  # Periodo ATR
    "MIN_BODY_RATIO": 0.5,  # Corpo minimo per break valido
    "RANGE_BARS_LIMIT": 10,  # Barre consecutive in range per bias NONE
    
    # Sweep Detection (STEP 2)
    "SWEEP_MIN_DIST_MULT": 0.10,  # Min sweep distance = ATR * 0.10
    "SWEEP_RECLAIM_MULT": 0.02,   # Reclaim buffer = ATR * 0.02
    "SWEEP_WICK_RATIO": 1.2,      # Wick deve essere >= body * 1.2
    "SWEEP_POOL_SIGNIFICANCE": 0.5,  # Pool deve essere > ATR * 0.5 di distanza
    
    # Displacement Detection (STEP 3)
    "DISPLACEMENT_BOS_BUFFER": 0.02,    # BOS buffer = ATR * 0.02
    "DISPLACEMENT_IMPULSE_MULT": 0.80,  # Impulso = range >= ATR * 0.80
    "DISPLACEMENT_BODY_RATIO": 0.55,    # Body dominance >= 55%
    "MAX_BARS_AFTER_SWEEP": 6,          # Timeout dopo sweep (barre M15)
    
    # Retrace Detection (STEP 4)
    "MAX_RETRACE_BARS": 8,              # Max barre M15 per retrace
    "RETRACE_INVALIDATION_MULT": 0.05,  # Invalidation buffer = ATR * 0.05
    "RETRACE_ZONE_MIN": 0.50,           # 50% del displacement range
    "RETRACE_ZONE_MAX": 0.79,           # 79% del displacement range
    
    # Confirmation Detection (STEP 5) - M5
    "MAX_CONFIRM_BARS": 12,             # Max barre M5 per confirmation (~60 min)
    "CONFIRM_ZONE_BUFFER": 0.25,        # Zone buffer = ATR M5 * 0.25
    "CONFIRM_BOS_BUFFER": 0.02,         # Micro BOS buffer = ATR M5 * 0.02
    "CONFIRM_IMPULSE_MULT": 0.60,       # Impulso M5 = range >= ATR M5 * 0.60
    "CONFIRM_BODY_RATIO": 0.50,         # Body dominance M5 >= 50%
    
    # Entry Logic (Final Step)
    "MAX_ENTRY_BARS": 6,                # Max barre M5 per entry dopo confirm
    "ENTRY_RETRACE_PCT": 0.50,          # Entry al 50% della candela confirm
    
    # Risk Management (Structural)
    "RISK_PER_TRADE": 0.02,             # 2% del capitale per trade
    "SL_ATR_BUFFER": 0.05,              # Stop Loss buffer = ATR M15 * 0.05
    "TP_RISK_MULTIPLE": 2.0,            # Take Profit = 2R (2x risk)
    
    # Limiti
    "MAX_POSITIONS": 2,  # Massimo 2 posizioni aperte contemporaneamente
    
    # Loop
    "LOOP_INTERVAL": 60,  # Secondi tra ogni ciclo (1 minuto per M5)
    
    # Logging
    "TRADES_LOG": "paper_trades.csv",
    "BALANCE_LOG": "paper_balance.csv",
    "BIAS_LOG": "paper_bias_log.csv",
    "ICT_SIGNALS_LOG": "ict_signals.csv",
    "DEBUG_LOG": "paper_trading_debug.log",
    "EXCEL_REPORT": "paper_trading_report.xlsx",
    "EXPORT_EXCEL_EVERY_N_TRADES": 10,  # Export Excel ogni 10 trade
    
    # Telegram (opzionale)
    "TELEGRAM_ENABLED": False,
}


# ===================== LOGGING SETUP =====================
def setup_logging():
    """Configura sistema di logging avanzato"""
    # Crea logger
    logger = logging.getLogger('PaperTradingBot')
    logger.setLevel(logging.DEBUG)
    
    # Rimuovi handler esistenti
    logger.handlers = []
    
    # Console handler (INFO e superiori)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_format = logging.Formatter(
        '%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_format)
    
    # File handler rotativo (DEBUG e superiori)
    file_handler = RotatingFileHandler(
        CONFIG["DEBUG_LOG"],
        maxBytes=10*1024*1024,  # 10 MB
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    file_format = logging.Formatter(
        '%(asctime)s [%(levelname)s] %(funcName)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_format)
    
    # Aggiungi handlers
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger

# Inizializza logger globale
logger = setup_logging()


# ===================== ICT SIGNALS LOGGER =====================
class ICTSignalLogger:
    """Logger dedicato per segnali ICT"""
    
    def __init__(self):
        self.signals = []
    
    def log_signal(self, timestamp, symbol, timeframe, step, result, grade=None, details=None):
        """Registra un segnale ICT"""
        signal = {
            "timestamp": timestamp,
            "symbol": symbol,
            "timeframe": timeframe,
            "step": step,  # BIAS, SWEEP, DISPLACEMENT, RETRACE, CONFIRM, ENTRY
            "result": result,  # VALID, INVALID, WAIT, EXPIRED, HIT, CONFIRMED
            "grade": grade,  # A, B, None
            "details": json.dumps(details) if details else ""
        }
        self.signals.append(signal)
        
        # Log su file CSV
        self._save_to_csv(signal)
        
        # Log dettagliato
        logger.debug(f"ICT Signal: {step} - {result} (Grade: {grade}) | {symbol} {timeframe}")
    
    def _save_to_csv(self, signal):
        """Salva segnale su CSV"""
        file_exists = os.path.isfile(CONFIG["ICT_SIGNALS_LOG"])
        
        with open(CONFIG["ICT_SIGNALS_LOG"], "a", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=[
                "timestamp", "symbol", "timeframe", "step", "result", "grade", "details"
            ])
            
            if not file_exists:
                writer.writeheader()
            
            writer.writerow(signal)
    
    def get_signals(self):
        """Ritorna tutti i segnali registrati"""
        return self.signals

# Inizializza ICT signal logger globale
ict_logger = ICTSignalLogger()


# ===================== ICT STATE MACHINE =====================
class ICTSetupState:
    """State machine per tracking setup ICT multi-candela
    
    Stati possibili:
    - WAIT_BIAS: In attesa di bias direzionale
    - WAIT_SWEEP: Bias trovato, cerca liquidity sweep
    - WAIT_DISPLACEMENT: Sweep trovato, cerca displacement (BOS + impulso)
    - WAIT_RETRACE: Displacement trovato, cerca retrace in zona
    - WAIT_CONFIRMATION: Retrace hit, cerca confirmation su M5
    - SETUP_COMPLETE: Confirmation trovata, pronto per entry
    """
    
    def __init__(self, symbol: str):
        self.symbol = symbol
        self.status = "WAIT_BIAS"
        self.last_update = datetime.now()
        
        # STEP 0: BIAS
        self.bias = None
        self.bias_timestamp = None
        
        # STEP 1: SWEEP
        self.sweep_data = None
        self.sweep_bar_index = None  # Index della barra dove sweep trovato
        self.sweep_timestamp = None
        
        # STEP 2: DISPLACEMENT
        self.displacement_data = None
        self.displacement_bar_index = None
        self.displacement_timestamp = None
        
        # STEP 3: RETRACE
        self.retrace_data = None
        self.retrace_bar_index = None
        self.retrace_timestamp = None
        
        # STEP 4: CONFIRMATION
        self.confirmation_data = None
        self.confirmation_bar_index = None  # Index su M5!
        self.confirmation_timestamp = None
        
        # COUNTERS (CRITICAL per timeout!)
        self.bars_since_bias = 0
        self.bars_since_sweep = 0
        self.bars_since_displacement = 0
        self.bars_since_retrace = 0
        self.bars_since_confirmation = 0
        
        # HISTORY per invalidation check
        self.last_displacement_high = None
        self.last_displacement_low = None
    
    def transition(self, new_status: str, reason: str = "") -> str:
        """Transizione a nuovo stato"""
        old_status = self.status
        self.status = new_status
        self.last_update = datetime.now()
        
        if old_status != new_status:
            logger.info(f"[{self.symbol}] STATE: {old_status} → {new_status} ({reason})")
        
        return new_status
    
    def reset(self, to_status: str = "WAIT_BIAS", reason: str = "") -> None:
        """Reset completo o parziale dello stato"""
        logger.warning(f"[{self.symbol}] RESET to {to_status} - {reason}")
        
        if to_status == "WAIT_BIAS":
            # Reset totale
            self.__init__(self.symbol)
        
        elif to_status == "WAIT_SWEEP":
            # Reset da SWEEP in poi (mantiene BIAS)
            self.sweep_data = None
            self.sweep_bar_index = None
            self.sweep_timestamp = None
            self.displacement_data = None
            self.displacement_bar_index = None
            self.displacement_timestamp = None
            self.retrace_data = None
            self.retrace_bar_index = None
            self.retrace_timestamp = None
            self.confirmation_data = None
            self.confirmation_bar_index = None
            self.confirmation_timestamp = None
            
            self.bars_since_sweep = 0
            self.bars_since_displacement = 0
            self.bars_since_retrace = 0
            self.bars_since_confirmation = 0
            
            self.last_displacement_high = None
            self.last_displacement_low = None
            
            self.status = "WAIT_SWEEP"
        
        elif to_status == "WAIT_DISPLACEMENT":
            # Reset da DISPLACEMENT in poi (mantiene BIAS e SWEEP)
            self.displacement_data = None
            self.displacement_bar_index = None
            self.displacement_timestamp = None
            self.retrace_data = None
            self.retrace_bar_index = None
            self.retrace_timestamp = None
            self.confirmation_data = None
            self.confirmation_bar_index = None
            self.confirmation_timestamp = None
            
            self.bars_since_displacement = 0
            self.bars_since_retrace = 0
            self.bars_since_confirmation = 0
            
            self.last_displacement_high = None
            self.last_displacement_low = None
            
            self.status = "WAIT_DISPLACEMENT"
    
    def increment_counters(self) -> None:
        """Incrementa counter basato su stato corrente (chiamato ogni iterazione M15)"""
        if self.status == "WAIT_SWEEP":
            self.bars_since_bias += 1
        elif self.status == "WAIT_DISPLACEMENT":
            self.bars_since_sweep += 1
        elif self.status == "WAIT_RETRACE":
            self.bars_since_displacement += 1
        elif self.status == "WAIT_CONFIRMATION":
            self.bars_since_retrace += 1
        elif self.status == "SETUP_COMPLETE":
            self.bars_since_confirmation += 1
    
    def get_age_description(self) -> str:
        """Descrizione età del setup corrente"""
        if self.status == "WAIT_BIAS":
            return "N/A"
        elif self.status == "WAIT_SWEEP":
            return f"{self.bars_since_bias} bars"
        elif self.status == "WAIT_DISPLACEMENT":
            return f"{self.bars_since_sweep} bars"
        elif self.status == "WAIT_RETRACE":
            return f"{self.bars_since_displacement} bars"
        elif self.status == "WAIT_CONFIRMATION":
            return f"{self.bars_since_retrace} bars M15"
        elif self.status == "SETUP_COMPLETE":
            return f"{self.bars_since_confirmation} bars M5"
        return "N/A"


class ICTStateManager:
    """Manager per stati di tutte le coppie"""
    
    def __init__(self):
        self.states = {}  # {symbol: ICTSetupState}
        self.stats = {
            "transitions_today": 0,
            "resets_today": 0,
            "setups_complete_today": 0,
            "timeouts_today": 0,
            "invalidations_today": 0
        }
    
    def get_state(self, symbol: str) -> ICTSetupState:
        """Get or create state per symbol"""
        if symbol not in self.states:
            self.states[symbol] = ICTSetupState(symbol)
            logger.info(f"Created new ICT state for {symbol}")
        return self.states[symbol]
    
    def increment_all_counters(self) -> None:
        """Incrementa counter per TUTTE le coppie (chiamato ogni iterazione)"""
        for symbol, state in self.states.items():
            state.increment_counters()
    
    def get_summary(self) -> Dict:
        """Summary stati di tutte le coppie"""
        summary = {}
        for symbol, state in self.states.items():
            summary[symbol] = {
                "status": state.status,
                "bias": state.bias if state.bias else "NONE",
                "age": state.get_age_description()
            }
        return summary
    
    def get_hot_setups(self) -> List[str]:
        """Ritorna simboli con setup near completion (WAIT_CONFIRMATION o SETUP_COMPLETE)"""
        hot = []
        for symbol, state in self.states.items():
            if state.status in ["WAIT_CONFIRMATION", "SETUP_COMPLETE"]:
                hot.append(symbol)
        return hot
    
    def reset_daily_stats(self) -> None:
        """Reset statistiche giornaliere"""
        self.stats = {
            "transitions_today": 0,
            "resets_today": 0,
            "setups_complete_today": 0,
            "timeouts_today": 0,
            "invalidations_today": 0
        }
        logger.info("Daily stats reset")




# ===================== PAPER ACCOUNT =====================
class PaperAccount:
    """Gestisce il capitale simulato e le posizioni"""
    
    def __init__(self, initial_capital: float):
        self.initial_capital = initial_capital
        self.balance = initial_capital  # USDT disponibili
        self.positions = {}  # Posizioni aperte {symbol: position_info}
        self.closed_trades = []  # Storico trades chiusi
        self.equity = initial_capital  # Capitale totale (balance + valore posizioni)
        
    def get_balance(self) -> float:
        """Ritorna il balance disponibile"""
        return self.balance
    
    def get_equity(self) -> float:
        """Calcola equity totale (balance + valore posizioni aperte)"""
        return self.equity
    
    def get_position(self, symbol: str) -> Optional[Dict]:
        """Ritorna la posizione per un simbolo"""
        return self.positions.get(symbol)
    
    def open_position(self, symbol: str, side: str, entry_price: float, 
                     size: float, stop_loss: float, take_profit: float):
        """Apre una nuova posizione"""
        cost = entry_price * size
        
        if cost > self.balance:
            print(f"[ERROR] Capitale insufficiente per aprire {symbol}")
            return False
        
        # Sottrai dal balance
        self.balance -= cost
        
        # Crea posizione
        self.positions[symbol] = {
            "side": side,
            "entry_price": entry_price,
            "size": size,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "open_time": datetime.now(),
            "cost": cost
        }
        
        print(f"[OPEN] {side} {symbol} @ {entry_price:.2f} | Size: {size:.6f} | Cost: ${cost:.2f}")
        print(f"       SL: {stop_loss:.2f} | TP: {take_profit:.2f}")
        
        return True
    
    def close_position(self, symbol: str, exit_price: float, reason: str = "MANUAL"):
        """Chiude una posizione esistente"""
        if symbol not in self.positions:
            return False
        
        pos = self.positions[symbol]
        
        # Calcola P&L
        if pos["side"] == "LONG":
            pnl = (exit_price - pos["entry_price"]) * pos["size"]
        else:  # SHORT
            pnl = (pos["entry_price"] - exit_price) * pos["size"]
        
        pnl_pct = (pnl / pos["cost"]) * 100
        
        # Aggiorna balance
        exit_value = exit_price * pos["size"]
        self.balance += exit_value
        
        # Salva trade chiuso
        trade_record = {
            "symbol": symbol,
            "side": pos["side"],
            "entry_price": pos["entry_price"],
            "exit_price": exit_price,
            "size": pos["size"],
            "pnl": pnl,
            "pnl_pct": pnl_pct,
            "open_time": pos["open_time"],
            "close_time": datetime.now(),
            "reason": reason
        }
        self.closed_trades.append(trade_record)
        
        print(f"[CLOSE] {pos['side']} {symbol} @ {exit_price:.2f} | PnL: ${pnl:.2f} ({pnl_pct:+.2f}%) | Reason: {reason}")
        
        # Rimuovi posizione
        del self.positions[symbol]
        
        # Salva su CSV
        self._log_trade(trade_record)
        
        return True
    
    def update_equity(self, current_prices: Dict[str, float]):
        """Aggiorna l'equity totale basandosi sui prezzi correnti"""
        position_value = 0.0
        
        for symbol, pos in self.positions.items():
            if symbol in current_prices:
                price = current_prices[symbol]
                position_value += price * pos["size"]
        
        self.equity = self.balance + position_value
    
    def _log_trade(self, trade: Dict):
        """Salva trade su CSV"""
        file_exists = os.path.isfile(CONFIG["TRADES_LOG"])
        
        with open(CONFIG["TRADES_LOG"], "a", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=[
                "symbol", "side", "entry_price", "exit_price", "size",
                "pnl", "pnl_pct", "open_time", "close_time", "reason"
            ])
            
            if not file_exists:
                writer.writeheader()
            
            writer.writerow(trade)
    
    def get_statistics(self) -> Dict:
        """Calcola statistiche performance"""
        roi = ((self.equity - self.initial_capital) / self.initial_capital * 100)
        
        if not self.closed_trades:
            return {
                "total_trades": 0,
                "winning_trades": 0,
                "losing_trades": 0,
                "win_rate": 0.0,
                "total_pnl": 0.0,
                "avg_pnl": 0.0,
                "roi": roi
            }
        
        total_trades = len(self.closed_trades)
        winning_trades = len([t for t in self.closed_trades if t["pnl"] > 0])
        losing_trades = len([t for t in self.closed_trades if t["pnl"] <= 0])
        total_pnl = sum(t["pnl"] for t in self.closed_trades)
        
        return {
            "total_trades": total_trades,
            "winning_trades": winning_trades,
            "losing_trades": losing_trades,
            "win_rate": (winning_trades / total_trades * 100) if total_trades > 0 else 0.0,
            "total_pnl": total_pnl,
            "avg_pnl": total_pnl / total_trades if total_trades > 0 else 0.0,
            "roi": roi
        }
    
    def get_advanced_statistics(self) -> Dict:
        """Calcola statistiche avanzate"""
        if not self.closed_trades:
            return {}
        
        total_trades = len(self.closed_trades)
        pnls = [t["pnl"] for t in self.closed_trades]
        winning_trades = [t for t in self.closed_trades if t["pnl"] > 0]
        losing_trades = [t for t in self.closed_trades if t["pnl"] <= 0]
        
        # Profit factor
        total_wins = sum(t["pnl"] for t in winning_trades) if winning_trades else 0
        total_losses = abs(sum(t["pnl"] for t in losing_trades)) if losing_trades else 0
        profit_factor = total_wins / total_losses if total_losses > 0 else float('inf')
        
        # Max drawdown
        equity_curve = [self.initial_capital]
        for trade in self.closed_trades:
            equity_curve.append(equity_curve[-1] + trade["pnl"])
        
        peak = equity_curve[0]
        max_dd = 0
        for equity in equity_curve:
            if equity > peak:
                peak = equity
            dd = (peak - equity) / peak * 100
            if dd > max_dd:
                max_dd = dd
        
        # Best & Worst trade
        best_trade = max(pnls)
        worst_trade = min(pnls)
        
        # Average trade duration
        durations = []
        for t in self.closed_trades:
            if isinstance(t["open_time"], datetime) and isinstance(t["close_time"], datetime):
                duration = (t["close_time"] - t["open_time"]).total_seconds() / 60  # minuti
                durations.append(duration)
        avg_duration = sum(durations) / len(durations) if durations else 0
        
        # Consecutive wins/losses
        max_consecutive_wins = 0
        max_consecutive_losses = 0
        current_wins = 0
        current_losses = 0
        
        for t in self.closed_trades:
            if t["pnl"] > 0:
                current_wins += 1
                current_losses = 0
                max_consecutive_wins = max(max_consecutive_wins, current_wins)
            else:
                current_losses += 1
                current_wins = 0
                max_consecutive_losses = max(max_consecutive_losses, current_losses)
        
        return {
            "profit_factor": profit_factor,
            "max_drawdown_pct": max_dd,
            "best_trade": best_trade,
            "worst_trade": worst_trade,
            "avg_trade_duration_min": avg_duration,
            "max_consecutive_wins": max_consecutive_wins,
            "max_consecutive_losses": max_consecutive_losses,
            "expectancy": sum(pnls) / total_trades if total_trades > 0 else 0,
            "sharpe_ratio": (np.mean(pnls) / np.std(pnls)) if len(pnls) > 1 and np.std(pnls) > 0 else 0
        }
    
    def export_to_excel(self):
        """Esporta tutto in Excel con formattazione"""
        logger.info(f"Exporting data to Excel: {CONFIG['EXCEL_REPORT']}")
        
        try:
            workbook = xlsxwriter.Workbook(CONFIG['EXCEL_REPORT'])
            
            # Formati
            header_format = workbook.add_format({
                'bold': True,
                'bg_color': '#4472C4',
                'font_color': 'white',
                'border': 1
            })
            
            win_format = workbook.add_format({
                'bg_color': '#C6EFCE',
                'font_color': '#006100'
            })
            
            loss_format = workbook.add_format({
                'bg_color': '#FFC7CE',
                'font_color': '#9C0006'
            })
            
            money_format = workbook.add_format({'num_format': '$#,##0.00'})
            pct_format = workbook.add_format({'num_format': '0.00%'})
            date_format = workbook.add_format({'num_format': 'yyyy-mm-dd hh:mm:ss'})
            
            # SHEET 1: Trades
            self._export_trades_sheet(workbook, header_format, win_format, loss_format, 
                                     money_format, pct_format, date_format)
            
            # SHEET 2: Daily Summary
            self._export_daily_summary_sheet(workbook, header_format, money_format)
            
            # SHEET 3: ICT Signals
            self._export_ict_signals_sheet(workbook, header_format)
            
            # SHEET 4: Statistics
            self._export_statistics_sheet(workbook, header_format, money_format, pct_format)
            
            # SHEET 5: Equity Curve
            self._export_equity_curve_sheet(workbook, header_format, money_format)
            
            workbook.close()
            logger.info(f"Excel export completed: {CONFIG['EXCEL_REPORT']}")
            
        except Exception as e:
            logger.error(f"Excel export failed: {e}")
    
    def _export_trades_sheet(self, workbook, header_format, win_format, loss_format,
                            money_format, pct_format, date_format):
        """Sheet 1: Tutti i trade"""
        worksheet = workbook.add_worksheet('Trades')
        
        # Headers
        headers = ['Symbol', 'Side', 'Entry Price', 'Exit Price', 'Size', 
                  'P&L', 'P&L %', 'Open Time', 'Close Time', 'Duration (min)', 'Reason']
        for col, header in enumerate(headers):
            worksheet.write(0, col, header, header_format)
        
        # Data
        for row, trade in enumerate(self.closed_trades, start=1):
            worksheet.write(row, 0, trade['symbol'])
            worksheet.write(row, 1, trade['side'])
            worksheet.write(row, 2, trade['entry_price'], money_format)
            worksheet.write(row, 3, trade['exit_price'], money_format)
            worksheet.write(row, 4, trade['size'])
            
            # P&L con colore
            pnl = trade['pnl']
            fmt = win_format if pnl > 0 else loss_format
            worksheet.write(row, 5, pnl, fmt)
            worksheet.write(row, 6, trade['pnl_pct'] / 100, fmt)
            
            worksheet.write(row, 7, trade['open_time'].strftime('%Y-%m-%d %H:%M:%S') if isinstance(trade['open_time'], datetime) else str(trade['open_time']))
            worksheet.write(row, 8, trade['close_time'].strftime('%Y-%m-%d %H:%M:%S') if isinstance(trade['close_time'], datetime) else str(trade['close_time']))
            
            # Duration
            if isinstance(trade['open_time'], datetime) and isinstance(trade['close_time'], datetime):
                duration = (trade['close_time'] - trade['open_time']).total_seconds() / 60
                worksheet.write(row, 9, duration)
            
            worksheet.write(row, 10, trade['reason'])
        
        # Totali
        if self.closed_trades:
            total_row = len(self.closed_trades) + 1
            worksheet.write(total_row, 4, 'TOTAL:', header_format)
            worksheet.write_formula(total_row, 5, f'=SUM(F2:F{total_row})', money_format)
            worksheet.write_formula(total_row, 6, f'=AVERAGE(G2:G{total_row})', pct_format)
        
        # Larghezza colonne
        worksheet.set_column('A:A', 12)
        worksheet.set_column('B:B', 8)
        worksheet.set_column('C:D', 12)
        worksheet.set_column('E:E', 10)
        worksheet.set_column('F:G', 12)
        worksheet.set_column('H:I', 20)
        worksheet.set_column('J:J', 15)
        worksheet.set_column('K:K', 10)
    
    def _export_daily_summary_sheet(self, workbook, header_format, money_format):
        """Sheet 2: Sommario giornaliero"""
        worksheet = workbook.add_worksheet('Daily Summary')
        
        # Raggruppa per giorno
        daily_data = defaultdict(lambda: {'trades': 0, 'pnl': 0, 'wins': 0, 'losses': 0})
        
        for trade in self.closed_trades:
            if isinstance(trade['close_time'], datetime):
                date = trade['close_time'].date()
                daily_data[date]['trades'] += 1
                daily_data[date]['pnl'] += trade['pnl']
                if trade['pnl'] > 0:
                    daily_data[date]['wins'] += 1
                else:
                    daily_data[date]['losses'] += 1
        
        # Headers
        headers = ['Date', 'Trades', 'Wins', 'Losses', 'Win Rate %', 'P&L']
        for col, header in enumerate(headers):
            worksheet.write(0, col, header, header_format)
        
        # Data
        for row, (date, data) in enumerate(sorted(daily_data.items()), start=1):
            worksheet.write(row, 0, str(date))
            worksheet.write(row, 1, data['trades'])
            worksheet.write(row, 2, data['wins'])
            worksheet.write(row, 3, data['losses'])
            win_rate = (data['wins'] / data['trades'] * 100) if data['trades'] > 0 else 0
            worksheet.write(row, 4, win_rate)
            worksheet.write(row, 5, data['pnl'], money_format)
        
        worksheet.set_column('A:A', 12)
        worksheet.set_column('B:E', 10)
        worksheet.set_column('F:F', 15)
    
    def _export_ict_signals_sheet(self, workbook, header_format):
        """Sheet 3: ICT Signals log"""
        worksheet = workbook.add_worksheet('ICT Signals')
        
        signals = ict_logger.get_signals()
        
        # Headers
        headers = ['Timestamp', 'Symbol', 'Timeframe', 'Step', 'Result', 'Grade', 'Details']
        for col, header in enumerate(headers):
            worksheet.write(0, col, header, header_format)
        
        # Data
        for row, signal in enumerate(signals, start=1):
            worksheet.write(row, 0, str(signal['timestamp']))
            worksheet.write(row, 1, signal['symbol'])
            worksheet.write(row, 2, signal['timeframe'])
            worksheet.write(row, 3, signal['step'])
            worksheet.write(row, 4, signal['result'])
            worksheet.write(row, 5, signal['grade'] or '')
            worksheet.write(row, 6, signal['details'])
        
        worksheet.set_column('A:A', 20)
        worksheet.set_column('B:C', 12)
        worksheet.set_column('D:E', 15)
        worksheet.set_column('F:F', 8)
        worksheet.set_column('G:G', 50)
    
    def _export_statistics_sheet(self, workbook, header_format, money_format, pct_format):
        """Sheet 4: Statistiche"""
        worksheet = workbook.add_worksheet('Statistics')
        
        stats = self.get_statistics()
        adv_stats = self.get_advanced_statistics()
        
        # Headers
        worksheet.write(0, 0, 'Metric', header_format)
        worksheet.write(0, 1, 'Value', header_format)
        
        # Basic stats
        metrics = [
            ('Total Trades', stats.get('total_trades', 0)),
            ('Winning Trades', stats.get('winning_trades', 0)),
            ('Losing Trades', stats.get('losing_trades', 0)),
            ('Win Rate %', stats.get('win_rate', 0)),
            ('Total P&L', stats.get('total_pnl', 0)),
            ('Average P&L', stats.get('avg_pnl', 0)),
            ('ROI %', stats.get('roi', 0)),
        ]
        
        # Advanced stats
        if adv_stats:
            metrics.extend([
                ('Profit Factor', adv_stats.get('profit_factor', 0)),
                ('Max Drawdown %', adv_stats.get('max_drawdown_pct', 0)),
                ('Best Trade', adv_stats.get('best_trade', 0)),
                ('Worst Trade', adv_stats.get('worst_trade', 0)),
                ('Avg Duration (min)', adv_stats.get('avg_trade_duration_min', 0)),
                ('Max Consecutive Wins', adv_stats.get('max_consecutive_wins', 0)),
                ('Max Consecutive Losses', adv_stats.get('max_consecutive_losses', 0)),
                ('Expectancy', adv_stats.get('expectancy', 0)),
                ('Sharpe Ratio', adv_stats.get('sharpe_ratio', 0)),
            ])
        
        for row, (metric, value) in enumerate(metrics, start=1):
            worksheet.write(row, 0, metric)
            if 'P&L' in metric or 'Trade' in metric:
                worksheet.write(row, 1, value, money_format)
            elif '%' in metric or 'Rate' in metric or 'ROI' in metric or 'Drawdown' in metric:
                worksheet.write(row, 1, value / 100 if value > 1 else value, pct_format)
            else:
                worksheet.write(row, 1, value)
        
        worksheet.set_column('A:A', 25)
        worksheet.set_column('B:B', 15)
    
    def _export_equity_curve_sheet(self, workbook, header_format, money_format):
        """Sheet 5: Equity curve"""
        worksheet = workbook.add_worksheet('Equity Curve')
        
        # Headers
        worksheet.write(0, 0, 'Trade #', header_format)
        worksheet.write(0, 1, 'Equity', header_format)
        worksheet.write(0, 2, 'P&L', header_format)
        
        # Data
        equity = self.initial_capital
        worksheet.write(1, 0, 0)
        worksheet.write(1, 1, equity, money_format)
        worksheet.write(1, 2, 0, money_format)
        
        for i, trade in enumerate(self.closed_trades, start=1):
            equity += trade['pnl']
            worksheet.write(i + 1, 0, i)
            worksheet.write(i + 1, 1, equity, money_format)
            worksheet.write(i + 1, 2, trade['pnl'], money_format)
        
        # Grafico
        chart = workbook.add_chart({'type': 'line'})
        chart.add_series({
            'name': 'Equity',
            'categories': f'=\'Equity Curve\'!$A$2:$A${len(self.closed_trades) + 2}',
            'values': f'=\'Equity Curve\'!$B$2:$B${len(self.closed_trades) + 2}',
            'line': {'color': 'blue', 'width': 2},
        })
        chart.set_title({'name': 'Equity Curve'})
        chart.set_x_axis({'name': 'Trade Number'})
        chart.set_y_axis({'name': 'Equity ($)'})
        chart.set_size({'width': 720, 'height': 400})
        
        worksheet.insert_chart('E2', chart)
        
        worksheet.set_column('A:A', 10)
        worksheet.set_column('B:C', 15)


# ===================== EXCHANGE CONNECTION =====================
def init_exchange():
    """Inizializza connessione exchange (solo lettura per paper trading)"""
    print(f"Connessione a {CONFIG['EXCHANGE']}...")
    
    exchange_class = getattr(ccxt, CONFIG["EXCHANGE"])
    exchange = exchange_class({
        "enableRateLimit": True,
        "timeout": 30000,
    })
    
    # Non servono API keys per dati pubblici
    print(f"Exchange {CONFIG['EXCHANGE']} connesso (modalità pubblica)")
    
    return exchange


def fetch_ohlcv(exchange, symbol: str, timeframe: str, limit: int = 100) -> pd.DataFrame:
    """Scarica dati OHLCV"""
    try:
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
        df = pd.DataFrame(ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"])
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
        return df
    except Exception as e:
        print(f"[ERROR] Fetch OHLCV {symbol}: {e}")
        return pd.DataFrame()


# ===================== SWING DETECTION (FRACTAL) =====================
def find_swing_highs_lows(df: pd.DataFrame, lr: int = 2) -> Tuple[List[Tuple[int, float]], List[Tuple[int, float]]]:
    """
    Trova swing highs e swing lows usando logica frattale
    lr = left/right bars (es: 2 significa 2 barre a sx e 2 a dx)
    Ritorna: (swing_highs, swing_lows) come liste di (index, price)
    """
    highs = df["high"].values
    lows = df["low"].values
    
    swing_highs = []
    swing_lows = []
    
    for i in range(lr, len(df) - lr):
        # Swing High: high[i] > tutti high nei lr prima e dopo
        is_swing_high = True
        for j in range(1, lr + 1):
            if highs[i] <= highs[i - j] or highs[i] <= highs[i + j]:
                is_swing_high = False
                break
        
        if is_swing_high:
            swing_highs.append((i, float(highs[i])))
        
        # Swing Low: low[i] < tutti low nei lr prima e dopo
        is_swing_low = True
        for j in range(1, lr + 1):
            if lows[i] >= lows[i - j] or lows[i] >= lows[i + j]:
                is_swing_low = False
                break
        
        if is_swing_low:
            swing_lows.append((i, float(lows[i])))
    
    return swing_highs, swing_lows


def get_last_confirmed_swings(swing_highs: List[Tuple[int, float]], 
                               swing_lows: List[Tuple[int, float]]) -> Tuple[Optional[float], Optional[float]]:
    """
    Ottiene l'ultimo swing high e swing low confermati
    Ritorna: (last_swing_high, last_swing_low)
    """
    last_high = swing_highs[-1][1] if swing_highs else None
    last_low = swing_lows[-1][1] if swing_lows else None
    
    return last_high, last_low


# ===================== ATR CALCULATION =====================
def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Calcola Average True Range"""
    high = df["high"]
    low = df["low"]
    close = df["close"]
    
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=period).mean()
    
    return atr


# ===================== BIAS COMPUTATION (ICT LOGIC) =====================
def compute_bias(df_htf: pd.DataFrame, lr: int = 2) -> Dict:
    """
    Determina il BIAS usando logica ICT completa
    
    Parametri:
    - df_htf: DataFrame HTF (15m)
    - lr: left/right per swing detection
    
    Ritorna: Dict con bias e dettagli
    """
    if len(df_htf) < 20:
        return {"bias": "NONE", "reason": "Dati insufficienti"}
    
    # 1. Trova swings
    swing_highs, swing_lows = find_swing_highs_lows(df_htf, lr)
    
    if not swing_highs or not swing_lows:
        return {"bias": "NONE", "reason": "Nessun swing trovato"}
    
    # 2. Ottieni last confirmed swings
    external_high, external_low = get_last_confirmed_swings(swing_highs, swing_lows)
    current_price = float(df_htf["close"].iloc[-1])
    current_high = float(df_htf["high"].iloc[-1])
    current_low = float(df_htf["low"].iloc[-1])
    
    # 3. Calcola ATR per compressione
    atr = calculate_atr(df_htf, CONFIG["ATR_PERIOD"])
    current_atr = float(atr.iloc[-1]) if not pd.isna(atr.iloc[-1]) else 0
    
    # Range HTF (ultimi n bars)
    recent_bars = 20
    range_htf = float(df_htf["high"].tail(recent_bars).max() - df_htf["low"].tail(recent_bars).min())
    
    # 4. Check compressione
    compression = False
    if current_atr > 0:
        if range_htf < current_atr * CONFIG["COMPRESSION_THRESHOLD"]:
            compression = True
    
    if compression:
        return {
            "bias": "NONE",
            "reason": "Compressione",
            "external_high": external_high,
            "external_low": external_low,
            "current_price": current_price,
            "atr": current_atr,
            "range": range_htf
        }
    
    # 5. Check body size per break valido
    last_candle = df_htf.iloc[-1]
    candle_body = abs(float(last_candle["close"]) - float(last_candle["open"]))
    candle_range = float(last_candle["high"]) - float(last_candle["low"])
    body_ratio = candle_body / candle_range if candle_range > 0 else 0
    
    body_confirmed = body_ratio >= CONFIG["MIN_BODY_RATIO"]
    
    # 6. Check break struttura
    break_up_valid = current_high > external_high and body_confirmed
    break_down_valid = current_low < external_low and body_confirmed
    
    if break_up_valid:
        return {
            "bias": "UP",
            "reason": "Break struttura UP",
            "external_high": external_high,
            "external_low": external_low,
            "current_price": current_price,
            "body_ratio": body_ratio
        }
    
    if break_down_valid:
        return {
            "bias": "DOWN",
            "reason": "Break struttura DOWN",
            "external_high": external_high,
            "external_low": external_low,
            "current_price": current_price,
            "body_ratio": body_ratio
        }
    
    # 7. Check liquidità
    liquidity_above = external_high > current_price
    liquidity_below = external_low < current_price
    
    if liquidity_above and not liquidity_below:
        return {
            "bias": "UP",
            "reason": "Liquidità sopra",
            "external_high": external_high,
            "external_low": external_low,
            "current_price": current_price
        }
    
    if liquidity_below and not liquidity_above:
        return {
            "bias": "DOWN",
            "reason": "Liquidità sotto",
            "external_high": external_high,
            "external_low": external_low,
            "current_price": current_price
        }
    
    # 8. Entrambe liquidità presenti -> distanza
    if liquidity_above and liquidity_below:
        distance_to_high = external_high - current_price
        distance_to_low = current_price - external_low
        
        if distance_to_high < distance_to_low:
            return {
                "bias": "UP",
                "reason": "Liquidità sopra più vicina",
                "external_high": external_high,
                "external_low": external_low,
                "current_price": current_price,
                "distance_to_high": distance_to_high,
                "distance_to_low": distance_to_low
            }
        elif distance_to_low < distance_to_high:
            return {
                "bias": "DOWN",
                "reason": "Liquidità sotto più vicina",
                "external_high": external_high,
                "external_low": external_low,
                "current_price": current_price,
                "distance_to_high": distance_to_high,
                "distance_to_low": distance_to_low
            }
    
    # 9. Nessuna condizione -> NONE
    return {
        "bias": "NONE",
        "reason": "Nessuna condizione valida",
        "external_high": external_high,
        "external_low": external_low,
        "current_price": current_price
    }


# ===================== SWEEP DETECTION (ICT STEP 2) =====================
def detect_sweep(bias: str, pool_high: float, pool_low: float, 
                 o: float, h: float, l: float, c: float, 
                 atr: float, current_price: float) -> Optional[Dict]:
    """
    Rileva sweep (liquidity grab) coerente con bias HTF
    
    Parametri:
    - bias: "UP", "DOWN", o "NONE"
    - pool_high: ultimo swing high (livello liquidità sopra)
    - pool_low: ultimo swing low (livello liquidità sotto)
    - o, h, l, c: open, high, low, close della candela corrente
    - atr: Average True Range corrente
    - current_price: prezzo corrente per filtri
    
    Ritorna: Dict con dettagli sweep o None se non valido
    
    REGOLA ICT: Sweep valido = wick oltre pool + reclaim dentro
    """
    if bias == "NONE" or atr == 0:
        return None
    
    # Calcola thresholds ATR-based
    min_sweep_dist = atr * CONFIG["SWEEP_MIN_DIST_MULT"]  # 0.10 * ATR
    reclaim_buffer = atr * CONFIG["SWEEP_RECLAIM_MULT"]   # 0.02 * ATR
    
    # A) SELL-SIDE SWEEP (per BIAS UP)
    # Wick sotto pool_low + close recupera sopra
    sweep_down = (
        l < pool_low - min_sweep_dist and 
        c > pool_low + reclaim_buffer
    )
    
    # B) BUY-SIDE SWEEP (per BIAS DOWN)
    # Wick sopra pool_high + close recupera sotto
    sweep_up = (
        h > pool_high + min_sweep_dist and 
        c < pool_high - reclaim_buffer
    )
    
    # Determina quale sweep è valido in base al bias
    if bias == "UP":
        valid = sweep_down
        direction = "DOWN"  # sweep DOWN per bias UP
        pool = pool_low
        extreme = l
    elif bias == "DOWN":
        valid = sweep_up
        direction = "UP"  # sweep UP per bias DOWN
        pool = pool_high
        extreme = h
    else:
        return None
    
    if not valid:
        return None
    
    # === FILTRI QUALITÀ (opzionali ma raccomandati) ===
    
    # Filter 1: Wick Dominance
    # Lo sweep deve avere un wick significativo (stop run vero)
    body = abs(c - o)
    if body == 0:
        return None
    
    if direction == "DOWN":
        # Sell-side: wick_down >= body * wick_ratio
        wick_down = min(o, c) - l
        wick_ok = wick_down >= body * CONFIG["SWEEP_WICK_RATIO"]
    else:
        # Buy-side: wick_up >= body * wick_ratio
        wick_up = h - max(o, c)
        wick_ok = wick_up >= body * CONFIG["SWEEP_WICK_RATIO"]
    
    if not wick_ok:
        # Sweep con wick troppo piccolo -> probabilmente non è un vero stop run
        return None
    
    # Filter 2: Pool Significance
    # La pool deve essere abbastanza distante dal prezzo corrente
    pool_distance = abs(current_price - pool)
    pool_significant = pool_distance > atr * CONFIG["SWEEP_POOL_SIGNIFICANCE"]
    
    if not pool_significant:
        # Pool troppo vicina, non è significativa
        return None
    
    # === INVALIDAZIONI ===
    
    # Invalidazione 1: Sweep senza reclaim (solo wick, close oltre pool)
    if direction == "DOWN" and c < pool_low:
        # Non è sweep, è possibile breakdown
        return None
    
    if direction == "UP" and c > pool_high:
        # Non è sweep, è possibile breakup
        return None
    
    # Invalidazione 2: Violazione troppo piccola (già coperto da min_sweep_dist)
    # È già verificato nelle condizioni sweep_down/sweep_up
    
    # === SWEEP VALIDO ===
    return {
        "direction": direction,
        "pool": pool,
        "extreme": extreme,
        "close": c,
        "atr": atr,
        "wick_ratio": (wick_down / body if body != 0 else 999) if direction == "DOWN" else (wick_up / body if body != 0 else 999),
        "pool_distance": pool_distance,
    }


# ===================== DISPLACEMENT DETECTION (ICT STEP 3) =====================
def detect_displacement_m15(bias: str, o: float, h: float, l: float, c: float,
                           atr: float, last_swing_high: float, last_swing_low: float,
                           h_i_2: float, l_i_2: float) -> Optional[Dict]:
    """
    Rileva displacement (cambio regime) su M15 dopo sweep
    
    Parametri:
    - bias: "UP", "DOWN", o "NONE"
    - o, h, l, c: open, high, low, close della candela corrente (i)
    - atr: Average True Range corrente
    - last_swing_high: ultimo swing high HTF
    - last_swing_low: ultimo swing low HTF
    - h_i_2: high della candela i-2 (per FVG)
    - l_i_2: low della candela i-2 (per FVG)
    
    Ritorna: Dict con dettagli displacement o None se non valido
    
    REGOLA ICT DISPLACEMENT:
    - BIAS UP → displacement UP atteso (BOS sopra swing high)
    - BIAS DOWN → displacement DOWN atteso (BOS sotto swing low)
    - Impulso: range >= ATR * 0.80
    - Body dominance: body >= range * 0.55
    - FVG opzionale: grade A se presente, B altrimenti
    """
    if bias == "NONE" or atr == 0:
        return None
    
    # === PARAMETRI ===
    bos_buffer = atr * CONFIG["DISPLACEMENT_BOS_BUFFER"]  # 0.02 * ATR
    impulse_mult = CONFIG["DISPLACEMENT_IMPULSE_MULT"]    # 0.80
    body_ratio = CONFIG["DISPLACEMENT_BODY_RATIO"]        # 0.55
    
    # === CALCOLI CANDELA ===
    candle_range = h - l
    body = abs(c - o)
    
    # === CONDIZIONI ===
    # 1. Impulso anomalo (range >= ATR * 0.80)
    impulse_ok = candle_range >= atr * impulse_mult
    
    # 2. Body dominance (body >= range * 0.55)
    body_ok = body >= candle_range * body_ratio if candle_range > 0 else False
    
    # 3. Break of Structure (BOS)
    bos_up = c > (last_swing_high + bos_buffer)
    bos_down = c < (last_swing_low - bos_buffer)
    
    # === FVG DETECTION (3-candle pattern) ===
    # FVG rialzista: low[i] > high[i-2] (gap verso l'alto)
    # FVG ribassista: high[i] < low[i-2] (gap verso il basso)
    fvg = None
    
    if l > h_i_2:
        # FVG UP: c'è un gap tra low corrente e high di 2 barre fa
        fvg = {
            "dir": "UP",
            "low": h_i_2,
            "high": l
        }
    elif h < l_i_2:
        # FVG DOWN: c'è un gap tra high corrente e low di 2 barre fa
        fvg = {
            "dir": "DOWN",
            "low": h,
            "high": l_i_2
        }
    
    # === VALIDAZIONE PER BIAS ===
    if bias == "UP":
        # Per BIAS UP, aspettiamo displacement UP
        valid = bos_up and impulse_ok and body_ok
        disp_dir = "UP"
        bos_level = last_swing_high
    elif bias == "DOWN":
        # Per BIAS DOWN, aspettiamo displacement DOWN
        valid = bos_down and impulse_ok and body_ok
        disp_dir = "DOWN"
        bos_level = last_swing_low
    else:
        return None
    
    if not valid:
        return None
    
    # === GRADE ===
    # Grade A: FVG presente e coerente con direzione
    # Grade B: nessun FVG o FVG non coerente
    grade = "A" if (fvg is not None and fvg["dir"] == disp_dir) else "B"
    
    # === DISPLACEMENT VALIDO ===
    return {
        "dir": disp_dir,
        "bos_level": bos_level,
        "impulse_ok": impulse_ok,
        "body_ok": body_ok,
        "candle_range": candle_range,
        "body": body,
        "fvg": fvg,
        "grade": grade
    }


# ===================== RETRACE DETECTION (ICT STEP 4) =====================
def detect_retrace_m15(disp_dir: str, fvg: Optional[Dict], 
                       disp_high: float, disp_low: float, atr: float,
                       o: float, h: float, l: float, c: float,
                       bars_since_disp: int) -> Dict:
    """
    Rileva retrace (pullback) su M15 dopo displacement
    
    Parametri:
    - disp_dir: "UP" o "DOWN" (direzione displacement)
    - fvg: Fair Value Gap dal displacement (o None)
    - disp_high: high del displacement range
    - disp_low: low del displacement range
    - atr: Average True Range corrente
    - o, h, l, c: open, high, low, close della candela corrente
    - bars_since_disp: numero di barre da displacement
    
    Ritorna: Dict con status e dettagli
    
    Status possibili:
    - "HIT": zona retrace toccata, procedi a confirmation
    - "WAIT": in attesa che prezzo torni in zona
    - "EXPIRED": timeout superato, reset a WAIT_SWEEP
    - "INVALIDATED": impulso invalidato, reset a WAIT_BIAS
    
    REGOLA ICT RETRACE:
    - Preferenza zona FVG se presente
    - Altrimenti: 50%-79% del displacement range
    - Depth ideale: 0.50-0.79 (Grade A)
    """
    
    # === FILTRO 1: TIMEOUT ===
    max_retrace_bars = CONFIG["MAX_RETRACE_BARS"]
    if bars_since_disp > max_retrace_bars:
        return {"status": "EXPIRED"}
    
    # === CALCOLO DISPLACEMENT RANGE ===
    disp_range = disp_high - disp_low
    if disp_range <= 0:
        return {"status": "INVALID"}
    
    # === FILTRO 2: INVALIDATION CHECK ===
    # Il prezzo non deve chiudere oltre il displacement range + buffer
    invalidation_buffer = atr * CONFIG["RETRACE_INVALIDATION_MULT"]
    
    if disp_dir == "UP":
        # Per UP: non deve chiudere sotto il low del displacement
        invalidate_level = disp_low - invalidation_buffer
        invalidated = c < invalidate_level
    else:
        # Per DOWN: non deve chiudere sopra il high del displacement
        invalidate_level = disp_high + invalidation_buffer
        invalidated = c > invalidate_level
    
    if invalidated:
        return {"status": "INVALIDATED"}
    
    # === DEFINIZIONE ZONA RETRACE ===
    # Caso A: FVG esiste e coerente con direzione
    if fvg is not None and fvg.get("dir") == disp_dir:
        z_low = fvg["low"]
        z_high = fvg["high"]
        zone_type = "FVG"
    else:
        # Caso B: Fallback a 50%-79% del range
        if disp_dir == "UP":
            # Per UP: zona discount (parte bassa del range)
            z_low = disp_low + disp_range * CONFIG["RETRACE_ZONE_MIN"]
            z_high = disp_low + disp_range * CONFIG["RETRACE_ZONE_MAX"]
        else:
            # Per DOWN: zona premium (parte alta del range)
            z_high = disp_high - disp_range * CONFIG["RETRACE_ZONE_MIN"]
            z_low = disp_high - disp_range * CONFIG["RETRACE_ZONE_MAX"]
        zone_type = "FALLBACK"
    
    # === HIT DETECTION (intersezione con zona) ===
    # Basta che il wick tocchi la zona
    retrace_hit = (l <= z_high) and (h >= z_low)
    
    if not retrace_hit:
        return {
            "status": "WAIT",
            "zone_low": z_low,
            "zone_high": z_high,
            "zone_type": zone_type
        }
    
    # === CALCOLO DEPTH E GRADING ===
    if disp_dir == "UP":
        # Per UP: retrace point è il low della candela
        retrace_point = l
        # Depth: quanto è sceso dal high del displacement
        retrace_depth = (disp_high - retrace_point) / disp_range
    else:
        # Per DOWN: retrace point è il high della candela
        retrace_point = h
        # Depth: quanto è salito dal low del displacement
        retrace_depth = (retrace_point - disp_low) / disp_range
    
    # Grading basato sulla profondità
    if CONFIG["RETRACE_ZONE_MIN"] <= retrace_depth <= CONFIG["RETRACE_ZONE_MAX"]:
        grade = "A"  # Profondità ideale
    else:
        grade = "B"  # Valido ma fuori range ideale
    
    # === RETRACE VALIDO ===
    return {
        "status": "HIT",
        "zone_low": z_low,
        "zone_high": z_high,
        "zone_type": zone_type,
        "retrace_point": retrace_point,
        "retrace_depth": retrace_depth,
        "grade": grade
    }


# ===================== CONFIRMATION DETECTION (ICT STEP 5) =====================
def detect_confirm_m5(disp_dir: str, zone_low: float, zone_high: float,
                      o: float, h: float, l: float, c: float,
                      atr5: float,
                      m5_last_swing_high: float, m5_last_swing_low: float,
                      h_i_2: float, l_i_2: float,
                      bars_since_retrace_hit: int) -> Dict:
    """
    Rileva confirmation su M5 dopo retrace su M15
    
    Parametri:
    - disp_dir: "UP" o "DOWN" (direzione displacement M15)
    - zone_low, zone_high: zona retrace da M15
    - o, h, l, c: open, high, low, close della candela M5 corrente
    - atr5: Average True Range su M5
    - m5_last_swing_high: ultimo swing high su M5
    - m5_last_swing_low: ultimo swing low su M5
    - h_i_2, l_i_2: high/low candela i-2 per mini FVG
    - bars_since_retrace_hit: barre M5 da retrace hit
    
    Ritorna: Dict con status e dettagli
    
    Status possibili:
    - "CONFIRMED": setup completo, entry valido
    - "WAIT": in attesa confirmation
    - "EXPIRED": timeout superato
    
    REGOLA ICT CONFIRM:
    - Deve essere vicino alla zona retrace (context gate)
    - Micro BOS su M5 nella direzione attesa
    - Impulso e body dominance (più leggeri rispetto a M15)
    - Mini FVG opzionale per Grade A
    """
    
    # === FILTRO 1: TIMEOUT ===
    max_confirm_bars = CONFIG["MAX_CONFIRM_BARS"]
    if bars_since_retrace_hit > max_confirm_bars:
        return {"status": "EXPIRED"}
    
    # === FILTRO 2: CONTEXT GATE (vicino alla zona) ===
    # Il prezzo deve essere in o vicino alla zona retrace
    zone_buffer = atr5 * CONFIG["CONFIRM_ZONE_BUFFER"]
    in_zone_or_near = (l <= zone_high + zone_buffer) and (h >= zone_low - zone_buffer)
    
    if not in_zone_or_near:
        return {
            "status": "WAIT",
            "reason": "Prezzo fuori zona"
        }
    
    # === CALCOLI CANDELA ===
    candle_range = h - l
    if candle_range <= 0:
        return {"status": "WAIT", "reason": "Range invalido"}
    
    body = abs(c - o)
    
    # === PARAMETRI M5 (più leggeri) ===
    bos_buffer5 = atr5 * CONFIG["CONFIRM_BOS_BUFFER"]
    impulse_mult5 = CONFIG["CONFIRM_IMPULSE_MULT"]
    body_ratio5 = CONFIG["CONFIRM_BODY_RATIO"]
    
    # === CONDIZIONI ===
    # 1. Impulso (più leggero: 60% ATR)
    impulse_ok = candle_range >= atr5 * impulse_mult5
    
    # 2. Body dominance (50%)
    body_ok = body >= candle_range * body_ratio5
    
    # 3. Micro BOS su M5
    micro_bos_up = c > (m5_last_swing_high + bos_buffer5)
    micro_bos_down = c < (m5_last_swing_low - bos_buffer5)
    
    # === MINI FVG M5 (opzionale per grading) ===
    fvg = None
    if l > h_i_2:
        # Mini FVG UP
        fvg = {
            "dir": "UP",
            "low": h_i_2,
            "high": l
        }
    elif h < l_i_2:
        # Mini FVG DOWN
        fvg = {
            "dir": "DOWN",
            "low": h,
            "high": l_i_2
        }
    
    # === VALIDAZIONE PER DIREZIONE ===
    if disp_dir == "UP":
        # Per displacement UP, serve confirmation UP
        valid = in_zone_or_near and micro_bos_up and impulse_ok and body_ok
        confirm_dir = "UP"
        bos_level = m5_last_swing_high
    elif disp_dir == "DOWN":
        # Per displacement DOWN, serve confirmation DOWN
        valid = in_zone_or_near and micro_bos_down and impulse_ok and body_ok
        confirm_dir = "DOWN"
        bos_level = m5_last_swing_low
    else:
        return {"status": "WAIT", "reason": "Direzione invalida"}
    
    if not valid:
        return {
            "status": "WAIT",
            "reason": "Condizioni non soddisfatte",
            "impulse_ok": impulse_ok,
            "body_ok": body_ok,
            "micro_bos_up": micro_bos_up,
            "micro_bos_down": micro_bos_down
        }
    
    # === GRADING ===
    # Grade A: confirmation + mini FVG coerente
    # Grade B: confirmation senza FVG
    grade = "A" if (fvg is not None and fvg["dir"] == confirm_dir) else "B"
    
    # === CONFIRMATION VALIDA ===
    return {
        "status": "CONFIRMED",
        "dir": confirm_dir,
        "micro_bos_level": bos_level,
        "impulse_ok": impulse_ok,
        "body_ok": body_ok,
        "fvg": fvg,
        "grade": grade
    }


# ===================== ENTRY LOGIC (FINAL STEP) =====================
def generate_entry(disp_dir: str, confirm_high: float, confirm_low: float,
                   bars_since_confirm: int) -> Dict:
    """
    Genera entry logic dopo confirmation
    
    Parametri:
    - disp_dir: "UP" o "DOWN" (direzione displacement/confirm)
    - confirm_high: high della candela di confirmation
    - confirm_low: low della candela di confirmation
    - bars_since_confirm: barre M5 da confirmation
    
    Ritorna: Dict con status e entry price
    
    LOGICA ENTRY:
    - LONG: entry al 50% della candela confirm (dal low)
    - SHORT: entry al 50% della candela confirm (dal high)
    - Timeout: max 6 barre M5
    """
    
    # === TIMEOUT CHECK ===
    max_entry_bars = CONFIG["MAX_ENTRY_BARS"]
    if bars_since_confirm > max_entry_bars:
        return {"status": "EXPIRED"}
    
    # === CALCOLO ENTRY PRICE ===
    confirm_range = confirm_high - confirm_low
    retrace_pct = CONFIG["ENTRY_RETRACE_PCT"]
    
    if disp_dir == "UP":
        # LONG: entry al 50% dal low della candela confirm
        entry_price = confirm_low + (confirm_range * retrace_pct)
        side = "LONG"
    elif disp_dir == "DOWN":
        # SHORT: entry al 50% dal high della candela confirm
        entry_price = confirm_high - (confirm_range * retrace_pct)
        side = "SHORT"
    else:
        return {"status": "INVALID", "reason": "Direzione invalida"}
    
    # === ENTRY READY ===
    return {
        "status": "READY",
        "side": side,
        "entry_price": entry_price,
        "confirm_high": confirm_high,
        "confirm_low": confirm_low,
        "confirm_range": confirm_range
    }


# ===================== RISK MANAGEMENT (STRUCTURAL SL & 2R TP) =====================
# Note: calculate_structural_sl e calculate_tp_from_risk sono definite 
# più avanti nel codice (lines ~2196-2217) con firma semplificata
# Le versioni dettagliate sopra sono state rimosse per evitare duplicati


def check_entry_signal(bias: str, df_ltf: pd.DataFrame) -> Optional[str]:
    """
    Controlla segnale di entrata su LTF basato su BIAS HTF
    Per ora ritorna semplicemente il bias come segnale
    (da espandere con logica entry su LTF)
    """
    if bias == "UP":
        return "LONG"
    elif bias == "DOWN":
        return "SHORT"
    else:
        return None


def check_exit_signal(position: Dict, current_price: float) -> Optional[str]:
    """
    Controlla se posizione deve essere chiusa (SL/TP)
    Ritorna: "STOP_LOSS", "TAKE_PROFIT", o None
    """
    if position["side"] == "LONG":
        if current_price <= position["stop_loss"]:
            return "STOP_LOSS"
        if current_price >= position["take_profit"]:
            return "TAKE_PROFIT"
    else:  # SHORT
        if current_price >= position["stop_loss"]:
            return "STOP_LOSS"
        if current_price <= position["take_profit"]:
            return "TAKE_PROFIT"
    
    return None


# ===================== MAIN LOOP =====================
def main():
    """Loop principale del bot con STATE MACHINE"""
    print("="*70)
    print("PAPER TRADING BOT - ICT MULTI-CANDELA STATE MACHINE")
    print("="*70)
    print(f"Capitale iniziale: ${CONFIG['INITIAL_CAPITAL']:,.2f}")
    print(f"Simboli: {', '.join(CONFIG['SYMBOLS'])}")
    print(f"HTF (Steps 1-4): {CONFIG['HTF']} | LTF (Step 5): {CONFIG['LTF']}")
    print(f"Strategia: ICT Multi-Candela con State Tracking")
    print("="*70)
    print()
    
    # Inizializza
    exchange = init_exchange()
    account = PaperAccount(CONFIG["INITIAL_CAPITAL"])
    
    # CRITICAL: Inizializza State Manager (FUORI dal loop!)
    state_manager = ICTStateManager()
    
    loop_count = 0
    last_status_print = time.time()
    
    try:
        while True:
            loop_count += 1
            
            # CRITICAL: Increment ALL counters ogni iterazione
            state_manager.increment_all_counters()
            
            # Analizza ogni simbolo
            for symbol in CONFIG["SYMBOLS"]:
                try:
                    # Get state per questo symbol
                    state = state_manager.get_state(symbol)
                    
                    # Scarica dati HTF e LTF
                    df_htf = fetch_ohlcv(exchange, symbol, CONFIG["HTF"], limit=CONFIG["HTF_LOOKBACK"])
                    df_ltf = fetch_ohlcv(exchange, symbol, CONFIG["LTF"], limit=CONFIG["LTF_LOOKBACK"])
                    
                    if df_htf.empty or df_ltf.empty:
                        continue
                    
                    current_price = float(df_ltf["close"].iloc[-1])
                    
                    # Calcola ATR HTF (serve per quasi tutto)
                    atr_htf_series = calculate_atr(df_htf, CONFIG["ATR_PERIOD"])
                    atr_htf = float(atr_htf_series.iloc[-1]) if not pd.isna(atr_htf_series.iloc[-1]) else 0
                    
                    if atr_htf <= 0:
                        continue
                    
                    # ============ STATE MACHINE LOGIC ============
                    
                    if state.status == "WAIT_BIAS":
                        # STEP 0: Cerca BIAS
                        bias_info = compute_bias(df_htf, CONFIG["SWING_LEFT_RIGHT"])
                        bias = bias_info.get("bias", "NONE")
                        
                        if bias != "NONE":
                            # BIAS trovato!
                            state.bias = bias
                            state.bias_timestamp = datetime.now()
                            state.transition("WAIT_SWEEP", f"BIAS {bias} detected")
                            
                            logger.info(f"[{symbol}] BIAS {bias} - {bias_info.get('reason', '')}")
                    
                    elif state.status == "WAIT_SWEEP":
                        # STEP 1: Cerca SWEEP
                        # bars_since_bias già incrementato automaticamente!
                        
                        # Timeout check
                        max_bars = CONFIG.get("MAX_BARS_AFTER_BIAS", 20)
                        if state.bars_since_bias > max_bars:
                            state.reset("WAIT_BIAS", f"Timeout: no sweep in {state.bars_since_bias} bars")
                            state_manager.stats["timeouts_today"] += 1
                            continue
                        
                        # Get pools da bias
                        bias_info = compute_bias(df_htf, CONFIG["SWING_LEFT_RIGHT"])
                        pool_high = bias_info.get('external_high')
                        pool_low = bias_info.get('external_low')
                        
                        if pool_high is not None and pool_low is not None:
                            # Cerca sweep su ultima candela
                            last_candle = df_htf.iloc[-1]
                            o = float(last_candle["open"])
                            h = float(last_candle["high"])
                            l = float(last_candle["low"])
                            c = float(last_candle["close"])
                            
                            sweep = detect_sweep(
                                state.bias, pool_high, pool_low,
                                o, h, l, c, atr_htf, current_price
                            )
                            
                            if sweep:
                                # SWEEP trovato!
                                state.sweep_data = sweep
                                state.sweep_bar_index = len(df_htf) - 1
                                state.sweep_timestamp = datetime.now()
                                state.transition("WAIT_DISPLACEMENT", f"SWEEP {sweep['direction']}")
                                
                                logger.info(f"[{symbol}] SWEEP detected at {sweep['pool']:.2f}")
                    
                    elif state.status == "WAIT_DISPLACEMENT":
                        # STEP 2: Cerca DISPLACEMENT
                        # bars_since_sweep già incrementato!
                        
                        # Timeout check
                        max_bars = CONFIG.get("MAX_BARS_AFTER_SWEEP", 6)
                        if state.bars_since_sweep > max_bars:
                            state.reset("WAIT_SWEEP", f"Timeout: no displacement in {state.bars_since_sweep} bars")
                            state_manager.stats["timeouts_today"] += 1
                            continue
                        
                        # Cerca displacement su ultima candela
                        # (deve essere DOPO la candela di sweep!)
                        current_bar_index = len(df_htf) - 1
                        
                        if current_bar_index > state.sweep_bar_index:
                            last_candle = df_htf.iloc[-1]
                            o = float(last_candle["open"])
                            h = float(last_candle["high"])
                            l = float(last_candle["low"])
                            c = float(last_candle["close"])
                            
                            # Get swing highs/lows per BOS check
                            swing_highs, swing_lows = find_swing_highs_lows(df_htf, CONFIG["SWING_LEFT_RIGHT"])
                            
                            if swing_highs and swing_lows:
                                last_swing_high = swing_highs[-1] if swing_highs else None
                                last_swing_low = swing_lows[-1] if swing_lows else None
                                
                                # Get previous bar high/low per BOS
                                if len(df_htf) >= 3:
                                    h_i_2 = float(df_htf["high"].iloc[-3])
                                    l_i_2 = float(df_htf["low"].iloc[-3])
                                    
                                    displacement = detect_displacement_m15(
                                        state.bias, o, h, l, c, atr_htf,
                                        last_swing_high, last_swing_low,
                                        h_i_2, l_i_2, current_bar_index
                                    )
                                    
                                    if displacement:
                                        # DISPLACEMENT trovato!
                                        state.displacement_data = displacement
                                        state.displacement_bar_index = current_bar_index
                                        state.displacement_timestamp = datetime.now()
                                        state.last_displacement_high = displacement.get('disp_high', h)
                                        state.last_displacement_low = displacement.get('disp_low', l)
                                        state.transition("WAIT_RETRACE", f"DISPLACEMENT Grade {displacement['grade']}")
                                        
                                        logger.info(f"[{symbol}] DISPLACEMENT Grade {displacement['grade']}")
                    
                    elif state.status == "WAIT_RETRACE":
                        # STEP 3: Cerca RETRACE
                        # bars_since_displacement già incrementato!
                        
                        # Timeout check
                        max_bars = CONFIG.get("MAX_RETRACE_BARS", 8)
                        if state.bars_since_displacement > max_bars:
                            state.reset("WAIT_SWEEP", f"Timeout: no retrace in {state.bars_since_displacement} bars")
                            state_manager.stats["timeouts_today"] += 1
                            continue
                        
                        # Check invalidazione (prezzo oltre displacement)
                        invalidation_buffer = atr_htf * CONFIG.get("RETRACE_INVALIDATION_MULT", 0.05)
                        
                        if state.bias == "UP":
                            if current_price < (state.last_displacement_low - invalidation_buffer):
                                state.reset("WAIT_BIAS", "Displacement invalidated (price below low)")
                                state_manager.stats["invalidations_today"] += 1
                                continue
                        else:  # DOWN
                            if current_price > (state.last_displacement_high + invalidation_buffer):
                                state.reset("WAIT_BIAS", "Displacement invalidated (price above high)")
                                state_manager.stats["invalidations_today"] += 1
                                continue
                        
                        # Cerca retrace su ultima candela
                        last_candle = df_htf.iloc[-1]
                        o = float(last_candle["open"])
                        h = float(last_candle["high"])
                        l = float(last_candle["low"])
                        c = float(last_candle["close"])
                        
                        # Get displacement data
                        disp_dir = state.displacement_data.get('dir')
                        disp_fvg = state.displacement_data.get('fvg')
                        disp_high = state.displacement_data.get('disp_high', h)
                        disp_low = state.displacement_data.get('disp_low', l)
                        
                        retrace = detect_retrace_m15(
                            disp_dir, disp_fvg, disp_high, disp_low,
                            atr_htf, o, h, l, c,
                            state.bars_since_displacement  # CRITICAL: usato correttamente!
                        )
                        
                        if retrace['status'] == "HIT":
                            # RETRACE HIT!
                            state.retrace_data = retrace
                            state.retrace_bar_index = len(df_htf) - 1
                            state.retrace_timestamp = datetime.now()
                            state.transition("WAIT_CONFIRMATION", f"RETRACE HIT Grade {retrace['grade']}")
                            
                            logger.info(f"[{symbol}] RETRACE HIT Grade {retrace['grade']}")
                        elif retrace['status'] == "INVALIDATED":
                            state.reset("WAIT_BIAS", "Retrace invalidated")
                            state_manager.stats["invalidations_today"] += 1
                            continue
                    
                    elif state.status == "WAIT_CONFIRMATION":
                        # STEP 4: Cerca CONFIRMATION su M5
                        # bars_since_retrace già incrementato! (in barre M15)
                        
                        # Timeout check (converti da M15 a M5: 1 M15 = 3 M5)
                        max_bars_m15 = CONFIG.get("MAX_CONFIRM_BARS_M15", 4)
                        if state.bars_since_retrace > max_bars_m15:
                            state.reset("WAIT_SWEEP", f"Timeout: no confirmation in {state.bars_since_retrace} bars M15")
                            state_manager.stats["timeouts_today"] += 1
                            continue
                        
                        # Cerca confirmation su M5
                        last_candle_m5 = df_ltf.iloc[-1]
                        o5 = float(last_candle_m5["open"])
                        h5 = float(last_candle_m5["high"])
                        l5 = float(last_candle_m5["low"])
                        c5 = float(last_candle_m5["close"])
                        
                        # ATR M5
                        atr_m5_series = calculate_atr(df_ltf, CONFIG["ATR_PERIOD"])
                        atr_m5 = float(atr_m5_series.iloc[-1]) if not pd.isna(atr_m5_series.iloc[-1]) else atr_htf
                        
                        # Get retrace zone
                        zone_low = state.retrace_data.get('zone_low', 0)
                        zone_high = state.retrace_data.get('zone_high', 0)
                        
                        # Swing highs/lows M5
                        m5_swing_highs, m5_swing_lows = find_swing_highs_lows(df_ltf, CONFIG["SWING_LEFT_RIGHT"])
                        m5_swing_high = m5_swing_highs[-1] if m5_swing_highs else None
                        m5_swing_low = m5_swing_lows[-1] if m5_swing_lows else None
                        
                        if len(df_ltf) >= 3 and m5_swing_high and m5_swing_low:
                            h5_i_2 = float(df_ltf["high"].iloc[-3])
                            l5_i_2 = float(df_ltf["low"].iloc[-3])
                            
                            confirmation = detect_confirm_m5(
                                state.displacement_data.get('dir'),
                                zone_low, zone_high,
                                o5, h5, l5, c5, atr_m5,
                                m5_swing_high, m5_swing_low,
                                h5_i_2, l5_i_2,
                                state.bars_since_retrace  # CRITICAL: usato correttamente!
                            )
                            
                            if confirmation['status'] == "CONFIRMED":
                                # CONFIRMATION trovata!
                                state.confirmation_data = confirmation
                                state.confirmation_bar_index = len(df_ltf) - 1
                                state.confirmation_timestamp = datetime.now()
                                state.transition("SETUP_COMPLETE", f"CONFIRMATION Grade {confirmation['grade']}")
                                
                                logger.info(f"[{symbol}] CONFIRMATION Grade {confirmation['grade']}")
                                state_manager.stats["setups_complete_today"] += 1
                            elif confirmation['status'] == "EXPIRED":
                                state.reset("WAIT_SWEEP", "Confirmation timeout")
                                state_manager.stats["timeouts_today"] += 1
                                continue
                    
                    elif state.status == "SETUP_COMPLETE":
                        # STEP 5: ENTRY LOGIC
                        # bars_since_confirmation già incrementato! (in barre M5 virtuali)
                        
                        # Timeout entry (6 barre M5 = 30 min)
                        max_bars_entry = CONFIG.get("MAX_ENTRY_BARS_M5", 6)
                        if state.bars_since_confirmation > max_bars_entry:
                            state.reset("WAIT_SWEEP", "Entry timeout")
                            state_manager.stats["timeouts_today"] += 1
                            continue
                        
                        # Generate entry
                        last_candle_m5 = df_ltf.iloc[-1]
                        h5 = float(last_candle_m5["high"])
                        l5 = float(last_candle_m5["low"])
                        c5 = float(last_candle_m5["close"])
                        
                        confirm_high = state.confirmation_data.get('confirm_high', h5)
                        confirm_low = state.confirmation_data.get('confirm_low', l5)
                        
                        entry = generate_entry(
                            state.displacement_data.get('dir'),
                            confirm_high, confirm_low,
                            state.bars_since_confirmation  # CRITICAL: usato correttamente!
                        )
                        
                        if entry['status'] == "READY":
                            # ENTRY READY!
                            signal = "LONG" if state.bias == "UP" else "SHORT"
                            entry_price = entry['entry_price']
                            
                            # Calculate SL and TP
                            sl_price = calculate_structural_sl(state, atr_htf)
                            tp_price = calculate_tp_from_risk(entry_price, sl_price, CONFIG.get("TP_RISK_MULTIPLE", 2.0))
                            
                            # Open position
                            success = account.open_position(symbol, signal, entry_price, sl_price, tp_price)
                            
                            if success:
                                logger.info(f"[{symbol}] POSITION OPENED: {signal} @ {entry_price:.2f}")
                                print(f"\n{'='*70}")
                                print(f"🎯 SETUP COMPLETO: {symbol} {signal}")
                                print(f"{'='*70}")
                                print(f"Entry: ${entry_price:.2f}")
                                print(f"Stop Loss: ${sl_price:.2f}")
                                print(f"Take Profit: ${tp_price:.2f}")
                                print(f"R:R: 1:{CONFIG.get('TP_RISK_MULTIPLE', 2.0):.1f}")
                                print(f"{'='*70}\n")
                                
                                # Reset per nuovo setup
                                state.reset("WAIT_BIAS", "Position opened")
                        
                        elif entry['status'] == "EXPIRED":
                            state.reset("WAIT_SWEEP", "Entry expired")
                            state_manager.stats["timeouts_today"] += 1
                            continue
                    
                    # Check exit per posizioni aperte
                    position = account.get_position(symbol)
                    if position:
                        # Check SL/TP
                        if position['side'] == "LONG":
                            if current_price <= position['stop_loss']:
                                account.close_position(symbol, current_price, "Stop Loss")
                                logger.info(f"[{symbol}] Position closed: Stop Loss hit")
                            elif current_price >= position['take_profit']:
                                account.close_position(symbol, current_price, "Take Profit")
                                logger.info(f"[{symbol}] Position closed: Take Profit hit")
                        else:  # SHORT
                            if current_price >= position['stop_loss']:
                                account.close_position(symbol, current_price, "Stop Loss")
                                logger.info(f"[{symbol}] Position closed: Stop Loss hit")
                            elif current_price <= position['take_profit']:
                                account.close_position(symbol, current_price, "Take Profit")
                                logger.info(f"[{symbol}] Position closed: Take Profit hit")
                
                except Exception as e:
                    logger.error(f"[{symbol}] Error: {e}", exc_info=True)
                    continue
            
            # Status table ogni 5 minuti
            current_time = time.time()
            if current_time - last_status_print >= 300:  # 5 minuti
                print_status_table(state_manager, account)
                last_status_print = current_time
            
            # Sleep
            time.sleep(CONFIG.get("LOOP_INTERVAL", 60))
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Bot interrotto dall'utente")
        
        # Report finale
        print_final_report(account, state_manager)
    
    except Exception as e:
        logger.error(f"Fatal error in main loop: {e}", exc_info=True)
        print(f"\n❌ Errore fatale: {e}")
    
    finally:
        # Cleanup
        logger.info("Bot terminato")


def print_status_table(state_manager: ICTStateManager, account: PaperAccount) -> None:
    """Stampa tabella status di tutte le coppie"""
    print("\n" + "="*80)
    print(f"📊 STATUS UPDATE - {datetime.now().strftime('%H:%M:%S')}")
    print("="*80)
    
    summary = state_manager.get_summary()
    hot_setups = state_manager.get_hot_setups()
    
    for symbol, info in summary.items():
        status_emoji = ""
        if symbol in hot_setups:
            status_emoji = "⚡"
        
        print(f"{symbol:12} {info['status']:20} (BIAS: {info['bias']:4}) {info['age']:15} {status_emoji}")
    
    print("="*80)
    print(f"⚡ Hot Setups: {len(hot_setups)} | Today: {state_manager.stats['setups_complete_today']} complete, "
          f"{state_manager.stats['timeouts_today']} timeouts, {state_manager.stats['invalidations_today']} invalidations")
    
    # Account status
    stats = account.get_statistics()
    print(f"💰 Balance: ${account.equity:.2f} | P&L: ${stats['total_pnl']:+.2f} | ROI: {stats.get('roi', 0.0):+.2f}%")
    print("="*80 + "\n")


def print_final_report(account: PaperAccount, state_manager: ICTStateManager) -> None:
    """Report finale alla chiusura"""
    print("\n" + "="*80)
    print("📋 REPORT FINALE")
    print("="*80)
    
    stats = account.get_statistics()
    
    print(f"Capitale iniziale: ${CONFIG['INITIAL_CAPITAL']:,.2f}")
    print(f"Capitale finale: ${account.equity:,.2f}")
    print(f"P&L Totale: ${stats['total_pnl']:+,.2f}")
    print(f"ROI: {stats.get('roi', 0.0):+.2f}%")
    print()
    print(f"Trade totali: {stats['total_trades']}")
    print(f"Win: {stats['winning_trades']} | Loss: {stats['losing_trades']}")
    print(f"Win Rate: {stats['win_rate']:.1f}%")
    print(f"P&L medio: ${stats['avg_pnl']:+.2f}")
    print()
    print(f"Setup completati oggi: {state_manager.stats['setups_complete_today']}")
    print(f"Timeout oggi: {state_manager.stats['timeouts_today']}")
    print(f"Invalidazioni oggi: {state_manager.stats['invalidations_today']}")
    print("="*80)
    
    # Export Excel
    try:
        export_to_excel(account, ict_logger)
        print("\n✅ Report Excel esportato con successo")
    except Exception as e:
        print(f"\n⚠️ Errore export Excel: {e}")


def calculate_structural_sl(state: ICTSetupState, atr: float) -> float:
    """Calcola SL strutturale basato su displacement/retrace"""
    if state.bias == "UP":
        # SL sotto displacement low
        sl = state.last_displacement_low - (atr * CONFIG.get("SL_ATR_BUFFER", 0.05))
    else:
        # SL sopra displacement high
        sl = state.last_displacement_high + (atr * CONFIG.get("SL_ATR_BUFFER", 0.05))
    
    return sl


def calculate_tp_from_risk(entry: float, sl: float, risk_multiple: float) -> float:
    """Calcola TP basato su risk multiple"""
    risk = abs(entry - sl)
    
    if entry > sl:  # LONG
        tp = entry + (risk * risk_multiple)
    else:  # SHORT
        tp = entry - (risk * risk_multiple)
    
    return tp



if __name__ == "__main__":
    main()
