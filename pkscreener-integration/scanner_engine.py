"""
Scanner Engine
Runs PKScreener strategies on all watchlist stocks
"""
import sys
import os

# Add parent directory to path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

# Add current directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

import pandas as pd
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging
from sqlalchemy.orm import Session

from app.db import get_db, engine
from app.models import Candle
from models import PKScreenerResult
from scanner_strategies import ScannerStrategies
from technical_indicators import TechnicalIndicators

logger = logging.getLogger(__name__)


class ScannerEngine:
    """
    Main engine to run PKScreener strategies on watchlist stocks
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.strategies = ScannerStrategies()
        self.ti = TechnicalIndicators()
        
        # Load watchlist
        self.watchlist = self._load_watchlist()
        logger.info(f"Loaded {len(self.watchlist)} stocks from watchlist")
    
    def _load_watchlist(self) -> List[Dict]:
        """Load F&O stocks from nse_fo_stock_symbols.txt"""
        try:
            watchlist_file = os.path.join(
                os.path.dirname(__file__), 
                '..', 
                'nse_fo_stock_symbols.txt'
            )
            
            stocks = []
            with open(watchlist_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    
                    parts = line.split(',')
                    if len(parts) >= 2:
                        symbol = parts[0].strip()
                        security_id = parts[1].strip()
                        instrument_key = f"DHAN_{security_id}"
                        
                        stocks.append({
                            'symbol': symbol,
                            'security_id': security_id,
                            'instrument_key': instrument_key
                        })
            
            return stocks
            
        except Exception as e:
            logger.error(f"Error loading watchlist: {e}")
            return []
    
    def get_stock_data(self, instrument_key: str, lookback_candles: int = 300) -> Optional[pd.DataFrame]:
        """
        Fetch stock data from database
        Returns DataFrame with most recent candle first (index 0)
        """
        try:
            # Get candles from database
            candles = self.db.query(Candle).filter(
                Candle.instrument_key == instrument_key,
                Candle.interval == '1minute'
            ).order_by(Candle.timestamp.desc()).limit(lookback_candles).all()
            
            if not candles or len(candles) < 50:
                logger.warning(f"Insufficient data for {instrument_key}: {len(candles) if candles else 0} candles")
                return None
            
            # Convert to DataFrame
            data = []
            for candle in candles:
                data.append({
                    'timestamp': candle.timestamp,
                    'open': candle.open,
                    'high': candle.high,
                    'low': candle.low,
                    'close': candle.close,
                    'volume': candle.volume
                })
            
            df = pd.DataFrame(data)
            
            # Data is already in descending order (most recent first)
            return df
            
        except Exception as e:
            logger.error(f"Error fetching data for {instrument_key}: {e}")
            return None
    
    def run_scanner(self, scanner_id: int, stock: Dict, df: pd.DataFrame) -> Optional[PKScreenerResult]:
        """
        Run a specific scanner on a stock
        Returns PKScreenerResult if scanner passes, None otherwise
        """
        try:
            passed = False
            metrics = {}
            
            # Run the appropriate scanner
            if scanner_id == 1:
                passed, metrics = self.strategies.scanner_1_volume_momentum_breakout_atr(df)
            elif scanner_id == 2:
                passed, metrics = self.strategies.scanner_2_volume_momentum_atr(df)
            elif scanner_id == 3:
                passed, metrics = self.strategies.scanner_3_volume_momentum(df)
            elif scanner_id == 4:
                passed, metrics = self.strategies.scanner_4_volume_atr(df)
            elif scanner_id == 5:
                passed, metrics = self.strategies.scanner_5_volume_bidask(df)
            elif scanner_id == 6:
                passed, metrics = self.strategies.scanner_6_volume_atr_trailing(df)
            elif scanner_id == 7:
                passed, metrics = self.strategies.scanner_7_volume_trailing(df)
            elif scanner_id == 8:
                passed, metrics = self.strategies.scanner_8_momentum_atr(df)
            elif scanner_id == 9:
                passed, metrics = self.strategies.scanner_9_momentum_trailing(df)
            elif scanner_id == 10:
                passed, metrics = self.strategies.scanner_10_atr_trailing(df)
            elif scanner_id == 11:
                passed, metrics = self.strategies.scanner_11_ttm_squeeze_rsi(df)
            elif scanner_id == 12:
                passed, metrics = self.strategies.scanner_12_volume_momentum_breakout_atr_rsi(df)
            elif scanner_id == 13:
                passed, metrics = self.strategies.scanner_13_volume_atr_rsi(df)
            elif scanner_id == 14:
                passed, metrics = self.strategies.scanner_14_vcp_chart_patterns_ma_support(df)
            elif scanner_id == 15:
                passed, metrics = self.strategies.scanner_15_vcp_patterns_ma(df)
            elif scanner_id == 16:
                passed, metrics = self.strategies.scanner_16_breakout_vcp_patterns_ma(df)
            elif scanner_id == 17:
                passed, metrics = self.strategies.scanner_17_trailing_vcp(df)
            elif scanner_id == 18:
                passed, metrics = self.strategies.scanner_18_vcp_trailing(df)
            elif scanner_id == 19:
                passed, metrics = self.strategies.scanner_19_nifty_vcp_trailing(df)
            elif scanner_id == 20:
                passed, metrics = self.strategies.scanner_20_comprehensive(df)
            elif scanner_id == 21:
                passed, metrics = self.strategies.scanner_21_bullcross_ma_fair_value(df)
            else:
                logger.warning(f"Unknown scanner_id: {scanner_id}")
                return None
            
            if not passed:
                return None
            
            # Create result object
            result = PKScreenerResult(
                scanner_id=scanner_id,
                scanner_name=metrics.get('scanner_name', f'Scanner #{scanner_id}'),
                instrument_key=stock['instrument_key'],
                symbol=stock['symbol'],
                scan_timestamp=datetime.now(),
                trigger_price=df['close'].iloc[0],
                volume=int(df['volume'].iloc[0]),
                volume_ratio=metrics.get('volume_ratio'),
                atr_value=metrics.get('atr'),
                rsi_value=metrics.get('rsi'),
                rsi_intraday=metrics.get('rsi_intraday'),
                momentum_score=metrics.get('momentum_score'),
                vcp_score=metrics.get('vcp_score'),
                additional_metrics=json.dumps(metrics),
                is_active=True
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error running scanner {scanner_id} on {stock['symbol']}: {e}")
            return None
    
    def scan_all_stocks(self, scanner_ids: List[int] = [1, 12, 14, 20, 21]) -> Dict[int, List[PKScreenerResult]]:
        """
        Run specified scanners on all watchlist stocks
        
        Args:
            scanner_ids: List of scanner IDs to run (default: top 5 scanners)
        
        Returns:
            Dict mapping scanner_id to list of results
        """
        results = {scanner_id: [] for scanner_id in scanner_ids}
        
        logger.info(f"Starting scan of {len(self.watchlist)} stocks with scanners: {scanner_ids}")
        
        for stock in self.watchlist:
            try:
                # Get stock data
                df = self.get_stock_data(stock['instrument_key'], lookback_candles=300)
                
                if df is None:
                    continue
                
                # Run each scanner
                for scanner_id in scanner_ids:
                    result = self.run_scanner(scanner_id, stock, df)
                    
                    if result:
                        results[scanner_id].append(result)
                        logger.info(f"✅ Scanner #{scanner_id} triggered for {stock['symbol']} at ₹{result.trigger_price:.2f}")
            
            except Exception as e:
                logger.error(f"Error scanning {stock['symbol']}: {e}")
                continue
        
        # Save results to database
        self._save_results(results)
        
        # Log summary
        total_triggers = sum(len(r) for r in results.values())
        logger.info(f"Scan complete: {total_triggers} total triggers across {len(scanner_ids)} scanners")
        for scanner_id, scanner_results in results.items():
            logger.info(f"  Scanner #{scanner_id}: {len(scanner_results)} triggers")
        
        return results
    
    def _save_results(self, results: Dict[int, List[PKScreenerResult]]):
        """Save scanner results to database"""
        try:
            # Deactivate old results (older than 1 hour)
            cutoff_time = datetime.now() - timedelta(hours=1)
            self.db.query(PKScreenerResult).filter(
                PKScreenerResult.scan_timestamp < cutoff_time
            ).update({'is_active': False})
            
            # Add new results
            for scanner_id, scanner_results in results.items():
                for result in scanner_results:
                    self.db.add(result)
            
            self.db.commit()
            logger.info("Scanner results saved to database")
            
        except Exception as e:
            logger.error(f"Error saving results: {e}")
            self.db.rollback()
    
    def get_active_results(self, scanner_id: Optional[int] = None) -> List[PKScreenerResult]:
        """
        Get active scanner results
        
        Args:
            scanner_id: Optional filter by scanner ID
        
        Returns:
            List of active PKScreenerResult objects
        """
        try:
            query = self.db.query(PKScreenerResult).filter(
                PKScreenerResult.is_active == True
            )
            
            if scanner_id:
                query = query.filter(PKScreenerResult.scanner_id == scanner_id)
            
            results = query.order_by(PKScreenerResult.scan_timestamp.desc()).all()
            
            return results
            
        except Exception as e:
            logger.error(f"Error fetching active results: {e}")
            return []


def main():
    """Test the scanner engine"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create database tables
    from models import PKScreenerResult, PKScreenerBacktestResult
    from app.db import Base
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created")
    
    # Run scanners
    db = next(get_db())
    engine_instance = ScannerEngine(db)
    
    results = engine_instance.scan_all_stocks(scanner_ids=[1, 12])
    
    # Display results
    print("\n" + "="*80)
    print("SCANNER RESULTS")
    print("="*80)
    
    for scanner_id, scanner_results in results.items():
        print(f"\n📊 Scanner #{scanner_id}: {len(scanner_results)} triggers")
        for result in scanner_results[:10]:  # Show top 10
            print(f"  • {result.symbol}: ₹{result.trigger_price:.2f} | Vol Ratio: {result.volume_ratio:.2f}x | RSI: {result.rsi_value}")
    
    db.close()


if __name__ == "__main__":
    main()

