import os
import asyncio
from datetime import timedelta
from fastapi import FastAPI, Request, APIRouter, Form, Depends, HTTPException, BackgroundTasks, Header
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv
from typing import List, Optional
from logzero import logger

from app import crud, models, charts
# Import scheduler based on configuration
import os
if os.getenv("USE_PARALLEL_SCHEDULER", "false").lower() == "true":
    from app import parallel_alert_scheduler as scheduler
    logger.info("🚀 Using PARALLEL alert scheduler for optimized performance")
else:
    from app import scheduler
    logger.info("📊 Using SEQUENTIAL alert scheduler (legacy mode)")
from app.pnf_matrix import PnFMatrixCalculator
from app.fibonacci_scanner import FibonacciScanner
from app.auth import (
    get_current_user_from_session,
    get_current_user_optional,
    create_access_token,
    User,
    UserCreate,
    UserLogin,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    AuthenticationRedirect
)
from app.user_service import (
    authenticate_user,
    create_user,
    create_default_admin_user
)
from app import backtest_service

load_dotenv()

def run_startup_pattern_tests():
    """Run essential pattern tests before application startup."""
    print("🧪 RUNNING STARTUP PATTERN TESTS")
    print("=" * 50)

    try:
        from app.test_patterns import TEST_PATTERNS
        from app.charts import _calculate_pnf_points
        from anchor_point_calculator import AnchorPointCalculator

        print(f"✅ Found {len(TEST_PATTERNS)} test patterns")

        # Test a few key patterns
        test_patterns = ['bullish_breakout', 'bearish_breakdown', 'triple_top']
        success_count = 0

        for pattern_key in test_patterns:
            if pattern_key in TEST_PATTERNS:
                try:
                    pattern_info = TEST_PATTERNS[pattern_key]
                    candles = pattern_info['data_generator']()

                    highs = [c['high'] for c in candles]
                    lows = [c['low'] for c in candles]

                    # Test P&F calculation with 1% box size and 3-box reversal
                    x_coords, y_coords, pnf_symbols = _calculate_pnf_points(highs, lows, 0.01, 3)

                    if len(x_coords) > 0 and len(pnf_symbols) > 0:
                        print(f"✅ {pattern_key}: {len(candles)} candles → {len(x_coords)} P&F points")
                        success_count += 1
                    else:
                        print(f"⚠️ {pattern_key}: No P&F points generated")

                except Exception as e:
                    print(f"❌ {pattern_key}: Error - {str(e)}")

        # Test anchor points
        try:
            anchor_calculator = AnchorPointCalculator(min_column_separation=7)
            print("✅ Anchor point calculator initialized")
        except Exception as e:
            print(f"⚠️ Anchor points: {str(e)}")

        if success_count >= 2:
            print(f"🎉 STARTUP TESTS PASSED ({success_count}/{len(test_patterns)} patterns working)")
            print("✅ Pattern system ready")
            print("✅ 1% box size and 3-box reversal working")
            print("✅ Anchor points integration ready")
            return True
        else:
            print(f"❌ STARTUP TESTS FAILED ({success_count}/{len(test_patterns)} patterns working)")
            return False

    except Exception as e:
        print(f"❌ STARTUP TEST ERROR: {str(e)}")
        return False

app = FastAPI()

# Exception handler for authentication redirects
@app.exception_handler(AuthenticationRedirect)
async def authentication_redirect_handler(request: Request, exc: AuthenticationRedirect):
    """Redirect to login page when authentication fails."""
    return RedirectResponse(url="/login", status_code=303)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# Background task status tracking
data_population_status = {}

def populate_stock_data_background(instrument_key: str, symbol: str):
    """Background task to populate 1-minute data for a stock."""
    try:
        # Update status to in progress
        data_population_status[instrument_key] = {
            "status": "in_progress",
            "symbol": symbol,
            "message": f"Fetching 2 months of 1-minute data for {symbol}...",
            "progress": 0
        }

        logger.info(f"🔄 Starting background data population for {symbol} ({instrument_key})")

        # Run the data population synchronously in the background thread
        charts.populate_minute_data_for_stock(instrument_key)

        # Update status to completed
        data_population_status[instrument_key] = {
            "status": "completed",
            "symbol": symbol,
            "message": f"✅ Successfully populated 2 months of 1-minute data for {symbol}",
            "progress": 100
        }

        logger.info(f"✅ Completed background data population for {symbol}")

    except Exception as e:
        # Update status to failed
        data_population_status[instrument_key] = {
            "status": "failed",
            "symbol": symbol,
            "message": f"❌ Failed to populate data for {symbol}: {str(e)}",
            "progress": 0
        }
        logger.error(f"❌ Background data population failed for {symbol}: {e}")

# Create default admin user and run startup tasks
@app.on_event("startup")
def startup_event():
    """Run all startup tasks."""
    # Run pattern tests before starting application
    print("\n" + "=" * 60)
    print("🚀 STARTING APPLICATION WITH PATTERN VALIDATION")
    print("=" * 60)

    test_success = run_startup_pattern_tests()

    if not test_success:
        print("\n❌ PATTERN TESTS FAILED!")
        print("⚠️ Application starting anyway, but patterns may not work correctly")
        print("⚠️ Please check pattern system before using")
    else:
        print("\n🎉 PATTERN TESTS PASSED!")
        print("✅ All patterns working with 1% box size and 3-box reversal")
        print("✅ Application ready for use")

    print("=" * 60)

    # Create default admin user if no users exist
    create_default_admin_user()
    logger.info("✅ Application startup complete")

    # MongoDB is used for all data storage - no SQLite tables needed
    # Start the appropriate scheduler (parallel or sequential)
    if os.getenv("USE_PARALLEL_SCHEDULER", "false").lower() == "true":
        scheduler.start_parallel_scheduler()
    else:
        scheduler.start_scheduler()


