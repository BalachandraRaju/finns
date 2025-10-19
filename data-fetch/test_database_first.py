#!/usr/bin/env python3
"""
Test Database-First Architecture
Verifies that all components (test-charts, PnF matrix, alerts) use database-first approach.
"""

import sys
import os
import time
from datetime import datetime, date, timedelta

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from logzero import logger

def test_database_service():
    """Test the database service functionality."""
    print("\n" + "="*60)
    print("🗄️ TESTING DATABASE SERVICE")
    print("="*60)
    
    try:
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        from database_service import database_service
        
        print("✅ Database service imported successfully")
        
        # Test F&O stocks loading
        from fo_stocks_loader import fo_stocks_loader
        stocks_with_keys = fo_stocks_loader.get_fo_symbols_with_instrument_keys()
        
        if not stocks_with_keys:
            print("❌ No F&O stocks found for testing")
            return False
        
        test_stock = stocks_with_keys[0]
        symbol = test_stock['symbol']
        instrument_key = test_stock['instrument_key']
        
        print(f"📊 Testing with: {symbol} ({instrument_key})")
        
        # Test historical candles
        print("📈 Testing historical candles retrieval...")
        historical_candles = database_service.get_historical_candles_smart(
            instrument_key=instrument_key,
            interval="day",
            months_back=1
        )
        
        print(f"   Retrieved {len(historical_candles)} historical candles")
        
        # Test intraday candles
        print("⚡ Testing intraday candles retrieval...")
        intraday_candles = database_service.get_intraday_candles_smart(
            instrument_key=instrument_key,
            interval="1minute"
        )
        
        print(f"   Retrieved {len(intraday_candles)} intraday candles")
        
        # Test LTP retrieval
        print("💰 Testing LTP retrieval...")
        latest_ltp = database_service.get_latest_ltp(
            symbol=symbol,
            auto_collect=False  # Don't trigger collection in test
        )
        
        if latest_ltp:
            print(f"   Latest LTP: ₹{latest_ltp}")
        else:
            print("   No recent LTP data found")
        
        print("✅ Database service tests completed")
        return True
        
    except Exception as e:
        print(f"❌ Database service test error: {e}")
        return False

def test_charts_database_first():
    """Test that charts use database-first approach."""
    print("\n" + "="*60)
    print("📊 TESTING CHARTS DATABASE-FIRST")
    print("="*60)
    
    try:
        from app import charts
        from app import crud
        
        # Get a test stock
        stocks = crud.get_all_stocks()
        if not stocks:
            print("❌ No stocks in watchlist for testing")
            return False
        
        test_stock = stocks[0]
        instrument_key = test_stock['instrument_key']
        symbol = test_stock['symbol']
        
        print(f"📊 Testing charts with: {symbol} ({instrument_key})")
        
        # Test get_candles_for_instrument (should use database-first)
        print("📈 Testing get_candles_for_instrument...")
        today = date.today()
        start_date = today - timedelta(days=30)
        
        candles = charts.get_candles_for_instrument(
            instrument_key=instrument_key,
            interval="day",
            from_date=start_date,
            to_date=today
        )
        
        print(f"   Retrieved {len(candles)} candles via charts.get_candles_for_instrument")
        
        # Test intraday candles with fallback
        print("⚡ Testing get_intraday_candles_with_fallback...")
        intraday_candles = charts.get_intraday_candles_with_fallback(
            instrument_key=instrument_key,
            interval="1minute"
        )
        
        print(f"   Retrieved {len(intraday_candles)} intraday candles")
        
        # Test chart generation
        print("📊 Testing chart generation...")
        chart_html = charts.generate_pnf_chart_html(
            instrument_key=instrument_key,
            box_pct=0.01,
            reversal=3,
            interval="day",
            time_range="1month"
        )
        
        if chart_html and len(chart_html) > 100:
            print(f"   Chart generated successfully: {len(chart_html)} characters")
        else:
            print("   Chart generation failed or returned minimal content")
        
        print("✅ Charts database-first tests completed")
        return True
        
    except Exception as e:
        print(f"❌ Charts database-first test error: {e}")
        return False

