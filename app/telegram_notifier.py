"""
Telegram Notification Service
Sends real-time trading alerts and system notifications via Telegram Bot API.
"""

import os
import requests
import time
from typing import Optional, Dict, Any
from logzero import logger
from dotenv import load_dotenv

load_dotenv()


class TelegramNotifier:
    """Service for sending Telegram notifications with retry logic."""

    def __init__(self):
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID")
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
        self.max_retries = 5
        self.retry_delays = [1, 2, 5, 10, 30]  # Exponential backoff in seconds

        # Rate limiting: Track last alert time per error type
        self.last_alert_time = {}
        self.rate_limit_seconds = 300  # 5 minutes between same error type alerts

        # Fallback: Store failed messages for later retry
        self.failed_messages = []
        self.max_failed_messages = 100
        
    def is_configured(self) -> bool:
        """Check if Telegram credentials are configured."""
        if not self.bot_token or self.bot_token == "your_telegram_bot_token_here":
            logger.warning("⚠️ TELEGRAM_BOT_TOKEN not configured in .env")
            return False
        if not self.chat_id or self.chat_id == "your_telegram_chat_id_here":
            logger.warning("⚠️ TELEGRAM_CHAT_ID not configured in .env")
            return False
        return True
    
    def send_message(
        self, 
        message: str, 
        parse_mode: str = "HTML",
        disable_web_page_preview: bool = False
    ) -> bool:
        """
        Send a message via Telegram with retry logic.
        
        Args:
            message: Message text (supports HTML formatting)
            parse_mode: Message formatting mode (HTML or Markdown)
            disable_web_page_preview: Whether to disable link previews
            
        Returns:
            True if message sent successfully, False otherwise
        """
        if not self.is_configured():
            logger.error("❌ Telegram not configured. Skipping notification.")
            return False
        
        url = f"{self.base_url}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": parse_mode,
            "disable_web_page_preview": disable_web_page_preview
        }
        
        # Retry logic with exponential backoff
        for attempt in range(self.max_retries):
            try:
                # Increased timeout from 10s to 30s to handle slow networks
                response = requests.post(url, json=payload, timeout=30)
                
                if response.status_code == 200:
                    logger.info(f"✅ Telegram message sent successfully (attempt {attempt + 1})")
                    return True
                else:
                    logger.warning(
                        f"⚠️ Telegram API returned status {response.status_code}: {response.text}"
                    )
                    
                    # Don't retry on client errors (4xx)
                    if 400 <= response.status_code < 500:
                        logger.error(f"❌ Client error - not retrying")
                        return False
                    
            except requests.exceptions.Timeout:
                logger.warning(f"⏱️ Telegram request timeout (attempt {attempt + 1}/{self.max_retries})")
            except requests.exceptions.ConnectionError:
                logger.warning(f"🔌 Telegram connection error (attempt {attempt + 1}/{self.max_retries})")
            except Exception as e:
                logger.error(f"❌ Telegram error: {e} (attempt {attempt + 1}/{self.max_retries})")
            
            # Wait before retry (except on last attempt)
            if attempt < self.max_retries - 1:
                delay = self.retry_delays[attempt]
                logger.info(f"⏳ Retrying in {delay} seconds...")
                time.sleep(delay)

        logger.error(f"❌ Failed to send Telegram message after {self.max_retries} attempts")

        # Store failed message for later retry
        if len(self.failed_messages) < self.max_failed_messages:
            self.failed_messages.append({
                'message': message,
                'parse_mode': parse_mode,
                'timestamp': time.time()
            })
            logger.info(f"💾 Stored failed message for later retry ({len(self.failed_messages)} pending)")

        return False
    
    def send_trading_alert(
        self,
        symbol: str,
        instrument_key: str,
        pattern_type: str,
        pattern_name: str,
        alert_type: str,
        signal_price: float,
        matrix_score: Optional[int] = None,
        is_super_alert: bool = False,
        box_size: float = 0.0025,
        interval: str = "1minute",
        time_range: str = "2months",
        trigger_reason: str = "",
        timestamp: str = ""
    ) -> bool:
        """
        Send a formatted trading alert to Telegram.
        
        Args:
            symbol: Stock symbol (e.g., NATIONALUM)
            instrument_key: Dhan instrument key (e.g., DHAN_6364)
            pattern_type: Pattern identifier (e.g., triple_top_buy)
            pattern_name: Human-readable pattern name
            alert_type: BUY or SELL
            signal_price: Price at which alert triggered
            matrix_score: P&F matrix score
            is_super_alert: Whether this is a super alert (±6 or ±8)
            box_size: Box size percentage
            interval: Time interval
            time_range: Time range for chart
            trigger_reason: Detailed trigger reason
            timestamp: Alert timestamp
            
        Returns:
            True if sent successfully
        """
        # Determine emoji based on alert type
        alert_emoji = "🟢" if alert_type == "BUY" else "🔴"
        super_emoji = " ⭐ SUPER ALERT ⭐" if is_super_alert else ""
        
        # Build chart URL
        base_url = os.getenv("APP_BASE_URL", "http://localhost:8000")
        chart_url = (
            f"{base_url}/test-charts?"
            f"symbol={symbol}&"
            f"instrument_key={instrument_key}&"
            f"pattern={pattern_type}&"
            f"box_size={box_size}&"
            f"interval={interval}&"
            f"time_range={time_range}"
        )
        
        # Format message
        message = f"""
🚨 <b>TRADING ALERT</b> 🚨{super_emoji}

{alert_emoji} <b>{alert_type} Signal</b>
📈 <b>Stock:</b> {symbol} ({instrument_key})
📊 <b>Pattern:</b> {pattern_name}
💰 <b>Price:</b> ₹{signal_price:.2f}
"""
        
        if matrix_score is not None:
            score_emoji = "🔥" if abs(matrix_score) >= 6 else "📊"
            message += f"{score_emoji} <b>Matrix Score:</b> {matrix_score:+d}\n"
        
        message += f"""
📦 <b>Box Size:</b> {box_size * 100:.2f}%
⏱️ <b>Interval:</b> {interval}
🕒 <b>Time:</b> {timestamp}

"""
        
        if trigger_reason:
            # Clean up trigger reason (remove emojis for cleaner Telegram display)
            clean_reason = trigger_reason.replace("🚨", "").replace("⭐", "").strip()
            message += f"<b>Trigger:</b> {clean_reason}\n\n"
        
        message += f'<a href="{chart_url}">📊 View Chart</a>'
        
        return self.send_message(message, parse_mode="HTML", disable_web_page_preview=True)
    
    def send_api_failure_alert(
        self,
        api_name: str,
        endpoint: str,
        error_type: str,
        error_message: str,
        stock_symbol: Optional[str] = None,
        instrument_key: Optional[str] = None,
        timestamp: str = "",
        retry_status: str = "Will retry"
    ) -> bool:
        """
        Send API failure notification to Telegram with rate limiting.

        Args:
            api_name: Name of the API (e.g., "Dhan Historical Data API")
            endpoint: API endpoint that failed
            error_type: Type of error (401, 500, Timeout, etc.)
            error_message: Detailed error message
            stock_symbol: Stock being fetched (if applicable)
            instrument_key: Instrument key (if applicable)
            timestamp: When the error occurred
            retry_status: Retry status message

        Returns:
            True if sent successfully
        """
        # Rate limiting: Only send 1 alert per error type per 5 minutes
        current_time = time.time()
        rate_limit_key = f"{api_name}_{error_type}"

        if rate_limit_key in self.last_alert_time:
            time_since_last = current_time - self.last_alert_time[rate_limit_key]
            if time_since_last < self.rate_limit_seconds:
                logger.info(
                    f"⏸️ Rate limit: Skipping {error_type} alert "
                    f"(last sent {int(time_since_last)}s ago, limit: {self.rate_limit_seconds}s)"
                )
                return False

        # Update last alert time
        self.last_alert_time[rate_limit_key] = current_time
        message = f"""
🚨 <b>API FAILURE ALERT</b> 🚨

⚠️ <b>API:</b> {api_name}
🔗 <b>Endpoint:</b> {endpoint}
❌ <b>Error:</b> {error_type}
🕒 <b>Time:</b> {timestamp}
"""
        
        if stock_symbol:
            message += f"📈 <b>Stock:</b> {stock_symbol}"
            if instrument_key:
                message += f" ({instrument_key})"
            message += "\n"
        
        message += f"""
📝 <b>Message:</b> {error_message}
🔄 <b>Status:</b> {retry_status}
"""
        
        # Add action items based on error type
        if "401" in error_type or "Unauthorized" in error_type:
            message += "\n⚡ <b>Action Required:</b> Please refresh Dhan access token in .env file"
        elif "403" in error_type or "Forbidden" in error_type:
            message += "\n⚡ <b>Action Required:</b> Check API permissions and subscription status"
        elif "500" in error_type:
            message += "\n⚡ <b>Action:</b> Dhan server error - will retry automatically"
        
        return self.send_message(message, parse_mode="HTML")
    
    def send_system_alert(
        self,
        alert_title: str,
        alert_message: str,
        severity: str = "INFO"
    ) -> bool:
        """
        Send a general system alert.
        
        Args:
            alert_title: Alert title
            alert_message: Alert message
            severity: Severity level (INFO, WARNING, ERROR, CRITICAL)
            
        Returns:
            True if sent successfully
        """
        severity_emojis = {
            "INFO": "ℹ️",
            "WARNING": "⚠️",
            "ERROR": "❌",
            "CRITICAL": "🚨"
        }
        
        emoji = severity_emojis.get(severity, "📢")
        
        message = f"""
{emoji} <b>{severity}: {alert_title}</b>

{alert_message}
"""
        
        return self.send_message(message, parse_mode="HTML")
    
    def retry_failed_messages(self) -> int:
        """
        Retry sending failed messages.

        Returns:
            Number of messages successfully sent
        """
        if not self.failed_messages:
            return 0

        logger.info(f"🔄 Retrying {len(self.failed_messages)} failed messages...")

        success_count = 0
        remaining_messages = []

        for msg_data in self.failed_messages:
            # Skip messages older than 1 hour
            if time.time() - msg_data['timestamp'] > 3600:
                logger.info(f"⏰ Skipping message older than 1 hour")
                continue

            # Try to send
            if self.send_message(msg_data['message'], msg_data['parse_mode']):
                success_count += 1
            else:
                remaining_messages.append(msg_data)

        self.failed_messages = remaining_messages

        if success_count > 0:
            logger.info(f"✅ Successfully sent {success_count} failed messages")

        return success_count

    def test_connection(self) -> bool:
        """
        Test Telegram bot connection.

        Returns:
            True if connection successful
        """
        if not self.is_configured():
            return False

        test_message = """
✅ <b>Telegram Bot Test</b>

Your trading alert system is connected and working!

🔔 You will receive:
• Real-time trading alerts
• API failure notifications
• System health updates

📊 Trading Application
"""

        return self.send_message(test_message, parse_mode="HTML")


# Global instance
telegram_notifier = TelegramNotifier()


# Convenience functions
def send_trading_alert(**kwargs) -> bool:
    """Send a trading alert via Telegram."""
    return telegram_notifier.send_trading_alert(**kwargs)


def send_api_failure_alert(**kwargs) -> bool:
    """Send an API failure alert via Telegram."""
    return telegram_notifier.send_api_failure_alert(**kwargs)


def send_system_alert(**kwargs) -> bool:
    """Send a system alert via Telegram."""
    return telegram_notifier.send_system_alert(**kwargs)


def test_telegram_connection() -> bool:
    """Test Telegram connection."""
    return telegram_notifier.test_connection()

