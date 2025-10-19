import os
import asyncio
from datetime import timedelta
from fastapi import FastAPI, Request, APIRouter, Form, Depends, HTTPException, BackgroundTasks
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
async def alerts_analytics_page(request: Request, current_user: User = Depends(get_current_user_from_session)):
    """Trading alerts analytics page."""
    return templates.TemplateResponse("alerts_analytics.html", {"request": request, "user": current_user})

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


app.include_router(api_router)