"""
Dhan Historical Intraday Data Client
Fetches 1-minute candle data from Dhan API for P&F chart analysis.
"""

import os
import sys
import requests
import time
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from logzero import logger
from dotenv import load_dotenv

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Load environment variables
load_dotenv()

# Import Telegram notifier
try:
    from app.telegram_notifier import send_api_failure_alert
    TELEGRAM_AVAILABLE = True
except ImportError:
    logger.warning("⚠️ Telegram notifier not available for API failure alerts")
    TELEGRAM_AVAILABLE = False


class DhanHistoricalClient:
    """Client for fetching historical intraday data from Dhan API."""
    
    BASE_URL = "https://api.dhan.co"
    INTRADAY_ENDPOINT = "/v2/charts/intraday"
    
    def __init__(self):
        """Initialize Dhan Historical Client with credentials from environment."""
        self.client_id = os.getenv('DHAN_CLIENT_ID')
        self.access_token = os.getenv('DHAN_ACCESS_TOKEN')
        
        if not self.client_id or not self.access_token:
            logger.error("❌ Dhan credentials not found in environment variables")
            logger.error("   Please set DHAN_CLIENT_ID and DHAN_ACCESS_TOKEN in .env file")
    
    def _get_headers(self) -> dict:
        """Get authentication headers for Dhan API."""
        return {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'access-token': self.access_token,
            'client-id': self.client_id
        }
    
    def _format_datetime(self, dt: datetime) -> str:
        """
        Format datetime for Dhan API.

        Args:
            dt: Datetime object

        Returns:
            Formatted string in "YYYY-MM-DD HH:MM:SS" format
        """
        return dt.strftime("%Y-%m-%d %H:%M:%S")

    def _send_failure_alert(
        self,
        error_type: str,
        error_message: str,
        stock_symbol: Optional[str] = None,
        security_id: Optional[int] = None,
        retry_status: str = "Will retry"
    ):
        """Send Telegram alert for API failure."""
        if not TELEGRAM_AVAILABLE:
            return

        try:
            instrument_key = f"DHAN_{security_id}" if security_id else None
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S IST")

            send_api_failure_alert(
                api_name="Dhan Historical Data API",
                endpoint=f"{self.BASE_URL}{self.INTRADAY_ENDPOINT}",
                error_type=error_type,
                error_message=error_message,
                stock_symbol=stock_symbol,
                instrument_key=instrument_key,
                timestamp=timestamp,
                retry_status=retry_status
            )
        except Exception as e:
            logger.error(f"❌ Failed to send Telegram failure alert: {e}")
    
    def get_intraday_data(
        self,
        security_id: int,
        from_date: datetime,
        to_date: datetime,
        interval: str = "1",
        exchange_segment: str = "NSE_EQ",
        instrument: str = "EQUITY",
        stock_symbol: Optional[str] = None
    ) -> Optional[List[Dict]]:
        """
        Fetch intraday historical data from Dhan API with retry logic and error monitoring.

        Args:
            security_id: Dhan security ID (integer)
            from_date: Start datetime
            to_date: End datetime
            interval: Candle interval ("1" for 1-minute, "5" for 5-minute, etc.)
            exchange_segment: Exchange segment (default: "NSE_EQ")
            instrument: Instrument type (default: "EQUITY")
            stock_symbol: Stock symbol for error reporting (optional)

        Returns:
            List of candle dictionaries or None if error
            Each candle dict contains: timestamp, open, high, low, close, volume
        """
        max_retries = 3
        retry_delays = [5, 15, 45]  # Exponential backoff in seconds

        for attempt in range(max_retries):
            try:
                if not self.access_token or not self.client_id:
                    error_msg = "Dhan credentials not available"
                    logger.error(f"❌ {error_msg}")
                    self._send_failure_alert(
                        error_type="Configuration Error",
                        error_message=error_msg,
                        stock_symbol=stock_symbol,
                        security_id=security_id
                    )
                    return None

                # Ensure security_id is integer
                if isinstance(security_id, str):
                    security_id = int(security_id)

                # Prepare request payload
                payload = {
                    "securityId": str(security_id),  # API expects string
                    "exchangeSegment": exchange_segment,
                    "instrument": instrument,
                    "interval": interval,
                    "oi": False,  # We don't need Open Interest for equity
                    "fromDate": self._format_datetime(from_date),
                    "toDate": self._format_datetime(to_date)
                }

                headers = self._get_headers()
                url = f"{self.BASE_URL}{self.INTRADAY_ENDPOINT}"

                logger.debug(f"📊 Fetching intraday data for security {security_id} (attempt {attempt + 1}/{max_retries})")
                logger.debug(f"   From: {self._format_datetime(from_date)}")
                logger.debug(f"   To: {self._format_datetime(to_date)}")

                response = requests.post(
                    url,
                    headers=headers,
                    json=payload,
                    timeout=30
                )

                if response.status_code == 200:
                    data = response.json()
                    logger.debug(f"Response data keys: {data.keys() if isinstance(data, dict) else 'not a dict'}")

                    # Dhan API returns data directly in the response (not wrapped in 'data' key)
                    if 'open' in data and 'timestamp' in data:
                        # Data is in array format
                        num_candles = len(data.get('timestamp', []))
                        logger.info(f"✅ Fetched {num_candles} candles for security {security_id}")
                        return self._parse_candles(data)
                    elif data.get('status') == 'success':
                        candles = data.get('data', {})
                        logger.info(f"✅ Fetched candles for security {security_id}")
                        return self._parse_candles(candles)
                    else:
                        error_msg = data.get('data', data)
                        logger.error(f"❌ Dhan API returned error: {error_msg}")

                        # Don't retry on data errors
                        self._send_failure_alert(
                            error_type="API Data Error",
                            error_message=str(error_msg),
                            stock_symbol=stock_symbol,
                            security_id=security_id,
                            retry_status="Not retrying (data error)"
                        )
                        return None

                elif response.status_code == 401:
                    # Unauthorized - token expired
                    error_msg = "Access token expired or invalid"
                    logger.error(f"❌ {error_msg}")
                    logger.error(f"   Response: {response.text}")

                    self._send_failure_alert(
                        error_type="401 Unauthorized",
                        error_message=f"{error_msg}. Response: {response.text}",
                        stock_symbol=stock_symbol,
                        security_id=security_id,
                        retry_status="Not retrying (auth error)"
                    )
                    return None

                elif response.status_code == 403:
                    # Forbidden - permission issue
                    error_msg = "Access forbidden - check API permissions"
                    logger.error(f"❌ {error_msg}")
                    logger.error(f"   Response: {response.text}")

                    self._send_failure_alert(
                        error_type="403 Forbidden",
                        error_message=f"{error_msg}. Response: {response.text}",
                        stock_symbol=stock_symbol,
                        security_id=security_id,
                        retry_status="Not retrying (permission error)"
                    )
                    return None

                elif response.status_code >= 500:
                    # Server error - retry
                    error_msg = f"Dhan server error: {response.status_code}"
                    logger.error(f"❌ {error_msg}")
                    logger.error(f"   Response: {response.text}")

                    if attempt < max_retries - 1:
                        delay = retry_delays[attempt]
                        logger.info(f"⏳ Retrying in {delay} seconds...")
                        time.sleep(delay)
                        continue
                    else:
                        self._send_failure_alert(
                            error_type=f"{response.status_code} Server Error",
                            error_message=f"{error_msg}. Response: {response.text}",
                            stock_symbol=stock_symbol,
                            security_id=security_id,
                            retry_status=f"Failed after {max_retries} attempts"
                        )
                        return None
                else:
                    # Other error
                    error_msg = f"Dhan API request failed: {response.status_code}"
                    logger.error(f"❌ {error_msg}")
                    logger.error(f"   Response: {response.text}")

                    self._send_failure_alert(
                        error_type=f"{response.status_code} Error",
                        error_message=f"{error_msg}. Response: {response.text}",
                        stock_symbol=stock_symbol,
                        security_id=security_id,
                        retry_status="Not retrying (client error)"
                    )
                    return None

            except requests.exceptions.Timeout:
                error_msg = "Request timeout"
                logger.warning(f"⏱️ {error_msg} (attempt {attempt + 1}/{max_retries})")

                if attempt < max_retries - 1:
                    delay = retry_delays[attempt]
                    logger.info(f"⏳ Retrying in {delay} seconds...")
                    time.sleep(delay)
                    continue
                else:
                    self._send_failure_alert(
                        error_type="Timeout",
                        error_message=error_msg,
                        stock_symbol=stock_symbol,
                        security_id=security_id,
                        retry_status=f"Failed after {max_retries} attempts"
                    )
                    return None

            except requests.exceptions.ConnectionError:
                error_msg = "Connection error"
                logger.warning(f"🔌 {error_msg} (attempt {attempt + 1}/{max_retries})")

                if attempt < max_retries - 1:
                    delay = retry_delays[attempt]
                    logger.info(f"⏳ Retrying in {delay} seconds...")
                    time.sleep(delay)
                    continue
                else:
                    self._send_failure_alert(
                        error_type="Connection Error",
                        error_message=error_msg,
                        stock_symbol=stock_symbol,
                        security_id=security_id,
                        retry_status=f"Failed after {max_retries} attempts"
                    )
                    return None

            except Exception as e:
                error_msg = f"Unexpected error: {str(e)}"
                logger.error(f"❌ {error_msg}")
                import traceback
                traceback.print_exc()

                self._send_failure_alert(
                    error_type="Exception",
                    error_message=error_msg,
                    stock_symbol=stock_symbol,
                    security_id=security_id,
                    retry_status="Not retrying (unexpected error)"
                )
                return None

        return None
    
    def _parse_candles(self, raw_data: Dict) -> List[Dict]:
        """
        Parse raw candle data from Dhan API response.

        Dhan API returns data in array format:
        {
            "open": [100.5, 101.0, ...],
            "high": [101.5, 102.0, ...],
            "low": [100.0, 100.5, ...],
            "close": [100.75, 101.25, ...],
            "volume": [10000, 15000, ...],
            "timestamp": [1726026360.0, 1726026420.0, ...]
        }

        Args:
            raw_data: Raw candle data dictionary from API

        Returns:
            List of parsed candle dictionaries
        """
        parsed_candles = []

        try:
            # Extract arrays from response
            opens = raw_data.get('open', [])
            highs = raw_data.get('high', [])
            lows = raw_data.get('low', [])
            closes = raw_data.get('close', [])
            volumes = raw_data.get('volume', [])
            timestamps = raw_data.get('timestamp', [])

            # Ensure all arrays have the same length
            if not all(len(arr) == len(timestamps) for arr in [opens, highs, lows, closes, volumes]):
                logger.error("❌ Mismatched array lengths in candle data")
                return []

            # Combine arrays into candle dictionaries
            for i in range(len(timestamps)):
                # Convert Unix timestamp to datetime
                timestamp = datetime.fromtimestamp(timestamps[i])

                parsed_candle = {
                    'timestamp': timestamp,
                    'open': float(opens[i]),
                    'high': float(highs[i]),
                    'low': float(lows[i]),
                    'close': float(closes[i]),
                    'volume': int(volumes[i])
                }

                parsed_candles.append(parsed_candle)

            return parsed_candles

        except Exception as e:
            logger.error(f"❌ Error parsing candles: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def get_2month_intraday_data(self, security_id: int) -> Optional[List[Dict]]:
        """
        Fetch 2 months of 1-minute intraday data for a security.
        
        Args:
            security_id: Dhan security ID
            
        Returns:
            List of candle dictionaries or None if error
        """
        # Calculate date range (2 months back from today)
        to_date = datetime.now()
        from_date = to_date - timedelta(days=60)  # Approximately 2 months
        
        # Set to market hours
        from_date = from_date.replace(hour=9, minute=15, second=0, microsecond=0)
        to_date = to_date.replace(hour=15, minute=30, second=0, microsecond=0)
        
        return self.get_intraday_data(
            security_id=security_id,
            from_date=from_date,
            to_date=to_date,
            interval="1"  # 1-minute candles
        )


# Singleton instance
dhan_historical_client = DhanHistoricalClient()


# Test code
if __name__ == "__main__":
    print("=" * 60)
    print("🧪 TESTING DHAN HISTORICAL CLIENT")
    print("=" * 60)
    print()
    
    # Test 1: Connection and basic fetch
    print("📡 Test 1: Fetching 1-week of 1-minute data for TCS...")
    print()
    
    # TCS security ID: 11536
    test_security_id = 11536
    
    # Fetch 1 week of data for testing (use September 2024 dates)
    to_date = datetime(2024, 9, 15, 15, 30, 0)
    from_date = datetime(2024, 9, 11, 9, 15, 0)
    
    candles = dhan_historical_client.get_intraday_data(
        security_id=test_security_id,
        from_date=from_date,
        to_date=to_date,
        interval="1"
    )
    
    if candles:
        print(f"✅ Successfully fetched {len(candles)} candles")
        print()
        print("📊 Sample candles (first 5):")
        for i, candle in enumerate(candles[:5]):
            print(f"   {i+1}. {candle['timestamp']} | O:{candle['open']} H:{candle['high']} L:{candle['low']} C:{candle['close']} V:{candle['volume']}")
        print()
        print("📊 Sample candles (last 5):")
        for i, candle in enumerate(candles[-5:]):
            print(f"   {i+1}. {candle['timestamp']} | O:{candle['open']} H:{candle['high']} L:{candle['low']} C:{candle['close']} V:{candle['volume']}")
    else:
        print("❌ Failed to fetch candles")
    
    print()
    print("=" * 60)
    print("🏁 TESTING COMPLETE")
    print("=" * 60)

