"""Bidirectional opening-range breakout: define the day's opening range
from its first `range_minutes` of bars, then long a break above the range
high or short a break below the range low (the original
OpeningRangeBreakout only takes the long side). Exits on a return into the
range, a hard ATR stop-loss, or end of day (never holds overnight)."""

import numpy as np
import pandas as pd
from backtesting import Strategy

from trading_bot.strategies.indicators import atr
from trading_bot.strategies.risk import risk_based_size


class OrbBidirectional(Strategy):
    range_minutes = 15
    atr_n = 14
    stop_atr_mult = 1.0
    risk_per_trade = 0.02
    cooldown_bars = 3

    def init(self):
        index = self.data.index
        high = pd.Series(self.data.High, index=index)
        low = pd.Series(self.data.Low, index=index)

        dates = index.date
        minutes_of_day = pd.Series([t.hour * 60 + t.minute for t in index.time], index=index)
        session_open_minute = minutes_of_day.groupby(dates).transform("min")
        minutes_since_open = minutes_of_day - session_open_minute
        in_opening_window = minutes_since_open < self.range_minutes

        window_high = high.where(in_opening_window)
        window_low = low.where(in_opening_window)
        self.or_high = window_high.groupby(dates).transform("max").ffill().values
        self.or_low = window_low.groupby(dates).transform("min").ffill().values
        self.after_window = (~in_opening_window).values
        self.atr = self.I(atr, self.data.High, self.data.Low, self.data.Close, self.atr_n)
        self.day_id = pd.factorize(dates)[0]
        self.last_exit_bar = -10**9
        self._was_in_position = False

    def next(self):
        i = len(self.data) - 1
        is_last_bar_of_day = i == len(self.day_id) - 1 or self.day_id[i + 1] != self.day_id[i]
        price = self.data.Close[-1]

        if self._was_in_position and not self.position:
            self.last_exit_bar = i
        self._was_in_position = bool(self.position)

        if self.position:
            if is_last_bar_of_day:
                self.position.close()
            elif self.position.is_long and price <= self.or_low[i]:
                self.position.close()
            elif self.position.is_short and price >= self.or_high[i]:
                self.position.close()
            return

        if not self.after_window[i] or is_last_bar_of_day or i - self.last_exit_bar < self.cooldown_bars:
            return

        atr_value = self.atr[-1]
        if not atr_value or np.isnan(atr_value):
            return

        if price >= self.or_high[i]:
            stop_price = price - self.stop_atr_mult * atr_value
            size = risk_based_size(self.equity, price, stop_price, self.risk_per_trade)
            if size:
                self.buy(size=size, sl=stop_price)
        elif price <= self.or_low[i]:
            stop_price = price + self.stop_atr_mult * atr_value
            size = risk_based_size(self.equity, price, stop_price, self.risk_per_trade)
            if size:
                self.sell(size=size, sl=stop_price)
