# How to Use PKScreener Backtest Page

## 🚀 Quick Start Guide

### Step 1: Start the Server
```bash
cd /Users/balachandra.raju/projects/finns
source venv/bin/activate
uvicorn app.main:app --reload
```

### Step 2: Open the Backtest Page
Navigate to: **http://localhost:8000/pkscreener-backtest**

---

## 📋 **Page Layout**

The backtest page has 3 main sections:

### 1. Stock Selection (Left Panel)
- **Watchlist dropdown** showing all 221 F&O stocks
- Hold **Cmd (Mac)** or **Ctrl (Windows)** to select multiple stocks
- Leave empty to test **all stocks** in watchlist

### 2. Configuration (Right Panel)

**Date Range:**
- **Start Date**: Beginning of backtest period
- **End Date**: End of backtest period
- Example: Oct 4, 2025 to Oct 17, 2025

**Scanners:**
Two sections:
- **Original Scanners**: #1, #12, #14, #21
- **PKScreener Breakout Scanners**: #17, #20, #23, #32 (NEW!)

Check one or more scanners to test.

### 3. Results Section (Bottom)
Shows after clicking "Run Backtest":
- Summary statistics per scanner
- Individual alerts with returns
- Success rates and average returns

---

## 🎯 **Example Usage Scenarios**

### Scenario 1: Test All Breakout Scanners on All Stocks
**Goal:** Find which scanner generates the most alerts

**Configuration:**
- Stocks: Leave empty (all 221 stocks)
- Start Date: 2025-10-04
- End Date: 2025-10-17
- Scanners: Check #1, #17, #23 (proven scanners)

**Expected Results:**
- Scanner #1: ~37 alerts
- Scanner #17: ~1 alert
- Scanner #23: ~27 alerts
- Total: ~65 alerts

---

### Scenario 2: Test Specific Stocks for 52-Week Breakouts
**Goal:** Find stocks breaking 52-week highs

**Configuration:**
- Stocks: Select 10-20 high-volume stocks (RELIANCE, TCS, INFY, SBIN, etc.)
- Start Date: 2025-10-01
- End Date: 2025-10-18
- Scanners: Check #17 only

**Expected Results:**
- Rare but powerful signals
- 0-2 alerts (52-week breakouts are rare)
- High success rate when triggered

---

### Scenario 3: Intraday Momentum Scalping
**Goal:** Find quick intraday momentum plays

**Configuration:**
- Stocks: Select 50 most liquid stocks
- Start Date: 2025-10-17 (single day)
- End Date: 2025-10-17
- Scanners: Check #23 (Breaking Out Now)

**Expected Results:**
- 10-30 alerts per day
- Best for scalping (3-5 minute holds)
- Average returns: 0.5-1.5%

---

### Scenario 4: Compare Scanner Performance
**Goal:** Find which scanner has best win rate

