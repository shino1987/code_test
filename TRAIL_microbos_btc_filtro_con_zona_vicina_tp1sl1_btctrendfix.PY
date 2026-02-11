# -*- coding: utf-8 -*-
# ===================== ICT SMART MONEY BOT (LIVE CROSS MARGIN) v9.8 =====================
# Logica:
#   Bias 30m -> Entry 5m:
#   WAIT_SWEEP -> WAIT_DISPLACEMENT -> WAIT_RETRACE -> WAIT_CONFIRM -> OPEN
#
# NOVITÀ (richiesta):
# ✅ Stop Loss STRUTTURALE ICT calcolato su TF 15m (NON 5m)
# ✅ CAP massimo SL: se SL strutturale supera -0.65% -> forza SL a -0.65%
# ✅ Telegram OPEN: stampa SL prezzo + % + tipo (STRUCT_15M oppure CAP_0.65%)
#
# Fix errori Binance:
# ✅ -1013 Filter failure LOT_SIZE -> quantità sempre allineata a stepSize + minQty
# ✅ 51077 precision over max -> quantizzazione robusta (no troppe decimali)
#
# NOTE IMPORTANTI:
# - CROSS margin (no isIsolated)
# - Close LONG: vende base free (Cross)
# - Close SHORT: compra usando quantità tracciata (amount)
# - TP: iniziale 0.50% (GROSS). Poi TP a gradini (senza nuovi messaggi Telegram).

import os
import time
import csv
from datetime import datetime
import math
import requests
import pandas as pd
import ccxt
from collections import Counter
from decimal import Decimal, ROUND_DOWN, getcontext

getcontext().prec = 28

# ===================== CONFIG =====================
BIAS_TF = "30m"
ENTRY_TF = "5m"
SL_TF = "15m"            # <<< SL strutturale su 15 minuti
LTF = "5m"               # <<< LTF (Lower Time Frame) for confirmation
LOOP_SEC = 25

MAX_OPEN_POS = 3

LOOKBACK_BIAS = 260
LOOKBACK_ENTRY = 320
LOOKBACK_SL = 220        # abbastanza per swing 15m
LOOKBACK_LTF = 320       # lookback for M5 confirmation

MIN_STRUCT_SL_PCT = 0.0035  # 0.35%

TP_LADDER_PCTS = [0.0120]   # TP0 = 1.20%
TP_AFTER_LAST_STEP = 0.0025  # +0.25% fisso


# ===== BTC CONFLICT FILTER (OB 15m con 2 rifiuti) =====
BTC_SYMBOL = "BTC/USDC"
BTC_TF = "15m"
BTC_LOOKBACK = 260

BTC_NEAR_PCT = 0.0040        # 0.40%
BTC_REJ_MIN = 2              # almeno 2 rifiuti
BTC_REJ_LOOKBACK = 120       # ~30 ore
BTC_REJ_COOLDOWN = 4         # 4x15m = 1h, evita doppio conteggio


# ===== BTC REJECTION ZONES (15m, >= 4 giorni) =====
BTC_ZONE_TF = "15m"
BTC_ZONE_DAYS = 4
BTC_ZONE_LOOKBACK = BTC_ZONE_DAYS * 24 * 4   # 384

BTC_ZONE_CLUSTER_PCT = 0.0020    # 0.20%
BTC_ZONE_NEAR_PCT    = 0.0040    # 0.40%
BTC_ZONE_MIN_REJ     = 2         # minimo 2 rifiuti

BTC_ZONE_REJECT_WINDOW   = 8      # 2 ore
BTC_ZONE_REJECT_MOVE_PCT = 0.0150 # 1.50%

BTC_ZONE_BREAK_PCT = 0.0010      # 0.10%

# ===== BTC TREND FILTER (15m) =====
BTC_TREND_LR = 2   # fractal LR per capire trend BTC su 15m (indipendente da SWING_LR_SL)

# ---- WHITELIST MERCATI LIQUIDI (USDC) ----
SYMBOLS = [
    "BTC/USDC", "ETH/USDC", "BNB/USDC", "SOL/USDC",
    "XRP/USDC", "ADA/USDC", "DOGE/USDC", "AVAX/USDC",
    "LINK/USDC", "MATIC/USDC", "LTC/USDC", "TRX/USDC",
    "DOT/USDC", "ATOM/USDC", "NEAR/USDC", "APT/USDC",
    "OP/USDC", "ARB/USDC", "UNI/USDC", "FIL/USDC",
    "INJ/USDC", "AAVE/USDC", "ETC/USDC", "XLM/USDC",
    "SUI/USDC",
]

TRADES_CSV_PATH = "trades_log.csv"


# ===== TARGETS =====
TP_GROSS_PCT = 0.0120            # TP0 iniziale = +1.20%
SL_CAP_PCT = 0.0065              # CAP massimo SL: -0.65%
SL_FIXED_PCT = 0.0100   # SL fisso 1.00%


# (opzionale) fee stimata SOLO per report/telegram, non per logica di prezzo
ROUND_TRIP_FEE_PCT = 0.0020      # 0.20% stimata

# ===== PROFIT LOCK + TP LADDER =====
# Tolleranza ritracciamento = 0.30% => SL = TP - 0.30%
LOCK_RETRACE_PCT = 0.0030

# ===== LIVE TRADING =====
LIVE_TRADING = True
TRADE_USDC_TARGET = 200.0
MIN_NOTIONAL_PAD = 1.05

# Swings (fractal)
SWING_LR_BIAS = 2
SWING_LR_ENTRY = 2
SWING_LR_SL = 2
SWING_LR = 2             # Default swing LR for M5

# Sweep
SWEEP_BUFFER_PCT = 0.00025

# Displacement
AVG_RANGE_LEN = 20
DISP_RANGE_MULT = 1.25
DISP_BODY_RATIO = 0.55

# OB / FVG
OB_LOOKBACK = 6
FVG_MIN_SIZE_PCT = 0.00010

# Buffer strutturale SL (piccolo margine oltre swing/OB)
STRUCT_SL_BUFFER_PCT = 0.00020  # 0.02%

# Confirm configuration (M5)
MAX_CONFIRM_BARS = 12            # Max bars M5 for confirm (≈60 min)
ZONE_BUFFER_ATR_MULT = 0.25      # 25% ATR buffer for zone proximity
MICRO_BOS_BUFFER_ATR_MULT = 0.02 # 2% ATR for micro BOS
CONFIRM_IMPULSE_MULT = 0.60      # Range must be >= 0.6 ATR
CONFIRM_BODY_RATIO = 0.50        # Body must be >= 50% of range

pending = {}
positions = {}

# ===================== DEBUG =====================
DEBUG_TERMINAL = True
HEARTBEAT_EVERY_LOOPS = 3
PRINT_PENDING_SAMPLE = 8
loop_count = 0

# ===================== TELEGRAM =====================
TG_TOKEN = os.getenv("TG_BOT_TOKEN")
TG_CHAT_ID = os.getenv("TG_CHAT_ID")

def tg_send(msg: str):
    try:
        if not TG_TOKEN or not TG_CHAT_ID:
            print("[TG] Variabili mancanti: TG_BOT_TOKEN o TG_CHAT_ID", flush=True)
            return False
        url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
        r = requests.post(url, json={"chat_id": TG_CHAT_ID, "text": msg}, timeout=15)
        if r.status_code != 200:
            print("[TG] HTTP", r.status_code, r.text, flush=True)
            return False
        return True
    except Exception as e:
        print("[TG] Exception:", e, flush=True)
        return False

# ===================== EXCHANGE =====================
print("Avvio... collegamento Binance (CCXT)", flush=True)
ex = ccxt.binance({
    "apiKey": os.getenv("BINANCE_API_KEY"),
    "secret": os.getenv("BINANCE_API_SECRET"),
    "enableRateLimit": True,
    "timeout": 60000,
    "options": {
        "adjustForTimeDifference": True,
        "recvWindow": 60000,
        "fetchCurrencies": False,
    }
})

print("API KEY LEN:", len(os.getenv("BINANCE_API_KEY") or ""), flush=True)
print("API SECRET LEN:", len(os.getenv("BINANCE_API_SECRET") or ""), flush=True)

print("Carico mercati...", flush=True)
ok = False
for attempt in range(5):
    try:
        ex.load_markets()
        ok = True
        break
    except Exception as e:
        wait = 3 + attempt * 3
        print(f"load_markets error attempt {attempt+1}/5 -> retry in {wait}s | {e}", flush=True)
        time.sleep(wait)

if not ok:
    print("ERRORE: impossibile caricare mercati Binance (dopo 5 tentativi). Chiudo.", flush=True)
    raise SystemExit(1)

