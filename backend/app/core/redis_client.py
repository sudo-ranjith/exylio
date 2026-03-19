import redis.asyncio as aioredis
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

redis_client: aioredis.Redis = None


async def init_redis():
    global redis_client
    redis_client = aioredis.from_url(
        settings.REDIS_URL,
        encoding="utf-8",
        decode_responses=True,
    )
    await redis_client.ping()
    logger.info("✅ Redis connected")


async def get_redis() -> aioredis.Redis:
    return redis_client


# ── Pub/Sub channel names ─────────────────────────────────────────
CHANNEL_TICKS      = "exylio:ticks:{token}"
CHANNEL_CANDLES_1S = "exylio:candles:1s:{token}"
CHANNEL_SIGNALS    = "exylio:signals"
CHANNEL_ORDERS     = "exylio:orders"
CHANNEL_ALERTS     = "exylio:alerts"
CHANNEL_RADAR      = "exylio:radar"

# ── Cache key patterns ────────────────────────────────────────────
CACHE_PORTFOLIO    = "exylio:portfolio:snapshot"
CACHE_UNIVERSE     = "exylio:universe:today"
CACHE_LTP          = "exylio:ltp:{token}"
CACHE_SESSION      = "exylio:angel:session"