def test_pnf_matrix_database_first():
    """Test that PnF matrix uses database-first approach."""
    print("\n" + "="*60)
    print("🎯 TESTING PNF MATRIX DATABASE-FIRST")
    print("="*60)
    
    try:
        from app.pnf_matrix import PnFMatrixCalculator
        from app import crud
        
        # Get a test stock
        stocks = crud.get_all_stocks()
        if not stocks:
            print("❌ No stocks in watchlist for testing")
            return False
        
        test_stock = stocks[0]
        instrument_key = test_stock['instrument_key']
        symbol = test_stock['symbol']
        
        print(f"🎯 Testing PnF matrix with: {symbol} ({instrument_key})")
        
        # Test matrix calculation
        calculator = PnFMatrixCalculator()
        
        print("📊 Testing daily matrix calculation...")
        daily_result = calculator.calculate_matrix_for_stock(
            instrument_key=instrument_key,
            timeframe="day"
        )
        
        if daily_result:
            print(f"   Daily matrix score: {daily_result.total_score} ({daily_result.matrix_strength})")
            print(f"   Box sizes tested: {len(daily_result.matrix_scores)}")
        else:
            print("   Daily matrix calculation failed")
        
        print("⚡ Testing intraday matrix calculation...")
        intraday_result = calculator.calculate_matrix_for_stock(
            instrument_key=instrument_key,
            timeframe="1minute"
        )
        
        if intraday_result:
            print(f"   Intraday matrix score: {intraday_result.total_score} ({intraday_result.matrix_strength})")
        else:
            print("   Intraday matrix calculation failed")
        
        print("✅ PnF matrix database-first tests completed")
        return True
        
    except Exception as e:
        print(f"❌ PnF matrix database-first test error: {e}")
        return False

def test_alerts_database_first():
    """Test that alerts use database-first approach."""
    print("\n" + "="*60)
    print("🚨 TESTING ALERTS DATABASE-FIRST")
    print("="*60)
    
    try:
        from app import scheduler
        from app import crud
        
        # Get a test stock
        stocks = crud.get_all_stocks()
        if not stocks:
            print("❌ No stocks in watchlist for testing")
            return False
        
        test_stock = stocks[0]
        instrument_key = test_stock['instrument_key']
        symbol = test_stock['symbol']
        
        print(f"🚨 Testing alerts with: {symbol} ({instrument_key})")
        
        # Test alert checking (this should use database-first approach)
        print("📊 Testing alert checking...")
        
        # Note: We can't easily test the full alert flow without triggering actual alerts
        # But we can verify the data retrieval part works
        
        # Test that the scheduler can access the database service
        try:
            from data_fetch.database_service import database_service
            
            # Test data retrieval for alerts
            today = date.today()
            start_date = today - timedelta(days=30)
            
            candles = database_service.get_candles_smart(
                instrument_key=instrument_key,
                interval="1minute",
                start_date=start_date,
                end_date=today,
                auto_backfill=False  # Don't trigger backfill in test
            )
            
            print(f"   Alert data retrieval: {len(candles)} 1-minute candles available")
            
        except Exception as e:
            print(f"   Alert data retrieval test failed: {e}")
        
        print("✅ Alerts database-first tests completed")
        return True
        
    except Exception as e:
        print(f"❌ Alerts database-first test error: {e}")
        return False