try:
    st = ex.fetch_time()
    lt = ex.milliseconds()
    print("SERVER TIME:", st, "LOCAL:", lt, "DIFF(ms):", lt - st, flush=True)
except Exception as e:
    print("WARN fetch_time:", e, flush=True)

def to_binance_symbol(sym: str) -> str:
    return sym.replace("/", "")

print("Mercati caricati OK", flush=True)
print(f"Cross Margin symbols attivi: {len(SYMBOLS)}", flush=True)
tg_send("✅ Crypto ICT bot avviato (v9.8 LIVE Cross Margin) - invierò SOLO OPEN e CLOSE")

# ===================== FETCH (robusto) =====================
def fetch_df(symbol: str, tf: str, limit: int) -> pd.DataFrame:
    for attempt in range(4):
        try:
            ohlcv = ex.fetch_ohlcv(symbol, timeframe=tf, limit=limit)
            if not ohlcv:
                raise Exception("Empty OHLCV")
            return pd.DataFrame(ohlcv, columns=["ts", "open", "high", "low", "close", "vol"])
        except Exception as e:
            wait = 3 + attempt * 3
            print(f"[{symbol}] fetch error tf={tf} attempt {attempt+1}/4 -> retry in {wait}s | {e}", flush=True)
            time.sleep(wait)
    print(f"[{symbol}] fetch FAILED tf={tf} -> skipped", flush=True)
    return pd.DataFrame()

# ===================== HELPERS =====================
def find_swings(df: pd.DataFrame, lr: int = 2):
    highs = df["high"].astype(float).values
    lows = df["low"].astype(float).values
    swing_highs = []
    swing_lows = []
    for i in range(lr, len(df) - lr):
        h = highs[i]; l = lows[i]
        if all(h > highs[i - k] for k in range(1, lr + 1)) and all(h > highs[i + k] for k in range(1, lr + 1)):
            swing_highs.append((i, float(h)))
        if all(l < lows[i - k] for k in range(1, lr + 1)) and all(l < lows[i + k] for k in range(1, lr + 1)):
            swing_lows.append((i, float(l)))
    return swing_highs, swing_lows

def candle_stats(row):
    o = float(row["open"])
    h = float(row["high"])
    l = float(row["low"])
    c = float(row["close"])
    rng = max(h - l, 1e-12)
    body = abs(c - o)
    return {
        "o": o, "h": h, "l": l, "c": c,
        "range": rng,
        "body_ratio": body / rng,
        "bull": c > o,
        "bear": c < o
    }


def has_room_to_tp(entry: float, side: str, tp_pct: float, df15: pd.DataFrame, lookback: int = 140) -> bool:
    """
    FILTRO "ROOM TO TP" su TF 15m:
    - LONG: se esiste uno swing-high (resistenza) sopra entry ma sotto TP0 -> NO ROOM
    - SHORT: se esiste uno swing-low (supporto) sotto entry ma sopra TP0 -> NO ROOM

    lookback=140 ~ circa 35 ore di 15m (140*15min).
    """
    try:
        if df15 is None or df15.empty or len(df15) < 20:
            return True  # non ho dati => non filtro

        entry = float(entry)
        tp_pct = float(tp_pct)
        side = str(side).upper()

        df = df15.iloc[:-1].tail(int(lookback)).copy()

        sh, sl = find_swings(df, lr=SWING_LR_SL)

        if side == "LONG":
            tp0 = entry * (1.0 + tp_pct)

            # Trova il primo swing-high sopra entry (il più vicino, andando a ritroso)
            for _, h in reversed(sh):
                h = float(h)
                if h > entry:
                    # se questa resistenza è prima di TP0 => poco spazio => skip
                    if h < tp0:
                        return False
                    # se è oltre TP0 => ok
                    return True

            # nessuna resistenza sopra entry trovata => ok
            return True

        else:  # SHORT
            tp0 = entry * (1.0 - tp_pct)

            # Trova il primo swing-low sotto entry (il più vicino, andando a ritroso)
            for _, l in reversed(sl):
                l = float(l)
                if l < entry:
                    # se questo supporto è prima di TP0 (cioè sopra tp0) => poco spazio => skip
                    if l > tp0:
                        return False
                    return True

            # nessun supporto sotto entry trovato => ok
            return True

    except Exception as e:
        if DEBUG_TERMINAL:
            print(f"[has_room_to_tp] WARN: {e}", flush=True)
        return True

def _cluster_by_pct(prices, cluster_pct: float):
    clusters = []
    for idx, p in prices:
        p = float(p)
        placed = False
        for cl in clusters:
            center = cl["center"]
            if abs(p - center) / max(center, 1e-12) <= cluster_pct:
                cl["items"].append((idx, p))
                cl["center"] = sum(x[1] for x in cl["items"]) / len(cl["items"])
                placed = True
                break
        if not placed:
            clusters.append({"center": p, "items": [(idx, p)]})
    return clusters

def detect_btc_rejection_zones(df15: pd.DataFrame):
    if df15 is None or df15.empty or len(df15) < 120:
        return [], []

    # solo candele chiuse
    df = df15.iloc[:-1].tail(int(BTC_ZONE_LOOKBACK)).copy()
    if len(df) < 120:
        return [], []

    highs = df["high"].astype(float).values
    lows  = df["low"].astype(float).values
    closes = df["close"].astype(float).values

    # 1) candidati touch = TUTTI gli high/low
    high_touches = [(i, highs[i]) for i in range(len(df))]
    low_touches  = [(i, lows[i])  for i in range(len(df))]

    # 2) clusterizza
    high_clusters = _cluster_by_pct(high_touches, BTC_ZONE_CLUSTER_PCT)
    low_clusters  = _cluster_by_pct(low_touches,  BTC_ZONE_CLUSTER_PCT)

    supply_zones = []
    demand_zones = []

    # helper: verifica rifiuto dopo touch
    def rejected_after_touch_supply(i, price_high):
        end = min(len(df) - 1, i + BTC_ZONE_REJECT_WINDOW)
        # reazione = drawdown dal massimo toccato
        min_low_after = float(min(lows[i:end+1]))
        drop_pct = (float(price_high) - min_low_after) / max(float(price_high), 1e-12)
        return drop_pct >= BTC_ZONE_REJECT_MOVE_PCT

    def rejected_after_touch_demand(i, price_low):
        end = min(len(df) - 1, i + BTC_ZONE_REJECT_WINDOW)
        max_high_after = float(max(highs[i:end+1]))
        bounce_pct = (max_high_after - float(price_low)) / max(float(price_low), 1e-12)
        return bounce_pct >= BTC_ZONE_REJECT_MOVE_PCT

    # 3) Supply: cluster di high con almeno 2 rifiuti
    for cl in high_clusters:
        items = cl["items"]
        valid = [(i, p) for (i, p) in items if rejected_after_touch_supply(i, p)]
        if len(valid) < BTC_ZONE_MIN_REJ:
            continue

        prices = [p for _, p in valid]
        z_low, z_high = float(min(prices)), float(max(prices))
        last_idx = max(i for i, _ in valid)

        # invalidazione: close sopra zona + buffer
        broken = any(float(closes[k]) > z_high * (1.0 + BTC_ZONE_BREAK_PCT) for k in range(last_idx, len(df)))
        if broken:
            continue

        supply_zones.append({"low": z_low, "high": z_high, "count": len(valid), "last_idx": int(last_idx)})

    # 4) Demand: cluster di low con almeno 2 rifiuti
    for cl in low_clusters:
        items = cl["items"]
        valid = [(i, p) for (i, p) in items if rejected_after_touch_demand(i, p)]
        if len(valid) < BTC_ZONE_MIN_REJ:
            continue

        prices = [p for _, p in valid]
        z_low, z_high = float(min(prices)), float(max(prices))
        last_idx = max(i for i, _ in valid)

        broken = any(float(closes[k]) < z_low * (1.0 - BTC_ZONE_BREAK_PCT) for k in range(last_idx, len(df)))
        if broken:
            continue

        demand_zones.append({"low": z_low, "high": z_high, "count": len(valid), "last_idx": int(last_idx)})

    # più recenti prima
    supply_zones.sort(key=lambda z: z["last_idx"], reverse=True)
    demand_zones.sort(key=lambda z: z["last_idx"], reverse=True)

    return supply_zones, demand_zones
