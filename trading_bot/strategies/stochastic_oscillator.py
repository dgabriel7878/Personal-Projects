"""Mean-reversion via the Stochastic Oscillator: buy when %K crosses back
above %D from an oversold reading, exit when %K crosses back below %D from
an overbought reading. A different oscillator family than RSI -- based on
where price sits in its recent high/low range, not on the size of recent
up/down moves."""

from backtesting import Strategy
from backtesting.lib import crossover

from trading_bot.strategies.indicators import stochastic


class StochasticOscillator(Strategy):
    k_period = 14
    d_period = 3
    oversold = 20
    overbought = 80

    def init(self):
        self.k, self.d = self.I(
            stochastic, self.data.High, self.data.Low, self.data.Close, self.k_period, self.d_period
        )

    def next(self):
        if not self.position and crossover(self.k, self.d) and self.k[-1] < self.oversold:
            self.buy()
        elif self.position and crossover(self.d, self.k) and self.k[-1] > self.overbought:
            self.position.close()
