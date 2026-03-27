# ✅ Live Mode Checklist

## Prima di Attivare Live Trading

Usa questa checklist per assicurarti di essere pronto per il live trading con margin su Binance.

---

## 📋 Pre-Requisiti

### Esperienza
- [ ] Ho esperienza con trading crypto
- [ ] Comprendo il margin trading e i suoi rischi
- [ ] Ho testato il bot in paper mode per almeno 1 settimana
- [ ] Ho letto tutta la documentazione (`BINANCE_MARGIN_GUIDE.md`, `MARGIN_TRADING_RISKS.md`)

### Conoscenza Tecnica
- [ ] Comprendo come funziona la strategia ICT
- [ ] So cosa sono: BIAS, SWEEP, DISPLACEMENT, RETRACE, CONFIRMATION
- [ ] Comprendo SL strutturale e TP a 2R
- [ ] So cos'è il margin level e la liquidation
- [ ] So come calcolare il risk per trade

---

## 🔐 Setup Binance

### Account
- [ ] Account Binance verificato (KYC completato)
- [ ] 2FA abilitato (Google Authenticator o SMS)
- [ ] Email verification attiva
- [ ] Anti-phishing code impostato

### API Key
- [ ] API key creata con nome descrittivo
- [ ] Permesso "Enable Reading" attivato
- [ ] Permesso "Enable Spot & Margin Trading" attivato
- [ ] **"Enable Withdrawals" DISABILITATO** ⚠️
- [ ] IP whitelist configurato (opzionale ma raccomandato)
- [ ] API key e secret salvati in luogo sicuro
- [ ] API key testata con `--test-connection`

### Margin Account
- [ ] Margin trading abilitato su Binance
- [ ] USDC depositato su Binance
- [ ] USDC trasferito da Spot a Margin Wallet
- [ ] Cross Margin selezionato (non Isolated)
- [ ] Balance verificato in Margin Wallet

---

## ⚙️ Configurazione Bot

### File Config
- [ ] `MODE` impostato a `"LIVE"`
- [ ] `LIVE_TRADING_ENABLED` = `True`
- [ ] `API_KEY` inserito correttamente
- [ ] `API_SECRET` inserito correttamente
- [ ] `REQUIRE_CONFIRMATION` = `True` (per controllo manuale)

### Symbols
- [ ] Coppie USDC configurate: `BTC/USDC`, `ETH/USDC`, etc.
- [ ] Verificato che coppie esistono su Binance Margin
- [ ] Verificato liquidità sufficiente

### Risk Management
- [ ] `MAX_LEVERAGE` impostato conservativo (≤ 3x)
- [ ] `RISK_PER_TRADE` basso (1-2%)
- [ ] `MIN_MARGIN_LEVEL` >= 1.5
- [ ] `INITIAL_CAPITAL` corrisponde al balance reale USDC
- [ ] Stop loss sempre attivo
- [ ] Take profit configurato (2R)

### Limiti
- [ ] `MAX_POSITIONS` limitato (1-2)
- [ ] `MAX_DAILY_LOSS` impostato (es. 5%)
- [ ] `MAX_DAILY_TRADES` limitato (es. 10)

---

## 🧪 Testing

### Connection Test
- [ ] Eseguito `--test-connection` con successo
- [ ] Connessione Binance OK
- [ ] Balance USDC visibile
- [ ] Margin enabled verificato
- [ ] Coppie disponibili caricate

### Paper Mode Results
- [ ] Testato in paper mode per minimo 1 settimana
- [ ] Win rate accettabile (>45%)
- [ ] Drawdown accettabile (<20%)
- [ ] Strategia funziona come atteso
- [ ] Nessun bug o crash

### Small Live Test
- [ ] Pronto a iniziare con capitale PICCOLO ($100-200)
- [ ] Primo trade con size minima
- [ ] Monitor attivo durante primo trade

---

## 🛡️ Safety Measures

### Pre-Trade
- [ ] Balance check prima di ogni trade
- [ ] Margin level > MIN_MARGIN_LEVEL
- [ ] Nessuna posizione vicina a liquidazione
- [ ] Leverage entro limiti configurati

### During Trade
- [ ] Monitor margin level ogni 5-10 minuti
- [ ] Alert configurati per margin basso
- [ ] Stop loss sempre attivo
- [ ] Liquidation price monitorato

### Emergency
- [ ] So come fare emergency stop (CTRL+C)
- [ ] So come chiudere posizione manualmente su Binance
- [ ] So come aggiungere collaterale se necessario
- [ ] Ho plan B se bot crash

---

## 📊 Monitoring Setup

### Real-time
- [ ] Console output visibile
- [ ] Log file monitored (`tail -f paper_trading_debug.log`)
- [ ] Excel report generato periodicamente
- [ ] Alert system configurato

### Logging
- [ ] Debug logging attivo
- [ ] ICT signals tracked
- [ ] Trade log CSV generato
- [ ] Balance log aggiornato

### Backup
- [ ] Config file backed up
- [ ] Strategia documentata
- [ ] Emergency contacts pronti

