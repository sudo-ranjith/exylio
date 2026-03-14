import React, { useEffect } from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "react-hot-toast";
import Layout from "./components/common/Layout";
import Dashboard from "./pages/Dashboard";
import Portfolio from "./pages/Portfolio";
import Charts from "./pages/Charts";
import Strategies from "./pages/Strategies";
import Backtest from "./pages/Backtest";
import Radar from "./pages/Radar";
import Alerts from "./pages/Alerts";
import Settings from "./pages/Settings";
import PaperTrading from "./pages/PaperTrading";
import "./styles/globals.css";

const queryClient = new QueryClient({
  defaultOptions: { queries: { refetchInterval: 30000 } },
});

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Toaster
          position="top-right"
          toastOptions={{
            style: {
              background: "#1E293B",
              color: "#CBD5E1",
              border: "1px solid #334155",
            },
          }}
        />
        <Routes>
          <Route path="/" element={<Layout />}>
            <Route index element={<Navigate to="/dashboard" replace />} />
            <Route path="dashboard"    element={<Dashboard />} />
            <Route path="portfolio"    element={<Portfolio />} />
            <Route path="charts"       element={<Charts />} />
            <Route path="strategies"   element={<Strategies />} />
            <Route path="backtest"     element={<Backtest />} />
            <Route path="radar"        element={<Radar />} />
            <Route path="alerts"       element={<Alerts />} />
            <Route path="paper"        element={<PaperTrading />} />
            <Route path="settings"     element={<Settings />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
