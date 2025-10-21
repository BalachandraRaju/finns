"""
Test patterns module for Point & Figure chart pattern validation.
Contains dummy data with known patterns for testing chart pattern recognition.
"""

import datetime
from typing import List, Dict, Any, Callable

def calculate_move_size(box_pct: float, reversal: int, base_price: float = 100.0) -> tuple:
    """
    Calculate appropriate price move sizes for a given box size.

    Args:
        box_pct: Box size as percentage (e.g., 0.01 for 1%)
        reversal: Number of boxes needed for reversal (typically 3)
        base_price: Base price to calculate from (default: 100)

    Returns:
        tuple: (single_box_move, reversal_move, column_move)
            - single_box_move: Price change for one box
            - reversal_move: Price change needed to trigger reversal
            - column_move: Typical price change for building a column (5-10 boxes)
    """
    single_box = base_price * box_pct
    reversal_move = single_box * reversal
    column_move = single_box * 8  # Typical column has 8 boxes

    return single_box, reversal_move, column_move

def generate_bullish_breakout_pattern() -> List[Dict[str, Any]]:
    """
    Generate dummy data for a double top buy with follow through pattern.
    Designed for 0.25% box size and 3-box reversal.
    """
    base_price = 100.0
    candles = []

    # Create a double top pattern followed by breakout with follow-through
    # Pattern: X-O-X-O-X (double top buy)
    prices = [
        # Column 1: X rises to 105 (first top)
        (100.0, 102.0, 100.0, 102.0),  # Day 1
        (102.0, 104.0, 102.0, 104.0),  # Day 2
        (104.0, 105.0, 104.0, 105.0),  # Day 3: First top at 105

        # Column 2: O falls to 102.5 (reversal)
        (105.0, 105.0, 103.2, 103.2),  # Day 4: Fall triggers reversal
        (103.2, 103.2, 102.5, 102.5),  # Day 5

        # Column 3: X rises to 105 again (EQUAL to column 1 - double top)
        (102.5, 103.5, 102.5, 103.5),  # Day 6
        (103.5, 104.5, 103.5, 104.5),  # Day 7
        (104.5, 105.0, 104.5, 105.0),  # Day 8: Second top at 105 (EQUAL)

        # Column 4: O falls to 102.5
        (105.0, 105.0, 103.2, 103.2),  # Day 9
        (103.2, 103.2, 102.5, 102.5),  # Day 10

        # Column 5: X BREAKS ABOVE to 108+ (Double Top Buy!)
        (102.5, 103.5, 102.5, 103.5),  # Day 11
        (103.5, 105.0, 103.5, 105.0),  # Day 12
        (105.0, 106.5, 105.0, 106.5),  # Day 13: BREAKOUT above 105
        (106.5, 108.0, 106.5, 108.0),  # Day 14: Strong follow-through
    ]

    base_date = datetime.datetime.now() - datetime.timedelta(days=len(prices))

    for i, (open_price, high, low, close) in enumerate(prices):
        candle_date = base_date + datetime.timedelta(days=i)
        candles.append({
            'timestamp': candle_date,
            'open': open_price,
            'high': high,
            'low': low,
            'close': close,
            'volume': 100000 + (i * 1000)
        })

    return candles

def generate_bearish_breakdown_pattern() -> List[Dict[str, Any]]:
    """Generate dummy data for a double bottom sell with follow through pattern."""
    candles = []

    # Create a double bottom pattern followed by breakdown with follow-through
    prices = [
        # First bottom formation
        (130, 131, 128, 129),  # Day 1 - Starting high
        (129, 130, 126, 127),  # Day 2
        (127, 128, 124, 125),  # Day 3
        (125, 126, 122, 123),  # Day 4
        (123, 124, 120, 121),  # Day 5 - First bottom at 120
        # Rally between bottoms
        (121, 124, 120, 123),  # Day 6 - Rally starts
        (123, 126, 122, 125),  # Day 7
        (125, 128, 124, 127),  # Day 8 - Peak between bottoms
        # Second bottom formation
        (127, 128, 125, 126),  # Day 9 - Building second bottom
        (126, 127, 123, 124),  # Day 10
        (124, 125, 121, 122),  # Day 11
        (122, 123, 120, 121),  # Day 12 - Second bottom at 120 (double bottom complete)
        # Breakdown with follow-through
        (121, 122, 115, 116),  # Day 13 - Breakdown below double bottom support
        (116, 117, 112, 113),  # Day 14 - Strong follow-through
        (113, 114, 108, 109),  # Day 15 - Continued momentum
        (109, 110, 105, 106),  # Day 16 - Follow-through confirmation
    ]
    
    base_date = datetime.datetime.now() - datetime.timedelta(days=len(prices))
    
    for i, (open_price, high, low, close) in enumerate(prices):
        candle_date = base_date + datetime.timedelta(days=i)
        candles.append({
            'timestamp': candle_date,
            'open': open_price,
            'high': high,
            'low': low,
            'close': close,
            'volume': 100000 + (i * 1000)
        })
    
    return candles

def generate_quadruple_top_pattern() -> List[Dict[str, Any]]:
    """
    Generate dummy data for a quadruple top buy with follow through pattern based on P&F definition.

    CORRECT Pattern: X-O-X-O-X-O-X-O-X (9 columns) where:
    - Columns 1, 3, 5, 7 have EQUAL tops (base pattern formation)
    - Column 9 breaks ABOVE the resistance (follow-through breakout)

    With 0.25% box size and 3-box reversal:
    - Need 3 × 0.25% = 0.75% move to reverse direction
    - Starting at 100, 0.75% = 0.75 points

    Strategy: Create 9 distinct columns with proper equal tops + breakout
    """
    candles = []

    # Quadruple Top Buy with Follow Through Pattern - 9 columns: X-O-X-O-X-O-X-O-X
    prices = [
        # Column 1: X rises from 100 to 105 (first top)
        (100.0, 102.0, 100.0, 102.0),  # Day 1: Strong start
        (102.0, 104.0, 102.0, 104.0),  # Day 2
        (104.0, 105.0, 104.0, 105.0),  # Day 3: First top at 105

        # Column 2: O falls to 102.5
        (105.0, 105.0, 103.2, 103.2),  # Day 4: Fall triggers reversal
        (103.2, 103.2, 102.5, 102.5),  # Day 5: Continue down

        # Column 3: X rises to 105 again (EQUAL to column 1)
        (102.5, 103.5, 102.5, 103.5),  # Day 6: Rise triggers reversal
        (103.5, 104.5, 103.5, 104.5),  # Day 7
        (104.5, 105.0, 104.5, 105.0),  # Day 8: Second top at 105 (EQUAL)

        # Column 4: O falls to 102.5
        (105.0, 105.0, 103.2, 103.2),  # Day 9: Fall triggers reversal
        (103.2, 103.2, 102.5, 102.5),  # Day 10: Continue down

        # Column 5: X rises to 105 again (EQUAL to columns 1 & 3)
        (102.5, 103.5, 102.5, 103.5),  # Day 11: Rise triggers reversal
        (103.5, 104.5, 103.5, 104.5),  # Day 12
        (104.5, 105.0, 104.5, 105.0),  # Day 13: Third top at 105 (EQUAL)

        # Column 6: O falls to 102.5
        (105.0, 105.0, 103.2, 103.2),  # Day 14: Fall triggers reversal
        (103.2, 103.2, 102.5, 102.5),  # Day 15: Continue down

        # Column 7: X rises to 105 again (EQUAL to columns 1, 3 & 5) - BASE PATTERN COMPLETE
        (102.5, 103.5, 102.5, 103.5),  # Day 16: Rise triggers reversal
        (103.5, 104.5, 103.5, 104.5),  # Day 17
        (104.5, 105.0, 104.5, 105.0),  # Day 18: Fourth top at 105 (EQUAL) - NO BREAKOUT YET

        # Column 8: O falls to 102.5 (start of follow-through setup)
        (105.0, 105.0, 103.2, 103.2),  # Day 19: Fall triggers reversal
        (103.2, 103.2, 102.5, 102.5),  # Day 20: Continue down

        # Column 9: X BREAKS ABOVE to 107+ (FOLLOW-THROUGH BREAKOUT!)
        (102.5, 103.5, 102.5, 103.5),  # Day 21: Rise triggers reversal
        (103.5, 105.0, 103.5, 105.0),  # Day 22: Pass previous tops
        (105.0, 106.5, 105.0, 106.5),  # Day 23: BREAKOUT above 105
        (106.5, 108.0, 106.5, 108.0),  # Day 24: Strong follow-through
    ]

    base_date = datetime.datetime.now() - datetime.timedelta(days=len(prices))

    for i, (open_price, high, low, close) in enumerate(prices):
        candle_date = base_date + datetime.timedelta(days=i)
        candles.append({
            'timestamp': candle_date,
            'open': open_price,
            'high': high,
            'low': low,
            'close': close,
            'volume': 100000 + (i * 1000)
        })

    return candles

def generate_quadruple_bottom_pattern() -> List[Dict[str, Any]]:
    """
    Generate dummy data for a quadruple bottom sell with follow through pattern based on P&F definition.

    CORRECT Pattern: O-X-O-X-O-X-O-X-O (9 columns) where:
    - Columns 1, 3, 5, 7 have EQUAL bottoms (base pattern formation)
    - Column 9 breaks BELOW the support (follow-through breakdown)

    With 0.25% box size, using large price moves for clarity.
    """
    candles = []

    # Quadruple Bottom Sell with Follow Through Pattern - 9 columns: O-X-O-X-O-X-O-X-O
    prices = [
        # Column 1: O column falling to 95 (first bottom)
        (105.0, 105.0, 95.0, 95.0),  # Day 1: Fall to 95

        # Column 2: X column rising to 99
        (95.0, 99.0, 95.0, 99.0),  # Day 2: Rally to 99

        # Column 3: O column falling to 95 again (second bottom - EQUAL to first)
        (99.0, 99.0, 95.0, 95.0),  # Day 3: Fall to 95 (same level)

        # Column 4: X column rising to 99
        (95.0, 99.0, 95.0, 99.0),  # Day 4: Rally to 99

        # Column 5: O column falling to 95 again (third bottom - EQUAL to first two)
        (99.0, 99.0, 95.0, 95.0),  # Day 5: Fall to 95 (same level)

        # Column 6: X column rising to 99
        (95.0, 99.0, 95.0, 99.0),  # Day 6: Rally to 99

        # Column 7: O column falling to 95 again (fourth bottom - EQUAL to first three) - BASE PATTERN COMPLETE
        (99.0, 99.0, 95.0, 95.0),  # Day 7: Fall to 95 (same level) - NO BREAKDOWN YET

        # Column 8: X column rising to 99 (start of follow-through setup)
        (95.0, 99.0, 95.0, 99.0),  # Day 8: Rally to 99

        # Column 9: O column BREAKS BELOW to 92- (FOLLOW-THROUGH BREAKDOWN!)
        (99.0, 99.0, 92.0, 92.0),  # Day 9: BREAKDOWN below 95 to 92

        # Additional follow-through
        (92.0, 92.0, 89.0, 89.0),  # Day 10: Continued weakness
        (89.0, 89.0, 86.0, 86.0),  # Day 11: Extended move
    ]

    base_date = datetime.datetime.now() - datetime.timedelta(days=len(prices))

    for i, (open_price, high, low, close) in enumerate(prices):
        candle_date = base_date + datetime.timedelta(days=i)
        candles.append({
            'timestamp': candle_date,
            'open': open_price,
            'high': high,
            'low': low,
            'close': close,
            'volume': 100000 + (i * 1000)
        })

    return candles

