#!/usr/bin/env python3
"""
Test script to verify the triple top buy with follow through pattern.
"""

import sys
import os

# Add the app directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.test_patterns import generate_triple_top_pattern
from app.charts import _calculate_pnf_points
from app.pattern_detector import PatternDetector, AlertType

def test_triple_top_pattern():
    """Test the triple top buy with follow through pattern."""
    print("🔝🔝🔝 Testing Triple Top Buy with Follow Through")
    print("=" * 70)
    
    # Generate test data
    candles = generate_triple_top_pattern()
    
    print(f"📊 Generated {len(candles)} candles for triple top pattern")
    
    # Extract price data
    highs = [float(c['high']) for c in candles]
    lows = [float(c['low']) for c in candles]
    
    print(f"📈 Price range: {min(lows):.0f} to {max(highs):.0f}")
    
    # Show the triple top structure
    print(f"\n📊 Triple Top Structure:")
    print(f"   Days 1-5: First top formation (building to {max(highs[:5]):.0f})")
    print(f"   Days 6-8: Pullback from first top (down to {min(lows[5:8]):.0f})")
    print(f"   Days 9-12: Second top formation (back to {max(highs[8:12]):.0f})")
    print(f"   Days 13-15: Pullback from second top (down to {min(lows[12:15]):.0f})")
    print(f"   Days 16-19: Third top formation (back to {max(highs[15:19]):.0f})")
    print(f"   Days 20-24: Breakout with follow-through (to {max(highs[19:]):.0f})")
    
    # Verify the three tops are at similar levels
    first_top = max(highs[:5])
    second_top = max(highs[8:12])
    third_top = max(highs[15:19])
    
    print(f"\n🎯 Triple Top Analysis:")
    print(f"   First Top:  {first_top:.0f}")
    print(f"   Second Top: {second_top:.0f}")
    print(f"   Third Top:  {third_top:.0f}")
    print(f"   Resistance Level: ~{(first_top + second_top + third_top) / 3:.0f}")
    
    # Check if tops are similar (within 1% of each other)
    avg_top = (first_top + second_top + third_top) / 3
    tolerance = avg_top * 0.01  # 1% tolerance
    
    if (abs(first_top - avg_top) <= tolerance and 
        abs(second_top - avg_top) <= tolerance and 
        abs(third_top - avg_top) <= tolerance):
        print(f"   ✅ Triple top formation confirmed (tops within 1% of each other)")
    else:
        print(f"   ⚠️ Tops may not be similar enough for classic triple top")
    
    # Calculate P&F points
    box_pct = 0.01  # 1%
    x_coords, y_coords, pnf_symbols = _calculate_pnf_points(highs, lows, box_pct, 3)
    
    print(f"\n📊 P&F Analysis:")
    print(f"   Generated {len(x_coords)} P&F points")
    print(f"   Columns: {max(x_coords) if x_coords else 0}")
    
    if x_coords:
        x_count = sum(1 for s in pnf_symbols if s == 'X')
        o_count = sum(1 for s in pnf_symbols if s == 'O')
        print(f"   X's: {x_count}, O's: {o_count}")
        
        # Show key points
        print(f"\n📋 Key P&F Points:")
        for i in range(min(12, len(x_coords))):
            print(f"      {i+1}. Column {x_coords[i]}: {pnf_symbols[i]} at {y_coords[i]:.0f}")
    
    # Test pattern detection
    detector = PatternDetector()
    alerts = detector.analyze_pattern_formation(x_coords, y_coords, pnf_symbols)
    
    print(f"\n🚨 Alert Analysis:")
    print(f"   Alerts generated: {len(alerts)}")
    
    buy_alerts = [a for a in alerts if a.alert_type == AlertType.BUY]
    
    for alert in buy_alerts:
        print(f"   🟢 BUY Alert: Column {alert.column}, Price {alert.price:.0f}")
        print(f"      Reason: {alert.trigger_reason}")
    
    if buy_alerts:
        print(f"   ✅ Triple top buy pattern detected successfully!")
        
        # Check if alert fired on the breakout (should be around 115+)
        breakout_alerts = [a for a in buy_alerts if a.price > 114]
        if breakout_alerts:
            print(f"   ✅ Alert fired on breakout above triple top resistance!")
        else:
            print(f"   ⚠️ Alert may not have fired on the actual breakout")
        
        return True
    else:
        print(f"   ❌ No buy alerts generated")
        return False