def debug_btc_selected_2_zones():
    df_btc = fetch_df(BTC_SYMBOL, BTC_ZONE_TF, BTC_ZONE_LOOKBACK + 10)
    if df_btc.empty or len(df_btc) < 120:
        print("[BTC FILTER ZONES] no_data", flush=True)
        return

    btc_price = float(df_btc["close"].astype(float).iloc[-1])
    supply, demand = detect_btc_rejection_zones(df_btc)

    # ---- SUPPLY scelta (stessa logica del filtro) ----
    sup = None
    if supply:
        above = [z for z in supply if float(z["low"]) > btc_price]
        inside = [z for z in supply if float(z["low"]) <= btc_price <= float(z["high"])]

        if above:
            sup = min(above, key=lambda zz: float(zz["low"]))   # prima supply sopra
        elif inside:
            sup = min(inside, key=lambda zz: float(zz["low"]))  # fallback: supply che contiene

    # ---- DEMAND scelta (stessa logica del filtro) ----
    dem = None
    if demand:
        below = [z for z in demand if float(z["high"]) < btc_price]
        inside = [z for z in demand if float(z["low"]) <= btc_price <= float(z["high"])]

        if below:
            dem = max(below, key=lambda zz: float(zz["high"]))  # prima demand sotto
        elif inside:
            dem = max(inside, key=lambda zz: float(zz["high"])) # fallback: demand che contiene

    if sup:
        s_low, s_high = float(sup["low"]), float(sup["high"])
        dist = (s_low - btc_price) / max(btc_price, 1e-12) if btc_price < s_low else 0.0
        print(f"[BTC FILTER ZONES] BTC={btc_price:.2f} | SUPPLY_USED low={s_low:.2f} high={s_high:.2f} rej={sup['count']} dist={dist*100:.2f}%", flush=True)
    else:
        print(f"[BTC FILTER ZONES] BTC={btc_price:.2f} | SUPPLY_USED none", flush=True)

    if dem:
        d_low, d_high = float(dem["low"]), float(dem["high"])
        dist = (btc_price - d_high) / max(btc_price, 1e-12) if btc_price > d_high else 0.0
        print(f"[BTC FILTER ZONES] BTC={btc_price:.2f} | DEMAND_USED low={d_low:.2f} high={d_high:.2f} rej={dem['count']} dist={dist*100:.2f}%", flush=True)
    else:
        print(f"[BTC FILTER ZONES] BTC={btc_price:.2f} | DEMAND_USED none", flush=True)


def btc_blocks_trade_by_rejection_zone(alt_side: str) -> (bool, str):
    df_btc = fetch_df(BTC_SYMBOL, BTC_ZONE_TF, BTC_ZONE_LOOKBACK + 10)
    if df_btc.empty or len(df_btc) < 120:
        return False, "btc_no_data"

    btc_price = float(df_btc["close"].astype(float).iloc[-1])

    # ✅ NUOVO: se BTC è "fluido" (trend pulito) su 15m -> NON bloccare ALT
    if btc_is_fluido_15m(df_btc):
        if DEBUG_TERMINAL:
            print("[BTC FILTER] BTC fluido 15m -> skip ALL blocking filters (allow ALTs)", flush=True)
        return False, "btc_fluido_15m_allow_alts"


    # ✅ NUOVO: se BTC è in trend (15m), NON bloccare le ALT e salta il filtro supply/demand
    is_trend, trend_dir = btc_is_trending(df_btc)
    if is_trend:
        if DEBUG_TERMINAL:
            print(f"[BTC FILTER] BTC trending {trend_dir} -> skip supply/demand filter", flush=True)
        return False, f"btc_trending_{trend_dir}_allow_alts"

    supply, demand = detect_btc_rejection_zones(df_btc)

    alt_side = alt_side.upper()

    if alt_side == "LONG":
        if not supply:
            return False, "btc_no_supply"

        # ✅ SUPPLY "sopra" o "che contiene" il prezzo:
        # - contiene: low <= price <= high
        # - sopra: low > price
        above = [z for z in supply if float(z["low"]) > btc_price]
        inside = [z for z in supply if float(z["low"]) <= btc_price <= float(z["high"])]

        if above:
            z = min(above, key=lambda zz: float(zz["low"]))   # prima supply sopra
        elif inside:
            z = min(inside, key=lambda zz: float(zz["low"]))  # fallback: supply che contiene
        else:
            return False, "btc_no_supply_above"

        z_low, z_high = float(z["low"]), float(z["high"])


        # ✅ se BTC è dentro, lascio lavorare
        if z_low <= btc_price <= z_high:
            return False, f"btc_supply_inside_allow_rej{z['count']}"

        # ✅ blocco solo se BTC è SOTTO e vicino al bordo basso della supply scelta
        # (cioè sta arrivando sotto una resistenza)
        if btc_price < z_low:
            dist = (z_low - btc_price) / max(btc_price, 1e-12)
            if dist <= BTC_ZONE_NEAR_PCT:
                return True, f"btc_supply_above_near{dist*100:.2f}%_rej{z['count']}"

        return False, "btc_supply_above_far"

    else:  # SHORT ALT
        if not demand:
            return False, "btc_no_demand"

        # ✅ DEMAND "sotto" o "che contiene" il prezzo:
        # - contiene: low <= price <= high
        # - sotto: high < price
        below = [z for z in demand if float(z["high"]) < btc_price]
        inside = [z for z in demand if float(z["low"]) <= btc_price <= float(z["high"])]

        if below:
            z = max(below, key=lambda zz: float(zz["high"]))  # prima demand sotto
        elif inside:
            z = max(inside, key=lambda zz: float(zz["high"])) # fallback: demand che contiene
        else:
            return False, "btc_no_demand_below"

        z_low, z_high = float(z["low"]), float(z["high"])


        # ✅ se BTC è dentro, lascio lavorare
        if z_low <= btc_price <= z_high:
            return False, f"btc_demand_inside_allow_rej{z['count']}"

        # ✅ blocco solo se BTC è SOPRA e vicino al bordo alto della demand scelta
        # (cioè sta arrivando sopra un supporto)
        if btc_price > z_high:
            dist = (btc_price - z_high) / max(btc_price, 1e-12)
            if dist <= BTC_ZONE_NEAR_PCT:
                return True, f"btc_demand_below_near{dist*100:.2f}%_rej{z['count']}"

        return False, "btc_demand_below_far"


def detect_trend(sh, sl):
    if len(sh) < 2 or len(sl) < 2:
        return "NONE"
    (_, h1), (_, h2) = sh[-2], sh[-1]
    (_, l1), (_, l2) = sl[-2], sl[-1]
    if h2 > h1 and l2 > l1:
        return "UP"
    if h2 < h1 and l2 < l1:
        return "DOWN"
    return "NONE"

def btc_is_trending(df_btc_15m: pd.DataFrame) -> (bool, str):
    """
    Ritorna (True, 'UP'/'DOWN') se BTC è in trend su 15m.
    Ritorna (False, 'NONE') se non c'è trend chiaro.
    """
    try:
        if df_btc_15m is None or df_btc_15m.empty or len(df_btc_15m) < 80:
            return False, "NONE"

        # usa candele chiuse
        df = df_btc_15m.iloc[:-1].copy()
        sh, sl = find_swings(df, lr=BTC_TREND_LR)   # oppure 2 fisso se preferisci
        trend = detect_trend(sh, sl)               # UP / DOWN / NONE

        if trend in ("UP", "DOWN"):
            return True, trend
        return False, "NONE"

    except Exception as e:
        if DEBUG_TERMINAL:
            print(f"[btc_is_trending] WARN: {e}", flush=True)
        return False, "NONE"


# ===================== BTC FLUIDO (15m, MOLTO PERMISSIVO) =====================
def btc_is_fluido_15m(df_btc_15m: pd.DataFrame,
                      ema_len: int = 50,
                      slope_lookback: int = 12,
                      slope_th_pct: float = 0.0005):
    """
    BTC fluido (molto permissivo):
    - EMA50 su 15m con pendenza minima
    """
    try:
        if df_btc_15m is None or df_btc_15m.empty:
            return False

        df = df_btc_15m.iloc[:-1].copy()
        if len(df) < ema_len + slope_lookback + 5:
            return False

        close = df["close"].astype(float)
        ema50 = close.ewm(span=ema_len, adjust=False).mean()

        now = float(ema50.iloc[-1])
        past = float(ema50.iloc[-1 - slope_lookback])

        slope_pct = abs(now - past) / max(float(close.iloc[-1]), 1e-12)

        return slope_pct >= slope_th_pct

    except Exception:
        return False


def ema(series: pd.Series, span: int) -> pd.Series:
    return series.ewm(span=span, adjust=False).mean()

def atr(df: pd.DataFrame, n: int = 14) -> pd.Series:
    h = df["high"].astype(float)
    l = df["low"].astype(float)
    c = df["close"].astype(float)
    prev_c = c.shift(1)
    tr = pd.concat([(h - l), (h - prev_c).abs(), (l - prev_c).abs()], axis=1).max(axis=1)
    return tr.rolling(n).mean()

