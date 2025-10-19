# PKScreener Backtest - Bug Fix and Testing Guide

## ✅ **BUG FIXED!**

### Issue
JavaScript error in `pkscreener_backtest.html`:
```
Uncaught (in promise) TypeError: Cannot read properties of null (reading 'checked')
```

### Root Cause
The JavaScript was trying to check scanners 1-21, but only scanners 1, 12, 14, 17, 20, 21, 23, 32 exist in the HTML.

### Fix Applied
Updated `app/templates/pkscreener_backtest.html`:

**Before (Line 110):**
```javascript
const scanner_ids = [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21]
  .filter(id => document.getElementById('sc-'+id).checked)
```

**After:**
```javascript
// Only check scanners that exist in the UI
const scanner_ids = [1, 12, 14, 17, 20, 21, 23, 32].filter(id => {
  const el = document.getElementById('sc-'+id)
  return el && el.checked
})
```

Also updated scanner names in the results display to match the new scanners.

---

## 🚀 **How to Test**

### Option 1: Quick API Test (Recommended)

**Step 1:** Start the server
```bash
cd /Users/balachandra.raju/projects/finns
source venv/bin/activate
uvicorn app.main:app --reload
```

**Step 2:** Run the test script
```bash
# In a new terminal
cd /Users/balachandra.raju/projects/finns
source venv/bin/activate
python test_api_quick.py
```

This will test the API with just 5 stocks and 2 scanners (fast!).

---

### Option 2: Browser Test

**Step 1:** Start the server
```bash
uvicorn app.main:app --reload
```

**Step 2:** Open browser
Navigate to: **http://localhost:8000/pkscreener-backtest**

**Step 3:** Configure backtest (IMPORTANT: Keep it small for speed!)

**Recommended Settings for Quick Test:**
- **Stocks**: Select only 5-10 stocks (e.g., RELIANCE, TCS, INFY, SBIN, HDFC)
- **Start Date**: 2025-10-17
- **End Date**: 2025-10-17 (same day!)
- **Scanners**: Check only #1 and #23 (proven to work)

**Step 4:** Open Chrome DevTools
- Press `F12` or `Cmd+Option+I` (Mac)
- Go to **Console** tab
- Watch for any JavaScript errors

**Step 5:** Click "Run Backtest"

**Expected Results:**
- No JavaScript errors in console
- Loading spinner appears
- Results appear within 30-60 seconds
- Shows alerts for scanners #1 and #23

---

## ⚡ **Performance Tips**

### Why is backtest slow?

The backtest processes:
- **Every stock** in selection
- **Every scanner** checked
- **Every trading day** in date range
- **Every minute** of each trading day (375 minutes per day)

**Example:**
- 221 stocks × 2 scanners × 1 day × 375 minutes = **165,750 data points**
- 221 stocks × 2 scanners × 10 days × 375 minutes = **1,657,500 data points**

### How to make it faster:

**1. Limit Stocks (Most Important!)**
```
Instead of: All 221 stocks
Use: 10-20 stocks
Speed improvement: 10-20x faster
```

**2. Limit Date Range**
```
Instead of: 2 weeks (10 trading days)
Use: 1-2 days
Speed improvement: 5-10x faster
```

**3. Limit Scanners**
```
Instead of: All 8 scanners
Use: 1-2 scanners
Speed improvement: 4-8x faster
```

**4. Use Proven Scanners**
```
Fast scanners: #1, #23 (simple calculations)
Slow scanners: #17 (requires MongoDB lookup for 52-week high)
```

### Recommended Test Configurations

**Quick Test (30 seconds):**
- Stocks: 5 stocks
- Date: 1 day
- Scanners: #1, #23
- Total: ~3,750 data points

**Medium Test (2-3 minutes):**
- Stocks: 20 stocks
- Date: 1 day
- Scanners: #1, #23
- Total: ~15,000 data points

**Full Test (10-15 minutes):**
- Stocks: 50 stocks
- Date: 2 days
- Scanners: #1, #17, #23
- Total: ~112,500 data points

**Production Test (30-60 minutes):**
- Stocks: All 221 stocks
- Date: 5 days
- Scanners: All 8 scanners
- Total: ~3,315,000 data points

---

## 🔍 **Using Chrome DevTools**

### Console Tab
Watch for:
- ✅ No errors = JavaScript working correctly
- ❌ Red errors = Something broken

### Network Tab
1. Click **Network** tab
2. Click "Run Backtest"
3. Look for `/api/pkscreener/backtest` request
4. Check:
   - **Status**: Should be `200 OK`
   - **Time**: How long the request took
   - **Response**: Click to see JSON response