def generate_double_top_pattern() -> List[Dict[str, Any]]:
    """Generate dummy data for a double top pattern."""
    candles = []
    
    # Create double top pattern
    prices = [
        # First peak
        (100, 102, 99, 101),   # Day 1
        (101, 105, 100, 104),  # Day 2
        (104, 108, 103, 107),  # Day 3
        (107, 111, 106, 110),  # Day 4 - First top
        (110, 111, 107, 108),  # Day 5 - Pullback
        (108, 109, 105, 106),  # Day 6
        (106, 107, 103, 104),  # Day 7
        # Valley
        (104, 105, 101, 102),  # Day 8
        (102, 103, 99, 100),   # Day 9 - Valley
        (100, 101, 98, 99),    # Day 10
        # Second peak
        (99, 103, 98, 102),    # Day 11
        (102, 106, 101, 105),  # Day 12
        (105, 109, 104, 108),  # Day 13
        (108, 112, 107, 111),  # Day 14 - Second top (similar to first)
        (111, 112, 108, 109),  # Day 15 - Start of breakdown
        (109, 110, 106, 107),  # Day 16
        (107, 108, 104, 105),  # Day 17
    ]
    
    base_date = datetime.datetime.now() - datetime.timedelta(days=len(prices))
    
    for i, (open_price, high, low, close) in enumerate(prices):
        candle_date = base_date + datetime.timedelta(days=i)
        candles.append({
            'timestamp': candle_date,
            'open': open_price,
            'high': high,
            'low': low,
            'close': close,
            'volume': 100000 + (i * 1000)
        })
    
    return candles

def generate_triple_top_pattern() -> List[Dict[str, Any]]:
    """
    Generate dummy data for a triple top buy with follow through pattern based on P&F definition.

    CORRECT Pattern: X-O-X-O-X-O-X (7 columns) where:
    - Columns 1, 3, 5 have EQUAL tops (base pattern formation)
    - Column 7 breaks ABOVE the resistance (follow-through breakout)

    With 0.25% box size and 3-box reversal:
    - Need 3 × 0.25% = 0.75% move to reverse direction
    - Starting at 100, 0.75% = 0.75 points

    Strategy: Create 7 distinct columns with proper equal tops + breakout
    """
    candles = []

    # Triple Top Buy with Follow Through Pattern - 7 columns: X-O-X-O-X-O-X
    prices = [
        # Column 1: X rises from 100 to 105 (first top)
        (100.0, 102.0, 100.0, 102.0),  # Day 1: Strong start
        (102.0, 104.0, 102.0, 104.0),  # Day 2
        (104.0, 105.0, 104.0, 105.0),  # Day 3: First top at 105

        # Column 2: O falls to 102.5 (reversal requires 3 boxes = 0.75%)
        (105.0, 105.0, 103.2, 103.2),  # Day 4: Fall triggers reversal
        (103.2, 103.2, 102.5, 102.5),  # Day 5: Continue down

        # Column 3: X rises to 105 again (EQUAL to column 1)
        (102.5, 103.5, 102.5, 103.5),  # Day 6: Rise triggers reversal
        (103.5, 104.5, 103.5, 104.5),  # Day 7
        (104.5, 105.0, 104.5, 105.0),  # Day 8: Second top at 105 (EQUAL)

        # Column 4: O falls to 102.5
        (105.0, 105.0, 103.2, 103.2),  # Day 9: Fall triggers reversal
        (103.2, 103.2, 102.5, 102.5),  # Day 10: Continue down

        # Column 5: X rises to 105 again (EQUAL to columns 1 & 3) - BASE PATTERN COMPLETE
        (102.5, 103.5, 102.5, 103.5),  # Day 11: Rise triggers reversal
        (103.5, 104.5, 103.5, 104.5),  # Day 12
        (104.5, 105.0, 104.5, 105.0),  # Day 13: Third top at 105 (EQUAL) - NO BREAKOUT YET

        # Column 6: O falls to 102.5 (start of follow-through setup)
        (105.0, 105.0, 103.2, 103.2),  # Day 14: Fall triggers reversal
        (103.2, 103.2, 102.5, 102.5),  # Day 15: Continue down

        # Column 7: X BREAKS ABOVE to 107+ (FOLLOW-THROUGH BREAKOUT!)
        (102.5, 103.5, 102.5, 103.5),  # Day 16: Rise triggers reversal
        (103.5, 105.0, 103.5, 105.0),  # Day 17: Pass previous tops
        (105.0, 106.5, 105.0, 106.5),  # Day 18: BREAKOUT above 105
        (106.5, 108.0, 106.5, 108.0),  # Day 19: Strong follow-through
    ]

    base_date = datetime.datetime.now() - datetime.timedelta(days=len(prices))

    for i, (open_price, high, low, close) in enumerate(prices):
        candle_date = base_date + datetime.timedelta(days=i)
        candles.append({
            'timestamp': candle_date,
            'open': open_price,
            'high': high,
            'low': low,
            'close': close,
            'volume': 100000 + (i * 1000)
        })

    return candles

def generate_triple_bottom_pattern() -> List[Dict[str, Any]]:
    """
    Generate dummy data for a triple bottom sell with follow through pattern based on P&F definition.

    CORRECT Pattern: O-X-O-X-O-X-O (7 columns) where:
    - Columns 1, 3, 5 have EQUAL bottoms (base pattern formation)
    - Column 7 breaks BELOW the support (follow-through breakdown)

    With 0.25% box size, using large price moves for clarity.
    """
    candles = []

    # Triple Bottom Sell with Follow Through Pattern - 7 columns: O-X-O-X-O-X-O
    prices = [
        # Column 1: O column falling to 95 (first bottom)
        (105.0, 105.0, 95.0, 95.0),  # Day 1: Fall to 95

        # Column 2: X column rising to 99
        (95.0, 99.0, 95.0, 99.0),  # Day 2: Rally to 99

        # Column 3: O column falling to 95 again (second bottom - EQUAL to first)
        (99.0, 99.0, 95.0, 95.0),  # Day 3: Fall to 95 (same level)

        # Column 4: X column rising to 99
        (95.0, 99.0, 95.0, 99.0),  # Day 4: Rally to 99

        # Column 5: O column falling to 95 again (third bottom - EQUAL to first two) - BASE PATTERN COMPLETE
        (99.0, 99.0, 95.0, 95.0),  # Day 5: Fall to 95 (same level) - NO BREAKDOWN YET

        # Column 6: X column rising to 99 (start of follow-through setup)
        (95.0, 99.0, 95.0, 99.0),  # Day 6: Rally to 99

        # Column 7: O column BREAKS BELOW to 92- (FOLLOW-THROUGH BREAKDOWN!)
        (99.0, 99.0, 92.0, 92.0),  # Day 7: BREAKDOWN below 95 to 92

        # Additional follow-through
        (92.0, 92.0, 89.0, 89.0),  # Day 8: Continued weakness
        (89.0, 89.0, 86.0, 86.0),  # Day 9: Extended move
    ]

    base_date = datetime.datetime.now() - datetime.timedelta(days=len(prices))

    for i, (open_price, high, low, close) in enumerate(prices):
        candle_date = base_date + datetime.timedelta(days=i)
        candles.append({
            'timestamp': candle_date,
            'open': open_price,
            'high': high,
            'low': low,
            'close': close,
            'volume': 100000 + (i * 1000)
        })

    return candles

def generate_ascending_triangle_pattern() -> List[Dict[str, Any]]:
    """Generate dummy data for an ascending triangle pattern."""
    candles = []
    
    # Create ascending triangle pattern (higher lows, same highs)
    prices = [
        (100, 102, 99, 101),   # Day 1
        (101, 105, 100, 104),  # Day 2
        (104, 108, 103, 107),  # Day 3
        (107, 110, 106, 110),  # Day 4 - Resistance level
        (110, 111, 107, 108),  # Day 5 - Pullback
        (108, 109, 105, 106),  # Day 6 - Higher low
        (106, 110, 105, 109),  # Day 7 - Test resistance
        (109, 110, 107, 108),  # Day 8 - Pullback
        (108, 109, 106, 107),  # Day 9 - Higher low again
        (107, 110, 106, 109),  # Day 10 - Test resistance
        (109, 110, 108, 109),  # Day 11 - Pullback (higher low)
        (109, 113, 108, 112),  # Day 12 - Breakout above resistance
        (112, 116, 111, 115),  # Day 13 - Follow through
    ]
    
    base_date = datetime.datetime.now() - datetime.timedelta(days=len(prices))
    
    for i, (open_price, high, low, close) in enumerate(prices):
        candle_date = base_date + datetime.timedelta(days=i)
        candles.append({
            'timestamp': candle_date,
            'open': open_price,
            'high': high,
            'low': low,
            'close': close,
            'volume': 100000 + (i * 1000)
        })
    
    return candles

def generate_turtle_breakout_ft_buy_pattern() -> List[Dict[str, Any]]:
    """
    Generate Turtle Breakout Follow Through (FT) Buy pattern.

    Pattern structure (from reference image):
    1. Consolidation: 5 consecutive columns with highs at or below resistance (base building)
    2. Initial turtle breakout: X breaks above the consolidation resistance
    3. Follow through: Double top buy pattern after turtle breakout
    4. Final breakout: X breaks above double top resistance

    With 1% box size and 3-box reversal (3% move needed to reverse).
    """
    prices = [
        # Columns 1-5: Consolidation at 100-104 level (5 consecutive columns with highs at ~104)
        # Column 1: X from 100 to 104 (4 boxes up) - consolidation column 1, high at 104
        (100.0, 104.0, 100.0, 104.0),

        # Column 2: O from 101 to 98 (3 boxes down) - consolidation column 2
        (101.0, 101.0, 98.0, 98.0),

        # Column 3: X from 101 to 104 (3 boxes up) - consolidation column 3, high at 104
        (101.0, 104.0, 101.0, 104.0),

        # Column 4: O from 101 to 98 (3 boxes down) - consolidation column 4
        (101.0, 101.0, 98.0, 98.0),

        # Column 5: X from 101 to 103 (2 boxes up) - consolidation column 5, high at 103 (below 104)
        (101.0, 103.0, 101.0, 103.0),

        # Column 6: TURTLE BREAKOUT - X from 107 to 115 (breaks above consolidation resistance of 104)
        (107.0, 115.0, 107.0, 115.0),

        # Column 7: O pullback from 112 to 109 (3 boxes down)
        (112.0, 112.0, 109.0, 109.0),

        # Column 8: X to 114 (5 boxes up) - First top
        (112.0, 114.0, 112.0, 114.0),

        # Column 9: O pullback from 111 to 108 (3 boxes down)
        (111.0, 111.0, 108.0, 108.0),

        # Column 10: X to 114 (6 boxes up) - Second top (double top at 114)
        (111.0, 114.0, 111.0, 114.0),

        # Column 11: O pullback from 111 to 109 (2 boxes down)
        (111.0, 111.0, 109.0, 109.0),

        # Column 12: TURTLE FT BREAKOUT - X from 112 to 118 (breaks above double top at 114)
        (112.0, 118.0, 112.0, 118.0),
    ]

    # Convert to candle format
    candles = []
    base_date = datetime.datetime.now() - datetime.timedelta(days=len(prices))
    for i, (open_price, high, low, close) in enumerate(prices):
        candle_date = base_date + datetime.timedelta(days=i)
        candles.append({
            'timestamp': candle_date,
            'open': open_price,
            'high': high,
            'low': low,
            'close': close,
            'volume': 100000 + (i * 1000)
        })

    return candles

