"""
Exylio Built-in Indicators
Pure pandas + numpy — no external TA library needed.
Covers everything pandas-ta was used for.
"""
import pandas as pd
import numpy as np


def ema(series: pd.Series, length: int) -> pd.Series:
    return series.ewm(span=length, adjust=False).mean()


def sma(series: pd.Series, length: int) -> pd.Series:
    return series.rolling(window=length).mean()


def rsi(series: pd.Series, length: int = 14) -> pd.Series:
    delta = series.diff()
    gain  = delta.clip(lower=0).rolling(length).mean()
    loss  = (-delta.clip(upper=0)).rolling(length).mean()
    rs    = gain / loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def macd(series: pd.Series, fast=12, slow=26, signal=9) -> pd.DataFrame:
    ema_fast   = ema(series, fast)
    ema_slow   = ema(series, slow)
    macd_line  = ema_fast - ema_slow
    signal_line= ema(macd_line, signal)
    histogram  = macd_line - signal_line
    return pd.DataFrame({
        f"MACD_{fast}_{slow}_{signal}":  macd_line,
        f"MACDs_{fast}_{slow}_{signal}": signal_line,
        f"MACDh_{fast}_{slow}_{signal}": histogram,
    })


def bbands(series: pd.Series, length=20, std=2.0) -> pd.DataFrame:
    mid   = sma(series, length)
    stdev = series.rolling(length).std()
    upper = mid + std * stdev
    lower = mid - std * stdev
    return pd.DataFrame({
        f"BBU_{length}_{std}": upper,
        f"BBM_{length}_{std}": mid,
        f"BBL_{length}_{std}": lower,
    })


def vwap(high: pd.Series, low: pd.Series,
         close: pd.Series, volume: pd.Series) -> pd.Series:
    tp  = (high + low + close) / 3
    return (tp * volume).cumsum() / volume.cumsum()


def atr(high: pd.Series, low: pd.Series,
        close: pd.Series, length=14) -> pd.Series:
    prev_close = close.shift(1)
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low  - prev_close).abs(),
    ], axis=1).max(axis=1)
    return tr.rolling(length).mean()


def stoch(high: pd.Series, low: pd.Series,
          close: pd.Series, k=14, d=3) -> pd.DataFrame:
    lowest  = low.rolling(k).min()
    highest = high.rolling(k).max()
    k_pct   = 100 * (close - lowest) / (highest - lowest).replace(0, np.nan)
    d_pct   = k_pct.rolling(d).mean()
    return pd.DataFrame({"STOCHk": k_pct, "STOCHd": d_pct})


def add_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add all standard indicators to an OHLCV dataframe.
    Used by market_data route and strategy engine.
    """
    df = df.copy()
    df["ema20"]    = ema(df["close"], 20)
    df["ema50"]    = ema(df["close"], 50)
    df["sma200"]   = sma(df["close"], 200)
    df["rsi"]      = rsi(df["close"], 14)
    df["vwap"]     = vwap(df["high"], df["low"], df["close"], df["volume"])
    df["vol_avg"]  = df["volume"].rolling(20).mean()
    df["atr"]      = atr(df["high"], df["low"], df["close"], 14)

    _macd = macd(df["close"])
    df["macd"]     = _macd["MACD_12_26_9"]
    df["macd_sig"] = _macd["MACDs_12_26_9"]
    df["macd_hist"]= _macd["MACDh_12_26_9"]

    _bb = bbands(df["close"], 20, 2.0)
    df["bb_upper"] = _bb["BBU_20_2.0"]
    df["bb_mid"]   = _bb["BBM_20_2.0"]
    df["bb_lower"] = _bb["BBL_20_2.0"]

    df["pivot"]    = (df["high"] + df["low"] + df["close"]) / 3
    df["r1"]       = 2 * df["pivot"] - df["low"]
    df["s1"]       = 2 * df["pivot"] - df["high"]

    return df
