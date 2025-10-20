import requests
import datetime
import pandas as pd
import plotly.graph_objects as go
from typing import Union, List, Tuple
from logzero import logger
import math
import os
from dotenv import load_dotenv
import numpy as np

from fastapi import APIRouter, Query, HTTPException
import upstox_client

from app import crud
from app.mongo_service import get_candles as get_candles_mongo, insert_candles_bulk

# Import anchor point calculator
import sys
sys.path.append('.')
from anchor_point_calculator import AnchorPointCalculator, AnchorPointVisualizer

load_dotenv()
ACCESS_TOKEN = os.getenv("UPSTOX_ACCESS_TOKEN", "")
# The Upstox client is configured here
configuration = upstox_client.Configuration()
configuration.access_token = ACCESS_TOKEN
api_client = upstox_client.ApiClient(configuration)

router = APIRouter()


# --- Utility Functions for Data Management ---

def populate_minute_data_for_watchlist():
    """
    Pre-populate 1-minute data for all stocks in the watchlist.
    This function fetches 2 months of 1-minute data for efficient chart loading.
    """
    from app import crud

    logger.info("Starting to populate 1-minute data for all watchlist stocks...")
    watchlist = crud.get_watchlist_details()

    if not watchlist:
        logger.info("No stocks in watchlist. Nothing to populate.")
        return

    today = datetime.date.today()
    start_date = today - datetime.timedelta(days=60)  # 2 months

    total_stocks = len(watchlist)
    for i, stock in enumerate(watchlist, 1):
        logger.info(f"Processing {i}/{total_stocks}: {stock.symbol} ({stock.instrument_key})")
        try:
            # This will automatically fetch missing data and save to DB
            get_candles_for_instrument(stock.instrument_key, "1minute", start_date, today)
            logger.info(f"✅ Completed 1-minute data population for {stock.symbol}")
        except Exception as e:
            logger.error(f"❌ Failed to populate 1-minute data for {stock.symbol}: {e}")

    logger.info("Finished populating 1-minute data for all watchlist stocks.")

def populate_minute_data_for_stock(instrument_key: str):
    """
    Pre-populate 1-minute data for a specific stock.
    Useful when adding new stocks to watchlist.
    """
    logger.info(f"Populating 1-minute data for {instrument_key}...")
    today = datetime.date.today()
    start_date = today - datetime.timedelta(days=60)  # 2 months

    try:
        get_candles_for_instrument(instrument_key, "1minute", start_date, today)
        logger.info(f"✅ Completed 1-minute data population for {instrument_key}")
    except Exception as e:
        logger.error(f"❌ Failed to populate 1-minute data for {instrument_key}: {e}")


# --- Main Data and Charting Logic ---

def get_candles_for_instrument(instrument_key: str, interval: str, from_date: datetime.date, to_date: datetime.date) -> list:
    """
    Database-first function to get all candle data with automatic backfill.
    Uses the new database service for intelligent data management.
    """
    logger.info(f"Getting candle data for {instrument_key} from {from_date} to {to_date} (database-first)")

    try:
        # Use database service for smart data retrieval
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data-fetch'))
        from database_service import database_service

        candles = database_service.get_candles_smart(
            instrument_key=instrument_key,
            interval=interval,
            start_date=from_date,
            end_date=to_date,
            auto_backfill=True
        )

        # Convert to legacy format for compatibility
        legacy_candles = []
        for candle in candles:
            legacy_candles.append({
                'timestamp': candle['timestamp'].isoformat() if hasattr(candle['timestamp'], 'isoformat') else str(candle['timestamp']),
                'open': candle['open'],
                'high': candle['high'],
                'low': candle['low'],
                'close': candle['close'],
                'volume': candle['volume']
            })

        logger.info(f"✅ Retrieved {len(legacy_candles)} candles from database service")
        return legacy_candles

    except Exception as e:
        logger.error(f"❌ Error using database service, falling back to legacy method: {e}")

        # Fallback to original method
        missing_hist_ranges = get_missing_date_ranges(instrument_key, interval, from_date, to_date)
        for from_r, to_r in missing_hist_ranges:
            fetch_and_save_api_data(instrument_key, interval, from_r, to_r)

    # 2. Always fetch latest intraday data if the range includes today and it's a trading day
    if (to_date >= datetime.date.today() and
        datetime.date.today().weekday() < 5 and  # Monday to Friday
        interval in ["1minute", "30minute"]):
        fetch_intraday_data(instrument_key, interval)

    # 3. Retrieve all candles from the DB for the complete range
    all_candles = get_candles(instrument_key, interval, from_date, to_date)
    return all_candles

