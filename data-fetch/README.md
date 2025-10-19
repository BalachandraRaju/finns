# Real-time Data Collection System

## Overview

This system implements **1-minute real-time data collection** using **Upstox APIs only** for both LTP (Last Traded Price) and historical data. It supports:

1. **1-minute LTP collection** every minute during market hours
2. **1-minute historical data backfill** for past 2 months
3. **F&O stocks support** from NSE F&O symbols file
4. **PostgreSQL database** (with SQLite fallback)
5. **Automatic data synchronization** and gap detection

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   F&O Stocks    │    │   Upstox APIs    │    │   Database      │
│   (247 symbols) │───▶│   - LTP API v3   │───▶│   - PostgreSQL  │
│                 │    │   - Historical   │    │   - SQLite      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Data Collection Scheduler                    │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │ LTP Collection  │  │ Backfill Check  │  │ Data Freshness  │ │
│  │ Every 1 minute  │  │ Every 5 minutes │  │ Every 2 minutes │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## Components

### 1. F&O Stocks Loader (`fo_stocks_loader.py`)
- Loads 247 F&O symbols from `nse_fo_stock_symbols.txt`
- Creates Upstox instrument keys (`NSE_EQ|{symbol}`)
- Manages stock list for data collection

### 2. Upstox LTP Client (`upstox_ltp_client.py`)
- Uses Upstox LTP API v3 (supports up to 500 instruments per call)
- Collects real-time LTP data with volume, change, change%
- Handles batch processing for efficient API usage

### 3. LTP Service (`ltp_service.py`)
- Manages 1-minute LTP data collection
- Stores data in database with timestamps
- Provides data freshness checking
- Tracks synchronization status

### 4. Backfill Service (`backfill_service.py`)
- Detects missing 1-minute data gaps
- Backfills historical data using Upstox Historical API
- Supports day-by-day backfill for past 2 months
- Handles both daily and 1-minute intervals

### 5. Data Scheduler (`data_scheduler.py`)
- **LTP Collection**: Every 1 minute during market hours (9:15 AM - 3:30 PM)
- **Backfill Check**: Every 5 minutes during market hours
- **Daily Backfill**: 4:00 PM (after market close)
- **Weekly Full Backfill**: Sundays at 10:00 AM (past 2 months)

### 6. Database Support
- **PostgreSQL**: Primary database (from finns_auto)
- **SQLite**: Fallback database
- **Tables**: `candles`, `ltp_data`, `data_sync_status`

## Setup Instructions

### 1. Environment Configuration

Create `.env` file with:
```bash
# Upstox API Configuration
UPSTOX_ACCESS_TOKEN=your_upstox_access_token_here

# PostgreSQL Configuration (Optional)
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=finns_auto
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password

# Or use direct DATABASE_URL
DATABASE_URL=postgresql://user:password@host:port/database

# Redis Configuration
REDIS_URL=redis://localhost:6379/0
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt

# For PostgreSQL support (optional)
pip install psycopg2-binary
```

### 3. Database Setup

```bash
# Create database tables
python migrate_add_ltp_tables.py

# Test database setup
python -c "from data_fetch.postgres_config import postgres_config; postgres_config.setup_postgres_for_data_collection()"
```

### 4. Test System

```bash
# Run comprehensive tests
python data-fetch/test_upstox_data_system.py

# Test individual components
python -c "from data_fetch.fo_stocks_loader import fo_stocks_loader; print(f'Loaded {len(fo_stocks_loader.load_fo_stocks_from_file())} F&O symbols')"
```

### 5. Start Data Collection

```bash
# Start the scheduler
python -c "from data_fetch.data_scheduler import data_scheduler; data_scheduler.start()"

# Or integrate with main application
# The scheduler will automatically start during market hours
```

## Data Collection Schedule

| Task | Frequency | Time | Description |
|------|-----------|------|-------------|
| LTP Collection | Every 1 minute | 9:15 AM - 3:30 PM | Real-time price data |
| Backfill Check | Every 5 minutes | 9:15 AM - 3:30 PM | Missing data detection |
| Data Freshness | Every 2 minutes | Always | Data quality monitoring |
| Daily Backfill | Once daily | 4:00 PM | Today's missing data |
| Weekly Backfill | Weekly | Sunday 10:00 AM | Past 2 months data |

## Database Schema

### LTP Data Table
```sql
CREATE TABLE ltp_data (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR NOT NULL,
    instrument_key VARCHAR,
    ltp FLOAT NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    volume INTEGER,
    change FLOAT,
    change_percent FLOAT,
    UNIQUE(symbol, timestamp)
);
```

### Candles Table (1-minute data)
```sql
CREATE TABLE candles (
    id SERIAL PRIMARY KEY,
    instrument_key VARCHAR NOT NULL,
    interval VARCHAR NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    open FLOAT NOT NULL,
    high FLOAT NOT NULL,
    low FLOAT NOT NULL,
    close FLOAT NOT NULL,
    volume INTEGER NOT NULL,
    oi INTEGER DEFAULT 0,
    UNIQUE(instrument_key, interval, timestamp)
);
```

## API Usage

### Upstox LTP API v3
- **Endpoint**: `/market-quote/ltp`
- **Limit**: 500 instruments per request
- **Rate Limit**: Reasonable for 1-minute collection
- **Data**: LTP, volume, change, change%

### Upstox Historical API
- **Endpoint**: `/historical-candle/{instrument_key}/{interval}/{to_date}/{from_date}`
- **Intervals**: `1minute`, `day`
- **Data**: OHLCV + OI

## Monitoring

### Data Freshness
- Tracks last update time for each symbol
- Alerts if data is stale (>5 minutes old)
- Automatic backfill triggers for missing data

### Sync Status
- Success/failure tracking per symbol
- Error message logging
- Records synced count

### Performance Metrics
- API response times
- Data collection success rates
- Database storage efficiency

## Troubleshooting

### Common Issues

1. **401 Authentication Error**
   - Check `UPSTOX_ACCESS_TOKEN` in `.env`
   - Verify token is valid and not expired
   - Regenerate token from Upstox developer console

2. **Database Connection Issues**
   - PostgreSQL: Check connection parameters
   - SQLite: Ensure write permissions in project directory

3. **Missing Data**
   - Check market hours (9:15 AM - 3:30 PM IST)
   - Verify symbol exists in F&O list
   - Check API rate limits

4. **Import Errors**
   - Ensure all dependencies are installed
   - Check Python path configuration
   - Verify virtual environment activation

### Logs

Check logs for detailed error information:
```bash
# View scheduler logs
tail -f logs/data_scheduler.log

# View LTP collection logs
tail -f logs/ltp_service.log

# View backfill logs
tail -f logs/backfill_service.log
```

## Next Steps

1. **Start Data Collection**: Configure Upstox access token and start scheduler
2. **Monitor Performance**: Check data freshness and sync status
3. **Integrate Alerts**: Connect with existing pattern detection system
4. **Scale Up**: Add more symbols or reduce collection intervals as needed

## Files Structure

```
data-fetch/
├── __init__.py
├── README.md                    # This file
├── fo_stocks_loader.py         # F&O stocks management
├── upstox_ltp_client.py        # Upstox LTP API client
├── ltp_service.py              # LTP data collection service
├── backfill_service.py         # Historical data backfill
├── data_scheduler.py           # Task scheduling
├── postgres_config.py          # PostgreSQL configuration
└── test_upstox_data_system.py  # Comprehensive tests
```

The system is now ready for **1-minute real-time data collection** using **Upstox APIs only**! 🚀
