"""Trend-following: fast EMA crossing a slow EMA. Reacts faster than an SMA
crossover since EMAs weight recent prices more heavily."""

from backtesting import Strategy
from backtesting.lib import crossover

from trading_bot.strategies.indicators import ema


class EmaCrossover(Strategy):
    fast_n = 12
    slow_n = 26

    def init(self):
        self.ema_fast = self.I(ema, self.data.Close, self.fast_n)
        self.ema_slow = self.I(ema, self.data.Close, self.slow_n)

    def next(self):
        if crossover(self.ema_fast, self.ema_slow):
            self.position.close()
            self.buy()
        elif crossover(self.ema_slow, self.ema_fast):
            self.position.close()
