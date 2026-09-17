"""Bill Williams' Awesome Oscillator: buy when the histogram (fast vs. slow
midpoint-price average) crosses above zero, exit on the reverse cross. A
momentum measure based on price range midpoints rather than closes alone."""

from backtesting import Strategy

from trading_bot.strategies.indicators import awesome_oscillator


class AwesomeOscillatorStrategy(Strategy):
    n_fast = 5
    n_slow = 34

    def init(self):
        self.ao = self.I(awesome_oscillator, self.data.High, self.data.Low, self.n_fast, self.n_slow)

    def next(self):
        if not self.position and self.ao[-1] > 0 and self.ao[-2] <= 0:
            self.buy()
        elif self.position and self.ao[-1] < 0 and self.ao[-2] >= 0:
            self.position.close()
