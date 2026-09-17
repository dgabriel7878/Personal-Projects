"""Trend-following via statistics rather than a moving-average line: fit a
linear regression over the trailing window and trade the sign of its
slope. Long while the recent trend is sloping up, flat once it turns down."""

from backtesting import Strategy

from trading_bot.strategies.indicators import linreg_slope


class LinregTrend(Strategy):
    n = 20

    def init(self):
        self.slope = self.I(linreg_slope, self.data.Close, self.n)

    def next(self):
        if not self.position and self.slope[-1] > 0:
            self.buy()
        elif self.position and self.slope[-1] < 0:
            self.position.close()
