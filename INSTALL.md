# 🚀 INSTALLAZIONE RAPIDA - Paper Trading Bot

## ⚡ Quick Start (3 minuti)

### Windows PowerShell

```powershell
# 1. Scarica bot
git clone https://github.com/shino1987/code_test.git
cd code_test

# 2. Installa dipendenze
pip install -r requirements.txt

# 3. Run!
python paper_trading_bot.py
```

### Linux / Mac

```bash
# 1. Scarica bot
git clone https://github.com/shino1987/code_test.git
cd code_test

# 2. Installa dipendenze
pip3 install -r requirements.txt

# 3. Run!
python3 paper_trading_bot.py
```

---

## 📦 Dipendenze Richieste

Il bot necessita di questi moduli Python:

| Modulo | Versione | Scopo |
|--------|----------|-------|
| `ccxt` | ≥4.0.0 | Exchange connectivity |
| `pandas` | ≥2.0.0 | Data manipulation |
| `numpy` | ≥1.24.0 | Numerical computing |
| `xlsxwriter` | ≥3.1.0 | Excel export |
| `openpyxl` | ≥3.1.0 | Excel read/write |

**Tutte incluse in `requirements.txt`!**

---

## ❌ ERRORI COMUNI

### Errore 1: ModuleNotFoundError

```
ModuleNotFoundError: No module named 'xlsxwriter'
```

**Soluzione:**
```bash
pip install -r requirements.txt
```

O manualmente:
```bash
pip install xlsxwriter ccxt pandas numpy openpyxl
```

---

### Errore 2: pip non trovato

```
'pip' is not recognized as an internal or external command
```

**Soluzione Windows:**
```powershell
# Usa python -m pip
python -m pip install -r requirements.txt

# O aggiungi Python a PATH
# Settings → System → About → Advanced system settings → Environment Variables
# Add: C:\Python3X\Scripts to PATH
```

**Soluzione Linux/Mac:**
```bash
# Usa pip3
pip3 install -r requirements.txt

# O install pip
sudo apt-get install python3-pip  # Ubuntu/Debian
brew install python3              # Mac
```

---

### Errore 3: Permission denied

```
ERROR: Could not install packages due to an EnvironmentError: [Errno 13] Permission denied
```

**Soluzione:**
```bash
# Install per utente (raccomandato)
pip install --user -r requirements.txt

# O con sudo (Linux/Mac)
sudo pip3 install -r requirements.txt

# O crea virtual environment (meglio!)
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
pip install -r requirements.txt
```

---

### Errore 4: Versione Python vecchia

```
ERROR: Python 3.7 is not supported
```

**Soluzione:**

Installa Python 3.8 o superiore:
- **Windows**: https://www.python.org/downloads/
- **Linux**: `sudo apt-get install python3.10`
- **Mac**: `brew install python@3.10`

Verifica versione:
```bash
python --version  # Deve essere ≥ 3.8
```

---

## 🔧 INSTALLAZIONE AVANZATA

### Con Virtual Environment (RACCOMANDATO)

**Vantaggi:**
- Isolamento dipendenze
- Nessun conflitto con altri progetti
- Facile cleanup

**Setup:**

```bash
# 1. Crea virtual environment
python -m venv venv

# 2. Attiva venv
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 3. Install dipendenze
pip install -r requirements.txt

# 4. Run bot
python paper_trading_bot.py

# 5. Quando finito, disattiva
deactivate
```

---

### Install Specifiche per Sistema

#### Windows con Anaconda

```powershell
# 1. Crea conda environment
conda create -n trading python=3.10
conda activate trading

# 2. Install dipendenze
conda install pandas numpy
pip install ccxt xlsxwriter openpyxl

# 3. Run
python paper_trading_bot.py
```

#### Ubuntu/Debian Linux

```bash
# 1. Install Python e pip
sudo apt-get update
sudo apt-get install python3 python3-pip python3-venv

# 2. Clone e install
git clone https://github.com/shino1987/code_test.git
cd code_test
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Run
python3 paper_trading_bot.py
```

#### macOS

