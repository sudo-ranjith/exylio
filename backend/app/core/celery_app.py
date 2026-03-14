from celery import Celery
from celery.schedules import crontab
from app.core.config import settings

celery_app = Celery(
    "exylio",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.core.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Kolkata",
    enable_utc=True,
    beat_schedule={
        # Build stock universe every day at 8:30 AM IST
        "build-universe": {
            "task": "app.core.tasks.build_daily_universe",
            "schedule": crontab(hour=8, minute=30),
        },
        # Refresh Angel One session every 6 hours
        "refresh-angel-session": {
            "task": "app.core.tasks.refresh_angel_session",
            "schedule": crontab(minute=0, hour="*/6"),
        },
        # Radar scan every 15 minutes during market hours
        "radar-scan": {
            "task": "app.core.tasks.run_radar_scan",
            "schedule": crontab(minute="*/15", hour="9-16"),
        },
        # Reset risk engine daily at 9:10 AM
        "reset-risk-engine": {
            "task": "app.core.tasks.reset_risk_daily",
            "schedule": crontab(hour=9, minute=10),
        },
        # Max holding check every hour
        "holding-expiry-check": {
            "task": "app.core.tasks.check_holding_expiry",
            "schedule": crontab(minute=0, hour="9-16"),
        },
    },
)
