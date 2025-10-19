#!/usr/bin/env python3
"""
Fetch 5 years of DAILY candle data from Dhan and store in MongoDB
This provides the baseline for daily volume averages used in intraday scanning
"""
import os
import sys
from datetime import datetime, timedelta
from typing import List, Dict
import requests
import time
from pymongo import MongoClient, ASCENDING
from pymongo.errors import DuplicateKeyError
import logging

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.crud import get_watchlist_details

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# MongoDB connection
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
MONGO_DB = os.getenv('MONGO_DB', 'trading_data')

# Dhan API configuration
DHAN_ACCESS_TOKEN = os.getenv('DHAN_ACCESS_TOKEN', 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJpc3MiOiJkaGFuIiwicGFydG5lcklkIjoiIiwiZXhwIjoxNzYwODM5MjU1LCJpYXQiOjE3NjA3NTI4NTUsInRva2VuQ29uc3VtZXJUeXBlIjoiU0VMRiIsIndlYmhvb2tVcmwiOiIiLCJkaGFuQ2xpZW50SWQiOiIxMDAwMDA0MjUzIn0.PuYRFpm2zxGkgPi1vMK-EKDvITjpoIFWF3t8uF6SWkk2rdHNR9zhu75_oSeRb_kYfGj9VNrX5amdEu_4O3texQ')
DHAN_API_URL = 'https://api.dhan.co'


class DailyHistoricalFetcher:
    """Fetch and store daily historical data for volume baseline"""
    
    def __init__(self):
        self.client = MongoClient(MONGO_URI)
        self.db = self.client[MONGO_DB]
        self.daily_candles = self.db['daily_candles']
        self.daily_stats = self.db['daily_stats']
        
        # Create indexes
        self._create_indexes()
    
    def _create_indexes(self):
        """Create MongoDB indexes for efficient querying"""
        # Compound index for querying by instrument and date
        self.daily_candles.create_index([
            ('instrument_key', ASCENDING),
            ('date', ASCENDING)
        ], unique=True)
        
        # Index for symbol lookup
        self.daily_candles.create_index([('symbol', ASCENDING)])

        # Index for date range queries
        self.daily_candles.create_index([('date', ASCENDING)])
        
        # Stats index
        self.daily_stats.create_index([('instrument_key', ASCENDING)], unique=True)
        
        logger.info("MongoDB indexes created")
    
    def fetch_daily_data(self, security_id: str, instrument_key: str, symbol: str, years: int = 5):
        """
        Fetch daily candle data from Dhan API
        
        Args:
            security_id: Dhan security ID
            instrument_key: Our instrument key (DHAN_xxxxx)
            symbol: Stock symbol
            years: Number of years of historical data
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=years * 365)
        
        logger.info(f"Fetching {years} years of daily data for {symbol} ({instrument_key})")
        
        headers = {
            'access-token': DHAN_ACCESS_TOKEN,
            'Content-Type': 'application/json'
        }
        
        payload = {
            'securityId': str(security_id),
            'exchangeSegment': 'NSE_EQ',
            'instrument': 'EQUITY',
            'expiryCode': 0,
            'oi': False,
            'fromDate': start_date.strftime('%Y-%m-%d'),
            'toDate': end_date.strftime('%Y-%m-%d')
        }
        
        try:
            response = requests.post(
                f'{DHAN_API_URL}/v2/charts/historical',
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()

                # Dhan returns arrays: {open: [], high: [], low: [], close: [], volume: [], timestamp: []}
                if 'timestamp' in data and len(data['timestamp']) > 0:
                    self._store_daily_candles(instrument_key, symbol, data, security_id)
                    self._calculate_daily_stats(instrument_key, symbol)
                    return True
                else:
                    logger.warning(f"No candles returned for {symbol}: {data}")
                    return False
            else:
                logger.error(f"HTTP {response.status_code} for {symbol}: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {e}")
            return False
    
    def _store_daily_candles(self, instrument_key: str, symbol: str, data: Dict, security_id: str = None):
        """Store daily candles in MongoDB with proper schema"""
        stored_count = 0
        updated_count = 0

        # Dhan returns arrays: {open: [], high: [], low: [], close: [], volume: [], timestamp: []}
        timestamps = data.get('timestamp', [])
        opens = data.get('open', [])
        highs = data.get('high', [])
        lows = data.get('low', [])
        closes = data.get('close', [])
        volumes = data.get('volume', [])

        for i in range(len(timestamps)):
            try:
                timestamp = datetime.fromtimestamp(timestamps[i])
                date_str = timestamp.strftime('%Y-%m-%d')

                doc = {
                    'instrument_key': instrument_key,
                    'security_id': security_id,
                    'symbol': symbol,
                    'exchange': 'NSE_EQ',
                    'date': date_str,
                    'timestamp': timestamp,
                    'open': float(opens[i]) if i < len(opens) else 0,
                    'high': float(highs[i]) if i < len(highs) else 0,
                    'low': float(lows[i]) if i < len(lows) else 0,
                    'close': float(closes[i]) if i < len(closes) else 0,
                    'volume': int(volumes[i]) if i < len(volumes) else 0,
                    'created_at': datetime.now()
                }

                # Upsert (insert or update)
                result = self.daily_candles.update_one(
                    {'instrument_key': instrument_key, 'date': date_str},
                    {'$set': doc},
                    upsert=True
                )

                if result.upserted_id:
                    stored_count += 1
                elif result.modified_count > 0:
                    updated_count += 1

            except Exception as e:
                logger.error(f"Error storing candle for {symbol}: {e}")

        logger.info(f"{symbol}: Stored {stored_count} new, updated {updated_count} candles")
    
    def _calculate_daily_stats(self, instrument_key: str, symbol: str):
        """Calculate and store daily volume statistics"""
        try:
            # Get all candles for this instrument
            candles = list(self.daily_candles.find(
                {'instrument_key': instrument_key}
            ).sort('date', -1))
            
            if not candles:
                return
            
            # Calculate statistics
            volumes = [c['volume'] for c in candles if c['volume'] > 0]
            
            if not volumes:
                return
            
            stats = {
                'instrument_key': instrument_key,
                'symbol': symbol,
                'total_days': len(candles),
                'avg_daily_volume': sum(volumes) / len(volumes),
                'max_daily_volume': max(volumes),
                'min_daily_volume': min(volumes),
                'avg_volume_20d': sum(volumes[:20]) / min(20, len(volumes)),
                'avg_volume_50d': sum(volumes[:50]) / min(50, len(volumes)),
                'last_updated': datetime.now()
            }
            
            # Store stats
            self.daily_stats.update_one(
                {'instrument_key': instrument_key},
                {'$set': stats},
                upsert=True
            )
            
            logger.info(f"{symbol}: Avg daily volume = {stats['avg_daily_volume']:,.0f}")
            
        except Exception as e:
            logger.error(f"Error calculating stats for {symbol}: {e}")
    
    def fetch_all_watchlist(self, years: int = 5):
        """Fetch daily data for all stocks in watchlist"""
        logger.info("="*80)
        logger.info("FETCHING DAILY HISTORICAL DATA FOR WATCHLIST")
        logger.info("="*80)
        
        # Get watchlist from database
        watchlist = get_watchlist_details()
        
        logger.info(f"Found {len(watchlist)} stocks in watchlist")
        logger.info(f"Fetching {years} years of daily data...")
        
        success_count = 0
        failed_count = 0
        
        for idx, stock in enumerate(watchlist, 1):
            # Extract security_id from instrument_key (DHAN_xxxxx)
            security_id = stock.instrument_key.replace('DHAN_', '')
            
            logger.info(f"\n[{idx}/{len(watchlist)}] Processing {stock.symbol}...")
            
            success = self.fetch_daily_data(
                security_id=security_id,
                instrument_key=stock.instrument_key,
                symbol=stock.symbol,
                years=years
            )
            
            if success:
                success_count += 1
            else:
                failed_count += 1
            
            # Rate limiting - Dhan allows 100 requests per minute
            if idx % 90 == 0:
                logger.info("Rate limit pause - waiting 60 seconds...")
                time.sleep(60)
            else:
                time.sleep(0.7)  # ~85 requests per minute
        
        logger.info("\n" + "="*80)
        logger.info("DAILY DATA FETCH COMPLETE")
        logger.info("="*80)
        logger.info(f"Success: {success_count}")
        logger.info(f"Failed: {failed_count}")
        logger.info(f"Total: {len(watchlist)}")
    
    def get_daily_volume_avg(self, instrument_key: str, days: int = 20) -> float:
        """Get average daily volume for an instrument"""
        stats = self.daily_stats.find_one({'instrument_key': instrument_key})
        
        if stats:
            if days == 20:
                return stats.get('avg_volume_20d', 0)
            elif days == 50:
                return stats.get('avg_volume_50d', 0)
            else:
                return stats.get('avg_daily_volume', 0)
        
        return 0


def main():
    """Main entry point"""
    fetcher = DailyHistoricalFetcher()
    fetcher.fetch_all_watchlist(years=5)


if __name__ == '__main__':
    main()