```bash
# 1. Install Python (Homebrew)
brew install python@3.10

# 2. Clone e install
git clone https://github.com/shino1987/code_test.git
cd code_test
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt

# 3. Run
python3 paper_trading_bot.py
```

---

## ✅ VERIFICA INSTALLAZIONE

### Check 1: Python Version
```bash
python --version
# Output atteso: Python 3.8.x o superiore
```

### Check 2: pip Funzionante
```bash
pip --version
# Output atteso: pip 21.x.x from ...
```

### Check 3: Dependencies Installate
```bash
pip list | grep -E "ccxt|pandas|numpy|xlsxwriter|openpyxl"
# Output atteso:
# ccxt          4.x.x
# pandas        2.x.x
# numpy         1.x.x
# xlsxwriter    3.x.x
# openpyxl      3.x.x
```

### Check 4: Bot Syntax
```bash
python -m py_compile paper_trading_bot.py
# Nessun output = SUCCESS
```

### Check 5: Bot Esecuzione
```bash
python paper_trading_bot.py
# Dovrebbe partire senza errori
```

---

## 🎯 CHECKLIST COMPLETA

Prima di eseguire il bot:

### Sistema
- [ ] Python 3.8+ installato
- [ ] pip funzionante
- [ ] Git installato (opzionale ma raccomandato)

### Files
- [ ] Repository clonato o file scaricati
- [ ] `requirements.txt` presente
- [ ] `paper_trading_bot.py` presente

### Dipendenze
- [ ] `pip install -r requirements.txt` eseguito
- [ ] Nessun errore durante install
- [ ] Tutti i moduli in `pip list`

### Verifica
- [ ] `python --version` ≥ 3.8
- [ ] `pip list` mostra tutte le dipendenze
- [ ] `python -m py_compile paper_trading_bot.py` passa
- [ ] File encoding UTF-8 (vedi TROUBLESHOOTING.md se errori)

### Esecuzione
- [ ] `python paper_trading_bot.py` parte
- [ ] Nessun ModuleNotFoundError
- [ ] Nessun SyntaxError
- [ ] Bot stampa messaggi iniziali

**Se tutti ✅ → PRONTO PER TRADING!** 🎉

---

## 📚 DOCUMENTAZIONE

### Guide Disponibili:
1. **INSTALL.md** ← Sei qui
2. **START_HERE.md** - Onboarding completo
3. **TROUBLESHOOTING.md** - Fix errori comuni
4. **README_PAPER_BOT.md** - Guida utente bot
5. **ICT_STRATEGY_COMPLETE.md** - Strategia ICT

### Next Steps:
1. ✅ Installa dipendenze (questa guida)
2. 📖 Leggi START_HERE.md
3. 🧪 Testa in paper mode
4. 📊 Analizza risultati Excel
5. 🚀 (Opzionale) Setup live trading

---

## 🆘 SUPPORTO

### Se problemi persistono:

1. **Check logs:**
   ```bash
   cat paper_trading_debug.log
   ```

2. **Reinstall clean:**
   ```bash
   pip uninstall -y -r requirements.txt
   pip install -r requirements.txt
   ```

3. **Virtual environment fresh:**
   ```bash
   rm -rf venv
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

4. **GitHub Issue:**
   - https://github.com/shino1987/code_test/issues
   - Include:
     - Output `python --version`
     - Output `pip list`
     - Messaggio errore completo
     - Sistema operativo

---

## 💡 TIPS

### Performance:
- Usa virtual environment (isolamento)
- Update pip regolarmente
- Install in ordine da requirements.txt

### Security:
- Virtual environment previene conflitti
- Non usare sudo pip se non necessario
- Verifica source dei package

### Maintenance:
- Update dipendenze periodicamente
- Check deprecated warnings
- Backup environment con `pip freeze`

---

## 🎊 SUCCESS!

Se sei arrivato qui e tutti i check sono ✅:

**CONGRATULAZIONI!** 🎉

Il bot è installato e pronto per paper trading!

```bash
python paper_trading_bot.py
```

**HAPPY TRADING!** 📊💰🚀

---

**Versione:** 1.0  
**Ultima update:** 2024-02-11  
**Status:** Complete & Tested
