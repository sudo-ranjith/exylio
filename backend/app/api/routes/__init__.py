"""
Exylio — All API Routes
Each section creates an APIRouter and registers all endpoints.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from app.core.config import settings
from app.services.market_data.charges import calculate_net_pnl, scale_charges_table
from app.services.risk.engine import risk_engine
import logging

logger = logging.getLogger(__name__)

# ══════════════════════════════════════════════════════════════════
# AUTH
# ══════════════════════════════════════════════════════════════════
auth = APIRouter()

@auth.post("/login")
async def login():
    try:
        from app.services.market_data.angel_broker import angel_service
        success = await angel_service.login()
        if not success:
            raise HTTPException(401, "Angel One login failed. Check credentials in .env")
        return {"status":"ok","message":"Angel One connected","client":settings.ANGEL_CLIENT_CODE}
    except Exception as e:
        raise HTTPException(500, str(e))

@auth.post("/refresh")
async def refresh():
    from app.services.market_data.angel_broker import angel_service
    await angel_service.refresh_session()
    return {"status":"ok"}

@auth.post("/logout")
async def logout():
    from app.services.market_data.angel_broker import angel_service
    await angel_service.logout()
    return {"status":"ok"}

@auth.get("/profile")
async def profile():
    from app.services.market_data.angel_broker import angel_service
    return angel_service.get_profile()


# ══════════════════════════════════════════════════════════════════
# MARKET DATA
# ══════════════════════════════════════════════════════════════════
market_data = APIRouter()

@market_data.get("/ltp/{ticker}")
async def get_ltp(ticker: str, token: str):
    from app.services.market_data.angel_broker import angel_service
    return angel_service.get_ltp("NSE", ticker, token)

@market_data.get("/candles/{token}")
async def get_candles(token: str, interval: str="ONE_MINUTE",
                       from_date: str="2024-01-01 09:15", to_date: str="2024-01-31 15:30"):
    import pandas as pd
    from app.utils.indicators import add_all_indicators
    from app.services.market_data.angel_broker import angel_service
    raw = angel_service.get_candles(token, interval, from_date, to_date)
    if not raw or not raw.get("status"):
        raise HTTPException(400, raw.get("message","Failed to fetch candles"))
    df = pd.DataFrame(raw["data"], columns=["time","open","high","low","close","volume"])
    df = add_all_indicators(df)
    return df.replace({float("nan"): None}).to_dict(orient="records")

@market_data.get("/search/{query}")
async def search_scrip(query: str, exchange: str = "NSE"):
    from app.services.market_data.angel_broker import angel_service
    return angel_service.search_scrip(exchange, query)

@market_data.get("/funds")
async def get_funds():
    from app.services.market_data.angel_broker import angel_service
    return angel_service.get_funds()

@market_data.get("/pcr")
async def get_pcr():
    from app.services.market_data.angel_broker import angel_service
    return angel_service.get_pcr()

@market_data.get("/oi-buildup")
async def get_oi(expiry_type: str = "NEAR"):
    from app.services.market_data.angel_broker import angel_service
    return angel_service.get_oi_buildup({"expiryType": expiry_type})


# ══════════════════════════════════════════════════════════════════
# UNIVERSE
# ══════════════════════════════════════════════════════════════════
universe = APIRouter()

NIFTY50 = [
    {"ticker":"RELIANCE-EQ","token":"2885","name":"Reliance Industries","sector":"Energy"},
    {"ticker":"TCS-EQ","token":"11536","name":"TCS","sector":"IT"},
    {"ticker":"HDFCBANK-EQ","token":"1333","name":"HDFC Bank","sector":"Banking"},
    {"ticker":"ICICIBANK-EQ","token":"4963","name":"ICICI Bank","sector":"Banking"},
    {"ticker":"INFY-EQ","token":"1594","name":"Infosys","sector":"IT"},
    {"ticker":"HINDUNILVR-EQ","token":"1394","name":"HUL","sector":"FMCG"},
    {"ticker":"SBIN-EQ","token":"3045","name":"SBI","sector":"Banking"},
    {"ticker":"BHARTIARTL-EQ","token":"10604","name":"Bharti Airtel","sector":"Telecom"},
    {"ticker":"ITC-EQ","token":"1660","name":"ITC","sector":"FMCG"},
    {"ticker":"KOTAKBANK-EQ","token":"1922","name":"Kotak Bank","sector":"Banking"},
    {"ticker":"LT-EQ","token":"11483","name":"L&T","sector":"Infrastructure"},
    {"ticker":"AXISBANK-EQ","token":"5900","name":"Axis Bank","sector":"Banking"},
    {"ticker":"ASIANPAINT-EQ","token":"236","name":"Asian Paints","sector":"Paints"},
    {"ticker":"MARUTI-EQ","token":"10999","name":"Maruti Suzuki","sector":"Auto"},
    {"ticker":"SUNPHARMA-EQ","token":"3351","name":"Sun Pharma","sector":"Pharma"},
    {"ticker":"TATAMOTORS-EQ","token":"3456","name":"Tata Motors","sector":"Auto"},
    {"ticker":"WIPRO-EQ","token":"3787","name":"Wipro","sector":"IT"},
    {"ticker":"ONGC-EQ","token":"2475","name":"ONGC","sector":"Energy"},
    {"ticker":"NTPC-EQ","token":"11630","name":"NTPC","sector":"Power"},
    {"ticker":"HCLTECH-EQ","token":"7229","name":"HCL Tech","sector":"IT"},
    {"ticker":"INDIGO-EQ","token":"11195","name":"IndiGo","sector":"Aviation"},
    {"ticker":"DLF-EQ","token":"14732","name":"DLF","sector":"RealEstate"},
    {"ticker":"BAJFINANCE-EQ","token":"317","name":"Bajaj Finance","sector":"NBFC"},
    {"ticker":"TATASTEEL-EQ","token":"3499","name":"Tata Steel","sector":"Metals"},
    {"ticker":"HINDALCO-EQ","token":"1363","name":"Hindalco","sector":"Metals"},
    {"ticker":"HAL-EQ","token":"2303","name":"HAL","sector":"Defence"},
    {"ticker":"BEL-EQ","token":"383","name":"BEL","sector":"Defence"},
    {"ticker":"DRREDDY-EQ","token":"881","name":"Dr Reddys","sector":"Pharma"},
    {"ticker":"COALINDIA-EQ","token":"20374","name":"Coal India","sector":"Mining"},
    {"ticker":"BRITANNIA-EQ","token":"547","name":"Britannia","sector":"FMCG"},
]

@universe.get("/today")
async def get_universe():
    return {"date":"today","count":len(NIFTY50),"stocks":NIFTY50}

@universe.get("/sectors")
async def get_sectors():
    return {"sectors": sorted(list(set(s["sector"] for s in NIFTY50)))}

@universe.get("/by-sector/{sector}")
async def get_by_sector(sector: str):
    return {"sector":sector,"stocks":[s for s in NIFTY50 if s["sector"].lower()==sector.lower()]}


# ══════════════════════════════════════════════════════════════════
# STRATEGY
# ══════════════════════════════════════════════════════════════════
strategy = APIRouter()

STRATEGIES = [
    {"id":1,"name":"Exylio Momentum","type":"MOMENTUM","is_active":True,"is_paper":False,
     "params":{"ema_fast":20,"ema_slow":50,"rsi_len":14,"rsi_min":55,"rsi_max":75,"vol_mult":1.5,"bap_min":1.3,"window":30}},
    {"id":2,"name":"Exylio Breakout","type":"BREAKOUT","is_active":True,"is_paper":False,
     "params":{"lookback":20,"vol_mult":2.0,"window":25}},
    {"id":3,"name":"Exylio VWAP","type":"VWAP","is_active":True,"is_paper":False,
     "params":{"rsi_len":9,"window":20}},
    {"id":4,"name":"Exylio Mean Reversion","type":"MEAN_REVERSION","is_active":False,"is_paper":True,
     "params":{"bb_len":20,"bb_std":2,"rsi_len":14,"rsi_os":35,"rsi_ob":65,"window":30}},
]

@strategy.get("/list")
async def list_strategies():
    return {"strategies": STRATEGIES}

@strategy.get("/{strategy_id}")
async def get_strategy_by_id(strategy_id: int):
    s = next((s for s in STRATEGIES if s["id"]==strategy_id), None)
    if not s: raise HTTPException(404,"Strategy not found")
    return s

class StrategyUpdate(BaseModel):
    is_active: Optional[bool] = None
    params: Optional[dict] = None

@strategy.put("/{strategy_id}")
async def update_strategy(strategy_id: int, req: StrategyUpdate):
    return {"status":"ok","strategy_id":strategy_id,"updated":req.dict()}


# ══════════════════════════════════════════════════════════════════
# SIGNALS
# ══════════════════════════════════════════════════════════════════
signals = APIRouter()

@signals.get("/history")
async def signal_history(limit: int = 50):
    return {"signals":[],"total":0}

@signals.get("/active")
async def active_signals():
    return {"signals":[],"count":0}


# ══════════════════════════════════════════════════════════════════
# RISK
# ══════════════════════════════════════════════════════════════════
risk = APIRouter()

@risk.get("/config")
async def risk_config():
    return {"max_positions":settings.MAX_POSITIONS,"max_capital_per_trade":settings.MAX_CAPITAL_PER_TRADE,
            "target_profit":settings.TARGET_PROFIT_PER_TRADE,"stop_loss_amount":settings.STOP_LOSS_PER_TRADE,
            "max_holding_days":settings.MAX_HOLDING_DAYS,"daily_loss_limit":settings.DAILY_LOSS_CIRCUIT_BREAKER,
            "total_capital":settings.DEFAULT_CAPITAL,"max_deployable":settings.DEFAULT_CAPITAL*0.80}

@risk.get("/status")
async def risk_status():
    return {"daily_pnl":risk_engine.daily_pnl,"circuit_halted":risk_engine.daily_loss_halted,
            "open_positions":len(risk_engine.open_positions),"total_deployed":risk_engine.total_deployed}

class TargetReq(BaseModel):
    entry_price: float
    quantity: int

@risk.post("/calculate-targets")
async def calc_targets(req: TargetReq):
    return risk_engine.calculate_targets(req.entry_price, req.quantity)


# ══════════════════════════════════════════════════════════════════
# PORTFOLIO
# ══════════════════════════════════════════════════════════════════
portfolio = APIRouter()

@portfolio.get("/snapshot")
async def portfolio_snapshot():
    try:
        from app.services.market_data.angel_broker import angel_service
        h = angel_service.get_holdings()
        p = angel_service.get_positions()
        f = angel_service.get_funds()
        return {"holdings":h.get("data",[]),"positions":p.get("data",[]),"funds":f.get("data",{})}
    except Exception as e:
        return {"holdings":[],"positions":[],"funds":{},"error":str(e)}

@portfolio.get("/holdings")
async def get_holdings():
    from app.services.market_data.angel_broker import angel_service
    return angel_service.get_holdings()

@portfolio.get("/positions")
async def get_positions():
    from app.services.market_data.angel_broker import angel_service
    return angel_service.get_positions()


# ══════════════════════════════════════════════════════════════════
# ORDERS
# ══════════════════════════════════════════════════════════════════
orders = APIRouter()

class BuyReq(BaseModel):
    ticker: str
    token: str
    entry_price: float
    sector: Optional[str] = ""

@orders.post("/buy")
async def place_buy(req: BuyReq):
    from app.services.execution.order_engine import order_engine
    return await order_engine.full_trade_entry(req.ticker, req.token, req.entry_price, req.sector)

class SellReq(BaseModel):
    ticker: str
    token: str
    quantity: int
    order_type: str = "MARKET"
    price: float = 0

@orders.post("/sell")
async def place_sell(req: SellReq):
    from app.services.execution.order_engine import order_engine
    return await order_engine.place_delivery_sell(req.ticker, req.token, req.quantity, req.order_type, req.price)

@orders.get("/book")
async def get_order_book():
    from app.services.execution.order_engine import order_engine
    return await order_engine.get_order_book()

@orders.delete("/{order_id}")
async def cancel_order(order_id: str):
    from app.services.execution.order_engine import order_engine
    return await order_engine.cancel_order(order_id)

@orders.get("/gtt/list")
async def list_gtt():
    from app.services.market_data.angel_broker import angel_service
    return angel_service.list_gtt()


# ══════════════════════════════════════════════════════════════════
# BACKTESTING
# ══════════════════════════════════════════════════════════════════
backtesting = APIRouter()

class BacktestReq(BaseModel):
    strategy_type: str = "MOMENTUM"
    params: dict = {}
    token: str = "2885"
    from_date: str = "2024-01-01 09:15"
    to_date: str = "2024-01-31 15:30"
    initial_capital: float = 200000

@backtesting.post("/run")
async def run_backtest(req: BacktestReq):
    from app.services.strategy.engine import get_strategy
    from app.services.market_data.angel_broker import angel_service
    raw = angel_service.get_candles(req.token, "ONE_MINUTE", req.from_date, req.to_date)
    if not raw or not raw.get("status") or not raw.get("data"):
        raise HTTPException(400, "Failed to fetch historical data")
    candles = [{"time":c[0],"open":c[1],"high":c[2],"low":c[3],"close":c[4],"volume":c[5]} for c in raw["data"]]
    strat = get_strategy(req.strategy_type, req.params)
    capital = req.initial_capital
    equity_curve = [{"time":candles[0]["time"],"value":capital}]
    wins = losses = 0
    position = None
    trades = []
    for candle in candles:
        sig = strat.update(candle)
        if sig and not position and sig["direction"]=="BUY":
            qty = max(1, int(40000/candle["close"]))
            position = {"entry":candle["close"],"qty":qty}
        elif sig and position and sig["direction"]=="SELL":
            pnl = calculate_net_pnl(position["entry"], candle["close"], position["qty"])
            capital += pnl["net_pnl"]
            if pnl["net_pnl"] > 0: wins += 1
            else: losses += 1
            trades.append(pnl)
            equity_curve.append({"time":candle["time"],"value":round(capital,2)})
            position = None
    total = wins + losses
    return {"strategy":req.strategy_type,"total_trades":total,"wins":wins,"losses":losses,
            "win_rate":round(wins/total*100,1) if total else 0,
            "net_pnl":round(capital-req.initial_capital,2),
            "equity_curve":equity_curve,"trades":trades[-10:]}

@backtesting.get("/history")
async def backtest_history():
    return {"runs":[]}


# ══════════════════════════════════════════════════════════════════
# PAPER TRADING
# ══════════════════════════════════════════════════════════════════
paper_trading = APIRouter()
_paper = {"capital":200000,"deployed":0,"holdings":[],"trades":[],"pnl":0}

class PaperBuyReq(BaseModel):
    ticker: str
    token: str
    price: float
    sector: Optional[str] = ""

@paper_trading.post("/buy")
async def paper_buy(req: PaperBuyReq):
    qty = max(1, int(40000/req.price))
    targets = risk_engine.calculate_targets(req.price, qty)
    holding = {"ticker":req.ticker,"token":req.token,"sector":req.sector,"quantity":qty,
               "avg_price":req.price,"target_price":targets["target_price"],
               "stop_loss":targets["stop_loss_price"],"is_paper":True}
    _paper["holdings"].append(holding)
    _paper["deployed"] += req.price * qty
    return {"status":"ok","holding":holding,"targets":targets}

@paper_trading.get("/portfolio")
async def paper_portfolio():
    return _paper

@paper_trading.get("/holdings")
async def paper_holdings():
    return {"holdings":_paper["holdings"]}


# ══════════════════════════════════════════════════════════════════
# AI ANALYTICS
# ══════════════════════════════════════════════════════════════════
ai_analytics = APIRouter()

@ai_analytics.get("/sentiment/{ticker}")
async def get_sentiment(ticker: str):
    return {"ticker":ticker,"bullish_prob":0.65,"bearish_prob":0.25,"neutral_prob":0.10,
            "sentiment_label":"BULLISH","confidence":0.65,"sources_analyzed":12}

@ai_analytics.get("/prediction/{ticker}")
async def get_prediction(ticker: str):
    return {"ticker":ticker,"direction":"UP","probability":0.68,"model":"XGBoost","horizon":"1-3 days"}

@ai_analytics.get("/smart-money/{ticker}")
async def get_smart_money(ticker: str, token: str = "2885"):
    try:
        from app.services.market_data.angel_broker import angel_service
        pcr = angel_service.get_pcr()
        oi  = angel_service.get_oi_buildup({"expiryType":"NEAR"})
        return {"ticker":ticker,"pcr":pcr.get("data",{}),"oi":oi.get("data",{}),"smart_money_score":72}
    except Exception as e:
        return {"ticker":ticker,"error":str(e),"smart_money_score":0}


# ══════════════════════════════════════════════════════════════════
# RADAR
# ══════════════════════════════════════════════════════════════════
radar = APIRouter()

@radar.get("/scan")
async def radar_scan():
    from app.services.radar.engine import radar_engine
    events = await radar_engine.run_radar_cycle()
    return {"events":events,"count":len(events)}

@radar.get("/events")
async def radar_events(limit: int = 20):
    return {"events":[],"total":0}

@radar.get("/sector-map/{event_type}")
async def sector_map(event_type: str):
    from app.services.radar.engine import SECTOR_IMPACT_MATRIX
    impact = SECTOR_IMPACT_MATRIX.get(event_type.upper())
    if not impact: raise HTTPException(404, f"No map for {event_type}")
    return {"event_type":event_type,"impact":impact}

@radar.post("/cross-check")
async def cross_check(holdings: List[dict]):
    return {"alerts":[],"message":"No active radar events"}


# ══════════════════════════════════════════════════════════════════
# ALERTS
# ══════════════════════════════════════════════════════════════════
alerts = APIRouter()

@alerts.get("/list")
async def alert_list(limit: int = 50):
    return {"alerts":[],"total":0}

@alerts.put("/{alert_id}/read")
async def mark_read(alert_id: int):
    return {"status":"ok"}

@alerts.get("/config")
async def alert_config():
    return {"telegram_enabled":bool(settings.TELEGRAM_BOT_TOKEN),
            "email_enabled":bool(settings.SENDGRID_API_KEY),"in_app_enabled":True}


# ══════════════════════════════════════════════════════════════════
# DASHBOARD
# ══════════════════════════════════════════════════════════════════
dashboard = APIRouter()

@dashboard.get("/summary")
async def dash_summary():
    try:
        from app.services.market_data.angel_broker import angel_service
        connected = angel_service.is_connected
        funds = angel_service.get_funds() if connected else {}
    except Exception:
        connected = False; funds = {}
    return {"capital":settings.DEFAULT_CAPITAL,"deployed":0,"available":settings.DEFAULT_CAPITAL,
            "gross_pnl":0,"total_charges":0,"net_pnl":0,"open_positions":0,"todays_trades":0,
            "daily_pnl":risk_engine.daily_pnl,"circuit_halted":risk_engine.daily_loss_halted,
            "angel_connected":connected,"funds":funds.get("data",{}),
            "target_per_trade":settings.TARGET_PROFIT_PER_TRADE,"warning_level":"GREEN"}

@dashboard.get("/pnl-panel")
async def pnl_panel():
    gross = 0.0; charge = 0.0; net = gross - charge; pct = 0.0
    return {"gross_pnl":gross,"total_charges":charge,"net_pnl":net,"charge_pct":pct,
            "warning":"GREEN","label":f"₹{gross} - ₹{charge} = ₹{net} in hand"}


# ══════════════════════════════════════════════════════════════════
# CHARGES
# ══════════════════════════════════════════════════════════════════
charges = APIRouter()

class ChargesReq(BaseModel):
    buy_price: float
    sell_price: float
    quantity: int

@charges.post("/calculate")
async def calc_charges(req: ChargesReq):
    return calculate_net_pnl(req.buy_price, req.sell_price, req.quantity)

@charges.get("/scale-table")
async def charges_scale(avg_trade_value: float = 10000):
    return {"table": scale_charges_table(avg_trade_value)}
