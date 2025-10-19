#!/usr/bin/env python3
"""
Script to remove legacy Upstox stocks from watchlist and replace with Dhan keys
"""

import sys
import os
from logzero import logger

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'data-fetch'))

from app import crud
from dhan_instruments import dhan_instruments

def cleanup_upstox_stocks():
    """Remove Upstox stocks and replace with Dhan keys where available"""
    
    print("=" * 80)
    print("🧹 CLEANING UP LEGACY UPSTOX STOCKS FROM WATCHLIST")
    print("=" * 80)
    
    # Get current watchlist
    watchlist = crud.get_watchlist_details()
    
    # Filter Upstox stocks
    upstox_stocks = [s for s in watchlist if s.instrument_key.startswith('NSE_EQ|')]
    dhan_stocks = [s for s in watchlist if s.instrument_key.startswith('DHAN_')]
    
    print(f"\n📊 Current Watchlist Status:")
    print(f"   Total stocks: {len(watchlist)}")
    print(f"   Upstox stocks: {len(upstox_stocks)}")
    print(f"   Dhan stocks: {len(dhan_stocks)}")
    
    if not upstox_stocks:
        print("\n✅ No Upstox stocks found in watchlist. Nothing to clean up.")
        return
    
    print(f"\n🔍 Found {len(upstox_stocks)} Upstox stocks to remove:")
    for stock in upstox_stocks:
        print(f"   ⚠️  {stock.symbol:15} | {stock.instrument_key}")
    
    # Check which stocks already have Dhan equivalents
    upstox_symbols = {s.symbol for s in upstox_stocks}
    dhan_symbols = {s.symbol for s in dhan_stocks}
    
    already_have_dhan = upstox_symbols & dhan_symbols
    need_dhan = upstox_symbols - dhan_symbols
    
    print(f"\n📋 Analysis:")
    print(f"   Already have Dhan keys: {len(already_have_dhan)}")
    print(f"   Need Dhan keys: {len(need_dhan)}")
    
    if already_have_dhan:
        print(f"\n✅ Stocks that already have Dhan keys (will just remove Upstox):")
        for symbol in sorted(already_have_dhan):
            print(f"   {symbol}")
    
    if need_dhan:
        print(f"\n⚠️  Stocks that need Dhan keys added:")
        for symbol in sorted(need_dhan):
            print(f"   {symbol}")
    
    # Ask for confirmation
    print(f"\n{'='*80}")
    response = input("Do you want to proceed with cleanup? (yes/no): ").strip().lower()
    
    if response not in ['yes', 'y']:
        print("❌ Cleanup cancelled.")
        return
    
    # Remove Upstox stocks
    print(f"\n🗑️  Removing Upstox stocks from watchlist...")
    removed_count = 0
    
    for stock in upstox_stocks:
        try:
            crud.remove_stock_from_watchlist(stock.symbol)
            print(f"   ✅ Removed {stock.symbol}")
            removed_count += 1
        except Exception as e:
            print(f"   ❌ Failed to remove {stock.symbol}: {e}")
    
    # Add Dhan keys for stocks that need them
    if need_dhan:
        print(f"\n➕ Adding Dhan keys for stocks that need them...")
        added_count = 0
        skipped_count = 0
        
        for symbol in sorted(need_dhan):
            try:
                # Get Dhan security ID
                security_id = dhan_instruments.get_security_id(symbol)
                
                if not security_id:
                    print(f"   ⚠️  Skipped {symbol} (no Dhan security ID found)")
                    skipped_count += 1
                    continue
                
                # Add to watchlist
                instrument_key = f"DHAN_{security_id}"
                crud.add_stock_to_watchlist(
                    symbol=symbol,
                    instrument_key=instrument_key,
                    company_name=symbol,
                    tags="F&O,Dhan"
                )
                print(f"   ✅ Added {symbol} with {instrument_key}")
                added_count += 1
                
            except Exception as e:
                print(f"   ❌ Failed to add {symbol}: {e}")
    
    # Verify final state
    print(f"\n{'='*80}")
    print("📊 CLEANUP SUMMARY")
    print(f"{'='*80}")
    print(f"   Upstox stocks removed: {removed_count}")
    if need_dhan:
        print(f"   Dhan stocks added: {added_count}")
        print(f"   Stocks skipped (no Dhan ID): {skipped_count}")
    
    # Get updated watchlist
    updated_watchlist = crud.get_watchlist_details()
    updated_upstox = [s for s in updated_watchlist if s.instrument_key.startswith('NSE_EQ|')]
    updated_dhan = [s for s in updated_watchlist if s.instrument_key.startswith('DHAN_')]
    
    print(f"\n📊 Updated Watchlist Status:")
    print(f"   Total stocks: {len(updated_watchlist)}")
    print(f"   Upstox stocks: {len(updated_upstox)}")
    print(f"   Dhan stocks: {len(updated_dhan)}")
    
    if updated_upstox:
        print(f"\n⚠️  Warning: Still have {len(updated_upstox)} Upstox stocks:")
        for stock in updated_upstox:
            print(f"   {stock.symbol} | {stock.instrument_key}")
    else:
        print(f"\n✅ SUCCESS! All Upstox stocks removed from watchlist")
        print(f"✅ Watchlist now has {len(updated_dhan)} Dhan stocks only")
    
    print(f"\n{'='*80}")

if __name__ == "__main__":
    try:
        cleanup_upstox_stocks()
    except KeyboardInterrupt:
        print("\n\n❌ Cleanup cancelled by user")
    except Exception as e:
        logger.error(f"❌ Error during cleanup: {e}", exc_info=True)

