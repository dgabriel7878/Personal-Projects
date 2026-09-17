"""Trend-following via the Vortex Indicator: buy when +VI crosses above
-VI (upward price movement dominating), exit on the reverse cross. Built
from how far each bar's high/low travels relative to the prior bar,
distinct from the moving-average and ATR-band approaches elsewhere here."""

from backtesting import Strategy
from backtesting.lib import crossover

from trading_bot.strategies.indicators import vortex_indicator


class VortexTrend(Strategy):
    n = 14

    def init(self):
        self.vi_plus, self.vi_minus = self.I(
            vortex_indicator, self.data.High, self.data.Low, self.data.Close, self.n
        )

    def next(self):
        if crossover(self.vi_plus, self.vi_minus):
            self.position.close()
            self.buy()
        elif crossover(self.vi_minus, self.vi_plus):
            self.position.close()
