"""
Technical Indicators Module
Extracted and adapted from PKScreener's Pktalib.py
Uses pandas_ta (ta library) which is already in requirements.txt
"""
import numpy as np
import pandas as pd
import ta
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class TechnicalIndicators:
    """Calculate technical indicators for scanner strategies"""
    
    @staticmethod
    def ATR(high: pd.Series, low: pd.Series, close: pd.Series, timeperiod: int = 14) -> pd.Series:
        """Calculate Average True Range"""
        try:
            return ta.volatility.average_true_range(high, low, close, window=timeperiod)
        except Exception as e:
            logger.error(f"Error calculating ATR: {e}")
            return pd.Series([np.nan] * len(close))
    
    @staticmethod
    def RSI(close: pd.Series, timeperiod: int = 14) -> pd.Series:
        """Calculate Relative Strength Index"""
        try:
            return ta.momentum.rsi(close, window=timeperiod)
        except Exception as e:
            logger.error(f"Error calculating RSI: {e}")
            return pd.Series([np.nan] * len(close))
    
    @staticmethod
    def EMA(close: pd.Series, timeperiod: int) -> pd.Series:
        """Calculate Exponential Moving Average"""
        try:
            return ta.trend.ema_indicator(close, window=timeperiod)
        except Exception as e:
            logger.error(f"Error calculating EMA: {e}")
            return pd.Series([np.nan] * len(close))
    
    @staticmethod
    def SMA(close: pd.Series, timeperiod: int) -> pd.Series:
        """Calculate Simple Moving Average"""
        try:
            return ta.trend.sma_indicator(close, window=timeperiod)
        except Exception as e:
            logger.error(f"Error calculating SMA: {e}")
            return pd.Series([np.nan] * len(close))
    
    @staticmethod
    def MACD(close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """Calculate MACD (Moving Average Convergence Divergence)"""
        try:
            macd_line = ta.trend.macd(close, window_slow=slow, window_fast=fast)
            signal_line = ta.trend.macd_signal(close, window_slow=slow, window_fast=fast, window_sign=signal)
            histogram = ta.trend.macd_diff(close, window_slow=slow, window_fast=fast, window_sign=signal)
            return macd_line, signal_line, histogram
        except Exception as e:
            logger.error(f"Error calculating MACD: {e}")
            return pd.Series([np.nan] * len(close)), pd.Series([np.nan] * len(close)), pd.Series([np.nan] * len(close))
    
    @staticmethod
    def MFI(high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series, timeperiod: int = 14) -> pd.Series:
        """Calculate Money Flow Index"""
        try:
            return ta.volume.money_flow_index(high, low, close, volume, window=timeperiod)
        except Exception as e:
            logger.error(f"Error calculating MFI: {e}")
            return pd.Series([np.nan] * len(close))
    
    @staticmethod
    def CCI(high: pd.Series, low: pd.Series, close: pd.Series, timeperiod: int = 20) -> pd.Series:
        """Calculate Commodity Channel Index"""
        try:
            return ta.trend.cci(high, low, close, window=timeperiod)
        except Exception as e:
            logger.error(f"Error calculating CCI: {e}")
            return pd.Series([np.nan] * len(close))
    
    @staticmethod
    def BBANDS(close: pd.Series, timeperiod: int = 20, std: int = 2) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """Calculate Bollinger Bands"""
        try:
            bb = ta.volatility.BollingerBands(close, window=timeperiod, window_dev=std)
            upper = bb.bollinger_hband()
            middle = bb.bollinger_mavg()
            lower = bb.bollinger_lband()
            return upper, middle, lower
        except Exception as e:
            logger.error(f"Error calculating Bollinger Bands: {e}")
            return pd.Series([np.nan] * len(close)), pd.Series([np.nan] * len(close)), pd.Series([np.nan] * len(close))
    
    @staticmethod
    def SuperTrend(df: pd.DataFrame, length: int = 7, multiplier: float = 3.0) -> pd.DataFrame:
        """
        Calculate SuperTrend indicator
        Returns DataFrame with columns: supertrend, direction
        """
        try:
            high = df['high']
            low = df['low']
            close = df['close']
            
            # Calculate ATR
            atr = TechnicalIndicators.ATR(high, low, close, length)
            
            # Calculate basic upper and lower bands
            hl_avg = (high + low) / 2
            upper_band = hl_avg + (multiplier * atr)
            lower_band = hl_avg - (multiplier * atr)
            
            # Initialize supertrend
            supertrend = pd.Series(index=df.index, dtype=float)
            direction = pd.Series(index=df.index, dtype=int)
            
            # First value
            supertrend.iloc[0] = lower_band.iloc[0]
            direction.iloc[0] = 1
            
            for i in range(1, len(df)):
                # Update bands
                if close.iloc[i] > supertrend.iloc[i-1]:
                    supertrend.iloc[i] = lower_band.iloc[i]
                    direction.iloc[i] = 1
                elif close.iloc[i] < supertrend.iloc[i-1]:
                    supertrend.iloc[i] = upper_band.iloc[i]
                    direction.iloc[i] = -1
                else:
                    supertrend.iloc[i] = supertrend.iloc[i-1]
                    direction.iloc[i] = direction.iloc[i-1]
            
            result = pd.DataFrame({
                'supertrend': supertrend,
                'direction': direction
            })
            return result
        except Exception as e:
            logger.error(f"Error calculating SuperTrend: {e}")
            return pd.DataFrame({'supertrend': [np.nan] * len(df), 'direction': [0] * len(df)})
    
    @staticmethod
    def calculate_volume_ratio(df: pd.DataFrame, period: int = 20) -> float:
        """
        Calculate volume ratio: current volume / average volume
        """
        try:
            if len(df) < period:
                return 0.0
            
            current_volume = df['volume'].iloc[0]
            avg_volume = df['volume'].head(period).mean()
            
            if avg_volume == 0:
                return 0.0
            
            return round(current_volume / avg_volume, 2)
        except Exception as e:
            logger.error(f"Error calculating volume ratio: {e}")
            return 0.0
    
    @staticmethod
    def calculate_momentum_score(df: pd.DataFrame) -> float:
        """
        Calculate momentum score based on RSI, MFI, and CCI
        Returns score from 0-100
        """
        try:
            if len(df) < 20:
                return 0.0
            
            # Calculate indicators
            rsi = TechnicalIndicators.RSI(df['close'], 14).iloc[0]
            mfi = TechnicalIndicators.MFI(df['high'], df['low'], df['close'], df['volume'], 14).iloc[0]
            cci = TechnicalIndicators.CCI(df['high'], df['low'], df['close'], 20).iloc[0]
            
            # Normalize CCI to 0-100 range (CCI typically ranges from -200 to +200)
            cci_normalized = min(100, max(0, (cci + 200) / 4))
            
            # Average of all three indicators
            momentum_score = (rsi + mfi + cci_normalized) / 3
            
            return round(momentum_score, 2)
        except Exception as e:
            logger.error(f"Error calculating momentum score: {e}")
            return 0.0
    
    @staticmethod
    def ATR_trailing_stop(df: pd.DataFrame, sensitivity: float = 1.0, atr_period: int = 10) -> pd.DataFrame:
        """
        Calculate ATR Trailing Stop
        Adapted from PKScreener's findATRTrailingStops method
        """
        try:
            data = df.copy()
            data = data[::-1]  # Reverse to oldest first
            
            # Calculate ATR and nLoss
            data['xATR'] = TechnicalIndicators.ATR(data['high'], data['low'], data['close'], atr_period)
            data['nLoss'] = sensitivity * data['xATR']
            
            # Drop NaN rows
            data = data.dropna()
            data = data.reset_index(drop=True)
            
            # Initialize ATRTrailingStop
            data['ATRTrailingStop'] = [0.0] + [np.nan for _ in range(len(data) - 1)]
            
            # Calculate trailing stop
            for i in range(1, len(data)):
                close_curr = data.loc[i, 'close']
                close_prev = data.loc[i - 1, 'close']
                atr_prev = data.loc[i - 1, 'ATRTrailingStop']
                nloss = data.loc[i, 'nLoss']
                
                if close_curr > atr_prev and close_prev > atr_prev:
                    data.loc[i, 'ATRTrailingStop'] = max(atr_prev, close_curr - nloss)
                elif close_curr < atr_prev and close_prev < atr_prev:
                    data.loc[i, 'ATRTrailingStop'] = min(atr_prev, close_curr + nloss)
                elif close_curr > atr_prev:
                    data.loc[i, 'ATRTrailingStop'] = close_curr - nloss
                else:
                    data.loc[i, 'ATRTrailingStop'] = close_curr + nloss
            
            # Calculate Buy/Sell signals
            data['Buy'] = (data['close'] > data['ATRTrailingStop'])
            data['Sell'] = (data['close'] < data['ATRTrailingStop'])
            
            # Reverse back to most recent first
            data = data[::-1].reset_index(drop=True)
            
            return data
        except Exception as e:
            logger.error(f"Error calculating ATR trailing stop: {e}")
            return df
    
    @staticmethod
    def is_breaking_out(df: pd.DataFrame, lookback_period: int = 20) -> bool:
        """
        Check if stock is breaking out (current close > highest high in lookback period)
        """
        try:
            if len(df) < lookback_period + 1:
                return False
            
            current_close = df['close'].iloc[0]
            previous_high = df['high'].iloc[1:lookback_period+1].max()
            
            return current_close > previous_high
        except Exception as e:
            logger.error(f"Error checking breakout: {e}")
            return False
    
    @staticmethod
    def calculate_candle_body_height(df: pd.DataFrame) -> float:
        """Calculate the height of the candle body (abs(close - open))"""
        try:
            recent = df.head(1)
            return abs(recent['close'].iloc[0] - recent['open'].iloc[0])
        except Exception as e:
            logger.error(f"Error calculating candle body height: {e}")
            return 0.0

    @staticmethod
    def calculate_intraday_volume_ratio(current_volume: float, instrument_key: str, daily_data_service) -> float:
        """
        Calculate volume ratio comparing current intraday volume to daily average per minute

        Args:
            current_volume: Current minute's volume
            instrument_key: Instrument key (e.g., 'DHAN_3506')
            daily_data_service: DailyDataService instance

        Returns:
            Volume ratio (current_volume / daily_avg_per_minute)
        """
        try:
            if daily_data_service is None:
                logger.warning("DailyDataService not provided, falling back to 0")
                return 0.0

            # Get daily average volume per minute
            daily_avg_per_minute = daily_data_service.get_daily_volume_per_minute(instrument_key, days=20)

            if daily_avg_per_minute > 0:
                ratio = current_volume / daily_avg_per_minute
                return ratio
            else:
                return 0.0

        except Exception as e:
            logger.error(f"Error calculating intraday volume ratio: {e}")
            return 0.0

