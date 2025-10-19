import os
import requests
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_telegram_alert(symbol: str, rsi: float = None, alert_type: str = "RSI", additional_info: str = ""):
    """
    Sends a formatted alert message to the configured Telegram chat.

    Args:
        symbol: Stock symbol
        rsi: RSI value (optional, for RSI alerts)
        alert_type: Type of alert (RSI, P&F, etc.)
        additional_info: Additional information to include
    """
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram credentials not set. Skipping alert.")
        # To see the message in the console during development:
        if rsi is not None:
            print(f"TELEGRAM_ALERT: {symbol} - {alert_type} Alert - RSI: {rsi:.2f}")
        else:
            print(f"TELEGRAM_ALERT: {symbol} - {alert_type} Alert {additional_info}")
        return

    # Format message based on alert type
    if rsi is not None and rsi > 0:
        if rsi >= 60:
            emoji = "🔴"
            condition = "Overbought"
        elif rsi <= 40:
            emoji = "🟢"
            condition = "Oversold"
        else:
            emoji = "🟡"
            condition = "Alert"
        message = f"{emoji} *RSI {condition}!* {emoji}\n\n*Stock:* `{symbol}`\n*RSI (3min):* `{rsi:.2f}`"
    else:
        message = f"📊 *{alert_type} Alert!* 📊\n\n*Stock:* `{symbol}`{additional_info}"
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }

    try:
        response = requests.post(url, json=payload, timeout=5)
        response.raise_for_status()
        print(f"Successfully sent Telegram alert for {symbol}.")
    except requests.exceptions.RequestException as e:
        print(f"Failed to send Telegram alert for {symbol}: {e}")


def send_alert_message(symbol: str, alert_dict: dict):
    """
    Send a comprehensive alert message based on alert dictionary.

    Args:
        symbol: Stock symbol
        alert_dict: Alert dictionary containing type, signal_price, etc.
    """
    alert_type = alert_dict.get('type', 'Unknown Alert')
    signal_price = alert_dict.get('signal_price', 0)

    if 'RSI' in alert_type:
        rsi_value = alert_dict.get('rsi_value', 0)
        threshold = alert_dict.get('threshold', 0)
        send_telegram_alert(symbol, rsi_value, alert_type, f"\n*Threshold:* `{threshold}`\n*Price:* `{signal_price:.2f}`")
    else:
        # P&F or other pattern alerts
        send_telegram_alert(symbol, None, alert_type, f"\n*Signal Price:* `{signal_price:.2f}`")


def send_enhanced_pattern_telegram(symbol: str, alert_dict: dict):
    """
    Send enhanced pattern alert to Telegram with detailed information.

    Args:
        symbol: Stock symbol
        alert_dict: Enhanced alert dictionary with pattern details
    """
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram credentials not set. Skipping enhanced pattern alert.")
        print(f"ENHANCED_PATTERN_ALERT: {symbol} - {alert_dict}")
        return

    # Extract alert details
    pattern_type = alert_dict.get('pattern_type', 'unknown')
    signal_price = alert_dict.get('signal_price', 0)
    alert_type = alert_dict.get('alert_type', 'BUY')
    column = alert_dict.get('column', 0)
    trigger_reason = alert_dict.get('trigger_reason', '')

    # Determine emoji and action based on alert type
    if alert_type == 'BUY':
        emoji = "🚀"
        action = "BUY SIGNAL"
        color_emoji = "🟢"
    else:
        emoji = "📉"
        action = "SELL SIGNAL"
        color_emoji = "🔴"

    # Extract pattern name for display
    pattern_display_name = pattern_type.replace('_', ' ').title()

    # Create enhanced message with pattern details
    message = f"{emoji} *{action}!* {color_emoji}\n\n"
    message += f"*Stock:* `{symbol}`\n"
    message += f"*Pattern:* `{pattern_display_name}`\n"
    message += f"*Price:* `₹{signal_price:.2f}`\n"
    message += f"*Column:* `{column}`\n"
    message += f"*Time:* `1min | 0.25% box | 3 reversal`\n\n"

    # Add trigger reason (cleaned up)
    if trigger_reason:
        # Clean up the trigger reason for better display
        clean_reason = trigger_reason.replace('🚨 ', '').replace(':', '')
        message += f"*Details:* {clean_reason}\n\n"

    message += f"📊 *P&F Chart Analysis Complete* 📊"

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }

    try:
        response = requests.post(url, json=payload, timeout=5)
        response.raise_for_status()
        print(f"Successfully sent enhanced pattern alert for {symbol} - {pattern_display_name}.")
    except requests.exceptions.RequestException as e:
        print(f"Failed to send enhanced pattern alert for {symbol}: {e}")


if __name__ == '__main__':
    # Example usage (will only print to console if credentials are not in .env)
    print("Sending test Telegram alert...")
    send_telegram_alert("TEST.NS", 85.5)
    print("Test complete.")
