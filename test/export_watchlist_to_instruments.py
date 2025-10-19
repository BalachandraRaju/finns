#!/usr/bin/env python3
"""
Export current watchlist (which has Dhan keys) to app/instruments.py
This ensures the Add Stocks dropdown shows Dhan keys instead of Upstox keys.
"""

import sys
import json

# Add project root to path
sys.path.insert(0, '/Users/balachandra.raju/projects/finns')

from app import crud

print("\n" + "="*70)
print("  EXPORTING WATCHLIST TO INSTRUMENTS FILE")
print("="*70 + "\n")

# Step 1: Get current watchlist
print("📋 Step 1: Getting current watchlist...")

try:
    watchlist = crud.get_watchlist_details()
    print(f"✅ Found {len(watchlist)} stocks in watchlist")
except Exception as e:
    print(f"❌ Error getting watchlist: {e}")
    sys.exit(1)

# Step 2: Filter for Dhan stocks only
print("\n🔍 Step 2: Filtering for Dhan stocks...")

dhan_stocks = [s for s in watchlist if s.instrument_key.startswith('DHAN_')]
upstox_stocks = [s for s in watchlist if s.instrument_key.startswith('NSE_')]

print(f"   Dhan stocks: {len(dhan_stocks)}")
print(f"   Upstox stocks: {len(upstox_stocks)}")

if not dhan_stocks:
    print("❌ No Dhan stocks found in watchlist!")
    sys.exit(1)

# Step 3: Convert to instruments format
print("\n📝 Step 3: Converting to instruments format...")

instrument_list = []

for stock in dhan_stocks:
    # Extract security ID from instrument key (DHAN_xxxxx)
    security_id = stock.instrument_key.replace('DHAN_', '')
    
    instrument_list.append({
        "symbol": stock.symbol,
        "instrument_key": stock.instrument_key,
        "name": stock.company_name or stock.symbol,
        "isin": "",  # We don't have ISIN in watchlist
        "security_id": security_id
    })

# Sort by symbol
instrument_list.sort(key=lambda x: x['symbol'])

print(f"✅ Converted {len(instrument_list)} stocks")

# Step 4: Write to app/instruments.py
print("\n💾 Step 4: Writing to app/instruments.py...")

try:
    with open('/Users/balachandra.raju/projects/finns/app/instruments.py', 'w') as f:
        f.write("# This file is auto-generated. Do not edit manually.\n")
        f.write("# Generated from current watchlist (Dhan keys)\n")
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
    sys.exit(1)

# Step 5: Show sample mappings
print("\n📋 Sample Mappings (first 10):")
for stock in instrument_list[:10]:
    print(f"   {stock['symbol']:15} → {stock['instrument_key']:20} ({stock['name'][:40]})")

print("\n" + "="*70)
print("✅ INSTRUMENTS FILE UPDATED SUCCESSFULLY")
print("="*70)
print("\nNext steps:")
print("1. Restart the application to load new instruments")
print("2. Add stocks dropdown will now show Dhan keys")
print("3. All new stocks will use Dhan instrument keys (DHAN_xxxxx)")
print()

