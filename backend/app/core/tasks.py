from app.core.celery_app import celery_app
from logzero import logger
import asyncio


@celery_app.task(name="app.core.tasks.build_daily_universe")
def build_daily_universe():
    """8:30 AM — Build today's tradable stock universe from NIFTY 50."""
    logger.info("📋 Building daily stock universe...")
    # Universe is currently static (NIFTY50_UNIVERSE in routes)
    # Future: fetch live constituents from NSE + apply filters
    logger.info("✅ Universe build complete")
    return {"status": "ok"}


@celery_app.task(name="app.core.tasks.refresh_angel_session")
def refresh_angel_session():
    """Every 6 hours — Refresh Angel One JWT token."""
    from app.services.market_data.angel_broker import angel_service
    logger.info("🔄 Refreshing Angel One session...")
    asyncio.run(angel_service.refresh_session())
    return {"status": "ok"}


@celery_app.task(name="app.core.tasks.run_radar_scan")
def run_radar_scan():
    """Every 15 min during market hours — Run macro event radar."""
    from app.services.radar.engine import radar_engine
    logger.info("🔭 Running Radar scan...")
    events = asyncio.run(radar_engine.run_radar_cycle())
    logger.info(f"🔭 Radar found {len(events)} events")
    return {"events_found": len(events)}


@celery_app.task(name="app.core.tasks.reset_risk_daily")
def reset_risk_daily():
    """9:10 AM — Reset daily P&L counters and circuit breakers."""
    from app.services.risk.engine import risk_engine
    risk_engine.reset_daily()
    return {"status": "ok"}


@celery_app.task(name="app.core.tasks.check_holding_expiry")
def check_holding_expiry():
    """
    Every hour — Check if any holdings have exceeded MAX_HOLDING_DAYS.
    Flag them for forced exit alert.
    """
    from app.core.config import settings
    logger.info("⏰ Checking holding expiry...")
    # Future: query DB holdings where holding_days >= MAX_HOLDING_DAYS
    # Send alert if found
    return {"status": "ok"}
