#!/usr/bin/env python3
"""
Fix app/instruments.py to use Dhan instrument keys instead of Upstox keys.
This script downloads Dhan instruments and generates the correct instruments file.
"""

import json
import requests
import csv

print("\n" + "="*70)
print("  FIXING INSTRUMENTS FILE TO USE DHAN KEYS")
print("="*70 + "\n")

# Step 1: Download Dhan instruments
print("📥 Step 1: Downloading Dhan instrument list...")

DHAN_URL = "https://images.dhan.co/api-data/api-scrip-master.csv"

try:
    response = requests.get(DHAN_URL, timeout=30)
    
    if response.status_code != 200:
        print(f"❌ Failed to download: HTTP {response.status_code}")
        exit(1)
    
    print("✅ Successfully downloaded Dhan instruments")
    
    # Parse CSV
    lines = response.text.strip().split('\n')
    reader = csv.DictReader(lines)
    instruments = list(reader)
    
    print(f"📊 Parsed {len(instruments)} instruments")
    
except Exception as e:
    print(f"❌ Error downloading: {e}")
    exit(1)

# Step 2: Build symbol to security ID mapping
print("\n📋 Step 2: Building symbol mappings...")

symbol_to_security_id = {}
security_id_to_info = {}

for instrument in instruments:
    exchange = instrument.get('SEM_EXM_EXCH_ID', '')
    security_id = instrument.get('SEM_SMST_SECURITY_ID', '')
    symbol = instrument.get('SEM_TRADING_SYMBOL', '')
    instrument_type = instrument.get('SEM_INSTRUMENT_NAME', '')
    
    # We're interested in NSE Equity instruments
    if exchange == 'NSE' and instrument_type == 'EQUITY':
        # Clean symbol (remove -EQ suffix if present)
        clean_symbol = symbol.replace('-EQ', '').strip()
        
        symbol_to_security_id[clean_symbol] = security_id
        security_id_to_info[security_id] = instrument

print(f"✅ Mapped {len(symbol_to_security_id)} NSE Equity symbols")

# Step 3: Load F&O symbols
print("\n📋 Step 3: Loading F&O symbols...")

try:
    with open('nse_fo_stock_symbols.txt', 'r') as f:
        content = f.read()
        fo_symbols = [s.strip().strip('"') for s in content.split(',')]
        fo_symbols = [s for s in fo_symbols if s and not s.startswith('0')]
    
    print(f"✅ Loaded {len(fo_symbols)} F&O symbols")
    
except Exception as e:
    print(f"❌ Error loading F&O symbols: {e}")
    exit(1)

# Step 4: Map F&O symbols to Dhan security IDs
print("\n🔍 Step 4: Mapping F&O symbols to Dhan security IDs...")

instrument_list = []
mapped_count = 0
not_found = []

for symbol in fo_symbols:
    security_id = symbol_to_security_id.get(symbol.upper())
    
    if security_id:
        instrument_info = security_id_to_info.get(security_id, {})
        
        instrument_list.append({
            "symbol": symbol,
            "instrument_key": f"DHAN_{security_id}",
            "name": instrument_info.get('SEM_CUSTOM_SYMBOL', symbol),
            "isin": instrument_info.get('SEM_ISIN', ''),
            "security_id": security_id
        })
        
        mapped_count += 1
    else:
        not_found.append(symbol)

print(f"✅ Mapped {mapped_count}/{len(fo_symbols)} symbols")

if not_found:
    print(f"⚠️  Not found ({len(not_found)}): {', '.join(not_found[:10])}")
    if len(not_found) > 10:
        print(f"   ... and {len(not_found) - 10} more")

# Step 5: Sort by symbol
instrument_list.sort(key=lambda x: x['symbol'])

# Step 6: Write to app/instruments.py
print("\n💾 Step 5: Writing to app/instruments.py...")

try:
    with open('app/instruments.py', 'w') as f:
        f.write("# This file is auto-generated. Do not edit manually.\n")
        f.write("# Generated from Dhan instruments API\n")
        f.write("# Format: DHAN_{security_id}\n\n")
        
        f.write("STOCKS_LIST = ")
        json.dump(instrument_list, f, indent=4)
        f.write("\n\n")
        
        # Add helper dictionaries
        f.write("# Helper dictionaries for quick lookups\n")
        f.write("STOCKS_MAP = {stock['instrument_key']: stock for stock in STOCKS_LIST}\n")
        f.write("STOCKS_BY_SYMBOL_MAP = {stock['symbol']: stock for stock in STOCKS_LIST}\n")
    
    print(f"✅ Successfully created app/instruments.py")
    print(f"📊 Total instruments: {len(instrument_list)}")
    
except Exception as e:
    print(f"❌ Error writing file: {e}")
    exit(1)

# Step 7: Show sample mappings
print("\n📋 Sample Mappings (first 10):")
for stock in instrument_list[:10]:
    print(f"   {stock['symbol']:15} → {stock['instrument_key']:20} ({stock['name'][:40]})")

print("\n" + "="*70)
print("✅ INSTRUMENTS FILE UPDATED SUCCESSFULLY")
print("="*70)
print("\nNext steps:")
print("1. Restart the application to load new instruments")
print("2. Add stocks from the updated list")
print("3. All new stocks will use Dhan instrument keys (DHAN_xxxxx)")
print()

