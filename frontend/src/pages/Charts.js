import React, { useEffect, useRef, useState } from "react";
import { createChart, CrosshairMode } from "lightweight-charts";
import { useQuery } from "@tanstack/react-query";
import { marketAPI, universeAPI } from "../services/api";
import { useExylioStore } from "../store";
import { Search, RefreshCw } from "lucide-react";

const INTERVALS = [
  { label: "1m", value: "ONE_MINUTE" },
  { label: "5m", value: "FIVE_MINUTE" },
  { label: "15m", value: "FIFTEEN_MINUTE" },
  { label: "1h", value: "ONE_HOUR" },
  { label: "1D", value: "ONE_DAY" },
];

export default function Charts() {
  const chartRef      = useRef(null);
  const chartInstance = useRef(null);
  const seriesRefs    = useRef({});
  const [interval, setInterval] = useState("ONE_MINUTE");
  const { selectedTicker, setSelectedTicker } = useExylioStore();

  const fromDate = "2024-01-01 09:15";
  const toDate   = "2024-01-31 15:30";

  const { data: candles, isLoading, refetch } = useQuery({
    queryKey:  ["candles", selectedTicker.token, interval],
    queryFn:   () => marketAPI.getCandles(selectedTicker.token, interval, fromDate, toDate)
                              .then(r => r.data),
    enabled:   !!selectedTicker.token,
  });

  const { data: universe } = useQuery({
    queryKey: ["universe"],
    queryFn:  () => universeAPI.getToday().then(r => r.data),
  });

  // ── Build chart once ─────────────────────────────────────────
  useEffect(() => {
    if (!chartRef.current) return;

    const chart = createChart(chartRef.current, {
      layout: {
        background: { color: "#0F172A" },
        textColor:  "#94A3B8",
      },
      grid: {
        vertLines: { color: "#1E293B" },
        horzLines: { color: "#1E293B" },
      },
      crosshair: { mode: CrosshairMode.Normal },
      rightPriceScale: { borderColor: "#334155" },
      timeScale: {
        borderColor:    "#334155",
        timeVisible:    true,
        secondsVisible: false,
      },
    });

    // Candlestick
    seriesRefs.current.candle = chart.addCandlestickSeries({
      upColor:         "#10B981",
      downColor:       "#EF4444",
      borderUpColor:   "#10B981",
      borderDownColor: "#EF4444",
      wickUpColor:     "#10B981",
      wickDownColor:   "#EF4444",
    });

    // EMA overlays
    seriesRefs.current.ema20 = chart.addLineSeries({
      color: "#6366F1", lineWidth: 1, title: "EMA20",
    });
    seriesRefs.current.ema50 = chart.addLineSeries({
      color: "#F59E0B", lineWidth: 1, title: "EMA50",
    });
    seriesRefs.current.vwap = chart.addLineSeries({
      color: "#10B981", lineWidth: 1, lineStyle: 1, title: "VWAP",
    });
    seriesRefs.current.bbUpper = chart.addLineSeries({
      color: "#475569", lineWidth: 1, lineStyle: 2,
    });
    seriesRefs.current.bbLower = chart.addLineSeries({
      color: "#475569", lineWidth: 1, lineStyle: 2,
    });

    // RSI pane
    seriesRefs.current.rsi = chart.addLineSeries({
      color: "#818CF8", lineWidth: 1,
      priceScaleId: "rsi", title: "RSI",
    });
    chart.priceScale("rsi").applyOptions({
      scaleMargins: { top: 0.82, bottom: 0.02 },
    });

    // RSI reference lines
    seriesRefs.current.rsiOB = chart.addLineSeries({
      color: "#EF444444", lineWidth: 1, lineStyle: 2, priceScaleId: "rsi",
    });
    seriesRefs.current.rsiOS = chart.addLineSeries({
      color: "#10B98144", lineWidth: 1, lineStyle: 2, priceScaleId: "rsi",
    });

    // MACD pane
    seriesRefs.current.macd = chart.addLineSeries({
      color: "#6366F1", lineWidth: 1, priceScaleId: "macd", title: "MACD",
    });
    seriesRefs.current.macdSig = chart.addLineSeries({
      color: "#F59E0B", lineWidth: 1, priceScaleId: "macd", title: "Signal",
    });
    seriesRefs.current.macdHist = chart.addHistogramSeries({
      priceScaleId: "macd",
    });
    chart.priceScale("macd").applyOptions({
      scaleMargins: { top: 0.93, bottom: 0.0 },
    });

    chartInstance.current = chart;

    const handleResize = () => {
      chart.applyOptions({ width: chartRef.current.clientWidth });
    };
    window.addEventListener("resize", handleResize);
    return () => {
      window.removeEventListener("resize", handleResize);
      chart.remove();
    };
  }, []);

  // ── Populate chart when data arrives ─────────────────────────
  useEffect(() => {
    if (!candles || !candles.length || !seriesRefs.current.candle) return;

    const valid = candles.filter(d => d.open !== null && d.time);

    const toTime = (t) => {
      // lightweight-charts expects unix timestamp or "YYYY-MM-DD"
      const d = new Date(t);
      return Math.floor(d.getTime() / 1000);
    };

    seriesRefs.current.candle.setData(valid.map(d => ({
      time: toTime(d.time), open: d.open, high: d.high, low: d.low, close: d.close,
    })));

    const setLine = (key, field) => {
      const data = valid.filter(d => d[field] != null)
                        .map(d => ({ time: toTime(d.time), value: d[field] }));
      if (data.length) seriesRefs.current[key]?.setData(data);
    };

    setLine("ema20",    "ema20");
    setLine("ema50",    "ema50");
    setLine("vwap",     "vwap");
    setLine("bbUpper",  "bb_upper");
    setLine("bbLower",  "bb_lower");
    setLine("rsi",      "rsi");
    setLine("macd",     "macd");
    setLine("macdSig",  "macd_sig");

    // MACD histogram with colour
    const histData = valid.filter(d => d.macd_hist != null).map(d => ({
      time:  toTime(d.time),
      value: d.macd_hist,
      color: d.macd_hist >= 0 ? "#10B981" : "#EF4444",
    }));
    if (histData.length) seriesRefs.current.macdHist?.setData(histData);

    // RSI reference lines
    const times = valid.map(d => ({ time: toTime(d.time), value: 70 }));
    const timesOS = valid.map(d => ({ time: toTime(d.time), value: 30 }));
    if (times.length) seriesRefs.current.rsiOB?.setData(times);
    if (timesOS.length) seriesRefs.current.rsiOS?.setData(timesOS);

    // S/R price lines
    const last = valid[valid.length - 1];
    if (last?.pivot) {
      [
        { price: last.r1, color: "#EF4444", title: "R1" },
        { price: last.pivot, color: "#F59E0B", title: "PP" },
        { price: last.s1, color: "#10B981", title: "S1" },
      ].forEach(({ price, color, title }) => {
        if (price) {
          seriesRefs.current.candle?.createPriceLine({
            price, color, lineWidth: 1, lineStyle: 2,
            axisLabelVisible: true, title,
          });
        }
      });
    }

    chartInstance.current?.timeScale().fitContent();
  }, [candles]);

  return (
    <div className="flex h-full bg-slate-950">
      {/* Ticker sidebar */}
      <aside className="w-52 bg-slate-900 border-r border-slate-800 overflow-y-auto">
        <div className="p-3 border-b border-slate-800">
          <div className="flex items-center gap-2 bg-slate-800 rounded-lg px-3 py-2">
            <Search size={13} className="text-slate-500" />
            <span className="text-xs text-slate-500">Search ticker...</span>
          </div>
        </div>
        <div className="p-2 space-y-0.5">
          {(universe?.stocks || []).map(s => (
            <button
              key={s.token}
              onClick={() => setSelectedTicker(s)}
              className={`w-full text-left px-3 py-2 rounded-lg text-xs transition-all
                ${selectedTicker.token === s.token
                  ? "bg-indigo-600 text-white"
                  : "text-slate-400 hover:bg-slate-800 hover:text-slate-200"
                }`}
            >
              <div className="font-medium">{s.name}</div>
              <div className="text-[10px] opacity-60">{s.sector}</div>
            </button>
          ))}
        </div>
      </aside>

      {/* Chart area */}
      <div className="flex-1 flex flex-col">
        {/* Toolbar */}
        <div className="flex items-center gap-4 px-4 py-2 bg-slate-900 border-b border-slate-800">
          <div>
            <span className="font-bold text-slate-100 text-sm">{selectedTicker.name}</span>
            <span className="text-slate-500 text-xs ml-2">{selectedTicker.ticker}</span>
          </div>

          {/* Interval selector */}
          <div className="flex items-center gap-1 ml-4">
            {INTERVALS.map(iv => (
              <button
                key={iv.value}
                onClick={() => setInterval(iv.value)}
                className={`text-xs px-2.5 py-1 rounded transition-all
                  ${interval === iv.value
                    ? "bg-indigo-600 text-white"
                    : "text-slate-400 hover:bg-slate-800"
                  }`}
              >
                {iv.label}
              </button>
            ))}
          </div>

          {/* Indicator legend */}
          <div className="flex items-center gap-3 ml-4 text-xs">
            <span className="flex items-center gap-1">
              <span className="w-3 h-0.5 bg-indigo-400 inline-block" /> EMA20
            </span>
            <span className="flex items-center gap-1">
              <span className="w-3 h-0.5 bg-yellow-400 inline-block" /> EMA50
            </span>
            <span className="flex items-center gap-1">
              <span className="w-3 h-0.5 bg-emerald-400 inline-block" /> VWAP
            </span>
          </div>

          <button
            onClick={() => refetch()}
            className="ml-auto text-slate-400 hover:text-slate-200 transition-colors"
          >
            <RefreshCw size={14} className={isLoading ? "animate-spin" : ""} />
          </button>
        </div>

        {/* Chart container */}
        <div className="flex-1 relative">
          {isLoading && (
            <div className="absolute inset-0 flex items-center justify-center z-10 bg-slate-950/80">
              <div className="text-sm text-slate-400">Loading chart data...</div>
            </div>
          )}
          <div ref={chartRef} className="w-full h-full" />
        </div>
      </div>
    </div>
  );
}
