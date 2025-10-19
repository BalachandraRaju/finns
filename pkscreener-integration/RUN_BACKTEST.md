# How to Run Comprehensive Backtest

## 📋 Purpose

Run a comprehensive 2-month backtest on Scanner #1 and Scanner #12 to validate their performance for momentum scalping.

---

## 🚀 Quick Run

```bash
cd /Users/balachandra.raju/projects/finns
python3 pkscreener-integration/backtest_engine.py
```

This will:
- Backtest last 7 days (default)
- Test on first 20 stocks (for speed)
- Display performance metrics

---

## 📊 Full 2-Month Backtest

### Step 1: Create Custom Backtest Script

Create `pkscreener-integration/run_full_backtest.py`:

```python
"""
Full 2-Month Backtest for Scanner #1 and #12
"""
import sys
sys.path.insert(0, 'pkscreener-integration')

from backtest_engine import BacktestEngine
from app.db import get_db
from datetime import datetime, timedelta
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def main():
    print("\n" + "="*80)
    print("FULL 2-MONTH BACKTEST - SCANNER #1 & #12")
    print("="*80)
    
    db = next(get_db())
    engine = BacktestEngine(db)
    
    # Set date range: Last 2 months
    end_date = datetime.now().replace(hour=15, minute=30, second=0, microsecond=0)
    start_date = end_date - timedelta(days=60)
    
    print(f"\n📅 Period: {start_date.date()} to {end_date.date()}")
    print(f"📊 Scanners: #1, #12")
    print(f"🎯 Stocks: All {len(engine.watchlist)} F&O stocks")
    print(f"⏱️  This may take 30-60 minutes...\n")
    
    # Run backtest
    results = engine.run_backtest(
        scanner_ids=[1, 12],
        start_date=start_date,
        end_date=end_date,
        max_stocks=None  # All stocks
    )
    
    # Detailed Analysis
    print("\n" + "="*80)
    print("DETAILED BACKTEST RESULTS")
    print("="*80)
    
    for scanner_id in [1, 12]:
        scanner_results = results[scanner_id]
        
        print(f"\n{'='*80}")
        print(f"SCANNER #{scanner_id}")
        print(f"{'='*80}")
        
        if not scanner_results:
            print("No triggers found in backtest period")
            continue
        
        # Calculate comprehensive statistics
        total_triggers = len(scanner_results)
        
        # Success metrics
        successful = [r for r in scanner_results if r.was_successful]
        hit_1pct = [r for r in scanner_results if r.hit_target_1pct]
        hit_2pct = [r for r in scanner_results if r.hit_target_2pct]
        hit_stoploss = [r for r in scanner_results if r.hit_stoploss]
        
        # Returns
        returns_5min = [r.return_5min_pct for r in scanner_results if r.return_5min_pct is not None]
        returns_15min = [r.return_15min_pct for r in scanner_results if r.return_15min_pct is not None]
        returns_30min = [r.return_30min_pct for r in scanner_results if r.return_30min_pct is not None]
        returns_1hour = [r.return_1hour_pct for r in scanner_results if r.return_1hour_pct is not None]
        returns_2hours = [r.return_2hours_pct for r in scanner_results if r.return_2hours_pct is not None]
        
        # Max profit/loss
        max_profits = [r.max_profit_pct for r in scanner_results if r.max_profit_pct is not None]
        max_losses = [r.max_loss_pct for r in scanner_results if r.max_loss_pct is not None]
        
        print(f"\n📊 OVERVIEW:")
        print(f"   Total Triggers: {total_triggers}")
        print(f"   Date Range: {min(r.backtest_date for r in scanner_results).date()} to {max(r.backtest_date for r in scanner_results).date()}")
        print(f"   Unique Stocks: {len(set(r.symbol for r in scanner_results))}")
        
        print(f"\n✅ SUCCESS METRICS:")
        print(f"   Success Rate (30min positive): {len(successful)}/{total_triggers} ({len(successful)/total_triggers*100:.1f}%)")
        print(f"   Hit 1% Target: {len(hit_1pct)}/{total_triggers} ({len(hit_1pct)/total_triggers*100:.1f}%)")
        print(f"   Hit 2% Target: {len(hit_2pct)}/{total_triggers} ({len(hit_2pct)/total_triggers*100:.1f}%)")
        print(f"   Hit Stop Loss (-1%): {len(hit_stoploss)}/{total_triggers} ({len(hit_stoploss)/total_triggers*100:.1f}%)")
        
        print(f"\n📈 AVERAGE RETURNS:")
        if returns_5min:
            print(f"   5 minutes:  {sum(returns_5min)/len(returns_5min):+.2f}%")
        if returns_15min:
            print(f"   15 minutes: {sum(returns_15min)/len(returns_15min):+.2f}%")
        if returns_30min:
            print(f"   30 minutes: {sum(returns_30min)/len(returns_30min):+.2f}%")
        if returns_1hour:
            print(f"   1 hour:     {sum(returns_1hour)/len(returns_1hour):+.2f}%")
        if returns_2hours:
            print(f"   2 hours:    {sum(returns_2hours)/len(returns_2hours):+.2f}%")
        
        print(f"\n🎯 EXTREMES:")
        if max_profits:
            print(f"   Max Profit: {max(max_profits):+.2f}%")
        if max_losses:
            print(f"   Max Loss:   {min(max_losses):+.2f}%")
        
        print(f"\n🏆 TOP 10 TRADES (by 30min return):")
        sorted_results = sorted(scanner_results, 
                               key=lambda x: x.return_30min_pct if x.return_30min_pct else -999, 
                               reverse=True)
        for i, r in enumerate(sorted_results[:10], 1):
            ret_30min = r.return_30min_pct if r.return_30min_pct else 0
            max_profit = r.max_profit_pct if r.max_profit_pct else 0
            print(f"   {i:2d}. {r.symbol:12s} on {r.backtest_date.date()}: "
                  f"{ret_30min:+6.2f}% (30min) | Max: {max_profit:+6.2f}%")
        
        print(f"\n📉 WORST 5 TRADES (by 30min return):")
        for i, r in enumerate(sorted_results[-5:][::-1], 1):
            ret_30min = r.return_30min_pct if r.return_30min_pct else 0
            max_loss = r.max_loss_pct if r.max_loss_pct else 0
            print(f"   {i}. {r.symbol:12s} on {r.backtest_date.date()}: "
                  f"{ret_30min:+6.2f}% (30min) | Max Loss: {max_loss:+6.2f}%")
        
        print(f"\n📊 STOCK-WISE PERFORMANCE:")
        stock_performance = {}
        for r in scanner_results:
            if r.symbol not in stock_performance:
                stock_performance[r.symbol] = []
            if r.return_30min_pct is not None:
                stock_performance[r.symbol].append(r.return_30min_pct)
        
        stock_avg = {symbol: sum(returns)/len(returns) 
                    for symbol, returns in stock_performance.items() if returns}
        
        sorted_stocks = sorted(stock_avg.items(), key=lambda x: x[1], reverse=True)
        
        print(f"\n   Top 10 Stocks by Avg Return:")
        for i, (symbol, avg_return) in enumerate(sorted_stocks[:10], 1):
            trigger_count = len(stock_performance[symbol])
            print(f"   {i:2d}. {symbol:12s}: {avg_return:+6.2f}% avg ({trigger_count} triggers)")
    
    # Comparative Analysis
    if results[1] and results[12]:
        print(f"\n{'='*80}")
        print("COMPARATIVE ANALYSIS: SCANNER #1 vs SCANNER #12")
        print(f"{'='*80}")
        
        for metric_name, metric_func in [
            ("Total Triggers", lambda r: len(r)),
            ("Success Rate", lambda r: len([x for x in r if x.was_successful])/len(r)*100 if r else 0),
            ("Avg 30min Return", lambda r: sum(x.return_30min_pct for x in r if x.return_30min_pct)/len(r) if r else 0),
            ("Hit 1% Target Rate", lambda r: len([x for x in r if x.hit_target_1pct])/len(r)*100 if r else 0),
            ("Hit 2% Target Rate", lambda r: len([x for x in r if x.hit_target_2pct])/len(r)*100 if r else 0),
        ]:
            val_1 = metric_func(results[1])
            val_12 = metric_func(results[12])
            
            if "Rate" in metric_name or "Return" in metric_name:
                print(f"\n{metric_name}:")
                print(f"   Scanner #1:  {val_1:6.2f}{'%' if 'Rate' in metric_name or 'Return' in metric_name else ''}")
                print(f"   Scanner #12: {val_12:6.2f}{'%' if 'Rate' in metric_name or 'Return' in metric_name else ''}")
                print(f"   Difference:  {val_12-val_1:+6.2f}{'%' if 'Rate' in metric_name or 'Return' in metric_name else ''}")
            else:
                print(f"\n{metric_name}:")
                print(f"   Scanner #1:  {val_1:.0f}")
                print(f"   Scanner #12: {val_12:.0f}")
    
    db.close()
    
    print(f"\n{'='*80}")
    print("BACKTEST COMPLETE!")
    print(f"{'='*80}")
    print("\n✅ Results saved to database table: pkscreener_backtest_results")
    print("✅ Use SQL queries to analyze further or export to CSV")
    print("\n")

if __name__ == "__main__":
    main()
```

