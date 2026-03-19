import React, { useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { dashboardAPI, riskAPI, universeAPI } from "../services/api";
import { useExylioStore } from "../store";
import {
  TrendingUp, TrendingDown, Shield, Zap,
  Activity, Target, AlertTriangle, CheckCircle
} from "lucide-react";

function StatCard({ label, value, sub, color = "indigo", icon: Icon }) {
  const colors = {
    indigo:  "border-indigo-500/30 bg-indigo-500/10",
    green:   "border-emerald-500/30 bg-emerald-500/10",
    red:     "border-red-500/30 bg-red-500/10",
    yellow:  "border-yellow-500/30 bg-yellow-500/10",
    slate:   "border-slate-700 bg-slate-800",
  };
  return (
    <div className={`rounded-xl border p-4 ${colors[color]}`}>
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs text-slate-500 mb-1">{label}</p>
          <p className={`text-xl font-bold font-mono
            ${color === "green" ? "text-emerald-400"
            : color === "red"   ? "text-red-400"
            : color === "yellow"? "text-yellow-400"
            : "text-slate-100"}`}>
            {value}
          </p>
          {sub && <p className="text-xs text-slate-500 mt-1">{sub}</p>}
        </div>
        {Icon && <Icon size={20} className="text-slate-600" />}
      </div>
    </div>
  );
}

export default function Dashboard() {
  const { setPnLPanel, setRiskStatus, setAngelConnected } = useExylioStore();

  const { data: summary } = useQuery({
    queryKey:  ["dashboard-summary"],
    queryFn:   () => dashboardAPI.getSummary().then(r => r.data),
    refetchInterval: 10000,
  });

  const { data: pnlPanel } = useQuery({
    queryKey:  ["pnl-panel"],
    queryFn:   () => dashboardAPI.getPnLPanel().then(r => r.data),
    refetchInterval: 5000,
  });

  const { data: riskStatus } = useQuery({
    queryKey:  ["risk-status"],
    queryFn:   () => riskAPI.getStatus().then(r => r.data),
    refetchInterval: 10000,
  });

  const { data: riskConfig } = useQuery({
    queryKey:  ["risk-config"],
    queryFn:   () => riskAPI.getConfig().then(r => r.data),
  });

  const { data: universe } = useQuery({
    queryKey:  ["universe"],
    queryFn:   () => universeAPI.getToday().then(r => r.data),
  });

  useEffect(() => {
    if (pnlPanel) setPnLPanel(pnlPanel);
    if (riskStatus) setRiskStatus(riskStatus);
    if (summary) setAngelConnected(summary.angel_connected);
  }, [pnlPanel, riskStatus, summary]);

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">Dashboard</h1>
          <p className="text-sm text-slate-500">
            NIFTY 50 · Delivery · ₹2L Capital Plan
          </p>
        </div>
        <div className="flex items-center gap-2">
          {summary?.angel_connected
            ? <span className="flex items-center gap-1.5 text-xs text-emerald-400 bg-emerald-400/10 px-3 py-1 rounded-full border border-emerald-400/20">
                <CheckCircle size={12} /> Angel One Live
              </span>
            : <span className="flex items-center gap-1.5 text-xs text-red-400 bg-red-400/10 px-3 py-1 rounded-full border border-red-400/20">
                <AlertTriangle size={12} /> Disconnected
              </span>
          }
        </div>
      </div>

      {/* Circuit breaker banner */}
      {riskStatus?.circuit_halted && (
        <div className="flex items-center gap-3 bg-red-500/10 border border-red-500/30 rounded-xl px-4 py-3">
          <AlertTriangle className="text-red-400" size={18} />
          <div>
            <p className="text-red-400 font-semibold text-sm">⚡ Circuit Breaker Active</p>
            <p className="text-xs text-slate-400">
              Daily loss limit hit. Trading halted until market open tomorrow.
            </p>
          </div>
        </div>
      )}

      {/* KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard
          label="Total Capital"
          value={`₹${(summary?.capital || 200000).toLocaleString("en-IN")}`}
          sub="₹2L plan"
          icon={Shield}
          color="slate"
        />
        <StatCard
          label="Deployed"
          value={`₹${(summary?.deployed || 0).toLocaleString("en-IN")}`}
          sub={`${summary?.open_positions || 0} positions`}
          icon={Activity}
          color="indigo"
        />
        <StatCard
          label="Daily P&L"
          value={`₹${(riskStatus?.daily_pnl || 0).toLocaleString("en-IN")}`}
          sub={`Limit: ₹${riskConfig?.daily_loss_limit || 800}`}
          icon={riskStatus?.daily_pnl >= 0 ? TrendingUp : TrendingDown}
          color={riskStatus?.daily_pnl >= 0 ? "green" : "red"}
        />
        <StatCard
          label="Target / Trade"
          value={`₹${riskConfig?.target_profit || 250}`}
          sub="net after charges"
          icon={Target}
          color="green"
        />
      </div>

      {/* Capital allocation breakdown */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bg-slate-900 rounded-xl border border-slate-800 p-5">
          <h3 className="text-sm font-semibold text-slate-300 mb-4 flex items-center gap-2">
            <Shield size={15} className="text-indigo-400" />
            Capital Allocation Rules
          </h3>
          <div className="space-y-3">
            {[
              ["Total Capital",        `₹${(riskConfig?.total_capital || 200000).toLocaleString("en-IN")}`],
              ["Max Deployable (80%)", `₹${(riskConfig?.max_deployable || 160000).toLocaleString("en-IN")}`],
              ["Per Trade Max",        `₹${riskConfig?.max_capital_per_trade || 40000}`],
              ["Max Positions",        riskConfig?.max_positions || 4],
              ["Max Holding Days",     riskConfig?.max_holding_days || 5],
              ["Daily Loss Limit",     `₹${riskConfig?.daily_loss_limit || 800}`],
            ].map(([k, v]) => (
              <div key={k} className="flex justify-between items-center text-sm">
                <span className="text-slate-500">{k}</span>
                <span className="font-mono text-slate-200 font-medium">{v}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-slate-900 rounded-xl border border-slate-800 p-5">
          <h3 className="text-sm font-semibold text-slate-300 mb-4 flex items-center gap-2">
            <Zap size={15} className="text-yellow-400" />
            Today's Universe
          </h3>
          <div className="flex items-center gap-4 mb-3">
            <div className="text-center">
              <p className="text-2xl font-bold text-indigo-400">{universe?.count || 0}</p>
              <p className="text-xs text-slate-500">Stocks</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-emerald-400">NIFTY 50</p>
              <p className="text-xs text-slate-500">Index</p>
            </div>
          </div>
          <div className="flex flex-wrap gap-1.5 mt-3">
            {(universe?.stocks || []).slice(0, 12).map(s => (
              <span key={s.ticker}
                className="text-xs bg-slate-800 text-slate-400 px-2 py-0.5 rounded">
                {s.name}
              </span>
            ))}
            {(universe?.count || 0) > 12 && (
              <span className="text-xs text-slate-600">
                +{universe.count - 12} more
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Strategies quick status */}
      <div className="bg-slate-900 rounded-xl border border-slate-800 p-5">
        <h3 className="text-sm font-semibold text-slate-300 mb-4">
          Active Strategies
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {[
            { name: "Momentum",       active: true,  mode: "Live"  },
            { name: "Breakout",       active: true,  mode: "Live"  },
            { name: "VWAP",           active: true,  mode: "Live"  },
            { name: "Mean Reversion", active: false, mode: "Paper" },
          ].map(s => (
            <div key={s.name}
              className={`rounded-lg p-3 border text-center
                ${s.active
                  ? "border-emerald-500/30 bg-emerald-500/10"
                  : "border-slate-700 bg-slate-800"
                }`}>
              <p className="text-xs font-medium text-slate-300">{s.name}</p>
              <p className={`text-xs mt-1 ${s.active ? "text-emerald-400" : "text-slate-500"}`}>
                {s.active ? "● Running" : "○ Paused"} · {s.mode}
              </p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
