"""
Dhan LTP Client for real-time Last Traded Price data collection.
Uses Dhan Market Quote API for LTP data.
"""

import os
import sys
import requests
from typing import List, Dict, Optional
from datetime import datetime
from logzero import logger

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from app import crud


class DhanLTPClient:
    """Dhan client for LTP data collection using Market Quote API."""

    def __init__(self):
        self.client_id = os.getenv("DHAN_CLIENT_ID")
        self.access_token = os.getenv("DHAN_ACCESS_TOKEN")
        self.api_key = os.getenv("DHAN_API_KEY")
        self.api_secret = os.getenv("DHAN_API_SECRET")
        self.base_url = "https://api.dhan.co"

        # Check which authentication method is available
        if not self.access_token and not (self.api_key and self.api_secret):
            logger.warning("⚠️ No Dhan authentication credentials found")
            logger.warning("   Please set either DHAN_ACCESS_TOKEN or (DHAN_API_KEY + DHAN_API_SECRET)")

        if not self.client_id:
            logger.warning("⚠️ DHAN_CLIENT_ID not found in environment variables")

    def _get_headers(self) -> dict:
        """Get authentication headers based on available credentials."""
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }

        # Add client-id header (required for Dhan API)
        if self.client_id:
            headers['client-id'] = self.client_id

        # Prefer Access Token if available
        if self.access_token:
            headers['access-token'] = self.access_token
            logger.debug("Using Access Token authentication")
        elif self.api_key and self.api_secret:
            # Use API Key authentication
            headers['api-key'] = self.api_key
            headers['api-secret'] = self.api_secret
            logger.debug("Using API Key authentication")

        return headers
    
    def test_connection(self) -> bool:
        """Test Dhan API connection using User Profile endpoint."""
        try:
            if not self.access_token and not (self.api_key and self.api_secret):
                logger.error("❌ No Dhan authentication credentials available")
                return False

            # Test with User Profile API
            headers = self._get_headers()

            response = requests.get(
                f"{self.base_url}/v2/profile",
                headers=headers,
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ Dhan connection test successful")
                logger.info(f"👤 Client ID: {data.get('dhanClientId', 'Unknown')}")
                logger.info(f"📅 Token Validity: {data.get('tokenValidity', 'Unknown')}")
                logger.info(f"📊 Data Plan: {data.get('dataPlan', 'Unknown')}")
                return True
            else:
                logger.error(f"❌ Dhan connection test failed: {response.status_code}")
                logger.error(f"Response: {response.text}")
                return False

        except Exception as e:
            logger.error(f"❌ Dhan connection test error: {e}")
            return False
    
    def get_ltp_data(self, security_ids: List[str]) -> Dict[str, float]:
        """
        Fetch LTP data for multiple securities using Dhan Market Quote API.

        Args:
            security_ids: List of Dhan security IDs (e.g., ["1333", "11536"] or [1333, 11536])

        Returns:
            Dictionary mapping security_id (as string) to LTP value
        """
        try:
            if not self.access_token and not (self.api_key and self.api_secret):
                logger.error("❌ No Dhan authentication credentials available")
                return {}

            if not security_ids:
                logger.warning("⚠️ No security IDs provided")
                return {}

            headers = self._get_headers()

            # Convert security IDs to integers (Dhan API requires integers)
            int_security_ids = [int(sid) if isinstance(sid, str) else sid for sid in security_ids]

            # Dhan Market Quote API payload
            # Format: {"NSE_EQ": [security_id1, security_id2, ...]} (integers)
            payload = {
                "NSE_EQ": int_security_ids
            }

            logger.info(f"📊 Fetching LTP for {len(security_ids)} securities...")

            # Make API request
            response = requests.post(
                f"{self.base_url}/v2/marketfeed/ltp",
                headers=headers,
                json=payload,
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()

                if data.get('status') == 'success':
                    ltp_data = {}

                    # Parse response - Dhan returns data in format:
                    # {"status": "success", "data": {"NSE_EQ": {"1333": {"last_price": 3500.0}}}}
                    nse_eq_data = data.get('data', {}).get('NSE_EQ', {})

                    for security_id, quote_data in nse_eq_data.items():
                        if isinstance(quote_data, dict) and 'last_price' in quote_data:
                            ltp_data[security_id] = quote_data['last_price']

                    logger.info(f"✅ Successfully fetched LTP for {len(ltp_data)} securities")
                    return ltp_data
                else:
                    logger.error(f"❌ LTP API returned error: {data}")
                    return {}
            else:
                logger.error(f"❌ LTP API request failed: {response.status_code}")
                logger.error(f"Response: {response.text}")
                return {}

        except Exception as e:
            logger.error(f"❌ Error fetching LTP data: {e}")
            return {}
    
    def convert_symbol_to_security_id(self, symbol: str) -> Optional[str]:
        """
        Convert stock symbol to Dhan security ID.
        This is a placeholder - you'll need to implement proper mapping.
        
        For now, we'll need to download and parse Dhan's instrument list.
        """
        # TODO: Implement proper symbol to security_id mapping
        # Dhan provides instrument list at: https://images.dhan.co/api-data/api-scrip-master.csv
        logger.warning(f"⚠️ Symbol to Security ID conversion not yet implemented for {symbol}")
        return None


# Create singleton instance
dhan_ltp_client = DhanLTPClient()


if __name__ == "__main__":
    """Test the Dhan LTP client."""
    from dotenv import load_dotenv
    load_dotenv()
    
    print("\n" + "="*60)
    print("🧪 TESTING DHAN LTP CLIENT")
    print("="*60 + "\n")
    
    # Test 1: Connection Test
    print("📡 Test 1: Testing Dhan API Connection...")
    if dhan_ltp_client.test_connection():
        print("✅ Connection test passed!\n")
    else:
        print("❌ Connection test failed!\n")
        sys.exit(1)
    
    # Test 2: LTP Data Fetch
    print("📊 Test 2: Testing LTP Data Fetch...")
    print("Note: Using actual security IDs from instrument mapper")
    print("TCS: 11536, Reliance: 2885\n")

    # Actual security IDs from Dhan instrument mapper
    # TCS: 11536, Reliance: 2885
    sample_security_ids = ["11536", "2885"]
    
    ltp_data = dhan_ltp_client.get_ltp_data(sample_security_ids)
    
    if ltp_data:
        print("✅ LTP data fetch successful!")
        for security_id, ltp in ltp_data.items():
            print(f"   Security ID {security_id}: ₹{ltp}")
    else:
        print("❌ LTP data fetch failed!")
    
    print("\n" + "="*60)
    print("🏁 TESTING COMPLETE")
    print("="*60 + "\n")

