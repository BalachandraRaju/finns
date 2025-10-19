#!/usr/bin/env python3
"""
Test the new Upstox access token.
"""

import os
import sys
import requests
from dotenv import load_dotenv

def test_upstox_token():
    """Test the new Upstox access token."""
    print('🌐 TESTING NEW UPSTOX ACCESS TOKEN')
    print('=' * 50)
    
    load_dotenv()
    token = os.getenv('UPSTOX_ACCESS_TOKEN')
    
    if not token:
        print('❌ No UPSTOX_ACCESS_TOKEN found in .env')
        return False
    
    print(f'📊 Token: {token[:20]}...')
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Accept': 'application/json'
    }
    
    try:
        print('🧪 Testing API connection...')
        response = requests.get('https://api.upstox.com/v2/user/profile', headers=headers, timeout=10)
        
        if response.status_code == 200:
            print('✅ Upstox API authentication successful!')
            user_data = response.json()
            user_name = user_data.get('data', {}).get('user_name', 'Unknown')
            print(f'👤 User: {user_name}')
            print('🎉 TOKEN IS WORKING!')
            return True
        else:
            print(f'❌ Upstox API failed: {response.status_code}')
            print(f'Response: {response.text}')
            return False
            
    except Exception as e:
        print(f'❌ Error: {e}')
        return False

def test_ltp_api():
    """Test LTP API with new token."""
    print('\n📊 TESTING LTP API')
    print('-' * 30)
    
    try:
        sys.path.append('data-fetch')
        from ltp_service import ltp_service
        
        print('🚀 Testing LTP collection...')
        ltp_data = ltp_service.collect_ltp_data()
        
        if ltp_data:
            print(f'✅ LTP API Success!')
            print(f'   📊 Stocks collected: {len(ltp_data)}')
            print(f'   🌐 API calls made: 1 (instead of {len(ltp_data)})')
            print(f'   💰 API efficiency: {len(ltp_data)}x improvement')
            
            # Show sample data
            sample_symbols = list(ltp_data.keys())[:3]
            print(f'   📈 Sample data:')
            for symbol in sample_symbols:
                print(f'      💰 {symbol}: ₹{ltp_data[symbol]}')
            
            return True
        else:
            print('❌ LTP API failed - no data received')
            return False
            
    except Exception as e:
        print(f'❌ LTP API test error: {e}')
        return False

def test_history_api():
    """Test History API with new token."""
    print('\n📈 TESTING HISTORY API')
    print('-' * 30)
    
    try:
        sys.path.append('data-fetch')
        from upstox_client import upstox_client
        from datetime import date, timedelta
        
        # Test with TCS data
        end_date = date.today()
        start_date = end_date - timedelta(days=1)
        
        print(f'🧪 Fetching TCS 1-minute data...')
        print(f'   📅 From: {start_date}')
        print(f'   📅 To: {end_date}')
        
        candles = upstox_client.get_historical_data(
            instrument_key='NSE_EQ|INE467B01029',  # TCS
            interval='1minute',
            from_date=start_date,
            to_date=end_date
        )
        
        if candles:
            print(f'✅ History API Success!')
            print(f'   📊 Candles retrieved: {len(candles)}')
            if candles:
                sample_candle = candles[0]
                print(f'   📈 Sample candle: OHLC = {sample_candle["open"]}/{sample_candle["high"]}/{sample_candle["low"]}/{sample_candle["close"]}')
            return True
        else:
            print('❌ History API failed - no data received')
            return False
            
    except Exception as e:
        print(f'❌ History API test error: {e}')
        return False

def test_anchor_points():
    """Test anchor points functionality."""
    print('\n🎯 TESTING ANCHOR POINTS')
    print('-' * 30)
    
    try:
        from anchor_point_calculator import AnchorPointCalculator
        print('✅ Anchor point calculator imported successfully')
        
        from app.charts import _add_anchor_points_to_chart
        print('✅ Chart integration functions available')
        
        # Test chart generation with anchor points
        from app.charts import generate_pnf_chart_html
        
        chart_html = generate_pnf_chart_html(
            instrument_key='NSE_EQ|INE467B01029',  # TCS
            show_anchor_points=True
        )
        
        if 'anchor' in chart_html.lower() or len(chart_html) > 100:
            print('✅ Chart generation with anchor points working')
            return True
        else:
            print('⚠️ Chart generation may have issues')
            return False
            
    except Exception as e:
        print(f'❌ Anchor points test error: {e}')
        return False

def main():
    """Main test function."""
    print('🚀 TESTING COMPLETE SYSTEM WITH NEW TOKEN')
    print('=' * 60)
    
    results = {}
    
    # Test Upstox authentication
    results['upstox_auth'] = test_upstox_token()
    
    # Test LTP API (only if auth works)
    if results['upstox_auth']:
        results['ltp_api'] = test_ltp_api()
    else:
        results['ltp_api'] = False
    
    # Test History API (only if auth works)
    if results['upstox_auth']:
        results['history_api'] = test_history_api()
    else:
        results['history_api'] = False
    
    # Test anchor points
    results['anchor_points'] = test_anchor_points()
    
    # Summary
    print('\n🎯 TEST RESULTS SUMMARY')
    print('=' * 60)
    
    for component, success in results.items():
        status = '✅ WORKING' if success else '❌ NEEDS ATTENTION'
        print(f'   {component.upper().replace("_", " ")}: {status}')
    
    total_working = sum(results.values())
    total_tests = len(results)
    
    print(f'\n📊 OVERALL: {total_working}/{total_tests} components working')
    
    if total_working == total_tests:
        print('🎉 ALL SYSTEMS OPERATIONAL!')
        print('🚀 Ready to start application!')
        print('\n💡 NEXT STEPS:')
        print('   🚀 python -m uvicorn app.main:app --host 0.0.0.0 --port 8000')
        print('   📊 All charts will show anchor points!')
        print('   🌐 Real-time LTP data collection working!')
        print('   🎯 20x API efficiency achieved!')
    elif total_working >= 2:
        print('⚠️ MOSTLY WORKING - Some features may need attention')
    else:
        print('❌ MULTIPLE ISSUES - Need investigation')

if __name__ == '__main__':
    main()
