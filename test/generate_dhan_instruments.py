#!/usr/bin/env python3
"""
Generate app/instruments.py with Dhan instrument keys.
Reads F&O symbols from nse_fo_stock_symbols.txt and maps them to Dhan security IDs.
"""

import os
import sys
import json
import requests
import csv
from typing import Dict, Optional, List

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)


class SimpleDhanInstruments:
    """Simple Dhan instruments mapper."""

    INSTRUMENT_URL = "https://images.dhan.co/api-data/api-scrip-master.csv"
    CACHE_FILE = "data-fetch/dhan_instruments_cache.json"

    def __init__(self):
        self.symbol_to_security_id = {}
        self.instruments = {}

    def download_and_load(self):
        """Download and load Dhan instruments."""
        print("📥 Downloading Dhan instrument list...")

        try:
            response = requests.get(self.INSTRUMENT_URL, timeout=30)

            if response.status_code == 200:
                print("✅ Successfully downloaded instrument list")

                # Parse CSV
                lines = response.text.strip().split('\n')
                reader = csv.DictReader(lines)

                instruments = list(reader)
                print(f"📊 Parsed {len(instruments)} instruments")

                # Save to cache
                cache_data = {'instruments': instruments}
                with open(self.CACHE_FILE, 'w') as f:
                    json.dump(cache_data, f, indent=2)

                # Build mappings
                self._build_mappings(instruments)

                return True
            else:
                print(f"❌ Failed to download: {response.status_code}")
                # Try loading from cache
                return self._load_from_cache()

        except Exception as e:
            print(f"❌ Error downloading: {e}")
            # Try loading from cache
            return self._load_from_cache()

    def _load_from_cache(self):
        """Load from cache file."""
        try:
            if os.path.exists(self.CACHE_FILE):
                with open(self.CACHE_FILE, 'r') as f:
                    cache_data = json.load(f)
                instruments = cache_data.get('instruments', [])
                print(f"📂 Loaded {len(instruments)} instruments from cache")
                self._build_mappings(instruments)
                return True
        except Exception as e:
            print(f"❌ Error loading cache: {e}")
        return False

    def _build_mappings(self, instruments: List[Dict]):
        """Build symbol to security ID mappings."""
        for instrument in instruments:
            exchange = instrument.get('SEM_EXM_EXCH_ID', '')
            security_id = instrument.get('SEM_SMST_SECURITY_ID', '')
            symbol = instrument.get('SEM_TRADING_SYMBOL', '')
            instrument_type = instrument.get('SEM_INSTRUMENT_NAME', '')

            # We're interested in NSE Equity instruments
            if exchange == 'NSE' and instrument_type == 'EQUITY':
                # Clean symbol (remove -EQ suffix if present)
                clean_symbol = symbol.replace('-EQ', '').strip()

                self.symbol_to_security_id[clean_symbol] = security_id
                self.instruments[security_id] = {
                    'symbol': clean_symbol,
                    'security_id': security_id,
                    'full_data': instrument
                }

        print(f"✅ Built mappings for {len(self.symbol_to_security_id)} NSE Equity symbols")

    def get_security_id(self, symbol: str) -> Optional[str]:
        """Get Dhan security ID for a given symbol."""
        return self.symbol_to_security_id.get(symbol.upper())

    def get_instrument_info(self, security_id: str) -> Optional[Dict]:
        """Get full instrument information for a security ID."""
        return self.instruments.get(security_id)


def generate_dhan_instruments_file():
    """
    Generate app/instruments.py with Dhan instrument keys.
    """
    print("\n" + "="*70)
    print("  GENERATING DHAN INSTRUMENTS FILE")
    print("="*70 + "\n")
    
    # Step 1: Load F&O symbols from file
    fo_symbols_file = "nse_fo_stock_symbols.txt"
    
    if not os.path.exists(fo_symbols_file):
        print(f"❌ Error: {fo_symbols_file} not found")
        return False
    
    print(f"📋 Step 1: Loading F&O symbols from {fo_symbols_file}...")
    
    with open(fo_symbols_file, 'r') as f:
        content = f.read()
        # Parse comma-separated symbols
        fo_symbols = [s.strip().strip('"') for s in content.split(',')]
        # Filter out empty strings and test symbols
        fo_symbols = [s for s in fo_symbols if s and not s.startswith('0')]
    
    print(f"   ✅ Loaded {len(fo_symbols)} F&O symbols")
    print()
    
    # Step 2: Download/load Dhan instruments
    print("📥 Step 2: Loading Dhan instruments...")

    dhan_mapper = SimpleDhanInstruments()
    if not dhan_mapper.download_and_load():
        print("   ❌ Failed to load Dhan instruments")
        return False

    print(f"   ✅ Loaded {len(dhan_mapper.symbol_to_security_id)} Dhan instruments")
    print()

    # Step 3: Map F&O symbols to Dhan security IDs
    print("🔍 Step 3: Mapping F&O symbols to Dhan security IDs...")

    instrument_list = []
    mapped_count = 0
    not_found = []

    for symbol in fo_symbols:
        security_id = dhan_mapper.get_security_id(symbol)

        if security_id:
            # Get full instrument info
            instrument_info = dhan_mapper.get_instrument_info(security_id)
            
            if instrument_info:
                full_data = instrument_info.get('full_data', {})
                
                instrument_list.append({
                    "symbol": symbol,
                    "instrument_key": f"DHAN_{security_id}",
                    "name": full_data.get('SEM_CUSTOM_SYMBOL', symbol),
                    "isin": full_data.get('SEM_ISIN', ''),
                    "security_id": security_id
                })
                
                mapped_count += 1
        else:
            not_found.append(symbol)
    
    print(f"   ✅ Mapped {mapped_count}/{len(fo_symbols)} symbols")
    
    if not_found:
        print(f"   ⚠️  Not found ({len(not_found)}): {', '.join(not_found[:10])}")
        if len(not_found) > 10:
            print(f"      ... and {len(not_found) - 10} more")
    
    print()
    
    # Step 4: Sort by symbol
    instrument_list.sort(key=lambda x: x['symbol'])
    
    # Step 5: Write to app/instruments.py
    print("💾 Step 4: Writing to app/instruments.py...")
    
    output_file = "app/instruments.py"
    
    try:
        with open(output_file, 'w') as f:
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
        
        print(f"   ✅ Successfully created {output_file}")
        print(f"   📊 Total instruments: {len(instrument_list)}")
        print()
        
    except IOError as e:
        print(f"   ❌ Error writing to file: {e}")
        return False
    
    # Step 6: Show sample mappings
    print("📋 Sample Mappings (first 10):")
    for stock in instrument_list[:10]:
        print(f"   {stock['symbol']:15} → {stock['instrument_key']:20} ({stock['name'][:40]})")
    
    print()
    print("="*70)
    print("✅ DHAN INSTRUMENTS FILE GENERATED SUCCESSFULLY")
    print("="*70)
    print()
    print("Next steps:")
    print("1. Restart the application to load new instruments")
    print("2. Add stocks from the updated list")
    print("3. All new stocks will use Dhan instrument keys (DHAN_xxxxx)")
    print()
    
    return True


if __name__ == "__main__":
    success = generate_dhan_instruments_file()
    sys.exit(0 if success else 1)

