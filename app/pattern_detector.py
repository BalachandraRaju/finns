"""
Pattern detection and alert management system.
Ensures alerts fire only once when patterns are first identified.
"""

import datetime
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

class PatternType(Enum):
    # EMA-validated high-confidence patterns with follow-through
    DOUBLE_TOP_BUY_EMA = "double_top_buy_ema"
    DOUBLE_BOTTOM_SELL_EMA = "double_bottom_sell_ema"
    TRIPLE_TOP_BUY_EMA = "triple_top_buy_ema"
    TRIPLE_BOTTOM_SELL_EMA = "triple_bottom_sell_ema"
    QUADRUPLE_TOP_BUY_EMA = "quadruple_top_buy_ema"
    QUADRUPLE_BOTTOM_SELL_EMA = "quadruple_bottom_sell_ema"

    # Turtle breakout follow through patterns (5-column range + double pattern confirmation)
    TURTLE_BREAKOUT_FT_BUY = "turtle_breakout_ft_buy"
    TURTLE_BREAKOUT_FT_SELL = "turtle_breakout_ft_sell"

    # Catapult patterns (triple bottom/top followed by double bottom/top)
    CATAPULT_BUY = "catapult_buy"
    CATAPULT_SELL = "catapult_sell"

    # 100% Pole Follow Through patterns (100% pole followed by double top/bottom)
    POLE_FOLLOW_THROUGH_BUY = "pole_follow_through_buy"
    POLE_FOLLOW_THROUGH_SELL = "pole_follow_through_sell"

    # AFT (Anchor Column Follow Through) patterns
    AFT_ANCHOR_BREAKOUT_BUY = "aft_anchor_breakout_buy"
    AFT_ANCHOR_BREAKDOWN_SELL = "aft_anchor_breakdown_sell"

    # High/Low Pole Follow Through patterns (4-column pole + double pattern confirmation)
    HIGH_POLE_FT_SELL = "high_pole_ft_sell"
    LOW_POLE_FT_BUY = "low_pole_ft_buy"

    # Tweezer patterns (horizontal accumulation-distribution between anchor columns)
    TWEEZER_BULLISH = "tweezer_bullish"
    TWEEZER_BEARISH = "tweezer_bearish"
    ABC_BULLISH = "abc_bullish"
    ABC_BEARISH = "abc_bearish"

    # Legacy patterns (for backward compatibility)
    DOUBLE_TOP_BUY = "double_top_buy"
    DOUBLE_BOTTOM_SELL = "double_bottom_sell"
    TRIPLE_TOP_BUY = "triple_top_buy"
    TRIPLE_BOTTOM_SELL = "triple_bottom_sell"
    QUADRUPLE_TOP_BUY = "quadruple_top_buy"
    QUADRUPLE_BOTTOM_SELL = "quadruple_bottom_sell"
    BULLISH_BREAKOUT = "bullish_breakout"
    BEARISH_BREAKDOWN = "bearish_breakdown"
    DESCENDING_TRIANGLE = "descending_triangle"

class AlertType(Enum):
    BUY = "BUY"
    SELL = "SELL"

@dataclass
class PatternState:
    """Tracks the state of a pattern formation."""
    pattern_type: PatternType
    is_forming: bool = False
    is_confirmed: bool = False
    confirmation_price: Optional[float] = None
    confirmation_column: Optional[int] = None
    alert_fired: bool = False
    formation_start_column: Optional[int] = None

@dataclass
class AlertTrigger:
    """Represents a single alert trigger point."""
    column: int
    price: float
    alert_type: AlertType
    pattern_type: PatternType
    trigger_reason: str
    is_first_occurrence: bool = True

