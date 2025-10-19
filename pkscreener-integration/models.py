"""
Database models for PKScreener integration
Completely separate from existing P&F pattern detection tables
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, Index
from datetime import datetime
from app.db import Base


class PKScreenerResult(Base):
    """Store scanner results from PKScreener strategies"""
    __tablename__ = 'pkscreener_results'

    id = Column(Integer, primary_key=True, index=True)
    scanner_id = Column(Integer, nullable=False, index=True)  # 1-21
    scanner_name = Column(String, nullable=False)  # e.g., "Volume + Momentum + Breakout + ATR"
    instrument_key = Column(String, nullable=False, index=True)  # e.g., "DHAN_3518"
    symbol = Column(String, nullable=False, index=True)  # e.g., "TORNTPHARM"
    scan_timestamp = Column(DateTime, nullable=False, index=True, default=datetime.utcnow)
    trigger_price = Column(Float, nullable=False)  # Stock price when scanner triggered
    volume = Column(Integer, nullable=True)  # Volume at trigger time
    volume_ratio = Column(Float, nullable=True)  # Volume / 20-day avg volume
    atr_value = Column(Float, nullable=True)  # ATR value if applicable
    rsi_value = Column(Float, nullable=True)  # RSI value if applicable
    rsi_intraday = Column(Float, nullable=True)  # Intraday RSI if applicable
    momentum_score = Column(Float, nullable=True)  # Momentum indicator score
    vcp_score = Column(Float, nullable=True)  # VCP pattern score
    additional_metrics = Column(Text, nullable=True)  # JSON field for scanner-specific data
    is_active = Column(Boolean, default=True, index=True)  # True if still valid
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_scanner_symbol_timestamp', 'scanner_id', 'symbol', 'scan_timestamp'),
        Index('idx_active_scanners', 'is_active', 'scan_timestamp'),
    )


class PKScreenerBacktestResult(Base):
    """Store backtesting results for scanner validation"""
    __tablename__ = 'pkscreener_backtest_results'

    id = Column(Integer, primary_key=True, index=True)
    scanner_id = Column(Integer, nullable=False, index=True)  # 1-21
    backtest_date = Column(DateTime, nullable=False, index=True)  # The date being backtested
    instrument_key = Column(String, nullable=False)
    symbol = Column(String, nullable=False, index=True)
    trigger_price = Column(Float, nullable=False)  # Entry price
    trigger_time = Column(DateTime, nullable=False)  # Exact trigger timestamp
    
    # Price movements after trigger (ADDED 3min for intraday scalping)
    price_after_3min = Column(Float, nullable=True)   # NEW: Critical for intraday
    price_after_5min = Column(Float, nullable=True)
    price_after_15min = Column(Float, nullable=True)
    price_after_30min = Column(Float, nullable=True)
    price_after_1hour = Column(Float, nullable=True)
    price_after_2hours = Column(Float, nullable=True)

    # Returns for scalping analysis (ADDED 3min)
    return_3min_pct = Column(Float, nullable=True)    # NEW: Critical for intraday
    return_5min_pct = Column(Float, nullable=True)
    return_15min_pct = Column(Float, nullable=True)
    return_30min_pct = Column(Float, nullable=True)
    return_1hour_pct = Column(Float, nullable=True)
    return_2hours_pct = Column(Float, nullable=True)
    
    # Max profit/loss during the period
    max_profit_pct = Column(Float, nullable=True)
    max_loss_pct = Column(Float, nullable=True)
    max_profit_time = Column(DateTime, nullable=True)
    max_loss_time = Column(DateTime, nullable=True)
    
    # Success criteria for momentum scalping
    was_successful = Column(Boolean, nullable=True)  # True if positive return after 3min (fast scalping)
    hit_target_1pct = Column(Boolean, nullable=True)  # Hit 1% profit target
    hit_target_2pct = Column(Boolean, nullable=True)  # Hit 2% profit target
    hit_stoploss = Column(Boolean, nullable=True)  # Hit -1% stop loss
    
    # Scanner-specific metrics at trigger time
    volume_ratio = Column(Float, nullable=True)
    atr_value = Column(Float, nullable=True)
    rsi_value = Column(Float, nullable=True)
    momentum_score = Column(Float, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_backtest_scanner_date', 'scanner_id', 'backtest_date'),
        Index('idx_backtest_success', 'scanner_id', 'was_successful'),
    )

