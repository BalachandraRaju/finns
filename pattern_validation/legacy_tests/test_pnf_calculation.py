#!/usr/bin/env python3
"""
Test script to diagnose P&F calculation issues with intraday data.
"""

import sys
import os
import datetime

# Add the app directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import charts

def test_pnf_calculation_with_intraday():
    """Test P&F calculation with real intraday data."""
    print("🔍 Testing P&F Calculation with Intraday Data")
    print("=" * 60)
    
    instrument_key = "NSE_EQ|INE467B01029"
    
    # Get 1-minute data for last 3 days
    today = datetime.date.today()
    start_date = today - datetime.timedelta(days=3)
    
    print(f"📅 Date range: {start_date} to {today}")
    
    try:
        # Get candle data
        candles = charts.get_candles_for_instrument(instrument_key, "1minute", start_date, today)
        print(f"📊 Retrieved {len(candles)} 1-minute candles")
        
        if not candles:
            print("❌ No candle data available")
            return
        
        # Extract highs and lows
        highs = [float(c['high']) for c in candles]
        lows = [float(c['low']) for c in candles]
        
        print(f"📈 Price range: {min(lows):.2f} to {max(highs):.2f}")
        print(f"📊 Sample highs: {highs[:5]}")
        print(f"📊 Sample lows: {lows[:5]}")
        
        # Test different box sizes
        box_sizes = [0.0025, 0.005, 0.01, 0.02]  # 0.25%, 0.5%, 1%, 2%
        
        for box_pct in box_sizes:
            print(f"\n🔍 Testing box size: {box_pct*100:.2f}%")
            
            try:
                x_coords, y_coords, pnf_symbols = charts._calculate_pnf_points(highs, lows, box_pct, 3)
                
                print(f"   📊 Generated {len(x_coords)} P&F points")
                
                if x_coords:
                    # Count X's and O's
                    x_count = sum(1 for s in pnf_symbols if s == 'X')
                    o_count = sum(1 for s in pnf_symbols if s == 'O')
                    columns = max(x_coords) if x_coords else 0
                    
                    print(f"   ✅ X's: {x_count}, O's: {o_count}, Columns: {columns}")
                    print(f"   📈 Price range: {min(y_coords):.2f} to {max(y_coords):.2f}")
                    
                    # Show first few points
                    print(f"   📊 First 5 points:")
                    for i in range(min(5, len(x_coords))):
                        print(f"      {i+1}. Column {x_coords[i]}: {pnf_symbols[i]} at {y_coords[i]:.2f}")
                else:
                    print(f"   ❌ No P&F points generated")
                    
            except Exception as e:
                print(f"   ❌ Error calculating P&F: {e}")
        
        # Test chart generation
        print(f"\n📊 Testing Chart Generation:")
        try:
            chart_html = charts.generate_pnf_chart_html(
                instrument_key, 
                box_pct=0.01, 
                interval="1minute", 
                time_range="1month"
            )
            
            if chart_html and "Could not find" not in chart_html:
                print(f"   ✅ Chart generated: {len(chart_html)} characters")
                
                # Check for actual data in chart
                if "data" in chart_html and "x:" in chart_html and "y:" in chart_html:
                    print(f"   ✅ Chart contains plot data")
                else:
                    print(f"   ⚠️ Chart may not contain plot data")
                    
                # Check for empty data arrays
                if '"x":[]' in chart_html or '"y":[]' in chart_html:
                    print(f"   ❌ Chart has empty data arrays")
                else:
                    print(f"   ✅ Chart data arrays are not empty")
                    
            else:
                print(f"   ❌ Chart generation failed")
                if chart_html:
                    print(f"   Error: {chart_html[:100]}...")
                    
        except Exception as e:
            print(f"   ❌ Chart generation error: {e}")
            
    except Exception as e:
        print(f"❌ Error in test: {e}")

