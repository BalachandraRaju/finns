#!/usr/bin/env python3
"""
Test script to verify the quadruple top buy and quadruple bottom sell patterns.
"""

import sys
import os

# Add the app directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.test_patterns import generate_quadruple_top_pattern, generate_quadruple_bottom_pattern
from app.charts import _calculate_pnf_points
from app.pattern_detector import PatternDetector, AlertType

def test_quadruple_top_pattern():
    """Test the quadruple top buy with follow through pattern."""
    print("🔝🔝🔝🔝 Testing Quadruple Top Buy with Follow Through")
    print("=" * 80)
    
    # Generate test data
    candles = generate_quadruple_top_pattern()
    
    print(f"📊 Generated {len(candles)} candles for quadruple top pattern")
    
    # Extract price data
    highs = [float(c['high']) for c in candles]
    lows = [float(c['low']) for c in candles]
    
    print(f"📈 Price range: {min(lows):.0f} to {max(highs):.0f}")
    
    # Show the quadruple top structure
    print(f"\n📊 Quadruple Top Structure:")
    print(f"   Days 1-5: First top formation (building to {max(highs[:5]):.0f})")
    print(f"   Days 6-8: Pullback from first top (down to {min(lows[5:8]):.0f})")
    print(f"   Days 9-12: Second top formation (back to {max(highs[8:12]):.0f})")
    print(f"   Days 13-15: Pullback from second top (down to {min(lows[12:15]):.0f})")
    print(f"   Days 16-19: Third top formation (back to {max(highs[15:19]):.0f})")
    print(f"   Days 20-22: Pullback from third top (down to {min(lows[19:22]):.0f})")
    print(f"   Days 23-26: Fourth top formation (back to {max(highs[22:26]):.0f})")
    print(f"   Days 27-32: ULTIMATE BREAKOUT with follow-through (to {max(highs[26:]):.0f})")
    
    # Verify the four tops are at similar levels
    first_top = max(highs[:5])
    second_top = max(highs[8:12])
    third_top = max(highs[15:19])
    fourth_top = max(highs[22:26])
    
    print(f"\n🎯 Quadruple Top Analysis:")
    print(f"   First Top:  {first_top:.0f}")
    print(f"   Second Top: {second_top:.0f}")
    print(f"   Third Top:  {third_top:.0f}")
    print(f"   Fourth Top: {fourth_top:.0f}")
    print(f"   Resistance Level: ~{(first_top + second_top + third_top + fourth_top) / 4:.0f}")
    
    # Check if tops are similar (within 1% of each other)
    avg_top = (first_top + second_top + third_top + fourth_top) / 4
    tolerance = avg_top * 0.01  # 1% tolerance
    
    if all(abs(top - avg_top) <= tolerance for top in [first_top, second_top, third_top, fourth_top]):
        print(f"   ✅ Quadruple top formation confirmed (all tops within 1% of each other)")
    else:
        print(f"   ⚠️ Tops may not be similar enough for classic quadruple top")
    
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
        print(f"   ✅ Quadruple top buy pattern detected successfully!")
        return True
    else:
        print(f"   ❌ No buy alerts generated")
        return False

def test_quadruple_bottom_pattern():
    """Test the quadruple bottom sell with follow through pattern."""
    print("\n🔻🔻🔻🔻 Testing Quadruple Bottom Sell with Follow Through")
    print("=" * 80)
    
    # Generate test data
    candles = generate_quadruple_bottom_pattern()
    
    print(f"📊 Generated {len(candles)} candles for quadruple bottom pattern")
    
    # Extract price data
    highs = [float(c['high']) for c in candles]
    lows = [float(c['low']) for c in candles]
    
    print(f"📈 Price range: {min(lows):.0f} to {max(highs):.0f}")
    
    # Show the quadruple bottom structure
    print(f"\n📊 Quadruple Bottom Structure:")
    print(f"   Days 1-5: First bottom formation (down to {min(lows[:5]):.0f})")
    print(f"   Days 6-8: Rally from first bottom (up to {max(highs[5:8]):.0f})")
    print(f"   Days 9-12: Second bottom formation (back to {min(lows[8:12]):.0f})")
    print(f"   Days 13-15: Rally from second bottom (up to {max(highs[12:15]):.0f})")
    print(f"   Days 16-19: Third bottom formation (back to {min(lows[15:19]):.0f})")
    print(f"   Days 20-22: Rally from third bottom (up to {max(highs[19:22]):.0f})")
    print(f"   Days 23-26: Fourth bottom formation (back to {min(lows[22:26]):.0f})")
    print(f"   Days 27-32: ULTIMATE BREAKDOWN with follow-through (to {min(lows[26:]):.0f})")
    
    # Verify the four bottoms are at similar levels
    first_bottom = min(lows[:5])
    second_bottom = min(lows[8:12])
    third_bottom = min(lows[15:19])
    fourth_bottom = min(lows[22:26])
    
    print(f"\n🎯 Quadruple Bottom Analysis:")
    print(f"   First Bottom:  {first_bottom:.0f}")
    print(f"   Second Bottom: {second_bottom:.0f}")
    print(f"   Third Bottom:  {third_bottom:.0f}")
    print(f"   Fourth Bottom: {fourth_bottom:.0f}")
    print(f"   Support Level: ~{(first_bottom + second_bottom + third_bottom + fourth_bottom) / 4:.0f}")
    
    # Test pattern detection
    detector = PatternDetector()
    box_pct = 0.01
    x_coords, y_coords, pnf_symbols = _calculate_pnf_points(highs, lows, box_pct, 3)
    alerts = detector.analyze_pattern_formation(x_coords, y_coords, pnf_symbols)
    
    sell_alerts = [a for a in alerts if a.alert_type == AlertType.SELL]
    
    if sell_alerts:
        print(f"   ✅ Quadruple bottom sell pattern detected successfully!")
        return True
    else:
        print(f"   ❌ No sell alerts generated")
        return False