def generate_turtle_breakout_ft_sell_pattern() -> List[Dict[str, Any]]:
    """
    Generate Turtle Breakout Follow Through (FT) Sell pattern.

    Pattern structure (from reference image):
    1. Consolidation: 5 consecutive columns with lows at or above support (base building)
    2. Initial turtle breakout: O breaks below the consolidation support
    3. Follow through: Double bottom sell pattern after turtle breakout
    4. Final breakdown: O breaks below double bottom support

    With 1% box size and 3-box reversal (3% move needed to reverse).
    """
    prices = [
        # Columns 1-5: Consolidation at 96-100 level (5 consecutive columns with lows at ~96)
        # Column 1: O from 100 to 96 (4 boxes down) - consolidation column 1, low at 96
        (100.0, 100.0, 96.0, 96.0),

        # Column 2: X from 99 to 102 (3 boxes up) - consolidation column 2
        (99.0, 102.0, 99.0, 102.0),

        # Column 3: O from 99 to 96 (3 boxes down) - consolidation column 3, low at 96
        (99.0, 99.0, 96.0, 96.0),

        # Column 4: X from 99 to 102 (3 boxes up) - consolidation column 4
        (99.0, 102.0, 99.0, 102.0),

        # Column 5: O from 99 to 97 (2 boxes down) - consolidation column 5, low at 97 (above 96)
        (99.0, 99.0, 97.0, 97.0),

        # Column 6: TURTLE BREAKOUT - O from 93 to 85 (breaks below consolidation support of 96)
        (93.0, 93.0, 85.0, 85.0),

        # Column 7: X bounce from 88 to 91 (3 boxes up)
        (88.0, 91.0, 88.0, 91.0),

        # Column 8: O to 86 (5 boxes down) - First bottom
        (88.0, 88.0, 86.0, 86.0),

        # Column 9: X bounce from 89 to 92 (3 boxes up)
        (89.0, 92.0, 89.0, 92.0),

        # Column 10: O to 86 (6 boxes down) - Second bottom (double bottom at 86)
        (89.0, 89.0, 86.0, 86.0),

        # Column 11: X bounce from 88 to 90 (2 boxes up)
        (88.0, 90.0, 88.0, 90.0),

        # Column 12: TURTLE FT BREAKDOWN - O from 87 to 81 (breaks below double bottom at 86)
        (87.0, 87.0, 81.0, 81.0),
    ]

    # Convert to candle format
    candles = []
    base_date = datetime.datetime.now() - datetime.timedelta(days=len(prices))
    for i, (open_price, high, low, close) in enumerate(prices):
        candle_date = base_date + datetime.timedelta(days=i)
        candles.append({
            'timestamp': candle_date,
            'open': open_price,
            'high': high,
            'low': low,
            'close': close,
            'volume': 100000 + (i * 1000)
        })

    return candles



def generate_ema_validated_triple_top_pattern() -> List[Dict[str, Any]]:
    """Generate dummy data for EMA-validated triple top pattern."""
    candles = []

    # Create a pattern that stays above 20 EMA with triple top formation
    prices = [
        # Initial trend above EMA
        (100, 102, 99, 101),   # Day 1 - EMA starts around 100
        (101, 104, 100, 103),  # Day 2 - above EMA
        (103, 106, 102, 105),  # Day 3 - above EMA
        (105, 108, 104, 107),  # Day 4 - above EMA
        (107, 110, 106, 110),  # Day 5 - First top at 110, above EMA

        # Pullback but stay above EMA
        (110, 110, 106, 107),  # Day 6 - pullback but above EMA
        (107, 108, 105, 106),  # Day 7 - above EMA
        (106, 107, 104, 105),  # Day 8 - above EMA

        # Second top formation above EMA
        (105, 107, 104, 106),  # Day 9 - building above EMA
        (106, 109, 105, 108),  # Day 10 - above EMA
        (108, 110, 107, 110),  # Day 11 - Second top at 110, above EMA

        # Pullback but stay above EMA
        (110, 110, 106, 107),  # Day 12 - pullback but above EMA
        (107, 108, 105, 106),  # Day 13 - above EMA
        (106, 107, 104, 105),  # Day 14 - above EMA

        # Third top formation above EMA
        (105, 107, 104, 106),  # Day 15 - building above EMA
        (106, 109, 105, 108),  # Day 16 - above EMA
        (108, 110, 107, 110),  # Day 17 - Third top at 110, above EMA

        # EMA-validated breakout
        (110, 116, 109, 115),  # Day 18 - BREAKOUT above 110, well above EMA
        (115, 119, 114, 118),  # Day 19 - strong follow-through above EMA
        (118, 122, 117, 121),  # Day 20 - continued momentum above EMA
    ]

    base_date = datetime.datetime.now() - datetime.timedelta(days=len(prices))

    for i, (open_price, high, low, close) in enumerate(prices):
        candle_date = base_date + datetime.timedelta(days=i)
        candles.append({
            'timestamp': candle_date,
            'open': open_price,
            'high': high,
            'low': low,
            'close': close,
            'volume': 100000 + (i * 1000)
        })

    return candles

def generate_catapult_buy_pattern() -> List[Dict[str, Any]]:
    """
    Generate dummy data for CATAPULT BUY pattern based on traditional P&F definition.

    Catapult Buy = Triple Top Buy + Double Top Buy

    Pattern structure:
    1. Triple Top Buy (TTB): X-O-X-O-X where X1 & X3 equal, X5 breaks above
    2. Double Top Buy (DTB): X-O-X where X7 breaks above X5
    3. CATAPULT BUY: Alert triggers at column 7 (X7)

    Total pattern: X-O-X-O-X-O-X (7 columns)

    With 1% box size and 3-box reversal (3% move needed to reverse).
    Using multi-day gradual moves to create clean P&F columns.
    """
    candles = []

    # Catapult Buy Pattern: X-O-X-O-X-O-X (7 columns)
    # Each column needs gradual moves to ensure proper P&F column formation
    prices = [
        # Column 1: X rises from 100 to 110 (first top) - gradual rise
        (100.0, 103.0, 100.0, 103.0),  # Day 1
        (103.0, 106.0, 103.0, 106.0),  # Day 2
        (106.0, 109.0, 106.0, 109.0),  # Day 3
        (109.0, 110.0, 109.0, 110.0),  # Day 4: First top at 110

        # Column 2: O falls from 110 to 100 - gradual fall (3% reversal triggers)
        (110.0, 110.0, 106.5, 106.5),  # Day 5: Fall triggers reversal
        (106.5, 106.5, 103.0, 103.0),  # Day 6
        (103.0, 103.0, 100.0, 100.0),  # Day 7: Fall to 100

        # Column 3: X rises from 100 to 110 again (EQUAL to column 1)
        (100.0, 103.5, 100.0, 103.5),  # Day 8: Rise triggers reversal
        (103.5, 107.0, 103.5, 107.0),  # Day 9
        (107.0, 110.0, 107.0, 110.0),  # Day 10: Second top at 110 (EQUAL)

        # Column 4: O falls from 110 to 100
        (110.0, 110.0, 106.5, 106.5),  # Day 11: Fall triggers reversal
        (106.5, 106.5, 103.0, 103.0),  # Day 12
        (103.0, 103.0, 100.0, 100.0),  # Day 13: Fall to 100

        # Column 5: X BREAKS ABOVE to 115 (TTB complete!)
        (100.0, 103.5, 100.0, 103.5),  # Day 14: Rise triggers reversal
        (103.5, 107.0, 103.5, 107.0),  # Day 15
        (107.0, 110.5, 107.0, 110.5),  # Day 16: Pass 110
        (110.5, 113.0, 110.5, 113.0),  # Day 17: BREAKOUT above 110
        (113.0, 115.0, 113.0, 115.0),  # Day 18: TTB complete at 115

        # Column 6: O falls from 115 to 105 (pullback after TTB)
        (115.0, 115.0, 111.5, 111.5),  # Day 19: Fall triggers reversal
        (111.5, 111.5, 108.0, 108.0),  # Day 20
        (108.0, 108.0, 105.0, 105.0),  # Day 21: Fall to 105

        # Column 7: X BREAKS ABOVE 115 to 120+ (CATAPULT BUY! DTB complete!)
        (105.0, 108.5, 105.0, 108.5),  # Day 22: Rise triggers reversal
        (108.5, 112.0, 108.5, 112.0),  # Day 23
        (112.0, 115.5, 112.0, 115.5),  # Day 24: Pass 115
        (115.5, 118.0, 115.5, 118.0),  # Day 25: CATAPULT BUY! Breaks above 115
        (118.0, 120.0, 118.0, 120.0),  # Day 26: DTB complete at 120
    ]

    base_date = datetime.datetime.now() - datetime.timedelta(days=len(prices))

    for i, (open_price, high, low, close) in enumerate(prices):
        candle_date = base_date + datetime.timedelta(days=i)
        candles.append({
            'timestamp': candle_date,
            'open': open_price,
            'high': high,
            'low': low,
            'close': close,
            'volume': 100000 + (i * 1000)
        })

    return candles

def generate_pole_follow_through_buy_pattern() -> List[Dict[str, Any]]:
    """
    Generate dummy data for 100% pole follow through buy pattern based on P&F definition.

    Pattern structure:
    1. Strong vertical X column (pole) - significant upward move (at least 5%)
    2. Followed by O-X-O-X pattern (double top buy formation)
    3. Final X breaks above the pole high for buy signal

    Total: 5 columns (Pole-X, O, X, O, X breakout)

    With 0.25% box size and 3-box reversal (0.75% move needed to reverse).
    Using gradual multi-day moves to build each column separately.
    """
    candles = []

    # 100% Pole Follow Through Buy Pattern: X-O-X-O-X (5 columns)
    prices = [
        # Column 1: POLE - Strong vertical X column from 100 to 108 (8% move, ~20-22 boxes)
        (100.0, 102.0, 100.0, 102.0),  # Day 1
        (102.0, 104.0, 102.0, 104.0),  # Day 2
        (104.0, 106.0, 104.0, 106.0),  # Day 3
        (106.0, 108.0, 106.0, 108.0),  # Day 4: Pole top at 108 (8% move)

        # Column 2: O pullback to 105
        (108.0, 108.0, 106.0, 106.0),  # Day 5: Fall triggers reversal
        (106.0, 106.0, 105.0, 105.0),  # Day 6

        # Column 3: X rises to 107 (clearly BELOW pole high of 108)
        (105.0, 106.0, 105.0, 106.0),  # Day 7: Rise triggers reversal
        (106.0, 107.0, 106.0, 107.0),  # Day 8: Stop at 107 (1 point below pole)

        # Column 4: O pullback to 105
        (107.0, 107.0, 106.0, 106.0),  # Day 9: Fall triggers reversal
        (106.0, 106.0, 105.0, 105.0),  # Day 10

        # Column 5: X BREAKS ABOVE pole high to 111+ (Pole FT Buy!)
        (105.0, 106.0, 105.0, 106.0),  # Day 11: Rise triggers reversal
        (106.0, 108.0, 106.0, 108.0),  # Day 12: Pass pole high
        (108.0, 109.5, 108.0, 109.5),  # Day 13: BREAKOUT above 108
        (109.5, 111.0, 109.5, 111.0),  # Day 14: POLE FT BUY!

        # Follow-through
        (111.0, 113.0, 111.0, 113.0),  # Day 15
        (113.0, 115.0, 113.0, 115.0),  # Day 16
    ]

    base_date = datetime.datetime.now() - datetime.timedelta(days=len(prices))

    for i, (open_price, high, low, close) in enumerate(prices):
        candle_date = base_date + datetime.timedelta(days=i)
        candles.append({
            'timestamp': candle_date,
            'open': open_price,
            'high': high,
            'low': low,
            'close': close,
            'volume': 100000 + (i * 1000)
        })

    return candles

