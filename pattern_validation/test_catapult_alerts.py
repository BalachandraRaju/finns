#!/usr/bin/env python3
"""
Test catapult pattern alert detection.
"""

import sys
import os
sys.path.append('/Users/balachandra.raju/projects/finns')

from app.test_patterns import generate_catapult_buy_pattern, generate_catapult_sell_pattern
from app.charts import _calculate_pnf_points
from app.pattern_detector import PatternDetector, PatternType

def test_catapult_alerts():
    """Test catapult pattern alert detection."""
    print("🧪 Testing Catapult Pattern Alert Detection")
    print("=" * 60)
    
    # Test Catapult Buy Pattern
    print("\n📈 Testing Catapult Buy Pattern")
    print("-" * 40)
    
    candles = generate_catapult_buy_pattern()
    highs = [c['high'] for c in candles]
    lows = [c['low'] for c in candles]
    closes = [c['close'] for c in candles]
    
    print(f"📊 Generated {len(candles)} candles")
    print(f"📊 Price range: {min(lows):.2f} - {max(highs):.2f}")
    
    x_coords, y_coords, pnf_symbols = _calculate_pnf_points(highs, lows, 0.01, 3)
    print(f"📊 Generated {len(x_coords)} P&F points")
    
    detector = PatternDetector()
    alerts = detector.analyze_pattern_formation(x_coords, y_coords, pnf_symbols, closes)
    
    print(f"🚨 Total alerts: {len(alerts)}")
    for alert in alerts:
        print(f"   {alert.alert_type.value}: {alert.pattern_type.value}")
    
    catapult_buy_alerts = [a for a in alerts if a.pattern_type == PatternType.CATAPULT_BUY]
    print(f"🎯 Catapult Buy alerts: {len(catapult_buy_alerts)}")
    
    # Test Catapult Sell Pattern
    print("\n📉 Testing Catapult Sell Pattern")
    print("-" * 40)
    
    candles = generate_catapult_sell_pattern()
    highs = [c['high'] for c in candles]
    lows = [c['low'] for c in candles]
    closes = [c['close'] for c in candles]
    
    print(f"📊 Generated {len(candles)} candles")
    print(f"📊 Price range: {min(lows):.2f} - {max(highs):.2f}")
    
    x_coords, y_coords, pnf_symbols = _calculate_pnf_points(highs, lows, 0.01, 3)
    print(f"📊 Generated {len(x_coords)} P&F points")
    
    detector = PatternDetector()
    alerts = detector.analyze_pattern_formation(x_coords, y_coords, pnf_symbols, closes)
    
    print(f"🚨 Total alerts: {len(alerts)}")
    for alert in alerts:
        print(f"   {alert.alert_type.value}: {alert.pattern_type.value}")
    
    catapult_sell_alerts = [a for a in alerts if a.pattern_type == PatternType.CATAPULT_SELL]
    print(f"🎯 Catapult Sell alerts: {len(catapult_sell_alerts)}")
    
    # Summary
    print(f"\n📋 SUMMARY:")
    print(f"   Catapult Buy alerts: {len(catapult_buy_alerts)}")
    print(f"   Catapult Sell alerts: {len(catapult_sell_alerts)}")
    
    if len(catapult_buy_alerts) > 0 and len(catapult_sell_alerts) > 0:
        print("✅ Both catapult patterns generating correct alerts!")
    else:
        print("❌ Catapult patterns need adjustment for proper alert detection")

if __name__ == "__main__":
    test_catapult_alerts()
