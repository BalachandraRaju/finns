#!/usr/bin/env python3
"""
Analyze volume patterns to understand why scanners aren't triggering
"""
import sys
sys.path.insert(0, 'pkscreener-integration')
sys.path.insert(0, '.')

from datetime import datetime, timedelta
from app.db import get_db
from app.models import Candle
import pandas as pd
from sqlalchemy import and_
from technical_indicators import TechnicalIndicators

def analyze_volume_patterns():
    """Analyze volume patterns across stocks"""
    print("\n" + "="*80)
    print("VOLUME PATTERN ANALYSIS - INTRADAY")
    print("="*80)
    
    db = next(get_db())
    ti = TechnicalIndicators()
    
    # Get stocks with good data
    test_date = datetime(2025, 10, 17, 9, 15, 0)
    end_date = datetime(2025, 10, 17, 15, 30, 0)
    
    # Get all stocks
    stocks = db.query(Candle.instrument_key).filter(
        Candle.interval == '1minute',
        Candle.timestamp >= test_date,
        Candle.timestamp <= end_date
    ).group_by(Candle.instrument_key).limit(50).all()
    
    print(f"\nAnalyzing {len(stocks)} stocks for Oct 17, 2025...")
    print(f"\nLooking for high volume spikes (volume ratio > 1.5x)")
    print(f"\n{'Stock':<15} {'Time':<20} {'Vol Ratio':<12} {'Volume':<15} {'Price':<10} {'Momentum':<10}")
    print("-"*95)
    
    high_volume_count = 0
    total_candles_checked = 0
    
    for (instrument_key,) in stocks:
        # Get all candles for this stock
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
        
        # Check each candle for volume spike
        for i in range(len(df) - 20):
            total_candles_checked += 1
            
            # Get slice from current position
            slice_df = df.iloc[i:i+50] if i+50 < len(df) else df.iloc[i:]
            
            if len(slice_df) < 20:
                continue
            
            # Calculate volume ratio
            volume_ratio = ti.calculate_volume_ratio(slice_df, period=20)
            
            # Check for high volume
            if volume_ratio >= 1.5:  # Lower threshold for analysis
                high_volume_count += 1
                
                # Check momentum
                close_now = slice_df['close'].iloc[0]
                close_3_ago = slice_df['close'].iloc[min(2, len(slice_df)-1)]
                momentum = "UP" if close_now > close_3_ago else "DOWN"
                
                # Only show first 20 high volume instances
                if high_volume_count <= 20:
                    print(f"{instrument_key:<15} {str(slice_df['timestamp'].iloc[0]):<20} {volume_ratio:>10.2f}x  {slice_df['volume'].iloc[0]:>12,}  Rs{close_now:>8.2f}  {momentum:<10}")
    
    print("\n" + "="*80)
    print(f"SUMMARY")
    print("="*80)
    print(f"Total candles checked: {total_candles_checked:,}")
    print(f"High volume instances (>1.5x): {high_volume_count:,}")
    print(f"Percentage: {high_volume_count/total_candles_checked*100:.2f}%")
    
    # Now check with different thresholds
    print(f"\n{'Threshold':<15} {'Expected Alerts':<20}")
    print("-"*35)
    for threshold in [1.5, 2.0, 2.5, 3.0]:
        expected = int(high_volume_count * (1.5/threshold) if threshold >= 1.5 else high_volume_count)
        print(f"{threshold}x{'':<12} ~{expected:,} alerts")
    
    db.close()

if __name__ == '__main__':
    analyze_volume_patterns()

