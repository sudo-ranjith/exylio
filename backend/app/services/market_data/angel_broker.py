from SmartApi import SmartConnect
from SmartApi.smartWebSocketV2 import SmartWebSocketV2
from SmartApi.smartWebSocketOrderUpdate import SmartWebSocketOrderUpdate
import pyotp
from logzero import logger
from app.core.config import settings
from app.core.redis_client import redis_client, CACHE_SESSION
import json, asyncio
from datetime import datetime


class AngelBrokerService:
    """
    Manages Angel One SmartAPI session lifecycle.
    Handles login, token refresh, and exposes
    SmartConnect for all other services to use.
    """

    def __init__(self):
        self.smart_api   = None
        self.auth_token  = None
        self.feed_token  = None
        self.refresh_token = None
        self.is_connected  = False

    async def login(self) -> bool:
        try:
            self.smart_api = SmartConnect(settings.ANGEL_API_KEY)
            totp = pyotp.TOTP(settings.ANGEL_TOTP_SECRET).now()
            data = self.smart_api.generateSession(
                settings.ANGEL_CLIENT_CODE,
                settings.ANGEL_PASSWORD,
                totp
            )
            if not data["status"]:
                logger.error(f"Angel One login failed: {data}")
                return False

            self.auth_token    = data["data"]["jwtToken"]
            self.refresh_token = data["data"]["refreshToken"]
            self.feed_token    = self.smart_api.getfeedToken()
            self.is_connected  = True

            # Cache session in Redis (6 hour TTL)
            session_data = {
                "auth_token":    self.auth_token,
                "feed_token":    self.feed_token,
                "refresh_token": self.refresh_token,
                "logged_at":     datetime.now().isoformat(),
            }
            await redis_client.setex(CACHE_SESSION, 21600, json.dumps(session_data))
            logger.info("✅ Angel One login successful")
            return True

        except Exception as e:
            logger.exception(f"Angel One login error: {e}")
            return False

    async def refresh_session(self):
        try:
            self.smart_api.generateToken(self.refresh_token)
            logger.info("🔄 Angel One session refreshed")
        except Exception as e:
            logger.error(f"Session refresh failed: {e}")
            await self.login()

    async def logout(self):
        try:
            self.smart_api.terminateSession(settings.ANGEL_CLIENT_CODE)
            self.is_connected = False
            logger.info("Angel One logged out")
        except Exception as e:
            logger.error(f"Logout error: {e}")

    def get_profile(self):
        return self.smart_api.getProfile(self.refresh_token)

    def get_funds(self):
        return self.smart_api.rmsLimit()

    def search_scrip(self, exchange: str, query: str):
        return self.smart_api.searchScrip(exchange, query)

    def get_ltp(self, exchange: str, ticker: str, token: str):
        return self.smart_api.ltpData(exchange, ticker, token)

    def get_candles(self, token: str, interval: str, from_date: str, to_date: str):
        params = {
            "exchange":    "NSE",
            "symboltoken": token,
            "interval":    interval,
            "fromdate":    from_date,
            "todate":      to_date,
        }
        return self.smart_api.getCandleData(params)

    def estimate_charges(self, params: dict):
        return self.smart_api.estimateCharges(params)

    def get_oi_buildup(self, params: dict):
        return self.smart_api.oIBuildup(params)

    def get_pcr(self):
        return self.smart_api.putCallRatio()

    def get_gainers_losers(self, params: dict):
        return self.smart_api.gainersLosers(params)

    # ── Order methods ──────────────────────────────────────────────
    def place_order(self, params: dict):
        return self.smart_api.placeOrderFullResponse(params)

    def modify_order(self, params: dict):
        return self.smart_api.modifyOrder(params)

    def cancel_order(self, order_id: str, variety: str = "NORMAL"):
        return self.smart_api.cancelOrder(order_id, variety)

    def get_order_book(self):
        return self.smart_api.orderBook()

    def get_trade_book(self):
        return self.smart_api.tradeBook()

    def get_positions(self):
        return self.smart_api.position()

    def get_holdings(self):
        return self.smart_api.allholding()

    def get_order_status(self, order_id: str):
        return self.smart_api.individual_order_details(order_id)

    # ── GTT Orders ────────────────────────────────────────────────
    def create_gtt(self, params: dict):
        return self.smart_api.gttCreateRule(params)

    def cancel_gtt(self, params: dict):
        return self.smart_api.gttCancelRule(params)

    def list_gtt(self, status: list = ["FORALL"], page: int = 1, count: int = 50):
        return self.smart_api.gttLists(status, page, count)


# ── Singleton ──────────────────────────────────────────────────────
angel_service = AngelBrokerService()
