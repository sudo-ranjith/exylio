# ⚡ EXYLIO — Algorithmic Trading Platform

Full-stack algo trading platform connected to Angel One SmartAPI.
Built with FastAPI + React + TimescaleDB + Redis.

---

## 🚀 Quick Start

### 1. Clone & Configure
```bash
git clone <your-repo>
cd exylio
cp .env.example .env
# Edit .env with your Angel One credentials
```

### 2. Fill .env
```
ANGEL_API_KEY=your_api_key
ANGEL_CLIENT_CODE=your_client_code
ANGEL_PASSWORD=your_trading_pin
ANGEL_TOTP_SECRET=your_base32_totp_secret
```

### 3. Run with Docker
```bash
docker-compose up --build
```

### 4. Access
- **Dashboard:** http://localhost:3000
- **API Docs:**  http://localhost:8000/docs
- **Health:**    http://localhost:8000/health

---

## 📦 Architecture

```
exylio/
├── backend/                  FastAPI Python backend
│   └── app/
│       ├── api/routes/       All 15 API route modules
│       ├── core/             Config, DB, Redis, Celery
│       ├── models/           SQLAlchemy ORM models
│       └── services/
│           ├── market_data/  Angel One broker + tick aggregator
│           ├── strategy/     4 strategy engines
│           ├── risk/         Risk management rules
│           ├── execution/    Order engine + GTT
│           └── radar/        Macro event intelligence
├── frontend/                 React dashboard
│   └── src/
│       ├── pages/            Dashboard, Charts, Portfolio...
│       ├── components/       Layout, Chart components
│       ├── services/api.js   All API calls
│       └── store/index.js    Zustand global state
└── docker/                   Nginx + DB init scripts
```

---

## 🧩 Modules Implemented

| # | Module | Status |
|---|--------|--------|
| 1 | Market Data (WebSocket + OHLCV) | ✅ |
| 2 | Stock Universe Builder (NIFTY 50) | ✅ |
| 3 | Strategy Engine (4 strategies) | ✅ |
| 4 | Signal Generation Engine | ✅ |
| 5 | Risk Management (6 rules) | ✅ |
| 6 | Portfolio Management | ✅ |
| 7 | Order Execution + GTT | ✅ |
| 8 | Backtesting Engine | ✅ |
| 9 | Paper Trading Module | ✅ |
| 10| AI Analytics (placeholder) | ✅ |
| 11| Monitoring Dashboard | ✅ |
| 12| Alert System | ✅ |
| 13| Radar (Macro Intelligence) | ✅ |
| 14| Trade Cost & Net P&L Panel | ✅ |
| 15| Smart Money Tracking | ✅ |
| 16| Capital Allocation (₹2L plan) | ✅ |
| 17| Charges Calculator | ✅ |

---

## 🔑 Angel One TOTP Setup

1. Login to Angel One developer portal
2. Enable TOTP for your account
3. Scan QR code with Google Authenticator
4. The base32 secret behind the QR = `ANGEL_TOTP_SECRET`

---

## 📅 Scheduled Tasks (Celery Beat)

| Task | Schedule |
|------|----------|
| Build stock universe | 8:30 AM IST daily |
| Refresh Angel One session | Every 6 hours |
| Radar macro scan | Every 15 min (9 AM–4 PM) |
| Reset risk engine | 9:10 AM IST daily |
| Check holding expiry | Every hour during market |

---

## 💰 ₹2L Capital Plan Built-In

- Max 4 positions simultaneously
- ₹40,000 per trade
- Target ₹250 net profit per trade
- Stop-loss ₹200 per trade
- Max holding 5 days
- Circuit breaker at ₹800 daily loss
- Auto GTT for target + stop-loss

---

## 🛠 Development

```bash
# Backend only
cd backend && pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend only
cd frontend && npm install && npm start

# Full stack
docker-compose up
```
