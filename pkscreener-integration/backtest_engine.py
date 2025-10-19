"""
Backtesting Engine for PKScreener Strategies
Focus: Momentum scalping - quick intraday moves
"""
import sys
import os

# Add parent directory to path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

# Add current directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
import logging
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.db import get_db
from app.models import Candle
from models import PKScreenerBacktestResult
from scanner_strategies import ScannerStrategies
from daily_data_service import get_daily_data_service

logger = logging.getLogger(__name__)


class BacktestEngine:
    """
    Backtest PKScreener strategies for momentum scalping
    Analyzes performance over short timeframes (5min, 15min, 30min, 1hr, 2hr)
    Uses DAILY volume averages from MongoDB for accurate intraday signals
    """

    def __init__(self, db: Session):
        self.db = db

        # Default timeframe in minutes (1, 3, 5 supported)
        self.timeframe: int = 1

        # Initialize daily data service
        try:
            self.daily_data_service = get_daily_data_service()
            logger.info("Daily data service initialized")
        except Exception as e:
            logger.error(f"Failed to initialize daily data service: {e}")
            self.daily_data_service = None

        # Initialize scanner strategies with daily data service
        self.strategies = ScannerStrategies(daily_data_service=self.daily_data_service)

        # Load watchlist
        self.watchlist = self._load_watchlist()
        logger.info(f"Loaded {len(self.watchlist)} stocks for backtesting")

    def _load_watchlist(self) -> List[Dict]:
        """Load watchlist from database"""
        try:
            from app.crud import get_watchlist_details

            watchlist_stocks = get_watchlist_details()

            stocks = []
            for stock in watchlist_stocks:
                stocks.append({
                    'symbol': stock.symbol,
                    'instrument_key': stock.instrument_key
                })

            return stocks

        except Exception as e:
            logger.error(f"Error loading watchlist: {e}")
            return []

    def get_candles_for_period(self, instrument_key: str, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """
        Fetch candles for a specific period
        Returns DataFrame with most recent candle first
        """
        try:
            candles = self.db.query(Candle).filter(
                and_(
                    Candle.instrument_key == instrument_key,
                    Candle.interval == '1minute',
                    Candle.timestamp >= start_date,
                    Candle.timestamp <= end_date
                )
            ).order_by(Candle.timestamp.desc()).all()

            if not candles:
                return pd.DataFrame()

            data = []
            for candle in candles:
                data.append({
                    'timestamp': candle.timestamp,
                    'open': candle.open,
                    'high': candle.high,
                    'low': candle.low,
                    'close': candle.close,
                    'volume': candle.volume
                })

            return pd.DataFrame(data)

        except Exception as e:
            logger.error(f"Error fetching candles: {e}")
            return pd.DataFrame()

    def calculate_future_returns(self, df: pd.DataFrame, trigger_idx: int) -> Dict:
        """
        Calculate returns after trigger point for scalping analysis

        Args:
            df: DataFrame with candles (most recent first)
            trigger_idx: Index where scanner triggered

        Returns:
            Dict with price movements and returns
        """
        try:
            trigger_price = df['close'].iloc[trigger_idx]
            trigger_time = df['timestamp'].iloc[trigger_idx]

            # Get future candles (indices before trigger_idx since data is reversed)
            future_candles = df.iloc[:trigger_idx] if trigger_idx > 0 else pd.DataFrame()

            if future_candles.empty:
                return {
                    'trigger_price': trigger_price,
                    'trigger_time': trigger_time,
                    'max_profit_pct': 0,
                    'max_loss_pct': 0
                }

            # Calculate time-based returns
            returns = {
                'trigger_price': trigger_price,
                'trigger_time': trigger_time
            }

            # Find prices at specific time intervals - ADDED 3min for intraday scalping
            time_intervals = [
                ('3min', timedelta(minutes=3)),   # NEW: Critical for intraday scalping
                ('5min', timedelta(minutes=5)),
                ('15min', timedelta(minutes=15)),
                ('30min', timedelta(minutes=30)),
                ('1hour', timedelta(hours=1)),
                ('2hours', timedelta(hours=2))
            ]

            for interval_name, interval_delta in time_intervals:
                target_time = trigger_time + interval_delta

                # Find closest candle to target time
                if 'time_diff' in future_candles.columns:
                    future_candles = future_candles.drop(columns=['time_diff'])
                future_candles = future_candles.copy()
                future_candles.loc[:, 'time_diff'] = (future_candles['timestamp'] - target_time).abs()
                closest_idx = future_candles['time_diff'].idxmin()

                if pd.notna(closest_idx):
                    price = future_candles.loc[closest_idx, 'close']
                    returns[f'price_after_{interval_name}'] = price
                    returns[f'return_{interval_name}_pct'] = ((price - trigger_price) / trigger_price) * 100
                else:
                    returns[f'price_after_{interval_name}'] = None
                    returns[f'return_{interval_name}_pct'] = None

            # Calculate max profit and max loss during the period
            max_high = future_candles['high'].max()
            min_low = future_candles['low'].min()

            returns['max_profit_pct'] = ((max_high - trigger_price) / trigger_price) * 100
            returns['max_loss_pct'] = ((min_low - trigger_price) / trigger_price) * 100

            # Find when max profit/loss occurred
            max_profit_idx = future_candles['high'].idxmax()
            max_loss_idx = future_candles['low'].idxmin()

            returns['max_profit_time'] = future_candles.loc[max_profit_idx, 'timestamp'] if pd.notna(max_profit_idx) else None
            returns['max_loss_time'] = future_candles.loc[max_loss_idx, 'timestamp'] if pd.notna(max_loss_idx) else None

            # Success criteria for scalping
            returns['hit_target_1pct'] = returns['max_profit_pct'] >= 1.0
            returns['hit_target_2pct'] = returns['max_profit_pct'] >= 2.0
            returns['hit_stoploss'] = returns['max_loss_pct'] <= -1.0

            # Consider successful if 3min return is positive (changed from 30min for faster scalping)
            returns['was_successful'] = returns.get('return_3min_pct', 0) > 0

            return returns

        except Exception as e:
            logger.error(f"Error calculating future returns: {e}")
    def calculate_future_returns_daily(self, df: pd.DataFrame, trigger_idx: int) -> Dict:
        """
        Calculate future returns for daily timeframe.
        Expects df in chronological order (oldest -> newest).
        """
        try:
            trigger_price = df['close'].iloc[trigger_idx]
            trigger_time = df['timestamp'].iloc[trigger_idx]

            returns = {
                'trigger_price': trigger_price,
                'trigger_time': trigger_time
            }

            horizons = {
                '1day': 1,
                '3day': 3,
                '5day': 5,
                '10day': 10,
            }

            for name, ahead in horizons.items():
                idx = trigger_idx + ahead
                if idx < len(df):
                    price = df['close'].iloc[idx]
                    returns[f'price_after_{name}'] = price
                    returns[f'return_{name}_pct'] = ((price - trigger_price) / trigger_price) * 100
                else:
                    returns[f'price_after_{name}'] = None
                    returns[f'return_{name}_pct'] = None

            # Max profit/loss over next 10 days
            future = df.iloc[trigger_idx+1: trigger_idx+11]
            if not future.empty:
                max_high = future['high'].max()
                min_low = future['low'].min()
                returns['max_profit_pct'] = ((max_high - trigger_price) / trigger_price) * 100
                returns['max_loss_pct'] = ((min_low - trigger_price) / trigger_price) * 100
            else:
                returns['max_profit_pct'] = 0
                returns['max_loss_pct'] = 0

            # Simple success: positive next-day return
            returns['was_successful'] = (returns.get('return_1day_pct') or 0) > 0
            return returns
        except Exception as e:
            logger.error(f"Error calculating daily future returns: {e}")
            return {}

            return {}

    def backtest_scanner_on_stock(self, scanner_id: int, stock: Dict, backtest_date: datetime) -> List[PKScreenerBacktestResult]:
        """
        Backtest a scanner on a single stock for a specific date

        IMPORTANT: Checks EVERY MINUTE to find exact trigger points
        When alert triggers, calculates gains from that exact minute

        Returns:
            List of backtest results (one per trigger)
        """
        try:
            results = []

            # Get data for the day (9:15 AM to 3:30 PM)
            start_time = backtest_date.replace(hour=9, minute=15, second=0, microsecond=0)
            end_time = backtest_date.replace(hour=15, minute=30, second=0, microsecond=0)

            # Get all candles for the day
            df_day = self.get_candles_for_period(stock['instrument_key'], start_time, end_time)

            if df_day.empty or len(df_day) < 50:
                return results

            # CRITICAL FIX: Check EVERY MINUTE (not every 30 minutes)
            # This simulates real-time scanning where we check each new candle
            check_interval = 1  # Check every 1 candle (1 minute) - CHANGED FROM 30

            # Track last trigger to avoid duplicate alerts within 30 minutes
            last_trigger_idx = None
            min_gap_between_triggers = 30  # Minimum 30 minutes between triggers

            # Build candidate indices based on timeframe
            candidate_indices: List[int] = []
            tf = getattr(self, 'timeframe', 1)
            if tf in (3, 5):
                try:
                    df_chron = df_day.iloc[::-1].reset_index(drop=True)
                    # Map timestamp -> reversed index (for df_day which is most recent first)
                    ts_to_rev_idx = {ts: (len(df_day) - 1 - idx) for idx, ts in enumerate(df_chron['timestamp'])}
                    res = (df_chron.set_index('timestamp')
                                   .resample(f"{tf}min", label='right', closed='right')
                                   .agg({'open':'first','high':'max','low':'min','close':'last','volume':'sum'})
                                   .dropna(subset=['close'])
                                   .reset_index())
                    res_timestamps = list(res['timestamp'])
                    # Warmup bars: fewer for higher TF to avoid empty scans
                    warmup_bars = 50 if tf == 1 else 20
                    if len(res_timestamps) > warmup_bars:
                        res_timestamps = res_timestamps[warmup_bars:]
                        candidate_indices = [ts_to_rev_idx[ts] for ts in res_timestamps if ts in ts_to_rev_idx]
                        candidate_indices = sorted(candidate_indices)
                except Exception as e:
                    logger.error(f"Timeframe resample failed, falling back to 1m: {e}")
                    candidate_indices = list(range(50, len(df_day), 1))
            else:
                candidate_indices = list(range(50, len(df_day), 1))

            # Final safeguard: if no indices computed, fall back to stepping through 1m by timeframe stride
            if not candidate_indices:
                candidate_indices = list(range(50, len(df_day), max(tf, 1)))

            for i in candidate_indices:
                # Skip if too close to last trigger (avoid duplicate alerts)
                if last_trigger_idx is not None and (i - last_trigger_idx) < min_gap_between_triggers:
                    continue

                # Get data up to this point (simulates real-time data available)
                df_upto_now = df_day.iloc[i:]
                # Indicators expect chronological order (oldest -> newest)
                df_for_indicators = df_upto_now.iloc[::-1].reset_index(drop=True)

                # Run scanner (pass instrument_key for daily volume comparison)
                passed = False
                metrics = {}

                if scanner_id == 1:
                    passed, metrics = self.strategies.scanner_1_volume_momentum_breakout_atr(df_for_indicators, stock['instrument_key'])
                elif scanner_id == 12:
                    passed, metrics = self.strategies.scanner_12_volume_momentum_breakout_atr_rsi(df_for_indicators, stock['instrument_key'])
                elif scanner_id == 14:
                    passed, metrics = self.strategies.scanner_14_vcp_chart_patterns_ma_support(df_for_indicators, stock['instrument_key'])
                elif scanner_id == 17:
                    passed, metrics = self.strategies.scanner_17_52week_high_breakout(df_for_indicators, stock['instrument_key'])
                elif scanner_id == 20:
                    passed, metrics = self.strategies.scanner_20_bullish_for_tomorrow(df_for_indicators, stock['instrument_key'])
                elif scanner_id == 21:
                    passed, metrics = self.strategies.scanner_21_bullcross_ma_fair_value(df_for_indicators, stock['instrument_key'])
                elif scanner_id == 23:
                    passed, metrics = self.strategies.scanner_23_breaking_out_now(df_for_indicators, stock['instrument_key'])
                elif scanner_id == 32:
                    passed, metrics = self.strategies.scanner_32_intraday_breakout_setup(df_for_indicators, stock['instrument_key'])

                if not passed:
                    continue

                # Scanner triggered at this exact minute! Calculate future returns
                last_trigger_idx = i  # Update last trigger
                future_returns = self.calculate_future_returns(df_day, i)

                # Create backtest result (ADDED 3min interval)
                result = PKScreenerBacktestResult(
                    scanner_id=scanner_id,
                    backtest_date=backtest_date,
                    instrument_key=stock['instrument_key'],
                    symbol=stock['symbol'],
                    trigger_price=future_returns.get('trigger_price', 0),
                    trigger_time=future_returns.get('trigger_time'),
                    price_after_3min=future_returns.get('price_after_3min'),      # NEW
                    price_after_5min=future_returns.get('price_after_5min'),
                    price_after_15min=future_returns.get('price_after_15min'),
                    price_after_30min=future_returns.get('price_after_30min'),
                    price_after_1hour=future_returns.get('price_after_1hour'),
                    price_after_2hours=future_returns.get('price_after_2hours'),
                    return_3min_pct=future_returns.get('return_3min_pct'),        # NEW
                    return_5min_pct=future_returns.get('return_5min_pct'),
                    return_15min_pct=future_returns.get('return_15min_pct'),
                    return_30min_pct=future_returns.get('return_30min_pct'),
                    return_1hour_pct=future_returns.get('return_1hour_pct'),
                    return_2hours_pct=future_returns.get('return_2hours_pct'),
                    max_profit_pct=future_returns.get('max_profit_pct'),
                    max_loss_pct=future_returns.get('max_loss_pct'),
                    max_profit_time=future_returns.get('max_profit_time'),
                    max_loss_time=future_returns.get('max_loss_time'),
                    was_successful=future_returns.get('was_successful'),
                    hit_target_1pct=future_returns.get('hit_target_1pct'),
                    hit_target_2pct=future_returns.get('hit_target_2pct'),
                    hit_stoploss=future_returns.get('hit_stoploss'),
                    volume_ratio=metrics.get('volume_ratio'),
                    atr_value=metrics.get('atr'),
                    rsi_value=metrics.get('rsi'),
                    momentum_score=metrics.get('momentum_score')
                )

                results.append(result)

                # Continue checking for more triggers (removed break to capture all triggers)
                # The min_gap_between_triggers ensures we don't get duplicate alerts


            return results

        except Exception as e:
            logger.error(f"Error backtesting {stock['symbol']} on {backtest_date}: {e}")
            return []




    def backtest_scanner_on_stock_daily(self, scanner_id: int, stock: Dict, start_date: datetime, end_date: datetime) -> List[PKScreenerBacktestResult]:
        """
        Backtest a scanner on daily timeframe using MongoDB daily candles.
        Evaluates on each day close within the date range.
        """
        results: List[PKScreenerBacktestResult] = []
        try:
            if not self.daily_data_service:
                logger.warning("Daily data service not available; skipping daily backtest")
                return results

            # Add lookback for indicators
            lookback_start = start_date - timedelta(days=300)
            candles = self.daily_data_service.get_daily_candles(stock['instrument_key'], lookback_start, end_date)
            if not candles or len(candles) < 60:
                return results

            df = pd.DataFrame(candles)
            # Ensure chronological order
            df = df.sort_values('timestamp').reset_index(drop=True)

            for j in range(50, len(df)):
                ts: datetime = df['timestamp'].iloc[j]
                if ts.date() < start_date.date() or ts.date() > end_date.date():
                    continue

                # Build df up to current day, newest first as scanners expect
                df_for_ind = df.iloc[:j+1].iloc[::-1].reset_index(drop=True)

                passed = False
                metrics: Dict = {}
                try:
                    if scanner_id == 17:
                        passed, metrics = self.strategies.scanner_17_52week_high_breakout(df_for_ind, stock['instrument_key'])
                    elif scanner_id == 20:
                        passed, metrics = self.strategies.scanner_20_bullish_for_tomorrow(df_for_ind, stock['instrument_key'])
                    elif scanner_id == 23:
                        passed, metrics = self.strategies.scanner_23_breaking_out_now(df_for_ind, stock['instrument_key'])
                    else:
                        # Other scanners may be intraday-oriented; run generically
                        method = None
                        if scanner_id == 1:
                            method = self.strategies.scanner_1_volume_momentum_breakout_atr
                        elif scanner_id == 12:
                            method = self.strategies.scanner_12_volume_momentum_breakout_atr_rsi
                        elif scanner_id == 14:
                            method = self.strategies.scanner_14_vcp_chart_patterns_ma_support
                        elif scanner_id == 21:
                            method = self.strategies.scanner_21_bullcross_ma_fair_value
                        elif scanner_id == 32:
                            method = self.strategies.scanner_32_intraday_breakout_setup
                        if method:
                            passed, metrics = method(df_for_ind, stock['instrument_key'])
                except Exception as e:
                    logger.error(f"Daily scan error for scanner {scanner_id} on {stock['symbol']}: {e}")
                    passed = False

                if not passed:
                    continue

                # Compute daily future returns
                daily_returns = self.calculate_future_returns_daily(df, j)
                if not daily_returns:
                    continue

                result = PKScreenerBacktestResult(
                    scanner_id=scanner_id,
                    backtest_date=ts,
                    instrument_key=stock['instrument_key'],
                    symbol=stock['symbol'],
                    trigger_price=daily_returns.get('trigger_price', 0.0),
                    trigger_time=daily_returns.get('trigger_time')
                )
                # Attach ephemeral daily return fields for API serialization
                setattr(result, 'return_1day_pct', daily_returns.get('return_1day_pct'))
                setattr(result, 'return_3day_pct', daily_returns.get('return_3day_pct'))
                setattr(result, 'return_5day_pct', daily_returns.get('return_5day_pct'))
                setattr(result, 'return_10day_pct', daily_returns.get('return_10day_pct'))
                result.max_profit_pct = daily_returns.get('max_profit_pct')
                result.max_loss_pct = daily_returns.get('max_loss_pct')
                result.was_successful = daily_returns.get('was_successful')

                results.append(result)

            return results
        except Exception as e:
            logger.error(f"Error in daily backtest for {stock['symbol']}: {e}")
            return results


            return []

    def run_backtest(self, scanner_ids: List[int], start_date: datetime, end_date: datetime, max_stocks: int = None, timeframe: int = 1) -> Dict[int, List[PKScreenerBacktestResult]]:
        """
        Run backtest for specified scanners over a date range

        Args:
            scanner_ids: List of scanner IDs to backtest
            start_date: Start date for backtest
            end_date: End date for backtest
            max_stocks: Optional limit on number of stocks to test
            timeframe: Bar size in minutes to evaluate scanners on (1, 3, 5). Returns are computed on 1m data.

        Returns:
            Dict mapping scanner_id to list of backtest results
        """
        # Set engine timeframe
        self.timeframe = timeframe if timeframe in (1, 3, 5, 1440) else 1

        results = {scanner_id: [] for scanner_id in scanner_ids}

        stocks_to_test = self.watchlist[:max_stocks] if max_stocks else self.watchlist

        if self.timeframe == 1440:
            logger.info("Starting DAILY backtest using MongoDB daily candles")
            for stock in stocks_to_test:
                for scanner_id in scanner_ids:
                    try:
                        stock_results = self.backtest_scanner_on_stock_daily(scanner_id, stock, start_date, end_date)
                        if stock_results:
                            results[scanner_id].extend(stock_results)
                            logger.info(f"  ✅ [Daily] Scanner #{scanner_id} triggered for {stock['symbol']}")
                    except Exception as e:
                        logger.error(f"Error daily backtesting scanner {scanner_id} on {stock['symbol']}: {e}")
                        continue
        else:
            # Get trading days in the range
            trading_days = self._get_trading_days(start_date, end_date)

            logger.info(f"Starting backtest for {len(trading_days)} trading days")
            logger.info(f"Scanners: {scanner_ids}")
            logger.info(f"Stocks: {len(stocks_to_test)}")
            logger.info(f"Timeframe: {self.timeframe}m")

            for day_idx, day in enumerate(trading_days, 1):
                logger.info(f"Backtesting day {day_idx}/{len(trading_days)}: {day.date()}")

                for stock in stocks_to_test:
                    for scanner_id in scanner_ids:
                        try:
                            stock_results = self.backtest_scanner_on_stock(scanner_id, stock, day)

                            if stock_results:
                                results[scanner_id].extend(stock_results)
                                logger.info(f"  ✅ Scanner #{scanner_id} triggered for {stock['symbol']}")

                        except Exception as e:
                            logger.error(f"Error backtesting scanner {scanner_id} on {stock['symbol']}: {e}")
                            continue

        # Save results to database
        self._save_backtest_results(results)

        # Log summary
        logger.info("\n" + "="*80)
        logger.info("BACKTEST COMPLETE")
        logger.info("="*80)
        for scanner_id, scanner_results in results.items():
            logger.info(f"Scanner #{scanner_id}: {len(scanner_results)} triggers")

        return results

    def _get_trading_days(self, start_date: datetime, end_date: datetime) -> List[datetime]:
        """Get list of trading days (Mon-Fri) in date range"""
        trading_days = []
        current_date = start_date

        while current_date <= end_date:
            # Skip weekends (Saturday=5, Sunday=6)
            if current_date.weekday() < 5:
                trading_days.append(current_date)
            current_date += timedelta(days=1)

        return trading_days

    def _save_backtest_results(self, results: Dict[int, List[PKScreenerBacktestResult]]):
        """Save backtest results to database"""
        try:
            for scanner_id, scanner_results in results.items():
                for result in scanner_results:
                    self.db.add(result)

            self.db.commit()
            logger.info("Backtest results saved to database")

        except Exception as e:
            logger.error(f"Error saving backtest results: {e}")
            self.db.rollback()


def main():
    """Run backtest on Scanner #1 and #12"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    db = next(get_db())
    engine = BacktestEngine(db)

    # Backtest last 5 trading days on limited stocks for testing
    end_date = datetime.now().replace(hour=15, minute=30, second=0, microsecond=0)
    start_date = end_date - timedelta(days=7)  # Last week

    print("\n" + "="*80)
    print("PKSCREENER BACKTEST - MOMENTUM SCALPING ANALYSIS")
    print("="*80)
    print(f"Period: {start_date.date()} to {end_date.date()}")
    print(f"Scanners: #1 (Volume+Momentum+Breakout+ATR), #12 (Same + RSI Filter)")
    print(f"Testing on first 20 stocks for speed...")
    print("="*80 + "\n")

    results = engine.run_backtest(
        scanner_ids=[1, 12],
        start_date=start_date,
        end_date=end_date,
        max_stocks=20  # Test on 20 stocks for speed
    )

    # Display summary
    print("\n" + "="*80)
    print("BACKTEST RESULTS SUMMARY")
    print("="*80)

    for scanner_id in [1, 12]:
        scanner_results = results[scanner_id]
        print(f"\n📊 Scanner #{scanner_id}: {len(scanner_results)} triggers")

        if scanner_results:
            # Calculate statistics
            successful = [r for r in scanner_results if r.was_successful]
            hit_1pct = [r for r in scanner_results if r.hit_target_1pct]
            hit_2pct = [r for r in scanner_results if r.hit_target_2pct]

            avg_30min_return = sum(r.return_30min_pct for r in scanner_results if r.return_30min_pct) / len(scanner_results)
            max_profit = max(r.max_profit_pct for r in scanner_results if r.max_profit_pct)
            max_loss = min(r.max_loss_pct for r in scanner_results if r.max_loss_pct)

            print(f"  Success Rate (30min positive): {len(successful)}/{len(scanner_results)} ({len(successful)/len(scanner_results)*100:.1f}%)")
            print(f"  Hit 1% Target: {len(hit_1pct)}/{len(scanner_results)} ({len(hit_1pct)/len(scanner_results)*100:.1f}%)")
            print(f"  Hit 2% Target: {len(hit_2pct)}/{len(scanner_results)} ({len(hit_2pct)/len(scanner_results)*100:.1f}%)")
            print(f"  Avg 30min Return: {avg_30min_return:.2f}%")
            print(f"  Max Profit: {max_profit:.2f}%")
            print(f"  Max Loss: {max_loss:.2f}%")

            print(f"\n  Top 5 Trades:")
            sorted_results = sorted(scanner_results, key=lambda x: x.return_30min_pct if x.return_30min_pct else -999, reverse=True)
            for i, r in enumerate(sorted_results[:5], 1):
                ret_30min = r.return_30min_pct if r.return_30min_pct else 0
                print(f"    {i}. {r.symbol} on {r.backtest_date.date()}: {ret_30min:+.2f}% in 30min")

    db.close()
    print("\n✅ Backtest complete!")


if __name__ == "__main__":
    main()


