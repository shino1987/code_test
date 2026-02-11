#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script di Fix Encoding - Pulisce file Python corrotti
Risolve: SyntaxError: invalid character '·' (U+00B7)
"""

import sys
import os
import shutil
from pathlib import Path

def detect_encoding(filepath):
    """Rileva encoding del file"""
    try:
        import chardet
        with open(filepath, 'rb') as f:
            raw = f.read()
            result = chardet.detect(raw)
            return result['encoding'], result['confidence']
    except ImportError:
        print("⚠️ chardet non installato. Assumo UTF-8")
        return 'utf-8', 1.0

def find_invalid_characters(filepath):
    """Trova caratteri invalidi nel file"""
    invalid_chars = []
    
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        for line_num, line in enumerate(f, 1):
            # Cerca caratteri problematici comuni
            problematic = ['·', '�', '\u00b7', '\ufffd']
            for char in problematic:
                if char in line:
                    invalid_chars.append({
                        'line': line_num,
                        'char': char,
                        'char_code': f'U+{ord(char):04X}',
                        'preview': line[:80].strip()
                    })
    
    return invalid_chars

def clean_file(input_file, output_file=None):
    """Pulisce file rimuovendo caratteri invalidi"""
    
    if output_file is None:
        output_file = input_file + '.clean'
    
    # Backup originale
    backup_file = input_file + '.backup'
    shutil.copy2(input_file, backup_file)
    print(f"✅ Backup creato: {backup_file}")
    
    # Leggi file
    try:
        with open(input_file, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
    except Exception as e:
        print(f"❌ Errore lettura file: {e}")
        return False
    
    # Rimuovi caratteri problematici
    replacements = {
        '·': '',  # Middle dot
        '\u00b7': '',  # Middle dot unicode
        '�': '',  # Replacement character
        '\ufffd': '',  # Replacement character unicode
        '\r\n': '\n',  # Normalizza line endings
    }
    
    original_len = len(content)
    for old, new in replacements.items():
        content = content.replace(old, new)
    
    cleaned_len = len(content)
    chars_removed = original_len - cleaned_len
    
    # Salva file pulito
    try:
        with open(output_file, 'w', encoding='utf-8', newline='\n') as f:
            f.write(content)
        print(f"✅ File pulito salvato: {output_file}")
        print(f"   Caratteri rimossi: {chars_removed}")
        return True
    except Exception as e:
        print(f"❌ Errore scrittura file: {e}")
        return False

def test_syntax(filepath):
    """Test syntax Python del file"""
    try:
        import py_compile
        py_compile.compile(filepath, doraise=True)
        print(f"✅ Syntax Python: OK")
        return True
    except SyntaxError as e:
        print(f"❌ Syntax Error: {e}")
        print(f"   Riga {e.lineno}: {e.text}")
        return False
    except Exception as e:
        print(f"❌ Errore: {e}")
        return False

def main():
    print("=" * 60)
    print("🔧 FIX ENCODING - Script di Pulizia File Python")
    print("=" * 60)
    print()
    
    # Get filename
    if len(sys.argv) > 1:
        filename = sys.argv[1]
    else:
        filename = input("📁 Nome file da pulire (es. GITHUB.PY): ").strip()
    
    if not filename:
        print("❌ Nome file non fornito!")
        sys.exit(1)
    
    # Check file esiste
    if not os.path.exists(filename):
        print(f"❌ File non trovato: {filename}")
        print()
        print("💡 Suggerimenti:")
        print("   - Verifica il path sia corretto")
        print("   - Usa path assoluto: C:\\Users\\...\\file.py")
        print("   - Verifica di essere nella directory corretta")
        sys.exit(1)
    
    print(f"📄 File: {filename}")
    print()
    
    # Step 1: Detect encoding
    print("🔍 Step 1: Rilevamento encoding...")
    encoding, confidence = detect_encoding(filename)
    print(f"   Encoding rilevato: {encoding} (confidence: {confidence:.2%})")
    
    if encoding.lower() != 'utf-8':
        print(f"   ⚠️ WARNING: Encoding non UTF-8!")
    print()
    
    # Step 2: Find invalid chars
    print("🔍 Step 2: Ricerca caratteri invalidi...")
    invalid = find_invalid_characters(filename)
    
    if invalid:
        print(f"   ⚠️ Trovati {len(invalid)} caratteri invalidi:")
        for item in invalid[:5]:  # Show first 5
            print(f"      Riga {item['line']}: {item['char']} ({item['char_code']})")
            print(f"         {item['preview']}")
        if len(invalid) > 5:
            print(f"      ... e altri {len(invalid) - 5}")
    else:
        print("   ✅ Nessun carattere invalido trovato")
    print()
    
    # Step 3: Clean file
    print("🧹 Step 3: Pulizia file...")
    clean_filename = filename.replace('.PY', '_CLEAN.PY').replace('.py', '_clean.py')
    
    if clean_file(filename, clean_filename):
        print()
        
        # Step 4: Test syntax
        print("🧪 Step 4: Test syntax Python...")
        if test_syntax(clean_filename):
            print()
            print("=" * 60)
            print("✅ FILE PULITO CON SUCCESSO!")
            print("=" * 60)
            print()
            print("📋 Prossimi passi:")
            print(f"   1. Rinomina file pulito:")
            print(f"      mv {clean_filename} {filename}")
            print(f"   2. Oppure usa il file pulito direttamente:")
            print(f"      python {clean_filename}")
            print()
            print(f"   Backup originale: {filename}.backup")
        else:
            print()
            print("⚠️ File pulito ma syntax ancora invalido")
            print("   Potrebbero esserci altri problemi nel codice")
    else:
        print("❌ Pulizia fallita!")
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ Operazione annullata dall'utente")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Errore inatteso: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
