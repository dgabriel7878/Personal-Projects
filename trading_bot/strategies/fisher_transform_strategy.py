"""Fisher Transform turning-point strategy: buy when the Fisher line
crosses above its own one-bar-lagged signal line, exit on the reverse
cross. The transform maps price into a near-Gaussian series that makes
turning points sharper and easier to trigger on than raw oscillators."""

from backtesting import Strategy
from backtesting.lib import crossover

from trading_bot.strategies.indicators import fisher_transform


class FisherTransformStrategy(Strategy):
    n = 10

    def init(self):
        self.fisher, self.signal = self.I(fisher_transform, self.data.High, self.data.Low, self.n)

    def next(self):
        if crossover(self.fisher, self.signal):
            self.position.close()
            self.buy()
        elif crossover(self.signal, self.fisher):
            self.position.close()