def is_lateral_market_5m(
    df5: pd.DataFrame,
    ema_len: int = 200,
    slope_lookback: int = 24,      # ~2 ore su 5m
    slope_th_pct: float = 0.0006,  # 0.06% (tarabile)
    atr_len: int = 14,
    atr_ratio_th: float = 0.75     # ATR attuale < 75% della media recente
) -> bool:
    """
    True = mercato laterale/compressivo su 5m:
    - EMA200 quasi piatta
    - ATR compresso (poca spinta)
    """
    if df5 is None or df5.empty or len(df5) < max(ema_len + slope_lookback + 5, 260):
        return False

    close = df5["close"].astype(float)
    ema200 = ema(close, ema_len)

    now = float(ema200.iloc[-1])
    past = float(ema200.iloc[-1 - slope_lookback])
    slope_pct = abs(now - past) / max(float(close.iloc[-1]), 1e-12)

    atrv = atr(df5, atr_len)
    if atrv.isna().iloc[-1]:
        return False

    atr_now = float(atrv.iloc[-1])
    atr_mean = float(atrv.tail(80).mean())  # ~6-7 ore
    atr_ratio = atr_now / max(atr_mean, 1e-12)

    return (slope_pct < slope_th_pct) and (atr_ratio < atr_ratio_th)

def avg_range(df: pd.DataFrame, n: int) -> float:
    rng = (df["high"].astype(float) - df["low"].astype(float)).tail(n)
    return float(rng.mean()) if len(rng) else 0.0

def get_bias_30m(df_bias: pd.DataFrame) -> str:
    """
    BIAS 30m NON permissivo (BOS + CHoCH):
      - Se trend UP:
          BOS   se close > prev_swing_high  => UP
          CHoCH se close < prev_swing_low   => DOWN
          altrimenti NONE
      - Se trend DOWN:
          BOS   se close < prev_swing_low   => DOWN
          CHoCH se close > prev_swing_high  => UP
          altrimenti NONE
    """
    sh, sl = find_swings(df_bias, lr=SWING_LR_BIAS)
    trend = detect_trend(sh, sl)

    if trend == "NONE" or len(sh) < 2 or len(sl) < 2:
        return "NONE"

    last_close = float(df_bias["close"].astype(float).iloc[-1])
    prev_sh = float(sh[-2][1])
    prev_sl = float(sl[-2][1])

    if trend == "UP":
        if last_close > prev_sh:
            return "UP"      # BOS
        if last_close < prev_sl:
            return "DOWN"    # CHoCH
        return "NONE"

    if trend == "DOWN":
        if last_close < prev_sl:
            return "DOWN"    # BOS
        if last_close > prev_sh:
            return "UP"      # CHoCH
        return "NONE"

    return "NONE"


def latest_entry_swings(df_entry: pd.DataFrame):
    sh, sl = find_swings(df_entry, lr=SWING_LR_ENTRY)
    if not sh or not sl:
        return None
    return {"swing_high": float(sh[-1][1]), "swing_low": float(sl[-1][1])}

def detect_bullish_fvg(df: pd.DataFrame, idx: int):
    if idx < 2:
        return None
    c1 = candle_stats(df.iloc[idx-2])
    c3 = candle_stats(df.iloc[idx])
    bot = c1["h"]
    top = c3["l"]
    if bot < top:
        mid = float(df.iloc[idx]["close"])
        if (top - bot) / max(mid, 1e-12) >= FVG_MIN_SIZE_PCT:
            return {"low": bot, "high": top}
    return None

def detect_bearish_fvg(df: pd.DataFrame, idx: int):
    if idx < 2:
        return None
    c1 = candle_stats(df.iloc[idx-2])
    c3 = candle_stats(df.iloc[idx])
    low = c3["h"]
    high = c1["l"]
    if low < high:
        mid = float(df.iloc[idx]["close"])
        if (high - low) / max(mid, 1e-12) >= FVG_MIN_SIZE_PCT:
            return {"low": low, "high": high}
    return None

def find_order_block(df: pd.DataFrame, disp_idx: int, side: str):
    start = max(0, disp_idx - OB_LOOKBACK)
    for j in range(disp_idx - 1, start - 1, -1):
        c = candle_stats(df.iloc[j])
        if side == "LONG" and c["bear"]:
            return {"low": c["l"], "high": c["h"], "idx": j}
        if side == "SHORT" and c["bull"]:
            return {"low": c["l"], "high": c["h"], "idx": j}
    return None

def zone_touched(candle, zone):
    return (candle["h"] >= zone["low"]) and (candle["l"] <= zone["high"])

def detect_confirm_m5(disp_dir: str, zone_low: float, zone_high: float,
                      o: float, h: float, l: float, c: float,
                      atr5: float,
                      m5_last_swing_high: float, m5_last_swing_low: float,
                      h_i_2: float, l_i_2: float,
                      bars_since_retrace_hit: int) -> dict:
    """
    Detect confirmation on M5 (LTF) after M15 retrace
    
    Requirements:
    - Must be in or near retrace zone (context gate)
    - Micro BOS (Break Of Structure) on M5
    - Impulse anomaly (range >= 0.6 ATR)
    - Body dominance (body >= 50% range)
    - Optional: mini FVG M5 = grade A, else grade B
    
    Returns dict with status and confirm info
    """
    # Time decay check
    if bars_since_retrace_hit > MAX_CONFIRM_BARS:
        return {"status": "EXPIRED"}  # Reset to WAIT_SWEEP
    
    # Context gate: must be in or near zone
    zone_buffer = atr5 * ZONE_BUFFER_ATR_MULT
    in_zone_or_near = (l <= zone_high + zone_buffer) and (h >= zone_low - zone_buffer)
    
    if not in_zone_or_near:
        return {"status": "WAIT"}  # Stay in WAIT_CONFIRM
    
    # Thresholds
    bos_buffer5 = atr5 * MICRO_BOS_BUFFER_ATR_MULT
    
    candle_range = h - l
    if candle_range <= 0:
        return {"status": "WAIT"}
    
    body = abs(c - o)
    
    # Impulse check
    impulse_ok = candle_range >= atr5 * CONFIRM_IMPULSE_MULT
    
    # Body dominance
    body_ok = body >= candle_range * CONFIRM_BODY_RATIO
    
    # Micro BOS check
    micro_bos_up = c > (m5_last_swing_high + bos_buffer5)
    micro_bos_down = c < (m5_last_swing_low - bos_buffer5)
    
    # Micro FVG check (3-candle rule)
    fvg = None
    if l > h_i_2:  # Bullish FVG
        fvg = {"dir": "UP", "low": h_i_2, "high": l}
    elif h < l_i_2:  # Bearish FVG
        fvg = {"dir": "DOWN", "low": h, "high": l_i_2}
    
    # Validate based on displacement direction
    if disp_dir == "UP":
        valid = in_zone_or_near and micro_bos_up and impulse_ok and body_ok
        confirm_dir = "UP"
        bos_level = m5_last_swing_high
    elif disp_dir == "DOWN":
        valid = in_zone_or_near and micro_bos_down and impulse_ok and body_ok
        confirm_dir = "DOWN"
        bos_level = m5_last_swing_low
    else:
        return {"status": "WAIT"}
    
    if not valid:
        return {"status": "WAIT"}
    
    # Grade: A if FVG present and aligned, else B
    grade = "A" if (fvg is not None and fvg["dir"] == confirm_dir) else "B"
    
    return {
        "status": "CONFIRMED",
        "dir": confirm_dir,
        "micro_bos_level": bos_level,
        "impulse_ok": impulse_ok,
        "body_ok": body_ok,
        "fvg": fvg,
        "grade": grade,
    }


def _count_ob_rejections(df15: pd.DataFrame, ob: dict, kind: str,
                         lookback: int, cooldown: int) -> int:
    """
    kind:
      - "RESIST": OB bearish (blocca LONG alt) -> reject se touch e close < ob.low
      - "SUPPORT": OB bullish (blocca SHORT alt) -> reject se touch e close > ob.high
    """
    try:
        if df15 is None or df15.empty or ob is None:
            return 0

        df = df15.iloc[:-1].tail(int(lookback)).copy()
        rej = 0
        i = 0
        while i < len(df):
            row = df.iloc[i]
            h = float(row["high"]); l = float(row["low"]); c = float(row["close"])
            touched = (h >= float(ob["low"])) and (l <= float(ob["high"]))

            if kind == "RESIST":
                is_reject = touched and (c < float(ob["low"]))
            else:
                is_reject = touched and (c > float(ob["high"]))

            if is_reject:
                rej += 1
                i += int(cooldown)
                continue

            i += 1

        return rej
    except Exception as e:
        if DEBUG_TERMINAL:
            print(f"[btc_ob_rej] WARN: {e}", flush=True)
        return 0


