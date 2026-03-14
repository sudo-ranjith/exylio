from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Exylio starting up...")
    # DB + Redis init (lazy — skips if not available in dev)
    try:
        from app.core.database import init_db
        await init_db()
    except Exception as e:
        logger.warning(f"DB init skipped: {e}")
    try:
        from app.core.redis_client import init_redis
        await init_redis()
    except Exception as e:
        logger.warning(f"Redis init skipped: {e}")
    logger.info("✅ Exylio ready")
    yield
    logger.info("🛑 Exylio shutting down...")


app = FastAPI(
    title="Exylio API",
    description="Algorithmic Trading Platform — Angel One Connected",
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Import all routers from combined routes module ─────────────────
from app.api.routes import (
    auth, market_data, universe, strategy,
    signals, risk, portfolio, orders,
    backtesting, paper_trading, ai_analytics,
    radar, alerts, dashboard, charges,
)

app.include_router(auth.router,          prefix="/api/auth",      tags=["Auth"])
app.include_router(market_data.router,   prefix="/api/market",    tags=["Market Data"])
app.include_router(universe.router,      prefix="/api/universe",  tags=["Universe"])
app.include_router(strategy.router,      prefix="/api/strategy",  tags=["Strategy"])
app.include_router(signals.router,       prefix="/api/signals",   tags=["Signals"])
app.include_router(risk.router,          prefix="/api/risk",      tags=["Risk"])
app.include_router(portfolio.router,     prefix="/api/portfolio", tags=["Portfolio"])
app.include_router(orders.router,        prefix="/api/orders",    tags=["Orders"])
app.include_router(backtesting.router,   prefix="/api/backtest",  tags=["Backtest"])
app.include_router(paper_trading.router, prefix="/api/paper",     tags=["Paper"])
app.include_router(ai_analytics.router,  prefix="/api/ai",        tags=["AI"])
app.include_router(radar.router,         prefix="/api/radar",     tags=["Radar"])
app.include_router(alerts.router,        prefix="/api/alerts",    tags=["Alerts"])
app.include_router(dashboard.router,     prefix="/api/dashboard", tags=["Dashboard"])
app.include_router(charges.router,       prefix="/api/charges",   tags=["Charges"])


@app.get("/health")
async def health():
    return {"status": "ok", "app": "Exylio", "version": settings.APP_VERSION}