def get_intraday_candles_with_fallback(instrument_key: str, interval: str) -> list:
    """
    Database-first intraday candles with smart fallback and historical context.
    Uses database service for intelligent data management.
    """
    logger.info(f"Getting intraday candles for {instrument_key} with database-first approach")

    try:
        # Use database service for smart intraday data retrieval
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data-fetch'))
        from database_service import database_service

        # Get intraday candles with historical context (past 10 days)
        today = datetime.date.today()
        start_date = today - datetime.timedelta(days=10)

        candles = database_service.get_candles_smart(
            instrument_key=instrument_key,
            interval=interval,
            start_date=start_date,
            end_date=today,
            auto_backfill=True
        )

        # Convert to legacy format for compatibility
        legacy_candles = []
        for candle in candles:
            legacy_candles.append({
                'timestamp': candle['timestamp'].isoformat() if hasattr(candle['timestamp'], 'isoformat') else str(candle['timestamp']),
                'open': candle['open'],
                'high': candle['high'],
                'low': candle['low'],
                'close': candle['close'],
                'volume': candle['volume']
            })

        # Check if we have today's data
        today_candles = [c for c in legacy_candles if str(today) in str(c['timestamp'])]

        if legacy_candles:
            logger.info(f"✅ Database-first: Using {len(legacy_candles)} total candles ({len(today_candles)} today's) for {instrument_key}")
            return legacy_candles

    except Exception as e:
        logger.error(f"❌ Error using database service for intraday data: {e}")

    # Fallback to original method
    logger.info("Falling back to original intraday method")
    today = datetime.date.today()

    # Include previous days for analysis context
    # For intraday analysis, we need at least 5-7 trading days of context
    start_date = today - datetime.timedelta(days=10)  # 10 days to ensure 5-7 trading days

    # Get historical data including today
    all_candles = get_candles_for_instrument(instrument_key, interval, start_date, today)

    # Check if we have today's data
    today_candles = [c for c in all_candles if str(today) in str(c['timestamp'])]

    # If no today's data or very little, force fresh API fetch
    if len(today_candles) < 10:  # Less than 10 today's candles suggests missing/incomplete data
        logger.info(f"🚨 Intraday mode: Forcing fresh API fetch for {instrument_key} (found only {len(today_candles)} today's candles)")

        # Force fetch current intraday data
        fetch_intraday_data(instrument_key, interval)

        # Get updated data including the fresh fetch
        all_candles = get_candles_for_instrument(instrument_key, interval, start_date, today)
        today_candles = [c for c in all_candles if str(today) in str(c['timestamp'])]

        if len(today_candles) < 5:  # Still very little today's data
            logger.warning(f"⚠️ Intraday mode: Still limited today's data after API fetch. Market may be closed or data unavailable.")

    logger.info(f"🚨 Intraday mode: Using {len(all_candles)} total candles ({len(today_candles)} today's) for {instrument_key}")
    return all_candles

def _calculate_fibonacci_levels(highs, lows):
    """
    Calculate Fibonacci retracement levels from swing low to swing high.

    Args:
        highs: List of high prices
        lows: List of low prices

    Returns:
        dict: Fibonacci levels with prices and percentages
    """
    if not highs or not lows:
        return None

    # Find swing low and swing high
    swing_low = min(lows)
    swing_high = max(highs)

    # Calculate the range
    price_range = swing_high - swing_low

    # Standard Fibonacci retracement levels (from swing low to swing high)
    fib_levels = {
        '0.0%': swing_high,  # 100% - Swing High (Top)
        '23.6%': swing_high - (price_range * 0.236),  # 76.4% from bottom
        '38.2%': swing_high - (price_range * 0.382),  # 61.8% from bottom
        '50.0%': swing_high - (price_range * 0.500),  # 50% from bottom (Mid-point)
        '61.8%': swing_high - (price_range * 0.618),  # 38.2% from bottom (Golden Ratio)
        '78.6%': swing_high - (price_range * 0.786),  # 21.4% from bottom
        '100.0%': swing_low,  # 0% - Swing Low (Bottom)
    }

    return {
        'levels': fib_levels,
        'swing_low': swing_low,
        'swing_high': swing_high,
        'range': price_range
    }

