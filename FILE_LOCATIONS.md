# 📁 File Locations Guide / Dove Scaricare i File

## 🇮🇹 Italiano

### Dove vengono salvati i file?

Il bot salva tutti i file nella **stessa cartella** dove si trova il file `ict_bot_minimal.py`.

#### File CSV delle Operazioni

**Nome file:** `ict_trades.csv`

**Posizione:** Nella stessa directory del bot

**Come trovarlo:**

1. **Su Windows:**
   ```cmd
   dir ict_trades.csv
   ```
   Oppure cerca nella cartella dove hai scaricato il bot.

2. **Su Linux/Mac:**
   ```bash
   ls ict_trades.csv
   pwd  # Mostra la directory corrente
   ```

3. **Percorso completo:**
   Se hai scaricato il bot in `C:\Users\TuoNome\bot\`, il file sarà:
   ```
   C:\Users\TuoNome\bot\ict_trades.csv
   ```

#### Aprire il File CSV

**Con Excel:**
1. Apri Microsoft Excel
2. File → Apri
3. Naviga alla cartella del bot
4. Seleziona `ict_trades.csv`

**Con Google Sheets:**
1. Vai su sheets.google.com
2. File → Importa
3. Carica `ict_trades.csv`

**Con un editor di testo:**
1. Fai doppio clic su `ict_trades.csv`
2. Si aprirà con il programma predefinito

---

## 🇬🇧 English

### Where are files saved?

The bot saves all files in the **same folder** where `ict_bot_minimal.py` is located.

#### Trade Log CSV File

**Filename:** `ict_trades.csv`

**Location:** Same directory as the bot script

**How to find it:**

1. **On Windows:**
   ```cmd
   dir ict_trades.csv
   ```
   Or look in the folder where you downloaded the bot.

2. **On Linux/Mac:**
   ```bash
   ls ict_trades.csv
   pwd  # Shows current directory
   ```

3. **Full path example:**
   If you downloaded the bot to `C:\Users\YourName\bot\`, the file will be at:
   ```
   C:\Users\YourName\bot\ict_trades.csv
   ```

#### Opening the CSV File

**With Excel:**
1. Open Microsoft Excel
2. File → Open
3. Navigate to bot folder
4. Select `ict_trades.csv`

**With Google Sheets:**
1. Go to sheets.google.com
2. File → Import
3. Upload `ict_trades.csv`

**With a text editor:**
1. Double-click `ict_trades.csv`
2. It will open with default program

---

## 📂 All Files Created by the Bot

| File Name | Description | Location |
|-----------|-------------|----------|
| `ict_trades.csv` | Trade log (all trades) | Same folder as bot |
| `.env` | API keys (if created) | Same folder as bot |

## 🔍 Finding Files by Operating System

### Windows

**Method 1: File Explorer**
1. Open File Explorer
2. Navigate to where you downloaded the bot
3. Look for `ict_trades.csv`

**Method 2: Command Prompt**
```cmd
cd path\to\your\bot
dir ict_trades.csv
```

**Method 3: Search**
1. Press Windows Key + S
2. Type `ict_trades.csv`
3. Click on the file to see its location

### Linux/Mac

**Method 1: Terminal**
```bash
# Navigate to bot directory
cd /path/to/your/bot

# List files
ls -la ict_trades.csv

# Show full path
pwd
realpath ict_trades.csv
```

**Method 2: File Manager**
1. Open Files (Linux) or Finder (Mac)
2. Navigate to bot directory
3. Look for `ict_trades.csv`

**Method 3: Find command**
```bash
find ~ -name "ict_trades.csv"
```

## 📍 Checking File Location from Within the Bot

You can verify where files are saved by checking the bot's console output:

```
[2026-02-11 15:30:00] CSV file created: ict_trades.csv
```

Or add this to check the absolute path:

```python
import os
print(f"CSV file location: {os.path.abspath('ict_trades.csv')}")
```

## 🔧 Changing File Location (Advanced)

If you want to save files in a different location, edit `ict_bot_minimal.py`:

```python
# Change this line (around line 65)
CSV_PATH = "ict_trades.csv"

