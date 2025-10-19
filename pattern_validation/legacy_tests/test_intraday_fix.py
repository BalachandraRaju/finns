#!/usr/bin/env python3
"""
Test script to verify the intraday chart display fix.
"""

import sys
import os
import datetime
import requests

# Add the app directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import charts

def test_box_size_fix():
    """Test that the box size fix works for intraday charts."""
    print("🔧 Testing Intraday Chart Display Fix")
    print("=" * 50)
    
    instrument_key = "NSE_EQ|INE467B01029"
    
    # Test different intervals with appropriate box sizes
    test_cases = [
        ("1minute", 0.0025, "1-minute with 0.25% box"),
        ("1minute", 0.001, "1-minute with 0.1% box"),
        ("30minute", 0.005, "30-minute with 0.5% box"),
        ("day", 0.01, "Daily with 1% box")
    ]
    
    for interval, box_size, description in test_cases:
        print(f"\n📊 Testing: {description}")
        
        try:
            # Test chart generation
            chart_html = charts.generate_pnf_chart_html(
                instrument_key, 
                box_pct=box_size, 
                interval=interval, 
                time_range="1month"
            )
            
            if chart_html and "Could not find" not in chart_html:
                print(f"   ✅ Chart generated: {len(chart_html)} characters")
                
                # Check for actual plot data
                if '"x":[]' in chart_html or '"y":[]' in chart_html:
                    print(f"   ❌ Chart has empty data arrays")
                elif "data" in chart_html and "x:" in chart_html:
                    print(f"   ✅ Chart contains plot data")
                else:
                    print(f"   ⚠️ Chart data unclear")
                    
            else:
                print(f"   ❌ Chart generation failed")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")

def test_endpoint_with_auto_box_size():
    """Test the endpoint with automatic box size selection."""
    print(f"\n🌐 Testing Endpoint with Auto Box Size")
    print("=" * 50)
    
    instrument_key = "NSE_EQ|INE467B01029"
    base_url = "http://localhost:8000"
    
    test_urls = [
        f"{base_url}/chart_data/{instrument_key}?interval=1minute",  # Should auto-select 0.25%
        f"{base_url}/chart_data/{instrument_key}?interval=30minute", # Should auto-select 0.5%
        f"{base_url}/chart_data/{instrument_key}?interval=day",      # Should auto-select 1%
        f"{base_url}/chart_data/{instrument_key}?interval=1minute&box_size=0.001",  # Manual 0.1%
    ]
    
    for url in test_urls:
        print(f"\n📡 Testing: {url}")
        
        try:
            response = requests.get(url, timeout=30)
            
            if response.status_code == 200:
                print(f"   ✅ Status: {response.status_code}")
                print(f"   📊 Response length: {len(response.text)} characters")
                
                # Check for chart content
                if "plotly" in response.text.lower():
                    print(f"   📈 Contains Plotly chart")
                    
                    # Check for data
                    if '"x":[]' in response.text or '"y":[]' in response.text:
                        print(f"   ❌ Empty data arrays")
                    elif '"x":[' in response.text and '"y":[' in response.text:
                        print(f"   ✅ Contains chart data")
                    else:
                        print(f"   ⚠️ Data status unclear")
                else:
                    print(f"   ❌ No Plotly chart found")
                    
            else:
                print(f"   ❌ Status: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")

def test_pnf_points_generation():
    """Test P&F points generation with different box sizes."""
    print(f"\n📊 Testing P&F Points Generation")
    print("=" * 40)
    
    instrument_key = "NSE_EQ|INE467B01029"
    today = datetime.date.today()
    start_date = today - datetime.timedelta(days=1)
    
    try:
        # Get 1-minute data
        candles = charts.get_candles_for_instrument(instrument_key, "1minute", start_date, today)
        
        if not candles:
            print("❌ No candle data available")
            return
            
        highs = [float(c['high']) for c in candles]
        lows = [float(c['low']) for c in candles]
        
        print(f"📈 Using {len(candles)} candles")
        print(f"📊 Price range: {min(lows):.2f} to {max(highs):.2f}")
        
        # Test the recommended box sizes
        recommended_sizes = [
            (0.001, "0.1% - Very detailed"),
            (0.0025, "0.25% - Recommended for 1-minute"),
            (0.005, "0.5% - Recommended for 30-minute"),
            (0.01, "1% - Recommended for daily")
        ]
        
        for box_pct, description in recommended_sizes:
            try:
                x_coords, y_coords, pnf_symbols = charts._calculate_pnf_points(highs, lows, box_pct, 3)
                
                points = len(x_coords)
                columns = max(x_coords) if x_coords else 0
                x_count = sum(1 for s in pnf_symbols if s == 'X')
                o_count = sum(1 for s in pnf_symbols if s == 'O')
                
                status = "✅ Good" if 5 <= points <= 100 else "⚠️ Check" if points > 0 else "❌ None"
                
                print(f"   {description}: {points} points, {columns} columns, {x_count}X/{o_count}O {status}")
                
            except Exception as e:
                print(f"   {description}: Error - {e}")
                
    except Exception as e:
        print(f"❌ Error in P&F test: {e}")

def main():
    """Run all intraday fix tests."""
    print("🔧 INTRADAY CHART DISPLAY FIX VALIDATION")
    print("Testing: Appropriate box sizes for intraday data")
    print("=" * 80)
    
    test_pnf_points_generation()
    test_box_size_fix()
    test_endpoint_with_auto_box_size()
    
    print("\n" + "=" * 80)
    print("📋 FIX VALIDATION SUMMARY:")
    print("✅ P&F Points Generation - Check if appropriate box sizes generate good data")
    print("✅ Chart Generation - Check if charts are created with plot data")
    print("✅ Endpoint Testing - Check if auto box size selection works")
    
    print("\n💡 Expected Results:")
    print("- 0.1%-0.25% box sizes should generate 10-50 P&F points for intraday")
    print("- Charts should contain actual plot data, not empty arrays")
    print("- Auto box size should select appropriate defaults")
    print("- Intraday charts should now display properly!")

if __name__ == "__main__":
    main()