def generate_pole_follow_through_sell_pattern() -> List[Dict[str, Any]]:
    """
    Generate dummy data for 100% pole follow through sell pattern.

    Pattern structure:
    1. 100% pole pattern (strong vertical O column move)
    2. Followed by double bottom sell pattern (X-O-X-O formation)
    3. Creates a six-column pattern total
    4. O column breaks below support for sell signal
    """
    # Create a 28-day price sequence with pole follow through sell pattern
    base_price = 120.0
    prices = []

    # Days 1-8: Build down to pole base
    for i in range(8):
        prices.append(base_price - i * 0.5)  # Gradual decline to 116.5

    # Days 9-12: 100% pole pattern (strong vertical move down)
    pole_base = prices[-1]
    pole_prices = [
        pole_base - 1.0,   # 115.5
        pole_base - 2.5,   # 114.0
        pole_base - 4.0,   # 112.5
        pole_base - 5.5    # 111.0 - Strong 5.5 point pole down
    ]
    prices.extend(pole_prices)

    # Days 13-16: First X column (bounce)
    bounce_prices = [
        pole_prices[-1] + 1.0,  # 112.0
        pole_prices[-1] + 2.0,  # 113.0
        pole_prices[-1] + 2.5,  # 113.5
        pole_prices[-1] + 3.0   # 114.0
    ]
    prices.extend(bounce_prices)

    # Days 17-20: First O column (test support)
    first_o_prices = [
        bounce_prices[-1] - 1.0,  # 113.0
        bounce_prices[-1] - 2.0,  # 112.0
        bounce_prices[-1] - 2.5,  # 111.5
        bounce_prices[-1] - 3.0   # 111.0 - Test previous low
    ]
    prices.extend(first_o_prices)

    # Days 21-24: Second X column (bounce)
    second_bounce_prices = [
        first_o_prices[-1] + 1.0,  # 112.0
        first_o_prices[-1] + 2.0,  # 113.0
        first_o_prices[-1] + 2.5,  # 113.5
        first_o_prices[-1] + 3.0   # 114.0
    ]
    prices.extend(second_bounce_prices)

    # Days 25-28: Final O column (breakdown below support)
    breakdown_prices = [
        second_bounce_prices[-1] - 1.5,  # 112.5
        second_bounce_prices[-1] - 3.0,  # 111.0 - Match support
        second_bounce_prices[-1] - 4.0,  # 110.0 - Break below support
        second_bounce_prices[-1] - 5.5   # 108.5 - Strong follow through
    ]
    prices.extend(breakdown_prices)

    # Convert to candle format
    candles = []
    base_date = datetime.datetime.now() - datetime.timedelta(days=len(prices))

    for i, price in enumerate(prices):
        # Create realistic OHLC data around the target price
        open_price = price + 0.2 if i > 0 else price
        high_price = price + 0.3
        low_price = price - 0.3
        close_price = price

        candle_date = base_date + datetime.timedelta(days=i)

        candles.append({
            'timestamp': candle_date,
            'open': open_price,  # Store as float, not string
            'high': high_price,  # Store as float, not string
            'low': low_price,    # Store as float, not string
            'close': close_price, # Store as float, not string
            'volume': 100000 + (i * 1000)
        })

    return candles

def generate_catapult_sell_pattern() -> List[Dict[str, Any]]:
    """
    Generate dummy data for CATAPULT SELL pattern based on traditional P&F definition.

    Catapult Sell = Triple Bottom Sell + Double Bottom Sell

    Pattern structure:
    1. Triple Bottom Sell (TBS): O-X-O-X-O where O1 & O3 equal, O5 breaks below
    2. Double Bottom Sell (DBS): O-X-O where O7 breaks below O5
    3. CATAPULT SELL: Alert triggers at column 7 (O7)

    Total pattern: O-X-O-X-O-X-O (7 columns)

    With 1% box size and 3-box reversal (3% move needed to reverse).
    Using multi-day gradual moves to create clean P&F columns.
    """
    candles = []

    # Catapult Sell Pattern: O-X-O-X-O-X-O (7 columns)
    # Each column needs gradual moves to ensure proper P&F column formation
    prices = [
        # Column 1: O falls from 110 to 100 (first bottom) - gradual decline
        (110.0, 110.0, 107.0, 107.0),  # Day 1
        (107.0, 107.0, 104.0, 104.0),  # Day 2
        (104.0, 104.0, 101.0, 101.0),  # Day 3
        (101.0, 101.0, 100.0, 100.0),  # Day 4: First bottom at 100

        # Column 2: X rises from 100 to 110 - gradual rise (3% reversal triggers)
        (100.0, 103.5, 100.0, 103.5),  # Day 5: Rise triggers reversal
        (103.5, 107.0, 103.5, 107.0),  # Day 6
        (107.0, 110.0, 107.0, 110.0),  # Day 7: Rise to 110

        # Column 3: O falls from 110 to 100 again (EQUAL to column 1)
        (110.0, 110.0, 106.5, 106.5),  # Day 8: Fall triggers reversal
        (106.5, 106.5, 103.0, 103.0),  # Day 9
        (103.0, 103.0, 100.0, 100.0),  # Day 10: Second bottom at 100 (EQUAL)

        # Column 4: X rises from 100 to 110
        (100.0, 103.5, 100.0, 103.5),  # Day 11: Rise triggers reversal
        (103.5, 107.0, 103.5, 107.0),  # Day 12
        (107.0, 110.0, 107.0, 110.0),  # Day 13: Rise to 110

        # Column 5: O BREAKS BELOW to 95 (TBS complete!)
        (110.0, 110.0, 106.5, 106.5),  # Day 14: Fall triggers reversal
        (106.5, 106.5, 103.0, 103.0),  # Day 15
        (103.0, 103.0, 99.5, 99.5),    # Day 16: Pass 100
        (99.5, 99.5, 97.0, 97.0),      # Day 17: BREAKDOWN below 100
        (97.0, 97.0, 95.0, 95.0),      # Day 18: TBS complete at 95

        # Column 6: X rises from 95 to 105 (pullback after TBS)
        (95.0, 98.5, 95.0, 98.5),      # Day 19: Rise triggers reversal
        (98.5, 102.0, 98.5, 102.0),    # Day 20
        (102.0, 105.0, 102.0, 105.0),  # Day 21: Rise to 105

        # Column 7: O BREAKS BELOW 95 to 90- (CATAPULT SELL! DBS complete!)
        (105.0, 105.0, 101.5, 101.5),  # Day 22: Fall triggers reversal
        (101.5, 101.5, 98.0, 98.0),    # Day 23
        (98.0, 98.0, 94.5, 94.5),      # Day 24: Pass 95
        (94.5, 94.5, 92.0, 92.0),      # Day 25: CATAPULT SELL! Breaks below 95
        (92.0, 92.0, 90.0, 90.0),      # Day 26: DBS complete at 90
    ]

    base_date = datetime.datetime.now() - datetime.timedelta(days=len(prices))

    for i, (open_price, high, low, close) in enumerate(prices):
        candle_date = base_date + datetime.timedelta(days=i)
        candles.append({
            'timestamp': candle_date,
            'open': open_price,
            'high': high,
            'low': low,
            'close': close,
            'volume': 100000 + (i * 1000)
        })

    return candles

def generate_ziddi_bulls_pattern() -> List[Dict[str, Any]]:
    """
    Generate dummy data for ZIDDI BULLS pattern (Stubborn Bulls).

    Pattern indicates bulls are stubborn and not willing to let prices fall.

    Pattern structure (10 columns): O-X-O-X-O-X-O-X-O-X
    1. Double Bottom Sell #1: O1 & O3 equal at 100, O5 breaks below to 98
    2. Double Bottom Sell #2: O7 breaks below O5 to 97 (but only small decline!)
    3. Double Top Buy: X10 breaks above X8 - Bulls take control

    With 1% box size and 3-box reversal (3% move needed to reverse).
    """
    candles = []

    prices = [
        # Start with a small rise to establish base, then fall for Column 1 (O)
        (100.0, 100.5, 100.0, 100.5),  # Day 0: Establish base

        # Column 1 (O): Falls from 110 to 100 (first bottom O1)
        (110.0, 110.0, 107.0, 107.0),  # Day 1
        (107.0, 107.0, 104.0, 104.0),  # Day 2
        (104.0, 104.0, 101.0, 101.0),  # Day 3
        (101.0, 101.0, 100.0, 100.0),  # Day 4: O1 bottom at 100

        # Column 2 (X): Rises from 100 to 110 (X2)
        (100.0, 103.5, 100.0, 103.5),  # Day 5: Rise triggers reversal
        (103.5, 107.0, 103.5, 107.0),  # Day 6
        (107.0, 110.0, 107.0, 110.0),  # Day 7: X2 top at 110

        # Column 3 (O): Falls from 110 to 100 again (O3 EQUAL to O1)
        (110.0, 110.0, 106.5, 106.5),  # Day 8: Fall triggers reversal
        (106.5, 106.5, 103.0, 103.0),  # Day 9
        (103.0, 103.0, 100.0, 100.0),  # Day 10: O3 bottom at 100 (EQUAL to O1)

        # Column 4 (X): Rises from 100 to 110 (X4)
        (100.0, 103.5, 100.0, 103.5),  # Day 11: Rise triggers reversal
        (103.5, 107.0, 103.5, 107.0),  # Day 12
        (107.0, 110.0, 107.0, 110.0),  # Day 13: X4 top at 110

        # Column 5 (O): BREAKS BELOW to 98 (O5 - DBS #1 complete)
        (110.0, 110.0, 106.5, 106.5),  # Day 14: Fall triggers reversal
        (106.5, 106.5, 103.0, 103.0),  # Day 15
        (103.0, 103.0, 99.5, 99.5),    # Day 16
        (99.5, 99.5, 98.0, 98.0),      # Day 17: O5 at 98 (breaks below O1/O3)

        # Column 6 (X): Rises from 98 to 108 (X6)
        (98.0, 101.5, 98.0, 101.5),    # Day 18: Rise triggers reversal
        (101.5, 105.0, 101.5, 105.0),  # Day 19
        (105.0, 108.0, 105.0, 108.0),  # Day 20: X6 top at 108

        # Column 7 (O): Falls to 97 (O7 - DBS #2, only 1 point below O5!)
        (108.0, 108.0, 104.5, 104.5),  # Day 21: Fall triggers reversal
        (104.5, 104.5, 101.0, 101.0),  # Day 22
        (101.0, 101.0, 98.5, 98.5),    # Day 23
        (98.5, 98.5, 97.0, 97.0),      # Day 24: O7 at 97 (stubborn bulls!)

        # Column 8 (X): Rises from 97 to 107 (X8)
        (97.0, 100.5, 97.0, 100.5),    # Day 25: Rise triggers reversal
        (100.5, 104.0, 100.5, 104.0),  # Day 26
        (104.0, 107.0, 104.0, 107.0),  # Day 27: X8 top at 107

        # Column 9 (O): Falls to 102 (O9 - bear trap)
        (107.0, 107.0, 103.5, 103.5),  # Day 28: Fall triggers reversal
        (103.5, 103.5, 102.0, 102.0),  # Day 29: O9 at 102

        # Column 10 (X): BREAKS ABOVE to 112+ (X10 - ZIDDI BULLS!)
        (102.0, 105.5, 102.0, 105.5),  # Day 30: Rise triggers reversal
        (105.5, 109.0, 105.5, 109.0),  # Day 31: Pass X8 high
        (109.0, 112.0, 109.0, 112.0),  # Day 32: ZIDDI BULLS! X10 breaks above
        (112.0, 115.0, 112.0, 115.0),  # Day 33: Strong follow-through
    ]

    base_date = datetime.datetime.now() - datetime.timedelta(days=len(prices))

    for i, (open_price, high, low, close) in enumerate(prices):
        candle_date = base_date + datetime.timedelta(days=i)
        candles.append({
            'timestamp': candle_date,
            'open': open_price,
            'high': high,
            'low': low,
            'close': close,
            'volume': 100000 + (i * 1000)
        })

    return candles

