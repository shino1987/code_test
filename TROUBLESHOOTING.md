# 🔧 TROUBLESHOOTING - Guida Risoluzione Problemi

## ⚠️ Errore: `SyntaxError: invalid character '·' (U+00B7)`

### Problema
```
File "C:\Users\...\GITHUB.PY", line 30
  ·
  ^
SyntaxError: invalid character '·' (U+00B7)
```

### Causa
Questo errore si verifica quando il file Python contiene **caratteri non validi** (come il middle dot '·') che non dovrebbero essere presenti nel codice. 

**Cause comuni:**
1. 📋 **Copy/paste da browser/documenti** - Inserisce caratteri invisibili
2. 💾 **Encoding file sbagliato** - File salvato con encoding non-UTF-8
3. 🔄 **Conversione Windows/Linux** - Problemi line endings o encoding
4. 📝 **Editor di testo problematico** - Alcuni editor inseriscono caratteri strani

---

## ✅ SOLUZIONI

### Soluzione 1: Re-download File Pulito (RACCOMANDATO)

**Step-by-step:**

1. **Elimina il file corrotto**
   ```bash
   # Windows PowerShell
   Remove-Item GITHUB.PY
   
   # Linux/Mac
   rm GITHUB.PY
   ```

2. **Re-download da GitHub**
   
   **Opzione A: Git Clone (migliore)**
   ```bash
   git clone https://github.com/shino1987/code_test.git
   cd code_test
   ```
   
   **Opzione B: Download diretto**
   - Vai su https://github.com/shino1987/code_test
   - Click su `paper_trading_bot.py`
   - Click su "Raw" (in alto a destra)
   - Ctrl+S per salvare (NON copiare il testo!)
   - Salva come `paper_trading_bot.py`

3. **Verifica encoding**
   ```bash
   # Windows PowerShell
   Get-Content paper_trading_bot.py | Select-Object -First 3
   
   # Linux/Mac
   head -3 paper_trading_bot.py
   ```
   
   Dovresti vedere:
   ```python
   #!/usr/bin/env python3
   # -*- coding: utf-8 -*-
   """
   ```

4. **Test esecuzione**
   ```bash
   python paper_trading_bot.py
   ```

---

### Soluzione 2: Pulisci File Esistente

Se vuoi tenere il file attuale e pulirlo:

**Windows PowerShell:**
```powershell
# 1. Apri in Notepad++, VS Code, o editor con encoding support
# 2. Seleziona: File → Save As
# 3. Encoding: UTF-8 (senza BOM)
# 4. Salva
```

**Python Script per pulizia:**
```python
# clean_file.py
with open('GITHUB.PY', 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

# Rimuovi caratteri strani
content = content.replace('·', '')  # Middle dot
content = content.replace('\u00b7', '')  # Middle dot unicode

# Salva pulito
with open('GITHUB_CLEAN.PY', 'w', encoding='utf-8') as f:
    f.write(content)

print("File pulito salvato come GITHUB_CLEAN.PY")
```

Esegui:
```bash
python clean_file.py
mv GITHUB_CLEAN.PY GITHUB.PY
```

---

### Soluzione 3: Verifica Encoding

**Check encoding attuale:**

```python
# check_encoding.py
import chardet

with open('GITHUB.PY', 'rb') as f:
    raw = f.read()
    result = chardet.detect(raw)
    print(f"Encoding: {result['encoding']}")
    print(f"Confidence: {result['confidence']}")
```

**Deve essere:** `UTF-8` con confidence > 0.9

**Se diverso, converti:**
```python
# convert_utf8.py
# Leggi con encoding rilevato
with open('GITHUB.PY', 'r', encoding='ISO-8859-1') as f:  # o altro encoding
    content = f.read()

# Salva come UTF-8
with open('GITHUB.PY', 'w', encoding='utf-8') as f:
    f.write(content)
```

---

### Soluzione 4: Trova Caratteri Invalidi

**Trova esattamente dove sono i problemi:**

```python
# find_invalid.py
with open('GITHUB.PY', 'r', encoding='utf-8', errors='replace') as f:
    for line_num, line in enumerate(f, 1):
        # Cerca caratteri strani
        if '·' in line or '�' in line:
            print(f"Riga {line_num}: {repr(line[:100])}")
        
        # Cerca bytes non-ASCII
        try:
            line.encode('ascii')
        except UnicodeEncodeError as e:
            print(f"Riga {line_num}: Carattere non-ASCII: {e}")
```

---

## 🛡️ PREVENZIONE

### Editor Raccomandati con UTF-8 Default:

1. **VS Code** ✅
   - Default UTF-8
   - Mostra encoding in basso
   - Auto-detect

2. **PyCharm** ✅
   - Default UTF-8
   - Syntax checking integrato

3. **Notepad++** ✅
   - Settings → Preferences → New Document → UTF-8

4. **Sublime Text** ✅
   - Default UTF-8

### ❌ Editor da EVITARE:
- Notepad Windows (usa encoding misto)
- WordPad (inserisce formattazione)
- Microsoft Word (MAI per codice!)

---

## 🧪 TEST FINALE

Dopo aver applicato una soluzione, testa:

```bash
# 1. Test syntax Python
python -m py_compile paper_trading_bot.py

# 2. Se passa, output: nessun errore
# 3. Se fallisce, mostra riga con errore

# 4. Test esecuzione
python paper_trading_bot.py --help
```

**Output atteso:**
- Nessun SyntaxError
- Bot parte correttamente

---

## 📞 SUPPORTO

Se i problemi persistono:

1. **Verifica versione Python**
   ```bash
   python --version  # Deve essere 3.8+
   ```

2. **Verifica pip e dipendenze**
   ```bash
   pip install -r requirements.txt
   ```

3. **Check file integrità**
   ```bash
   # Linux/Mac
   md5sum paper_trading_bot.py
   
   # Windows
   certutil -hashfile paper_trading_bot.py MD5
   ```

4. **GitHub Issue**
   - Apri issue su https://github.com/shino1987/code_test/issues
   - Includi:
     - Messaggio errore completo
     - Output `python --version`
     - Sistema operativo
     - Come hai ottenuto il file

---

## 🎯 CHECKLIST RAPIDA

- [ ] File eliminato e re-downloaded da GitHub?
- [ ] Encoding verificato (UTF-8)?
- [ ] Editor con UTF-8 support?
- [ ] `python -m py_compile` passa senza errori?
- [ ] Nessun carattere '·' o '�' visibile?
- [ ] File inizia con `#!/usr/bin/env python3`?
- [ ] Python versione 3.8+?

Se tutte ✅ → Il bot dovrebbe funzionare!

---

## 💡 TIP PRO

**Per evitare problemi futuri:**

1. Usa sempre `git clone` invece di download manuale
2. Configura editor per UTF-8 default
3. Non copiare codice da browser (usa git)
4. Attiva "Show all characters" nell'editor
5. Usa virtual environment Python

```bash
# Setup pulito
git clone https://github.com/shino1987/code_test.git
cd code_test
python -m venv venv
source venv/bin/activate  # Linux/Mac
# o: venv\Scripts\activate  # Windows
pip install -r requirements.txt
python paper_trading_bot.py
```

**HAPPY TRADING!** 📊🚀
