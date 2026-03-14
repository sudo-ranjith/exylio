from collections import defaultdict, deque
from datetime import datetime
from app.core.redis_client import redis_client, CHANNEL_CANDLES_1S
from SmartApi.smartWebSocketV2 import SmartWebSocketV2
from app.services.market_data.angel_broker import angel_service
import json, asyncio, threading
from logzero import logger


class TickAggregator:
    """
    Receives raw Angel One WebSocket ticks.
    Aggregates them into 1-second OHLCV candles.
    Publishes to Redis for strategy engine consumption.
    """

    def __init__(self):
        self.buckets      = defaultdict(lambda: {
            "open": None, "high": None,
            "low": None,  "close": None,
            "volume": 0,  "ticks": 0,
            "tbq": 0,     "tsq": 0,
        })
        self.prev_volume  = defaultdict(float)
        self.subscribed   = set()
        self.sws          = None
        self._flush_task  = None

    def process_tick(self, tick: dict):
        token  = str(tick.get("tk", ""))
        ltp    = float(tick.get("ltp", 0))
        volume = float(tick.get("v", 0))
        tbq    = float(tick.get("tbq", 0))  # total buy qty — order flow
        tsq    = float(tick.get("tsq", 0))  # total sell qty

        if not token or not ltp:
            return

        delta_vol = volume - self.prev_volume[token]
        self.prev_volume[token] = volume

        b = self.buckets[token]
        if b["open"] is None:
            b["open"] = ltp
        b["high"]    = max(b["high"] or ltp, ltp)
        b["low"]     = min(b["low"]  or ltp, ltp)
        b["close"]   = ltp
        b["volume"] += max(delta_vol, 0)
        b["ticks"]  += 1
        b["tbq"]     = tbq
        b["tsq"]     = tsq

    def flush_candle(self, token: str, timestamp: datetime) -> dict | None:
        b = self.buckets[token]
        if b["open"] is None:
            return None
        candle = {
            "token":       token,
            "time":        timestamp.isoformat(),
            "open":        b["open"],
            "high":        b["high"],
            "low":         b["low"],
            "close":       b["close"],
            "volume":      b["volume"],
            "tick_count":  b["ticks"],
            "tbq":         b["tbq"],
            "tsq":         b["tsq"],
            "bid_ask_ratio": round(b["tbq"] / max(b["tsq"], 1), 2),
        }
        self.buckets[token] = {
            "open": None, "high": None, "low": None, "close": None,
            "volume": 0,  "ticks": 0,  "tbq": 0,     "tsq": 0,
        }
        return candle

    async def flush_loop(self):
        """Runs every 1 second — flushes all token buckets."""
        while True:
            await asyncio.sleep(1)
            now = datetime.now()
            for token in list(self.subscribed):
                candle = self.flush_candle(token, now)
                if candle:
                    channel = CHANNEL_CANDLES_1S.format(token=token)
                    await redis_client.publish(channel, json.dumps(candle))

    def start_feed(self, tokens: list[str]):
        """Connect Angel One WebSocket and subscribe tokens."""
        self.subscribed.update(tokens)
        token_list = [{"exchangeType": 1, "tokens": tokens}]

        self.sws = SmartWebSocketV2(
            angel_service.auth_token,
            angel_service.smart_api.api_key,
            angel_service.smart_api.userId,
            angel_service.feed_token,
            max_retry_attempt=5,
        )

        def on_open(wsapp):
            logger.info(f"📡 Feed connected — subscribing {len(tokens)} tokens")
            self.sws.subscribe("exylio_feed", 3, token_list)  # Mode 3 = SNAP_QUOTE

        def on_data(wsapp, tick):
            self.process_tick(tick)

        def on_error(wsapp, error):
            logger.error(f"Feed error: {error}")

        def on_close(wsapp, code, msg):
            logger.warning(f"Feed closed [{code}]: {msg}")

        self.sws.on_open  = on_open
        self.sws.on_data  = on_data
        self.sws.on_error = on_error
        self.sws.on_close = on_close

        # Run in background thread (WebSocket is synchronous)
        thread = threading.Thread(target=self.sws.connect, daemon=True)
        thread.start()
        logger.info("✅ Tick aggregator started")

    def add_tokens(self, tokens: list[str]):
        new_tokens = [t for t in tokens if t not in self.subscribed]
        if new_tokens and self.sws:
            self.subscribed.update(new_tokens)
            token_list = [{"exchangeType": 1, "tokens": new_tokens}]
            self.sws.subscribe("exylio_feed", 3, token_list)

    def stop(self):
        if self.sws:
            self.sws.close_connection()


tick_aggregator = TickAggregator()
