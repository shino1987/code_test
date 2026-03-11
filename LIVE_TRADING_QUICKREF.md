# Live Trading Quick Reference

## ⚡ Quick Start

### 1. Setup API Keys
```bash
export BINANCE_API_KEY="your_key"
export BINANCE_API_SECRET="your_secret"
```

### 2. Configure Bot
```python
# In ict_bot_minimal.py
LIVE_TRADING = True           # Enable live trading
TRADE_USDC_TARGET = 200.0     # $ per trade
MAX_OPEN_POS = 3              # Max positions
```

### 3. Run
```bash
python ict_bot_minimal.py
```

## 🎯 Configuration Matrix

| Mode | LIVE_TRADING | API Keys | Position Size | Risk |
|------|--------------|----------|---------------|------|
| Paper | `False` | Not needed | $100 (simulated) | None |
| Live | `True` | Required | $200 (real) | High |

## 📊 Position Sizing Guide

| Risk Level | TRADE_USDC_TARGET | MAX_OPEN_POS | Total Exposure |
|------------|-------------------|--------------|----------------|
| Conservative | $50 | 2 | $100 |
| Moderate | $200 | 3 | $600 |
| Aggressive | $500 | 5 | $2,500 |

## 🔧 Key Settings

```python
# Trading Mode
LIVE_TRADING = True              # True=Live, False=Paper

# Position Management
TRADE_USDC_TARGET = 200.0        # USDT per trade
MAX_OPEN_POS = 3                 # Max concurrent positions
PAPER_POSITION_SIZE_USDC = 100.0 # Paper trading size

# Risk Management
STRUCT_SL_BUFFER_PCT = 0.0005    # 0.05% SL buffer
MIN_SL_PCT = 0.003               # 0.3% min SL

# Timeframes
BIAS_TF = "30m"                  # Bias detection
ENTRY_TF = "5m"                  # Entry signals
LOOP_SEC = 30                    # Loop interval

# Symbols
SYMBOLS = ["BTC/USDT", "ETH/USDT"]
```

## 📝 Order Types

### LONG Entry
```
Type: MARKET BUY
sideEffectType: MARGIN_BUY
quoteOrderQty: $200
```

### SHORT Entry
```
Type: MARKET SELL
sideEffectType: AUTO_BORROW_REPAY
quantity: calculated
```

### Close
```
Type: MARKET (opposite side)
sideEffectType: AUTO_REPAY
quantity: position size
```

## 🚨 Safety Checks

- [ ] Tested in paper mode first
- [ ] API keys have correct permissions
- [ ] Funds in Cross Margin account
- [ ] Position size appropriate for account
- [ ] Understand cross margin risks
- [ ] Monitoring plan in place
- [ ] Emergency stop procedure known

## 🎮 Console Commands

| Action | Command |
|--------|---------|
| Stop bot | `Ctrl+C` |
| Force kill | `kill -9 <PID>` |
| Check process | `ps aux \| grep ict_bot` |

## 📈 Monitoring Points

### Check Every Hour
- Open positions count
- Margin ratio (keep > 1.5)
- Recent trades in CSV

### Check Daily
- Win rate from CSV
- Average PnL
- Total exposure
- Interest charges

## ⚠️ Red Flags

Stop immediately if:
- Margin ratio < 1.5
- Repeated API errors
- Unexpected position sizes
- Orders failing repeatedly
- Console shows errors

## 🔗 Quick Links

- [Full Guide](LIVE_TRADING_GUIDE.md)
- [API Setup](https://www.binance.com/en/support/faq/360002502072)
- [Cross Margin](https://www.binance.com/en/support/faq/360033162192)
- [Main README](README.md)

## 💡 Pro Tips

1. **Start small** - Use minimum viable position size
2. **Monitor actively** - Especially first 24 hours
3. **Keep buffer** - 2x minimum margin requirement
4. **Log analysis** - Review trades daily
5. **Scale gradually** - Only after consistent results

## 📊 Expected Performance

Typical trade metrics:
- Entry precision: Within 0.1% of ICT levels
- SL distance: 0.5% - 2% from entry
- TP1 distance: 0.5% - 2% from entry
- TP2 distance: 1% - 4% from entry
- Win rate target: > 50%
- Risk/Reward: 1:1 to 1:2

## 🆘 Emergency Contacts

**If something goes wrong:**
1. Stop bot immediately (`Ctrl+C`)
2. Check Binance for open positions
3. Manually close positions if needed
4. Check margin account balance
5. Document the issue
6. Review logs in CSV file

---

**Remember:** Cross margin trading is risky. Only use funds you can afford to lose.
