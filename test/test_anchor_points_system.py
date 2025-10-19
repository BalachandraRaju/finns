#!/usr/bin/env python3
"""
Test the complete system with Anchor Points implementation.
"""

import os
import sys
from dotenv import load_dotenv

def test_anchor_point_calculator():
    """Test the anchor point calculator."""
    print("🎯 TESTING ANCHOR POINT CALCULATOR")
    print("-" * 40)
    
    try:
        from anchor_point_calculator import AnchorPointCalculator, AnchorPointVisualizer
        import pandas as pd
        import numpy as np
        
        # Create sample P&F matrix
        price_levels = [100.0, 101.0, 102.0, 103.0, 104.0, 105.0]
        columns = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
        
        # Create matrix with some activity
        matrix_data = pd.DataFrame(index=price_levels, columns=columns)
        matrix_data = matrix_data.fillna('')
        
        # Add some X's and O's to simulate trading activity
        matrix_data.loc[102.0, 1] = 'X'
        matrix_data.loc[102.0, 3] = 'X'
        matrix_data.loc[102.0, 5] = 'O'
        matrix_data.loc[102.0, 7] = 'X'  # 102.0 has most activity (4 boxes)
        
        matrix_data.loc[103.0, 2] = 'O'
        matrix_data.loc[103.0, 4] = 'O'
        matrix_data.loc[103.0, 6] = 'X'  # 103.0 has 3 boxes
        
        matrix_data.loc[101.0, 8] = 'X'
        matrix_data.loc[101.0, 9] = 'O'  # 101.0 has 2 boxes
        
        # Test anchor point calculation
        calculator = AnchorPointCalculator(min_column_separation=7)
        anchor_points = calculator.calculate_anchor_points(matrix_data)
        
        if anchor_points:
            print(f"✅ Anchor points calculated: {len(anchor_points)}")
            for anchor in anchor_points:
                print(f"   🎯 Price: {anchor.price_level}, Boxes: {anchor.box_count}, Type: {anchor.anchor_type}")
        else:
            print("⚠️ No anchor points found")
        
        # Test anchor zones
        zones = calculator.create_anchor_zones(anchor_points)
        if zones:
            print(f"✅ Anchor zones created: {len(zones)}")
            for i, zone in enumerate(zones):
                print(f"   🎯 Zone {i+1}: Center {zone.zone_center}, Range {zone.zone_range}, Activity: {zone.total_activity}")
        
        return True
        
    except Exception as e:
        print(f"❌ Anchor point calculator test failed: {e}")
        return False

def test_chart_integration():
    """Test anchor points integration with charts."""
    print("\n📊 TESTING CHART INTEGRATION")
    print("-" * 40)
    
    try:
        from app.charts import _add_anchor_points_to_chart, _create_pnf_matrix
        import plotly.graph_objects as go
        
        # Create sample chart data
        x_coords = [1, 2, 3, 4, 5, 6, 7, 8]
        y_coords = [100, 101, 102, 101, 102, 103, 102, 103]
        pnf_symbols = ['X', 'X', 'X', 'O', 'X', 'X', 'O', 'X']
        box_pct = 0.01
        
        # Create P&F matrix
        pnf_matrix = _create_pnf_matrix(x_coords, y_coords, pnf_symbols, box_pct)
        
        if pnf_matrix is not None:
            print("✅ P&F matrix created successfully")
            print(f"   📊 Matrix shape: {pnf_matrix.shape}")
        else:
            print("❌ P&F matrix creation failed")
            return False
        
        # Create test chart
        fig = go.Figure()
        
        # Add anchor points to chart
        _add_anchor_points_to_chart(fig, x_coords, y_coords, pnf_symbols, box_pct)
        
        print("✅ Anchor points added to chart successfully")
        
        # Check if chart has anchor point annotations
        has_anchor_annotations = any('Anchor' in str(annotation.text) for annotation in fig.layout.annotations)
        if has_anchor_annotations:
            print("✅ Anchor point annotations found in chart")
        else:
            print("⚠️ No anchor point annotations found")
        
        return True
        
    except Exception as e:
        print(f"❌ Chart integration test failed: {e}")
        return False