def generate_ziddi_bears_pattern() -> List[Dict[str, Any]]:
    """
    Generate dummy data for ZIDDI BEARS pattern (Stubborn Bears).

    Pattern indicates bears are stubborn and not willing to let prices rise.

    Pattern structure (10 columns): X-O-X-O-X-O-X-O-X-O
    1. Double Top Buy #1: X1 & X3 equal at 110, X5 breaks above to 112
    2. Double Top Buy #2: X7 breaks above X5 to 113 (but only small rise!)
    3. Double Bottom Sell: O10 breaks below O8 - Bears take control

    With 1% box size and 3-box reversal (3% move needed to reverse).
    """
    candles = []

    prices = [
        # Column 1 (X): Rises from 100 to 110 (first top X1)
        (100.0, 103.0, 100.0, 103.0),  # Day 1
        (103.0, 106.0, 103.0, 106.0),  # Day 2
        (106.0, 109.0, 106.0, 109.0),  # Day 3
        (109.0, 110.0, 109.0, 110.0),  # Day 4: X1 top at 110

        # Column 2 (O): Falls from 110 to 100 (O2)
        (110.0, 110.0, 106.5, 106.5),  # Day 5: Fall triggers reversal
        (106.5, 106.5, 103.0, 103.0),  # Day 6
        (103.0, 103.0, 100.0, 100.0),  # Day 7: O2 bottom at 100

        # Column 3 (X): Rises from 100 to 110 again (X3 EQUAL to X1)
        (100.0, 103.5, 100.0, 103.5),  # Day 8: Rise triggers reversal
        (103.5, 107.0, 103.5, 107.0),  # Day 9
        (107.0, 110.0, 107.0, 110.0),  # Day 10: X3 top at 110 (EQUAL to X1)

        # Column 4 (O): Falls from 110 to 100 (O4)
        (110.0, 110.0, 106.5, 106.5),  # Day 11: Fall triggers reversal
        (106.5, 106.5, 103.0, 103.0),  # Day 12
        (103.0, 103.0, 100.0, 100.0),  # Day 13: O4 bottom at 100

        # Column 5 (X): BREAKS ABOVE to 112 (X5 - DTB #1 complete)
        (100.0, 103.5, 100.0, 103.5),  # Day 14: Rise triggers reversal
        (103.5, 107.0, 103.5, 107.0),  # Day 15
        (107.0, 110.5, 107.0, 110.5),  # Day 16
        (110.5, 112.0, 110.5, 112.0),  # Day 17: X5 at 112 (breaks above X1/X3)

        # Column 6 (O): Falls from 112 to 102 (O6)
        (112.0, 112.0, 108.5, 108.5),  # Day 18: Fall triggers reversal
        (108.5, 108.5, 105.0, 105.0),  # Day 19
        (105.0, 105.0, 102.0, 102.0),  # Day 20: O6 bottom at 102

        # Column 7 (X): Rises to 113 (X7 - DTB #2, only 1 point above X5!)
        (102.0, 105.5, 102.0, 105.5),  # Day 21: Rise triggers reversal
        (105.5, 109.0, 105.5, 109.0),  # Day 22
        (109.0, 112.5, 109.0, 112.5),  # Day 23
        (112.5, 113.0, 112.5, 113.0),  # Day 24: X7 at 113 (stubborn bears!)

        # Column 8 (O): Falls from 113 to 103 (O8)
        (113.0, 113.0, 109.5, 109.5),  # Day 25: Fall triggers reversal
        (109.5, 109.5, 106.0, 106.0),  # Day 26
        (106.0, 106.0, 103.0, 103.0),  # Day 27: O8 bottom at 103

        # Column 9 (X): Rises to 108 (X9 - bull trap)
        (103.0, 106.5, 103.0, 106.5),  # Day 28: Rise triggers reversal
        (106.5, 108.0, 106.5, 108.0),  # Day 29: X9 top at 108

        # Column 10 (O): BREAKS BELOW to 98- (O10 - ZIDDI BEARS!)
        (108.0, 108.0, 104.5, 104.5),  # Day 30: Fall triggers reversal
        (104.5, 104.5, 101.0, 101.0),  # Day 31: Pass O8 low
        (101.0, 101.0, 98.0, 98.0),    # Day 32: ZIDDI BEARS! O10 breaks below
        (98.0, 98.0, 95.0, 95.0),      # Day 33: Strong follow-through
    ]

    base_date = datetime.datetime.now() - datetime.timedelta(days=len(prices))

    for i, (open_price, high, low, close) in enumerate(prices):
        candle_date = base_date + datetime.timedelta(days=i)
        candles.append({
            'timestamp': candle_date,
            'open': open_price,
            'high': high,
            'low': low,
            'close': close,
            'volume': 100000 + (i * 1000)
        })

    return candles

def generate_aft_anchor_breakout_buy_pattern():
    """
    Generate AFT (Anchor Follow Through) Bullish Breakout pattern based on P&F definition.

    Pattern requirements:
    1. Anchor Column: Tall X column (height >= 15 boxes)
    2. Consolidation: Price stays below anchor high for several columns
    3. Breakout: On the 4th column after anchor, X column:
       - Performs Double Top Buy (breaks above previous X column)
       - AND breaks above anchor.top

    With 0.25% box size and 3-box reversal (0.75% move needed to reverse).
    Using gradual multi-day moves to build each column separately.
    """
    candles = []

    # AFT Anchor Breakout Buy Pattern: X-O-X-O-X (5 columns)
    prices = [
        # Column 1: ANCHOR - Tall X column from 100 to 115 (15-point anchor, ~60 boxes)
        (100.0, 102.0, 100.0, 102.0),  # Day 1
        (102.0, 104.0, 102.0, 104.0),  # Day 2
        (104.0, 106.0, 104.0, 106.0),  # Day 3
        (106.0, 108.0, 106.0, 108.0),  # Day 4
        (108.0, 110.0, 108.0, 110.0),  # Day 5
        (110.0, 112.0, 110.0, 112.0),  # Day 6
        (112.0, 114.0, 112.0, 114.0),  # Day 7
        (114.0, 115.0, 114.0, 115.0),  # Day 8: Anchor top at 115

        # Column 2: O pullback to 111
        (115.0, 115.0, 113.0, 113.0),  # Day 9: Fall triggers reversal
        (113.0, 113.0, 111.0, 111.0),  # Day 10

        # Column 3: X rises to 114 (below anchor high of 115)
        (111.0, 112.0, 111.0, 112.0),  # Day 11: Rise triggers reversal
        (112.0, 113.5, 112.0, 113.5),  # Day 12
        (113.5, 114.0, 113.5, 114.0),  # Day 13: Test but below anchor

        # Column 4: O pullback to 111
        (114.0, 114.0, 112.0, 112.0),  # Day 14: Fall triggers reversal
        (112.0, 112.0, 111.0, 111.0),  # Day 15

        # Column 5 (4th after anchor): X BREAKS ABOVE anchor high to 117+
        # This is DTB (breaks above col 3) AND breaks above anchor (115)
        (111.0, 112.0, 111.0, 112.0),  # Day 16: Rise triggers reversal
        (112.0, 114.0, 112.0, 114.0),  # Day 17: Pass previous high
        (114.0, 115.5, 114.0, 115.5),  # Day 18: BREAK above anchor!
        (115.5, 117.0, 115.5, 117.0),  # Day 19: AFT BREAKOUT!

        # Follow-through
        (117.0, 119.0, 117.0, 119.0),  # Day 20
        (119.0, 121.0, 119.0, 121.0),  # Day 21
    ]

    base_date = datetime.datetime.now() - datetime.timedelta(days=len(prices))

    for i, (open_price, high, low, close) in enumerate(prices):
        candle_date = base_date + datetime.timedelta(days=i)
        candles.append({
            'timestamp': candle_date,
            'open': open_price,
            'high': high,
            'low': low,
            'close': close,
            'volume': 100000 + (i * 5000)
        })

    return candles

def generate_aft_anchor_breakdown_sell_pattern():
    """
    Generate AFT (Anchor Column Follow Through) Bearish Breakdown pattern.

    Pattern structure:
    1. Tall O anchor column (25+ O symbols) - strong bearish momentum
    2. Consolidation: Price stays above anchor low for several columns
    3. Breakdown: On the 4th column after anchor, O column:
       - Performs Double Bottom Breakdown (breaks below previous O column)
       - AND breaks below anchor low

    With 0.25% box size and 3-box reversal (0.75% move needed to reverse).
    Using gradual multi-day moves to build each column separately.
    """
    candles = []

    # AFT Anchor Breakdown Sell Pattern: O-X-O-X-O (5 columns)
    prices = [
        # Column 1: ANCHOR - Tall O column from 125 to 100 (25-point anchor, ~100 boxes)
        (125.0, 125.0, 123.0, 123.0),  # Day 1
        (123.0, 123.0, 121.0, 121.0),  # Day 2
        (121.0, 121.0, 119.0, 119.0),  # Day 3
        (119.0, 119.0, 117.0, 117.0),  # Day 4
        (117.0, 117.0, 115.0, 115.0),  # Day 5
        (115.0, 115.0, 113.0, 113.0),  # Day 6
        (113.0, 113.0, 111.0, 111.0),  # Day 7
        (111.0, 111.0, 109.0, 109.0),  # Day 8
        (109.0, 109.0, 107.0, 107.0),  # Day 9
        (107.0, 107.0, 105.0, 105.0),  # Day 10
        (105.0, 105.0, 103.0, 103.0),  # Day 11
        (103.0, 103.0, 101.0, 101.0),  # Day 12
        (101.0, 101.0, 100.0, 100.0),  # Day 13: Anchor low at 100

        # Column 2: X recovery to 103
        (100.0, 103.0, 100.0, 103.0),  # Day 14: Rise triggers reversal

        # Column 3: O pullback to 101 (above anchor low)
        (103.0, 103.0, 101.0, 101.0),  # Day 15: First O column in consolidation

        # Column 4: X rise to 104
        (101.0, 104.0, 101.0, 104.0),  # Day 16: X column

        # Column 5: AFT BREAKDOWN - O column breaks below previous O (101) AND anchor low (100)
        (104.0, 104.0, 99.0, 99.0),   # Day 17: Double Bottom Breakdown + AFT
    ]

    base_date = datetime.datetime.now() - datetime.timedelta(days=len(prices))

    for i, (open_price, high, low, close) in enumerate(prices):
        candle_date = base_date + datetime.timedelta(days=i)
        candles.append({
            'timestamp': candle_date,
            'open': open_price,
            'high': high,
            'low': low,
            'close': close,
            'volume': 100000 + (i * 5000)
        })

    return candles

def generate_high_pole_ft_sell_pattern():
    """
    Generate High Pole Follow Through Sell pattern.
    Creates proper P&F structure: High pole (4-column bearish) + Double bottom sell confirmation.

    Target P&F Structure (with 1% box size and 3-box reversal):
    Need to create 8+ columns with distinct price movements
    """
    candles = []

    # Column 1: X rise from 100 to 108 (8 X's) - Strong upward movement
    candles.extend([
        {'timestamp': '2024-01-01T09:30:00Z', 'open': 100.0, 'high': 108.5, 'low': 100.0, 'close': 108.0, 'volume': 100000},
    ])

    # Column 2: O fall from 107 to 95 (12 O's) - High pole (strong bearish move)
    candles.extend([
        {'timestamp': '2024-01-02T09:30:00Z', 'open': 107.0, 'high': 107.0, 'low': 95.0, 'close': 95.5, 'volume': 125000},
    ])

    # Column 3: X rise from 98 to 103 (5 X's) - Partial recovery
    candles.extend([
        {'timestamp': '2024-01-03T09:30:00Z', 'open': 98.0, 'high': 103.5, 'low': 98.0, 'close': 103.0, 'volume': 160000},
    ])

    # Column 4: O fall from 102 to 98 (4 O's) - Completes 4-column pole
    candles.extend([
        {'timestamp': '2024-01-04T09:30:00Z', 'open': 102.0, 'high': 102.0, 'low': 98.0, 'close': 98.5, 'volume': 175000},
    ])

    # Column 5: X rise from 101 to 105 (4 X's) - First recovery attempt
    candles.extend([
        {'timestamp': '2024-01-05T09:30:00Z', 'open': 101.0, 'high': 105.5, 'low': 101.0, 'close': 105.0, 'volume': 185000},
    ])

    # Column 6: O fall to 102 (3 O's) - First bottom
    candles.extend([
        {'timestamp': '2024-01-06T09:30:00Z', 'open': 104.0, 'high': 104.0, 'low': 102.0, 'close': 102.5, 'volume': 195000},
    ])

    # Column 7: X rise from 105 to 108 (3 X's) - Second recovery attempt
    candles.extend([
        {'timestamp': '2024-01-07T09:30:00Z', 'open': 105.0, 'high': 108.5, 'low': 105.0, 'close': 108.0, 'volume': 205000},
    ])

    # Column 8: O fall to 102 (3 O's) - Second bottom (double bottom at same level)
    candles.extend([
        {'timestamp': '2024-01-08T09:30:00Z', 'open': 107.0, 'high': 107.0, 'low': 102.0, 'close': 102.5, 'volume': 215000},
    ])

    # Column 9: X brief recovery to 108 (3 X's) - Third recovery attempt
    candles.extend([
        {'timestamp': '2024-01-09T09:30:00Z', 'open': 108.0, 'high': 111.0, 'low': 108.0, 'close': 110.5, 'volume': 225000},
    ])

    # Column 10: O fall to 107 (3 O's) - Third bottom
    candles.extend([
        {'timestamp': '2024-01-10T09:30:00Z', 'open': 109.0, 'high': 109.0, 'low': 107.0, 'close': 107.5, 'volume': 230000},
    ])

    # Column 11: O break below 96 (7 O's) - Follow-through breakdown >5 boxes below support
    # Support level is 102.21, need to go below 97.21 (more than 5 boxes)
    candles.extend([
        {'timestamp': '2024-01-11T09:30:00Z', 'open': 106.0, 'high': 106.0, 'low': 96.0, 'close': 96.5, 'volume': 235000},
    ])

    return candles

