#!/usr/bin/env python3
"""
Test the new intraday scanners
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

def test_intraday_scanners():
    """Test intraday scanners on real data"""
    print("\n" + "="*80)
    print("TESTING INTRADAY SCANNERS (22-25)")
    print("="*80)
    
    db = next(get_db())
    strategies = ScannerStrategies()
    
    # Get stocks with data
    test_date = datetime(2025, 10, 17, 9, 15, 0)
    end_date = datetime(2025, 10, 17, 15, 30, 0)
    
    stocks = db.query(Candle.instrument_key).filter(
        Candle.interval == '1minute',
        Candle.timestamp >= test_date,
        Candle.timestamp <= end_date
    ).group_by(Candle.instrument_key).limit(50).all()
    
    print(f"\nTesting on {len(stocks)} stocks for Oct 17, 2025...")
    
    # Scanners to test
    scanners = [
        (22, 'scanner_22_intraday_volume_momentum'),
        (23, 'scanner_23_intraday_breakout'),
        (24, 'scanner_24_intraday_momentum_rsi'),
        (25, 'scanner_25_intraday_comprehensive')
    ]
    
    results = {sid: [] for sid, _ in scanners}
    
    # Test each stock
    for (instrument_key,) in stocks:
        # Get candles
        candles = db.query(Candle).filter(
            and_(
                Candle.instrument_key == instrument_key,
                Candle.interval == '1minute',
                Candle.timestamp >= test_date,
                Candle.timestamp <= end_date
            )
        ).order_by(Candle.timestamp.desc()).all()
        
        if len(candles) < 50:
            continue
        
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
        
        # Test each scanner on multiple time points
        for i in range(0, min(len(df) - 50, 100), 10):  # Test every 10 candles
            slice_df = df.iloc[i:i+100] if i+100 < len(df) else df.iloc[i:]
            
            if len(slice_df) < 30:
                continue
            
            for scanner_id, method_name in scanners:
                try:
                    method = getattr(strategies, method_name)
                    passed, metrics = method(slice_df)
                    
                    if passed:
                        results[scanner_id].append({
                            'stock': instrument_key,
                            'time': slice_df['timestamp'].iloc[0],
                            'price': slice_df['close'].iloc[0],
                            'metrics': metrics
                        })
                except Exception as e:
                    pass
    
    # Print results
    print("\n" + "="*80)
    print("RESULTS")
    print("="*80)
    
    for scanner_id, method_name in scanners:
        alerts = results[scanner_id]
        print(f"\n📊 Scanner #{scanner_id}: {len(alerts)} alerts")
        
        if alerts:
            print(f"\nFirst 5 alerts:")
            print(f"{'Stock':<15} {'Time':<20} {'Price':<10} {'Vol Ratio':<12} {'Details':<30}")
            print("-"*95)
            
            for alert in alerts[:5]:
                vol_ratio = alert['metrics'].get('volume_ratio', 0)
                price_change = alert['metrics'].get('price_change_pct', alert['metrics'].get('price_move_pct', 0))
                rsi = alert['metrics'].get('rsi', 0)
                
                details = f"Vol:{vol_ratio:.1f}x"
                if price_change:
                    details += f" Chg:{price_change:+.2f}%"
                if rsi:
                    details += f" RSI:{rsi:.0f}"
                
                print(f"{alert['stock']:<15} {str(alert['time']):<20} Rs{alert['price']:<9.2f} {vol_ratio:>10.2f}x  {details:<30}")
    
    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    total_alerts = sum(len(results[sid]) for sid, _ in scanners)
    print(f"Total alerts across all intraday scanners: {total_alerts}")
    
    for scanner_id, method_name in scanners:
        count = len(results[scanner_id])
        print(f"  Scanner #{scanner_id}: {count:4d} alerts")
    
    db.close()
    
    return total_alerts > 0

if __name__ == '__main__':
    success = test_intraday_scanners()
    sys.exit(0 if success else 1)

