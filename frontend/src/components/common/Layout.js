import React from "react";
import { Outlet, NavLink } from "react-router-dom";
import { useExylioStore } from "../../store";
import {
  LayoutDashboard, LineChart, Briefcase, Cpu,
  FlaskConical, Radar, Bell, Settings,
  TestTube2, Wifi, WifiOff, AlertTriangle,
  TrendingUp, TrendingDown, Minus
} from "lucide-react";

const NAV = [
  { to: "/dashboard",  icon: LayoutDashboard, label: "Dashboard"   },
  { to: "/charts",     icon: LineChart,        label: "Charts"      },
  { to: "/portfolio",  icon: Briefcase,        label: "Portfolio"   },
  { to: "/strategies", icon: Cpu,              label: "Strategies"  },
  { to: "/backtest",   icon: FlaskConical,     label: "Backtest"    },
  { to: "/paper",      icon: TestTube2,        label: "Paper Trade" },
  { to: "/radar",      icon: Radar,            label: "Radar"       },
  { to: "/alerts",     icon: Bell,             label: "Alerts"      },
  { to: "/settings",   icon: Settings,         label: "Settings"    },
];

export default function Layout() {
  const { angelConnected, grossPnL, totalCharges, netPnL,
          warningLevel, dailyPnL, circuitHalted,
          unreadCount, isPaperMode, togglePaperMode } = useExylioStore();

  const warnColor = {
    GREEN:  "text-emerald-400",
    YELLOW: "text-yellow-400",
    RED:    "text-red-400",
  }[warningLevel] || "text-emerald-400";

  return (
    <div className="flex h-screen bg-slate-950 text-slate-300 overflow-hidden">

      {/* ── Sidebar ──────────────────────────────────────────── */}
      <aside className="w-56 bg-slate-900 border-r border-slate-800 flex flex-col">
        {/* Logo */}
        <div className="px-5 py-4 border-b border-slate-800">
          <h1 className="text-xl font-bold text-indigo-400 tracking-tight">⚡ EXYLIO</h1>
          <p className="text-xs text-slate-500 mt-0.5">Algo Trading Platform</p>
        </div>

        {/* Nav */}
        <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
          {NAV.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to} to={to}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-all
                 ${isActive
                   ? "bg-indigo-600 text-white"
                   : "text-slate-400 hover:bg-slate-800 hover:text-slate-200"
                 }`
              }
            >
              <Icon size={16} />
              {label}
            </NavLink>
          ))}
        </nav>

        {/* Paper mode toggle */}
        <div className="px-4 py-3 border-t border-slate-800">
          <button
            onClick={togglePaperMode}
            className={`w-full text-xs px-3 py-1.5 rounded-lg font-medium transition-all
              ${isPaperMode
                ? "bg-yellow-500/20 text-yellow-400 border border-yellow-500/30"
                : "bg-slate-800 text-slate-400 hover:text-slate-200"
              }`}
          >
            {isPaperMode ? "📋 Paper Mode ON" : "📋 Switch to Paper"}
          </button>
        </div>

        {/* Connection status */}
        <div className="px-4 py-3 border-t border-slate-800">
          <div className={`flex items-center gap-2 text-xs
            ${angelConnected ? "text-emerald-400" : "text-red-400"}`}>
            {angelConnected ? <Wifi size={12} /> : <WifiOff size={12} />}
            {angelConnected ? "Angel One Connected" : "Disconnected"}
          </div>
          {circuitHalted && (
            <div className="flex items-center gap-1 text-xs text-red-400 mt-1">
              <AlertTriangle size={12} />
              Circuit Breaker Active
            </div>
          )}
        </div>
      </aside>

      {/* ── Main ────────────────────────────────────────────── */}
      <div className="flex-1 flex flex-col overflow-hidden">

        {/* ── Top P&L Panel ──────────────────────────────────── */}
        <header className="bg-slate-900 border-b border-slate-800 px-6 py-3">
          <div className="flex items-center justify-between">

            {/* P&L Summary */}
            <div className="flex items-center gap-8">
              <div className="flex items-center gap-2">
                <span className="text-xs text-slate-500">Gross P&L</span>
                <span className={`font-mono font-bold text-sm
                  ${grossPnL >= 0 ? "text-emerald-400" : "text-red-400"}`}>
                  {grossPnL >= 0 ? "+" : ""}₹{grossPnL.toLocaleString("en-IN")}
                </span>
              </div>

              <span className="text-slate-600">−</span>

              <div className="flex items-center gap-2">
                <span className="text-xs text-slate-500">Charges</span>
                <span className="font-mono font-bold text-sm text-slate-300">
                  ₹{totalCharges.toLocaleString("en-IN")}
                </span>
              </div>

              <span className="text-slate-600">=</span>

              <div className="flex items-center gap-2">
                <span className="text-xs text-slate-500">Net in Hand</span>
                <span className={`font-mono font-bold text-base ${warnColor}`}>
                  {netPnL >= 0 ? "+" : ""}₹{netPnL.toLocaleString("en-IN")}
                </span>
                {netPnL > 0 && <TrendingUp size={14} className="text-emerald-400" />}
                {netPnL < 0 && <TrendingDown size={14} className="text-red-400" />}
                {netPnL === 0 && <Minus size={14} className="text-slate-500" />}
              </div>

              {/* Warning badge */}
              {warningLevel !== "GREEN" && (
                <span className={`text-xs px-2 py-0.5 rounded-full font-medium
                  ${warningLevel === "RED"
                    ? "bg-red-500/20 text-red-400 border border-red-500/30"
                    : "bg-yellow-500/20 text-yellow-400 border border-yellow-500/30"
                  }`}>
                  {warningLevel === "RED" ? "⚠ High Charges" : "⚠ Watch Charges"}
                </span>
              )}
            </div>

            {/* Right side */}
            <div className="flex items-center gap-6">
              <div className="text-xs text-slate-500">
                Daily P&L:{" "}
                <span className={dailyPnL >= 0 ? "text-emerald-400" : "text-red-400"}>
                  ₹{dailyPnL.toLocaleString("en-IN")}
                </span>
              </div>

              {/* Alerts bell */}
              <div className="relative">
                <Bell size={16} className="text-slate-400" />
                {unreadCount > 0 && (
                  <span className="absolute -top-1.5 -right-1.5 bg-red-500 text-white
                    text-[10px] rounded-full w-4 h-4 flex items-center justify-center">
                    {unreadCount}
                  </span>
                )}
              </div>

              {/* Clock */}
              <Clock />
            </div>
          </div>
        </header>

        {/* ── Page content ───────────────────────────────────── */}
        <main className="flex-1 overflow-auto">
          <Outlet />
        </main>
      </div>
    </div>
  );
}

function Clock() {
  const [time, setTime] = React.useState(new Date());
  React.useEffect(() => {
    const t = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(t);
  }, []);
  return (
    <span className="font-mono text-xs text-slate-400">
      {time.toLocaleTimeString("en-IN", { timeZone: "Asia/Kolkata" })} IST
    </span>
  );
}
