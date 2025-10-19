#!/usr/bin/env python3
"""
Test script to verify the double top buy and double bottom sell patterns.
"""

import sys
import os

# Add the app directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.test_patterns import generate_bullish_breakout_pattern, generate_bearish_breakdown_pattern
from app.charts import _calculate_pnf_points
from app.pattern_detector import PatternDetector, AlertType

def test_double_top_buy_pattern():
    """Test the double top buy with follow through pattern."""
    print("🔝 Testing Double Top Buy with Follow Through")
    print("=" * 60)
    
    # Generate test data
    candles = generate_bullish_breakout_pattern()
    
    print(f"📊 Generated {len(candles)} candles for double top pattern")
    
    # Extract price data
    highs = [float(c['high']) for c in candles]
    lows = [float(c['low']) for c in candles]
    
    print(f"📈 Price range: {min(lows):.0f} to {max(highs):.0f}")
    
    # Show the double top structure
    print(f"\n📊 Double Top Structure:")
    print(f"   Days 1-5: First top formation (building to {max(highs[:5]):.0f})")
    print(f"   Days 6-8: Valley between tops (down to {min(lows[5:8]):.0f})")
    print(f"   Days 9-12: Second top formation (back to {max(highs[8:12]):.0f})")
    print(f"   Days 13-16: Breakout with follow-through (to {max(highs[12:]):.0f})")
    
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
        for i in range(min(10, len(x_coords))):
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
        print(f"   ✅ Double top buy pattern detected successfully!")
        return True
    else:
        print(f"   ❌ No buy alerts generated")
        return False

def test_double_bottom_sell_pattern():
    """Test the double bottom sell with follow through pattern."""
    print("\n🔻 Testing Double Bottom Sell with Follow Through")
    print("=" * 60)
    
    # Generate test data
    candles = generate_bearish_breakdown_pattern()
    
    print(f"📊 Generated {len(candles)} candles for double bottom pattern")
    
    # Extract price data
    highs = [float(c['high']) for c in candles]
    lows = [float(c['low']) for c in candles]
    
    print(f"📈 Price range: {min(lows):.0f} to {max(highs):.0f}")
    
    # Show the double bottom structure
    print(f"\n📊 Double Bottom Structure:")
    print(f"   Days 1-5: First bottom formation (down to {min(lows[:5]):.0f})")
    print(f"   Days 6-8: Rally between bottoms (up to {max(highs[5:8]):.0f})")
    print(f"   Days 9-12: Second bottom formation (back to {min(lows[8:12]):.0f})")
    print(f"   Days 13-16: Breakdown with follow-through (to {min(lows[12:]):.0f})")
    
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
        for i in range(min(10, len(x_coords))):
            print(f"      {i+1}. Column {x_coords[i]}: {pnf_symbols[i]} at {y_coords[i]:.0f}")
    
    # Test pattern detection
    detector = PatternDetector()
    alerts = detector.analyze_pattern_formation(x_coords, y_coords, pnf_symbols)
    
    print(f"\n🚨 Alert Analysis:")
    print(f"   Alerts generated: {len(alerts)}")
    
    sell_alerts = [a for a in alerts if a.alert_type == AlertType.SELL]
    
    for alert in sell_alerts:
        print(f"   🔴 SELL Alert: Column {alert.column}, Price {alert.price:.0f}")
        print(f"      Reason: {alert.trigger_reason}")
    
    if sell_alerts:
        print(f"   ✅ Double bottom sell pattern detected successfully!")
        return True
    else:
        print(f"   ❌ No sell alerts generated")
        return False

def test_pattern_comparison():
    """Compare the two patterns side by side."""
    print("\n🔄 Pattern Comparison")
    print("=" * 40)
    
    # Generate both patterns
    double_top_candles = generate_bullish_breakout_pattern()
    double_bottom_candles = generate_bearish_breakdown_pattern()
    
    print(f"📊 Pattern Comparison:")
    print(f"   Double Top Candles: {len(double_top_candles)}")
    print(f"   Double Bottom Candles: {len(double_bottom_candles)}")
    
    # Compare price ranges
    top_highs = [float(c['high']) for c in double_top_candles]
    top_lows = [float(c['low']) for c in double_top_candles]
    
    bottom_highs = [float(c['high']) for c in double_bottom_candles]
    bottom_lows = [float(c['low']) for c in double_bottom_candles]
    
    print(f"\n📈 Price Ranges:")
    print(f"   Double Top: {min(top_lows):.0f} to {max(top_highs):.0f} (Range: {max(top_highs) - min(top_lows):.0f})")
    print(f"   Double Bottom: {min(bottom_lows):.0f} to {max(bottom_highs):.0f} (Range: {max(bottom_highs) - min(bottom_lows):.0f})")
    
    print(f"\n🎯 Pattern Characteristics:")
    print(f"   Double Top: Bullish breakout above resistance")
    print(f"   Double Bottom: Bearish breakdown below support")
    print(f"   Both: Include strong follow-through momentum")

def main():
    """Run all double pattern tests."""
    print("🔝🔻 DOUBLE TOP & DOUBLE BOTTOM PATTERN TESTING")
    print("Testing: Double Top Buy + Double Bottom Sell with Follow Through")
    print("=" * 80)
    
    test1 = test_double_top_buy_pattern()
    test2 = test_double_bottom_sell_pattern()
    test_pattern_comparison()
    
    print("\n" + "=" * 80)
    print("📋 DOUBLE PATTERN TEST RESULTS:")
    print(f"  Double Top Buy Pattern: {'✅ PASS' if test1 else '❌ FAIL'}")
    print(f"  Double Bottom Sell Pattern: {'✅ PASS' if test2 else '❌ FAIL'}")
    
    if test1 and test2:
        print("\n🎉 ALL DOUBLE PATTERNS WORKING!")
        print("🔝 Double Top Buy: Breakout above resistance with follow-through")
        print("🔻 Double Bottom Sell: Breakdown below support with follow-through")
        print("💰 Perfect for identifying key reversal and continuation signals!")
    else:
        print("\n❌ SOME PATTERNS FAILED!")
        print("🔧 Pattern detection needs adjustment")

if __name__ == "__main__":
    main()
