"""Bidirectional intraday trend-following: long when a fast EMA is above a
slow EMA (uptrend), short when below (downtrend), both computed on
5-minute closes. Opposite premise from the mean-reversion intraday
strategies -- bets that an intraday move continues rather than reverts.
Exits on a trend-crossover reversal, a hard ATR stop-loss, or end of day
(never holds overnight)."""

import numpy as np
import pandas as pd
from backtesting import Strategy

from trading_bot.strategies.indicators import atr, ema
from trading_bot.strategies.risk import risk_based_size


class IntradayEmaTrend(Strategy):
    fast_n = 9
    slow_n = 21
    atr_n = 14
    stop_atr_mult = 1.5
    risk_per_trade = 0.02
    # Same re-entry whipsaw concern as the mean-reversion strategies: a
    # stop-out in a choppy market can leave the EMAs on the verge of
    # re-crossing right back, so a short cooldown avoids re-entering into
    # the same chop repeatedly.
    cooldown_bars = 3

    def init(self):
        self.fast = self.I(ema, self.data.Close, self.fast_n)
        self.slow = self.I(ema, self.data.Close, self.slow_n)
        self.atr = self.I(atr, self.data.High, self.data.Low, self.data.Close, self.atr_n)
        self.day_id = pd.factorize(self.data.index.date)[0]
        self.last_exit_bar = -10**9
        self._was_in_position = False

    def next(self):
        i = len(self.data) - 1
        is_last_bar_of_day = i == len(self.day_id) - 1 or self.day_id[i + 1] != self.day_id[i]
        price = self.data.Close[-1]

        if self._was_in_position and not self.position:
            self.last_exit_bar = i
        self._was_in_position = bool(self.position)

        if np.isnan(self.slow[-1]):
            return
        uptrend = self.fast[-1] > self.slow[-1]

        if self.position:
            if is_last_bar_of_day:
                self.position.close()
            elif self.position.is_long and not uptrend:
                self.position.close()
            elif self.position.is_short and uptrend:
                self.position.close()
            return

        if is_last_bar_of_day or i - self.last_exit_bar < self.cooldown_bars:
            return

        atr_value = self.atr[-1]
        if not atr_value or np.isnan(atr_value):
            return

        if uptrend:
            stop_price = price - self.stop_atr_mult * atr_value
            size = risk_based_size(self.equity, price, stop_price, self.risk_per_trade)
            if size:
                self.buy(size=size, sl=stop_price)
        else:
            stop_price = price + self.stop_atr_mult * atr_value
            size = risk_based_size(self.equity, price, stop_price, self.risk_per_trade)
            if size:
                self.sell(size=size, sl=stop_price)
