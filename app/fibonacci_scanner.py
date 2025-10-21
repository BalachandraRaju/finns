"""
Fibonacci Pattern Scanner Module

Identifies stocks with bullish/bearish patterns in specific Fibonacci retracement zones:
- Bullish patterns in 50-61% retracement (golden zone for buying dips)
- Bearish patterns in 23-38% retracement (early warning zone for selling rallies)
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from logzero import logger
from datetime import datetime
import app.crud as crud
from app.charts import get_intraday_candles_with_fallback, _calculate_pnf_points
from app.pattern_detector import PatternDetector, PatternType, AlertType


@dataclass
class FibonacciSignal:
    """Represents a Fibonacci pattern signal."""
    symbol: str
    instrument_key: str
    pattern_type: str
    pattern_name: str
    alert_type: str  # BUY or SELL
    current_price: float
    fibonacci_level: float  # Percentage (e.g., 50.0, 61.8)
    fibonacci_price: float  # Actual price at Fibonacci level
    swing_low: float
    swing_high: float
    entry_price: float
    stop_loss: float
    target_price: float
    risk_reward_ratio: float
    trigger_reason: str
    timestamp: datetime


class FibonacciScanner:
    """Scanner for identifying pattern + Fibonacci retracement opportunities."""
    
    # Bullish patterns
    BULLISH_PATTERNS = {
        PatternType.ABC_BULLISH,
        PatternType.DOUBLE_BOTTOM,
        PatternType.TRIPLE_BOTTOM_SELL,  # Triple bottom = bullish
        PatternType.QUADRUPLE_BOTTOM_SELL,  # Quadruple bottom = bullish
        PatternType.CATAPULT_BUY,
        PatternType.POLE_FT_BUY,
        PatternType.TURTLE_BREAKOUT_BUY,
        PatternType.ZIDDI_BULLS,
        PatternType.TWEEZER_BULLISH,
    }
    
    # Bearish patterns
    BEARISH_PATTERNS = {
        PatternType.ABC_BEARISH,
        PatternType.DOUBLE_TOP,
        PatternType.TRIPLE_TOP_BUY,  # Triple top = bearish
        PatternType.QUADRUPLE_TOP_BUY,  # Quadruple top = bearish
        PatternType.CATAPULT_SELL,
        PatternType.POLE_FT_SELL,
        PatternType.TURTLE_BREAKOUT_SELL,
        PatternType.ZIDDI_BEARS,
        PatternType.TWEEZER_BEARISH,
    }
    
    def __init__(self):
        self.detector = PatternDetector()
    
    def _calculate_fibonacci_levels(self, highs: List[float], lows: List[float]) -> Optional[Dict]:
        """Calculate Fibonacci retracement levels from swing low to swing high."""
        if not highs or not lows:
            return None
        
        swing_low = min(lows)
        swing_high = max(highs)
        price_range = swing_high - swing_low
        
        if price_range == 0:
            return None
        
        # Fibonacci retracement levels (from swing high down to swing low)
        fib_levels = {
            0.0: swing_high,      # 0% retracement (swing high)
            23.6: swing_high - (price_range * 0.236),
            38.2: swing_high - (price_range * 0.382),
            50.0: swing_high - (price_range * 0.500),
            61.8: swing_high - (price_range * 0.618),
            78.6: swing_high - (price_range * 0.786),
            100.0: swing_low,     # 100% retracement (swing low)
        }
        
        return {
            'levels': fib_levels,
            'swing_low': swing_low,
            'swing_high': swing_high,
            'range': price_range
        }
    
    def _get_fibonacci_level_for_price(self, price: float, fib_data: Dict) -> Optional[Tuple[float, float]]:
        """
        Determine which Fibonacci level the price is at.
        
        Returns:
            Tuple of (fibonacci_percentage, fibonacci_price) or None
        """
        if not fib_data:
            return None
        
        levels = fib_data['levels']
        
        # Check each Fibonacci level with 2% tolerance
        for fib_pct, fib_price in levels.items():
            tolerance = fib_price * 0.02  # 2% tolerance
            if abs(price - fib_price) <= tolerance:
                return (fib_pct, fib_price)
        
        return None
    
    def _is_in_bullish_zone(self, price: float, fib_data: Dict) -> Optional[Tuple[float, float]]:
        """
        Check if price is in bullish Fibonacci zone (50-61.8% retracement).
        
        Returns:
            Tuple of (fibonacci_percentage, fibonacci_price) or None
        """
        if not fib_data:
            return None
        
        levels = fib_data['levels']
        fib_50 = levels[50.0]
        fib_61_8 = levels[61.8]
        
        # Price should be between 50% and 61.8% (golden zone)
        if fib_61_8 <= price <= fib_50:
            # Determine which level is closer
            dist_50 = abs(price - fib_50)
            dist_61_8 = abs(price - fib_61_8)
            
            if dist_50 < dist_61_8:
                return (50.0, fib_50)
            else:
                return (61.8, fib_61_8)
        
        return None
    
    def _is_in_bearish_zone(self, price: float, fib_data: Dict) -> Optional[Tuple[float, float]]:
        """
        Check if price is in bearish Fibonacci zone (23.6-38.2% retracement).
        
        Returns:
            Tuple of (fibonacci_percentage, fibonacci_price) or None
        """
        if not fib_data:
            return None
        
        levels = fib_data['levels']
        fib_23_6 = levels[23.6]
        fib_38_2 = levels[38.2]
        
        # Price should be between 23.6% and 38.2% (early warning zone)
        if fib_38_2 <= price <= fib_23_6:
            # Determine which level is closer
            dist_23_6 = abs(price - fib_23_6)
            dist_38_2 = abs(price - fib_38_2)
            
            if dist_23_6 < dist_38_2:
                return (23.6, fib_23_6)
            else:
                return (38.2, fib_38_2)
        
        return None
    
    def _calculate_risk_reward(self, entry: float, stop_loss: float, target: float) -> float:
        """Calculate risk-reward ratio."""
        risk = abs(entry - stop_loss)
        reward = abs(target - entry)
        
        if risk == 0:
            return 0.0
        
        return round(reward / risk, 2)
    
    def scan_stock(self, instrument_key: str, symbol: str, 
                   scan_type: str = "bullish") -> Optional[FibonacciSignal]:
        """
        Scan a single stock for Fibonacci pattern opportunities.
        
        Args:
            instrument_key: Stock instrument key
            symbol: Stock symbol
            scan_type: "bullish" or "bearish"
        
        Returns:
            FibonacciSignal if opportunity found, None otherwise
        """
        try:
            # Get intraday candles (1-minute)
            candles = get_intraday_candles_with_fallback(instrument_key, "1minute")
            
            if not candles or len(candles) < 50:
                return None
            
            # Extract price data
            highs = [float(c['high']) for c in candles]
            lows = [float(c['low']) for c in candles]
            closes = [float(c['close']) for c in candles]
            current_price = closes[-1]
            
            # Calculate Fibonacci levels
            fib_data = self._calculate_fibonacci_levels(highs, lows)
            if not fib_data:
                return None
            
            # Calculate P&F points
            box_percentage = 0.0025  # 0.25%
            reversal = 3
            x_coords, y_coords, pnf_symbols = _calculate_pnf_points(highs, lows, box_percentage, reversal)
            
            if not x_coords:
                return None
            
            # Detect patterns
            alert_triggers = self.detector.analyze_pattern_formation(
                x_coords, y_coords, pnf_symbols, closes, box_percentage
            )
            
            if not alert_triggers:
                return None
            
            # Check for bullish or bearish patterns in appropriate Fibonacci zones
            for alert in alert_triggers:
                if scan_type == "bullish":
                    # Check if bullish pattern in 50-61% zone
                    if alert.pattern_type in self.BULLISH_PATTERNS:
                        fib_zone = self._is_in_bullish_zone(current_price, fib_data)
                        if fib_zone:
                            fib_pct, fib_price = fib_zone
                            
                            # Calculate entry, stop loss, and target
                            entry_price = current_price
                            stop_loss = fib_data['levels'][61.8] * 0.98  # 2% below 61.8%
                            target_price = fib_data['swing_high'] * 1.02  # 2% above swing high
                            
                            risk_reward = self._calculate_risk_reward(entry_price, stop_loss, target_price)
                            
                            return FibonacciSignal(
                                symbol=symbol,
                                instrument_key=instrument_key,
                                pattern_type=alert.pattern_type.value,
                                pattern_name=alert.pattern_name,
                                alert_type="BUY",
                                current_price=current_price,
                                fibonacci_level=fib_pct,
                                fibonacci_price=fib_price,
                                swing_low=fib_data['swing_low'],
                                swing_high=fib_data['swing_high'],
                                entry_price=entry_price,
                                stop_loss=stop_loss,
                                target_price=target_price,
                                risk_reward_ratio=risk_reward,
                                trigger_reason=f"{alert.pattern_name} in {fib_pct}% Fibonacci golden zone",
                                timestamp=datetime.utcnow()
                            )
                
                elif scan_type == "bearish":
                    # Check if bearish pattern in 23-38% zone
                    if alert.pattern_type in self.BEARISH_PATTERNS:
                        fib_zone = self._is_in_bearish_zone(current_price, fib_data)
                        if fib_zone:
                            fib_pct, fib_price = fib_zone
                            
                            # Calculate entry, stop loss, and target
                            entry_price = current_price
                            stop_loss = fib_data['levels'][23.6] * 1.02  # 2% above 23.6%
                            target_price = fib_data['swing_low'] * 0.98  # 2% below swing low
                            
                            risk_reward = self._calculate_risk_reward(entry_price, stop_loss, target_price)
                            
                            return FibonacciSignal(
                                symbol=symbol,
                                instrument_key=instrument_key,
                                pattern_type=alert.pattern_type.value,
                                pattern_name=alert.pattern_name,
                                alert_type="SELL",
                                current_price=current_price,
                                fibonacci_level=fib_pct,
                                fibonacci_price=fib_price,
                                swing_low=fib_data['swing_low'],
                                swing_high=fib_data['swing_high'],
                                entry_price=entry_price,
                                stop_loss=stop_loss,
                                target_price=target_price,
                                risk_reward_ratio=risk_reward,
                                trigger_reason=f"{alert.pattern_name} in {fib_pct}% Fibonacci warning zone",
                                timestamp=datetime.utcnow()
                            )
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Error scanning {symbol}: {e}")
            return None
    
    def scan_watchlist(self, scan_type: str = "bullish") -> List[FibonacciSignal]:
        """
        Scan all watchlist stocks for Fibonacci pattern opportunities.
        
        Args:
            scan_type: "bullish" or "bearish"
        
        Returns:
            List of FibonacciSignal objects sorted by risk-reward ratio
        """
        signals = []
        watchlist = crud.get_watchlist_details()
        
        logger.info(f"🔍 Scanning {len(watchlist)} stocks for {scan_type} Fibonacci patterns...")
        
        for stock in watchlist:
            signal = self.scan_stock(stock.instrument_key, stock.symbol, scan_type)
            if signal:
                signals.append(signal)
                logger.info(f"✅ Found {scan_type} signal: {stock.symbol} @ ₹{signal.current_price:.2f} ({signal.fibonacci_level}% Fib)")
        
        # Sort by risk-reward ratio (highest first)
        signals.sort(key=lambda x: x.risk_reward_ratio, reverse=True)
        
        logger.info(f"📊 Found {len(signals)} {scan_type} Fibonacci signals")
        return signals