### Step 2: Run the Backtest

```bash
cd /Users/balachandra.raju/projects/finns
python3 pkscreener-integration/run_full_backtest.py
```

**Expected Duration:** 30-60 minutes (depending on data availability)

---

## 📊 Interpreting Results

### Key Metrics to Look For

1. **Success Rate (30min positive)**
   - **Good:** > 60%
   - **Excellent:** > 70%
   - Target: Majority of trades should be profitable after 30 minutes

2. **Hit 1% Target Rate**
   - **Good:** > 50%
   - **Excellent:** > 65%
   - Shows scanner's ability to find momentum moves

3. **Hit 2% Target Rate**
   - **Good:** > 30%
   - **Excellent:** > 45%
   - Indicates strong momentum potential

4. **Average 30min Return**
   - **Good:** > +0.5%
   - **Excellent:** > +1.0%
   - Should be significantly positive

5. **Hit Stop Loss Rate**
   - **Good:** < 20%
   - **Excellent:** < 10%
   - Lower is better - shows good entry timing

### Decision Criteria

**Deploy Scanner if:**
- Success rate > 60%
- Average 30min return > +0.5%
- Hit 1% target rate > 50%
- Hit stop loss rate < 20%

**Further Optimization Needed if:**
- Success rate < 50%
- Average 30min return < +0.3%
- Hit stop loss rate > 30%

