// ── Portfolio Page ────────────────────────────────────────────────
import React from "react";
import { useQuery } from "@tanstack/react-query";
import { portfolioAPI, chargesAPI } from "../services/api";

export function Portfolio() {
  const { data: snapshot } = useQuery({
    queryKey: ["portfolio-snapshot"],
    queryFn:  () => portfolioAPI.getSnapshot().then(r => r.data),
    refetchInterval: 15000,
  });

  const { data: scaleTable } = useQuery({
    queryKey: ["charges-scale"],
    queryFn:  () => chargesAPI.getScaleTable(10000).then(r => r.data),
  });

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-2xl font-bold text-slate-100">Portfolio</h1>

      {/* Holdings */}
      <div className="bg-slate-900 rounded-xl border border-slate-800 p-5">
        <h2 className="text-sm font-semibold text-slate-300 mb-4">Open Holdings</h2>
        {(snapshot?.holdings || []).length === 0 ? (
          <p className="text-sm text-slate-500 text-center py-8">
            No open holdings. Strategies will auto-buy when signals fire.
          </p>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="text-xs text-slate-500 border-b border-slate-800">
                <th className="text-left pb-2">Stock</th>
                <th className="text-right pb-2">Qty</th>
                <th className="text-right pb-2">Avg Price</th>
                <th className="text-right pb-2">LTP</th>
                <th className="text-right pb-2">P&L</th>
                <th className="text-right pb-2">Target</th>
              </tr>
            </thead>
            <tbody>
              {(snapshot.holdings).map((h, i) => (
                <tr key={i} className="border-b border-slate-800/50 hover:bg-slate-800/30">
                  <td className="py-2 text-slate-200 font-medium">{h.tradingsymbol}</td>
                  <td className="py-2 text-right text-slate-400">{h.quantity}</td>
                  <td className="py-2 text-right font-mono text-slate-300">₹{h.averageprice}</td>
                  <td className="py-2 text-right font-mono text-slate-300">₹{h.ltp}</td>
                  <td className={`py-2 text-right font-mono font-bold
                    ${h.profitandloss >= 0 ? "text-emerald-400" : "text-red-400"}`}>
                    ₹{h.profitandloss}
                  </td>
                  <td className="py-2 text-right text-slate-500">—</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Charges scale table */}
      <div className="bg-slate-900 rounded-xl border border-slate-800 p-5">
        <h2 className="text-sm font-semibold text-slate-300 mb-4">
          📊 Brokerage Scale — Angel One Delivery (₹10K avg trade)
        </h2>
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="text-slate-500 border-b border-slate-800">
                {["Trades/Day","Brokerage","STT","DP Charges","Other","Total/Day","Total/Month","Total/Year"]
                  .map(h => <th key={h} className="text-right pb-2 pr-4 last:pr-0">{h}</th>)}
              </tr>
            </thead>
            <tbody>
              {(scaleTable?.table || []).map((row) => (
                <tr key={row.trades_per_day} className="border-b border-slate-800/50">
                  <td className="py-2 pr-4 font-bold text-indigo-400">{row.trades_per_day}</td>
                  <td className="py-2 pr-4 text-right font-mono text-slate-300">₹{row.brokerage?.toLocaleString("en-IN")}</td>
                  <td className="py-2 pr-4 text-right font-mono text-slate-300">₹{row.stt?.toLocaleString("en-IN")}</td>
                  <td className="py-2 pr-4 text-right font-mono text-slate-300">₹{row.dp_charge?.toLocaleString("en-IN")}</td>
                  <td className="py-2 pr-4 text-right font-mono text-slate-300">₹{row.other_charges?.toLocaleString("en-IN")}</td>
                  <td className="py-2 pr-4 text-right font-mono font-bold text-yellow-400">₹{row.total_per_day?.toLocaleString("en-IN")}</td>
                  <td className="py-2 pr-4 text-right font-mono text-slate-400">₹{row.total_per_month?.toLocaleString("en-IN")}</td>
                  <td className="py-2 text-right font-mono text-red-400">₹{row.total_per_year?.toLocaleString("en-IN")}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

// ── Radar Page ────────────────────────────────────────────────────
export function Radar() {
  const [scanning, setScanning] = React.useState(false);
  const [events, setEvents]     = React.useState([]);

  const { radarAPI } = require("../services/api");

  const handleScan = async () => {
    setScanning(true);
    try {
      const res = await radarAPI.scan();
      setEvents(res.data.events || []);
    } finally {
      setScanning(false);
    }
  };

  const severityColor = {
    LOW:     "text-slate-400 bg-slate-800 border-slate-700",
    MEDIUM:  "text-yellow-400 bg-yellow-500/10 border-yellow-500/30",
    HIGH:    "text-orange-400 bg-orange-500/10 border-orange-500/30",
    EXTREME: "text-red-400 bg-red-500/10 border-red-500/30",
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">🔭 Exylio Radar</h1>
          <p className="text-sm text-slate-500">Macro Event Intelligence Engine</p>
        </div>
        <button
          onClick={handleScan}
          disabled={scanning}
          className="bg-indigo-600 hover:bg-indigo-700 text-white text-sm px-4 py-2 rounded-lg
                     disabled:opacity-50 transition-all"
        >
          {scanning ? "Scanning..." : "🔭 Run Radar Scan"}
        </button>
      </div>

      {/* Sector impact reference */}
      <div className="grid grid-cols-2 gap-4">
        <div className="bg-slate-900 rounded-xl border border-emerald-500/20 p-4">
          <h3 className="text-xs font-bold text-emerald-400 mb-3">📈 WAR EVENT — Stocks to RISE</h3>
          {[
            ["Defence", "HAL, BEL, BHEL", "HIGH"],
            ["Energy", "ONGC, Oil India", "HIGH"],
            ["IT", "TCS, Infy (INR depreciation)", "MEDIUM"],
            ["Pharma", "Sun Pharma, Dr Reddy's", "MEDIUM"],
          ].map(([sector, stocks, conf]) => (
            <div key={sector} className="flex justify-between items-center py-1.5 border-b border-slate-800 text-xs">
              <div>
                <span className="text-slate-300 font-medium">{sector}</span>
                <span className="text-slate-500 ml-2">{stocks}</span>
              </div>
              <span className="text-emerald-400">{conf}</span>
            </div>
          ))}
        </div>
        <div className="bg-slate-900 rounded-xl border border-red-500/20 p-4">
          <h3 className="text-xs font-bold text-red-400 mb-3">📉 WAR EVENT — Stocks to FALL</h3>
          {[
            ["Aviation", "IndiGo", "HIGH"],
            ["Auto", "Maruti, Tata Motors", "HIGH"],
            ["Paints", "Asian Paints", "HIGH"],
            ["Banking", "HDFC Bank, ICICI", "MEDIUM"],
          ].map(([sector, stocks, conf]) => (
            <div key={sector} className="flex justify-between items-center py-1.5 border-b border-slate-800 text-xs">
              <div>
                <span className="text-slate-300 font-medium">{sector}</span>
                <span className="text-slate-500 ml-2">{stocks}</span>
              </div>
              <span className="text-red-400">{conf}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Live radar events */}
      {events.length > 0 && (
        <div className="space-y-3">
          <h2 className="text-sm font-semibold text-slate-300">Latest Radar Events</h2>
          {events.map((e, i) => (
            <div key={i} className={`rounded-xl border p-4 ${severityColor[e.severity_label] || severityColor.LOW}`}>
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-xs font-bold px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                      {e.event_type}
                    </span>
                    <span className="text-xs font-bold">{e.severity_label}</span>
                    <span className="text-xs text-slate-500">
                      Confidence: {Math.round(e.confidence * 100)}%
                    </span>
                  </div>
                  <p className="text-sm text-slate-200">{e.headline}</p>
                </div>
                <span className="text-xs text-slate-500 ml-4">Score: {e.severity_score}</span>
              </div>
            </div>
          ))}
        </div>
      )}

      {events.length === 0 && !scanning && (
        <div className="text-center py-12 text-slate-500 text-sm">
          No events scanned yet. Click "Run Radar Scan" to fetch latest macro events.
        </div>
      )}
    </div>
  );
}

// ── Strategies Page ───────────────────────────────────────────────
export function Strategies() {
  const { data: strategies } = require("@tanstack/react-query").useQuery({
    queryKey: ["strategies"],
    queryFn:  () => require("../services/api").strategyAPI.list().then(r => r.data),
  });

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-2xl font-bold text-slate-100">Strategy Engine</h1>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {(strategies?.strategies || []).map(s => (
          <div key={s.id} className="bg-slate-900 rounded-xl border border-slate-800 p-5">
            <div className="flex items-center justify-between mb-3">
              <div>
                <h3 className="font-bold text-slate-200">{s.name}</h3>
                <span className="text-xs text-indigo-400">{s.type}</span>
              </div>
              <div className="flex items-center gap-2">
                {s.is_paper && (
                  <span className="text-xs bg-yellow-500/20 text-yellow-400 px-2 py-0.5 rounded">PAPER</span>
                )}
                <span className={`text-xs px-2 py-0.5 rounded ${
                  s.is_active ? "bg-emerald-500/20 text-emerald-400" : "bg-slate-800 text-slate-500"
                }`}>
                  {s.is_active ? "Active" : "Paused"}
                </span>
              </div>
            </div>
            <div className="space-y-1">
              {Object.entries(s.params || {}).map(([k, v]) => (
                <div key={k} className="flex justify-between text-xs">
                  <span className="text-slate-500">{k}</span>
                  <span className="font-mono text-slate-300">{v}</span>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ── Backtest Page ─────────────────────────────────────────────────
export function Backtest() {
  const [form, setForm] = React.useState({
    strategy_type: "MOMENTUM", token: "2885",
    from_date: "2024-01-01 09:15", to_date: "2024-01-31 15:30",
    params: { ema_fast: 20, ema_slow: 50, rsi_len: 14, rsi_min: 55, rsi_max: 75, vol_mult: 1.5, bap_min: 1.3, window: 30 }
  });
  const [result, setResult] = React.useState(null);
  const [running, setRunning] = React.useState(false);

  const run = async () => {
    setRunning(true);
    try {
      const res = await require("../services/api").backtestAPI.run(form);
      setResult(res.data);
    } finally { setRunning(false); }
  };

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-2xl font-bold text-slate-100">Backtesting Engine</h1>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-slate-900 rounded-xl border border-slate-800 p-5 space-y-4">
          <h2 className="text-sm font-semibold text-slate-300">Configure Backtest</h2>
          <div>
            <label className="text-xs text-slate-500">Strategy</label>
            <select
              value={form.strategy_type}
              onChange={e => setForm(f => ({...f, strategy_type: e.target.value}))}
              className="w-full mt-1 bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200"
            >
              {["MOMENTUM","BREAKOUT","VWAP","MEAN_REVERSION"].map(s => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs text-slate-500">From Date</label>
              <input value={form.from_date}
                onChange={e => setForm(f => ({...f, from_date: e.target.value}))}
                className="w-full mt-1 bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-200" />
            </div>
            <div>
              <label className="text-xs text-slate-500">To Date</label>
              <input value={form.to_date}
                onChange={e => setForm(f => ({...f, to_date: e.target.value}))}
                className="w-full mt-1 bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-200" />
            </div>
          </div>
          <button onClick={run} disabled={running}
            className="w-full bg-indigo-600 hover:bg-indigo-700 text-white py-2 rounded-lg text-sm disabled:opacity-50">
            {running ? "Running..." : "▶ Run Backtest"}
          </button>
        </div>

        {result && (
          <div className="bg-slate-900 rounded-xl border border-slate-800 p-5">
            <h2 className="text-sm font-semibold text-slate-300 mb-4">Results</h2>
            <div className="grid grid-cols-2 gap-3">
              {[
                ["Total Trades", result.total_trades],
                ["Win Rate",     `${result.win_rate}%`],
                ["Wins",         result.wins],
                ["Losses",       result.losses],
                ["Net P&L",      `₹${result.net_pnl?.toLocaleString("en-IN")}`],
              ].map(([k, v]) => (
                <div key={k} className="bg-slate-800 rounded-lg p-3">
                  <p className="text-xs text-slate-500">{k}</p>
                  <p className="font-bold text-slate-100 font-mono">{v}</p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// ── Paper Trading Page ────────────────────────────────────────────
export function PaperTrading() {
  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold text-slate-100 mb-2">📋 Paper Trading</h1>
      <p className="text-sm text-slate-500 mb-6">
        Live simulation using real market prices — no real capital at risk.
      </p>
      <div className="bg-slate-900 rounded-xl border border-slate-800 p-8 text-center">
        <p className="text-slate-400 text-sm">
          Paper trading mode mirrors all live strategies with virtual capital.
          Toggle paper mode from the sidebar to activate.
        </p>
      </div>
    </div>
  );
}

// ── Alerts Page ───────────────────────────────────────────────────
export function Alerts() {
  const { alerts } = require("../store").useExylioStore();
  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold text-slate-100 mb-6">🔔 Alerts</h1>
      {alerts.length === 0 ? (
        <div className="bg-slate-900 rounded-xl border border-slate-800 p-8 text-center">
          <p className="text-slate-500 text-sm">No alerts yet. System will notify on trades, risk events, and radar detections.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {alerts.map((a, i) => (
            <div key={i} className="bg-slate-900 rounded-xl border border-slate-800 p-4">
              <p className="font-medium text-slate-200 text-sm">{a.title}</p>
              <p className="text-xs text-slate-500 mt-1">{a.message}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ── Settings Page ─────────────────────────────────────────────────
export function Settings() {
  const { data: config } = require("@tanstack/react-query").useQuery({
    queryKey: ["risk-config"],
    queryFn:  () => require("../services/api").riskAPI.getConfig().then(r => r.data),
  });

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-2xl font-bold text-slate-100">Settings</h1>
      <div className="bg-slate-900 rounded-xl border border-slate-800 p-5">
        <h2 className="text-sm font-semibold text-slate-300 mb-4">Capital & Risk Configuration</h2>
        <div className="space-y-3">
          {Object.entries(config || {}).map(([k, v]) => (
            <div key={k} className="flex justify-between items-center py-2 border-b border-slate-800">
              <span className="text-sm text-slate-400 capitalize">{k.replace(/_/g, " ")}</span>
              <span className="font-mono text-slate-200 font-medium">{typeof v === "number" ? v.toLocaleString("en-IN") : String(v)}</span>
            </div>
          ))}
        </div>
        <p className="text-xs text-slate-600 mt-4">
          Edit values in your .env file and restart the backend to apply changes.
        </p>
      </div>
    </div>
  );
}