def generate_low_pole_ft_buy_pattern():
    """
    Generate Low Pole Follow Through Buy pattern.
    Creates proper P&F structure: Low pole (4-column bullish) + Double top buy confirmation.

    Target P&F Structure (with 1% box size and 3-box reversal):
    Col 1: O fall from 100 to 95 (5 O's)
    Col 2: X rise from 98 to 106 (8 X's) - Low pole completion
    Col 3: O fall from 105 to 102 (3 O's)
    Col 4: X rise from 105 to 107 (2 X's) - Completes 4-column pole
    Col 5: O fall from 106 to 103 (3 O's) - First decline
    Col 6: X rise to 106 (3 X's) - First top
    Col 7: O fall from 105 to 102 (3 O's) - Second decline
    Col 8: X rise to 105 (3 X's) - Second top (double top)
    Col 9: X break above 108 (4 X's) - Follow-through breakout
    """
    candles = []

    # Column 1: O fall from 100 to 95 (5 O's) - Strong downward movement
    candles.extend([
        {'timestamp': '2024-01-01T09:30:00Z', 'open': 100.0, 'high': 100.0, 'low': 95.0, 'close': 95.5, 'volume': 100000},
    ])

    # Column 2: X rise from 98 to 106 (8 X's) - Low pole (strong bullish move)
    # Need 3-box rise from low to trigger X column
    candles.extend([
        {'timestamp': '2024-01-02T09:30:00Z', 'open': 98.0, 'high': 106.5, 'low': 98.0, 'close': 106.0, 'volume': 125000},
    ])

    # Column 3: O fall from 105 to 102 (3 O's) - Partial decline
    # Need 3-box fall to trigger O column
    candles.extend([
        {'timestamp': '2024-01-03T09:30:00Z', 'open': 105.0, 'high': 105.0, 'low': 102.0, 'close': 102.5, 'volume': 165000},
    ])

    # Column 4: X rise from 105 to 107 (2 X's) - Completes 4-column pole
    candles.extend([
        {'timestamp': '2024-01-04T09:30:00Z', 'open': 105.0, 'high': 107.5, 'low': 105.0, 'close': 107.0, 'volume': 180000},
    ])

    # Column 5: O fall from 106 to 103 (3 O's) - First decline
    candles.extend([
        {'timestamp': '2024-01-05T09:30:00Z', 'open': 106.0, 'high': 106.0, 'low': 103.0, 'close': 103.5, 'volume': 190000},
    ])

    # Column 6: X rise to 105 (3 X's) - First top (lower resistance level)
    candles.extend([
        {'timestamp': '2024-01-06T09:30:00Z', 'open': 104.0, 'high': 105.5, 'low': 104.0, 'close': 105.0, 'volume': 200000},
    ])

    # Column 7: O fall from 104 to 102 (2 O's) - Second decline
    candles.extend([
        {'timestamp': '2024-01-07T09:30:00Z', 'open': 104.0, 'high': 104.0, 'low': 102.0, 'close': 102.5, 'volume': 210000},
    ])

    # Column 8: X rise to 105 (3 X's) - Second top (double top at same level)
    candles.extend([
        {'timestamp': '2024-01-08T09:30:00Z', 'open': 103.0, 'high': 105.5, 'low': 103.0, 'close': 105.0, 'volume': 220000},
    ])

    # Column 9: O fall from 104 to 103 (1 O) - Brief pullback before breakout
    candles.extend([
        {'timestamp': '2024-01-09T09:30:00Z', 'open': 104.0, 'high': 104.0, 'low': 103.0, 'close': 103.5, 'volume': 225000},
    ])

    # Column 10: X break above 111 (8 X's) - Follow-through breakout >5 boxes above resistance
    # Resistance level is now ~105, need to start above 110 (more than 5 boxes)
    # Start the breakout at 111 to ensure first breakout point is already >5 boxes above resistance
    candles.extend([
        {'timestamp': '2024-01-10T09:30:00Z', 'open': 111.0, 'high': 118.0, 'low': 111.0, 'close': 117.5, 'volume': 230000},
    ])

    return candles


def generate_tweezer_bullish_pattern():
    """
    Generate Tweezer Bullish pattern data.

    Pattern structure:
    A = Bearish Anchor column (strong fall) - 14+ O symbols
    B = Base (consolidation between 2-6 columns) - horizontal movement
    C = Bullish Anchor column (strong rally) - 14+ X symbols
    D = Follow-through DTB (Double Top Breakout) - X breaks above C high

    Based on the P&F chart image provided in documentation.
    """
    candles = []

    # Initial setup - start at 100
    candles.extend([
        {'timestamp': '2024-01-01T09:30:00Z', 'open': 100.0, 'high': 100.5, 'low': 99.5, 'close': 100.0, 'volume': 100000},
    ])

    # Column A: Bearish Anchor column (strong fall) - 14+ O symbols
    # Fall from 100 to 85 (15 O symbols)
    candles.extend([
        {'timestamp': '2024-01-02T09:30:00Z', 'open': 100.0, 'high': 100.0, 'low': 85.0, 'close': 85.5, 'volume': 150000},
    ])

    # Column 2: X rise from 88 to 92 (4 X's) - Start of base
    candles.extend([
        {'timestamp': '2024-01-03T09:30:00Z', 'open': 88.0, 'high': 92.0, 'low': 88.0, 'close': 91.5, 'volume': 120000},
    ])

    # Column 3: O fall from 89 to 87 (2 O's) - Base consolidation
    candles.extend([
        {'timestamp': '2024-01-04T09:30:00Z', 'open': 89.0, 'high': 89.0, 'low': 87.0, 'close': 87.5, 'volume': 110000},
    ])

    # Column 4: X rise from 90 to 93 (3 X's) - Base consolidation
    candles.extend([
        {'timestamp': '2024-01-05T09:30:00Z', 'open': 90.0, 'high': 93.0, 'low': 90.0, 'close': 92.5, 'volume': 115000},
    ])

    # Column 5: O fall from 90 to 88 (2 O's) - Base consolidation
    candles.extend([
        {'timestamp': '2024-01-06T09:30:00Z', 'open': 90.0, 'high': 90.0, 'low': 88.0, 'close': 88.5, 'volume': 105000},
    ])

    # Column 6: X rise from 91 to 94 (3 X's) - End of base
    candles.extend([
        {'timestamp': '2024-01-07T09:30:00Z', 'open': 91.0, 'high': 94.0, 'low': 91.0, 'close': 93.5, 'volume': 118000},
    ])

    # Column C: Bullish Anchor column (strong rally) - 14+ X symbols
    # Rise from 97 to 112 (15 X symbols)
    candles.extend([
        {'timestamp': '2024-01-08T09:30:00Z', 'open': 97.0, 'high': 112.0, 'low': 97.0, 'close': 111.5, 'volume': 180000},
    ])

    # Column 8: O fall from 109 to 106 (3 O's) - Small pullback
    candles.extend([
        {'timestamp': '2024-01-09T09:30:00Z', 'open': 109.0, 'high': 109.0, 'low': 106.0, 'close': 106.5, 'volume': 125000},
    ])

    # Column 9: X rise to 111 (5 X's) - First top attempt (double top level)
    candles.extend([
        {'timestamp': '2024-01-10T09:30:00Z', 'open': 109.0, 'high': 111.5, 'low': 109.0, 'close': 111.0, 'volume': 140000},
    ])

    # Column 10: O fall from 108 to 106 (2 O's) - Second pullback
    candles.extend([
        {'timestamp': '2024-01-11T09:30:00Z', 'open': 108.0, 'high': 108.0, 'low': 106.0, 'close': 106.5, 'volume': 130000},
    ])

    # Column 11: X rise to 111 (5 X's) - Second top attempt (double top level)
    candles.extend([
        {'timestamp': '2024-01-12T09:30:00Z', 'open': 109.0, 'high': 111.5, 'low': 109.0, 'close': 111.0, 'volume': 135000},
    ])

    # Column 12: O fall from 108 to 107 (1 O) - Brief pullback
    candles.extend([
        {'timestamp': '2024-01-13T09:30:00Z', 'open': 108.0, 'high': 108.0, 'low': 107.0, 'close': 107.5, 'volume': 125000},
    ])

    # Column D: Follow-through DTB - X breaks above double top resistance (111)
    # Rise from 110 to 116 (6 X's) - Breakout above double top
    candles.extend([
        {'timestamp': '2024-01-14T09:30:00Z', 'open': 110.0, 'high': 116.0, 'low': 110.0, 'close': 115.5, 'volume': 200000},
    ])

    return candles


def generate_tweezer_bearish_pattern():
    """
    Generate Tweezer Bearish pattern data.

    Pattern structure:
    A = Bullish Anchor column (strong rally) - 14+ X symbols
    B = Base (consolidation between 2-6 columns) - horizontal movement
    C = Bearish Anchor column (strong fall) - 14+ O symbols
    D = Follow-through DBB (Double Bottom Breakdown) - O breaks below C low

    Based on the P&F chart image provided in documentation.
    """
    candles = []

    # Initial setup - start at 85
    candles.extend([
        {'timestamp': '2024-01-01T09:30:00Z', 'open': 85.0, 'high': 85.5, 'low': 84.5, 'close': 85.0, 'volume': 100000},
    ])

    # Column A: Bullish Anchor column (strong rally) - 14+ X symbols
    # Rise from 85 to 100 (15 X symbols)
    candles.extend([
        {'timestamp': '2024-01-02T09:30:00Z', 'open': 85.0, 'high': 100.0, 'low': 85.0, 'close': 99.5, 'volume': 150000},
    ])

    # Column 2: O fall from 97 to 93 (4 O's) - Start of base
    candles.extend([
        {'timestamp': '2024-01-03T09:30:00Z', 'open': 97.0, 'high': 97.0, 'low': 93.0, 'close': 93.5, 'volume': 120000},
    ])

    # Column 3: X rise from 96 to 98 (2 X's) - Base consolidation
    candles.extend([
        {'timestamp': '2024-01-04T09:30:00Z', 'open': 96.0, 'high': 98.0, 'low': 96.0, 'close': 97.5, 'volume': 110000},
    ])

    # Column 4: O fall from 95 to 92 (3 O's) - Base consolidation
    candles.extend([
        {'timestamp': '2024-01-05T09:30:00Z', 'open': 95.0, 'high': 95.0, 'low': 92.0, 'close': 92.5, 'volume': 115000},
    ])

    # Column 5: X rise from 95 to 97 (2 X's) - Base consolidation
    candles.extend([
        {'timestamp': '2024-01-06T09:30:00Z', 'open': 95.0, 'high': 97.0, 'low': 95.0, 'close': 96.5, 'volume': 105000},
    ])

    # Column 6: O fall from 94 to 91 (3 O's) - End of base
    candles.extend([
        {'timestamp': '2024-01-07T09:30:00Z', 'open': 94.0, 'high': 94.0, 'low': 91.0, 'close': 91.5, 'volume': 118000},
    ])

    # Column C: Bearish Anchor column (strong fall) - 14+ O symbols
    # Fall from 88 to 73 (15 O symbols) - Keep original range but adjust breakdown logic
    candles.extend([
        {'timestamp': '2024-01-08T09:30:00Z', 'open': 88.0, 'high': 88.0, 'low': 73.0, 'close': 73.5, 'volume': 180000},
    ])

    # Column 8: X rise from 76 to 79 (3 X's) - Small bounce
    candles.extend([
        {'timestamp': '2024-01-09T09:30:00Z', 'open': 76.0, 'high': 79.0, 'low': 76.0, 'close': 78.5, 'volume': 125000},
    ])

    # Column 9: O fall to 74 (5 O's) - First bottom attempt (double bottom level)
    candles.extend([
        {'timestamp': '2024-01-10T09:30:00Z', 'open': 76.0, 'high': 76.0, 'low': 74.0, 'close': 74.5, 'volume': 140000},
    ])

    # Column 10: X rise from 77 to 79 (2 X's) - Second bounce
    candles.extend([
        {'timestamp': '2024-01-11T09:30:00Z', 'open': 77.0, 'high': 79.0, 'low': 77.0, 'close': 78.5, 'volume': 130000},
    ])

    # Column 11: O fall to 74 (5 O's) - Second bottom attempt (double bottom level)
    candles.extend([
        {'timestamp': '2024-01-12T09:30:00Z', 'open': 76.0, 'high': 76.0, 'low': 74.0, 'close': 74.5, 'volume': 135000},
    ])

    # Column 12: X rise from 76 to 77 (1 X) - Brief bounce
    candles.extend([
        {'timestamp': '2024-01-13T09:30:00Z', 'open': 76.0, 'high': 77.0, 'low': 76.0, 'close': 76.5, 'volume': 125000},
    ])

    # Column D: Follow-through DBB - O breaks below double bottom support (74)
    # Fall from 75 to 70 (5 O's) - Breakdown below double bottom
    candles.extend([
        {'timestamp': '2024-01-14T09:30:00Z', 'open': 75.0, 'high': 75.0, 'low': 70.0, 'close': 70.5, 'volume': 200000},
    ])

    return candles