def _add_fibonacci_to_chart(fig, fib_data, x_range):
    """
    Add Fibonacci retracement levels to the chart.

    Args:
        fig: Plotly figure object
        fib_data: Fibonacci levels data
        x_range: Range of x-axis for drawing lines
    """
    if not fib_data:
        return

    # Colors for different Fibonacci levels
    fib_colors = {
        '0.0%': '#FF6B6B',    # Red for swing high
        '23.6%': '#4ECDC4',   # Teal
        '38.2%': '#45B7D1',   # Blue
        '50.0%': '#96CEB4',   # Green (most important level)
        '61.8%': '#FFEAA7',   # Yellow (golden ratio)
        '78.6%': '#DDA0DD',   # Plum
        '100.0%': '#FF6B6B'   # Red for swing low
    }

    # Add horizontal lines for each Fibonacci level
    for level_name, price in fib_data['levels'].items():
        color = fib_colors.get(level_name, '#888888')

        # Create detailed annotation text with larger, more visible percentages
        if level_name == '0.0%':
            annotation_text = f"<b>📈 0.0%</b> | {price:.2f} | SWING HIGH"
        elif level_name == '100.0%':
            annotation_text = f"<b>📉 100%</b> | {price:.2f} | SWING LOW"
        elif level_name == '50.0%':
            annotation_text = f"<b>🎯 50.0%</b> | {price:.2f} | MID-POINT"
        elif level_name == '61.8%':
            annotation_text = f"<b>⭐ 61.8%</b> | {price:.2f} | GOLDEN RATIO"
        else:
            annotation_text = f"<b>📊 {level_name}</b> | {price:.2f}"

        # Add horizontal line
        fig.add_hline(
            y=price,
            line=dict(
                color=color,
                width=2 if level_name in ['50.0%', '61.8%'] else 1.5 if level_name in ['0.0%', '100.0%'] else 1,
                dash='dot' if level_name in ['0.0%', '100.0%'] else 'solid'
            ),
            annotation_text=annotation_text,
            annotation_position="right",
            annotation=dict(
                font=dict(
                    size=15 if level_name in ['50.0%', '61.8%'] else 14 if level_name in ['0.0%', '100.0%'] else 13,
                    color="white",
                    family="Arial Black"
                ),
                bgcolor=color,
                bordercolor="white",
                borderwidth=3,
                opacity=0.95
            )
        )

        # Add large percentage labels on the left side for better visibility
        if x_range:
            fig.add_annotation(
                x=x_range[0] - 0.5,  # Position to the left of the chart
                y=price,
                text=f"<b style='font-size:18px;'>{level_name}</b>",
                showarrow=False,
                font=dict(
                    size=18 if level_name in ['50.0%', '61.8%'] else 16,
                    color="white",
                    family="Arial Black"
                ),
                bgcolor=color,
                bordercolor="white",
                borderwidth=3,
                opacity=0.95,
                xanchor="center",
                yanchor="middle"
            )

    # Add Fibonacci calculation info box
    range_info = f"Range: {fib_data['range']:.2f} ({fib_data['swing_high']:.2f} - {fib_data['swing_low']:.2f})"

    # Add a text box showing calculation method
    fig.add_annotation(
        x=0.02,
        y=0.98,
        xref="paper",
        yref="paper",
        text=f"<b>📊 Fibonacci Retracement</b><br>" +
             f"📈 Swing High: {fib_data['swing_high']:.2f}<br>" +
             f"📉 Swing Low: {fib_data['swing_low']:.2f}<br>" +
             f"📏 Range: {fib_data['range']:.2f}<br>" +
             f"🔢 Method: Low → High",
        showarrow=False,
        align="left",
        bgcolor="rgba(0,0,0,0.8)",
        bordercolor="rgba(255,255,255,0.3)",
        borderwidth=1,
        font=dict(size=10, color="white", family="Arial"),
        xanchor="left",
        yanchor="top"
    )

    # Add visual range indicator (vertical line at start)
    if x_range:
        fig.add_shape(
            type="line",
            x0=x_range[0], y0=fib_data['swing_low'],
            x1=x_range[0], y1=fib_data['swing_high'],
            line=dict(color="rgba(255,255,255,0.4)", width=3, dash="dash"),
        )

        # Add arrows to show direction
        fig.add_annotation(
            x=x_range[0], y=fib_data['swing_high'],
            text="▲", showarrow=False,
            font=dict(size=16, color="rgba(255,255,255,0.6)"),
            xshift=-10
        )
        fig.add_annotation(
            x=x_range[0], y=fib_data['swing_low'],
            text="▼", showarrow=False,
            font=dict(size=16, color="rgba(255,255,255,0.6)"),
            xshift=-10
        )

def _calculate_ema(prices, period=20):
    """
    Calculate Exponential Moving Average.

    Args:
        prices: List of closing prices
        period: EMA period (default 20)

    Returns:
        List of EMA values
    """
    if len(prices) < period:
        return []

    # Calculate multiplier
    multiplier = 2 / (period + 1)

    # Initialize EMA with SMA of first 'period' values
    ema_values = []
    sma = sum(prices[:period]) / period
    ema_values.append(sma)

    # Calculate EMA for remaining values
    for i in range(period, len(prices)):
        ema = (prices[i] * multiplier) + (ema_values[-1] * (1 - multiplier))
        ema_values.append(ema)

    return ema_values

def _add_ema_to_chart(fig, closes, x_coords, period=20):
    """
    Add 20-period EMA line to the chart.

    Args:
        fig: Plotly figure object
        closes: List of closing prices
        x_coords: X coordinates for the chart
        period: EMA period
    """
    if len(closes) < period:
        return

    ema_values = _calculate_ema(closes, period)
    if not ema_values:
        return

    # Create x coordinates for EMA (starting from period index)
    ema_x = list(range(period, len(closes) + 1))

    # Map to chart columns (approximate)
    if x_coords:
        max_col = max(x_coords)
        ema_x_mapped = [i * max_col / len(closes) for i in ema_x]
    else:
        ema_x_mapped = ema_x

    # Add EMA line (lighter and less dominant)
    fig.add_trace(go.Scatter(
        x=ema_x_mapped,
        y=ema_values,
        mode='lines',
        name=f'{period}-EMA',
        line=dict(color='#FFD700', width=1, dash='dot'),
        opacity=0.4,
        hovertemplate=f'<b>{period}-EMA</b><br>Price: %{{y:.2f}}<extra></extra>'
    ))

def _add_trendlines_to_chart(fig, x_coords, y_coords, pnf_symbols):
    """
    Add basic trend lines to the chart.

    Args:
        fig: Plotly figure object
        x_coords: X coordinates
        y_coords: Y coordinates
        pnf_symbols: P&F symbols (X/O)
    """
    if len(x_coords) < 4:
        return

    # Find swing highs and lows for trend lines
    highs = []
    lows = []

    for i, (x, y, symbol) in enumerate(zip(x_coords, y_coords, pnf_symbols)):
        if symbol == 'X':
            highs.append((x, y))
        else:
            lows.append((x, y))

    # Draw trend line connecting recent highs
    if len(highs) >= 2:
        recent_highs = highs[-3:] if len(highs) >= 3 else highs[-2:]
        if len(recent_highs) >= 2:
            x_vals = [point[0] for point in recent_highs]
            y_vals = [point[1] for point in recent_highs]

            fig.add_trace(go.Scatter(
                x=x_vals,
                y=y_vals,
                mode='lines',
                name='Resistance Trend',
                line=dict(color='#FF6B6B', width=1, dash='dash'),
                opacity=0.5,
                showlegend=True,
                hovertemplate='<b>Resistance Trend</b><br>Price: %{y:.2f}<extra></extra>'
            ))

    # Draw trend line connecting recent lows
    if len(lows) >= 2:
        recent_lows = lows[-3:] if len(lows) >= 3 else lows[-2:]
        if len(recent_lows) >= 2:
            x_vals = [point[0] for point in recent_lows]
            y_vals = [point[1] for point in recent_lows]

            fig.add_trace(go.Scatter(
                x=x_vals,
                y=y_vals,
                mode='lines',
                name='Support Trend',
                line=dict(color='#4ECDC4', width=1, dash='dash'),
                opacity=0.5,
                showlegend=True,
                hovertemplate='<b>Support Trend</b><br>Price: %{y:.2f}<extra></extra>'
            ))

