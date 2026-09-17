"""Bidirectional intraday mean reversion: when price strays far from the
day's volume-weighted average price (more than `entry_atr_mult` ATRs
away), bet on it reverting back toward VWAP -- long when price is well
below VWAP, short when well above. Exits on reversion to VWAP, a hard
ATR stop-loss, or end of day (never holds overnight)."""

import numpy as np
import pandas as pd
from backtesting import Strategy

from trading_bot.strategies.indicators import atr, session_vwap
from trading_bot.strategies.risk import risk_based_size


class VwapMeanReversion(Strategy):
    atr_n = 14
    entry_atr_mult = 1.5
    stop_atr_mult = 1.0
    risk_per_trade = 0.02
    # Bars to wait after a stop-out before re-entering. Without this, a
    # stop-out on a mean-reversion bet leaves price further from VWAP than
    # when the trade opened, so the entry condition re-fires on the very
    # next bar and the strategy re-enters the same losing direction over
    # and over through a real trend -- validated on real 5-min data as
    # 1,000+ trades in 60 days and -70%+ returns. The cooldown breaks that
    # loop; it does not by itself make the premise profitable.
    cooldown_bars = 6

    def init(self):
        self.vwap = self.I(
            session_vwap, self.data.High, self.data.Low, self.data.Close, self.data.Volume, self.data.index
        )
        self.atr = self.I(atr, self.data.High, self.data.Low, self.data.Close, self.atr_n)
        self.day_id = pd.factorize(self.data.index.date)[0]
        self.last_exit_bar = -10**9
        self._was_in_position = False

    def next(self):
        i = len(self.data) - 1
        is_last_bar_of_day = i == len(self.day_id) - 1 or self.day_id[i + 1] != self.day_id[i]
        price = self.data.Close[-1]

        # Catches every exit, including a stop-loss fill, which backtesting.py
        # closes internally -- never through position.close() below -- so
        # relying only on the explicit close() calls would miss it and let
        # the cooldown be skipped right after the exit that most needs it.
        if self._was_in_position and not self.position:
            self.last_exit_bar = i
        self._was_in_position = bool(self.position)

        if self.position:
            if is_last_bar_of_day:
                self.position.close()
            elif self.position.is_long and price >= self.vwap[-1]:
                self.position.close()
            elif self.position.is_short and price <= self.vwap[-1]:
                self.position.close()
            return

        if is_last_bar_of_day or i - self.last_exit_bar < self.cooldown_bars:
            return

        atr_value = self.atr[-1]
        if not atr_value or np.isnan(atr_value):
            return

        deviation = price - self.vwap[-1]
        if deviation < -self.entry_atr_mult * atr_value:
            stop_price = price - self.stop_atr_mult * atr_value
            size = risk_based_size(self.equity, price, stop_price, self.risk_per_trade)
            if size:
                self.buy(size=size, sl=stop_price)
        elif deviation > self.entry_atr_mult * atr_value:
            stop_price = price + self.stop_atr_mult * atr_value
            size = risk_based_size(self.equity, price, stop_price, self.risk_per_trade)
            if size:
                self.sell(size=size, sl=stop_price)
