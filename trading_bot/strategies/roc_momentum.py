"""Momentum via Rate of Change: buy once the N-bar percentage change turns
positive, exit once it turns negative. A faster, more reactive cousin of
the 252-day absolute-momentum strategy."""

from backtesting import Strategy

from trading_bot.strategies.indicators import roc


class RocMomentum(Strategy):
    n = 20

    def init(self):
        self.roc = self.I(roc, self.data.Close, self.n)

    def next(self):
        if not self.position and self.roc[-1] > 0:
            self.buy()
        elif self.position and self.roc[-1] < 0:
            self.position.close()