def _add_anchor_points_to_chart(fig, x_coords, y_coords, pnf_symbols, box_pct):
    """
    Add anchor points to the P&F chart.
    Anchor points are the most populated price levels between reference points.

    Args:
        fig: Plotly figure object
        x_coords: X coordinates of P&F points
        y_coords: Y coordinates of P&F points
        pnf_symbols: P&F symbols (X/O)
        box_pct: Box size percentage for price level calculation
    """
    try:
        # Create P&F matrix for anchor point calculation
        pnf_matrix = _create_pnf_matrix(x_coords, y_coords, pnf_symbols, box_pct)

        if pnf_matrix is None or pnf_matrix.empty:
            return

        # Initialize anchor point calculator
        anchor_calculator = AnchorPointCalculator(min_column_separation=7)

        # Calculate anchor points
        anchor_points = anchor_calculator.calculate_anchor_points(pnf_matrix)

        if not anchor_points:
            return

        # Add anchor points to chart
        visualizer = AnchorPointVisualizer()

        for anchor in anchor_points:
            # Determine line style and color based on anchor type
            if anchor.anchor_type == 'zone':
                line_color = '#A23B72'  # Purple for zones
                line_dash = 'dash'
                line_width = 1
                label = f"Anchor Zone ({anchor.box_count} boxes)"
            else:
                line_color = '#2E86AB'  # Blue for single points
                line_dash = 'dot'
                line_width = 2
                label = f"Anchor Point ({anchor.box_count} boxes)"

            # Add horizontal line for anchor point
            fig.add_hline(
                y=anchor.price_level,
                line=dict(
                    color=line_color,
                    width=line_width,
                    dash=line_dash
                ),
                annotation_text=label,
                annotation_position="right",
                annotation=dict(
                    font=dict(size=10, color=line_color),
                    bgcolor="rgba(255,255,255,0.8)",
                    bordercolor=line_color,
                    borderwidth=1
                )
            )

        # Create anchor zones if multiple points exist
        zones = anchor_calculator.create_anchor_zones(anchor_points)

        for i, zone in enumerate(zones):
            # Add zone center line
            fig.add_hline(
                y=zone.zone_center,
                line=dict(color='#FF6B35', width=3, dash='solid'),  # Orange for zone centers
                annotation_text=f"Anchor Zone {i+1} Center ({zone.total_activity} total boxes)",
                annotation_position="right",
                annotation=dict(
                    font=dict(size=12, color='#FF6B35', weight='bold'),
                    bgcolor="rgba(255,255,255,0.9)",
                    bordercolor='#FF6B35',
                    borderwidth=2
                )
            )

            # Add zone boundaries if zone has range
            if zone.zone_range[1] - zone.zone_range[0] > 0:
                fig.add_hline(
                    y=zone.zone_range[0],
                    line=dict(color='#FF6B35', width=1, dash='dash'),
                    annotation_text=f"Zone {i+1} Bottom",
                    annotation_position="right"
                )
                fig.add_hline(
                    y=zone.zone_range[1],
                    line=dict(color='#FF6B35', width=1, dash='dash'),
                    annotation_text=f"Zone {i+1} Top",
                    annotation_position="right"
                )

        logger.info(f"Added {len(anchor_points)} anchor points and {len(zones)} zones to chart")

    except Exception as e:
        logger.error(f"Error adding anchor points to chart: {e}")

def _create_pnf_matrix(x_coords, y_coords, pnf_symbols, box_pct):
    """
    Create a P&F matrix from coordinates and symbols for anchor point calculation.

    Args:
        x_coords: X coordinates
        y_coords: Y coordinates
        pnf_symbols: P&F symbols (X/O)
        box_pct: Box size percentage

    Returns:
        pandas.DataFrame: P&F matrix with columns as time, rows as price levels
    """
    try:
        if not x_coords or not y_coords or not pnf_symbols:
            return None

        # Calculate price levels based on box size
        min_price = min(y_coords)
        max_price = max(y_coords)
        box_size = min_price * box_pct

        # Create price levels
        price_levels = []
        current_price = min_price
        while current_price <= max_price:
            price_levels.append(round(current_price, 2))
            current_price += box_size

        # Create matrix columns (time points)
        max_column = max(x_coords) if x_coords else 0
        columns = list(range(int(max_column) + 1))

        # Initialize matrix with empty values
        matrix_data = pd.DataFrame(index=price_levels, columns=columns)
        matrix_data = matrix_data.fillna('')

        # Fill matrix with X's and O's
        for x, y, symbol in zip(x_coords, y_coords, pnf_symbols):
            # Find closest price level
            closest_price = min(price_levels, key=lambda p: abs(p - y))
            col_index = int(x)

            if col_index < len(columns):
                matrix_data.loc[closest_price, col_index] = symbol

        return matrix_data

    except Exception as e:
        logger.error(f"Error creating P&F matrix: {e}")
        return None

