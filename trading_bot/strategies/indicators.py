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
    # avg_loss == 0 with avg_gain > 0 (no losses at all in the window) is a
    # real, if rare, case -- RSI should be 100 there, not NaN from a 0
    # division guard. Zero gain AND zero loss (no movement at all) is
    # genuinely undefined; 50 (neutral) is the conventional value.
    rs = avg_gain / avg_loss
    result = 100 - (100 / (1 + rs))
    return result.where(~(avg_gain.eq(0) & avg_loss.eq(0)), 50.0)


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


def bollinger_bandwidth(values, n: int = 20, n_std: float = 2.0) -> pd.Series:
    upper, mid, lower = bollinger_bands(values, n, n_std)
    return (upper - lower) / mid


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


def adx_dmi(high, low, close, n: int = 14):
    """Average Directional Index + Directional Movement Indicators.
    Returns (+DI, -DI, ADX)."""
    high, low, close = pd.Series(high), pd.Series(low), pd.Series(close)
    up_move = high.diff()
    down_move = -low.diff()
    plus_dm = pd.Series(np.where((up_move > down_move) & (up_move > 0), up_move, 0.0), index=high.index)
    minus_dm = pd.Series(np.where((down_move > up_move) & (down_move > 0), down_move, 0.0), index=high.index)

    smoothed_atr = atr(high, low, close, n)
    plus_di = 100 * plus_dm.ewm(alpha=1 / n, adjust=False).mean() / smoothed_atr
    minus_di = 100 * minus_dm.ewm(alpha=1 / n, adjust=False).mean() / smoothed_atr
    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di)
    adx = dx.ewm(alpha=1 / n, adjust=False).mean()
    return plus_di, minus_di, adx


def ichimoku(high, low, close, tenkan_n: int = 9, kijun_n: int = 26, senkou_b_n: int = 52, shift: int = 26):
    """Returns (tenkan, kijun, span_a, span_b). Spans are shifted forward by
    `shift` bars, same convention as how the cloud is plotted -- so at bar i
    they reflect data known `shift` bars ago, never the future."""
    high, low = pd.Series(high), pd.Series(low)
    tenkan = (high.rolling(tenkan_n).max() + low.rolling(tenkan_n).min()) / 2
    kijun = (high.rolling(kijun_n).max() + low.rolling(kijun_n).min()) / 2
    span_a = ((tenkan + kijun) / 2).shift(shift)
    span_b = ((high.rolling(senkou_b_n).max() + low.rolling(senkou_b_n).min()) / 2).shift(shift)
    return tenkan, kijun, span_a, span_b


def parabolic_sar(high, low, af_step: float = 0.02, af_max: float = 0.2):
    """Returns (sar, direction), direction=+1 uptrend/-1 downtrend.
    Recursive by definition; computed with a plain Python loop."""
    high, low = pd.Series(high), pd.Series(low)
    n = len(high)
    sar = pd.Series(index=high.index, dtype=float)
    direction = pd.Series(index=high.index, dtype=float)

    uptrend = True
    af = af_step
    ep = high.iloc[0]
    sar.iloc[0] = low.iloc[0]
    direction.iloc[0] = 1

    for i in range(1, n):
        prev_sar = sar.iloc[i - 1]
        new_sar = prev_sar + af * (ep - prev_sar)

        if uptrend:
            new_sar = min(new_sar, low.iloc[i - 1], low.iloc[i - 2] if i >= 2 else low.iloc[i - 1])
            if low.iloc[i] < new_sar:
                uptrend = False
                new_sar = ep
                ep = low.iloc[i]
                af = af_step
            elif high.iloc[i] > ep:
                ep = high.iloc[i]
                af = min(af + af_step, af_max)
        else:
            new_sar = max(new_sar, high.iloc[i - 1], high.iloc[i - 2] if i >= 2 else high.iloc[i - 1])
            if high.iloc[i] > new_sar:
                uptrend = True
                new_sar = ep
                ep = high.iloc[i]
                af = af_step
            elif low.iloc[i] < ep:
                ep = low.iloc[i]
                af = min(af + af_step, af_max)

        sar.iloc[i] = new_sar
        direction.iloc[i] = 1 if uptrend else -1

    return sar, direction


def keltner_channel(high, low, close, n: int = 20, multiplier: float = 2.0):
    middle = ema(close, n)
    atr_val = atr(high, low, close, n)
    upper = middle + multiplier * atr_val
    lower = middle - multiplier * atr_val
    return upper, middle, lower


def linreg_slope(values, n: int = 20) -> pd.Series:
    series = pd.Series(values)
    x = np.arange(n)
    x_mean = x.mean()
    denom = ((x - x_mean) ** 2).sum()

    def _slope(y):
        return ((x - x_mean) * (y - y.mean())).sum() / denom

    return series.rolling(n).apply(_slope, raw=True)


def roc(values, n: int = 12) -> pd.Series:
    series = pd.Series(values)
    return (series / series.shift(n) - 1) * 100


def momentum_return(values, n: int = 252) -> pd.Series:
    series = pd.Series(values)
    return series / series.shift(n) - 1


