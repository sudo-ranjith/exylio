"""
Exylio Strategy Engine
Uses built-in indicators — no pandas-ta dependency.
"""
from abc import ABC, abstractmethod
from collections import deque
import pandas as pd
from app.utils.indicators import ema, rsi, vwap, bbands, sma


class BaseStrategy(ABC):
    def __init__(self, params: dict):
        self.params  = params
        self.window  = params.get("window", 30)
        self.candles = deque(maxlen=self.window)

    def update(self, candle: dict) -> dict | None:
        self.candles.append(candle)
        if len(self.candles) < self.window:
            return None
        df = pd.DataFrame(list(self.candles))
        return self.generate_signal(df, candle)

    @abstractmethod
    def generate_signal(self, df: pd.DataFrame, latest: dict) -> dict | None:
        pass

    def _signal(self, direction, strength, confidence, price, reason):
        return {"direction": direction, "strength": strength,
                "confidence": round(confidence, 2), "price": price, "reason": reason}


class MomentumStrategy(BaseStrategy):
    def generate_signal(self, df, latest):
        p = self.params
        df["ema20"]   = ema(df["close"], p.get("ema_fast", 20))
        df["ema50"]   = ema(df["close"], p.get("ema_slow", 50))
        df["rsi"]     = rsi(df["close"], p.get("rsi_len", 14))
        df["vwap"]    = vwap(df["high"], df["low"], df["close"], df["volume"])
        df["vol_avg"] = df["volume"].rolling(20).mean()
        last, prev    = df.iloc[-1], df.iloc[-2]

        trend_ok     = last["close"] > last["ema20"] > last["ema50"]
        rsi_ok       = p.get("rsi_min", 55) <= last["rsi"] <= p.get("rsi_max", 75)
        vol_spike    = (last["volume"] / max(last["vol_avg"], 1)) >= p.get("vol_mult", 1.5)
        above_vwap   = last["close"] > last["vwap"]
        buy_pressure = latest.get("bid_ask_ratio", 1.0) >= p.get("bap_min", 1.3)

        if trend_ok and rsi_ok and above_vwap and vol_spike:
            conf = 0.65 + (0.1 if buy_pressure else 0)
            return self._signal("BUY", "STRONG", min(conf, 0.95), last["close"],
                                "EMA trend + RSI momentum + volume surge")
        if last["close"] < last["ema20"] or last["rsi"] < 40:
            return self._signal("SELL", "MODERATE", 0.65, last["close"],
                                "Price below EMA20 or RSI oversold")
        return None


class BreakoutStrategy(BaseStrategy):
    def generate_signal(self, df, latest):
        p  = self.params
        lb = p.get("lookback", 20)
        df["resistance"] = df["high"].rolling(lb).max()
        df["support"]    = df["low"].rolling(lb).min()
        df["vol_avg"]    = df["volume"].rolling(lb).mean()
        last, prev       = df.iloc[-1], df.iloc[-2]

        breakout = (last["close"] > prev["resistance"] and
                    last["volume"] > last["vol_avg"] * p.get("vol_mult", 2.0))
        breakdown = (last["close"] < prev["support"] and
                     last["volume"] > last["vol_avg"] * 1.5)

        if breakout:
            return self._signal("BUY", "STRONG", 0.75, last["close"],
                                f"Breakout above {round(prev['resistance'], 2)}")
        if breakdown:
            return self._signal("SELL", "STRONG", 0.70, last["close"],
                                f"Breakdown below {round(prev['support'], 2)}")
        return None


class VWAPStrategy(BaseStrategy):
    def generate_signal(self, df, latest):
        df["vwap"] = vwap(df["high"], df["low"], df["close"], df["volume"])
        df["rsi"]  = rsi(df["close"], self.params.get("rsi_len", 9))
        last, prev = df.iloc[-1], df.iloc[-2]

        cross_up = last["close"] > last["vwap"] and prev["close"] <= prev["vwap"]
        rsi_up   = last["rsi"] > prev["rsi"] and last["rsi"] > 45

        if cross_up and rsi_up:
            return self._signal("BUY", "STRONG", 0.72, last["close"],
                                "VWAP cross from below + RSI recovery")
        if last["close"] < last["vwap"] and prev["close"] >= prev["vwap"]:
            return self._signal("SELL", "MODERATE", 0.62, last["close"],
                                "Price crossed below VWAP")
        return None


class MeanReversionStrategy(BaseStrategy):
    def generate_signal(self, df, latest):
        p   = self.params
        _bb = bbands(df["close"], p.get("bb_len", 20), p.get("bb_std", 2))
        key = f"{float(p.get('bb_std', 2)):.1f}"
        df["bb_upper"] = _bb[f"BBU_{p.get('bb_len',20)}_{key}"]
        df["bb_lower"] = _bb[f"BBL_{p.get('bb_len',20)}_{key}"]
        df["bb_mid"]   = _bb[f"BBM_{p.get('bb_len',20)}_{key}"]
        df["rsi"]      = rsi(df["close"], p.get("rsi_len", 14))
        last           = df.iloc[-1]

        if last["close"] < last["bb_lower"] and last["rsi"] < p.get("rsi_os", 35):
            return self._signal("BUY", "STRONG", 0.70, last["close"],
                                f"Oversold below BB lower — RSI {round(last['rsi'],1)}")
        if last["close"] > last["bb_upper"] and last["rsi"] > p.get("rsi_ob", 65):
            return self._signal("SELL", "STRONG", 0.68, last["close"],
                                f"Overbought above BB upper — RSI {round(last['rsi'],1)}")
        return None


STRATEGY_REGISTRY = {
    "MOMENTUM":       MomentumStrategy,
    "BREAKOUT":       BreakoutStrategy,
    "VWAP":           VWAPStrategy,
    "MEAN_REVERSION": MeanReversionStrategy,
}

def get_strategy(strategy_type: str, params: dict) -> BaseStrategy:
    cls = STRATEGY_REGISTRY.get(strategy_type.upper())
    if not cls:
        raise ValueError(f"Unknown strategy: {strategy_type}")
    return cls(params)