def test_ultimate_pattern_suite():
    """Test the complete ultimate pattern suite."""
    print(f"\n🏆 ULTIMATE PATTERN SUITE TEST")
    print("=" * 60)
    
    from app.test_patterns import (
        generate_bullish_breakout_pattern,
        generate_bearish_breakdown_pattern,
        generate_triple_top_pattern,
        generate_triple_bottom_pattern
    )
    
    patterns = {
        'Double Top Buy': generate_bullish_breakout_pattern(),
        'Double Bottom Sell': generate_bearish_breakdown_pattern(),
        'Triple Top Buy': generate_triple_top_pattern(),
        'Triple Bottom Sell': generate_triple_bottom_pattern(),
        'Quadruple Top Buy': generate_quadruple_top_pattern(),
        'Quadruple Bottom Sell': generate_quadruple_bottom_pattern()
    }
    
    print(f"📊 Ultimate Pattern Suite:")
    for name, candles in patterns.items():
        highs = [float(c['high']) for c in candles]
        lows = [float(c['low']) for c in candles]
        print(f"   {name}: {len(candles)} candles, Range: {min(lows):.0f}-{max(highs):.0f}")
    
    print(f"\n🎯 Pattern Hierarchy (by ultimate conviction):")
    print(f"   1. 🔝🔝🔝🔝 Quadruple Top Buy: ULTIMATE conviction breakout (4 attempts)")
    print(f"   2. 🔻🔻🔻🔻 Quadruple Bottom Sell: ULTIMATE conviction breakdown (4 attempts)")
    print(f"   3. 🔝🔝🔝 Triple Top Buy: High conviction breakout (3 attempts)")
    print(f"   4. 🔻🔻🔻 Triple Bottom Sell: High conviction breakdown (3 attempts)")
    print(f"   5. 🔝🔝 Double Top Buy: Medium conviction breakout (2 attempts)")
    print(f"   6. 🔻🔻 Double Bottom Sell: Medium conviction breakdown (2 attempts)")
    
    print(f"\n💎 Ultimate Trading Applications:")
    print(f"   • Quadruple patterns = Maximum possible conviction")
    print(f"   • Four failed attempts = Ultimate pressure buildup")
    print(f"   • When quadruple patterns finally break = EXPLOSIVE moves")
    print(f"   • Perfect for highest-conviction, highest-risk/reward trades")
    print(f"   • Rare but extremely powerful when they occur")

def main():
    """Run all quadruple pattern tests."""
    print("🔝🔻 QUADRUPLE PATTERN TESTING - ULTIMATE CONVICTION SIGNALS")
    print("Testing: Four attempts + ultimate breakthrough with maximum follow-through")
    print("=" * 100)
    
    test1 = test_quadruple_top_pattern()
    test2 = test_quadruple_bottom_pattern()
    test_ultimate_pattern_suite()
    
    print("\n" + "=" * 100)
    print("📋 QUADRUPLE PATTERN TEST RESULTS:")
    print(f"  Quadruple Top Buy Pattern: {'✅ PASS' if test1 else '❌ FAIL'}")
    print(f"  Quadruple Bottom Sell Pattern: {'✅ PASS' if test2 else '❌ FAIL'}")
    
    if test1 and test2:
        print("\n🎉 ULTIMATE PATTERN SUITE COMPLETE!")
        print("🏆 SIX POWERFUL PATTERNS NOW AVAILABLE:")
        print("   🔝🔝 Double Top Buy with Follow Through")
        print("   🔻🔻 Double Bottom Sell with Follow Through")
        print("   🔝🔝🔝 Triple Top Buy with Follow Through")
        print("   🔻🔻🔻 Triple Bottom Sell with Follow Through")
        print("   🔝🔝🔝🔝 Quadruple Top Buy with Follow Through")
        print("   🔻🔻🔻🔻 Quadruple Bottom Sell with Follow Through")
        print("\n💎 From medium to ultimate conviction - complete trading arsenal!")
        print("🚀 Ready for any market condition with maximum signal strength!")
    else:
        print("\n❌ SOME QUADRUPLE PATTERNS FAILED!")
        print("🔧 Pattern detection needs adjustment")

if __name__ == "__main__":
    main()