def generate_pnf_chart_html(instrument_key, box_pct=0.01, reversal=3, interval="day", time_range="2months", mode=None, show_fibonacci=True, show_ema=True, show_trendlines=True, show_anchor_points=True):
    """
    Generates the HTML for a self-contained Plotly P&F chart with enhanced features.
    It handles fetching data from the local DB and Upstox API.

    Args:
        instrument_key: Stock instrument key
        box_pct: Box size percentage
        reversal: Reversal amount
        interval: Data interval ("day", "1minute", "3minute", "30minute")
        time_range: Time range for 1-minute charts ("1month", "2months")
        mode: Chart mode
        show_fibonacci: Show Fibonacci retracement levels
        show_ema: Show 20-period EMA line
        show_trendlines: Show trend lines
        show_anchor_points: Show anchor points (most populated price levels)
    """
    # Handle both Upstox and Dhan instrument keys
    stock_info = crud.get_stock_by_instrument_key(instrument_key)

    if not stock_info:
        # Check if this is a Dhan instrument key
        if instrument_key.startswith('DHAN_'):
            # Extract symbol from watchlist (Dhan keys are in watchlist)
            watchlist = crud.get_watchlist_details()
            dhan_stock = next((s for s in watchlist if s.instrument_key == instrument_key), None)
            if dhan_stock:
                symbol = dhan_stock.symbol
                stock_info = {'symbol': symbol, 'name': dhan_stock.company_name or symbol}
            else:
                return f"<h3>Dhan stock not found in watchlist: {instrument_key}</h3>"
        else:
            return "<h3>Stock not found</h3>"
    else:
        symbol = stock_info['symbol']

    today = datetime.date.today()

    # For intraday intervals, fetch data till current time (not just end of day)
    # This ensures charts show the latest data during market hours
    end_date_hist = today  # Default end date for daily charts

    # Handle intraday mode - use only current day data
    if mode == "intraday" or time_range == "today":
        start_date_hist = today  # Only today's data for intraday
    else:
        # Adjust date range based on interval
        if interval == "day":
            start_date_hist = today - datetime.timedelta(days=365)  # 1 year for daily
        elif interval == "1minute":
            # Use time_range parameter for 1-minute charts
            if time_range == "1month":
                start_date_hist = today - datetime.timedelta(days=30)   # 1 month for 1-minute data
            else:  # "2months" or default
                start_date_hist = today - datetime.timedelta(days=60)   # 2 months for 1-minute data
        elif interval == "3minute":
            # 3minute is not supported by Upstox API, use 1minute data instead
            start_date_hist = today - datetime.timedelta(days=30)   # 1 month for 1-minute data (to aggregate to 3min)
        elif interval == "30minute":
            start_date_hist = today - datetime.timedelta(days=30)   # 30 days for 30-minute data
        else:
            start_date_hist = today - datetime.timedelta(days=365)  # Default to 1 year

    # Handle different data fetching modes
    if mode == "intraday":
        # For intraday mode, prioritize current day data and force API fetch if needed
        all_candles = get_intraday_candles_with_fallback(instrument_key, interval)
    elif interval == "3minute":
        # For 3-minute charts, fetch 1-minute data and aggregate
        candles_1min = get_candles_for_instrument(instrument_key, "1minute", start_date_hist, end_date_hist)
        all_candles = aggregate_to_3minute(candles_1min)
    else:
        # For intraday intervals during market hours, ensure we get latest data
        # by triggering backfill if needed
        if interval in ["1minute", "30minute"] and today.weekday() < 5:  # Monday to Friday
            # Fetch latest data from Dhan API before getting from database
            try:
                import sys
                import os
                sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data-fetch'))
                from dhan_live_data_service import dhan_live_data_service

                # Extract security_id from instrument_key (format: DHAN_3518)
                if instrument_key.startswith('DHAN_'):
                    security_id = instrument_key.replace('DHAN_', '')

                    # Backfill missing data to ensure we have latest candles
                    logger.info(f"📊 Ensuring latest data for chart: {symbol}")
                    dhan_live_data_service.backfill_missing_data(instrument_key, symbol, security_id)
            except Exception as e:
                logger.warning(f"⚠️ Could not fetch latest data for chart: {e}")

        all_candles = get_candles_for_instrument(instrument_key, interval, start_date_hist, end_date_hist)

    if not all_candles:
        logger.warning(f"Could not generate P&F chart for {instrument_key} due to missing data.")
        return "<h3>Could not find or fetch any chart data for this stock.</h3>"

    highs = [float(c['high']) for c in all_candles]
    lows = [float(c['low']) for c in all_candles]
    closes = [float(c['close']) for c in all_candles]

    x_coords, y_coords, pnf_symbols = _calculate_pnf_points(highs, lows, box_pct, reversal)

    if not x_coords:
        return "<p>Not enough data to generate a Point and Figure chart.</p>"

    # Separate X's and O's for plotting
    x_x = [x for x, s in zip(x_coords, pnf_symbols) if s == 'X']
    y_x = [y for y, s in zip(y_coords, pnf_symbols) if s == 'X']
    x_o = [x for x, s in zip(x_coords, pnf_symbols) if s == 'O']
    y_o = [y for y, s in zip(y_coords, pnf_symbols) if s == 'O']

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x_x, y=y_x, mode='text', text='X', name='Uptrend (X)', textfont=dict(color='#00b069', size=10)))
    fig.add_trace(go.Scatter(x=x_o, y=y_o, mode='text', text='O', name='Downtrend (O)', textfont=dict(color='#fe3d62', size=10)))

    # Calculate and add Fibonacci retracement levels
    if show_fibonacci:
        fib_data = _calculate_fibonacci_levels(highs, lows)
        if fib_data:
            x_range = [min(x_coords), max(x_coords)] if x_coords else [0, 1]
            _add_fibonacci_to_chart(fig, fib_data, x_range)

    # Add 20-EMA line
    if show_ema and closes:
        _add_ema_to_chart(fig, closes, x_coords)

    # Add trend lines
    if show_trendlines and x_coords:
        _add_trendlines_to_chart(fig, x_coords, y_coords, pnf_symbols)

    # Add anchor points
    if show_anchor_points and x_coords and y_coords:
        _add_anchor_points_to_chart(fig, x_coords, y_coords, pnf_symbols, box_pct)

    # Create title with mode and time range info
    title = f'{symbol} - P&F (High/Low, {box_pct*100:.2f}% Box, {reversal} Box Reversal)'
    if mode == "intraday":
        # Count today's candles for intraday mode
        today = datetime.date.today()
        today_candles = [c for c in all_candles if str(today) in str(c['timestamp'])]
        title += f' - 🚨 LIVE INTRADAY (Last 7 days + {len(today_candles)} live candles)'
    elif interval == "1minute":
        time_range_text = "Last 1 Month" if time_range == "1month" else "Last 2 Months"
        title += f' - {time_range_text}'

    # Calculate appropriate Y-axis range from actual data
    if y_coords:
        y_min = min(y_coords)
        y_max = max(y_coords)
        y_padding = (y_max - y_min) * 0.1  # 10% padding
        y_range = [y_min - y_padding, y_max + y_padding]
    else:
        y_range = None

    fig.update_layout(
        title=title,
        template='plotly_dark',
        xaxis_title="Column", yaxis_title="Price",
        xaxis=dict(showgrid=False, tickmode='linear', tick0=1, dtick=1),
        yaxis=dict(
            tickformat='.2f',
            range=y_range,  # Set explicit range based on data
            showgrid=True,
            gridcolor='rgba(128, 128, 128, 0.2)'
        ),
        showlegend=True,
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
        margin=dict(l=20, r=20, t=40, b=20),
        plot_bgcolor="#111111", paper_bgcolor="#111111", font_color="white"
    )

    # Add data availability annotation and expose meta for parent page
    first_ts_str = ""
    last_ts_str = ""
    last_price = closes[-1] if closes else 0

    try:
        first_ts = all_candles[0]['timestamp']
        last_ts = all_candles[-1]['timestamp']
        first_ts_str = first_ts.isoformat(sep=' ') if hasattr(first_ts, 'isoformat') else str(first_ts)
        last_ts_str = last_ts.isoformat(sep=' ') if hasattr(last_ts, 'isoformat') else str(last_ts)

        # Format last timestamp for display
        if hasattr(last_ts, 'strftime'):
            last_ts_display = last_ts.strftime('%d-%b %H:%M')
        else:
            last_ts_display = str(last_ts).split('.')[0]

        # Add LTP (Last Traded Price) annotation at top-left
        fig.add_annotation(
            xref='paper', yref='paper', x=0.02, y=0.98,
            text=f"<b>LTP: ₹{last_price:.2f}</b><br>{last_ts_display}",
            showarrow=False,
            font=dict(size=14, color='#00ff00'),
            align='left',
            bgcolor='rgba(0,0,0,0.7)',
            bordercolor='rgba(0,255,0,0.5)',
            borderwidth=2
        )

        # Small footer-right annotation with data range (show only date, not full timestamp)
        first_date = first_ts_str.split('T')[0] if 'T' in first_ts_str else first_ts_str.split(' ')[0]
        last_date = last_ts_str.split('T')[0] if 'T' in last_ts_str else last_ts_str.split(' ')[0]

        fig.add_annotation(
            xref='paper', yref='paper', x=0.98, y=0.02,
            text=f"Data: {first_date} to {last_date}",
            showarrow=False,
            font=dict(size=10, color='#ddd'),
            align='right',
            bgcolor='rgba(0,0,0,0.4)',
            bordercolor='rgba(255,255,255,0.2)',
            borderwidth=1
        )
    except Exception as e:
        logger.warning(f"Unable to add data range annotation: {e}")

    # Generate clean HTML without any potential syntax issues
    try:
        chart_html = fig.to_html(
            full_html=False,
            include_plotlyjs='cdn',
            config={'displayModeBar': True, 'responsive': True}
        )
        # Prepend a hidden meta div with data range for the parent page to read
        meta_div = f'<div id="chart-meta" data-start="{first_ts_str}" data-end="{last_ts_str}" style="display:none;"></div>'
        return meta_div + chart_html
    except Exception as e:
        logger.error(f"Error generating chart HTML: {e}")
        return f"<p>Error generating chart: {str(e)}</p>"

