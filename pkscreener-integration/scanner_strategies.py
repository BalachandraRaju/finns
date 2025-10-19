"""
Scanner Strategies Module
Implements PKScreener strategies for intraday momentum detection
Uses DAILY volume averages for accurate intraday signals
"""
import pandas as pd
import numpy as np
from typing import Tuple, Dict, Optional
import logging
import sys
import os

# Add current directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from technical_indicators import TechnicalIndicators as ti

logger = logging.getLogger(__name__)


class ScannerStrategies:
    """
    Implements PKScreener scanner strategies for momentum/scalping detection
    All scanners work on 1-minute candle data
    Uses DAILY volume averages for accurate intraday volume comparison
    """

    def __init__(self, daily_data_service=None):
        self.ti = ti
        self.daily_data_service = daily_data_service

    # ==================== SCANNER #1 ====================
    def scanner_1_volume_momentum_breakout_atr(self, df: pd.DataFrame, instrument_key: str = None) -> Tuple[bool, Dict]:
        """
        Scanner #1: HIGH VOLUME BREAKOUT (PIP Scanner Style - INTRADAY OPTIMIZED)

        Criteria (SIMPLIFIED for intraday):
        1. Volume ratio >= 1.5x (current volume vs DAILY average per minute)
        2. Price momentum: Close > Open (green candle)
        3. Price action: Close near high (upper 50% of candle range)

        Returns:
            (passed: bool, metrics: dict)
        """
        try:
            if len(df) < 20:
                return False, {"error": "Insufficient data"}

            metrics = {}

            # 1. Volume Scanner - Compare to DAILY average
            recent_volume = df['volume'].iloc[0]

            if self.daily_data_service and instrument_key:
                # Use daily volume baseline
                volume_ratio = self.ti.calculate_intraday_volume_ratio(
                    recent_volume, instrument_key, self.daily_data_service
                )
                # INTRADAY THRESHOLD: 1.5x (industry standard for intraday momentum)
                volume_pass = volume_ratio >= 1.5
            else:
                # Fallback to intraday average
                volume_ratio = self.ti.calculate_volume_ratio(df, period=20)
                volume_pass = volume_ratio >= 1.5

            metrics['volume_ratio'] = volume_ratio
            metrics['recent_volume'] = int(recent_volume)

            if not volume_pass:
                return False, metrics

            # 2. Green Candle (bullish momentum)
            current_candle = df.iloc[0]
            is_green = current_candle['close'] > current_candle['open']
            metrics['is_green'] = is_green

            if not is_green:
                return False, metrics

            # 3. Close near high (strong buying pressure)
            candle_range = current_candle['high'] - current_candle['low']
            if candle_range > 0:
                close_position = (current_candle['close'] - current_candle['low']) / candle_range
                close_near_high = close_position >= 0.5  # Close in upper 50% of range
            else:
                close_near_high = True  # Doji candle, allow it

            metrics['close_position'] = round(close_position * 100, 1) if candle_range > 0 else 50.0
            metrics['close_near_high'] = close_near_high

            if not close_near_high:
                return False, metrics

            # All conditions passed
            metrics['scanner_id'] = 1
            metrics['scanner_name'] = 'High Volume Breakout (Intraday)'
            return True, metrics

        except Exception as e:
            logger.error(f"Error in scanner_1: {e}")
            return False, {"error": str(e)}

    # ==================== SCANNER #2 ====================
    def scanner_2_volume_momentum_atr(self, df: pd.DataFrame) -> Tuple[bool, Dict]:
        """Scanner #2: Volume + Momentum + ATR (no breakout check)"""
        try:
            if len(df) < 50:
                return False, {"error": "Insufficient data"}

            metrics = {}

            # 1. Volume Scanner
            volume_ratio = self.ti.calculate_volume_ratio(df, period=20)
            volume_pass = volume_ratio >= 2.5
            metrics['volume_ratio'] = volume_ratio

            recent_volume = df['volume'].iloc[0]
            avg_volume = df['volume'].head(20).mean()
            has_min_volume = recent_volume >= 10000 or avg_volume >= 10000
            metrics['recent_volume'] = int(recent_volume)
            metrics['avg_volume'] = int(avg_volume)

            if not (volume_pass and has_min_volume):
                return False, metrics

            # 2. High Momentum
            momentum_pass = self._check_momentum(df)
            metrics['momentum'] = momentum_pass
            if not momentum_pass:
                return False, metrics

            # 3. ATR Cross
            atr_cross_pass, atr_metrics = self._check_atr_cross(df)
            metrics.update(atr_metrics)
            if not atr_cross_pass:
                return False, metrics

            metrics['scanner_id'] = 2
            metrics['scanner_name'] = 'Volume + Momentum + ATR'
            return True, metrics

        except Exception as e:
            logger.error(f"Error in scanner_2: {e}")
            return False, {"error": str(e)}

    # ==================== SCANNER #3 ====================
    def scanner_3_volume_momentum(self, df: pd.DataFrame) -> Tuple[bool, Dict]:
        """Scanner #3: Volume + Momentum"""
        try:
            if len(df) < 50:
                return False, {"error": "Insufficient data"}

            metrics = {}

            # 1. Volume Scanner
            volume_ratio = self.ti.calculate_volume_ratio(df, period=20)
            volume_pass = volume_ratio >= 2.5
            metrics['volume_ratio'] = volume_ratio

            recent_volume = df['volume'].iloc[0]
            avg_volume = df['volume'].head(20).mean()
            has_min_volume = recent_volume >= 10000 or avg_volume >= 10000
            metrics['recent_volume'] = int(recent_volume)
            metrics['avg_volume'] = int(avg_volume)

            if not (volume_pass and has_min_volume):
                return False, metrics

            # 2. High Momentum
            momentum_pass = self._check_momentum(df)
            metrics['momentum'] = momentum_pass
            if not momentum_pass:
                return False, metrics

            metrics['scanner_id'] = 3
            metrics['scanner_name'] = 'Volume + Momentum'
            return True, metrics

        except Exception as e:
            logger.error(f"Error in scanner_3: {e}")
            return False, {"error": str(e)}

    # ==================== SCANNER #4 ====================
    def scanner_4_volume_atr(self, df: pd.DataFrame) -> Tuple[bool, Dict]:
        """Scanner #4: Volume + ATR"""
        try:
            if len(df) < 50:
                return False, {"error": "Insufficient data"}

            metrics = {}

            # 1. Volume Scanner
            volume_ratio = self.ti.calculate_volume_ratio(df, period=20)
            volume_pass = volume_ratio >= 2.5
            metrics['volume_ratio'] = volume_ratio

            recent_volume = df['volume'].iloc[0]
            avg_volume = df['volume'].head(20).mean()
            has_min_volume = recent_volume >= 10000 or avg_volume >= 10000
            metrics['recent_volume'] = int(recent_volume)
            metrics['avg_volume'] = int(avg_volume)

            if not (volume_pass and has_min_volume):
                return False, metrics

            # 2. ATR Cross
            atr_cross_pass, atr_metrics = self._check_atr_cross(df)
            metrics.update(atr_metrics)
            if not atr_cross_pass:
                return False, metrics

            metrics['scanner_id'] = 4
            metrics['scanner_name'] = 'Volume + ATR'
            return True, metrics

        except Exception as e:
            logger.error(f"Error in scanner_4: {e}")
            return False, {"error": str(e)}

    # ==================== SCANNER #5 ====================
    def scanner_5_volume_bidask(self, df: pd.DataFrame) -> Tuple[bool, Dict]:
        """Scanner #5: Volume + Bid/Ask Build Up (using volume acceleration proxy)"""
        try:
            if len(df) < 50:
                return False, {"error": "Insufficient data"}

            metrics = {}

            # 1. Volume Scanner (higher threshold)
            volume_ratio = self.ti.calculate_volume_ratio(df, period=20)
            volume_pass = volume_ratio >= 3.0  # Higher threshold for bid/ask buildup
            metrics['volume_ratio'] = volume_ratio

            recent_volume = df['volume'].iloc[0]
            avg_volume = df['volume'].head(20).mean()
            has_min_volume = recent_volume >= 10000 or avg_volume >= 10000
            metrics['recent_volume'] = int(recent_volume)
            metrics['avg_volume'] = int(avg_volume)

            if not (volume_pass and has_min_volume):
                return False, metrics

            # 2. Bid/Ask Build Up (proxy: volume acceleration)
            recent_5_vol = df['volume'].head(5).mean()
            prev_20_vol = df['volume'].iloc[5:25].mean()
            vol_acceleration = recent_5_vol / prev_20_vol if prev_20_vol > 0 else 0
            metrics['volume_acceleration'] = round(vol_acceleration, 2)

            acceleration_pass = vol_acceleration >= 1.5
            if not acceleration_pass:
                return False, metrics

            metrics['scanner_id'] = 5
            metrics['scanner_name'] = 'Volume + Bid/Ask Build Up'
            return True, metrics

        except Exception as e:
            logger.error(f"Error in scanner_5: {e}")
            return False, {"error": str(e)}

    # ==================== SCANNER #6 ====================
    def scanner_6_volume_atr_trailing(self, df: pd.DataFrame) -> Tuple[bool, Dict]:
        """Scanner #6: Volume + ATR + Trailing Stop"""
        try:
            if len(df) < 50:
                return False, {"error": "Insufficient data"}

            metrics = {}

            # 1. Volume Scanner
            volume_ratio = self.ti.calculate_volume_ratio(df, period=20)
            volume_pass = volume_ratio >= 2.5
            metrics['volume_ratio'] = volume_ratio

            recent_volume = df['volume'].iloc[0]
            avg_volume = df['volume'].head(20).mean()
            has_min_volume = recent_volume >= 10000 or avg_volume >= 10000
            metrics['recent_volume'] = int(recent_volume)
            metrics['avg_volume'] = int(avg_volume)

            if not (volume_pass and has_min_volume):
                return False, metrics

            # 2. ATR Cross
            atr_cross_pass, atr_metrics = self._check_atr_cross(df)
            metrics.update(atr_metrics)
            if not atr_cross_pass:
                return False, metrics

            # 3. ATR Trailing Stop
            atr_stop_pass, atr_stop_metrics = self._check_atr_trailing_stop(df)
            metrics.update(atr_stop_metrics)
            if not atr_stop_pass:
                return False, metrics

            metrics['scanner_id'] = 6
            metrics['scanner_name'] = 'Volume + ATR + Trailing Stop'
            return True, metrics

        except Exception as e:
            logger.error(f"Error in scanner_6: {e}")
            return False, {"error": str(e)}

    # ==================== SCANNER #7 ====================
    def scanner_7_volume_trailing(self, df: pd.DataFrame) -> Tuple[bool, Dict]:
        """Scanner #7: Volume + Trailing Stop"""
        try:
            if len(df) < 50:
                return False, {"error": "Insufficient data"}

            metrics = {}

            # 1. Volume Scanner
            volume_ratio = self.ti.calculate_volume_ratio(df, period=20)
            volume_pass = volume_ratio >= 2.5
            metrics['volume_ratio'] = volume_ratio

            recent_volume = df['volume'].iloc[0]
            avg_volume = df['volume'].head(20).mean()
            has_min_volume = recent_volume >= 10000 or avg_volume >= 10000
            metrics['recent_volume'] = int(recent_volume)
            metrics['avg_volume'] = int(avg_volume)

            if not (volume_pass and has_min_volume):
                return False, metrics

            # 2. ATR Trailing Stop
            atr_stop_pass, atr_stop_metrics = self._check_atr_trailing_stop(df)
            metrics.update(atr_stop_metrics)
            if not atr_stop_pass:
                return False, metrics

            metrics['scanner_id'] = 7
            metrics['scanner_name'] = 'Volume + Trailing Stop'
            return True, metrics

        except Exception as e:
            logger.error(f"Error in scanner_7: {e}")
            return False, {"error": str(e)}

    # ==================== SCANNER #8 ====================
    def scanner_8_momentum_atr(self, df: pd.DataFrame) -> Tuple[bool, Dict]:
        """Scanner #8: Momentum + ATR"""
        try:
            if len(df) < 50:
                return False, {"error": "Insufficient data"}

            metrics = {}

            # 1. High Momentum
            momentum_pass = self._check_momentum(df)
            metrics['momentum'] = momentum_pass
            if not momentum_pass:
                return False, metrics

            # 2. ATR Cross
            atr_cross_pass, atr_metrics = self._check_atr_cross(df)
            metrics.update(atr_metrics)
            if not atr_cross_pass:
                return False, metrics

            metrics['scanner_id'] = 8
            metrics['scanner_name'] = 'Momentum + ATR'
            return True, metrics

        except Exception as e:
            logger.error(f"Error in scanner_8: {e}")
            return False, {"error": str(e)}

    # ==================== SCANNER #9 ====================
    def scanner_9_momentum_trailing(self, df: pd.DataFrame) -> Tuple[bool, Dict]:
        """Scanner #9: Momentum + Trailing Stop"""
        try:
            if len(df) < 50:
                return False, {"error": "Insufficient data"}

            metrics = {}

            # 1. High Momentum
            momentum_pass = self._check_momentum(df)
            metrics['momentum'] = momentum_pass
            if not momentum_pass:
                return False, metrics

            # 2. ATR Trailing Stop
            atr_stop_pass, atr_stop_metrics = self._check_atr_trailing_stop(df)
            metrics.update(atr_stop_metrics)
            if not atr_stop_pass:
                return False, metrics

            metrics['scanner_id'] = 9
            metrics['scanner_name'] = 'Momentum + Trailing Stop'
            return True, metrics

        except Exception as e:
            logger.error(f"Error in scanner_9: {e}")
            return False, {"error": str(e)}

    # ==================== SCANNER #10 ====================
    def scanner_10_atr_trailing(self, df: pd.DataFrame) -> Tuple[bool, Dict]:
        """Scanner #10: ATR + Trailing Stop"""
        try:
            if len(df) < 50:
                return False, {"error": "Insufficient data"}

            metrics = {}

            # 1. ATR Cross
            atr_cross_pass, atr_metrics = self._check_atr_cross(df)
            metrics.update(atr_metrics)
            if not atr_cross_pass:
                return False, metrics

            # 2. ATR Trailing Stop
            atr_stop_pass, atr_stop_metrics = self._check_atr_trailing_stop(df)
            metrics.update(atr_stop_metrics)
            if not atr_stop_pass:
                return False, metrics

            metrics['scanner_id'] = 10
            metrics['scanner_name'] = 'ATR + Trailing Stop'
            return True, metrics

        except Exception as e:
            logger.error(f"Error in scanner_10: {e}")
            return False, {"error": str(e)}

    # ==================== SCANNER #11 ====================
    def scanner_11_ttm_squeeze_rsi(self, df: pd.DataFrame) -> Tuple[bool, Dict]:
        """Scanner #11: TTM Squeeze Buy + Intraday RSI b/w 0 to 54"""
        try:
            if len(df) < 50:
                return False, {"error": "Insufficient data"}

            metrics = {}

            close = df['close']
            high = df['high']
            low = df['low']

            # 1. TTM Squeeze: Bollinger Bands inside Keltner Channels
            bb_upper, bb_middle, bb_lower = self.ti.BBANDS(close, timeperiod=20, nbdevup=2, nbdevdn=2)
            atr = self.ti.ATR(high, low, close, timeperiod=20)

            # Keltner Channels = Middle (SMA) +/- (1.5 * ATR)
            kc_upper = bb_middle + (1.5 * atr)
            kc_lower = bb_middle - (1.5 * atr)

            # Squeeze is ON when BB is inside KC
            squeeze_on = (bb_lower.iloc[0] > kc_lower.iloc[0]) and (bb_upper.iloc[0] < kc_upper.iloc[0])
            metrics['ttm_squeeze'] = squeeze_on

            if not squeeze_on:
                return False, metrics

            # 2. Intraday RSI between 0 to 54
            rsi = self.ti.RSI(close, timeperiod=14)
            current_rsi = rsi.iloc[0]
            metrics['rsi'] = round(current_rsi, 2)

            rsi_pass = 0 <= current_rsi <= 54
            if not rsi_pass:
                return False, metrics

            # 3. Momentum confirmation
            momentum_pass = self._check_momentum(df)
            metrics['momentum'] = momentum_pass
            if not momentum_pass:
                return False, metrics

            metrics['scanner_id'] = 11
            metrics['scanner_name'] = 'TTM Squeeze + RSI'
            return True, metrics

        except Exception as e:
            logger.error(f"Error in scanner_11: {e}")
            return False, {"error": str(e)}

    # ==================== SCANNER #12 ====================
    def scanner_12_volume_momentum_breakout_atr_rsi(self, df: pd.DataFrame, instrument_key: str = None) -> Tuple[bool, Dict]:
        """
        Scanner #12: HIGH VOLUME + STRONG MOMENTUM (PIP Scanner 12 Style - INTRADAY OPTIMIZED)

        Criteria (SIMPLIFIED for intraday):
        1. Volume ratio >= 1.5x (vs DAILY average per minute)
        2. Strong momentum: 2 consecutive green candles
        3. Increasing closes: Each close higher than previous

        Returns:
            (passed: bool, metrics: dict)
        """
        try:
            if len(df) < 20:
                return False, {"error": "Insufficient data"}

            metrics = {}

            # 1. Volume Scanner - Compare to DAILY average
            recent_volume = df['volume'].iloc[0]

            if self.daily_data_service and instrument_key:
                volume_ratio = self.ti.calculate_intraday_volume_ratio(
                    recent_volume, instrument_key, self.daily_data_service
                )
                volume_pass = volume_ratio >= 1.5
            else:
                volume_ratio = self.ti.calculate_volume_ratio(df, period=20)
                volume_pass = volume_ratio >= 1.5

            metrics['volume_ratio'] = volume_ratio
            metrics['recent_volume'] = int(recent_volume)

            if not volume_pass:
                return False, metrics

            # 2. Two consecutive green candles
            candle_0 = df.iloc[0]
            candle_1 = df.iloc[1]

            green_0 = candle_0['close'] > candle_0['open']
            green_1 = candle_1['close'] > candle_1['open']

            two_green = green_0 and green_1
            metrics['two_green_candles'] = two_green

            if not two_green:
                return False, metrics

            # 3. Increasing closes (momentum building)
            increasing_closes = candle_0['close'] > candle_1['close']
            metrics['increasing_closes'] = increasing_closes

            if not increasing_closes:
                return False, metrics

            # All conditions passed
            metrics['scanner_id'] = 12
            metrics['scanner_name'] = 'High Volume + Strong Momentum (Intraday)'
            return True, metrics

        except Exception as e:
            logger.error(f"Error in scanner_12: {e}")
            return False, {"error": str(e)}

    # ==================== SCANNER #13 ====================
    def scanner_13_volume_atr_rsi(self, df: pd.DataFrame) -> Tuple[bool, Dict]:
        """Scanner #13: Volume + ATR + Intraday RSI b/w 0 to 54"""
        try:
            if len(df) < 50:
                return False, {"error": "Insufficient data"}

            metrics = {}

            # 1. Volume Scanner
            volume_ratio = self.ti.calculate_volume_ratio(df, period=20)
            volume_pass = volume_ratio >= 2.5
            metrics['volume_ratio'] = volume_ratio

            recent_volume = df['volume'].iloc[0]
            avg_volume = df['volume'].head(20).mean()
            has_min_volume = recent_volume >= 10000 or avg_volume >= 10000
            metrics['recent_volume'] = int(recent_volume)
            metrics['avg_volume'] = int(avg_volume)

            if not (volume_pass and has_min_volume):
                return False, metrics

            # 2. ATR Cross
            atr_cross_pass, atr_metrics = self._check_atr_cross(df)
            metrics.update(atr_metrics)
            if not atr_cross_pass:
                return False, metrics

            # 3. Intraday RSI between 0 to 54
            close = df['close']
            rsi = self.ti.RSI(close, timeperiod=14)
            current_rsi = rsi.iloc[0]
            metrics['rsi'] = round(current_rsi, 2)

            rsi_pass = 0 <= current_rsi <= 54
            if not rsi_pass:
                return False, metrics

            metrics['scanner_id'] = 13
            metrics['scanner_name'] = 'Volume + ATR + RSI'
            return True, metrics

        except Exception as e:
            logger.error(f"Error in scanner_13: {e}")
            return False, {"error": str(e)}

    # ==================== SCANNER #14 ====================
    def scanner_14_vcp_chart_patterns_ma_support(self, df: pd.DataFrame, instrument_key: str = None) -> Tuple[bool, Dict]:
        """
        Scanner #14: VCP (Mark Minervini) + Chart Patterns + MA Support

        VCP (Volatility Contraction Pattern) criteria:
        1. Price consolidating with decreasing volatility
        2. Volume drying up during consolidation
        3. Price above key moving averages
        4. Recent volume spike on breakout

        Note: VCP is typically a weekly pattern, adapted for intraday 1-minute data

        Returns:
            (passed: bool, metrics: dict)
        """
        try:
            if len(df) < 200:
                return False, {"error": "Insufficient data for VCP"}

            metrics = {}

            # 1. Moving Average Alignment (bullish setup)
            ma_pass, ma_metrics = self._check_ma_alignment(df)
            metrics.update(ma_metrics)

            if not ma_pass:
                return False, metrics

            # 2. Volatility Contraction (ATR decreasing)
            volatility_pass, vol_metrics = self._check_volatility_contraction(df)
            metrics.update(vol_metrics)

            if not volatility_pass:
                return False, metrics

            # 3. Volume Pattern (drying up then spiking)
            volume_pattern_pass, vol_pattern_metrics = self._check_vcp_volume_pattern(df)
            metrics.update(vol_pattern_metrics)

            if not volume_pattern_pass:
                return False, metrics

            # 4. Price above MA support
            recent_close = df['close'].iloc[0]
            ema_20 = self.ti.EMA(df['close'], 20).iloc[0]
            sma_50 = self.ti.SMA(df['close'], 50).iloc[0]

            price_above_ma = recent_close > ema_20 and recent_close > sma_50
            metrics['price_above_ma'] = price_above_ma

            if not price_above_ma:
                return False, metrics

            # All conditions passed
            metrics['scanner_id'] = 14
            metrics['scanner_name'] = 'VCP + Chart Patterns + MA Support'
            return True, metrics

        except Exception as e:
            logger.error(f"Error in scanner_14: {e}")
            return False, {"error": str(e)}

    # ==================== SCANNER #15 ====================
    def scanner_15_vcp_patterns_ma(self, df: pd.DataFrame) -> Tuple[bool, Dict]:
        """Scanner #15: VCP + Chart Patterns + MA Support (similar to #14)"""
        try:
            if len(df) < 50:
                return False, {"error": "Insufficient data"}

            metrics = {}

            # 1. VCP (simplified for intraday)
            vcp_pass = self._check_vcp_simplified(df)
            metrics['vcp'] = vcp_pass
            if not vcp_pass:
                return False, metrics

            # 2. MA Alignment
            ma_align_pass = self._check_ma_alignment(df)
            metrics['ma_alignment'] = ma_align_pass
            if not ma_align_pass:
                return False, metrics

            # 3. RSI confirmation
            close = df['close']
            rsi = self.ti.RSI(close, timeperiod=14)
            current_rsi = rsi.iloc[0]
            metrics['rsi'] = round(current_rsi, 2)

            rsi_pass = current_rsi >= 50
            if not rsi_pass:
                return False, metrics

            metrics['scanner_id'] = 15
            metrics['scanner_name'] = 'VCP + Patterns + MA'
            return True, metrics

        except Exception as e:
            logger.error(f"Error in scanner_15: {e}")
            return False, {"error": str(e)}

    # ==================== SCANNER #16 ====================
    def scanner_16_breakout_vcp_patterns_ma(self, df: pd.DataFrame) -> Tuple[bool, Dict]:
        """Scanner #16: Already Breaking out + VCP + Chart Patterns + MA Support"""
        try:
            if len(df) < 50:
                return False, {"error": "Insufficient data"}

            metrics = {}

            # 1. Breaking Out
            breakout_pass = self.ti.is_breaking_out(df, lookback_period=20)
            metrics['breakout'] = breakout_pass
            if not breakout_pass:
                return False, metrics

            # 2. VCP (simplified for intraday)
            vcp_pass = self._check_vcp_simplified(df)
            metrics['vcp'] = vcp_pass
            if not vcp_pass:
                return False, metrics

            # 3. MA Alignment
            ma_align_pass = self._check_ma_alignment(df)
            metrics['ma_alignment'] = ma_align_pass
            if not ma_align_pass:
                return False, metrics

            # 4. RSI confirmation
            close = df['close']
            rsi = self.ti.RSI(close, timeperiod=14)
            current_rsi = rsi.iloc[0]
            metrics['rsi'] = round(current_rsi, 2)

            rsi_pass = current_rsi >= 50
            if not rsi_pass:
                return False, metrics

            metrics['scanner_id'] = 16
            metrics['scanner_name'] = 'Breakout + VCP + Patterns + MA'
            return True, metrics

        except Exception as e:
            logger.error(f"Error in scanner_16: {e}")
            return False, {"error": str(e)}

    # ==================== SCANNER #17 ====================
    def scanner_17_trailing_vcp(self, df: pd.DataFrame) -> Tuple[bool, Dict]:
        """Scanner #17: ATR Trailing Stops + VCP (Minervini)"""
        try:
            if len(df) < 50:
                return False, {"error": "Insufficient data"}

            metrics = {}

            # 1. ATR Trailing Stop
            atr_stop_pass, atr_stop_metrics = self._check_atr_trailing_stop(df)
            metrics.update(atr_stop_metrics)
            if not atr_stop_pass:
                return False, metrics

            # 2. VCP (simplified for intraday)
            vcp_pass = self._check_vcp_simplified(df)
            metrics['vcp'] = vcp_pass
            if not vcp_pass:
                return False, metrics

            metrics['scanner_id'] = 17
            metrics['scanner_name'] = 'Trailing Stop + VCP'
            return True, metrics

        except Exception as e:
            logger.error(f"Error in scanner_17: {e}")
            return False, {"error": str(e)}

    # ==================== SCANNER #18 ====================
    def scanner_18_vcp_trailing(self, df: pd.DataFrame) -> Tuple[bool, Dict]:
        """Scanner #18: VCP + ATR Trailing Stops"""
        try:
            if len(df) < 50:
                return False, {"error": "Insufficient data"}

            metrics = {}

            # 1. VCP (simplified for intraday)
            vcp_pass = self._check_vcp_simplified(df)
            metrics['vcp'] = vcp_pass
            if not vcp_pass:
                return False, metrics

            # 2. ATR Trailing Stop
            atr_stop_pass, atr_stop_metrics = self._check_atr_trailing_stop(df)
            metrics.update(atr_stop_metrics)
            if not atr_stop_pass:
                return False, metrics

            metrics['scanner_id'] = 18
            metrics['scanner_name'] = 'VCP + Trailing Stop'
            return True, metrics

        except Exception as e:
            logger.error(f"Error in scanner_18: {e}")
            return False, {"error": str(e)}

    # ==================== SCANNER #19 ====================
    def scanner_19_nifty_vcp_trailing(self, df: pd.DataFrame) -> Tuple[bool, Dict]:
        """Scanner #19: Nifty 50, Nifty Bank + VCP + ATR Trailing Stops"""
        try:
            if len(df) < 50:
                return False, {"error": "Insufficient data"}

            metrics = {}

            # 1. VCP (simplified for intraday)
            vcp_pass = self._check_vcp_simplified(df)
            metrics['vcp'] = vcp_pass
            if not vcp_pass:
                return False, metrics

            # 2. ATR Trailing Stop
            atr_stop_pass, atr_stop_metrics = self._check_atr_trailing_stop(df)
            metrics.update(atr_stop_metrics)
            if not atr_stop_pass:
                return False, metrics

            # 3. MA Alignment (additional filter for Nifty stocks)
            ma_align_pass = self._check_ma_alignment(df)
            metrics['ma_alignment'] = ma_align_pass
            if not ma_align_pass:
                return False, metrics

            metrics['scanner_id'] = 19
            metrics['scanner_name'] = 'Nifty + VCP + Trailing Stop'
            return True, metrics

        except Exception as e:
            logger.error(f"Error in scanner_19: {e}")
            return False, {"error": str(e)}

    # ==================== SCANNER #20 ====================
    def scanner_20_comprehensive(self, df: pd.DataFrame, instrument_key: str = None) -> Tuple[bool, Dict]:
        """
        Scanner #20: Volume + Momentum + Breakout + ATR + VCP + ATR Trailing Stops

        Most comprehensive scanner combining multiple strategies

        Returns:
            (passed: bool, metrics: dict)
        """
        try:
            # First check Scanner #1 (Volume + Momentum + Breakout + ATR)
            scanner_1_pass, metrics = self.scanner_1_volume_momentum_breakout_atr(df)

            if not scanner_1_pass:
                return False, metrics

            # Add VCP check
            vcp_pass, vcp_metrics = self._check_vcp_simplified(df)
            metrics['vcp_score'] = vcp_metrics.get('vcp_score', 0)

            if not vcp_pass:
                return False, metrics

            # Add ATR Trailing Stop check
            atr_stop_pass, atr_stop_metrics = self._check_atr_trailing_stop(df)
            metrics.update(atr_stop_metrics)

            if not atr_stop_pass:
                return False, metrics

            # All conditions passed
            metrics['scanner_id'] = 20
            metrics['scanner_name'] = 'Comprehensive: Volume + Momentum + Breakout + ATR + VCP + Trailing Stop'
            return True, metrics

        except Exception as e:
            logger.error(f"Error in scanner_20: {e}")
            return False, {"error": str(e)}

    # ==================== SCANNER #21 ====================
    def scanner_21_bullcross_ma_fair_value(self, df: pd.DataFrame, instrument_key: str = None) -> Tuple[bool, Dict]:
        """
        Scanner #21: BullCross-MA + Fair Value Buy Opportunities

        Criteria:
        1. Bullish MA crossover (price crosses above MA)
        2. Price near "fair value" (not extended from MA)
        3. Volume confirmation

        Returns:
            (passed: bool, metrics: dict)
        """
        try:
            if len(df) < 100:
                return False, {"error": "Insufficient data"}

            metrics = {}

            # 1. Check for bullish MA crossover
            bullcross_pass, bullcross_metrics = self._check_bullish_ma_cross(df)
            metrics.update(bullcross_metrics)

            if not bullcross_pass:
                return False, metrics

            # 2. Fair value check (price within 2.5% of MA)
            fair_value_pass, fv_metrics = self._check_fair_value(df)
            metrics.update(fv_metrics)

            if not fair_value_pass:
                return False, metrics

            # 3. Volume confirmation
            volume_ratio = self.ti.calculate_volume_ratio(df, period=20)
            volume_pass = volume_ratio >= 1.5  # Lower threshold for MA cross
            metrics['volume_ratio'] = volume_ratio

            if not volume_pass:
                return False, metrics

            # All conditions passed
            metrics['scanner_id'] = 21
            metrics['scanner_name'] = 'BullCross MA + Fair Value'
            return True, metrics

        except Exception as e:
            logger.error(f"Error in scanner_21: {e}")
            return False, {"error": str(e)}

    # ==================== HELPER METHODS ====================

    def _check_momentum(self, df: pd.DataFrame) -> bool:
        """
        Check for momentum: 3 consecutive green candles with increasing open, close, volume
        Extracted from PKScreener's validateMomentum
        """
        try:
            if len(df) < 3:
                return False

            data = df.head(3)

            # All 3 candles should be green (close > open)
            for i in range(3):
                if data['close'].iloc[i] <= data['open'].iloc[i]:
                    return False

            # Check if open, close, volume are in descending order (most recent highest)
            opens = list(data['open'])
            closes = list(data['close'])
            volumes = list(data['volume'])

            opens_desc = opens == sorted(opens, reverse=True)
            closes_desc = closes == sorted(closes, reverse=True)
            volumes_desc = volumes == sorted(volumes, reverse=True)

            return opens_desc and closes_desc and volumes_desc

        except Exception as e:
            logger.error(f"Error checking momentum: {e}")
            return False

    def _check_momentum_relaxed(self, df: pd.DataFrame, num_candles: int = 2) -> bool:
        """
        Relaxed momentum check for intraday: N consecutive green candles with increasing close
        More suitable for 1-minute data

        Args:
            df: DataFrame with OHLCV data
            num_candles: Number of consecutive green candles to check (default: 2)
        """
        try:
            if len(df) < num_candles:
                return False

            data = df.head(num_candles)

            # All candles should be green (close > open)
            for i in range(num_candles):
                if data['close'].iloc[i] <= data['open'].iloc[i]:
                    return False

            # Check if closes are in descending order (most recent highest)
            closes = list(data['close'])
            closes_desc = closes == sorted(closes, reverse=True)

            return closes_desc

        except Exception as e:
            logger.error(f"Error checking relaxed momentum: {e}")
            return False

    def _check_atr_cross(self, df: pd.DataFrame) -> Tuple[bool, Dict]:
        """
        Check ATR Cross condition
        Extracted from PKScreener's findATRCross

        Criteria:
        - Candle body height >= ATR(14)
        - RSI >= 55 (bullish)
        - Volume > SMA(7) of volume
        """
        try:
            metrics = {}

            # Calculate ATR
            atr = self.ti.ATR(df['high'], df['low'], df['close'], 14)
            atr_value = atr.iloc[0]
            metrics['atr'] = round(atr_value, 2)

            # Candle body height
            candle_height = self.ti.calculate_candle_body_height(df)
            metrics['candle_height'] = round(candle_height, 2)

            # Check if candle height >= ATR
            atr_cross = candle_height >= atr_value

            # RSI check
            rsi = self.ti.RSI(df['close'], 14).iloc[0]
            metrics['rsi'] = round(rsi, 2)
            bullish_rsi = rsi >= 55

            # Volume check
            volume_sma7 = self.ti.SMA(df['volume'], 7).iloc[0]
            current_volume = df['volume'].iloc[0]
            volume_above_avg = current_volume > volume_sma7

            passed = atr_cross and bullish_rsi and volume_above_avg
            metrics['atr_cross'] = passed

            return passed, metrics

        except Exception as e:
            logger.error(f"Error checking ATR cross: {e}")
            return False, {"error": str(e)}

    def _check_ma_alignment(self, df: pd.DataFrame) -> Tuple[bool, Dict]:
        """
        Check if moving averages are in bullish alignment
        EMA(13) > EMA(26) > SMA(50)
        """
        try:
            metrics = {}

            ema_13 = self.ti.EMA(df['close'], 13).iloc[0]
            ema_26 = self.ti.EMA(df['close'], 26).iloc[0]
            sma_50 = self.ti.SMA(df['close'], 50).iloc[0]

            metrics['ema_13'] = round(ema_13, 2)
            metrics['ema_26'] = round(ema_26, 2)
            metrics['sma_50'] = round(sma_50, 2)

            aligned = ema_13 > ema_26 > sma_50
            metrics['ma_aligned'] = aligned

            return aligned, metrics

        except Exception as e:
            logger.error(f"Error checking MA alignment: {e}")
            return False, {"error": str(e)}

    def _check_volatility_contraction(self, df: pd.DataFrame) -> Tuple[bool, Dict]:
        """
        Check if volatility is contracting (ATR decreasing over time)
        """
        try:
            metrics = {}

            # Calculate ATR for recent periods
            atr = self.ti.ATR(df['high'], df['low'], df['close'], 14)

            # Compare recent ATR to older ATR
            recent_atr = atr.iloc[0:10].mean()
            older_atr = atr.iloc[10:30].mean()

            metrics['recent_atr'] = round(recent_atr, 2)
            metrics['older_atr'] = round(older_atr, 2)

            # Volatility is contracting if recent ATR < older ATR
            contracting = recent_atr < older_atr
            metrics['volatility_contracting'] = contracting

            return contracting, metrics

        except Exception as e:
            logger.error(f"Error checking volatility contraction: {e}")
            return False, {"error": str(e)}

    def _check_vcp_volume_pattern(self, df: pd.DataFrame) -> Tuple[bool, Dict]:
        """
        Check VCP volume pattern: volume drying up then spiking
        """
        try:
            metrics = {}

            # Recent volume vs average
            recent_volume = df['volume'].iloc[0]
            avg_volume_20 = df['volume'].iloc[1:21].mean()
            avg_volume_50 = df['volume'].iloc[1:51].mean()

            # Volume should spike recently (above average)
            volume_spike = recent_volume > avg_volume_20 * 1.5

            # Volume should have dried up before (20-day avg < 50-day avg)
            volume_dried_up = avg_volume_20 < avg_volume_50

            metrics['recent_volume'] = int(recent_volume)
            metrics['avg_volume_20'] = int(avg_volume_20)
            metrics['volume_spike'] = volume_spike
            metrics['volume_dried_up'] = volume_dried_up

            passed = volume_spike and volume_dried_up

            return passed, metrics

        except Exception as e:
            logger.error(f"Error checking VCP volume pattern: {e}")
            return False, {"error": str(e)}

    def _check_vcp_simplified(self, df: pd.DataFrame) -> Tuple[bool, Dict]:
        """
        Simplified VCP check for intraday data
        """
        try:
            metrics = {}

            # MA alignment
            ma_pass, _ = self._check_ma_alignment(df)

            # Volatility contraction
            vol_pass, _ = self._check_volatility_contraction(df)

            # Volume pattern
            volume_pass, _ = self._check_vcp_volume_pattern(df)

            # VCP score (0-3)
            vcp_score = sum([ma_pass, vol_pass, volume_pass])
            metrics['vcp_score'] = vcp_score

            # Pass if at least 2 out of 3 conditions met
            passed = vcp_score >= 2

            return passed, metrics

        except Exception as e:
            logger.error(f"Error checking VCP: {e}")
            return False, {"error": str(e)}

    def _check_atr_trailing_stop(self, df: pd.DataFrame) -> Tuple[bool, Dict]:
        """
        Check ATR Trailing Stop signal
        """
        try:
            metrics = {}

            # Calculate ATR trailing stop
            df_with_stop = self.ti.ATR_trailing_stop(df, sensitivity=1.0, atr_period=10)

            # Check if current candle has buy signal
            buy_signal = df_with_stop['Buy'].iloc[0]
            atr_stop_value = df_with_stop['ATRTrailingStop'].iloc[0]

            metrics['atr_trailing_stop'] = round(atr_stop_value, 2)
            metrics['buy_signal'] = buy_signal

            return buy_signal, metrics

        except Exception as e:
            logger.error(f"Error checking ATR trailing stop: {e}")
            return False, {"error": str(e)}

    def _check_bullish_ma_cross(self, df: pd.DataFrame) -> Tuple[bool, Dict]:
        """
        Check for bullish MA crossover (price crosses above MA)
        """
        try:
            metrics = {}

            # Check multiple MAs
            ema_20 = self.ti.EMA(df['close'], 20)
            sma_50 = self.ti.SMA(df['close'], 50)

            # Current and previous candles
            current_close = df['close'].iloc[0]
            current_open = df['open'].iloc[0]
            prev_close = df['close'].iloc[1]

            # Check EMA 20 cross
            ema_20_current = ema_20.iloc[0]
            bullish_ema20_cross = (current_open < ema_20_current and current_close > ema_20_current)

            # Check SMA 50 cross
            sma_50_current = sma_50.iloc[0]
            bullish_sma50_cross = (current_open < sma_50_current and current_close > sma_50_current)

            # Either cross is valid
            bullcross = bullish_ema20_cross or bullish_sma50_cross

            metrics['ema_20'] = round(ema_20_current, 2)
            metrics['sma_50'] = round(sma_50_current, 2)
            metrics['bullish_cross'] = bullcross

            return bullcross, metrics

        except Exception as e:
            logger.error(f"Error checking bullish MA cross: {e}")
            return False, {"error": str(e)}

    def _check_fair_value(self, df: pd.DataFrame, deviation_pct: float = 2.5) -> Tuple[bool, Dict]:
        """
        Check if price is near fair value (within deviation % of MA)
        """
        try:
            metrics = {}

            current_close = df['close'].iloc[0]
            ema_20 = self.ti.EMA(df['close'], 20).iloc[0]

            # Calculate deviation from MA
            deviation = abs(current_close - ema_20) / ema_20 * 100

            # Price should be within deviation_pct of MA
            fair_value = deviation <= deviation_pct

            metrics['price_deviation_pct'] = round(deviation, 2)
            metrics['fair_value'] = fair_value

            return fair_value, metrics

        except Exception as e:
            logger.error(f"Error checking fair value: {e}")
            return False, {"error": str(e)}



    # ==================== PKSCREENER BREAKOUT SCANNERS ====================
    # Scanners based on PKScreener GitHub repository
    # https://github.com/pkjmesra/PKScreener

    def scanner_17_52week_high_breakout(self, df: pd.DataFrame, instrument_key: str = None) -> Tuple[bool, Dict]:
        """
        Scanner #17: 52-Week High Breakout (PKScreener Style)

        Criteria:
        1. Current high >= 52-week high (uses daily data from MongoDB)
        2. Volume >= 1.5x average (confirmation)

        Returns:
            (passed: bool, metrics: dict)
        """
        try:
            if len(df) < 20:
                return False, {"error": "Insufficient data"}

            metrics = {}

            # Get daily candles from MongoDB for 52-week calculation
            if self.daily_data_service and instrument_key:
                try:
                    # Try to import pymongo
                    try:
                        from pymongo import MongoClient
                    except ImportError:
                        logger.warning("pymongo not available. Scanner #17 (52-Week High) disabled.")
                        return False, {"error": "pymongo not installed"}

                    import os

                    mongo_uri = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
                    client = MongoClient(mongo_uri)
                    db = client['trading_data']

                    # Get last 250 trading days (52 weeks * 5 days)
                    daily_candles = list(db.daily_candles.find(
                        {'instrument_key': instrument_key},
                        {'_id': 0, 'high': 1}
                    ).sort('date', -1).limit(250))

                    client.close()

                    if len(daily_candles) >= 50:
                        # Get 52-week high (exclude most recent day)
                        week_52_high = max([c['high'] for c in daily_candles[1:]])
                        current_high = df['high'].iloc[0]

                        is_52week_breakout = current_high >= week_52_high

                        metrics['52week_high'] = round(week_52_high, 2)
                        metrics['current_high'] = round(current_high, 2)
                        metrics['is_52week_breakout'] = is_52week_breakout

                        if not is_52week_breakout:
                            return False, metrics
                    else:
                        return False, {"error": "Insufficient daily data"}

                except Exception as e:
                    logger.error(f"Error fetching daily data: {e}")
                    return False, {"error": str(e)}
            else:
                # Fallback: use intraday data (less accurate)
                lookback = min(250, len(df))
                week_52_high = df['high'].iloc[1:lookback].max()
                current_high = df['high'].iloc[0]

                is_52week_breakout = current_high >= week_52_high
                metrics['52week_high'] = round(week_52_high, 2)
                metrics['current_high'] = round(current_high, 2)
                metrics['is_52week_breakout'] = is_52week_breakout

                if not is_52week_breakout:
                    return False, metrics

            # Volume confirmation
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
            logger.error(f"Error in scanner_17: {e}")
            return False, {"error": str(e)}

    def scanner_20_bullish_for_tomorrow(self, df: pd.DataFrame, instrument_key: str = None) -> Tuple[bool, Dict]:
        """
        Scanner #20: Bullish for Next Day (PKScreener MACD-based)

        Criteria:
        1. MACD histogram V-shape recovery
        2. MACD-Signal difference increasing >= 0.2 (relaxed for intraday)
        3. MACD line > Signal line (bullish crossover)

        Returns:
            (passed: bool, metrics: dict)
        """
        try:
            if len(df) < 50:
                return False, {"error": "Insufficient data"}

            metrics = {}

            # Calculate MACD
            macd_line, signal_line, macd_hist = self.ti.MACD(df['close'], fast=12, slow=26, signal=9)

            # Get last 3 values
            hist_0 = macd_hist.iloc[0]
            hist_1 = macd_hist.iloc[1]
            hist_2 = macd_hist.iloc[2]

            macd_0 = macd_line.iloc[0]
            signal_0 = signal_line.iloc[0]
            macd_1 = macd_line.iloc[1]
            signal_1 = signal_line.iloc[1]

            # 1. V-shape recovery
            v_shape = (hist_2 < hist_1) and (hist_0 > hist_1)
            metrics['v_shape_recovery'] = v_shape

            if not v_shape:
                return False, metrics

            # 2. MACD-Signal difference increasing (relaxed to 0.2 for intraday)
            diff_increase = (macd_0 - signal_0) - (macd_1 - signal_1)
            strong_momentum = diff_increase >= 0.2
            metrics['macd_signal_diff_increase'] = round(diff_increase, 3)

            if not strong_momentum:
                return False, metrics

            # 3. MACD above signal
            bullish_crossover = macd_0 > signal_0
            metrics['bullish_crossover'] = bullish_crossover

            if not bullish_crossover:
                return False, metrics

            # All conditions passed
            metrics['scanner_id'] = 20
            metrics['scanner_name'] = 'Bullish for Tomorrow'
            metrics['macd'] = round(macd_0, 3)
            metrics['signal'] = round(signal_0, 3)
            return True, metrics

        except Exception as e:
            logger.error(f"Error in scanner_20: {e}")
            return False, {"error": str(e)}

    def scanner_23_breaking_out_now(self, df: pd.DataFrame, instrument_key: str = None) -> Tuple[bool, Dict]:
        """
        Scanner #23: Breaking Out Now (PKScreener Style)

        Criteria:
        1. Current candle body >= 3x average of last 10 candles
        2. Bollinger Bands expansion
        3. Green candle (bullish)

        Returns:
            (passed: bool, metrics: dict)
        """
        try:
            if len(df) < 30:
                return False, {"error": "Insufficient data"}

            metrics = {}

            # 1. Candle body height check
            current_candle_height = abs(df['close'].iloc[0] - df['open'].iloc[0])
            avg_candle_height = df.iloc[1:11].apply(
                lambda row: abs(row['close'] - row['open']), axis=1
            ).mean()

            height_ratio = current_candle_height / avg_candle_height if avg_candle_height > 0 else 0
            is_breakout_candle = height_ratio >= 3.0

            metrics['recent_candle_height'] = round(current_candle_height, 2)
            metrics['avg_candle_height'] = round(avg_candle_height, 2)
            metrics['height_ratio'] = round(height_ratio, 2)
            metrics['is_breakout_candle'] = is_breakout_candle

            if not is_breakout_candle:
                return False, metrics

            # 2. Bollinger Bands expansion check
            upper_band, middle_band, lower_band = self.ti.BBANDS(df['close'], timeperiod=20, std=2)

            bb_width_current = upper_band.iloc[0] - lower_band.iloc[0]
            bb_width_prev = upper_band.iloc[1] - lower_band.iloc[1]

            bb_expanding = bb_width_current > bb_width_prev
            metrics['bb_expanding'] = bb_expanding

            if not bb_expanding:
                return False, metrics

            # 3. Green candle check
            is_green = df['close'].iloc[0] > df['open'].iloc[0]
            metrics['is_green_candle'] = is_green

            if not is_green:
                return False, metrics

            # All conditions passed
            metrics['scanner_id'] = 23
            metrics['scanner_name'] = 'Breaking Out Now'
            return True, metrics

        except Exception as e:
            logger.error(f"Error in scanner_23: {e}")
            return False, {"error": str(e)}

    def scanner_32_intraday_breakout_setup(self, df: pd.DataFrame, instrument_key: str = None) -> Tuple[bool, Dict]:
        """
        Scanner #32: Intraday Breakout/Breakdown Setup (PKScreener Style)

        Criteria:
        1. Price breaking above/below opening range (first 15 minutes)
        2. Volume >= 2x daily average per minute
        3. RSI confirmation (> 55 for breakout, < 45 for breakdown) - relaxed for intraday

        Returns:
            (passed: bool, metrics: dict)
        """
        try:
            if len(df) < 30:
                return False, {"error": "Insufficient data"}

            metrics = {}

            # 1. Opening range breakout (first 15 candles = 15 minutes)
            opening_range_candles = min(15, len(df) - 1)
            opening_high = df['high'].iloc[-opening_range_candles:].max()
            opening_low = df['low'].iloc[-opening_range_candles:].min()

            current_close = df['close'].iloc[0]

            breakout_type = None
            if current_close > opening_high:
                breakout_type = 'bullish'
            elif current_close < opening_low:
                breakout_type = 'bearish'

            metrics['opening_high'] = round(opening_high, 2)
            metrics['opening_low'] = round(opening_low, 2)
            metrics['current_close'] = round(current_close, 2)
            metrics['breakout_type'] = breakout_type

            if not breakout_type:
                return False, metrics

            # 2. Volume surge check (2x for strong breakouts)
            if self.daily_data_service and instrument_key:
                daily_avg_volume = self.daily_data_service.get_daily_volume_avg(instrument_key, days=20)
                daily_volume_per_minute = daily_avg_volume / 375.0 if daily_avg_volume > 0 else 0

                recent_volume = df['volume'].iloc[0]
                volume_ratio = recent_volume / daily_volume_per_minute if daily_volume_per_minute > 0 else 0
            else:
                # Fallback to intraday average
                recent_volume = df['volume'].iloc[0]
                avg_volume = df['volume'].iloc[1:21].mean()
                volume_ratio = recent_volume / avg_volume if avg_volume > 0 else 0

            volume_surge = volume_ratio >= 2.0
            metrics['volume_ratio'] = round(volume_ratio, 2)
            metrics['volume_surge'] = volume_surge

            if not volume_surge:
                return False, metrics

            # 3. RSI confirmation (relaxed to 55/45 for intraday)
            rsi = self.ti.RSI(df['close'], timeperiod=14).iloc[0]

            rsi_confirmed = False
            if breakout_type == 'bullish' and rsi > 55:
                rsi_confirmed = True
            elif breakout_type == 'bearish' and rsi < 45:
                rsi_confirmed = True

            metrics['rsi'] = round(rsi, 2)
            metrics['rsi_confirmed'] = rsi_confirmed

            if not rsi_confirmed:
                return False, metrics

            # All conditions passed
            metrics['scanner_id'] = 32
            metrics['scanner_name'] = 'Intraday Breakout Setup'
            return True, metrics

        except Exception as e:
            logger.error(f"Error in scanner_32: {e}")
            return False, {"error": str(e)}

