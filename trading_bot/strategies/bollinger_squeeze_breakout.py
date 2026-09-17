"""Volatility breakout: wait for a Bollinger Band "squeeze" (bandwidth near
its lowest in `squeeze_lookback` bars, signaling compressed volatility),
then buy when price breaks out above the upper band. Exits back at the
midline. Squeezes are a well-known precursor to sharp directional moves."""

import numpy as np
from backtesting import Strategy

from trading_bot.strategies.indicators import bollinger_bands, bollinger_bandwidth


class BollingerSqueezeBreakout(Strategy):
    n = 20
    n_std = 2.0
    squeeze_lookback = 120
    squeeze_percentile = 0.2

    def init(self):
        self.upper, self.mid, self.lower = self.I(bollinger_bands, self.data.Close, self.n, self.n_std)
        self.width = self.I(bollinger_bandwidth, self.data.Close, self.n, self.n_std)

    def next(self):
        if len(self.data) < self.squeeze_lookback + 1:
            return

        threshold = np.nanquantile(self.width[-self.squeeze_lookback :], self.squeeze_percentile)
        was_squeezed = self.width[-2] <= threshold
        price = self.data.Close[-1]

        if not self.position and was_squeezed and price > self.upper[-1]:
            self.buy()
        elif self.position and price < self.mid[-1]:
            self.position.close()
