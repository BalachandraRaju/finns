# Finns - Stock Watchlist & Point & Figure Charts

A FastAPI-based stock watchlist application with Point & Figure (P&F) charting capabilities, integrated with Upstox API for real-time data.

## Features

- 📊 **Point & Figure Charts**: Interactive P&F charts with customizable box sizes
- 📈 **Stock Watchlist**: Add/remove stocks with target prices and stop losses
- 🔔 **Smart Alerts**: Pattern-based alerts (buy/sell signals, breakouts, breakdowns)
- ⏰ **Market Hours Scheduler**: Automated alerts during trading hours (9 AM - 3:30 PM IST)
- 📱 **Telegram Integration**: Real-time notifications via Telegram bot
- 🗄️ **Data Storage**: SQLite for historical data, Redis for real-time caching
- 🐳 **Docker Ready**: Containerized deployment with Docker Compose

## Tech Stack

- **Backend**: FastAPI, Python 3.9+
- **Database**: SQLite (historical data), Redis (caching/watchlist)
- **Charts**: Plotly.js for interactive P&F charts
- **Frontend**: HTML, HTMX for dynamic updates
- **API**: Upstox API for market data
- **Deployment**: Docker, Docker Compose

## Quick Start with Docker

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd finns
   ```

2. **Create environment file**:
   ```bash
   cp .env.example .env
   # Edit .env with your Upstox API credentials
   ```

3. **Run with Docker Compose**:
   ```bash
   docker-compose up -d
   ```

4. **Access the application**:
   - Web Interface: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

## Manual Installation

### Prerequisites

- Python 3.9+
- Redis server
- Upstox API account

### Setup

1. **Clone and setup virtual environment**:
   ```bash
   git clone <repository-url>
   cd finns
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Setup environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Run database migration**:
   ```bash
   python migrate_add_oi_column.py
   ```

5. **Start Redis** (if not using Docker):
   ```bash
   redis-server
   ```

6. **Run the application**:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

## Configuration

Create a `.env` file with the following variables:

```env
# Upstox API Configuration
UPSTOX_ACCESS_TOKEN=your_access_token_here
UPSTOX_API_SECRET=your_api_secret_here

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379

# Telegram Bot (Optional)
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here

# Application Settings
RSI_THRESHOLD=70
TELEGRAM_ALERTS_ENABLED=true
```

## API Endpoints

### Watchlist Management
- `GET /` - Main watchlist page
- `POST /api/watchlist/add` - Add stocks to watchlist
- `DELETE /watchlist/delete/{instrument_key}` - Remove stock from watchlist

### Charts
- `GET /chart/{instrument_key}` - Chart page for a stock
- `GET /chart_data/{instrument_key}` - P&F chart data (JSON/HTML)

### Settings
- `GET /api/settings` - Get application settings
- `POST /api/settings` - Update settings

## Features in Detail

### Point & Figure Charts
- Interactive charts with zoom and pan
- Customizable box sizes (0.10%, 0.15%, 0.25%, etc.)
- 3-box reversal pattern
- X's for uptrends, O's for downtrends

### Alert System
- **Buy Signals**: Triple bottom breakouts, ascending patterns
- **Sell Signals**: Triple top breakdowns, descending patterns
- **Market Hours Only**: Alerts run 9 AM - 3:30 PM IST, Monday-Friday
- **Duplicate Prevention**: Redis-based deduplication

### Data Management
- **Historical Data**: Stored in SQLite with automatic API fetching
- **Real-time Updates**: Redis caching for fast access
- **Market Hours Awareness**: Respects trading hours for data requests

## Development

### Running Tests
```bash
python test_chart_generation.py
python upstox_test.py
```

### Database Migration
```bash
python migrate_add_oi_column.py
```

### Clear Data (for testing)
```bash
python -c "
import sqlite3, redis
# Clear SQLite
conn = sqlite3.connect('historical_data.db')
conn.execute('DELETE FROM candles')
conn.commit()
# Clear Redis
r = redis.Redis()
r.flushdb()
"
```

## Docker Deployment

### Build and Run
```bash
# Build image
docker build -t finns-app .

# Run with compose
docker-compose up -d

# View logs
docker-compose logs -f app

# Stop services
docker-compose down
```

### Environment Variables in Docker
Mount your `.env` file or set environment variables in `docker-compose.yml`.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This application is for educational and research purposes. Always verify trading signals and consult with financial advisors before making investment decisions.

## Support

For issues and questions:
1. Check the [Issues](../../issues) page
2. Create a new issue with detailed description
3. Include logs and configuration (without sensitive data)