def btc_blocks_trade_by_ob_conflict(alt_side: str) -> (bool, str):
    """
    alt_side: "LONG" o "SHORT" (trade che stai per aprire sull'ALT)
    Ritorna: (block, reason)
    """
    try:
        df_btc = fetch_df(BTC_SYMBOL, BTC_TF, BTC_LOOKBACK)
        if df_btc.empty or len(df_btc) < 80:
            return False, "btc_no_data"

        btc_price = float(df_btc["close"].astype(float).iloc[-1])

        if alt_side.upper() == "LONG":
            # Per bloccare LONG alt, cerco RESISTENZA BTC => bearish OB
            disp_idx = _find_last_displacement_idx_15m(df_btc, "SHORT")
            if disp_idx < 0:
                return False, "btc_no_disp_short"

            ob = find_order_block(df_btc, disp_idx, "SHORT")
            if not ob:
                return False, "btc_no_ob_resist"

            # BTC deve essere sotto la resistenza e vicino entro 0.40% a ob.low
            dist = (float(ob["low"]) - btc_price) / max(btc_price, 1e-12)
            if dist < 0 or dist > BTC_NEAR_PCT:
                return False, "btc_not_near_resist"

            rej = _count_ob_rejections(df_btc, ob, "RESIST", BTC_REJ_LOOKBACK, BTC_REJ_COOLDOWN)
            if rej >= BTC_REJ_MIN:
                return True, f"btc_resist_ob_rej{rej}_near{dist*100:.2f}%"
            return False, f"btc_resist_ob_rej{rej}_insufficient"

        else:
            # Per bloccare SHORT alt, cerco SUPPORTO BTC => bullish OB
            disp_idx = _find_last_displacement_idx_15m(df_btc, "LONG")
            if disp_idx < 0:
                return False, "btc_no_disp_long"

            ob = find_order_block(df_btc, disp_idx, "LONG")
            if not ob:
                return False, "btc_no_ob_support"

            # BTC deve essere sopra il supporto e vicino entro 0.40% a ob.high
            dist = (btc_price - float(ob["high"])) / max(btc_price, 1e-12)
            if dist < 0 or dist > BTC_NEAR_PCT:
                return False, "btc_not_near_support"

            rej = _count_ob_rejections(df_btc, ob, "SUPPORT", BTC_REJ_LOOKBACK, BTC_REJ_COOLDOWN)
            if rej >= BTC_REJ_MIN:
                return True, f"btc_support_ob_rej{rej}_near{dist*100:.2f}%"
            return False, f"btc_support_ob_rej{rej}_insufficient"

    except Exception as e:
        if DEBUG_TERMINAL:
            print(f"[btc_filter] WARN: {e}", flush=True)
        return False, f"btc_filter_error"


# ===================== NUOVO SL: ULTIMO ORDER BLOCK 15m + CAP 1.50% =====================
def _find_last_displacement_idx_15m(df15: pd.DataFrame, side: str) -> int:
    if df15 is None or df15.empty or len(df15) < (AVG_RANGE_LEN + 10):
        return -1

    ar = avg_range(df15, AVG_RANGE_LEN)
    if ar <= 0:
        return -1

    lookback_disp = 60
    start = max(AVG_RANGE_LEN + 2, len(df15) - lookback_disp)

    for i in range(len(df15) - 1, start, -1):
        c = candle_stats(df15.iloc[i])
        rng_ok = c["range"] >= (DISP_RANGE_MULT * ar)
        body_ok = c["body_ratio"] >= DISP_BODY_RATIO
        dir_ok = c["bull"] if side == "LONG" else c["bear"]
        if rng_ok and body_ok and dir_ok:
            return i

    return -1

def structural_sl_from_last_ob_15m(entry: float, side: str, df15: pd.DataFrame):
    entry = float(entry)
    buf = entry * STRUCT_SL_BUFFER_PCT

    disp_idx = _find_last_displacement_idx_15m(df15, side)
    if disp_idx < 0:
        return None, None

    ob15 = find_order_block(df15, disp_idx, side)
    if not ob15:
        return None, None

    if side == "LONG":
        sl_struct = float(ob15["low"]) - buf
        sl_cap = entry * (1.0 - SL_CAP_PCT)

        # distanza % tra entry e sl_struct
        sl_dist_pct = abs(entry - sl_struct) / max(entry, 1e-12)

        # 1) direzione sbagliata
        if sl_struct >= entry:
            return sl_cap, "CAP_0.65%"

        # 2) troppo vicino (<0.35%) -> CAP
        if sl_dist_pct < MIN_STRUCT_SL_PCT:
            return sl_cap, "CAP_0.65%"

        # 3) troppo lontano (>0.65%) -> CAP
        if sl_dist_pct > SL_CAP_PCT:
            return sl_cap, "CAP_0.65%"

        # ok: tra 0.35% e 0.65%
        return sl_struct, "STRUCT_15M"

    else:  # SHORT
        sl_struct = float(ob15["high"]) + buf
        sl_cap = entry * (1.0 + SL_CAP_PCT)

        sl_dist_pct = abs(entry - sl_struct) / max(entry, 1e-12)

        if sl_struct <= entry:
            return sl_cap, "CAP_0.65%"

        if sl_dist_pct < MIN_STRUCT_SL_PCT:
            return sl_cap, "CAP_0.65%"

        if sl_dist_pct > SL_CAP_PCT:
            return sl_cap, "CAP_0.65%"

        return sl_struct, "STRUCT_15M"





# ===================== TP LADDER + PROFIT LOCK (NO TELEGRAM EXTRA) =====================
def _next_tp_pct(current_pct: float) -> float:
    # trova il prossimo gradino fisso > current, altrimenti step +0.10% oltre 1.60
    for p in TP_LADDER_PCTS:
        if p > current_pct + 1e-12:
            return p
    return float(current_pct + TP_AFTER_LAST_STEP)

def update_tp_sl_ladder_if_needed(symbol: str, pos: dict, high: float, low: float):
    """
    - Quando TP corrente viene toccato: SL = TP - 0.30% (tolleranza) e TP avanza al gradino successivo.
    - Usa HIGH/LOW per non perdere spike.
    - SL migliora solo (mai si allarga).
    """
    try:
        entry = float(pos["entry"])
        side = str(pos["side"])
        cur_tp_pct = float(pos.get("tp_pct") or TP_LADDER_PCTS[0])

        # Protezione: limite massimo iterazioni per spike enormi in una singola candela
        max_steps = 25
        steps = 0

        if side == "LONG":
            while steps < max_steps:
                cur_tp_price = entry * (1.0 + cur_tp_pct)
                if high < cur_tp_price:
                    break

                # TP toccato -> profit lock SL = TP - 0.30%
                lock_sl = entry * (1.0 + (cur_tp_pct - LOCK_RETRACE_PCT))
                old_sl = float(pos["sl"])
                if lock_sl > old_sl:
                    pos["sl"] = float(lock_sl)
                    pos["sl_type"] = "LOCK_TP"  # formato invariato

                # Avanza TP
                cur_tp_pct = _next_tp_pct(cur_tp_pct)
                steps += 1

            pos["tp_pct"] = float(cur_tp_pct)
            pos["tp"] = float(entry * (1.0 + cur_tp_pct))

        else:  # SHORT
            while steps < max_steps:
                cur_tp_price = entry * (1.0 - cur_tp_pct)
                if low > cur_tp_price:
                    break

                # TP toccato -> profit lock SL = TP - 0.30% (in senso SHORT)
                lock_sl = entry * (1.0 - (cur_tp_pct - LOCK_RETRACE_PCT))
                old_sl = float(pos["sl"])
                if lock_sl < old_sl:
                    pos["sl"] = float(lock_sl)
                    pos["sl_type"] = "LOCK_TP"

                # Avanza TP
                cur_tp_pct = _next_tp_pct(cur_tp_pct)
                steps += 1

            pos["tp_pct"] = float(cur_tp_pct)
            pos["tp"] = float(entry * (1.0 - cur_tp_pct))

    except Exception as e:
        if DEBUG_TERMINAL:
            print(f"[{symbol}] WARN update_tp_sl_ladder_if_needed: {e}", flush=True)

# ===================== PRECISION / BINANCE FILTERS =====================
def _safe_float(x, default=None):
    try:
        if x is None:
            return default
        return float(x)
    except:
        return default