def williams_r(high, low, close, n: int = 14) -> pd.Series:
    high, low, close = pd.Series(high), pd.Series(low), pd.Series(close)
    highest_high = high.rolling(n).max()
    lowest_low = low.rolling(n).min()
    return -100 * (highest_high - close) / (highest_high - lowest_low)


def cci(high, low, close, n: int = 20) -> pd.Series:
    high, low, close = pd.Series(high), pd.Series(low), pd.Series(close)
    typical_price = (high + low + close) / 3
    sma_tp = typical_price.rolling(n).mean()
    mean_abs_dev = typical_price.rolling(n).apply(lambda x: np.abs(x - x.mean()).mean(), raw=True)
    return (typical_price - sma_tp) / (0.015 * mean_abs_dev)


def return_zscore(values, n: int = 20) -> pd.Series:
    series = pd.Series(values)
    ret = series.pct_change()
    return (ret - ret.rolling(n).mean()) / ret.rolling(n).std()


def obv(close, volume) -> pd.Series:
    close, volume = pd.Series(close), pd.Series(volume)
    direction = np.sign(close.diff()).fillna(0)
    return (direction * volume).cumsum()


def chaikin_money_flow(high, low, close, volume, n: int = 20) -> pd.Series:
    high, low, close, volume = pd.Series(high), pd.Series(low), pd.Series(close), pd.Series(volume)
    money_flow_mult = ((close - low) - (high - close)) / (high - low).replace(0, np.nan)
    money_flow_volume = money_flow_mult * volume
    return money_flow_volume.rolling(n).sum() / volume.rolling(n).sum()


def accum_dist(high, low, close, volume) -> pd.Series:
    high, low, close, volume = pd.Series(high), pd.Series(low), pd.Series(close), pd.Series(volume)
    money_flow_mult = ((close - low) - (high - close)) / (high - low).replace(0, np.nan)
    return (money_flow_mult * volume).cumsum()


def awesome_oscillator(high, low, n_fast: int = 5, n_slow: int = 34) -> pd.Series:
    high, low = pd.Series(high), pd.Series(low)
    median_price = (high + low) / 2
    return median_price.rolling(n_fast).mean() - median_price.rolling(n_slow).mean()


def fisher_transform(high, low, n: int = 10):
    high, low = pd.Series(high), pd.Series(low)
    median_price = (high + low) / 2
    highest = median_price.rolling(n).max()
    lowest = median_price.rolling(n).min()
    raw = 2 * ((median_price - lowest) / (highest - lowest).replace(0, np.nan) - 0.5)
    raw = raw.clip(-0.999, 0.999)
    value = raw.ewm(alpha=0.5, adjust=False).mean()
    fisher = 0.5 * np.log((1 + value) / (1 - value))
    fisher = fisher.ewm(alpha=0.5, adjust=False).mean()
    signal = fisher.shift(1)
    return fisher, signal


def money_flow_index(high, low, close, volume, n: int = 14) -> pd.Series:
    high, low, close, volume = pd.Series(high), pd.Series(low), pd.Series(close), pd.Series(volume)
    typical_price = (high + low + close) / 3
    raw_money_flow = typical_price * volume
    direction = typical_price.diff()

    positive_flow = raw_money_flow.where(direction > 0, 0.0).rolling(n).sum()
    negative_flow = raw_money_flow.where(direction < 0, 0.0).rolling(n).sum()
    money_ratio = positive_flow / negative_flow.replace(0, np.nan)
    return 100 - (100 / (1 + money_ratio))


def vortex_indicator(high, low, close, n: int = 14):
    high, low, close = pd.Series(high), pd.Series(low), pd.Series(close)
    prev_close = close.shift(1)
    prev_low = low.shift(1)
    prev_high = high.shift(1)

    vm_plus = (high - prev_low).abs()
    vm_minus = (low - prev_high).abs()
    true_range = pd.concat(
        [high - low, (high - prev_close).abs(), (low - prev_close).abs()], axis=1
    ).max(axis=1)

    tr_sum = true_range.rolling(n).sum()
    vi_plus = vm_plus.rolling(n).sum() / tr_sum
    vi_minus = vm_minus.rolling(n).sum() / tr_sum
    return vi_plus, vi_minus


def session_vwap(high, low, close, volume, index) -> pd.Series:
    """Volume-weighted average price, resetting at the start of each
    calendar day -- the standard intraday VWAP, not a rolling one.
    `index` is the bar timestamps (pass `self.data.index`); backtesting.py
    forwards non-price args through Strategy.I() untouched, so this slots
    in the same way as any other multi-arg indicator here."""
    high, low, close, volume = pd.Series(high), pd.Series(low), pd.Series(close), pd.Series(volume)
    typical_price = (high + low + close) / 3
    dates = np.asarray(index.date) if hasattr(index, "date") else pd.DatetimeIndex(index).date
    cum_pv = (typical_price * volume).groupby(dates).cumsum()
    cum_vol = volume.groupby(dates).cumsum()
    return cum_pv / cum_vol
