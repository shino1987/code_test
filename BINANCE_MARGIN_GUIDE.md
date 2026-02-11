# 📘 Guida Binance Cross Margin Trading

## 🎯 Obiettivo

Questa guida ti aiuta a configurare il bot per fare **Cross Margin Trading** su Binance con coppie USDC ad alta liquidità.

---

## ⚠️ IMPORTANTE - Leggi Prima

### Cos'è il Margin Trading?

Il **margin trading** ti permette di prendere in prestito fondi per aumentare la tua posizione (leverage). 

**Vantaggi:**
- Maggiore potere d'acquisto
- Possibilità di profitti amplificati

**Rischi:**
- Perdite amplificate
- Rischio di liquidazione
- Interest accumulation
- Maggiore complessità

### Cross vs Isolated Margin

**Cross Margin** (usato dal bot):
- Il tuo intero account bilancia fa da collaterale
- Se una posizione va male, può intaccare tutto il balance
- Più flessibile, margin level condiviso

**Isolated Margin**:
- Ogni posizione ha collaterale separato
- Rischio limitato per posizione
- Meno flessibile

---

## 🚀 Setup Binance API

### Step 1: Creare API Key

1. **Login** su Binance.com
2. Vai a **Account** → **API Management**
3. Click **Create API**
4. Nome suggerito: "ICT Trading Bot"
5. **Abilita 2FA** (obbligatorio)

### Step 2: Configurare Permessi

**Permessi da abilitare:**
- ✅ **Enable Reading** (lettura balance, orders)
- ✅ **Enable Spot & Margin Trading** (IMPORTANTE!)
- ❌ **Disable Withdrawals** (per sicurezza!)
- ❌ **Disable Futures** (non necessario)

### Step 3: IP Whitelist (RACCOMANDATO)

Per sicurezza, limita l'API a specifici IP:

1. Click **Edit restrictions**
2. Seleziona **Restrict access to trusted IPs only**
3. Aggiungi il tuo IP (o server IP se hosting remoto)
4. Salva

### Step 4: Salvare Credenziali

1. **API Key**: Copia e salva in luogo sicuro
2. **Secret Key**: Copia IMMEDIATAMENTE (mostrato solo una volta!)
3. NON condividere mai queste chiavi

---

## 💰 Preparare Account Binance

### 1. Depositare USDC

Il bot usa coppie **USDC** (non USDT):
- Deposita USDC su Binance
- Minimo raccomandato: $500-1000 USDC per iniziare
- Per testing serio: $100-200 USDC

### 2. Abilitare Margin Trading

1. Vai su **Wallet** → **Margin**
2. Se non abilitato, click **Activate Margin Account**
3. Leggi e accetta i termini
4. Trasferisci USDC da Spot a Margin:
   - Spot Wallet → Margin Wallet
   - Amount: quanto vuoi usare per trading

### 3. Verificare Balance

```
Margin Wallet > Cross Margin > USDC Balance
```

Questo sarà il tuo collaterale iniziale.

---

## ⚙️ Configurare il Bot

### Paper Mode (Testing - RACCOMANDATO)

Prima di usare fondi reali, testa in paper mode:

```python
CONFIG = {
    "MODE": "PAPER",
    "LIVE_TRADING_ENABLED": False,
    # Nessuna API key necessaria
}
```

Esegui:
```bash
python3 paper_trading_bot.py
```

Il bot simula tutto senza usare API o fondi reali.

### Live Mode (Real Trading)

**SOLO dopo testing estensivo in paper mode!**

1. **Modifica configurazione:**

```python
CONFIG = {
    # Trading Mode
    "MODE": "LIVE",
    "LIVE_TRADING_ENABLED": True,
    "REQUIRE_CONFIRMATION": True,  # Il bot chiede conferma
    
    # API Keys
    "API_KEY": "your_binance_api_key_here",
    "API_SECRET": "your_binance_api_secret_here",
    
    # Margin Settings
    "MARGIN_TYPE": "cross",
    "MAX_LEVERAGE": 2.0,  # Start basso! (2x = conservativo)
    
    # Risk Management
    "RISK_PER_TRADE": 0.01,  # 1% per trade (conservativo)
    "INITIAL_CAPITAL": 1000.0,  # Tuo balance USDC reale
}
```

2. **Test connessione:**

```bash
python3 paper_trading_bot.py --test-connection
```

Verifica:
- ✅ API connessione OK
- ✅ Margin enabled
- ✅ Balance USDC visibile
- ✅ Coppie disponibili

3. **Start trading:**

```bash
python3 paper_trading_bot.py
```

Se `REQUIRE_CONFIRMATION = True`, il bot chiederà:
```
Trade Signal: LONG BTC/USDC @ 50000
Leverage: 2.5x
Risk: $20 USDC

Confirm trade? (yes/no):
```

---

## 📊 Monitoraggio

### Console Output

Il bot mostra real-time:
```
[INFO] Margin Level: 2.35 💚
[INFO] Borrowed: 3000 USDC
[INFO] Collateral: 2000 USDC
[WARNING] Price approaching liquidation: 10% buffer
```

### Margin Level Interpretazione

```
Margin Level = Total Assets / Total Borrowed

> 2.0: HEALTHY 💚 (200% collateral)
1.5-2.0: CAUTION ⚠️ (150-200%)
1.1-1.5: WARNING 🟡 (110-150%)
< 1.1: CRITICAL 🔴 (< 110% - vicino liquidazione!)
```

### Liquidation Alert

Se margin level < 1.5:
- ⚠️ WARNING alert
- Bot può auto-chiudere posizioni
- Considera deposito più collaterale