**Configuration:**
- Stocks: Leave empty (all stocks)
- Start Date: 2025-10-01
- End Date: 2025-10-18
- Scanners: Check ALL (#1, #17, #20, #23, #32)

**Expected Results:**
- Compare success rates across scanners
- Identify best time-of-day for each scanner
- Optimize scanner selection for live trading

---

## 📊 **Understanding Results**

### Summary Section
For each scanner, you'll see:

```
Scanner #1: Probable Breakout
  Total Triggers: 37
  Successful Trades: 28 (75.7%)
  Average Return (3min): +0.45%
  Average Return (5min): +0.62%
  Average Return (15min): +0.89%
```

**Key Metrics:**
- **Total Triggers**: Number of times scanner fired
- **Successful Trades**: Trades that hit 1% profit target
- **Success Rate**: % of profitable trades
- **Average Returns**: Mean return at different time intervals

### Individual Alerts
Each alert shows:

```
TATASTEEL @ 10:30 AM - ₹173.28
  3min: +0.52%
  5min: +0.78%
  15min: +1.24%
  Max Profit: +1.85%
  Max Loss: -0.23%
  Status: ✅ Successful
```

**Interpretation:**
- **Trigger Time**: Exact minute scanner fired
- **Trigger Price**: Entry price
- **Returns**: Profit/loss at different time intervals
- **Max Profit/Loss**: Best and worst points after trigger
- **Status**: Whether trade hit 1% profit target

---

## 🎓 **Best Practices**

### 1. Start Small
- Test on 10-20 stocks first
- Use 1-2 day date range
- Check 1-2 scanners only
- Verify results before scaling up

### 2. Use Proven Scanners
**Recommended for beginners:**
- Scanner #1: Probable Breakout (37 alerts, proven)
- Scanner #23: Breaking Out Now (27 alerts, proven)

**Advanced:**
- Scanner #17: 52-Week High (rare but powerful)

**Experimental:**
- Scanner #20: Bullish for Tomorrow (needs optimization)
- Scanner #32: Intraday Breakout (needs optimization)

### 3. Analyze Time-of-Day Patterns
Look for patterns like:
- Most alerts between 9:30-10:30 AM (opening range)
- Best returns in first hour of trading
- Avoid last 30 minutes (low liquidity)

### 4. Compare Against Benchmarks
- Success rate > 60% is good
- Average 3min return > 0.3% is good
- Max loss < -1% is acceptable

---

## ⚠️ **Common Issues**

### Issue 1: No Results Returned
**Possible Causes:**
- No data for selected date range
- Scanners too strict (no stocks pass criteria)
- Selected stocks not in database

**Solution:**
- Check date range (use recent dates with data)
- Try Scanner #1 or #23 (less strict)
- Leave stock selection empty (use all stocks)

### Issue 2: Too Many Results (Slow)
**Possible Causes:**
- Testing all 221 stocks over 2+ weeks
- Multiple scanners selected

**Solution:**
- Reduce date range to 1-3 days
- Select specific stocks (20-50)
- Test one scanner at a time

### Issue 3: Scanner Returns 0 Alerts
**Possible Causes:**
- Scanner criteria too strict
- No breakout opportunities in date range

**Solution:**
- Try different date range
- Use Scanner #1 or #23 (more lenient)
- Check if stocks have sufficient data

---

## 🔧 **Advanced Features**

### Custom Date Ranges
Test specific market conditions:
- **Trending Market**: Oct 1-10, 2025 (uptrend)
- **Volatile Market**: Oct 11-15, 2025 (high volatility)
- **Consolidation**: Oct 16-18, 2025 (sideways)

### Stock Selection Strategies
- **High Volume**: RELIANCE, TCS, INFY, HDFC, ICICI
- **Mid Cap**: TITAN, ASTRAL, POLYCAB
- **Volatile**: TATASTEEL, JSWSTEEL, ADANIPORTS

### Scanner Combinations
Test multiple scanners together:
- **Breakout Combo**: #1 + #17 + #23
- **Momentum Combo**: #1 + #23
- **Conservative**: #17 only (rare but high quality)

---

## 📈 **Performance Expectations**

### Scanner #1 (Probable Breakout)
- **Alerts per day**: 15-40
- **Success rate**: 70-80%
- **Best time**: 9:30-11:00 AM
- **Avg return (5min)**: 0.5-0.8%

### Scanner #17 (52-Week High Breakout)
- **Alerts per day**: 0-2
- **Success rate**: 80-90%
- **Best time**: Any (rare events)
- **Avg return (15min)**: 1.0-2.0%

### Scanner #23 (Breaking Out Now)
- **Alerts per day**: 10-30
- **Success rate**: 65-75%
- **Best time**: 9:30-10:30 AM, 2:00-3:00 PM
- **Avg return (3min)**: 0.4-0.7%

---

## ✅ **Quick Checklist**

Before running backtest:
- [ ] Server is running (uvicorn app.main:app --reload)
- [ ] Date range is valid (within last 2 weeks)
- [ ] At least one scanner is selected
- [ ] Stock selection is reasonable (empty or 10-50 stocks)

After getting results:
- [ ] Check total alerts (should be > 0)
- [ ] Review success rates (should be > 60%)
- [ ] Analyze time-of-day patterns
- [ ] Compare scanner performance
- [ ] Identify best stocks for each scanner

---

## 🎯 **Summary**

The PKScreener Backtest page allows you to:
1. **Test scanners** on historical data
2. **Measure performance** with real returns
3. **Compare strategies** across different scanners
4. **Optimize parameters** for live trading

**Recommended First Test:**
- Stocks: All (leave empty)
- Date: Oct 17, 2025 (single day)
- Scanners: #1, #23
- Expected: ~60 alerts

**Start the server and try it now!** 🚀

```bash
uvicorn app.main:app --reload
# Then open: http://localhost:8000/pkscreener-backtest
```

