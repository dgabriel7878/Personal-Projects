"""ATR-based trend-following: stay long while the Supertrend line signals
an uptrend, flat when it flips to a downtrend. A popular alternative to
moving-average crossovers that adapts its stop distance to volatility."""

from backtesting import Strategy

from trading_bot.strategies.indicators import supertrend


class SupertrendStrategy(Strategy):
    atr_n = 10
    multiplier = 3.0

    def init(self):
        _, self.direction = self.I(
            supertrend, self.data.High, self.data.Low, self.data.Close, self.atr_n, self.multiplier
        )

    def next(self):
        if not self.position and self.direction[-1] == 1:
            self.buy()
        elif self.position and self.direction[-1] == -1:
            self.position.close()
