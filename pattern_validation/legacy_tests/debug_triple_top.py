#!/usr/bin/env python3
"""
Debug the triple top pattern generation and P&F calculation.
"""

import sys
import os
sys.path.append('/Users/balachandra.raju/projects/finns')

from app.test_patterns import generate_triple_top_pattern
from app.charts import _calculate_pnf_points

def debug_pattern_data():
    """Debug the pattern data and P&F calculation."""
    
    print("🔍 Debugging Triple Top Pattern Data")
    print("=" * 60)
    
    # Generate the test pattern data
    candles = generate_triple_top_pattern()
    
    # Extract price data
    highs = [c['high'] for c in candles]
    lows = [c['low'] for c in candles]
    
    print(f"📊 Raw Pattern Data:")
    print(f"   Total candles: {len(candles)}")
    
    # Show the key days with tops at 110
    print(f"\n📈 Days with highs at 110:")
    for i, (high, low) in enumerate(zip(highs, lows)):
        if high >= 110:
            print(f"   Day {i+1}: High={high}, Low={low}")
    
    # Show the pattern structure more clearly
    print(f"\n🎯 Expected Triple Top Structure:")
    print(f"   Days 1-5: Building to first top (110)")
    print(f"   Days 6-8: Pullback from first top")
    print(f"   Days 9-12: Building to second top (110)")
    print(f"   Days 13-15: Pullback from second top")
    print(f"   Days 16-19: Building to third top (110)")
    print(f"   Days 20+: Breakout above 110")
    
    # Test different box sizes
    print(f"\n📊 Testing Different Box Sizes:")
    
    for box_pct in [0.005, 0.01, 0.015, 0.02]:
        print(f"\n   Box Size: {box_pct*100:.1f}%")
        x_coords, y_coords, pnf_symbols = _calculate_pnf_points(highs, lows, box_pct, 3)
        
        if x_coords:
            # Find X column highs
            x_columns = {}
            for i, (col, price, symbol) in enumerate(zip(x_coords, y_coords, pnf_symbols)):
                if symbol == 'X':
                    if col not in x_columns or price > x_columns[col]:
                        x_columns[col] = price
            
            print(f"      Columns: {max(x_coords)}")
            print(f"      X column highs: {len(x_columns)}")
            
            # Count similar highs near 110
            similar_highs = []
            for price in x_columns.values():
                if abs(price - 110) <= 110 * 0.015:  # 1.5% tolerance
                    similar_highs.append(price)
            
            print(f"      Similar highs near 110: {len(similar_highs)}")
            print(f"      Values: {[f'{h:.2f}' for h in similar_highs]}")
            
            if len(similar_highs) >= 3:
                print(f"      ✅ Triple top formation possible")
            else:
                print(f"      ❌ Not enough similar highs")

def create_better_triple_top():
    """Create a more explicit triple top pattern."""
    
    print(f"\n🔧 Creating Better Triple Top Pattern")
    print("=" * 60)
    
    # Create a clearer triple top pattern
    # Three distinct peaks at exactly 110, with clear valleys between
    highs = [
        # Build up to first top
        100, 102, 105, 108, 110,  # Days 1-5: First top at 110
        # Pullback
        108, 105, 102,  # Days 6-8: Valley
        # Build up to second top  
        105, 108, 110,  # Days 9-11: Second top at 110
        # Pullback
        108, 105, 102,  # Days 12-14: Valley
        # Build up to third top
        105, 108, 110,  # Days 15-17: Third top at 110
        # Breakout
        112, 115, 118, 120  # Days 18-21: Breakout above resistance
    ]
    
    lows = [
        # Build up to first top
        98, 100, 103, 106, 108,  # Days 1-5
        # Pullback
        105, 102, 100,  # Days 6-8
        # Build up to second top
        102, 105, 108,  # Days 9-11
        # Pullback
        105, 102, 100,  # Days 12-14
        # Build up to third top
        102, 105, 108,  # Days 15-17
        # Breakout
        110, 113, 116, 118  # Days 18-21
    ]
    
    print(f"📊 Explicit Triple Top Data:")
    print(f"   Total days: {len(highs)}")
    print(f"   Tops at 110: Days 5, 11, 17")
    print(f"   Valleys at ~100: Days 8, 14")
    print(f"   Breakout starts: Day 18")
    
    # Test this pattern
    for box_pct in [0.005, 0.01, 0.015]:
        print(f"\n   Box Size: {box_pct*100:.1f}%")
        x_coords, y_coords, pnf_symbols = _calculate_pnf_points(highs, lows, box_pct, 3)
        
        if x_coords:
            # Find X column highs
            x_columns = {}
            for i, (col, price, symbol) in enumerate(zip(x_coords, y_coords, pnf_symbols)):
                if symbol == 'X':
                    if col not in x_columns or price > x_columns[col]:
                        x_columns[col] = price
            
            print(f"      Columns: {max(x_coords)}")
            print(f"      X columns: {sorted(x_columns.keys())}")
            print(f"      X highs: {[f'{x_columns[col]:.1f}' for col in sorted(x_columns.keys())]}")
            
            # Count similar highs near 110
            similar_highs = []
            for price in x_columns.values():
                if abs(price - 110) <= 110 * 0.015:  # 1.5% tolerance
                    similar_highs.append(price)
            
            print(f"      Similar highs near 110: {len(similar_highs)}")
            
            if len(similar_highs) >= 3:
                print(f"      ✅ Triple top formation confirmed!")
                return highs, lows, box_pct
            else:
                print(f"      ❌ Only {len(similar_highs)} similar highs")
    
    return None, None, None

if __name__ == "__main__":
    # Debug the original pattern
    debug_pattern_data()
    
    # Try to create a better pattern
    better_highs, better_lows, best_box_size = create_better_triple_top()
    
    if better_highs:
        print(f"\n🎉 Found working pattern with box size {best_box_size*100:.1f}%")
        print(f"   This pattern should generate proper triple top alerts")
    else:
        print(f"\n⚠️ Need to adjust the pattern or P&F calculation logic")
