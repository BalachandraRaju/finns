"""
PKScreener-style Breakout Scanners
Implemented based on PKScreener GitHub repository logic
https://github.com/pkjmesra/PKScreener

Scanners:
1. Probable Breakouts/Breakdown
17. 52 Week High Breakout (today)
20. Bullish for Next Day
23. Breaking Out Now
32. Intraday Breakout/Breakdown Setup
"""
import pandas as pd
import numpy as np
from typing import Tuple, Dict
import logging
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import technical indicators
try:
    from technical_indicators import TechnicalIndicators
except ImportError:
    # Try relative import
    from pkscreener_integration.technical_indicators import TechnicalIndicators

logger = logging.getLogger(__name__)


class PKBreakoutScanners:
    """PKScreener-style breakout scanners optimized for intraday trading"""

    def __init__(self, daily_data_service=None):
        """
        Initialize breakout scanners

        Args:
            daily_data_service: Service to fetch daily candle data for baseline calculations
        """
        self.daily_data_service = daily_data_service
        self.ti = TechnicalIndicators()

    # ==================== SCANNER #1: PROBABLE BREAKOUTS ====================
    def scanner_1_probable_breakout(self, df: pd.DataFrame, instrument_key: str = None) -> Tuple[bool, Dict]:
        """
        Scanner #1: Probable Breakouts/Breakdown (PKScreener Style)

        Logic from PKScreener:
        - Stock is near resistance (within 2% of recent high)
        - Volume is building up (>= 1.5x average)
        - Price consolidating in tight range

        Criteria:
        1. Close within 2% of 10-day high
        2. Volume >= 1.5x daily average
        3. Tight consolidation: ATR(14) < 3% of price

        Returns:
            (passed: bool, metrics: dict)
        """
        try:
            if len(df) < 50:
                return False, {"error": "Insufficient data"}

            metrics = {}

            # 1. Near resistance (within 2% of 10-day high)
            current_close = df['close'].iloc[0]
            ten_day_high = df['high'].iloc[0:10].max()

            distance_from_high = ((ten_day_high - current_close) / ten_day_high) * 100
            near_resistance = distance_from_high <= 2.0

            metrics['ten_day_high'] = round(ten_day_high, 2)
            metrics['distance_from_high_pct'] = round(distance_from_high, 2)
            metrics['near_resistance'] = near_resistance

            if not near_resistance:
                return False, metrics

            # 2. Volume building up
            if self.daily_data_service and instrument_key:
                recent_volume = df['volume'].iloc[0]
                daily_avg_per_min = self.daily_data_service.get_daily_volume_per_minute(instrument_key, days=20)
                volume_ratio = recent_volume / daily_avg_per_min if daily_avg_per_min > 0 else 0
                volume_building = volume_ratio >= 1.5
            else:
                recent_volume = df['volume'].iloc[0]
                avg_volume = df['volume'].iloc[1:21].mean()
                volume_ratio = recent_volume / avg_volume if avg_volume > 0 else 0
                volume_building = volume_ratio >= 1.5

            metrics['volume_ratio'] = round(volume_ratio, 2)
            metrics['volume_building'] = volume_building

            if not volume_building:
                return False, metrics

            # 3. Tight consolidation (low volatility before breakout)
            atr = self.ti.ATR(df['high'], df['low'], df['close'], timeperiod=14).iloc[0]
            atr_pct = (atr / current_close) * 100
            tight_consolidation = atr_pct < 3.0

            metrics['atr'] = round(atr, 2)
            metrics['atr_pct'] = round(atr_pct, 2)
            metrics['tight_consolidation'] = tight_consolidation

            if not tight_consolidation:
                return False, metrics

            # All conditions passed
            metrics['scanner_id'] = 1
            metrics['scanner_name'] = 'Probable Breakout'
            return True, metrics

        except Exception as e:
            logger.error(f"Error in scanner_1_probable_breakout: {e}")
            return False, {"error": str(e)}

    # ==================== SCANNER #17: 52 WEEK HIGH BREAKOUT ====================
    def scanner_17_52week_high_breakout(self, df: pd.DataFrame, daily_df: pd.DataFrame = None) -> Tuple[bool, Dict]:
        """
        Scanner #17: 52 Week High Breakout (PKScreener Style)

        Logic from PKScreener:
        - Current high >= 52-week high
        - Uses 250 trading days (50 weeks * 5 days)

        Criteria:
        1. Today's high >= 52-week high
        2. Volume >= 1.5x average (confirmation)

        Args:
            df: Intraday dataframe
            daily_df: Daily dataframe (if available, otherwise use intraday)

        Returns:
            (passed: bool, metrics: dict)
        """
        try:
            metrics = {}

            # Use daily data if available, otherwise use intraday
            data_to_use = daily_df if daily_df is not None and len(daily_df) >= 250 else df

            if len(data_to_use) < 50:
                return False, {"error": "Insufficient data for 52-week calculation"}

            # 1. 52-week high breakout
            # PKScreener uses 250 trading days (50 weeks * 5 days)
            lookback_period = min(250, len(data_to_use))
            week_52_high = data_to_use['high'].iloc[1:lookback_period].max()  # Exclude current candle
            current_high = data_to_use['high'].iloc[0]

            is_52week_breakout = current_high >= week_52_high

            metrics['52week_high'] = round(week_52_high, 2)
            metrics['current_high'] = round(current_high, 2)
            metrics['is_52week_breakout'] = is_52week_breakout

            if not is_52week_breakout:
                return False, metrics

            # 2. Volume confirmation (using intraday data)
            recent_volume = df['volume'].iloc[0]
            avg_volume = df['volume'].iloc[1:21].mean()
            volume_ratio = recent_volume / avg_volume if avg_volume > 0 else 0
            volume_confirmed = volume_ratio >= 1.5

            metrics['volume_ratio'] = round(volume_ratio, 2)
            metrics['volume_confirmed'] = volume_confirmed

            if not volume_confirmed:
                return False, metrics

            # All conditions passed
            metrics['scanner_id'] = 17
            metrics['scanner_name'] = '52-Week High Breakout'
            return True, metrics

        except Exception as e:
            logger.error(f"Error in scanner_17_52week_high_breakout: {e}")
            return False, {"error": str(e)}

    # ==================== SCANNER #20: BULLISH FOR NEXT DAY ====================
    def scanner_20_bullish_for_tomorrow(self, df: pd.DataFrame) -> Tuple[bool, Dict]:
        """
        Scanner #20: Bullish for Next Day (PKScreener Style)

        Logic from PKScreener (MACD-based):
        - MACD histogram showing bullish divergence
        - MACD line crossing above signal line
        - Momentum building for next day

        Criteria (from PKScreener code):
        1. MACD histogram: hist[t-2] < hist[t-1] AND hist[t] > hist[t-1] (V-shape recovery)
        2. MACD line - Signal line difference increasing >= 0.4
        3. MACD line > Signal line (bullish crossover)

        Returns:
            (passed: bool, metrics: dict)
        """
        try:
            if len(df) < 50:
                return False, {"error": "Insufficient data"}

            metrics = {}

            # Calculate MACD (12, 26, 9)
            macd_line, signal_line, macd_hist = self.ti.MACD(
                df['close'],
                fast=12,
                slow=26,
                signal=9
            )

            # Get last 3 values
            hist_0 = macd_hist.iloc[0]  # Most recent
            hist_1 = macd_hist.iloc[1]  # Yesterday
            hist_2 = macd_hist.iloc[2]  # Day before yesterday

            macd_0 = macd_line.iloc[0]
            macd_1 = macd_line.iloc[1]
            macd_2 = macd_line.iloc[2]

            signal_0 = signal_line.iloc[0]
            signal_1 = signal_line.iloc[1]
            signal_2 = signal_line.iloc[2]

            # 1. V-shape recovery in histogram
            v_shape = (hist_2 < hist_1) and (hist_0 > hist_1)
            metrics['v_shape_recovery'] = v_shape

            if not v_shape:
                return False, metrics

            # 2. MACD-Signal difference increasing >= 0.4
            diff_increase = (macd_0 - signal_0) - (macd_1 - signal_1)
            strong_momentum = diff_increase >= 0.4
            metrics['macd_signal_diff_increase'] = round(diff_increase, 3)
            metrics['strong_momentum'] = strong_momentum

            if not strong_momentum:
                return False, metrics

            # 3. MACD above signal (bullish)
            bullish_crossover = macd_0 > signal_0
            metrics['bullish_crossover'] = bullish_crossover

            if not bullish_crossover:
                return False, metrics

            # 4. Additional check: difference not too large (< 1.0)
            diff_not_too_large = (macd_0 - signal_0) - (macd_1 - signal_1) < 1.0
            metrics['diff_not_too_large'] = diff_not_too_large

            if not diff_not_too_large:
                return False, metrics

            # All conditions passed
            metrics['scanner_id'] = 20
            metrics['scanner_name'] = 'Bullish for Tomorrow'
            metrics['macd'] = round(macd_0, 3)
            metrics['signal'] = round(signal_0, 3)
            metrics['histogram'] = round(hist_0, 3)
            return True, metrics

        except Exception as e:
            logger.error(f"Error in scanner_20_bullish_for_tomorrow: {e}")
            return False, {"error": str(e)}




    # ==================== SCANNER #23: BREAKING OUT NOW ====================
    def scanner_23_breaking_out_now(self, df: pd.DataFrame, instrument_key: str = None) -> Tuple[bool, Dict]:
        """
        Scanner #23: Breaking Out Now (PKScreener Style)

        Logic from PKScreener:
        - Recent candle body height >= 3x average of last 10 candles
        - Bollinger Bands expansion (current ULR ratio vs max of last 5)
        - Strong momentum candle breaking out

        Criteria:
        1. Current candle body >= 3x average body of last 10 candles
        2. Bollinger Bands ULR ratio check
        3. Green candle (bullish)

        Returns:
            (passed: bool, metrics: dict)
        """
        try:
            if len(df) < 30:
                return False, {"error": "Insufficient data"}

            metrics = {}

            # 1. Candle body height comparison
            def get_candle_body_height(candle_df):
                """Calculate candle body height (abs(close - open))"""
                if len(candle_df) == 0:
                    return 0
                return abs(candle_df['close'].iloc[0] - candle_df['open'].iloc[0])

            recent_candle_height = get_candle_body_height(df.iloc[0:1])

            if recent_candle_height <= 0:
                return False, {"error": "Zero candle height"}

            # Calculate average of last 10 candles (excluding current)
            total_candle_height = 0
            for i in range(1, 11):
                candle_height = abs(df['close'].iloc[i] - df['open'].iloc[i])
                total_candle_height += candle_height

            avg_candle_height = total_candle_height / 10

            # Check if current candle >= 3x average
            is_breakout_candle = recent_candle_height >= (3 * avg_candle_height)

            metrics['recent_candle_height'] = round(recent_candle_height, 2)
            metrics['avg_candle_height'] = round(avg_candle_height, 2)
            metrics['height_ratio'] = round(recent_candle_height / avg_candle_height, 2) if avg_candle_height > 0 else 0
            metrics['is_breakout_candle'] = is_breakout_candle

            if not is_breakout_candle:
                return False, metrics

            # 2. Bollinger Bands expansion check
            upper_band, middle_band, lower_band = self.ti.BBANDS(
                df['close'],
                timeperiod=20,
                std=2
            )

            # Calculate ULR (Upper - Lower Range) for last 6 candles
            ulr = upper_band - lower_band
            ulr_recent = ulr.iloc[0:6]

            current_ulr = ulr_recent.iloc[0]
            max_ulr_last_5 = ulr_recent.iloc[1:6].max()

            ulr_ratio = current_ulr / max_ulr_last_5 if max_ulr_last_5 > 0 else 0

            metrics['bbands_ulr_ratio'] = round(ulr_ratio, 2)

            # 3. Green candle (bullish breakout)
            is_green = df['close'].iloc[0] > df['open'].iloc[0]
            metrics['is_green'] = is_green

            if not is_green:
                return False, metrics

            # All conditions passed
            metrics['scanner_id'] = 23
            metrics['scanner_name'] = 'Breaking Out Now'
            return True, metrics

        except Exception as e:
            logger.error(f"Error in scanner_23_breaking_out_now: {e}")
            return False, {"error": str(e)}


    # ==================== SCANNER #32: INTRADAY BREAKOUT/BREAKDOWN SETUP ====================
    def scanner_32_intraday_breakout_setup(self, df: pd.DataFrame, instrument_key: str = None) -> Tuple[bool, Dict]:
        """
        Scanner #32: Intraday Breakout/Breakdown Setup (PKScreener Style)

        Logic for intraday breakout setup:
        - Price breaking above opening range high (first 15 minutes)
        - Volume surge (>= 2x average)
        - Strong momentum (RSI > 60 for breakout, RSI < 40 for breakdown)

        Criteria:
        1. Price > Opening Range High (first 15 candles) OR Price < Opening Range Low
        2. Volume >= 2x daily average per minute
        3. RSI confirmation (> 60 for breakout, < 40 for breakdown)

        Returns:
            (passed: bool, metrics: dict)
        """
        try:
            if len(df) < 30:
                return False, {"error": "Insufficient data"}

            metrics = {}

            # 1. Opening range breakout (first 15 minutes = 15 candles for 1-min data)
            opening_range_candles = min(15, len(df) - 1)
            opening_range_high = df['high'].iloc[1:opening_range_candles+1].max()
            opening_range_low = df['low'].iloc[1:opening_range_candles+1].min()

            current_close = df['close'].iloc[0]

            is_breakout = current_close > opening_range_high
            is_breakdown = current_close < opening_range_low

            metrics['opening_range_high'] = round(opening_range_high, 2)
            metrics['opening_range_low'] = round(opening_range_low, 2)
            metrics['current_close'] = round(current_close, 2)
            metrics['is_breakout'] = is_breakout
            metrics['is_breakdown'] = is_breakdown

            if not (is_breakout or is_breakdown):
                return False, metrics

            # 2. Volume surge
            if self.daily_data_service and instrument_key:
                recent_volume = df['volume'].iloc[0]
                daily_avg_per_min = self.daily_data_service.get_daily_volume_per_minute(instrument_key, days=20)
                volume_ratio = recent_volume / daily_avg_per_min if daily_avg_per_min > 0 else 0
                volume_surge = volume_ratio >= 2.0
            else:
                recent_volume = df['volume'].iloc[0]
                avg_volume = df['volume'].iloc[1:21].mean()
                volume_ratio = recent_volume / avg_volume if avg_volume > 0 else 0
                volume_surge = volume_ratio >= 2.0

            metrics['volume_ratio'] = round(volume_ratio, 2)
            metrics['volume_surge'] = volume_surge

            if not volume_surge:
                return False, metrics

            # 3. RSI confirmation
            rsi = self.ti.RSI(df['close'], timeperiod=14).iloc[0]

            if is_breakout:
                rsi_confirmed = rsi > 60
                setup_type = 'Breakout'
            else:  # is_breakdown
                rsi_confirmed = rsi < 40
                setup_type = 'Breakdown'

            metrics['rsi'] = round(rsi, 2)
            metrics['rsi_confirmed'] = rsi_confirmed
            metrics['setup_type'] = setup_type

            if not rsi_confirmed:
                return False, metrics

            # All conditions passed
            metrics['scanner_id'] = 32
            metrics['scanner_name'] = f'Intraday {setup_type} Setup'
            return True, metrics

        except Exception as e:
            logger.error(f"Error in scanner_32_intraday_breakout_setup: {e}")
            return False, {"error": str(e)}


def get_breakout_scanners(daily_data_service=None):
    """Factory function to get breakout scanners instance"""
    return PKBreakoutScanners(daily_data_service=daily_data_service)