# --- Helper Functions for Data Fetching and DB Interaction ---

def get_missing_date_ranges(instrument_key: str, interval: str, start_date: datetime.date, end_date: datetime.date) -> list[tuple]:
    """Compares dates in the database with the required date range to find gaps."""
    # Convert to datetime for MongoDB query
    start_datetime = datetime.datetime.combine(start_date, datetime.time.min)
    end_datetime = datetime.datetime.combine(end_date, datetime.time.max)

    # Get existing candles from MongoDB
    candles = get_candles_mongo(
        instrument_key=instrument_key,
        interval=interval,
        start_time=start_datetime,
        end_time=end_datetime
    )

    existing_dates = {c["timestamp"].date() for c in candles}
    required_dates = set(pd.date_range(start=start_date, end=end_date, freq='B').date)

    missing_dates = sorted(list(required_dates - existing_dates))
    if not missing_dates:
        return []

    # Group consecutive missing dates into ranges
    missing_ranges = []
    if missing_dates:
        start_range = missing_dates[0]
        for i in range(1, len(missing_dates)):
            if (missing_dates[i] - missing_dates[i-1]).days > 1:
                missing_ranges.append((start_range, missing_dates[i-1]))
                start_range = missing_dates[i]
        missing_ranges.append((start_range, missing_dates[-1]))
    return missing_ranges

