# Fix: "No module named 'pymongo'" Error

## ❌ Error
```
[E 251018 10:20:45 main:793] Error running PKScreener backtest: No module named 'pymongo'
```

## 🔍 Root Cause
The server was started **before** `pymongo` was installed (or the virtual environment wasn't activated). The running server process doesn't have access to the `pymongo` module.

## ✅ Solution: Restart the Server

### Step 1: Stop the Current Server
In the terminal where the server is running, press:
```
Ctrl + C
```

### Step 2: Verify pymongo is Installed
```bash
cd /Users/balachandra.raju/projects/finns
source venv/bin/activate
python -c "import pymongo; print('✅ pymongo installed:', pymongo.__version__)"
```

**Expected Output:**
```
✅ pymongo installed: 4.15.3
```

If you see an error, install pymongo:
```bash
pip install pymongo
```

### Step 3: Restart the Server
```bash
cd /Users/balachandra.raju/projects/finns
source venv/bin/activate
uvicorn app.main:app --reload
```

**Expected Output:**
```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000
```

### Step 4: Test the Backtest Page
1. Open: **http://localhost:8000/pkscreener-backtest**
2. Configure:
   - Stocks: Select 5 stocks (RELIANCE, TCS, INFY, SBIN, HDFC)
   - Start Date: 2025-10-17
   - End Date: 2025-10-17
   - Scanners: ✓ #1, ✓ #23
3. Click **"Run Backtest"**
4. Wait for results

**Expected:** No more "No module named 'pymongo'" errors!

---

## 🔍 Why This Happens

### Module Import Flow
```
Server starts
  ↓
Imports app.main
  ↓
Imports backtest_engine.py
  ↓
Imports daily_data_service.py
  ↓
Imports pymongo ← ERROR if not installed!
```

### When Server Starts
- Python loads all modules into memory
- If `pymongo` isn't installed, import fails
- Server continues but backtest won't work

### After Installing pymongo
- Server is still running with old imports
- New module not loaded into memory
- **Must restart server** to reload imports

---

## ✅ Verification

After restarting the server, check the logs:

**Good Logs (No Errors):**
```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
Connected to MongoDB: trading_data
Daily data service initialized
INFO:     Application startup complete.
```

**Bad Logs (Still Errors):**
```
ERROR: Failed to connect to MongoDB: No module named 'pymongo'
```

If you still see errors after restarting:
1. Make sure virtual environment is activated: `source venv/bin/activate`
2. Verify pymongo is installed: `pip list | grep pymongo`
3. Check Python version: `python --version` (should be 3.9+)

---

## 🚀 Quick Fix Commands

**All-in-One Fix:**
```bash
# Stop server (Ctrl+C in server terminal)

# Then run:
cd /Users/balachandra.raju/projects/finns
source venv/bin/activate
pip install pymongo
uvicorn app.main:app --reload
```

**Verify Fix:**
```bash
# In a new terminal:
cd /Users/balachandra.raju/projects/finns
source venv/bin/activate
python -c "
import sys
sys.path.insert(0, 'pkscreener-integration')
from daily_data_service import get_daily_data_service
service = get_daily_data_service()
print('✅ Daily data service working!')
"
```

---

## 📝 Summary

**Problem:** Server doesn't have `pymongo` module  
**Solution:** Restart server after ensuring `pymongo` is installed  
**Time:** 30 seconds  

**Steps:**
1. ⏹️ Stop server (Ctrl+C)
2. ✅ Verify pymongo installed (`pip list | grep pymongo`)
3. 🚀 Restart server (`uvicorn app.main:app --reload`)
4. 🧪 Test backtest page

**After this fix, all scanners including #17 (52-Week High Breakout) will work!** 🎉

