"""
Quick API test - verify backtest works with minimal data
"""
import requests
import json
from datetime import datetime, timedelta

# Test configuration
BASE_URL = "http://localhost:8000"

def test_backtest_api():
    """Test the backtest API with minimal parameters"""
    
    print("="*80)
    print("TESTING PKSCREENER BACKTEST API")
    print("="*80)
    
    # Use a single day and limited stocks for speed
    end_date = datetime(2025, 10, 17, 15, 30)
    start_date = end_date  # Same day for speed
    
    # Test payload - only 2 scanners for speed
    payload = {
        "instrument_keys": [],  # Empty = all stocks (will be slow)
        "symbols": ["RELIANCE", "TCS", "INFY", "SBIN", "HDFC"],  # Just 5 stocks
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "scanner_ids": [1, 23]  # Only test scanners 1 and 23 (proven to work)
    }
    
    print(f"\nTest Configuration:")
    print(f"  URL: {BASE_URL}/api/pkscreener/backtest")
    print(f"  Date: {start_date.date()}")
    print(f"  Stocks: {payload['symbols']}")
    print(f"  Scanners: {payload['scanner_ids']}")
    print()
    
    print("Sending request...")
    try:
        response = requests.post(
            f"{BASE_URL}/api/pkscreener/backtest",
            json=payload,
            timeout=120  # 2 minute timeout
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            print("\n" + "="*80)
            print("RESPONSE")
            print("="*80)
            
            if data.get("status") == "success":
                print("✅ SUCCESS!")
                
                # Print summary
                print("\nSummary:")
                for scanner_id, summary in data.get("summary", {}).items():
                    print(f"\n  Scanner #{scanner_id}:")
                    print(f"    Total Triggers: {summary.get('total_triggers', 0)}")
                    print(f"    Success Rate: {summary.get('success_rate_pct', 0)}%")
                    print(f"    Avg 3min Return: {summary.get('avg_returns', {}).get('3min', 0):.2f}%")
                    print(f"    Avg 5min Return: {summary.get('avg_returns', {}).get('5min', 0):.2f}%")
                
                # Print first few results
                print("\nSample Results:")
                for scanner_id, results in data.get("results", {}).items():
                    print(f"\n  Scanner #{scanner_id}: {len(results)} alerts")
                    for i, result in enumerate(results[:3], 1):
                        print(f"    {i}. {result.get('symbol')} @ {result.get('trigger_time')} - "
                              f"₹{result.get('trigger_price', 0):.2f} "
                              f"(3min: {result.get('return_3min_pct', 0):+.2f}%)")
                
                print("\n✅ API TEST PASSED!")
                
            else:
                print(f"❌ API returned error: {data.get('message', 'Unknown error')}")
                
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"Response: {response.text[:500]}")
            
    except requests.exceptions.Timeout:
        print("❌ Request timed out (> 2 minutes)")
        print("Backtest is taking too long - need to optimize!")
        
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    print("\n⚠️  Make sure the server is running:")
    print("   uvicorn app.main:app --reload")
    print()
    input("Press Enter to continue...")
    
    test_backtest_api()

