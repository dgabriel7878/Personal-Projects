"""Classic trend-following swing strategy: fast SMA crossing a slow SMA."""

from backtesting import Strategy
from backtesting.lib import crossover

from trading_bot.strategies.indicators import sma


class SmaCrossover(Strategy):
    fast_n = 20
    slow_n = 50

    def init(self):
        self.sma_fast = self.I(sma, self.data.Close, self.fast_n)
        self.sma_slow = self.I(sma, self.data.Close, self.slow_n)

    def next(self):
        if crossover(self.sma_fast, self.sma_slow):
            self.position.close()
            self.buy()
        elif crossover(self.sma_slow, self.sma_fast):
            self.position.close()
