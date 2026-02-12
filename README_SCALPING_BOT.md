# Scalping Trading Bot

Un bot di trading automatico per lo scalping basato su indicatori tecnici (RSI).

## Caratteristiche

- 🎯 **Strategia RSI**: Segnali di trading basati su livelli di ipercomprato/ipervenduto
- 📊 **Gestione del rischio**: Stop Loss e Take Profit automatici
- 💹 **Modalità Paper Trading**: Testa la strategia senza rischiare capitale reale
- 📱 **Notifiche Telegram**: Ricevi aggiornamenti sui trade in tempo reale
- 📈 **Statistiche**: Monitora performance, win rate e PnL
- 🔄 **Multi-exchange**: Supporta Binance e altri exchange tramite CCXT

## Struttura del Progetto

```
scalping_bot/
├── __init__.py       # Package initialization
├── config.py         # Configurazione del bot
├── strategy.py       # Logica della strategia di trading
├── trader.py         # Gestione posizioni e ordini
└── main.py          # Entry point principale
```

## Installazione

### Prerequisiti

- Python 3.8 o superiore
- pip (package manager Python)

### Setup

1. **Clona il repository**:
```bash
git clone https://github.com/shino1987/code_test.git
cd code_test
```

2. **Installa le dipendenze**:
```bash
pip install -r requirements.txt
```

3. **Configura le variabili d'ambiente** (opzionale per live trading):

Crea un file `.env` nella root del progetto:

```bash
# Exchange Configuration (richiesto solo per live trading)
EXCHANGE_API_KEY=your_api_key_here
EXCHANGE_API_SECRET=your_api_secret_here
EXCHANGE_NAME=binance

# Telegram Notifications (opzionale)
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_telegram_chat_id
```

## Configurazione

Modifica `scalping_bot/config.py` per personalizzare:

- **SYMBOL**: Coppia di trading (default: "BTC/USDT")
- **TIMEFRAME**: Intervallo temporale (default: "1m")
- **RSI_OVERSOLD**: Livello di ipervenduto (default: 30)
- **RSI_OVERBOUGHT**: Livello di ipercomprato (default: 70)
- **POSITION_SIZE_USDT**: Dimensione posizione in USDT (default: 100)
- **STOP_LOSS_PERCENTAGE**: Stop loss % (default: 0.5%)
- **TAKE_PROFIT_PERCENTAGE**: Take profit % (default: 0.8%)
- **LIVE_TRADING**: True per trading reale, False per paper trading (default: False)

## Utilizzo

### Modalità Paper Trading (default)

Esegui il bot senza rischiare capitale reale:

```bash
python -m scalping_bot.main
```

Il bot utilizzerà dati simulati per testare la strategia.

### Modalità Live Trading

⚠️ **ATTENZIONE**: Il live trading comporta rischi reali. Usa solo con capitale che puoi permetterti di perdere.

1. Configura le credenziali API nel file `.env`
2. Modifica `config.py` e imposta `LIVE_TRADING = True`
3. Esegui il bot:

```bash
python -m scalping_bot.main
```

## Strategia di Trading

### Logica RSI

Il bot utilizza l'indicatore RSI (Relative Strength Index) per identificare condizioni di ipercomprato/ipervenduto:

- **Segnale LONG**: RSI attraversa il livello di ipervenduto (30) verso l'alto
- **Segnale SHORT**: RSI attraversa il livello di ipercomprato (70) verso il basso

### Gestione del Rischio

Ogni posizione include:
- **Stop Loss**: -0.5% (configurabile)
- **Take Profit**: +0.8% (configurabile)
- **Dimensione posizione**: 100 USDT (configurabile)

### Timeframe

Lo scalping utilizza timeframe brevi (1 minuto) per cogliere piccoli movimenti di prezzo con frequenza elevata.

## Monitoraggio

Il bot fornisce:
- Log in tempo reale nella console
- File di log: `scalping_bot.log`
- Notifiche Telegram (se configurate)
- Statistiche ogni 10 iterazioni:
  - Totale trade
  - Win rate
  - PnL cumulativo

## Esempio Output

```
============================================================
Starting Scalping Trading Bot
============================================================
Symbol: BTC/USDT
Timeframe: 1m
Trading Mode: PAPER
============================================================

--- Loop 1 ---
Current price: 50234.50
Signal: BUY | RSI crossed above 30 | RSI: 32.5
Opened LONG position: BTC/USDT @ 50234.50 | SL: 49983.27 | TP: 50636.10

--- Loop 2 ---
Current price: 50456.20
Closed LONG position: BTC/USDT @ 50456.20 | PnL: 0.44% | Reason: TAKE_PROFIT

============================================================
STATISTICS
Total Trades: 1
Winning: 1 | Losing: 0
Win Rate: 100.0%
Total PnL: 0.44%
============================================================
```

## Avvisi e Disclaimer

⚠️ **IMPORTANTE**:
- Questo bot è fornito a scopo educativo
- Il trading comporta rischi significativi
- Non investire più di quanto puoi permetterti di perdere
- Testa sempre in modalità paper trading prima di usare capitale reale
- Le performance passate non garantiscono risultati futuri
- L'autore non è responsabile per perdite finanziarie

## Supporto e Contributi

Per problemi, suggerimenti o contributi, apri una issue su GitHub.

## Licenza

Questo progetto è rilasciato sotto licenza MIT.
