#!/usr/bin/env python3
"""
Debug why low_pole_ft_buy specific alert is not triggering.
"""

from app.test_patterns import generate_low_pole_ft_buy_pattern
from app.charts import _calculate_pnf_points
from app.pattern_detector import PatternDetector

def debug_low_pole_specific():
    print('🔍 Debugging Low Pole FT Buy Specific Alert...')
    candles = generate_low_pole_ft_buy_pattern()
    highs = [c['high'] for c in candles]
    lows = [c['low'] for c in candles]
    closes = [c['close'] for c in candles]

    x_coords, y_coords, symbols = _calculate_pnf_points(highs, lows, 0.01, 3)
    print(f'  P&F Data: {len(symbols)} symbols, {len(set(x_coords))} columns')
    
    all_columns = sorted(set(x_coords))
    latest_column = max(all_columns)
    print(f'  Latest column: {latest_column}')
    
    # Check latest column symbol type
    latest_column_symbols = []
    for i in range(len(symbols)):
        if x_coords[i] == latest_column:
            latest_column_symbols.append((symbols[i], y_coords[i]))
    
    print(f'  Latest column symbols: {latest_column_symbols}')
    latest_symbol_type = latest_column_symbols[0][0] if latest_column_symbols else None
    print(f'  Latest column type: {latest_symbol_type}')
    
    # The low_pole_ft_buy pattern should only trigger on X columns
    if latest_symbol_type != 'X':
        print(f'  ❌ Latest column is not X - low_pole_ft_buy requires X column')
        return
    
    # Check X columns after pole
    pole_column = 4
    x_columns_after_pole = {}
    for i in range(len(symbols)):
        if (symbols[i] == 'X' and
            x_coords[i] > pole_column and
            x_coords[i] <= latest_column):
            col = x_coords[i]
            if col not in x_columns_after_pole or y_coords[i] > x_columns_after_pole[col]:
                x_columns_after_pole[col] = y_coords[i]
    
    print(f'  X columns after pole: {x_columns_after_pole}')
    
    # Get X column highs before current
    x_column_highs_before_current = []
    for col, high in x_columns_after_pole.items():
        if col < latest_column:
            x_column_highs_before_current.append(high)
    
    print(f'  X column highs before current: {x_column_highs_before_current}')
    
    if len(x_column_highs_before_current) >= 2:
        resistance_level = max(x_column_highs_before_current)
        current_price = x_columns_after_pole[latest_column]
        box_difference = current_price - resistance_level
        
        print(f'  Resistance level: {resistance_level:.2f}')
        print(f'  Current price: {current_price:.2f}')
        print(f'  Box difference: {box_difference:.2f}')
        print(f'  Meets 5+ box requirement: {box_difference > 5}')
        print(f'  Price > resistance: {current_price > resistance_level}')
        
        # Check similar highs for double top
        tolerance = resistance_level * 0.005
        similar_highs = [h for h in x_column_highs_before_current if abs(h - resistance_level) <= tolerance]
        print(f'  Similar highs: {similar_highs}')
        print(f'  Double top formed: {len(similar_highs) >= 2}')
        
        # All conditions for low_pole_ft_buy
        print(f'\n  ✅ All conditions check:')
        print(f'    - Latest column is X: {latest_symbol_type == "X"}')
        print(f'    - Double top formed: {len(similar_highs) >= 2}')
        print(f'    - More than 5 boxes: {box_difference > 5}')
        print(f'    - Price > resistance: {current_price > resistance_level}')
    
    # Test pattern detection
    detector = PatternDetector()
    alerts = detector.analyze_pattern_formation(x_coords, y_coords, symbols, closes)
    
    print(f'\n  Alerts generated: {len(alerts)}')
    for alert in alerts:
        print(f'    - {alert.pattern_type.value}: {alert.trigger_reason}')

if __name__ == "__main__":
    debug_low_pole_specific()
