"""
Pydantic models for API requests/responses.
All data is stored in MongoDB - no SQLAlchemy models needed.
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Union
from datetime import datetime

# --- Pydantic Models (for API requests/responses) ---
class AddStockRequest(BaseModel):
    """Request model for adding a new stock to the watchlist."""
    instrument_key: str
    symbol: str
    target_price: Optional[float] = None
    stoploss: Optional[float] = None
    trade_type: str  # e.g., "Bullish" or "Bearish"
    tags: str        # Comma-separated string of tags

class WatchlistStock(BaseModel):
    """Represents a single stock in the watchlist with all its details."""
    instrument_key: str
    symbol: str
    company_name: Optional[str] = None
    target_price: Optional[float] = None
    stoploss: Optional[float] = None
    trade_type: str
    tags: str
    added_at: datetime
    ltp: Optional[float] = None  # To be populated with the live Last Traded Price
    latest_alert: Optional[dict] = None

class Settings(BaseModel):
    rsi_threshold: int
    telegram_alerts_enabled: bool

    # Alert type preferences
    enable_pattern_alerts: Optional[bool] = True
    enable_rsi_alerts: Optional[bool] = False
    enable_super_alerts_only: Optional[bool] = False

    # Pattern-specific preferences
    enable_double_top_bottom: Optional[bool] = True
    enable_triple_top_bottom: Optional[bool] = True
    enable_quadruple_top_bottom: Optional[bool] = True
    enable_pole_patterns: Optional[bool] = True
    enable_catapult_patterns: Optional[bool] = True
    enable_turtle_patterns: Optional[bool] = True
    enable_aft_patterns: Optional[bool] = True
    enable_tweezer_patterns: Optional[bool] = True
    enable_abc_patterns: Optional[bool] = True
    enable_ziddi_patterns: Optional[bool] = True

    # API Configuration (optional)
    dhan_access_token: Optional[str] = None

# --- Alert Pydantic Models ---
class AlertResponse(BaseModel):
    """Response model for alert data."""
    id: Optional[int] = None  # Made optional for MongoDB compatibility
    symbol: str
    instrument_key: Optional[str] = None
    alert_type: str  # 'BUY', 'SELL'
    pattern_type: str
    pattern_name: str
    signal_price: float
    trigger_reason: str
    is_super_alert: bool
    pnf_matrix_score: Optional[int] = None
    fibonacci_level: Optional[str] = None
    column_number: Optional[int] = None
    timestamp: datetime
    environment: str = "LOCAL"  # PRODUCTION, LOCAL, TEST

    # Analysis fields
    accuracy_checked: bool = False  # Default value for MongoDB compatibility
    outcome: Optional[str] = None  # "SUCCESS", "FAILURE", "PENDING"
    outcome_price: Optional[float] = None
    outcome_date: Optional[datetime] = None
    profit_loss_percent: Optional[float] = None
    days_to_outcome: Optional[int] = None

    # Validation fields
    validation_status: Optional[str] = "PENDING"  # "VALID", "INVALID", "PENDING"
    validated_by: Optional[str] = None
    validation_date: Optional[datetime] = None

    # Additional metadata
    market_conditions: Optional[str] = None
    volume_at_alert: Optional[int] = None
    notes: Optional[str] = None

    class Config:
        from_attributes = True

class AlertFilters(BaseModel):
    """Model for alert filtering parameters."""
    symbol: Optional[str] = None
    alert_type: Optional[str] = None  # 'BUY', 'SELL', 'ALL'
    pattern_type: Optional[str] = None
    is_super_alert: Optional[bool] = None
    start_date: Optional[Union[str, datetime]] = None
    end_date: Optional[Union[str, datetime]] = None
    outcome: Optional[str] = None  # 'SUCCESS', 'FAILURE', 'PENDING', 'ALL'
    validation_status: Optional[str] = None  # 'VALID', 'INVALID', 'PENDING', 'ALL'
    environment: Optional[str] = None  # 'PRODUCTION', 'LOCAL', 'TEST', 'ALL'
    fibonacci_level: Optional[str] = None
    limit: Optional[int] = 100
    offset: Optional[int] = 0

class AlertValidationUpdate(BaseModel):
    """Model for updating alert validation status."""
    validation_status: str  # "VALID", "INVALID", "PENDING"
    notes: Optional[str] = None
    validated_by: Optional[str] = None

class AlertAnalysisUpdate(BaseModel):
    """Model for updating alert analysis data."""
    alert_id: int
    outcome: str  # 'SUCCESS', 'FAILURE', 'PENDING'
    outcome_price: Optional[float] = None
    outcome_date: Optional[datetime] = None
    profit_loss_percent: Optional[float] = None
    notes: Optional[str] = None

# --- Pattern Validation Dashboard Models ---

class DailySummary(BaseModel):
    """Model for daily pattern summary data."""
    date: str
    total_alerts: int
    buy_alerts: int
    sell_alerts: int
    super_alerts: int
    pattern_breakdown: Dict[str, int]
    environment_breakdown: Dict[str, int]
    validation_breakdown: Dict[str, int]
    outcome_breakdown: Dict[str, int]

class PatternAnalytics(BaseModel):
    """Model for pattern performance analytics."""
    pattern_type: str
    total_alerts: int
    success_rate: float
    average_profit_loss: float
    average_days_to_outcome: float
    fibonacci_level_performance: Dict[str, Dict[str, float]]
    environment_performance: Dict[str, Dict[str, float]]

class ValidationDashboardResponse(BaseModel):
    """Response model for validation dashboard data."""
    alerts: List[AlertResponse]
    total_count: int
    summary: Optional[DailySummary] = None
    analytics: Optional[List[PatternAnalytics]] = None
