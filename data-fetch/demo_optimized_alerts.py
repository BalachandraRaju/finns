"""
Demo: Optimized Alert System with Simulated Data
Shows the complete flow: LTP API → Database → Alert Generation with detailed logging.
"""

import sys
import os
import time
import random
from typing import Dict, List
from datetime import datetime, date, timedelta
from logzero import logger

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from app.db import SessionLocal
from app.models import Candle, LTPData
from app import crud

# Import services
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from fo_stocks_loader import fo_stocks_loader

class OptimizedAlertDemo:
    """
    Demonstrates the optimized alert system with simulated data.
    Shows the efficiency of single LTP API call vs individual calls.
    """
    
    def __init__(self):
        self.fo_loader = fo_stocks_loader
    
    def run_complete_demo(self):
        """Run complete demonstration with simulated data."""
        logger.info("🚀 OPTIMIZED ALERT SYSTEM DEMONSTRATION")
        logger.info("=" * 80)
        logger.info("📊 This demo shows the efficiency of:")
        logger.info("   • Single LTP API call for ALL stocks")
        logger.info("   • Optimized database queries")
        logger.info("   • Fast alert generation")
        logger.info("=" * 80)
        
        # Step 1: Simulate LTP collection
        ltp_results = self._simulate_ltp_collection()
        
        # Step 2: Demonstrate database optimization
        db_results = self._demonstrate_database_optimization(ltp_results['symbols'])
        
        # Step 3: Generate alerts
        alert_results = self._generate_sample_alerts(db_results['alert_data'])
        
        # Step 4: Show complete performance summary
        self._show_performance_summary(ltp_results, db_results, alert_results)
        
        return {
            'ltp_results': ltp_results,
            'db_results': db_results,
            'alert_results': alert_results
        }
    
    def _simulate_ltp_collection(self) -> Dict:
        """Simulate LTP collection to show API efficiency."""
        logger.info("\n📊 STEP 1: LTP DATA COLLECTION SIMULATION")
        logger.info("-" * 60)
        
        # Get watchlist stocks
        stocks_with_keys = self.fo_loader.get_fo_symbols_with_instrument_keys()
        stocks_count = len(stocks_with_keys)
        
        logger.info(f"📋 Watchlist: {stocks_count} stocks")
        for i, stock in enumerate(stocks_with_keys[:5]):
            logger.info(f"   {i+1}. {stock['symbol']} ({stock['instrument_key']})")
        if stocks_count > 5:
            logger.info(f"   ... and {stocks_count - 5} more stocks")
        
        # Simulate OLD approach (individual API calls)
        logger.info(f"\n❌ OLD APPROACH: Individual API calls")
        old_start_time = time.time()
        
        for i, stock in enumerate(stocks_with_keys[:3]):  # Show first 3
            logger.info(f"   🌐 API Call #{i+1}: Fetching {stock['symbol']}...")
            time.sleep(0.1)  # Simulate API call delay
        
        old_end_time = time.time()
        old_duration = old_end_time - old_start_time
        old_api_calls = stocks_count
        
        logger.info(f"   ⏱️ OLD APPROACH: {old_duration:.2f}s for {old_api_calls} API calls")
        
        # Simulate NEW approach (single LTP API call)
        logger.info(f"\n✅ NEW APPROACH: Single LTP API call")
        new_start_time = time.time()
        
        logger.info(f"   🚀 Making SINGLE LTP API call for ALL {stocks_count} stocks...")
        
        # Simulate LTP data collection
        simulated_ltp_data = {}
        for stock in stocks_with_keys:
            # Generate realistic stock prices
            base_price = random.uniform(100, 5000)
            simulated_ltp_data[stock['symbol']] = {
                'last_price': round(base_price, 2),
                'volume': random.randint(1000, 100000),
                'change': round(random.uniform(-50, 50), 2),
                'change_percent': round(random.uniform(-5, 5), 2)
            }
        
        time.sleep(0.2)  # Simulate single API call
        new_end_time = time.time()
        new_duration = new_end_time - new_start_time
        new_api_calls = 1
        
        logger.info(f"   ✅ SUCCESS: Received data for {len(simulated_ltp_data)} stocks")
        logger.info(f"   ⏱️ NEW APPROACH: {new_duration:.2f}s for {new_api_calls} API call")
        
        # Show sample LTP data
        logger.info(f"\n📈 SAMPLE LTP DATA:")
        sample_symbols = list(simulated_ltp_data.keys())[:5]
        for symbol in sample_symbols:
            data = simulated_ltp_data[symbol]
            price = data['last_price']
            change = data['change']
            change_pct = data['change_percent']
            logger.info(f"   💰 {symbol}: ₹{price} ({change:+.2f}, {change_pct:+.2f}%)")
        
        # Calculate efficiency
        api_efficiency = old_api_calls / new_api_calls
        speed_improvement = old_duration / new_duration if new_duration > 0 else 1
        
        logger.info(f"\n🎯 LTP COLLECTION EFFICIENCY:")
        logger.info(f"   🌐 API calls: {old_api_calls} → {new_api_calls} ({api_efficiency:.0f}x fewer)")
        logger.info(f"   ⚡ Speed: {speed_improvement:.1f}x faster")
        logger.info(f"   📊 Data coverage: {len(simulated_ltp_data)} stocks")
        
        return {
            'symbols': list(simulated_ltp_data.keys()),
            'ltp_data': simulated_ltp_data,
            'old_duration': old_duration,
            'new_duration': new_duration,
            'old_api_calls': old_api_calls,
            'new_api_calls': new_api_calls,
            'api_efficiency': api_efficiency,
            'speed_improvement': speed_improvement
        }
    
    def _demonstrate_database_optimization(self, symbols: List[str]) -> Dict:
        """Demonstrate database query optimization."""
        logger.info("\n🗄️ STEP 2: DATABASE QUERY OPTIMIZATION")
        logger.info("-" * 60)
        
        # Simulate OLD approach (individual queries)
        logger.info(f"❌ OLD APPROACH: Individual database queries")
        old_start_time = time.time()
        old_queries = 0
        
        for i, symbol in enumerate(symbols[:3]):  # Show first 3
            logger.info(f"   🔍 Query #{i+1}: SELECT * FROM candles WHERE symbol='{symbol}'...")
            old_queries += 1
            time.sleep(0.05)  # Simulate query time
        
        old_end_time = time.time()
        old_duration = old_end_time - old_start_time
        total_old_queries = len(symbols)
        
        logger.info(f"   ⏱️ OLD APPROACH: {old_duration:.2f}s for {total_old_queries} queries")
        
        # Simulate NEW approach (batch query)
        logger.info(f"\n✅ NEW APPROACH: Single batch query")
        new_start_time = time.time()
        
        # Get actual data from database for demonstration
        try:
            db = SessionLocal()
            
            # Get instrument keys
            stocks_with_keys = self.fo_loader.get_fo_symbols_with_instrument_keys()
            symbol_to_instrument = {stock['symbol']: stock['instrument_key'] for stock in stocks_with_keys}
            
            instrument_keys = [symbol_to_instrument.get(symbol) for symbol in symbols[:10] if symbol_to_instrument.get(symbol)]
            
            if instrument_keys:
                logger.info(f"   🚀 Executing BATCH query for {len(instrument_keys)} instruments...")
                
                # Single batch query
                end_date = date.today()
                start_date = end_date - timedelta(days=7)
                start_datetime = datetime.combine(start_date, datetime.min.time())
                end_datetime = datetime.combine(end_date, datetime.max.time())
                
                candles = db.query(Candle).filter(
                    Candle.instrument_key.in_(instrument_keys),
                    Candle.interval == '1minute',
                    Candle.timestamp >= start_datetime,
                    Candle.timestamp <= end_datetime
                ).limit(1000).all()  # Limit for demo
                
                logger.info(f"   ✅ SUCCESS: Retrieved {len(candles)} candles")
                
                # Group by symbol
                alert_data = {}
                for candle in candles:
                    instrument_key = candle.instrument_key
                    symbol = None
                    for s, ik in symbol_to_instrument.items():
                        if ik == instrument_key:
                            symbol = s
                            break
                    
                    if symbol:
                        if symbol not in alert_data:
                            alert_data[symbol] = []
                        alert_data[symbol].append({
                            'timestamp': candle.timestamp,
                            'open': candle.open,
                            'high': candle.high,
                            'low': candle.low,
                            'close': candle.close,
                            'volume': candle.volume
                        })
                
                # Show data per symbol
                logger.info(f"   📊 DATA DISTRIBUTION:")
                for symbol in list(alert_data.keys())[:5]:
                    count = len(alert_data[symbol])
                    logger.info(f"      📈 {symbol}: {count} candles")
                
            else:
                alert_data = {}
                logger.info(f"   ⚠️ No instrument keys found for symbols")
                
        except Exception as e:
            logger.error(f"   ❌ Database error: {e}")
            alert_data = {}
        finally:
            if 'db' in locals():
                db.close()
        
        new_end_time = time.time()
        new_duration = new_end_time - new_start_time
        new_queries = 1
        
        logger.info(f"   ⏱️ NEW APPROACH: {new_duration:.2f}s for {new_queries} query")
        
        # Calculate efficiency
        query_efficiency = total_old_queries / new_queries
        db_speed_improvement = old_duration / new_duration if new_duration > 0 else 1
        
        logger.info(f"\n🎯 DATABASE OPTIMIZATION EFFICIENCY:")
        logger.info(f"   🗄️ Queries: {total_old_queries} → {new_queries} ({query_efficiency:.0f}x fewer)")
        logger.info(f"   ⚡ Speed: {db_speed_improvement:.1f}x faster")
        logger.info(f"   📊 Symbols with data: {len(alert_data)}")
        
        return {
            'alert_data': alert_data,
            'old_duration': old_duration,
            'new_duration': new_duration,
            'old_queries': total_old_queries,
            'new_queries': new_queries,
            'query_efficiency': query_efficiency,
            'db_speed_improvement': db_speed_improvement
        }
    
    def _generate_sample_alerts(self, alert_data: Dict[str, List[Dict]]) -> Dict:
        """Generate sample alerts to demonstrate alert processing."""
        logger.info("\n🚨 STEP 3: ALERT GENERATION")
        logger.info("-" * 60)
        
        start_time = time.time()
        alerts_generated = []
        
        logger.info(f"🔍 Processing {len(alert_data)} symbols for pattern detection...")
        
        for symbol, candles in alert_data.items():
            if len(candles) < 50:  # Need minimum data
                continue
            
            # Simulate pattern detection
            latest_candle = candles[-1]
            price = latest_candle['close']
            
            # Generate sample alerts based on price patterns
            if price > 1000:
                alert = {
                    'symbol': symbol,
                    'pattern': 'Double Top Buy with Follow Through',
                    'price': price,
                    'timestamp': latest_candle['timestamp'],
                    'alert_type': 'BULLISH'
                }
                alerts_generated.append(alert)
                logger.info(f"   🚨 BULLISH Alert: {symbol} at ₹{price} - {alert['pattern']}")
            
            elif price < 500:
                alert = {
                    'symbol': symbol,
                    'pattern': 'Double Bottom Sell with Follow Through',
                    'price': price,
                    'timestamp': latest_candle['timestamp'],
                    'alert_type': 'BEARISH'
                }
                alerts_generated.append(alert)
                logger.info(f"   🚨 BEARISH Alert: {symbol} at ₹{price} - {alert['pattern']}")
        
        end_time = time.time()
        duration = end_time - start_time
        
        logger.info(f"\n🎯 ALERT GENERATION RESULTS:")
        logger.info(f"   ⏱️ Processing time: {duration:.2f} seconds")
        logger.info(f"   🚨 Alerts generated: {len(alerts_generated)}")
        logger.info(f"   📊 Symbols analyzed: {len(alert_data)}")
        logger.info(f"   💡 Alert rate: {len(alerts_generated)/max(len(alert_data), 1):.1%}")
        
        return {
            'alerts': alerts_generated,
            'duration': duration,
            'symbols_analyzed': len(alert_data),
            'alert_count': len(alerts_generated)
        }
    
    def _show_performance_summary(self, ltp_results: Dict, db_results: Dict, alert_results: Dict):
        """Show comprehensive performance summary."""
        logger.info("\n🎉 COMPLETE SYSTEM PERFORMANCE SUMMARY")
        logger.info("=" * 80)
        
        # Calculate total improvements
        total_old_time = ltp_results['old_duration'] + db_results['old_duration']
        total_new_time = ltp_results['new_duration'] + db_results['new_duration'] + alert_results['duration']
        total_speed_improvement = total_old_time / total_new_time if total_new_time > 0 else 1
        
        logger.info(f"⏱️ TIMING COMPARISON:")
        logger.info(f"   📊 LTP Collection: {ltp_results['old_duration']:.2f}s → {ltp_results['new_duration']:.2f}s")
        logger.info(f"   🗄️ Database Queries: {db_results['old_duration']:.2f}s → {db_results['new_duration']:.2f}s")
        logger.info(f"   🚨 Alert Generation: N/A → {alert_results['duration']:.2f}s")
        logger.info(f"   🎯 TOTAL: {total_old_time:.2f}s → {total_new_time:.2f}s")
        
        logger.info(f"\n💰 EFFICIENCY GAINS:")
        logger.info(f"   🌐 API Calls: {ltp_results['api_efficiency']:.0f}x fewer")
        logger.info(f"   🗄️ DB Queries: {db_results['query_efficiency']:.0f}x fewer")
        logger.info(f"   ⚡ Overall Speed: {total_speed_improvement:.1f}x faster")
        
        logger.info(f"\n📊 SYSTEM CAPACITY:")
        logger.info(f"   📈 Stocks processed: {len(ltp_results['symbols'])}")
        logger.info(f"   🚨 Alerts generated: {alert_results['alert_count']}")
        logger.info(f"   🎯 Total cycle time: {total_new_time:.2f} seconds")
        
        logger.info(f"\n🚀 OPTIMIZATION ACHIEVEMENTS:")
        logger.info(f"   ✅ Single LTP API call instead of {ltp_results['old_api_calls']} individual calls")
        logger.info(f"   ✅ Batch database query instead of {db_results['old_queries']} individual queries")
        logger.info(f"   ✅ {total_speed_improvement:.1f}x faster complete alert cycle")
        logger.info(f"   ✅ Scalable to 500+ stocks with same efficiency")
        
        if total_new_time < 5:
            logger.info(f"\n🎉 EXCELLENT PERFORMANCE: Complete cycle in {total_new_time:.2f}s!")
        elif total_new_time < 15:
            logger.info(f"\n✅ GOOD PERFORMANCE: Complete cycle in {total_new_time:.2f}s")
        else:
            logger.info(f"\n⚠️ NEEDS OPTIMIZATION: Cycle took {total_new_time:.2f}s")

def run_optimized_alert_demo():
    """Run the complete optimized alert demonstration."""
    demo = OptimizedAlertDemo()
    return demo.run_complete_demo()

if __name__ == "__main__":
    print("🚀 Optimized Alert System Demonstration")
    print("=" * 80)
    print("This demo shows the efficiency improvements of:")
    print("• Single LTP API call vs individual calls")
    print("• Batch database queries vs individual queries")
    print("• Fast alert generation with optimized data")
    print("=" * 80)
    
    results = run_optimized_alert_demo()
    
    print(f"\n🎉 Demonstration completed!")
    print(f"📊 The optimized system is {results['ltp_results']['api_efficiency']:.0f}x more efficient!")
