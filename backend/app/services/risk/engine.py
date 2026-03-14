"""
Exylio Risk Management Module
All rules enforced before any order reaches Angel One.
Designed for ₹2L capital, 4 positions, ₹40K per trade.
"""
from app.core.config import settings
from logzero import logger
from datetime import datetime


class RiskEngine:

    def __init__(self):
        self.daily_pnl          = 0.0
        self.daily_loss_halted  = False
        self.open_positions     = {}    # token -> holding data
        self.total_deployed     = 0.0

    def check_signal(self, signal: dict, portfolio_state: dict) -> tuple[bool, str]:
        """
        Run all risk rules. Returns (approved: bool, reason: str).
        """
        ticker = signal.get("ticker")
        price  = signal.get("price_at_signal", 0)
        qty    = signal.get("quantity", 0)
        trade_value = price * qty

        # Rule 1: Daily loss circuit breaker
        if self.daily_loss_halted:
            return False, f"CIRCUIT_BREAKER: Daily loss limit ₹{settings.DAILY_LOSS_CIRCUIT_BREAKER} hit. Trading halted."

        # Rule 2: Max positions
        open_count = portfolio_state.get("open_positions_count", 0)
        if open_count >= settings.MAX_POSITIONS and signal.get("direction") == "BUY":
            return False, f"MAX_POSITIONS: Already at max {settings.MAX_POSITIONS} open positions."

        # Rule 3: Max capital per trade
        if trade_value > settings.MAX_CAPITAL_PER_TRADE:
            return False, f"MAX_TRADE_SIZE: ₹{trade_value} exceeds limit ₹{settings.MAX_CAPITAL_PER_TRADE}."

        # Rule 4: Total portfolio exposure (max 80%)
        deployed       = portfolio_state.get("total_deployed", 0)
        available      = settings.DEFAULT_CAPITAL * 0.80
        if deployed + trade_value > available:
            return False, f"EXPOSURE_LIMIT: Deploying ₹{trade_value} would exceed 80% capital limit."

        # Rule 5: Sector concentration (max 30%)
        sector = signal.get("sector", "")
        sector_deployed = portfolio_state.get("sector_exposure", {}).get(sector, 0)
        sector_limit    = settings.DEFAULT_CAPITAL * 0.30
        if sector_deployed + trade_value > sector_limit and signal.get("direction") == "BUY":
            return False, f"SECTOR_LIMIT: {sector} exposure would exceed 30% limit."

        # Rule 6: Sufficient funds
        available_funds = portfolio_state.get("available_funds", settings.DEFAULT_CAPITAL)
        if trade_value > available_funds:
            return False, f"INSUFFICIENT_FUNDS: ₹{trade_value} needed, ₹{available_funds} available."

        # Rule 7: Radar EXTREME event — block new buys
        if signal.get("direction") == "BUY" and portfolio_state.get("radar_extreme_active"):
            return False, "RADAR_EXTREME: Extreme event active. New buy positions blocked."

        logger.info(f"✅ Risk approved: {ticker} {signal.get('direction')} ₹{trade_value}")
        return True, "APPROVED"

    def update_daily_pnl(self, pnl_delta: float):
        self.daily_pnl += pnl_delta
        if self.daily_pnl <= -abs(settings.DAILY_LOSS_CIRCUIT_BREAKER):
            self.daily_loss_halted = True
            logger.warning(f"🚨 CIRCUIT BREAKER TRIGGERED: Daily P&L = ₹{self.daily_pnl}")

    def reset_daily(self):
        """Call at market open each day."""
        self.daily_pnl         = 0.0
        self.daily_loss_halted = False
        logger.info("✅ Risk engine daily reset complete")

    def calculate_position_size(self, price: float, capital: float = None) -> int:
        """
        Given entry price, return safe quantity for ₹40K trade size.
        """
        capital = capital or settings.MAX_CAPITAL_PER_TRADE
        qty = int(capital / price)
        return max(qty, 1)

    def calculate_targets(self, entry_price: float, qty: int) -> dict:
        """
        Given entry, calculate target and stop-loss prices
        to achieve ₹250 net profit after charges.
        """
        from app.services.market_data.charges import calculate_delivery_charges

        trade_value = entry_price * qty

        # Work backwards: need gross ₹316+ to net ₹250 at ₹10K trade
        charges = calculate_delivery_charges(trade_value, trade_value * 1.032)
        total_charges = charges["total_charges"]

        target_gross  = settings.TARGET_PROFIT_PER_TRADE + total_charges
        target_pct    = target_gross / trade_value

        stop_loss_pct  = (settings.STOP_LOSS_PER_TRADE / trade_value)

        target_price   = round(entry_price * (1 + target_pct), 2)
        stop_loss_price= round(entry_price * (1 - stop_loss_pct), 2)

        return {
            "entry_price":     entry_price,
            "target_price":    target_price,
            "stop_loss_price": stop_loss_price,
            "target_pct":      round(target_pct * 100, 2),
            "stop_loss_pct":   round(stop_loss_pct * 100, 2),
            "estimated_charges": total_charges,
            "net_profit_at_target": settings.TARGET_PROFIT_PER_TRADE,
        }


risk_engine = RiskEngine()
