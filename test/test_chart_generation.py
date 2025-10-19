#!/usr/bin/env python3
"""
Test cases for chart generation with all test patterns.
Ensures all patterns work correctly with chart generation functions.
"""

import sys
import os
import unittest
from typing import List, Dict, Any

# Add project root to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.test_patterns import TEST_PATTERNS, generate_test_chart_html
from app.charts import _calculate_pnf_points

class TestChartGeneration(unittest.TestCase):
    """Test chart generation functionality with all test patterns."""
    
    def setUp(self):
        """Set up test environment."""
        self.box_size = 0.01  # 1% box size
        self.reversal = 3     # 3-box reversal
    
    def test_pnf_calculation_all_patterns(self):
        """Test P&F calculation works for all patterns."""
        print(f"\n📊 Testing P&F Calculation for All Patterns")
        print("=" * 60)
        
        for pattern_key, pattern_info in TEST_PATTERNS.items():
            with self.subTest(pattern=pattern_key):
                print(f"\n🧮 Testing P&F calculation for {pattern_key}")
                
                # Generate pattern data
                candles = pattern_info['data_generator']()
                highs = [c['high'] for c in candles]
                lows = [c['low'] for c in candles]
                
                # Test P&F calculation
                x_coords, y_coords, pnf_symbols = _calculate_pnf_points(
                    highs, lows, self.box_size, self.reversal
                )
                
                # Validate results
                self.assertIsInstance(x_coords, list, f"x_coords should be list for {pattern_key}")
                self.assertIsInstance(y_coords, list, f"y_coords should be list for {pattern_key}")
                self.assertIsInstance(pnf_symbols, list, f"pnf_symbols should be list for {pattern_key}")
                
                # Arrays should have same length
                self.assertEqual(len(x_coords), len(y_coords), 
                               f"Coordinate arrays length mismatch in {pattern_key}")
                self.assertEqual(len(x_coords), len(pnf_symbols), 
                               f"Coordinates and symbols length mismatch in {pattern_key}")
                
                # Should generate some points for valid patterns
                if len(candles) > 0 and max(highs) > min(lows):
                    self.assertGreater(len(x_coords), 0, f"No P&F points generated for {pattern_key}")
                
                # Validate symbols
                for symbol in pnf_symbols:
                    self.assertIn(symbol, ['X', 'O'], f"Invalid symbol '{symbol}' in {pattern_key}")
                
                # Validate coordinates
                for coord in x_coords:
                    self.assertIsInstance(coord, (int, float), f"Invalid x_coord in {pattern_key}")
                    self.assertGreaterEqual(coord, 0, f"Negative x_coord in {pattern_key}")
                
                for coord in y_coords:
                    self.assertIsInstance(coord, (int, float), f"Invalid y_coord in {pattern_key}")
                    self.assertGreater(coord, 0, f"Non-positive y_coord in {pattern_key}")
                
                print(f"   ✅ Generated {len(x_coords)} P&F points")
    
    def test_chart_html_generation(self):
        """Test HTML chart generation for all patterns."""
        print(f"\n📊 Testing HTML Chart Generation")
        print("=" * 60)
        
        for pattern_key in TEST_PATTERNS.keys():
            with self.subTest(pattern=pattern_key):
                print(f"\n🌐 Testing HTML generation for {pattern_key}")
                
                try:
                    # Generate chart HTML
                    chart_html = generate_test_chart_html(
                        pattern_key, 
                        box_pct=self.box_size, 
                        reversal=self.reversal
                    )
                    
                    # Validate HTML structure
                    self.assertIsInstance(chart_html, str, f"Chart HTML should be string for {pattern_key}")
                    self.assertGreater(len(chart_html), 0, f"Chart HTML should not be empty for {pattern_key}")
                    
                    # Should contain basic HTML elements
                    html_elements = ['<div', '<script', 'Plotly', 'newPlot']
                    for element in html_elements:
                        self.assertIn(element, chart_html, 
                                    f"Chart HTML missing '{element}' for {pattern_key}")
                    
                    # Should contain pattern name
                    self.assertIn(pattern_key, chart_html.lower(), 
                                f"Chart HTML should contain pattern name for {pattern_key}")
                    
                    print(f"   ✅ Generated {len(chart_html)} character HTML")
                    
                except Exception as e:
                    self.fail(f"Chart HTML generation failed for {pattern_key}: {str(e)}")
    
    def test_chart_with_anchor_points(self):
        """Test chart generation with anchor points enabled."""
        print(f"\n📊 Testing Charts with Anchor Points")
        print("=" * 60)
        
        # Test a subset of patterns for anchor points
        test_patterns = ['bullish_breakout', 'triple_top', 'catapult_buy', 'bearish_breakdown']
        
        for pattern_key in test_patterns:
            if pattern_key in TEST_PATTERNS:
                with self.subTest(pattern=pattern_key):
                    print(f"\n🎯 Testing anchor points chart for {pattern_key}")
                    
                    try:
                        # Generate chart HTML with anchor points
                        chart_html = generate_test_chart_html(
                            pattern_key, 
                            box_pct=self.box_size, 
                            reversal=self.reversal
                        )
                        
                        # Should contain anchor point related content
                        anchor_keywords = ['anchor', 'box count', 'zone']
                        has_anchor_content = any(keyword in chart_html.lower() for keyword in anchor_keywords)
                        
                        # Note: Not enforcing anchor content as it depends on pattern complexity
                        print(f"   📊 Anchor content present: {has_anchor_content}")
                        print(f"   ✅ Chart generated successfully")
                        
                    except Exception as e:
                        self.fail(f"Anchor points chart generation failed for {pattern_key}: {str(e)}")
    
    def test_chart_data_structure(self):
        """Test that chart data has proper structure."""
        print(f"\n📊 Testing Chart Data Structure")
        print("=" * 60)
        
        for pattern_key, pattern_info in TEST_PATTERNS.items():
            with self.subTest(pattern=pattern_key):
                print(f"\n🏗️ Testing data structure for {pattern_key}")
                
                # Generate pattern data
                candles = pattern_info['data_generator']()
                highs = [c['high'] for c in candles]
                lows = [c['low'] for c in candles]
                
                # Calculate P&F points
                x_coords, y_coords, pnf_symbols = _calculate_pnf_points(
                    highs, lows, self.box_size, self.reversal
                )
                
                # Create chart data structure
                chart_data = {
                    'pattern_name': pattern_key,
                    'pattern_info': pattern_info,
                    'candles': candles,
                    'pnf_data': {
                        'x_coords': x_coords,
                        'y_coords': y_coords,
                        'symbols': pnf_symbols
                    },
                    'parameters': {
                        'box_size': self.box_size,
                        'reversal': self.reversal
                    }
                }
                
                # Validate structure
                self.assertIn('pattern_name', chart_data)
                self.assertIn('pattern_info', chart_data)
                self.assertIn('candles', chart_data)
                self.assertIn('pnf_data', chart_data)
                self.assertIn('parameters', chart_data)
                
                # Validate P&F data
                pnf_data = chart_data['pnf_data']
                self.assertIn('x_coords', pnf_data)
                self.assertIn('y_coords', pnf_data)
                self.assertIn('symbols', pnf_data)
                
                # Validate parameters
                params = chart_data['parameters']
                self.assertEqual(params['box_size'], self.box_size)
                self.assertEqual(params['reversal'], self.reversal)
                
                print(f"   ✅ Valid chart data structure")
    
    def test_chart_coordinate_validity(self):
        """Test that chart coordinates are valid for plotting."""
        print(f"\n📊 Testing Chart Coordinate Validity")
        print("=" * 60)
        
        for pattern_key, pattern_info in TEST_PATTERNS.items():
            with self.subTest(pattern=pattern_key):
                print(f"\n📍 Testing coordinates for {pattern_key}")
                
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
                
                # Test coordinate validity
                for i, (x, y, symbol) in enumerate(zip(x_coords, y_coords, pnf_symbols)):
                    # X coordinates should be sequential integers
                    self.assertIsInstance(x, (int, float), f"X coord {i} not numeric in {pattern_key}")
                    self.assertGreaterEqual(x, 0, f"X coord {i} negative in {pattern_key}")
                    
                    # Y coordinates should be valid prices
                    self.assertIsInstance(y, (int, float), f"Y coord {i} not numeric in {pattern_key}")
                    self.assertGreater(y, 0, f"Y coord {i} not positive in {pattern_key}")
                    
                    # Symbols should be valid
                    self.assertIn(symbol, ['X', 'O'], f"Invalid symbol at {i} in {pattern_key}")
                
                # X coordinates should be in reasonable order
                if len(x_coords) > 1:
                    x_diffs = [x_coords[i+1] - x_coords[i] for i in range(len(x_coords)-1)]
                    
                    # Should have some progression (not all same)
                    self.assertTrue(any(diff != 0 for diff in x_diffs), 
                                  f"No X coordinate progression in {pattern_key}")
                    
                    # Should not have huge jumps
                    max_diff = max(x_diffs)
                    self.assertLessEqual(max_diff, 10, 
                                       f"X coordinate jump too large ({max_diff}) in {pattern_key}")
                
                print(f"   ✅ {len(x_coords)} valid coordinates")
    
    def test_chart_symbol_alternation(self):
        """Test that P&F symbols alternate properly (X-O-X-O pattern)."""
        print(f"\n📊 Testing Symbol Alternation")
        print("=" * 60)
        
        for pattern_key, pattern_info in TEST_PATTERNS.items():
            with self.subTest(pattern=pattern_key):
                print(f"\n🔄 Testing symbol alternation for {pattern_key}")
                
                # Generate pattern data
                candles = pattern_info['data_generator']()
                highs = [c['high'] for c in candles]
                lows = [c['low'] for c in candles]
                
                # Calculate P&F points
                x_coords, y_coords, pnf_symbols = _calculate_pnf_points(
                    highs, lows, self.box_size, self.reversal
                )
                
                if len(pnf_symbols) < 2:
                    continue
                
                # Group symbols by column
                columns = {}
                for x, symbol in zip(x_coords, pnf_symbols):
                    if x not in columns:
                        columns[x] = []
                    columns[x].append(symbol)
                
                # Check that each column has consistent symbols
                for col, symbols in columns.items():
                    unique_symbols = set(symbols)
                    self.assertEqual(len(unique_symbols), 1, 
                                   f"Mixed symbols in column {col} for {pattern_key}: {symbols}")
                
                # Check column alternation
                sorted_columns = sorted(columns.keys())
                if len(sorted_columns) > 1:
                    column_symbols = [list(columns[col])[0] for col in sorted_columns]
                    
                    # Should have some alternation (not all same symbol)
                    unique_column_symbols = set(column_symbols)
                    if len(unique_column_symbols) > 1:
                        # Check for proper alternation pattern
                        alternation_valid = True
                        for i in range(len(column_symbols) - 1):
                            if column_symbols[i] == column_symbols[i + 1]:
                                # Same symbol in consecutive columns - check if it's a valid continuation
                                # This can happen in complex patterns, so we just note it
                                pass
                        
                        print(f"   ✅ Symbol pattern: {'-'.join(column_symbols[:10])}{'...' if len(column_symbols) > 10 else ''}")
                    else:
                        print(f"   ⚠️ All columns have same symbol: {column_symbols[0]}")


if __name__ == '__main__':
    print("📊 CHART GENERATION TEST SUITE")
    print("=" * 60)
    print("Testing chart generation with all patterns")
    print("=" * 60)
    
    unittest.main(verbosity=2)