---

## 💰 Capital Management

### Initial Capital
- [ ] Amount che posso permettermi di PERDERE
- [ ] Non denaro per spese essenziali
- [ ] Non prestiti o debiti
- [ ] Buffer per emergenze fuori dal trading

### Position Sizing
- [ ] Comprendo come bot calcola size
- [ ] Size considera leverage
- [ ] Risk per trade accettabile (1-2% balance)
- [ ] Total exposure < 10% balance

### Limits
- [ ] Max loss giornaliero definito
- [ ] Max drawdown tollerabile definito
- [ ] Se raggiungo limite, STOP trading

---

## 📖 Risk Understanding

### Margin Trading Risks
- [ ] Comprendo che leverage amplifica PERDITE
- [ ] So cos'è la liquidazione
- [ ] Comprendo interest accumulation
- [ ] So calcolare liquidation price

### Market Risks
- [ ] Comprendo volatilità crypto
- [ ] So cosa sono gap di prezzo
- [ ] Comprendo slippage
- [ ] Aware di eventi black swan

### Technical Risks
- [ ] So che connessione può interrompersi
- [ ] API può avere problemi
- [ ] Bot può avere bug (testato ma non perfetto)
- [ ] Exchange può avere downtime

---

## 🚨 Emergency Procedures

### If Margin Level Drops
- [ ] Procedura: Deposito collaterale o chiudo posizione
- [ ] Account Binance accessibile da mobile
- [ ] Fondi extra disponibili se necessario

### If Bot Crashes
- [ ] Procedura: Verifica posizioni su Binance
- [ ] SL/TP sono attivi su exchange
- [ ] Posso gestire manualmente se necessario

### If Major Loss
- [ ] Procedura: Stop trading, analizza, impara
- [ ] Non revenge trading
- [ ] Review strategia
- [ ] Riduci risk se riprendi

---

## 📝 Documentation

### Before Starting
- [ ] Screenshot config completo
- [ ] Annotato strategia e obiettivi
- [ ] Trading plan scritto
- [ ] Risk management plan documentato

### Trading Journal
- [ ] Pronto a tenere journal
- [ ] Track thoughts e decisioni
- [ ] Review settimanale pianificata
- [ ] Metrics da monitorare definiti

---

## ✅ Final Confirmation

Prima di attivare live trading, conferma:

- [ ] **HO LETTO E COMPRESO TUTTO**
- [ ] **ACCETTO TUTTI I RISCHI**
- [ ] **POSSO PERMETTERMI DI PERDERE QUESTO CAPITALE**
- [ ] **NON USERÒ LEVERAGE ECCESSIVO**
- [ ] **INIZIERÒ CON CAPITALE PICCOLO**
- [ ] **MONITORERÒ ATTIVAMENTE**
- [ ] **FERMERÒ SE NECESSARIO**

---

## 🎯 First Live Trade Checklist

Quando sei pronto per il primo trade live:

1. [ ] Balance check: `python3 paper_trading_bot.py --test-connection`
2. [ ] Start bot: `python3 paper_trading_bot.py`
3. [ ] Wait per segnale ICT completo (tutti i 5 step)
4. [ ] Review segnale attentamente
5. [ ] Conferma trade (se REQUIRE_CONFIRMATION = True)
6. [ ] Monitor posizione attivamente
7. [ ] Non panico se va contro - SL ti protegge
8. [ ] Review trade dopo chiusura
9. [ ] Aggiorna journal
10. [ ] Pausa e rifletti prima del prossimo trade

---

## ⚠️ QUANDO NON TRADARE

**FERMA il bot se:**
- ⛔ Emotivamente compromesso (stress, rabbia, euforia)
- ⛔ Sotto influenza di alcol o droghe
- ⛔ Stanco o non concentrato
- ⛔ Alta volatilità anomala (flash crash, news major)
- ⛔ Problemi tecnici (connessione, API issues)
- ⛔ Superato daily loss limit
- ⛔ Margin level troppo basso
- ⛔ Non hai tempo per monitorare

**Trading è un business, non gambling!**

---

## 📞 Support & Help

Se hai dubbi o problemi:

1. **Stop trading** - sicurezza prima
2. Review documentazione
3. Check logs per errori
4. Verifica posizioni su Binance
5. Community/support se disponibile

---

## 🎓 Continuous Learning

Anche dopo live trading:

- [ ] Review ogni trade (win o loss)
- [ ] Tieni trading journal dettagliato
- [ ] Analizza performance settimanale
- [ ] Studia ICT methodology (sempre meglio)
- [ ] Adatta strategia basata su risultati
- [ ] Never stop learning!

---

## ✅ Ready to Go?

Se hai completato TUTTI i checkbox sopra:

**SEI PRONTO PER LIVE TRADING! 🚀**

**Remember:**
- Start small
- Monitor actively
- Stop on loss limit
- Learn continuously
- Trade responsibly

**BUONA FORTUNA E TRADE SICURO! 📈💪**

---

**Ultima verifica:** Ho letto tutto e confermo di essere pronto: _________ (Firma/Data)