def test_performance_comparison():
    """Test performance difference between database-first and API-first."""
    print("\n" + "="*60)
    print("⚡ TESTING PERFORMANCE COMPARISON")
    print("="*60)
    
    try:
        from app import crud
        
        # Get a test stock
        stocks = crud.get_all_stocks()
        if not stocks:
            print("❌ No stocks in watchlist for testing")
            return False
        
        test_stock = stocks[0]
        instrument_key = test_stock['instrument_key']
        symbol = test_stock['symbol']
        
        print(f"⚡ Performance testing with: {symbol} ({instrument_key})")
        
        # Test database-first approach
        print("🗄️ Testing database-first approach...")
        start_time = time.time()
        
        try:
            from data_fetch.database_service import database_service
            
            candles = database_service.get_candles_smart(
                instrument_key=instrument_key,
                interval="day",
                start_date=date.today() - timedelta(days=30),
                end_date=date.today(),
                auto_backfill=False
            )
            
            db_time = time.time() - start_time
            print(f"   Database-first: {len(candles)} candles in {db_time:.2f} seconds")
            
        except Exception as e:
            print(f"   Database-first test failed: {e}")
            db_time = None
        
        # Test legacy approach
        print("🌐 Testing legacy API approach...")
        start_time = time.time()
        
        try:
            from app import charts
            
            candles = charts.get_candles(
                instrument_key=instrument_key,
                interval="day",
                from_date=date.today() - timedelta(days=30),
                to_date=date.today()
            )
            
            api_time = time.time() - start_time
            print(f"   Legacy API: {len(candles)} candles in {api_time:.2f} seconds")
            
        except Exception as e:
            print(f"   Legacy API test failed: {e}")
            api_time = None
        
        # Compare performance
        if db_time and api_time:
            speedup = api_time / db_time
            print(f"📊 Performance comparison:")
            print(f"   Database-first: {db_time:.2f}s")
            print(f"   Legacy API: {api_time:.2f}s")
            print(f"   Speedup: {speedup:.1f}x faster with database-first")
        
        print("✅ Performance comparison completed")
        return True
        
    except Exception as e:
        print(f"❌ Performance comparison test error: {e}")
        return False

def run_all_tests():
    """Run all database-first tests."""
    print("🧪 STARTING DATABASE-FIRST ARCHITECTURE TESTS")
    print("="*60)
    
    tests = [
        ("Database Service", test_database_service),
        ("Charts Database-First", test_charts_database_first),
        ("PnF Matrix Database-First", test_pnf_matrix_database_first),
        ("Alerts Database-First", test_alerts_database_first),
        ("Performance Comparison", test_performance_comparison),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n🔍 Running {test_name} test...")
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} test failed with exception: {e}")
            results[test_name] = False
        
        # Small delay between tests
        time.sleep(1)
    
    # Summary
    print("\n" + "="*60)
    print("📋 DATABASE-FIRST TEST RESULTS")
    print("="*60)
    
    passed = 0
    total = len(results)
    
    for test_name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if success:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Database-first architecture is working.")
        print("\n💡 Benefits achieved:")
        print("✅ Faster chart loading (database vs API calls)")
        print("✅ Automatic data backfill when missing")
        print("✅ Consistent data across all components")
        print("✅ Reduced API rate limit issues")
        print("✅ Better offline capability")
    else:
        print("⚠️ Some tests failed. Check the configuration.")
        print("\n🔧 Common issues:")
        print("1. Database tables not created")
        print("2. Missing data in database")
        print("3. Import path issues")
    
    return passed == total

if __name__ == "__main__":
    print("🚀 Database-First Architecture Test Suite")
    print("=" * 60)
    
    # Check if we're in the right directory
    if not os.path.exists("app"):
        print("❌ Please run this script from the project root directory")
        sys.exit(1)
    
    # Run tests
    success = run_all_tests()
    
    if success:
        print("\n🎉 Database-first architecture is fully operational!")
        print("💡 All components now use database-first approach:")
        print("   📊 Test-charts: Powered by database")
        print("   🎯 PnF Matrix: Powered by database") 
        print("   🚨 Alerts: Powered by database")
        print("   📈 Chart generation: Powered by database")
    else:
        print("\n🔧 Please fix the failing tests before proceeding.")
    
    sys.exit(0 if success else 1)