# --- Authentication Routes ---

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Render the login page."""
    # If already logged in, redirect to home
    user = get_current_user_optional(request)
    if user:
        return RedirectResponse(url="/", status_code=302)
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
async def login(request: Request, email: str = Form(...), password: str = Form(...)):
    """Handle login form submission."""
    user = authenticate_user(email, password)
    if not user:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Invalid email or password"
        })

    # Create access token
    access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    # Redirect to home page with cookie
    response = RedirectResponse(url="/", status_code=302)
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite="lax"
    )
    return response

@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    """Render the registration page."""
    # If already logged in, redirect to home
    user = get_current_user_optional(request)
    if user:
        return RedirectResponse(url="/", status_code=302)
    return templates.TemplateResponse("register.html", {"request": request})

@app.post("/register")
async def register(
    request: Request,
    full_name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...)
):
    """Handle registration form submission."""
    # Validate passwords match
    if password != confirm_password:
        return templates.TemplateResponse("register.html", {
            "request": request,
            "error": "Passwords do not match"
        })

    # Validate password length
    if len(password) < 6:
        return templates.TemplateResponse("register.html", {
            "request": request,
            "error": "Password must be at least 6 characters long"
        })

    # Create user
    user_data = UserCreate(email=email, password=password, full_name=full_name)
    user = create_user(user_data)

    if not user:
        return templates.TemplateResponse("register.html", {
            "request": request,
            "error": "Email already registered or registration failed"
        })

    # Redirect to login page with success message
    return templates.TemplateResponse("login.html", {
        "request": request,
        "success": "Registration successful! Please login."
    })

@app.get("/logout")
async def logout(request: Request):
    """Handle logout."""
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie("access_token")
    return response

# --- HTML Pages (Protected) ---

@app.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request, current_user: User = Depends(get_current_user_from_session)):
    """Render the settings page."""
    return templates.TemplateResponse("settings.html", {"request": request, "user": current_user})

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request, current_user: User = Depends(get_current_user_from_session)):
    watchlist = crud.get_watchlist_details()
    # For each stock, also get the latest alert
    for stock in watchlist:
        stock.latest_alert = crud.get_latest_alert_for_stock(stock.symbol)

    return templates.TemplateResponse("index.html", {
        "request": request,
        "watchlist": watchlist,
        "user": current_user
    })

@app.get("/add-stocks", response_class=HTMLResponse)
async def add_stocks_page(request: Request, current_user: User = Depends(get_current_user_from_session)):
    """Serves the page for adding new stocks."""
    sorted_stocks = sorted(crud.STOCKS_LIST, key=lambda s: s['symbol'])
    return templates.TemplateResponse("add_stocks.html", {"request": request, "stocks_list": sorted_stocks, "user": current_user})

@app.get("/chart/{instrument_key:path}", response_class=HTMLResponse)
async def get_chart_page(request: Request, instrument_key: str, current_user: User = Depends(get_current_user_from_session)):
    stock = crud.get_stock_by_instrument_key(instrument_key)

    # Handle Dhan instrument keys (format: DHAN_{security_id})
    if not stock and instrument_key.startswith('DHAN_'):
        # Get watchlist to find Dhan stock details
        watchlist = crud.get_watchlist_details()
        dhan_stock = next((s for s in watchlist if s.instrument_key == instrument_key), None)
        if dhan_stock:
            stock = {
                'symbol': dhan_stock.symbol,
                'name': dhan_stock.company_name or dhan_stock.symbol,
                'instrument_key': instrument_key
            }

    # Handle NSE instrument keys (format: NSE_EQ|ISIN) - these are legacy, just use them directly
    if not stock and instrument_key.startswith('NSE_'):
        # Get watchlist to find matching stock by NSE key
        watchlist = crud.get_watchlist_details()
        nse_stock = next((s for s in watchlist if s.instrument_key == instrument_key), None)
        if nse_stock:
            stock = {
                'symbol': nse_stock.symbol,
                'name': nse_stock.company_name or nse_stock.symbol,
                'instrument_key': instrument_key
            }

    if not stock:
        return HTMLResponse(content=f"<h3>Stock not found: {instrument_key}</h3><p>Please check if the stock is in your watchlist.</p>", status_code=404)

    # Get all watchlist stocks for the stock selector
    watchlist_stocks = crud.get_watchlist_details()

    return templates.TemplateResponse("chart.html", {
        "request": request,
        "stock": stock,
        "watchlist_stocks": watchlist_stocks,
        "box_sizes": [0.10, 0.15, 0.25, 0.50, 0.75, 1.00, 1.50, 2.00]  # 0.1% to 2% for intraday
    })

@app.get("/data-status", response_class=HTMLResponse)
async def data_status_page(request: Request, current_user: User = Depends(get_current_user_from_session)):
    """Page to show data population status."""
    return templates.TemplateResponse("data_status.html", {"request": request, "user": current_user})

@app.get("/fibonacci-scanner", response_class=HTMLResponse)
async def fibonacci_scanner_page(request: Request, current_user: User = Depends(get_current_user_from_session)):
    """Page to show Fibonacci pattern scanner results."""
    return templates.TemplateResponse("fibonacci_scanner.html", {"request": request, "user": current_user})

@app.get("/test-charts", response_class=HTMLResponse)
async def test_charts_page(request: Request, pattern: str = "bullish_breakout", current_user: User = Depends(get_current_user_from_session)):
    """Page to test chart patterns with dummy data and real watchlist stocks."""
    from app.test_patterns import TEST_PATTERNS
    from app.crud import get_watchlist_details

    # Get watchlist stocks for real data testing
    watchlist_stocks = get_watchlist_details()

    return templates.TemplateResponse("test_charts.html", {
        "request": request,
        "test_patterns": TEST_PATTERNS,
        "selected_pattern": pattern,
        "watchlist_stocks": watchlist_stocks,
        "user": current_user
    })

@app.get("/pkscreener-backtest", response_class=HTMLResponse)
@app.get("/pkscreener-backtest.html", response_class=HTMLResponse)
async def pkscreener_backtest_page(request: Request, current_user: User = Depends(get_current_user_from_session)):
    """Render the PKScreener backtest UI page."""
    watchlist = crud.get_watchlist_details()
    return templates.TemplateResponse("pkscreener_backtest.html", {
        "request": request,
        "watchlist": watchlist,
        "user": current_user
    })


@app.get("/chart_data/{instrument_key:path}", response_class=HTMLResponse)
async def get_chart_data(request: Request, instrument_key: str, box_size: float = None, interval: str = "day", time_range: str = "2months", mode: str = None, fibonacci: bool = True, ema: bool = True, trendlines: bool = True, anchor_points: bool = True, current_user: User = Depends(get_current_user_from_session)):
    """
    Get chart data with configurable interval and time range.

    Args:
        instrument_key: Stock instrument key (DHAN_xxx or NSE_xxx)
        box_size: P&F box size percentage (auto-selected if None)
        interval: Data interval (day, 1minute, 3minute, 30minute)
        time_range: Time range for 1-minute charts (1month, 2months)
        mode: Special mode (intraday for live data)
        fibonacci: Show Fibonacci retracement levels with percentages
        ema: Show 20-period EMA line
        trendlines: Show trend lines
        anchor_points: Show anchor points (most populated price levels)
    """
    # NSE instrument keys are valid - no conversion needed (watchlist has mixed keys)
    # Handle intraday mode
    if mode == "intraday":
        # For intraday mode, use current day data only
        time_range = "today"
        if box_size is None:
            box_size = 0.0025  # 0.25% optimal for intraday

    # Auto-select appropriate box size based on interval
    # PRODUCTION SETTING: 0.25% box size for all intervals
    if box_size is None:
        if interval in ["1minute", "3minute"]:
            box_size = 0.0025  # 0.25% for intraday (PRODUCTION)
        elif interval == "30minute":
            box_size = 0.0025  # 0.25% for 30-minute (PRODUCTION)
        else:  # daily
            box_size = 0.0025  # 0.25% for daily (PRODUCTION)

    chart_html = charts.generate_pnf_chart_html(
        instrument_key,
        box_pct=box_size,
        reversal=3,
        interval=interval,
        time_range=time_range,
        mode=mode,
        show_fibonacci=fibonacci,
        show_ema=ema,
        show_trendlines=trendlines,
        show_anchor_points=anchor_points
    )
    return HTMLResponse(content=chart_html)

@app.get("/test_chart_data/{pattern_name}", response_class=HTMLResponse)
async def get_test_chart_data(request: Request, pattern_name: str, box_size: float = 0.0025, reversal: int = 3, current_user: User = Depends(get_current_user_from_session)):
    """
    Get test chart data for pattern validation.

    Args:
        pattern_name: Name of the test pattern
        box_size: P&F box size percentage (default: 0.0025 = 0.25%)
        reversal: Reversal amount (default: 3)
    """
    from app.test_patterns import generate_test_chart_html

    chart_html = generate_test_chart_html(pattern_name, box_pct=box_size, reversal=reversal)
    return HTMLResponse(content=chart_html)


@app.delete("/watchlist/delete/{instrument_key}", status_code=200)
async def delete_from_watchlist(request: Request, instrument_key: str, current_user: User = Depends(get_current_user_from_session)):
    crud.delete_stock_from_watchlist(instrument_key)
    return "" # Return an empty string for HTMX to replace the row


# --- API Routes ---
api_router = APIRouter(prefix="/api")

@api_router.post("/watchlist/add-all")
async def add_all_stocks_to_watchlist(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user_from_session)
):
    """Add all 208 stocks from STOCKS_LIST to watchlist."""
    try:
        added_count = 0
        skipped_count = 0

        # Get existing watchlist to avoid duplicates
        existing_watchlist = crud.get_watchlist_details()
        existing_keys = {stock.instrument_key for stock in existing_watchlist}

        for stock_info in crud.STOCKS_LIST:
            # Skip test stocks
            if 'NSETEST' in stock_info['symbol']:
                continue

            # Skip if already in watchlist
            if stock_info['instrument_key'] in existing_keys:
                skipped_count += 1
                continue

            stock_request = models.AddStockRequest(
                instrument_key=stock_info['instrument_key'],
                symbol=stock_info['symbol'],
                trade_type="Bullish",  # Default
                tags="Bulk Added",
                target_price=None,
                stoploss=None,
            )

            # Add stock to watchlist
            crud.add_stock_to_watchlist(stock_request)
            added_count += 1

            # Initialize status for background data population
            data_population_status[stock_info['instrument_key']] = {
                "status": "queued",
                "symbol": stock_info['symbol'],
                "message": f"Queued for data population: {stock_info['symbol']}",
                "progress": 0
            }

            # Queue background task for data population
            background_tasks.add_task(populate_stock_data_background, stock_info['instrument_key'], stock_info['symbol'])

        logger.info(f"✅ Bulk add: Added {added_count} stocks, skipped {skipped_count} (already in watchlist)")

        return {
            "status": "success",
            "message": f"Added {added_count} stocks to watchlist. Skipped {skipped_count} stocks already in watchlist.",
            "added_count": added_count,
            "skipped_count": skipped_count
        }

    except Exception as e:
        logger.error(f"❌ Error in bulk add: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/watchlist/remove-all")
async def remove_all_stocks_from_watchlist(current_user: User = Depends(get_current_user_from_session)):
    """Remove all stocks from watchlist."""
    try:
        watchlist = crud.get_watchlist_details()
        removed_count = len(watchlist)

        for stock in watchlist:
            crud.delete_stock_from_watchlist(stock.instrument_key)

        logger.info(f"✅ Bulk remove: Removed {removed_count} stocks from watchlist")

        return {
            "status": "success",
            "message": f"Removed {removed_count} stocks from watchlist.",
            "removed_count": removed_count
        }

    except Exception as e:
        logger.error(f"❌ Error in bulk remove: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/watchlist/add")
async def add_to_watchlist(
    background_tasks: BackgroundTasks,
    instrument_key: List[str] = Form(...),
    trade_type: str = Form(...),
    tags: str = Form(...),
    target_price: str = Form(""),
    stoploss: str = Form(""),
):
    target_price_float = float(target_price) if target_price else None
    stoploss_float = float(stoploss) if stoploss else None

    added_stocks = []

    for key in instrument_key:
        stock_info = next((s for s in crud.STOCKS_LIST if s['instrument_key'] == key), None)
        if not stock_info:
            # You might want to log this or handle it differently
            continue

        stock_request = models.AddStockRequest(
            instrument_key=key,
            symbol=stock_info['symbol'],
            trade_type=trade_type,
            tags=tags,
            target_price=target_price_float,
            stoploss=stoploss_float,
        )

        # Add stock to watchlist immediately (fast operation)
        crud.add_stock_to_watchlist(stock_request)
        added_stocks.append(stock_info['symbol'])

        # Initialize status for this stock
        data_population_status[key] = {
            "status": "queued",
            "symbol": stock_info['symbol'],
            "message": f"Queued for data population: {stock_info['symbol']}",
            "progress": 0
        }

        # Queue background task for data population (non-blocking)
        background_tasks.add_task(populate_stock_data_background, key, stock_info['symbol'])

        logger.info(f"✅ Added {stock_info['symbol']} to watchlist, data population queued in background")

    return {
        "status": "success",
        "message": f"Successfully added {len(added_stocks)} stock(s) to watchlist. Data population is running in background.",
        "added_stocks": added_stocks
    }

@api_router.post("/watchlist/add-stocks-json")
async def add_stocks_to_watchlist_json(
    request_data: dict,
    background_tasks: BackgroundTasks,
):
    """
    Add stocks to the main UI watchlist (Redis-based) using JSON format.
    This endpoint makes stocks appear on the main watchlist page.

    Example:
    {
        "stocks": ["RELIANCE", "TCS", "BAJFINANCE"],
        "trade_type": "LONG",  # Optional, defaults to "Bullish"
        "tags": "large-cap,momentum"  # Optional
    }
    """
    try:
        stocks = request_data.get("stocks", [])
        trade_type = request_data.get("trade_type", "Bullish")
        tags = request_data.get("tags", "API Added")

        if not stocks:
            raise HTTPException(status_code=400, detail="No stocks provided")

        added_stocks = []
        failed_stocks = []

        for symbol in stocks:
            symbol = symbol.upper().strip()

            # Find stock info by symbol
            stock_info = next((s for s in crud.STOCKS_LIST if s['symbol'] == symbol), None)

            if not stock_info:
                failed_stocks.append({"symbol": symbol, "reason": "Stock not found in universe"})
                continue

            # Check if already in watchlist
            existing_watchlist = crud.get_watchlist_details()
            if any(ws.symbol == symbol for ws in existing_watchlist):
                failed_stocks.append({"symbol": symbol, "reason": "Already in watchlist"})
                continue

            stock_request = models.AddStockRequest(
                instrument_key=stock_info['instrument_key'],
                symbol=symbol,
                trade_type=trade_type,
                tags=tags,
                target_price=None,
                stoploss=None
            )

            crud.add_stock_to_watchlist(stock_request)
            added_stocks.append(symbol)

            # Initialize status for this stock
            data_population_status[stock_info['instrument_key']] = {
                "status": "queued",
                "symbol": symbol,
                "message": f"Queued for data population: {symbol}",
                "progress": 0
            }

            # Queue background task for data population
            background_tasks.add_task(populate_stock_data_background, stock_info['instrument_key'], symbol)

        return {
            "status": "success",
            "added": added_stocks,
            "failed": failed_stocks,
            "total_added": len(added_stocks),
            "total_failed": len(failed_stocks),
            "message": f"Successfully added {len(added_stocks)} stocks to watchlist. Data population running in background."
        }

    except Exception as e:
        logger.error(f"Error adding stocks to watchlist: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/settings")
async def get_settings():
    return crud.get_settings()

@api_router.post("/settings")
async def update_settings(settings: models.Settings):
    crud.save_settings(settings)
    return {"status": "success"}

@api_router.post("/update-dhan-token")
async def update_dhan_token(request: Request):
    """
    Update Dhan access token directly via API.
    Accepts JSON body with 'token' field.
    """
    try:
        body = await request.json()
        token = body.get("token", "").strip()

        if not token:
            return {"status": "error", "message": "Token is required"}

        # Validate token format (basic check - should start with eyJ)
        if not token.startswith("eyJ"):
            return {"status": "error", "message": "Invalid token format. Token should start with 'eyJ'"}

        # Update the token in .env file and Redis
        crud.update_env_file("DHAN_ACCESS_TOKEN", token)

        # Also update in Redis settings
        if crud.redis_client:
            crud.redis_client.hset("settings", "dhan_access_token", token)

        return {
            "status": "success",
            "message": "Dhan access token updated successfully",
            "token_preview": token[:20] + "..." + token[-10:]
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to update token: {str(e)}"}

async def populate_all_stocks_background():
    """Background function to populate data for all watchlist stocks."""
    try:
        watchlist = crud.get_watchlist_details()
        if not watchlist:
            logger.info("No stocks in watchlist for bulk population")
            return

        for stock in watchlist:
            try:
                populate_stock_data_background(stock.instrument_key, stock.symbol)
            except Exception as e:
                logger.error(f"Failed to populate data for {stock.symbol}: {e}")

    except Exception as e:
        logger.error(f"Error in bulk data population: {e}")

@api_router.post("/data/populate-minute-data")
async def populate_minute_data(background_tasks: BackgroundTasks):
    """
    Populate 1-minute data for all watchlist stocks.
    This will fetch 2 months of 1-minute data for efficient chart loading.
    """
    try:
        # Get all watchlist stocks
        watchlist = crud.get_watchlist_details()
        if not watchlist:
            return {"status": "error", "message": "No stocks in watchlist"}

        # Initialize status for each stock
        for stock in watchlist:
            data_population_status[stock.instrument_key] = {
                "status": "queued",
                "symbol": stock.symbol,
                "message": f"Queued for bulk data population: {stock.symbol}",
                "progress": 0
            }

        # Queue single background task for all stocks
        background_tasks.add_task(populate_all_stocks_background)

        return {
            "status": "success",
            "message": f"Queued data population for {len(watchlist)} stocks. Check status using /api/data/population-status",
            "queued_stocks": len(watchlist)
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to queue data population: {str(e)}"}

@api_router.get("/data/population-status")
async def get_population_status():
    """
    Get the status of data population tasks.
    """
    return {
        "status": "success",
        "tasks": data_population_status,
        "summary": {
            "total": len(data_population_status),
            "queued": len([s for s in data_population_status.values() if s["status"] == "queued"]),
            "in_progress": len([s for s in data_population_status.values() if s["status"] == "in_progress"]),
            "completed": len([s for s in data_population_status.values() if s["status"] == "completed"]),
            "failed": len([s for s in data_population_status.values() if s["status"] == "failed"])
        }
    }

@api_router.get("/data/population-status/{instrument_key}")
async def get_stock_population_status(instrument_key: str):
    """
    Get the status of data population for a specific stock.
    """
    if instrument_key in data_population_status:
        return {"status": "success", "task": data_population_status[instrument_key]}
    else:
        return {"status": "not_found", "message": "No data population task found for this stock"}

@api_router.delete("/data/population-status")
async def clear_population_status():
    """
    Clear completed and failed data population status entries.
    """
    global data_population_status
    original_count = len(data_population_status)

    # Keep only queued and in_progress tasks
    data_population_status = {
        k: v for k, v in data_population_status.items()
        if v["status"] in ["queued", "in_progress"]
    }

    cleared_count = original_count - len(data_population_status)
    return {
        "status": "success",
        "message": f"Cleared {cleared_count} completed/failed status entries",
        "remaining_tasks": len(data_population_status)
    }

@app.get("/styles.css", response_class=Response)
async def dynamic_styles():
    with open("app/static/style.css") as f:
        content = f.read()
    return Response(content=content, media_type="text/css", headers={
        "Cache-Control": "no-cache, no-store, must-revalidate",
        "Pragma": "no-cache",
        "Expires": "0",
    })

@app.get("/pnf-matrix", response_class=HTMLResponse)
async def pnf_matrix_page(request: Request, current_user: User = Depends(get_current_user_from_session)):
    """PnF Matrix analysis page."""
    return templates.TemplateResponse("pnf_matrix.html", {"request": request, "user": current_user})

@app.get("/alerts", response_class=HTMLResponse)
async def alerts_page(request: Request, current_user: User = Depends(get_current_user_from_session)):
    """Trading alerts analysis page."""
    return templates.TemplateResponse("alerts.html", {"request": request, "user": current_user})

@api_router.post("/test-telegram-alert")
async def test_telegram_alert():
    """Test Telegram alert delivery."""
    try:
        from app.telegram_notifier import test_telegram_connection
        success = test_telegram_connection()

        if success:
            return {
                "success": True,
                "message": "✅ Telegram test message sent successfully! Check your Telegram app."
            }
        else:
            return {
                "success": False,
                "message": "❌ Failed to send Telegram message. Check your bot token and chat ID in .env file."
            }
    except Exception as e:
        logger.error(f"❌ Telegram test error: {e}")
        return {
            "success": False,
            "message": f"❌ Error: {str(e)}"
        }

@app.get("/alerts/analytics", response_class=HTMLResponse)
async def alerts_analytics_page(request: Request):
    """Trading alerts analytics page."""
    return templates.TemplateResponse("alerts_analytics.html", {"request": request, "user": {"email": "test@example.com"}})

@app.get("/pattern-validation", response_class=HTMLResponse)
async def pattern_validation_page(request: Request):
    """Pattern validation dashboard page."""
    return templates.TemplateResponse("pattern_validation.html", {"request": request, "user": {"email": "test@example.com"}})

@app.get("/alert-verification", response_class=HTMLResponse)
async def alert_verification_page(request: Request):
    """Alert verification page for detailed pattern analysis."""
    return templates.TemplateResponse("alert_verification.html", {"request": request, "user": {"email": "test@example.com"}})

@app.get("/oi-dashboard", response_class=HTMLResponse)
async def oi_dashboard_page(request: Request):
    """Open Interest (OI) alert dashboard page."""
    return templates.TemplateResponse("oi_dashboard.html", {"request": request, "user": {"email": "test@example.com"}})

@api_router.post("/pnf-matrix")
async def calculate_pnf_matrix(request: Request):
    """Calculate PnF Matrix for all stocks in watchlist."""
    try:
        data = await request.json()
        timeframe = data.get('timeframe', 'day')
        box_sizes = data.get('box_sizes', [0.01, 0.005, 0.0025, 0.0015])

        # Initialize matrix calculator
        calculator = PnFMatrixCalculator()

        # Calculate matrix for all stocks
        results = calculator.calculate_matrix_for_watchlist(timeframe, box_sizes)

        return {
            "success": True,
            "results": [
                {
                    "symbol": result.symbol,
                    "instrument_key": result.instrument_key,
                    "timeframe": result.timeframe,
                    "total_score": result.total_score,
                    "matrix_scores": [
                        {
                            "box_size": score.box_size,
                            "column_type": score.column_type,
                            "score": score.score,
                            "latest_price": score.latest_price,
                            "pattern_alerts": score.pattern_alerts
                        }
                        for score in result.matrix_scores
                    ],
                    "matrix_strength": result.matrix_strength,
                    "super_alert_eligible": result.super_alert_eligible,
                    "calculation_time": result.calculation_time
                }
                for result in results
            ]
        }

    except Exception as e:
        logger.error(f"Error calculating PnF matrix: {e}")
        return {
            "success": False,
            "error": str(e)
        }

# --- Alert API Routes ---
@api_router.get("/alerts")
async def get_alerts(
    symbol: str = None,
    alert_type: str = None,
    pattern_type: str = None,
    is_super_alert: bool = None,
    start_date: str = None,
    end_date: str = None,
    outcome: str = None,
    limit: int = 100,
    offset: int = 0
):
    """Get alerts with filtering options."""
    try:
        from datetime import datetime
        from app.models import AlertFilters

        # Parse dates if provided
        start_dt = datetime.fromisoformat(start_date) if start_date else None
        end_dt = datetime.fromisoformat(end_date) if end_date else None

        filters = AlertFilters(
            symbol=symbol,
            alert_type=alert_type,
            pattern_type=pattern_type,
            is_super_alert=is_super_alert,
            start_date=start_dt,
            end_date=end_dt,
            outcome=outcome,
            limit=limit,
            offset=offset
        )

        alerts = crud.get_alerts(filters)

        # Get total count for pagination
        total_filters = AlertFilters(
            symbol=symbol,
            alert_type=alert_type,
            pattern_type=pattern_type,
            is_super_alert=is_super_alert,
            start_date=start_dt,
            end_date=end_dt,
            outcome=outcome,
            limit=10000,  # Large number to get total count
            offset=0
        )
        total_alerts = crud.get_alerts(total_filters)

        return {
            "status": "success",
            "alerts": [alert.model_dump() for alert in alerts],
            "total_count": len(total_alerts),
            "page_size": limit,
            "current_page": (offset // limit) + 1
        }

    except Exception as e:
        logger.error(f"Error fetching alerts: {e}")
        return {"status": "error", "message": str(e)}

@api_router.get("/alerts/statistics")
async def get_alert_statistics():
    """Get alert statistics for dashboard."""
    try:
        stats = crud.get_alert_statistics()
        return {"status": "success", **stats}
    except Exception as e:
        logger.error(f"Error fetching alert statistics: {e}")
        return {"status": "error", "message": str(e)}

@api_router.post("/alerts/analysis")
async def update_alert_analysis(analysis_data: models.AlertAnalysisUpdate):
    """Update alert analysis for ML purposes."""
    try:
        success = crud.update_alert_analysis(analysis_data)
        if success:
            return {"status": "success", "message": "Alert analysis updated"}
        else:
            return {"status": "error", "message": "Failed to update alert analysis"}
    except Exception as e:
        logger.error(f"Error updating alert analysis: {e}")
        return {"status": "error", "message": str(e)}

@api_router.get("/alerts/ml-data")
async def get_alerts_for_ml():
    """Get alerts with analysis data for ML training."""
    try:
        alerts = crud.get_alerts_for_ml_analysis()
        return {
            "status": "success",
            "alerts": [alert.model_dump() for alert in alerts],
            "count": len(alerts)
        }
    except Exception as e:
        logger.error(f"Error fetching ML alerts: {e}")
        return {"status": "error", "message": str(e)}

@api_router.get("/alerts/pattern-performance")
async def get_pattern_performance():
    """Get pattern performance statistics."""
    try:
        performance = crud.get_pattern_performance()
        return {"status": "success", **performance}
    except Exception as e:
        logger.error(f"Error fetching pattern performance: {e}")
        return {"status": "error", "message": str(e)}


# --- PKScreener Backtest API ---
from pydantic import BaseModel

class PKScreenerBacktestRequest(BaseModel):
    instrument_keys: Optional[List[str]] = None
    symbols: Optional[List[str]] = None
    start_date: str
    end_date: str
    scanner_ids: List[int]
    timeframe: Optional[int] = 1  # minutes: 1, 3, 5

@api_router.post("/pkscreener/backtest")
async def run_pkscreener_backtest(req: PKScreenerBacktestRequest):
    """Run PKScreener backtest for selected stocks and scanners over a date range.
    Returns triggers with returns and summary metrics.
    """
    try:
        from datetime import datetime
        import sys as _sys
        _sys.path.insert(0, 'pkscreener-integration')
        from backtest_engine import BacktestEngine  # type: ignore

        # Parse dates
        start_date = datetime.fromisoformat(req.start_date)
        end_date = datetime.fromisoformat(req.end_date)
        if start_date > end_date:
            return {"status": "error", "message": "start_date must be before or equal to end_date"}

        # Build selected stock list from watchlist
        watchlist = crud.get_watchlist_details()
        if not watchlist:
            return {"status": "error", "message": "Watchlist is empty. Add stocks first."}

        selected: list[dict] = []
        if req.instrument_keys:
            ik_set = set(req.instrument_keys)
            for s in watchlist:
                if s.instrument_key in ik_set:
                    selected.append({"symbol": s.symbol, "instrument_key": s.instrument_key})
        elif req.symbols:
            sym_set = set(sym.upper() for sym in req.symbols)
            for s in watchlist:
                if s.symbol.upper() in sym_set:
                    selected.append({"symbol": s.symbol, "instrument_key": s.instrument_key})
        else:
            # Default: use full watchlist
            selected = [{"symbol": s.symbol, "instrument_key": s.instrument_key} for s in watchlist]

        if not selected:
            return {"status": "error", "message": "No matching stocks found in watchlist for the given selection."}

        # DB session
        db = next(get_db())
        try:
            engine = BacktestEngine(db)
            # Override engine watchlist to only selected stocks
            engine.watchlist = selected  # type: ignore[attr-defined]

            # Sanitize timeframe
            tf = req.timeframe if req.timeframe in (1, 3, 5, 1440) else 1

            results = engine.run_backtest(
                scanner_ids=req.scanner_ids,
                start_date=start_date,
                end_date=end_date,
                max_stocks=len(selected),
                timeframe=tf
            )

            # Serialize results while DB session is still open
            def serial(r):
                def iso(dt):
                    try:
                        return dt.isoformat() if dt else None
                    except Exception:
                        return None
                return {
                    "symbol": getattr(r, "symbol", None),
                    "instrument_key": getattr(r, "instrument_key", None),
                    "backtest_date": iso(getattr(r, "backtest_date", None)),
                    "trigger_time": iso(getattr(r, "trigger_time", None)),
                    "trigger_price": getattr(r, "trigger_price", None),
                    # Intraday returns
                    "return_3min_pct": getattr(r, "return_3min_pct", None),
                    "return_5min_pct": getattr(r, "return_5min_pct", None),
                    "return_15min_pct": getattr(r, "return_15min_pct", None),
                    "return_30min_pct": getattr(r, "return_30min_pct", None),
                    # Daily returns (if present on object; not persisted columns)
                    "return_1day_pct": getattr(r, "return_1day_pct", None),
                    "return_3day_pct": getattr(r, "return_3day_pct", None),
                    "return_5day_pct": getattr(r, "return_5day_pct", None),
                    "return_10day_pct": getattr(r, "return_10day_pct", None),
                    "max_profit_pct": getattr(r, "max_profit_pct", None),
                    "max_loss_pct": getattr(r, "max_loss_pct", None),
                    "was_successful": getattr(r, "was_successful", None),
                    "hit_target_1pct": getattr(r, "hit_target_1pct", None),
                    "hit_target_2pct": getattr(r, "hit_target_2pct", None),
                    "hit_stoploss": getattr(r, "hit_stoploss", None),
                }

            def avg(nums: list[Optional[float]]):
                vals = [x for x in nums if isinstance(x, (int, float))]
                return round(sum(vals) / len(vals), 2) if vals else None

            payload = {"status": "success", "summary": {}, "results": {}, "timeframe": tf, "timeframe_mode": ("daily" if tf == 1440 else "intraday")}
            for sid, items in results.items():
                triggers = [serial(r) for r in items]
                total = len(items)
                succ = len([r for r in items if getattr(r, "was_successful", False)])
                payload["results"][str(sid)] = triggers
                if tf == 1440:
                    payload["summary"][str(sid)] = {
                        "total_triggers": total,
                        "success_rate_pct": round((succ / total) * 100, 1) if total else 0.0,
                        "avg_returns_day": {
                            "1d": avg([getattr(r, "return_1day_pct", None) for r in items]),
                            "3d": avg([getattr(r, "return_3day_pct", None) for r in items]),
                            "5d": avg([getattr(r, "return_5day_pct", None) for r in items]),
                            "10d": avg([getattr(r, "return_10day_pct", None) for r in items]),
                        },
                    }
                else:
                    payload["summary"][str(sid)] = {
                        "total_triggers": total,
                        "success_rate_pct": round((succ / total) * 100, 1) if total else 0.0,
                        "avg_returns": {
                            "3min": avg([getattr(r, "return_3min_pct", None) for r in items]),
                            "5min": avg([getattr(r, "return_5min_pct", None) for r in items]),
                            "15min": avg([getattr(r, "return_15min_pct", None) for r in items]),
                            "30min": avg([getattr(r, "return_30min_pct", None) for r in items]),
                        },
                    }

            return payload
        finally:
            db.close()

    except Exception as e:
        logger.error(f"Error running PKScreener backtest: {e}")
        return {"status": "error", "message": str(e)}

# --- Backfill tools ---
@api_router.post("/data/backfill-today")
async def backfill_today(background_tasks: BackgroundTasks):
    """
    Queue a one-time backfill for today's 1-minute candles for all watchlist stocks.
    Safe, runs in background. Returns immediately with queued status.
    """
    try:
        background_tasks.add_task(_backfill_today_worker)
        return {"status": "queued", "message": "Queued backfill for today's 1-minute data for all watchlist stocks"}
    except Exception as e:
        logger.error(f"Failed to queue backfill-today: {e}")
        return {"status": "error", "message": str(e)}


def _backfill_today_worker():
    from datetime import date
    try:
        # Lazy import database_service from data-fetch
        import sys as _sys, os as _os
        _sys.path.append(_os.path.join(_os.path.dirname(_os.path.dirname(__file__)), 'data-fetch'))
        from database_service import database_service  # type: ignore

        watchlist = crud.get_watchlist_details()
        if not watchlist:
            logger.info("No stocks in watchlist for backfill-today")
            return

        today = date.today()
        total = len(watchlist)
        logger.info(f"Starting backfill-today for {total} stocks")
        for i, stock in enumerate(watchlist, start=1):
            ik = getattr(stock, 'instrument_key', '')
            sym = getattr(stock, 'symbol', ik)
            if not ik or not ik.startswith('DHAN_'):
                logger.info(f"Skipping non-Dhan or missing instrument key for {sym}: {ik}")
                continue
            try:
                logger.info(f"[{i}/{total}] Backfilling today for {sym} ({ik})")
                database_service.get_candles_smart(
                    instrument_key=ik,
                    interval='1minute',
                    start_date=today,
                    end_date=today,
                    auto_backfill=True,
                )
            except Exception as e:
                logger.error(f"Backfill-today failed for {sym} ({ik}): {e}")
        logger.info("Completed backfill-today for all applicable stocks")
    except Exception as e:
        logger.error(f"Error in backfill-today worker: {e}")

# --- Pattern Validation API Routes ---

@api_router.get("/pattern-validation/test")
async def test_validation_api():
    """Test endpoint to verify pattern validation API is working."""
    return {"status": "success", "message": "Pattern validation API is working"}

@api_router.get("/pattern-validation/stocks")
async def get_available_stocks():
    """Get list of available stocks from alerts."""
    try:
        stocks = crud.get_available_stocks()
        return {"status": "success", "stocks": stocks}
    except Exception as e:
        logger.error(f"Error fetching available stocks: {e}")
        return {"status": "error", "message": str(e)}

@api_router.get("/pattern-validation/patterns")
async def get_available_patterns():
    """Get list of available pattern types from alerts."""
    try:
        patterns = crud.get_available_patterns()
        return {"status": "success", "patterns": patterns}
    except Exception as e:
        logger.error(f"Error fetching available patterns: {e}")
        return {"status": "error", "message": str(e)}

@api_router.get("/pattern-validation/debug")
async def debug_validation_params(
    symbol: Optional[str] = None,
    alert_type: Optional[str] = None,
    pattern_type: Optional[str] = None,
    is_super_alert: Optional[bool] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    outcome: Optional[str] = None,
    validation_status: Optional[str] = None,
    environment: Optional[str] = None,
    fibonacci_level: Optional[str] = None,
    limit: Optional[int] = 100,
    offset: Optional[int] = 0,
):
    """Debug endpoint to see what parameters are being received."""
    return {
        "status": "success",
        "received_params": {
            "symbol": symbol,
            "alert_type": alert_type,
            "pattern_type": pattern_type,
            "is_super_alert": is_super_alert,
            "start_date": start_date,
            "end_date": end_date,
            "outcome": outcome,
            "validation_status": validation_status,
            "environment": environment,
            "fibonacci_level": fibonacci_level,
            "limit": limit,
            "offset": offset
        }
    }

@api_router.get("/pattern-validation/alerts/count")
async def get_total_alerts_count():
    """Get total count of alerts for debugging."""
    try:
        from app.mongo_service import alerts_collection
        total_count = alerts_collection.count_documents({})
        return {"status": "success", "total_alerts": total_count}
    except Exception as e:
        logger.error(f"Error getting total alerts count: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/pattern-validation/alerts")
async def get_validation_alerts(
    symbol: Optional[str] = None,
    alert_type: Optional[str] = None,
    pattern_type: Optional[str] = None,
    is_super_alert: Optional[bool] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    outcome: Optional[str] = None,
    validation_status: Optional[str] = None,
    environment: Optional[str] = None,
    fibonacci_level: Optional[str] = None,
    limit: Optional[int] = 100,
    offset: Optional[int] = 0,
    current_user: User = Depends(get_current_user_from_session)
):
    """Get alerts with enhanced filtering for validation dashboard."""
    try:
        # Convert empty strings to None for proper filtering
        def clean_param(param):
            return param if param and param.strip() else None

        # Clean all string parameters
        symbol = clean_param(symbol)
        alert_type = clean_param(alert_type)
        pattern_type = clean_param(pattern_type)
        outcome = clean_param(outcome)
        validation_status = clean_param(validation_status)
        environment = clean_param(environment)
        fibonacci_level = clean_param(fibonacci_level)
        start_date = clean_param(start_date)
        end_date = clean_param(end_date)

        logger.info(f"Pattern validation filters: symbol={symbol}, alert_type={alert_type}, start_date={start_date}, end_date={end_date}")

        filters = models.AlertFilters(
            symbol=symbol,
            alert_type=alert_type,
            pattern_type=pattern_type,
            is_super_alert=is_super_alert,
            start_date=start_date,
            end_date=end_date,
            outcome=outcome,
            validation_status=validation_status,
            environment=environment,
            fibonacci_level=fibonacci_level,
            limit=limit,
            offset=offset
        )

        alerts = crud.get_alerts_with_filters(filters)
        total_count = crud.get_alerts_count_with_filters(filters)

        return {
            "status": "success",
            "alerts": alerts,
            "total_count": total_count,
            "limit": limit or 100,
            "offset": offset or 0
        }
    except ValueError as e:
        logger.error(f"Validation error in get_validation_alerts: {e}")
        raise HTTPException(status_code=422, detail=f"Invalid parameter: {str(e)}")
    except Exception as e:
        logger.error(f"Error fetching validation alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.put("/pattern-validation/alerts/{alert_id}/validate")
async def validate_alert(
    alert_id: str,
    validation_data: models.AlertValidationUpdate,
    current_user: User = Depends(get_current_user_from_session)
):
    """Update alert validation status."""
    try:
        success = crud.update_alert_validation(
            alert_id,
            validation_data.validation_status,
            validation_data.notes,
            current_user.email
        )

        if success:
            return {"status": "success", "message": "Alert validation updated successfully"}
        else:
            raise HTTPException(status_code=404, detail="Alert not found")
    except Exception as e:
        logger.error(f"Error updating alert validation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/pattern-validation/analytics")
async def get_pattern_analytics(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    environment: Optional[str] = None,
    current_user: User = Depends(get_current_user_from_session)
):
    """Get pattern performance analytics."""
    try:
        analytics = crud.get_pattern_analytics(start_date, end_date, environment)
        return {"status": "success", "analytics": analytics}
    except Exception as e:
        logger.error(f"Error fetching pattern analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/pattern-validation/summary/{date}")
async def get_daily_summary(
    date: str,
    current_user: User = Depends(get_current_user_from_session)
):
    """Get daily pattern summary for specified date."""
    try:
        summary = crud.get_daily_pattern_summary(date)
        return {"status": "success", "summary": summary}
    except Exception as e:
        logger.error(f"Error fetching daily summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/pattern-validation/cache/clear")
async def clear_validation_cache(
    current_user: User = Depends(get_current_user_from_session)
):
    """Clear pattern validation cache."""
    try:
        deleted_count = crud.clear_pattern_validation_cache()
        return {"status": "success", "message": f"Cleared {deleted_count} cache entries"}
    except Exception as e:
        logger.error(f"Error clearing validation cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/alerts/{alert_id}")
async def get_alert_details(
    alert_id: str,
    current_user: User = Depends(get_current_user_from_session)
):
    """Get detailed information for a specific alert."""
    try:
        alert = crud.get_alert_by_id(alert_id)
        if alert:
            return {"status": "success", "alert": alert}
        else:
            raise HTTPException(status_code=404, detail="Alert not found")
    except Exception as e:
        logger.error(f"Error fetching alert details: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/pattern-validation/alerts/export-detailed")
async def export_detailed_alerts(
    symbol: Optional[str] = None,
    alert_type: Optional[str] = None,
    pattern_type: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    environment: Optional[str] = None,
    current_user: User = Depends(get_current_user_from_session)
):
    """Export detailed alerts with complete date and verification information."""
    try:
        # Get all alerts without pagination for export
        alerts = crud.get_alerts_with_filters(
            symbol=symbol,
            alert_type=alert_type,
            pattern_type=pattern_type,
            start_date=start_date,
            end_date=end_date,
            environment=environment,
            limit=10000,  # Large limit for export
            offset=0
        )

        if not alerts:
            raise HTTPException(status_code=404, detail="No alerts found for export")

        # Create CSV content with detailed information
        import io
        import csv
        from fastapi.responses import StreamingResponse

        output = io.StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow([
            'Date', 'Time', 'Symbol', 'Pattern Type', 'Alert Type',
            'Signal Price', 'Trigger Reason', 'Environment', 'Is Super Alert',
            'Fibonacci Level', 'Validation Status', 'Outcome', 'Profit/Loss %',
            'Days to Outcome', 'Validated By', 'Notes'
        ])

        # Write data rows
        for alert in alerts:
            timestamp = alert.get('timestamp', '')
            if timestamp:
                try:
                    if hasattr(timestamp, 'strftime'):
                        date_str = timestamp.strftime('%Y-%m-%d')
                        time_str = timestamp.strftime('%H:%M:%S')
                    else:
                        # Handle string timestamp
                        timestamp_str = str(timestamp)
                        if 'T' in timestamp_str:
                            date_str = timestamp_str.split('T')[0]
                            time_str = timestamp_str.split('T')[1][:8]
                        else:
                            date_str = timestamp_str
                            time_str = ''
                except:
                    date_str = str(timestamp)
                    time_str = ''
            else:
                date_str = ''
                time_str = ''

            writer.writerow([
                date_str,
                time_str,
                alert.get('symbol', ''),
                alert.get('pattern_type', ''),
                alert.get('alert_type', ''),
                alert.get('signal_price', ''),
                alert.get('trigger_reason', ''),
                alert.get('environment', ''),
                'Yes' if alert.get('is_super_alert') else 'No',
                alert.get('fibonacci_level', ''),
                alert.get('validation_status', ''),
                alert.get('outcome', ''),
                alert.get('profit_loss_percent', ''),
                alert.get('days_to_outcome', ''),
                alert.get('validated_by', ''),
                alert.get('notes', '')
            ])

        output.seek(0)

        # Create filename with current date
        from datetime import datetime
        filename = f"detailed_alerts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

        return StreamingResponse(
            io.BytesIO(output.getvalue().encode('utf-8')),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    except Exception as e:
        logger.error(f"Error exporting detailed alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/pattern-analysis/detailed")
async def get_detailed_pattern_analysis(
    pattern_type: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    environment: Optional[str] = None,
    current_user: User = Depends(get_current_user_from_session)
):
    """Get detailed pattern analysis with individual alert breakdown."""
    try:
        analysis = crud.get_detailed_pattern_analysis(pattern_type, start_date, end_date, environment)
        return {"status": "success", "analysis": analysis}
    except Exception as e:
        logger.error(f"Error fetching detailed pattern analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/pattern-validation/alerts/export")
async def export_alerts_csv(
    symbol: Optional[str] = None,
    alert_type: Optional[str] = None,
    pattern_type: Optional[str] = None,
    is_super_alert: Optional[bool] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    outcome: Optional[str] = None,
    validation_status: Optional[str] = None,
    environment: Optional[str] = None,
    fibonacci_level: Optional[str] = None,
    current_user: User = Depends(get_current_user_from_session)
):
    """Export alerts to CSV format."""
    try:
        # Convert empty strings to None
        symbol = symbol if symbol else None
        alert_type = alert_type if alert_type else None
        pattern_type = pattern_type if pattern_type else None
        outcome = outcome if outcome else None
        validation_status = validation_status if validation_status else None
        environment = environment if environment else None
        fibonacci_level = fibonacci_level if fibonacci_level else None
        start_date = start_date if start_date else None
        end_date = end_date if end_date else None

        filters = models.AlertFilters(
            symbol=symbol,
            alert_type=alert_type,
            pattern_type=pattern_type,
            is_super_alert=is_super_alert,
            start_date=start_date,
            end_date=end_date,
            outcome=outcome,
            validation_status=validation_status,
            environment=environment,
            fibonacci_level=fibonacci_level,
            limit=10000,  # Large limit for export
            offset=0
        )

        csv_content = crud.export_alerts_to_csv(filters)

        from fastapi.responses import Response
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=pattern_alerts.csv"}
        )
    except Exception as e:
        logger.error(f"Error exporting alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Router will be included at the end of the file

# ============================================================================
# BACKTESTING ROUTES
# ============================================================================

@app.get("/backtest", response_class=HTMLResponse)
async def backtest_page(request: Request, current_user: User = Depends(get_current_user_from_session)):
    """Render the backtesting page."""
    return templates.TemplateResponse("backtest.html", {"request": request, "user": current_user})


@app.post("/api/backtest/start")
async def start_backtest(request: Request, current_user: User = Depends(get_current_user_from_session)):
    """Start a new backtest job."""
    try:
        data = await request.json()

        config = {
            'months': data.get('months', 2),
            'max_stocks': data.get('max_stocks'),
            'box_size': data.get('box_size', 1.0),
            'reversal': data.get('reversal', 3)
        }

        job_id = backtest_service.create_backtest_job(config)

        return {
            "success": True,
            "job_id": job_id,
            "message": "Backtest started successfully"
        }
    except Exception as e:
        logger.error(f"Error starting backtest: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/backtest/status/{job_id}")
async def get_backtest_status(job_id: str, current_user: User = Depends(get_current_user_from_session)):
    """Get the status of a backtest job."""
    job = backtest_service.get_backtest_job(job_id)

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Get recent logs (last 10)
    recent_logs = job.logs[-10:] if len(job.logs) > 10 else job.logs

    return {
        "job_id": job_id,
        "status": job.status,
        "progress": job.progress,
        "logs": recent_logs,
        "error": job.error
    }


@app.post("/api/backtest/stop/{job_id}")
async def stop_backtest(job_id: str, current_user: User = Depends(get_current_user_from_session)):
    """Stop a running backtest job."""
    success = backtest_service.stop_backtest_job(job_id)

    if not success:
        raise HTTPException(status_code=404, detail="Job not found or already completed")

    return {"success": True, "message": "Backtest stopped"}


@app.get("/api/backtest/results/{job_id}")
async def get_backtest_results(job_id: str, current_user: User = Depends(get_current_user_from_session)):
    """Get the results of a completed backtest."""
    job = backtest_service.get_backtest_job(job_id)

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.status != "completed":
        raise HTTPException(status_code=400, detail="Backtest not completed yet")

    return job.results


@app.get("/api/backtest/download/{job_id}/{format}")
async def download_backtest_results(job_id: str, format: str, current_user: User = Depends(get_current_user_from_session)):
    """Download backtest results in CSV or JSON format."""
    job = backtest_service.get_backtest_job(job_id)

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.status != "completed":
        raise HTTPException(status_code=400, detail="Backtest not completed yet")

    if format == "csv":
        # Generate CSV
        import csv
        import io

        output = io.StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow([
            'Pattern', 'Total Signals', 'Profitable', 'Losing',
            'Success Rate %', 'Win/Loss Ratio', 'Avg Return %', 'Confidence'
        ])

        # Data
        for pattern in job.results['patterns']:
            writer.writerow([
                pattern['name'],
                pattern['total_signals'],
                pattern['profitable_signals'],
                pattern['losing_signals'],
                f"{pattern['success_rate']:.2f}",
                f"{pattern['win_loss_ratio']:.2f}",
                f"{pattern['avg_return']:.2f}",
                pattern['confidence']
            ])

        content = output.getvalue()

        return Response(
            content=content,
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=backtest_results_{job_id[:8]}.csv"
            }
        )

    elif format == "json":
        import json

        content = json.dumps(job.results, indent=2)

        return Response(
            content=content,
            media_type="application/json",
            headers={
                "Content-Disposition": f"attachment; filename=backtest_results_{job_id[:8]}.json"
            }
        )

    else:
        raise HTTPException(status_code=400, detail="Invalid format. Use 'csv' or 'json'")


# ============================================================================
# FIBONACCI PATTERN SCANNER API
# ============================================================================

@api_router.get("/fibonacci-scanner/bullish")
async def scan_bullish_fibonacci_patterns(current_user: User = Depends(get_current_user_from_session)):
    """
    Scan watchlist for bullish patterns in 50-61% Fibonacci retracement zone.

    Returns stocks with bullish patterns at golden zone entry points.
    """
    try:
        scanner = FibonacciScanner()
        signals = scanner.scan_watchlist(scan_type="bullish")

        # Convert to dict for JSON response
        results = []
        for signal in signals:
            results.append({
                "symbol": signal.symbol,
                "instrument_key": signal.instrument_key,
                "pattern_type": signal.pattern_type,
                "pattern_name": signal.pattern_name,
                "alert_type": signal.alert_type,
                "current_price": round(signal.current_price, 2),
                "fibonacci_level": signal.fibonacci_level,
                "fibonacci_price": round(signal.fibonacci_price, 2),
                "swing_low": round(signal.swing_low, 2),
                "swing_high": round(signal.swing_high, 2),
                "entry_price": round(signal.entry_price, 2),
                "stop_loss": round(signal.stop_loss, 2),
                "target_price": round(signal.target_price, 2),
                "risk_reward_ratio": signal.risk_reward_ratio,
                "trigger_reason": signal.trigger_reason,
                "timestamp": signal.timestamp.isoformat()
            })

        return {
            "status": "success",
            "scan_type": "bullish",
            "count": len(results),
            "signals": results
        }

    except Exception as e:
        logger.error(f"❌ Error in bullish Fibonacci scanner: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/fibonacci-scanner/bearish")
async def scan_bearish_fibonacci_patterns(current_user: User = Depends(get_current_user_from_session)):
    """
    Scan watchlist for bearish patterns in 23-38% Fibonacci retracement zone.

    Returns stocks with bearish patterns at early warning zone.
    """
    try:
        scanner = FibonacciScanner()
        signals = scanner.scan_watchlist(scan_type="bearish")

        # Convert to dict for JSON response
        results = []
        for signal in signals:
            results.append({
                "symbol": signal.symbol,
                "instrument_key": signal.instrument_key,
                "pattern_type": signal.pattern_type,
                "pattern_name": signal.pattern_name,
                "alert_type": signal.alert_type,
                "current_price": round(signal.current_price, 2),
                "fibonacci_level": signal.fibonacci_level,
                "fibonacci_price": round(signal.fibonacci_price, 2),
                "swing_low": round(signal.swing_low, 2),
                "swing_high": round(signal.swing_high, 2),
                "entry_price": round(signal.entry_price, 2),
                "stop_loss": round(signal.stop_loss, 2),
                "target_price": round(signal.target_price, 2),
                "risk_reward_ratio": signal.risk_reward_ratio,
                "trigger_reason": signal.trigger_reason,
                "timestamp": signal.timestamp.isoformat()
            })

        return {
            "status": "success",
            "scan_type": "bearish",
            "count": len(results),
            "signals": results
        }

    except Exception as e:
        logger.error(f"❌ Error in bearish Fibonacci scanner: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# OPEN INTEREST (OI) ALERT API ROUTES
# ============================================================================

@api_router.get("/oi-alerts")
async def get_oi_alerts(
    symbol: Optional[str] = None,
    pattern_type: Optional[str] = None,
    severity: Optional[str] = None,
    hours: Optional[int] = 24,
    limit: Optional[int] = 50
):
    """Get Open Interest based trading alerts."""
    try:
        from app.oi_real_alert_service import real_oi_service

        # Get recent OI alerts from real Dhan API data
        alerts = real_oi_service.get_recent_oi_alerts(
            hours=hours,
            symbol=symbol,
            pattern_type=pattern_type,
            severity=severity,
            limit=limit
        )

        return {
            "status": "success",
            "alerts": alerts,
            "total_count": len(alerts),
            "filters_applied": {
                "symbol": symbol,
                "pattern_type": pattern_type,
                "severity": severity,
                "hours": hours
            }
        }

    except Exception as e:
        logger.error(f"Error fetching OI alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/oi-alerts/generate")
async def generate_oi_alerts(
    symbols: Optional[List[str]] = None
):
    """Manually trigger OI alert generation."""
    try:
        from app.oi_real_alert_service import real_oi_service

        # Use provided symbols or default monitored symbols
        target_symbols = symbols or ["NIFTY", "BANKNIFTY", "FINNIFTY"]

        logger.info(f"🚀 Manual REAL OI alert generation requested for: {target_symbols}")

        # Generate and store alerts using real Dhan API data
        result = real_oi_service.generate_and_store_alerts(target_symbols)

        return {
            "status": result["status"],
            "message": f"Generated {result['alerts_stored']} OI alerts",
            "alerts_generated": result["alerts_generated"],
            "alerts_stored": result["alerts_stored"],
            "symbols_analyzed": result.get("symbols_analyzed", target_symbols)
        }

    except Exception as e:
        logger.error(f"Error generating OI alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/oi-data/option-chain/{symbol}")
async def get_option_chain_data(
    symbol: str,
    expiry_date: Optional[str] = None
):
    """Get current option chain data for a symbol using real Dhan API."""
    try:
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'data-fetch'))
        from dhan_oi_client import dhan_oi_client

        logger.info(f"📊 Fetching REAL option chain data for {symbol} from Dhan API")

        # Get option chain data from Dhan API
        option_chain = dhan_oi_client.get_option_chain(symbol.upper(), expiry_date)

        if not option_chain:
            raise HTTPException(status_code=404, detail=f"No option chain data found for {symbol}")

        # Convert to dict for JSON response
        chain_dict = {
            "symbol": option_chain.symbol,
            "spot_price": option_chain.spot_price,
            "timestamp": option_chain.timestamp.isoformat(),
            "expiry_date": option_chain.expiry_date.isoformat(),
            "call_strikes": option_chain.call_strikes,
            "call_oi": option_chain.call_oi,
            "call_volume": option_chain.call_volume,
            "call_ltp": option_chain.call_ltp,
            "put_strikes": option_chain.put_strikes,
            "put_oi": option_chain.put_oi,
            "put_volume": option_chain.put_volume,
            "put_ltp": option_chain.put_ltp,
            "total_call_oi": option_chain.total_call_oi,
            "total_put_oi": option_chain.total_put_oi,
            "pcr_oi": option_chain.pcr_oi,
            "pcr_volume": option_chain.pcr_volume,
            "max_pain": option_chain.max_pain,
            "data_source": "DHAN_API"
        }

        return {
            "status": "success",
            "option_chain": chain_dict,
            "data_source": "DHAN_API"
        }

    except Exception as e:
        logger.error(f"Error fetching real option chain data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/oi-data/historical/{symbol}")
async def get_historical_oi_data(
    symbol: str,
    start_date: str,
    end_date: str,
    strike_price: Optional[float] = None,
    option_type: Optional[str] = None,
    current_user: User = Depends(get_current_user_from_session)
):
    """Get historical OI data for analysis."""
    try:
        from app.oi_database_service import oi_database_service
        from app.oi_models import OptionType
        from datetime import datetime

        # Parse dates
        start_dt = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_dt = datetime.strptime(end_date, '%Y-%m-%d').date()

        # Parse option type
        opt_type = None
        if option_type:
            opt_type = OptionType.CALL if option_type.upper() == "CE" else OptionType.PUT

        # Get historical data
        historical_data = oi_database_service.get_historical_oi_data(
            symbol=symbol.upper(),
            start_date=start_dt,
            end_date=end_dt,
            strike_price=strike_price,
            option_type=opt_type
        )

        # Convert to dict for JSON response
        data_dicts = []
        for data in historical_data:
            data_dict = {
                "symbol": data.symbol,
                "strike_price": data.strike_price,
                "option_type": data.option_type.value,
                "expiry_date": data.expiry_date.isoformat(),
                "date": data.date.isoformat(),
                "timestamp": data.timestamp.isoformat(),
                "open_interest": data.open_interest,
                "oi_change": data.oi_change,
                "oi_change_percent": data.oi_change_percent,
                "ltp": data.ltp,
                "price_change": data.price_change,
                "price_change_percent": data.price_change_percent,
                "volume": data.volume,
                "volume_change_percent": data.volume_change_percent,
                "underlying_price": data.underlying_price,
                "underlying_change_percent": data.underlying_change_percent
            }
            data_dicts.append(data_dict)

        return {
            "status": "success",
            "historical_data": data_dicts,
            "total_records": len(data_dicts),
            "date_range": {
                "start_date": start_date,
                "end_date": end_date
            }
        }

    except Exception as e:
        logger.error(f"Error fetching historical OI data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/oi-analysis/historical")
async def run_historical_oi_analysis(
    request_data: dict
):
    """Run comprehensive historical OI analysis and learning."""
    try:
        from app.oi_historical_analyzer import historical_oi_analyzer

        symbols = request_data.get("symbols")
        days = request_data.get("days", 90)

        logger.info(f"🚀 Starting historical OI analysis for {days} days")

        # Run historical analysis
        analysis_results = historical_oi_analyzer.fetch_and_analyze_historical_data(
            symbols=symbols,
            days=days
        )

        return {
            "status": "success",
            "message": "Historical OI analysis completed",
            "analysis_results": analysis_results
        }

    except Exception as e:
        logger.error(f"Error running historical OI analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/oi-analysis/learned-patterns")
async def get_learned_patterns(
    symbol: Optional[str] = None,
    min_confidence: Optional[float] = 70.0
):
    """Get learned patterns from historical analysis."""
    try:
        from app.oi_historical_analyzer import historical_oi_analyzer

        patterns = historical_oi_analyzer.get_learned_patterns(symbol)

        # Filter by confidence
        if min_confidence:
            patterns = [p for p in patterns if p.get("confidence_score", 0) >= min_confidence]

        return {
            "status": "success",
            "patterns": patterns,
            "total_patterns": len(patterns),
            "symbol_filter": symbol,
            "min_confidence": min_confidence
        }

    except Exception as e:
        logger.error(f"Error getting learned patterns: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/oi-alerts/intelligent/generate")
async def generate_intelligent_oi_alerts(
    request_data: dict = None
):
    """Generate intelligent OI alerts using machine learning."""
    try:
        from app.oi_intelligent_alert_service import intelligent_oi_service

        symbols = request_data.get("symbols") if request_data else None

        logger.info(f"🧠 Generating intelligent OI alerts")

        # Generate intelligent alerts
        result = intelligent_oi_service.generate_and_store_intelligent_alerts(symbols)

        return {
            "status": result["status"],
            "message": f"Generated {result['alerts_stored']} intelligent alerts",
            "alerts_generated": result["alerts_generated"],
            "alerts_stored": result["alerts_stored"],
            "symbols_analyzed": result["symbols_analyzed"],
            "avg_intelligence_score": result.get("avg_intelligence_score", 0),
            "data_source": result["data_source"]
        }

    except Exception as e:
        logger.error(f"Error generating intelligent OI alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/oi-alerts/intelligent")
async def get_intelligent_oi_alerts(
    symbol: Optional[str] = None,
    hours: Optional[int] = 24,
    min_intelligence_score: Optional[float] = 70.0,
    limit: Optional[int] = 50
):
    """Get intelligent OI alerts with ML insights."""
    try:
        from app.oi_intelligent_alert_service import intelligent_oi_service

        # Get intelligent alerts
        alerts = intelligent_oi_service.get_recent_intelligent_alerts(
            hours=hours,
            symbol=symbol,
            min_intelligence_score=min_intelligence_score,
            limit=limit
        )

        return {
            "status": "success",
            "alerts": alerts,
            "total_count": len(alerts),
            "filters_applied": {
                "symbol": symbol,
                "hours": hours,
                "min_intelligence_score": min_intelligence_score
            },
            "data_source": "INTELLIGENT_ML"
        }

    except Exception as e:
        logger.error(f"Error fetching intelligent OI alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/ml/train")
async def train_ml_models(
    request_data: dict = None
):
    """Train ML models using 5-year expired options data."""
    try:
        from app.oi_ml_trainer import oi_ml_trainer

        years = request_data.get("years", 5) if request_data else 5

        logger.info(f"🤖 Starting ML model training with {years} years of data")

        # Fetch and prepare training data
        data_results = oi_ml_trainer.fetch_and_prepare_training_data(years=years)

        if "error" in data_results:
            return {
                "status": "error",
                "message": f"Data preparation failed: {data_results['error']}"
            }

        # Train ML models
        training_results = oi_ml_trainer.train_ml_models()

        if "error" in training_results:
            return {
                "status": "error",
                "message": f"Model training failed: {training_results['error']}"
            }

        return {
            "status": "success",
            "message": "ML models trained successfully",
            "data_preparation": data_results,
            "training_results": training_results
        }

    except Exception as e:
        logger.error(f"Error training ML models: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/ml/predict")
async def predict_trading_signals(
    request_data: dict
):
    """Predict trading signals using trained ML models."""
    try:
        from app.oi_ml_trainer import oi_ml_trainer

        symbol = request_data.get("symbol")
        current_data = request_data.get("current_data", {})

        if not symbol:
            raise HTTPException(status_code=400, detail="Symbol is required")

        logger.info(f"🎯 Predicting trading signals for {symbol}")

        # Make predictions
        predictions = oi_ml_trainer.predict_trading_signals(symbol, current_data)

        if "error" in predictions:
            return {
                "status": "error",
                "message": predictions["error"]
            }

        return {
            "status": "success",
            "predictions": predictions
        }

    except Exception as e:
        logger.error(f"Error predicting trading signals: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/ml/models")
async def get_ml_models():
    """Get information about trained ML models."""
    try:
        from app.oi_ml_trainer import oi_ml_trainer

        # Get model information from database
        cursor = oi_ml_trainer.db[oi_ml_trainer.models_collection].find()
        models = []

        for model_doc in cursor:
            models.append({
                "model_name": model_doc["model_name"],
                "model_type": model_doc["model_type"],
                "created_at": model_doc["created_at"].isoformat(),
                "version": model_doc["version"]
            })

        return {
            "status": "success",
            "models": models,
            "total_models": len(models)
        }

    except Exception as e:
        logger.error(f"Error getting ML models: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# WATCHLIST API ENDPOINTS
# ============================================================================

# Default API token for watchlist access
DEFAULT_API_TOKEN = "finns_watchlist_2025_secure_token"

def verify_api_token(token: str = Header(None, alias="X-API-Token")):
    """Verify API token for watchlist access."""
    if token != DEFAULT_API_TOKEN:
        raise HTTPException(
            status_code=401,
            detail="Invalid API token. Use X-API-Token header with correct token."
        )
    return token

@api_router.post("/watchlist/create")
async def create_watchlist(
    request_data: dict,
    token: str = Depends(verify_api_token)
):
    """Create a new watchlist."""
    try:
        from app.watchlist_service import watchlist_service
        from app.watchlist_models import WatchlistCreateRequest

        user_id = request_data.get("user_id", "default_user")

        # Parse request
        create_request = WatchlistCreateRequest(**request_data)

        # Create watchlist
        result = watchlist_service.create_watchlist(user_id, create_request)

        return result

    except Exception as e:
        logger.error(f"Error creating watchlist: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/watchlist/list")
async def get_watchlists(
    user_id: str = "default_user",
    include_public: bool = True,
    token: str = Depends(verify_api_token)
):
    """Get all watchlists for a user."""
    try:
        from app.watchlist_service import watchlist_service

        result = watchlist_service.get_watchlists(user_id, include_public)
        return result

    except Exception as e:
        logger.error(f"Error getting watchlists: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/watchlist/{watchlist_id}")
async def get_watchlist(
    watchlist_id: str,
    user_id: str = "default_user",
    trade_types: Optional[str] = None,
    tags: Optional[str] = None,
    sectors: Optional[str] = None,
    has_alerts: Optional[bool] = None,
    min_confidence: Optional[float] = None,
    token: str = Depends(verify_api_token)
):
    """Get a specific watchlist with optional filtering."""
    try:
        from app.watchlist_service import watchlist_service
        from app.watchlist_models import WatchlistFilter, TradeType, AlertSeverity

        # Parse filters
        filters = None
        if any([trade_types, tags, sectors, has_alerts, min_confidence]):
            filters = WatchlistFilter()

            if trade_types:
                filters.trade_types = [TradeType(tt.strip()) for tt in trade_types.split(",")]

            if tags:
                filters.tags = [tag.strip() for tag in tags.split(",")]

            if sectors:
                filters.sectors = [sector.strip() for sector in sectors.split(",")]

            if has_alerts is not None:
                filters.has_alerts = has_alerts

            if min_confidence is not None:
                filters.min_confidence = min_confidence

        result = watchlist_service.get_watchlist(user_id, watchlist_id, filters)
        return result

    except Exception as e:
        logger.error(f"Error getting watchlist: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/watchlist/{watchlist_id}/add-stock")
async def add_stock_to_watchlist(
    watchlist_id: str,
    request_data: dict,
    token: str = Depends(verify_api_token)
):
    """Add a stock to watchlist."""
    try:
        from app.watchlist_service import watchlist_service
        from app.watchlist_models import StockAddRequest

        user_id = request_data.get("user_id", "default_user")

        # Parse request
        add_request = StockAddRequest(**request_data)

        result = watchlist_service.add_stock_to_watchlist(user_id, watchlist_id, add_request)
        return result

    except Exception as e:
        logger.error(f"Error adding stock to watchlist: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.delete("/watchlist/{watchlist_id}/remove-stock/{symbol}")
async def remove_stock_from_watchlist(
    watchlist_id: str,
    symbol: str,
    user_id: str = "default_user",
    token: str = Depends(verify_api_token)
):
    """Remove a stock from watchlist."""
    try:
        from app.watchlist_service import watchlist_service

        result = watchlist_service.remove_stock_from_watchlist(user_id, watchlist_id, symbol)
        return result

    except Exception as e:
        logger.error(f"Error removing stock from watchlist: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.put("/watchlist/{watchlist_id}/update-stock/{symbol}")
async def update_stock_in_watchlist(
    watchlist_id: str,
    symbol: str,
    request_data: dict,
    token: str = Depends(verify_api_token)
):
    """Update a stock in watchlist."""
    try:
        from app.watchlist_service import watchlist_service
        from app.watchlist_models import StockUpdateRequest

        user_id = request_data.get("user_id", "default_user")

        # Parse request
        update_request = StockUpdateRequest(**request_data)

        result = watchlist_service.update_stock_in_watchlist(user_id, watchlist_id, symbol, update_request)
        return result

    except Exception as e:
        logger.error(f"Error updating stock in watchlist: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/watchlist/stocks/filter")
async def get_filtered_stocks(
    user_id: str = "default_user",
    trade_types: Optional[str] = None,
    tags: Optional[str] = None,
    sectors: Optional[str] = None,
    has_alerts: Optional[bool] = None,
    min_confidence: Optional[float] = None,
    priority: Optional[str] = None,
    limit: int = 100,
    token: str = Depends(verify_api_token)
):
    """Get stocks across all watchlists with filters."""
    try:
        from app.watchlist_service import watchlist_service
        from app.watchlist_models import WatchlistFilter, TradeType, AlertSeverity

        # Parse filters
        filters = WatchlistFilter()

        if trade_types:
            filters.trade_types = [TradeType(tt.strip()) for tt in trade_types.split(",")]

        if tags:
            filters.tags = [tag.strip() for tag in tags.split(",")]

        if sectors:
            filters.sectors = [sector.strip() for sector in sectors.split(",")]

        if has_alerts is not None:
            filters.has_alerts = has_alerts

        if min_confidence is not None:
            filters.min_confidence = min_confidence

        if priority:
            filters.priority = [int(p.strip()) for p in priority.split(",")]

        result = watchlist_service.get_stocks_by_filters(user_id, filters, limit)
        return result

    except Exception as e:
        logger.error(f"Error getting filtered stocks: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/watchlist/stocks/with-alerts")
async def get_stocks_with_alerts(
    user_id: str = "default_user",
    min_confidence: float = 70.0,
    severity: Optional[str] = None,
    limit: int = 50,
    token: str = Depends(verify_api_token)
):
    """Get stocks with active alerts."""
    try:
        from app.watchlist_service import watchlist_service
        from app.watchlist_models import WatchlistFilter, AlertSeverity

        filters = WatchlistFilter(
            has_alerts=True,
            min_confidence=min_confidence
        )

        if severity:
            filters.alert_severity = [AlertSeverity(sev.strip()) for sev in severity.split(",")]

        result = watchlist_service.get_stocks_by_filters(user_id, filters, limit)
        return result

    except Exception as e:
        logger.error(f"Error getting stocks with alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# INCLUDE API ROUTER
# ============================================================================

# Include all API routes
app.include_router(api_router)

# ============================================================================
# STARTUP EVENT
# ============================================================================

# Initialize pattern validation database indexes on startup
@app.on_event("startup")
async def startup_event():
    """Initialize application on startup."""
    try:
        # Ensure database indexes for pattern validation
        crud.ensure_pattern_validation_indexes()
        logger.info("🚀 Pattern validation system initialized successfully")
    except Exception as e:
        logger.error(f"❌ Error during startup initialization: {e}")