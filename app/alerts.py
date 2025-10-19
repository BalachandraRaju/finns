from typing import List, Dict, Union
import pandas as pd
import numpy as np
from logzero import logger

def _get_pnf_columns(x_coords: List[int], y_coords: List[float], symbols: List[str]) -> List[Dict]:
    """Helper to structure raw P&F data into a list of column objects."""
    if not x_coords:
        return []
    
    pnf_columns = []
    last_col_idx = -1
    for x, y, s in zip(x_coords, y_coords, symbols):
        if x != last_col_idx:
            pnf_columns.append({'type': s, 'values': []})
            last_col_idx = x
        pnf_columns[-1]['values'].append(y)
    
    for col in pnf_columns:
        col['values'].sort()
        if col['values']:
            col['high'] = col['values'][-1]
            col['low'] = col['values'][0]
        else:
            col['high'] = col['low'] = 0

    return pnf_columns

# --- Foundational Patterns (from chartschool.stockcharts.com) ---

def find_buy_signal(x_coords: List[int], y_coords: List[float], symbols: List[str], **kwargs) -> Union[dict, None]:
    """AKA Double Top Breakout. A new X column rises above the high of the previous X column."""
    columns = _get_pnf_columns(x_coords, y_coords, symbols)
    if len(columns) < 2 or columns[-1]['type'] != 'X':
        return None

    latest_col = columns[-1]
    
    # Find the most recent 'X' column before the latest one
    prev_x_cols = [c for c in columns[:-1] if c['type'] == 'X']
    if not prev_x_cols:
        return None
    
    resistance = prev_x_cols[-1]['high']

    if latest_col['high'] > resistance and latest_col['low'] <= resistance:
        return {'type': 'P&F Buy Signal', 'signal_price': min([p for p in latest_col['values'] if p > resistance])}
    return None

def find_sell_signal(x_coords: List[int], y_coords: List[float], symbols: List[str], **kwargs) -> Union[dict, None]:
    """AKA Double Bottom Breakdown. A new O column drops below the low of the previous O column."""
    columns = _get_pnf_columns(x_coords, y_coords, symbols)
    if len(columns) < 2 or columns[-1]['type'] != 'O':
        return None

    latest_col = columns[-1]

    # Find the most recent 'O' column before the latest one
    prev_o_cols = [c for c in columns[:-1] if c['type'] == 'O']
    if not prev_o_cols:
        return None
        
    support = prev_o_cols[-1]['low']

    if latest_col['low'] < support and latest_col['high'] >= support:
        return {'type': 'P&F Sell Signal', 'signal_price': max([p for p in latest_col['values'] if p < support])}
    return None

def find_triple_top_breakout(x_coords: List[int], y_coords: List[float], symbols: List[str], **kwargs) -> Union[dict, None]:
    """A new X column rises above the highs of the two previous X columns."""
    columns = _get_pnf_columns(x_coords, y_coords, symbols)
    if len(columns) < 3 or columns[-1]['type'] != 'X':
        return None

    latest_col = columns[-1]
    prev_x_cols = [c for c in columns[:-1] if c['type'] == 'X']
    if len(prev_x_cols) < 2:
        return None
    
    resistance = max(prev_x_cols[-1]['high'], prev_x_cols[-2]['high'])

    if latest_col['high'] > resistance and latest_col['low'] <= resistance:
        return {'type': 'Triple Top Breakout', 'signal_price': min([p for p in latest_col['values'] if p > resistance])}
    return None

def find_triple_bottom_breakdown(x_coords: List[int], y_coords: List[float], symbols: List[str], **kwargs) -> Union[dict, None]:
    """A new O column drops below the lows of the two previous O columns."""
    columns = _get_pnf_columns(x_coords, y_coords, symbols)
    if len(columns) < 3 or columns[-1]['type'] != 'O':
        return None

    latest_col = columns[-1]
    prev_o_cols = [c for c in columns[:-1] if c['type'] == 'O']
    if len(prev_o_cols) < 2:
        return None

    support = min(prev_o_cols[-1]['low'], prev_o_cols[-2]['low'])

    if latest_col['low'] < support and latest_col['high'] >= support:
        return {'type': 'Triple Bottom Breakdown', 'signal_price': max([p for p in latest_col['values'] if p < support])}
    return None

def find_ascending_triple_top(x_coords: List[int], y_coords: List[float], symbols: List[str], **kwargs) -> Union[dict, None]:
    """A series of three X columns, each with a higher high (H3 > H2 > H1)."""
    columns = _get_pnf_columns(x_coords, y_coords, symbols)
    if len(columns) < 5 or columns[-1]['type'] != 'X':
        return None

    prev_x_cols = [c for c in columns if c['type'] == 'X']
    if len(prev_x_cols) < 3:
        return None

    c1, c2, c3 = prev_x_cols[-3], prev_x_cols[-2], prev_x_cols[-1]
    h1, h2, h3 = c1['high'], c2['high'], c3['high']

    if h3 > h2 and h2 > h1:
        if c3['low'] <= h2:  # Ensure it's a breakout, not a gap
            return {'type': 'Ascending Triple Top', 'signal_price': min([p for p in c3['values'] if p > h2])}
    return None

