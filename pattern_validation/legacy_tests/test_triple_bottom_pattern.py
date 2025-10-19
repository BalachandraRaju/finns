#!/usr/bin/env python3
"""
Test script to verify the triple bottom sell with follow through pattern.
"""

import sys
import os

# Add the app directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.test_patterns import generate_triple_bottom_pattern
from app.charts import _calculate_pnf_points
from app.pattern_detector import PatternDetector, AlertType

def test_triple_bottom_pattern():
    """Test the triple bottom sell with follow through pattern."""
    print("🔻🔻🔻 Testing Triple Bottom Sell with Follow Through")
    print("=" * 70)
    
    # Generate test data
    candles = generate_triple_bottom_pattern()
    
    print(f"📊 Generated {len(candles)} candles for triple bottom pattern")
    
    # Extract price data
    highs = [float(c['high']) for c in candles]
    lows = [float(c['low']) for c in candles]
    
    print(f"📈 Price range: {min(lows):.0f} to {max(highs):.0f}")
    
    # Show the triple bottom structure
    print(f"\n📊 Triple Bottom Structure:")
    print(f"   Days 1-5: First bottom formation (down to {min(lows[:5]):.0f})")
    print(f"   Days 6-8: Rally from first bottom (up to {max(highs[5:8]):.0f})")
    print(f"   Days 9-12: Second bottom formation (back to {min(lows[8:12]):.0f})")
    print(f"   Days 13-15: Rally from second bottom (up to {max(highs[12:15]):.0f})")
    print(f"   Days 16-19: Third bottom formation (back to {min(lows[15:19]):.0f})")
    print(f"   Days 20-24: Breakdown with follow-through (to {min(lows[19:]):.0f})")
    
    # Verify the three bottoms are at similar levels
    first_bottom = min(lows[:5])
    second_bottom = min(lows[8:12])
    third_bottom = min(lows[15:19])
    
    print(f"\n🎯 Triple Bottom Analysis:")
    print(f"   First Bottom:  {first_bottom:.0f}")
    print(f"   Second Bottom: {second_bottom:.0f}")
    print(f"   Third Bottom:  {third_bottom:.0f}")
    print(f"   Support Level: ~{(first_bottom + second_bottom + third_bottom) / 3:.0f}")
    
    # Check if bottoms are similar (within 1% of each other)
    avg_bottom = (first_bottom + second_bottom + third_bottom) / 3
    tolerance = avg_bottom * 0.01  # 1% tolerance
    
    if (abs(first_bottom - avg_bottom) <= tolerance and 
        abs(second_bottom - avg_bottom) <= tolerance and 
        abs(third_bottom - avg_bottom) <= tolerance):
        print(f"   ✅ Triple bottom formation confirmed (bottoms within 1% of each other)")
    else:
        print(f"   ⚠️ Bottoms may not be similar enough for classic triple bottom")
    
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
    
    sell_alerts = [a for a in alerts if a.alert_type == AlertType.SELL]
    
    for alert in sell_alerts:
        print(f"   🔴 SELL Alert: Column {alert.column}, Price {alert.price:.0f}")
        print(f"      Reason: {alert.trigger_reason}")
    
    if sell_alerts:
        print(f"   ✅ Triple bottom sell pattern detected successfully!")
        
        # Check if alert fired on the breakdown (should be around 135 or below)
        breakdown_alerts = [a for a in sell_alerts if a.price < 140]
        if breakdown_alerts:
            print(f"   ✅ Alert fired on breakdown below triple bottom support!")
        else:
            print(f"   ⚠️ Alert may not have fired on the actual breakdown")
        
        return True
    else:
        print(f"   ❌ No sell alerts generated")
        return False

