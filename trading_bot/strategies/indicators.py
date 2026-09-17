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


def atr(high, low, close, n: int = 14) -> pd.Series:
    high, low, close = pd.Series(high), pd.Series(low), pd.Series(close)
    prev_close = close.shift(1)
    true_range = pd.concat(
        [high - low, (high - prev_close).abs(), (low - prev_close).abs()], axis=1
    ).max(axis=1)
    return true_range.ewm(alpha=1 / n, adjust=False).mean()


def stochastic(high, low, close, k_period: int = 14, d_period: int = 3):
    high, low, close = pd.Series(high), pd.Series(low), pd.Series(close)
    lowest_low = low.rolling(k_period).min()
    highest_high = high.rolling(k_period).max()
    percent_k = 100 * (close - lowest_low) / (highest_high - lowest_low)
    percent_d = percent_k.rolling(d_period).mean()
    return percent_k, percent_d


def supertrend(high, low, close, n: int = 10, multiplier: float = 3.0):
    """Returns (supertrend_line, direction), direction=+1 uptrend/-1 downtrend.

    Recursive by definition (each band depends on its own previous value),
    so it's computed with a plain Python loop rather than vectorized -- this
    runs once in Strategy.init() over the whole series, not per bar.
    """
    high, low, close = pd.Series(high), pd.Series(low), pd.Series(close)
    hl2 = (high + low) / 2
    atr_val = atr(high, low, close, n)

    basic_upper = hl2 + multiplier * atr_val
    basic_lower = hl2 - multiplier * atr_val

    final_upper = basic_upper.copy()
    final_lower = basic_lower.copy()
    for i in range(1, len(close)):
        if basic_upper.iloc[i] < final_upper.iloc[i - 1] or close.iloc[i - 1] > final_upper.iloc[i - 1]:
            final_upper.iloc[i] = basic_upper.iloc[i]
        else:
            final_upper.iloc[i] = final_upper.iloc[i - 1]

        if basic_lower.iloc[i] > final_lower.iloc[i - 1] or close.iloc[i - 1] < final_lower.iloc[i - 1]:
            final_lower.iloc[i] = basic_lower.iloc[i]
        else:
            final_lower.iloc[i] = final_lower.iloc[i - 1]

    line = pd.Series(index=close.index, dtype=float)
    direction = pd.Series(index=close.index, dtype=float)
    line.iloc[0] = final_upper.iloc[0]
    direction.iloc[0] = -1

    for i in range(1, len(close)):
        was_upper = line.iloc[i - 1] == final_upper.iloc[i - 1]
        if was_upper:
            if close.iloc[i] <= final_upper.iloc[i]:
                line.iloc[i], direction.iloc[i] = final_upper.iloc[i], -1
            else:
                line.iloc[i], direction.iloc[i] = final_lower.iloc[i], 1
        else:
            if close.iloc[i] >= final_lower.iloc[i]:
                line.iloc[i], direction.iloc[i] = final_lower.iloc[i], 1
            else:
                line.iloc[i], direction.iloc[i] = final_upper.iloc[i], -1

    return line, direction