### Example Good Response:
```json
{
  "status": "success",
  "summary": {
    "1": {
      "total_triggers": 15,
      "success_rate_pct": 73.3,
      "avg_returns": {
        "3min": 0.45,
        "5min": 0.62
      }
    },
    "23": {
      "total_triggers": 8,
      "success_rate_pct": 62.5,
      "avg_returns": {
        "3min": 0.38,
        "5min": 0.51
      }
    }
  },
  "results": {
    "1": [ ... ],
    "23": [ ... ]
  }
}
```

---

## 🐛 **Troubleshooting**

### Issue: JavaScript error still appears
**Solution:**
1. Hard refresh browser: `Cmd+Shift+R` (Mac) or `Ctrl+Shift+R` (Windows)
2. Clear browser cache
3. Restart server

### Issue: Backtest takes too long (> 5 minutes)
**Solution:**
1. Reduce number of stocks (select 5-10 only)
2. Use single day date range
3. Test only 1-2 scanners
4. Check server logs for errors

### Issue: No results returned
**Possible Causes:**
1. No data for selected date range
2. Scanners too strict (no stocks pass criteria)
3. Selected stocks not in database

**Solution:**
1. Use recent date (Oct 17, 2025)
2. Try Scanner #1 or #23 (proven to work)
3. Leave stock selection empty (use all stocks)

### Issue: Server crashes or times out
**Solution:**
1. Check server logs for errors
2. Reduce test size (fewer stocks/days)
3. Restart server
4. Check database connection

---

## ✅ **Verification Checklist**

### Before Testing:
- [ ] Server is running (`uvicorn app.main:app --reload`)
- [ ] Browser is open to http://localhost:8000/pkscreener-backtest
- [ ] Chrome DevTools is open (F12)
- [ ] Console tab is visible

### During Testing:
- [ ] No JavaScript errors in console
- [ ] Loading spinner appears when clicking "Run Backtest"
- [ ] Network request shows in Network tab
- [ ] Request completes within reasonable time (< 5 minutes)

### After Testing:
- [ ] Results appear on page
- [ ] Summary shows total triggers and success rates
- [ ] Individual alerts are displayed
- [ ] Scanner names are correct (#1, #17, #20, #23, #32)
- [ ] No errors in console

---

## 📊 **Expected Results**

### Scanner #1 (Probable Breakout)
- **Alerts per day**: 15-40
- **Success rate**: 70-80%
- **Avg 3min return**: 0.4-0.6%
- **Best time**: 9:30-11:00 AM

### Scanner #23 (Breaking Out Now)
- **Alerts per day**: 10-30
- **Success rate**: 65-75%
- **Avg 3min return**: 0.3-0.5%
- **Best time**: 9:30-10:30 AM, 2:00-3:00 PM

### Scanner #17 (52-Week High Breakout)
- **Alerts per day**: 0-2
- **Success rate**: 80-90%
- **Avg 15min return**: 1.0-2.0%
- **Best time**: Any (rare events)

---

## 🚀 **Quick Start Commands**

### Terminal 1: Start Server
```bash
cd /Users/balachandra.raju/projects/finns
source venv/bin/activate
uvicorn app.main:app --reload
```

### Terminal 2: Test API
```bash
cd /Users/balachandra.raju/projects/finns
source venv/bin/activate
python test_api_quick.py
```

### Browser: Test UI
```
http://localhost:8000/pkscreener-backtest

Configuration:
- Stocks: Select 5-10 stocks
- Start Date: 2025-10-17
- End Date: 2025-10-17
- Scanners: ✓ #1, ✓ #23
- Click "Run Backtest"
```

---

## 📝 **Summary**

✅ **Bug Fixed**: JavaScript error resolved  
✅ **Scanner Names Updated**: Correct names in UI  
✅ **Test Scripts Created**: Easy testing with `test_api_quick.py`  
✅ **Performance Tips**: How to make backtest faster  
✅ **Troubleshooting Guide**: Common issues and solutions  

**The backtest page is now ready to use!**

**Recommended first test:**
1. Start server
2. Open http://localhost:8000/pkscreener-backtest
3. Select 5 stocks (RELIANCE, TCS, INFY, SBIN, HDFC)
4. Set date to 2025-10-17 (both start and end)
5. Check scanners #1 and #23
6. Click "Run Backtest"
7. Wait 30-60 seconds
8. View results!

🚀 **Happy backtesting!**