def test_triple_top_vs_double_top():
    """Compare triple top with double top pattern."""
    print(f"\n🔄 Triple Top vs Double Top Comparison")
    print("=" * 50)
    
    from app.test_patterns import generate_bullish_breakout_pattern
    
    # Generate both patterns
    triple_top_candles = generate_triple_top_pattern()
    double_top_candles = generate_bullish_breakout_pattern()
    
    print(f"📊 Pattern Comparison:")
    print(f"   Triple Top Candles: {len(triple_top_candles)}")
    print(f"   Double Top Candles: {len(double_top_candles)}")
    
    # Compare price ranges
    triple_highs = [float(c['high']) for c in triple_top_candles]
    triple_lows = [float(c['low']) for c in triple_top_candles]
    
    double_highs = [float(c['high']) for c in double_top_candles]
    double_lows = [float(c['low']) for c in double_top_candles]
    
    print(f"\n📈 Price Ranges:")
    print(f"   Triple Top: {min(triple_lows):.0f} to {max(triple_highs):.0f} (Range: {max(triple_highs) - min(triple_lows):.0f})")
    print(f"   Double Top: {min(double_lows):.0f} to {max(double_highs):.0f} (Range: {max(double_highs) - min(double_lows):.0f})")
    
    print(f"\n🎯 Pattern Characteristics:")
    print(f"   Triple Top: Three attempts at resistance before breakout")
    print(f"   Double Top: Two attempts at resistance before breakout")
    print(f"   Both: Include strong follow-through momentum after breakout")
    print(f"   Triple Top: Shows more conviction when finally breaking out")

def test_chart_generation():
    """Test chart generation for triple top pattern."""
    print(f"\n📊 Testing Triple Top Chart Generation")
    print("=" * 50)
    
    try:
        from app.charts import generate_test_chart_html
        
        chart_html = generate_test_chart_html("triple_top", box_pct=0.01, reversal=3)
        
        if chart_html:
            print(f"   ✅ Chart HTML generated: {len(chart_html)} characters")
            
            # Check for triple top indicators in title
            if "Triple Top" in chart_html:
                print(f"   ✅ Chart shows triple top pattern in title")
            else:
                print(f"   ⚠️ Chart may not show triple top pattern")
            
            # Check for data
            if '"x":[]' in chart_html or '"y":[]' in chart_html:
                print(f"   ❌ Chart has empty data arrays")
            elif '"x":[' in chart_html and '"y":[' in chart_html:
                print(f"   ✅ Chart contains plot data")
                
                # Extract sample data to verify it includes the pattern
                import re
                x_match = re.search(r'"x":\[([^\]]+)\]', chart_html)
                if x_match:
                    x_data = x_match.group(1).split(',')
                    max_column = max([int(x.strip()) for x in x_data if x.strip().isdigit()])
                    print(f"   📊 Chart has {max_column} columns (good for triple top analysis)")
            else:
                print(f"   ⚠️ Chart data format unclear")
        else:
            print(f"   ❌ No chart generated")
            
    except Exception as e:
        print(f"   ❌ Chart generation error: {e}")

def main():
    """Run all triple top pattern tests."""
    print("🔝🔝🔝 TRIPLE TOP BUY WITH FOLLOW THROUGH PATTERN TESTING")
    print("Testing: Three attempts at resistance + successful breakout with follow-through")
    print("=" * 90)
    
    test1 = test_triple_top_pattern()
    test_triple_top_vs_double_top()
    test_chart_generation()
    
    print("\n" + "=" * 90)
    print("📋 TRIPLE TOP PATTERN TEST RESULTS:")
    print(f"  Triple Top Buy Pattern: {'✅ PASS' if test1 else '❌ FAIL'}")
    
    if test1:
        print("\n🎉 TRIPLE TOP PATTERN WORKING!")
        print("🔝 Triple Top Buy: Three failed attempts at resistance")
        print("💥 Followed by: Strong breakout with follow-through momentum")
        print("🎯 Perfect for: Identifying high-conviction breakout signals!")
        print("📈 Trading Logic: More attempts = stronger breakout when it finally happens")
    else:
        print("\n❌ TRIPLE TOP PATTERN FAILED!")
        print("🔧 Pattern detection needs adjustment")

if __name__ == "__main__":
    main()