def get_candles(instrument_key: str, interval: str, start_date: datetime.date, end_date: datetime.date) -> list[dict]:
    """Fetches candle data from MongoDB."""
    # Convert date objects to datetime objects for proper comparison
    start_datetime = datetime.datetime.combine(start_date, datetime.time.min)  # 00:00:00
    end_datetime = datetime.datetime.combine(end_date, datetime.time.max)    # 23:59:59.999999

    # Use MongoDB service
    candles = get_candles_mongo(
        instrument_key=instrument_key,
        interval=interval,
        start_time=start_datetime,
        end_time=end_datetime
    )

    return [
        {"timestamp": c["timestamp"], "open": c["open"], "high": c["high"], "low": c["low"], "close": c["close"], "volume": c["volume"]}
        for c in candles
    ]

def save_candles(instrument_key: str, interval: str, candles: list):
    """Saves a batch of candle data from the API to MongoDB."""
    to_insert = []
    for candle_data in candles:
        if not candle_data or len(candle_data) < 6:
            continue

        try:
            timestamp = datetime.datetime.fromisoformat(candle_data[0])
        except ValueError:
            logger.warning(f"Could not parse timestamp '{candle_data[0]}'. Skipping candle.")
            continue

        to_insert.append({
            "instrument_key": instrument_key,
            "interval": interval,
            "timestamp": timestamp,
            "open": float(candle_data[1]),
            "high": float(candle_data[2]),
            "low": float(candle_data[3]),
            "close": float(candle_data[4]),
            "volume": int(candle_data[5]),
            "oi": int(candle_data[6]) if len(candle_data) > 6 else 0
        })

    if not to_insert:
        return

    try:
        # Use MongoDB bulk insert
        insert_candles_bulk(to_insert)
        logger.info(f"Successfully saved {len(to_insert)} candles for {instrument_key} ({interval})")
    except Exception as e:
        logger.error(f"Error saving candles to MongoDB for {instrument_key}: {e}")

def fetch_intraday_data(instrument_key: str, interval: str):
    """
    Fetch and save current day's intraday data.
    This should be called to get the latest intraday data for the current trading day.
    """
    if interval not in ["1minute", "30minute"]:
        return

    api_instance = upstox_client.HistoryApi(api_client)

    try:
        logger.info(f"Fetching current intraday data for {instrument_key} ({interval})...")
        api_response = api_instance.get_intra_day_candle_data(
            instrument_key=instrument_key,
            interval=interval,
            api_version="v2"
        )

        if api_response.status == 'success' and api_response.data.candles:
            save_candles(instrument_key, interval, api_response.data.candles)
            logger.info(f"✅ Successfully saved {len(api_response.data.candles)} current intraday candles for {instrument_key} ({interval})")
        else:
            logger.info(f"No current intraday data available for {instrument_key} ({interval})")

    except Exception as e:
        logger.warning(f"Could not fetch current intraday data for {instrument_key} ({interval}). This can be normal outside market hours. Error: {e}")

def fetch_and_save_api_data(instrument_key: str, interval: str, from_date: datetime.date, to_date: datetime.date):
    """Fetches historical data from the appropriate API (Dhan or Upstox) and saves it."""
    logger.info(f"Fetching from API for {instrument_key} from {from_date} to {to_date}...")

    # Check if this is a Dhan instrument key
    if instrument_key.startswith('DHAN_'):
        logger.info(f"⚠️ Dhan instrument key detected: {instrument_key}")
        logger.info(f"⚠️ Dhan data should be fetched via database_service auto-backfill, not this legacy function")
        logger.info(f"⚠️ Skipping Upstox API call for Dhan instrument")
        return

    api_instance = upstox_client.HistoryApi(api_client)

    # For 1-minute data over large date ranges, we might need to batch the requests
    # Upstox API might have limitations on how much data can be fetched in one call
    if interval == "1minute" and (to_date - from_date).days > 30:
        logger.info(f"Large date range detected for 1-minute data. Batching requests...")
        current_date = from_date
        while current_date <= to_date:
            batch_end_date = min(current_date + datetime.timedelta(days=30), to_date)
            _fetch_single_batch(api_instance, instrument_key, interval, current_date, batch_end_date)
            current_date = batch_end_date + datetime.timedelta(days=1)
    else:
        _fetch_single_batch(api_instance, instrument_key, interval, from_date, to_date)