def _get_binance_filters(_ex, symbol: str):
    m = _ex.markets.get(symbol)
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
            step = _safe_float(f.get("stepSize"), 0.0) or 0.0
            min_qty = _safe_float(f.get("minQty"), 0.0) or 0.0
        if ft in ("MIN_NOTIONAL", "NOTIONAL"):
            mn = f.get("minNotional") or f.get("notional")
            if mn is not None:
                min_notional = _safe_float(mn, 0.0) or 0.0

    return step, min_qty, min_notional, quote_asset_prec

def _decimals_from_step(step: float) -> int:
    if not step or step <= 0:
        return 8
    s = f"{step:.20f}".rstrip("0")
    return len(s.split(".")[1]) if "." in s else 0

def _quantize_down_str(value: float, decimals: int) -> str:
    d = Decimal(str(value))
    q = Decimal("1e-" + str(decimals))
    return format(d.quantize(q, rounding=ROUND_DOWN), "f")

def fmt_qty(symbol: str, qty: float) -> str:
    step, min_qty, _, _ = _get_binance_filters(ex, symbol)
    if qty <= 0:
        return "0"
    if step and step > 0:
        q = math.floor(qty / step) * step
    else:
        q = qty

    if min_qty and q < min_qty:
        q = min_qty

    dec = _decimals_from_step(step) if step and step > 0 else 8
    return _quantize_down_str(q, dec)

def fmt_quote(symbol: str, quote: float) -> str:
    _, _, min_notional, quote_prec = _get_binance_filters(ex, symbol)
    q = float(quote)

    if min_notional and q < min_notional:
        q = float(min_notional) * MIN_NOTIONAL_PAD

    dec = int(quote_prec) if quote_prec is not None else 6
    return _quantize_down_str(q, dec)

def get_real_entry_from_sapi_order(order: dict, fallback_price: float) -> float:
    exec_qty = _safe_float(order.get("executedQty"), 0.0) or 0.0
    cum_quote = _safe_float(order.get("cummulativeQuoteQty"), 0.0) or 0.0
    if exec_qty > 0 and cum_quote > 0:
        return cum_quote / exec_qty
    return float(fallback_price)

# ===================== CROSS MARGIN BALANCE (LONG close) =====================
def get_cross_base_free(symbol: str) -> float:
    base = symbol.split("/")[0].strip().upper()
    try:
        data = ex.sapiGetMarginAccount({"timestamp": ex.milliseconds(), "recvWindow": 60000})
        assets = data.get("userAssets") or []
        for a in assets:
            if (a.get("asset") or "").upper() == base:
                return float(_safe_float(a.get("free"), 0.0) or 0.0)
        return 0.0
    except Exception as e:
        print(f"[{symbol}] WARN cannot fetch cross margin balance: {e}", flush=True)
        return 0.0

# ===================== ORDER HELPERS =====================
def calc_amount_from_usdc(symbol: str, usdc_target: float, ref_price: float) -> float:
    step, min_qty, min_notional, _ = _get_binance_filters(ex, symbol)

    target = float(usdc_target)
    if min_notional and target < min_notional:
        target = min_notional * MIN_NOTIONAL_PAD

    amt = target / max(ref_price, 1e-12)

    if step and step > 0:
        amt = math.floor(amt / step) * step

    if min_qty and amt < min_qty:
        amt = min_qty

    return float(amt)

def place_entry_market(symbol: str, side: str, ref_price: float):
    bsym = to_binance_symbol(symbol)

    if side == "LONG":
        params = {
            "symbol": bsym,
            "side": "BUY",
            "type": "MARKET",
            "sideEffectType": "MARGIN_BUY",
            "quoteOrderQty": fmt_quote(symbol, float(TRADE_USDC_TARGET)),
            "timestamp": ex.milliseconds(),
            "recvWindow": 60000,
        }
        order = ex.sapiPostMarginOrder(params)
        filled_qty = float(order.get("executedQty") or 0.0)
        return order, filled_qty

    else:
        amount = calc_amount_from_usdc(symbol, float(TRADE_USDC_TARGET), ref_price)
        params = {
            "symbol": bsym,
            "side": "SELL",
            "type": "MARKET",
            "quantity": fmt_qty(symbol, amount),
            "sideEffectType": "AUTO_BORROW_REPAY",
            "timestamp": ex.milliseconds(),
            "recvWindow": 60000,
        }
        order = ex.sapiPostMarginOrder(params)
        filled_qty = float(order.get("executedQty") or amount)
        return order, filled_qty

def place_close_market(symbol: str, side: str, amount: float):
    bsym = to_binance_symbol(symbol)
    if amount <= 0:
        raise Exception("amount<=0 in close")

    params = {
        "symbol": bsym,
        "type": "MARKET",
        "quantity": fmt_qty(symbol, float(amount)),
        "sideEffectType": "AUTO_REPAY",
        "timestamp": ex.milliseconds(),
        "recvWindow": 60000,
    }
    params["side"] = "SELL" if side == "LONG" else "BUY"
    return ex.sapiPostMarginOrder(params)

# ===================== OPEN/CLOSE =====================
def open_position(symbol, side, entry_ref, sl_price, sl_type, tp_price, note=""):
    if len(positions) >= MAX_OPEN_POS:
        print(f"[{symbol}] SKIP open: max posizioni aperte ({MAX_OPEN_POS})", flush=True)
        return

    real_entry = float(entry_ref)
    amount = None
    entry_order_id = None
    entry_candle_ts = None

    # ricava tp_pct dal tp_price rispetto a entry_ref (serve per la ladder)
    tp_pct = abs((float(tp_price) - float(entry_ref)) / max(float(entry_ref), 1e-12))

    if LIVE_TRADING:
        try:
            order, filled_qty = place_entry_market(symbol, side, float(entry_ref))
            amount = float(filled_qty)
            entry_order_id = order.get("orderId") or order.get("id")
            real_entry = get_real_entry_from_sapi_order(order, float(entry_ref))

            # ricalcolo TP su entry reale usando tp_pct
            tp_price = real_entry * (1 + tp_pct) if side == "LONG" else real_entry * (1 - tp_pct)

            # ricalcolo SL su entry reale mantenendo la stessa % rispetto entry_ref
            sl_pct = (float(sl_price) - float(entry_ref)) / float(entry_ref)  # + per SHORT, - per LONG
            sl_price = real_entry * (1.0 + sl_pct)

            print(
                f"[LIVE ENTRY OK] {symbol} {side} "
                f"orderId={entry_order_id} execQty={order.get('executedQty')} "
                f"cumQuote={order.get('cummulativeQuoteQty')} "
                f"realEntry={real_entry:.8f} tp={tp_price:.8f} sl={sl_price:.8f} ({sl_type})",
                flush=True
            )

            df_tmp = fetch_df(symbol, ENTRY_TF, 2)
            entry_candle_ts = int(df_tmp.iloc[-1]["ts"]) if not df_tmp.empty else int(ex.milliseconds())

        except Exception as e:
            print(f"[{symbol}] ENTRY LIVE FAILED: {e}", flush=True)
            return

    positions[symbol] = {
        "side": side,
        "entry": float(real_entry),
        "sl": float(sl_price),
        "sl_type": str(sl_type),
        "tp": float(tp_price),
        "tp_pct": float(tp_pct),  # <<< per ladder
        "note": note,
        "amount": float(amount) if amount else None,
        "entry_order_id": entry_order_id,
        "entry_candle_ts": int(entry_candle_ts) if entry_candle_ts is not None else None,
    }

    # % SL e % TP (per messaggio)
    sl_pct_abs = abs((float(real_entry) - float(sl_price)) / max(float(real_entry), 1e-12)) * 100.0
    tp_pct_abs = abs((float(tp_price) - float(real_entry)) / max(float(real_entry), 1e-12)) * 100.0

    tg_send(
        f"🟢 OPEN {side} {symbol}\n{note}\n"
        f"Entry REAL {real_entry:.6f} (ref {float(entry_ref):.6f})\n"
        f"TP {float(tp_price):.6f} ({tp_pct_abs:.2f}%)\n"
        f"SL {float(sl_price):.6f} ({sl_pct_abs:.2f}%) | SL_TYPE: {sl_type}\n"
        f"Size target {TRADE_USDC_TARGET} USDC (auto-min)"
    )

