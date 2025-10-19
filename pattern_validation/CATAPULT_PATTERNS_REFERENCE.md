# Catapult Patterns Reference

This document explains the Catapult Buy and Catapult Sell patterns based on the provided visual references and their implementation in the trading system.

## Overview

Catapult patterns are advanced Point & Figure (P&F) chart formations that combine multiple pattern types to create powerful trading signals. They are considered traditional P&F patterns that are very difficult to find in real market conditions.

## Catapult Buy Pattern

### Visual Structure (from provided image)
- **Formation**: Triple top buy pattern followed by double top buy pattern
- **Pattern Sequence**: X-O-X-O-X (triple top) + X-O-X (double top) 
- **Signal Trigger**: Final O column breaks below the breakdown level of the triple top buy pattern
- **Expected Signal**: BUY (bullish catapult)

### Key Characteristics
1. **Triple Top Buy Formation**: Three X columns reaching the same resistance level with O columns in between
2. **Double Top Buy Formation**: Two additional X columns at the same resistance level
3. **Catapult Trigger**: The final O column breaks below the established breakdown level
4. **Signal Type**: Bullish - despite the breakdown, this creates a buy signal due to the catapult effect

### Trading Logic
The pattern is counterintuitive - when the O column breaks below the breakdown level after multiple failed attempts to break higher, it creates a "catapult" effect that often leads to a strong bullish reversal.

## Catapult Sell Pattern

### Visual Structure (from provided image)
- **Formation**: Triple bottom sell pattern followed by double bottom sell pattern
- **Pattern Sequence**: O-X-O-X-O (triple bottom) + O-X-O (double bottom)
- **Signal Trigger**: Final X column breaks above the breakout level of the triple bottom sell pattern
- **Expected Signal**: SELL (bearish catapult)

### Key Characteristics
1. **Triple Bottom Sell Formation**: Three O columns reaching the same support level with X columns in between
2. **Double Bottom Sell Formation**: Two additional O columns at the same support level
3. **Catapult Trigger**: The final X column breaks above the established breakout level
4. **Signal Type**: Bearish - despite the breakout, this creates a sell signal due to the catapult effect

### Trading Logic
Similar to the buy pattern, this is counterintuitive - when the X column breaks above the breakout level after multiple failed attempts to break lower, it creates a "catapult" effect that often leads to a strong bearish reversal.

## Implementation Details

### Pattern Detection
- Both patterns are implemented in `app/test_patterns.py`
- Each pattern generates 30 days of dummy price data
- The patterns create the exact P&F formations shown in the reference images
- Pattern detection is handled by the `PatternDetector` class

### Test Chart Integration
- Available in the test charts dropdown as "Catapult Buy" and "Catapult Sell"
- Can be tested with different box sizes and reversal amounts
- Includes pattern analysis and trigger point identification

### Alert Generation
- Catapult Buy: Triggers when O column breaks below breakdown level
- Catapult Sell: Triggers when X column breaks above breakout level
- Alerts are generated only once when the pattern is first identified

## Usage in Trading System

### Test Charts
1. Navigate to `/test-charts`
2. Select "Catapult Buy" or "Catapult Sell" from the pattern dropdown
3. Use dummy data to see the ideal pattern formation
4. Switch to real data to look for similar formations in actual stocks

### Pattern Recognition
- Look for the specific sequence of triple + double formations
- Identify the key breakout/breakdown levels
- Wait for the catapult trigger (opposite direction break)
- Confirm with EMA and other technical indicators

## Important Notes

1. **Rarity**: These are traditional P&F patterns that are very difficult to find in real markets
2. **Counterintuitive**: The signal direction is opposite to the immediate price movement
3. **Validation**: Always confirm with additional technical analysis
4. **Risk Management**: Use appropriate stop-losses due to the counterintuitive nature

## Pattern Validation

The patterns have been tested and validated to ensure:
- Correct P&F point generation
- Proper pattern detection
- Accurate alert triggering
- Visual representation matches reference images

Both catapult patterns are now fully integrated into the trading system and available for testing and real-time detection.