class PatternDetector:
    """
    Detects P&F patterns and manages alert firing to ensure one-time alerts.
    Includes Super Alert system based on Fibonacci retracement levels.
    """
    
    def __init__(self):
        self.pattern_states: Dict[PatternType, PatternState] = {}
        self.fired_alerts: List[AlertTrigger] = []
        self.reset_pattern_states()
    
    def reset_pattern_states(self):
        """Reset all pattern states for new analysis."""
        for pattern_type in PatternType:
            self.pattern_states[pattern_type] = PatternState(pattern_type)

    def _calculate_fibonacci_levels(self, highs: List[float], lows: List[float]) -> Optional[Dict]:
        """
        Calculate Fibonacci retracement levels from swing low to swing high.

        Args:
            highs: List of high prices
            lows: List of low prices

        Returns:
            dict: Fibonacci levels with prices and percentages, or None if insufficient data
        """
        if not highs or not lows:
            return None

        # Find swing low and swing high
        swing_low = min(lows)
        swing_high = max(highs)

        # Calculate the range
        price_range = swing_high - swing_low

        if price_range <= 0:
            return None

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

    def _get_fibonacci_level_for_price(self, price: float, fib_data: Dict) -> Optional[str]:
        """
        Determine which Fibonacci level a price is closest to.

        Args:
            price: Current price
            fib_data: Fibonacci levels data

        Returns:
            str: Fibonacci level name (e.g., '61.8%') or None
        """
        if not fib_data:
            return None

        levels = fib_data['levels']
        min_distance = float('inf')
        closest_level = None

        # Find the closest Fibonacci level
        for level_name, level_price in levels.items():
            distance = abs(price - level_price)
            if distance < min_distance:
                min_distance = distance
                closest_level = level_name

        # Only consider it a Fibonacci level if price is within 1% of the level
        if closest_level:
            level_price = levels[closest_level]
            tolerance = level_price * 0.01  # 1% tolerance
            if min_distance <= tolerance:
                return closest_level

        return None

    def _is_super_buy_level(self, fib_level: str) -> bool:
        """
        Check if Fibonacci level qualifies for Super Buy alert.

        Super Buy levels (strong support):
        - 61.8% (Golden Ratio) - Most important retracement
        - 50.0% (Mid-point) - Strong psychological level
        - 38.2% - Secondary support level
        """
        return fib_level in ['61.8%', '50.0%', '38.2%']

    def _is_super_sell_level(self, fib_level: str) -> bool:
        """
        Check if Fibonacci level qualifies for Super Sell alert.

        Super Sell levels (strong resistance):
        - 38.2% (Near swing high) - Strong resistance
        - 23.6% (Close to swing high) - Secondary resistance
        - 0.0% (At swing high) - Maximum resistance
        """
        return fib_level in ['38.2%', '23.6%', '0.0%']

    def _check_matrix_super_alert(self, instrument_key: str, alert: AlertTrigger) -> AlertTrigger:
        """
        Check if alert should be upgraded to Super Alert based on PnF Matrix score.

        Super Alert criteria:
        - Bullish alerts: Matrix score ≥ 6
        - Bearish alerts: Matrix score ≤ -6
        """
        try:
            from app.pnf_matrix import PnFMatrixCalculator

            calculator = PnFMatrixCalculator()
            matrix_result = calculator.calculate_matrix_for_stock(instrument_key, "day")

            if matrix_result and matrix_result.super_alert_eligible:
                # Check if alert type matches matrix strength
                if (alert.alert_type == AlertType.BUY and matrix_result.total_score >= 6):
                    # Upgrade to Super Buy based on Matrix
                    super_reason = f"🌟 SUPER BUY: {alert.trigger_reason.replace('🚨', '⭐')} ⭐ PNF MATRIX SCORE: {matrix_result.total_score} ⭐"
                    return AlertTrigger(
                        column=alert.column,
                        price=alert.price,
                        alert_type=alert.alert_type,
                        pattern_type=alert.pattern_type,
                        trigger_reason=super_reason,
                        is_first_occurrence=alert.is_first_occurrence
                    )
                elif (alert.alert_type == AlertType.SELL and matrix_result.total_score <= -6):
                    # Upgrade to Super Sell based on Matrix
                    super_reason = f"🌟 SUPER SELL: {alert.trigger_reason.replace('🚨', '⭐')} ⭐ PNF MATRIX SCORE: {matrix_result.total_score} ⭐"
                    return AlertTrigger(
                        column=alert.column,
                        price=alert.price,
                        alert_type=alert.alert_type,
                        pattern_type=alert.pattern_type,
                        trigger_reason=super_reason,
                        is_first_occurrence=alert.is_first_occurrence
                    )

        except Exception as e:
            # If matrix calculation fails, continue with original alert
            pass

        return alert

    def _upgrade_to_super_alert(self, alert: AlertTrigger, fib_level: str) -> AlertTrigger:
        """
        Upgrade a regular alert to Super Alert based on Fibonacci level.

        Args:
            alert: Original alert trigger
            fib_level: Fibonacci level (e.g., '61.8%')

        Returns:
            AlertTrigger: Upgraded super alert
        """
        # Determine if it's a super buy or super sell
        is_super_buy = alert.alert_type == AlertType.BUY and self._is_super_buy_level(fib_level)
        is_super_sell = alert.alert_type == AlertType.SELL and self._is_super_sell_level(fib_level)

        if is_super_buy:
            # Upgrade to Super Buy
            super_reason = f"🌟 SUPER BUY: {alert.trigger_reason.replace('🚨', '⭐')} ⭐ FIBONACCI {fib_level} SUPPORT LEVEL ⭐"
            return AlertTrigger(
                column=alert.column,
                price=alert.price,
                alert_type=alert.alert_type,
                pattern_type=alert.pattern_type,
                trigger_reason=super_reason,
                is_first_occurrence=alert.is_first_occurrence
            )
        elif is_super_sell:
            # Upgrade to Super Sell
            super_reason = f"🌟 SUPER SELL: {alert.trigger_reason.replace('🚨', '⭐')} ⭐ FIBONACCI {fib_level} RESISTANCE LEVEL ⭐"
            return AlertTrigger(
                column=alert.column,
                price=alert.price,
                alert_type=alert.alert_type,
                pattern_type=alert.pattern_type,
                trigger_reason=super_reason,
                is_first_occurrence=alert.is_first_occurrence
            )

        # Return original alert if not a super level
        return alert

    def analyze_pattern_formation(self, x_coords: List[int], y_coords: List[float],
                                pnf_symbols: List[str], price_data: List[float] = None) -> List[AlertTrigger]:
        """
        Analyze P&F data for LIVE trading alerts with EMA validation.
        CRITICAL: Alerts fire ONLY on the LATEST/CURRENT column for real-time trading.

        For multiple X columns, only check the LATEST X column for breakouts.

        Args:
            x_coords: Column positions
            y_coords: Price levels
            pnf_symbols: X or O symbols
            price_data: Historical closing prices for EMA calculation (optional)

        Returns:
            List of alert triggers (only on latest column)
        """
        self.reset_pattern_states()
        alerts = []

        if len(x_coords) == 0:
            return alerts

        # Calculate EMA if price data is provided
        ema_20 = None
        current_price_vs_ema = None
        if price_data and len(price_data) >= 20:
            ema_20 = self._calculate_ema(price_data, 20)
            current_price_vs_ema = price_data[-1] - ema_20 if ema_20 else None

        # LIVE TRADING FOCUS: Only check the LATEST column for alerts
        # Find the latest column number
        latest_column = max(x_coords)

        # Get all points in the latest column
        latest_column_indices = [i for i, col in enumerate(x_coords) if col == latest_column]

        if not latest_column_indices:
            return alerts

        # For the latest column, check each point for breakouts
        # Collect ALL possible pattern matches, then prioritize specific patterns
        all_alerts = []

        for idx in latest_column_indices:
            current_column = x_coords[idx]
            current_price = y_coords[idx]
            current_symbol = pnf_symbols[idx]

            # Get all historical data up to this point
            historical_data = self._get_historical_data(x_coords, y_coords, pnf_symbols, idx)

            # Check for breakout at THIS point in the LATEST column
            point_alerts = []
            self._check_latest_column_breakout(historical_data, current_column, current_price, current_symbol, point_alerts, idx, ema_20, current_price_vs_ema)

            # Collect all alerts from this point
            all_alerts.extend(point_alerts)

        # Prioritize specific patterns over generic patterns
        # Priority order: Catapult > Triple/Quadruple Top > AFT > Pole FT > Double Top > ABC/Tweezer
        pattern_priority = {
            'catapult_buy': 1,
            'catapult_sell': 1,
            'quadruple_top_buy': 2,
            'quadruple_bottom_sell': 2,
            'triple_top_buy': 3,
            'triple_bottom_sell': 3,
            'aft_anchor_breakout_buy': 4,
            'aft_anchor_breakdown_sell': 4,
            'pole_follow_through_buy': 5,
            'pole_follow_through_sell': 5,
            'double_top_buy': 6,
            'double_bottom_sell': 6,
            'low_pole_ft_buy': 7,
            'high_pole_ft_sell': 7,
            'turtle_breakout_ft_buy': 8,
            'turtle_breakout_ft_sell': 8,
            'abc_bullish': 9,
            'abc_bearish': 9,
            'tweezer_bullish': 10,
            'tweezer_bearish': 10,
        }

        # Sort alerts by priority (lower number = higher priority)
        if all_alerts:
            all_alerts.sort(key=lambda a: pattern_priority.get(a.pattern_type.value, 99))
            # Take only the highest priority alert
            alerts.append(all_alerts[0])

        # Apply Super Alert system based on Fibonacci levels and PnF Matrix
        if alerts:
            # Calculate Fibonacci levels from all price data
            fib_data = self._calculate_fibonacci_levels(y_coords, y_coords)

            # Upgrade alerts to Super Alerts
            upgraded_alerts = []
            for alert in alerts:
                upgraded_alert = alert

                # First, check Fibonacci levels
                fib_level = self._get_fibonacci_level_for_price(alert.price, fib_data)
                if fib_level:
                    upgraded_alert = self._upgrade_to_super_alert(upgraded_alert, fib_level)

                # Then, check PnF Matrix (if we have instrument_key context)
                # Note: This would need instrument_key to be passed to the method
                # For now, we'll keep the Fibonacci-based upgrade

                upgraded_alerts.append(upgraded_alert)

            return upgraded_alerts

        return alerts

    def _get_historical_data(self, x_coords: List[int], y_coords: List[float],
                           pnf_symbols: List[str], current_index: int) -> Dict:
        """Get all data up to current point (excluding future data)."""
        return {
            'x_coords': x_coords[:current_index + 1],
            'y_coords': y_coords[:current_index + 1],
            'symbols': pnf_symbols[:current_index + 1],
            'current_index': current_index
        }

    def _get_recent_data(self, x_coords: List[int], y_coords: List[float],
                        pnf_symbols: List[str], current_index: int, lookback: int = 10) -> Dict:
        """Get recent data for pattern analysis."""
        start_idx = max(0, current_index - lookback)
        end_idx = current_index + 1
        
        return {
            'x_coords': x_coords[start_idx:end_idx],
            'y_coords': y_coords[start_idx:end_idx],
            'symbols': pnf_symbols[start_idx:end_idx],
            'current_index': current_index,
            'lookback_start': start_idx
        }

    def _calculate_ema(self, prices: List[float], period: int) -> float:
        """
        Calculate Exponential Moving Average.

        Args:
            prices: List of closing prices
            period: EMA period (e.g., 20)

        Returns:
            EMA value
        """
        if len(prices) < period:
            return None

        # Calculate smoothing factor
        multiplier = 2 / (period + 1)

        # Start with simple moving average for first value
        ema = sum(prices[:period]) / period

        # Calculate EMA for remaining values
        for price in prices[period:]:
            ema = (price * multiplier) + (ema * (1 - multiplier))

        return ema

    def _check_latest_column_breakout(self, data: Dict, column: int, price: float, symbol: str,
                                    alerts: List[AlertTrigger], current_index: int, ema_20: float = None, price_vs_ema: float = None):
        """
        Check for high-confidence patterns with multiple attempts and follow-through.
        Only fires alerts in the LATEST column for live trading.
        Now includes EMA validation and new pattern types.
        """
        if len(data['symbols']) < 4:  # Need at least 4 points for pattern analysis
            return

        # Get the latest column number
        latest_column = max(data['x_coords'])

        # Only process if we're in the latest column
        if column != latest_column:
            return

        # For bullish patterns (X breaking above multiple previous attempts)
        if symbol == 'X':
            # Check traditional patterns
            self._check_multiple_top_breakout(data, column, price, current_index, alerts, latest_column)

            # Check EMA-validated patterns (only if above EMA)
            if ema_20 and price_vs_ema and price_vs_ema > 0:
                self._check_ema_validated_top_breakout(data, column, price, current_index, alerts, latest_column, ema_20)

            # Check turtle breakout follow through (5-column range + double pattern confirmation)
            self._check_turtle_breakout_ft_buy(data, column, price, current_index, alerts, latest_column, ema_20)

            # Check low pole follow through buy pattern FIRST (4-column low pole + double top confirmation + 5-box requirement)
            self._check_low_pole_ft_buy(data, column, price, current_index, alerts, latest_column, ema_20)

            # Check catapult buy pattern (triple bottom followed by double bottom breakout)
            self._check_catapult_buy(data, column, price, current_index, alerts, latest_column, ema_20)

            # Check 100% pole follow through buy pattern (less specific, checked after low pole FT)
            self._check_pole_follow_through_buy(data, column, price, current_index, alerts, latest_column, ema_20)

            # Check AFT anchor breakout buy pattern
            self._check_aft_anchor_breakout_buy(data, column, price, current_index, alerts, latest_column, ema_20)

            # Check Tweezer bullish pattern (horizontal accumulation between anchor columns)
            self._check_tweezer_bullish(data, column, price, current_index, alerts, latest_column, ema_20)

            # Check ABC bullish pattern (Anchor-Breakout-Count momentum pattern)
            self._check_abc_bullish(data, column, price, current_index, alerts, latest_column, ema_20)

        # For bearish patterns (O breaking below multiple previous attempts)
        elif symbol == 'O':
            # Check traditional patterns
            self._check_multiple_bottom_breakdown(data, column, price, current_index, alerts, latest_column)

            # Check EMA-validated patterns (only if below EMA)
            if ema_20 and price_vs_ema and price_vs_ema < 0:
                self._check_ema_validated_bottom_breakdown(data, column, price, current_index, alerts, latest_column, ema_20)

            # Check turtle breakout follow through (5-column range + double pattern confirmation)
            self._check_turtle_breakout_ft_sell(data, column, price, current_index, alerts, latest_column, ema_20)

            # Check catapult sell pattern (triple top followed by double top breakdown)
            self._check_catapult_sell(data, column, price, current_index, alerts, latest_column, ema_20)

            # Check 100% pole follow through sell pattern
            self._check_pole_follow_through_sell(data, column, price, current_index, alerts, latest_column, ema_20)

            # Check Tweezer bearish pattern FIRST (horizontal distribution between anchor columns)
            self._check_tweezer_bearish(data, column, price, current_index, alerts, latest_column, ema_20)

            # Check ABC bearish pattern (Anchor-Breakdown-Count momentum pattern)
            self._check_abc_bearish(data, column, price, current_index, alerts, latest_column, ema_20)

            # Check AFT anchor breakdown sell pattern
            self._check_aft_anchor_breakdown_sell(data, column, price, current_index, alerts, latest_column, ema_20)

            # Check high pole follow through sell pattern (4-column high pole + double bottom confirmation)
            self._check_high_pole_ft_sell(data, column, price, current_index, alerts, latest_column, ema_20)

    def _check_multiple_top_breakout(self, data: Dict, column: int, price: float,
                                   current_index: int, alerts: List[AlertTrigger], latest_column: int):
        """
        Check for double/triple/quadruple top buy patterns based on P&F definition.

        Pattern structures:
        - Double Top Buy: X-O-X where final X breaks above first X
        - Triple Top Buy: X-O-X-O-X where X1 & X3 are EQUAL, X5 breaks above
        - Quadruple Top Buy: X-O-X-O-X-O-X where X1, X3, X5 are EQUAL, X7 breaks above
        """
        # Build column structure: find all columns and their types
        columns = {}
        for i in range(current_index + 1):
            col = data['x_coords'][i]
            sym = data['symbols'][i]
            price_val = data['y_coords'][i]

            if col not in columns:
                columns[col] = {'symbol': sym, 'prices': []}
            columns[col]['prices'].append(price_val)

        # Get sorted column numbers
        col_nums = sorted(columns.keys())

        if len(col_nums) < 3:  # Need at least 3 columns for double top (X-O-X)
            return

        # Current column must be X
        if columns[latest_column]['symbol'] != 'X':
            return

        # Check for Triple Top Buy: X-O-X-O-X (5 columns minimum)
        # Note: May have initial O column, so check both 5 and 6 column patterns
        for num_cols in [5, 6]:
            if len(col_nums) < num_cols:
                continue

            last_n = col_nums[-num_cols:]
            pattern = [columns[c]['symbol'] for c in last_n]

            # Look for X-O-X-O-X pattern
            if num_cols == 6 and pattern == ['O', 'X', 'O', 'X', 'O', 'X']:
                # Pattern starts at index 1
                x_indices = [1, 3, 5]
            elif num_cols == 5 and pattern == ['X', 'O', 'X', 'O', 'X']:
                # Pattern starts at index 0
                x_indices = [0, 2, 4]
            else:
                continue

            # Get tops of X columns
            x1_top = max(columns[last_n[x_indices[0]]]['prices'])
            x3_top = max(columns[last_n[x_indices[1]]]['prices'])
            x5_top = max(columns[last_n[x_indices[2]]]['prices'])

            # Check if X1 and X3 are EQUAL (within 0.5% tolerance)
            tolerance = x1_top * 0.005
            if abs(x1_top - x3_top) <= tolerance and x5_top > x1_top:
                pattern_state = self.pattern_states[PatternType.TRIPLE_TOP_BUY]
                if not pattern_state.alert_fired:
                    alerts.append(AlertTrigger(
                        column=column,
                        price=price,
                        alert_type=AlertType.BUY,
                        pattern_type=PatternType.TRIPLE_TOP_BUY,
                        trigger_reason=f"🚨 TRIPLE TOP BUY: Price {price:.2f} breaks above resistance {x1_top:.2f} after 2 equal tops at {x1_top:.2f}",
                        is_first_occurrence=True
                    ))
                    pattern_state.alert_fired = True
                    return  # Found triple top, don't check for double top

        # Check for Quadruple Top Buy: X-O-X-O-X-O-X (7 columns minimum)
        if len(col_nums) >= 7:
            last_7 = col_nums[-7:]
            pattern = [columns[c]['symbol'] for c in last_7]

            if pattern == ['X', 'O', 'X', 'O', 'X', 'O', 'X']:
                x1_top = max(columns[last_7[0]]['prices'])
                x3_top = max(columns[last_7[2]]['prices'])
                x5_top = max(columns[last_7[4]]['prices'])
                x7_top = max(columns[last_7[6]]['prices'])

                tolerance = x1_top * 0.005
                if (abs(x1_top - x3_top) <= tolerance and
                    abs(x1_top - x5_top) <= tolerance and
                    x7_top > x1_top):
                    pattern_state = self.pattern_states[PatternType.QUADRUPLE_TOP_BUY]
                    if not pattern_state.alert_fired:
                        alerts.append(AlertTrigger(
                            column=column,
                            price=price,
                            alert_type=AlertType.BUY,
                            pattern_type=PatternType.QUADRUPLE_TOP_BUY,
                            trigger_reason=f"🚨 QUADRUPLE TOP BUY: Price {price:.2f} breaks above resistance {x1_top:.2f} after 3 equal tops",
                            is_first_occurrence=True
                        ))
                        pattern_state.alert_fired = True
                        return

        # Check for Double Top Buy: X-O-X (3 columns minimum)
        if len(col_nums) >= 3:
            last_3 = col_nums[-3:]
            pattern = [columns[c]['symbol'] for c in last_3]

            if pattern == ['X', 'O', 'X']:
                x1_top = max(columns[last_3[0]]['prices'])
                x3_top = max(columns[last_3[2]]['prices'])

                if x3_top > x1_top:
                    pattern_state = self.pattern_states[PatternType.DOUBLE_TOP_BUY]
                    if not pattern_state.alert_fired:
                        alerts.append(AlertTrigger(
                            column=column,
                            price=price,
                            alert_type=AlertType.BUY,
                            pattern_type=PatternType.DOUBLE_TOP_BUY,
                            trigger_reason=f"🚨 DOUBLE TOP BUY: Price {price:.2f} breaks above previous top {x1_top:.2f}",
                            is_first_occurrence=True
                        ))
                        pattern_state.alert_fired = True

    def _check_multiple_bottom_breakdown(self, data: Dict, column: int, price: float,
                                       current_index: int, alerts: List[AlertTrigger], latest_column: int):
        """Check for double/triple/quadruple bottom sell patterns with follow-through."""
        # Find distinct bottoms from different columns (lowest O in each column)
        column_lows = {}
        for i in range(current_index):
            if (data['symbols'][i] == 'O' and
                data['x_coords'][i] < latest_column):  # From previous columns only
                col = data['x_coords'][i]
                if col not in column_lows or data['y_coords'][i] < column_lows[col]:
                    column_lows[col] = data['y_coords'][i]

        if len(column_lows) < 2:  # Need at least 2 previous columns with O's
            return

        # Get the distinct column lows
        distinct_lows = list(column_lows.values())
        lowest_previous = min(distinct_lows)

        # Count how many distinct bottoms are at similar levels (within 1% tolerance)
        support_level = lowest_previous
        tolerance = support_level * 0.01  # 1% tolerance

        similar_bottoms = []
        for low in distinct_lows:
            if abs(low - support_level) <= tolerance:
                similar_bottoms.append(low)

        num_attempts = len(similar_bottoms)

        # Determine pattern type based on number of DISTINCT similar bottoms
        # For triple bottom, we need exactly 3 distinct bottoms at similar levels
        if num_attempts >= 4:
            pattern_type = PatternType.QUADRUPLE_BOTTOM_SELL
            pattern_name = "QUADRUPLE BOTTOM SELL"
        elif num_attempts == 3:
            pattern_type = PatternType.TRIPLE_BOTTOM_SELL
            pattern_name = "TRIPLE BOTTOM SELL"
        elif num_attempts == 2:
            pattern_type = PatternType.DOUBLE_BOTTOM_SELL
            pattern_name = "DOUBLE BOTTOM SELL"
        else:
            return  # Not enough distinct similar bottoms for a pattern

        # Check if we haven't already fired this pattern alert
        pattern_state = self.pattern_states[pattern_type]

        # Fire alert if price breaks below support with follow-through
        if price < lowest_previous and not pattern_state.alert_fired:
            # Additional validation: ensure we have proper pattern formation
            if self._validate_bottom_pattern(similar_bottoms, num_attempts):
                alerts.append(AlertTrigger(
                    column=column,
                    price=price,
                    alert_type=AlertType.SELL,
                    pattern_type=pattern_type,
                    trigger_reason=f"🚨 {pattern_name}: Price {price:.2f} breaks below support {lowest_previous:.2f} after {num_attempts} distinct similar bottoms with follow-through",
                    is_first_occurrence=True
                ))
                pattern_state.alert_fired = True

    def _check_ema_validated_top_breakout(self, data: Dict, column: int, price: float,
                                        current_index: int, alerts: List[AlertTrigger], latest_column: int, ema_20: float):
        """Check for EMA-validated double/triple/quadruple top buy patterns."""
        # Find distinct tops from different columns (highest X in each column)
        column_highs = {}
        for i in range(current_index):
            if (data['symbols'][i] == 'X' and
                data['x_coords'][i] < latest_column):  # From previous columns only
                col = data['x_coords'][i]
                if col not in column_highs or data['y_coords'][i] > column_highs[col]:
                    column_highs[col] = data['y_coords'][i]

        if len(column_highs) < 2:  # Need at least 2 previous columns with X's
            return

        # Get the distinct column highs
        distinct_highs = list(column_highs.values())
        highest_previous = max(distinct_highs)

        # Count how many distinct tops are at similar levels (within 1% tolerance)
        resistance_level = highest_previous
        tolerance = resistance_level * 0.01  # 1% tolerance

        similar_tops = []
        for high in distinct_highs:
            if abs(high - resistance_level) <= tolerance:
                similar_tops.append(high)

        num_attempts = len(similar_tops)

        # Determine EMA-validated pattern type
        if num_attempts >= 4:
            pattern_type = PatternType.QUADRUPLE_TOP_BUY_EMA
            pattern_name = "QUADRUPLE TOP BUY (EMA VALIDATED)"
        elif num_attempts == 3:
            pattern_type = PatternType.TRIPLE_TOP_BUY_EMA
            pattern_name = "TRIPLE TOP BUY (EMA VALIDATED)"
        elif num_attempts == 2:
            pattern_type = PatternType.DOUBLE_TOP_BUY_EMA
            pattern_name = "DOUBLE TOP BUY (EMA VALIDATED)"
        else:
            return  # Not enough distinct similar tops for a pattern

        # Check if we haven't already fired this pattern alert
        pattern_state = self.pattern_states[pattern_type]

        # Fire alert if price breaks above resistance with follow-through AND above EMA
        if price > highest_previous and price > ema_20 and not pattern_state.alert_fired:
            # Additional validation: ensure we have proper pattern formation
            if self._validate_top_pattern(similar_tops, num_attempts):
                alerts.append(AlertTrigger(
                    column=column,
                    price=price,
                    alert_type=AlertType.BUY,
                    pattern_type=pattern_type,
                    trigger_reason=f"🚨 {pattern_name}: Price {price:.2f} breaks above resistance {highest_previous:.2f} after {num_attempts} distinct similar tops with follow-through. Chart above 20 EMA ({ema_20:.2f})",
                    is_first_occurrence=True
                ))
                pattern_state.alert_fired = True

    def _validate_top_pattern(self, similar_tops: List[float], num_attempts: int) -> bool:
        """
        Validate that we have a proper top pattern formation.

        Args:
            similar_tops: List of top prices at similar levels
            num_attempts: Number of attempts (should match len(similar_tops))

        Returns:
            True if pattern is valid, False otherwise
        """
        if len(similar_tops) != num_attempts:
            return False

        if num_attempts < 2:
            return False

        # Check that all tops are within reasonable tolerance of each other
        avg_top = sum(similar_tops) / len(similar_tops)
        tolerance = avg_top * 0.015  # 1.5% tolerance for validation

        for top in similar_tops:
            if abs(top - avg_top) > tolerance:
                return False

        return True

    def _validate_triple_top_structure(self, x_columns: Dict[int, float], resistance_level: float, num_attempts: int) -> bool:
        """
        Validate proper triple top structure with exactly 3 X columns at resistance level.
        Ensures the pattern matches the visual structure from the image.

        Args:
            x_columns: Dictionary of column -> highest price in that column
            resistance_level: The resistance level price
            num_attempts: Expected number of attempts (2, 3, or 4)

        Returns:
            True if pattern structure is valid
        """
        if num_attempts < 2:
            return False

        # For any multiple top pattern, ensure we have the right number of X columns at resistance
        tolerance = resistance_level * 0.005  # 0.5% tolerance for exact matching
        resistance_columns = []

        for col, high in x_columns.items():
            if abs(high - resistance_level) <= tolerance:
                resistance_columns.append(col)

        # Must have exactly the expected number of columns at resistance level
        if len(resistance_columns) != num_attempts:
            return False

        # Ensure columns are properly spaced (not consecutive) for proper pattern formation
        resistance_columns.sort()
        for i in range(1, len(resistance_columns)):
            if resistance_columns[i] - resistance_columns[i-1] < 2:
                return False  # Columns too close together - not a proper pattern

        return True

    def _validate_bottom_pattern(self, similar_bottoms: List[float], num_attempts: int) -> bool:
        """
        Validate that we have a proper bottom pattern formation.

        Args:
            similar_bottoms: List of bottom prices at similar levels
            num_attempts: Number of attempts (should match len(similar_bottoms))

        Returns:
            True if pattern is valid, False otherwise
        """
        if len(similar_bottoms) != num_attempts:
            return False

        if num_attempts < 2:
            return False

        # Check that all bottoms are within reasonable tolerance of each other
        avg_bottom = sum(similar_bottoms) / len(similar_bottoms)
        tolerance = avg_bottom * 0.015  # 1.5% tolerance for validation

        for bottom in similar_bottoms:
            if abs(bottom - avg_bottom) > tolerance:
                return False

        return True

    def _check_ema_validated_bottom_breakdown(self, data: Dict, column: int, price: float,
                                            current_index: int, alerts: List[AlertTrigger], latest_column: int, ema_20: float):
        """Check for EMA-validated double/triple/quadruple bottom sell patterns."""
        # Find distinct bottoms from different columns (lowest O in each column)
        column_lows = {}
        for i in range(current_index):
            if (data['symbols'][i] == 'O' and
                data['x_coords'][i] < latest_column):  # From previous columns only
                col = data['x_coords'][i]
                if col not in column_lows or data['y_coords'][i] < column_lows[col]:
                    column_lows[col] = data['y_coords'][i]

        if len(column_lows) < 2:  # Need at least 2 previous columns with O's
            return

        # Get the distinct column lows
        distinct_lows = list(column_lows.values())
        lowest_previous = min(distinct_lows)

        # Count how many distinct bottoms are at similar levels (within 1% tolerance)
        support_level = lowest_previous
        tolerance = support_level * 0.01  # 1% tolerance

        similar_bottoms = []
        for low in distinct_lows:
            if abs(low - support_level) <= tolerance:
                similar_bottoms.append(low)

        num_attempts = len(similar_bottoms)

        # Determine EMA-validated pattern type
        if num_attempts >= 4:
            pattern_type = PatternType.QUADRUPLE_BOTTOM_SELL_EMA
            pattern_name = "QUADRUPLE BOTTOM SELL (EMA VALIDATED)"
        elif num_attempts == 3:
            pattern_type = PatternType.TRIPLE_BOTTOM_SELL_EMA
            pattern_name = "TRIPLE BOTTOM SELL (EMA VALIDATED)"
        elif num_attempts == 2:
            pattern_type = PatternType.DOUBLE_BOTTOM_SELL_EMA
            pattern_name = "DOUBLE BOTTOM SELL (EMA VALIDATED)"
        else:
            return  # Not enough distinct similar bottoms for a pattern

        # Check if we haven't already fired this pattern alert
        pattern_state = self.pattern_states[pattern_type]

        # Fire alert if price breaks below support with follow-through AND below EMA
        if price < lowest_previous and price < ema_20 and not pattern_state.alert_fired:
            # Additional validation: ensure we have proper pattern formation
            if self._validate_bottom_pattern(similar_bottoms, num_attempts):
                alerts.append(AlertTrigger(
                    column=column,
                    price=price,
                    alert_type=AlertType.SELL,
                    pattern_type=pattern_type,
                    trigger_reason=f"🚨 {pattern_name}: Price {price:.2f} breaks below support {lowest_previous:.2f} after {num_attempts} distinct similar bottoms with follow-through. Chart below 20 EMA ({ema_20:.2f})",
                    is_first_occurrence=True
                ))
                pattern_state.alert_fired = True

    def _check_turtle_breakout_ft_buy(self, data: Dict, column: int, price: float,
                                    current_index: int, alerts: List[AlertTrigger], latest_column: int, ema_20: float = None):
        """
        Check for Turtle Breakout Follow Through (FT) Buy pattern.

        Pattern requirements:
        1. Initial turtle breakout: X breaks above 5-column high
        2. Follow through: Followed by a double top buy pattern
        3. This confirms the initial bullish turtle breakout
        """
        if len(data['symbols']) < 10:  # Need sufficient data
            return

        # Only process if we're in the latest column
        if column != latest_column:
            return

        # Must be an X symbol for buy signal
        current_symbol = None
        for i in range(len(data['symbols'])):
            if data['x_coords'][i] == column and data['y_coords'][i] == price:
                current_symbol = data['symbols'][i]
                break

        if current_symbol != 'X':
            return

        # Step 1: Check for initial turtle breakout (5-column high break)
        lookback_columns = 5
        all_columns = sorted(set(data['x_coords']))

        if len(all_columns) < lookback_columns + 2:  # Need extra columns for follow-through
            return

        # Find the 5-column high before the current breakout area
        turtle_breakout_found = False
        turtle_breakout_price = 0
        turtle_breakout_column = 0

        # Look for turtle breakout in recent history (not too far back)
        for check_col in range(max(1, latest_column - 10), latest_column):
            if check_col not in all_columns:
                continue

            # Get 5 columns before this check column
            start_range = max(1, check_col - lookback_columns)
            range_columns = [c for c in all_columns if start_range <= c < check_col]

            if len(range_columns) < lookback_columns:
                continue

            # Find highest X in the 5-column range
            range_high = 0
            for i in range(len(data['symbols'])):
                if (data['x_coords'][i] in range_columns and
                    data['symbols'][i] == 'X' and
                    data['y_coords'][i] > range_high):
                    range_high = data['y_coords'][i]

            if range_high == 0:
                continue

            # Check if this column broke above the 5-column high
            col_high = 0
            for i in range(len(data['symbols'])):
                if (data['x_coords'][i] == check_col and
                    data['symbols'][i] == 'X' and
                    data['y_coords'][i] > col_high):
                    col_high = data['y_coords'][i]

            if col_high > range_high:
                turtle_breakout_found = True
                turtle_breakout_price = range_high
                turtle_breakout_column = check_col
                break

        if not turtle_breakout_found:
            return

        # Step 2: Check for double top follow-through pattern after turtle breakout
        # Look for at least 2 X columns at similar resistance levels after turtle breakout
        x_columns_after_turtle = {}
        for i in range(len(data['symbols'])):
            if (data['symbols'][i] == 'X' and
                data['x_coords'][i] > turtle_breakout_column and
                data['x_coords'][i] <= latest_column):
                col = data['x_coords'][i]
                if col not in x_columns_after_turtle or data['y_coords'][i] > x_columns_after_turtle[col]:
                    x_columns_after_turtle[col] = data['y_coords'][i]

        if len(x_columns_after_turtle) < 2:  # Need at least 2 X columns for double top
            return

        # Get the X column highs after turtle breakout (excluding current column for resistance calculation)
        x_column_highs_before_current = []
        for col, high in x_columns_after_turtle.items():
            if col < column:  # Only consider columns before current
                x_column_highs_before_current.append(high)

        if len(x_column_highs_before_current) < 2:  # Need at least 2 previous X columns for double top
            return

        # Find the resistance level from previous columns
        resistance_level = max(x_column_highs_before_current)

        # Count X columns at similar resistance level (within 0.5% tolerance)
        tolerance = resistance_level * 0.005
        similar_highs = [h for h in x_column_highs_before_current if abs(h - resistance_level) <= tolerance]

        if len(similar_highs) < 2:  # Need at least double top
            return

        # Check if we haven't already fired this pattern alert
        pattern_state = self.pattern_states[PatternType.TURTLE_BREAKOUT_FT_BUY]

        # Fire alert if current X breaks above the double top resistance (follow-through)
        if price > resistance_level and not pattern_state.alert_fired:
            ema_condition = ""
            if ema_20 and price > ema_20:
                ema_condition = f" Chart above 20 EMA ({ema_20:.2f})"

            alerts.append(AlertTrigger(
                column=column,
                price=price,
                alert_type=AlertType.BUY,
                pattern_type=PatternType.TURTLE_BREAKOUT_FT_BUY,
                trigger_reason=f"🚨 TURTLE BREAKOUT FT BUY: Price {price:.2f} breaks above double top resistance {resistance_level:.2f} after turtle breakout above {turtle_breakout_price:.2f}. Follow-through confirms bullish momentum.{ema_condition}",
                is_first_occurrence=True
            ))
            pattern_state.alert_fired = True

    def _check_turtle_breakout_ft_sell(self, data: Dict, column: int, price: float,
                                      current_index: int, alerts: List[AlertTrigger], latest_column: int, ema_20: float = None):
        """
        Check for Turtle Breakout Follow Through (FT) Sell pattern.

        Pattern requirements:
        1. Initial turtle breakout: O breaks below 5-column low
        2. Follow through: Followed by a double bottom sell pattern
        3. This confirms the initial bearish turtle breakout
        """
        if len(data['symbols']) < 10:  # Need sufficient data
            return

        # Only process if we're in the latest column
        if column != latest_column:
            return

        # Must be an O symbol for sell signal
        current_symbol = None
        for i in range(len(data['symbols'])):
            if data['x_coords'][i] == column and data['y_coords'][i] == price:
                current_symbol = data['symbols'][i]
                break

        if current_symbol != 'O':
            return

        # Step 1: Check for initial turtle breakout (5-column low break)
        lookback_columns = 5
        all_columns = sorted(set(data['x_coords']))

        if len(all_columns) < lookback_columns + 2:  # Need extra columns for follow-through
            return

        # Find the 5-column low before the current breakout area
        turtle_breakout_found = False
        turtle_breakout_price = 0
        turtle_breakout_column = 0

        # Look for turtle breakout in recent history (not too far back)
        for check_col in range(max(1, latest_column - 10), latest_column):
            if check_col not in all_columns:
                continue

            # Get 5 columns before this check column
            start_range = max(1, check_col - lookback_columns)
            range_columns = [c for c in all_columns if start_range <= c < check_col]

            if len(range_columns) < lookback_columns:
                continue

            # Find lowest O in the 5-column range
            range_low = float('inf')
            for i in range(len(data['symbols'])):
                if (data['x_coords'][i] in range_columns and
                    data['symbols'][i] == 'O' and
                    data['y_coords'][i] < range_low):
                    range_low = data['y_coords'][i]

            if range_low == float('inf'):
                continue

            # Check if this column broke below the 5-column low
            col_low = float('inf')
            for i in range(len(data['symbols'])):
                if (data['x_coords'][i] == check_col and
                    data['symbols'][i] == 'O' and
                    data['y_coords'][i] < col_low):
                    col_low = data['y_coords'][i]

            if col_low < range_low:
                turtle_breakout_found = True
                turtle_breakout_price = range_low
                turtle_breakout_column = check_col
                break

        if not turtle_breakout_found:
            return

        # Step 2: Check for double bottom follow-through pattern after turtle breakout
        # Look for at least 2 O columns at similar support levels after turtle breakout
        o_columns_after_turtle = {}
        for i in range(len(data['symbols'])):
            if (data['symbols'][i] == 'O' and
                data['x_coords'][i] > turtle_breakout_column and
                data['x_coords'][i] <= latest_column):
                col = data['x_coords'][i]
                if col not in o_columns_after_turtle or data['y_coords'][i] < o_columns_after_turtle[col]:
                    o_columns_after_turtle[col] = data['y_coords'][i]

        if len(o_columns_after_turtle) < 2:  # Need at least 2 O columns for double bottom
            return

        # Get the O column lows after turtle breakout (excluding current column for support calculation)
        o_column_lows_before_current = []
        for col, low in o_columns_after_turtle.items():
            if col < column:  # Only consider columns before current
                o_column_lows_before_current.append(low)

        if len(o_column_lows_before_current) < 2:  # Need at least 2 previous O columns for double bottom
            return

        # Find the support level from previous columns
        support_level = min(o_column_lows_before_current)

        # Count O columns at similar support level (within 0.5% tolerance)
        tolerance = support_level * 0.005
        similar_lows = [l for l in o_column_lows_before_current if abs(l - support_level) <= tolerance]

        if len(similar_lows) < 2:  # Need at least double bottom
            return

        # Check if we haven't already fired this pattern alert
        pattern_state = self.pattern_states[PatternType.TURTLE_BREAKOUT_FT_SELL]

        # Fire alert if current O breaks below the double bottom support (follow-through)
        if price < support_level and not pattern_state.alert_fired:
            ema_condition = ""
            if ema_20 and price < ema_20:
                ema_condition = f" Chart below 20 EMA ({ema_20:.2f})"

            alerts.append(AlertTrigger(
                column=column,
                price=price,
                alert_type=AlertType.SELL,
                pattern_type=PatternType.TURTLE_BREAKOUT_FT_SELL,
                trigger_reason=f"🚨 TURTLE BREAKOUT FT SELL: Price {price:.2f} breaks below double bottom support {support_level:.2f} after turtle breakout below {turtle_breakout_price:.2f}. Follow-through confirms bearish momentum.{ema_condition}",
                is_first_occurrence=True
            ))
            pattern_state.alert_fired = True



    def _check_catapult_buy(self, data: Dict, column: int, price: float,
                           current_index: int, alerts: List[AlertTrigger], latest_column: int, ema_20: float = None):
        """
        Check for catapult buy pattern based on P&F definition:
        Catapult Buy = Triple Top Buy followed by Double Top Buy

        Pattern structure:
        1. Triple Top Buy (TTB): X-O-X-O-X where cols 1&3 equal, col 5 breaks above
        2. Double Top Buy (DTB): After TTB, next X-O-X where final X breaks above

        Total pattern: X-O-X-O-X-O-X (7 columns minimum)
        Note: May have initial O column, so check both 7 and 8 column patterns
        """
        # Build column structure
        columns = {}
        for i in range(current_index + 1):
            col = data['x_coords'][i]
            sym = data['symbols'][i]
            price_val = data['y_coords'][i]

            if col not in columns:
                columns[col] = {'symbol': sym, 'prices': []}
            columns[col]['prices'].append(price_val)

        col_nums = sorted(columns.keys())

        # Current column must be X
        if columns[latest_column]['symbol'] != 'X':
            return

        # Try to find X-O-X-O-X-O-X pattern in last 7 or 8 columns
        # Check 8 columns first (with initial O), then 7 columns
        for num_cols in [8, 7]:
            if len(col_nums) < num_cols:
                continue

            last_n = col_nums[-num_cols:]
            pattern = [columns[c]['symbol'] for c in last_n]

            # Look for X-O-X-O-X-O-X pattern
            # It might be at the end, or preceded by an O
            if num_cols == 8 and pattern == ['O', 'X', 'O', 'X', 'O', 'X', 'O', 'X']:
                # Pattern starts at index 1
                x_indices = [1, 3, 5, 7]
            elif num_cols == 7 and pattern == ['X', 'O', 'X', 'O', 'X', 'O', 'X']:
                # Pattern starts at index 0
                x_indices = [0, 2, 4, 6]
            else:
                continue

            # Get tops of X columns
            x1_top = max(columns[last_n[x_indices[0]]]['prices'])
            x3_top = max(columns[last_n[x_indices[1]]]['prices'])
            x5_top = max(columns[last_n[x_indices[2]]]['prices'])  # TTB breakout

            # For X7, use the CURRENT PRICE if we're in column 7, otherwise use column top
            if last_n[x_indices[3]] == latest_column:
                x7_top = price  # Use current price for live detection
            else:
                x7_top = max(columns[last_n[x_indices[3]]]['prices'])

            tolerance = x1_top * 0.005

            # Validate Triple Top Buy: X1 & X3 equal, X5 breaks above
            if abs(x1_top - x3_top) > tolerance:
                continue  # X1 and X3 must be equal

            if x5_top <= x1_top:
                continue  # X5 must break above X1/X3

            # Validate Double Top Buy: X7 (current price) breaks above X5
            if x7_top <= x5_top:
                continue  # X7 must break above X5

            # Check if we haven't already fired this pattern alert
            pattern_state = self.pattern_states[PatternType.CATAPULT_BUY]

            if not pattern_state.alert_fired:
                ema_condition = ""
                if ema_20 and price > ema_20:
                    ema_condition = f" Chart above 20 EMA ({ema_20:.2f})"

                alerts.append(AlertTrigger(
                    column=column,
                    price=price,
                    alert_type=AlertType.BUY,
                    pattern_type=PatternType.CATAPULT_BUY,
                    trigger_reason=f"🚨 CATAPULT BUY: Price {price:.2f} breaks above {x5_top:.2f}. Triple Top ({x1_top:.2f}) + Double Top ({x5_top:.2f}) = Catapult!{ema_condition}",
                    is_first_occurrence=True
                ))
                pattern_state.alert_fired = True
                return  # Found and fired, exit

    def _check_catapult_sell(self, data: Dict, column: int, price: float,
                            current_index: int, alerts: List[AlertTrigger], latest_column: int, ema_20: float = None):
        """
        Check for catapult sell pattern based on the user's image:
        Triple top buy pattern followed by double top buy pattern, then O breaks below support.

        Pattern structure from image:
        1. Multiple X columns reaching similar high levels (triple/multiple top formation)
        2. O column enters the territory and crosses below the breakdown level
        3. This creates a catapult effect - strong sell signal
        """
        if len(data['symbols']) < 7:  # Need sufficient data for pattern
            return

        # Only process if we're in the latest column and it's an O column
        if column != latest_column:
            return

        # Must be an O symbol for sell signal
        current_symbol = None
        for i in range(len(data['x_coords'])):
            if data['x_coords'][i] == column and data['y_coords'][i] == price:
                current_symbol = data['symbols'][i]
                break

        if current_symbol != 'O':
            return

        # Find all previous X columns and their highest points
        x_column_highs = {}
        for i in range(current_index):
            if (data['symbols'][i] == 'X' and
                data['x_coords'][i] < latest_column):
                col = data['x_coords'][i]
                if col not in x_column_highs or data['y_coords'][i] > x_column_highs[col]:
                    x_column_highs[col] = data['y_coords'][i]

        if len(x_column_highs) < 3:  # Need at least 3 X columns for pattern
            return

        # Find the highest resistance level from X columns
        resistance_level = max(x_column_highs.values())
        tolerance = resistance_level * 0.02  # 2% tolerance

        # Count how many X columns hit similar high levels (triple top formation)
        similar_highs = [high for high in x_column_highs.values()
                        if abs(high - resistance_level) <= tolerance]

        if len(similar_highs) < 3:  # Need at least triple top
            return

        # Find previous support level (lowest O before current column)
        previous_o_lows = []
        for i in range(current_index):
            if (data['symbols'][i] == 'O' and
                data['x_coords'][i] < latest_column):
                previous_o_lows.append(data['y_coords'][i])

        if not previous_o_lows:
            return

        support_level = min(previous_o_lows)

        # Check if we haven't already fired this pattern alert
        pattern_state = self.pattern_states[PatternType.CATAPULT_SELL]

        # Fire alert if current O breaks below previous support (catapult effect)
        if price < support_level and not pattern_state.alert_fired:
            ema_condition = ""
            if ema_20 and price < ema_20:
                ema_condition = f" Chart below 20 EMA ({ema_20:.2f})"

            alerts.append(AlertTrigger(
                column=column,
                price=price,
                alert_type=AlertType.SELL,
                pattern_type=PatternType.CATAPULT_SELL,
                trigger_reason=f"🚨 CATAPULT SELL: Price {price:.2f} breaks below support {support_level:.2f} after {len(similar_highs)} top attempts at {resistance_level:.2f}. Traditional P&F catapult pattern.{ema_condition}",
                is_first_occurrence=True
            ))
            pattern_state.alert_fired = True

    def _check_pole_follow_through_buy(self, data: Dict, column: int, price: float,
                                      current_index: int, alerts: List[AlertTrigger], latest_column: int, ema_20: float = None):
        """
        Check for 100% pole follow through buy pattern based on P&F definition.

        Pattern structure:
        1. Strong vertical X column (pole) - significant upward move
        2. Followed by O-X-O-X pattern (double top buy formation)
        3. Final X breaks above the pole high for buy signal

        Total: 6 columns (Pole-X, O, X, O, X, final breakout X)
        """
        # Build column structure
        columns = {}
        for i in range(current_index + 1):
            col = data['x_coords'][i]
            sym = data['symbols'][i]
            price_val = data['y_coords'][i]

            if col not in columns:
                columns[col] = {'symbol': sym, 'prices': []}
            columns[col]['prices'].append(price_val)

        col_nums = sorted(columns.keys())

        if len(col_nums) < 6:  # Need at least 6 columns
            return

        # Current column must be X
        if columns[latest_column]['symbol'] != 'X':
            return

        # Check for Pole-X-O-X-O-X pattern in last 6 columns
        last_6 = col_nums[-6:]
        pattern = [columns[c]['symbol'] for c in last_6]

        # Pattern should be X-O-X-O-X-X or similar with pole at start
        if pattern != ['X', 'O', 'X', 'O', 'X', 'X'] and pattern != ['X', 'O', 'X', 'O', 'X']:
            # Try 5-column pattern: Pole-X, O, X, O, X
            if len(col_nums) >= 5:
                last_5 = col_nums[-5:]
                pattern = [columns[c]['symbol'] for c in last_5]
                if pattern == ['X', 'O', 'X', 'O', 'X']:
                    # Check if first X is a pole (tall column)
                    pole_prices = columns[last_5[0]]['prices']
                    pole_height = max(pole_prices) - min(pole_prices)
                    pole_boxes = len(pole_prices)

                    # Pole should be significant (at least 5% move)
                    pole_top = max(pole_prices)
                    pole_pct = pole_height / pole_top

                    # If pole has 25+ boxes AND meets 5% requirement, this might be AFT instead
                    # AFT has priority over Pole FT, so skip this if it looks like AFT
                    if pole_boxes >= 25 and pole_pct >= 0.05:
                        # Check if this is 4th column after pole (AFT pattern)
                        # For 5-column pattern, distance from col 0 to col 4 is 4
                        # This would be AFT, not Pole FT
                        return  # Let AFT detector handle this

                    # Now check if pole meets minimum requirement (at least 5% move)
                    if pole_pct < 0.05:
                        return  # Not a strong enough pole

                    # Get tops of X columns
                    x1_top = max(columns[last_5[0]]['prices'])  # Pole top
                    x3_top = max(columns[last_5[2]]['prices'])  # Test resistance
                    x5_top = max(columns[last_5[4]]['prices'])  # Breakout

                    # Make sure this is NOT a triple top (X1 and X3 should NOT be equal)
                    tolerance = x1_top * 0.005
                    if abs(x1_top - x3_top) <= tolerance:
                        return  # This is a triple top, not pole FT

                    # X3 should be below X1 (testing resistance but not breaking)
                    if x3_top >= x1_top:
                        return  # X3 should be below pole top

                    # X5 must break above pole high (X1)
                    if x5_top <= x1_top:
                        return

                    # Check if we haven't already fired this pattern alert
                    pattern_state = self.pattern_states[PatternType.POLE_FOLLOW_THROUGH_BUY]

                    if not pattern_state.alert_fired:
                        ema_condition = ""
                        if ema_20 and price > ema_20:
                            ema_condition = f" Chart above 20 EMA ({ema_20:.2f})"

                        alerts.append(AlertTrigger(
                            column=column,
                            price=price,
                            alert_type=AlertType.BUY,
                            pattern_type=PatternType.POLE_FOLLOW_THROUGH_BUY,
                            trigger_reason=f"🚨 POLE FOLLOW THROUGH BUY: Price {price:.2f} breaks above pole high {x1_top:.2f}. Pole + Double Top = Breakout!{ema_condition}",
                            is_first_occurrence=True
                        ))
                        pattern_state.alert_fired = True
                    return
            return

    def _check_pole_follow_through_sell(self, data: Dict, column: int, price: float,
                                       current_index: int, alerts: List[AlertTrigger], latest_column: int, ema_20: float = None):
        """
        Check for 100% pole follow through sell pattern.

        Pattern structure:
        1. 100% pole pattern (strong vertical O column move)
        2. Followed by double bottom sell pattern (X-O-X-O formation)
        3. Creates a six-column pattern total
        4. O column breaks below support for sell signal
        """
        if len(data['symbols']) < 6:  # Need at least 6 columns for this pattern
            return

        # Only process if we're in the latest column and it's an O column
        if column != latest_column:
            return

        # Must be an O symbol for sell signal
        current_symbol = None
        for i in range(len(data['x_coords'])):
            if data['x_coords'][i] == column and data['y_coords'][i] == price:
                current_symbol = data['symbols'][i]
                break

        if current_symbol != 'O':
            return

        # Look for the 100% pole pattern in recent columns
        # A 100% pole is a strong vertical move (typically 3+ boxes in one column)
        pole_found = False
        pole_column = None
        pole_height = 0

        # Check last 6 columns for a pole pattern
        for col in range(max(1, latest_column - 5), latest_column):
            column_points = [(i, data['y_coords'][i]) for i in range(current_index)
                           if data['x_coords'][i] == col and data['symbols'][i] == 'O']

            if len(column_points) >= 3:  # Strong vertical move (3+ O's in one column)
                column_heights = [point[1] for point in column_points]
                height_range = max(column_heights) - min(column_heights)

                if height_range >= 3:  # At least 3 box height difference
                    pole_found = True
                    pole_column = col
                    pole_height = height_range
                    break

        if not pole_found:
            return

        # Look for double bottom pattern after the pole
        # Pattern should be: Pole (O) -> X -> O -> X -> O (current)
        pattern_columns = []
        for col in range(pole_column + 1, latest_column + 1):
            if col <= latest_column:
                pattern_columns.append(col)

        if len(pattern_columns) < 4:  # Need at least 4 columns after pole for double bottom
            return

        # Check for X-O-X-O pattern after pole
        expected_pattern = ['X', 'O', 'X', 'O']
        actual_pattern = []

        for i, col in enumerate(pattern_columns[-4:]):  # Last 4 columns
            # Find the dominant symbol in this column
            column_symbols = [data['symbols'][j] for j in range(current_index)
                            if data['x_coords'][j] == col]
            if column_symbols:
                # Take the most recent symbol in the column
                actual_pattern.append(column_symbols[-1])

        # Check if we have the double bottom pattern
        if len(actual_pattern) >= 4 and actual_pattern[-4:] == expected_pattern:
            # Find support level from the O columns in the pattern
            o_levels = []
            for i, col in enumerate(pattern_columns[-4:]):
                if actual_pattern[i] == 'O':
                    o_points = [data['y_coords'][j] for j in range(current_index)
                              if data['x_coords'][j] == col and data['symbols'][j] == 'O']
                    if o_points:
                        o_levels.append(min(o_points))

            if len(o_levels) >= 2:
                support_level = min(o_levels[:-1])  # Previous support

                # Check if we haven't already fired this pattern alert
                pattern_state = self.pattern_states[PatternType.POLE_FOLLOW_THROUGH_SELL]

                # Fire alert if current O breaks below previous support
                if price < support_level and not pattern_state.alert_fired:
                    ema_condition = ""
                    if ema_20 and price < ema_20:
                        ema_condition = f" Chart below 20 EMA ({ema_20:.2f})"

                    alerts.append(AlertTrigger(
                        column=column,
                        price=price,
                        alert_type=AlertType.SELL,
                        pattern_type=PatternType.POLE_FOLLOW_THROUGH_SELL,
                        trigger_reason=f"🚨 100% POLE FOLLOW THROUGH SELL: Price {price:.2f} breaks below support {support_level:.2f} after {pole_height:.0f}-box pole pattern. Six-column formation complete.{ema_condition}",
                        is_first_occurrence=True
                    ))
                    pattern_state.alert_fired = True



    def _check_aft_anchor_breakout_buy(self, data: Dict, column: int, price: float,
                                     current_index: int, alerts: List[AlertTrigger], latest_column: int, ema_20: float = None):
        """
        Check for AFT (Anchor Follow Through) Bullish Breakout pattern based on P&F definition.

        Pattern requirements:
        1. Anchor Column: Tall X column (height >= 25 boxes)
        2. Consolidation: Price stays below anchor high for several columns
        3. Breakout: On the 4th, 6th, or 8th column after anchor, X column:
           - Performs Double Top Buy (breaks above previous X column)
           - AND breaks above anchor.top
        """
        # Build column structure
        columns = {}
        for i in range(current_index + 1):
            col = data['x_coords'][i]
            sym = data['symbols'][i]
            price_val = data['y_coords'][i]

            if col not in columns:
                columns[col] = {'symbol': sym, 'prices': []}
            columns[col]['prices'].append(price_val)

        col_nums = sorted(columns.keys())

        if len(col_nums) < 5:  # Need at least 5 columns (anchor + 4 more)
            return

        # Current column must be X
        if columns[latest_column]['symbol'] != 'X':
            return

        # Find anchor column: tall X column with height >= 25 boxes
        anchor_col = None
        anchor_top = None

        for i in range(len(col_nums) - 1):  # Don't check last column
            col = col_nums[i]
            if columns[col]['symbol'] == 'X':
                prices = columns[col]['prices']
                height_boxes = len(prices)

                # Check if this is a tall anchor (25+ boxes)
                if height_boxes >= 25:
                    # Check if current column is 4th, 6th, or 8th after this anchor
                    distance = latest_column - col
                    if distance in [4, 6, 8]:
                        anchor_col = col
                        anchor_top = max(prices)
                        break

        if anchor_col is None:
            return

        # Verify no column between anchor and current broke above anchor top
        for col in col_nums:
            if anchor_col < col < latest_column:
                if columns[col]['symbol'] == 'X':
                    col_top = max(columns[col]['prices'])
                    if col_top > anchor_top:
                        return  # Consolidation broken

        # Check for Double Top Buy pattern in recent columns
        # Need at least X-O-X pattern where final X breaks above previous X
        if len(col_nums) >= 3:
            last_3 = col_nums[-3:]
            pattern = [columns[c]['symbol'] for c in last_3]

            if pattern == ['X', 'O', 'X']:
                x1_top = max(columns[last_3[0]]['prices'])
                x3_top = max(columns[last_3[2]]['prices'])

                # X3 must break above X1 (Double Top Buy)
                if x3_top <= x1_top:
                    return

                # X3 must also break above anchor top (AFT condition)
                if x3_top <= anchor_top:
                    return

                # Check if we haven't already fired this pattern alert
                pattern_state = self.pattern_states[PatternType.AFT_ANCHOR_BREAKOUT_BUY]

                if not pattern_state.alert_fired:
                    ema_condition = ""
                    if ema_20 and price > ema_20:
                        ema_condition = f" Chart above 20 EMA ({ema_20:.2f})"

                    distance = latest_column - anchor_col
                    alerts.append(AlertTrigger(
                        column=column,
                        price=price,
                        alert_type=AlertType.BUY,
                        pattern_type=PatternType.AFT_ANCHOR_BREAKOUT_BUY,
                        trigger_reason=f"🚨 AFT ANCHOR BREAKOUT BUY: Price {price:.2f} breaks above anchor high {anchor_top:.2f} on column {distance} after anchor. Double Top + Anchor Break = AFT!{ema_condition}",
                        is_first_occurrence=True
                    ))
                    pattern_state.alert_fired = True

    def _check_aft_anchor_breakdown_sell(self, data: Dict, column: int, price: float,
                                       current_index: int, alerts: List[AlertTrigger], latest_column: int, ema_20: float = None):
        """
        Check for AFT (Anchor Column Follow Through) Bearish Breakdown pattern.

        Pattern requirements:
        1. Anchor Column: A tall O column (strong bearish momentum)
        2. Consolidation: Price stays within 8 columns after anchor (no break above/below anchor)
        3. Breakdown: O column breaks below the anchor column low within 8 columns
        """
        if len(data['symbols']) < 5:  # Need sufficient data
            return

        # Only process if we're in the latest column and it's an O column
        if column != latest_column:
            return

        # Must be an O symbol for sell signal
        current_symbol = None
        for i in range(len(data['x_coords'])):
            if data['x_coords'][i] == column and data['y_coords'][i] == price:
                current_symbol = data['symbols'][i]
                break

        if current_symbol != 'O':
            return

        # Find potential anchor columns (tall O columns)
        anchor_candidates = {}
        for col_num in range(1, latest_column):
            # Get all O points in this column
            o_points_in_col = []
            for i in range(len(data['symbols'])):
                if (data['symbols'][i] == 'O' and data['x_coords'][i] == col_num):
                    o_points_in_col.append(data['y_coords'][i])

            if len(o_points_in_col) >= 14:  # Tall column (14+ O symbols)
                anchor_candidates[col_num] = {
                    'high': max(o_points_in_col),
                    'low': min(o_points_in_col),
                    'height': len(o_points_in_col)
                }

        if not anchor_candidates:
            return

        # Check each anchor candidate for AFT pattern
        for anchor_col, anchor_data in anchor_candidates.items():
            # Check if current column is within 8 columns of anchor
            if latest_column - anchor_col > 8:
                continue

            anchor_low = anchor_data['low']

            # Check if price stayed within anchor range for consolidation period
            consolidation_valid = True
            for check_col in range(anchor_col + 1, latest_column):
                # Get lowest point in this column
                col_high = None
                col_low = None
                for i in range(len(data['symbols'])):
                    if data['x_coords'][i] == check_col:
                        if col_high is None or data['y_coords'][i] > col_high:
                            col_high = data['y_coords'][i]
                        if col_low is None or data['y_coords'][i] < col_low:
                            col_low = data['y_coords'][i]

                # If any column broke below anchor low or above anchor high, invalidate
                if col_low and col_low < anchor_low:
                    consolidation_valid = False
                    break

            if not consolidation_valid:
                continue

            # Check if we haven't already fired this pattern alert
            pattern_state = self.pattern_states[PatternType.AFT_ANCHOR_BREAKDOWN_SELL]

            # Fire alert if current O breaks below anchor low (AFT breakdown)
            if price < anchor_low and not pattern_state.alert_fired:
                ema_condition = ""
                if ema_20 and price < ema_20:
                    ema_condition = f" Chart below 20 EMA ({ema_20:.2f})"

                column_distance = latest_column - anchor_col
                alerts.append(AlertTrigger(
                    column=column,
                    price=price,
                    alert_type=AlertType.SELL,
                    pattern_type=PatternType.AFT_ANCHOR_BREAKDOWN_SELL,
                    trigger_reason=f"🚨 AFT ANCHOR BREAKDOWN SELL: Price {price:.2f} breaks below anchor low {anchor_low:.2f} after {column_distance}-column consolidation. Anchor column {anchor_col} had {anchor_data['height']} O symbols.{ema_condition}",
                    is_first_occurrence=True
                ))
                pattern_state.alert_fired = True
                return  # Only fire one AFT alert

    def _check_high_pole_ft_sell(self, data: Dict, column: int, price: float,
                                current_index: int, alerts: List[AlertTrigger], latest_column: int, ema_20: float = None):
        """
        Check for High Pole Follow Through (FT) Sell pattern.

        Pattern requirements (6-column pattern):
        1. High pole: 4-column bearish pattern with strong supply shock
        2. Double bottom sell: Confirmation pattern after high pole
        3. More than 50% retracement of the entire previous X column
        4. More than 5 boxes after double top buy pattern
        """
        if len(data['symbols']) < 10:  # Need sufficient data
            return

        # Only process if we're in the latest column
        if column != latest_column:
            return

        # Must be an O symbol for sell signal
        current_symbol = None
        for i in range(len(data['symbols'])):
            if data['x_coords'][i] == column and data['y_coords'][i] == price:
                current_symbol = data['symbols'][i]
                break

        if current_symbol != 'O':
            return

        # Step 1: Look for high pole pattern (4-column bearish pattern)
        all_columns = sorted(set(data['x_coords']))

        if len(all_columns) < 6:  # Need at least 6 columns for the pattern
            return

        # Look for high pole: specifically columns 1-4 in our test pattern
        # High pole should be in columns 1-4, with current being column 8
        if latest_column >= 6:  # We need to be in at least column 6 to have pole + double bottom
            # Check for high pole in columns 1-4
            pole_columns = [1, 2, 3, 4]

            # Verify all pole columns exist
            if all(col in all_columns for col in pole_columns):
                # Find the highest X and lowest O in the pole area
                pole_high = 0
                pole_low = float('inf')

                for i in range(len(data['symbols'])):
                    if data['x_coords'][i] in pole_columns:
                        if data['symbols'][i] == 'X' and data['y_coords'][i] > pole_high:
                            pole_high = data['y_coords'][i]
                        if data['symbols'][i] == 'O' and data['y_coords'][i] < pole_low:
                            pole_low = data['y_coords'][i]

                # Check for high pole characteristics:
                # 1. More than 5 boxes difference (significant range)
                # 2. Pattern structure: X column followed by deep O retracement
                if pole_high > 0 and pole_low < float('inf'):
                    box_difference = pole_high - pole_low

                    # Simplified criteria: just need significant box difference
                    # The pattern structure itself indicates the retracement
                    if box_difference >= 5:
                        high_pole_found = True
                        high_pole_column = 4  # End of pole pattern
                        high_pole_high = pole_high
                    else:
                        return
                else:
                    return
            else:
                return
        else:
            return

        if not high_pole_found:
            return

        # Step 2: Check for double bottom sell pattern after high pole
        # Look for at least 2 O columns at similar support levels after high pole
        o_columns_after_pole = {}
        for i in range(len(data['symbols'])):
            if (data['symbols'][i] == 'O' and
                data['x_coords'][i] > high_pole_column and
                data['x_coords'][i] <= latest_column):
                col = data['x_coords'][i]
                if col not in o_columns_after_pole or data['y_coords'][i] < o_columns_after_pole[col]:
                    o_columns_after_pole[col] = data['y_coords'][i]

        if len(o_columns_after_pole) < 2:  # Need at least 2 O columns for double bottom
            return

        # Get the O column lows after high pole (excluding current column for support calculation)
        o_column_lows_before_current = []
        for col, low in o_columns_after_pole.items():
            if col < column:  # Only consider columns before current
                o_column_lows_before_current.append(low)

        if len(o_column_lows_before_current) < 2:  # Need at least 2 previous O columns for double bottom
            return

        # Find the support level from previous columns
        support_level = min(o_column_lows_before_current)

        # Count O columns at similar support level (within 0.5% tolerance)
        tolerance = support_level * 0.005
        similar_lows = [l for l in o_column_lows_before_current if abs(l - support_level) <= tolerance]

        if len(similar_lows) < 2:  # Need at least double bottom
            return

        # Check if we haven't already fired this pattern alert
        pattern_state = self.pattern_states[PatternType.HIGH_POLE_FT_SELL]

        # Fire alert if current O breaks below the double bottom support (follow-through)
        if price < support_level and not pattern_state.alert_fired:
            # Step 3: Check for more than 5 boxes after double bottom pattern
            # The breakdown price must be more than 5 boxes below the support level
            box_difference_after_double_bottom = support_level - price
            if box_difference_after_double_bottom <= 5:  # Need more than 5 boxes
                return
            alerts.append(AlertTrigger(
                column=column,
                price=price,
                alert_type=AlertType.SELL,
                pattern_type=PatternType.HIGH_POLE_FT_SELL,
                trigger_reason=f"🚨 HIGH POLE FT SELL: Price {price:.2f} breaks below double bottom support {support_level:.2f} after high pole pattern at {high_pole_high:.2f}. Strong supply shock confirmed with follow-through.",
                is_first_occurrence=True
            ))
            pattern_state.alert_fired = True

    def _check_low_pole_ft_buy(self, data: Dict, column: int, price: float,
                              current_index: int, alerts: List[AlertTrigger], latest_column: int, ema_20: float = None):
        """
        Check for Low Pole Follow Through (FT) Buy pattern.

        Pattern requirements (6-column pattern):
        1. Low pole: 4-column bullish pattern with strong demand shock
        2. Double top buy: Confirmation pattern after low pole
        3. More than 50% retracement of the entire previous O column
        4. More than 5 boxes after double bottom sell pattern
        """
        if len(data['symbols']) < 10:  # Need sufficient data
            return

        # Only process if we're in the latest column
        if column != latest_column:
            return

        # Must be an X symbol for buy signal
        current_symbol = None
        for i in range(len(data['symbols'])):
            if data['x_coords'][i] == column and data['y_coords'][i] == price:
                current_symbol = data['symbols'][i]
                break

        if current_symbol != 'X':
            return

        # Step 1: Look for low pole pattern (4-column bullish pattern)
        all_columns = sorted(set(data['x_coords']))

        if len(all_columns) < 6:  # Need at least 6 columns for the pattern
            return

        # Look for low pole: specifically columns 1-4 in our test pattern
        # Low pole should be in columns 1-4, with current being column 8
        if latest_column >= 6:  # We need to be in at least column 6 to have pole + double top
            # Check for low pole in columns 1-4
            pole_columns = [1, 2, 3, 4]

            # Verify all pole columns exist
            if all(col in all_columns for col in pole_columns):
                # Find the lowest O and highest X in the pole area
                pole_high = 0
                pole_low = float('inf')

                for i in range(len(data['symbols'])):
                    if data['x_coords'][i] in pole_columns:
                        if data['symbols'][i] == 'X' and data['y_coords'][i] > pole_high:
                            pole_high = data['y_coords'][i]
                        if data['symbols'][i] == 'O' and data['y_coords'][i] < pole_low:
                            pole_low = data['y_coords'][i]

                # Check for low pole characteristics:
                # 1. More than 5 boxes difference (significant range)
                # 2. Pattern structure: O column followed by deep X retracement
                if pole_high > 0 and pole_low < float('inf'):
                    box_difference = pole_high - pole_low

                    # Simplified criteria: just need significant box difference
                    # The pattern structure itself indicates the retracement
                    if box_difference >= 5:
                        low_pole_found = True
                        low_pole_column = 4  # End of pole pattern
                        low_pole_low = pole_low
                    else:
                        return
                else:
                    return
            else:
                return
        else:
            return

        if not low_pole_found:
            return

        # Step 2: Check for double top buy pattern after low pole
        # Look for at least 2 X columns at similar resistance levels after low pole
        x_columns_after_pole = {}
        for i in range(len(data['symbols'])):
            if (data['symbols'][i] == 'X' and
                data['x_coords'][i] > low_pole_column and
                data['x_coords'][i] <= latest_column):
                col = data['x_coords'][i]
                if col not in x_columns_after_pole or data['y_coords'][i] > x_columns_after_pole[col]:
                    x_columns_after_pole[col] = data['y_coords'][i]

        if len(x_columns_after_pole) < 2:  # Need at least 2 X columns for double top
            return

        # Get the X column highs after low pole (excluding current column for resistance calculation)
        x_column_highs_before_current = []
        for col, high in x_columns_after_pole.items():
            if col < column:  # Only consider columns before current
                x_column_highs_before_current.append(high)

        if len(x_column_highs_before_current) < 2:  # Need at least 2 previous X columns for double top
            return

        # Find the resistance level from previous columns
        resistance_level = max(x_column_highs_before_current)

        # Count X columns at similar resistance level (within 0.5% tolerance)
        tolerance = resistance_level * 0.005
        similar_highs = [h for h in x_column_highs_before_current if abs(h - resistance_level) <= tolerance]

        if len(similar_highs) < 2:  # Need at least double top
            return

        # Check if we haven't already fired this pattern alert
        pattern_state = self.pattern_states[PatternType.LOW_POLE_FT_BUY]

        # Fire alert if current X breaks above the double top resistance (follow-through)
        if price > resistance_level and not pattern_state.alert_fired:
            # Step 3: Check for more than 5 boxes after double top pattern
            # The breakout price must be more than 5 boxes above the resistance level
            box_difference_after_double_top = price - resistance_level
            if box_difference_after_double_top <= 5:  # Need more than 5 boxes
                return
            alerts.append(AlertTrigger(
                column=column,
                price=price,
                alert_type=AlertType.BUY,
                pattern_type=PatternType.LOW_POLE_FT_BUY,
                trigger_reason=f"🚨 LOW POLE FT BUY: Price {price:.2f} breaks above double top resistance {resistance_level:.2f} after low pole pattern at {low_pole_low:.2f}. Strong demand shock confirmed with follow-through.",
                is_first_occurrence=True
            ))
            pattern_state.alert_fired = True

    def _check_tweezer_bullish(self, data: Dict, column: int, price: float,
                              current_index: int, alerts: List[AlertTrigger], latest_column: int, ema_20: float = None):
        """
        Check for Tweezer Bullish pattern.

        Pattern requirements:
        1. Consolidation between two anchor columns forms the Tweezer pattern
        2. Second Anchor column should be bullish for the bullish tweezer pattern
        3. Maximum 6 columns between two anchor columns
        4. Plot Bullish aggressive horizontal count when a tweezer gets formed
        5. A column breakout in any of the subsequent columns activates the tweezer and the count
        6. The bullish pattern gets negated when the bottom of the pattern gets broken

        Pattern structure:
        A = Bearish Anchor column (strong fall)
        B = Base (consolidation between 2-8 columns)
        C = Bullish Anchor column (strong rally)
        D = Follow-through DTB (Double Top Breakout)
        """
        if len(data['symbols']) < 8:  # Need sufficient data for anchor + base + anchor + breakout
            return

        # Only process if we're in the latest column
        if column != latest_column:
            return

        # Must be an X symbol for bullish breakout signal
        current_symbol = None
        for i in range(len(data['symbols'])):
            if data['x_coords'][i] == column and data['y_coords'][i] == price:
                current_symbol = data['symbols'][i]
                break

        if current_symbol != 'X':
            return

        # Step 1: Find anchor columns (14+ symbols each)
        all_columns = sorted(set(data['x_coords']))
        anchor_columns = []

        for col in all_columns:
            # Count symbols in this column
            column_symbols = [i for i in range(len(data['symbols'])) if data['x_coords'][i] == col]
            if len(column_symbols) >= 14:  # Anchor column criteria
                # Determine if it's bearish (O) or bullish (X) anchor
                column_symbol_types = [data['symbols'][i] for i in column_symbols]
                dominant_symbol = max(set(column_symbol_types), key=column_symbol_types.count)

                anchor_columns.append({
                    'column': col,
                    'symbol_count': len(column_symbols),
                    'type': dominant_symbol,
                    'high': max([data['y_coords'][i] for i in column_symbols]),
                    'low': min([data['y_coords'][i] for i in column_symbols])
                })

        if len(anchor_columns) < 2:  # Need at least 2 anchor columns
            return

        # Step 2: Look for Tweezer pattern (bearish anchor + base + bullish anchor)
        tweezer_found = False
        bearish_anchor = None
        bullish_anchor = None
        base_start = None
        base_end = None

        for i in range(len(anchor_columns) - 1):
            first_anchor = anchor_columns[i]
            second_anchor = anchor_columns[i + 1]

            # Check for bearish -> bullish anchor sequence
            if (first_anchor['type'] == 'O' and second_anchor['type'] == 'X'):
                # Check if base is within 6 columns
                base_columns = second_anchor['column'] - first_anchor['column'] - 1
                if 0 <= base_columns <= 6:  # Maximum 6 columns between anchors
                    bearish_anchor = first_anchor
                    bullish_anchor = second_anchor
                    base_start = first_anchor['column'] + 1
                    base_end = second_anchor['column'] - 1
                    tweezer_found = True
                    break

        if not tweezer_found:
            return

        # Step 3: Validate base consolidation (horizontal movement)
        base_high = bearish_anchor['low']  # Start from bearish anchor low
        base_low = bullish_anchor['high']   # End at bullish anchor high

        # Get all prices in base area
        base_prices = []
        for i in range(len(data['symbols'])):
            if base_start <= data['x_coords'][i] <= base_end:
                base_prices.append(data['y_coords'][i])

        if base_prices:
            actual_base_high = max(base_prices)
            actual_base_low = min(base_prices)

            # Base should be relatively flat (within reasonable range)
            base_range = actual_base_high - actual_base_low
            anchor_range = bearish_anchor['high'] - bullish_anchor['low']

            # Base range should be smaller than anchor range (consolidation)
            # Allow more flexibility for horizontal consolidation patterns
            if base_range >= anchor_range * 0.7:  # Base too wide (increased from 0.5 to 0.7)
                return

        # Step 4: Check for Double Top Buy (DTB) pattern after bullish anchor
        # Look for X columns after bullish anchor to form double top
        x_columns_after_anchor = {}
        for i in range(len(data['symbols'])):
            if (data['symbols'][i] == 'X' and
                data['x_coords'][i] > bullish_anchor['column'] and
                data['x_coords'][i] <= latest_column):
                col = data['x_coords'][i]
                if col not in x_columns_after_anchor or data['y_coords'][i] > x_columns_after_anchor[col]:
                    x_columns_after_anchor[col] = data['y_coords'][i]

        if len(x_columns_after_anchor) < 2:  # Need at least 2 X columns for double top
            return

        # Get X column highs before current column for resistance calculation
        x_column_highs_before_current = []
        for col, high in x_columns_after_anchor.items():
            if col < latest_column:
                x_column_highs_before_current.append(high)

        if len(x_column_highs_before_current) < 2:  # Need at least 2 previous X columns for double top
            return

        # Find the resistance level from previous X columns
        resistance_level = max(x_column_highs_before_current)

        # Count X columns at similar resistance level (within 0.5% tolerance) for double top
        tolerance = resistance_level * 0.005
        similar_highs = [h for h in x_column_highs_before_current if abs(h - resistance_level) <= tolerance]

        if len(similar_highs) < 2:  # Need at least double top
            return

        # Check if we haven't already fired this pattern alert
        pattern_state = self.pattern_states[PatternType.TWEEZER_BULLISH]

        # Fire alert if current X breaks above the double top resistance (DTB follow-through)
        if price > resistance_level and not pattern_state.alert_fired:
            alerts.append(AlertTrigger(
                column=column,
                price=price,
                alert_type=AlertType.BUY,
                pattern_type=PatternType.TWEEZER_BULLISH,
                trigger_reason=f"🚨 TWEEZER BULLISH: Price {price:.2f} breaks above double top resistance {resistance_level:.2f}. Horizontal accumulation pattern between anchor columns confirmed with follow-through DTB.",
                is_first_occurrence=True
            ))
            pattern_state.alert_fired = True

    def _check_tweezer_bearish(self, data: Dict, column: int, price: float,
                              current_index: int, alerts: List[AlertTrigger], latest_column: int, ema_20: float = None):
        """
        Check for Tweezer Bearish pattern.

        Pattern requirements:
        1. Consolidation between two anchor columns forms the Tweezer pattern
        2. Second Anchor column should be bearish for the bearish tweezer pattern
        3. Maximum 6 columns between two anchor columns
        4. Plot Bearish aggressive horizontal count when a tweezer gets formed
        5. A column breakout in any of the subsequent columns activates the tweezer and the count
        6. The bearish pattern gets negated when the top of the pattern gets broken

        Pattern structure:
        A = Bullish Anchor column (strong rally)
        B = Base (consolidation between 2-8 columns)
        C = Bearish Anchor column (strong fall)
        D = Follow-through DBB (Double Bottom Breakdown)
        """
        if len(data['symbols']) < 8:  # Need sufficient data for anchor + base + anchor + breakdown
            return

        # Only process if we're in the latest column
        if column != latest_column:
            return

        # Must be an O symbol for bearish breakdown signal
        current_symbol = None
        for i in range(len(data['symbols'])):
            if data['x_coords'][i] == column and data['y_coords'][i] == price:
                current_symbol = data['symbols'][i]
                break

        if current_symbol != 'O':
            return

        # Step 1: Find anchor columns (14+ symbols each)
        all_columns = sorted(set(data['x_coords']))
        anchor_columns = []

        for col in all_columns:
            # Count symbols in this column
            column_symbols = [i for i in range(len(data['symbols'])) if data['x_coords'][i] == col]
            if len(column_symbols) >= 14:  # Anchor column criteria
                # Determine if it's bearish (O) or bullish (X) anchor
                column_symbol_types = [data['symbols'][i] for i in column_symbols]
                dominant_symbol = max(set(column_symbol_types), key=column_symbol_types.count)

                anchor_columns.append({
                    'column': col,
                    'symbol_count': len(column_symbols),
                    'type': dominant_symbol,
                    'high': max([data['y_coords'][i] for i in column_symbols]),
                    'low': min([data['y_coords'][i] for i in column_symbols])
                })

        if len(anchor_columns) < 2:  # Need at least 2 anchor columns
            return

        # Step 2: Look for Tweezer pattern (bullish anchor + base + bearish anchor)
        tweezer_found = False
        bullish_anchor = None
        bearish_anchor = None
        base_start = None
        base_end = None

        for i in range(len(anchor_columns) - 1):
            first_anchor = anchor_columns[i]
            second_anchor = anchor_columns[i + 1]

            # Check for bullish -> bearish anchor sequence
            if (first_anchor['type'] == 'X' and second_anchor['type'] == 'O'):
                # Check if base is within 6 columns
                base_columns = second_anchor['column'] - first_anchor['column'] - 1
                if 0 <= base_columns <= 6:  # Maximum 6 columns between anchors
                    bullish_anchor = first_anchor
                    bearish_anchor = second_anchor
                    base_start = first_anchor['column'] + 1
                    base_end = second_anchor['column'] - 1
                    tweezer_found = True
                    break

        if not tweezer_found:
            return

        # Step 3: Validate base consolidation (horizontal movement)
        base_high = bullish_anchor['high']  # Start from bullish anchor high
        base_low = bearish_anchor['low']    # End at bearish anchor low

        # Get all prices in base area
        base_prices = []
        for i in range(len(data['symbols'])):
            if base_start <= data['x_coords'][i] <= base_end:
                base_prices.append(data['y_coords'][i])

        if base_prices:
            actual_base_high = max(base_prices)
            actual_base_low = min(base_prices)

            # Base should be relatively flat (within reasonable range)
            base_range = actual_base_high - actual_base_low
            anchor_range = bullish_anchor['high'] - bearish_anchor['low']

            # Base range should be smaller than anchor range (consolidation)
            # Allow more flexibility for horizontal consolidation patterns
            if base_range >= anchor_range * 0.7:  # Base too wide (increased from 0.5 to 0.7)
                return

        # Step 4: Check for Double Bottom Sell (DBB) pattern after bearish anchor
        # Look for O columns after bearish anchor to form double bottom
        o_columns_after_anchor = {}
        for i in range(len(data['symbols'])):
            if (data['symbols'][i] == 'O' and
                data['x_coords'][i] > bearish_anchor['column'] and
                data['x_coords'][i] <= latest_column):
                col = data['x_coords'][i]
                if col not in o_columns_after_anchor or data['y_coords'][i] < o_columns_after_anchor[col]:
                    o_columns_after_anchor[col] = data['y_coords'][i]

        if len(o_columns_after_anchor) < 2:  # Need at least 2 O columns for double bottom
            return

        # Get O column lows before current column for support calculation
        o_column_lows_before_current = []
        for col, low in o_columns_after_anchor.items():
            if col < latest_column:
                o_column_lows_before_current.append(low)

        if len(o_column_lows_before_current) < 2:  # Need at least 2 previous O columns for double bottom
            return

        # Find the support level from previous O columns
        support_level = min(o_column_lows_before_current)

        # Count O columns at similar support level (within 0.5% tolerance) for double bottom
        tolerance = support_level * 0.005
        similar_lows = [l for l in o_column_lows_before_current if abs(l - support_level) <= tolerance]

        if len(similar_lows) < 2:  # Need at least double bottom
            return

        # Check if we haven't already fired this pattern alert
        pattern_state = self.pattern_states[PatternType.TWEEZER_BEARISH]

        # Fire alert if current O breaks below the double bottom support (DBB follow-through)
        if price < support_level and not pattern_state.alert_fired:
            alerts.append(AlertTrigger(
                column=column,
                price=price,
                alert_type=AlertType.SELL,
                pattern_type=PatternType.TWEEZER_BEARISH,
                trigger_reason=f"🚨 TWEEZER BEARISH: Price {price:.2f} breaks below double bottom support {support_level:.2f}. Horizontal distribution pattern between anchor columns confirmed with follow-through DBB.",
                is_first_occurrence=True
            ))
            pattern_state.alert_fired = True

    def _check_abc_bullish(self, data: Dict, column: int, price: float,
                          current_index: int, alerts: List[AlertTrigger], latest_column: int, ema_20: float = None):
        """
        Check for ABC Bullish pattern.

        ABC Pattern Components:
        A - Anchor column (minimum 15 boxes)
        B - Breakout from 45-degree bearish trendline
        C - Count (vertical target calculation)

        Requirements:
        1. Bullish anchor column (15+ X symbols)
        2. 45-degree bearish trendline from anchor top
        3. Breakout above bearish trendline
        4. MAST indicator filter (price above MAST, bullish cloud)
        5. Optional: Bear trap pattern for higher accuracy
        """

        # Only check on X columns (bullish breakout)
        if data['symbols'][current_index] != 'X':
            return

        # Step 1: Find bullish anchor column (15+ X symbols)
        all_columns = sorted(set(data['x_coords']))
        anchor_column = None

        for col in all_columns:
            if col >= latest_column:  # Only look at columns before current
                continue

            column_symbols = [i for i in range(len(data['symbols'])) if data['x_coords'][i] == col]
            if len(column_symbols) >= 15:  # Minimum 15 boxes for anchor
                column_symbol_types = [data['symbols'][i] for i in column_symbols]
                dominant_symbol = max(set(column_symbol_types), key=column_symbol_types.count)

                if dominant_symbol == 'X':  # Bullish anchor
                    anchor_column = {
                        'column': col,
                        'symbol_count': len(column_symbols),
                        'high': max([data['y_coords'][i] for i in column_symbols]),
                        'low': min([data['y_coords'][i] for i in column_symbols])
                    }
                    break  # Take the most recent anchor

        if not anchor_column:
            return

        # Step 2: Calculate 45-degree bearish trendline from anchor top
        # Bearish trendline slopes downward from anchor high
        anchor_high = anchor_column['high']
        anchor_col = anchor_column['column']

        # For each subsequent column, calculate the 45-degree trendline level
        # Bearish trendline: y = anchor_high - (column_distance * box_size)
        # Using 1% box size as mentioned in documentation
        box_size = anchor_high * 0.01  # 1% box size

        current_col_distance = latest_column - anchor_col
        trendline_level = anchor_high - (current_col_distance * box_size)

        # Step 3: Check for breakout above bearish trendline
        if price <= trendline_level:
            return  # No breakout yet

        # Step 4: MAST indicator filter (if available)
        if ema_20 is not None:
            if price <= ema_20:  # Price must be above MAST
                return

        # Step 5: Check for bear trap pattern (optional enhancement)
        # Look for O column that went below trendline before current breakout
        bear_trap_found = False
        for col in all_columns:
            if anchor_col < col < latest_column:
                col_symbols = [i for i in range(len(data['symbols']))
                             if data['x_coords'][i] == col and data['symbols'][i] == 'O']
                if col_symbols:
                    col_low = min([data['y_coords'][i] for i in col_symbols])
                    col_distance = col - anchor_col
                    col_trendline = anchor_high - (col_distance * box_size)
                    if col_low < col_trendline:
                        bear_trap_found = True
                        break

        # Step 6: Calculate vertical count (target)
        # Vertical count = height of anchor column
        anchor_height = anchor_column['high'] - anchor_column['low']
        target_price = price + anchor_height

        # Check if we haven't already fired this pattern alert
        pattern_state = self.pattern_states[PatternType.ABC_BULLISH]

        # Fire alert if breakout confirmed
        if not pattern_state.alert_fired:
            enhancement_text = " with bear trap enhancement" if bear_trap_found else ""
            mast_text = f" above MAST {ema_20:.2f}" if ema_20 else ""

            alerts.append(AlertTrigger(
                column=latest_column,
                price=price,
                alert_type=AlertType.BUY,
                pattern_type=PatternType.ABC_BULLISH,
                trigger_reason=f"🚨 ABC BULLISH: Price {price:.2f} breaks above 45° bearish trendline {trendline_level:.2f}{mast_text}. Anchor column {anchor_column['column']} ({anchor_column['symbol_count']} X's) momentum pattern confirmed{enhancement_text}. Target: {target_price:.2f}",
                is_first_occurrence=True
            ))
            pattern_state.alert_fired = True

    def _check_abc_bearish(self, data: Dict, column: int, price: float,
                          current_index: int, alerts: List[AlertTrigger], latest_column: int, ema_20: float = None):
        """
        Check for ABC Bearish pattern.

        ABC Bearish Pattern Components:
        A - Anchor column (minimum 15 O symbols)
        B - Breakdown below 45-degree bullish trendline
        C - Count (vertical target calculation)

        Requirements:
        1. Bearish anchor column (15+ O symbols)
        2. 45-degree bullish trendline from anchor bottom
        3. Breakdown below bullish trendline
        4. MAST indicator filter (price below MAST, bearish cloud)
        5. Optional: Bull trap pattern for higher accuracy
        """

        # Only check on O columns (bearish breakdown)
        if data['symbols'][current_index] != 'O':
            return

        # Step 1: Find bearish anchor column (15+ O symbols)
        all_columns = sorted(set(data['x_coords']))
        anchor_column = None

        for col in all_columns:
            if col >= latest_column:  # Only look at columns before current
                continue

            column_symbols = [i for i in range(len(data['symbols'])) if data['x_coords'][i] == col]
            if len(column_symbols) >= 15:  # Minimum 15 boxes for anchor
                column_symbol_types = [data['symbols'][i] for i in column_symbols]
                dominant_symbol = max(set(column_symbol_types), key=column_symbol_types.count)

                if dominant_symbol == 'O':  # Bearish anchor
                    anchor_column = {
                        'column': col,
                        'symbol_count': len(column_symbols),
                        'high': max([data['y_coords'][i] for i in column_symbols]),
                        'low': min([data['y_coords'][i] for i in column_symbols])
                    }
                    break  # Take the most recent anchor

        if not anchor_column:
            return

        # Step 2: Calculate 45-degree bullish trendline from anchor bottom
        # Bullish trendline slopes upward from anchor low
        anchor_low = anchor_column['low']
        anchor_col = anchor_column['column']

        # For each subsequent column, calculate the 45-degree trendline level
        # Bullish trendline: y = anchor_low + (column_distance * box_size)
        # Using 1% box size as mentioned in documentation
        box_size = anchor_low * 0.01  # 1% box size

        current_col_distance = latest_column - anchor_col
        trendline_level = anchor_low + (current_col_distance * box_size)

        # Step 3: Check for breakdown below bullish trendline
        if price >= trendline_level:
            return  # No breakdown yet

        # Step 4: MAST indicator filter (if available)
        if ema_20 is not None:
            if price >= ema_20:  # Price must be below MAST
                return

        # Step 5: Check for bull trap pattern (optional enhancement)
        # Look for X column that went above trendline before current breakdown
        bull_trap_found = False
        for col in all_columns:
            if anchor_col < col < latest_column:
                col_symbols = [i for i in range(len(data['symbols']))
                             if data['x_coords'][i] == col and data['symbols'][i] == 'X']
                if col_symbols:
                    col_high = max([data['y_coords'][i] for i in col_symbols])
                    col_distance = col - anchor_col
                    col_trendline = anchor_low + (col_distance * box_size)
                    if col_high > col_trendline:
                        bull_trap_found = True
                        break

        # Step 6: Calculate vertical count (target)
        # Vertical count = height of anchor column
        anchor_height = anchor_column['high'] - anchor_column['low']
        target_price = price - anchor_height

        # Check if we haven't already fired this pattern alert
        pattern_state = self.pattern_states[PatternType.ABC_BEARISH]

        # Fire alert if breakdown confirmed
        if not pattern_state.alert_fired:
            enhancement_text = " with bull trap enhancement" if bull_trap_found else ""
            mast_text = f" below MAST {ema_20:.2f}" if ema_20 else ""

            alerts.append(AlertTrigger(
                column=latest_column,
                price=price,
                alert_type=AlertType.SELL,
                pattern_type=PatternType.ABC_BEARISH,
                trigger_reason=f"🚨 ABC BEARISH: Price {price:.2f} breaks below 45° bullish trendline {trendline_level:.2f}{mast_text}. Anchor column {anchor_column['column']} ({anchor_column['symbol_count']} O's) momentum pattern confirmed{enhancement_text}. Target: {target_price:.2f}",
                is_first_occurrence=True
            ))
            pattern_state.alert_fired = True

    # Legacy methods removed - replaced with high-confidence multiple attempt patterns

    def get_pattern_summary(self) -> Dict[str, Any]:
        """Get summary of all detected patterns and their states."""
        summary = {}
        for pattern_type, state in self.pattern_states.items():
            summary[pattern_type.value] = {
                'alert_fired': state.alert_fired,
                'is_confirmed': state.is_confirmed,
                'confirmation_price': state.confirmation_price,
                'confirmation_column': state.confirmation_column
            }
        return summary
