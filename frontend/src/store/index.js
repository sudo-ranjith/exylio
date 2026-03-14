import { create } from "zustand";

export const useExylioStore = create((set, get) => ({
  // ── Connection ─────────────────────────────────────────────────
  angelConnected: false,
  setAngelConnected: (v) => set({ angelConnected: v }),

  // ── Portfolio ──────────────────────────────────────────────────
  holdings:       [],
  positions:      [],
  funds:          {},
  setHoldings:    (h) => set({ holdings: h }),
  setPositions:   (p) => set({ positions: p }),
  setFunds:       (f) => set({ funds: f }),

  // ── P&L Panel (top bar) ────────────────────────────────────────
  grossPnL:       0,
  totalCharges:   0,
  netPnL:         0,
  warningLevel:   "GREEN",
  setPnLPanel: ({ grossPnL, totalCharges, netPnL, warningLevel }) =>
    set({ grossPnL, totalCharges, netPnL, warningLevel }),

  // ── Risk ───────────────────────────────────────────────────────
  dailyPnL:       0,
  circuitHalted:  false,
  openPositions:  0,
  setRiskStatus: ({ dailyPnL, circuitHalted, openPositions }) =>
    set({ dailyPnL, circuitHalted, openPositions }),

  // ── Radar ──────────────────────────────────────────────────────
  radarEvents:    [],
  radarAlerts:    [],
  addRadarEvent:  (e) => set((s) => ({ radarEvents: [e, ...s.radarEvents].slice(0, 20) })),
  setRadarAlerts: (a) => set({ radarAlerts: a }),

  // ── Alerts ─────────────────────────────────────────────────────
  alerts:         [],
  unreadCount:    0,
  addAlert: (alert) =>
    set((s) => ({
      alerts: [alert, ...s.alerts].slice(0, 50),
      unreadCount: s.unreadCount + 1,
    })),
  clearUnread: () => set({ unreadCount: 0 }),

  // ── Signals ────────────────────────────────────────────────────
  latestSignals:  [],
  addSignal: (sig) =>
    set((s) => ({ latestSignals: [sig, ...s.latestSignals].slice(0, 30) })),

  // ── Selected ticker (for chart) ────────────────────────────────
  selectedTicker: { ticker: "RELIANCE-EQ", token: "2885", name: "Reliance Industries" },
  setSelectedTicker: (t) => set({ selectedTicker: t }),

  // ── Paper mode ─────────────────────────────────────────────────
  isPaperMode:    false,
  togglePaperMode: () => set((s) => ({ isPaperMode: !s.isPaperMode })),
}));