def close_position(symbol, exit_price, reason):
    pos = positions.get(symbol)
    if not pos:
        return

    side = pos["side"]
    tracked_amt = float(pos.get("amount") or 0.0)

    if LIVE_TRADING:
        try:
            if side == "LONG":
                real_base_free = get_cross_base_free(symbol)
                qty_to_close = min(real_base_free, tracked_amt) if tracked_amt > 0 else real_base_free

                if qty_to_close > 0:
                    resp = place_close_market(symbol, side, qty_to_close)
                    print(f"[LIVE CLOSE OK] {symbol} {side} orderId={resp.get('orderId')} execQty={resp.get('executedQty')}", flush=True)
                else:
                    print(f"[{symbol}] SYNC: base_free=0 -> posizione LONG già chiusa (manual/other). Rimuovo.", flush=True)
                    del positions[symbol]
                    tg_send(f"⚠️ SYNC {symbol}: posizione LONG non trovata (base=0). Rimossa dal tracking.")
                    return
            else:
                if tracked_amt <= 0:
                    print(f"[{symbol}] WARN: amount mancante per SHORT. Skip close.", flush=True)
                    return
                resp = place_close_market(symbol, side, tracked_amt)
                print(f"[LIVE CLOSE OK] {symbol} {side} orderId={resp.get('orderId')} execQty={resp.get('executedQty')}", flush=True)

        except Exception as e:
            print(f"[{symbol}] CLOSE LIVE FAILED: {e}", flush=True)
            return

    entry = float(pos["entry"])
    pnl_gross = (exit_price - entry) / entry if side == "LONG" else (entry - exit_price) / entry
    pnl_net_est = pnl_gross - ROUND_TRIP_FEE_PCT

    tg_send(
        f"🔴 CLOSE {symbol} ({reason})\n"
        f"PNL gross {pnl_gross*100:.2f}% | net(est) {pnl_net_est*100:.2f}%\n"
        f"SL_TYPE (se SL): {pos.get('sl_type')}"
    )
    del positions[symbol]

