"""
PnF Matrix calculation module.

Calculates matrix scores based on different box size percentages and timeframes.
Scoring system:
- X column: +1 point
- Double Top Buy: +2 points
- O column: -1 point  
- Double Bottom Sell: -2 points

Matrix range: -8 (all bearish) to +8 (all bullish)
Super Alert thresholds: ≥6 for bullish, ≤-6 for bearish
"""

from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from logzero import logger
from app.charts import _calculate_pnf_points
from app.pattern_detector import PatternDetector, PatternType, AlertType
import app.crud as crud
from datetime import datetime, date, timedelta

@dataclass
class MatrixScore:
    """Individual matrix score for a specific box size."""
    box_size: float
    column_type: str  # 'X', 'O', 'DTB', 'DBB'
    score: int
    latest_price: float
    pattern_alerts: List[str]

@dataclass
class PnFMatrixResult:
    """Complete PnF Matrix result for a stock."""
    symbol: str
    instrument_key: str
    timeframe: str
    total_score: int
    matrix_scores: List[MatrixScore]
    matrix_strength: str  # 'SUPER BULLISH', 'BULLISH', 'NEUTRAL', 'BEARISH', 'SUPER BEARISH'
    super_alert_eligible: bool
    calculation_time: str

class PnFMatrixCalculator:
    """Calculate PnF Matrix scores for stocks."""

    def __init__(self):
        self.default_box_sizes = [0.0025, 0.005, 0.01, 0.015]  # 0.25%, 0.5%, 1%, 1.5% (PRIMARY: 0.25%)
        self.reversal = 3  # Standard 3-box reversal
        
    def calculate_matrix_for_stock(self, instrument_key: str, 
                                 timeframe: str = "day",
                                 box_sizes: List[float] = None) -> Optional[PnFMatrixResult]:
        """
        Calculate PnF Matrix for a single stock.
        
        Args:
            instrument_key: Stock instrument key
            timeframe: Data timeframe ('day', '1minute', etc.)
            box_sizes: List of box size percentages (default: [1%, 0.5%, 0.25%, 0.15%])
            
        Returns:
            PnFMatrixResult or None if calculation fails
        """
        if box_sizes is None:
            box_sizes = self.default_box_sizes
            
        # Get stock info
        stock_info = crud.get_stock_by_instrument_key(instrument_key)
        if not stock_info:
            return None
            
        symbol = stock_info['symbol']
        
        # Get price data using database-first approach
        try:
            # Use database service for smart data retrieval
            import sys
            import os
            sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data-fetch'))
            from database_service import database_service

            if timeframe == "day":
                # Get 2 months of daily data
                candles = database_service.get_historical_candles_smart(
                    instrument_key=instrument_key,
                    interval=timeframe,
                    months_back=2
                )
            else:
                # For intraday, get recent data with context
                candles = database_service.get_intraday_candles_smart(
                    instrument_key=instrument_key,
                    interval=timeframe
                )

            if not candles or len(candles) < 10:
                logger.warning(f"Insufficient data for {symbol}: {len(candles) if candles else 0} candles")
                return None

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

            candles = legacy_candles
            logger.info(f"✅ PnF Matrix: Retrieved {len(candles)} {timeframe} candles for {symbol}")

        except Exception as e:
            logger.error(f"❌ Error fetching data for {symbol} using database service: {e}")

            # Fallback to original method
            try:
                if timeframe == "day":
                    end_date = date.today()
                    start_date = end_date - timedelta(days=60)  # 2 months of daily data
                    from app.charts import get_candles
                    candles = get_candles(instrument_key, timeframe, start_date, end_date)
                else:
                    # For intraday, get recent data
                    from app.charts import get_intraday_candles_with_fallback
                    candles = get_intraday_candles_with_fallback(instrument_key, timeframe)

                if not candles or len(candles) < 10:
                    return None

            except Exception as fallback_error:
                logger.error(f"❌ Fallback also failed for {symbol}: {fallback_error}")
                return None
        
        # Calculate matrix scores for each box size
        matrix_scores = []
        total_score = 0
        
        for box_size in box_sizes:
            score_result = self._calculate_score_for_box_size(candles, box_size)
            if score_result:
                matrix_scores.append(score_result)
                total_score += score_result.score
        
        if not matrix_scores:
            return None
            
        # Determine matrix strength
        matrix_strength = self._get_matrix_strength(total_score)
        super_alert_eligible = abs(total_score) >= 6
        
        return PnFMatrixResult(
            symbol=symbol,
            instrument_key=instrument_key,
            timeframe=timeframe,
            total_score=total_score,
            matrix_scores=matrix_scores,
            matrix_strength=matrix_strength,
            super_alert_eligible=super_alert_eligible,
            calculation_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
    
    def _calculate_score_for_box_size(self, candles: List[Dict], box_size: float) -> Optional[MatrixScore]:
        """Calculate score for a specific box size."""
        try:
            # Extract price data
            highs = [float(c['high']) for c in candles]
            lows = [float(c['low']) for c in candles]
            closes = [float(c['close']) for c in candles]
            
            # Calculate P&F points
            x_coords, y_coords, symbols = _calculate_pnf_points(highs, lows, box_size, self.reversal)
            
            if not x_coords:
                return None
                
            # Get latest column info
            latest_column = max(x_coords)
            latest_indices = [i for i, col in enumerate(x_coords) if col == latest_column]
            latest_symbol = symbols[latest_indices[0]] if latest_indices else 'X'
            latest_price = y_coords[latest_indices[-1]] if latest_indices else closes[-1]
            
            # Detect patterns using pattern detector
            detector = PatternDetector()
            alerts = detector.analyze_pattern_formation(x_coords, y_coords, symbols, closes)

            # Determine column type and score
            column_type, score = self._get_column_score(latest_symbol, alerts)

            # Get pattern alert descriptions
            pattern_alerts = [alert.pattern_type.value for alert in alerts]
            
            return MatrixScore(
                box_size=box_size,
                column_type=column_type,
                score=score,
                latest_price=latest_price,
                pattern_alerts=pattern_alerts
            )
            
        except Exception as e:
            print(f"Error calculating score for box size {box_size}: {e}")
            return None
    
    def _get_column_score(self, latest_symbol: str, alerts: List) -> Tuple[str, int]:
        """
        Determine column type and score based on latest symbol and alerts.

        Scoring:
        - X column: +1 point
        - Double Top Buy: +2 points
        - O column: -1 point
        - Double Bottom Sell: -2 points
        """
        # Check for specific pattern alerts first
        for alert in alerts:
            if alert.alert_type == AlertType.BUY:
                # Check for any bullish breakout patterns (all should get +2 points)
                pattern_name = alert.pattern_type.value.lower()
                if any(keyword in pattern_name for keyword in [
                    'double_top', 'triple_top', 'quadruple_top',
                    'turtle_breakout', 'catapult', 'pole_follow_through',
                    'low_pole_ft', 'aft_anchor', 'tweezer_bullish',
                    'abc_bullish'  # ABC bullish is a strong momentum pattern
                ]):
                    return 'DTB', 2
            elif alert.alert_type == AlertType.SELL:
                # Check for any bearish breakdown patterns (all should get -2 points)
                pattern_name = alert.pattern_type.value.lower()
                if any(keyword in pattern_name for keyword in [
                    'double_bottom', 'triple_bottom', 'quadruple_bottom',
                    'turtle_breakout', 'catapult', 'pole_follow_through',
                    'high_pole_ft', 'aft_anchor', 'tweezer_bearish',
                    'abc_bearish'  # ABC bearish is a strong momentum pattern
                ]):
                    return 'DBB', -2

        # If no specific pattern, use column type
        if latest_symbol == 'X':
            return 'X', 1
        else:  # 'O'
            return 'O', -1
    
    def _get_matrix_strength(self, total_score: int) -> str:
        """Determine matrix strength based on total score."""
        if total_score >= 8:
            return 'SUPER BULLISH'
        elif total_score >= 6:
            return 'BULLISH'
        elif total_score >= 2:
            return 'NEUTRAL BULLISH'
        elif total_score >= -1:
            return 'NEUTRAL'
        elif total_score >= -5:
            return 'NEUTRAL BEARISH'
        elif total_score >= -6:
            return 'BEARISH'
        else:
            return 'SUPER BEARISH'
    
    def calculate_matrix_for_watchlist(self, timeframe: str = "day", 
                                     box_sizes: List[float] = None) -> List[PnFMatrixResult]:
        """Calculate PnF Matrix for all stocks in watchlist."""
        results = []
        
        # Get all stocks from watchlist
        stocks = crud.get_all_stocks()
        
        for stock in stocks:
            try:
                result = self.calculate_matrix_for_stock(
                    stock['instrument_key'], 
                    timeframe, 
                    box_sizes
                )
                if result:
                    results.append(result)
            except Exception as e:
                print(f"Error calculating matrix for {stock.get('symbol', 'Unknown')}: {e}")
                continue
        
        # Sort by total score (highest first)
        results.sort(key=lambda x: x.total_score, reverse=True)
        
        return results
