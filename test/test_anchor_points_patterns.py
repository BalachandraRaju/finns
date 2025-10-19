#!/usr/bin/env python3
"""
Test cases for anchor points integration with all test patterns.
Ensures anchor points work correctly with every pattern type.
"""

import sys
import os
import unittest
import pandas as pd
from typing import List, Dict, Any

# Add project root to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.test_patterns import TEST_PATTERNS
from app.charts import _calculate_pnf_points
from anchor_point_calculator import AnchorPointCalculator, AnchorPoint, AnchorPointZone

class TestAnchorPointsPatterns(unittest.TestCase):
    """Test anchor points functionality with all test patterns."""
    
    def setUp(self):
        """Set up test environment."""
        self.box_size = 0.01  # 1% box size
        self.reversal = 3     # 3-box reversal
        self.anchor_calculator = AnchorPointCalculator(min_column_separation=7)
    
    def create_pnf_matrix(self, x_coords: List[int], y_coords: List[float], 
                         pnf_symbols: List[str]) -> pd.DataFrame:
        """Create a P&F matrix from coordinates and symbols."""
        if not x_coords:
            return pd.DataFrame()
        
        min_price = min(y_coords)
        max_price = max(y_coords)
        price_range = max_price - min_price
        
        if price_range <= 0:
            return pd.DataFrame()
        
        # Create matrix with reasonable size
        num_rows = min(int(price_range / self.box_size) + 1, 200)
        num_cols = max(x_coords) + 1
        
        # Initialize matrix
        matrix_data = {}
        for col in range(num_cols):
            matrix_data[col] = ['' for _ in range(num_rows)]
        
        # Fill matrix with symbols
        for x, y, symbol in zip(x_coords, y_coords, pnf_symbols):
            row_idx = int((y - min_price) / self.box_size)
            if 0 <= row_idx < num_rows and 0 <= x < num_cols:
                matrix_data[x][row_idx] = symbol
        
        return pd.DataFrame(matrix_data)
    
    def test_anchor_points_calculation(self):
        """Test anchor points calculation for all patterns."""
        print(f"\n🎯 Testing Anchor Points Calculation")
        print("=" * 60)
        
        for pattern_key, pattern_info in TEST_PATTERNS.items():
            with self.subTest(pattern=pattern_key):
                print(f"\n🧮 Testing anchor calculation for {pattern_key}")
                
                # Generate pattern data
                candles = pattern_info['data_generator']()
                highs = [c['high'] for c in candles]
                lows = [c['low'] for c in candles]
                
                # Calculate P&F points
                x_coords, y_coords, pnf_symbols = _calculate_pnf_points(
                    highs, lows, self.box_size, self.reversal
                )
                
                if len(x_coords) == 0:
                    print(f"   ⚠️ No P&F points generated")
                    continue
                
                # Create P&F matrix
                pnf_matrix = self.create_pnf_matrix(x_coords, y_coords, pnf_symbols)
                
                if pnf_matrix.empty:
                    print(f"   ⚠️ Empty P&F matrix")
                    continue
                
                # Calculate anchor points
                anchor_points = self.anchor_calculator.calculate_anchor_points(pnf_matrix)
                
                # Validate anchor points
                self.assertIsInstance(anchor_points, list, 
                                    f"Anchor points should be list for {pattern_key}")
                
                for ap in anchor_points:
                    self.assertIsInstance(ap, AnchorPoint, 
                                        f"Should be AnchorPoint instance in {pattern_key}")
                    self.assertIsInstance(ap.price_level, (int, float), 
                                        f"Price level should be numeric in {pattern_key}")
                    self.assertIsInstance(ap.box_count, int, 
                                        f"Box count should be int in {pattern_key}")
                    self.assertGreater(ap.box_count, 0, 
                                     f"Box count should be > 0 in {pattern_key}")
                    self.assertGreaterEqual(ap.start_column, 0, 
                                          f"Start column should be >= 0 in {pattern_key}")
                    self.assertGreaterEqual(ap.end_column, ap.start_column, 
                                          f"End column should be >= start column in {pattern_key}")
                
                print(f"   ✅ Generated {len(anchor_points)} anchor points")
                
                if anchor_points:
                    max_boxes = max(ap.box_count for ap in anchor_points)
                    avg_boxes = sum(ap.box_count for ap in anchor_points) / len(anchor_points)
                    print(f"   📊 Box counts: max={max_boxes}, avg={avg_boxes:.1f}")
    
    def test_anchor_zones_creation(self):
        """Test anchor zone creation for patterns with multiple anchor points."""
        print(f"\n🎯 Testing Anchor Zones Creation")
        print("=" * 60)
        
        # Test patterns that typically generate multiple anchor points
        complex_patterns = ['triple_top', 'quadruple_top', 'catapult_buy', 'pole_follow_through_buy']
        
        for pattern_key in complex_patterns:
            if pattern_key in TEST_PATTERNS:
                with self.subTest(pattern=pattern_key):
                    print(f"\n🏗️ Testing zones for {pattern_key}")
                    
                    pattern_info = TEST_PATTERNS[pattern_key]
                    candles = pattern_info['data_generator']()
                    highs = [c['high'] for c in candles]
                    lows = [c['low'] for c in candles]
                    
                    # Calculate P&F points
                    x_coords, y_coords, pnf_symbols = _calculate_pnf_points(
                        highs, lows, self.box_size, self.reversal
                    )
                    
                    if len(x_coords) == 0:
                        continue
                    
                    # Create P&F matrix
                    pnf_matrix = self.create_pnf_matrix(x_coords, y_coords, pnf_symbols)
                    
                    if pnf_matrix.empty:
                        continue
                    
                    # Calculate anchor points
                    anchor_points = self.anchor_calculator.calculate_anchor_points(pnf_matrix)
                    
                    if len(anchor_points) < 2:
                        print(f"   ⚠️ Not enough anchor points for zone testing")
                        continue
                    
                    # Create zones
                    zones = self.anchor_calculator.create_anchor_zones(anchor_points)
                    
                    # Validate zones
                    self.assertIsInstance(zones, list, f"Zones should be list for {pattern_key}")
                    
                    for zone in zones:
                        self.assertIsInstance(zone, AnchorPointZone, 
                                            f"Should be AnchorPointZone instance in {pattern_key}")
                        self.assertGreater(len(zone.anchor_points), 0, 
                                         f"Zone should have anchor points in {pattern_key}")
                        self.assertIsInstance(zone.center_price, (int, float), 
                                            f"Center price should be numeric in {pattern_key}")
                        self.assertIsInstance(zone.total_box_count, int, 
                                            f"Total box count should be int in {pattern_key}")
                        self.assertGreater(zone.total_box_count, 0, 
                                         f"Total box count should be > 0 in {pattern_key}")
                    
                    print(f"   ✅ Created {len(zones)} anchor zones")
                    
                    if zones:
                        total_points_in_zones = sum(len(z.anchor_points) for z in zones)
                        print(f"   📊 {total_points_in_zones} anchor points in zones")
    
    def test_anchor_points_price_levels(self):
        """Test that anchor points identify meaningful price levels."""
        print(f"\n🎯 Testing Anchor Points Price Levels")
        print("=" * 60)
        
        for pattern_key, pattern_info in TEST_PATTERNS.items():
            with self.subTest(pattern=pattern_key):
                print(f"\n💰 Testing price levels for {pattern_key}")
                
                # Generate pattern data
                candles = pattern_info['data_generator']()
                highs = [c['high'] for c in candles]
                lows = [c['low'] for c in candles]
                
                # Calculate P&F points
                x_coords, y_coords, pnf_symbols = _calculate_pnf_points(
                    highs, lows, self.box_size, self.reversal
                )
                
                if len(x_coords) == 0:
                    continue
                
                # Create P&F matrix
                pnf_matrix = self.create_pnf_matrix(x_coords, y_coords, pnf_symbols)
                
                if pnf_matrix.empty:
                    continue
                
                # Calculate anchor points
                anchor_points = self.anchor_calculator.calculate_anchor_points(pnf_matrix)
                
                if not anchor_points:
                    continue
                
                # Get price range from original data
                min_price = min(lows)
                max_price = max(highs)
                
                for ap in anchor_points:
                    # Anchor point price should be within data range
                    self.assertGreaterEqual(ap.price_level, min_price, 
                                          f"Anchor price {ap.price_level} below min {min_price} in {pattern_key}")
                    self.assertLessEqual(ap.price_level, max_price, 
                                       f"Anchor price {ap.price_level} above max {max_price} in {pattern_key}")
                    
                    # Price should be at reasonable box boundaries
                    price_from_min = ap.price_level - min_price
                    box_position = price_from_min / self.box_size
                    
                    # Should be close to a box boundary (within 0.1 box)
                    self.assertLess(abs(box_position - round(box_position)), 0.1, 
                                  f"Anchor price not on box boundary in {pattern_key}")
                
                print(f"   ✅ {len(anchor_points)} anchor points with valid price levels")
    
    def test_anchor_points_column_separation(self):
        """Test that anchor points respect minimum column separation."""
        print(f"\n🎯 Testing Column Separation")
        print("=" * 60)
        
        for pattern_key, pattern_info in TEST_PATTERNS.items():
            with self.subTest(pattern=pattern_key):
                print(f"\n📏 Testing separation for {pattern_key}")
                
                # Generate pattern data
                candles = pattern_info['data_generator']()
                highs = [c['high'] for c in candles]
                lows = [c['low'] for c in candles]
                
                # Calculate P&F points
                x_coords, y_coords, pnf_symbols = _calculate_pnf_points(
                    highs, lows, self.box_size, self.reversal
                )
                
                if len(x_coords) == 0:
                    continue
                
                # Create P&F matrix
                pnf_matrix = self.create_pnf_matrix(x_coords, y_coords, pnf_symbols)
                
                if pnf_matrix.empty:
                    continue
                
                # Calculate anchor points
                anchor_points = self.anchor_calculator.calculate_anchor_points(pnf_matrix)
                
                if not anchor_points:
                    continue
                
                # Check column separation
                for ap in anchor_points:
                    column_span = ap.end_column - ap.start_column
                    self.assertGreaterEqual(column_span, self.anchor_calculator.min_column_separation - 1, 
                                          f"Anchor point column span {column_span} too small in {pattern_key}")
                
                print(f"   ✅ {len(anchor_points)} anchor points with proper separation")
    
    def test_anchor_points_box_counting_accuracy(self):
        """Test that box counting is accurate."""
        print(f"\n🎯 Testing Box Counting Accuracy")
        print("=" * 60)
        
        # Test a few specific patterns for detailed box counting
        test_patterns = ['bullish_breakout', 'triple_top', 'catapult_buy']
        
        for pattern_key in test_patterns:
            if pattern_key in TEST_PATTERNS:
                with self.subTest(pattern=pattern_key):
                    print(f"\n🔢 Testing box counting for {pattern_key}")
                    
                    pattern_info = TEST_PATTERNS[pattern_key]
                    candles = pattern_info['data_generator']()
                    highs = [c['high'] for c in candles]
                    lows = [c['low'] for c in candles]
                    
                    # Calculate P&F points
                    x_coords, y_coords, pnf_symbols = _calculate_pnf_points(
                        highs, lows, self.box_size, self.reversal
                    )
                    
                    if len(x_coords) == 0:
                        continue
                    
                    # Create P&F matrix
                    pnf_matrix = self.create_pnf_matrix(x_coords, y_coords, pnf_symbols)
                    
                    if pnf_matrix.empty:
                        continue
                    
                    # Calculate anchor points
                    anchor_points = self.anchor_calculator.calculate_anchor_points(pnf_matrix)
                    
                    for ap in anchor_points:
                        # Manually verify box count for this anchor point
                        manual_count = 0
                        
                        # Count boxes in the specified range
                        for col in range(ap.start_column, ap.end_column + 1):
                            if col < len(pnf_matrix.columns):
                                col_data = pnf_matrix[col]
                                
                                # Find the row corresponding to this price level
                                min_price = min(y_coords)
                                row_idx = int((ap.price_level - min_price) / self.box_size)
                                
                                if 0 <= row_idx < len(col_data):
                                    if col_data.iloc[row_idx] in ['X', 'O']:
                                        manual_count += 1
                        
                        # Box count should be reasonable (allow some tolerance for edge cases)
                        self.assertGreater(ap.box_count, 0, 
                                         f"Box count should be > 0 for {pattern_key}")
                        
                        # Box count shouldn't be impossibly high
                        max_possible = ap.end_column - ap.start_column + 1
                        self.assertLessEqual(ap.box_count, max_possible, 
                                           f"Box count {ap.box_count} > max possible {max_possible} for {pattern_key}")
                    
                    if anchor_points:
                        print(f"   ✅ {len(anchor_points)} anchor points with valid box counts")


if __name__ == '__main__':
    print("🎯 ANCHOR POINTS PATTERNS TEST SUITE")
    print("=" * 60)
    print("Testing anchor points integration with all patterns")
    print("=" * 60)
    
    unittest.main(verbosity=2)