---

## 💾 Export Results to CSV

```python
import sys
sys.path.insert(0, 'pkscreener-integration')
from app.db import get_db
from models import PKScreenerBacktestResult
import pandas as pd

db = next(get_db())

# Query results
results = db.query(PKScreenerBacktestResult).filter(
    PKScreenerBacktestResult.scanner_id.in_([1, 12])
).all()

# Convert to DataFrame
data = []
for r in results:
    data.append({
        'scanner_id': r.scanner_id,
        'date': r.backtest_date,
        'symbol': r.symbol,
        'trigger_price': r.trigger_price,
        'return_5min': r.return_5min_pct,
        'return_15min': r.return_15min_pct,
        'return_30min': r.return_30min_pct,
        'return_1hour': r.return_1hour_pct,
        'return_2hours': r.return_2hours_pct,
        'max_profit': r.max_profit_pct,
        'max_loss': r.max_loss_pct,
        'was_successful': r.was_successful,
        'hit_1pct': r.hit_target_1pct,
        'hit_2pct': r.hit_target_2pct,
        'hit_stoploss': r.hit_stoploss
    })

df = pd.DataFrame(data)
df.to_csv('pkscreener_backtest_results.csv', index=False)

print(f"✅ Exported {len(df)} results to pkscreener_backtest_results.csv")

db.close()
```

---

## 📈 Next Steps After Backtest

1. **Review Results**
   - Analyze success rates
   - Identify best-performing stocks
   - Compare Scanner #1 vs #12

2. **Make Decision**
   - Deploy scanners with good performance
   - Optimize or discard poor performers

3. **Integrate into Main App**
   - Add scheduler to `app/main.py`
   - Create UI pages for live results
   - Set up alerts/notifications

4. **Monitor Live Performance**
   - Compare live results to backtest
   - Adjust parameters if needed
   - Track actual P&L

---

## ✅ Success Checklist

- [ ] Database tables created
- [ ] Full 2-month backtest completed
- [ ] Results analyzed and documented
- [ ] Decision made on which scanners to deploy
- [ ] Scheduler integrated into main app
- [ ] UI pages created
- [ ] Live monitoring in place


