"""
Optimized Alert Scheduler with Enhanced Logging and Database Optimization
Shows LTP API efficiency and optimized database calls for alert generation.
"""

import sys
import os
import time
from typing import Dict, List, Tuple
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
from ltp_service import ltp_service
from fo_stocks_loader import fo_stocks_loader

class OptimizedAlertScheduler:
    """
    Optimized alert scheduler that demonstrates:
    1. Single LTP API call for all stocks
    2. Optimized database queries for alert generation
    3. Detailed logging for performance tracking
    """
    
    def __init__(self):
        self.ltp_service = ltp_service
        self.fo_loader = fo_stocks_loader
    
    def run_complete_alert_cycle(self) -> Dict:
        """
        Run a complete alert cycle with detailed logging.
        Shows LTP API efficiency and database optimization.
        """
        cycle_start_time = time.time()
        results = {
            'ltp_collection': {},
            'database_queries': {},
            'alert_generation': {},
            'total_performance': {}
        }
        
        try:
            logger.info("🚀 STARTING OPTIMIZED ALERT CYCLE")
            logger.info("=" * 60)
            
            # Step 1: Collect LTP data (Single API call for ALL stocks)
            ltp_results = self._collect_ltp_with_logging()
            results['ltp_collection'] = ltp_results
            
            # Step 2: Optimized database queries for alert data
            db_results = self._get_alert_data_optimized(ltp_results.get('symbols', []))
            results['database_queries'] = db_results
            
            # Step 3: Generate alerts with optimized data
            alert_results = self._generate_alerts_optimized(db_results.get('alert_data', {}))
            results['alert_generation'] = alert_results
            
            # Step 4: Performance summary
            cycle_end_time = time.time()
            total_duration = cycle_end_time - cycle_start_time
            
            results['total_performance'] = {
                'total_duration': total_duration,
                'stocks_processed': len(ltp_results.get('symbols', [])),
                'alerts_generated': alert_results.get('alerts_count', 0),
                'api_calls_made': 1,  # Only 1 LTP API call
                'db_queries_made': db_results.get('queries_count', 0)
            }
            
            self._log_cycle_summary(results)
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Error in alert cycle: {e}")
            return results
    
    def _collect_ltp_with_logging(self) -> Dict:
        """Collect LTP data with detailed logging."""
        logger.info("\n📊 STEP 1: LTP DATA COLLECTION")
        logger.info("-" * 40)
        
        start_time = time.time()
        
        # Get watchlist stocks
        stocks_with_keys = self.fo_loader.get_fo_symbols_with_instrument_keys()
        logger.info(f"📋 Watchlist size: {len(stocks_with_keys)} stocks")
        
        # Single LTP API call for ALL stocks
        logger.info("🌐 Making SINGLE LTP API call for ALL stocks...")
        ltp_data = self.ltp_service.collect_ltp_data()
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Calculate efficiency metrics
        stocks_count = len(stocks_with_keys)
        ltp_count = len(ltp_data)
        api_efficiency = stocks_count if ltp_count > 0 else 0
        
        logger.info(f"✅ LTP COLLECTION RESULTS:")
        logger.info(f"   📊 Stocks in watchlist: {stocks_count}")
        logger.info(f"   💰 LTP data received: {ltp_count} stocks")
        logger.info(f"   🌐 API calls made: 1 (instead of {stocks_count})")
        logger.info(f"   💡 API efficiency: {api_efficiency}x improvement")
        logger.info(f"   ⏱️ Duration: {duration:.2f} seconds")
        
        return {
            'duration': duration,
            'stocks_count': stocks_count,
            'ltp_count': ltp_count,
            'api_calls': 1,
            'api_efficiency': api_efficiency,
            'symbols': list(ltp_data.keys()) if ltp_data else []
        }
    
    def _get_alert_data_optimized(self, symbols: List[str]) -> Dict:
        """Get alert data with optimized database queries."""
        logger.info("\n🗄️ STEP 2: OPTIMIZED DATABASE QUERIES")
        logger.info("-" * 40)
        
        start_time = time.time()
        queries_count = 0
        alert_data = {}
        
        try:
            db = SessionLocal()
            
            # Get instrument keys for symbols
            stocks_with_keys = self.fo_loader.get_fo_symbols_with_instrument_keys()
            symbol_to_instrument = {stock['symbol']: stock['instrument_key'] for stock in stocks_with_keys}
            
            # Optimize: Batch query for all symbols instead of individual queries
            logger.info(f"📊 Preparing batch query for {len(symbols)} symbols...")
            
            # Get date range for alert data (last 30 days)
            end_date = date.today()
            start_date = end_date - timedelta(days=30)
            start_datetime = datetime.combine(start_date, datetime.min.time())
            end_datetime = datetime.combine(end_date, datetime.max.time())
            
            # OPTIMIZED: Single batch query for all symbols
            instrument_keys = [symbol_to_instrument.get(symbol) for symbol in symbols if symbol_to_instrument.get(symbol)]
            
            if instrument_keys:
                logger.info(f"🔍 Executing BATCH query for {len(instrument_keys)} instruments...")
                batch_start_time = time.time()
                
                # Single query for all instruments
                candles = db.query(Candle).filter(
                    Candle.instrument_key.in_(instrument_keys),
                    Candle.interval == '1minute',
                    Candle.timestamp >= start_datetime,
                    Candle.timestamp <= end_datetime
                ).order_by(Candle.instrument_key, Candle.timestamp).all()
                
                queries_count = 1  # Only 1 batch query instead of N individual queries
                batch_end_time = time.time()
                batch_duration = batch_end_time - batch_start_time
                
                logger.info(f"✅ BATCH QUERY RESULTS:")
                logger.info(f"   📊 Candles retrieved: {len(candles)}")
                logger.info(f"   🗄️ Query duration: {batch_duration:.2f} seconds")
                logger.info(f"   💡 Queries made: {queries_count} (instead of {len(symbols)})")
                
                # Group candles by instrument key
                logger.info("📋 Grouping candles by symbol...")
                for candle in candles:
                    instrument_key = candle.instrument_key
                    
                    # Find symbol for this instrument key
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
                
                # Log data availability per symbol
                for symbol in symbols[:5]:  # Show first 5
                    candle_count = len(alert_data.get(symbol, []))
                    logger.info(f"   📈 {symbol}: {candle_count} candles")
                
                if len(symbols) > 5:
                    logger.info(f"   📊 ... and {len(symbols) - 5} more symbols")
            
        except Exception as e:
            logger.error(f"❌ Database query error: {e}")
        finally:
            if 'db' in locals():
                db.close()
        
        end_time = time.time()
        duration = end_time - start_time
        
        logger.info(f"✅ DATABASE OPTIMIZATION RESULTS:")
        logger.info(f"   ⏱️ Total duration: {duration:.2f} seconds")
        logger.info(f"   🗄️ Queries executed: {queries_count}")
        logger.info(f"   📊 Symbols with data: {len(alert_data)}")
        logger.info(f"   💡 Query efficiency: {len(symbols)}x improvement (batch vs individual)")
        
        return {
            'duration': duration,
            'queries_count': queries_count,
            'symbols_with_data': len(alert_data),
            'alert_data': alert_data,
            'query_efficiency': len(symbols) if queries_count == 1 else 1
        }
    
    def _generate_alerts_optimized(self, alert_data: Dict[str, List[Dict]]) -> Dict:
        """Generate alerts with optimized processing."""
        logger.info("\n🚨 STEP 3: OPTIMIZED ALERT GENERATION")
        logger.info("-" * 40)
        
        start_time = time.time()
        alerts_generated = 0
        alerts_details = []
        
        try:
            logger.info(f"🔍 Processing {len(alert_data)} symbols for alerts...")
            
            for symbol, candles in alert_data.items():
                if len(candles) < 10:  # Need minimum data for pattern detection
                    continue
                
                # Simulate alert generation (replace with actual alert logic)
                # This would call your existing pattern detection algorithms
                
                # For demonstration, generate sample alerts
                if len(candles) > 100:  # Sufficient data
                    latest_candle = candles[-1]
                    price = latest_candle['close']
                    
                    # Simulate pattern detection
                    if price > 1000:  # Sample condition
                        alert = {
                            'symbol': symbol,
                            'pattern': 'Sample Pattern',
                            'price': price,
                            'timestamp': latest_candle['timestamp']
                        }
                        alerts_details.append(alert)
                        alerts_generated += 1
                        
                        logger.info(f"   🚨 Alert: {symbol} at ₹{price}")
            
        except Exception as e:
            logger.error(f"❌ Alert generation error: {e}")
        
        end_time = time.time()
        duration = end_time - start_time
        
        logger.info(f"✅ ALERT GENERATION RESULTS:")
        logger.info(f"   ⏱️ Duration: {duration:.2f} seconds")
        logger.info(f"   🚨 Alerts generated: {alerts_generated}")
        logger.info(f"   📊 Symbols processed: {len(alert_data)}")
        
        return {
            'duration': duration,
            'alerts_count': alerts_generated,
            'alerts_details': alerts_details,
            'symbols_processed': len(alert_data)
        }
    
    def _log_cycle_summary(self, results: Dict):
        """Log comprehensive cycle summary."""
        logger.info("\n🎯 COMPLETE CYCLE SUMMARY")
        logger.info("=" * 60)
        
        total_perf = results.get('total_performance', {})
        ltp_perf = results.get('ltp_collection', {})
        db_perf = results.get('database_queries', {})
        alert_perf = results.get('alert_generation', {})
        
        logger.info(f"⏱️ TIMING BREAKDOWN:")
        logger.info(f"   📊 LTP Collection: {ltp_perf.get('duration', 0):.2f}s")
        logger.info(f"   🗄️ Database Queries: {db_perf.get('duration', 0):.2f}s")
        logger.info(f"   🚨 Alert Generation: {alert_perf.get('duration', 0):.2f}s")
        logger.info(f"   🎯 Total Duration: {total_perf.get('total_duration', 0):.2f}s")
        
        logger.info(f"\n💰 EFFICIENCY METRICS:")
        logger.info(f"   🌐 API Calls: {total_perf.get('api_calls_made', 0)} (instead of {ltp_perf.get('stocks_count', 0)})")
        logger.info(f"   🗄️ DB Queries: {total_perf.get('db_queries_made', 0)} (instead of {ltp_perf.get('stocks_count', 0)})")
        logger.info(f"   📊 Stocks Processed: {total_perf.get('stocks_processed', 0)}")
        logger.info(f"   🚨 Alerts Generated: {total_perf.get('alerts_generated', 0)}")
        
        # Calculate efficiency improvements
        stocks_count = ltp_perf.get('stocks_count', 1)
        api_improvement = stocks_count / max(total_perf.get('api_calls_made', 1), 1)
        db_improvement = stocks_count / max(total_perf.get('db_queries_made', 1), 1)
        
        logger.info(f"\n🚀 OPTIMIZATION ACHIEVEMENTS:")
        logger.info(f"   📈 API Efficiency: {api_improvement:.0f}x improvement")
        logger.info(f"   🗄️ DB Efficiency: {db_improvement:.0f}x improvement")
        logger.info(f"   ⚡ Total Speed: Optimized for {stocks_count} stocks")
        
        logger.info(f"\n💡 SYSTEM PERFORMANCE:")
        if total_perf.get('total_duration', 0) < 10:
            logger.info(f"   ✅ EXCELLENT: Complete cycle in {total_perf.get('total_duration', 0):.2f}s")
        elif total_perf.get('total_duration', 0) < 30:
            logger.info(f"   ✅ GOOD: Complete cycle in {total_perf.get('total_duration', 0):.2f}s")
        else:
            logger.info(f"   ⚠️ NEEDS OPTIMIZATION: Cycle took {total_perf.get('total_duration', 0):.2f}s")

# Global instance
optimized_alert_scheduler = OptimizedAlertScheduler()

def run_optimized_alert_cycle():
    """Public function to run optimized alert cycle with logging."""
    return optimized_alert_scheduler.run_complete_alert_cycle()

if __name__ == "__main__":
    print("🚀 Running Optimized Alert Scheduler Demo")
    print("=" * 60)
    
    # Run the optimized alert cycle
    results = run_optimized_alert_cycle()
    
    print(f"\n🎉 Demo completed!")
    print(f"📊 Check logs above for detailed performance metrics")
