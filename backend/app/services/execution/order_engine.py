"""
Exylio Order Execution Engine
Connects to Angel One SmartAPI for all order operations.
Supports delivery (CNC), GTT orders, and bracket orders.
"""
from app.services.market_data.angel_broker import angel_service
from app.services.market_data.charges import calculate_net_pnl
from app.services.risk.engine import risk_engine
from logzero import logger


class OrderExecutionEngine:

    async def place_delivery_buy(
        self,
        ticker: str, token: str, qty: int,
        order_type: str = "MARKET", price: float = 0
    ) -> dict:
        params = {
            "variety":         "NORMAL",
            "tradingsymbol":   ticker,
            "symboltoken":     token,
            "transactiontype": "BUY",
            "exchange":        "NSE",
            "ordertype":       order_type,
            "producttype":     "DELIVERY",          # CNC
            "duration":        "DAY",
            "price":           str(price) if price else "0",
            "squareoff":       "0",
            "stoploss":        "0",
            "quantity":        str(qty),
        }
        response = angel_service.place_order(params)
        logger.info(f"📤 BUY order: {ticker} x{qty} → {response}")
        return response

    async def place_delivery_sell(
        self,
        ticker: str, token: str, qty: int,
        order_type: str = "MARKET", price: float = 0
    ) -> dict:
        params = {
            "variety":         "NORMAL",
            "tradingsymbol":   ticker,
            "symboltoken":     token,
            "transactiontype": "SELL",
            "exchange":        "NSE",
            "ordertype":       order_type,
            "producttype":     "DELIVERY",
            "duration":        "DAY",
            "price":           str(price) if price else "0",
            "squareoff":       "0",
            "stoploss":        "0",
            "quantity":        str(qty),
        }
        response = angel_service.place_order(params)
        logger.info(f"📤 SELL order: {ticker} x{qty} → {response}")
        return response

    async def place_gtt_target_and_stoploss(
        self,
        ticker: str, token: str, qty: int,
        entry_price: float, target_price: float, stop_loss_price: float
    ) -> dict:
        """
        Place GTT rule immediately after buy to auto-sell at:
        - target_price (profit booking)
        - stop_loss_price (loss protection)
        Angel One GTT handles this even when app is offline.
        """
        # Target GTT (take profit)
        target_gtt = angel_service.create_gtt({
            "tradingsymbol":   ticker,
            "symboltoken":     token,
            "exchange":        "NSE",
            "producttype":     "DELIVERY",
            "transactiontype": "SELL",
            "price":           target_price * qty,
            "qty":             qty,
            "disclosedqty":    qty,
            "triggerprice":    target_price,
            "timeperiod":      365,
        })

        # Stop-loss GTT
        sl_gtt = angel_service.create_gtt({
            "tradingsymbol":   ticker,
            "symboltoken":     token,
            "exchange":        "NSE",
            "producttype":     "DELIVERY",
            "transactiontype": "SELL",
            "price":           stop_loss_price * qty,
            "qty":             qty,
            "disclosedqty":    qty,
            "triggerprice":    stop_loss_price,
            "timeperiod":      365,
        })

        logger.info(f"✅ GTT set: {ticker} target={target_price} SL={stop_loss_price}")
        return {
            "target_gtt": target_gtt,
            "sl_gtt":     sl_gtt,
        }

    async def full_trade_entry(
        self,
        ticker: str, token: str, entry_price: float, sector: str = ""
    ) -> dict:
        """
        Complete trade flow:
        1. Calculate position size
        2. Place delivery buy (MARKET)
        3. Immediately set GTT for target + stop-loss
        Returns full trade summary.
        """
        qty     = risk_engine.calculate_position_size(entry_price)
        targets = risk_engine.calculate_targets(entry_price, qty)

        # Place buy
        buy_response = await self.place_delivery_buy(ticker, token, qty)

        if not buy_response.get("status"):
            return {"success": False, "error": buy_response.get("message")}

        order_id = buy_response["data"]["orderid"]

        # Place GTT immediately
        gtt_response = await self.place_gtt_target_and_stoploss(
            ticker, token, qty,
            entry_price,
            targets["target_price"],
            targets["stop_loss_price"],
        )

        # Net P&L preview
        pnl_preview = calculate_net_pnl(entry_price, targets["target_price"], qty)

        return {
            "success":         True,
            "order_id":        order_id,
            "ticker":          ticker,
            "quantity":        qty,
            "entry_price":     entry_price,
            "target_price":    targets["target_price"],
            "stop_loss_price": targets["stop_loss_price"],
            "gtt":             gtt_response,
            "estimated_net_pnl": pnl_preview["net_pnl"],
            "charges":         pnl_preview["charges"],
        }

    async def cancel_order(self, order_id: str) -> dict:
        return angel_service.cancel_order(order_id)

    async def get_order_book(self) -> list:
        data = angel_service.get_order_book()
        return data.get("data", [])

    async def get_positions(self) -> list:
        data = angel_service.get_positions()
        return data.get("data", [])


order_engine = OrderExecutionEngine()
