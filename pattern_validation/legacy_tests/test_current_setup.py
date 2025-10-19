#!/usr/bin/env python3
"""
Test the current trading system setup to see what's actually configured and working.
"""

import sys
import os
from dotenv import load_dotenv

# Add the app directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

def test_current_configuration():
    """Test what's currently configured in the system."""
    print("🔍 CURRENT SYSTEM CONFIGURATION TEST")
    print("=" * 60)
    
    # Check environment variables
    print("1. 🔧 Environment Variables:")
    env_vars = {
        'UPSTOX_ACCESS_TOKEN': os.getenv("UPSTOX_ACCESS_TOKEN", ""),
        'ANGEL_API_KEY': os.getenv("ANGEL_API_KEY", ""),
        'ANGEL_USERNAME': os.getenv("ANGEL_USERNAME", ""),
        'ANGEL_PASSWORD': os.getenv("ANGEL_PASSWORD", ""),
        'TELEGRAM_BOT_TOKEN': os.getenv("TELEGRAM_BOT_TOKEN", ""),
    }
    
    for var, value in env_vars.items():
        if value:
            display_value = f"{value[:6]}...{value[-4:]}" if len(value) > 10 else value
            print(f"   ✅ {var}: {display_value}")
        else:
            print(f"   ❌ {var}: Not configured")
    
    # Check what broker is actually being used
    print("\n2. 📊 Broker Configuration:")
    try:
        # Check if Upstox is configured
        upstox_token = os.getenv("UPSTOX_ACCESS_TOKEN", "")
        if upstox_token:
            print("   🎯 Upstox: Configured")
            try:
                import upstox_client
                print("   ✅ Upstox SDK: Available")
            except ImportError:
                print("   ❌ Upstox SDK: Not installed")
        else:
            print("   ❌ Upstox: Not configured")
        
        # Check if Angel One is configured
        angel_key = os.getenv("ANGEL_API_KEY", "")
        if angel_key:
            print("   🎯 Angel One: Configured")
            try:
                from SmartApi import SmartConnect
                print("   ✅ Angel One SDK: Available")
            except ImportError:
                print("   ❌ Angel One SDK: Not installed")
        else:
            print("   ❌ Angel One: Not configured")
            
    except Exception as e:
        print(f"   ❌ Error checking broker config: {e}")
    
    # Test database
    print("\n3. 🗄️ Database:")
    try:
        from app.crud import get_watchlist_details
        stocks = get_watchlist_details()
        print(f"   ✅ Database working: {len(stocks)} stocks in watchlist")
        
        if stocks:
            print("   📊 Sample stocks:")
            for i, stock in enumerate(stocks[:3], 1):
                print(f"      {i}. {stock.name} ({stock.symbol})")
        else:
            print("   ⚠️ No stocks in watchlist")
            
    except Exception as e:
        print(f"   ❌ Database error: {e}")
    
    # Test chart generation with dummy data
    print("\n4. 📈 Chart Generation:")
    try:
        from app.test_patterns import generate_bullish_breakout_pattern
        from app.charts import _calculate_pnf_points
        
        # Test with dummy data
        dummy_candles = generate_bullish_breakout_pattern()
        highs = [float(c['high']) for c in dummy_candles]
        lows = [float(c['low']) for c in dummy_candles]
        
        x_coords, y_coords, pnf_symbols = _calculate_pnf_points(highs, lows, 0.01, 3)
        
        if x_coords:
            print(f"   ✅ P&F calculation working: {len(x_coords)} points generated")
        else:
            print("   ❌ P&F calculation failed")
            
        # Test Fibonacci
        from app.charts import _calculate_fibonacci_levels
        fib_data = _calculate_fibonacci_levels(highs, lows)
        if fib_data:
            print(f"   ✅ Fibonacci calculation working: {len(fib_data['levels'])} levels")
        else:
            print("   ❌ Fibonacci calculation failed")
            
    except Exception as e:
        print(f"   ❌ Chart generation error: {e}")
    
    # Test pattern detection
    print("\n5. 🔍 Pattern Detection:")
    try:
        from app.pattern_detector import PatternDetector
        detector = PatternDetector()
        print("   ✅ Pattern detector initialized")
        
        # Test with sample data
        if 'x_coords' in locals() and x_coords:
            alerts = detector.analyze_pattern_formation(x_coords, y_coords, pnf_symbols)
            print(f"   ✅ Pattern detection working: {len(alerts)} alerts generated")
        else:
            print("   ⚠️ No P&F data to test pattern detection")
            
    except Exception as e:
        print(f"   ❌ Pattern detection error: {e}")
    
    # Test web server endpoints
    print("\n6. 🌐 Web Server:")
    try:
        import requests
        
        # Test if server is running
        response = requests.get("http://localhost:8000/", timeout=5)
        if response.status_code == 200:
            print("   ✅ Web server running")
            
            # Test test charts endpoint
            test_response = requests.get("http://localhost:8000/test-charts", timeout=5)
            if test_response.status_code == 200:
                print("   ✅ Test charts page working")
            else:
                print(f"   ⚠️ Test charts page: {test_response.status_code}")
                
        else:
            print(f"   ⚠️ Web server response: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("   ❌ Web server not running")
    except Exception as e:
        print(f"   ❌ Web server test error: {e}")
    
    print("\n" + "=" * 60)
    print("📋 SUMMARY:")
    
    # Determine what's working
    upstox_configured = bool(os.getenv("UPSTOX_ACCESS_TOKEN", ""))
    angel_configured = bool(os.getenv("ANGEL_API_KEY", ""))
    
    if upstox_configured:
        print("🎯 PRIMARY BROKER: Upstox (configured)")
        print("💡 To test Upstox: Ensure access token is valid and not expired")
    elif angel_configured:
        print("🎯 PRIMARY BROKER: Angel One (configured)")
        print("💡 System is set up for Angel One, not Upstox")
    else:
        print("❌ NO BROKER CONFIGURED")
        print("💡 Configure either Upstox or Angel One API credentials")
    
    print("\n🔧 RECOMMENDATIONS:")
    if not upstox_configured and not angel_configured:
        print("1. Add broker API credentials to .env file")
        print("2. Install required SDK (upstox-python-sdk or smartapi-python)")
    elif angel_configured and not upstox_configured:
        print("1. System is working with Angel One")
        print("2. To use Upstox: Add UPSTOX_ACCESS_TOKEN to .env")
        print("3. Install: pip install upstox-python-sdk")
    elif upstox_configured:
        print("1. Verify Upstox access token is valid")
        print("2. Check token expiration")
        print("3. Test API connection")
    
    return upstox_configured or angel_configured

if __name__ == "__main__":
    test_current_configuration()