# ===================== MAIN LOOP =====================
while True:
    try:
        loop_count += 1
        reasons = Counter()
        analyzed = 0

        for symbol in SYMBOLS:
            analyzed += 1
            try:
                # 1) Gestione posizione aperta (TP come TRIGGER, NON come exit)
                if symbol in positions:
                    df_e = fetch_df(symbol, ENTRY_TF, LOOKBACK_ENTRY)
                    if df_e.empty or len(df_e) < 30:
                        reasons["pos_fetch_empty"] += 1
                        continue

                    last_row = df_e.iloc[-1]
                    high = float(last_row["high"])
                    low = float(last_row["low"])
                    pos = positions[symbol]

                    # evita chiusura usando HIGH/LOW della stessa candela di ingresso
                    if pos.get("entry_candle_ts") is not None and int(last_row["ts"]) == int(pos["entry_candle_ts"]):
                        continue

                    # TP ladder aggiorna SL e sposta il prossimo trigger
                    update_tp_sl_ladder_if_needed(symbol, pos, high, low)

                    # EXIT SOLO SU SL (lockato a gradini)
                    if pos["side"] == "LONG":
                        if low <= pos["sl"]:
                            close_position(symbol, pos["sl"], f"SL ({pos.get('sl_type')})")
                    else:  # SHORT
                        if high >= pos["sl"]:
                            close_position(symbol, pos["sl"], f"SL ({pos.get('sl_type')})")

                    continue



                # 2) Bias 30m
                df_b = fetch_df(symbol, BIAS_TF, LOOKBACK_BIAS)
                if df_b.empty or len(df_b) < 80:
                    reasons["bias_fetch_empty"] += 1
                    continue

                bias = get_bias_30m(df_b)
                if bias == "NONE":
                    reasons["bias_none"] += 1
                    if symbol in pending:
                        del pending[symbol]
                    continue

                side = "LONG" if bias == "UP" else "SHORT"

                # 3) Entry 5m
                df = fetch_df(symbol, ENTRY_TF, LOOKBACK_ENTRY)
                if df.empty or len(df) < 120:
                    reasons["entry_fetch_empty"] += 1
                    continue

                last = candle_stats(df.iloc[-1])
                price = last["c"]

                pools_5m = latest_entry_swings(df)
                if not pools_5m:
                    reasons["no_swings_5m"] += 1
                    continue

                buffer = price * SWEEP_BUFFER_PCT

                # init pending
                if symbol not in pending or pending[symbol].get("side") != side:
                    pending[symbol] = {"state": "WAIT_SWEEP", "side": side}

                p = pending[symbol]

                # WAIT_SWEEP
                if p["state"] == "WAIT_SWEEP":
                    if side == "LONG":
                        sw = pools_5m["swing_low"]
                        if (last["l"] < (sw - buffer)) and (last["c"] > sw):
                            p["state"] = "WAIT_DISPLACEMENT"
                        else:
                            reasons["no_sweep"] += 1
                    else:
                        sw = pools_5m["swing_high"]
                        if (last["h"] > (sw + buffer)) and (last["c"] < sw):
                            p["state"] = "WAIT_DISPLACEMENT"
                        else:
                            reasons["no_sweep"] += 1

                # WAIT_DISPLACEMENT
                elif p["state"] == "WAIT_DISPLACEMENT":
                    ar = avg_range(df, AVG_RANGE_LEN)
                    rng_ok = (last["range"] >= DISP_RANGE_MULT * ar) if ar > 0 else False
                    body_ok = (last["body_ratio"] >= DISP_BODY_RATIO)
                    disp_ok = rng_ok and body_ok and ((side == "LONG" and last["bull"]) or (side == "SHORT" and last["bear"]))

                    if not disp_ok:
                        reasons["no_displacement"] += 1
                        continue

                    disp_idx = len(df) - 1
                    fvg = detect_bullish_fvg(df, disp_idx) if side == "LONG" else detect_bearish_fvg(df, disp_idx)
                    ob = find_order_block(df, disp_idx, side)

                    if not fvg and not ob:
                        reasons["no_fvg_ob"] += 1
                        continue

                    p["state"] = "WAIT_RETRACE"
                    p["fvg"] = fvg
                    p["ob"] = ob
                    p["displacement_dir"] = "UP" if side == "LONG" else "DOWN"

                # WAIT_RETRACE
                elif p["state"] == "WAIT_RETRACE":
                    zones = []
                    if p.get("ob"):
                        zones.append(("OB", p["ob"]))
                    if p.get("fvg"):
                        zones.append(("FVG", p["fvg"]))

                    touched = None
                    for name, z in zones:
                        if zone_touched(last, z):
                            touched = (name, z)
                            break

                    if not touched:
                        reasons["no_retrace_touch"] += 1
                        continue

                    # Fetch LTF to track bar index for confirmation timeout
                    df_ltf_init = fetch_df(symbol, LTF, LOOKBACK_LTF)
                    if not df_ltf_init.empty and len(df_ltf_init) >= 50:
                        df_ltf_closed_init = df_ltf_init.iloc[:-1].copy()
                        p["retrace_hit_bar_index"] = len(df_ltf_closed_init) - 1
                    else:
                        p["retrace_hit_bar_index"] = 0

                    p["state"] = "WAIT_CONFIRM"
                    p["touch_name"], p["touch_zone"] = touched
                    p["bars_since_retrace_hit"] = 0

                # WAIT_CONFIRM
                elif p["state"] == "WAIT_CONFIRM":
                    # Check bias coherence - if bias changes, reset
                    if (side == "LONG" and bias != "UP") or (side == "SHORT" and bias != "DOWN"):
                        if DEBUG_TERMINAL:
                            print(f"[{symbol}] BIAS changed from {side} to {bias}, reset to WAIT_SWEEP", flush=True)
                        pending[symbol] = {"state": "WAIT_SWEEP", "side": side}
                        continue

                    z = p.get("touch_zone")
                    if not z:
                        reasons["confirm_missing_zone"] += 1
                        pending[symbol] = {"state": "WAIT_SWEEP", "side": side}
                        continue

                    disp_dir = p.get("displacement_dir", "UP" if side == "LONG" else "DOWN")

                    # Fetch LTF (M5) data
                    df_ltf = fetch_df(symbol, LTF, LOOKBACK_LTF)
                    if df_ltf.empty or len(df_ltf) < 50:
                        reasons["ltf_fetch_empty"] += 1
                        continue

                    df_ltf_closed = df_ltf.iloc[:-1].copy()

                    # Get M5 swings for micro structure
                    sh_m5, sl_m5 = find_swings(df_ltf_closed, lr=SWING_LR)

                    if len(sh_m5) < 1 or len(sl_m5) < 1:
                        reasons["no_swings_ltf"] += 1
                        continue

                    m5_last_swing_high = float(sh_m5[-1][1])
                    m5_last_swing_low = float(sl_m5[-1][1])

                    # Update bars since retrace hit
                    p["bars_since_retrace_hit"] = len(df_ltf_closed) - 1 - p.get("retrace_hit_bar_index", 0)

                    # Get current M5 candle
                    last_m5 = candle_stats(df_ltf.iloc[-1])
                    o_m5 = last_m5["o"]
                    h_m5 = last_m5["h"]
                    l_m5 = last_m5["l"]
                    c_m5 = last_m5["c"]

                    # Get i-2 candle for FVG detection (need at least 3 candles)
                    if len(df_ltf) >= 3:
                        candle_i_2 = candle_stats(df_ltf.iloc[-3])
                        h_i_2 = candle_i_2["h"]
                        l_i_2 = candle_i_2["l"]
                    else:
                        h_i_2 = h_m5
                        l_i_2 = l_m5

                    # Calculate ATR M5
                    atr_series = atr(df_ltf_closed, 14)
                    if atr_series.isna().iloc[-1]:
                        reasons["no_atr_m5"] += 1
                        continue
                    atr5 = float(atr_series.iloc[-1])

                    # Detect confirm
                    confirm = detect_confirm_m5(
                        disp_dir=disp_dir,
                        zone_low=float(z["low"]),
                        zone_high=float(z["high"]),
                        o=o_m5,
                        h=h_m5,
                        l=l_m5,
                        c=c_m5,
                        atr5=atr5,
                        m5_last_swing_high=m5_last_swing_high,
                        m5_last_swing_low=m5_last_swing_low,
                        h_i_2=h_i_2,
                        l_i_2=l_i_2,
                        bars_since_retrace_hit=p["bars_since_retrace_hit"]
                    )

                    status = confirm.get("status")

                    if status == "CONFIRMED":
                        p["state"] = "VALID_SETUP"
                        p["confirm"] = confirm
                        if DEBUG_TERMINAL:
                            fvg_info = f"miniFVG {confirm['fvg']['dir']} [{confirm['fvg']['low']:.6f}-{confirm['fvg']['high']:.6f}]" if confirm.get('fvg') else "NO miniFVG"
                            print(
                                f"[{symbol}] CONFIRM DETECTED! "
                                f"dir={confirm['dir']} grade={confirm['grade']} "
                                f"micro_BOS_level={confirm['micro_bos_level']:.6f} "
                                f"{fvg_info} "
                                f"→ VALID_SETUP",
                                flush=True
                            )

                    elif status == "EXPIRED":
                        if DEBUG_TERMINAL:
                            print(f"[{symbol}] CONFIRM EXPIRED (>{MAX_CONFIRM_BARS} bars) → reset to WAIT_SWEEP", flush=True)
                        pending[symbol] = {"state": "WAIT_SWEEP", "side": side}

                    elif status == "WAIT":
                        # Stay in WAIT_CONFIRM
                        pass

                # VALID_SETUP (placeholder - will handle entry in next step)
                elif p["state"] == "VALID_SETUP":
                    z = p.get("touch_zone")
                    if not z:
                        reasons["confirm_missing_zone"] += 1
                        pending[symbol] = {"state": "WAIT_SWEEP", "side": side}
                        continue

                    df_sl = fetch_df(symbol, SL_TF, LOOKBACK_SL)

                    # ✅ CHECK anti-blocco "silenzioso" (se il 15m non arriva, non provo a calcolare SL)
                    if df_sl.empty or len(df_sl) < 80:
                        reasons["sl15_fetch_empty"] += 1
                        pending[symbol] = {"state": "WAIT_SWEEP", "side": side}
                        continue

                    

                    if side == "LONG":
                        if last["c"] < float(z["low"]):
                            reasons["confirm_invalidated"] += 1
                            pending[symbol] = {"state": "WAIT_SWEEP", "side": side}
                            continue

                        if last["bull"] and last["c"] > float(z["high"]):
                            entry = last["c"]

                            # ✅ BOS obbligatorio SOLO se mercato laterale (5m)
                            lateral = is_lateral_market_5m(df)
                            if lateral:
                                # BOS LONG = close sopra swing_high 5m
                                if float(last["c"]) <= float(pools_5m["swing_high"]):
                                    reasons["no_bos_lateral"] += 1
                                    continue
                            # ✅ BTC CONFLICT FILTER (OB 15m con 2 rifiuti + distanza 0.40%)
                            if symbol != BTC_SYMBOL:
                                block, why = btc_blocks_trade_by_rejection_zone("LONG")
                                if block:
                                    reasons["btc_conflict"] += 1
                                    if DEBUG_TERMINAL:
                                        print(f"[{symbol}] SKIP LONG (BTC conflict): {why}", flush=True)
                                    pending[symbol] = {"state": "WAIT_SWEEP", "side": side}
                                    continue


                            # TP iniziale = TP0 (da TP_LADDER_PCTS[0])
                            tp0_pct = TP_LADDER_PCTS[0]
                            tp = entry * (1.0 + tp0_pct)
                            if not has_room_to_tp(entry, "LONG", tp0_pct, df_sl):

                                reasons["no_room_to_tp"] += 1
                                pending[symbol] = {"state": "WAIT_SWEEP", "side": side}
                                continue

                            # SL su ultimo OB 15m + CAP 0.65%
                            sl = entry * (1.0 - SL_FIXED_PCT)
                            sl_type = "FIXED_1%"

                            note = f"ICT LONG | {p.get('touch_name')} confirm | TP0={tp0_pct*100:.2f}% | SL FIXED 1.00%"
                            open_position(symbol, "LONG", entry, sl, sl_type, tp, note)
                            del pending[symbol]
                        else:
                            reasons["no_confirm_candle"] += 1

                    else:
                        if last["c"] > float(z["high"]):
                            reasons["confirm_invalidated"] += 1
                            pending[symbol] = {"state": "WAIT_SWEEP", "side": side}
                            continue

                        if last["bear"] and last["c"] < float(z["low"]):
                            entry = last["c"]

                            # ✅ BOS obbligatorio SOLO se mercato laterale (5m)
                            lateral = is_lateral_market_5m(df)
                            if lateral:
                                # BOS SHORT = close sotto swing_low 5m
                                if float(last["c"]) >= float(pools_5m["swing_low"]):
                                    reasons["no_bos_lateral"] += 1
                                    continue

                            # ✅ BTC CONFLICT FILTER (OB 15m con 2 rifiuti + distanza 0.40%)
                            if symbol != BTC_SYMBOL:
                                block, why = btc_blocks_trade_by_rejection_zone("SHORT")
                                if block:
                                    reasons["btc_conflict"] += 1
                                    if DEBUG_TERMINAL:
                                        print(f"[{symbol}] SKIP SHORT (BTC conflict): {why}", flush=True)
                                    pending[symbol] = {"state": "WAIT_SWEEP", "side": side}
                                    continue


                            tp0_pct = TP_LADDER_PCTS[0]
                            tp = entry * (1.0 - tp0_pct)
                            if not has_room_to_tp(entry, "SHORT", tp0_pct, df_sl):


                                reasons["no_room_to_tp"] += 1
                                pending[symbol] = {"state": "WAIT_SWEEP", "side": side}
                                continue

                            sl = entry * (1.0 + SL_FIXED_PCT)
                            sl_type = "FIXED_1%"

                            note = f"ICT SHORT | {p.get('touch_name')} confirm | TP0={tp0_pct*100:.2f}% | SL FIXED 1.00%"

                            open_position(symbol, "SHORT", entry, sl, sl_type, tp, note)
                            del pending[symbol]
                        else:
                            reasons["no_confirm_candle"] += 1

            except Exception as sym_err:
                reasons["symbol_error"] += 1
                print(f"[{symbol}] errore: {sym_err}", flush=True)
                continue

        # ===== DEBUG SUMMARY =====
        if DEBUG_TERMINAL and (loop_count % HEARTBEAT_EVERY_LOOPS == 0):
            now = time.strftime("%H:%M:%S")
            pending_states = Counter(pending[s]["state"] for s in pending) if pending else Counter()
            print("\n" + "="*72, flush=True)
            print(f"[{now}] HEARTBEAT | analyzed={analyzed} | open_positions={len(positions)} | pending={len(pending)}", flush=True)
            if pending_states:
                print("pending states:", dict(pending_states), flush=True)

            top_reasons = reasons.most_common(10)
            if top_reasons:
                print("top reasons (why no entry):", top_reasons, flush=True)

            if pending:
                i = 0
                print("pending sample:", flush=True)
                for sym, st in pending.items():
                    print(f" - {sym}: {st.get('side')} {st.get('state')}", flush=True)
                    i += 1
                    if i >= PRINT_PENDING_SAMPLE:
                        break

            debug_btc_selected_2_zones()

            print("="*72 + "\n", flush=True)

        time.sleep(LOOP_SEC)

    except KeyboardInterrupt:
        tg_send("🛑 Bot stoppato manualmente.")
        raise

    except Exception as e:
        print("Errore generale:", e, flush=True)
        time.sleep(LOOP_SEC)