def generate_abc_bullish_pattern():
    """
    Generate ABC Bullish pattern test data.

    ABC Pattern Components:
    A - Anchor column (15+ X symbols showing momentum)
    B - Breakout from 45-degree bearish trendline
    C - Count (vertical target calculation)

    Pattern Structure:
    1. Initial setup with some O columns
    2. Bullish Anchor column (15+ X symbols) - Component A
    3. Consolidation with bearish trendline formation
    4. Bear trap (O column below trendline) - Enhancement
    5. Breakout above bearish trendline - Component B
    6. Vertical count target - Component C
    """
    candles = []

    # Initial setup - some consolidation
    candles.extend([
        {'timestamp': '2024-01-01T09:30:00Z', 'open': 100.0, 'high': 100.0, 'low': 95.0, 'close': 95.5, 'volume': 100000},
    ])

    # Column A: Bullish Anchor column (strong rise) - 15+ X symbols
    # Rise from 98 to 115 (17 X symbols) - Shows momentum
    candles.extend([
        {'timestamp': '2024-01-02T09:30:00Z', 'open': 98.0, 'high': 115.0, 'low': 98.0, 'close': 114.5, 'volume': 200000},
    ])

    # Column 3: O fall from 112 to 108 (4 O's) - Start of consolidation
    candles.extend([
        {'timestamp': '2024-01-03T09:30:00Z', 'open': 112.0, 'high': 112.0, 'low': 108.0, 'close': 108.5, 'volume': 120000},
    ])

    # Column 4: X rise from 111 to 113 (2 X's) - Small bounce
    candles.extend([
        {'timestamp': '2024-01-04T09:30:00Z', 'open': 111.0, 'high': 113.0, 'low': 111.0, 'close': 112.5, 'volume': 110000},
    ])

    # Column 5: O fall from 110 to 106 (4 O's) - Continued consolidation
    candles.extend([
        {'timestamp': '2024-01-05T09:30:00Z', 'open': 110.0, 'high': 110.0, 'low': 106.0, 'close': 106.5, 'volume': 115000},
    ])

    # Column 6: X rise from 109 to 111 (2 X's) - Another bounce
    candles.extend([
        {'timestamp': '2024-01-06T09:30:00Z', 'open': 109.0, 'high': 111.0, 'low': 109.0, 'close': 110.5, 'volume': 105000},
    ])

    # Column 7: O fall from 108 to 104 (4 O's) - Bear trap below trendline
    # This creates the bear trap pattern for enhanced accuracy
    candles.extend([
        {'timestamp': '2024-01-07T09:30:00Z', 'open': 108.0, 'high': 108.0, 'low': 104.0, 'close': 104.5, 'volume': 125000},
    ])

    # Column 8: X rise from 107 to 109 (2 X's) - Recovery from bear trap
    candles.extend([
        {'timestamp': '2024-01-08T09:30:00Z', 'open': 107.0, 'high': 109.0, 'low': 107.0, 'close': 108.5, 'volume': 115000},
    ])

    # Column B: Breakout above 45-degree bearish trendline
    # Rise from 111 to 118 (7 X's) - Breakout above trendline
    # At column 9, trendline level would be approximately: 115 - (7 * 1.15) ≈ 107
    # Breakout above this level confirms ABC pattern
    candles.extend([
        {'timestamp': '2024-01-09T09:30:00Z', 'open': 111.0, 'high': 118.0, 'low': 111.0, 'close': 117.5, 'volume': 180000},
    ])

    return candles

def generate_abc_bearish_pattern():
    """
    Generate ABC Bearish pattern test data.

    ABC Bearish Pattern Components:
    A - Anchor column (15+ O symbols showing downward momentum)
    B - Breakdown below 45-degree bullish trendline
    C - Count (vertical target calculation)

    Pattern Structure:
    1. Initial setup with some X columns
    2. Bearish Anchor column (15+ O symbols) - Component A
    3. Consolidation with bullish trendline formation
    4. Bull trap (X column above trendline) - Enhancement
    5. Breakdown below bullish trendline - Component B
    6. Vertical count target - Component C
    """
    candles = []

    # Initial setup - some consolidation
    candles.extend([
        {'timestamp': '2024-01-01T09:30:00Z', 'open': 100.0, 'high': 105.0, 'low': 100.0, 'close': 104.5, 'volume': 100000},
    ])

    # Column A: Bearish Anchor column (strong fall) - 15+ O symbols
    # Fall from 102 to 85 (17 O symbols) - Shows downward momentum
    candles.extend([
        {'timestamp': '2024-01-02T09:30:00Z', 'open': 102.0, 'high': 102.0, 'low': 85.0, 'close': 85.5, 'volume': 200000},
    ])

    # Column 3: X rise from 88 to 92 (4 X's) - Start of consolidation
    candles.extend([
        {'timestamp': '2024-01-03T09:30:00Z', 'open': 88.0, 'high': 92.0, 'low': 88.0, 'close': 91.5, 'volume': 120000},
    ])

    # Column 4: O fall from 89 to 87 (2 O's) - Small pullback
    candles.extend([
        {'timestamp': '2024-01-04T09:30:00Z', 'open': 89.0, 'high': 89.0, 'low': 87.0, 'close': 87.5, 'volume': 110000},
    ])

    # Column 5: X rise from 90 to 94 (4 X's) - Continued consolidation
    candles.extend([
        {'timestamp': '2024-01-05T09:30:00Z', 'open': 90.0, 'high': 94.0, 'low': 90.0, 'close': 93.5, 'volume': 115000},
    ])

    # Column 6: O fall from 91 to 89 (2 O's) - Another pullback
    candles.extend([
        {'timestamp': '2024-01-06T09:30:00Z', 'open': 91.0, 'high': 91.0, 'low': 89.0, 'close': 89.5, 'volume': 105000},
    ])

    # Column 7: X rise from 92 to 96 (4 X's) - Bull trap above trendline
    # This creates the bull trap pattern for enhanced accuracy
    candles.extend([
        {'timestamp': '2024-01-07T09:30:00Z', 'open': 92.0, 'high': 96.0, 'low': 92.0, 'close': 95.5, 'volume': 125000},
    ])

    # Column 8: O fall from 93 to 91 (2 O's) - Pullback from bull trap
    candles.extend([
        {'timestamp': '2024-01-08T09:30:00Z', 'open': 93.0, 'high': 93.0, 'low': 91.0, 'close': 91.5, 'volume': 115000},
    ])

    # Column B: Breakdown below 45-degree bullish trendline
    # Fall from 89 to 82 (7 O's) - Breakdown below trendline
    # At column 9, trendline level would be approximately: 85 + (7 * 0.85) ≈ 91
    # Breakdown below this level confirms ABC bearish pattern
    candles.extend([
        {'timestamp': '2024-01-09T09:30:00Z', 'open': 89.0, 'high': 89.0, 'low': 82.0, 'close': 82.5, 'volume': 180000},
    ])

    return candles