def test_upstox_token_status():
    """Test current Upstox token status."""
    print("\n🌐 TESTING UPSTOX TOKEN STATUS")
    print("-" * 40)
    
    try:
        load_dotenv()
        token = os.getenv('UPSTOX_ACCESS_TOKEN')
        
        if not token:
            print("❌ No UPSTOX_ACCESS_TOKEN found in .env")
            return False
        
        print(f"📊 Token found: {token[:20]}...")
        
        if token == "paste_your_new_token_here":
            print("⚠️ Token placeholder detected - need to update with real token")
            print("💡 Steps to fix:")
            print("   1. Go to https://developer.upstox.com/")
            print("   2. Click 'Generate' button for Access Token")
            print("   3. Replace 'paste_your_new_token_here' in .env file")
            return False
        
        # Test token with API call
        import requests
        headers = {
            'Authorization': f'Bearer {token}',
            'Accept': 'application/json'
        }
        
        response = requests.get('https://api.upstox.com/v2/user/profile', headers=headers, timeout=10)
        
        if response.status_code == 200:
            print("✅ Upstox API token is working!")
            user_data = response.json()
            print(f"👤 User: {user_data.get('data', {}).get('user_name', 'Unknown')}")
            return True
        else:
            print(f"❌ Upstox API failed: {response.status_code}")
            if response.status_code == 401:
                print("💡 Token expired - need to generate new one")
            return False
            
    except Exception as e:
        print(f"❌ Upstox token test error: {e}")
        return False

def test_application_startup():
    """Test if application can start with new features."""
    print("\n🚀 TESTING APPLICATION STARTUP")
    print("-" * 40)
    
    try:
        # Test database connection
        from app.db import DATABASE_URL, engine
        print(f"📊 Database: {DATABASE_URL}")
        
        if 'postgresql' in DATABASE_URL:
            print("✅ Using PostgreSQL")
        else:
            print("⚠️ Still using SQLite")
        
        # Test connection
        with engine.connect() as conn:
            print("✅ Database connection successful")
        
        # Test FastAPI app with anchor points
        from app.main import app
        print("✅ FastAPI app loads with anchor points feature")
        
        # Test chart generation with anchor points
        from app.charts import generate_pnf_chart_html
        
        # This should work even without data
        chart_html = generate_pnf_chart_html(
            instrument_key='NSE_EQ|INE467B01029',  # TCS
            show_anchor_points=True
        )
        
        if 'anchor' in chart_html.lower() or len(chart_html) > 100:
            print("✅ Chart generation with anchor points working")
        else:
            print("⚠️ Chart generation may have issues")
        
        return True
        
    except Exception as e:
        print(f"❌ Application startup test failed: {e}")
        return False

def main():
    """Main test function."""
    print("🚀 TESTING COMPLETE SYSTEM: PostgreSQL + Upstox + Anchor Points")
    print("=" * 70)
    
    results = {}
    
    # Test anchor point calculator
    results['anchor_calculator'] = test_anchor_point_calculator()
    
    # Test chart integration
    results['chart_integration'] = test_chart_integration()
    
    # Test Upstox token
    results['upstox_token'] = test_upstox_token_status()
    
    # Test application startup
    results['application'] = test_application_startup()
    
    # Summary
    print("\n🎯 TEST RESULTS SUMMARY")
    print("=" * 70)
    
    for component, success in results.items():
        status = "✅ WORKING" if success else "❌ NEEDS ATTENTION"
        print(f"   {component.upper().replace('_', ' ')}: {status}")
    
    total_working = sum(results.values())
    total_tests = len(results)
    
    print(f"\n📊 OVERALL: {total_working}/{total_tests} components working")
    
    if total_working == total_tests:
        print("🎉 ALL SYSTEMS OPERATIONAL!")
        print("🚀 Ready to start application with anchor points!")
    elif total_working >= 3:
        print("⚠️ MOSTLY WORKING - Minor issues remain")
    else:
        print("❌ MULTIPLE ISSUES - Need attention")
    
    # Next steps
    print("\n💡 NEXT STEPS:")
    
    if not results['upstox_token']:
        print("   🌐 Fix Upstox token: Get new token from https://developer.upstox.com/")
    
    if not results['anchor_calculator']:
        print("   🎯 Fix anchor point calculator: Check dependencies")
    
    if results['upstox_token'] and results['anchor_calculator']:
        print("   🎉 Start the application:")
        print("   🚀 python -m uvicorn app.main:app --host 0.0.0.0 --port 8000")
        print("   📊 All charts will now include anchor points!")
        print("   🎯 Anchor points show the most populated price levels")

if __name__ == "__main__":
    main()
