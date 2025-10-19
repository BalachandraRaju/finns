# Pattern Test Suite

This directory contains comprehensive unit test cases for all test patterns with 1% box size and 3-box reversal. These tests ensure code stability and prevent regressions when making changes to the pattern system.

## Test Requirements

- **Box Size**: 1% (0.01)
- **Reversal**: 3 boxes
- **Independence**: Tests work independently of the main application
- **Comprehensive Coverage**: All patterns tested for multiple aspects

## Test Files

### 1. `test_all_patterns_comprehensive.py`
**Main comprehensive test suite covering:**
- Pattern data generation validation
- P&F calculation with 1% box size and 3-box reversal
- Anchor points integration
- Pattern detection and alert generation
- Chart generation compatibility
- Data consistency across multiple generations

### 2. `test_pattern_alerts.py`
**Alert generation testing:**
- Bullish patterns generate BUY alerts
- Bearish patterns generate SELL alerts
- Alert trigger reasons are meaningful
- Alert prices are within valid ranges
- No duplicate alerts generated

### 3. `test_anchor_points_patterns.py`
**Anchor points integration testing:**
- Anchor points calculation for all patterns
- Anchor zone creation for complex patterns
- Price level validation
- Column separation requirements
- Box counting accuracy

### 4. `test_chart_generation.py`
**Chart generation testing:**
- P&F calculation for all patterns
- HTML chart generation
- Chart data structure validation
- Coordinate validity for plotting
- Symbol alternation patterns

### 5. `run_all_tests.py`
**Master test runner:**
- Runs all test suites
- Provides comprehensive results summary
- Tracks performance metrics
- Gives deployment recommendations

## Tested Patterns

The test suite covers all patterns in `TEST_PATTERNS`:

### Bullish Patterns (BUY signals)
- `bullish_breakout` - Double Top Buy with Follow Through
- `triple_top` - Triple Top Buy with Follow Through
- `quadruple_top` - Quadruple Top Buy with Follow Through
- `turtle_breakout_ft_buy` - Turtle Breakout FT Buy
- `catapult_buy` - Catapult Buy
- `pole_follow_through_buy` - 100% Pole Follow Through Buy
- `aft_anchor_breakout_buy` - AFT Anchor Breakout Buy
- `low_pole_ft_buy` - Low Pole Follow Through Buy
- `tweezer_bullish` - Tweezer Bullish
- `abc_bullish` - ABC Bullish

### Bearish Patterns (SELL signals)
- `bearish_breakdown` - Double Bottom Sell with Follow Through
- `triple_bottom` - Triple Bottom Sell with Follow Through
- `quadruple_bottom` - Quadruple Bottom Sell with Follow Through
- `turtle_breakout_ft_sell` - Turtle Breakout FT Sell
- `catapult_sell` - Catapult Sell
- `pole_follow_through_sell` - 100% Pole Follow Through Sell
- `aft_anchor_breakdown_sell` - AFT Anchor Breakdown Sell
- `high_pole_ft_sell` - High Pole Follow Through Sell
- `tweezer_bearish` - Tweezer Bearish
- `abc_bearish` - ABC Bearish

## Running Tests

### Run All Tests
```bash
cd test
python run_all_tests.py
```

### Run Individual Test Suites
```bash
# Comprehensive tests
python test_all_patterns_comprehensive.py

# Alert tests
python test_pattern_alerts.py

# Anchor points tests
python test_anchor_points_patterns.py

# Chart generation tests
python test_chart_generation.py
```

### Run Specific Pattern Tests
```bash
# Using unittest
python -m unittest test_all_patterns_comprehensive.TestAllPatternsComprehensive.test_pattern_data_generation

# Using pytest (if installed)
pytest test_all_patterns_comprehensive.py::TestAllPatternsComprehensive::test_pattern_data_generation
```

## Test Results Interpretation

### ✅ All Tests Pass
- All patterns work correctly with 1% box size and 3-box reversal
- Anchor points integration is working
- Pattern detection is functioning
- Chart generation is compatible
- Alert generation is working
- Code is stable and ready for production

### ❌ Some Tests Fail
- Issues detected in pattern system
- Fix failing tests before deployment
- Review test output for specific issues
- Re-run tests after fixes

## Test Coverage

Each pattern is tested for:

1. **Data Generation**
   - Valid candle structure (OHLC, timestamp, volume)
   - Proper OHLC relationships (low ≤ open,close ≤ high)
   - Minimum candle count requirements
   - Data consistency across generations

2. **P&F Calculation**
   - Valid coordinate arrays
   - Proper symbol generation (X/O)
   - Minimum point requirements
   - Coordinate validity

3. **Anchor Points**
   - Anchor point calculation
   - Zone creation for complex patterns
   - Price level validation
   - Column separation compliance
   - Box counting accuracy

4. **Pattern Detection**
   - Alert generation
   - Correct alert types (BUY/SELL)
   - Valid trigger reasons
   - Price range validation
   - No duplicate alerts

5. **Chart Generation**
   - HTML generation
   - Data structure validation
   - Coordinate plotting validity
   - Symbol alternation patterns

## Adding New Patterns

When adding new patterns to `TEST_PATTERNS`:

1. **Add to pattern mappings** in `test_all_patterns_comprehensive.py`
2. **Update expected patterns** in test files
3. **Run full test suite** to ensure compatibility
4. **Verify all tests pass** before deployment

## Continuous Integration

These tests should be run:
- Before any code deployment
- After modifying pattern generators
- After changing P&F calculation logic
- After updating anchor points algorithm
- After modifying chart generation
- Before major releases

## Performance Benchmarks

Typical test execution times:
- Comprehensive tests: ~30-60 seconds
- Alert tests: ~20-40 seconds
- Anchor points tests: ~25-45 seconds
- Chart generation tests: ~15-30 seconds
- **Total suite**: ~90-180 seconds

## Troubleshooting

### Common Issues

1. **Import Errors**
   - Ensure you're running from the test directory
   - Check that project root is in Python path

2. **Pattern Not Found**
   - Verify pattern exists in `TEST_PATTERNS`
   - Check pattern key spelling

3. **P&F Calculation Fails**
   - Check candle data validity
   - Verify box size and reversal parameters

4. **Anchor Points Errors**
   - Ensure sufficient P&F points generated
   - Check column separation requirements

### Debug Mode

For detailed debugging, modify test files to add:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Maintenance

- **Review tests quarterly** for new pattern additions
- **Update expected results** when algorithms improve
- **Add performance benchmarks** for regression testing
- **Document any test modifications** in commit messages

---

**Remember**: These tests are your safety net. Always run them before making changes to ensure system stability!
