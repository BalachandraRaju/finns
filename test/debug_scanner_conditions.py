#!/usr/bin/env python3
"""
Debug script to check why scanners are not triggering
"""
import sys
sys.path.insert(0, 'pkscreener-integration')
sys.path.insert(0, '.')

from datetime import datetime, timedelta
from app.db import get_db
from app.models import Candle
import pandas as pd
from scanner_strategies import ScannerStrategies
from sqlalchemy import and_

def test_scanner_on_stock(instrument_key, symbol):
    """Test scanner on a specific stock"""
    print(f"\n{'='*80}")
    print(f"Testing scanners on {symbol} ({instrument_key})")
    print(f"{'='*80}")
    
    db = next(get_db())
    strategies = ScannerStrategies()
    
    # Get recent data (use Oct 17 since that's the latest data we have)
    end_time = datetime(2025, 10, 17, 15, 30, 0)
    start_time = end_time - timedelta(days=1)
    
    candles = db.query(Candle).filter(
        and_(
            Candle.instrument_key == instrument_key,
            Candle.interval == '1minute',
            Candle.timestamp >= start_time,
            Candle.timestamp <= end_time
        )
    ).order_by(Candle.timestamp.desc()).all()
    
    if not candles:
        print(f"❌ No candles found for {symbol}")
        return
    
    print(f"✅ Found {len(candles)} candles")
    
    # Convert to DataFrame
    data = []
    for candle in candles:
        data.append({
            'timestamp': candle.timestamp,
            'open': candle.open,
            'high': candle.high,
            'low': candle.low,
            'close': candle.close,
            'volume': candle.volume
        })
    
    df = pd.DataFrame(data)
    
    if len(df) < 50:
        print(f"⚠️  Only {len(df)} candles, need at least 50")
        return
    
    print(f"\nLatest candle: {df.iloc[0]['timestamp']}")
    print(f"Close: ₹{df.iloc[0]['close']:.2f}")
    print(f"Volume: {df.iloc[0]['volume']:,.0f}")
    
    # Test each scanner
    scanners = [
        (1, 'scanner_1_volume_momentum_breakout_atr'),
        (12, 'scanner_12_volume_momentum_breakout_atr_rsi'),
        (14, 'scanner_14_vcp_chart_patterns_ma_support'),
        (20, 'scanner_20_comprehensive'),
        (21, 'scanner_21_bullcross_ma_fair_value')
    ]
    
    print(f"\n{'Scanner Results':^80}")
    print(f"{'-'*80}")
    
    for scanner_id, method_name in scanners:
        try:
            method = getattr(strategies, method_name)
            passed, metrics = method(df)
            
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"{status} Scanner #{scanner_id:2d}: {method_name}")
            
            if passed:
                print(f"   Metrics: {metrics}")
            elif 'error' in metrics:
                print(f"   Error: {metrics['error']}")
            else:
                # Show why it failed
                print(f"   Failed conditions:")
                for key, value in metrics.items():
                    if isinstance(value, bool) and not value:
                        print(f"     - {key}: {value}")
                    elif key in ['volume_ratio', 'atr', 'rsi', 'momentum_score']:
                        print(f"     - {key}: {value}")
        except Exception as e:
            print(f"❌ Scanner #{scanner_id:2d}: Exception - {str(e)[:60]}")
    
    db.close()

def main():
    """Test scanners on multiple stocks"""
    print("\n" + "="*80)
    print("SCANNER CONDITION DEBUG")
    print("="*80)
    
    # Get some stocks with data
    db = next(get_db())
    
    stocks_with_data = db.query(Candle.instrument_key).filter(
        Candle.interval == '1minute',
        Candle.timestamp >= datetime(2025, 10, 17, 9, 15, 0)
    ).group_by(Candle.instrument_key).limit(5).all()
    
    print(f"\nTesting on {len(stocks_with_data)} stocks with recent data...")
    
    for (instrument_key,) in stocks_with_data:
        # Get symbol from watchlist
        from app.crud import get_watchlist_details
        watchlist = get_watchlist_details()
        symbol = next((s.symbol for s in watchlist if s.instrument_key == instrument_key), instrument_key)
        
        test_scanner_on_stock(instrument_key, symbol)
    
    db.close()

if __name__ == '__main__':
    main()