def test_triple_bottom_vs_double_bottom():
    """Compare triple bottom with double bottom pattern."""
    print(f"\n🔄 Triple Bottom vs Double Bottom Comparison")
    print("=" * 50)
    
    from app.test_patterns import generate_bearish_breakdown_pattern
    
    # Generate both patterns
    triple_bottom_candles = generate_triple_bottom_pattern()
    double_bottom_candles = generate_bearish_breakdown_pattern()
    
    print(f"📊 Pattern Comparison:")
    print(f"   Triple Bottom Candles: {len(triple_bottom_candles)}")
    print(f"   Double Bottom Candles: {len(double_bottom_candles)}")
    
    # Compare price ranges
    triple_highs = [float(c['high']) for c in triple_bottom_candles]
    triple_lows = [float(c['low']) for c in triple_bottom_candles]
    
    double_highs = [float(c['high']) for c in double_bottom_candles]
    double_lows = [float(c['low']) for c in double_bottom_candles]
    
    print(f"\n📈 Price Ranges:")
    print(f"   Triple Bottom: {min(triple_lows):.0f} to {max(triple_highs):.0f} (Range: {max(triple_highs) - min(triple_lows):.0f})")
    print(f"   Double Bottom: {min(double_lows):.0f} to {max(double_highs):.0f} (Range: {max(double_highs) - min(double_lows):.0f})")
    
    print(f"\n🎯 Pattern Characteristics:")
    print(f"   Triple Bottom: Three attempts at support before breakdown")
    print(f"   Double Bottom: Two attempts at support before breakdown")
    print(f"   Both: Include strong follow-through momentum after breakdown")
    print(f"   Triple Bottom: Shows more conviction when finally breaking down")

def test_complete_pattern_suite():
    """Test all four patterns together."""
    print(f"\n🔄 Complete Pattern Suite Test")
    print("=" * 50)
    
    from app.test_patterns import (
        generate_bullish_breakout_pattern,
        generate_bearish_breakdown_pattern,
        generate_triple_top_pattern
    )
    
    patterns = {
        'Double Top Buy': generate_bullish_breakout_pattern(),
        'Double Bottom Sell': generate_bearish_breakdown_pattern(),
        'Triple Top Buy': generate_triple_top_pattern(),
        'Triple Bottom Sell': generate_triple_bottom_pattern()
    }
    
    print(f"📊 Complete Pattern Suite:")
    for name, candles in patterns.items():
        highs = [float(c['high']) for c in candles]
        lows = [float(c['low']) for c in candles]
        print(f"   {name}: {len(candles)} candles, Range: {min(lows):.0f}-{max(highs):.0f}")
    
    print(f"\n🎯 Pattern Hierarchy (by conviction):")
    print(f"   1. 🔝🔝🔝 Triple Top Buy: Highest conviction breakout (3 attempts)")
    print(f"   2. 🔻🔻🔻 Triple Bottom Sell: Highest conviction breakdown (3 attempts)")
    print(f"   3. 🔝🔝 Double Top Buy: Medium conviction breakout (2 attempts)")
    print(f"   4. 🔻🔻 Double Bottom Sell: Medium conviction breakdown (2 attempts)")
    
    print(f"\n💰 Trading Applications:")
    print(f"   • More attempts = Higher conviction when pattern finally breaks")
    print(f"   • Triple patterns show maximum resistance/support testing")
    print(f"   • Follow-through momentum confirms pattern validity")
    print(f"   • Perfect for generating high-probability trading signals")

def main():
    """Run all triple bottom pattern tests."""
    print("🔻🔻🔻 TRIPLE BOTTOM SELL WITH FOLLOW THROUGH PATTERN TESTING")
    print("Testing: Three attempts at support + successful breakdown with follow-through")
    print("=" * 90)
    
    test1 = test_triple_bottom_pattern()
    test_triple_bottom_vs_double_bottom()
    test_complete_pattern_suite()
    
    print("\n" + "=" * 90)
    print("📋 TRIPLE BOTTOM PATTERN TEST RESULTS:")
    print(f"  Triple Bottom Sell Pattern: {'✅ PASS' if test1 else '❌ FAIL'}")
    
    if test1:
        print("\n🎉 TRIPLE BOTTOM PATTERN WORKING!")
        print("🔻 Triple Bottom Sell: Three failed attempts at support")
        print("💥 Followed by: Strong breakdown with follow-through momentum")
        print("🎯 Perfect for: Identifying high-conviction breakdown signals!")
        print("📉 Trading Logic: More attempts = stronger breakdown when it finally happens")
        
        print("\n🏆 COMPLETE PATTERN SUITE NOW AVAILABLE:")
        print("   🔝🔝 Double Top Buy with Follow Through")
        print("   🔻🔻 Double Bottom Sell with Follow Through")
        print("   🔝🔝🔝 Triple Top Buy with Follow Through")
        print("   🔻🔻🔻 Triple Bottom Sell with Follow Through")
        print("\n💎 Four powerful patterns for comprehensive market analysis!")
    else:
        print("\n❌ TRIPLE BOTTOM PATTERN FAILED!")
        print("🔧 Pattern detection needs adjustment")

if __name__ == "__main__":
    main()
