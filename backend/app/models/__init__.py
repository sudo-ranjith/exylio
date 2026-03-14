from sqlalchemy import Column, String, Float, Integer, Boolean, DateTime, JSON, Text, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum


# ── Enums ─────────────────────────────────────────────────────────
class OrderStatus(str, enum.Enum):
    PENDING   = "PENDING"
    OPEN      = "OPEN"
    COMPLETE  = "COMPLETE"
    REJECTED  = "REJECTED"
    CANCELLED = "CANCELLED"

class OrderType(str, enum.Enum):
    MARKET = "MARKET"
    LIMIT  = "LIMIT"
    SL     = "SL"

class Direction(str, enum.Enum):
    BUY  = "BUY"
    SELL = "SELL"

class ProductType(str, enum.Enum):
    DELIVERY  = "DELIVERY"   # CNC
    INTRADAY  = "INTRADAY"   # MIS

class SignalStrength(str, enum.Enum):
    STRONG   = "STRONG"
    MODERATE = "MODERATE"
    WEAK     = "WEAK"

class AlertSeverity(str, enum.Enum):
    LOW     = "LOW"
    MEDIUM  = "MEDIUM"
    HIGH    = "HIGH"
    EXTREME = "EXTREME"

class RadarEventType(str, enum.Enum):
    WAR          = "WAR"
    GEOPOLITICAL = "GEOPOLITICAL"
    CRUDE        = "CRUDE"
    RBI          = "RBI"
    FED          = "FED"
    ELECTION     = "ELECTION"
    BUDGET       = "BUDGET"
    RECESSION    = "RECESSION"
    DISASTER     = "DISASTER"


# ── User ──────────────────────────────────────────────────────────
class User(Base):
    __tablename__ = "users"
    id                    = Column(Integer, primary_key=True, index=True)
    email                 = Column(String, unique=True, index=True, nullable=False)
    hashed_password       = Column(String, nullable=False)
    is_active             = Column(Boolean, default=True)
    risk_profile          = Column(String, default="MODERATE")   # CONSERVATIVE/MODERATE/AGGRESSIVE
    total_capital         = Column(Float, default=200000)
    max_positions         = Column(Integer, default=4)
    max_capital_per_trade = Column(Float, default=40000)
    target_profit         = Column(Float, default=250)
    stop_loss_amount      = Column(Float, default=200)
    max_holding_days      = Column(Integer, default=5)
    daily_loss_limit      = Column(Float, default=800)
    created_at            = Column(DateTime(timezone=True), server_default=func.now())
    updated_at            = Column(DateTime(timezone=True), onupdate=func.now())


# ── OHLCV (TimescaleDB hypertable) ────────────────────────────────
class OHLCVCandle(Base):
    __tablename__ = "ohlcv_candles"
    id         = Column(Integer, primary_key=True, index=True)
    ticker     = Column(String, index=True, nullable=False)
    token      = Column(String, index=True, nullable=False)
    interval   = Column(String, nullable=False)              # 1s, 1m, 5m, 1h, 1D
    time       = Column(DateTime(timezone=True), nullable=False, index=True)
    open       = Column(Float, nullable=False)
    high       = Column(Float, nullable=False)
    low        = Column(Float, nullable=False)
    close      = Column(Float, nullable=False)
    volume     = Column(Float, nullable=False)
    tick_count = Column(Integer, default=0)
    exchange   = Column(String, default="NSE")


# ── Stock Universe ────────────────────────────────────────────────
class StockUniverse(Base):
    __tablename__ = "stock_universe"
    id          = Column(Integer, primary_key=True, index=True)
    date        = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    ticker      = Column(String, nullable=False, index=True)
    token       = Column(String, nullable=False)
    name        = Column(String)
    sector      = Column(String)
    market_cap  = Column(Float)
    avg_volume  = Column(Float)
    index_group = Column(String)                             # NIFTY50/NIFTY200/NIFTY500
    is_active   = Column(Boolean, default=True)
    is_blacklisted = Column(Boolean, default=False)


# ── Strategy Config ───────────────────────────────────────────────
class StrategyConfig(Base):
    __tablename__ = "strategy_configs"
    id          = Column(Integer, primary_key=True, index=True)
    name        = Column(String, unique=True, nullable=False)
    type        = Column(String, nullable=False)             # MOMENTUM/BREAKOUT/VWAP/MEAN_REVERSION
    is_active   = Column(Boolean, default=True)
    is_paper    = Column(Boolean, default=False)
    params      = Column(JSON, default={})
    created_at  = Column(DateTime(timezone=True), server_default=func.now())
    updated_at  = Column(DateTime(timezone=True), onupdate=func.now())


# ── Signal ────────────────────────────────────────────────────────
class Signal(Base):
    __tablename__ = "signals"
    id              = Column(Integer, primary_key=True, index=True)
    ticker          = Column(String, nullable=False, index=True)
    token           = Column(String, nullable=False)
    strategy_name   = Column(String, nullable=False)
    direction       = Column(Enum(Direction), nullable=False)
    strength        = Column(Enum(SignalStrength), nullable=False)
    confidence      = Column(Float, nullable=False)
    price_at_signal = Column(Float, nullable=False)
    status          = Column(String, default="PENDING")      # PENDING/APPROVED/REJECTED/EXECUTED
    rejection_reason= Column(String, nullable=True)
    is_paper        = Column(Boolean, default=False)
    created_at      = Column(DateTime(timezone=True), server_default=func.now(), index=True)


