import axios from "axios";

const API = axios.create({
  baseURL: process.env.REACT_APP_API_URL || "http://localhost:8000",
  timeout: 15000,
});

// ── Market Data ───────────────────────────────────────────────────
export const marketAPI = {
  getLTP:       (ticker, token)                     => API.get(`/api/market/ltp/${ticker}?token=${token}`),
  getCandles:   (token, interval, from, to)         => API.get(`/api/market/candles/${token}?interval=${interval}&from_date=${from}&to_date=${to}`),
  getFunds:     ()                                   => API.get("/api/market/funds"),
  getPCR:       ()                                   => API.get("/api/market/pcr"),
  searchSymbol: (query)                              => API.get(`/api/market/search/${query}`),
};

// ── Universe ──────────────────────────────────────────────────────
export const universeAPI = {
  getToday:     ()         => API.get("/api/universe/today"),
  getSectors:   ()         => API.get("/api/universe/sectors"),
  getBySector:  (sector)   => API.get(`/api/universe/by-sector/${sector}`),
};

// ── Strategy ──────────────────────────────────────────────────────
export const strategyAPI = {
  list:         ()                     => API.get("/api/strategy/list"),
  get:          (id)                   => API.get(`/api/strategy/${id}`),
  update:       (id, data)             => API.put(`/api/strategy/${id}`, data),
};

// ── Portfolio ─────────────────────────────────────────────────────
export const portfolioAPI = {
  getSnapshot:  ()   => API.get("/api/portfolio/snapshot"),
  getHoldings:  ()   => API.get("/api/portfolio/holdings"),
  getPositions: ()   => API.get("/api/portfolio/positions"),
};

// ── Orders ────────────────────────────────────────────────────────
export const ordersAPI = {
  buy:          (data)       => API.post("/api/orders/buy", data),
  sell:         (data)       => API.post("/api/orders/sell", data),
  getBook:      ()           => API.get("/api/orders/book"),
  cancel:       (orderId)    => API.delete(`/api/orders/${orderId}`),
  getGTT:       ()           => API.get("/api/orders/gtt/list"),
};

// ── Dashboard ─────────────────────────────────────────────────────
export const dashboardAPI = {
  getSummary:   ()   => API.get("/api/dashboard/summary"),
  getPnLPanel:  ()   => API.get("/api/dashboard/pnl-panel"),
};

// ── Charges ───────────────────────────────────────────────────────
export const chargesAPI = {
  calculate:    (data)            => API.post("/api/charges/calculate", data),
  getScaleTable:(avgValue)        => API.get(`/api/charges/scale-table?avg_trade_value=${avgValue}`),
};

// ── Signals ───────────────────────────────────────────────────────
export const signalsAPI = {
  getHistory:   (limit)  => API.get(`/api/signals/history?limit=${limit}`),
  getActive:    ()       => API.get("/api/signals/active"),
};

// ── Risk ──────────────────────────────────────────────────────────
export const riskAPI = {
  getConfig:    ()       => API.get("/api/risk/config"),
  getStatus:    ()       => API.get("/api/risk/status"),
  calcTargets:  (data)   => API.post("/api/risk/calculate-targets", data),
};

// ── Radar ─────────────────────────────────────────────────────────
export const radarAPI = {
  scan:         ()             => API.get("/api/radar/scan"),
  getEvents:    ()             => API.get("/api/radar/events"),
  getSectorMap: (eventType)    => API.get(`/api/radar/sector-map/${eventType}`),
};

// ── Alerts ────────────────────────────────────────────────────────
export const alertsAPI = {
  list:         ()        => API.get("/api/alerts/list"),
  markRead:     (id)      => API.put(`/api/alerts/${id}/read`),
};

// ── Backtesting ───────────────────────────────────────────────────
export const backtestAPI = {
  run:          (data)   => API.post("/api/backtest/run", data),
  getHistory:   ()       => API.get("/api/backtest/history"),
};

// ── Auth ──────────────────────────────────────────────────────────
export const authAPI = {
  login:        (data)   => API.post("/api/auth/login", data),
  logout:       ()       => API.post("/api/auth/logout"),
  getProfile:   ()       => API.get("/api/auth/profile"),
  refresh:      ()       => API.post("/api/auth/refresh"),
};

// ── WebSocket helper ──────────────────────────────────────────────
export const createWebSocket = (path) => {
  const wsUrl = process.env.REACT_APP_WS_URL || "ws://localhost:8000";
  return new WebSocket(`${wsUrl}${path}`);
};

export default API;
