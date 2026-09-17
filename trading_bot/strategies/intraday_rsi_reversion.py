"""Bidirectional intraday mean reversion via RSI: long when RSI is
oversold, short when overbought, exit on reversion to the RSI midline, a
hard ATR stop-loss, or end of day (never holds overnight). Same idea as
the daily RSI strategies, but on 5-minute bars and trading both
directions instead of only fading dips in an uptrend."""

import numpy as np
import pandas as pd
from backtesting import Strategy

from trading_bot.strategies.indicators import atr, rsi
from trading_bot.strategies.risk import risk_based_size


class IntradayRsiReversion(Strategy):
    rsi_n = 14
    oversold = 30
    overbought = 70
    atr_n = 14
    stop_atr_mult = 1.0
    risk_per_trade = 0.02

    def init(self):
        self.rsi = self.I(rsi, self.data.Close, self.rsi_n)
        self.atr = self.I(atr, self.data.High, self.data.Low, self.data.Close, self.atr_n)
        self.day_id = pd.factorize(self.data.index.date)[0]

    def next(self):
        i = len(self.data) - 1
        is_last_bar_of_day = i == len(self.day_id) - 1 or self.day_id[i + 1] != self.day_id[i]
        price = self.data.Close[-1]

        if self.position:
            if is_last_bar_of_day:
                self.position.close()
            elif self.position.is_long and self.rsi[-1] >= 50:
                self.position.close()
            elif self.position.is_short and self.rsi[-1] <= 50:
                self.position.close()
            return

        if is_last_bar_of_day:
            return

        atr_value = self.atr[-1]
        if not atr_value or np.isnan(atr_value):
            return

        if self.rsi[-1] < self.oversold:
            stop_price = price - self.stop_atr_mult * atr_value
            size = risk_based_size(self.equity, price, stop_price, self.risk_per_trade)
            if size:
                self.buy(size=size, sl=stop_price)
        elif self.rsi[-1] > self.overbought:
            stop_price = price + self.stop_atr_mult * atr_value
            size = risk_based_size(self.equity, price, stop_price, self.risk_per_trade)
            if size:
                self.sell(size=size, sl=stop_price)
