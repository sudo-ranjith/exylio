from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import yfinance as yf
from database import SessionLocal, User, Portfolio, pwd_context, init_db

app = FastAPI()

app.add_middleware(CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.on_event("startup")
def startup():
    init_db()

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def root():
    return FileResponse("static/index.html")

class LoginRequest(BaseModel):
    email: str
    password: str

@app.post("/api/login")
def login(req: LoginRequest):
    db = SessionLocal()
    user = db.query(User).filter_by(email=req.email).first()
    db.close()
    if not user or not pwd_context.verify(req.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"success": True, "name": user.name, "email": user.email}

@app.get("/api/stocks")
def get_stocks():
    symbols = ["RELIANCE.NS","TCS.NS","HDFCBANK.NS","INFY.NS",
               "ICICIBANK.NS","HAL.NS","ONGC.NS","SBIN.NS"]
    result = []
    for sym in symbols:
        try:
            ticker = yf.Ticker(sym)
            price = ticker.fast_info["last_price"]
            prev  = ticker.fast_info["previous_close"]
            change = ((price - prev) / prev) * 100
            result.append({
                "symbol": sym.replace(".NS",""),
                "price": round(price, 2),
                "change": round(change, 2),
                "up": change > 0
            })
        except:
            pass
    return result

@app.get("/api/portfolio")
def get_portfolio():
    db = SessionLocal()
    positions = db.query(Portfolio).filter_by(user_id=1).all()
    db.close()
    data = []
    for p in positions:
        try:
            ticker = yf.Ticker(p.symbol + ".NS")
            current = ticker.fast_info["last_price"]
            pnl = (current - p.avg_price) * p.qty
            data.append({
                "symbol": p.symbol,
                "qty": p.qty,
                "avg_price": p.avg_price,
                "current_price": round(current, 2),
                "pnl": round(pnl, 2)
            })
        except:
            pass
    return data