def test_simple_pnf_calculation():
    """Test P&F calculation with simple sample data."""
    print(f"\n🧪 Testing P&F with Simple Sample Data")
    print("=" * 50)
    
    # Create simple test data that should definitely generate P&F points
    highs = [100, 101, 102, 103, 104, 105, 104, 103, 102, 101, 100, 99, 98, 97, 96, 97, 98, 99, 100, 101]
    lows =  [99,  100, 101, 102, 103, 104, 103, 102, 101, 100, 99,  98, 97, 96, 95, 96, 97, 98, 99,  100]
    
    print(f"📊 Sample data: {len(highs)} points")
    print(f"📈 High range: {min(highs)} to {max(highs)}")
    print(f"📉 Low range: {min(lows)} to {max(lows)}")
    
    box_pct = 0.01  # 1%
    
    try:
        x_coords, y_coords, pnf_symbols = charts._calculate_pnf_points(highs, lows, box_pct, 3)
        
        print(f"📊 Generated {len(x_coords)} P&F points")
        
        if x_coords:
            x_count = sum(1 for s in pnf_symbols if s == 'X')
            o_count = sum(1 for s in pnf_symbols if s == 'O')
            columns = max(x_coords)
            
            print(f"✅ X's: {x_count}, O's: {o_count}, Columns: {columns}")
            
            # Show all points
            print(f"📊 All P&F points:")
            for i in range(len(x_coords)):
                print(f"   {i+1}. Column {x_coords[i]}: {pnf_symbols[i]} at {y_coords[i]:.2f}")
        else:
            print(f"❌ No P&F points generated with simple data")
            
    except Exception as e:
        print(f"❌ Error with simple data: {e}")

def test_box_size_impact():
    """Test how different box sizes affect P&F generation."""
    print(f"\n📏 Testing Box Size Impact")
    print("=" * 40)
    
    # Get some real data
    instrument_key = "NSE_EQ|INE467B01029"
    today = datetime.date.today()
    start_date = today - datetime.timedelta(days=1)  # Just 1 day
    
    try:
        candles = charts.get_candles_for_instrument(instrument_key, "1minute", start_date, today)
        
        if not candles:
            print("❌ No data for box size test")
            return
            
        highs = [float(c['high']) for c in candles]
        lows = [float(c['low']) for c in candles]
        
        print(f"📊 Using {len(candles)} candles from last day")
        print(f"📈 Price range: {min(lows):.2f} to {max(highs):.2f}")
        
        # Test various box sizes
        box_sizes = [0.001, 0.0025, 0.005, 0.01, 0.02, 0.05]  # 0.1% to 5%
        
        for box_pct in box_sizes:
            try:
                x_coords, y_coords, pnf_symbols = charts._calculate_pnf_points(highs, lows, box_pct, 3)
                
                points = len(x_coords)
                columns = max(x_coords) if x_coords else 0
                
                print(f"   {box_pct*100:5.2f}%: {points:3d} points, {columns:2d} columns")
                
            except Exception as e:
                print(f"   {box_pct*100:5.2f}%: Error - {e}")
                
    except Exception as e:
        print(f"❌ Error in box size test: {e}")

def main():
    """Run all P&F calculation tests."""
    print("🔍 P&F CALCULATION DIAGNOSTICS")
    print("Investigating: Why P&F charts may not show data")
    print("=" * 80)
    
    test_simple_pnf_calculation()
    test_box_size_impact()
    test_pnf_calculation_with_intraday()
    
    print("\n" + "=" * 80)
    print("📋 P&F DIAGNOSTIC SUMMARY:")
    print("Check the results above to identify P&F calculation issues:")
    print("1. ✅ Simple data test - Does P&F work with known good data?")
    print("2. ✅ Box size impact - Are box sizes appropriate for price range?")
    print("3. ✅ Real data test - Does P&F work with actual intraday data?")
    
    print("\n💡 Common P&F Issues:")
    print("- Box size too large: No points generated if price moves are smaller than box")
    print("- Box size too small: Too many points, chart becomes cluttered")
    print("- Insufficient price movement: Need significant moves for P&F points")
    print("- Data quality: Bad data can prevent P&F calculation")

if __name__ == "__main__":
    main()