# To something like:
CSV_PATH = "/home/user/trading_logs/ict_trades.csv"  # Linux/Mac
CSV_PATH = "C:\\Users\\YourName\\Documents\\ict_trades.csv"  # Windows
```

**Important:** Make sure the directory exists before running the bot!

## 📊 CSV File Format

The CSV file contains these columns:

```csv
timestamp,symbol,side,entry_price,sl_price,tp1_price,tp2_price,exit_price,pnl_gross_pct,pnl_net_pct,duration_min,exit_reason
```

**Example row:**
```csv
2026-02-11 15:30:00,BTC/USDT,LONG,41523.45,40479.75,42100.00,42650.00,42100.00,1.39,1.19,45.3,TP1_HIT
```

## 🔄 Backing Up Your Data

### Manual Backup

**Copy the file:**
```bash
# Linux/Mac
cp ict_trades.csv ict_trades_backup_$(date +%Y%m%d).csv

# Windows
copy ict_trades.csv ict_trades_backup_%date%.csv
```

### Automatic Backup (Script)

Create `backup_trades.sh` (Linux/Mac):
```bash
#!/bin/bash
cp ict_trades.csv "backups/ict_trades_$(date +%Y%m%d_%H%M%S).csv"
```

Create `backup_trades.bat` (Windows):
```batch
@echo off
copy ict_trades.csv "backups\ict_trades_%date%_%time%.csv"
```

## 📈 Viewing Trade History

### Quick View (Terminal)

**Show last 10 trades:**
```bash
# Linux/Mac
tail -n 10 ict_trades.csv

# Windows (PowerShell)
Get-Content ict_trades.csv -Tail 10
```

**Count total trades:**
```bash
# Linux/Mac (subtract 1 for header)
wc -l ict_trades.csv

# Windows (PowerShell)
(Get-Content ict_trades.csv).Length - 1
```

### Analyze with Python

```python
import pandas as pd

# Load trades
df = pd.read_csv('ict_trades.csv')

# Show summary
print(f"Total trades: {len(df)}")
print(f"Win rate: {(df['exit_reason'] != 'SL_HIT').sum() / len(df) * 100:.1f}%")
print(f"Average PnL: {df['pnl_net_pct'].mean():.2f}%")
print(f"Total PnL: {df['pnl_net_pct'].sum():.2f}%")

# Show last trades
print("\nLast 5 trades:")
print(df.tail(5))
```

## ❓ FAQ

**Q: Il file CSV non esiste**
- A: Il file viene creato quando il bot apre la prima operazione. Se non vedi il file, il bot non ha ancora fatto trade.

**Q: Non trovo il file**
- A: Usa il comando `pwd` (Linux/Mac) o `cd` (Windows) per vedere dove ti trovi, poi cerca `ict_trades.csv` in quella cartella.

**Q: Il file è vuoto**
- A: Il file contiene solo l'header finché non vengono registrate operazioni.

**Q: Posso aprire il file mentre il bot è in esecuzione?**
- A: Sì, ma meglio usare "solo lettura" per evitare problemi. Excel potrebbe bloccare il file.

**Q: Come esporto i dati?**
- A: Il file CSV è già in formato esportabile. Puoi aprirlo con Excel, Google Sheets, o qualsiasi programma.

---

## 🆘 Troubleshooting

### File Not Found

**Problem:** Can't find `ict_trades.csv`

**Solutions:**
1. Check you're in the right directory:
   ```bash
   pwd  # Linux/Mac
   cd   # Windows
   ```

2. Search for the file:
   ```bash
   # Linux/Mac
   find . -name "ict_trades.csv"
   
   # Windows (PowerShell)
   Get-ChildItem -Recurse -Filter "ict_trades.csv"
   ```

3. The bot creates the file on first trade - run the bot and wait for a trade

### Permission Denied

**Problem:** Can't open or modify the file

**Solutions:**
1. Close Excel or any program that has the file open
2. Check file permissions:
   ```bash
   # Linux/Mac
   ls -l ict_trades.csv
   chmod 644 ict_trades.csv  # If needed
   ```

### File is Locked

**Problem:** Excel says file is in use

**Solutions:**
1. Close the bot (Ctrl+C)
2. Close Excel
3. Reopen the file

---

## 📞 Need Help?

If you still can't find your files:

1. Check the console output when starting the bot
2. Look for "CSV file created: ict_trades.csv" message
3. Use `pwd` or `cd` to see current directory
4. Search your computer for "ict_trades.csv"

---

**Tip:** Always run the bot from the same directory to keep all your trade logs in one place!