# Pattern definitions for testing
TEST_PATTERNS = {
    'bullish_breakout': {
        'name': 'Double Top Buy with Follow Through',
        'description': 'Price breaks above double top resistance with strong follow-through momentum',
        'expected_signal': 'BUY',
        'data_generator': generate_bullish_breakout_pattern
    },
    'bearish_breakdown': {
        'name': 'Double Bottom Sell with Follow Through',
        'description': 'Price breaks below double bottom support with strong follow-through momentum',
        'expected_signal': 'SELL',
        'data_generator': generate_bearish_breakdown_pattern
    },
    'triple_top': {
        'name': 'Triple Top Buy with Follow Through',
        'description': 'Price breaks above triple top resistance after three failed attempts with strong follow-through momentum',
        'expected_signal': 'BUY',
        'data_generator': generate_triple_top_pattern
    },

    'triple_bottom': {
        'name': 'Triple Bottom Sell with Follow Through',
        'description': 'Price breaks below triple bottom support after three failed attempts with strong follow-through momentum',
        'expected_signal': 'SELL',
        'data_generator': generate_triple_bottom_pattern
    },
    'quadruple_top': {
        'name': 'Quadruple Top Buy with Follow Through',
        'description': 'Price breaks above quadruple top resistance after four failed attempts with ultimate follow-through momentum',
        'expected_signal': 'BUY',
        'data_generator': generate_quadruple_top_pattern
    },
    'quadruple_bottom': {
        'name': 'Quadruple Bottom Sell with Follow Through',
        'description': 'Price breaks below quadruple bottom support after four failed attempts with ultimate follow-through momentum',
        'expected_signal': 'SELL',
        'data_generator': generate_quadruple_bottom_pattern
    },


    # New EMA-validated and advanced patterns
    'turtle_breakout_ft_buy': {
        'name': 'Turtle Breakout FT Buy',
        'description': 'Turtle breakout (5-column high) followed by double top buy pattern - confirms bullish momentum',
        'expected_signal': 'BUY',
        'data_generator': generate_turtle_breakout_ft_buy_pattern
    },
    'turtle_breakout_ft_sell': {
        'name': 'Turtle Breakout FT Sell',
        'description': 'Turtle breakout (5-column low) followed by double bottom sell pattern - confirms bearish momentum',
        'expected_signal': 'SELL',
        'data_generator': generate_turtle_breakout_ft_sell_pattern
    },

    'catapult_buy': {
        'name': 'Catapult Buy',
        'description': 'Triple bottom sell + double bottom sell patterns, then X column enters territory and breaks above resistance creating bullish catapult signal',
        'expected_signal': 'BUY',
        'data_generator': generate_catapult_buy_pattern
    },
    'catapult_sell': {
        'name': 'Catapult Sell',
        'description': 'Triple top buy + double top buy patterns, then O column enters territory and breaks below support creating bearish catapult signal',
        'expected_signal': 'SELL',
        'data_generator': generate_catapult_sell_pattern
    },
    'pole_follow_through_buy': {
        'name': '100% Pole Follow Through Buy',
        'description': '100% pole pattern followed by double top buy pattern creating six-column formation with breakout above resistance',
        'expected_signal': 'BUY',
        'data_generator': generate_pole_follow_through_buy_pattern
    },
    'pole_follow_through_sell': {
        'name': '100% Pole Follow Through Sell',
        'description': '100% pole pattern followed by double bottom sell pattern creating six-column formation with breakdown below support',
        'expected_signal': 'SELL',
        'data_generator': generate_pole_follow_through_sell_pattern
    },
    'aft_anchor_breakout_buy': {
        'name': 'AFT Anchor Breakout Buy',
        'description': 'Anchor Column Follow Through - tall X anchor column followed by consolidation within 8 columns, then breakout above anchor high',
        'expected_signal': 'BUY',
        'data_generator': generate_aft_anchor_breakout_buy_pattern
    },
    'aft_anchor_breakdown_sell': {
        'name': 'AFT Anchor Breakdown Sell',
        'description': 'Anchor Column Follow Through - tall O anchor column (25+ boxes) followed by consolidation, then Double Bottom Breakdown + anchor break on 4th column',
        'expected_signal': 'SELL',
        'data_generator': generate_aft_anchor_breakdown_sell_pattern
    },
    'high_pole_ft_sell': {
        'name': 'High Pole Follow Through Sell',
        'description': 'High pole (4-column bearish pattern) followed by double bottom sell pattern - confirms bearish momentum after supply shock',
        'expected_signal': 'SELL',
        'data_generator': generate_high_pole_ft_sell_pattern
    },
    'low_pole_ft_buy': {
        'name': 'Low Pole Follow Through Buy',
        'description': 'Low pole (4-column bullish pattern) followed by double top buy pattern - confirms bullish momentum after demand shock',
        'expected_signal': 'BUY',
        'data_generator': generate_low_pole_ft_buy_pattern
    },
    'tweezer_bullish': {
        'name': 'Tweezer Bullish',
        'description': 'Horizontal accumulation pattern between bearish and bullish anchor columns with follow-through DTB breakout',
        'expected_signal': 'BUY',
        'data_generator': generate_tweezer_bullish_pattern
    },
    'tweezer_bearish': {
        'name': 'Tweezer Bearish',
        'description': 'Horizontal distribution pattern between bullish and bearish anchor columns with follow-through DBB breakdown',
        'expected_signal': 'SELL',
        'data_generator': generate_tweezer_bearish_pattern
    },
    'abc_bullish': {
        'name': 'ABC Bullish',
        'description': 'Anchor-Breakout-Count momentum pattern with 45-degree bearish trendline breakout after bullish anchor column',
        'expected_signal': 'BUY',
        'data_generator': generate_abc_bullish_pattern
    },
    'abc_bearish': {
        'name': 'ABC Bearish',
        'description': 'Anchor-Breakdown-Count momentum pattern with 45-degree bullish trendline breakdown after bearish anchor column',
        'expected_signal': 'SELL',
        'data_generator': generate_abc_bearish_pattern
    },
    'ziddi_bulls': {
        'name': 'Ziddi Bulls (BUY)',
        'description': 'Stubborn bulls pattern - Failed double bottom sells followed by double top buy breakout. Bulls not letting price fall!',
        'expected_signal': 'BUY',
        'data_generator': generate_ziddi_bulls_pattern
    },
    'ziddi_bears': {
        'name': 'Ziddi Bears (SELL)',
        'description': 'Stubborn bears pattern - Failed double top buys followed by double bottom sell breakdown. Bears not letting price rise!',
        'expected_signal': 'SELL',
        'data_generator': generate_ziddi_bears_pattern
    }
}

def analyze_alert_triggers(highs: list, lows: list, box_pct: float, reversal: int, pattern_name: str, closes: list = None) -> dict:
    """
    Analyze where alert triggers would occur in the pattern using the new pattern detector.
    This ensures alerts fire only once when patterns are first identified.

    Returns:
        dict: Alert trigger analysis including one-time trigger points
    """
    from app.charts import _calculate_pnf_points
    from app.pattern_detector import PatternDetector

    # Calculate P&F points
    x_coords, y_coords, pnf_symbols = _calculate_pnf_points(highs, lows, box_pct, reversal)

    # Use the pattern detector to find one-time alerts with EMA validation
    detector = PatternDetector()

    # Pass closing prices for EMA calculation if available
    price_data = closes if closes else None
    alert_triggers = detector.analyze_pattern_formation(x_coords, y_coords, pnf_symbols, price_data, box_pct)

    # Convert to the expected format
    triggers = []
    for alert in alert_triggers:
        triggers.append({
            'column': alert.column,
            'price': alert.price,
            'type': f"{alert.pattern_type.value.replace('_', ' ').title()} Alert",
            'signal': alert.alert_type.value,
            'description': alert.trigger_reason,
            'is_first_occurrence': alert.is_first_occurrence
        })

    # Add pattern state information
    pattern_states = {}
    for pattern_type, state in detector.pattern_states.items():
        # Check alert_fired instead of is_confirmed (pattern detector sets alert_fired, not is_confirmed)
        if state.alert_fired:
            pattern_states[pattern_type.value] = {
                'confirmed': True,  # Mark as confirmed if alert was fired
                'confirmation_price': state.confirmation_price if state.confirmation_price else 0.0,
                'confirmation_column': state.confirmation_column if state.confirmation_column else 0,
                'alert_fired': state.alert_fired
            }

    return {
        'triggers': triggers,
        'pattern_states': pattern_states,
        'total_columns': len(set(x_coords)),
        'pattern_name': pattern_name,
        'box_size': box_pct,
        'reversal': reversal,
        'alert_count': len(triggers),
        'unique_patterns_detected': len([s for s in pattern_states.values() if s['confirmed']])
    }

def generate_test_chart_html(pattern_name: str, box_pct: float = 0.0025, reversal: int = 3) -> str:
    """
    Generate a test P&F chart HTML for a specific pattern with alert trigger points.

    Args:
        pattern_name: Name of the pattern to test
        box_pct: Box size percentage (IGNORED - test patterns always use 0.25%)
        reversal: Reversal amount (default: 3-box reversal)

    Note:
        Test patterns are designed specifically for 0.25% box size and 3-box reversal.
        The box_pct parameter is ignored to ensure patterns display correctly.
        For testing different box sizes, use real stock data instead.
    """
    import plotly.graph_objects as go
    from app.charts import _calculate_pnf_points, _add_anchor_points_to_chart

    if pattern_name not in TEST_PATTERNS:
        return f"<h3>Pattern '{pattern_name}' not found</h3>"

    # IMPORTANT: Test patterns are designed for 0.25% box size only
    # Override any user-selected box size to ensure patterns work correctly
    PATTERN_BOX_SIZE = 0.0025  # 0.25% - hardcoded for test patterns
    PATTERN_REVERSAL = 3       # 3-box reversal - hardcoded for test patterns

    pattern_info = TEST_PATTERNS[pattern_name]

    # Call generator without parameters (all patterns use fixed 0.25% box size)
    candles = pattern_info['data_generator']()

    # Extract highs, lows, and closes
    highs = [candle['high'] for candle in candles]
    lows = [candle['low'] for candle in candles]
    closes = [candle['close'] for candle in candles]

    # Calculate P&F points using hardcoded pattern box size
    x_coords, y_coords, pnf_symbols = _calculate_pnf_points(highs, lows, PATTERN_BOX_SIZE, PATTERN_REVERSAL)

    # Analyze alert triggers with EMA validation using hardcoded pattern box size
    trigger_analysis = analyze_alert_triggers(highs, lows, PATTERN_BOX_SIZE, PATTERN_REVERSAL, pattern_name, closes)

    # Separate X's and O's for plotting
    x_x = [x for x, s in zip(x_coords, pnf_symbols) if s == 'X']
    y_x = [y for y, s in zip(y_coords, pnf_symbols) if s == 'X']
    x_o = [x for x, s in zip(x_coords, pnf_symbols) if s == 'O']
    y_o = [y for y, s in zip(y_coords, pnf_symbols) if s == 'O']

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x_x, y=y_x, mode='text', text='X', name='Uptrend (X)',
                            textfont=dict(color='#00b069', size=12)))
    fig.add_trace(go.Scatter(x=x_o, y=y_o, mode='text', text='O', name='Downtrend (O)',
                            textfont=dict(color='#fe3d62', size=12)))

    # Add alert trigger points
    trigger_x = [t['column'] for t in trigger_analysis['triggers']]
    trigger_y = [t['price'] for t in trigger_analysis['triggers']]
    trigger_text = [f"🚨 {t['signal']}" for t in trigger_analysis['triggers']]
    trigger_colors = ['#FFD700' if t['signal'] == 'BUY' else '#FF6B6B' for t in trigger_analysis['triggers']]

    if trigger_x:
        fig.add_trace(go.Scatter(
            x=trigger_x, y=trigger_y,
            mode='markers+text',
            text=trigger_text,
            textposition="top center",
            marker=dict(
                size=15,
                color=trigger_colors,
                symbol='star',
                line=dict(width=2, color='white')
            ),
            name='Alert Triggers',
            textfont=dict(size=10, color='white')
        ))

    # Add anchor points to test chart
    if x_coords and y_coords:
        _add_anchor_points_to_chart(fig, x_coords, y_coords, pnf_symbols, PATTERN_BOX_SIZE)

    # Create title with pattern info and one-time trigger count
    trigger_count = trigger_analysis['alert_count']
    unique_patterns = trigger_analysis['unique_patterns_detected']
    title = f'TEST: {pattern_info["name"]} - Expected Signal: {pattern_info["expected_signal"]} ({trigger_count} One-Time Alerts)'
    subtitle = f'{pattern_info["description"]}<br>Box Size: {PATTERN_BOX_SIZE*100:.2f}% (FIXED), Reversal: {PATTERN_REVERSAL} | Patterns Detected: {unique_patterns}'

    # Calculate appropriate Y-axis range from actual data
    if y_coords:
        y_min = min(y_coords)
        y_max = max(y_coords)
        y_padding = (y_max - y_min) * 0.1  # 10% padding
        y_range = [y_min - y_padding, y_max + y_padding]
    else:
        y_range = None

    fig.update_layout(
        title=f'{title}<br><sub>{subtitle}</sub>',
        template='plotly_dark',
        xaxis_title="Column",
        yaxis_title="Price",
        xaxis=dict(showgrid=False, tickmode='linear', tick0=1, dtick=1),
        yaxis=dict(
            tickformat='.2f',
            range=y_range,  # Set explicit range based on data
            showgrid=True,
            gridcolor='rgba(128, 128, 128, 0.2)'
        ),
        showlegend=True,
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
        margin=dict(l=20, r=20, t=80, b=20),
        plot_bgcolor="#111111",
        paper_bgcolor="#111111",
        font_color="white",
        height=600
    )

    # Add one-time trigger analysis as annotations
    if trigger_analysis['triggers']:
        trigger_info = "<br>".join([
            f"Column {t['column']}: {t['type']} - {t['signal']} at {t['price']:.2f}"
            for t in trigger_analysis['triggers']
        ])

        # Add pattern state information
        pattern_info_text = ""
        if trigger_analysis['pattern_states']:
            confirmed_patterns = [
                f"{ptype.replace('_', ' ').title()}: ✅ at {pstate['confirmation_price']:.2f}"
                for ptype, pstate in trigger_analysis['pattern_states'].items()
                if pstate['confirmed']
            ]
            if confirmed_patterns:
                pattern_info_text = f"<br><b>Confirmed Patterns:</b><br>{'<br>'.join(confirmed_patterns)}"

        fig.add_annotation(
            text=f"<b>One-Time Alert Triggers:</b><br>{trigger_info}{pattern_info_text}",
            xref="paper", yref="paper",
            x=0.02, y=0.02,
            xanchor="left", yanchor="bottom",
            showarrow=False,
            font=dict(size=10, color="white"),
            bgcolor="rgba(0,0,0,0.7)",
            bordercolor="white",
            borderwidth=1
        )

    return fig.to_html(full_html=False, include_plotlyjs='cdn')
