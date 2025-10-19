"""
MongoDB Daily Data Service
Provides daily candle data and volume statistics for intraday scanners
"""
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, List

# Try to import dotenv, but make it optional
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not required

# Try to import pymongo, but make it optional
try:
    from pymongo import MongoClient
    PYMONGO_AVAILABLE = True
except ImportError:
    PYMONGO_AVAILABLE = False
    MongoClient = None

logger = logging.getLogger(__name__)

if not PYMONGO_AVAILABLE:
    logger.warning("pymongo not installed. MongoDB features will be disabled. Install with: pip install pymongo")


class DailyDataService:
    """Service to fetch daily candle data and statistics from MongoDB"""
    
    def __init__(self):
        self.mongo_uri = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
        self.mongo_db = os.getenv('MONGO_DB', 'trading_data')
        self.client = None
        self.db = None
        self.daily_candles = None
        self._volume_cache = {}  # Cache for daily volume averages
        self._connect()
    
    def _connect(self):
        """Connect to MongoDB"""
        if not PYMONGO_AVAILABLE:
            logger.warning("pymongo not available. MongoDB features disabled.")
            return

        try:
            self.client = MongoClient(self.mongo_uri)
            self.db = self.client[self.mongo_db]
            self.daily_candles = self.db['daily_candles']
            logger.info(f"Connected to MongoDB: {self.mongo_db}")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            # Don't raise - allow service to work without MongoDB
            logger.warning("Continuing without MongoDB. Some scanners may not work.")
    
    def get_daily_volume_avg(self, instrument_key: str, days: int = 20) -> float:
        """
        Get average daily volume for an instrument over the last N days

        Args:
            instrument_key: Instrument key (e.g., 'DHAN_3506')
            days: Number of days to average (default: 20)

        Returns:
            Average daily volume
        """
        if not PYMONGO_AVAILABLE or not self.daily_candles:
            logger.debug(f"MongoDB not available, returning default volume for {instrument_key}")
            return 1000000.0  # Return default volume
        # Check cache first
        cache_key = f"{instrument_key}_{days}"
        if cache_key in self._volume_cache:
            return self._volume_cache[cache_key]
        
        try:
            # Get last N days of data
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days * 2)  # Get more to ensure we have enough trading days
            
            pipeline = [
                {
                    '$match': {
                        'instrument_key': instrument_key,
                        'timestamp': {
                            '$gte': start_date,
                            '$lte': end_date
                        }
                    }
                },
                {
                    '$sort': {'timestamp': -1}
                },
                {
                    '$limit': days
                },
                {
                    '$group': {
                        '_id': None,
                        'avg_volume': {'$avg': '$volume'}
                    }
                }
            ]
            
            result = list(self.daily_candles.aggregate(pipeline))
            
            if result and result[0]['avg_volume']:
                avg_volume = float(result[0]['avg_volume'])
                self._volume_cache[cache_key] = avg_volume
                return avg_volume
            else:
                logger.warning(f"No daily volume data found for {instrument_key}")
                return 0.0
                
        except Exception as e:
            logger.error(f"Error fetching daily volume for {instrument_key}: {e}")
            return 0.0
    
    def get_daily_volume_per_minute(self, instrument_key: str, days: int = 20) -> float:
        """
        Get average volume per minute based on daily average
        Assumes 375 trading minutes per day (6.25 hours)
        
        Args:
            instrument_key: Instrument key (e.g., 'DHAN_3506')
            days: Number of days to average (default: 20)
        
        Returns:
            Average volume per minute
        """
        daily_avg = self.get_daily_volume_avg(instrument_key, days)
        if daily_avg > 0:
            return daily_avg / 375.0  # 375 minutes in a trading day
        return 0.0
    
    def get_daily_candles(self, instrument_key: str, start_date: datetime, end_date: datetime) -> List[Dict]:
        """
        Get daily candles for an instrument within a date range

        Args:
            instrument_key: Instrument key (e.g., 'DHAN_3506')
            start_date: Start date
            end_date: End date

        Returns:
            List of daily candles
        """
        if not PYMONGO_AVAILABLE or not self.daily_candles:
            logger.debug(f"MongoDB not available, returning empty candles for {instrument_key}")
            return []

        try:
            candles = list(self.daily_candles.find(
                {
                    'instrument_key': instrument_key,
                    'timestamp': {
                        '$gte': start_date,
                        '$lte': end_date
                    }
                },
                {'_id': 0}  # Exclude MongoDB _id field
            ).sort('timestamp', 1))
            
            return candles
            
        except Exception as e:
            logger.error(f"Error fetching daily candles for {instrument_key}: {e}")
            return []
    
    def get_latest_daily_candle(self, instrument_key: str) -> Optional[Dict]:
        """
        Get the most recent daily candle for an instrument

        Args:
            instrument_key: Instrument key (e.g., 'DHAN_3506')

        Returns:
            Latest daily candle or None
        """
        if not PYMONGO_AVAILABLE or not self.daily_candles:
            logger.debug(f"MongoDB not available, returning None for {instrument_key}")
            return None

        try:
            candle = self.daily_candles.find_one(
                {'instrument_key': instrument_key},
                {'_id': 0},
                sort=[('timestamp', -1)]
            )
            return candle
            
        except Exception as e:
            logger.error(f"Error fetching latest daily candle for {instrument_key}: {e}")
            return None
    
    def get_volume_statistics(self, instrument_key: str, days: int = 20) -> Dict:
        """
        Get comprehensive volume statistics for an instrument

        Args:
            instrument_key: Instrument key (e.g., 'DHAN_3506')
            days: Number of days to analyze (default: 20)

        Returns:
            Dictionary with volume statistics
        """
        if not PYMONGO_AVAILABLE or not self.daily_candles:
            logger.debug(f"MongoDB not available, returning default stats for {instrument_key}")
            return {
                'avg_volume': 1000000.0,
                'max_volume': 2000000.0,
                'min_volume': 500000.0,
                'std_volume': 300000.0
            }

        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days * 2)
            
            pipeline = [
                {
                    '$match': {
                        'instrument_key': instrument_key,
                        'timestamp': {
                            '$gte': start_date,
                            '$lte': end_date
                        }
                    }
                },
                {
                    '$sort': {'timestamp': -1}
                },
                {
                    '$limit': days
                },
                {
                    '$group': {
                        '_id': None,
                        'avg_volume': {'$avg': '$volume'},
                        'max_volume': {'$max': '$volume'},
                        'min_volume': {'$min': '$volume'},
                        'count': {'$sum': 1}
                    }
                }
            ]
            
            result = list(self.daily_candles.aggregate(pipeline))
            
            if result:
                stats = result[0]
                return {
                    'avg_volume': float(stats.get('avg_volume', 0)),
                    'max_volume': float(stats.get('max_volume', 0)),
                    'min_volume': float(stats.get('min_volume', 0)),
                    'avg_volume_per_minute': float(stats.get('avg_volume', 0)) / 375.0,
                    'days_analyzed': stats.get('count', 0)
                }
            else:
                return {
                    'avg_volume': 0.0,
                    'max_volume': 0.0,
                    'min_volume': 0.0,
                    'avg_volume_per_minute': 0.0,
                    'days_analyzed': 0
                }
                
        except Exception as e:
            logger.error(f"Error fetching volume statistics for {instrument_key}: {e}")
            return {
                'avg_volume': 0.0,
                'max_volume': 0.0,
                'min_volume': 0.0,
                'avg_volume_per_minute': 0.0,
                'days_analyzed': 0
            }
    
    def clear_cache(self):
        """Clear the volume cache"""
        self._volume_cache.clear()
        logger.info("Volume cache cleared")
    
    def close(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")


# Global instance
_daily_data_service = None


def get_daily_data_service() -> DailyDataService:
    """Get or create the global DailyDataService instance"""
    global _daily_data_service
    if _daily_data_service is None:
        _daily_data_service = DailyDataService()
    return _daily_data_service