def _fetch_single_batch(api_instance, instrument_key: str, interval: str, from_date: datetime.date, to_date: datetime.date):
    """Fetches a single batch of data from the API."""
    try:
        api_response = api_instance.get_historical_candle_data(
            instrument_key=instrument_key,
            interval=interval,
            to_date=to_date.strftime('%Y-%m-%d'),
            api_version="v2"
        )
        if api_response.status == 'success':
            save_candles(instrument_key, interval, api_response.data.candles)
            logger.info(f"Successfully saved {len(api_response.data.candles)} candles for {instrument_key} ({interval})")
    except Exception as e:
        logger.error(f"Failed to fetch historical data for {instrument_key} from {from_date} to {to_date}: {e}")

    # Fetch and save intraday data (if applicable)
    if interval in ["1minute", "30minute"] and to_date >= datetime.date.today():
        try:
            api_response = api_instance.get_intra_day_candle_data(
                instrument_key=instrument_key,
                interval=interval,
                api_version="v2"
            )
            if api_response.status == 'success' and api_response.data.candles:
                save_candles(instrument_key, interval, api_response.data.candles)
                logger.info(f"Successfully saved {len(api_response.data.candles)} intraday candles for {instrument_key} ({interval})")
            else:
                logger.info(f"No new intraday data available for {instrument_key}.")
        except Exception as e:
            logger.warning(f"Could not fetch intraday data for {instrument_key}. This can be normal outside market hours. Error: {e}")


# --- P&F Calculation Logic ---
def _calculate_pnf_points(highs: List[float], lows: List[float], box_pct: float, reversal: int) -> Tuple[List[int], List[float], List[str]]:
    if not highs or len(highs) < 2:
        return [], [], []

    x_coords, y_coords, symbols = [], [], []
    col_idx = 1
    direction = 0  # 1 for up, -1 for down
    last_price_level = highs[0]
    box_up_thresh = last_price_level * (1 + box_pct)
    box_down_thresh = last_price_level / (1 + box_pct)

    if highs[0] >= box_up_thresh:
        direction = 1
        x_coords.extend([col_idx, col_idx]); y_coords.extend([last_price_level, box_up_thresh]); symbols.extend(['X', 'X'])
        last_price_level = box_up_thresh
    elif lows[0] <= box_down_thresh:
        direction = -1
        x_coords.extend([col_idx, col_idx]); y_coords.extend([last_price_level, box_down_thresh]); symbols.extend(['O', 'O'])
        last_price_level = box_down_thresh
    
    for i in range(1, len(highs)):
        high = highs[i]
        low = lows[i]

        if direction == 1:  # Uptrend (X column)
            reversal_level = last_price_level / ((1 + box_pct) ** reversal)
            if low <= reversal_level:
                direction = -1
                col_idx += 1
                new_level = last_price_level / (1 + box_pct)
                while low <= new_level:
                    x_coords.append(col_idx); y_coords.append(new_level); symbols.append('O')
                    new_level /= (1 + box_pct)
                last_price_level = y_coords[-1] if y_coords else new_level * (1+box_pct)
            else:
                new_level = last_price_level * (1 + box_pct)
                while high >= new_level:
                     x_coords.append(col_idx); y_coords.append(new_level); symbols.append('X')
                     last_price_level = new_level
                     new_level *= (1 + box_pct)
        elif direction == -1:  # Downtrend (O column)
            reversal_level = last_price_level * ((1 + box_pct) ** reversal)
            if high >= reversal_level:
                direction = 1
                col_idx += 1
                new_level = last_price_level * (1 + box_pct)
                while high >= new_level:
                    x_coords.append(col_idx); y_coords.append(new_level); symbols.append('X')
                    new_level *= (1 + box_pct)
                last_price_level = y_coords[-1] if y_coords else new_level / (1+box_pct)
            else:
                new_level = last_price_level / (1 + box_pct)
                while low <= new_level:
                    x_coords.append(col_idx); y_coords.append(new_level); symbols.append('O')
                    last_price_level = new_level
                    new_level /= (1 + box_pct)
        else: # Determining initial direction
            if high >= box_up_thresh:
                direction = 1
                last_price_level = box_up_thresh
                x_coords.extend([col_idx, col_idx]); y_coords.extend([highs[0], box_up_thresh]); symbols.extend(['X', 'X'])
            elif low <= box_down_thresh:
                direction = -1
                last_price_level = box_down_thresh
                x_coords.extend([col_idx, col_idx]); y_coords.extend([highs[0], box_down_thresh]); symbols.extend(['O', 'O'])
    return x_coords, y_coords, symbols

def aggregate_to_3minute(candles_1min: list) -> list:
    """
    Aggregate 1-minute candle data to 3-minute intervals.

    Args:
        candles_1min: List of 1-minute candle dictionaries

    Returns:
        List of 3-minute candle dictionaries
    """
    if not candles_1min:
        return []

    # Convert to DataFrame for easier manipulation
    df = pd.DataFrame(candles_1min)

    # Convert timestamp to datetime
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.set_index('timestamp')

    # Convert price columns to float
    for col in ['open', 'high', 'low', 'close']:
        df[col] = df[col].astype(float)
    df['volume'] = df['volume'].astype(int)

    # Resample to 3-minute intervals
    # 'min' means minute, so '3min' means 3 minutes (updated from deprecated 'T')
    agg_dict = {
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'volume': 'sum'
    }

    df_3min = df.resample('3min').agg(agg_dict).dropna()

    # Convert back to list of dictionaries
    result = []
    for timestamp, row in df_3min.iterrows():
        result.append({
            'timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'open': str(row['open']),
            'high': str(row['high']),
            'low': str(row['low']),
            'close': str(row['close']),
            'volume': str(int(row['volume']))
        })

    return result

def get_latest_close(instrument_key: str) -> float:
    """Gets the last traded price from Redis or falls back to the DB."""
    # ... existing code ...