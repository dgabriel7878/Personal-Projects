"""Momentum swing strategy: MACD line crossing its signal line."""

from backtesting import Strategy
from backtesting.lib import crossover

from trading_bot.strategies.indicators import macd


class MacdMomentum(Strategy):
    n_fast = 12
    n_slow = 26
    n_signal = 9

    def init(self):
        self.macd_line, self.signal_line, _ = self.I(
            macd, self.data.Close, self.n_fast, self.n_slow, self.n_signal
        )

    def next(self):
        if crossover(self.macd_line, self.signal_line):
            self.position.close()
            self.buy()
        elif crossover(self.signal_line, self.macd_line):
            self.position.close()
