"""Bidirectional intraday momentum: when price breaks more than
`entry_atr_mult` ATRs away from the day's volume-weighted average price,
bet the move continues -- long on a breakout above VWAP, short on a
breakdown below. This is the trend-following mirror of VwapMeanReversion
(same distance-from-VWAP signal, opposite bet). Exits when price falls
back to VWAP (the move failed), a hard ATR stop-loss, or end of day
(never holds overnight)."""

import numpy as np
import pandas as pd
from backtesting import Strategy

from trading_bot.strategies.indicators import atr, session_vwap
from trading_bot.strategies.risk import risk_based_size


class VwapMomentum(Strategy):
    atr_n = 14
    entry_atr_mult = 1.5
    stop_atr_mult = 1.0
    risk_per_trade = 0.02
    # Same re-entry whipsaw concern as VwapMeanReversion: a stop-out near
    # the entry threshold can leave price right back at that threshold.
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

        if self._was_in_position and not self.position:
            self.last_exit_bar = i
        self._was_in_position = bool(self.position)

        if self.position:
            if is_last_bar_of_day:
                self.position.close()
            elif self.position.is_long and price <= self.vwap[-1]:
                self.position.close()
            elif self.position.is_short and price >= self.vwap[-1]:
                self.position.close()
            return

        if is_last_bar_of_day or i - self.last_exit_bar < self.cooldown_bars:
            return

        atr_value = self.atr[-1]
        if not atr_value or np.isnan(atr_value):
            return

        deviation = price - self.vwap[-1]
        if deviation > self.entry_atr_mult * atr_value:
            stop_price = price - self.stop_atr_mult * atr_value
            size = risk_based_size(self.equity, price, stop_price, self.risk_per_trade)
            if size:
                self.buy(size=size, sl=stop_price)
        elif deviation < -self.entry_atr_mult * atr_value:
            stop_price = price + self.stop_atr_mult * atr_value
            size = risk_based_size(self.equity, price, stop_price, self.risk_per_trade)
            if size:
                self.sell(size=size, sl=stop_price)
