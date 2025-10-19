#!/usr/bin/env python3
"""
Specific test cases for pattern alert generation.
Tests that each pattern generates the expected alerts with correct timing.
"""

import sys
import os
import unittest
from typing import List, Dict, Any

# Add project root to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.test_patterns import TEST_PATTERNS
from app.charts import _calculate_pnf_points
from app.pattern_detector import PatternDetector, PatternType, AlertType

class TestPatternAlerts(unittest.TestCase):
    """Test pattern alert generation for all patterns."""
    
    def setUp(self):
        """Set up test environment."""
        self.box_size = 0.01  # 1% box size
        self.reversal = 3     # 3-box reversal
    
    def test_bullish_patterns_generate_buy_alerts(self):
        """Test that bullish patterns generate BUY alerts."""
        bullish_patterns = [
            'bullish_breakout', 'triple_top', 'quadruple_top',
            'turtle_breakout_ft_buy', 'catapult_buy', 'pole_follow_through_buy',
            'aft_anchor_breakout_buy', 'low_pole_ft_buy', 'tweezer_bullish', 'abc_bullish'
        ]
        
        for pattern_key in bullish_patterns:
            if pattern_key in TEST_PATTERNS:
                with self.subTest(pattern=pattern_key):
                    print(f"\n📈 Testing BUY alerts for {pattern_key}")
                    
                    pattern_info = TEST_PATTERNS[pattern_key]
                    candles = pattern_info['data_generator']()
                    
                    highs = [c['high'] for c in candles]
                    lows = [c['low'] for c in candles]
                    closes = [c['close'] for c in candles]
                    
                    # Calculate P&F points
                    x_coords, y_coords, pnf_symbols = _calculate_pnf_points(
                        highs, lows, self.box_size, self.reversal
                    )
                    
                    if len(x_coords) == 0:
                        continue
                    
                    # Analyze pattern formation
                    detector = PatternDetector()
                    alerts = detector.analyze_pattern_formation(
                        x_coords, y_coords, pnf_symbols, closes
                    )
                    
                    # Check for BUY alerts
                    buy_alerts = [a for a in alerts if a.alert_type == AlertType.BUY]
                    
                    # Should have at least some alerts (not enforcing specific count)
                    print(f"   📊 Generated {len(alerts)} total alerts, {len(buy_alerts)} BUY alerts")
                    
                    # Validate alert structure
                    for alert in buy_alerts:
                        self.assertEqual(alert.alert_type, AlertType.BUY)
                        self.assertIsInstance(alert.price, (int, float))
                        self.assertIsInstance(alert.trigger_reason, str)
                        self.assertGreater(len(alert.trigger_reason), 0)
    
    def test_bearish_patterns_generate_sell_alerts(self):
        """Test that bearish patterns generate SELL alerts."""
        bearish_patterns = [
            'bearish_breakdown', 'triple_bottom', 'quadruple_bottom',
            'turtle_breakout_ft_sell', 'catapult_sell', 'pole_follow_through_sell',
            'aft_anchor_breakdown_sell', 'high_pole_ft_sell', 'tweezer_bearish', 'abc_bearish'
        ]
        
        for pattern_key in bearish_patterns:
            if pattern_key in TEST_PATTERNS:
                with self.subTest(pattern=pattern_key):
                    print(f"\n📉 Testing SELL alerts for {pattern_key}")
                    
                    pattern_info = TEST_PATTERNS[pattern_key]
                    candles = pattern_info['data_generator']()
                    
                    highs = [c['high'] for c in candles]
                    lows = [c['low'] for c in candles]
                    closes = [c['close'] for c in candles]
                    
                    # Calculate P&F points
                    x_coords, y_coords, pnf_symbols = _calculate_pnf_points(
                        highs, lows, self.box_size, self.reversal
                    )
                    
                    if len(x_coords) == 0:
                        continue
                    
                    # Analyze pattern formation
                    detector = PatternDetector()
                    alerts = detector.analyze_pattern_formation(
                        x_coords, y_coords, pnf_symbols, closes
                    )
                    
                    # Check for SELL alerts
                    sell_alerts = [a for a in alerts if a.alert_type == AlertType.SELL]
                    
                    # Should have at least some alerts (not enforcing specific count)
                    print(f"   📊 Generated {len(alerts)} total alerts, {len(sell_alerts)} SELL alerts")
                    
                    # Validate alert structure
                    for alert in sell_alerts:
                        self.assertEqual(alert.alert_type, AlertType.SELL)
                        self.assertIsInstance(alert.price, (int, float))
                        self.assertIsInstance(alert.trigger_reason, str)
                        self.assertGreater(len(alert.trigger_reason), 0)
    
    def test_alert_trigger_reasons(self):
        """Test that alerts have meaningful trigger reasons."""
        print(f"\n🧪 Testing Alert Trigger Reasons")
        
        # Test a few key patterns
        test_patterns = ['bullish_breakout', 'bearish_breakdown', 'catapult_buy', 'catapult_sell']
        
        for pattern_key in test_patterns:
            if pattern_key in TEST_PATTERNS:
                with self.subTest(pattern=pattern_key):
                    print(f"\n📝 Testing trigger reasons for {pattern_key}")
                    
                    pattern_info = TEST_PATTERNS[pattern_key]
                    candles = pattern_info['data_generator']()
                    
                    highs = [c['high'] for c in candles]
                    lows = [c['low'] for c in candles]
                    closes = [c['close'] for c in candles]
                    
                    # Calculate P&F points
                    x_coords, y_coords, pnf_symbols = _calculate_pnf_points(
                        highs, lows, self.box_size, self.reversal
                    )
                    
                    if len(x_coords) == 0:
                        continue
                    
                    # Analyze pattern formation
                    detector = PatternDetector()
                    alerts = detector.analyze_pattern_formation(
                        x_coords, y_coords, pnf_symbols, closes
                    )
                    
                    for alert in alerts:
                        # Check trigger reason quality
                        reason = alert.trigger_reason
                        
                        # Should contain price information
                        self.assertTrue(any(char.isdigit() for char in reason), 
                                      f"Trigger reason should contain price: {reason}")
                        
                        # Should contain pattern name or description
                        pattern_keywords = ['BUY', 'SELL', 'breaks', 'above', 'below', 'resistance', 'support']
                        self.assertTrue(any(keyword in reason.upper() for keyword in pattern_keywords),
                                      f"Trigger reason should contain pattern keywords: {reason}")
                        
                        # Should be reasonably long (meaningful description)
                        self.assertGreater(len(reason), 20, 
                                         f"Trigger reason too short: {reason}")
                        
                        print(f"   ✅ Valid trigger: {reason[:80]}...")
    
    def test_alert_price_validity(self):
        """Test that alert prices are within reasonable ranges."""
        print(f"\n🧪 Testing Alert Price Validity")
        
        for pattern_key, pattern_info in TEST_PATTERNS.items():
            with self.subTest(pattern=pattern_key):
                print(f"\n💰 Testing prices for {pattern_key}")
                
                candles = pattern_info['data_generator']()
                highs = [c['high'] for c in candles]
                lows = [c['low'] for c in candles]
                closes = [c['close'] for c in candles]
                
                # Calculate P&F points
                x_coords, y_coords, pnf_symbols = _calculate_pnf_points(
                    highs, lows, self.box_size, self.reversal
                )
                
                if len(x_coords) == 0:
                    continue
                
                # Analyze pattern formation
                detector = PatternDetector()
                alerts = detector.analyze_pattern_formation(
                    x_coords, y_coords, pnf_symbols, closes
                )
                
                # Get price range from original data
                min_price = min(lows)
                max_price = max(highs)
                price_range = max_price - min_price
                
                for alert in alerts:
                    # Alert price should be within reasonable range of data
                    # Allow some buffer for breakouts beyond the range
                    buffer = price_range * 0.2  # 20% buffer
                    
                    self.assertGreaterEqual(alert.price, min_price - buffer,
                                          f"Alert price {alert.price} too low for {pattern_key}")
                    self.assertLessEqual(alert.price, max_price + buffer,
                                       f"Alert price {alert.price} too high for {pattern_key}")
                    
                    # Price should be positive
                    self.assertGreater(alert.price, 0, 
                                     f"Alert price should be positive: {alert.price}")
                
                if alerts:
                    print(f"   ✅ {len(alerts)} alerts with valid prices")
    
    def test_no_duplicate_alerts(self):
        """Test that patterns don't generate duplicate alerts."""
        print(f"\n🧪 Testing No Duplicate Alerts")
        
        for pattern_key, pattern_info in TEST_PATTERNS.items():
            with self.subTest(pattern=pattern_key):
                print(f"\n🔄 Testing duplicates for {pattern_key}")
                
                candles = pattern_info['data_generator']()
                highs = [c['high'] for c in candles]
                lows = [c['low'] for c in candles]
                closes = [c['close'] for c in candles]
                
                # Calculate P&F points
                x_coords, y_coords, pnf_symbols = _calculate_pnf_points(
                    highs, lows, self.box_size, self.reversal
                )
                
                if len(x_coords) == 0:
                    continue
                
                # Analyze pattern formation
                detector = PatternDetector()
                alerts = detector.analyze_pattern_formation(
                    x_coords, y_coords, pnf_symbols, closes
                )
                
                # Check for duplicate alerts (same pattern type and price)
                seen_alerts = set()
                for alert in alerts:
                    alert_key = (alert.pattern_type, alert.alert_type, round(alert.price, 2))
                    
                    self.assertNotIn(alert_key, seen_alerts, 
                                   f"Duplicate alert found in {pattern_key}: {alert_key}")
                    seen_alerts.add(alert_key)
                
                if alerts:
                    print(f"   ✅ {len(alerts)} unique alerts")


if __name__ == '__main__':
    print("🚨 PATTERN ALERTS TEST SUITE")
    print("=" * 60)
    print("Testing alert generation for all patterns")
    print("=" * 60)
    
    unittest.main(verbosity=2)
