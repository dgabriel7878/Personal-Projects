"""Hand-rolled technical indicators, kept dependency-free and easy to audit.

Each function accepts an array-like (backtesting.py passes its own _Array
wrapper) and returns a plain pandas Series/tuple of Series so it can be
plugged straight into Strategy.I().
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def sma(values, n: int) -> pd.Series:
    return pd.Series(values).rolling(n).mean()


def ema(values, n: int) -> pd.Series:
    return pd.Series(values).ewm(span=n, adjust=False).mean()


def rsi(values, n: int = 14) -> pd.Series:
    series = pd.Series(values)
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / n, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / n, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def macd(values, n_fast: int = 12, n_slow: int = 26, n_signal: int = 9):
    fast = ema(values, n_fast)
    slow = ema(values, n_slow)
    macd_line = fast - slow
    signal_line = macd_line.ewm(span=n_signal, adjust=False).mean()
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram


def bollinger_bands(values, n: int = 20, n_std: float = 2.0):
    series = pd.Series(values)
    mid = series.rolling(n).mean()
    std = series.rolling(n).std()
    upper = mid + n_std * std
    lower = mid - n_std * std
    return upper, mid, lower


def donchian_channel(high, low, n: int = 20):
    upper = pd.Series(high).rolling(n).max()
    lower = pd.Series(low).rolling(n).min()
    return upper, lower