# ── Order ─────────────────────────────────────────────────────────
class Order(Base):
    __tablename__ = "orders"
    id              = Column(Integer, primary_key=True, index=True)
    signal_id       = Column(Integer, ForeignKey("signals.id"), nullable=True)
    broker_order_id = Column(String, nullable=True, index=True)
    ticker          = Column(String, nullable=False, index=True)
    token           = Column(String, nullable=False)
    direction       = Column(Enum(Direction), nullable=False)
    order_type      = Column(Enum(OrderType), nullable=False)
    product_type    = Column(Enum(ProductType), nullable=False)
    quantity        = Column(Integer, nullable=False)
    price           = Column(Float, nullable=True)           # None for MARKET orders
    fill_price      = Column(Float, nullable=True)
    status          = Column(Enum(OrderStatus), default=OrderStatus.PENDING)
    is_paper        = Column(Boolean, default=False)
    is_gtt          = Column(Boolean, default=False)
    gtt_rule_id     = Column(String, nullable=True)
    charges         = Column(JSON, nullable=True)            # brokerage, STT, DP etc
    created_at      = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at      = Column(DateTime(timezone=True), onupdate=func.now())
    signal          = relationship("Signal", backref="orders")


# ── Portfolio Holding ─────────────────────────────────────────────
class Holding(Base):
    __tablename__ = "holdings"
    id              = Column(Integer, primary_key=True, index=True)
    ticker          = Column(String, nullable=False, index=True)
    token           = Column(String, nullable=False)
    sector          = Column(String, nullable=True)
    quantity        = Column(Integer, nullable=False)
    avg_price       = Column(Float, nullable=False)
    current_price   = Column(Float, nullable=True)
    buy_date        = Column(DateTime(timezone=True), server_default=func.now())
    target_price    = Column(Float, nullable=True)
    stop_loss_price = Column(Float, nullable=True)
    is_paper        = Column(Boolean, default=False)
    gtt_rule_id     = Column(String, nullable=True)
    holding_days    = Column(Integer, default=0)
    unrealized_pnl  = Column(Float, default=0.0)
    charges_paid    = Column(Float, default=0.0)
    is_active       = Column(Boolean, default=True)
    updated_at      = Column(DateTime(timezone=True), onupdate=func.now())


# ── Trade (closed position) ───────────────────────────────────────
class Trade(Base):
    __tablename__ = "trades"
    id              = Column(Integer, primary_key=True, index=True)
    ticker          = Column(String, nullable=False, index=True)
    sector          = Column(String, nullable=True)
    buy_price       = Column(Float, nullable=False)
    sell_price      = Column(Float, nullable=False)
    quantity        = Column(Integer, nullable=False)
    gross_pnl       = Column(Float, nullable=False)
    total_charges   = Column(Float, nullable=False)
    net_pnl         = Column(Float, nullable=False)
    holding_days    = Column(Integer, nullable=False)
    strategy_name   = Column(String, nullable=True)
    is_paper        = Column(Boolean, default=False)
    buy_date        = Column(DateTime(timezone=True))
    sell_date       = Column(DateTime(timezone=True), server_default=func.now())


# ── Backtest Run ──────────────────────────────────────────────────
class BacktestRun(Base):
    __tablename__ = "backtest_runs"
    id              = Column(Integer, primary_key=True, index=True)
    strategy_name   = Column(String, nullable=False)
    strategy_params = Column(JSON, nullable=False)
    from_date       = Column(DateTime(timezone=True), nullable=False)
    to_date         = Column(DateTime(timezone=True), nullable=False)
    universe        = Column(String, default="NIFTY50")
    total_trades    = Column(Integer, default=0)
    winning_trades  = Column(Integer, default=0)
    losing_trades   = Column(Integer, default=0)
    win_rate        = Column(Float, default=0.0)
    total_pnl       = Column(Float, default=0.0)
    max_drawdown    = Column(Float, default=0.0)
    sharpe_ratio    = Column(Float, default=0.0)
    cagr            = Column(Float, default=0.0)
    equity_curve    = Column(JSON, default=[])
    created_at      = Column(DateTime(timezone=True), server_default=func.now())


# ── Radar Event ───────────────────────────────────────────────────
class RadarEvent(Base):
    __tablename__ = "radar_events"
    id              = Column(Integer, primary_key=True, index=True)
    event_id        = Column(String, unique=True, nullable=False, index=True)
    event_type      = Column(Enum(RadarEventType), nullable=False)
    severity_score  = Column(Integer, nullable=False)
    severity_label  = Column(Enum(AlertSeverity), nullable=False)
    confidence      = Column(Float, nullable=False)
    headline        = Column(String, nullable=False)
    source_count    = Column(Integer, default=0)
    sources         = Column(JSON, default=[])
    sectors_rise    = Column(JSON, default=[])
    sectors_fall    = Column(JSON, default=[])
    alert_generated = Column(Boolean, default=False)
    gdelt_goldstein = Column(Float, nullable=True)
    detected_at     = Column(DateTime(timezone=True), server_default=func.now(), index=True)


# ── Alert ─────────────────────────────────────────────────────────
class Alert(Base):
    __tablename__ = "alerts"
    id              = Column(Integer, primary_key=True, index=True)
    alert_type      = Column(String, nullable=False)
    severity        = Column(Enum(AlertSeverity), nullable=False)
    title           = Column(String, nullable=False)
    message         = Column(Text, nullable=False)
    data            = Column(JSON, default={})
    is_read         = Column(Boolean, default=False)
    channels_sent   = Column(JSON, default=[])
    radar_event_id  = Column(Integer, ForeignKey("radar_events.id"), nullable=True)
    created_at      = Column(DateTime(timezone=True), server_default=func.now(), index=True)
