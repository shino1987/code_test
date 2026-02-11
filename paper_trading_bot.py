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
from datetime import datetime
from decimal import Decimal, ROUND_DOWN
import ccxt
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple

# ===================== CONFIGURAZIONE =====================
CONFIG = {
    # Capitale iniziale
    "INITIAL_CAPITAL": 10000.0,  # $10,000 USDT simulati
    
    # Exchange e Mercati
    "EXCHANGE": "binance",
    "SYMBOLS": ["BTC/USDT", "ETH/USDT"],  # Mercati da monitorare
    
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
    
    # Risk Management
    "RISK_PER_TRADE": 0.02,  # 2% del capitale per trade
    "STOP_LOSS_PCT": 0.015,  # Stop Loss al 1.5%
    "TAKE_PROFIT_PCT": 0.03, # Take Profit al 3%
    
    # Limiti
    "MAX_POSITIONS": 2,  # Massimo 2 posizioni aperte contemporaneamente
    
    # Loop
    "LOOP_INTERVAL": 60,  # Secondi tra ogni ciclo (1 minuto per M5)
    
    # Logging
    "TRADES_LOG": "paper_trades.csv",
    "BALANCE_LOG": "paper_balance.csv",
    "BIAS_LOG": "paper_bias_log.csv",
    
    # Telegram (opzionale)
    "TELEGRAM_ENABLED": False,
}


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
        if not self.closed_trades:
            return {
                "total_trades": 0,
                "winning_trades": 0,
                "losing_trades": 0,
                "win_rate": 0.0,
                "total_pnl": 0.0,
                "avg_pnl": 0.0
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
            "roi": ((self.equity - self.initial_capital) / self.initial_capital * 100)
        }


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
    """Loop principale del bot"""
    print("="*70)
    print("PAPER TRADING BOT - ICT BIAS DETECTION SYSTEM")
    print("="*70)
    print(f"Capitale iniziale: ${CONFIG['INITIAL_CAPITAL']:,.2f}")
    print(f"Simboli: {', '.join(CONFIG['SYMBOLS'])}")
    print(f"HTF (BIAS): {CONFIG['HTF']} | LTF (ENTRY): {CONFIG['LTF']}")
    print(f"Swing Detection: Fractal L/R={CONFIG['SWING_LEFT_RIGHT']}")
    print(f"Strategia: ICT Liquidity + Structure + Compression")
    print("="*70)
    print()
    
    # Inizializza
    exchange = init_exchange()
    account = PaperAccount(CONFIG["INITIAL_CAPITAL"])
    
    loop_count = 0
    
    try:
        while True:
            loop_count += 1
            print(f"\n{'='*70}")
            print(f"[LOOP {loop_count}] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"{'='*70}")
            
            current_prices = {}
            
            # Analizza ogni simbolo
            for symbol in CONFIG["SYMBOLS"]:
                try:
                    print(f"\n[{symbol}]")
                    
                    # Scarica dati HTF e LTF
                    df_htf = fetch_ohlcv(exchange, symbol, CONFIG["HTF"], limit=CONFIG["HTF_LOOKBACK"])
                    df_ltf = fetch_ohlcv(exchange, symbol, CONFIG["LTF"], limit=CONFIG["LTF_LOOKBACK"])
                    
                    if df_htf.empty or df_ltf.empty:
                        print(f"  [SKIP] Dati insufficienti")
                        continue
                    
                    current_price = float(df_ltf["close"].iloc[-1])
                    current_prices[symbol] = current_price
                    
                    print(f"  Prezzo: ${current_price:,.2f}")
                    
                    # 1. COMPUTE BIAS su HTF
                    bias_info = compute_bias(df_htf, CONFIG["SWING_LEFT_RIGHT"])
                    bias = bias_info["bias"]
                    
                    print(f"  BIAS HTF: {bias} ({bias_info.get('reason', 'N/A')})")
                    
                    # Log dettagli bias
                    if "external_high" in bias_info:
                        print(f"    External High: ${bias_info['external_high']:,.2f}")
                        print(f"    External Low: ${bias_info['external_low']:,.2f}")
                    
                    # Controlla posizione esistente
                    position = account.get_position(symbol)
                    
                    if position:
                        # Controlla exit
                        exit_reason = check_exit_signal(position, current_price)
                        if exit_reason:
                            account.close_position(symbol, current_price, exit_reason)
                    else:
                        # Controlla entry (solo se sotto il limite di posizioni)
                        if len(account.positions) < CONFIG["MAX_POSITIONS"]:
                            signal = check_entry_signal(bias, df_ltf)
                            
                            if signal:
                                print(f"  [SIGNAL] {signal} detected!")
                                
                                # Calcola size basato sul risk management
                                risk_amount = account.get_balance() * CONFIG["RISK_PER_TRADE"]
                                position_size = risk_amount / current_price
                                
                                # Calcola SL e TP
                                if signal == "LONG":
                                    stop_loss = current_price * (1 - CONFIG["STOP_LOSS_PCT"])
                                    take_profit = current_price * (1 + CONFIG["TAKE_PROFIT_PCT"])
                                else:  # SHORT
                                    stop_loss = current_price * (1 + CONFIG["STOP_LOSS_PCT"])
                                    take_profit = current_price * (1 - CONFIG["TAKE_PROFIT_PCT"])
                                
                                # Apri posizione
                                account.open_position(
                                    symbol, signal, current_price,
                                    position_size, stop_loss, take_profit
                                )
                
                except Exception as e:
                    print(f"[ERROR] Elaborazione {symbol}: {e}")
                    import traceback
                    traceback.print_exc()
                    continue
            
            # Aggiorna equity
            account.update_equity(current_prices)
            
            # Stampa stato account
            print(f"\n{'='*70}")
            print(f"ACCOUNT STATUS:")
            print(f"  Balance: ${account.get_balance():,.2f}")
            print(f"  Equity: ${account.get_equity():,.2f}")
            print(f"  Posizioni aperte: {len(account.positions)}")
            
            stats = account.get_statistics()
            if stats["total_trades"] > 0:
                print(f"\nSTATISTICHE:")
                print(f"  Trades totali: {stats['total_trades']}")
                print(f"  Win Rate: {stats['win_rate']:.2f}%")
                print(f"  PnL totale: ${stats['total_pnl']:,.2f}")
                print(f"  ROI: {stats['roi']:+.2f}%")
            
            print(f"{'='*70}")
            
            # Attendi prossimo loop
            time.sleep(CONFIG["LOOP_INTERVAL"])
    
    except KeyboardInterrupt:
        print("\n\n[STOP] Bot fermato dall'utente")
        print(f"\n{'='*70}")
        print("REPORT FINALE")
        print(f"{'='*70}")
        
        stats = account.get_statistics()
        print(f"Capitale iniziale: ${account.initial_capital:,.2f}")
        print(f"Capitale finale: ${account.get_equity():,.2f}")
        print(f"PnL totale: ${stats['total_pnl']:,.2f}")
        print(f"ROI: {stats['roi']:+.2f}%")
        print(f"Trades totali: {stats['total_trades']}")
        print(f"Win Rate: {stats['win_rate']:.2f}%")
        print(f"{'='*70}")


if __name__ == "__main__":
    main()