def find_descending_triple_bottom(x_coords: List[int], y_coords: List[float], symbols: List[str], **kwargs) -> Union[dict, None]:
    """A series of three O columns, each with a lower low (L3 < L2 < L1)."""
    columns = _get_pnf_columns(x_coords, y_coords, symbols)
    if len(columns) < 5 or columns[-1]['type'] != 'O':
        return None

    prev_o_cols = [c for c in columns if c['type'] == 'O']
    if len(prev_o_cols) < 3:
        return None

    c1, c2, c3 = prev_o_cols[-3], prev_o_cols[-2], prev_o_cols[-1]
    l1, l2, l3 = c1['low'], c2['low'], c3['low']

    if l3 < l2 and l2 < l1:
        if c3['high'] >= l2: # Ensure it's a breakdown, not a gap
            return {'type': 'Descending Triple Bottom', 'signal_price': max([p for p in c3['values'] if p < l2])}
    return None


# --- RSI-based Alerts ---

def calculate_rsi(prices: List[float], period: int = 9) -> float:
    """
    Calculate RSI (Relative Strength Index) for the given prices.

    Args:
        prices: List of closing prices
        period: RSI period (default 9)

    Returns:
        RSI value (0-100) or None if insufficient data
    """
    if len(prices) < period + 1:
        return None

    # Convert to pandas Series for easier calculation
    price_series = pd.Series(prices)

    # Calculate price changes
    delta = price_series.diff()

    # Separate gains and losses
    gains = delta.where(delta > 0, 0)
    losses = -delta.where(delta < 0, 0)

    # Calculate average gains and losses using exponential moving average
    avg_gains = gains.ewm(span=period, adjust=False).mean()
    avg_losses = losses.ewm(span=period, adjust=False).mean()

    # Calculate RS and RSI
    rs = avg_gains / avg_losses
    rsi = 100 - (100 / (1 + rs))

    return rsi.iloc[-1] if not pd.isna(rsi.iloc[-1]) else None


def find_rsi_overbought_alert(candle_data: List[Dict], symbol: str, rsi_threshold: float = 60, period: int = 9) -> Union[dict, None]:
    """
    Check if RSI crosses above the threshold (overbought condition).

    Args:
        candle_data: List of candle dictionaries with 'close' prices
        symbol: Stock symbol
        rsi_threshold: RSI threshold to trigger alert (default 60)
        period: RSI calculation period (default 9)

    Returns:
        Alert dictionary if RSI crosses threshold, None otherwise
    """
    if len(candle_data) < period + 2:
        logger.warning(f"Insufficient data for RSI calculation for {symbol}. Need at least {period + 2} candles.")
        return None

    # Extract closing prices
    closes = [float(candle['close']) for candle in candle_data]

    # Calculate current and previous RSI
    current_rsi = calculate_rsi(closes, period)
    previous_rsi = calculate_rsi(closes[:-1], period) if len(closes) > period + 1 else None

    if current_rsi is None:
        return None

    # Check if RSI crossed above threshold
    if current_rsi > rsi_threshold and (previous_rsi is None or previous_rsi <= rsi_threshold):
        current_price = closes[-1]
        return {
            'type': 'RSI Overbought Alert',
            'signal_price': current_price,
            'rsi_value': round(current_rsi, 2),
            'threshold': rsi_threshold,
            'period': period
        }

    return None


def find_rsi_oversold_alert(candle_data: List[Dict], symbol: str, rsi_threshold: float = 40, period: int = 9) -> Union[dict, None]:
    """
    Check if RSI crosses below the threshold (oversold condition).

    Args:
        candle_data: List of candle dictionaries with 'close' prices
        symbol: Stock symbol
        rsi_threshold: RSI threshold to trigger alert (default 40)
        period: RSI calculation period (default 9)

    Returns:
        Alert dictionary if RSI crosses threshold, None otherwise
    """
    if len(candle_data) < period + 2:
        logger.warning(f"Insufficient data for RSI calculation for {symbol}. Need at least {period + 2} candles.")
        return None

    # Extract closing prices
    closes = [float(candle['close']) for candle in candle_data]

    # Calculate current and previous RSI
    current_rsi = calculate_rsi(closes, period)
    previous_rsi = calculate_rsi(closes[:-1], period) if len(closes) > period + 1 else None

    if current_rsi is None:
        return None

    # Check if RSI crossed below threshold
    if current_rsi < rsi_threshold and (previous_rsi is None or previous_rsi >= rsi_threshold):
        current_price = closes[-1]
        return {
            'type': 'RSI Oversold Alert',
            'signal_price': current_price,
            'rsi_value': round(current_rsi, 2),
            'threshold': rsi_threshold,
            'period': period
        }

    return None