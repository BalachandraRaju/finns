#!/usr/bin/env python3
"""
Test script to verify chart generation works with the fixed interval.
"""

import os
import sys
sys.path.append('.')

from app import charts, crud
from dotenv import load_dotenv

load_dotenv()

def test_chart_generation():
    """Test chart generation for TCS"""
    
    # TCS instrument key
    instrument_key = "NSE_EQ|INE467B01029"
    
    print(f"Testing chart generation for {instrument_key}")
    
    # Test if we can get stock info
    stock_info = crud.get_stock_by_instrument_key(instrument_key)
    if stock_info:
        print(f"Stock found: {stock_info['symbol']} - {stock_info['name']}")
    else:
        print("Stock not found in instruments list")
        return
    
    # Test chart generation
    try:
        print("Generating P&F chart...")
        chart_html = charts.generate_pnf_chart_html(instrument_key, box_pct=0.01, reversal=3)
        
        if "Could not find or fetch any chart data" in chart_html:
            print("❌ Chart generation failed - no data")
        elif "Stock not found" in chart_html:
            print("❌ Chart generation failed - stock not found")
        elif len(chart_html) > 1000:  # Assume successful if HTML is substantial
            print("✅ Chart generation successful!")
            print(f"Generated HTML length: {len(chart_html)} characters")
        else:
            print(f"⚠️  Chart generation returned: {chart_html[:200]}...")
            
    except Exception as e:
        print(f"❌ Chart generation failed with error: {e}")

if __name__ == "__main__":
    test_chart_generation()