### Excel Report

Il bot genera `paper_trading_report.xlsx`:
- **Trades sheet**: Tutti i trade con margin data
- **Margin Stats**: Statistiche margin (borrowed, interest, etc.)
- **Equity Curve**: Grafico performance

---

## 🛡️ Risk Management

### Leverage Raccomandato

| Esperienza | Leverage | Note |
|-----------|----------|------|
| **Beginner** | 1.5x-2x | Conservativo, impara i basics |
| **Intermediate** | 2x-3x | Esperienza con margin |
| **Advanced** | 3x-5x | Solo se sai cosa fai |

**Il bot limita a MAX_LEVERAGE configurato.**

### Position Sizing

Il bot calcola automaticamente:
```
Risk per trade = Balance × RISK_PER_TRADE
Position size considerando leverage e SL
```

Raccomandazioni:
- RISK_PER_TRADE: 0.01-0.02 (1-2%)
- Mai più di 5% per trade
- Con leverage, il risk è amplificato!

### Stop Loss

SL è SEMPRE attivo:
- Basato su struttura (sweep, retrace low)
- Include buffer ATR
- Automaticamente triggera close + repay

### Daily Limits

Configura limiti giornalieri:
```python
"MAX_DAILY_LOSS": 0.05,  # 5% max loss al giorno
"MAX_DAILY_TRADES": 10,  # Max 10 trade al giorno
```

---

## 🚨 Emergency Procedures

### Se Margin Level Scende

**Opzione 1: Deposita Collaterale**
- Trasferisci più USDC da Spot a Margin
- Aumenta margin level immediatamente

**Opzione 2: Chiudi Posizioni**
- Chiudi manualmente su Binance
- Oppure usa emergency stop del bot

**Opzione 3: Partial Close**
- Riduci size della posizione
- Mantieni trade aperto ma con meno risk

### Emergency Stop

Nel terminale dove gira il bot:
```
CTRL+C (stop gracefully)
```

Il bot:
1. Ferma nuovo trading
2. Opzionalmente chiude posizioni aperte
3. Salva stato
4. Exit pulito

### Liquidation Prevention

Il bot include:
- Real-time margin monitoring
- Auto-alert quando level < 1.5
- Auto-close opzionale se critical
- Liquidation price sempre visibile

---

## ❓ FAQ

### Q: Quanto capitale serve per iniziare?

**Paper mode**: $0 (simulazione)
**Live mode**: Minimo $100-200 USDC per testing, $500-1000 per trading serio

### Q: Qual è il leverage ottimale?

Dipende dalla tua esperienza:
- Beginner: 1.5x-2x
- Intermediate: 2x-3x
- Advanced: 3x max

Più leverage = più rischio!

### Q: Come calcolo la liquidation price?

Il bot lo calcola automaticamente:
```
Liq Price = Entry Price × (1 - 1/Leverage + buffer)
```

Esempio:
- Entry: $50,000
- Leverage: 3x
- Liquidation: ~$45,500 (-9%)

### Q: Quanto interest pago?

Binance Margin interest varia per coin, tipicamente:
- BTC: ~0.02% daily (~7% yearly)
- ETH: ~0.02% daily
- Calcolato ogni ora

Il bot traccia interest e lo sottrae dal P&L.

### Q: Posso usare Isolated Margin?

Attualmente il bot supporta solo Cross Margin. Isolated può essere aggiunto in futuro.

### Q: È sicuro lasciare il bot running overnight?

**Rischi:**
- Movimenti di mercato improvvisi
- Gap di prezzo
- Problemi connessione

**Precauzioni:**
- Set stop loss sempre
- Monitor margin level
- Start con leverage basso
- Considera VPS per uptime

### Q: Cosa succede se perdo connessione?

Se il bot perde connessione:
- Posizioni su Binance restano aperte
- SL/TP su Binance sono attivi
- Riconnetti e bot riprende monitoring

---

## 📚 Risorse Utili

### Binance Docs
- [Margin Trading Guide](https://www.binance.com/en/support/faq/margin-trading)
- [Cross Margin vs Isolated](https://www.binance.com/en/support/faq/cross-margin-vs-isolated-margin)
- [Margin Level Calculation](https://www.binance.com/en/support/faq/how-to-calculate-margin-level)

### Risk Education
- Leggi: `MARGIN_TRADING_RISKS.md`
- Leggi: `LIVE_MODE_CHECKLIST.md`

---

## ✅ Pre-Live Checklist

Prima di passare a live trading:

- [ ] Testato in paper mode minimo 1 settimana
- [ ] Compresi tutti i rischi margin trading
- [ ] API key creata con permessi corretti
- [ ] IP whitelist configurato
- [ ] Withdraw disabilitato su API
- [ ] Balance USDC depositato e trasferito a Margin
- [ ] Leverage impostato conservativo (2x-3x)
- [ ] Risk per trade basso (1-2%)
- [ ] Stop loss sempre attivo
- [ ] Monitoring setup (Excel, logs)
- [ ] Emergency stop procedure chiara

---

## ⚠️ DISCLAIMER FINALE

**ATTENZIONE:**
- Margin trading comporta rischi elevati
- Puoi perdere più del tuo investimento iniziale
- Leverage amplifica sia guadagni che perdite
- Non investire denaro che non puoi permetterti di perdere
- Questo è un tool educativo
- Gli autori non sono responsabili per perdite

**USA A TUO RISCHIO E RESPONSABILITÀ**

---

**Buon trading responsabile! 📈**

Per domande o problemi, consulta la documentazione o contatta supporto.
